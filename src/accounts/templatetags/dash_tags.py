from django import template
from ..models import *
from django.db.models import Sum

register = template.Library()

# @register.inclusion_tag()
# def

@register.simple_tag
def add_commas(value):
    return '{:,}'.format(value)

@register.simple_tag
def total_payment_by_customer(customer):
    payments = customer.payment_set.all().aggregate(Sum('payment_amount'))
    if payments['payment_amount__sum']:
        return '{:,}'.format(payments['payment_amount__sum'])
    else:
        return 0

@register.filter
def to_float(value):
    return float(value)

@register.simple_tag
def total_order_price_by_customer(customer):
    orders = customer.order_set.filter(status__in=['Order Processing','Fulfilled','Pending','Delivery Assigned', 'Pick-up Assigned']).aggregate(Sum('pricing'))
    payments = customer.payment_set.all().aggregate(Sum('payment_amount'))
    if orders['pricing__sum']:
        ord = orders['pricing__sum']
    else: 
        ord = 0
    
    if payments['payment_amount__sum']:
        paym = payments['payment_amount__sum']
    else:
        paym = 0
    
    order_price = ord - paym
    
    return '{:,}'.format((order_price))

@register.filter
def add_prefixphone(value):
    return "+234" + value[1:]

@register.filter
def hyphenate_phone(value):    
    return "+234-{}-{}-{}".format(value[1:3], value[3:7], value[7:])