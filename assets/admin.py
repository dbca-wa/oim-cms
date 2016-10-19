from __future__ import unicode_literals, absolute_import
from django.contrib.admin import register
from reversion.admin import VersionAdmin

from .models import Vendor, Invoice, SoftwareLicense, HardwareModel, HardwareAsset


@register(Vendor)
class VendorAdmin(VersionAdmin):
    pass


@register(Invoice)
class InvoiceAdmin(VersionAdmin):
    pass


@register(SoftwareLicense)
class SoftwareLicenseAdmin(VersionAdmin):
    list_display = ('name', 'vendor', 'oss')
    list_filter = ('oss', 'vendor')
    search_fields = ('name', 'url', 'support', 'support_url', 'vendor')
    raw_id_fields = ('org_unit', 'primary_user')


@register(HardwareModel)
class HardwareModelAdmin(VersionAdmin):
    pass


@register(HardwareAsset)
class HardwareAssetAdmin(VersionAdmin):
    pass
