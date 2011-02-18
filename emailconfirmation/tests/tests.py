import datetime

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.signals import template_rendered

from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from emailconfirmation import models, signals



NO_SETTING = object()


class EmailConfirmationTestCase(TestCase):

    def _template_rendered(self, sender, template, context, **kwargs):
        self.templates.append(template)
        self.contexts.append(context)

    def setUp(self):
        self.user = User.objects.create(username="daphne")
        self.email = "daphne@example.com"

        self._old_confirmation_days = getattr(models.settings,
                                              "EMAIL_CONFIRMATION_DAYS",
                                              NO_SETTING)
        models.settings.EMAIL_CONFIRMATION_DAYS = 10

        self.templates = []
        self.contexts = []
        template_rendered.connect(self._template_rendered)


    def tearDown(self):
        if self._old_confirmation_days is NO_SETTING:
            delattr(models.settings._wrapped, "EMAIL_CONFIRMATION_DAYS")
        else:
            models.settings.EMAIL_CONFIRMATION_DAYS = self._old_confirmation_days

        template_rendered.disconnect(self._template_rendered)



class EmailAddressManagerTests(EmailConfirmationTestCase):

    def test_add_email(self):
        """
        ``add_email`` creates and returns the ``EmailAddress`` object and sends
        a confirmation email (creating an ``EmailConfirmation`` object).

        """
        result = models.EmailAddress.objects.add_email(self.user, self.email)

        self.assertEqual(result, models.EmailAddress.objects.get(user=self.user, email=self.email))
        self.assertEqual(mail.outbox[-1].to, [self.email])
        self.assertEqual(models.EmailConfirmation.objects.filter(email_address=result).count(), 1)


    def test_add_dupe_email(self):
        """
        ``add_email`` returns ``None`` and sends no confirmation if that
        address already exists for that user.

        """
        models.EmailAddress.objects.create(user=self.user, email=self.email)

        result = models.EmailAddress.objects.add_email(self.user, self.email)

        self.assertEqual(result, None)
        self.assertEqual(models.EmailAddress.objects.filter(user=self.user, email=self.email).count(), 1)
        self.assertEqual(len(mail.outbox), 0)


    def test_get_primary(self):
        """
        ``get_primary`` returns the primary ``EmailAddress`` for a given user.

        """
        main = models.EmailAddress.objects.create(user=self.user, email=self.email, primary=True)
        other = models.EmailAddress.objects.create(user=self.user, email="other@example.com")

        result = models.EmailAddress.objects.get_primary(self.user)

        self.assertEqual(result, main)


    def test_get_primary_none(self):
        """
        ``get_primary`` returns ``None`` if the given user has no primary
        e-mail.

        """
        main = models.EmailAddress.objects.create(user=self.user, email=self.email)

        result = models.EmailAddress.objects.get_primary(self.user)

        self.assertEqual(result, None)


    def test_get_users_for(self):
        """
        ``get_users_for`` returns a list of all the users who have the given
        e-mail address as a verified ``EmailAddress``.

        """
        scooby = User.objects.create(username="scooby")

        models.EmailAddress.objects.create(user=self.user, email=self.email, verified=True)
        models.EmailAddress.objects.create(user=scooby, email=self.email, verified=True)

        result = models.EmailAddress.objects.get_users_for(self.email)

        self.assertEqual(set(result), set([scooby, self.user]))


    def test_get_users_for_unverified(self):
        """
        ``get_users_for`` does not return users who have the given
        ``EmailAddress``, but unverified.

        """
        scooby = User.objects.create(username="scooby")

        models.EmailAddress.objects.create(user=self.user, email=self.email)
        models.EmailAddress.objects.create(user=scooby, email=self.email)

        result = models.EmailAddress.objects.get_users_for(self.email)

        self.assertEqual(result, [])



