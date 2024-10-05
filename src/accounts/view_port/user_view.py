

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from ..models import  User,  UserInfoExtend

@login_required(login_url = "/")
def user_create(request):
    usif = UserInfoExtend.objects.get(user = request.user)
    if usif.user_type=='super_admin':
        if request.method == 'POST':
            full_name = request.POST.get('fullName')
            username = request.POST.get('userName')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')

            if password != password_confirm:
                messages.error(request, 'Passwords do not match')
                return render(request, 'new-user.html')

            first_name, last_name = full_name.split(' ', 1)

            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                password=password
            )
            user_info = UserInfoExtend.objects.create(
                user=user
            )

            messages.success(request, 'User created successfully', timeout=5)
            return redirect('user_create')
        return render(request, 'new-user.html')
    return redirect('index_admin')

@login_required(login_url = "/")
def user_list(request):
    usif = UserInfoExtend.objects.get(user = request.user)
    if usif.user_type=='super_admin':
        users = UserInfoExtend.objects.all()
        for user in users:
            user.date_created = timezone.localtime(user.date_created).date()
        context = {'users': users}
        return render(request, 'users.html', context)
    else: 
        return redirect('index_admin')