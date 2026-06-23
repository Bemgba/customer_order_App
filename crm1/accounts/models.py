from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator
import uuid

_phone_validator = RegexValidator(
    regex=r'^\+?1?\d{7,15}$',
    message='Enter a valid phone number (7–15 digits, optional leading +).'
)


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------

class Role(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='created_roles'
    )
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    can_manage_orders = models.BooleanField(default=False, help_text='Create and update orders')
    can_delete_orders = models.BooleanField(default=False, help_text='Delete orders')
    # Product permissions (granular)
    can_view_products = models.BooleanField(default=False, help_text='View product list')
    can_add_products = models.BooleanField(default=False, help_text='Add new products')
    can_edit_products = models.BooleanField(default=False, help_text='Edit existing products')
    can_delete_products = models.BooleanField(default=False, help_text='Delete products')
    # Legacy alias — kept for backwards compatibility with existing role data
    can_manage_products = models.BooleanField(default=False, help_text='Add and edit products (legacy — use granular flags above)')
    can_manage_customers = models.BooleanField(default=False, help_text='View and manage customers')
    can_view_reports = models.BooleanField(default=False, help_text='Access PDF reports and analytics')
    can_manage_payments = models.BooleanField(default=False, help_text='Confirm and manage order payments')
    can_manage_inventory = models.BooleanField(default=False, help_text='Manage ingredients and stock levels')
    can_manage_users = models.BooleanField(default=False, help_text='Create users and assign roles')
    can_manage_branches = models.BooleanField(default=False, help_text='Create and manage branches')
    can_confirm_delivery = models.BooleanField(default=False, help_text='Confirm delivery of orders (dispatcher role)')
    can_assign_dispatcher = models.BooleanField(default=False, help_text='Assign a dispatcher to an order')

    def __str__(self):
        return self.name

    def permission_summary(self):
        flags = {
            'Manage Orders': self.can_manage_orders,
            'Delete Orders': self.can_delete_orders,
            'View Products': self.can_view_products,
            'Add Products': self.can_add_products,
            'Edit Products': self.can_edit_products,
            'Delete Products': self.can_delete_products,
            'Manage Customers': self.can_manage_customers,
            'View Reports': self.can_view_reports,
            'Manage Inventory': self.can_manage_inventory,
            'Manage Payments': self.can_manage_payments,
            'Manage Users': self.can_manage_users,
            'Manage Branches': self.can_manage_branches,
            'Confirm Delivery': self.can_confirm_delivery,
            'Assign Dispatcher': self.can_assign_dispatcher,
        }
        active = [label for label, value in flags.items() if value]
        return ', '.join(active) if active else 'No permissions'


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles = models.ManyToManyField(Role, blank=True, related_name='users')
    branch = models.ForeignKey(
        'Branch', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='staff'
    )
    is_ceo = models.BooleanField(
        default=False,
        help_text='CEO has full access to all branches and can manage roles/users.'
    )
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f'{self.user.username} – Profile'

    def has_permission(self, perm):
        """
        Check if this user has a specific permission flag through any of
        their roles. CEO bypasses all checks.

        Iterates self.roles.all() in Python so that a prefetched roles
        queryset (e.g. from _get_profile's select_related path) is reused
        without extra DB hits. Falls back to a single query when not prefetched.
        """
        if self.is_ceo or self.user.is_superuser:
            return True
        
        # Check if any of the user's roles grant this permission
        for role in self.roles.all():
            if getattr(role, perm, False):
                return True
        
        return False

    def role_names(self):
        return ', '.join(self.roles.values_list('name', flat=True)) or 'No roles'


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------

class Branch(models.Model):
    STATUS = (('active', 'Active'), ('inactive', 'Inactive'))
    name      = models.CharField(max_length=200, null=True)
    address   = models.CharField(max_length=300, null=True, blank=True)
    location  = models.CharField(max_length=300, null=True, blank=True)   # kept for compat
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone     = models.CharField(max_length=200, null=True, blank=True)
    status    = models.CharField(max_length=20, choices=STATUS, default='active')
    manager   = models.OneToOneField(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='managed_branch'
    )
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Branches'


