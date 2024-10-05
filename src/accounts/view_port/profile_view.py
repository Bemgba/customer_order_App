
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string,  get_template


from ..models import Notification, User, UserInfoExtend, Payment, Order, Counter

@login_required(login_url = "/")
def profileSet_view(request):
    usif = UserInfoExtend.objects.get(user = request.user)
    if usif.user_type=='super_admin':
        user = User.objects.get(id=request.user.id)

        if request.method == 'POST':
            current_password = request.POST.get('old_password')
            new_password = request.POST.get('password')
            new_password_confirmation = request.POST.get('password_confirm')

            user = request.user

            if user.check_password(current_password):
                if new_password == new_password_confirmation:

                    user.set_password(new_password)
                    user.save()
                    # Re-authenticate the user with the new password
                    user = authenticate(username=user.username, password=new_password)
                    login(request, user)
                    return redirect('profileSet_view')
                else:
                    # Return an error message if the new password and confirmation do not match
                    error_message = "The new password and confirmation do not match."
            else:
                # Return an error message if the current password is incorrect
                error_message = "The current password is incorrect."
        else:
            error_message = None

        # Render the settings template with the error message, if any
        return render(request, 'profile-settings.html', {'error_message': error_message, 'user': user})
    else:
        return redirect('index_admin')