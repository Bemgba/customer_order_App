<<<<<<< HEAD
import logging
from datetime import datetime
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Case, When, IntegerField, Prefetch, Q
from django.db import IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.views.decorators.http import require_GET

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from .forms import (
    CustomerForm, CheckoutForm, OrderStatusForm,
    CreateUserForm, CreateStaffForm, EditUserRolesForm,
    BranchForm, ProductForm, ProductCategoryForm, RoleForm,
    IngredientForm,
)
from .filters import OrderFilter
from .decorators import (
    unauthenticated_user, admin_only, ceo_only,
    manager_or_ceo, requires_permission,
    _get_profile as _get_profile,   # shared helper — defined once in decorators
)
from .models import (
    AuditLog, Branch, Coupon, Customer,
    Ingredient, IngredientConsumption, LGA, Notification, Order, OrderItem,
    OrderTracking, Payment, Product, ProductCategory,
    ProductIngredient, Role, State, UserProfile,
)

logger = logging.getLogger('accounts')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PAGE_SIZE = getattr(settings, 'PAGINATION_PAGE_SIZE', 20)


# _get_profile is imported from decorators — defined once, shared across both modules.

def _is_ceo(user):
    profile = _get_profile(user)
    return user.is_superuser or (profile is not None and profile.is_ceo)


def _get_branch(user):
    """
    Return the branch assigned to this staff member.
    Checks two sources in order:
      1. UserProfile.branch  — set when CEO creates/edits a staff user
      2. Branch.manager      — set when CEO assigns a manager on the Branch form
    This ensures branch lookup works regardless of which path the CEO used.
    """
    profile = _get_profile(user)
    if profile and profile.branch is not None:
        return profile.branch
    # Fallback: check if this user is set as the manager of any branch
    try:
        return user.managed_branch  # reverse of Branch.manager OneToOneField
    except Branch.DoesNotExist:
        return None


def _sync_manager_profile_branch(branch):
    """
    When a Branch is saved with a manager, ensure that manager's
    UserProfile.branch is also updated to point to this branch.
    This keeps both assignment paths in sync.
    """
    if branch.manager:
        profile = _get_profile(branch.manager)
        if profile and profile.branch != branch:
            profile.branch = branch
            profile.save(update_fields=['branch'])


def _notify(user, title, message):
    """Create an in-app notification for a user."""
    Notification.objects.create(user=user, title=title, message=message)


def _paginate(request, queryset, page_size=PAGE_SIZE):
    paginator = Paginator(queryset, page_size)
    page_num = request.GET.get('page', 1)
    try:
        return paginator.page(page_num)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


# ---------------------------------------------------------------------------
# Cart — stored in the session as {product_id: quantity}
# ---------------------------------------------------------------------------

CART_KEY = 'cart'


def _get_cart(request):
    return request.session.get(CART_KEY, {})


def _save_cart(request, cart):
    request.session[CART_KEY] = cart
    request.session.modified = True


def _cart_items(cart):
    """Return list of dicts with product + qty + line_total for display."""
    if not cart:
        return [], Decimal('0.00')
    ids = [int(k) for k in cart.keys()]
    products = {p.id: p for p in Product.objects.filter(
        id__in=ids, is_available=True
    ).select_related('branch')}
    items = []
    grand_total = Decimal('0.00')
    for pid_str, qty in cart.items():
        product = products.get(int(pid_str))
        if product and product.price:
            lt = product.price * qty
            items.append({'product': product, 'qty': qty, 'line_total': lt})
            grand_total += lt
    return items, grand_total


# ---------------------------------------------------------------------------
# PUBLIC: Menu (index / home for non-staff visitors)
# ---------------------------------------------------------------------------

@ensure_csrf_cookie
def menu(request):
    """
    Public-facing menu page. No login required.
    Displays all available products grouped by category.
    Cart item count shown in the navbar.
    """
    # Fetch all available products in a single query, then group in Python.
    # Products may use either the legacy category CharField OR the category FK.
    # We handle both: prefer category FK name, fall back to category_legacy.
    all_products = (
        Product.objects
        .filter(is_available=True)
        .select_related('category')
        .order_by('name')
    )

    # Canonical display order from CATEGORY tuple
    category_order = [label for _, label in Product.CATEGORY]
    category_label_map = {code: label for code, label in Product.CATEGORY}

    grouped = {}
    for product in all_products:
        # Prefer the FK category name; fall back to legacy CharField
        if product.category:
            label = product.category.name
        elif product.category_legacy:
            label = category_label_map.get(product.category_legacy, product.category_legacy)
        else:
            label = 'Other'
        grouped.setdefault(label, []).append(product)

    # Order by canonical CATEGORY order first, then any extras (FK categories) after
    products_by_category = {}
    for label in category_order:
        if label in grouped:
            products_by_category[label] = grouped[label]
    # Append any FK-based categories not in the legacy list
    for label, items in grouped.items():
        if label not in products_by_category:
            products_by_category[label] = items

    cart = _get_cart(request)
    _, grand_total = _cart_items(cart)

    context = {
        'products_by_category': products_by_category,
        'cart_count': sum(cart.values()),
        'grand_total': grand_total,
    }
    return render(request, 'accounts/menu.html', context)


# ---------------------------------------------------------------------------
# CART: Add / Update / Remove / View
# ---------------------------------------------------------------------------

def cart_add(request, product_id):
    """Add one unit of a product to the session cart (or set qty via POST)."""
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = _get_cart(request)
    pid = str(product_id)

    if request.method == 'POST':
        try:
            qty = int(request.POST.get('qty', 1))
        except (ValueError, TypeError):
            qty = 1
        qty = max(1, min(qty, 999))  # clamp: 1 ≤ qty ≤ 999
        if qty < 1:
            cart.pop(pid, None)
        else:
            cart[pid] = qty
    else:
        cart[pid] = cart.get(pid, 0) + 1

    _save_cart(request, cart)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        _, grand_total = _cart_items(cart)
        return JsonResponse({
            'cart_count': sum(cart.values()),
            'grand_total': str(grand_total),
        })
    return redirect('menu')


