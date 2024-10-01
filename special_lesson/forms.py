from django import forms
from .models import SpecialLessonStudentRequest, SpecialLessonTeacherRequest, SpecialLessonAdmin
from students.models import Student

class SpecialLessonAdminCreateForm(forms.ModelForm):
    class Meta:
        model = SpecialLessonAdmin
        exclude = ['special_lesson']

    def __init__(self, *args, **kwargs):
        # 必要に応じてフィルタリングの条件を受け取るためのキーワード引数を追加することもできます
        super(SpecialLessonAdminCreateForm, self).__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(is_on_leave=False, is_withdrawn=False)

class SpecialLessonTeacherRequestForm(forms.ModelForm):
    class Meta:
        model = SpecialLessonTeacherRequest
        fields = '__all__'

class SpecialLessonStudentRequestForm(forms.ModelForm):
    class Meta:
        model = SpecialLessonStudentRequest
        fields = '__all__'