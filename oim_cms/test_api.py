from django.contrib.auth.models import User
from django.test import TestCase, Client
from mixer.backend.django import mixer
import random
import string

from organisation.models import DepartmentUser


def random_dbca_email():
    """Return a random email address ending in dbca.wa.gov.au
    """
    s = ''.join(random.choice(string.ascii_letters) for i in range(20))
    return '{}@dbca.wa.gov.au'.format(s)


class ApiTestCase(TestCase):
    client = Client()

    def setUp(self):
        # Generate some other DepartmentUser objects.
        mixer.cycle(8).blend(DepartmentUser, username=mixer.RANDOM, email=random_dbca_email)
        # Generate a test user for endpoint responses.
        self.testuser = User.objects.create_user(
            username='testuser', email='user@dbca.wa.gov.au.com', password='pass')
        # Create a DepartmentUser object for testuser.
        mixer.blend(DepartmentUser, username=mixer.RANDOM, email=self.testuser.email)
        # Log in testuser by default.
        self.client.login(username='testuser', password='pass')
