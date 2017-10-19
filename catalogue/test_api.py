from django.contrib.auth.models import User
from django.test import TestCase
import json
from mixer.backend.django import mixer

from catalogue.models import Record, Application


class RecordAPITestCase(TestCase):

    def setUp(self):
        # Generate a test user for endpoint responses.
        self.testuser = User.objects.create_user(
            username='testuser', email='user@dpaw.wa.gov.au.com', password='pass')
        # Log in testuser by default.
        self.client.login(username='testuser', password='pass')
        # Generate some Record objects.
        mixer.cycle(8).blend(Record, title=mixer.RANDOM)

    def test_list(self):
        url = '/catalogue/api/records/'
        params = {'format': 'json'}
        resp = self.client.get(url, data=params)
        self.assertEqual(resp.status_code, 200)

    def test_list_filter(self):
        url = '/catalogue/api/records/'
        params = {'format': 'json'}
        resp = self.client.get(url, data=params)
        unfiltered = json.loads(resp.content.decode('utf-8'))
        records = Record.objects.all()
        rec1, rec2 = records[0], records[1]
        # Generate an Application
        app = mixer.blend(Application, name='test')
        app.records.add(rec1)
        params = {'format': 'json', 'application__name': 'test'}
        resp = self.client.get(url, data=params)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, rec1.title)
        self.assertNotContains(resp, rec2.title)
        # The filtered response will be shorter than the unfiltered one.
        filtered = json.loads(resp.content.decode('utf-8'))
        self.assertTrue(len(unfiltered) > len(filtered))
