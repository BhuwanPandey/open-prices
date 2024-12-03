# Generated by Django 5.1 on 2024-12-03 14:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("locations", "0006_location_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="osm_brand",
            field=models.CharField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="location",
            name="osm_version",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
