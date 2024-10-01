from django import forms
from .models import ReportGrade

class GradeForm(forms.ModelForm):
    class Meta:
        model = ReportGrade
        fields = ['value', 'subject', 'student', 'semester']
        widgets = {
            'value': forms.NumberInput(attrs={'style': 'width: 100%; height: 30px;'}),
        }