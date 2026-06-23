"""
Migration: Add phone/email validators to Customer, price validator to Product.
Validators are Python-level only — no DB schema change needed.
"""
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_role_userprofile'),
    ]

    operations = [
        # Customer.phone: CharField with validator + tighter max_length
        migrations.AlterField(
            model_name='customer',
            name='phone',
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                help_text='7–15 digits, optional leading +',
                validators=[
                    django.core.validators.RegexValidator(
                        regex=r'^\+?1?\d{7,15}$',
                        message='Enter a valid phone number (7–15 digits, optional leading +).',
                    )
                ],
            ),
        ),
        # Customer.email: proper EmailField
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        # Product.price: add MinValueValidator(0)
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                help_text='Price in Naira (N). Must be 0 or greater.',
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
    ]
