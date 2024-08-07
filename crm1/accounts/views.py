from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .forms import CustomerForm, OrderForm, CreateUserForm
from django.contrib import messages
from django.contrib.auth.models import Group
from django.http import HttpResponse
# from django.db.models import fields
# from crm1 import accounts
from .filters import OrderFilter
from .decorators import unauthenticated_user,allowed_users,admin_only
from .models import *
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from django.db.models import Count
# Create your views here.

# Register

'''@unauthenticated_user
def registerPage(request):
    form = CreateUserForm()
    if request.method == "POST":
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                #username=form.cleaned_data.get('username')
            # group =group.objects.get(name='customers')
            # User.groups.add(group)
            # Customer.objects.create(user=User)
            return redirect('login')
    context = {'form': form}
    return render(request, 'accounts/register.html', context)'''
#@unauthenticated_user
#@admin_only
@unauthenticated_user
def registerPage(request):
    print("In registerPage view")
    form = CreateUserForm()
    if request.method == "POST":
        print("Handling POST request")
        form = CreateUserForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            user = form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            name = form.cleaned_data.get('username')  # Assuming you want to use the username as the name
            
            #TAKEN TO SIGNALS.PY
            # group = Group.objects.get(name='customers')
            # user.groups.add(group)
            
            # Customer.objects.create(
            #     user=user,
            #     # name=user.username
            #     name=name,
            #     email=email
            # )
            
            messages.success(request, 'Account created for ' + username)
            return redirect('login')
    else:
        print("Handling GET request")
        
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

# Login
@unauthenticated_user
def loginPage(request):
    if request.method == "POST":
         username = request.POST.get('username')
         password = request.POST.get('password')
         user = authenticate(request, username=username, password=password)
         if user is not None:
                login(request, user)
                messages.info(request, "login successful!")
                return redirect('home')
         else:
                messages.info(request, 'username OR password incorrect')
                return render(request, 'accounts/login.html')
    context = {}
    return render(request, 'accounts/login.html', context)

#logout
def logoutUser(request):
    logout(request)
    messages.success(request, "Logout success!")
    return redirect("login")

# Home page
@login_required(login_url='login')#prevent unauthorised user access
#@allowed_users(allowed_roles=['admins'])
@admin_only
def home(request):
    orders = Order.objects.all()
    customers = Customer.objects.all()
    total_orders = orders.count()
    total_customers = customers.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()

    # Create a list of customers with their order counts
    customers_with_order_counts = []
    for customer in customers:
        customer_orders = orders.filter(customer=customer)
        customers_with_order_counts.append({
            'customer': customer,
            'order_count': customer_orders.count()
        })

    context = {
        'orders': orders,
        'customers_with_order_counts': customers_with_order_counts,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'delivered': delivered,
        'pending': pending
    }

    return render(request, 'accounts/dashboard1.html', context)

@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['customers'])
def userPage(request):
    orders=request.user.customer.order_set.all()
    total_orders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    #print('oders',orders)
    context={'orders':orders,
             'total_orders': total_orders,
              'delivered': delivered,
               'pending': pending}
    return render(request, 'accounts/user.html',context)


@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['admins'])
def products(request):
    products = Product.objects.all()
    return render(request, 'accounts/products.html', {'products': products})


@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['admins', 'customers'])
def customer(request, pk_test):
    customer = get_object_or_404(Customer, id=pk_test)
    orders = customer.order_set.all()
    order_count = orders.count()
    myFilter = OrderFilter(request.GET, queryset=orders)
    orders = myFilter.qs

    context = {
        'customer': customer,
        'orders': orders,
        'order_count': order_count,
        'myFilter': myFilter
    }

    return render(request, 'accounts/customer.html', context)

