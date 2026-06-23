from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_customer_profile_pic"),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="nates",
            new_name="notes",
        ),
    ]
