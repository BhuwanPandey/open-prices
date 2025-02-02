# Generated by Django 5.1.4 on 2025-02-02 16:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_user_proof_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="location_type_osm_country_count",
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="price_currency_count",
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]
