"""
Test suite for the Food Vendor CRM.

Coverage:
  1. Model layer       — __str__, validators, has_permission, role_names
  2. Signal            — UserProfile auto-created on User save
  3. Role permissions  — has_permission across single/multiple roles, CEO bypass
  4. Decorators        — unauthenticated_user, ceo_only, requires_permission,
                         manager_or_ceo, admin_only routing
  5. Views (auth)      — register, login, logout
  6. Views (staff)     — dashboard, view_all_orders, products, customer detail
  7. Branch scoping    — manager sees only their branch; CEO sees all
  8. CEO management    — role CRUD, user CRUD, branch CRUD
  9. Input validation  — phone, email, price validators
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse

from .models import Branch, Customer, Order, Product, Role, Tag, UserProfile


# ---------------------------------------------------------------------------
# Helpers — factory functions keep each test clean and DRY
# ---------------------------------------------------------------------------

def make_branch(name='Main Branch', location='Lagos'):
    return Branch.objects.create(name=name, location=location)


def make_role(name='Cashier', **perms):
    defaults = dict(
        can_manage_orders=False,
        can_delete_orders=False,
        can_manage_products=False,
        can_manage_customers=False,
        can_view_reports=False,
        can_manage_users=False,
        can_manage_branches=False,
    )
    defaults.update(perms)
    return Role.objects.create(name=name, **defaults)


def make_user(username, password='TestPass123!', is_superuser=False):
    user = User.objects.create_user(
        username=username,
        password=password,
        email=f'{username}@test.com',
    )
    if is_superuser:
        user.is_superuser = True
        user.is_staff = True
        user.save()
    return user


def make_staff(username, branch=None, is_ceo=False, roles=None, password='TestPass123!'):
    """Create a user, set up their UserProfile as staff."""
    user = make_user(username, password)
    profile = user.profile          # created by signal
    profile.branch = branch
    profile.is_ceo = is_ceo
    profile.save()
    if roles:
        profile.roles.set(roles)
    return user


def make_customer(name, branch=None, user=None):
    return Customer.objects.create(name=name, branch=branch, user=user)


def make_product(name, branch=None, price='500.00', category='Mains'):
    return Product.objects.create(
        name=name, branch=branch,
        price=Decimal(price), category=category
    )


def make_order(customer, product, branch=None, status='Pending'):
    return Order.objects.create(
        customer=customer, product=product,
        branch=branch, status=status
    )


# ===========================================================================
# 1. MODEL TESTS
# ===========================================================================

class RoleModelTests(TestCase):

    def test_str_returns_name(self):
        role = make_role('Floor Supervisor')
        self.assertEqual(str(role), 'Floor Supervisor')

    def test_permission_summary_no_permissions(self):
        role = make_role('Empty Role')
        self.assertEqual(role.permission_summary(), 'No permissions')

    def test_permission_summary_with_permissions(self):
        role = make_role('Senior Cashier', can_manage_orders=True, can_view_reports=True)
        summary = role.permission_summary()
        self.assertIn('Manage Orders', summary)
        self.assertIn('View Reports', summary)
        self.assertNotIn('Delete Orders', summary)


class UserProfileModelTests(TestCase):

    def setUp(self):
        self.branch = make_branch()
        self.user = make_user('staffuser')
        self.profile = self.user.profile

    def test_profile_auto_created_by_signal(self):
        self.assertIsNotNone(self.profile)
        self.assertIsInstance(self.profile, UserProfile)

    def test_str_contains_username(self):
        self.assertIn('staffuser', str(self.profile))

    def test_role_names_no_roles(self):
        self.assertEqual(self.profile.role_names(), 'No roles')

    def test_role_names_with_roles(self):
        r1 = make_role('Cashier')
        r2 = make_role('Supervisor')
        self.profile.roles.add(r1, r2)
        names = self.profile.role_names()
        self.assertIn('Cashier', names)
        self.assertIn('Supervisor', names)

    def test_ceo_flag_overrides_all_permissions(self):
        self.profile.is_ceo = True
        self.profile.save()
        for perm in (
            'can_manage_orders', 'can_delete_orders', 'can_manage_products',
            'can_manage_customers', 'can_view_reports',
            'can_manage_users', 'can_manage_branches',
        ):
            self.assertTrue(self.profile.has_permission(perm))

    def test_superuser_bypasses_permission_check(self):
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.profile.has_permission('can_delete_orders'))


class BranchModelTests(TestCase):

    def test_str_returns_name(self):
        branch = make_branch('Ikeja Branch')
        self.assertEqual(str(branch), 'Ikeja Branch')


class CustomerModelTests(TestCase):

    def test_str_returns_name(self):
        c = Customer.objects.create(name='Ada Okafor')
        self.assertEqual(str(c), 'Ada Okafor')

    def test_str_fallback_when_name_is_none(self):
        c = Customer.objects.create(name=None)
        self.assertIn('Customer #', str(c))

    def test_valid_phone_passes_validation(self):
        c = Customer(name='Test', phone='+2348012345678')
        c.full_clean()   # should not raise

    def test_invalid_phone_fails_validation(self):
        c = Customer(name='Test', phone='not-a-phone')
        with self.assertRaises(ValidationError):
            c.full_clean()

    def test_valid_email_passes_validation(self):
        c = Customer(name='Test', email='test@example.com')
        c.full_clean()

    def test_invalid_email_fails_validation(self):
        c = Customer(name='Test', email='not-an-email')
        with self.assertRaises(ValidationError):
            c.full_clean()


class ProductModelTests(TestCase):

    def test_str_returns_name(self):
        p = make_product('Jollof Rice')
        self.assertEqual(str(p), 'Jollof Rice')

    def test_negative_price_fails_validation(self):
        p = Product(name='Bad Item', price=Decimal('-1.00'))
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_zero_price_passes_validation(self):
        p = Product(name='Free Item', price=Decimal('0.00'))
        p.full_clean()


class OrderModelTests(TestCase):

    def test_str_returns_product_name(self):
        branch = make_branch()
        customer = make_customer('Emeka', branch)
        product = make_product('Egusi Soup', branch)
        order = make_order(customer, product, branch)
        self.assertEqual(str(order), 'Egusi Soup')

    def test_str_fallback_with_no_product(self):
        customer = make_customer('Emeka')
        order = Order.objects.create(customer=customer, product=None)
        self.assertEqual(str(order), 'No Product')


# ===========================================================================
# 2. ROLE PERMISSION LOGIC
# ===========================================================================

class RolePermissionTests(TestCase):

    def setUp(self):
        self.branch = make_branch()

    def test_no_roles_denies_all_permissions(self):
        user = make_staff('noroler', branch=self.branch)
        for perm in ('can_manage_orders', 'can_view_reports', 'can_delete_orders'):
            self.assertFalse(user.profile.has_permission(perm))

    def test_single_role_grants_its_permissions(self):
        role = make_role('Order Manager', can_manage_orders=True)
        user = make_staff('mgr', branch=self.branch, roles=[role])
        self.assertTrue(user.profile.has_permission('can_manage_orders'))
        self.assertFalse(user.profile.has_permission('can_delete_orders'))

    def test_multiple_roles_union_permissions(self):
        """A user with two roles has the union of both roles' permissions."""
        r1 = make_role('Role A', can_manage_orders=True)
        r2 = make_role('Role B', can_view_reports=True)
        user = make_staff('multiroler', branch=self.branch, roles=[r1, r2])
        self.assertTrue(user.profile.has_permission('can_manage_orders'))
        self.assertTrue(user.profile.has_permission('can_view_reports'))
        self.assertFalse(user.profile.has_permission('can_delete_orders'))

    def test_ceo_has_all_permissions_without_any_role(self):
        user = make_staff('boss', branch=self.branch, is_ceo=True)
        for perm in (
            'can_manage_orders', 'can_delete_orders', 'can_manage_products',
            'can_manage_customers', 'can_view_reports',
            'can_manage_users', 'can_manage_branches',
        ):
            self.assertTrue(user.profile.has_permission(perm))


