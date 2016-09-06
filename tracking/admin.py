from __future__ import absolute_import
from django import forms
from django.conf.urls import url
from django.contrib import messages
from django.contrib.admin import register, site, ModelAdmin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from StringIO import StringIO
import unicodecsv

from tracking.models import DepartmentUser, Computer, Mobile, EC2Instance, FreshdeskTicket
from tracking.utils import logger_setup, alesco_data_import, departmentuser_csv_report


@register(DepartmentUser)
class DepartmentUserAdmin(ModelAdmin):
    list_display = [
        'email', 'employee_id', 'username', 'active', 'vip', 'executive',
        'cost_centre', 'account_type', 'date_ad_updated']
    list_filter = ['account_type', 'active', 'vip', 'executive']
    search_fields = ['name', 'email', 'username', 'employee_id', 'preferred_name']
    raw_id_fields = ['parent', 'cost_centre', 'org_unit']
    readonly_fields = [
        'username', 'email', 'org_data_pretty', 'ad_data_pretty',
        'active', 'in_sync', 'ad_deleted', 'date_ad_updated', 'expiry_date',
        'alesco_data_pretty']
    fieldsets = (
        ('Email/username', {
            'fields': ('email', 'username'),
        }),
        ('Name and organisational fields', {
            'description': '''<p class="errornote">Do not edit information in this section
            without written permission from People Services or the cost centre manager
            (forms are required).</p>''',
            'fields': (
                'given_name', 'surname', 'name', 'employee_id',
                'cost_centre', 'org_unit', 'security_clearance',
                'name_update_reference'),
        }),
        ('Other details', {
            'fields': (
                'preferred_name', 'photo', 'title', 'parent',
                'account_type', 'position_type',
                'cost_centres_secondary', 'org_units_secondary',
                'telephone', 'mobile_phone', 'other_phone',
                'populate_primary_group', 'vip', 'executive', 'contractor',
                'secondary_locations', 'notes', 'working_hours', 'extra_data',
            )
        }),
        ('AD sync and HR data (read-only)', {
            'fields': (
                'active', 'in_sync', 'ad_deleted', 'date_ad_updated', 'expiry_date',
                'org_data_pretty', 'ad_data_pretty', 'alesco_data_pretty',
            )
        })
    )

    def save_model(self, request, obj, form, change):
        """Override save_model in order to log any changes to some fields:
        'given_name', 'surname', 'employee_id', 'cost_centre', 'name', 'org_unit'
        """
        logger = logger_setup('departmentuser_updates')
        l = 'DepartmentUser: {}, field: {}, original_value: {} new_value: {}, changed_by: {}, reference: {}'
        if obj._DepartmentUser__original_given_name != obj.given_name:
            logger.info(l.format(
                obj.email, 'given_name', obj._DepartmentUser__original_given_name, obj.given_name,
                request.user.username, obj.name_update_reference
            ))
        if obj._DepartmentUser__original_surname != obj.surname:
            logger.info(l.format(
                obj.email, 'surname', obj._DepartmentUser__original_surname, obj.surname,
                request.user.username, obj.name_update_reference
            ))
        if obj._DepartmentUser__original_employee_id != obj.employee_id:
            logger.info(l.format(
                obj.email, 'employee_id', obj._DepartmentUser__original_employee_id,
                obj.employee_id, request.user.username, obj.name_update_reference
            ))
        if obj._DepartmentUser__original_cost_centre != obj.cost_centre:
            logger.info(l.format(
                obj.email, 'cost_centre', obj._DepartmentUser__original_cost_centre,
                obj.cost_centre, request.user.username, obj.name_update_reference
            ))
        if obj._DepartmentUser__original_name != obj.name:
            logger.info(l.format(
                obj.email, 'name', obj._DepartmentUser__original_name, obj.name,
                request.user.username, obj.name_update_reference
            ))
        if obj._DepartmentUser__original_org_unit != obj.org_unit:
            logger.info(l.format(
                obj.email, 'org_unit', obj._DepartmentUser__original_org_unit, obj.org_unit,
                request.user.username, obj.name_update_reference
            ))
        obj.save()

    def get_urls(self):
        urls = super(DepartmentUserAdmin, self).get_urls()
        urls = [
            url(r'^alesco-import/$', self.admin_site.admin_view(self.alesco_import), name='alesco_import'),
            url(r'^export/$', self.admin_site.admin_view(self.export), name='departmentuser_export'),
        ] + urls
        return urls

    class AlescoImportForm(forms.Form):
        spreadsheet = forms.FileField()

    def alesco_import(self, request):
        """Displays a form prompting user to upload an Excel spreadsheet of
        employee data from Alesco. Temporary measure until database link is
        worked out.
        """
        context = dict(
            site.each_context(request),
            title='Alesco data import'
        )

        if request.method == 'POST':
            form = self.AlescoImportForm(request.POST, request.FILES)
            if form.is_valid():
                upload = request.FILES['spreadsheet']
                # Write the uploaded file to a temp file.
                f = open('/tmp/alesco-data.xlsx', 'w')
                f.write(upload.read())
                f.close()
                alesco_data_import(f.name)
                messages.info(request, 'Spreadsheet uploaded successfully!')
                return redirect('admin:tracking_departmentuser_changelist')
        else:
            form = self.AlescoImportForm()
        context['form'] = form

        return TemplateResponse(request, 'tracking/alesco_import.html', context)

    def export(self, request):
        """Exports DepartmentUser data to a CSV, and returns
        """
        data = departmentuser_csv_report()
        response = HttpResponse(data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=departmentuser_export.csv'
        return response


@register(Computer)
class ComputerAdmin(ModelAdmin):
    list_display = ['sam_account_name',
                    'hostname', 'managed_by', 'probable_owner']
    search_fields = ['sam_account_name', 'hostname']


@register(Mobile)
class MobileAdmin(ModelAdmin):
    list_display = ('identity', 'model', 'imei', 'serial_number',
                    'asset_id', 'finance_asset_id', 'registered_to')
    search_fields = ('identity', 'model', 'imei',
                     'serial_number', 'asset_id', 'finance_asset_id')


@register(EC2Instance)
class EC2InstanceAdmin(ModelAdmin):
    list_display = ('name', 'ec2id', 'launch_time', 'running', 'next_state')
    search_fields = ('name', 'ec2id', 'launch_time')
    readonly_fields = ["extra_data_pretty", "extra_data"]


@register(FreshdeskTicket)
class FreshdeskTicketAdmin(ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'ticket_id', 'created_at', 'freshdesk_requester', 'subject',
        'source_display', 'status_display', 'priority_display', 'type',
        'it_system')
    fields = (
        'ticket_id', 'created_at', 'freshdesk_requester', 'subject',
        'source_display', 'status_display', 'priority_display', 'type',
        'due_by', 'description_text', 'it_system')
    readonly_fields = (
        'attachments', 'cc_emails', 'created_at', 'custom_fields',
        'deleted', 'description', 'description_text', 'due_by',
        'email', 'fr_due_by', 'fr_escalated', 'fwd_emails',
        'group_id', 'is_escalated', 'name', 'phone', 'priority',
        'reply_cc_emails', 'requester_id', 'responder_id', 'source',
        'spam', 'status', 'subject', 'tags', 'ticket_id', 'to_emails',
        'type', 'updated_at', 'freshdesk_requester',
        'freshdesk_responder', 'du_requester', 'du_responder',
        # Callables below.
        'source_display', 'status_display', 'priority_display')
    search_fields = (
        'it_system__name', 'subject', 'description_text',
        'freshdesk_requester__name', 'freshdesk_requester__email',)

    def source_display(self, obj):
        return obj.get_source_display()
    source_display.short_description = 'Source'

    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Status'

    def priority_display(self, obj):
        return obj.get_priority_display()
    priority_display.short_description = 'Priority'

    def get_urls(self):
        urls = super(FreshdeskTicketAdmin, self).get_urls()
        urls = [
            url(r'^export-summary/$',
                self.admin_site.admin_view(self.export_summary),
                name='freshdeskticket_export_summary'),
        ] + urls
        return urls

    def export_summary(self, request):
        """Exports Freshdesk ticket summary data to a CSV.
        """
        from datetime import date
        from dateutil.relativedelta import relativedelta
        base = date.today()
        date_list = [base - relativedelta(months=x) for x in range(0, 12)]

        # Define fields to output.
        fields = ['month', 'category', 'subcategory', 'ticket_count']

        # Write data for ITSystemHardware objects to the CSV.
        stream = StringIO()
        wr = unicodecsv.writer(stream, encoding='utf-8')
        wr.writerow(fields)  # CSV header row.

        # Write month count of each category & subcategory
        for d in date_list:
            tickets = FreshdeskTicket.objects.filter(created_at__year=d.year, created_at__month=d.month)
            # Find the categories and subcategories for this queryset.
            cat = set()
            for t in tickets:  # Add tuples: (category, subcategory)
                cat.add((t.custom_fields['support_category'], t.custom_fields['support_subcategory']))
            cat = sorted(cat)
            # For each (category, subcategory), obtain a count of tickets.
            # TODO: save the category and subcategory onto each model so we
            # can just get Aggregate queries.
            for c in cat:
                count = 0
                for t in tickets:
                    if t.custom_fields['support_category'] == c[0] and t.custom_fields['support_subcategory'] == c[1]:
                        count += 1
                wr.writerow([d.strftime('%b-%Y'), c[0], c[1], count])

        response = HttpResponse(stream.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=freshdesktick_summary.csv'
        return response
