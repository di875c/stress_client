from django import forms
from .model import *
import re

TYPE_FIELD = {'float': forms.FloatField, 'str': forms.CharField}

def validate_with_condition(value):
    if re.search(r"^[=><]{1,2}[ ]\w+", value) or value == '' or \
            re.search(r"^between[ ][+-]?((\d+\.?\d*)|(\.\d+))[ ][+-]?((\d+\.?\d*)|(\.\d+))", value):
        return
    else:
        raise forms.ValidationError(
            "Your string has to include condition (==, >, between, etc.) and value",
            params={'value': value},
        )


class BaseDynamicForm(forms.Form):
    def __init__(self, *args, **kwargs):
        _condition = True
        for arg in args:
            if 'dynamic_fields' in arg:
                dynamic_fields = arg.pop('dynamic_fields')
            if 'validate' in arg:
                _condition = arg.pop('validate')
            type_fields = arg.pop('type_fields') if 'type_fields' in arg else 'str'
        validator = [validate_with_condition] if _condition else []
        super(BaseDynamicForm, self).__init__(*args, **kwargs)
        for key in dynamic_fields:
            self.fields[key] = TYPE_FIELD[type_fields](validators=validator, help_text='описание', required=False)


class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = '__all__'


# class FileSaveForm(forms.Form):
#     file_type = forms.TypedChoiceField()