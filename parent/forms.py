from django import forms
from accounts.models import ParentProfile

class SwitchStudentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        parent_profile = kwargs.pop('parent_profile', None)
        super(SwitchStudentForm, self).__init__(*args, **kwargs)
        self.fields['student'].queryset = parent_profile.student.all()

    student = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='生徒',  # ラベルを日本語に変更
        required=True,
    )
