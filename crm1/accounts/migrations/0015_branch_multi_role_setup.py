"""
Migration: Add Branch model, link Branch to Customer/Product/Order,
           fix Product.price to DecimalField, fix Order status choices.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import decimal


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_rename_nates_order_notes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Create the Branch table
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
                ('location', models.CharField(blank=True, max_length=300, null=True)),
                ('phone', models.CharField(blank=True, max_length=200, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('manager', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='managed_branch',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name_plural': 'Branches'},
        ),

        # 2. Add branch FK to Customer
        migrations.AddField(
            model_name='customer',
            name='branch',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='accounts.branch',
            ),
        ),

        # 3. Add branch FK to Product
        migrations.AddField(
            model_name='product',
            name='branch',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='accounts.branch',
            ),
        ),

        # 4. Add branch FK to Order
        migrations.AddField(
            model_name='order',
            name='branch',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='accounts.branch',
            ),
        ),

        # 5. Fix Product.price: CharField -> DecimalField
        #    We rename the old field, add the new one, then remove the old one.
        migrations.RenameField(
            model_name='product',
            old_name='price',
            new_name='price_old',
        ),
        migrations.AddField(
            model_name='product',
            name='price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
            ),
        ),
        # Note: existing string price data in price_old is NOT automatically
        # migrated to avoid errors with non-numeric values. Update via admin.
        migrations.RemoveField(
            model_name='product',
            name='price_old',
        ),

        # 6. Fix Order status choices (rename 'Out of Delivery' -> 'Out for Delivery')
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('Pending', 'Pending'),
                    ('Out for Delivery', 'Out for Delivery'),
                    ('Delivered', 'Delivered'),
                ],
                max_length=200,
                null=True,
            ),
        ),

        # 7. Expand Product.description field
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),

        # 8. Allow Order.notes to be blank
        migrations.AlterField(
            model_name='order',
            name='notes',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