def cart_remove(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    _save_cart(request, cart)
    return redirect('cart_view')


@ensure_csrf_cookie
def cart_view(request):
    cart = _get_cart(request)
    items, grand_total = _cart_items(cart)
    return render(request, 'accounts/cart.html', {
        'cart_items': items,
        'grand_total': grand_total,
        'cart_count': sum(cart.values()),
    })


# ---------------------------------------------------------------------------
# CHECKOUT
# ---------------------------------------------------------------------------

@ensure_csrf_cookie
def checkout(request):
    """
    Checkout flow:
      1. Customer fills delivery form
      2. We create/retrieve a Django User  (email=username, phone=password)
      3. Create/retrieve a Customer record linked to that User
      4. Create the Order + OrderItems + pending Payment
      5. Auto-login the customer
      6. Redirect to confirmation page
    """
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('menu')

    items, grand_total = _cart_items(cart)
    form = CheckoutForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data

        email  = (cd.get('delivery_email') or '').strip().lower()
        phone  = cd['delivery_phone'].strip()
        name   = cd['delivery_name'].strip()

        # ------------------------------------------------------------------
        # 1. Find or create a Django User
        # ------------------------------------------------------------------
        username = email if email else phone

        user = None
        existing_match = None   # holds the matched existing user if found

        # If already logged in as a customer, reuse their account directly
        if request.user.is_authenticated and not _get_profile(request.user, request):
            user = request.user
        else:
            # Look up by email
            if email:
                try:
                    existing_match = User.objects.get(username=email)
                except User.DoesNotExist:
                    # Also check by email field
                    existing_match = User.objects.filter(email__iexact=email).first()

            # Look up by phone if still no match
            if existing_match is None:
                customer_by_phone = Customer.objects.filter(phone=phone).select_related('user').first()
                if customer_by_phone and customer_by_phone.user:
                    existing_match = customer_by_phone.user

            # ---------------------------------------------------------------
            # DUPLICATE DETECTION: If we found an existing account and the
            # customer has NOT yet confirmed they want to proceed with it,
            # re-render the form with a notification asking them to confirm.
            # ---------------------------------------------------------------
            confirmed = request.POST.get('account_confirmed') == '1'

            if existing_match and not confirmed:
                # Show warning — re-render with confirmation prompt
                matched_email = existing_match.email or ''
                matched_phone = ''
                try:
                    matched_phone = existing_match.customer.phone or ''
                except Exception:
                    pass

                return render(request, 'accounts/checkout.html', {
                    'form': form,
                    'cart_items': items,
                    'grand_total': grand_total,
                    'cart_count': sum(cart.values()),
                    'existing_account': {
                        'email': matched_email,
                        'phone': matched_phone,
                        'name': existing_match.get_full_name() or existing_match.username,
                    },
                })

            if existing_match:
                # Customer confirmed — use the existing account
                user = existing_match
                logger.info('Checkout: customer confirmed use of existing account: %s', user.username)
            else:
                # No match — create a brand-new account
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=phone,
                        first_name=name.split()[0] if name else '',
                        last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                    )
                    logger.info('New user account created at checkout: %s', username)
                except IntegrityError:
                    if email:
                        user = User.objects.filter(email__iexact=email).first()
                    if user is None:
                        form.add_error('delivery_email', 'An account with this email already exists. Please log in or use a different email.')
                        return render(request, 'accounts/checkout.html', {
                            'form': form,
                            'cart_items': items,
                            'grand_total': grand_total,
                            'cart_count': sum(cart.values()),
                        })

        # ------------------------------------------------------------------
        # 2. Find or create the Customer record
        # ------------------------------------------------------------------
        customer_obj, _ = Customer.objects.get_or_create(
            user=user,
            defaults={
                'name':    name,
                'phone':   phone,
                'email':   email,
                'state':   cd.get('delivery_state'),
                'lga':     cd.get('delivery_lga'),
                'address': cd['delivery_address'],
            }
        )
        # Update address fields if this is a returning customer
        Customer.objects.filter(pk=customer_obj.pk).update(
            name=name,
            phone=phone,
            state=cd.get('delivery_state'),
            lga=cd.get('delivery_lga'),
            address=cd['delivery_address'],
        )

        # ------------------------------------------------------------------
        # 3. Create Order + Items + Payment
        # ------------------------------------------------------------------
        first_product = items[0]['product']
        branch = first_product.branch

        order = Order.objects.create(
            branch=branch,
            customer=customer_obj,
            delivery_name=name,
            delivery_phone=phone,
            delivery_email=email,
            delivery_state=cd.get('delivery_state'),
            delivery_lga=cd.get('delivery_lga'),
            delivery_address=cd['delivery_address'],
            notes=cd.get('notes', ''),
            status='Pending',  # Changed from 'Awaiting Payment' to 'Pending'
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                unit_price=item['product'].price,
                quantity=item['qty'],
            )

        Payment.objects.create(
            order=order,
            amount=grand_total,
            method=cd['payment_method'],
            status='Pending',
        )

        # ------------------------------------------------------------------
        # 4. Auto-login the customer (only if not already logged in as staff)
        # ------------------------------------------------------------------
        if not request.user.is_authenticated:
            request.session.cycle_key()  # prevent session fixation
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

        # Store reference in session so order_confirmation can verify ownership
        request.session['last_order_reference'] = order.reference

        # Clear the session cart
        _save_cart(request, {})

        logger.info('Order %s placed by %s (user: %s)',
                    order.reference, name, user.username)

        return redirect('order_confirmation', reference=order.reference)

    return render(request, 'accounts/checkout.html', {
        'form': form,
        'cart_items': items,
        'grand_total': grand_total,
        'cart_count': sum(cart.values()),
    })


def order_confirmation(request, reference):
    """Thank-you / payment instruction page shown after checkout."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product').select_related('payment'),
        reference=reference
    )
    # Only the customer who placed the order (or staff) may view the confirmation.
    if request.user.is_authenticated:
        profile = _get_profile(request.user, request)
        is_staff = request.user.is_superuser or (
            profile and (profile.is_ceo or profile.roles.exists())
        )
        if not is_staff:
            # Customer must own this order
            try:
                if order.customer is None or order.customer.user != request.user:
                    raise PermissionDenied("You are not authorized to view this order.")
            except Exception:
                raise PermissionDenied("You are not authorized to view this order.")
    else:
        # Unauthenticated: only allow if the session contains this reference
        # (set immediately after checkout before redirect)
        allowed_ref = request.session.get('last_order_reference')
        if allowed_ref != reference:
            return redirect('login')
    return render(request, 'accounts/order_confirmation.html', {'order': order})


# ---------------------------------------------------------------------------
# CUSTOMER: My Orders (login required) + Cancel
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def account_settings(request):
    """Customer profile settings page."""
    try:
        customer_obj = request.user.customer
    except Exception:
        return redirect('my_orders')

    form = CustomerForm(instance=customer_obj)
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('account_settings')

    return render(request, 'accounts/account_settings.html', {'form': form})


@ensure_csrf_cookie
@login_required(login_url='login')
def my_orders(request):
    """Customer portal — shows all orders for the logged-in customer."""
    try:
        customer_obj = request.user.customer
    except Customer.DoesNotExist:
        return render(request, 'accounts/my_orders.html', {'orders': [], 'customer': None})

    orders = (
        Order.objects
        .filter(customer=customer_obj)
        .prefetch_related('items__product')
        .select_related('payment', 'delivery_state', 'delivery_lga')
        .order_by('-date_create')
    )
    return render(request, 'accounts/my_orders.html', {
        'orders': orders,
        'customer': customer_obj,
    })


@ensure_csrf_cookie
@login_required(login_url='login')
def cancel_order(request, reference):
    """Customer can cancel their own order if it hasn't been prepared yet."""
    try:
        customer_obj = request.user.customer
    except Customer.DoesNotExist:
        raise PermissionDenied("No customer account found.")

    order = get_object_or_404(
        Order.objects.prefetch_related('items__product').select_related('payment'),
        reference=reference, customer=customer_obj
    )

    # Only allow cancellation before preparation starts
    cancellable = order.status in ('Pending', 'Confirmed')
    if not cancellable:
        messages.error(
            request,
            f'Order {reference} cannot be cancelled — it is already {order.status}.'
        )
        return redirect('my_orders')

    if request.method == 'POST':
        order.status = 'Cancelled'
        order.save(update_fields=['status'])
        logger.info('Order %s cancelled by customer %s', reference, request.user.username)
        messages.success(request, f'Order {reference} has been cancelled.')
        return redirect('my_orders')

    return render(request, 'accounts/cancel_order_confirm.html', {'order': order})


# ---------------------------------------------------------------------------
# PUBLIC: Order tracking (no login required — enter ref + phone)
# ---------------------------------------------------------------------------

@ensure_csrf_cookie
def order_track(request):
    """
    Public order tracking page.
    Customer enters their order reference + phone number to see status.
    """
    order = None
    error = None
    steps = []

    # Updated STATUS_STEPS for new order status system
    STATUS_STEPS = [
        'Pending',
        'Confirmed',
        'Preparing',
        'Out for Delivery',
        'Delivered',
    ]

    if request.method == 'POST':
        reference = request.POST.get('reference', '').strip().upper()
        phone     = request.POST.get('phone', '').strip()

        if reference and phone:
            try:
                order = (
                    Order.objects
                    .prefetch_related('items__product')
                    .select_related('payment', 'delivery_state', 'delivery_lga')
                    .get(reference=reference, delivery_phone=phone)
                )

                # Build progress steps for the template
                current_index = STATUS_STEPS.index(order.status) if order.status in STATUS_STEPS else -1
                for i, label in enumerate(STATUS_STEPS):
                    if i < current_index:
                        dot, line = 'past', 'done'
                    elif i == current_index:
                        dot, line = 'active', ''
                    else:
                        dot, line = '', ''
                    steps.append((label, dot, line))

            except Order.DoesNotExist:
                error = 'No order found with that reference and phone number. Please check and try again.'
        else:
            error = 'Please enter both your order reference and phone number.'

    return render(request, 'accounts/order_track.html', {
        'order': order,
        'error': error,
        'steps': steps,
    })


# ---------------------------------------------------------------------------
# AJAX — Load LGAs for a selected state (dependent dropdown)
# ---------------------------------------------------------------------------

@require_GET
def load_lgas(request):
    state_id = request.GET.get('state_id', '').strip()
    if not state_id:
        return JsonResponse([], safe=False)
    lgas = LGA.objects.filter(state_id=state_id).order_by('name').values('id', 'name')
    return JsonResponse(list(lgas), safe=False)


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

