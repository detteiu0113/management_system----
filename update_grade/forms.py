from django import forms
from students.models import Student

class StudentUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StudentUpdateForm, self).__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['school'].initial = '高校名を入力してください'

    class Meta:
        model = Student
        fields = ['school']
        widgets = {
            'school': forms.Select(attrs={'class': 'form-control'}),
        }
