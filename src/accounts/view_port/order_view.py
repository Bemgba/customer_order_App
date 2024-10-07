import json
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from rest_framework.views import APIView, status
from rest_framework.permissions import IsAuthenticated

from accounts.models import Notification, Rider, Order, Customer, Counter, Receipient


@login_required(login_url = "/")
def order_list(request):
    if request.method == "POST":
        form_id = request.POST.get('form_id')
        #print(form_id)
        if form_id == 'assignRider':
            assignmentType = request.POST.get('assignmentType')
            #print(assignmentType)
            riderName = request.POST.get('riderAssigned')
            rider = Rider.objects.get(name=riderName)
            order_id = request.POST.get('order_id')
            #print(order_id)
            order_instance = Order.objects.get(id=order_id)
            rider.assignedTasks =+ 1
            rider.save()
            # Update the rider field of the Order instance
            order_instance.rider = rider
            # Update the status field of the Order instance
            if assignmentType == '1':
                order_instance.status= 'Pick-up Assigned'
            elif assignmentType == '2':
                order_instance.status= 'Delivery Assigned'
            order_instance.save()

        if form_id == 'updateOrder':
            oStatus = request.POST.get('orderId')
            orde_instance = get_object_or_404(Order, id=oStatus)

            nStatus = request.POST.get('newStatus')
            if nStatus == 'received':
                orde_instance.status = 'Received'
            elif nStatus == 'fulfilled':
                orde_instance.status = 'Fulfilled'
                rider = get_object_or_404(Rider, id=orde_instance.rider_id)
                rider.completedTasks += 1
                rider.save()
            elif nStatus == 'unsuccessful':   
                orde_instance.status = 'Unsuccessful'
            elif nStatus == 'returned':
                orde_instance.status = 'Returned to Sender'
            elif nStatus == 'processing':
                orde_instance.status = 'Order Processing'
            
            orde_instance.save()

        if form_id == 'cancelOrder':
            reason = request.POST.get('cancelReason')
            if reason == None:
                messages.error(request, 'You have to specify a reason, please attempt to cancel Order with a reason')
            elif reason == 'other':
                otherreason = request.POST.get('specify')
                if not otherreason == None:
                    print(reason)
                    cha = Order.objects.get(id = request.POST.get('orderid'))
                    otherreason = request.POST.get('specify')
                    print(otherreason)
                    cha.reason = otherreason
                    cha.status = 'Cancelled'
                    cha.save()
                else:
                    messages.error(request, 'Please type in a reason for selecting other')
            else:
                cha = Order.objects.get(id = request.POST.get('orderid'))
                print(reason)
                print(cha)
                cha.reason = reason
                cha.status = 'Cancelled'
                cha.save()

    
    order_pending = Order.objects.filter(status__in = ['Pending', 'Received'])
    order_cancelled = Order.objects.filter(status__in = ['Cancelled', 'Unsuccessful', 'Returned to Sender'])
    order_assigned = Order.objects.filter(status__in=['Pick-up Assigned', 'Delivery Assigned'])    
    order_processing = Order.objects.filter(status = 'Order Processing')
    order_fulfilled = Order.objects.filter(status = 'Fulfilled')
    context =  {
        'orders' : Order.objects.all(),
        'customers' : Customer.objects.all(),
        'riders': Rider.objects.all(),
        'order_fulfilled': order_fulfilled,
        'order_cancelled': order_cancelled,
        'order_pending' : order_pending,
        'order_assigned' : order_assigned,
        'order_processing' : order_processing,
        }
    
    return render(request, 'orders.html', context)

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order_pending = Order.objects.filter(status__in=['Pending', 'Received'])
        order_cancelled = Order.objects.filter(status__in=['Cancelled', 'Unsuccessful', 'Returned to Sender'])
        order_assigned = Order.objects.filter(status__in=['Pick-up Assigned', 'Delivery Assigned'])
        order_processing = Order.objects.filter(status='Order Processing')
        order_fulfilled = Order.objects.filter(status='Fulfilled')
        
        orders = Order.objects.all()
        customers = Customer.objects.all()
        riders = Rider.objects.all()

        context = {
            'orders': orders,
            'customers': customers,
            'riders': riders,
            'order_fulfilled': order_fulfilled,
            'order_cancelled': order_cancelled,
            'order_pending': order_pending,
            'order_assigned': order_assigned,
            'order_processing': order_processing,
        }
        return render(request, 'orders.html', context, status=status.HTTP_200_OK)

    def post(self, request):
        form_id = request.data.get('form_id')

        if form_id == 'assignRider':
            return self.assign_rider(request)
        elif form_id == 'updateOrder':
            return self.update_order_status(request)
        elif form_id == 'cancelOrder':
            return self.cancel_order(request)
        messages.error(request, 'Invalid form_id')
        return redirect("index_admin", request, status=status.HTTP_400_BAD_REQUEST)

    def assign_rider(self, request):
        assignmentType = request.data.get('assignmentType')
        rider_name = request.data.get('riderAssigned')
        order_id = request.data.get('order_id')

        rider = get_object_or_404(Rider, name=rider_name)
        order_instance = get_object_or_404(Order, id=order_id)

        rider.assignedTasks += 1
        rider.save()

        order_instance.rider = rider
        if assignmentType == '1':
            order_instance.status = 'Pick-up Assigned'
        elif assignmentType == '2':
            order_instance.status = 'Delivery Assigned'

        order_instance.save()
        messages.success(request, 'Rider assigned successfully')

        return JsonResponse(request, status=status.HTTP_200_OK)

    def update_order_status(self, request):
        order_id = request.data.get('orderId')
        new_status = request.data.get('newStatus')

        order_instance = get_object_or_404(Order, id=order_id)

        if new_status == 'received':
            order_instance.status = 'Received'
        elif new_status == 'fulfilled':
            order_instance.status = 'Fulfilled'
            rider = get_object_or_404(Rider, id=order_instance.rider_id)
            rider.completedTasks += 1
            rider.save()
        elif new_status == 'unsuccessful':
            order_instance.status = 'Unsuccessful'
        elif new_status == 'returned':
            order_instance.status = 'Returned to Sender'
        elif new_status == 'processing':
            order_instance.status = 'Order Processing'

        order_instance.save()
        messages.success(request, 'Order status updated successfully')

        return JsonResponse(request, status=status.HTTP_200_OK)


    def cancel_order(self, request):
        reason = request.data.get('cancelReason')
        order_id = request.data.get('orderid')

        if reason is None:

            messages.error(request, 'You have to specify a reason')
            return JsonResponse(request, status=status.HTTP_400_BAD_REQUEST)
        
        order_instance = get_object_or_404(Order, id=order_id)

        if reason == 'other':
            other_reason = request.data.get('specify')
            if not other_reason:
                messages.error(request, 'Please type in a reason for selecting other')
                return JsonResponse(request, status=status.HTTP_400_BAD_REQUEST)
            order_instance.reason = other_reason
        else:
            order_instance.reason = reason

        order_instance.status = 'Cancelled'
        order_instance.save()
        
        messages.success(request, 'Order cancelled successfully')
        return JsonResponse(request, status=status.HTTP_200_OK)

