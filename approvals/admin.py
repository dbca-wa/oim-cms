from django.contrib.admin import register, ModelAdmin
from organisation.models import DepartmentUser
from .forms import ApprovalForm
from .models import Approval


@register(Approval)
class ApprovalAdmin(ModelAdmin):
    list_display = ['pk', 'guid', 'requester', 'approver', 'confirmed_date']
    form = ApprovalForm

    def save_model(self, request, obj, form, change):
        # Set the approval requester for new objects.
        if not obj.pk:
            obj.requester = DepartmentUser.objects.get(
                email__iexact=request.user.email)
        obj.save()
