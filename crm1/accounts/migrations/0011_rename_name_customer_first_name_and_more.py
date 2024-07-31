# Generated by Django 5.0.6 on 2024-07-15 17:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_customer_user"),
    ]

    operations = [
        migrations.RenameField(
            model_name="customer",
            old_name="name",
            new_name="first_name",
        ),
        migrations.RemoveField(
            model_name="customer",
            name="date_create",
        ),
        migrations.AddField(
            model_name="customer",
            name="date_created",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="customer",
            name="last_name",
            field=models.CharField(max_length=200, null=True),
        ),
    ]
