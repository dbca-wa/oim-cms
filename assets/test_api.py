from __future__ import unicode_literals, absolute_import
from mixer.backend.django import mixer
from oim_cms.test_api import ApiTestCase

from .models import HardwareAsset


class HardwareAssetResourceTestCase(ApiTestCase):

    def setUp(self):
        super(HardwareAssetResourceTestCase, self).setUp()
        # Create some hardware.
        mixer.cycle(2).blend(HardwareAsset)

    def test_list(self):
        url = '/api/hardware-assets/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        hw = HardwareAsset.objects.first()
        url = '/api/hardware-assets/{}/'.format(hw.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
