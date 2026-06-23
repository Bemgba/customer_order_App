# Order & Payment Status Redesign - Implementation Roadmap

## Problem Analysis

### Current Issues:
1. ❌ "Paid" is an ORDER status, not a PAYMENT status
2. ❌ Payment and Order statuses are conflated
3. ❌ No support for "Pay on Delivery" workflow
4. ❌ Payment must happen before order preparation
5. ❌ Only one person confirms delivery (no dual confirmation)
6. ❌ No distinction between digital and cash payments

---

## Proposed Solution Architecture

### Core Principle: **Separate Order Fulfillment from Payment**

```
ORDER STATUS     = Physical fulfillment state (food preparation & delivery)
PAYMENT STATUS   = Financial transaction state (money collection)
```

---

## New Status Definitions

### A. ORDER STATUS (Order Model)
```python
ORDER_STATUS_CHOICES = [
    ('Pending',            'Pending Review'),       # New order, awaiting staff review
    ('Confirmed',          'Confirmed'),            # Staff accepted, ready to prepare
    ('Preparing',          'Preparing'),            # Kitchen is cooking
    ('Ready',              'Ready for Pickup'),     # Optional: Food ready, waiting for driver
    ('Out for Delivery',   'Out for Delivery'),     # Driver has the food
    ('Delivered',          'Delivered'),            # Successfully delivered
    ('Cancelled',          'Cancelled'),            # Order cancelled
]
```

### B. PAYMENT STATUS (Payment Model)
```python
PAYMENT_STATUS_CHOICES = [
    ('Pending',           'Pending Payment'),       # Not paid yet
    ('Paid',              'Paid'),                  # Payment received & confirmed
    ('Refunded',          'Refunded'),              # Money returned to customer
    ('Failed',            'Failed'),                # Payment attempt failed
]
```

### C. PAYMENT METHOD (Payment Model)
```python
PAYMENT_METHOD_CHOICES = [
    ('Cash on Delivery',  'Cash on Delivery'),     # Pay when delivered
    ('Bank Transfer',     'Bank Transfer'),         # Offline bank payment
    ('Card',              'Debit/Credit Card'),     # Online card payment
    ('Mobile Money',      'Mobile Money'),          # USSD/wallet payment
]
```

---

## Workflow Scenarios

### Scenario 1: Pay on Delivery (Cash)
```
1. Customer Checkout:
   - Payment Method: "Cash on Delivery"
   - Payment Status: "Pending"
   - Order Status: "Pending" → Manager review needed

2. Manager Reviews:
   - Checks stock availability
   - Order Status: "Pending" → "Confirmed"
   - (Payment still "Pending" - no problem!)

3. Kitchen Prepares:
   - Manager clicks "Start Preparation"
   - Check: Can prepare even if payment = "Pending" (for COD orders)
   - Order Status: "Confirmed" → "Preparing"
   - Inventory auto-deducted

4. Driver Dispatches:
   - Order Status: "Preparing" → "Out for Delivery"
   - Payment Status: Still "Pending"

5. Delivery & Payment:
   a) Dispatcher arrives, collects cash
   b) Dispatcher confirms delivery in app
   c) Customer confirms delivery in app
   d) BOTH confirmations received:
      - Order Status → "Delivered"
      - Payment Status → "Paid"
      - Manager notified of cash collection
```

### Scenario 2: Digital Payment (Card/Mobile Money)
```
1. Customer Checkout:
   - Payment Method: "Card" or "Mobile Money"
   - Redirected to payment gateway
   - Payment successful: 
     - Payment Status: Auto → "Paid"
     - Order Status: "Pending"

2. Manager Reviews:
   - Sees payment is confirmed
   - Order Status: "Pending" → "Confirmed"

3. Kitchen Prepares:
   - Order Status: "Confirmed" → "Preparing"
   - Inventory auto-deducted

4. Driver Dispatches:
   - Order Status: "Preparing" → "Out for Delivery"

5. Delivery Confirmation:
   - Both dispatcher & customer confirm
   - Order Status → "Delivered"
```

