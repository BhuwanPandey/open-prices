import gzip
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase
from PIL import Image

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.ml.image_classifier import run_and_save_proof_prediction
from open_prices.proofs.models import Proof
from open_prices.proofs.utils import fetch_and_save_ocr_data

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
}
LOCATION_OSM_NODE_6509705997 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 6509705997,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Carrefour",
}


class ProofModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_proof_date_validation(self):
        for DATE_OK in [None, "2024-01-01"]:
            ProofFactory(date=DATE_OK)
        for DATE_NOT_OK in ["3000-01-01", "01-01-2000"]:
            self.assertRaises(ValidationError, ProofFactory, date=DATE_NOT_OK)

    def test_proof_location_validation(self):
        location_osm = LocationFactory()
        location_online = LocationFactory(type=location_constants.TYPE_ONLINE)
        # both location_osm_id & location_osm_type not set
        ProofFactory(location_osm_id=None, location_osm_type=None)
        # location_osm_id
        for LOCATION_OSM_ID_OK in location_constants.OSM_ID_OK_LIST:
            ProofFactory(
                location_osm_id=LOCATION_OSM_ID_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        for LOCATION_OSM_ID_NOT_OK in location_constants.OSM_ID_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                ProofFactory,
                location_osm_id=LOCATION_OSM_ID_NOT_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        # location_osm_type
        for LOCATION_OSM_TYPE_OK in location_constants.OSM_TYPE_OK_LIST:
            ProofFactory(
                location_osm_id=652825274, location_osm_type=LOCATION_OSM_TYPE_OK
            )
        for LOCATION_OSM_TYPE_NOT_OK in location_constants.OSM_TYPE_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                ProofFactory,
                location_osm_id=652825274,
                location_osm_type=LOCATION_OSM_TYPE_NOT_OK,
            )
        # location_id unknown
        self.assertRaises(
            ValidationError,
            ProofFactory,
            location_id=999,
            location_osm_id=None,
            location_osm_type=None,
        )
        # cannot mix location_id & location_osm_id/type
        self.assertRaises(
            ValidationError,
            ProofFactory,
            location_id=location_osm.id,
            location_osm_id=None,  # needed
            location_osm_type=None,  # needed
        )
        self.assertRaises(
            ValidationError,
            ProofFactory,
            location_id=location_online.id,
            location_osm_id=LOCATION_OSM_ID_OK,  # should be None
        )
        # location_id ok
        ProofFactory(
            location_id=location_osm.id,
            location_osm_id=location_osm.osm_id,
            location_osm_type=location_osm.osm_type,
        )
        ProofFactory(
            location_id=location_online.id, location_osm_id=None, location_osm_type=None
        )

    def test_proof_receipt_fields(self):
        # receipt_price_count
        for RECEIPT_PRICE_COUNT_NOT_OK in [-5]:  # Decimal("45.10")
            with self.subTest(RECEIPT_PRICE_COUNT_NOT_OK=RECEIPT_PRICE_COUNT_NOT_OK):
                self.assertRaises(
                    ValidationError,
                    ProofFactory,
                    receipt_price_count=RECEIPT_PRICE_COUNT_NOT_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        for RECEIPT_PRICE_COUNT_OK in [None, 0, 5]:
            with self.subTest(RECEIPT_PRICE_COUNT_OK=RECEIPT_PRICE_COUNT_OK):
                ProofFactory(
                    receipt_price_count=RECEIPT_PRICE_COUNT_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        self.assertRaises(
            ValidationError,
            ProofFactory,
            receipt_price_count=5,
            type=proof_constants.TYPE_PRICE_TAG,
        )
        # receipt_price_total
        for RECEIPT_PRICE_TOTAL_NOT_OK in [-5]:
            with self.subTest(RECEIPT_PRICE_TOTAL_NOT_OK=RECEIPT_PRICE_TOTAL_NOT_OK):
                self.assertRaises(
                    ValidationError,
                    ProofFactory,
                    receipt_price_total=RECEIPT_PRICE_TOTAL_NOT_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        for RECEIPT_PRICE_TOTAL_OK in [None, 0, 5, Decimal("45.10")]:
            with self.subTest(RECEIPT_PRICE_TOTAL_OK=RECEIPT_PRICE_TOTAL_OK):
                ProofFactory(
                    receipt_price_total=RECEIPT_PRICE_TOTAL_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        self.assertRaises(
            ValidationError,
            ProofFactory,
            receipt_price_total=5,
            type=proof_constants.TYPE_PRICE_TAG,
        )


class ProofQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof_without_price = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.proof_with_price = ProofFactory(type=proof_constants.TYPE_GDPR_REQUEST)
        PriceFactory(proof_id=cls.proof_with_price.id, price=1.0)

    def test_has_type_single_shop(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.has_type_single_shop().count(), 1)

    def test_has_prices(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.has_prices().count(), 1)

    def test_with_stats(self):
        proof = Proof.objects.with_stats().get(id=self.proof_without_price.id)
        self.assertEqual(proof.price_count_annotated, 0)
        self.assertEqual(proof.price_count, 0)
        proof = Proof.objects.with_stats().get(id=self.proof_with_price.id)
        self.assertEqual(proof.price_count_annotated, 1)
        self.assertEqual(proof.price_count, 1)


class ProofPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location_osm_1 = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_osm_2 = LocationFactory(**LOCATION_OSM_NODE_6509705997)
        cls.proof_price_tag = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location_osm_1.osm_id,
            location_osm_type=cls.location_osm_1.osm_type,
        )
        PriceFactory(
            proof_id=cls.proof_price_tag.id,
            location_osm_id=cls.proof_price_tag.location.osm_id,
            location_osm_type=cls.proof_price_tag.location.osm_type,
            price=1.0,
        )
        PriceFactory(
            proof_id=cls.proof_price_tag.id,
            location_osm_id=cls.proof_price_tag.location.osm_id,
            location_osm_type=cls.proof_price_tag.location.osm_type,
            price=2.0,
        )
        cls.proof_receipt = ProofFactory(type=proof_constants.TYPE_RECEIPT)
        PriceFactory(
            proof_id=cls.proof_receipt.id,
            location_osm_id=cls.location_osm_1.osm_id,
            location_osm_type=cls.location_osm_1.osm_type,
            price=2.0,
            currency="EUR",
            date="2024-06-30",
        )

    def test_is_type_single_shop(self):
        self.assertTrue(self.proof_price_tag.is_type_single_shop)

    def test_update_price_count(self):
        self.proof_price_tag.refresh_from_db()
        self.assertEqual(self.proof_price_tag.price_count, 2)  # price post_save
        # bulk delete prices to skip signals
        self.proof_price_tag.prices.all().delete()
        self.assertEqual(self.proof_price_tag.price_count, 2)  # should be 0
        # update_price_count() should fix price_count
        self.proof_price_tag.update_price_count()
        self.assertEqual(self.proof_price_tag.price_count, 0)  # all deleted

    def test_update_location(self):
        # existing
        self.proof_price_tag.refresh_from_db()
        self.location_osm_1.refresh_from_db()
        self.assertEqual(self.proof_price_tag.price_count, 2)
        self.assertEqual(self.proof_price_tag.location.id, self.location_osm_1.id)
        self.assertEqual(self.location_osm_1.price_count, 2 + 1)
        # update location
        self.proof_price_tag.update_location(
            location_osm_id=self.location_osm_2.osm_id,
            location_osm_type=self.location_osm_2.osm_type,
        )
        # check changes
        self.proof_price_tag.refresh_from_db()
        self.location_osm_1.refresh_from_db()
        self.location_osm_2.refresh_from_db()
        self.assertEqual(self.proof_price_tag.location, self.location_osm_2)
        self.assertEqual(self.proof_price_tag.price_count, 2)  # same
        self.assertEqual(self.proof_price_tag.location.price_count, 2)
        self.assertEqual(self.location_osm_1.price_count, 3 - 2)
        self.assertEqual(self.location_osm_2.price_count, 2)
        # update again, same location
        self.proof_price_tag.update_location(
            location_osm_id=self.location_osm_2.osm_id,
            location_osm_type=self.location_osm_2.osm_type,
        )
        self.proof_price_tag.refresh_from_db()
        self.location_osm_1.refresh_from_db()
        self.location_osm_2.refresh_from_db()
        self.assertEqual(self.proof_price_tag.location, self.location_osm_2)
        self.assertEqual(self.proof_price_tag.price_count, 2)
        self.assertEqual(self.proof_price_tag.location.price_count, 2)
        self.assertEqual(self.location_osm_1.price_count, 1)
        self.assertEqual(self.location_osm_2.price_count, 2)

    def test_set_missing_fields_from_prices(self):
        self.proof_receipt.refresh_from_db()
        self.assertTrue(self.proof_receipt.location is None)
        self.assertTrue(self.proof_receipt.date is None)
        self.assertTrue(self.proof_receipt.currency is None)
        self.assertEqual(self.proof_receipt.price_count, 1)
        self.proof_receipt.set_missing_fields_from_prices()
        self.assertEqual(self.proof_receipt.location, self.location_osm_1)
        self.assertEqual(
            self.proof_receipt.date, self.proof_receipt.prices.first().date
        )
        self.assertEqual(
            self.proof_receipt.currency, self.proof_receipt.prices.first().currency
        )


class ProofModelUpdateTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location_osm_1 = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_osm_2 = LocationFactory(**LOCATION_OSM_NODE_6509705997)
        cls.proof_price_tag = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location_osm_1.osm_id,
            location_osm_type=cls.location_osm_1.osm_type,
            currency="EUR",
            date="2024-06-30",
        )
        PriceFactory(
            proof_id=cls.proof_price_tag.id,
            location_osm_id=cls.proof_price_tag.location.osm_id,
            location_osm_type=cls.proof_price_tag.location.osm_type,
            price=1.0,
            currency="EUR",
            date="2024-06-30",
        )

    def test_proof_update(self):
        # currency
        self.assertEqual(self.proof_price_tag.prices.count(), 1)
        self.proof_price_tag.currency = "USD"
        self.proof_price_tag.save()
        self.assertEqual(self.proof_price_tag.prices.first().currency, "USD")
        # date
        self.proof_price_tag.date = "2024-07-01"
        self.proof_price_tag.save()
        self.assertEqual(str(self.proof_price_tag.prices.first().date), "2024-07-01")
        # location
        self.proof_price_tag.location_osm_id = self.location_osm_2.osm_id
        self.proof_price_tag.location_osm_type = self.location_osm_2.osm_type
        self.proof_price_tag.save()
        self.proof_price_tag.refresh_from_db()
        self.assertEqual(self.proof_price_tag.location, self.location_osm_2)
        self.assertEqual(
            self.proof_price_tag.prices.first().location, self.location_osm_2
        )


class RunOCRTaskTest(TestCase):
    def test_fetch_and_save_ocr_data_success(self):
        response_data = {"responses": [{"textAnnotations": [{"description": "test"}]}]}
        with self.settings(GOOGLE_CLOUD_VISION_API_KEY="test_api_key"):
            # mock call to run_ocr_on_image
            with unittest.mock.patch(
                "open_prices.proofs.utils.run_ocr_on_image",
                return_value=response_data,
            ) as mock_run_ocr_on_image:
                with tempfile.TemporaryDirectory() as tmpdirname:
                    image_path = Path(f"{tmpdirname}/test.jpg")
                    with image_path.open("w") as f:
                        f.write("test")
                    output = fetch_and_save_ocr_data(image_path)
                    self.assertTrue(output)
                    mock_run_ocr_on_image.assert_called_once_with(
                        image_path, "test_api_key"
                    )
                    ocr_path = image_path.with_suffix(".json.gz")
                    self.assertTrue(ocr_path.is_file())

                    with gzip.open(ocr_path, "rt") as f:
                        actual_data = json.loads(f.read())
                        self.assertEqual(
                            set(actual_data.keys()), {"responses", "created_at"}
                        )
                        self.assertIsInstance(actual_data["created_at"], int)
                        self.assertEqual(
                            actual_data["responses"], response_data["responses"]
                        )

    def test_fetch_and_save_ocr_data_invalid_extension(self):
        with self.settings(GOOGLE_CLOUD_VISION_API_KEY="test_api_key"):
            with tempfile.TemporaryDirectory() as tmpdirname:
                image_path = Path(f"{tmpdirname}/test.bin")
                with image_path.open("w") as f:
                    f.write("test")
                output = fetch_and_save_ocr_data(image_path)
                self.assertFalse(output)


class ImageClassifierTest(TestCase):
    def test_run_and_save_proof_prediction_proof_does_not_exist(self):
        # check that we emit an error log
        with self.assertLogs(
            "open_prices.proofs.ml.image_classifier", level="ERROR"
        ) as cm:
            self.assertIsNone(run_and_save_proof_prediction(1))
            self.assertEqual(
                cm.output,
                [
                    "ERROR:open_prices.proofs.ml.image_classifier:Proof with id 1 not found"
                ],
            )

    def test_run_and_save_proof_prediction_proof_file_not_found(self):
        proof = ProofFactory()
        # check that we emit an error log
        with self.assertLogs(
            "open_prices.proofs.ml.image_classifier", level="ERROR"
        ) as cm:
            self.assertIsNone(run_and_save_proof_prediction(proof.id))
            self.assertEqual(
                cm.output,
                [
                    f"ERROR:open_prices.proofs.ml.image_classifier:Proof file not found: {proof.file_path_full}"
                ],
            )

    def test_run_and_save_proof_prediction_proof(self):
        # Create a white blank image with Pillow
        image = Image.new("RGB", (100, 100), "white")
        predict_proof_type_response = [
            ("SHELF", 0.9786477088928223),
            ("PRICE_TAG", 0.021345501765608788),
        ]

        # We save the image to a temporary file
        with tempfile.TemporaryDirectory() as tmpdirname:
            NEW_IMAGE_DIR = Path(tmpdirname)
            file_path = NEW_IMAGE_DIR / "1.jpg"
            image.save(file_path)

            # change temporarily settings.IMAGE_DIR
            with self.settings(IMAGE_DIR=NEW_IMAGE_DIR):
                proof = ProofFactory(file_path=file_path)

                # Patch predict_proof_type to return a fixed response
                with unittest.mock.patch(
                    "open_prices.proofs.ml.image_classifier.predict_proof_type",
                    return_value=predict_proof_type_response,
                ) as mock_predict_proof_type:
                    run_and_save_proof_prediction(proof.id)
                    mock_predict_proof_type.assert_called_once()
                proof_prediction = proof.predictions.first()
                self.assertIsNotNone(proof_prediction)
                self.assertEqual(
                    proof_prediction.type,
                    proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
                )

                self.assertEqual(
                    proof_prediction.model_name, "price_proof_classification"
                )
                self.assertEqual(
                    proof_prediction.model_version, "price_proof_classification-1.0"
                )
                self.assertEqual(proof_prediction.value, "SHELF")
                self.assertEqual(proof_prediction.max_confidence, 0.9786477088928223)
                self.assertEqual(
                    proof_prediction.data,
                    {
                        "prediction": [
                            {"label": "SHELF", "score": 0.9786477088928223},
                            {"label": "PRICE_TAG", "score": 0.021345501765608788},
                        ]
                    },
                )
                proof_prediction.delete()
                proof.delete()