@login_required(login_url = "/")
def create_single_order(request):
    #c_instance = Customer.objects.all()
    if request.method == "POST":
        receipients = Receipient.objects.create(
            receiver_name = request.POST['receiverName'],
            receiver_email = request.POST['receiverEmail'],
            receiver_phone = request.POST['receiverPhone'],
            receiver_address =  request.POST['deliveryAddress'],
            receiver_town = request.POST['deliveryTown'],
            receiver_city = request.POST['deliveryCity'],
            # receiver_state = receiver_state,
            # receiver_country = receiver_country,
        )
        
        # Generate reference number
        highest_ref_num = Order.objects.all().order_by('-reference_number').first()
        if highest_ref_num:
            ref_num = highest_ref_num.reference_number.split("-")[1]
            new_ref_num = int(ref_num) + 1
        else:
            new_ref_num = 1000

        reference_number = 'PJQ-'+ str(new_ref_num)
        
        # Create and save new Order/invoice
        ord = Order.objects.create(
            reference_number=reference_number, 
            created_at=request.POST['dateTime'],
            branch = request.POST['branch'],
            receipient=receipients,
            pricing= request.POST['invoiceTotal'], 
            customer=Customer.objects.get(pk=request.POST['customerName']),
            delivery_type=request.POST['deliveryType'],
            pck_description=request.POST['packageDescription'],
            pck_weight=request.POST['packageWeight'],

            )
        # Order.save()

        # Create or update Order count
    
        if not Counter.objects.filter(customer=Customer.objects.get(pk=request.POST['customerName'])).exists():
            Counter.objects.create(customer=ord.customer, orderC=1)
        
        else:
            con = Counter.objects.get(customer=Customer.objects.get(pk=request.POST['customerName']))
            con.orderC += 1

            con.save()
        price = request.POST['invoiceTotal']
        Notification.objects.create( message=f'A new Order {reference_number} has been made, the total price is {price}.')

        return redirect('invoice_generate', order_id=ord.id)
    else:
        context = {"customers" : Customer.objects.all(  )}
        return render(request, 'single-order.html', context)
        
@login_required(login_url = "/")
def create_bulk_order(request):
    print('get request works')
    if request.method == "POST":
        print('we got here tho')
        OrderCounter = len([key for key in request.POST.keys() if 'price' in key])
        print(OrderCounter)
        for i in range(1, OrderCounter + 1):
            print('here next')
            receipients = Receipient.objects.create(
                receiver_name = request.POST['receiverName'],
                receiver_email = request.POST['receiverEmail'],
                receiver_phone = request.POST['receiverPhone'],
                receiver_address = request.POST[f'deliveryAddress{i}'],
                receiver_town = request.POST[f'deliveryTown{i}'],
                receiver_city = request.POST[f'deliveryCity{i}'],
            )

            print(request.POST['subTotal'],)
            # Generate reference number
            highest_ref_num = Order.objects.all().order_by('-reference_number').first()
            if highest_ref_num:
                ref_num = highest_ref_num.reference_number.split("-")[1]
                new_ref_num = int(ref_num) + 1
            else:
                new_ref_num = 1000

            reference_number = 'PJQ-'+ str(new_ref_num)

            
            print('what is the issue')
            # Create and save new Order/invoice
            Order.objects.create(
                reference_number=reference_number, 
                created_at=request.POST['dateTime'],
                branch = request.POST['branch'],
                receipient=receipients,
                pricing= request.POST[f'price{i}'], 
                Customer=Customer.objects.get(pk=request.POST['customerName']),
                # delivery_type=request.POST['deliveryType'],
                pck_description=request.POST['packageDescription'],
                # pck_weight=request.POST['packageWeight'],

                )
            # Order.save()

            # Create or update Order count
        
            if not Counter.objects.filter(Customer=Customer.objects.get(pk=request.POST['customerName'])).exists():
                Counter.objects.create(Customer=Customer, orderC=1)
        
            else:
                con = Counter.objects.get(Customer=Customer.objects.get(pk=request.POST['customerName']))
                con.orderC += 1

                con.save()
        price = request.POST['subTotal']
        Notification.objects.create( message=f'A new bulk Order has been made, with a sub-total of {price}.')
        return redirect('order_list')
    else:
        context = {"customers" : Customer.objects.all()}
        return render(request, 'bulk-Order.html', context)