### Scenario 3: Offline Bank Transfer
```
1. Customer Checkout:
   - Payment Method: "Bank Transfer"
   - Payment Status: "Pending"
   - Order Status: "Pending"
   - Customer makes transfer separately

2. Customer Calls/WhatsApp:
   - Sends payment proof
   - Manager verifies in bank account

3. Manager Updates Payment:
   - Payment Status: "Pending" → "Paid"
   - Order Status: "Pending" → "Confirmed"

4. Continue normal flow...
```

---

## Implementation Phases

### PHASE 1: Database Redesign (Week 1)
**Goal:** Update models to separate concerns

#### 1.1 Update Order Model
```python
# Remove "Paid" from ORDER_STATUS_CHOICES
ORDER_STATUS_CHOICES = [
    ('Pending',            'Pending Review'),
    ('Confirmed',          'Confirmed'),
    ('Preparing',          'Preparing'),
    ('Out for Delivery',   'Out for Delivery'),
    ('Delivered',          'Delivered'),
    ('Cancelled',          'Cancelled'),
]

# Add new fields
class Order(models.Model):
    # ... existing fields ...
    
    # Delivery confirmation
    dispatcher_confirmed = models.BooleanField(default=False)
    dispatcher_confirmed_at = models.DateTimeField(null=True, blank=True)
    dispatcher_confirmed_by = models.ForeignKey(
        User, null=True, blank=True, 
        on_delete=models.SET_NULL,
        related_name='confirmed_deliveries'
    )
    
    customer_confirmed = models.BooleanField(default=False)
    customer_confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Helper property
    @property
    def is_fully_delivered(self):
        """Both parties confirmed delivery"""
        return self.dispatcher_confirmed and self.customer_confirmed
```

#### 1.2 Update Payment Model
```python
PAYMENT_STATUS_CHOICES = [
    ('Pending',   'Pending Payment'),
    ('Paid',      'Paid'),
    ('Refunded',  'Refunded'),
    ('Failed',    'Failed'),
]

PAYMENT_METHOD_CHOICES = [
    ('Cash on Delivery', 'Cash on Delivery'),
    ('Bank Transfer',    'Bank Transfer'),
    ('Card',             'Debit/Credit Card'),
    ('Mobile Money',     'Mobile Money'),
]

class Payment(models.Model):
    # ... existing fields ...
    method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    
    # New fields
    paid_by = models.CharField(max_length=50, blank=True)  # Who confirmed payment
    payment_reference = models.CharField(max_length=100, blank=True)  # Transaction ref
    payment_notes = models.TextField(blank=True)  # For offline payments
```

#### 1.3 Create Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

---

### PHASE 2: Business Logic Updates (Week 1-2)

#### 2.1 Update Order Status Validation
```python
# In Order model
def can_prepare(self):
    """Check if order can be moved to Preparing status"""
    # For COD orders, can prepare without payment
    if self.payment.method == 'Cash on Delivery':
        return self.status == 'Confirmed'
    
    # For other methods, payment must be confirmed
    return self.status == 'Confirmed' and self.payment.status == 'Paid'

def can_confirm(self):
    """Check if manager can confirm order"""
    return self.status == 'Pending'
```

#### 2.2 Update Inventory Deduction
```python
# Keep existing logic but check can_prepare()
if new_status == 'Preparing' and old_status != 'Preparing':
    if not order.can_prepare():
        messages.error(request, 'Cannot prepare: Payment not confirmed for this payment method')
        return
    
    success, inv_message = order.deduct_inventory(user=request.user)
    # ... rest of code
```

