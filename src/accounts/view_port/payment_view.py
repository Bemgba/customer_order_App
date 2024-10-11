

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max, Sum, Count
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required


from ..models import Notification, Customer, Payment, Order


@login_required(login_url = "/")
def new_payment(request):
    if request.method == 'POST':
        date_time = request.POST.get('dateTime')
        cstomer_name = request.POST.get('customerName')
        # order_ref = request.POST.get('orderRef')
        # payment_ref = request.POST.get('paymentReferenceNumber')
        payment_banks = request.POST.getlist('paymentBank')
        amounts = request.POST.getlist('paymentAmount')
        amounts = list(map(int, amounts))
        customer = Customer.objects.get(id=cstomer_name)
        # Order = order.objects.get(reference_number=order_ref)
        # Order.paid = True
        # Order.save()
        # Generate payment reference number
        # fill = order_ref.split('-', 1)[1]
        for payment_bank, amount in zip(payment_banks, amounts):
            highest_ref_num = Payment.objects.all().aggregate(Max('id'))['id__max']
            if highest_ref_num:
                fill = highest_ref_num.split('-', 1)[1]
                highr_ref_convert = int(fill.split("-")[1])+ 1 

                new_ref_num = str(highr_ref_convert)
            else:
                new_ref_num = 1000

            payment_ref = 'PJQ-P-'+ str(new_ref_num)
            # Check if payment_ref already exists in the database
            counter = 1
            while Payment.objects.filter(id=payment_ref).exists():
                payment_ref = 'PJQ-P-' + str(new_ref_num) + '-' + str(counter)
                counter += 1
        
            Payment.objects.create(
                id=payment_ref,
                customer=customer,
                bank=payment_bank,
                payment_amount=amount,
                order_date=date_time,
                # order=Order,
                payment_status=True,
            )
            print(amount)
                    # Creating and saving the notification
            
            Notification.objects.create(message = f"Payment of {amount} has been made with the Ref.Id {payment_ref}.")

        return redirect('payment_history')
    else:
        context = { 
            "customers" : Customer.objects.all(),
            "orders" : Order.objects.filter(paid=False),
            }
        return render(request, 'new-payment.html', context)

@login_required(login_url = "/")
def payment_history(request):
    if request.method == "POST":
        form_id = request.POST.get('form_id')
        #print(form_id)
        if form_id == 'confirmDeleteTransactionModal':
            pay_checking=request.POST.get('paymentId')
            opayment = Payment.objects.get( id = pay_checking)
            order = opayment.order
            order.paid=False
            order.save()
            opayment.delete()
            
            # opayment.delete()
    context= {"payments" : Payment.objects.all()}

    return render(request, 'payment-history.html', context)
