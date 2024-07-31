from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import Customer, Order
from django import forms
from django.contrib.auth.models import User


class OrderForm(ModelForm):
    class Meta:
        model = Order
        #fields = ['customer','product']
        fields = '__all__'
        
class CreateUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    # first_name = forms.CharField(required=True)
    #last_name = forms.CharField(required=True)
    class Meta:
        model = User
        fields = ['username','email','password1','password2' ]
       #fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        #fields = '__all__'
class CustomerForm(ModelForm):
    class Meta:
        model=Customer
        fields='__all__'
        exclude=['user']