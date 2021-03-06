from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from emailconfirmation.models import EmailConfirmation


def confirm_email(request, confirmation_key, success_url=None):
    confirmation_key = confirmation_key.lower()
    email_address = EmailConfirmation.objects.confirm_email(confirmation_key)
    if email_address and success_url:
        messages.success(request, _("Thanks for confirming your email."))
        return HttpResponseRedirect(success_url)
    return render_to_response("emailconfirmation/confirm_email.html", {
        "email_address": email_address,
    }, context_instance=RequestContext(request))