# ---------------------------------------------------------------------------
# Country / State / LGA  (three-level location hierarchy)
# ---------------------------------------------------------------------------

class Country(models.Model):
    """
    Country. PK is a varchar you insert manually.
    Recommended format: ISO 3166-1 alpha-2 code, e.g. 'NG', 'GH', 'US'.
    """
    id   = models.CharField(primary_key=True, max_length=5)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Countries'


class State(models.Model):
    """
    State / Province. PK is a short varchar you insert manually.
    Recommended format: '<country_id>-<code>', e.g. 'NG-AB', 'NG-BE'.
    """
    id      = models.CharField(primary_key=True, max_length=10)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    name    = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class LGA(models.Model):
    """
    Local Government Area. PK is a varchar you insert manually.
    Recommended format: '<state_id>-<sequence>', e.g. 'NG-BE-01'.
    """
    id    = models.CharField(primary_key=True, max_length=20)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='lgas')
    name  = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'LGA'
        verbose_name_plural = 'LGAs'


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class Customer(models.Model):
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(
        max_length=20, null=True, blank=True,
        validators=[_phone_validator],
        help_text='7–15 digits, optional leading +'
    )
    email = models.EmailField(max_length=254, null=True, blank=True)
    # Delivery address fields
    country = models.ForeignKey(
        'Country', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='customers'
    )
    state = models.ForeignKey(
        State, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='customers'
    )
    lga = models.ForeignKey(
        LGA, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='customers'
    )
    address = models.CharField(max_length=500, null=True, blank=True,
                               help_text='Street / house number / landmark')
    profile_pic = models.ImageField(default='user_avatar.png', null=True, blank=True)
    date_create = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name or f'Customer #{self.pk}'


# ---------------------------------------------------------------------------
# Product Category
# ---------------------------------------------------------------------------

class ProductCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['name']


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------

class Tag(models.Model):
    name = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Product (master definition — branch-agnostic)
# ---------------------------------------------------------------------------

class Product(models.Model):
    # Legacy CATEGORY kept so existing data/filters still work.
    # New code should use ProductCategory FK.
    CATEGORY = (
        ('Mains', 'Mains'),
        ('Sides', 'Sides'),
        ('Drinks', 'Drinks'),
        ('Snacks', 'Snacks'),
        ('Chops', 'Chops'),
        ('Appetizer', 'Appetizer'),
        ('Dessert', 'Dessert'),
    )
    # Branch FK kept for simple branch-scoping; BranchProduct allows overrides
    branch   = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(
        ProductCategory, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='products'
    )
    # legacy category charfield — still used by existing filters
    category_legacy = models.CharField(
        max_length=200, null=True, blank=True, choices=CATEGORY,
        help_text='Legacy — use category FK for new products.'
    )
    name        = models.CharField(max_length=200, null=True)
    price       = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text='Base price (N). BranchProduct can override per branch.'
    )
    description  = models.CharField(max_length=500, null=True, blank=True)
    image        = models.ImageField(upload_to='menu/', null=True, blank=True)
    tags         = models.ManyToManyField(Tag, blank=True)
    is_available = models.BooleanField(default=True)
    date_create  = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    def get_category_display_name(self):
        if self.category:
            return self.category.name
        return self.category_legacy or '—'


# ---------------------------------------------------------------------------
# Branch Product — price/availability override per branch
# ---------------------------------------------------------------------------

class BranchProduct(models.Model):
    """
    Allows a product to have a different price or availability per branch.
    If no BranchProduct row exists for a branch+product, fall back to Product.price.
    """
    branch           = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='branch_products')
    product          = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='branch_products')
    price            = models.DecimalField(max_digits=10, decimal_places=2,
                                           validators=[MinValueValidator(0)])
    quantity_available = models.PositiveIntegerField(default=0,
                                                     help_text='Current stock count')
    is_available     = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.product.name} @ {self.branch.name}'

    class Meta:
        unique_together = ('branch', 'product')
        verbose_name = 'Branch Product'


