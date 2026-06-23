"""
Migration 0020: Add granular product permission flags to Role.
  - can_view_products
  - can_add_products
  - can_edit_products
  - can_delete_products

The existing can_manage_products field is retained for backwards compatibility.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_country_add_to_state_customer_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='can_view_products',
            field=models.BooleanField(default=False, help_text='View product list'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_add_products',
            field=models.BooleanField(default=False, help_text='Add new products'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_edit_products',
            field=models.BooleanField(default=False, help_text='Edit existing products'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_delete_products',
            field=models.BooleanField(default=False, help_text='Delete products'),
        ),
    ]
