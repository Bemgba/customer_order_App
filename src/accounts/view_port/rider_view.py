
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Rider


@login_required(login_url = "/")
def rider_view(request):
    if request.method == 'POST':
        registration_date = request.POST.get('dateTime')
        name = request.POST.get('riderName')
        phone = request.POST.get('riderNumber')
        address = request.POST.get('streetAddress')
        apart = request.POST.get('alternateAddress')
        city = request.POST.get('city')
        state = request.POST.get('state')
        Guarantor_name = request.POST.get('guarantorName')
        Guarantor_mobile_number = request.POST.get('guarantorNumber')
        Guarantor_address = request.POST.get('guarantorStreetAddress')
        Guarantor_apart = request.POST.get('guarantorAlternateAddress')
        Guarantor_city = request.POST.get('guarantorCity')
        Guarantor_state = request.POST.get('guarantorState')
        
        
        
        Rider.objects.create(
            registration_date = registration_date,
            name = name,
            phone = phone,
            address = address,
            apart = apart,
            city = city,
            state = state,
            Guarantor_name = Guarantor_name,
            Guarantor_mobile_number = Guarantor_mobile_number,
            Guarantor_address = Guarantor_address,
            Guarantor_apart = Guarantor_apart,
            Guarantor_city = Guarantor_city,
            Guarantor_state = Guarantor_state,

        )
    context={'riders': Rider.objects.all() }
    return render(request, 'riders.html', context)