# ---------------------------------------------------------------------------
# Customer Address (multiple addresses per customer)
# ---------------------------------------------------------------------------

class CustomerAddress(models.Model):
    customer  = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    label     = models.CharField(max_length=100, blank=True,
                                 help_text='e.g. Home, Office')
    address   = models.CharField(max_length=500)
    state     = models.ForeignKey(State, null=True, blank=True,
                                  on_delete=models.SET_NULL)
    lga       = models.ForeignKey(LGA, null=True, blank=True,
                                  on_delete=models.SET_NULL)
    landmark  = models.CharField(max_length=300, blank=True, null=True)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.customer} – {self.label or self.address[:30]}'

    class Meta:
        verbose_name = 'Customer Address'


# ---------------------------------------------------------------------------
# Order Tracking (history log — one row per status change)
# ---------------------------------------------------------------------------

class OrderTracking(models.Model):
    order      = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='tracking')
    status     = models.CharField(max_length=50)
    remark     = models.CharField(max_length=500, blank=True, null=True)
    updated_by = models.ForeignKey(User, null=True, blank=True,
                                   on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.order.reference} → {self.status}'

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Order Tracking'


# ---------------------------------------------------------------------------
# Dispatcher & Delivery
# ---------------------------------------------------------------------------

class DispatcherAssignment(models.Model):
    STATUS = (
        ('Assigned',   'Assigned'),
        ('Accepted',   'Accepted'),
        ('Rejected',   'Rejected'),
        ('Completed',  'Completed'),
    )
    order       = models.ForeignKey('Order', on_delete=models.CASCADE,
                                    related_name='dispatcher_assignments')
    dispatcher  = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='assignments')
    assigned_by = models.ForeignKey(User, null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='dispatched_orders')
    assigned_at = models.DateTimeField(auto_now_add=True)
    status      = models.CharField(max_length=20, choices=STATUS, default='Assigned')

    def __str__(self):
        return f'{self.order.reference} → {self.dispatcher.username}'

    class Meta:
        verbose_name = 'Dispatcher Assignment'


class Delivery(models.Model):
    STATUS = (
        ('Pending',   'Pending'),
        ('Picked Up', 'Picked Up'),
        ('In Transit','In Transit'),
        ('Delivered', 'Delivered'),
        ('Failed',    'Failed'),
    )
    order               = models.OneToOneField('Order', on_delete=models.CASCADE,
                                               related_name='delivery')
    dispatcher          = models.ForeignKey(User, null=True, blank=True,
                                            on_delete=models.SET_NULL,
                                            related_name='deliveries')
    pickup_time         = models.DateTimeField(null=True, blank=True)
    delivery_start_time = models.DateTimeField(null=True, blank=True)
    delivery_end_time   = models.DateTimeField(null=True, blank=True)
    delivery_status     = models.CharField(max_length=20, choices=STATUS, default='Pending')
    proof_of_delivery   = models.ImageField(upload_to='deliveries/', null=True, blank=True,
                                            help_text='Photo confirmation of delivery')
    remarks             = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f'Delivery – {self.order.reference}'

    class Meta:
        verbose_name_plural = 'Deliveries'


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notification(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} – {self.title}'

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------------------------------
# Promotions / Coupons
# ---------------------------------------------------------------------------

