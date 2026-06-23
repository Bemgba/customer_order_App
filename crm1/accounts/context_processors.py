def user_profile(request):
    """
    Inject the current user's UserProfile, unread notification count,
    and company branding into every template context automatically.
    """
    from django.conf import settings as django_settings

    def _brand(key, default):
        return getattr(django_settings, key, default)

    branding = {
        'COMPANY_NAME':       _brand('COMPANY_NAME',       'G & G Divine Favour Catering Ventures'),
        'COMPANY_SHORT_NAME': _brand('COMPANY_SHORT_NAME', 'G&G Catering'),
        'COMPANY_TAGLINE':    _brand('COMPANY_TAGLINE',    'Fresh meals, delivered with love.'),
    }

    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Exception:
            # Ensure a UserProfile exists for older users created before the signal
            try:
                from .models import UserProfile
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
            except Exception:
                profile = None

        try:
            unread_notifications = request.user.notifications.filter(is_read=False).count()
        except Exception:
            unread_notifications = 0

        # Check granular permissions
        # Superusers and CEOs should always have access to everything
        try:
            if request.user.is_superuser or (profile and profile.is_ceo):
                # CEO/Superuser has all permissions
                can_view_products = True
                can_add_products = True
                can_edit_products = True
                can_delete_products = True
                can_manage_orders = True
                can_delete_orders = True
                can_manage_customers = True
                can_manage_inventory = True
                can_view_reports = True
                can_manage_users = True
                can_manage_branches = True
                can_confirm_delivery = True
                can_assign_dispatcher = True
            elif profile:
                # Check each permission individually
                can_view_products = profile.has_permission('can_view_products')
                can_add_products = profile.has_permission('can_add_products')
                can_edit_products = profile.has_permission('can_edit_products')
                can_delete_products = profile.has_permission('can_delete_products')
                can_manage_orders = profile.has_permission('can_manage_orders')
                can_delete_orders = profile.has_permission('can_delete_orders')
                can_manage_customers = profile.has_permission('can_manage_customers')
                can_manage_inventory = profile.has_permission('can_manage_inventory')
                can_view_reports = profile.has_permission('can_view_reports')
                can_manage_users = profile.has_permission('can_manage_users')
                can_manage_branches = profile.has_permission('can_manage_branches')
                can_confirm_delivery = profile.has_permission('can_confirm_delivery')
                can_assign_dispatcher = profile.has_permission('can_assign_dispatcher')
            else:
                # No profile = no permissions
                can_view_products = False
                can_add_products = False
                can_edit_products = False
                can_delete_products = False
                can_manage_orders = False
                can_delete_orders = False
                can_manage_customers = False
                can_manage_inventory = False
                can_view_reports = False
                can_manage_users = False
                can_manage_branches = False
                can_confirm_delivery = False
                can_assign_dispatcher = False
        except Exception:
            # Error = no permissions
            can_view_products = False
            can_add_products = False
            can_edit_products = False
            can_delete_products = False
            can_manage_orders = False
            can_delete_orders = False
            can_manage_customers = False
            can_manage_inventory = False
            can_view_reports = False
            can_manage_users = False
            can_manage_branches = False
            can_confirm_delivery = False
            can_assign_dispatcher = False

        # Show menus based on permissions
        show_inventory = can_manage_inventory
        show_reports = can_view_reports
        show_dispatcher = can_confirm_delivery

        return {
            'user_profile': profile,
            'unread_notifications': unread_notifications,
            'can_view_products': can_view_products,
            'can_add_products': can_add_products,
            'can_edit_products': can_edit_products,
            'can_delete_products': can_delete_products,
            'can_manage_orders': can_manage_orders,
            'can_delete_orders': can_delete_orders,
            'can_manage_customers': can_manage_customers,
            'can_manage_inventory': can_manage_inventory,
            'can_view_reports': can_view_reports,
            'can_manage_users': can_manage_users,
            'can_manage_branches': can_manage_branches,
            'can_confirm_delivery': can_confirm_delivery,
            'can_assign_dispatcher': can_assign_dispatcher,
            'show_inventory': show_inventory,
            'show_reports': show_reports,
            'show_dispatcher': show_dispatcher,
            **branding,
        }
    return {
        'user_profile': None,
        'unread_notifications': 0,
        'can_view_products': False,
        'can_add_products': False,
        'can_edit_products': False,
        'can_delete_products': False,
        'can_manage_orders': False,
        'can_delete_orders': False,
        'can_manage_customers': False,
        'can_manage_inventory': False,
        'can_view_reports': False,
        'can_manage_users': False,
        'can_manage_branches': False,
        'can_confirm_delivery': False,
        'can_assign_dispatcher': False,
        'show_inventory': False,
        'show_reports': False,
        'show_dispatcher': False,
        'COMPANY_NAME':       _brand('COMPANY_NAME',       'G & G Divine Favour Catering Ventures'),
        'COMPANY_SHORT_NAME': _brand('COMPANY_SHORT_NAME', 'G&G Catering'),
        'COMPANY_TAGLINE':    _brand('COMPANY_TAGLINE',    'Fresh meals, delivered with love.'),
    }