@login_required(login_url='login')#prevent unauthorised user access
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required(login_url='login')#prevent unauthorised user access
def createOrder(request, pk):
    OrderFormSet = inlineformset_factory(
        Customer, Order, fields=('product', 'status'), extra=5)
    customer = Customer.objects.get(id=pk)
    # order=Order.objects.get(id=pk)
    # queryset=Order.object.none()// clear the pre filled form
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    # formset=OrderFormSet(instance=order)
    # form=OrderForm(initial={'customer':customer})

    if request.method == 'POST':
       # form=OrderForm(request.POST)
        # print('Printing Post:',request.POST)
        formset = OrderFormSet(request.POST, instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect('/')
    # context={'form':form,
    context = {'formset': formset
               # 'customer':customer
               }
    return render(request, 'accounts/createOrder_form.html', context)

@login_required(login_url='login')#prevent unauthorised user access
def updateOrder(request, pk):
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        # print('Printing Post:',request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    context = {'form': form}
    return render(request, 'accounts/order_form.html', context)

@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['admins'])
def deleteOrder(request, pk):
    order = Order.objects.get(id=pk)
    if request.method == "POST":
        order.delete()
        return redirect('/')
    context = {'item': order}
    return render(request, 'accounts/delete.html', context)

@login_required(login_url='login')#prevent unauthorised user access
@allowed_users(allowed_roles=['customers'])
def accountSettings(request):
    customer=request.user.customer
    form=CustomerForm(instance=customer)
    if request.method == 'POST':
        form=CustomerForm(request.POST,request.FILES, instance=customer)
        if form.is_valid():
            form.save()
    context = {'form':form}
    return render(request, 'accounts/account_settings.html', context)

def view_all_orders(request):
    orders = Order.objects.all()
    # orders = Order.objects.all()[:5]
    customers = Customer.objects.all()
    total_orders = orders.count()
    total_customers = customers.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    context = {'orders': orders,
               'customers': customers,
               'total_orders': total_orders,
               'total_customers': total_customers,
               'delivered': delivered,
               'pending': pending
               }
    return render(request, 'accounts/view_all_orders.html', context)


def generate_pdf_response(filename):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

def format_date(date):
    return date.strftime("%m/%d/%y")  # Format date as Month:Day:Year  MM/DD/YY

def delivered_orders_pdf(request):
    response = generate_pdf_response("delivered_orders")
    p = canvas.Canvas(response, pagesize=letter)
    p.setTitle("Delivered Orders")

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Delivered Orders Report")

    # Table header
    p.setFont("Helvetica-Bold", 12)
    p.drawString(30, 720, "Customer")
    p.drawString(200, 720, "Product")
    p.drawString(370, 720, "Date Created")
    p.drawString(500, 720, "Amount")

    # Table data
    y = 700
    total_amount = 0
    orders = Order.objects.filter(status='Delivered')
    for order in orders:
        product_price = float(order.product.price)  # Ensure the price is a float
        p.setFont("Helvetica", 12)
        p.drawString(30, y, str(order.customer))
        p.drawString(200, y, str(order.product))
        p.drawString(370, y, format_date(order.date_create))
        p.drawString(500, y, f"N{product_price:.2f}")
        total_amount += product_price
        y -= 20

    # Total amount
    p.setFont("Helvetica-Bold", 12)
    p.drawString(30, y - 20, f"Total Amount: N{total_amount:.2f}")

    p.showPage()
    p.save()
    return response

def customer_delivered_orders_pdf(request, pk_test):
    customer = get_object_or_404(Customer, id=pk_test)
    response = generate_pdf_response(f"{customer.name}_delivered_orders")
    p = canvas.Canvas(response, pagesize=letter)
    p.setTitle(f"{customer.name} Delivered Orders Report")

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Delivered Orders for {customer.name}")

    # Table header
    p.setFont("Helvetica-Bold", 12)
    p.drawString(30, 720, "Product")
    p.drawString(200, 720, "Date Created")
    p.drawString(370, 720, "Amount")

    # Table data
    y = 700
    total_amount = 0
    orders = customer.order_set.filter(status='Delivered')
    for order in orders:
        product_price = float(order.product.price)  # Ensure the price is a float
        p.setFont("Helvetica", 12)
        p.drawString(30, y, str(order.product))
        p.drawString(200, y, format_date(order.date_create))
        p.drawString(370, y, f"N{product_price:.2f}")
        total_amount += product_price
        y -= 20

    # Total amount
    p.setFont("Helvetica-Bold", 12)
    p.drawString(30, y - 20, f"Total Amount: N{total_amount:.2f}")

    p.showPage()
    p.save()
    return response

#most ordered products in descending order
def most_ordered_products(request):
    products = Product.objects.annotate(order_count=Count('order')).order_by('-order_count')
    return render(request, 'accounts/most_ordered_products.html', {'products': products})