#### 2.3 Add Delivery Confirmation Methods
```python
# In Order model
def confirm_delivery_by_dispatcher(self, user):
    """Dispatcher confirms delivery"""
    if self.status != 'Out for Delivery':
        return False, 'Order must be Out for Delivery'
    
    self.dispatcher_confirmed = True
    self.dispatcher_confirmed_at = timezone.now()
    self.dispatcher_confirmed_by = user
    self.save()
    
    # Check if both confirmed
    if self.is_fully_delivered:
        self.status = 'Delivered'
        self.save()
        
        # Update payment for COD
        if self.payment.method == 'Cash on Delivery':
            self.payment.status = 'Paid'
            self.payment.paid_at = timezone.now()
            self.payment.paid_by = f'Dispatcher: {user.username}'
            self.payment.save()
    
    return True, 'Delivery confirmed by dispatcher'

def confirm_delivery_by_customer(self):
    """Customer confirms delivery"""
    if self.status != 'Out for Delivery':
        return False, 'Order must be Out for Delivery'
    
    self.customer_confirmed = True
    self.customer_confirmed_at = timezone.now()
    self.save()
    
    # Check if both confirmed
    if self.is_fully_delivered:
        self.status = 'Delivered'
        self.save()
        
        # Update payment for COD
        if self.payment.method == 'Cash on Delivery':
            self.payment.status = 'Paid'
            self.payment.paid_at = timezone.now()
            self.payment.save()
    
    return True, 'Delivery confirmed by customer'
```

---

### PHASE 3: Manager Interface (Week 2)

#### 3.1 Update Order Detail Page
Add TWO separate sections:

```html
<!-- Order Status Section -->
<div class="card">
    <h5>Order Status</h5>
    <form method="POST" action="{% url 'update_order_status' order.id %}">
        {% csrf_token %}
        <select name="order_status">
            <option>Pending</option>
            <option>Confirmed</option>
            <option>Preparing</option>
            <option>Out for Delivery</option>
            <option>Delivered</option>
            <option>Cancelled</option>
        </select>
        <button>Update Order Status</button>
    </form>
</div>

<!-- Payment Status Section (Separate!) -->
<div class="card mt-3">
    <h5>Payment Status</h5>
    <p>Method: {{ order.payment.method }}</p>
    <p>Status: {{ order.payment.status }}</p>
    
    {% if order.payment.status == 'Pending' %}
    <form method="POST" action="{% url 'update_payment_status' order.id %}">
        {% csrf_token %}
        <select name="payment_status">
            <option value="Paid">Mark as Paid</option>
            <option value="Failed">Mark as Failed</option>
        </select>
        <input type="text" name="payment_reference" placeholder="Payment Reference">
        <textarea name="payment_notes" placeholder="Notes (optional)"></textarea>
        <button>Update Payment Status</button>
    </form>
    {% endif %}
</div>

<!-- Delivery Confirmation Section -->
<div class="card mt-3">
    <h5>Delivery Confirmation</h5>
    <div class="row">
        <div class="col-md-6">
            <strong>Dispatcher:</strong>
            {% if order.dispatcher_confirmed %}
                ✅ Confirmed at {{ order.dispatcher_confirmed_at }}
            {% else %}
                ⏳ Pending
            {% endif %}
        </div>
        <div class="col-md-6">
            <strong>Customer:</strong>
            {% if order.customer_confirmed %}
                ✅ Confirmed at {{ order.customer_confirmed_at }}
            {% else %}
                ⏳ Pending
            {% endif %}
        </div>
    </div>
</div>
```

#### 3.2 Create Separate Views
```python
@login_required
@requires_permission('can_manage_orders')
def update_order_status(request, order_id):
    """Update ONLY order fulfillment status"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('order_status')
        
        # Validation
        if new_status == 'Preparing' and not order.can_prepare():
            messages.error(request, 'Cannot prepare order yet')
            return redirect('order_detail', pk=order_id)
        
        # Update status
        order.status = new_status
        order.save()
        
        messages.success(request, f'Order status updated to {new_status}')
    
    return redirect('order_detail', pk=order_id)


@login_required
@requires_permission('can_manage_orders')
def update_payment_status(request, order_id):
    """Update ONLY payment status"""
    order = get_object_or_404(Order, id=order_id)
    payment = order.payment
    
    if request.method == 'POST':
        new_status = request.POST.get('payment_status')
        payment.status = new_status
        payment.payment_reference = request.POST.get('payment_reference', '')
        payment.payment_notes = request.POST.get('payment_notes', '')
        payment.paid_at = timezone.now()
        payment.paid_by = f'Manager: {request.user.username}'
        payment.save()
        
        messages.success(request, f'Payment status updated to {new_status}')
    
    return redirect('order_detail', pk=order_id)
```

