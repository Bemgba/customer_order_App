"""
Migration 0022: Remove the temporary category_old_tmp column from Product.

Before running this migration, copy old values if needed:
  UPDATE accounts_product SET category_legacy = category_old_tmp
  WHERE category_legacy IS NULL AND category_old_tmp IS NOT NULL;

This migration is safe to run immediately — it only drops the now-redundant
column that was left by the 0021 rename operation.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_new_features'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='category_old_tmp',
        ),
    ]
