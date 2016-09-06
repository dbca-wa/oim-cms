from django.test import TestCase
from mixer.backend.django import mixer

from .models import (
    DepartmentUser, Computer, Mobile, EC2Instance, FreshdeskTicket,
    FreshdeskConversation, FreshdeskContact)


class DepartmentUserTestCase(TestCase):

    def setUp(self):
        mixer.blend(DepartmentUser, photo=None)
        self.du = DepartmentUser.objects.first()

    def test_save(self):
        """Test save() override for DepartmentUser
        """
        self.du.employee_id = '1'
        self.du.save()  # employee_id should be left-padded with zeroes.
        self.assertEqual(self.du.employee_id, '000001')
        self.du.employee_id = 'n/a'
        self.du.save()  # employee_id should be set to None.
        self.assertFalse(self.du.employee_id)