---

### PHASE 4: Dispatcher Interface (Week 3)

#### 4.1 Create Dispatcher Role
```python
# Add to Role model permissions
class Role(models.Model):
    # ... existing fields ...
    can_confirm_delivery = models.BooleanField(default=False)
```

#### 4.2 Create Dispatcher Dashboard
```python
@login_required
@requires_permission('can_confirm_delivery')
def dispatcher_dashboard(request):
    """Show orders assigned for delivery"""
    # Get user's deliveries
    my_deliveries = Order.objects.filter(
        status='Out for Delivery',
        branch=_get_branch(request.user)
    ).select_related('customer', 'payment')
    
    return render(request, 'accounts/dispatcher_dashboard.html', {
        'deliveries': my_deliveries
    })


@login_required
@requires_permission('can_confirm_delivery')
def confirm_delivery_dispatcher(request, order_id):
    """Dispatcher confirms successful delivery"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        success, msg = order.confirm_delivery_by_dispatcher(request.user)
        
        if success:
            messages.success(request, msg)
            if order.is_fully_delivered:
                messages.info(request, 'Order fully delivered! Customer also confirmed.')
        else:
            messages.error(request, msg)
    
    return redirect('dispatcher_dashboard')
```

#### 4.3 Dispatcher Template
```html
<!-- dispatcher_dashboard.html -->
<h2>My Deliveries</h2>

{% for order in deliveries %}
<div class="card mb-3">
    <h5>Order #{{ order.reference }}</h5>
    <p>Customer: {{ order.delivery_name }}</p>
    <p>Address: {{ order.delivery_address }}</p>
    <p>Phone: {{ order.delivery_phone }}</p>
    <p>Payment: {{ order.payment.method }}
        {% if order.payment.method == 'Cash on Delivery' %}
            - <strong>Collect ₦{{ order.total }}</strong>
        {% endif %}
    </p>
    
    <div class="confirmations">
        <p>Your Confirmation: 
            {% if order.dispatcher_confirmed %}
                ✅ Confirmed
            {% else %}
                ⏳ Pending
            {% endif %}
        </p>
        <p>Customer Confirmation: 
            {% if order.customer_confirmed %}
                ✅ Confirmed
            {% else %}
                ⏳ Waiting...
            {% endif %}
        </p>
    </div>
    
    {% if not order.dispatcher_confirmed %}
    <form method="POST" action="{% url 'confirm_delivery_dispatcher' order.id %}">
        {% csrf_token %}
        <button class="btn btn-success">Confirm Delivery</button>
    </form>
    {% endif %}
</div>
{% endfor %}
```

---

### PHASE 5: Customer Interface (Week 3-4)

#### 5.1 Update My Orders Page
```python
@login_required
def my_orders(request):
    """Customer order portal with delivery confirmation"""
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        return render(request, 'accounts/my_orders.html', {'orders': []})
    
    orders = Order.objects.filter(
        customer=customer
    ).select_related('payment').order_by('-date_create')
    
    return render(request, 'accounts/my_orders.html', {
        'orders': orders,
        'customer': customer,
    })


@login_required
def confirm_delivery_customer(request, order_id):
    """Customer confirms they received the order"""
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer)
    
    if request.method == 'POST':
        success, msg = order.confirm_delivery_by_customer()
        
        if success:
            messages.success(request, msg)
            if order.is_fully_delivered:
                messages.success(request, 'Thank you! Your delivery is complete.')
        else:
            messages.error(request, msg)
    
    return redirect('my_orders')
```

