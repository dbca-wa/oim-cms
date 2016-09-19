from django.contrib.admin import register
from reversion.admin import VersionAdmin

from .models import Vendor, SoftwareLicense


@register(Vendor)
class VendorAdmin(VersionAdmin):
    pass


@register(SoftwareLicense)
class SoftwareLicenseAdmin(VersionAdmin):
    list_display = ('name', 'vendor', 'oss')
    list_filter = ('oss', 'vendor')
    search_fields = ('name', 'url', 'support', 'support_url', 'vendor')
    raw_id_fields = ('org_unit', 'primary_user')
