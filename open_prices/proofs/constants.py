import enum

TYPE_PRICE_TAG = "PRICE_TAG"
TYPE_RECEIPT = "RECEIPT"
TYPE_GDPR_REQUEST = "GDPR_REQUEST"
TYPE_SHOP_IMPORT = "SHOP_IMPORT"

TYPE_LIST = [TYPE_PRICE_TAG, TYPE_RECEIPT, TYPE_GDPR_REQUEST, TYPE_SHOP_IMPORT]
TYPE_CHOICES = [(key, key) for key in TYPE_LIST]

# SINGLE_SHOP: same location, date & currency
TYPE_GROUP_SINGLE_SHOP = "SINGLE_SHOP"
TYPE_GROUP_SINGLE_SHOP_LIST = [TYPE_PRICE_TAG, TYPE_RECEIPT, TYPE_SHOP_IMPORT]
# MULTIPLE_SHOP
TYPE_GROUP_MULTIPLE_SHOP = "MULTIPLE_SHOP"
TYPE_GROUP_MULTIPLE_SHOP_LIST = [TYPE_GDPR_REQUEST]
# ALLOW_ANY_USER_PRICE_ADD
TYPE_GROUP_ALLOW_ANY_USER_PRICE_ADD = "ALLOW_ANY_USER_PRICE_ADD"
TYPE_GROUP_ALLOW_ANY_USER_PRICE_ADD_LIST = [TYPE_PRICE_TAG]
# COMMUNITY
TYPE_GROUP_COMMUNITY = "COMMUNITY"
TYPE_GROUP_COMMUNITY_LIST = [TYPE_PRICE_TAG, TYPE_SHOP_IMPORT]
# CONSUMPTION: extra fields
TYPE_GROUP_CONSUMPTION = "CONSUMPTION"
TYPE_GROUP_CONSUMPTION_LIST = [TYPE_RECEIPT, TYPE_GDPR_REQUEST]
TYPE_GROUP_LIST = [
    TYPE_GROUP_SINGLE_SHOP,
    TYPE_GROUP_MULTIPLE_SHOP,
    TYPE_GROUP_ALLOW_ANY_USER_PRICE_ADD,
    TYPE_GROUP_COMMUNITY,
    TYPE_GROUP_CONSUMPTION,
]

PROOF_PREDICTION_OBJECT_DETECTION_TYPE = "OBJECT_DETECTION"
PROOF_PREDICTION_CLASSIFICATION_TYPE = "CLASSIFICATION"
PROOF_PREDICTION_RECEIPT_EXTRACTION_TYPE = "RECEIPT_EXTRACTION"
PROOF_PREDICTION_LIST = [
    PROOF_PREDICTION_OBJECT_DETECTION_TYPE,
    PROOF_PREDICTION_CLASSIFICATION_TYPE,
    PROOF_PREDICTION_RECEIPT_EXTRACTION_TYPE,
]

PROOF_PREDICTION_TYPE_CHOICES = [(key, key) for key in PROOF_PREDICTION_LIST]

PRICE_TAG_EXTRACTION_TYPE = "PRICE_TAG_EXTRACTION"

PRICE_TAG_PREDICTION_TYPE_CHOICES = [
    (PRICE_TAG_EXTRACTION_TYPE, PRICE_TAG_EXTRACTION_TYPE)
]


class PriceTagStatus(enum.IntEnum):
    deleted = 0
    linked_to_price = 1
    not_readable = 2
    truncated = 3
    not_price_tag = 4


PRICE_TAG_STATUS_CHOICES = [(item.value, item.name) for item in PriceTagStatus]
