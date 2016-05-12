from __future__ import unicode_literals, absolute_import
from django.conf import settings
from django.contrib.admin import register, ModelAdmin
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from reversion.admin import VersionAdmin
from mptt.admin import MPTTModelAdmin
from leaflet.admin import LeafletGeoAdmin

from .models import (
    UserGroup, Software, Hardware, Device, SoftwareLicense, CostCentre,
    Backup, ITSystem, OrgUnit, Location, SecondaryLocation,
    Vendor, ITSystemHardware, BusinessService, BusinessFunction,
    BusinessProcess, ProcessITSystemRelationship, ITSystemDependency,
    DocumentApproval)


@register(DocumentApproval)
class DocumentApprovalAdmin(ModelAdmin):
    list_diplay = ('department_user', 'approval_role', 'date_created')
    raw_id_fields = ('department_user',)


@register(UserGroup)
class UserGroupAdmin(VersionAdmin):
    list_display = ('name', 'user_count')
    search_fields = ('name',)


@register(Software)
class SoftwareAdmin(VersionAdmin):
    list_display = ('name', 'url', 'license', 'os')
    list_filter = ('license', 'os')
    search_fields = (
        'name', 'url', 'license__name', 'license__url', 'license__support',
        'license__vendor__name')


@register(Hardware)
class HardwareAdmin(VersionAdmin):
    list_display = (
        'device_type', 'name', 'username', 'email', 'cost_centre', 'ipv4',
        'ports', 'serials', 'os')
    list_filter = ('device_type', 'os', 'ports', 'cost_centre')
    search_fields = (
        'name', 'username', 'email', 'ipv4', 'serials', 'ports', 'os__name')


@register(SoftwareLicense)
class SoftwareLicenseAdmin(VersionAdmin):
    list_display = ('name', 'vendor', 'oss')
    list_filter = ('oss', 'vendor')
    search_fields = ('name', 'url', 'support', 'support_url', 'vendor')
    raw_id_fields = ('org_unit', 'primary_user')


@register(ITSystem)
class ITSystemAdmin(VersionAdmin):
    list_display = (
        'system_id', 'name', 'acronym', 'status', 'cost_centre', 'owner', 'custodian',
        'preferred_contact', 'access', 'authentication')
    list_filter = ('access', 'authentication', 'status', 'contingency_plan_status')
    search_fields = (
        'system_id', 'owner__username', 'owner__email', 'name', 'acronym', 'description',
        'custodian__username', 'custodian__email', 'link', 'documentation', 'cost_centre__code')
    raw_id_fields = (
        'devices', 'owner', 'custodian', 'data_custodian', 'preferred_contact', 'cost_centre',
        'bh_support', 'ah_support')
    readonly_fields = ('extra_data_pretty', 'description_html')
    filter_horizontal = ('contingency_plan_approvals',)
    fields = (
        ('system_id', 'acronym'),
        ('name', 'status'),
        ('link',),
        ('cost_centre', 'owner'),
        ('custodian', 'data_custodian'),
        ('preferred_contact',),
        ('bh_support', 'ah_support'),
        ('documentation', 'technical_documentation'),
        ('status_html'),
        ('authentication', 'access'),
        ('description', 'extra_data'),
        ('criticality', 'availability'),
        ('schema_url'),
        ('softwares', 'hardwares'),
        ('user_groups'),
        ('system_reqs', 'system_type'),
        ('vulnerability_docs', 'recovery_docs'),
        ('workaround'),
        ('mtd', 'rto', 'rpo'),
        ('contingency_plan', 'contingency_plan_status'),
        ('contingency_plan_approvals'),
        ('contingency_plan_last_tested'),
    )

    def save_model(self, request, obj, form, change):
        """Override save_model in order to log any changes to the
        contingency_plan field.
        """
        # If contingency_plan changes, delete any associated DocumentApproval
        # objects.
        if obj._ITSystem__original_contingency_plan != obj.contingency_plan:
            # Clear the selected approvals from the modeladmin form.
            form.cleaned_data['contingency_plan_approvals'] = []
            approvals = [i for i in obj.contingency_plan_approvals.all()]
            obj.contingency_plan_approvals.clear()  # Remove M2M relationships
            obj.save()
            for i in approvals:
                i.delete()  # Delete each approval object.
        super(ITSystemAdmin, self).save_model(request, obj, form, change)


