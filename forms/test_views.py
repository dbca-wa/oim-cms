from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from mixer.backend.django import mixer
from organisation.models import DepartmentUser
from forms.api import ITSystemObj, PeopleObj, SaveITSystemRequest
from registers.models import ITSystem

#from .models import Approval

User = get_user_model()


class ITSystemFormsViewsTestCase(TestCase):
    client = Client()

    def setUp(self):
        # Create User and linked DepartmentUser objects.
        self.du1 = mixer.blend(DepartmentUser, photo=None)
        self.user1 = User.objects.create_user(
            username=self.du1.username, email=self.du1.email)
        self.user1.set_password('pass')
        self.user1.save()
        # Log in user1 by default.
        self.client.login(username=self.user1.username, password='pass')
        self.du2 = mixer.blend(DepartmentUser, photo=None)
        self.user2 = User.objects.create_user(
            username=self.du2.username, email=self.du2.email)
        self.user2.set_password('pass')
        self.user2.save()

        self.itsystem = mixer.blend(ITSystem)

    def test_api_itsystemreq(self):
        """Test the api_itsystemreq GET response
        """
        
        url = reverse('api_itsystemreq')
        response = self.client.get(url, data={'reqid': self.itsystem.pk})
        self.assertEqual(response.status_code, 200)

