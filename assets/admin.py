from __future__ import unicode_literals, absolute_import
from datetime import date, timedelta
from django.conf.urls import url
from django.contrib.admin import register
from django.core.urlresolvers import reverse
from django.forms import Form, FileField
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from reversion.admin import VersionAdmin
from six import StringIO

from .models import Vendor, Invoice, SoftwareLicense, HardwareModel, HardwareAsset
from .utils import humanise_age


@register(Vendor)
class VendorAdmin(VersionAdmin):
    list_display = (
        'name', 'account_rep', 'contact_email', 'contact_phone', 'website',
        'software_licences', 'hardware_assets')
    search_fields = ('name', 'details', 'account_rep', 'website')

    def software_licences(self, obj):
        return obj.softwarelicense_set.count()

    def hardware_assets(self, obj):
        return obj.hardwareasset_set.count()


@register(Invoice)
class InvoiceAdmin(VersionAdmin):
    date_hierarchy = 'date'
    list_display = ('job_number', 'vendor', 'vendor_ref', 'date', 'total_value')
    list_filter = ('vendor',)
    search_fields = (
        'vendor__name', 'vendor_ref', 'job_number', 'etj_number', 'notes')


@register(SoftwareLicense)
class SoftwareLicenseAdmin(VersionAdmin):
    list_display = ('name', 'vendor', 'oss')
    list_filter = ('oss', 'vendor')
    search_fields = ('name', 'url', 'support', 'support_url', 'vendor__name')
    raw_id_fields = ('org_unit', 'assigned_user')


@register(HardwareModel)
class HardwareModelAdmin(VersionAdmin):
    list_display = ('vendor', 'model_type', 'model_no')
    search_fields = ('vendor__name', 'model_type', 'model_no')


@register(HardwareAsset)
class HardwareAssetAdmin(VersionAdmin):
    date_hierarchy = 'date_purchased'
    fieldsets = (
        ('Asset details', {
            'fields': (
                'asset_tag', 'finance_asset_tag', 'serial', 'vendor',
                'hardware_model', 'status', 'date_purchased', 'invoice',
                'purchased_value', 'notes')
        }),
        ('Location & ownership details', {
            'fields': ('assigned_user', 'location', 'cost_centre')
        }),
        ('Extra data (history)', {
            'fields': ('extra_data_ro',)
        }),
    )
    list_display = (
        'asset_tag', 'vendor', 'model_type', 'hardware_model', 'serial', 'status',
        'age', 'location', 'assigned_user')
    list_filter = ('status', 'vendor')
    raw_id_fields = (
        'vendor', 'hardware_model', 'invoice', 'assigned_user', 'location', 'cost_centre')
    search_fields = (
        'asset_tag', 'vendor__name', 'hardware_model__model_type',
        'hardware_model__model_no')
    readonly_fields = ['extra_data_ro']
    # Override the default reversion/change_list.html template:
    change_list_template = 'admin/assets/hardwareasset/change_list.html'

    def model_type(self, obj):
        return obj.hardware_model.model_type

    def age(self, obj):
        d = date.today() - obj.date_purchased
        max_age = timedelta(days=obj.hardware_model.lifecycle * 365)

        if d > max_age:
            if obj.hardware_model.lifecycle == 1:
                y = "year"
            else:
                y = "years"
            return mark_safe('<font color="#FF0000"><b>{}</b></font> (max {} {})'.format(
                humanise_age(d), obj.hardware_model.lifecycle, y))
        else:
            return humanise_age(d)

    def extra_data_ro(self, obj):
        return obj.get_extra_data_html()
    extra_data_ro.short_description = 'extra data'

    def get_urls(self):
        urls = super(HardwareAssetAdmin, self).get_urls()
        extra_urls = [
            url(
                r'^import/$',
                self.admin_site.admin_view(self.asset_import),
                name='asset_import'),
            url(
                r'^import/confirm/$',
                self.admin_site.admin_view(self.asset_import_confirm),
                name='asset_import_confirm'),
        ]
        return extra_urls + urls

    class AssetImportForm(Form):
        assets_csv = FileField()

    def asset_import(self, request):
        """Displays a form prompting user to upload CSV containing assets.
        Validates data in the uploaded file and prompts the user for confirmation.
        """
        from .utils import validate_csv  # Avoid circular import.

        if request.method == 'POST':
            form = self.AssetImportForm(request.POST, request.FILES)
            if form.is_valid():
                # Perform validation on the CSV file.
                fileobj = request.FILES['assets_csv']
                (num_assets, errors, warnings, notes) = validate_csv(fileobj)
                context = dict(
                    self.admin_site.each_context(request),
                    title='Hardware asset import',
                    csv=fileobj.read(),
                    record_count=num_assets,
                    errors=errors,
                    warnings=warnings,
                    notes=notes
                )
                # Stop and complain if we've got errors.
                if errors:
                    return TemplateResponse(
                        request, 'admin/hardwareasset_import_errors.html', context)

                # Otherwise, render the confirmation page.
                return TemplateResponse(
                    request, 'admin/hardwareasset_import_confirm.html', context)
        else:
            form = self.AssetImportForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            title='Hardware asset import'
        )
        return TemplateResponse(
            request, 'admin/hardwareasset_import_start.html', context)

    def asset_import_confirm(self, request):
        """Receives a POST request from the user, indicating that they would
        like to proceed with the import.
        """
        from .utils import validate_csv, import_csv  # Avoid circular import.

        if request.method != 'POST':
            return HttpResponseRedirect(reverse('admin:asset_import'))

        # Build a file object from the CSV data in POST and validate the input
        fileobj = StringIO(request.POST['csv'])
        (num_assets, errors, warnings, notes) = validate_csv(fileobj)

        context = dict(
            self.admin_site.each_context(request),
            title='Hardware asset import',
            record_count=num_assets,
            errors=errors,
            warnings=warnings,
            notes=notes
        )
        # Stop and complain if we've got errors.
        if errors:
            return TemplateResponse(
                request, 'admin/hardwareasset_import_errors.html', context)

        # Otherwise, render the success page.
        assets_created = import_csv(fileobj)
        context['assets_created'] = assets_created
        context['record_count'] = len(assets_created)
        return TemplateResponse(
            request, 'admin/hardwareasset_import_complete.html', context)
