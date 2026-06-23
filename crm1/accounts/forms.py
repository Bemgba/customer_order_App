from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models
from .models import Branch, Customer, Ingredient, LGA, Order, Product, ProductCategory, ProductIngredient, Role, State, UserProfile


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class CreateUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


# ---------------------------------------------------------------------------
# Checkout form — collected just before the customer confirms the order
# ---------------------------------------------------------------------------

class CheckoutForm(forms.Form):
    """
    Captures delivery info from any visitor (no login required).
    State/LGA are rendered as dependent selects via AJAX.
    """
    delivery_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Full name', 'class': 'form-control'})
    )
    delivery_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 08012345678', 'class': 'form-control'})
    )
    delivery_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Optional', 'class': 'form-control'})
    )
    delivery_state = forms.ModelChoiceField(
        queryset=State.objects.all(),
        empty_label='-- Select State --',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_delivery_state'})
    )
    delivery_lga = forms.ModelChoiceField(
        queryset=LGA.objects.none(),   # populated via AJAX based on state selection
        empty_label='-- Select LGA --',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_delivery_lga'})
    )
    delivery_address = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'placeholder': 'House number, street name, landmark',
            'class': 'form-control'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Special instructions (optional)',
            'class': 'form-control'
        })
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('Cash on Delivery', 'Cash on Delivery'),
            ('Bank Transfer',    'Bank Transfer'),
            ('Card',             'Debit/Credit Card'),
            ('Mobile Money',     'Mobile Money'),
        ],
        initial='Cash on Delivery',
        widget=forms.RadioSelect,
        help_text='Select how you will pay for your order'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If a state was already submitted, load its LGAs
        if 'delivery_state' in self.data:
            state_id = self.data.get('delivery_state')  # already a string — no int() cast needed
            if state_id:
                self.fields['delivery_lga'].queryset = LGA.objects.filter(
                    state_id=state_id
                ).order_by('name')
        elif self.initial.get('delivery_state'):
            self.fields['delivery_lga'].queryset = LGA.objects.filter(
                state=self.initial['delivery_state']
            ).order_by('name')


# ---------------------------------------------------------------------------
# Staff — update order status
# ---------------------------------------------------------------------------

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'textarea w-full rounded-xl border-ink-200 focus:border-brand-400 focus:outline-none text-sm bg-sand-50 focus:bg-white resize-none',
                'placeholder': 'Internal notes (optional)',
            }),
            'status': forms.Select(attrs={
                'class': 'select w-full rounded-xl border-ink-200 focus:border-brand-400 text-sm bg-sand-50 focus:bg-white focus:outline-none',
            }),
        }


# ---------------------------------------------------------------------------
# CEO: create staff users
# ---------------------------------------------------------------------------

class CreateStaffForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text='Select one or more roles for this staff member.'
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        empty_label='-- No branch (CEO/Global) --'
    )
    is_ceo = forms.BooleanField(
        required=False,
        label='Grant CEO access',
        help_text='CEO has full unrestricted access across all branches.'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class EditUserRolesForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = UserProfile
        fields = ['roles', 'branch', 'is_ceo']


# ---------------------------------------------------------------------------
# Role CRUD
# ---------------------------------------------------------------------------

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = [
            'name', 'description',
            # Orders
            'can_manage_orders', 'can_delete_orders',
            # Products (granular)
            'can_view_products', 'can_add_products',
            'can_edit_products', 'can_delete_products',
            # Other
            'can_manage_customers',
            'can_view_reports', 'can_manage_inventory',
            'can_manage_payments',
            'can_manage_users', 'can_manage_branches',
            'can_confirm_delivery',
            'can_assign_dispatcher',
        ]
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}


# ---------------------------------------------------------------------------
# Customer profile (staff edit)
# ---------------------------------------------------------------------------

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        exclude = ['user']


# ---------------------------------------------------------------------------
# Branch / Product
# ---------------------------------------------------------------------------

class BranchForm(forms.ModelForm):
    manager = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Will be set in __init__
        required=False,
        empty_label='-- No manager assigned --',
        help_text='Select a staff member to manage this branch.'
    )
    
    class Meta:
        model = Branch
        fields = ['name', 'address', 'location', 'phone', 'status', 'manager']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff users (those with UserProfile who are staff or CEO)
        # Exclude customers (users who only have a Customer record)
        from .models import UserProfile
        staff_user_ids = UserProfile.objects.filter(
            models.Q(is_ceo=True) | models.Q(roles__isnull=False)
        ).distinct().values_list('user_id', flat=True)
        
        self.fields['manager'].queryset = (
            User.objects
            .filter(models.Q(id__in=staff_user_ids) | models.Q(is_superuser=True))
            .distinct()
            .order_by('username')
        )


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'category', 'description', 'image',
                  'tags', 'branch', 'is_available']


# ---------------------------------------------------------------------------
# Product Category
# ---------------------------------------------------------------------------

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ---------------------------------------------------------------------------
# Inventory — Ingredient Management
# ---------------------------------------------------------------------------

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['branch', 'name', 'unit', 'quantity_available', 'reorder_level']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Flour, Chicken, Oil'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. kg, litres, pieces'}),
            'quantity_available': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        }
        help_texts = {
            'reorder_level': 'Alert when stock falls below this level',
        }
