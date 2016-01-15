from __future__ import unicode_literals, absolute_import
from django.conf import settings
from django.contrib import admin
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from reversion.admin import VersionAdmin
from mptt.admin import MPTTModelAdmin
from leaflet.admin import LeafletGeoAdmin

from .models import Hardware, Device, SoftwareLicense, CostCentre, Backup, ITSystem, OrgUnit, Location, SecondaryLocation, Process, Function


class HardwareAdmin(VersionAdmin):
    list_display = ('device_type', 'name', 'username', 'email', 'cost_centre', 'ipv4', 'ports', 'serials')
    list_filter = ('device_type', 'ports', 'cost_centre',)
    search_fields = ('name', 'username', 'email', 'ipv4', 'serials', 'ports')
    list_editable = ('cost_centre',)


class ITSystemAdmin(VersionAdmin):
    list_display = ('system_id', 'name', 'acronym', 'status', 'function', 'process', 'cost_centre', 'owner', 'custodian', 'preferred_contact', 'access', 'authentication')
    list_filter = ('access', 'authentication', 'status')
    search_fields = ('system_id', 'owner__username', 'owner__email', 'name', 'acronym', 'description', 'custodian__username', 'custodian__email', 'link', 'documentation', 'cost_centre__code')
    raw_id_fields = ("devices", "owner", "custodian", "data_custodian", "preferred_contact", "cost_centre")
    readonly_fields = ("extra_data_pretty", "description_html")
    fields = (
        ("system_id", "acronym"), ("name", "status"), ("process", "function"),
        ("cost_centre", "owner"), ("custodian", "data_custodian"),
        ("preferred_contact", "link"), ("documentation", "status_html"),
        ("authentication", "access"), ("description_html", "extra_data_pretty"),
        ("description", "extra_data")
    )


class BackupAdmin(VersionAdmin):
    raw_id_fields = ("system", "parent_host")
    list_display = ("name", "host", "operating_system", "role", "status", "last_tested", "backup_documentation")
    list_editable = ("operating_system", "role", "status", "last_tested")
    search_fields = ("system__name", "parent_host__name")
    list_filter = ("role", "status", "operating_system")
    date_hierarchy = 'last_tested'

    def name(self, obj):
        return obj.system.name.split(".")[0]

    def host(self, obj):
        if not obj.parent_host:
            return None
        return obj.parent_host.name.split(".")[0]

    def backup_documentation(self, obj):
        return render_to_string("registers/backup_snippet.html", {
            "obj": obj, "settings": settings, "name": self.name(obj)}
        )


class DeviceAdmin(VersionAdmin):
    list_display = ('name', 'owner', 'cost_centre', 'guid')
    raw_id_fields = ('owner', 'cost_centre')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return self.readonly_fields + ('guid',)
        return self.readonly_fields


class OrgUnitAdmin(MPTTModelAdmin, VersionAdmin):
    list_display = ("name", "unit_type", "users", "members", "it_systems", "cc", "acronym", "manager")
    search_fields = ('name', 'acronym')
    raw_id_fields = ('manager', "parent", "location")
    list_filter = ("unit_type", "location")

    def users(self, obj):
        return format_html(
            '<a href="{}?org_unit={}">{}</a>',
            reverse("admin:tracking_departmentuser_changelist"),
            obj.pk, obj.departmentuser_set.count())

    def members(self, obj):
        return format_html(
            '<a href="{}?org_unit__in={}">{}</a>',
            reverse("admin:tracking_departmentuser_changelist"),
            ",".join([str(o.pk) for o in obj.get_descendants(include_self=True)]), 
            obj.members().count())

    def it_systems(self, obj):
        return format_html(
            '<a href="{}?org_unit={}">{}</a>',
            reverse("admin:registers_itsystem_changelist"),
            obj.pk, obj.itsystem_set.count())


class CostCentreAdmin(VersionAdmin):
    list_display = ('code', 'name', 'org_position', 'division', 'users', 'manager', 'business_manager', 'admin', 'tech_contact')
    search_fields = ('code', 'name', 'org_position__name', 'division__name', 'org_position__acronym', 'division__acronym')
    raw_id_fields = ('org_position', 'manager', 'business_manager', 'admin', 'tech_contact')

    def users(self, obj):
        return format_html(
            '<a href="{}?cost_centre={}">{}</a>',
            reverse("admin:tracking_departmentuser_changelist"),
            obj.pk, obj.departmentuser_set.count())


class LocationAdmin(LeafletGeoAdmin, VersionAdmin):
    list_display = ('name', 'address', 'phone', 'fax', 'email', 'point')
    search_fields = ('name', 'address', 'phone', 'fax', 'email')
    settings_overrides = {
        'DEFAULT_CENTER': (-31.0, 115.0),
        'DEFAULT_ZOOM': 5
    }


admin.site.register(Hardware, HardwareAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Backup, BackupAdmin)
admin.site.register(CostCentre, CostCentreAdmin)
admin.site.register(OrgUnit, OrgUnitAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(SecondaryLocation, VersionAdmin)
admin.site.register(SoftwareLicense, VersionAdmin)
admin.site.register(Process, VersionAdmin)
admin.site.register(Function, VersionAdmin)
admin.site.register(ITSystem, ITSystemAdmin)