@unauthenticated_user
def registerPage(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
            except IntegrityError:
                form.add_error('email', 'A user with this email already exists.')
            else:
                Customer.objects.get_or_create(
                    user=user,
                    defaults={'name': user.username, 'email': user.email}
                )
                logger.info('New customer registered: %s', user.username)
                messages.success(request, f'Account created for {user.username}. Please log in.')
                return redirect('login')
    return render(request, 'accounts/register.html', {'form': form})


@unauthenticated_user
def loginPage(request):
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password   = request.POST.get('password', '')

        # Try username login first.
        user = authenticate(request, username=identifier, password=password)

        # If username auth fails, also allow login by email (robust check).
        if user is None and '@' in identifier:
            matched = User.objects.filter(email__iexact=identifier)
            if matched.exists():
                logger.info('Login email lookup found %d candidate(s): %s', matched.count(), ','.join([u.username for u in matched]))
            else:
                logger.info('Login email lookup found 0 candidates for %s', identifier)
            for candidate in matched:
                pw_ok = candidate.check_password(password)
                logger.info('Password check for candidate %s: %s', candidate.username, 'OK' if pw_ok else 'NO')
                if pw_ok:
                    user = candidate
                    break

        if user is not None:
            # Ensure a backend is set on users obtained without `authenticate()`
            if not hasattr(user, 'backend'):
                user.backend = 'django.contrib.auth.backends.ModelBackend'
            # Cycle the session on login to invalidate any old session
            # (prevents sessions surviving app redeployment)
            request.session.cycle_key()
            login(request, user)
            logger.info('User logged in: %s', user.username)

            # Route based on role: staff → dashboard, customer → my orders
            profile = _get_profile(user, request)
            if user.is_superuser or (profile and (profile.is_ceo or profile.roles.exists())):
                return redirect('home')
            return redirect('my_orders')

        logger.warning('Failed login attempt for identifier: %s', identifier)
        messages.error(request, 'Username/email or password incorrect.')
    return render(request, 'accounts/login.html', {})


def logoutUser(request):
    logger.info('User logged out: %s', request.user.username)
    logout(request)
    return redirect('login')


# ---------------------------------------------------------------------------
# STAFF DASHBOARD
# ---------------------------------------------------------------------------

@ensure_csrf_cookie
@login_required(login_url='login')
@admin_only
def home(request):
    profile = _get_profile(request.user, request)
    is_ceo_user = _is_ceo(request.user)
    # Staff see active orders (not just paid - new system separates order/payment status)
    active_statuses = ('Pending', 'Confirmed', 'Preparing', 'Out for Delivery', 'Delivered')

    if is_ceo_user:
        orders_qs = (
            Order.objects
            .filter(status__in=active_statuses)
            .select_related('branch', 'payment')
            .prefetch_related('items__product')
        )
        branches = Branch.objects.annotate(
            order_count=Count('order'),
            customer_count=Count('customer')
        )
        branch_context = 'All Branches'
    else:
        branch = _get_branch(request.user)
        if branch is None:
            return HttpResponse(
                '<h3>You are not assigned to any branch. Contact the CEO.</h3>',
                status=403
            )
        orders_qs = (
            Order.objects
            .filter(branch=branch, status__in=active_statuses)
            .select_related('payment')
            .prefetch_related('items__product')
        )
        branches = Branch.objects.filter(id=branch.id).annotate(
            order_count=Count('order'),
            customer_count=Count('customer')
        )
        branch_context = branch.name

    orders_page = _paginate(request, orders_qs, page_size=15)

    stats = orders_qs.aggregate(
        total_orders=Count('id'),
        delivered=Count('id', filter=Q(status='Delivered')),
        pending=Count('id', filter=Q(status='Pending')),
        preparing=Count('id', filter=Q(status='Preparing')),
        total_revenue=Sum('payment__amount', filter=Q(payment__status='Paid')),
    )
    total_orders  = stats['total_orders']
    delivered     = stats['delivered']
    pending       = stats['pending'] + stats['preparing']  # Combine pending counts
    total_revenue = stats['total_revenue'] or Decimal('0.00')

    context = {
        'orders_page': orders_page,
        'total_orders': total_orders,
        'delivered': delivered,
        'pending': pending,
        'total_revenue': total_revenue,
        'branches': branches,
        'branch_context': branch_context,
        'is_ceo': is_ceo_user,
        'user_profile': profile,
    }
    return render(request, 'accounts/dashboard1.html', context)


# ---------------------------------------------------------------------------
# STAFF — Order detail & status update
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_manage_orders')
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects
        .prefetch_related('items__product', 'tracking')
        .select_related('payment', 'branch', 'delivery_state', 'delivery_lga',
                        'customer__user'),
        id=pk
    )

    if not _is_ceo(request.user):
        branch = _get_branch(request.user)
        if branch is None or order.branch != branch:
            raise PermissionDenied("This order belongs to a different branch.")

    form = OrderStatusForm(instance=order)
    
    # This view now only handles ORDER status updates
    # Payment status is handled by update_payment_status view
    if request.method == 'POST':
        old_status = order.status  # capture BEFORE form validation mutates the instance
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            remark = form.cleaned_data.get('notes', '') or ''

            # Validation: Check if status change is allowed
            # Use old_status for the check — form.is_valid() may have mutated order.status
            if new_status == 'Preparing' and old_status != 'Preparing':
                # Temporarily restore old status on the instance so can_prepare() reads correctly
                order.status = old_status
                can_prep, prep_msg = order.can_prepare()
                if not can_prep:
                    messages.error(request, f'Cannot prepare order: {prep_msg}')
                    return render(request, 'accounts/order_detail.html', {
                        'order': order,
                        'form': form,
                        'tracking_history': order.tracking.all().order_by('created_at'),
                    })
                
                # Auto-deduct inventory
                success, inv_message = order.deduct_inventory(user=request.user)
                if not success:
                    messages.error(request, f'Cannot prepare order: {inv_message}')
                    return render(request, 'accounts/order_detail.html', {
                        'order': order,
                        'form': form,
                        'tracking_history': order.tracking.all().order_by('created_at'),
                    })
                else:
                    messages.info(request, f'Inventory updated: {inv_message}')

            # Update status with tracking
            order.add_tracking(
                status=new_status,
                remark=remark,
                updated_by=request.user
            )

            # Audit log entry
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                table_name='accounts_order',
                record_id=str(order.pk),
                old_values={'status': old_status},
                new_values={'status': new_status, 'notes': remark},
            )

            # Notify the customer if they have an account
            if order.customer and order.customer.user:
                status_messages = {
                    'Confirmed':        'Your order has been confirmed and will be prepared soon.',
                    'Preparing':        'Your order is now being prepared.',
                    'Out for Delivery': 'Your order is on its way!',
                    'Delivered':        'Your order has been delivered. Enjoy your meal!',
                    'Cancelled':        f'Your order {order.reference} has been cancelled.',
                }
                msg = status_messages.get(new_status)
                if msg:
                    _notify(
                        order.customer.user,
                        title=f'Order {order.reference} – {new_status}',
                        message=msg,
                    )

            logger.info('Order %s: %s → %s by %s',
                        order.reference, old_status, new_status, request.user.username)
            messages.success(request, f'Order status updated to {new_status}.')
            return redirect('order_detail', pk=order.id)

    tracking_history = order.tracking.all().order_by('created_at')

    # Build list of available dispatchers from same branch for assignment UI
    from .models import DispatcherAssignment, UserProfile
    dispatcher_profile_ids = UserProfile.objects.filter(
        roles__can_confirm_delivery=True
    ).values_list('user_id', flat=True)
    if _is_ceo(request.user):
        available_dispatchers = User.objects.filter(
            id__in=dispatcher_profile_ids
        ).order_by('username')
    else:
        branch = _get_branch(request.user)
        # Filter dispatchers to the same branch
        branch_dispatcher_ids = UserProfile.objects.filter(
            roles__can_confirm_delivery=True,
            branch=branch
        ).values_list('user_id', flat=True)
        available_dispatchers = User.objects.filter(
            id__in=branch_dispatcher_ids
        ).order_by('username')

    # Get current assignment if any
    current_assignment = DispatcherAssignment.objects.filter(
        order=order
    ).select_related('dispatcher').first()

    return render(request, 'accounts/order_detail.html', {
        'order': order,
        'form': form,
        'tracking_history': tracking_history,
        'available_dispatchers': available_dispatchers,
        'current_assignment': current_assignment,
    })


