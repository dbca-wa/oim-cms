from django.contrib.auth.models import User
from django.test import TestCase, Client
import json
from mixer.backend.django import mixer
import random
import string

from organisation.models import DepartmentUser, Location, OrgUnit, CostCentre
from registers.models import ITSystem


def random_dpaw_email():
    """Return a random email address ending in dpaw.wa.gov.au
    """
    s = ''.join(random.choice(string.ascii_letters) for i in range(20))
    return '{}@dpaw.wa.gov.au'.format(s)


class ApiTestCase(TestCase):
    client = Client()

    def setUp(self):
        # Generate some other DepartmentUser objects.
        mixer.cycle(5).blend(
            DepartmentUser, photo=None, active=True,
            email=random_dpaw_email, org_unit=None,
            cost_centre=None)
        # Generate some locations.
        self.loc1 = mixer.blend(Location, manager=None)
        self.loc2 = mixer.blend(Location, manager=None)
        # Generate a basic org structure.
        # NOTE: don't use mixer to create OrgUnit objects (it breaks MPTT).
        self.dept = OrgUnit.objects.create(name='Department 1', unit_type=0)
        self.div1 = OrgUnit.objects.create(
            name='Divison 1', unit_type=1, parent=self.dept, location=self.loc1)
        self.cc1 = CostCentre.objects.create(
            name='Cost centre 1', code='001', division=self.div1, org_position=self.div1)
        self.div2 = OrgUnit.objects.create(
            name='Divison 2', unit_type=1, parent=self.dept, location=self.loc2)
        self.cc2 = CostCentre.objects.create(
            name='Cost centre 2', code='002', division=self.div2, org_position=self.div2)
        # Give each of the divisions some members.
        users = DepartmentUser.objects.all()
        self.user1 = users[0]
        self.user1.org_unit = self.div1
        self.user1.cost_centre = self.cc1
        self.user1.save()
        self.div1.manager = self.user1
        self.div1.save()
        self.user2 = users[1]
        self.user2.org_unit = self.div2
        self.user2.cost_centre = self.cc2
        self.user2.save()
        self.div2.manager = self.user2
        self.div2.save()
        # Generate some IT Systems.
        self.it1 = mixer.blend(ITSystem, status=0, owner=self.user1)
        self.it2 = mixer.blend(ITSystem, status=1, owner=self.user2)
        # Generate a test user for endpoint responses.
        self.testuser = User.objects.create_user(
            username='testuser', email='user@dpaw.wa.gov.au.com', password='pass')
        # Create a DepartmentUser object for testuser.
        mixer.blend(
            DepartmentUser, photo=None, active=True, email=self.testuser.email,
            org_unit=None, cost_centre=None)
        # Log in testuser by default.
        self.client.login(username='testuser', password='pass')


class ProfileTestCase(ApiTestCase):
    url = '/api/profile'

    def test_profile_api_get(self):
        """Test the profile API endpoint GET response
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_profile_api_post(self):
        """Test the profile API endpoint GET response
        """
        response = self.client.get(self.url)
        j = json.loads(response.content)
        obj = j['objects'][0]
        self.assertFalse(obj['telephone'])
        tel = '9111 1111'
        response = self.client.post(self.url, {'telephone': tel})
        self.assertEqual(response.status_code, 200)
        j = json.loads(response.content)
        obj = j['objects'][0]
        self.assertEqual(obj['telephone'], tel)

    def test_profile_api_anon(self):
        """Test that anonymous users can't use the profile endpoint
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


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
        # Remove members from an org unit to test exclusion.
        self.user1.org_unit = None
        self.user1.cost_centre = None
        self.user1.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Division 1 won't be present in the response.
        self.assertNotContains(response, self.div1.name)

    def test_data_cost_centre(self):
        """Test the data_cost_centre API endpoint
        """
        url = '/api/options?list=cost_centre'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # 001 will be present in the response.
        self.assertContains(response, self.cc1.code)
        # Add 'inactive' to Division 1 name to inactivate the CC.
        self.div1.name = 'Division 1 (inactive)'
        self.div1.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # 001 won't be present in the response.
        self.assertNotContains(response, self.cc1.code)

    def test_data_org_unit(self):
        """Test the data_org_unit API endpoint
        """
        url = '/api/options?list=org_unit'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Org unit names will be present in the response.
        self.assertContains(response, self.dept.name)
        self.assertContains(response, self.div1.name)
        self.assertContains(response, self.div2.name)

    def test_data_dept_user(self):
        """Test the data_dept_user API endpoint
        """
        url = '/api/options?list=dept_user'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # User 1 will be present in the response.
        self.assertContains(response, self.user1.email)
        # Make a user inactive to test excludion
        self.user1.active = False
        self.user1.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # User 1 won't be present in the response.
        self.assertNotContains(response, self.user1.email)


class UserResourceTestCase(ApiTestCase):

    def test_user_list(self):
        """Test the UserResource list responses
        """
        url = '/api/users'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        r = json.loads(response.content)
        self.assertTrue(isinstance(r['objects'], list))
        # Test the compact response.
        url = '/api/users?compact=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Test the minimal response.
        url = '/api/users?minimal=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Test filtering by email.
        url = '/api/users?email={}'.format(self.user1.email)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_org_structure(self):
        """Test the UserResource org_structure response
        """
        url = '/api/users?org_structure=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # User 1 will be present in the response.
        self.assertContains(response, self.user1.email)
        # Test sync_o365=true request parameter.
        self.div1.sync_o365 = False
        self.div1.save()
        url = '/api/users?org_structure=true&sync_o365=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Division 1 won't be present in the response.
        self.assertNotContains(response, self.div1.name)


class LocationResourceTestCase(ApiTestCase):

    def test_list(self):
        """Test the LocationResource list response
        """
        url = '/api/locations'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Test filtering by location_id.
        url = '/api/locations?location_id={}'.format(self.loc1.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ITSystemResourceTestCase(ApiTestCase):

    def test_list(self):
        """Test the LocationResource list response
        """
        url = '/api/itsystems/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # The 'development' IT system won't be in the response.
        self.assertNotContains(response, self.it2.name)
        # Test all request parameter.
        url = '/api/itsystems/?all'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # The 'development' IT system will be in the response.
        self.assertContains(response, self.it2.name)
        # Test filtering by system_id
        url = '/api/itsystems/?system_id={}'.format(self.it1.system_id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.it1.name)
        self.assertNotContains(response, self.it2.name)
