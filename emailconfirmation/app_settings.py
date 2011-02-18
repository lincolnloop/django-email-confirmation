from django.conf import settings

EMAIL_CONFIRMATION_DAYS = getattr(settings, 'EMAIL_CONFIRMATION_DAYS', 14)