@login_required(login_url='login')
@requires_permission('can_delete_orders')
def deleteOrder(request, pk):
    order = get_object_or_404(Order, id=pk)

    if not _is_ceo(request.user):
        branch = _get_branch(request.user)
        if branch is None or order.branch != branch:
            raise PermissionDenied("This order belongs to a different branch.")

    if request.method == 'POST':
        logger.warning('Order %s deleted by %s', order.reference, request.user.username)
        order.delete()
        messages.success(request, 'Order deleted.')
        return redirect('view_all_orders')

    return render(request, 'accounts/delete.html', {'item': order})


# ---------------------------------------------------------------------------
# NEW: Separate Payment Status Management
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@login_required(login_url='login')
@requires_permission('can_manage_orders')
def update_payment_status(request, order_id):
    """
    Update ONLY payment status (separate from order fulfillment status).
    Validates that payment_reference is not already used by another order.
    """
    order = get_object_or_404(Order, id=order_id)
    payment = order.payment

    if not _is_ceo(request.user):
        branch = _get_branch(request.user)
        if branch is None or order.branch != branch:
            raise PermissionDenied("This order belongs to a different branch.")

    if request.method == 'POST':
        old_status = payment.status
        new_status = request.POST.get('payment_status')
        new_reference = request.POST.get('payment_reference', '').strip()

        if new_status in ['Paid', 'Failed', 'Refunded']:

            # Guard: reject if payment already marked Paid
            if payment.status == 'Paid':
                messages.error(request, 'Payment has already been confirmed. It cannot be updated again.')
                return redirect('order_detail', pk=order_id)

            # Guard: reject duplicate payment_reference
            if new_reference:
                duplicate = Payment.objects.filter(
                    payment_reference=new_reference
                ).exclude(pk=payment.pk).first()
                if duplicate:
                    messages.error(
                        request,
                        f'Reference "{new_reference}" is already recorded on order '
                        f'{duplicate.order.reference}. Each payment reference must be unique.'
                    )
                    return redirect('order_detail', pk=order_id)

            payment.status = new_status
            payment.payment_reference = new_reference
            payment.payment_notes = request.POST.get('payment_notes', '').strip()

            if new_status == 'Paid':
                from django.utils import timezone
                payment.paid_at = timezone.now()
                payment.paid_by = f'Manager: {request.user.username}'

            payment.save()

            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                table_name='accounts_payment',
                record_id=str(payment.pk),
                old_values={'status': old_status},
                new_values={
                    'status': new_status,
                    'reference': payment.payment_reference,
                    'notes': payment.payment_notes
                },
            )

            logger.info('Payment for order %s: %s → %s by %s',
                        order.reference, old_status, new_status, request.user.username)
            messages.success(request, f'Payment status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid payment status.')

    return redirect('order_detail', pk=order_id)


# ---------------------------------------------------------------------------
# NEW: Delivery Confirmation Views
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_confirm_delivery')
def confirm_delivery_dispatcher(request, order_id):
    """
    Dispatcher/Staff confirms successful delivery.
    Part of dual-confirmation system for security.
    """
    order = get_object_or_404(Order, id=order_id)

    if not _is_ceo(request.user):
        branch = _get_branch(request.user)
        if branch is None or order.branch != branch:
            raise PermissionDenied("This order belongs to a different branch.")

    if request.method == 'POST':
        success, msg = order.confirm_delivery_by_dispatcher(request.user)
        
        if success:
            messages.success(request, msg)
            logger.info('Dispatcher confirmed delivery for order %s by %s',
                        order.reference, request.user.username)
            
            # Notify customer if both confirmed
            if order.is_fully_delivered and order.customer and order.customer.user:
                _notify(
                    order.customer.user,
                    title=f'Order {order.reference} Delivered',
                    message='Your order has been successfully delivered. Thank you!'
                )
        else:
            messages.error(request, msg)
    
    # Redirect: dispatchers go to their dashboard, managers to order detail
    profile = _get_profile(request.user, request)
    if profile and profile.has_permission('can_manage_orders') and not profile.has_permission('can_confirm_delivery') or _is_ceo(request.user):
        return redirect('order_detail', pk=order_id)
    return redirect('dispatcher_dashboard')


@login_required(login_url='login')
def confirm_delivery_customer(request, order_id):
    """
    Customer confirms they received the order.
    Part of dual-confirmation system for trust and security.
    """
    try:
        order = get_object_or_404(Order, id=order_id, customer=request.user.customer)
    except Exception:
        raise PermissionDenied("You don't have permission to confirm this order.")

    if request.method == 'POST':
        success, msg = order.confirm_delivery_by_customer()
        
        if success:
            messages.success(request, msg)
            logger.info('Customer confirmed delivery for order %s', order.reference)
        else:
            messages.error(request, msg)
    
    return redirect('my_orders')


# ---------------------------------------------------------------------------
# DISPATCHER DASHBOARD — Phase 4
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_confirm_delivery')
def dispatcher_dashboard(request):
    """
    Dispatcher dashboard.
    Shows:
    - Orders explicitly assigned to this dispatcher via DispatcherAssignment
    - PLUS unassigned 'Out for Delivery' orders from the same branch
      (no DispatcherAssignment exists yet — manager moved status directly)
    CEO sees all Out for Delivery orders regardless of assignment.
    """
    from .models import DispatcherAssignment
    from django.db.models import Q

    branch = _get_branch(request.user)

    if _is_ceo(request.user):
        deliveries = (
            Order.objects
            .filter(status='Out for Delivery')
            .select_related('payment', 'branch', 'delivery_state', 'delivery_lga')
            .prefetch_related('items__product', 'dispatcher_assignments')
            .order_by('date_create')
        )
        recent_delivered = (
            Order.objects.filter(status='Delivered')
            .select_related('payment')
            .order_by('-updated_at')[:20]
        )
    else:
        # Orders assigned to THIS dispatcher
        assigned_ids = DispatcherAssignment.objects.filter(
            dispatcher=request.user,
            status__in=['Assigned', 'Accepted']
        ).values_list('order_id', flat=True)

        # Orders that have ANY dispatcher assignment (assigned to someone else)
        any_assigned_ids = DispatcherAssignment.objects.filter(
            status__in=['Assigned', 'Accepted']
        ).values_list('order_id', flat=True)

        # Deliveries = assigned to me + unassigned branch orders
        base_qs = Order.objects.filter(status='Out for Delivery')
        if branch:
            base_qs = base_qs.filter(branch=branch)

        deliveries = (
            base_qs
            .filter(
                Q(id__in=assigned_ids) |          # assigned to me
                ~Q(id__in=any_assigned_ids)        # OR not assigned to anyone
            )
            .select_related('payment', 'branch', 'delivery_state', 'delivery_lga')
            .prefetch_related('items__product', 'dispatcher_assignments')
            .distinct()
            .order_by('date_create')
        )

        completed_ids = DispatcherAssignment.objects.filter(
            dispatcher=request.user, status='Completed'
        ).values_list('order_id', flat=True)

        recent_delivered = (
            Order.objects
            .filter(id__in=completed_ids, status='Delivered')
            .select_related('payment')
            .order_by('-updated_at')[:20]
        )

    return render(request, 'accounts/dispatcher_dashboard.html', {
        'deliveries': deliveries,
        'recent_delivered': recent_delivered,
        'branch': branch,
    })


