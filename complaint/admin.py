from django.contrib import admin
from django.utils.html import format_html
from .models import Complaint, Profile, SMSLog

# 🔹 SMS Log Admin (read-only)
@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    readonly_fields = ('mobile_number', 'message', 'sent_at')
    list_display = ('mobile_number', 'sent_at')
    search_fields = ('mobile_number', 'message')
    ordering = ('-sent_at',)


# 🔹 Complaint Admin with Image Previews
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket_number', 'customer_name', 'product', 'status', 'assigned_engineer')
    list_filter = ('status', 'assigned_engineer')
    search_fields = ('ticket_number', 'customer_name', 'product')

    fields = (
        'customer_name',
        'mobile_number',
        'product',
        'description',
        'ticket_number',
        'status',
        'assigned_engineer',
        'resolution_photo',
        'preview_resolution_photo',  # 👁️ Image preview
        'product_serial_number',
        'service_cost',
        'payment_method',
        'payment_proof',
        'preview_payment_proof',     # 👁️ Image preview
        'sms_log',
    )

    readonly_fields = (
        'ticket_number',
        'sms_log',
        'created_at',
        'updated_at',
        'preview_resolution_photo',
        'preview_payment_proof',
    )

    def preview_resolution_photo(self, obj):
        if obj.resolution_photo:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.resolution_photo.url)
        return "No resolution photo"
    preview_resolution_photo.short_description = "Resolution Photo Preview"

    def preview_payment_proof(self, obj):
        if obj.payment_proof:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.payment_proof.url)
        return "No payment proof"
    preview_payment_proof.short_description = "Payment Proof Preview"


# 🔹 Profile Admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)
