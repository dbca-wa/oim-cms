from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
import uuid

from organisation.models import DepartmentUser


@python_2_unicode_compatible
class Approval(models.Model):
    """Represents a unique, generic request for approval by one DepartmentUser
    to another.
    """
    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    guid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(
        DepartmentUser, editable=False, related_name='requester')
    approver = models.ForeignKey(
        DepartmentUser, related_name='approver',
        help_text='The staff member that is requested to approve the item.')
    proposal_url = models.URLField(
        max_length=2000, null=True, blank=True, verbose_name='proposal URL',
        help_text='Optional URL to the item that requires approval.')
    proposal_desc = models.TextField(
        null=True, blank=True, verbose_name='proposal description',
        help_text='Optional description of the item that requires approval.')
    confirmed_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '{} ({} -> {})'.format(self.pk, self.requester, self.approver)

    def get_absolute_url(self):
        return reverse('approval_detail', kwargs={'pk': self.pk})

    def get_confirm_html(self):
        """Generates the HTML for approval confirmation.
        """
        confirm_url = reverse('approval_confirm', kwargs={'guid': self.guid})
        t = '''Open the following URL in a browser to provide
        confirmation of this approval request: <a href="{0}">{0}</a>'''
        return t.format(confirm_url)