class Coupon(models.Model):
    TYPE = (
        ('percent', 'Percentage'),
        ('fixed',   'Fixed Amount'),
    )
    STATUS = (
        ('active',   'Active'),
        ('inactive', 'Inactive'),
        ('expired',  'Expired'),
    )
    code           = models.CharField(max_length=50, unique=True)
    discount_type  = models.CharField(max_length=10, choices=TYPE, default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date     = models.DateField()
    end_date       = models.DateField()
    usage_limit    = models.PositiveIntegerField(default=1,
                                                 help_text='Max total uses, 0 = unlimited')
    times_used     = models.PositiveIntegerField(default=0)
    status         = models.CharField(max_length=10, choices=STATUS, default='active')
    branch         = models.ForeignKey(Branch, null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       help_text='Null = valid at all branches')

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        from django.utils import timezone
        today = timezone.now().date()
        if self.status != 'active':
            return False
        if not (self.start_date <= today <= self.end_date):
            return False
        if self.usage_limit > 0 and self.times_used >= self.usage_limit:
            return False
        return True


# ---------------------------------------------------------------------------
# Inventory — Ingredients & Product Recipes
# ---------------------------------------------------------------------------

class Ingredient(models.Model):
    branch             = models.ForeignKey(Branch, on_delete=models.CASCADE,
                                           related_name='ingredients')
    name               = models.CharField(max_length=200)
    unit               = models.CharField(max_length=50,
                                          help_text='e.g. kg, litres, pieces')
    quantity_available = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    reorder_level      = models.DecimalField(max_digits=10, decimal_places=3, default=0,
                                             help_text='Alert when stock falls below this')
    updated_at         = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.branch.name})'

    @property
    def is_low(self):
        return self.quantity_available <= self.reorder_level


class ProductIngredient(models.Model):
    """Recipe: how much of each ingredient one unit of a product needs."""
    product           = models.ForeignKey(Product, on_delete=models.CASCADE,
                                          related_name='ingredients')
    ingredient        = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f'{self.product.name} needs {self.quantity_required} {self.ingredient.unit} of {self.ingredient.name}'

    class Meta:
        unique_together = ('product', 'ingredient')
        verbose_name = 'Product Ingredient'


class IngredientConsumption(models.Model):
    """
    Track ingredient usage history - records each time ingredients are consumed.
    Automatically created when orders are marked as 'Preparing'.
    """
    ingredient     = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                       related_name='consumptions')
    order          = models.ForeignKey('Order', null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name='ingredient_consumptions')
    quantity_used  = models.DecimalField(max_digits=10, decimal_places=3)
    consumed_by    = models.ForeignKey(User, null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       help_text='Staff who marked order as preparing')
    consumed_at    = models.DateTimeField(auto_now_add=True)
    notes          = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f'{self.quantity_used} {self.ingredient.unit} of {self.ingredient.name} used on {self.consumed_at.strftime("%Y-%m-%d")}'

    class Meta:
        ordering = ['-consumed_at']
        verbose_name = 'Ingredient Consumption'
        verbose_name_plural = 'Ingredient Consumptions'


# ---------------------------------------------------------------------------
# Reviews & Ratings
# ---------------------------------------------------------------------------

class Review(models.Model):
    order    = models.OneToOneField('Order', on_delete=models.CASCADE,
                                    related_name='review')
    customer = models.ForeignKey(Customer, null=True, blank=True,
                                 on_delete=models.SET_NULL)
    rating   = models.PositiveSmallIntegerField(
        help_text='1–5 stars',
        validators=[MinValueValidator(1)]
    )
    comment    = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.order.reference} – {self.rating}★'


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class AuditLog(models.Model):
    user        = models.ForeignKey(User, null=True, blank=True,
                                    on_delete=models.SET_NULL)
    action      = models.CharField(max_length=50,
                                   help_text='e.g. CREATE, UPDATE, DELETE')
    table_name  = models.CharField(max_length=100)
    record_id   = models.CharField(max_length=50)
    old_values  = models.JSONField(null=True, blank=True)
    new_values  = models.JSONField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.action} on {self.table_name}#{self.record_id} by {self.user}'

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'


# ---------------------------------------------------------------------------
# Order  (the transaction header — one per checkout)
# ---------------------------------------------------------------------------

