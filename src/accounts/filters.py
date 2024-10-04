import django_filters
from .models import *
from django_filters import DateFilter, CharFilter,ModelChoiceFilter, ChoiceFilter
# from django.forms import ModelForm
#FILTER SEARCH BY VARIOUS PARAMETERS
class OrderFilter(django_filters.FilterSet):
    start_date=DateFilter(field_name="date_create",lookup_expr='gte', label='Start Date')#gte= greater than or equal to
    end_date=DateFilter(field_name="date_create",lookup_expr='lte', label='End Date')#lte= less than or equal to
   # product = CharFilter(field_name='product__name', lookup_expr='icontains')
    #status = CharFilter(field_name='status', lookup_expr='icontains')
    notes= CharFilter(field_name='nates', lookup_expr='icontains',label='Notes')
    
    product = ModelChoiceFilter(
        queryset=Product.objects.all(),
        empty_label='Select Product',
        label='Product'
    )
    
    status = ChoiceFilter(
        choices=Order.STATUS,
        empty_label='Select Status',
        label='Status'
    )
    class meta:
        model =Order
        fields= '__all__'
        exclude=[ 'customer','date_create']