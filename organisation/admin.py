from django.contrib.admin import register, ModelAdmin
from .models import DepartmentUser


@register(DepartmentUser)
class DepartmentUserAdmin(ModelAdmin):
    list_display = ['email', 'username']
    search_fields = ['email', 'username']
