from django.contrib.auth.models import User
from django.test import TestCase, Client
import json
from mixer.backend.django import mixer
import random
import string

from tracking.models import DepartmentUser


def random_dpaw_email():
    """Return a random email address ending in dpaw.wa.gov.au
    """
    s = ''.join(random.choice(string.ascii_letters) for i in range(20))
    return '{}@dpaw.wa.gov.au'.format(s)


class ApiTestCase(TestCase):
    client = Client()

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='user@dpaw.wa.gov.au.com', password='pass')
        self.admin = User.objects.create_user(
            username='admin', email='admin@dpaw.wa.gov.com', password='pass', is_superuser=True)
        # Generate some fixture data
        mixer.cycle(10).blend(
            DepartmentUser, photo=None, active=True,
            email=random_dpaw_email)
        # Log in testuser by default.
        self.client.login(username='testuser', password='pass')


class OptionResourceTestCase(ApiTestCase):

    def test_data_dept_user(self):
        """Test the data_dept_user API endpoint returns a serialised list
        """
        url = '/api/options?list=dept_user'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        r = json.loads(response.content)
        self.assertTrue(isinstance(r['objects'], list))


class UserResourceTestCase(ApiTestCase):

    def test_user_list(self):
        """Test the full user list API response
        """
        url = '/api/users'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        r = json.loads(response.content)
        self.assertTrue(isinstance(r['objects'], list))
