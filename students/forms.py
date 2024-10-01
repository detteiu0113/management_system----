from django import forms
from .models import StudentNotable, Student

class StudentNotableForm(forms.ModelForm):
    class Meta:
        model = StudentNotable
        fields = ['notable']
        labels = {
            'notable': '内容'
        }
        widgets = {
            'notable': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '特筆事項を記入'}),
        }

class StudentStatusForm(forms.Form):
    STATUS_CHOICES = (
        ('', '受講中'),
        ('on_leave', '休塾'),
        ('withdrawn', '退塾'),
        ('planning_to_withdraw', '年度末で退塾'),
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label='ステータス')

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        labels = {
            'last_name':'姓',
            'first_name':'名',
            'birth_date': '誕生日',
            'elementary_school': '小学校',
            'school': '中学校',
            'high_school': '高校',
            'enrollment_date': '入塾日',
            'grade': '学年',
            'is_elementary_school': '小学生かどうか',
            'is_middle_school': '中学生かどうか',
            'is_high_school': '高校生かどうか',
            'is_on_leave': '休塾しているかどうか',
            'is_withdrawn': '退塾しているかどうか',
            'is_planning_to_withdraw': '年度末に退塾するかどうか',
            'is_upgraded': '年度切り替えの処理が完了しているかどうか',
        }