# ---------------------------------------------------------------------------
# Assign Dispatcher to an Order
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_assign_dispatcher')
def assign_dispatcher(request, order_id):
    """
    Manager assigns a dispatcher to a specific order.
    Creates/updates a DispatcherAssignment record.
    Also advances order status to Out for Delivery if currently Preparing.
    """
    from .models import DispatcherAssignment

    order = get_object_or_404(
        Order.objects.select_related('branch', 'payment'),
        id=order_id
    )

    if not _is_ceo(request.user):
        branch = _get_branch(request.user)
        if branch is None or order.branch != branch:
            raise PermissionDenied("This order belongs to a different branch.")

    if request.method == 'POST':
        dispatcher_id = request.POST.get('dispatcher_id', '').strip()
        if not dispatcher_id:
            messages.error(request, 'Please select a dispatcher.')
            return redirect('order_detail', pk=order_id)

        try:
            dispatcher_user = User.objects.get(id=dispatcher_id)
        except User.DoesNotExist:
            messages.error(request, 'Selected dispatcher not found.')
            return redirect('order_detail', pk=order_id)

        # Create or update the assignment
        assignment, created = DispatcherAssignment.objects.update_or_create(
            order=order,
            defaults={
                'dispatcher': dispatcher_user,
                'assigned_by': request.user,
                'status': 'Assigned',
            }
        )

        # Advance order to Out for Delivery if it was Preparing
        if order.status == 'Preparing':
            order.add_tracking(
                status='Out for Delivery',
                remark=f'Assigned to dispatcher: {dispatcher_user.username}',
                updated_by=request.user
            )
        elif order.status == 'Out for Delivery':
            order.add_tracking(
                status='Out for Delivery',
                remark=f'Reassigned to: {dispatcher_user.username}',
                updated_by=request.user
            )

        # Notify the dispatcher
        _notify(
            dispatcher_user,
            title=f'Delivery Assigned: {order.reference}',
            message=(
                f'You have been assigned to deliver order {order.reference} to '
                f'{order.delivery_name} at {order.delivery_address}. '
                f'Customer phone: {order.delivery_phone}'
            )
        )

        action = 'assigned' if created else 'reassigned'
        messages.success(
            request,
            f'Order {order.reference} {action} to '
            f'{dispatcher_user.get_full_name() or dispatcher_user.username}.'
        )
        logger.info(
            'Order %s %s to dispatcher %s by %s',
            order.reference, action, dispatcher_user.username, request.user.username
        )

    return redirect('order_detail', pk=order_id)


# ---------------------------------------------------------------------------
# STAFF — View all orders (paid orders, scoped by branch)
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_manage_orders')
def view_all_orders(request):
    # Priority ordering: Updated for new status system
    priority = Case(
        When(status='Pending', then=0),       # New orders need review first
        When(status='Confirmed', then=1),     # Confirmed, ready to prepare
        When(status='Preparing', then=2),     # Being cooked
        When(status='Out for Delivery', then=3),  # In transit
        When(status='Delivered', then=4),     # Completed
        When(status='Cancelled', then=5),     # Cancelled
        default=9,
        output_field=IntegerField(),
    )

    if _is_ceo(request.user):
        orders_qs = (
            Order.objects
            .select_related('branch', 'payment', 'delivery_state', 'delivery_lga')
            .prefetch_related('items__product')
            .annotate(priority=priority)
            .order_by('priority', 'date_create')   # FIFO within each status group
        )
    else:
        branch = _get_branch(request.user)
        orders_qs = (
            Order.objects
            .filter(branch=branch)
            .select_related('payment', 'delivery_state', 'delivery_lga')
            .prefetch_related('items__product')
            .annotate(priority=priority)
            .order_by('priority', 'date_create')
        )

    myFilter = OrderFilter(request.GET, queryset=orders_qs)
    filtered_qs = myFilter.qs
    orders_page = _paginate(request, filtered_qs)

    stats = filtered_qs.aggregate(
        total_orders=Count('id'),
        confirmed_count=Count('id', filter=Q(status='Confirmed')),
        delivered=Count('id', filter=Q(status='Delivered')),
        pending=Count('id', filter=Q(status__in=('Pending', 'Confirmed', 'Preparing'))),
    )

    context = {
        'orders_page': orders_page,
        'myFilter': myFilter,
        'total_orders': stats['total_orders'],
        'confirmed_count': stats['confirmed_count'],
        'delivered': stats['delivered'],
        'pending': stats['pending'],
    }
    response = render(request, 'accounts/view_all_orders.html', context)

    # Instruct the browser to revalidate after 60 seconds
    # (lightweight cache: avoids re-fetching unchanged data on tab switch)
    response['Cache-Control'] = 'private, max-age=60, must-revalidate'
    return response


# ---------------------------------------------------------------------------
# STAFF — Products (paginated)
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_view_products')
def products(request):
    profile = _get_profile(request.user, request)
    if _is_ceo(request.user):
        products_qs = Product.objects.all().select_related('branch').order_by('name')
    else:
        branch = _get_branch(request.user)
        products_qs = Product.objects.filter(branch=branch).select_related('branch').order_by('name')
    products_page = _paginate(request, products_qs)

    # Pass per-action permission flags into the template
    can_add    = profile.has_permission('can_add_products') if profile else False
    can_edit   = profile.has_permission('can_edit_products') if profile else False
    can_delete = profile.has_permission('can_delete_products') if profile else False

    return render(request, 'accounts/products.html', {
        'products_page': products_page,
        'can_add': can_add,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })


@login_required(login_url='login')
@requires_permission('can_add_products')
def createProduct(request):
    branch = _get_branch(request.user)
    form = ProductForm(initial={'branch': branch} if branch else {})

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # Non-CEO staff: lock product to their branch
            if not _is_ceo(request.user) and branch:
                product.branch = branch
            product.save()
            form.save_m2m()  # save tags
            messages.success(request, f'Product "{product.name}" created.')
            return redirect('products')

    return render(request, 'accounts/product_form.html', {'form': form, 'action': 'Add'})


@login_required(login_url='login')
@requires_permission('can_edit_products')
def updateProduct(request, pk):
    product = get_object_or_404(Product, id=pk)

    # Branch-scope check for non-CEO
    if not _is_ceo(request.user):
        branch = _get_branch(request.user)
        if product.branch != branch:
            return HttpResponse(
                '<h3>403 – This product belongs to a different branch.</h3>', status=403
            )

    form = ProductForm(instance=product)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated.')
            return redirect('products')

    return render(request, 'accounts/product_form.html', {'form': form, 'action': 'Edit', 'product': product})


@login_required(login_url='login')
@requires_permission('can_delete_products')
def deleteProduct(request, pk):
    product = get_object_or_404(Product, id=pk)

    if not _is_ceo(request.user):
        branch = _get_branch(request.user)
        if product.branch != branch:
            return HttpResponse(
                '<h3>403 – This product belongs to a different branch.</h3>', status=403
            )

    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted.')
        return redirect('products')

    return render(request, 'accounts/delete.html', {'item': product})


# ---------------------------------------------------------------------------
# STAFF — Product Categories
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_view_products')
def category_list(request):
    profile = _get_profile(request.user, request)
    categories = ProductCategory.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    can_add    = profile.has_permission('can_add_products') if profile else False
    can_edit   = profile.has_permission('can_edit_products') if profile else False
    can_delete = profile.has_permission('can_delete_products') if profile else False
    return render(request, 'accounts/category_list.html', {
        'categories': categories,
        'can_add': can_add,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })


@login_required(login_url='login')
@requires_permission('can_add_products')
def createCategory(request):
    form = ProductCategoryForm()
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f'Category "{cat.name}" created.')
            return redirect('category_list')
    return render(request, 'accounts/category_form.html', {'form': form, 'action': 'Add'})


@login_required(login_url='login')
@requires_permission('can_edit_products')
def updateCategory(request, pk):
    category = get_object_or_404(ProductCategory, id=pk)
    form = ProductCategoryForm(instance=category)
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated.')
            return redirect('category_list')
    return render(request, 'accounts/category_form.html', {
        'form': form, 'action': 'Edit', 'category': category
    })


