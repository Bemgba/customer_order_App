# Generated by Django 5.0.6 on 2024-06-23 06:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_order_customer_order_product"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Out of Delivery", "Out of Delivery"),
                    ("Delivered", "Delivered"),
                ],
                max_length=200,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="tags",
            field=models.ManyToManyField(to="accounts.tag"),
        ),
    ]