#### 5.2 Customer Template
```html
<!-- my_orders.html -->
{% for order in orders %}
<div class="order-card">
    <h5>Order #{{ order.reference }}</h5>
    <p>Status: {{ order.get_status_display }}</p>
    <p>Payment: {{ order.payment.get_status_display }} ({{ order.payment.method }})</p>
    
    {% if order.status == 'Out for Delivery' %}
    <div class="alert alert-info">
        <p>📦 Your order is on the way!</p>
        
        {% if order.payment.method == 'Cash on Delivery' %}
        <p><strong>Please prepare ₦{{ order.total }} in cash</strong></p>
        {% endif %}
        
        <div class="confirmations">
            <p>Dispatcher: 
                {% if order.dispatcher_confirmed %}✅{% else %}⏳{% endif %}
            </p>
            <p>You: 
                {% if order.customer_confirmed %}✅{% else %}⏳{% endif %}
            </p>
        </div>
        
        {% if not order.customer_confirmed %}
        <form method="POST" action="{% url 'confirm_delivery_customer' order.id %}">
            {% csrf_token %}
            <button class="btn btn-success btn-lg">
                ✓ Confirm I Received This Order
            </button>
        </form>
        {% endif %}
    </div>
    {% endif %}
</div>
{% endfor %}
```

---

### PHASE 6: Checkout Flow Update (Week 4)

#### 6.1 Update Checkout View
```python
@ensure_csrf_cookie
def checkout(request):
    """Updated checkout with proper payment method handling"""
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('menu')

    items, grand_total = _cart_items(cart)
    form = CheckoutForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        
        # ... create customer/user as before ...
        
        # Create Order
        order = Order.objects.create(
            branch=branch,
            customer=customer_obj,
            # ... delivery fields ...
            status='Pending',  # Changed from 'Awaiting Payment'
        )

        # Create OrderItems
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                unit_price=item['product'].price,
                quantity=item['qty'],
            )

        # Create Payment
        payment_method = cd['payment_method']
        payment = Payment.objects.create(
            order=order,
            amount=grand_total,
            method=payment_method,
            status='Pending',  # Start as Pending
        )

        # Handle payment based on method
        if payment_method == 'Cash on Delivery':
            # COD: No payment needed now
            messages.info(request, f'Order placed! Pay ₦{grand_total} when delivered.')
            logger.info('COD Order %s placed', order.reference)
            return redirect('order_confirmation', reference=order.reference)
        
        elif payment_method in ['Card', 'Mobile Money']:
            # Digital: Redirect to payment gateway
            return redirect('payment_gateway', reference=order.reference)
        
        elif payment_method == 'Bank Transfer':
            # Offline: Show bank details
            messages.info(request, 'Please transfer to our bank account and contact us.')
            return redirect('order_confirmation', reference=order.reference)

    return render(request, 'accounts/checkout.html', {
        'form': form,
        'cart_items': items,
        'grand_total': grand_total,
        'cart_count': sum(cart.values()),
    })
```

#### 6.2 Add Payment Gateway View (Stub)
```python
def payment_gateway(request, reference):
    """Handle online payment (integrate with Paystack/Flutterwave)"""
    order = get_object_or_404(Order, reference=reference)
    
    # TODO: Integrate with actual payment provider
    # For now, simulate successful payment
    
    return render(request, 'accounts/payment_gateway.html', {
        'order': order,
        'amount': order.payment.amount,
    })


def payment_callback(request):
    """Payment gateway callback (webhook)"""
    # Verify payment with provider
    # Update payment status
    
    reference = request.GET.get('reference')
    status = request.GET.get('status')  # From payment provider
    
    order = get_object_or_404(Order, reference=reference)
    payment = order.payment
    
    if status == 'success':
        payment.status = 'Paid'
        payment.paid_at = timezone.now()
        payment.payment_reference = request.GET.get('transaction_ref')
        payment.save()
        
        messages.success(request, 'Payment successful!')
    else:
        payment.status = 'Failed'
        payment.save()
        messages.error(request, 'Payment failed. Please try again.')
    
    return redirect('order_confirmation', reference=reference)
```

---

## Database Migration Strategy