class Order(models.Model):
    # Updated STATUS choices - removed "Paid", added "Pending" and "Confirmed"
    ORDER_STATUS_CHOICES = (
        ('Pending',            'Pending Review'),      # New order awaiting staff review
        ('Confirmed',          'Confirmed'),           # Staff accepted order
        ('Preparing',          'Preparing'),           # Kitchen cooking
        ('Out for Delivery',   'Out for Delivery'),    # Driver has the food
        ('Delivered',          'Delivered'),           # Successfully delivered
        ('Cancelled',          'Cancelled'),           # Order cancelled
    )

    # Unique reference shown to customer & staff (e.g. ORD-3F7A)
    reference = models.CharField(max_length=20, unique=True, editable=False, db_index=True)

    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL)

    # For logged-in customers this links to their account.
    # Guest checkouts leave this null — delivery info captured separately.
    customer = models.ForeignKey(
        Customer, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='orders'
    )

    # Delivery details (captured at checkout for every order)
    delivery_name    = models.CharField(max_length=200)
    delivery_phone   = models.CharField(max_length=20, validators=[_phone_validator])
    delivery_email   = models.EmailField(blank=True, null=True)
    delivery_country = models.ForeignKey(
        'Country', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='orders'
    )
    delivery_state   = models.ForeignKey(
        State, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='orders'
    )
    delivery_lga     = models.ForeignKey(
        LGA, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='orders'
    )
    delivery_address = models.CharField(max_length=500)

    notes           = models.CharField(max_length=1000, null=True, blank=True)
    delivery_fee    = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount        = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    coupon          = models.ForeignKey(
        'Coupon', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='orders'
    )
    
    # Order fulfillment status (physical state, not payment)
    status = models.CharField(
        max_length=30, 
        choices=ORDER_STATUS_CHOICES, 
        default='Pending',
        db_index=True,
        help_text='Physical fulfillment status of the order'
    )
    
    # Dual delivery confirmation fields
    dispatcher_confirmed = models.BooleanField(
        default=False,
        help_text='Has the dispatcher confirmed delivery?'
    )
    dispatcher_confirmed_at = models.DateTimeField(null=True, blank=True)
    dispatcher_confirmed_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='confirmed_deliveries',
        help_text='Staff member who confirmed delivery'
    )
    
    customer_confirmed = models.BooleanField(
        default=False,
        help_text='Has the customer confirmed receiving the order?'
    )
    customer_confirmed_at = models.DateTimeField(null=True, blank=True)
    
    date_create = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_create']

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f'ORD-{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference
    
    @property
    def is_fully_delivered(self):
        """
        Returns True if both dispatcher and customer have confirmed delivery.
        Used to determine when order status can be updated to 'Delivered'.
        """
        return self.dispatcher_confirmed and self.customer_confirmed

    @property
    def total_amount(self):
        """
        Grand total = items subtotal + delivery_fee − discount.
        Uses pre-annotated `_total_amount` if set by the queryset
        (via annotate()), otherwise falls back to a DB query.
        Call with .annotate(_total_amount=...) on querysets that
        render this in loops to avoid N+1.
        """
        if hasattr(self, '_total_amount') and self._total_amount is not None:
            return self._total_amount + self.delivery_fee - self.discount
        subtotal = sum(item.line_total for item in self.items.all())
        return subtotal + self.delivery_fee - self.discount

    @property
    def is_paid(self):
        """Check if payment has been confirmed for this order."""
        try:
            return self.payment.status == 'Paid'
        except Exception:
            return False

    def add_tracking(self, status, remark='', updated_by=None):
        """Append a tracking record and update order status atomically."""
        self.status = status
        self.save(update_fields=['status', 'updated_at'])
        OrderTracking.objects.create(
            order=self,
            status=status,
            remark=remark,
            updated_by=updated_by,
        )
    
    def deduct_inventory(self, user=None):
        """
        Deduct ingredients from inventory based on order items.
        Should be called when order status changes to 'Preparing'.
        Returns tuple: (success: bool, message: str)
        """
        from decimal import Decimal
        
        if not self.branch:
            return False, 'Order has no branch assigned'
        
        # Import here to avoid circular import
        from .models import IngredientConsumption
        
        deductions = []
        errors = []
        
        # Calculate required ingredients for all items in order
        for order_item in self.items.select_related('product').all():
            product = order_item.product
            quantity = order_item.quantity
            
            # Get recipe (ProductIngredient) for this product
            for recipe in product.ingredients.select_related('ingredient').all():
                ingredient = recipe.ingredient
                
                # Only deduct from same branch
                if ingredient.branch_id != self.branch_id:
                    continue
                
                required_qty = recipe.quantity_required * Decimal(quantity)
                
                # Check if sufficient stock
                if ingredient.quantity_available < required_qty:
                    errors.append(
                        f'Insufficient {ingredient.name}: need {required_qty}{ingredient.unit}, '
                        f'have {ingredient.quantity_available}{ingredient.unit}'
                    )
                    continue
                
                # Deduct from inventory
                ingredient.quantity_available -= required_qty
                ingredient.save(update_fields=['quantity_available', 'updated_at'])
                
                # Record consumption
                IngredientConsumption.objects.create(
                    ingredient=ingredient,
                    order=self,
                    quantity_used=required_qty,
                    consumed_by=user,
                    notes=f'Order {self.reference}: {quantity}x {product.name}'
                )
                
                deductions.append(f'{ingredient.name}: -{required_qty}{ingredient.unit}')
        
        if errors:
            return False, '; '.join(errors)
        
        if deductions:
            return True, f'Deducted: {", ".join(deductions)}'
        
        return True, 'No ingredients to deduct (products have no recipes defined)'
    
    def can_prepare(self):
        """
        Check if order can be moved to 'Preparing' status.
        Business rules:
        - For Cash on Delivery: Can prepare if order is 'Confirmed'
        - For other payment methods: Can prepare only if payment is 'Paid'
        """
        if self.status != 'Confirmed':
            return False, 'Order must be Confirmed first'
        
        # Check payment status
        try:
            payment = self.payment
            if payment.method == 'Cash on Delivery':
                # COD orders can be prepared without payment
                return True, 'OK'
            else:
                # Other methods require payment confirmation first
                if payment.status == 'Paid':
                    return True, 'OK'
                else:
                    return False, f'Payment must be confirmed for {payment.method} orders'
        except Exception:
            return False, 'No payment record found'
    
    def can_confirm(self):
        """Check if manager can confirm a pending order"""
        return self.status == 'Pending'
    
    def confirm_delivery_by_dispatcher(self, user):
        """
        Dispatcher confirms successful delivery.
        If both dispatcher and customer confirm, order status → 'Delivered'
        and COD payment is marked as 'Paid'.
        Also marks the DispatcherAssignment as 'Completed'.
        """
        from django.utils import timezone

        if self.status != 'Out for Delivery':
            return False, 'Order must be "Out for Delivery" to confirm'

        if self.dispatcher_confirmed:
            return False, 'Dispatcher already confirmed this delivery'

        # Mark dispatcher confirmation on the Order
        self.dispatcher_confirmed = True
        self.dispatcher_confirmed_at = timezone.now()
        self.dispatcher_confirmed_by = user
        self.save(update_fields=[
            'dispatcher_confirmed',
            'dispatcher_confirmed_at',
            'dispatcher_confirmed_by',
            'updated_at'
        ])

        # Mark the DispatcherAssignment as Completed so it appears in the
        # dispatcher's "recently delivered" list
        try:
            from .models import DispatcherAssignment
            DispatcherAssignment.objects.filter(
                order=self, dispatcher=user
            ).update(status='Completed')
        except Exception:
            pass

        # Check if both parties confirmed
        if self.is_fully_delivered:
            self.status = 'Delivered'
            self.save(update_fields=['status', 'updated_at'])

            OrderTracking.objects.create(
                order=self,
                status='Delivered',
                remark='Delivery confirmed by dispatcher and customer.',
                updated_by=user,
            )

            try:
                payment = self.payment
                if payment.method == 'Cash on Delivery' and payment.status != 'Paid':
                    payment.status = 'Paid'
                    payment.paid_at = timezone.now()
                    payment.paid_by = f'Dispatcher: {user.username}'
                    payment.save(update_fields=['status', 'paid_at', 'paid_by'])
            except Exception:
                pass

            return True, 'Delivery fully confirmed! Order completed and payment received.'

        return True, 'Dispatcher confirmation recorded. Waiting for customer confirmation.'
    
    def confirm_delivery_by_customer(self):
        """
        Customer confirms they received the order.
        If both dispatcher and customer confirm, order status → 'Delivered'.
        
        Returns tuple: (success: bool, message: str)
        """
        from django.utils import timezone
        
        if self.status != 'Out for Delivery':
            return False, 'Order must be "Out for Delivery" to confirm'
        
        if self.customer_confirmed:
            return False, 'You already confirmed this delivery'
        
        # Mark customer confirmation
        self.customer_confirmed = True
        self.customer_confirmed_at = timezone.now()
        self.save(update_fields=[
            'customer_confirmed',
            'customer_confirmed_at',
            'updated_at'
        ])
        
        # Check if both parties confirmed
        if self.is_fully_delivered:
            self.status = 'Delivered'
            self.save(update_fields=['status', 'updated_at'])
            
            # Write a tracking history row
            OrderTracking.objects.create(
                order=self,
                status='Delivered',
                remark='Delivery confirmed by dispatcher and customer.',
                updated_by=None,  # customer has no staff user object
            )
            
            # For COD orders, mark payment as received
            try:
                payment = self.payment
                if payment.method == 'Cash on Delivery' and payment.status != 'Paid':
                    payment.status = 'Paid'
                    payment.paid_at = timezone.now()
                    payment.save(update_fields=['status', 'paid_at'])
            except Exception:
                pass
            
            return True, 'Thank you! Delivery confirmed and order completed.'
        
        return True, 'Your confirmation recorded. Waiting for dispatcher confirmation.'


