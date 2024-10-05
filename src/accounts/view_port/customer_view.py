import calendar

import json
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Sum, Count
from django.contrib import messages

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import Customer, Counter, Order, Payment

from datetime import datetime, timedelta

today = datetime.now()

@login_required(login_url = "/")
def get_customer_info(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        customer_id = data['customer_id']
        custo = Customer.objects.get(id=customer_id)
        return JsonResponse({
            'name': custo.customer_name,
            'email': custo.customer_email,
            'phone': custo.customer_no,
            # 'address': custo.customer_address,
            # 'town' : custo.customer_town,
            # 'city' : custo.customer_city,
        })
   
   
@login_required(login_url = "/")
def customer_view(request):
    if request.method == 'POST':
        form_id = request.POST.get('form_id')
        if form_id == 'deleteModal':
            custo = request.POST.get('customerId')
            print(custo)
            cha = Customer.objects.get(id = custo)
            cha.delete()
        elif form_id == 'editCustomer':
            custom = request.POST.get('customerId')
            customes = Customer.objects.get(id=custom)
            return redirect(request, customes)
    context = {
        "customers": Customer.objects.all(),
        # "totalSpend": 
        }
    return render(request, 'Customer.html', context)

@login_required(login_url = "/")
def viewCustomer_page(request):
    first_day_prev_month = today.replace(day=1) - timedelta(days=0)
    if today.month == 1:
        last_day_prev_month = today.replace(year=today.year-1, month=12) - timedelta(days=0) + timedelta(days=calendar.monthrange(today.year-1, 12)[1])
    else:
        last_day_prev_month = today.replace(day=1) - timedelta(days=0) + timedelta(days=calendar.monthrange(today.year, today.month-1)[1])
    
    customer_id = request.GET.get('customer_id')
    customers = Customer.objects.get(id=customer_id)

    ordering = Order.objects.filter(Customer=customer_id)
    orderCount = Order.objects.filter(Customer=customer_id).count()
    orders = Order.objects.filter(created_at__gte=first_day_prev_month, created_at__lte=last_day_prev_month).values('created_at', 'reference_number', 'pricing', 'id')
    
    paymenttotal = Payment.objects.filter(Customer=customer_id).aggregate(Sum('payment_amount'))
    invoicetotal = Order.objects.filter(status__in=['Order Processing','Fulfilled','Pending','Delivery Assigned', 'Pick-up Assigned'], Customer=customer_id).aggregate(Sum('pricing'))
    payments = Payment.objects.filter(order_date__gte=first_day_prev_month, order_date__lte=last_day_prev_month).values('order_date', 'id','payment_amount')
    
    
    if invoicetotal['pricing__sum']:
        inv = invoicetotal['pricing__sum']
    else: 
        inv = 0
    
    if paymenttotal['payment_amount__sum']:
        paym = paymenttotal['payment_amount__sum']
    else:
        paym = 0
    
    creditBalance =  inv - paym
    
    context = {
        'Customer' :customers,
        'orders': orders,
        'orderCount':  0 if orderCount == None else orderCount,
        'ordering': ordering,
        'payments' : payments,
        'paymenttotal':  0 if paymenttotal['payment_amount__sum'] == None else paymenttotal['payment_amount__sum'],
        'invoicetotal': invoicetotal,
        'creditBalance': 0 if creditBalance ==None else creditBalance ,
        }
    return render(request, 'view-Customer.html', context)

@login_required(login_url = "/")
def customer_create(request):
    if request.method == 'POST':
        customer_creation = Customer.objects.create(
            dt_reg = request.POST['dateTime'],
            company_name = request.POST['customerName'],
            customer_address = request.POST['streetAddress'],
            customer_apart = request.POST['alternateAddress'],
            customer_city = request.POST['pickupCity'],
            customer_town = request.POST['pickupTown'],
            customer_state = request.POST['state'],
            customer_country = request.POST['country'],
            customer_no = request.POST['phoneNumber'],
            customer_name = request.POST['contactName'],
            customer_email = request.POST['email'],
            
            )
        Counter.objects.create( Customer=customer_creation, orderC=0)
        messages.success(request, 'Customer Creation Successful')
        return redirect("/pjq_admin/Customer/")
    
    return render(request, 'new-Customer.html')
