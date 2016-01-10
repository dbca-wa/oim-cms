from django.contrib import admin
from .models import DepartmentUser, Computer, Mobile


class DepartmentUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'employee_id', 'username', 'active', 'vip', 'executive', 'cost_centre', 'date_updated', 'date_ad_updated', 'org_unit', 'parent']
    list_filter = ['active', 'vip', 'executive', 'date_ad_updated']
    search_fields = ['name', 'email', 'username', 'employee_id']
    raw_id_fields = ['parent', 'cost_centre', 'org_unit']
    readonly_fields = ['username', 'email', 'org_data_pretty', 'ad_data_pretty']
    fields = (
        ('email', 'username'), ('given_name', 'surname'),
        ('employee_id', 'cost_centre'), ('name', 'org_unit'),
        ('telephone', 'mobile_phone'), ('vip', 'executive'),
        ('title', 'parent'),
        ('other_phone', 'extra_data'),
        ('org_data_pretty', 'ad_data_pretty')
    )


class ComputerAdmin(admin.ModelAdmin):
    list_display = ['sam_account_name', 'hostname', 'managed_by', 'probable_owner']
    search_fields = ['sam_account_name', 'hostname']


class MobileAdmin(admin.ModelAdmin):
    list_display = ('identity', 'model', 'imei', 'serial_number', 'asset_id', 'finance_asset_id', 'registered_to')
    search_fields = ('identity', 'model', 'imei', 'serial_number', 'asset_id', 'finance_asset_id')


admin.site.register(DepartmentUser, DepartmentUserAdmin)
admin.site.register(Computer, ComputerAdmin)
admin.site.register(Mobile, MobileAdmin)
