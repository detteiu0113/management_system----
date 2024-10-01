from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re

from .models import CustomUser
from students.models import Student
from utils.choices import SCHOOL_CHOICES

#　 UserCreationFormをCustomUserに適応させる
class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = CustomUser

# 全ユーザー用の共通ログインフォーム
class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名', 'id': 'username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'パスワード', 'id': 'password'}))

# 塾長登録フォーム(未使用)
class OwnerCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['last_name', 'first_name', 'username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            self.fields[field_name].widget.attrs['class'] = 'form-control form-control-sm'

# 講師登録フォーム
class TeacherCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['last_name', 'first_name', 'username']
        labels = {
            'last_name': '姓',
            'first_name': '名',
            'username': 'メールアドレス'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            self.fields[field_name].widget.attrs['class'] = 'form-control form-control-sm'
            self.fields['last_name'].widget.attrs['class'] += ' last-name-field'
            self.fields['last_name'].required = True
            self.fields['first_name'].required = True

# 保護者登録フォーム
class ParentCreationForm(UserCreationForm):
    student_last_name = forms.CharField(max_length=100, required=True, label='生徒の姓', widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))
    student_first_name = forms.CharField(max_length=100, required=True, label='生徒の名', widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))
    student_birth_date = forms.DateField(required=True, label='生徒の誕生日', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'YYYY-MM-DD'}))
    student_elementary_school = forms.CharField(max_length=100, required=False, label='小学校', widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '学校名のみを記載してください。※例：野口南'}))
    student_school = forms.ChoiceField(choices=SCHOOL_CHOICES, required=False, label='中学校', widget=forms.Select(attrs={'class': 'form-control form-control-sm'}))
    student_high_school = forms.CharField(max_length=100, required=False, label='高校', widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '学校名のみを記載してください。※例：加古川北'}))

    class Meta:
        model = CustomUser
        fields = ['last_name', 'first_name', 'username']
        labels = {
            'last_name': '姓',
            'first_name': '名',
            'username': 'メールアドレス'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['last_name'].required = True
        self.fields['first_name'].required = True
        self.fields['username'].required = True
        for field_name, field in self.fields.items():
            self.fields[field_name].widget.attrs['class'] = 'form-control'
    
# 生徒(兄弟)追加フォーム
class StudentCreationForm(forms.ModelForm):
    birth_date = forms.DateField(
        required=True,
        label='誕生日',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = Student
        fields = ['last_name', 'first_name', 'birth_date', 'elementary_school', 'school', 'high_school']
        labels = {
            'last_name': '姓',
            'first_name': '名',
            'birth_date': '誕生日',
            'elementary_school': '小学校',
            'school': '中学校',
            'high_school': '高校',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            self.fields[field_name].widget.attrs['class'] = 'form-control'
            field.help_text = ''

        self.fields['elementary_school'].widget.attrs['placeholder'] = '学校名のみを記入してください。※例：野口南'
        self.fields['high_school'].widget.attrs['placeholder'] = '学校名のみを記入してください。※例：加古川北'

class TeacherStatusForm(forms.Form):
    STATUS_CHOICES = (
        ('', '勤務中'),
        ('withdrawn', '退塾'),
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label='ステータス')