from django import forms
from regular_lesson.models import Lesson
from accounts.models import CustomUser
from special_lesson.models import SpecialLessonAdmin
from students.models import Student
from utils.choices import ROOM_CHOICES, TIME_CHOICES, SPECIAL_TIME_CHOICES, SUBJECT_CHOICES

class TeacherAddForm(forms.Form):
    teacher = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_teacher=True).filter(teacher_profile__is_withdrawn=False),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='臨時講師'
    )
    special_teacher = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_teacher=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='出勤可能講師(講習)',
    )
    room = forms.ChoiceField(
        choices=ROOM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='部屋'
    )
    time = forms.ChoiceField(
        choices=SPECIAL_TIME_CHOICES+TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='時間'
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control'}),
        label='日付'
    )

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get('teacher')
        special_teacher = cleaned_data.get('special_teacher')

        if not teacher and not special_teacher:
            raise forms.ValidationError('臨時講師または出勤可能講師(講習)のいずれかを選択してください。')

        return cleaned_data

class SpecialLessonOptionWidget(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value:
            # 特別なオプションの値が存在する場合、その値を元にStudentのIDを取得し、data-属性に追加する
            special_lesson = SpecialLessonAdmin.objects.get(pk=value.value)
            student_id = special_lesson.student.id
            option['attrs']['data-student-id'] = student_id
        else:
            option['attrs']['data-student-id'] = ''
        return option

class TransferLessonForm(forms.Form):
    lesson = forms.ModelChoiceField(
        queryset=Lesson.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'lesson-select'}),
        label='振替授業',  # ラベルを日本語に設定
        required=False
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_on_leave=False, is_withdrawn=False),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'student-select'}),
        label='生徒',  # ラベルを日本語に設定
        required=False
    )
    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'subject-select'}),
        label='科目',  # ラベルを日本語に設定
        required=False,
    )
    special_lesson = forms.ModelChoiceField(
        queryset=SpecialLessonAdmin.objects.all(),
        widget=SpecialLessonOptionWidget(attrs={'class': 'form-select', 'id': 'special-lesson-select'}),
        label='講習授業(希望)',  # ラベルを日本語に設定
        required=False
    )
    special_lesson_others = forms.ModelChoiceField(
        queryset=SpecialLessonAdmin.objects.all(),
        widget=SpecialLessonOptionWidget(attrs={'class': 'form-select', 'id': 'special-lesson-others-select'}),
        label='講習授業(希望以外)',  # ラベルを日本語に設定
        required=False
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'id': 'date-input'}),
        label='日付'  # ラベルを日本語に設定
    )
    room = forms.ChoiceField(
        choices=ROOM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'room-select'}),
        label='部屋'  # ラベルを日本語に設定
    )
    time = forms.ChoiceField(
        choices=SPECIAL_TIME_CHOICES + TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'time-select'}),
        label='時間'  # ラベルを日本語に設定
    )