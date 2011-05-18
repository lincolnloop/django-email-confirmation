from django import template
from django.contrib.auth.models import User

from emailconfirmation import models

register = template.Library()


@register.filter
def verified_emails(user):
    """
    This filter returns a list of verified emails for a user.

    The emails are ordered by primary first and then alphabetically.

    If the user is not authenticated, this will still return an empty queryset.
    """
    if not isinstance(user, User):
        return models.EmailAddress.objects.none()
    return models.EmailAddress.objects.filter(user=user, verified=True)\
        .order_by('-primary', 'email')