# ===========================================================================
# 3. VIEW TESTS — Auth
# ===========================================================================

class AuthViewTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_login_page_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_register_page_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_successful_login_redirects_to_home(self):
        branch = make_branch()
        user = make_staff('logintest', branch=branch, is_ceo=True)
        response = self.client.post(reverse('login'), {
            'username': 'logintest',
            'password': 'TestPass123!',
        })
        self.assertRedirects(response, reverse('home'))

    def test_wrong_password_stays_on_login(self):
        make_user('badlogin')
        response = self.client.post(reverse('login'), {
            'username': 'badlogin',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects_to_login(self):
        user = make_user('logoutuser')
        self.client.force_login(user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_authenticated_user_cannot_access_register(self):
        """@unauthenticated_user should redirect logged-in users to home."""
        branch = make_branch()
        user = make_staff('alreadyin', branch=branch, is_ceo=True)
        self.client.force_login(user)
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('home'))

    def test_unauthenticated_user_redirected_from_home(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")


# ===========================================================================
# 4. VIEW TESTS — Dashboard & Branch scoping
# ===========================================================================

class DashboardViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.branch_a = make_branch('Branch A', 'Lagos')
        self.branch_b = make_branch('Branch B', 'Abuja')

        # CEO
        self.ceo = make_staff('ceo', is_ceo=True)

        # Manager assigned to Branch A only
        self.manager = make_staff('manager', branch=self.branch_a)

        # Products, customers, orders in each branch
        self.prod_a = make_product('Jollof', self.branch_a)
        self.prod_b = make_product('Fried Rice', self.branch_b)
        self.cust_a = make_customer('Ada', self.branch_a)
        self.cust_b = make_customer('Bola', self.branch_b)
        make_order(self.cust_a, self.prod_a, self.branch_a)
        make_order(self.cust_b, self.prod_b, self.branch_b)

    def test_ceo_dashboard_loads(self):
        self.client.force_login(self.ceo)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_ceo_sees_all_branches_in_context(self):
        self.client.force_login(self.ceo)
        response = self.client.get(reverse('home'))
        self.assertIn('Branch A', response.content.decode())
        self.assertIn('Branch B', response.content.decode())

    def test_manager_dashboard_loads(self):
        role = make_role('Manager Role', can_manage_orders=True, can_manage_customers=True)
        self.manager.profile.roles.add(role)
        self.client.force_login(self.manager)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_manager_sees_only_own_branch_customers(self):
        role = make_role('Manager Role 2', can_manage_customers=True)
        self.manager.profile.roles.add(role)
        self.client.force_login(self.manager)
        response = self.client.get(reverse('home'))
        content = response.content.decode()
        self.assertIn('Ada', content)       # Branch A customer
        self.assertNotIn('Bola', content)   # Branch B customer

    def test_manager_without_branch_gets_403(self):
        no_branch_manager = make_staff('nobranch')
        role = make_role('Some Role', can_manage_orders=True)
        no_branch_manager.profile.roles.add(role)
        self.client.force_login(no_branch_manager)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 403)


# ===========================================================================
# 5. VIEW TESTS — Branch scoping on orders & customers
# ===========================================================================

class BranchScopingTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.branch_a = make_branch('Lagos')
        self.branch_b = make_branch('Abuja')

        order_role = make_role('Order Staff',
            can_manage_orders=True,
            can_delete_orders=True,
            can_manage_customers=True,
        )

        self.manager_a = make_staff('mgr_a', branch=self.branch_a, roles=[order_role])
        self.ceo = make_staff('ceo', is_ceo=True)

        self.cust_a = make_customer('Amara', self.branch_a)
        self.cust_b = make_customer('Ngozi', self.branch_b)
        self.prod_a = make_product('Suya', self.branch_a)
        self.prod_b = make_product('Pepper Soup', self.branch_b)
        self.order_a = make_order(self.cust_a, self.prod_a, self.branch_a)
        self.order_b = make_order(self.cust_b, self.prod_b, self.branch_b)

    def test_manager_cannot_view_other_branch_customer(self):
        self.client.force_login(self.manager_a)
        response = self.client.get(reverse('customer', args=[self.cust_b.id]))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_view_own_branch_customer(self):
        self.client.force_login(self.manager_a)
        response = self.client.get(reverse('customer', args=[self.cust_a.id]))
        self.assertEqual(response.status_code, 200)

    def test_ceo_can_view_any_branch_customer(self):
        self.client.force_login(self.ceo)
        response = self.client.get(reverse('customer', args=[self.cust_b.id]))
        self.assertEqual(response.status_code, 200)

    def test_manager_cannot_delete_other_branch_order(self):
        self.client.force_login(self.manager_a)
        response = self.client.post(reverse('delete_order', args=[self.order_b.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Order.objects.filter(id=self.order_b.id).exists())

    def test_manager_can_delete_own_branch_order(self):
        self.client.force_login(self.manager_a)
        response = self.client.post(reverse('delete_order', args=[self.order_a.id]))
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Order.objects.filter(id=self.order_a.id).exists())

    def test_view_all_orders_manager_scoped(self):
        self.client.force_login(self.manager_a)
        response = self.client.get(reverse('view_all_orders'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Suya', content)          # own branch product
        self.assertNotIn('Pepper Soup', content) # other branch product

    def test_view_all_orders_ceo_sees_all(self):
        self.client.force_login(self.ceo)
        response = self.client.get(reverse('view_all_orders'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Suya', content)
        self.assertIn('Pepper Soup', content)


# ===========================================================================
# 6. VIEW TESTS — CEO management (roles, users, branches)
# ===========================================================================

class CEOManagementViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.ceo = make_staff('ceo_boss', is_ceo=True)
        self.branch = make_branch('Test Branch')

    # --- Role CRUD ---

    def test_role_list_accessible_by_ceo(self):
        self.client.force_login(self.ceo)
        response = self.client.get(reverse('role_list'))
        self.assertEqual(response.status_code, 200)

    def test_role_list_blocked_for_non_ceo(self):
        plain_user = make_staff('plain', branch=self.branch)
        self.client.force_login(plain_user)
        response = self.client.get(reverse('role_list'))
        self.assertEqual(response.status_code, 403)

    def test_create_role_post(self):
        self.client.force_login(self.ceo)
        response = self.client.post(reverse('create_role'), {
            'name': 'Waiter',
            'description': 'Serves food',
            'can_manage_orders': True,
            'can_delete_orders': False,
            'can_manage_products': False,
            'can_manage_customers': True,
            'can_view_reports': False,
            'can_manage_users': False,
            'can_manage_branches': False,
        })
        self.assertRedirects(response, reverse('role_list'))
        self.assertTrue(Role.objects.filter(name='Waiter').exists())

    def test_delete_role(self):
        role = make_role('Temp Role')
        self.client.force_login(self.ceo)
        response = self.client.post(reverse('delete_role', args=[role.id]))
        self.assertRedirects(response, reverse('role_list'))
        self.assertFalse(Role.objects.filter(id=role.id).exists())

    # --- Branch CRUD ---

    def test_branch_list_accessible_by_ceo(self):
        self.client.force_login(self.ceo)
        response = self.client.get(reverse('branch_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_branch_post(self):
        self.client.force_login(self.ceo)
        response = self.client.post(reverse('create_branch'), {
            'name': 'New Branch',
            'location': 'Port Harcourt',
            'phone': '',
        })
        self.assertRedirects(response, reverse('branch_list'))
        self.assertTrue(Branch.objects.filter(name='New Branch').exists())

    def test_delete_branch(self):
        branch = make_branch('Temp Branch')
        self.client.force_login(self.ceo)
        response = self.client.post(reverse('delete_branch', args=[branch.id]))
        self.assertRedirects(response, reverse('branch_list'))
        self.assertFalse(Branch.objects.filter(id=branch.id).exists())

    # --- User management ---

    def test_user_list_accessible_by_ceo(self):
        self.client.force_login(self.ceo)
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_list_blocked_for_non_ceo(self):
        plain = make_staff('plain2', branch=self.branch)
        self.client.force_login(plain)
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 403)

    def test_create_staff_user(self):
        role = make_role('Cashier Role')
        self.client.force_login(self.ceo)
        response = self.client.post(reverse('create_staff_user'), {
            'username': 'newstaff',
            'email': 'newstaff@test.com',
            'first_name': 'New',
            'last_name': 'Staff',
            'password1': 'StrongPass99!',
            'password2': 'StrongPass99!',
            'branch': self.branch.id,
            'roles': [role.id],
            'is_ceo': False,
        })
        self.assertRedirects(response, reverse('user_list'))
        self.assertTrue(User.objects.filter(username='newstaff').exists())
        new_user = User.objects.get(username='newstaff')
        self.assertIn(role, new_user.profile.roles.all())
        self.assertEqual(new_user.profile.branch, self.branch)


# ===========================================================================
# 7. VIEW TESTS — Permission decorator enforcement
# ===========================================================================

class PermissionDecoratorTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.branch = make_branch()

    def test_requires_permission_blocks_user_without_flag(self):
        """A staff user with no can_manage_products role cannot access products."""
        role = make_role('No Products Role', can_manage_products=False)
        user = make_staff('blocked', branch=self.branch, roles=[role])
        self.client.force_login(user)
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 403)

    def test_requires_permission_allows_user_with_flag(self):
        role = make_role('Product Staff', can_manage_products=True)
        user = make_staff('allowed', branch=self.branch, roles=[role])
        self.client.force_login(user)
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)

    def test_ceo_bypasses_requires_permission(self):
        ceo = make_staff('ceobypass', is_ceo=True)
        self.client.force_login(ceo)
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)

    def test_customer_portal_blocked_for_staff(self):
        """Staff users (with profile + roles) cannot access the customer portal."""
        role = make_role('Any Role', can_manage_orders=True)
        staff = make_staff('staffuser', branch=self.branch, roles=[role])
        self.client.force_login(staff)
        response = self.client.get(reverse('user-page'))
        self.assertEqual(response.status_code, 403)

    def test_customer_portal_accessible_for_plain_customer(self):
        """Self-registered users (bare profile, no roles) can access the customer portal."""
        plain = make_user('plainuser')
        # Manually create a customer record since we skipped the register view
        Customer.objects.create(user=plain, name='Plain User')
        self.client.force_login(plain)
        response = self.client.get(reverse('user-page'))
        self.assertEqual(response.status_code, 200)


# ===========================================================================
# 8. SIGNAL TESTS
# ===========================================================================

class SignalTests(TestCase):

    def test_user_profile_created_on_new_user(self):
        user = User.objects.create_user(username='sigtest', password='pass')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_profile_not_duplicated_on_user_save(self):
        user = User.objects.create_user(username='dup', password='pass')
        user.email = 'dup@test.com'
        user.save()   # second save — should not create a second profile
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

    def test_new_profile_defaults_to_no_ceo(self):
        user = User.objects.create_user(username='newdefault', password='pass')
        self.assertFalse(user.profile.is_ceo)

    def test_new_profile_has_no_roles(self):
        user = User.objects.create_user(username='noroles', password='pass')
        self.assertEqual(user.profile.roles.count(), 0)
