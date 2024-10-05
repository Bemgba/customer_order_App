from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from django.contrib import auth, messages
from django.contrib.auth.models import Group
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse, HttpResponseServerError
from knox.models import AuthToken

from rest_framework.response import Response
from rest_framework.views import APIView, status

from accounts.models import UserInfoExtend, User

def login_view(request):
    if request.user.is_authenticated:
        return redirect("/dashboard/")
        
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None :
            user_i = UserInfoExtend.objects.get(user_id = user.id)
            if user_i.verification_status == False:
                messages.error(request, 'you are not verified')
                return render(request, 'login.html', status=status.HTTP_401_UNAUTHORIZED)
            else:
                if user_i.user_type == "customer":
                    # Correct password, and the user is marked "active"
                    login(request, user)
                    # Redirect to a success page.
                    return redirect("/u/")
                elif user_i.user_type == "rider":
                    # Correct password, and the user is marked "active"
                    login(request, user)
                    # Redirect to a success page.
                    return redirect("/r/")
                elif user_i.user_type == "sub_admin" :
                    # Correct password, and the user is marked "active"
                    login(request, user)
                    messages.success(request, 'Login Successful')
                    return redirect("/dashboard/")
                elif user_i.user_type == "super_admin" :
                    # Correct password, and the user is marked "active"
                    login(request, user)
                    messages.success(request, 'Login Successful')
                    return redirect("/dashboard/")
        else:
            messages.error(request,'username or password not correct')
            return redirect(login_view)
    
    else:
        return render(request, 'login.html')
    
    
class LoginView(APIView):
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            if User.objects.filter(username=username).exists():

                user = authenticate(username=username, password=password)
                if user is not None:
                    user_i = UserInfoExtend.objects.get(user_id=user.id)
                    if user_i.verification_status == False:
                        
                        messages.error(request, 'You are not verified')
                        return render ( 
                                    request,
                                    'login.html',
                                    status=status.HTTP_401_UNAUTHORIZED
                                )
                    else:
                        login(request, user)
                        
                        # Setting user_id in the session
                        request.session['user_id'] = user.id
                        return Response({
                            "access_token": AuthToken.objects.create(user=user)[1],
                            "client": user_i.user_type,
                            "user": {
                                "email": user.email,
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "active_subscription": '',
                            },
                            'message': 'Logged in successfully'
                        }, status=status.HTTP_200_OK)
        except Exception as e:
            # Handle exceptions here and log them
            return HttpResponseServerError(f"An error occurred: {str(e)}")


def logout_view(request):
    auth.logout(request)
    # Redirect to a login page.
    return redirect(login_view)