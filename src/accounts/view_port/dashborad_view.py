from django.contrib.auth.decorators import login_required
from django.db.models import Max, Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.views import APIView, status

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone

from ..models import Notification, UserInfoExtend, Payment, Order, Counter
from datetime import datetime, timedelta

today = datetime.now()

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Equivalent of @login_required

    def get_user_info(self, request):
        return UserInfoExtend.objects.get(user=request.user)
    
    def get_orders_and_totals(self, status_filter=None):
        orders = Order.objects.all()
        order_dispatched = orders.filter(status__in=['Delivery Assigned']).count()
        orders_received = orders.filter(status__in=['Order Processing', 'Fulfilled', 'Pending', 'Delivery Assigned', 'Pick-up Assigned']).count()
        return orders, order_dispatched, orders_received
    
    def get_payment_and_revenue(self):
        total_revenue = Order.objects.filter(
            status__in=['Order Processing', 'Fulfilled', 'Pending', 'Delivery Assigned', 'Pick-up Assigned']
        ).aggregate(total=Sum('pricing'))['total'] or 0
        
        payment_received = Payment.objects.aggregate(total=Sum('payment_amount'))['total'] or 0
        return total_revenue, payment_received
    
    def get_past_30_days_data(self):
        today = timezone.now()
        first_day_prev_month = today - timedelta(days=30)
        
        orders_data = Order.objects.filter(
            status__in=['Order Processing', 'Fulfilled', 'Pending', 'Delivery Assigned', 'Pick-up Assigned'],
            created_at__gte=first_day_prev_month
        ).values('created_at', 'pricing')

        orders_count_data = Order.objects.filter(
            created_at__gte=first_day_prev_month
        ).values('created_at').annotate(count=Count('id'))
        
        return orders_data, orders_count_data
    
    def process_data_for_charts(self, orders_data, orders_count_data):
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Initialize totals dictionaries for pricing and order counts
        pricing_totals = {(thirty_days_ago + timedelta(days=x)).date(): 0 for x in range(30)}
        count_totals = pricing_totals.copy()  # Reuse the same keys for counts

        for datum in orders_data:
            date = datum["created_at"].date()
            pricing_totals[date] += datum["pricing"]

        for info in orders_count_data:
            date = info["created_at"].date()
            count_totals[date] += info["count"]

        # Convert totals to the required string format for chart data
        modified_data_string = ','.join(f'{{"meta": "{date.strftime("%m/%d/%Y")}", "value": "{value}"}}' for date, value in pricing_totals.items())
        modified_info_string = ','.join(f'{{"meta": "{date.strftime("%m/%d/%Y")}", "value": "{value}"}}' for date, value in count_totals.items())
        
        dates = [(thirty_days_ago + timedelta(days=x)).strftime("%B %d") for x in range(30)]
        data_labels = ','.join(f'"{date}"' for date in dates)
        
        return modified_data_string, modified_info_string, data_labels, dates
    
    def get_notifications(self):
        time_threshold = timezone.now() - timedelta(days=30)
        return Notification.objects.filter(created_at__gte=time_threshold, is_read=False)

    def post(self, request):
        usif = self.get_user_info(request)
        
        if usif.user_type == 'super_admin':
            Notification.objects.all().update(is_read=True)
            return JsonResponse({'detail': 'Notifications marked as read'})

        return JsonResponse({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    def get(self, request):
        usif = self.get_user_info(request)
        
        # Fetch necessary data
        orders, order_dispatched, orders_received = self.get_orders_and_totals()
        total_revenue, payment_received = self.get_payment_and_revenue()
        orders_data, orders_count_data = self.get_past_30_days_data()
        
        # Process data for charts
        modified_data_string, modified_info_string, data_labels, dates = self.process_data_for_charts(orders_data, orders_count_data)

        # Get unread notifications
        notifications = self.get_notifications()

        # Prepare the response data
        context = {
            'usif': usif,
            'orders': orders,
            'order_dispatched': order_dispatched or 0,
            'orders_received': orders_received or 0,
            'total_revenue': total_revenue or 0,
            'payment_received': payment_received or 0,
            'modified_data_string': modified_data_string,
            'modified_info_string': modified_info_string,
            'dates': dates,
            "num_orders_lmonth": orders_data.count(),
            "data_labels": data_labels,
            'notifications': notifications,
        }
        
        return render(request, 'dashboard.html', context)
