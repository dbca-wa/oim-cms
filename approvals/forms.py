from django import forms
from .models import Approval


class ApprovalForm(forms.ModelForm):

    class Meta:
        model = Approval
        fields = ['approver', 'proposal_url', 'proposal_desc']

    def clean(self):
        super(ApprovalForm, self).clean()
        proposal_url = self.cleaned_data.get('proposal_url')
        proposal_desc = self.cleaned_data.get('proposal_desc')
        if not proposal_url and not proposal_desc:
            raise forms.ValidationError(
                'You must specify proposal URL and/or description',
                code='invalid')
