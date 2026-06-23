"""
Migration 0021 — New feature models:
  Branch:    + address, latitude, longitude, status
  Product:   + ProductCategory FK, category_legacy field (renames old category)
  Order:     + delivery_fee, discount, coupon FK
  New:       ProductCategory, BranchProduct, CustomerAddress,
             OrderTracking, DispatcherAssignment, Delivery,
             Notification, Coupon, Ingredient, ProductIngredient,
             Review, AuditLog
"""
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_role_granular_product_permissions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── Branch improvements ────────────────────────────────────────────
        migrations.AddField(
            model_name='branch', name='address',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='branch', name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='branch', name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='branch', name='status',
            field=models.CharField(
                choices=[('active', 'Active'), ('inactive', 'Inactive')],
                default='active', max_length=20,
            ),
        ),

        # ── ProductCategory ────────────────────────────────────────────────
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.CharField(blank=True, max_length=300, null=True)),
            ],
            options={'verbose_name_plural': 'Product Categories', 'ordering': ['name']},
        ),

        # ── Product — add category FK + rename old charfield ──────────────
        migrations.AddField(
            model_name='product', name='category_legacy',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Mains','Mains'),('Sides','Sides'),('Drinks','Drinks'),
                    ('Snacks','Snacks'),('Chops','Chops'),
                    ('Appetizer','Appetizer'),('Dessert','Dessert'),
                ],
                help_text='Legacy — use category FK for new products.',
                max_length=200, null=True,
            ),
        ),
        # Copy old category values into category_legacy, then drop old column
        migrations.RenameField(
            model_name='product', old_name='category', new_name='category_old_tmp',
        ),
        migrations.AddField(
            model_name='product', name='category',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products', to='accounts.productcategory',
            ),
        ),
        # We intentionally keep category_old_tmp so no data is lost.
        # Run the data migration manually: UPDATE accounts_product SET category_legacy = category_old_tmp
        # then drop: migrations.RemoveField(model_name='product', name='category_old_tmp')

        # ── BranchProduct ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='BranchProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(
                    decimal_places=2, max_digits=10,
                    validators=[django.core.validators.MinValueValidator(0)],
                )),
                ('quantity_available', models.PositiveIntegerField(default=0)),
                ('is_available', models.BooleanField(default=True)),
                ('branch', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='branch_products', to='accounts.branch',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='branch_products', to='accounts.product',
                )),
            ],
            options={'verbose_name': 'Branch Product', 'unique_together': {('branch', 'product')}},
        ),

        # ── CustomerAddress ────────────────────────────────────────────────
        migrations.CreateModel(
            name='CustomerAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('label', models.CharField(blank=True, max_length=100)),
                ('address', models.CharField(max_length=500)),
                ('landmark', models.CharField(blank=True, max_length=300, null=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6,
                                                 max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6,
                                                  max_digits=9, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='addresses', to='accounts.customer',
                )),
                ('lga', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='accounts.lga',
                )),
                ('state', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='accounts.state',
                )),
            ],
            options={'verbose_name': 'Customer Address'},
        ),

        # ── Order improvements ─────────────────────────────────────────────
        migrations.AddField(
            model_name='order', name='delivery_fee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name='order', name='discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),

        # ── Coupon (must exist before Order FK) ───────────────────────────
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('discount_type', models.CharField(
                    choices=[('percent','Percentage'),('fixed','Fixed Amount')],
                    default='percent', max_length=10,
                )),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('usage_limit', models.PositiveIntegerField(default=1)),
                ('times_used', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(
                    choices=[('active','Active'),('inactive','Inactive'),('expired','Expired')],
                    default='active', max_length=10,
                )),
                ('branch', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='accounts.branch',
                )),
            ],
        ),
        migrations.AddField(
            model_name='order', name='coupon',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders', to='accounts.coupon',
            ),
        ),

        # ── OrderTracking ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='OrderTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=50)),
                ('remark', models.CharField(blank=True, max_length=500, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tracking', to='accounts.order',
                )),
                ('updated_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['created_at'], 'verbose_name': 'Order Tracking'},
        ),

        # ── DispatcherAssignment ───────────────────────────────────────────
        migrations.CreateModel(
            name='DispatcherAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(
                    choices=[('Assigned','Assigned'),('Accepted','Accepted'),
                             ('Rejected','Rejected'),('Completed','Completed')],
                    default='Assigned', max_length=20,
                )),
                ('assigned_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='dispatched_orders', to=settings.AUTH_USER_MODEL,
                )),
                ('dispatcher', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments', to=settings.AUTH_USER_MODEL,
                )),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dispatcher_assignments', to='accounts.order',
                )),
            ],
            options={'verbose_name': 'Dispatcher Assignment'},
        ),

        # ── Delivery ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('pickup_time', models.DateTimeField(blank=True, null=True)),
                ('delivery_start_time', models.DateTimeField(blank=True, null=True)),
                ('delivery_end_time', models.DateTimeField(blank=True, null=True)),
                ('delivery_status', models.CharField(
                    choices=[('Pending','Pending'),('Picked Up','Picked Up'),
                             ('In Transit','In Transit'),('Delivered','Delivered'),
                             ('Failed','Failed')],
                    default='Pending', max_length=20,
                )),
                ('proof_of_delivery', models.ImageField(
                    blank=True, null=True, upload_to='deliveries/',
                )),
                ('remarks', models.CharField(blank=True, max_length=500, null=True)),
                ('dispatcher', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='deliveries', to=settings.AUTH_USER_MODEL,
                )),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='delivery', to='accounts.order',
                )),
            ],
            options={'verbose_name_plural': 'Deliveries'},
        ),

        # ── Notification ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-created_at']},
        ),

        # ── Ingredient & ProductIngredient ─────────────────────────────────
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('unit', models.CharField(max_length=50)),
                ('quantity_available', models.DecimalField(decimal_places=3,
                                                           default=0, max_digits=10)),
                ('reorder_level', models.DecimalField(decimal_places=3,
                                                      default=0, max_digits=10)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ingredients', to='accounts.branch',
                )),
            ],
        ),
        migrations.CreateModel(
            name='ProductIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('quantity_required', models.DecimalField(decimal_places=3, max_digits=10)),
                ('ingredient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='accounts.ingredient',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ingredients', to='accounts.product',
                )),
            ],
            options={
                'verbose_name': 'Product Ingredient',
                'unique_together': {('product', 'ingredient')},
            },
        ),

        # ── Review ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(
                    validators=[django.core.validators.MinValueValidator(1)],
                )),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='accounts.customer',
                )),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='review', to='accounts.order',
                )),
            ],
        ),

        # ── AuditLog ───────────────────────────────────────────────────────
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50)),
                ('table_name', models.CharField(max_length=100)),
                ('record_id', models.CharField(max_length=50)),
                ('old_values', models.JSONField(blank=True, null=True)),
                ('new_values', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-created_at'], 'verbose_name': 'Audit Log'},
        ),
    ]
