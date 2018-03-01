from __future__ import unicode_literals, absolute_import
from datetime import date, datetime, timedelta
from django.conf.urls import url
from django.contrib.admin import register
from django.core.urlresolvers import reverse
from django.forms import Form, FileField
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from reversion.admin import VersionAdmin
from six import StringIO
import unicodecsv as csv

from .models import Vendor, HardwareModel, HardwareAsset, SoftwareAsset
from .utils import humanise_age


@register(Vendor)
class VendorAdmin(VersionAdmin):
    list_display = (
        'name', 'account_rep', 'contact_email', 'contact_phone', 'website',
        'hardware_assets')
    search_fields = ('name', 'details', 'account_rep', 'website')

    def hardware_assets(self, obj):
        return obj.hardwareasset_set.count()


@register(HardwareModel)
class HardwareModelAdmin(VersionAdmin):
    list_display = ('model_no', 'model_type', 'vendor')
    list_filter = ('model_type',)
    search_fields = ('vendor__name', 'model_type', 'model_no')


@register(HardwareAsset)
class HardwareAssetAdmin(VersionAdmin):
    date_hierarchy = 'date_purchased'
    exclude = ('invoice',)
    fieldsets = (
        ('Hardware asset details', {
            'fields': (
                'asset_tag', 'finance_asset_tag', 'serial', 'vendor', 'hardware_model',
                'status', 'notes', 'service_request_url')
        }),
        ('Location & ownership details', {
            'fields': (
                'cost_centre', 'location', 'assigned_user', 'date_purchased', 'invoice_copy',
                'purchased_value', 'is_asset', 'local_property', 'warranty_end')
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
        'vendor', 'hardware_model', 'assigned_user', 'location', 'cost_centre')
    search_fields = (
        'asset_tag', 'vendor__name', 'serial', 'hardware_model__model_type',
        'hardware_model__vendor__name', 'hardware_model__model_no', 'service_request_url',
        'location__name', 'assigned_user__email')
    readonly_fields = ['extra_data_ro']
    # Override the default reversion/change_list.html template:
    change_list_template = 'admin/assets/hardwareasset/change_list.html'

    def model_type(self, obj):
        return obj.hardware_model.model_type

    def age(self, obj):
        if not obj.date_purchased:
            return ''
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
                r'^import/$', self.admin_site.admin_view(self.asset_import),
                name='asset_import'),
            url(
                r'^import/confirm/$', self.admin_site.admin_view(self.asset_import_confirm),
                name='asset_import_confirm'),
            url(r'^export/$', self.hardwareasset_export, name='hardwareasset_export'),
        ]
        return extra_urls + urls

    def hardwareasset_export(self, request):
        """Export all HardwareAssets to a CSV.
        """
        f = StringIO()
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, encoding='utf-8')
        writer.writerow([
            'ASSET TAG', 'FINANCE ASSET TAG', 'SERIAL', 'VENDOR', 'MODEL TYPE', 'HARDWARE MODEL',
            'STATUS', 'COST CENTRE', 'LOCATION', 'ASSIGNED USER', 'DATE PURCHASED',
            'PURCHASED VALUE', 'SERVICE REQUEST URL', 'LOCAL PROPERTY', 'IS ASSET',
            'WARRANTY END'])
        for i in HardwareAsset.objects.all():
            writer.writerow([
                i.asset_tag, i.finance_asset_tag, i.serial, i.vendor,
                i.hardware_model.get_model_type_display(), i.hardware_model, i.get_status_display(),
                i.cost_centre.code if i.cost_centre else '', i.location if i.location else '',
                i.assigned_user if i.assigned_user else '',
                datetime.strftime(i.date_purchased, '%d/%b/%Y') if i.date_purchased else '',
                i.purchased_value, i.service_request_url, i.local_property, i.is_asset,
                datetime.strftime(i.warranty_end, '%d/%b/%Y') if i.warranty_end else ''])

        response = HttpResponse(f.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=hardwareasset_export.csv'
        return response

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


@register(SoftwareAsset)
class SoftwareAssetAdmin(VersionAdmin):
    date_hierarchy = 'date_purchased'
    exclude = ('invoice',)
    fieldsets = (
        ('Software asset details', {
            'fields': (
                'name', 'url', 'vendor', 'publisher', 'support', 'support_expiry',
                'purchased_value', 'notes', 'service_request_url')
        }),
        ('License details', {
            'fields': ('license', 'license_details', 'license_count')
        }),
        ('Asset ownership details', {
            'fields': ('cost_centre', 'date_purchased', 'invoice_copy')
        }),
    )
    list_display = ('name', 'vendor', 'license')
    list_filter = ('license',)
    raw_id_fields = ('org_unit', 'cost_centre')
    search_fields = ('name', 'vendor__name', 'service_request_url')
