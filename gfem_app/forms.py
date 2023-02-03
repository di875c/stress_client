from django import forms
from .model import *
import re


def validate_not_simple(value):
    if re.search(r"^[=><]{1,2}[ ]\w+", value) or value == '':
        return
    else:
        raise forms.ValidationError(
            "Your string has to include condition (==, >, etc.) and value",
            params={'value': value},
        )

# class BaseIComForm(forms.Form):
#     id = forms.CharField(validators=[validate_not_simple], required=False)
#     comment = forms.RegexField(regex='simple')


class BaseDynamicForm(forms.Form):
    def __init__(self, *args, **kwargs):
        for arg in args:
            if 'dynamic_fields' in arg:
                dynamic_fields = arg.pop('dynamic_fields')
        super(BaseDynamicForm, self).__init__(*args, **kwargs)
        for key in dynamic_fields:
            self.fields[key] = forms.CharField(validators=[validate_not_simple], help_text='описание', required=False)
        # self.fields['button'] = forms.FileField(widget=forms.ClearableFileInput)


class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = '__all__'
