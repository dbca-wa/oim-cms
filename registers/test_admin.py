from django.apps import apps
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from mixer.backend.django import mixer

from .models import ITSystem


class ITSystemAdminTest(TestCase):

    client = Client()

    def setUp(self):
        mixer.blend(ITSystem)
        self.it = ITSystem.objects.first()
        # Generate a test user for admin responses.
        self.testuser = User.objects.create_superuser(
            username='testuser', email='user@dpaw.wa.gov.au.com', password='pass')
        # Log in testuser by default.
        self.client.login(username='testuser', password='pass')

    def test_changelist(self):
        """Test the ITSystem changelist response
        """
        url = reverse('admin:registers_itsystem_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_change(self):
        """Test the ITSystem change form response
        """
        url = reverse('admin:registers_itsystem_change', args=(self.it.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class PermissionsTestCase(TestCase):
    group = None

    def setUp(self):
        User.objects.create(
            username="test-user1",
            password="password1",
            is_superuser=False,
            is_active=True,
            is_staff=True)
        User.objects.create(
            username="test-user2",
            password="password1",
            is_superuser=False,
            is_active=True,
            is_staff=True)
        User.objects.create(
            username="test-user3",
            password="password1",
            is_superuser=True,
            is_active=True,
            is_staff=True)
        User.objects.create(
            username="test-user4",
            password="password1",
            is_superuser=False,
            is_active=True,
            is_staff=False)

        mods = list(apps.get_app_config('organisation').get_models())
        grp = Group.objects.get_or_create(name='OIM Staff')
        self.group = grp[0]

        for model in mods:
            ct = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=ct)
            self.group.permissions.set(perms)

    def test_in_group(self):
        '''Test user who is not a super user but is staff and in oim staff group'''
        test_user1 = User.objects.get(username='test-user1')
        test_user2 = User.objects.get(username='test-user2')
        test_user3 = User.objects.get(username='test-user3')
        test_user4 = User.objects.get(username='test-user4')

        # add test_user1 to group
        test_user1.groups.add(self.group)

        self.assertEqual(
            test_user1.has_module_perms('organisation'),
            True)  # in oim group
        self.assertEqual(
            test_user2.has_module_perms('organisation'),
            False)  # staff not in group
        self.assertEqual(
            test_user3.has_module_perms('organisation'),
            True)  # super user
        self.assertEqual(
            test_user4.has_module_perms('organisation'),
            False)  # user who is not staff
        self.assertEqual(
            test_user1.has_module_perms('some_app'),
            False)  # test functinality in another group
        # test supper user functinality in another group
        self.assertEqual(test_user3.has_module_perms('some_app'), True)
