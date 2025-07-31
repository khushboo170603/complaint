# complaint/sms_utils.py

from .models import Complaint, SMSLog

def send_sms_mock(mobile, ticket_number):
    """
    Mocks sending an SMS to a customer and logs the message.

    Args:
        mobile (str): The customer's mobile number.
        ticket_number (str): The auto-generated complaint ticket number.
    """
    message = f"Your complaint has been registered. Ticket No: {ticket_number}"

    # ✅ Mock sending
    print(f"[MOCK SMS] Sent to {mobile}: {message}")

    # ✅ Save SMS log to SMSLog model
    SMSLog.objects.create(mobile_number=mobile, message=message)

    # ✅ Optional: update complaint's sms_log field (if it exists)
    try:
        complaint = Complaint.objects.get(ticket_number=ticket_number)
        complaint.sms_log = message
        complaint.save()
    except Complaint.DoesNotExist:
        print(f"[ERROR] Complaint with ticket number '{ticket_number}' not found.")
