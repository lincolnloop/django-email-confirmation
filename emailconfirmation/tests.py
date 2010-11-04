from django.core import mail
from django.test import TestCase

from django.contrib.auth.models import User

from emailconfirmation.models import EmailAddress, EmailConfirmation

class EmailConfirmationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="daphne")



class EmailAddressTests(EmailConfirmationTestCase):
    def test_add_email(self):
        EmailAddress.objects.add_email(self.user, "daphne@example.com")

        self.assertEqual(EmailAddress.objects.filter(user=self.user, email="daphne@example.com").count(), 1)
        self.assertEqual(mail.outbox[-1].to, ["daphne@example.com"])
