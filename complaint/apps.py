from django.apps import AppConfig

class ComplaintConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'complaint'

    def ready(self):
        # ✅ Import signals so that Profile is auto-created/updated with User
        import complaint.signals
