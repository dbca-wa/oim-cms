from django.test import TestCase
from mixer.backend.django import mixer

from .models import ITSystem


class ITSystemTestCase(TestCase):

    def setUp(self):
        mixer.blend(ITSystem)
        self.it = ITSystem.objects.first()

    def test_save(self):
        """Test save() override for ITSystem
        """
        # The following fields have defaults.
        self.assertTrue(self.it.system_id)
        self.assertTrue(self.it.status_display)
        self.assertTrue(self.it.authentication_display)
        self.assertTrue(self.it.access_display)
        # Test other fields set on save.
        self.it.criticality = 1
        self.it.availability = 1
        self.it.system_type = 1
        self.it.save()
        self.assertTrue(self.it.criticality_display)
        self.assertTrue(self.it.availability_display)
        self.assertTrue(self.it.system_type_display)
