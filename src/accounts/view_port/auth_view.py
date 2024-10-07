from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from django.contrib import auth, messages

from rest_framework.response import Response
from rest_framework.views import APIView, status

from accounts.models import UserInfoExtend, User

class LoginView(APIView):
    def get(self, request, *args, **kwargs):
        # Render the login page when a GET request is made
        return render(request, 'login.html')

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            # Check if the username exists in the database
            if User.objects.filter(username=username).exists():
                user = authenticate(username=username, password=password)
                
                # If the user is authenticated
                if user is not None:
                    user_i = UserInfoExtend.objects.get(user_id=user.id)
                    
                    # Check verification status
                    if not user_i.verification_status:
                        messages.error(request, 'You are not verified')
                        return render(request, 'login.html', status=status.HTTP_401_UNAUTHORIZED)

                    # Log in and redirect based on user type
                    login(request, user)
                    request.session['user_id'] = user.id

                    if user_i.user_type == "customer":
                        return redirect("/u/")
                    elif user_i.user_type == "rider":
                        return redirect("/r/")
                    elif user_i.user_type in ["sub_admin", "super_admin"]:
                        messages.success(request, 'Login Successful')
                        return redirect("index_admin")
                
                else:
                    messages.error(request, 'Username or password not correct')
                    return render(request, 'login.html', status=status.HTTP_401_UNAUTHORIZED)

            else:
                messages.error(request, 'Username or password not correct')
                return render(request, 'login.html', status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            messages.error(request, 'An unexpected error occurred. Please try again later.')
            return render(request, 'login.html', status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class LogoutView(APIView):
    def post(self, request):
        auth.logout(request)
        
        # Return a success message
        messages.success(request, 'You have been logged out successfully.')

        return render(request, 'login.html', status=status.HTTP_200_OK)