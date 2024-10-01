from django import forms
from django.core.exceptions import ValidationError

from .models import FixedShift, Salary
from accounts.models import CustomUser
from utils.helpers import get_fiscal_year_boundaries

class FixedShiftCreateForm(forms.ModelForm):
    class Meta:
        model = FixedShift
        fields = '__all__'
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'time': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        _, end_fiscal_date = get_fiscal_year_boundaries(start_date)
        if start_date > end_date:
            raise ValidationError("開始日は終了日より後にすることはできません。")
        if end_date > end_fiscal_date:
            raise ValidationError("終了日は年度末より後にすることはできません。")

    def __init__(self, *args, **kwargs):
        super(FixedShiftCreateForm, self).__init__(*args, **kwargs)
        self.fields['teacher'].queryset = CustomUser.objects.filter(is_teacher=True).filter(teacher_profile__is_withdrawn=False)

class SalaryForm(forms.ModelForm):
    class Meta:
        model = Salary
        fields = ['teacher', 'cost_name', 'price', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'cost_name': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'teacher': '講師',
            'cost_name': '費用名',
            'price': '金額',
            'date': '日付',
        }

    def __init__(self, *args, **kwargs):
        super(SalaryForm, self).__init__(*args, **kwargs)
        self.fields['teacher'].queryset = CustomUser.objects.filter(is_teacher=True).filter(teacher_profile__is_withdrawn=False)
        # 現在の選択肢を取得
        current_choices = list(self.fields['cost_name'].choices)
        # '授業手当' に該当する選択肢を除外
        filtered_choices = [choice for choice in current_choices if choice[1] != '授業手当']
        self.fields['cost_name'].choices = filtered_choices