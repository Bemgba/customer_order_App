# Generated by Django 5.0.6 on 2024-06-23 06:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_alter_product_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="description",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]