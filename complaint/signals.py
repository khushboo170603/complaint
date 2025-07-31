from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    🔹 This signal creates or updates the Profile
    whenever a User is created or saved.
    """
    if created:
        # Assign default role (e.g., customer)
        Profile.objects.create(user=instance, role='customer')
    else:
        profile, _ = Profile.objects.get_or_create(user=instance)
        profile.save()
