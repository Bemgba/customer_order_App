from django.contrib.auth.decorators import login_required
from django.db.models import Max, Sum, Count
from django.shortcuts import render, redirect, get_object_or_404

from django.utils import timezone

from ..models import Notification, UserInfoExtend, Payment, Order, Counter
from datetime import datetime, timedelta

today = datetime.now()

@login_required(login_url = "login")
def index_admin(request):  
    usif = UserInfoExtend.objects.get(user = request.user)

    if usif.user_type == 'super_admin':
        if request.method == 'POST':
            # Mark all notifications as read
            Notification.objects.all().update(is_read=True)
        else:
    
            usif = UserInfoExtend.objects.get(user = request.user)
            orders = Order.objects.all()
            order_dispatched = Order.objects.filter(status__in=['Delivery Assigned']).count()
            orders_received = Order.objects.filter(status__in=['Order Processing','Fulfilled','Pending','Delivery Assigned', 'Pick-up Assigned']).count()

            first_day_prev_month = today - timedelta(days=30)
            last_day_prev_month = today  
            data = Order.objects.filter(status__in=['Order Processing','Fulfilled','Pending','Delivery Assigned', 'Pick-up Assigned'], created_at__gte=first_day_prev_month, created_at__lte=last_day_prev_month).values('created_at', 'pricing')
            # The annotate function in Django is used to add an additional column to the query results, where the values in the column are derived from the existing data in the queryset. This is useful when you want to perform aggregations or calculations on the data and display the results in your template.
            infos = Order.objects.filter(created_at__gte=first_day_prev_month, created_at__lte=last_day_prev_month).values('created_at').annotate(Count('id'))

            dates = []
            date = first_day_prev_month
            while date <= last_day_prev_month:
                dates.append(date.strftime("%B %d"))
                date += timedelta(days=1)
            
            total_revenue = 0
            payment_received = 0
            for x in Payment.objects.all().values('payment_amount'):
                payment_received +=x['payment_amount']
            for y in Order.objects.filter(status__in=['Order Processing', 'Fulfilled', 'Pending', 'Delivery Assigned', 'Pick-up Assigned']).values('pricing'):
                total_revenue +=y['pricing']

            data_labels = ','.join(f'"{date}"' for date in dates)

            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)

            # Initializing the dictionary with keys for each day in the past 30 days, and values set to 0
            pricing_totals = {(thirty_days_ago + timedelta(days=x)).date(): 0 for x in range(30)}
            
            # Iterate through the data
            for datum in data:
                # Get the date and pricing value
                date = datum["created_at"].date()
                value = datum["pricing"]

                # If the date is not in the dictionary, add it and set the value to the pricing value
                if date not in pricing_totals:
                    pricing_totals[date] = value
                # If the date is already in the dictionary, add the pricing value to the existing value
                else:
                    pricing_totals[date] += value
            # Modify the data to match the format in the data-series
            modified_data = []
            for date, value in pricing_totals.items():
                meta = date.strftime("%m/%d/%Y %I:%M %p")
                modified_data_string = ''.join(f'{{"meta": "{meta}", "value": "{value}"}}')
                modified_data.append(modified_data_string)
                modified_data_string = ','.join(modified_data[0:])
            
            # print(modified_data_string)
            
            # Initializing the dictionary with keys for each day in the past 30 days, and values set to 0
            count_totals = {(thirty_days_ago + timedelta(days=x)).date(): 0 for x in range(30)}

            #for the second graph
            for info in infos:
                date = info["created_at"].date()
                value = info["id__count"]
                if date not in count_totals:
                    count_totals[date] = value
                # If the date is already in the dictionary, add the pricing value to the existing value
                else:
                    count_totals[date] += value
            # Modify the data to match the format in the data-series
            modified_info = []
            for date, value in count_totals.items():
                meta = date.strftime("%m/%d/%Y %I:%M %p")
                modified_info_string = ''.join(f'{{"meta": "{meta}", "value": "{value}"}}')
                modified_info.append(modified_info_string)
                modified_info_string = ','.join(modified_info[0:])

            # Filter notifications for the last 30 days for a GET request
            time_threshold = timezone.now() - timedelta(days=30)
            notifications = Notification.objects.filter(created_at__gte=time_threshold, is_read=False)
            
            context = {
                'usif': usif,
                'orders': orders,
                'order_dispatched': 0 if order_dispatched == None else order_dispatched,
                'orders_received': 0 if orders_received == None else orders_received,
                'total_revenue': 0 if total_revenue == None else total_revenue,
                'payment_received': 0 if payment_received == None else payment_received,
                'modified_data_string': modified_data_string,
                'modified_info_string': modified_info_string,
                'dates': dates,
                "num_orders_lmonth" : data.count(),
                "net_profit" : "",
                "orderpermonths" : [''],
                "data_labels": data_labels,
                'notifications': notifications,
                }

            return render(request, 'dashboard.html', context)

    else:
        usif = UserInfoExtend.objects.get(user = request.user)
        orders = Order.objects.all()
        order_dispatched = Order.objects.filter(status__in=['Delivery Assigned']).count()
        orders_received = Order.objects.filter(status__in=['Order Processing','Fulfilled','Pending','Delivery Assigned', 'Pick-up Assigned']).count()

        first_day_prev_month = today - timedelta(days=30)
        last_day_prev_month = today  
        data = Order.objects.filter(status__in=['Order Processing','Fulfilled','Pending','Delivery Assigned', 'Pick-up Assigned'], created_at__gte=first_day_prev_month, created_at__lte=last_day_prev_month).values('created_at', 'pricing')
        # The annotate function in Django is used to add an additional column to the query results, where the values in the column are derived from the existing data in the queryset. This is useful when you want to perform aggregations or calculations on the data and display the results in your template.
        infos = Order.objects.filter(created_at__gte=first_day_prev_month, created_at__lte=last_day_prev_month).values('created_at').annotate(Count('id'))

        dates = []
        date = first_day_prev_month
        while date <= last_day_prev_month:
            dates.append(date.strftime("%B %d"))
            date += timedelta(days=1)
        
        total_revenue = 0
        payment_received = 0
        for x in Payment.objects.all().values('payment_amount'):
            payment_received +=x['payment_amount']
        for y in Order.objects.filter(status__in=['Order Processing', 'Fulfilled', 'Pending', 'Delivery Assigned', 'Pick-up Assigned']).values('pricing'):
            total_revenue +=y['pricing']

        data_labels = ','.join(f'"{date}"' for date in dates)

        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)

        # Initializing the dictionary with keys for each day in the past 30 days, and values set to 0
        pricing_totals = {(thirty_days_ago + timedelta(days=x)).date(): 0 for x in range(30)}
        
        # Iterate through the data
        for datum in data:
            # Get the date and pricing value
            date = datum["created_at"].date()
            value = datum["pricing"]

            # If the date is not in the dictionary, add it and set the value to the pricing value
            if date not in pricing_totals:
                pricing_totals[date] = value
            # If the date is already in the dictionary, add the pricing value to the existing value
            else:
                pricing_totals[date] += value
        # Modify the data to match the format in the data-series
        modified_data = []
        for date, value in pricing_totals.items():
            meta = date.strftime("%m/%d/%Y %I:%M %p")
            modified_data_string = ''.join(f'{{"meta": "{meta}", "value": "{value}"}}')
            modified_data.append(modified_data_string)
            modified_data_string = ','.join(modified_data[0:])
        
        # print(modified_data_string)
        
        # Initializing the dictionary with keys for each day in the past 30 days, and values set to 0
        count_totals = {(thirty_days_ago + timedelta(days=x)).date(): 0 for x in range(30)}

        #for the second graph
        for info in infos:
            date = info["created_at"].date()
            value = info["id__count"]
            if date not in count_totals:
                count_totals[date] = value
            # If the date is already in the dictionary, add the pricing value to the existing value
            else:
                count_totals[date] += value
        # Modify the data to match the format in the data-series
        modified_info = []
        for date, value in count_totals.items():
            meta = date.strftime("%m/%d/%Y %I:%M %p")
            modified_info_string = ''.join(f'{{"meta": "{meta}", "value": "{value}"}}')
            modified_info.append(modified_info_string)
            modified_info_string = ','.join(modified_info[0:])

        
        context = {
            'usif': usif,
            'orders': orders,
            'order_dispatched': 0 if order_dispatched == None else order_dispatched,
            'orders_received': 0 if orders_received == None else orders_received,
            'total_revenue': 0 if total_revenue == None else total_revenue,
            'payment_received': 0 if payment_received == None else payment_received,
            'modified_data_string': modified_data_string,
            'modified_info_string': modified_info_string,
            'dates': dates,
            "num_orders_lmonth" : data.count(),
            "net_profit" : "",
            "orderpermonths" : [''],
            "data_labels": data_labels,
            }

        return render(request, 'dashboard.html', context)


@login_required(login_url='login')#prevent unauthorised user access
def dashboard_view(request):
    return render(request, 'dashboard.html')