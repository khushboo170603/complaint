from django import forms
from product.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'serial_number',
            'model_name',
            'sold_to',
            'sold_date',
            'installation_date',
            'assigned_engineer',
            'invoice',
            'warranty_start',
            'warranty_end',
        ]
        widgets = {
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sold_to': forms.TextInput(attrs={'class': 'form-control'}),
            'sold_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'installation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_engineer': forms.Select(attrs={'class': 'form-control'}),
            'invoice': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'warranty_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ Filter to show only engineers
        if 'assigned_engineer' in self.fields:
            self.fields['assigned_engineer'].queryset = User.objects.filter(profile__role='engineer')
