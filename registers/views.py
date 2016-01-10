from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, HTML
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import ListView, FormView, DetailView

from .models import LocalPropertyRegister
from .tasks import validate_lpr


class LprUploadForm(forms.ModelForm):
    """Upload form for local property register spreadsheets.
    """
    uploaded_file = forms.FileField(
        label='Local property register', help_text='.xls, .xlsx or .csv only')

    def __init__(self, *args, **kwargs):
        super(LprUploadForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        # crispy_forms layout
        self.helper.layout = Layout(
            'uploaded_file',
            Div(
                Submit('upload', 'Upload'),
                HTML('<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>'),
                css_class='modal-footer')
        )

    def clean(self):
        # Allow CSV & Excel mimetypes only.
        mime = [
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        if 'uploaded_file' in self.cleaned_data:
            f = self.cleaned_data['uploaded_file'].content_type
            if f not in mime:
                msg = '{} is not an allowed file type'.format(f)
                self._errors['uploaded_file'] = self.error_class([msg])
        return self.cleaned_data

    class Meta:
        model = LocalPropertyRegister
        exclude = ['uploaded_by']


class LocalPropertyRegisterList(FormView):
    """List view of local property register validation errors.

    Allows upload of local property registers (Excel workbooks in a standard
    format) to alter some device information. Imported informatin is subject
    to validation, and then the uploading user is emailed a report of the
    import results.
    """
    form_class = LprUploadForm
    template_name = 'tracking/localpropertyregister_list.html'

    def get_context_data(self, **kwargs):
        context = super(LocalPropertyRegisterList, self).get_context_data(**kwargs)
        context['lpr_tab'] = True
        context['page_title'] = '{} - Local Property Registers'.format(settings.SITE_TITLE)
        context['object_list'] = LocalPropertyRegister.objects.all()
        return context

    def form_valid(self, form):
        lpr = form.save(commit=False)
        lpr.uploaded_by = self.request.user
        lpr.save()
        # NOTE: don't process the LPR spreadsheet asynchronously.
        validate_lpr(lpr.pk)
        # Process the uploaded LPR spreadsheet as an async task.
        #validate_lpr.delay(lpr.pk)
        return super(LocalPropertyRegisterList, self).form_valid(form)

    def get_success_url(self):
        return reverse('lpr_list')


class LocalPropertyRegisterDetail(DetailView):
    """Detail view of a single uploaded local property register.
    """
    model = LocalPropertyRegister

    def get_context_data(self, **kwargs):
        context = super(LocalPropertyRegisterDetail, self).get_context_data(**kwargs)
        context['lpr_tab'] = True
        context['errors'] = self.get_object().lprvalidation_set.all()
        return context

