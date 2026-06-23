"""
Migration 0019: Add Country model.
  - Country (varchar PK — insert manually, e.g. 'NG', 'GH')
  - State.country FK  (State now belongs to a Country)
  - Customer.country FK
  - Order.delivery_country FK
  - State.name unique constraint removed (names can repeat across countries)
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_state_lga_order_redesign'),
    ]

    operations = [

        # ──────────────────────────────────────────────────────────────────
        # 1. Create Country table
        # ──────────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Country',
            fields=[
                # varchar PK — e.g. 'NG', 'GH', 'US'
                ('id',   models.CharField(primary_key=True, max_length=5,
                                          serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Countries',
            },
        ),

        # ──────────────────────────────────────────────────────────────────
        # 2. Add country FK to State (nullable so existing rows don't break)
        # ──────────────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='state',
            name='country',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='states',
                to='accounts.country',
            ),
        ),

        # ──────────────────────────────────────────────────────────────────
        # 3. Remove old unique constraint on State.name
        #    (state names can repeat across countries, e.g. two countries
        #     both having a "Delta" state)
        # ──────────────────────────────────────────────────────────────────
        migrations.AlterField(
            model_name='state',
            name='name',
            field=models.CharField(max_length=100),
        ),

        # ──────────────────────────────────────────────────────────────────
        # 4. Add country FK to Customer
        # ──────────────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='customer',
            name='country',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='customers',
                to='accounts.country',
            ),
        ),

        # ──────────────────────────────────────────────────────────────────
        # 5. Add delivery_country FK to Order
        # ──────────────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='order',
            name='delivery_country',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='accounts.country',
            ),
        ),
    ]