# ---------------------------------------------------------------------------
# OrderItem  (one row per product in the cart)
# ---------------------------------------------------------------------------

class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product    = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    # Snapshot the price at the time of order so historical records stay accurate
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity   = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity}× {self.product}'

    @property
    def line_total(self):
        return self.unit_price * self.quantity


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class Payment(models.Model):
    # Payment status choices - separate from order status
    PAYMENT_STATUS_CHOICES = (
        ('Pending',   'Pending Payment'),
        ('Paid',      'Paid'),
        ('Failed',    'Failed'),
        ('Refunded',  'Refunded'),
    )
    
    # Payment method choices - updated with clearer names
    PAYMENT_METHOD_CHOICES = (
        ('Cash on Delivery', 'Cash on Delivery'),
        ('Bank Transfer',    'Bank Transfer'),
        ('Card',             'Debit/Credit Card'),
        ('Mobile Money',     'Mobile Money'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    method = models.CharField(
        max_length=30, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='Cash on Delivery',
        help_text='How the customer will pay'
    )
    
    status = models.CharField(
        max_length=30, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='Pending',
        help_text='Payment collection status'
    )
    
    # External payment gateway transaction reference (Paystack, Flutterwave, etc.)
    gateway_ref = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text='Reference from payment gateway'
    )
    
    # New fields for payment tracking
    payment_reference = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Bank transfer reference or transaction ID'
    )
    
    paid_by = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Who confirmed/processed the payment'
    )
    
    payment_notes = models.TextField(
        blank=True,
        help_text='Additional notes for offline payments'
    )
    
    paid_at = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payment'
        # Prevent duplicate payment references across the system.
        # Empty strings are excluded (blank references are allowed on COD / no-ref payments).
        constraints = [
            models.UniqueConstraint(
                fields=['payment_reference'],
                condition=models.Q(payment_reference__gt=''),
                name='unique_nonempty_payment_reference',
            )
        ]

    def __str__(self):
        return f'Payment {self.order.reference} – {self.status} ({self.method})'

    def is_cod(self):
        return self.method == 'Cash on Delivery'

    def requires_prepayment(self):
        return self.method != 'Cash on Delivery'

