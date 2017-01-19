from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client
from django_webtest import WebTest
from mixer.backend.django import mixer
from organisation.models import DepartmentUser
from registers.models import ITSystem


User = get_user_model()


class KnowledgeViewsTestCase(WebTest):
    client = Client()

    def setUp(self):
        # Create User and linked DepartmentUser objects.
        self.du1 = mixer.blend(DepartmentUser, photo=None)
        self.user1 = User.objects.create_user(
            username=self.du1.username, email=self.du1.email)
        self.user1.is_superuser = True
        self.user1.set_password('pass')
        self.user1.save()
        # Log in user1 by default.
        self.client.login(username=self.user1.username, password='pass')
        self.du2 = mixer.blend(DepartmentUser, photo=None)
        self.user2 = User.objects.create_user(
            username=self.du2.username, email=self.du2.email)
        self.user2.set_password('pass')
        self.user2.save()
        self.itsystem = mixer.blend(ITSystem, system_id='S001')

    def test_km_address_book(self):
        """Test the km_address_book GET response
        """
        url = reverse('km_address_book')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_km_user_accounts(self):
        """Test the km_user_accounts GET response
        """
        url = reverse('km_user_accounts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_km_itsystem_register(self):
        """Test the km_itsystem_register GET response
        """
        url = reverse('km_itsystem_register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_km_itsystem_detail(self):
        """Test the km_itsystem_detail GET response
        """
        url = reverse('km_itsystem_detail', kwargs={'system_id': self.itsystem.system_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_km_itsystem_update_get(self):
        """Test the km_itsystem_update GET response
        """
        url = reverse('km_itsystem_update', kwargs={'system_id': self.itsystem.system_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_km_itsystem_update_post(self):
        """Test the km_itsystem_update POST response
        """
        url = reverse('km_itsystem_update', kwargs={'system_id': self.itsystem.system_id})
        r = self.app.get(url, user='user1')
        form = r.form
        form['description'] = 'Test'
        r = form.submit().follow()
        self.assertEqual(r.status_code, 200)
        system = ITSystem.objects.get(pk=self.itsystem.pk)  # Re-read from db
        self.assertEqual(system.description, 'Test')

    # ==================================================
    # Legacy views below.
    # ==================================================

    def test_km_itsystemreq(self):
        """Test the km_itsystem GET response
        """
        url = reverse('km_itsystem')
        response = self.client.get(url, data={'reqid': self.itsystem.pk})
        self.assertEqual(response.status_code, 200)

    def test_km_peoplelist(self):
        """Test the km_peoplelist GET response
        """
        url = reverse('km_peoplelist')
        response = self.client.get(url, data={'keyword': '%'})
        self.assertEqual(response.status_code, 200)
