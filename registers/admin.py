from __future__ import unicode_literals, absolute_import
from django import forms
from django.conf.urls import url
from django.contrib.admin import register
from django.http import HttpResponse
from reversion.admin import VersionAdmin
from six import BytesIO
import unicodecsv
from .models import (
    UserGroup, ITSystemHardware, ITSystem, ITSystemDependency,
    Backup, BusinessService, BusinessFunction, BusinessProcess,
    ProcessITSystemRelationship)


@register(UserGroup)
class UserGroupAdmin(VersionAdmin):
    list_display = ('name', 'user_count')
    search_fields = ('name',)


@register(ITSystemHardware)
class ITSystemHardwareAdmin(VersionAdmin):
    list_display = ('computer', 'role', 'affected_itsystems')
    list_filter = ('role',)
    raw_id_fields = ('computer',)
    # Override the default reversion/change_list.html template:
    change_list_template = 'admin/registers/itsystemhardware/change_list.html'

    def affected_itsystems(self, obj):
        return obj.itsystem_set.all().exclude(status=3).count()
    affected_itsystems.short_description = 'IT Systems'

    def get_urls(self):
        urls = super(ITSystemHardwareAdmin, self).get_urls()
        urls = [
            url(r'^export/$',
                self.admin_site.admin_view(self.export),
                name='itsystemhardware_export'),
        ] + urls
        return urls

    def export(self, request):
        """Exports ITSystemHardware data to a CSV.
        """
        # Define fields to output.
        fields = [
            'hostname', 'location', 'role', 'it_system_system_id',
            'it_system_name', 'itsystem_availability', 'itsystem_criticality']

        # Write data for ITSystemHardware objects to the CSV.
        stream = BytesIO()
        wr = unicodecsv.writer(stream, encoding='utf-8')
        wr.writerow(fields)  # CSV header row.
        for i in ITSystemHardware.objects.all():
            # Write a row for each linked ITSystem (non-decommissioned).
            for it in i.itsystem_set.all().exclude(status=3):
                wr.writerow([
                    i.computer.hostname, i.computer.location, i.get_role_display(),
                    it.system_id, it.name, it.get_availability_display(),
                    it.get_criticality_display()])

        response = HttpResponse(stream.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=itsystemhardware_export.csv'
        return response


class ITSystemForm(forms.ModelForm):

    class Meta:
        model = ITSystem
        exclude = []

    def clean_biller_code(self):
        """Validation on the biller_code field: must be unique (ignore null values).
        """
        data = self.cleaned_data['biller_code']
        if ITSystem.objects.filter(biller_code=data).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('An IT System with this biller code already exists.')
        return data


@register(ITSystem)
class ITSystemAdmin(VersionAdmin):
    list_display = (
        'system_id', 'name', 'acronym', 'status', 'cost_centre', 'owner', 'custodian',
        'preferred_contact', 'access', 'authentication')
    list_filter = (
        'access',
        'authentication',
        'status',
        'contingency_plan_status',
        'system_type')
    search_fields = (
        'system_id', 'owner__username', 'owner__email', 'name', 'acronym', 'description',
        'custodian__username', 'custodian__email', 'link', 'documentation', 'cost_centre__code')
    raw_id_fields = (
        'owner', 'custodian', 'data_custodian', 'preferred_contact', 'cost_centre',
        'bh_support', 'ah_support')
    readonly_fields = ('extra_data_pretty', 'description_html')
    fields = [
        ('system_id', 'acronym'),
        ('name', 'status'),
        'link',
        ('cost_centre', 'owner'),
        ('custodian', 'data_custodian'),
        'preferred_contact',
        ('bh_support', 'ah_support'),
        'documentation',
        'technical_documentation',
        'status_html',
        ('authentication', 'access'),
        'description',
        'notes',
        ('criticality', 'availability'),
        'schema_url',
        'hardwares',
        'user_groups',
        'system_reqs',
        'system_type',
        'request_access',
        ('vulnerability_docs', 'recovery_docs'),
        'workaround',
        ('mtd', 'rto', 'rpo'),
        ('contingency_plan', 'contingency_plan_status'),
        'contingency_plan_last_tested',
        'system_health',
        'system_creation_date',
        'backup_info',
        'risks',
        'sla',
        'critical_period',
        'alt_processing',
        'technical_recov',
        'post_recovery',
        'variation_iscp',
        'user_notification',
        'other_projects',
        'function',
        'use',
        'capability',
        'unique_evidence',
        'point_of_truth',
        'legal_need_to_retain',
        'biller_code',
        'extra_data',
    ]
    # Override the default reversion/change_list.html template:
    change_list_template = 'admin/registers/itsystem/change_list.html'
    form = ITSystemForm  # Use the custom ModelForm.

    def get_urls(self):
        urls = super(ITSystemAdmin, self).get_urls()
        urls = [
            # Note that we don't wrap the view below in AdminSite.admin_view()
            # on purpose, as we want it generally accessible.
            url(r'^export/$', self.export, name='itsystem_export'),
        ] + urls
        return urls

    def export(self, request):
        """Exports ITSystem data to a CSV.
        """
        # Define fields to output.
        fields = [
            'system_id', 'name', 'acronym', 'status_display', 'description',
            'criticality_display', 'availability_display', 'system_type_display',
            'cost_centre', 'division_name', 'owner', 'custodian', 'data_custodian', 'preferred_contact',
            'link', 'documentation', 'technical_documentation', 'authentication_display',
            'access_display', 'request_access', 'status_html', 'schema_url',
            'bh_support', 'ah_support', 'system_reqs', 'vulnerability_docs',
            'workaround', 'recovery_docs', 'date_updated']

        # Write data for ITSystem objects to the CSV:
        stream = BytesIO()
        wr = unicodecsv.writer(stream, encoding='utf-8')
        wr.writerow(fields)
        for i in ITSystem.objects.all().order_by(
                'system_id').exclude(status=3):  # Exclude decommissioned
            wr.writerow([getattr(i, f) for f in fields])

        response = HttpResponse(stream.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=itsystem_export.csv'
        return response


@register(ITSystemDependency)
class ITSystemDependencyAdmin(VersionAdmin):
    list_display = ('itsystem', 'dependency', 'criticality')
    list_filter = ('criticality',)
    search_fields = ('itsystem__name', 'dependency__name')


@register(Backup)
class BackupAdmin(VersionAdmin):
    raw_id_fields = ('computer',)
    list_display = (
        'computer', 'operating_system', 'role', 'status', 'last_tested')
    list_editable = ('operating_system', 'role', 'status', 'last_tested')
    search_fields = ('computer__hostname',)
    list_filter = ('role', 'status', 'operating_system')
    date_hierarchy = 'last_tested'


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
