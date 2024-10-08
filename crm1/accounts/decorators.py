#Role Base Permission and Authentication
from django.http import HttpResponse
from django.shortcuts import redirect
from functools import wraps

#Stop unauthenticated user from viewing the LOGIN and REGISTER page
def unauthenticated_user(view_func): 
    def wrapper_func(request, *args,  **kwargs):
        print(f"Authenticated: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            print("Redirecting to home")
            return redirect('home')
        else:
            print("Rendering view")
            return view_func(request, *args, **kwargs)
    
    return wrapper_func

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper_func(request, *args, **kwargs):
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name
            if group in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse('You are not authorized to view this page')
        return wrapper_func
    return decorator

def admin_only(view_func):
    def wrapper_function(request, *args, **kwargs):
        group=None
        if request.user.groups.exists():
            group=request.user.groups.all()[0].name
        if group=='customers':
            return redirect('user-page')
        if group=='admins':
            return view_func(request, *args, **kwargs)
        
    return wrapper_function