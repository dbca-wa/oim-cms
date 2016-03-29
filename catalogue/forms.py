from django import forms

from catalogue.models import Record

class RecordForm(forms.ModelForm):
    """
    A form for Record Model
    """
    def __init__(self, *args, **kwargs):
        super(RecordForm, self).__init__(*args, **kwargs)
        self.fields['identifier'].widget.attrs['readonly'] = True


    class Meta:
        model = Record
        fields = ("identifier","title","abstract","keywords","any_text","auto_update")
        #fields = "__all__"
        widgets = {
                'keywords': forms.TextInput(attrs={"style":"width:70%"})
        }

