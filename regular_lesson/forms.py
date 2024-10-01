from django import forms
from .models import  RegularLessonAdmin
from students.models import Student

class RegularLessonAdminCreateForm(forms.ModelForm): 
    periods = forms.IntegerField(label='Periods', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    class Meta:
        model = RegularLessonAdmin
        fields = ['student', 'subject', 'start_date', 'end_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # 必要に応じてフィルタリングの条件を受け取るためのキーワード引数を追加することもできます
        super(RegularLessonAdminCreateForm, self).__init__(*args, **kwargs)
        
        # ここで student フィールドの queryset をフィルタリングします
        # 例：is_active フィールドが True の学生のみを表示する
        self.fields['student'].queryset = Student.objects.filter(is_on_leave=False, is_withdrawn=False)