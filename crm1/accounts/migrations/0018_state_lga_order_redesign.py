"""
Migration 0018: Full order redesign.
  - Add State  (varchar PK — inserted manually)
  - Add LGA    (varchar PK — inserted manually, FK to State)
  - Add delivery fields + state/lga FK to Customer
  - Redesign Order: remove old single-product FK, add delivery fields,
    auto-reference, new statuses
  - Add OrderItem (multi-product line items with price snapshot)
  - Add Payment table
  - Add Product.image, Product.is_available
"""
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_customer_email_phone_validation'),
    ]

    operations = [

        # ──────────────────────────────────────────────────────────────────
        # 1. State  — varchar PK, you insert records directly via psql/pgAdmin
        # ──────────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='State',
            fields=[
                # varchar PK — e.g. 'AB', 'BE', 'KN'
                ('id',   models.CharField(primary_key=True, max_length=10,
                                          serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={'ordering': ['name']},
        ),

        # ──────────────────────────────────────────────────────────────────
        # 2. LGA  — varchar PK, FK → State
        # ──────────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='LGA',
            fields=[
                # varchar PK — e.g. 'AB-01', 'BE-03'
                ('id',    models.CharField(primary_key=True, max_length=20,
                                           serialize=False)),
                ('name',  models.CharField(max_length=100)),
                ('state', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lgas',
                    to='accounts.state',
                )),
            ],
            options={
                'verbose_name': 'LGA',
                'verbose_name_plural': 'LGAs',
                'ordering': ['name'],
            },
        ),

        # ──────────────────────────────────────────────────────────────────
        # 3. Customer — add state, lga, address
        # ──────────────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='customer',
            name='state',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='customers',
                to='accounts.state',
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='lga',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='customers',
                to='accounts.lga',
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='address',
            field=models.CharField(
                blank=True, max_length=500, null=True,
                help_text='Street / house number / landmark',
            ),
        ),

        # ──────────────────────────────────────────────────────────────────
        # 4. Product — image + is_available
        # ──────────────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(
                blank=True, null=True, upload_to='menu/',
                help_text='Optional product photo for the menu page.',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='is_available',
            field=models.BooleanField(
                default=True,
                help_text='Uncheck to hide from the public menu.',
            ),
        ),

        # ──────────────────────────────────────────────────────────────────
        # 5. Order — remove old single-product FK
        # ──────────────────────────────────────────────────────────────────
        migrations.RemoveField(model_name='order', name='product'),

        # ──────────────────────────────────────────────────────────────────
        # 6. Order — add all new fields
        # ──────────────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='order',
            name='reference',
            field=models.CharField(
                default='TMP', editable=False, max_length=20, unique=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_name',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_phone',
            field=models.CharField(
                default='', max_length=20,
                validators=[django.core.validators.RegexValidator(
                    regex=r'^\+?1?\d{7,15}$',
                    message='Enter a valid phone number.',
                )],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_state',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='accounts.state',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_lga',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='accounts.lga',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_address',
            field=models.CharField(default='', max_length=500),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('Awaiting Payment', 'Awaiting Payment'),
                    ('Paid',             'Paid'),
                    ('Preparing',        'Preparing'),
                    ('Out for Delivery', 'Out for Delivery'),
                    ('Delivered',        'Delivered'),
                    ('Cancelled',        'Cancelled'),
                ],
                default='Awaiting Payment',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='accounts.customer',
            ),
        ),

        # ──────────────────────────────────────────────────────────────────
        # 7. OrderItem
        # ──────────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity',   models.PositiveIntegerField(default=1)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='accounts.order',
                )),
                ('product', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='accounts.product',
                )),
            ],
        ),

        # ──────────────────────────────────────────────────────────────────
        # 8. Payment
        # ──────────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('method', models.CharField(
                    choices=[
                        ('Transfer', 'Bank Transfer'),
                        ('Card',     'Card'),
                        ('Cash',     'Cash on Delivery'),
                        ('USSD',     'USSD'),
                    ],
                    default='Transfer', max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('Pending',  'Pending'),
                        ('Paid',     'Paid'),
                        ('Failed',   'Failed'),
                        ('Refunded', 'Refunded'),
                    ],
                    default='Pending', max_length=20,
                )),
                ('gateway_ref', models.CharField(
                    blank=True, max_length=200, null=True,
                    help_text='Reference from payment gateway',
                )),
                ('paid_at',      models.DateTimeField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment',
                    to='accounts.order',
                )),
            ],
        ),
    ]
