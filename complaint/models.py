from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import uuid
from product.models import Product


# Extend User string representation for better dropdown display
User.__str__ = lambda self: self.get_full_name() or self.username

# 🔹 Extended User Profile with Roles
class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Service Manager'),
        ('engineer', 'Service Engineer'),
        ('accountant', 'Accountant'),
        ('tally', 'Tally User'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    class Meta:
        ordering = ['role']
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

ISSUE_TYPE_CHOICES = [
    ('Screen-blank', 'Screen Blank'),
    ('Total-Dead', 'Total Dead'),
    ('Installation', 'Installation'),
    ('App-Issue', 'App Issue'),
    ('Break', 'Break'),
    ('Sound-Problem', 'Sound Problem'),
    ('Touch-Issue', 'Touch Issue'),
    ('OPS-not-working', 'OPS Not Working'),
    ('Software-Issue', 'Software Issue'),
    ('Other', 'Other'),
]

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('pending', 'Pending'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('online', 'Online'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]

    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, null=True, blank=True)

    issue_type = models.CharField(max_length=50, choices=[
        ('Screen-blank', 'Screen Blank'),
        ('Total-Dead', 'Total Dead'),
        ('Installation', 'Installation'),
        ('App-Issue', 'App Issue'),
        ('Break', 'Break'),
        ('Sound-Problem', 'Sound Problem'),
        ('Touch-Issue', 'Touch Issue'),
        ('OPS-not-working', 'OPS Not Working'),
        ('Software-Issue', 'Software Issue'),
        ('Other', 'Other'),
    ], default='Other')

    description = models.TextField()
    ticket_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    assigned_engineer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolution_photo = models.ImageField(upload_to='resolution_photos/', blank=True, null=True)

    assigned_date = models.DateTimeField(null=True, blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)

    product_serial_number = models.CharField(max_length=100, blank=True, null=True)
    service_confirmation_photo = models.ImageField(upload_to='service_confirmations/', blank=True, null=True)

    service_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)

    # New fields for payment tracking
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )

    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    payment_confirmation_photo = models.ImageField(upload_to='payment_confirmations/', blank=True, null=True)

    sms_log = models.TextField(blank=True, null=True)

    # 🔹 Address Fields
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=150, blank=True, null=True)
    street = models.CharField(max_length=150, blank=True, null=True)
    landmark = models.CharField(max_length=150, blank=True, null=True)  # optional

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"TCKT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('update_complaint', args=[self.pk])

    def __str__(self):
        return f"{self.customer_name} - {self.product.name if self.product else 'Other'} - {self.ticket_number}"

    def full_address(self):
        parts = [
            self.street,
            self.area,
            self.landmark,
            self.city,
            self.state,
            self.pincode
        ]
        return ', '.join([p for p in parts if p])

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Customer Complaint"
        verbose_name_plural = "Customer Complaints"

# 🔹 SMS Log Model
class SMSLog(models.Model):
    mobile_number = models.CharField(max_length=15)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMS to {self.mobile_number} at {self.sent_at.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-sent_at']
        verbose_name = "SMS Log"
        verbose_name_plural = "SMS Logs"
