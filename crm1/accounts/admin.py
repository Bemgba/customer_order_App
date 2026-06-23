from django.contrib import admin
from django.db.models import Sum, F, DecimalField, Value
from django.db.models.functions import Coalesce
from .models import (
    AuditLog, Branch, BranchProduct, Coupon, Country,
    Customer, CustomerAddress, Delivery, DispatcherAssignment,
    Ingredient, LGA, Notification, Order, OrderItem,
    OrderTracking, Payment, Product, ProductCategory,
    ProductIngredient, Review, Role, State, Tag, UserProfile,
)


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country')
    list_filter = ('country',)
    search_fields = ('id', 'name')


@admin.register(LGA)
class LGAAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'state')
    list_filter = ('state',)
    search_fields = ('id', 'name')


# ---------------------------------------------------------------------------
# Roles & Users
# ---------------------------------------------------------------------------

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'can_manage_orders', 'can_delete_orders',
        'can_manage_products', 'can_view_products', 'can_add_products',
        'can_edit_products', 'can_delete_products',
        'can_manage_inventory', 'can_manage_payments', 'can_view_reports',
        'can_manage_customers', 'can_manage_users', 'can_manage_branches',
        'date_created',
    )
    search_fields = ('name',)
    readonly_fields = ('date_created',)

    fieldsets = (
        ('General', {
            'fields': ('name', 'description')
        }),
        ('Orders', {
            'fields': ('can_manage_orders', 'can_delete_orders'),
        }),
        ('Products', {
            'fields': (
                'can_manage_products', 'can_view_products', 'can_add_products',
                'can_edit_products', 'can_delete_products',
            ),
            'description': 'Granular product permissions. "can_manage_products" is a legacy alias.',
        }),
        ('Inventory & Reports', {
            'fields': ('can_manage_inventory', 'can_manage_payments', 'can_view_reports'),
        }),
        ('Management', {
            'fields': ('can_manage_customers', 'can_manage_users', 'can_manage_branches'),
        }),
        ('Metadata', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_ceo', 'branch', 'role_names', 'date_created')
    list_filter = ('is_ceo', 'branch')
    filter_horizontal = ('roles',)
    search_fields = ('user__username',)


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'status', 'manager', 'date_created')
    list_filter = ('status',)
    search_fields = ('name', 'address')


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'branch', 'date_create')
    list_filter = ('category', 'branch', 'is_available')
    search_fields = ('name',)


@admin.register(BranchProduct)
class BranchProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'branch', 'price', 'quantity_available', 'is_available')
    list_filter = ('branch', 'is_available')
    search_fields = ('product__name',)


# ---------------------------------------------------------------------------
# Customers & Addresses
# ---------------------------------------------------------------------------

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'state', 'lga', 'branch', 'date_create')
    list_filter = ('branch', 'state')
    search_fields = ('name', 'email', 'phone')


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'label', 'address', 'state', 'lga', 'is_default')
    list_filter = ('state', 'is_default')
    search_fields = ('customer__name', 'address')


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('line_total',)


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0


class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'delivery_name', 'delivery_phone',
                    'branch', 'status', 'total_amount', 'date_create')
    list_filter = ('status', 'branch')
    search_fields = ('reference', 'delivery_name', 'delivery_phone')
    readonly_fields = ('reference', 'total_amount')
    inlines = [OrderItemInline, PaymentInline, OrderTrackingInline]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .annotate(
                _total_amount=Coalesce(
                    Sum(F('items__unit_price') * F('items__quantity')),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'method', 'status', 'gateway_ref', 'paid_at')
    list_filter = ('status', 'method')
    search_fields = ('order__reference', 'gateway_ref')


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'remark', 'updated_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('order__reference',)


# ---------------------------------------------------------------------------
# Dispatcher & Delivery
# ---------------------------------------------------------------------------

@admin.register(DispatcherAssignment)
class DispatcherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'dispatcher', 'assigned_by', 'assigned_at', 'status')
    list_filter = ('status',)
    search_fields = ('order__reference', 'dispatcher__username')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'dispatcher', 'delivery_status',
                    'pickup_time', 'delivery_end_time')
    list_filter = ('delivery_status',)
    search_fields = ('order__reference', 'dispatcher__username')


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('user__username', 'title')


# ---------------------------------------------------------------------------
# Promotions
# ---------------------------------------------------------------------------

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value',
                    'start_date', 'end_date', 'usage_limit', 'times_used', 'status')
    list_filter = ('status', 'discount_type', 'branch')
    search_fields = ('code',)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'unit', 'quantity_available',
                    'reorder_level', 'is_low')
    list_filter = ('branch',)
    search_fields = ('name',)


@admin.register(ProductIngredient)
class ProductIngredientAdmin(admin.ModelAdmin):
    list_display = ('product', 'ingredient', 'quantity_required')
    search_fields = ('product__name', 'ingredient__name')


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'customer', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('order__reference', 'customer__name')


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'table_name', 'record_id', 'user', 'created_at')
    list_filter = ('action', 'table_name')
    search_fields = ('table_name', 'record_id', 'user__username')
    readonly_fields = ('action', 'table_name', 'record_id',
                       'old_values', 'new_values', 'created_at', 'user')


admin.site.register(Tag)