@login_required(login_url='login')
@requires_permission('can_delete_products')
def deleteCategory(request, pk):
    category = get_object_or_404(ProductCategory, id=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('category_list')
    return render(request, 'accounts/delete.html', {'item': category})


# ---------------------------------------------------------------------------
# STAFF — Customer detail
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_manage_customers')
def customer(request, pk_test):
    customer_obj = get_object_or_404(
        Customer.objects.select_related('branch', 'state', 'lga'),
        id=pk_test
    )

    if not _is_ceo(request.user):
        branch = _get_branch(request.user)
        if customer_obj.branch != branch:
            raise PermissionDenied("This customer belongs to a different branch.")

    orders_qs = (
        Order.objects
        .filter(customer=customer_obj)
        .prefetch_related('items__product')
        .select_related('payment', 'delivery_state', 'delivery_lga')
        .order_by('-date_create')
    )
    orders_page = _paginate(request, orders_qs)

    return render(request, 'accounts/customer.html', {
        'customer': customer_obj,
        'orders_page': orders_page,
        'order_count': orders_qs.count(),
    })


@login_required(login_url='login')
def profile(request):
    return render(request, 'accounts/profile.html', {'user_profile': _get_profile(request.user, request)})


# ---------------------------------------------------------------------------
# Branch management (CEO only)
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@ceo_only
def branch_list(request):
    branches = Branch.objects.annotate(
        order_count=Count('order'), customer_count=Count('customer')
    ).order_by('name')
    return render(request, 'accounts/branch_list.html', {'branches': branches})


@login_required(login_url='login')
@ceo_only
def createBranch(request):
    form = BranchForm()
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            branch = form.save()
            # Sync UserProfile.branch for the assigned manager
            _sync_manager_profile_branch(branch)
            messages.success(request, 'Branch created.')
            return redirect('branch_list')
    return render(request, 'accounts/branch_form.html', {'form': form, 'action': 'Create'})


@login_required(login_url='login')
@ceo_only
def updateBranch(request, pk):
    branch = get_object_or_404(Branch, id=pk)
    form = BranchForm(instance=branch)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            branch = form.save()
            # Sync UserProfile.branch for the assigned manager
            _sync_manager_profile_branch(branch)
            messages.success(request, 'Branch updated.')
            return redirect('branch_list')
    return render(request, 'accounts/branch_form.html', {'form': form, 'action': 'Update'})


@login_required(login_url='login')
@ceo_only
def deleteBranch(request, pk):
    branch = get_object_or_404(Branch, id=pk)
    if request.method == 'POST':
        branch.delete()
        messages.success(request, 'Branch deleted.')
        return redirect('branch_list')
    return render(request, 'accounts/delete.html', {'item': branch})


# ---------------------------------------------------------------------------
# Role management (CEO only)
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@ceo_only
def role_list(request):
    roles = Role.objects.annotate(user_count=Count('users')).order_by('name')
    return render(request, 'accounts/role_list.html', {'roles': roles})


@ensure_csrf_cookie
@login_required(login_url='login')
@ceo_only
def createRole(request):
    form = RoleForm()
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.created_by = request.user
            role.save()
            messages.success(request, f'Role "{role.name}" created.')
            return redirect('role_list')
    return render(request, 'accounts/role_form.html', {'form': form, 'action': 'Create'})


@ensure_csrf_cookie
@login_required(login_url='login')
@ceo_only
def updateRole(request, pk):
    role = get_object_or_404(Role, id=pk)
    form = RoleForm(instance=role)
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, f'Role "{role.name}" updated.')
            return redirect('role_list')
    return render(request, 'accounts/role_form.html', {'form': form, 'action': 'Update', 'role': role})


@login_required(login_url='login')
@ceo_only
def deleteRole(request, pk):
    role = get_object_or_404(Role, id=pk)
    if request.method == 'POST':
        role.delete()
        messages.success(request, 'Role deleted.')
        return redirect('role_list')
    return render(request, 'accounts/delete.html', {'item': role})


# ---------------------------------------------------------------------------
# User management (CEO only)
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@ceo_only
def user_list(request):
    profiles_qs = (
        UserProfile.objects
        .select_related('user', 'branch')
        .prefetch_related('roles')
        .order_by('user__username')
    )
    return render(request, 'accounts/user_list.html',
                  {'profiles_page': _paginate(request, profiles_qs)})


@login_required(login_url='login')
@ceo_only
def createStaffUser(request):
    if request.method == 'POST':
        form = CreateStaffForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name  = form.cleaned_data.get('last_name', '')
            
            try:
                user.save()
                logger.info('Staff user created: %s', user.username)
                
                # Refresh from DB to ensure profile is loaded (created by signal)
                user.refresh_from_db()
                
                profile = user.profile
                profile.branch = form.cleaned_data.get('branch')
                profile.is_ceo = form.cleaned_data.get('is_ceo', False)
                profile.save()
                
                roles = form.cleaned_data.get('roles', [])
                profile.roles.set(roles)
                
                messages.success(request, f'Staff user "{user.username}" created.')
                return redirect('user_list')
                
            except IntegrityError as e:
                logger.error('IntegrityError creating user: %s', str(e))
                messages.error(request, f'Error creating user: A user with this email or username already exists.')
                form.add_error('username', 'A user with this username or email already exists.')
            except Exception as e:
                logger.error('Unexpected error creating user: %s', str(e), exc_info=True)
                messages.error(request, f'Unexpected error: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CreateStaffForm()
    
    return render(request, 'accounts/staff_form.html', {'form': form, 'action': 'Create'})


@login_required(login_url='login')
@ceo_only
def editUserRoles(request, pk):
    profile = get_object_or_404(UserProfile, id=pk)
    form = EditUserRolesForm(instance=profile)
    if request.method == 'POST':
        form = EditUserRolesForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f'Roles updated for {profile.user.username}.')
            return redirect('user_list')
    return render(request, 'accounts/staff_form.html',
                  {'form': form, 'action': 'Edit Roles for', 'target_user': profile.user})


@login_required(login_url='login')
@ceo_only
def deleteUser(request, pk):
    target_user = get_object_or_404(User, id=pk)

    # Block self-deletion and deletion of other CEO accounts
    target_profile = _get_profile(target_user)
    if target_user == request.user or (target_profile and target_profile.is_ceo):
        raise PermissionDenied("CEO accounts cannot be deleted.")

    if request.method == 'POST':
        target_user.delete()
        messages.success(request, 'User deleted.')
        return redirect('user_list')
    return render(request, 'accounts/delete.html', {'item': target_user})


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def notifications_view(request):
    """Mark all as read when page is visited, then display all."""
    notifs = request.user.notifications.all().order_by('-created_at')
    # Mark all unread as read
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'accounts/notifications.html', {
        'notifications': notifs,
    })


@login_required(login_url='login')
@requires_permission('can_view_reports')
def most_ordered_products(request):
    if _is_ceo(request.user):
        qs = (Product.objects.select_related('branch')
              .annotate(order_count=Count('orderitem'))
              .order_by('-order_count'))
    else:
        branch = _get_branch(request.user)
        qs = (Product.objects.filter(branch=branch)
              .annotate(order_count=Count('orderitem'))
              .order_by('-order_count'))
    return render(request, 'accounts/most_ordered_products.html',
                  {'products_page': _paginate(request, qs)})


def _pdf_response(filename):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response


def _fmt_date(date):
    return date.strftime('%d/%m/%Y') if date else 'N/A'


@login_required(login_url='login')
@requires_permission('can_view_reports')
def delivered_orders_pdf(request):
    if _is_ceo(request.user):
        orders = (Order.objects.filter(status='Delivered')
                  .select_related('branch', 'payment')
                  .prefetch_related('items__product')
                  .order_by('-date_create'))
        title = 'All Branches – Delivered Orders'
    else:
        branch = _get_branch(request.user)
        orders = (Order.objects.filter(status='Delivered', branch=branch)
                  .select_related('payment')
                  .prefetch_related('items__product')
                  .order_by('-date_create'))
        title = f'{branch.name} – Delivered Orders'

    response = _pdf_response('delivered_orders')
    p = canvas.Canvas(response, pagesize=letter)
    p.setTitle(title)
    p.setFont('Helvetica-Bold', 16)
    p.drawString(100, 750, title)
    p.setFont('Helvetica-Bold', 11)
    p.drawString(30, 720, 'Ref')
    p.drawString(110, 720, 'Customer')
    p.drawString(260, 720, 'Date')
    p.drawString(360, 720, 'Items')
    p.drawString(500, 720, 'Amount (N)')

    y = 700
    grand = Decimal('0')
    for order in orders:
        amt = order.payment.amount if hasattr(order, 'payment') else Decimal('0')
        items_str = ', '.join(
            f'{i.quantity}×{i.product}' for i in order.items.all()
        )[:40]
        p.setFont('Helvetica', 10)
        p.drawString(30,  y, str(order.reference))
        p.drawString(110, y, str(order.delivery_name)[:20])
        p.drawString(260, y, _fmt_date(order.date_create))
        p.drawString(360, y, items_str)
        p.drawString(500, y, f'{amt:,.2f}')
        grand += amt
        y -= 18
        if y < 60:
            p.showPage()
            y = 750

    p.setFont('Helvetica-Bold', 12)
    p.drawString(30, y - 20, f'Total: N{grand:,.2f}')
    p.showPage()
    p.save()
    return response

