from datetime import datetime
from restless.dj import DjangoResource
from restless.exceptions import BadRequest
from restless.preparers import FieldsPreparer
from organisation.models import DepartmentUser
from .models import Approval
from .forms import ApprovalForm


class ApprovalResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'created_date': 'created_date',
        'requester': 'requester.email',
        'approver': 'approver.email',
        'proposal_url': 'proposal_url',
        'proposal_desc': 'proposal_desc',
        'confirmed_date': 'confirmed_date',
    })

    def is_authenticated(self):
        return self.request.user.is_authenticated()

    def list(self):
        return Approval.objects.all()

    def detail(self, pk):
        return Approval.objects.get(pk=pk)

    def create(self):
        """POST request requires approver (email), proposal_url and/or
        proposal_desc parameters.
        """
        if 'approver' not in self.data:
            raise BadRequest('Missing parameter: approver')

        requester = DepartmentUser.objects.get(email__iexact=self.request.user.email)
        approver = DepartmentUser.objects.get(email__iexact=self.data['approver'])
        self.data['approver'] = approver.pk  # ModelForm requires an approver by PK, not email.
        form = ApprovalForm(self.data)

        if not form.is_valid():
            raise BadRequest(form.errors.as_json())

        return Approval.objects.create(
            requester=requester,
            approver=approver,
            proposal_url=form.cleaned_data['proposal_url'],
            proposal_desc=form.cleaned_data['proposal_desc']
        )

    def update(self, pk):
        """PUT request should only change confirmed_date when a matching guid
        is provided.
        """
        if 'guid' not in self.data:
            raise BadRequest('Missing parameter: guid')
        try:
            approval = Approval.objects.get(pk=pk)
        except Approval.DoesNotExist:
            raise BadRequest('Approval not found')

        if approval.confirmed_date:
            raise BadRequest('Approval is already confirmed')
            # Disallow anyone but the approver from confirming a request.
        elif self.request.user.email.lower() != approval.approver.email.lower():
            raise BadRequest('Only {} may confirm the approval request'.format(approval.approver))
        elif self.data['guid'] != str(approval.guid):
            raise BadRequest('Incorrect GUID')

        approval.confirmed_date = datetime.now()
        approval.save()

        return approval
