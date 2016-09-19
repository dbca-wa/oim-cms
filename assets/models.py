from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField
from django.db import models

from organisation.models import DepartmentUser
from tracking.models import CommonFields


class Vendor(models.Model):
    """Represents the vendor for an external product (software or hardware).
    """
    name = models.CharField(max_length=256, unique=True)
    details = models.TextField(blank=True)
    extra_data = JSONField(default=dict(), null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class SoftwareLicense(CommonFields):
    """Represents a software licensing arrangement.
    """
    name = models.CharField(max_length=256, unique=True)
    url = models.URLField(max_length=2000, null=True, blank=True)
    support = models.TextField(
        blank=True, help_text='Support timeframe or scope')
    support_url = models.URLField(max_length=2000, null=True, blank=True)
    oss = models.NullBooleanField(
        default=None,
        help_text='Open-source/free software license?')
    primary_user = models.ForeignKey(
        DepartmentUser,
        on_delete=models.PROTECT,
        null=True,
        blank=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        null=True,
        blank=True)
    used_licenses = models.PositiveSmallIntegerField(default=0, editable=False)
    available_licenses = models.PositiveSmallIntegerField(
        default=0, null=True, blank=True)
    license_details = models.TextField(
        blank=True, help_text='Direct license keys or details')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
