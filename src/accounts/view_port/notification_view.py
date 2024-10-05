from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import Notification


def clear_notification(request, notification_id):
    notification = Notification.objects.get(id=notification_id)
    notification.is_read = True
    notification.save()
    print('it worked')
    return redirect('index_admin')


@login_required(login_url = "/")
def clear_all_notifications(request):
    Notification.objects.all().update(is_read=True)
    # Redirect the user back to the index page
    return redirect('index_admin')