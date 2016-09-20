from datetime import datetime
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.views.generic import CreateView, DetailView
from organisation.models import DepartmentUser
from .forms import ApprovalForm
from .models import Approval


class ApprovalCreate(CreateView):
    """Basic form view to create an approval request.
    """
    model = Approval
    form_class = ApprovalForm

    def form_valid(self, form):
        approval = form.save(commit=False)
        # Set the requester.
        approval.requester = DepartmentUser.objects.get(
            email__iexact=self.request.user.email)
        approval.save()
        # TODO: Email the approver.
        return super(ApprovalCreate, self).form_valid(form)


class ApprovalDetail(DetailView):
    """Basic detail view for an approval request.
    """
    model = Approval


class ApprovalConfirm(DetailView):
    """A view to confirm an approval request via a unique URL.
    """
    model = Approval

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        # Look up the object by GUID.
        guid = self.kwargs.get('guid', None)
        if guid is not None:
            queryset = queryset.filter(guid=guid)
        else:
            raise AttributeError(
                'Approval confirm view must be called with an object GUID')
        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404('No approval found matching the GUID')
        return obj

    def get(self, request, *args, **kwargs):
        approval = self.get_object()
        user = DepartmentUser.objects.get(email__iexact=self.request.user.email)
        if approval.confirmed_date:
            # If the approval is already confirmed, redirect to detail view.
            messages.error(
                request,
                'Approval request {} is already confirmed'.format(approval.pk)
            )
        elif user != approval.approver:
            # Disallow anyone but the approver from confirming a request.
            messages.error(
                request,
                'Only {} may confirm the approval request'.format(approval.approver)
            )
        else:
            # Confirm the request.
            approval.confirmed_date = datetime.now()
            approval.save()
            messages.success(
                request,
                'Approval request {} has been confirmed'.format(approval.pk)
            )
        return HttpResponseRedirect(approval.get_absolute_url())
