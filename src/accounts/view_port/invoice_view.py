
import base64

from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string,  get_template

from django.http import JsonResponse, HttpResponse
from bs4 import BeautifulSoup
from weasyprint import HTML

from ..models import Payment, Order


@login_required(login_url = "/")
def invoice_generate(request, order_id):
    # orderid = request.GET.get('orderid')
    with open("src/static/public/img/Quest.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()

    data_uri = "data:Quest/png;base64," + encoded_string

    ord = Order.objects.get(id=order_id)
    custom = ord.customer

    ordprice = Order.objects.filter(status__in=['Order Processing','Fulfilled','Pending','Delivery Assigned', 'Pick-up Assigned'], customer=custom).aggregate(Sum('pricing'))['pricing__sum']
    payments = Payment.objects.filter(customer = custom)
    
    payment_sum = payments.aggregate(Sum('payment_amount'))['payment_amount__sum']
    # Set the payment amount to zero if there is no payment amount available
    payment_amount = payment_sum if payment_sum else 0

    credit_balance = int(payment_amount) - int(ordprice)

    context= {
        'order_id': ord.id,
        'order': ord, 
        'credit_balance': credit_balance,
        'data_uri':data_uri,
        }
    return render(request, 'invoice.html', context)


@login_required(login_url = "/")
def render_template_as_jpeg(request, order_id):
    ord = Order.objects.get(id=order_id)
    custom = ord.customer
    ordprice = Order.objects.filter(status__in=['Order Processing','Fulfilled','Pending','Delivery Assigned', 'Pick-up Assigned'], customer=custom).aggregate(Sum('pricing'))['pricing__sum']
    payments = Payment.objects.filter(customer=custom)
    payment_sum = payments.aggregate(Sum('payment_amount'))['payment_amount__sum']
    payment_amount = payment_sum if payment_sum else 0
    credit_balance = int(payment_amount) - int(ordprice)
    print(credit_balance)

    
    # Use the `get_template` function to load the desired template
    template = get_template('invoice.html')
    # Render the template with the context data
    with open("pjquest/static/public/img/Quest.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()

    data_uri = "data:Quest/png;base64," + encoded_string
    context= {
        'order_id': ord.id,
        'order': ord, 
        'credit_balance': credit_balance,
        'data_uri':data_uri,
        }
    html = render_to_string('invoice.html', {'order': ord,'data_uri':data_uri, 'credit_balance': credit_balance, 'order_id': ord.id})
    soup = BeautifulSoup(html, 'html.parser')
    element = soup.find('div', {'class': 'download_pdf'})

    weasyprint_html = HTML(string=str(element))
    pdf = weasyprint_html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice-{}.pdf"'.format(ord.reference_number)
    response.write(pdf)
    return response