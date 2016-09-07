from django.contrib.auth.models import User
from django.test import TestCase, Client
import json
from mixer.backend.django import mixer
import random
import string

from registers.models import OrgUnit, CostCentre
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
        # Log in testuser by default.
        self.client.login(username='testuser', password='pass')
        # Generate some DepartmentUser objects.
        mixer.cycle(5).blend(
            DepartmentUser, photo=None, active=True,
            email=random_dpaw_email, org_unit=None,
            cost_centre=None)
        # Generate a basic org structure.
        # NOTE: don't use mixer to create OrgUnit objects (breaks MPTT).
        self.dept = OrgUnit.objects.create(name='Department 1', unit_type=0)
        self.div1 = OrgUnit.objects.create(
            name='Divison 1', unit_type=1, parent=self.dept)
        self.cc1 = CostCentre.objects.create(
            name='Cost centre 1', code='001', division=self.div1, org_position=self.div1)
        self.div2 = OrgUnit.objects.create(
            name='Divison 2', unit_type=1, parent=self.dept)
        self.cc2 = CostCentre.objects.create(
            name='Cost centre 2', code='002', division=self.div2, org_position=self.div2)
        # Give each of the divisions some members.
        users = DepartmentUser.objects.all()
        self.user1 = users[0]
        self.user1.org_unit = self.div1
        self.user1.cost_centre = self.cc1
        self.user1.save()
        self.user2 = users[1]
        self.user2.org_unit = self.div2
        self.user2.cost_centre = self.cc2
        self.user2.save()


class OptionResourceTestCase(ApiTestCase):

    def test_data_org_structure(self):
        """Test the data_org_structure API endpoint
        """
        url = '/api/options?list=org_structure'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Division 1 will be present in the response.
        self.assertContains(response, self.div1.name)
        # Response can be deserialised into a dict.
        r = json.loads(response.content)
        self.assertTrue(isinstance(r, dict))
        # Deserialised response contains a list.
        self.assertTrue(isinstance(r['objects'], list))

    def test_data_org_structure_inactive(self):
        """Test the data_org_structure API endpoint only returns units with members
        """
        self.user1.org_unit = None
        self.user1.cost_centre = None
        self.user1.save()
        url = '/api/options?list=org_structure'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Division 1 won't be present in the response.
        self.assertIs(response.content.find(self.div1.name), -1)

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
