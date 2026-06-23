import django_filters
from django_filters import DateFilter, CharFilter, ChoiceFilter
from django import forms
from .models import Order

_text_widget   = forms.TextInput(attrs={'class': 'form-control form-control-sm', 'style': 'min-width:140px'})
_date_widget   = forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date', 'style': 'min-width:130px'})
_select_widget = forms.Select(attrs={'class': 'form-control form-control-sm', 'style': 'min-width:160px'})


class OrderFilter(django_filters.FilterSet):
    start_date = DateFilter(
        field_name='date_create', lookup_expr='gte', label='From',
        widget=_date_widget,
    )
    end_date = DateFilter(
        field_name='date_create', lookup_expr='lte', label='To',
        widget=_date_widget,
    )
    delivery_name = CharFilter(
        field_name='delivery_name', lookup_expr='icontains',
        label='Customer Name', widget=_text_widget,
    )
    # reference has editable=False on the model so we use a custom method
    # to bypass django_filters field introspection
    reference = CharFilter(
        method='filter_reference',
        label='Order Ref',
        widget=_text_widget,
    )
    status = ChoiceFilter(
        choices=[('', 'All Statuses')] + list(Order.ORDER_STATUS_CHOICES),
        label='Status',
        widget=_select_widget,
        empty_label=None,
    )

    class Meta:
        model = Order
        fields = ['status', 'delivery_name', 'reference', 'start_date', 'end_date']

    def filter_reference(self, queryset, name, value):
        """Case-insensitive partial match on the reference field."""
        if value:
            return queryset.filter(reference__icontains=value.strip())
        return queryset
