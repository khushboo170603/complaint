from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'serial_number',
        'model_name',
        'sold_to',
        'sold_date',
        'installation_date',
        'assigned_engineer',
        'warranty_start',
        'warranty_end',
        'warranty_status',
    )
    search_fields = ('serial_number', 'model_name', 'sold_to')
    list_filter = ('sold_date', 'warranty_start', 'warranty_end', 'assigned_engineer')
