from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0023_alter_order_options_role_can_manage_inventory_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE UNIQUE INDEX IF NOT EXISTS auth_user_email_unique ON auth_user (email);"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS auth_user_email_unique;"
            ),
        ),
    ]
