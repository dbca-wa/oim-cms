from django.contrib.admin import register, ModelAdmin
from django.contrib.auth.models import User, Group

class OimModelAdmin(ModelAdmin):
    """ OimModelAdmin"""

    def has_module_permission(self,request):
        user = request.user
        if user.is_superuser :
            return True

        if user.is_staff :
            if user.groups.filter(name = "OIM Staff").exists():
                return True

        return False
