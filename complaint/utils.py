import random
import string
import uuid
from .models import Profile

def user_has_role(user, role_name):
    """
    Safely checks if a user has a specific role.
    """
    try:
        return user.profile.role == role_name
    except Profile.DoesNotExist:
        return False

def generate_ticket_number():
    """
    Generates a consistent 8-character ticket number with 'TCKT-' prefix.
    """
    return f"TCKT-{uuid.uuid4().hex[:8].upper()}"