# ---------------------------------------------------------------------------
# INVENTORY MANAGEMENT (CEO only)
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_manage_inventory')
def ingredient_list(request):
    """List all ingredients with stock status."""
    profile = _get_profile(request.user, request)
    is_ceo_user = _is_ceo(request.user)
    
    if is_ceo_user:
        # CEO sees all branches
        ingredients = Ingredient.objects.select_related('branch').order_by('branch__name', 'name')
    else:
        # Manager sees only their branch
        branch = _get_branch(request.user)
        if branch is None:
            return HttpResponse(
                '<h3>You are not assigned to any branch. Contact the CEO.</h3>',
                status=403
            )
        ingredients = Ingredient.objects.filter(branch=branch).order_by('name')
    
    # Annotate low stock count
    low_stock_count = sum(1 for ing in ingredients if ing.is_low)
    
    return render(request, 'accounts/ingredient_list.html', {
        'ingredients': ingredients,
        'low_stock_count': low_stock_count,
        'is_ceo': is_ceo_user,
        'user_profile': profile,
    })


@login_required(login_url='login')
@requires_permission('can_manage_inventory')
def createIngredient(request):
    """Create a new ingredient."""
    branch = _get_branch(request.user)
    is_ceo_user = _is_ceo(request.user)
    
    # Check if there are any branches in the system
    if not Branch.objects.exists():
        messages.error(request, 'No branches found. Please create a branch first before adding ingredients.')
        return redirect('ingredient_list')
    
    # For non-CEO users, verify they have a branch assignment
    if not is_ceo_user and not branch:
        messages.error(request, 'You are not assigned to any branch. Contact the CEO.')
        return redirect('ingredient_list')
    
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        
        if form.is_valid():
            ingredient = form.save(commit=False)
            # For non-CEO users, force their branch
            if not is_ceo_user:
                ingredient.branch = branch
            ingredient.save()
            messages.success(request, f'Ingredient "{ingredient.name}" created.')
            return redirect('ingredient_list')
    else:
        # GET request - initialize form
        initial = {'branch': branch} if not is_ceo_user else {}
        form = IngredientForm(initial=initial)
        
        # For non-CEO users, make branch field readonly instead of disabled
        if not is_ceo_user:
            form.fields['branch'].widget.attrs['readonly'] = True
            form.fields['branch'].widget.attrs['disabled'] = True
    
    return render(request, 'accounts/ingredient_form.html', {
        'form': form,
        'action': 'Add',
        'is_ceo': is_ceo_user,
    })


@login_required(login_url='login')
@requires_permission('can_manage_inventory')
def updateIngredient(request, pk):
    """Update an existing ingredient."""
    ingredient = get_object_or_404(Ingredient, id=pk)
    is_ceo_user = _is_ceo(request.user)
    
    # Verify permission: CEO can edit any, managers only their branch
    if not is_ceo_user:
        branch = _get_branch(request.user)
        if ingredient.branch != branch:
            return HttpResponse(
                '<h3>403 – You can only edit ingredients in your branch.</h3>',
                status=403
            )
    
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        
        if form.is_valid():
            updated_ingredient = form.save(commit=False)
            # For non-CEO users, ensure branch doesn't change
            if not is_ceo_user:
                updated_ingredient.branch = ingredient.branch
            updated_ingredient.save()
            messages.success(request, f'Ingredient "{ingredient.name}" updated.')
            return redirect('ingredient_list')
    else:
        # GET request - initialize form with instance
        form = IngredientForm(instance=ingredient)
        
        # For non-CEO users, make branch field readonly
        if not is_ceo_user:
            form.fields['branch'].widget.attrs['readonly'] = True
            form.fields['branch'].widget.attrs['disabled'] = True
    
    return render(request, 'accounts/ingredient_form.html', {
        'form': form,
        'action': 'Edit',
        'ingredient': ingredient,
        'is_ceo': is_ceo_user,
    })


@login_required(login_url='login')
@requires_permission('can_manage_inventory')
def deleteIngredient(request, pk):
    """Delete an ingredient."""
    ingredient = get_object_or_404(Ingredient, id=pk)
    is_ceo_user = _is_ceo(request.user)
    
    # Verify permission: CEO can delete any, managers only their branch
    if not is_ceo_user:
        branch = _get_branch(request.user)
        if ingredient.branch != branch:
            return HttpResponse(
                '<h3>403 – You can only delete ingredients in your branch.</h3>',
                status=403
            )
    
    if request.method == 'POST':
        name = ingredient.name
        ingredient.delete()
        messages.success(request, f'Ingredient "{name}" deleted.')
        return redirect('ingredient_list')
    
    return render(request, 'accounts/delete.html', {'item': ingredient})


# ---------------------------------------------------------------------------
# INVENTORY CONSUMPTION REPORTS
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_manage_inventory')
def ingredient_consumption_history(request):
    """View ingredient consumption history with date filtering."""
    profile = _get_profile(request.user, request)
    is_ceo_user = _is_ceo(request.user)
    
    # Date filters
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    ingredient_id = request.GET.get('ingredient', '')
    
    if is_ceo_user:
        consumptions_qs = IngredientConsumption.objects.select_related(
            'ingredient__branch', 'order', 'consumed_by'
        )
    else:
        branch = _get_branch(request.user)
        if not branch:
            raise PermissionDenied("You are not assigned to any branch.")
        consumptions_qs = IngredientConsumption.objects.filter(
            ingredient__branch=branch
        ).select_related('ingredient', 'order', 'consumed_by')
    
    # Apply filters
    if from_date:
        consumptions_qs = consumptions_qs.filter(consumed_at__gte=from_date)
    if to_date:
        consumptions_qs = consumptions_qs.filter(consumed_at__lte=to_date)
    if ingredient_id:
        consumptions_qs = consumptions_qs.filter(ingredient_id=ingredient_id)
    
    consumptions_qs = consumptions_qs.order_by('-consumed_at')
    
    # Get available ingredients for filter dropdown
    if is_ceo_user:
        ingredients = Ingredient.objects.select_related('branch').order_by('branch__name', 'name')
    else:
        branch = _get_branch(request.user)
        ingredients = Ingredient.objects.filter(branch=branch).order_by('name')
    
    # Calculate summary
    summary = consumptions_qs.aggregate(
        total_records=Count('id'),
        total_consumption=Sum('quantity_used')
    )
    
    consumptions_page = _paginate(request, consumptions_qs, page_size=50)
    
    return render(request, 'accounts/ingredient_consumption_history.html', {
        'consumptions_page': consumptions_page,
        'ingredients': ingredients,
        'from_date': from_date,
        'to_date': to_date,
        'selected_ingredient': ingredient_id,
        'summary': summary,
        'is_ceo': is_ceo_user,
        'user_profile': profile,
    })


