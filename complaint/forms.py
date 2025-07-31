from django import forms
from django.core.validators import RegexValidator, MinLengthValidator, EmailValidator, MinValueValidator
from django.contrib.auth import get_user_model
from .models import Complaint, Profile
from product.models import Product

User = get_user_model()

# 🚪 Complaint Form
class ComplaintForm(forms.ModelForm):
    mobile_number = forms.CharField(
        validators=[RegexValidator(r'^\d{10}$', message="Enter a valid 10-digit mobile number.")]
    )
    email = forms.EmailField(
        required=True,
        validators=[EmailValidator(message="Enter a valid email address.")]
    )
    service_cost = forms.DecimalField(
        required=False,
        min_value=0,
        error_messages={'min_value': 'Service cost cannot be negative.'}
    )

    # 🆕 Address Fields
    pincode = forms.CharField(
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter Pincode', 'class': 'form-control'})
    )
    city = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control'})
    )
    state = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-control'})
    )
    area = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Area', 'class': 'form-control'})
    )
    street = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Street', 'class': 'form-control'})
    )
    landmark = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Landmark (optional)', 'class': 'form-control'})
    )

    class Meta:
        model = Complaint
        fields = [
            'customer_name',
            'mobile_number',
            'email',
            'product',
            'issue_type',
            'status',
            'assigned_engineer',
            'description',
            'service_cost',
            'payment_method',
            'pincode',
            'city',
            'state',
            'area',
            'street',
            'landmark',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the issue...'}),
        }

    def __init__(self, *args, show_admin_fields=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update({'placeholder': 'Enter your email address'})

        if 'assigned_engineer' in self.fields:
            self.fields['assigned_engineer'].queryset = User.objects.filter(profile__role='engineer')

        if not show_admin_fields:
            for field in ['status', 'assigned_engineer', 'service_cost', 'payment_method']:
                self.fields.pop(field, None)

    
# 🛠 Complaint Update Form
class ComplaintUpdateForm(forms.ModelForm):
    mark_cash_paid = forms.BooleanField(required=False, label="Mark Cash Payment as Paid")
    service_cost = forms.DecimalField(
        required=False,
        min_value=0,
        error_messages={'min_value': 'Service cost cannot be negative.'}
    )

    class Meta:
        model = Complaint
        fields = [
            'status',
            'assigned_engineer',
            'product_serial_number',
            'service_confirmation_photo',
            'service_cost',
            'payment_method',
            'payment_confirmation_photo',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        role = getattr(getattr(user, 'profile', None), 'role', None)

        if 'assigned_engineer' in self.fields:
            self.fields['assigned_engineer'].queryset = User.objects.filter(profile__role='engineer')

        if role == 'accountant':
            allowed = ['service_cost', 'payment_method', 'payment_confirmation_photo', 'mark_cash_paid']
            for field in list(self.fields):
                if field not in allowed:
                    self.fields.pop(field, None)

            if self.instance.payment_method != 'cash':
                self.fields['mark_cash_paid'].widget = forms.HiddenInput()
                self.fields['mark_cash_paid'].required = False

            if self.instance.payment_method != 'online':
                self.fields['payment_confirmation_photo'].required = False

        elif role == 'engineer':
            allowed = ['product_serial_number', 'service_confirmation_photo']
            for field in list(self.fields):
                if field not in allowed:
                    self.fields.pop(field, None)

        elif role not in ['admin', 'manager']:
            allowed = ['status']
            for field in list(self.fields):
                if field not in allowed:
                    self.fields.pop(field, None)
            self.fields.pop('mark_cash_paid', None)

#Staff Forms
ROLE_CHOICES = [
    ('engineer', 'Engineer'),
    ('service_manager', 'Service Manager'),
    ('accountant', 'Accountant'),
    ('tally_user', 'Tally User'),
]

# ➕ Add Staff Form
class AddStaffForm(forms.ModelForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'password-input', 'autocomplete': 'new-password'}),
        validators=[MinLengthValidator(6, message="Password must be at least 6 characters long.")]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['username', 'email']:
            self.fields[field].widget.attrs.update({'autocomplete': 'off'})
        self.fields['password'].widget.attrs.update({'autocomplete': 'new-password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_staff = True
        if commit:
            user.save()
        return user


# ✏️ Edit Staff Form
class EditStaffForm(forms.ModelForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'password-input'}),
        required=False,
        validators=[MinLengthValidator(6, message="Password must be at least 6 characters long.")]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        user.is_staff = True
        if commit:
            user.save()
        return user


# 🧑‍🔧 Manager Edit Form
class ComplaintManagerEditForm(forms.ModelForm):
    assigned_engineer = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='engineer'),
        required=False,
        label='Assign Engineer'
    )
    service_cost = forms.DecimalField(
        required=True,
        min_value=0,
        error_messages={'min_value': 'Service cost cannot be negative.'}
    )

    class Meta:
        model = Complaint
        fields = ['assigned_engineer', 'service_cost']

    def __init__(self, *args, **kwargs):
        self.service_cost_editable = kwargs.pop('service_cost_editable', True)
        super().__init__(*args, **kwargs)

        if not self.service_cost_editable:
            self.fields['service_cost'].disabled = True


from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomPasswordResetForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label="Username")
    email = forms.EmailField(required=True, label="Email")

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        if username and email:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise ValidationError("Invalid username or email.")

            if user.email != email:
                raise ValidationError("The email does not match the username.")
        return cleaned_data