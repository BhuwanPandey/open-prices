# Generated by Django 5.1.7 on 2025-03-23 13:48

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "stats",
            "0015_rename_proof_type_group_community_count_totalstats_proof_kind_community_count_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="totalstats",
            old_name="price_type_group_community_count",
            new_name="price_kind_community_count",
        ),
        migrations.RenameField(
            model_name="totalstats",
            old_name="price_type_group_consumption_count",
            new_name="price_kind_consumption_count",
        ),
    ]