class EmailAddressTests(EmailConfirmationTestCase):

    def test_set_as_primary(self):
        """
        ``set_as_primary`` sets an email address as primary, sets the
        ``User.email`` field to that address, and returns ``True``.

        """
        email = models.EmailAddress.objects.create(user=self.user, email=self.email)
        result = email.set_as_primary()

        self.assertEqual(result, True)
        self.assertEqual(email.primary, True)
        self.assertEqual(models.EmailAddress.objects.get(pk=email.pk).primary, True)
        self.assertEqual(self.user.email, self.email)


    def test_set_as_primary_replace(self):
        """
        ``set_as_primary`` happily replaces an existing primary.

        """
        first = models.EmailAddress.objects.create(user=self.user, email="other@example.com")
        first.set_as_primary()

        email = models.EmailAddress.objects.create(user=self.user, email=self.email)
        result = email.set_as_primary()

        self.assertEqual(result, True)
        self.assertEqual(email.primary, True)
        self.assertEqual(models.EmailAddress.objects.get(pk=email.pk).primary, True)
        self.assertEqual(models.EmailAddress.objects.get(pk=first.pk).primary, False)
        self.assertEqual(self.user.email, self.email)


    def test_set_as_primary_conditional(self):
        """
        With the ``conditional=True`` argument, ``set_as_primary`` returns
        False rather than replace an existing primary.

        """
        first = models.EmailAddress.objects.create(user=self.user, email="other@example.com")
        first.set_as_primary()

        email = models.EmailAddress.objects.create(user=self.user, email=self.email)
        result = email.set_as_primary(conditional=True)

        self.assertEqual(result, False)
        self.assertEqual(email.primary, False)
        self.assertEqual(models.EmailAddress.objects.get(pk=email.pk).primary, False)
        self.assertEqual(models.EmailAddress.objects.get(pk=first.pk).primary, True)
        self.assertEqual(self.user.email, first.email)


    def test_set_as_primary_conditional_success(self):
        """
        With the ``conditional=True`` argument, ``set_as_primary`` still works
        normally if there is no existing primary.

        """
        first = models.EmailAddress.objects.create(user=self.user, email="other@example.com")

        email = models.EmailAddress.objects.create(user=self.user, email=self.email)
        result = email.set_as_primary(conditional=True)

        self.assertEqual(result, True)
        self.assertEqual(email.primary, True)
        self.assertEqual(models.EmailAddress.objects.get(pk=email.pk).primary, True)
        self.assertEqual(self.user.email, self.email)


    def test_unicode(self):
        email = models.EmailAddress.objects.create(user=self.user, email=self.email)

        self.assertEqual(unicode(email), u"%s (%s)" % (self.email, self.user))



class EmailConfirmationManagerTests(EmailConfirmationTestCase):

    def setUp(self):
        super(EmailConfirmationManagerTests, self).setUp()


    def test_confirm_email(self):
        """
        ``confirm_email`` marks an email as verified and primary
        (conditionally), sends the ``email_confirmed`` signal, and returns the
        confirmed ``EmailAddress`` object.

        """
        received = []
        def listener(sender, email_address, **kwargs):
            received.append(email_address)
        signals.email_confirmed.connect(listener, sender=models.EmailConfirmation)

        address = models.EmailAddress.objects.add_email(self.user, self.email)
        confirmation = models.EmailConfirmation.objects.get(email_address=address)

        result = models.EmailConfirmation.objects.confirm_email(confirmation.confirmation_key)

        self.assertEqual(result, address)
        self.assertEqual(result.verified, True)
        self.assertEqual(result.primary, True)
        self.assertEqual(received, [address])


    def test_confirm_email_conditional(self):
        """
        ``confirm_email`` won't replace an existing primary.

        """
        first = models.EmailAddress.objects.create(user=self.user,
                                                   email="other@example.com",
                                                   primary=True)

        address = models.EmailAddress.objects.add_email(self.user, self.email)
        confirmation = models.EmailConfirmation.objects.get(email_address=address)

        result = models.EmailConfirmation.objects.confirm_email(confirmation.confirmation_key)

        self.assertEqual(result.primary, False)
        self.assertEqual(models.EmailAddress.objects.get(pk=first.pk).primary, True)


    def test_confirm_email_bad_key(self):
        """
        ``confirm_email`` returns ``None`` if it gets a bad key.

        """
        result = models.EmailConfirmation.objects.confirm_email("junk")

        self.assertEqual(result, None)


    def test_confirm_email_expired(self):
        """
        ``confirm_email`` returns ``None`` if it gets an expired key.

        """
        address = models.EmailAddress.objects.add_email(self.user, self.email)
        confirmation = models.EmailConfirmation.objects.get(email_address=address)
        confirmation.sent = confirmation.sent - datetime.timedelta(days=11)
        confirmation.save()

        result = models.EmailConfirmation.objects.confirm_email(confirmation.confirmation_key)

        self.assertEqual(result, None)


    def test_send_confirmation(self):
        """
        ``send_confirmation`` sends a confirmation email to the given address
        (by rendering subject and body templates) and creates and returns an
        ``EmailConfirmation`` object.

        """
        address = models.EmailAddress.objects.create(user=self.user, email=self.email)
        confirmation = models.EmailConfirmation.objects.send_confirmation(address)

        self.assertEqual(mail.outbox[-1].to, [self.email])
        self.assertEqual([t.name for t in self.templates],
                          ["emailconfirmation/email_confirmation_subject.txt",
                           "emailconfirmation/email_confirmation_message.txt"])
        self.assertEqual([d for d in self.contexts[0]],
                         [d for d in self.contexts[1]])
        c = self.contexts[0]
        self.assertEqual(c["user"], self.user)
        self.assertEqual(c["activate_url"], "http://example.com/confirm/%s/" % confirmation.confirmation_key)
        self.assertEqual(c["current_site"], Site.objects.get_current())
        self.assertEqual(c["confirmation_key"], confirmation.confirmation_key)


    def test_send_confirmation_respects_DEFAULT_HTTP_PROTOCOL(self):
        """
        ``send_confirmation`` generates a confirmation URL with the protocol
        defined by the DEFAULT_HTTP_PROTOCOL setting.

        """
        _old_default_protocol = getattr(models.settings, "DEFAULT_HTTP_PROTOCOL", NO_SETTING)
        models.settings.DEFAULT_HTTP_PROTOCOL = "https"

        address = models.EmailAddress.objects.create(user=self.user, email=self.email)
        confirmation = models.EmailConfirmation.objects.send_confirmation(address)

        self.assertTrue(self.contexts[0]["activate_url"].startswith("https://"))

        if _old_default_protocol is NO_SETTING:
            delattr(models.settings._wrapped, "DEFAULT_HTTP_PROTOCOL")
        else:
            models.settings.DEFAULT_HTTP_PROTOCOL = _old_default_protocol


    def test_delete_expired_confirmations(self):
        """
        ``delete_expired_confirmations`` does just that.

        """
        address = models.EmailAddress.objects.add_email(self.user, self.email)
        confirmation = models.EmailConfirmation.objects.get(email_address=address)
        confirmation.sent = confirmation.sent - datetime.timedelta(days=11)
        confirmation.save()

        models.EmailConfirmation.objects.delete_expired_confirmations()

        self.assertFalse(models.EmailConfirmation.objects.exists())



