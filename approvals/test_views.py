from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from mixer.backend.django import mixer
from organisation.models import DepartmentUser
from .models import Approval

User = get_user_model()


class ApprovalViewsTestCase(TestCase):
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

    def test_approval_create_get(self):
        """Test the approval_create GET response
        """
        url = reverse('approval_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_approval_create_post(self):
        """Test the approval_create POST response
        """
        url = reverse('approval_create')
        self.assertEqual(Approval.objects.count(), 0)
        response = self.client.post(url, {
            'approver': self.du2.pk,
            'proposal_desc': 'Test approval request',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Approval.objects.count(), 1)

    def test_approval_detail(self):
        """Test the approval_detail view
        """
        app = mixer.blend(Approval, approver=self.du2)
        url = reverse('approval_detail', kwargs={'pk': app.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_approval_confirm(self):
        """Test the approval_confirm view
        """
        app = mixer.blend(Approval, approver=self.du2)
        self.assertFalse(app.confirmed_date)
        # Log in user2.
        self.client.logout()
        self.client.login(username=self.user2.username, password='pass')
        url = reverse('approval_confirm', kwargs={'guid': app.guid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        app = Approval.objects.get(pk=app.pk)  # Refresh from db.
        self.assertTrue(app.confirmed_date)