### Data Migration Script
```python
# migrations/00XX_migrate_paid_status.py
from django.db import migrations

def migrate_paid_orders(apps, schema_editor):
    """Convert old 'Paid' order status to new system"""
    Order = apps.get_model('accounts', 'Order')
    Payment = apps.get_model('accounts', 'Payment')
    
    # Find all orders with status='Paid'
    paid_orders = Order.objects.filter(status='Paid')
    
    for order in paid_orders:
        # Update order status to 'Confirmed'
        order.status = 'Confirmed'
        order.save()
        
        # Update payment status to 'Paid'
        if hasattr(order, 'payment'):
            order.payment.status = 'Paid'
            order.payment.save()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', 'previous_migration'),
    ]
    
    operations = [
        migrations.RunPython(migrate_paid_orders),
    ]
```

---

## Testing Checklist

### Scenario Testing
- [ ] COD order: Place → Confirm → Prepare → Deliver → Both confirm → Payment marked paid
- [ ] Digital payment: Pay online → Status auto-updates → Prepare → Deliver
- [ ] Bank transfer: Order → Manager verifies → Marks paid → Prepare
- [ ] Dispatcher confirms first: Status stays "Out for Delivery"
- [ ] Customer confirms first: Status stays "Out for Delivery"
- [ ] Both confirm: Status → "Delivered", COD payment → "Paid"
- [ ] Cancel paid order: Payment refund flow
- [ ] Inventory deduction: Only when "Preparing" + payment valid

---

## URL Routing Updates

```python
# accounts/urls.py
urlpatterns = [
    # ... existing URLs ...
    
    # Separate order and payment management
    path('orders/<int:order_id>/status/update/', 
         views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/payment/update/', 
         views.update_payment_status, name='update_payment_status'),
    
    # Delivery confirmations
    path('dispatcher/dashboard/', 
         views.dispatcher_dashboard, name='dispatcher_dashboard'),
    path('dispatcher/confirm/<int:order_id>/', 
         views.confirm_delivery_dispatcher, name='confirm_delivery_dispatcher'),
    path('customer/confirm/<int:order_id>/', 
         views.confirm_delivery_customer, name='confirm_delivery_customer'),
    
    # Payment gateway
    path('payment/<str:reference>/', 
         views.payment_gateway, name='payment_gateway'),
    path('payment/callback/', 
         views.payment_callback, name='payment_callback'),
]
```

---

## Security Considerations

1. **Dispatcher Confirmation:**
   - Require OTP or PIN code from customer before confirming
   - Log GPS location of confirmation
   - Time-limit confirmation window (e.g., 2 hours after dispatch)

2. **Payment Verification:**
   - For bank transfers: Require screenshot upload
   - For COD: Limit max amount (e.g., ₦50,000 requires prepayment)
   - Log all payment status changes with user + timestamp

3. **Fraud Prevention:**
   - Track failed delivery attempts
   - Flag customers with multiple unconfirmed deliveries
   - Require prepayment after X failed COD orders

---

## Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Database | 3-4 days | Models updated, migrations created |
| Phase 2: Business Logic | 4-5 days | Validation, deduction, confirmation methods |
| Phase 3: Manager UI | 3-4 days | Separate order/payment controls |
| Phase 4: Dispatcher | 3-4 days | Dashboard, confirmation interface |
| Phase 5: Customer | 3-4 days | Updated portal, confirmation button |
| Phase 6: Checkout | 3-4 days | Payment method handling, gateway integration |
| **Total** | **3-4 weeks** | Complete system redesign |

---

## Quick Start Implementation Order

### Priority 1 (Must Have):
1. Separate order and payment status
2. COD payment method support
3. Dual delivery confirmation

### Priority 2 (Important):
4. Manager separate controls
5. Dispatcher dashboard

### Priority 3 (Nice to Have):
6. Payment gateway integration
7. Advanced security features

---

## Next Steps

1. **Review this roadmap** with your team
2. **Decide on timeline** - implement all at once or phase by phase?
3. **Choose payment gateway** (if digital payments needed)
4. **Create test database** backup before migration
5. **Start with Phase 1** - database changes

Would you like me to start implementing Phase 1 now?
