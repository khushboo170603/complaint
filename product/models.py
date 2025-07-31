from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Product(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    model_name = models.CharField(max_length=100)
    sold_to = models.CharField(max_length=100)
    sold_date = models.DateField()
    installation_date = models.DateField(null=True, blank=True)
    assigned_engineer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'profile__role': 'engineer'}  # Optional: if you're using profile model with roles
    )
    invoice = models.FileField(upload_to='invoices/', null=True, blank=True)
    warranty_start = models.DateField(null=True, blank=True)
    warranty_end = models.DateField(null=True, blank=True)

    def warranty_status(self):
        from datetime import date
        today = date.today()
        if self.warranty_end and self.warranty_end >= today:
            return "Active"
        return "Expired"

    '''def __str__(self):
        return f"{self.model_name} ({self.serial_number})"'''
    
    def __str__(self):
        return self.model_name
