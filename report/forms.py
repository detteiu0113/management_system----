from django import forms
from .models import Report
from vocabulary_test.models import TestResult

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        exclude = ['student', 'teacher', 'lesson']
        labels = {
            'homework': '宿題を出したか',
            'homework_done': '宿題をしてきたか',
            'unit': '単元',
            'behavior': '授業中の様子',
            'weakness': '苦手単元、改善点',
        }
        widgets = {
            'homework': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'homework_done': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'behavior': forms.Textarea(attrs={'class': 'form-control', 'style': 'resize: none; height: 100px;'}),
            'weakness': forms.Textarea(attrs={'class': 'form-control', 'style': 'resize: none; height: 100px;'}),
        }

class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = ['student', 'program', 'category', 'score', 'fullscore']
        labels = {
            'student': '生徒名',
            'category': 'カテゴリ',
            'program': 'プログラム',
            'fullscore': '満点',
            'score': '得点',
        }
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'program': forms.Select(attrs={'class': 'form-control'}),
            'fullscore': forms.NumberInput(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
        }
