from django.core import mail
from django.test import TestCase

from django.contrib.auth.models import User

from emailconfirmation.models import EmailAddress, EmailConfirmation

class EmailConfirmationTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="daphne")
        self.email = "daphne@example.com"


class EmailAddressManagerTests(EmailConfirmationTestCase):

    def test_add_email(self):
        """
        ``add_email`` creates and returns the ``EmailAddress`` object and sends
        a confirmation email.

        """
        result = EmailAddress.objects.add_email(self.user, self.email)

        self.assertEqual(result, EmailAddress.objects.get(user=self.user, email=self.email))
        self.assertEqual(mail.outbox[-1].to, [self.email])


    def test_add_dupe_email(self):
        """
        ``add_email`` returns ``None`` and sends no confirmation if that
        address already exists for that user.

        """
        EmailAddress.objects.create(user=self.user, email=self.email)

        result = EmailAddress.objects.add_email(self.user, self.email)

        self.assertEqual(result, None)
        self.assertEqual(EmailAddress.objects.filter(user=self.user, email=self.email).count(), 1)
        self.assertEqual(len(mail.outbox), 0)


    def test_get_primary(self):
        """
        ``get_primary`` returns the primary ``EmailAddress`` for a given user.

        """
        main = EmailAddress.objects.create(user=self.user, email=self.email, primary=True)
        other = EmailAddress.objects.create(user=self.user, email="other@example.com")

        result = EmailAddress.objects.get_primary(self.user)

        self.assertEqual(result, main)


    def test_get_primary_none(self):
        """
        ``get_primary`` returns ``None`` if the given user has no primary
        e-mail.

        """
        main = EmailAddress.objects.create(user=self.user, email=self.email)

        result = EmailAddress.objects.get_primary(self.user)

        self.assertEqual(result, None)


    def test_get_users_for(self):
        """
        ``get_users_for`` returns a list of all the users who have the given
        e-mail address as a verified ``EmailAddress``.

        """
        scooby = User.objects.create(username="scooby")

        EmailAddress.objects.create(user=self.user, email=self.email, verified=True)
        EmailAddress.objects.create(user=scooby, email=self.email, verified=True)

        result = EmailAddress.objects.get_users_for(self.email)

        self.assertEqual(set(result), set([scooby, self.user]))


    def test_get_users_for_unverified(self):
        """
        ``get_users_for`` does not return users who have the given
        ``EmailAddress``, but unverified.

        """
        scooby = User.objects.create(username="scooby")

        EmailAddress.objects.create(user=self.user, email=self.email)
        EmailAddress.objects.create(user=scooby, email=self.email)

        result = EmailAddress.objects.get_users_for(self.email)

        self.assertEqual(result, [])



class EmailAddressTests(EmailConfirmationTestCase):

    def test_set_as_primary(self):
        """
        ``set_as_primary`` sets an email address as primary, sets the
        ``User.email`` field to that address, and returns ``True``.

        """
        email = EmailAddress.objects.create(user=self.user, email=self.email)
        result = email.set_as_primary()

        self.assertEqual(result, True)
        self.assertEqual(email.primary, True)
        self.assertEqual(EmailAddress.objects.get(pk=email.pk).primary, True)
        self.assertEqual(self.user.email, self.email)


    def test_set_as_primary_replace(self):
        """
        ``set_as_primary`` happily replaces an existing primary.

        """
        first = EmailAddress.objects.create(user=self.user, email="other@example.com")
        first.set_as_primary()

        email = EmailAddress.objects.create(user=self.user, email=self.email)
        result = email.set_as_primary()

        self.assertEqual(result, True)
        self.assertEqual(email.primary, True)
        self.assertEqual(EmailAddress.objects.get(pk=email.pk).primary, True)
        self.assertEqual(EmailAddress.objects.get(pk=first.pk).primary, False)
        self.assertEqual(self.user.email, self.email)


    def test_set_as_primary_conditional(self):
        """
        With the ``conditional=True`` argument, ``set_as_primary`` returns
        False rather than replace an existing primary.

        """
        first = EmailAddress.objects.create(user=self.user, email="other@example.com")
        first.set_as_primary()

        email = EmailAddress.objects.create(user=self.user, email=self.email)
        result = email.set_as_primary(conditional=True)

        self.assertEqual(result, False)
        self.assertEqual(email.primary, False)
        self.assertEqual(EmailAddress.objects.get(pk=email.pk).primary, False)
        self.assertEqual(EmailAddress.objects.get(pk=first.pk).primary, True)
        self.assertEqual(self.user.email, first.email)


    def test_set_as_primary_conditional_success(self):
        """
        With the ``conditional=True`` argument, ``set_as_primary`` still works
        normally if there is no existing primary.

        """
        first = EmailAddress.objects.create(user=self.user, email="other@example.com")

        email = EmailAddress.objects.create(user=self.user, email=self.email)
        result = email.set_as_primary(conditional=True)

        self.assertEqual(result, True)
        self.assertEqual(email.primary, True)
        self.assertEqual(EmailAddress.objects.get(pk=email.pk).primary, True)
        self.assertEqual(self.user.email, self.email)


    def test_unicode(self):
        email = EmailAddress.objects.create(user=self.user, email=self.email)

        self.assertEqual(unicode(email), u"%s (%s)" % (self.email, self.user))
