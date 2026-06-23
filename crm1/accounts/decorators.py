# Role-Based Permission and Authentication
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.core.exceptions import PermissionDenied
from functools import wraps


def _get_profile(user, request=None):
    """
    Safely return the user's UserProfile, or None.

    When `request` is provided the result is cached on the request object
    so subsequent calls within the same request cycle hit the DB only once.
    The profile is fetched with prefetch_related('roles') so that
    has_permission() can iterate roles in Python without extra queries.
    """
    if request is not None:
        cached = getattr(request, '_cached_profile', None)
        if cached is not None:
            return cached
    try:
        from django.db.models import Prefetch  # local import avoids circular risk
        profile = (
            user.profile.__class__._default_manager
            .prefetch_related('roles')
            .get(user=user)
        )
    except Exception:
        profile = None
    if request is not None:
        request._cached_profile = profile
    return profile


def _is_staff_user(user, profile):
    """True if this user has a staff role or is CEO/superuser."""
    if user.is_superuser:
        return True
    if profile and profile.is_ceo:
        return True
    # Use roles.all() so a prefetched queryset is reused in Python
    if profile and any(True for _ in profile.roles.all()):
        return True
    return False


# ---------------------------------------------------------------------------
# unauthenticated_user
# ---------------------------------------------------------------------------

def unauthenticated_user(view_func):
    """
    Redirect already-logged-in users away from login/register.
    Staff → /dashboard/   |   Customers → /my-orders/
    """
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            profile = _get_profile(request.user, request)
            if _is_staff_user(request.user, profile):
                return redirect('home')
            return redirect('my_orders')
        return view_func(request, *args, **kwargs)
    return wrapper_func


# ---------------------------------------------------------------------------
# admin_only  — staff dashboard gate
# ---------------------------------------------------------------------------

def admin_only(view_func):
    """
    Only staff (roles / CEO / superuser) reach the staff dashboard.
    Customers are redirected to their order portal.
    """
    @wraps(view_func)
    def wrapper_function(request, *args, **kwargs):
        profile = _get_profile(request.user, request)
        if _is_staff_user(request.user, profile):
            return view_func(request, *args, **kwargs)
        return redirect('my_orders')
    return wrapper_function


# ---------------------------------------------------------------------------
# ceo_only
# ---------------------------------------------------------------------------

def ceo_only(view_func):
    """Restrict a view to CEO users (and Django superusers) only."""
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = _get_profile(request.user, request)
        if profile and profile.is_ceo:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Only the CEO can access this page.")
    return wrapper_func


# ---------------------------------------------------------------------------
# manager_or_ceo  — any staff member
# ---------------------------------------------------------------------------

def manager_or_ceo(view_func):
    """Allow any staff member (has roles, is CEO, or is superuser)."""
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        profile = _get_profile(request.user, request)
        if _is_staff_user(request.user, profile):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("You are not authorized to view this page.")
    return wrapper_func


# ---------------------------------------------------------------------------
# requires_permission  — role flag check
# ---------------------------------------------------------------------------

def requires_permission(perm):
    """
    Allow only users whose roles grant the given permission flag.
    CEO and superusers bypass all checks.
    Usage: @requires_permission('can_manage_orders')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper_func(request, *args, **kwargs):
            profile = _get_profile(request.user, request)
            # CEO and superusers bypass permission checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if profile and profile.is_ceo:
                return view_func(request, *args, **kwargs)
            if profile and profile.has_permission(perm):
                return view_func(request, *args, **kwargs)
            # Raise PermissionDenied to trigger custom 403 page
            perm_display = perm.replace("_", " ").title()
            raise PermissionDenied(f"Your roles do not grant '{perm_display}' permission.")
        return wrapper_func
    return decorator


# ---------------------------------------------------------------------------
# allowed_users  — legacy, kept for any remaining direct usages
# ---------------------------------------------------------------------------

def allowed_users(allowed_roles=[]):
    """
    Allows only non-staff users (customers) when allowed_roles=['customers'].
    Staff users are blocked from customer-only views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper_func(request, *args, **kwargs):
            profile = _get_profile(request.user, request)
            if 'customers' in allowed_roles:
                # Block staff from customer-only pages
                if not _is_staff_user(request.user, profile):
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied("You are not authorized to view this page.")
        return wrapper_func
    return decorator