# ---------------------------------------------------------------------------
# PAYMENT & REVENUE REPORTS
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@requires_permission('can_view_reports')
def payment_reports(request):
    """
    Comprehensive payment/revenue reports with filtering by:
    - Date range
    - Branch
    - Delivery location (state/LGA)
    - Payment method
    """
    profile = _get_profile(request.user, request)
    is_ceo_user = _is_ceo(request.user)
    
    # Filters from request
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    branch_id = request.GET.get('branch', '')
    state_id = request.GET.get('state', '')
    lga_id = request.GET.get('lga', '')
    payment_method = request.GET.get('payment_method', '')
    
    # Base queryset - only paid orders
    payments_qs = Payment.objects.filter(
        status='Paid'
    ).select_related(
        'order__branch',
        'order__delivery_state',
        'order__delivery_lga',
        'order__customer'
    )
    
    # Branch filter
    if is_ceo_user:
        if branch_id:
            payments_qs = payments_qs.filter(order__branch_id=branch_id)
    else:
        branch = _get_branch(request.user)
        if not branch:
            raise PermissionDenied("You are not assigned to any branch.")
        payments_qs = payments_qs.filter(order__branch=branch)
    
    # Date filters
    if from_date:
        payments_qs = payments_qs.filter(paid_at__gte=from_date)
    if to_date:
        payments_qs = payments_qs.filter(paid_at__lte=to_date)
    
    # Location filters
    if state_id:
        payments_qs = payments_qs.filter(order__delivery_state_id=state_id)
    if lga_id:
        payments_qs = payments_qs.filter(order__delivery_lga_id=lga_id)
    
    # Payment method filter
    if payment_method:
        payments_qs = payments_qs.filter(method=payment_method)
    
    # Revenue summary
    from django.db.models import Avg
    revenue_summary = payments_qs.aggregate(
        total_revenue=Sum('amount'),
        total_transactions=Count('id'),
        avg_transaction=Avg('amount')
    )
    
    # Handle None values when no payments exist
    if revenue_summary['total_revenue'] is None:
        revenue_summary['total_revenue'] = Decimal('0.00')
    if revenue_summary['avg_transaction'] is None:
        revenue_summary['avg_transaction'] = Decimal('0.00')
    
    # Revenue by branch (CEO only)
    revenue_by_branch = None
    if is_ceo_user:
        revenue_by_branch = (
            payments_qs.values('order__branch__name')
            .annotate(
                revenue=Sum('amount'),
                order_count=Count('id')
            )
            .order_by('-revenue')
        )
    
    # Revenue by location (state)
    revenue_by_state = (
        payments_qs.values('order__delivery_state__name')
        .annotate(
            revenue=Sum('amount'),
            order_count=Count('id')
        )
        .order_by('-revenue')
    )
    
    # Revenue by payment method
    revenue_by_method = (
        payments_qs.values('method')
        .annotate(
            revenue=Sum('amount'),
            order_count=Count('id')
        )
        .order_by('-revenue')
    )
    
    # Get filter options
    branches = Branch.objects.all() if is_ceo_user else None
    states = State.objects.all()
    lgas = LGA.objects.filter(state_id=state_id) if state_id else LGA.objects.none()
    payment_methods = Payment.PAYMENT_METHOD_CHOICES
    
    payments_page = _paginate(request, payments_qs.order_by('-paid_at'), page_size=25)
    
    return render(request, 'accounts/payment_reports.html', {
        'payments_page': payments_page,
        'revenue_summary': revenue_summary,
        'revenue_by_branch': revenue_by_branch,
        'revenue_by_state': revenue_by_state,
        'revenue_by_method': revenue_by_method,
        'branches': branches,
        'states': states,
        'lgas': lgas,
        'payment_methods': payment_methods,
        'filters': {
            'from_date': from_date,
            'to_date': to_date,
            'branch': branch_id,
            'state': state_id,
            'lga': lga_id,
            'payment_method': payment_method,
        },
        'is_ceo': is_ceo_user,
        'user_profile': profile,
    })


# ---------------------------------------------------------------------------
# CUSTOM ERROR HANDLERS
# ---------------------------------------------------------------------------

def custom_403(request, exception=None):
    """Custom 403 Forbidden error page."""
    return render(request, '403.html', status=403)


def custom_404(request, exception=None):
    """Custom 404 Not Found error page."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 Internal Server Error page."""
    return render(request, '500.html', status=500)
=======
from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .forms import CustomerForm, OrderForm, CreateUserForm
from django.contrib import messages
from django.contrib.auth.models import Group

# from django.http import HttpResponse
# from django.db.models import fields
# from crm1 import accounts
from .filters import OrderFilter
from .decorators import unauthenticated_user,allowed_users,admin_only
from .models import *
# Create your views here.

# Register

'''@unauthenticated_user
def registerPage(request):
    form = CreateUserForm()
    if request.method == "POST":
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                #username=form.cleaned_data.get('username')
            # group =group.objects.get(name='customers')
            # User.groups.add(group)
            # Customer.objects.create(user=User)
            return redirect('login')
    context = {'form': form}
    return render(request, 'accounts/register.html', context)'''
#@unauthenticated_user
#@admin_only
@unauthenticated_user
def registerPage(request):
    print("In registerPage view")
    form = CreateUserForm()
    if request.method == "POST":
        print("Handling POST request")
        form = CreateUserForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            user = form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            name = form.cleaned_data.get('username')  # Assuming you want to use the username as the name
            
            #TAKEN TO SIGNALS.PY
            # group = Group.objects.get(name='customers')
            # user.groups.add(group)
            
            # Customer.objects.create(
            #     user=user,
            #     # name=user.username
            #     name=name,
            #     email=email
            # )
            
            messages.success(request, 'Account created for ' + username)
            return redirect('login')
    else:
        print("Handling GET request")
        
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

# Login
@unauthenticated_user
def loginPage(request):
    if request.method == "POST":
         username = request.POST.get('username')
         password = request.POST.get('password')
         user = authenticate(request, username=username, password=password)
         if user is not None:
                login(request, user)
                messages.info(request, "login successful!")
                return redirect('home')
         else:
                messages.info(request, 'username OR password incorrect')
                return render(request, 'accounts/login.html')
    context = {}
    return render(request, 'accounts/login.html', context)

#logout
def logoutUser(request):
    logout(request)
    messages.success(request, "Logout success!")
    return redirect("login")

# Home page
@login_required(login_url='login')#prevent unauthorised user access
#@allowed_users(allowed_roles=['admins'])
@admin_only
def home(request):
    orders = Order.objects.all()
    # orders = Order.objects.all()[:5]
    customers = Customer.objects.all()
    total_orders = orders.count()
    total_customers = customers.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    context = {'orders': orders,
               'customers': customers,
               'total_orders': total_orders,
               'total_customers': total_customers,
               'delivered': delivered,
               'pending': pending
               }

    return render(request, 'accounts/dashboard.html', context)

@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['customers'])
def userPage(request):
    orders=request.user.customer.order_set.all()
    total_orders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    #print('oders',orders)
    context={'orders':orders,
             'total_orders': total_orders,
              'delivered': delivered,
               'pending': pending}
    return render(request, 'accounts/user.html',context)


@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['admins'])
def products(request):
    products = Product.objects.all()
    return render(request, 'accounts/products.html', {'products': products})


@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['admins'])
def customer(request, pk_test):
   # try:
    # customer=Customer.objects.get(id=pk_test)
   # except Customer.DoesNotExist:
    # Handle the case where the customer does not exist
    # customer = None
    customer = get_object_or_404(Customer, id=pk_test)
    orders = customer.order_set.all()
    order_count = orders.count()
    myFilter = OrderFilter(request.GET, queryset=orders)
    orders = myFilter.qs
    context = {'customer': customer,
               'orders': orders,
               'order_count': order_count,
               'myFilter': myFilter}
    # Debugging output
    # print(f"Customer: {customer}")
    # print(f"Orders: {orders}")
    # print(f"Order count: {order_count}")
    # print(f"Filtered orders: {myFilter.qs}")
    return render(request, 'accounts/customer.html', context)

@login_required(login_url='login')#prevent unauthorised user access
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required(login_url='login')#prevent unauthorised user access
def createOrder(request, pk):
    OrderFormSet = inlineformset_factory(
        Customer, Order, fields=('product', 'status'), extra=10)
    customer = Customer.objects.get(id=pk)
    # order=Order.objects.get(id=pk)
    # queryset=Order.object.none()// clear the pre filled form
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    # formset=OrderFormSet(instance=order)
    # form=OrderForm(initial={'customer':customer})

    if request.method == 'POST':
       # form=OrderForm(request.POST)
        # print('Printing Post:',request.POST)
        formset = OrderFormSet(request.POST, instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect('/')
    # context={'form':form,
    context = {'formset': formset
               # 'customer':customer
               }
    return render(request, 'accounts/createOrder_form.html', context)

@login_required(login_url='login')#prevent unauthorised user access
def updateOrder(request, pk):
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        # print('Printing Post:',request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    context = {'form': form}
    return render(request, 'accounts/order_form.html', context)

@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['admins'])
def deleteOrder(request, pk):
    order = Order.objects.get(id=pk)
    if request.method == "POST":
        order.delete()
        return redirect('/')
    context = {'item': order}
    return render(request, 'accounts/delete.html', context)

@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['customers'])
def accountSettings(request):
    customer=request.user.customer
    form=CustomerForm(instance=customer)
    if request.method == 'POST':
        form=CustomerForm(request.POST,request.FILES, instance=customer)
        if form.is_valid():
            form.save()
    context = {'form':form}
    return render(request, 'accounts/account_settings.html', context)
>>>>>>> bda2651b2d659a1fa8eddca086b4a11b677495ca