@register(Backup)
class BackupAdmin(VersionAdmin):
    raw_id_fields = ("system", "parent_host")
    list_display = (
        "name", "host", "operating_system", "role", "status", "last_tested", "backup_documentation")
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


@register(Device)
class DeviceAdmin(VersionAdmin):
    list_display = ('name', 'owner', 'cost_centre', 'guid')
    raw_id_fields = ('owner', 'cost_centre')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return self.readonly_fields + ('guid',)
        return self.readonly_fields


@register(OrgUnit)
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
            obj.members().count()
        )

    def it_systems(self, obj):
        return format_html(
            '<a href="{}?org_unit={}">{}</a>',
            reverse("admin:registers_itsystem_changelist"),
            obj.pk, obj.itsystem_set.count())


@register(CostCentre)
class CostCentreAdmin(VersionAdmin):
    list_display = (
        'code', 'name', 'org_position', 'division', 'users', 'manager', 'business_manager',
        'admin', 'tech_contact')
    search_fields = (
        'code', 'name', 'org_position__name', 'division__name', 'org_position__acronym',
        'division__acronym')
    raw_id_fields = ('org_position', 'manager', 'business_manager', 'admin', 'tech_contact')

    def users(self, obj):
        return format_html(
            '<a href="{}?cost_centre={}">{}</a>',
            reverse("admin:tracking_departmentuser_changelist"),
            obj.pk, obj.departmentuser_set.count())


@register(Location)
class LocationAdmin(LeafletGeoAdmin, VersionAdmin):
    list_display = ('name', 'address', 'phone', 'fax', 'email', 'point')
    search_fields = ('name', 'address', 'phone', 'fax', 'email')
    settings_overrides = {
        'DEFAULT_CENTER': (-31.0, 115.0),
        'DEFAULT_ZOOM': 5
    }


@register(ITSystemHardware)
class ITSystemHardwareAdmin(VersionAdmin):
    list_display = ('host', 'role')
    list_filter = ('role',)
    raw_id_fields = ('host',)


@register(BusinessService)
class BusinessServiceAdmin(VersionAdmin):
    list_display = ('number', 'name')
    search_fields = ('name', 'description')


@register(BusinessFunction)
class BusinessFunctionAdmin(VersionAdmin):
    list_display = ('name', 'function_services')
    list_filter = ('services',)
    search_fields = ('name', 'description')

    def function_services(self, obj):
        return ', '.join([str(i.number) for i in obj.services.all()])
    function_services.short_description = 'services'


@register(BusinessProcess)
class BusinessProcessAdmin(VersionAdmin):
    list_display = ('name', 'criticality')
    list_filter = ('criticality', 'functions')
    search_fields = ('name', 'description', 'functions__name')


@register(ProcessITSystemRelationship)
class ProcessITSystemRelationshipAdmin(VersionAdmin):
    list_display = ('process', 'itsystem', 'importance')
    list_filter = ('importance', 'process', 'itsystem')
    search_fields = ('process__name', 'itsystem__name')


@register(ITSystemDependency)
class ITSystemDependencyAdmin(VersionAdmin):
    list_display = ('itsystem', 'dependency', 'criticality')
    list_filter = ('criticality',)
    search_fields = ('itsystem__name', 'dependency__name')


@register(SecondaryLocation)
class SecondaryLocationAdmin(VersionAdmin):
    pass


@register(Vendor)
class VendorAdmin(VersionAdmin):
    pass