class EmailConfirmationTests(EmailConfirmationTestCase):

    def test_key_expired(self):
        """
        ``key_expired`` returns ``True`` for an expired key, ``False``
        otherwise.

        """
        address = models.EmailAddress.objects.add_email(self.user, self.email)
        confirmation = models.EmailConfirmation.objects.get(email_address=address)

        self.assertEqual(confirmation.key_expired(), False)

        confirmation.sent = confirmation.sent - datetime.timedelta(days=11)
        confirmation.save()

        self.assertEqual(confirmation.key_expired(), True)


    def test_unicode(self):
        address = models.EmailAddress.objects.add_email(self.user, self.email)
        confirmation = models.EmailConfirmation.objects.get(email_address=address)

        self.assertEqual(unicode(confirmation), u"confirmation for %s" % confirmation.email_address)



class ViewTests(EmailConfirmationTestCase):

    def test_confirm(self):
        """
        ``confirm`` takes the given confirmation key and attempts to confirm that email.

        """
        address = models.EmailAddress.objects.add_email(self.user, self.email)
        confirmation = models.EmailConfirmation.objects.get(email_address=address)

        url = reverse("emailconfirmation_confirm", args=[confirmation.confirmation_key])

        response = self.client.get(url)

        self.assertTemplateUsed(response, "emailconfirmation/confirm_email.html")
        self.assertEqual(response.context["email_address"], address)
        self.assertEqual(models.EmailAddress.objects.get(pk=address.pk).verified, True)
        self.assertContains(response, "Confirmed %s" % self.email)


    def test_confirm_bad_key(self):
        """
        ``confirm`` takes the given confirmation key and attempts to confirm that email.

        """
        url = reverse("emailconfirmation_confirm", args=["junk"])

        response = self.client.get(url)

        self.assertEqual(response.context["email_address"], None)
        self.assertContains(response, "Invalid or expired key")


    def test_confirm_lowercases_key(self):
        """
        ``confirm`` lowercases the key it is given.

        """
        address = models.EmailAddress.objects.add_email(self.user, self.email)
        confirmation = models.EmailConfirmation.objects.get(email_address=address)

        url = reverse("emailconfirmation_confirm", args=[confirmation.confirmation_key.upper()])

        response = self.client.get(url)

        self.assertEqual(response.context["email_address"], address)
        self.assertEqual(models.EmailAddress.objects.get(pk=address.pk).verified, True)
        self.assertContains(response, "Confirmed %s" % self.email)

