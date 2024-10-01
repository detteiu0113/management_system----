from django import forms
from .models import TestResult, AverageScore
from utils.choices import SCHOOL_CHOICES, GRADE_CHOICES, GRADE_MIDDLE_CHOICES

class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = '__all__'

class AverageScoreForm(forms.Form):
    TEST_NAME_CHOICES = [
        (None, '---------'),
        ('1学期中間', '1学期中間'),
        ('1学期期末', '1学期期末'),
        ('2学期中間', '2学期中間'),
        ('2学期期末', '2学期期末'),
        ('3学期学年末', '3学期学年末'),
        ('テスト名を入力', 'テスト名を入力')
    ]

    test_name = forms.ChoiceField(
        choices=TEST_NAME_CHOICES,
        label='テスト名',
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': 'テスト名'})
    )
    custom_test_name = forms.CharField(
        label='カスタムのテスト名',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'カスタムのテスト名'})
    )
    school = forms.ChoiceField(
        choices=SCHOOL_CHOICES,
        label='学校',
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': '学校'})
    )
    grade = forms.ChoiceField(
        choices=GRADE_MIDDLE_CHOICES,
        label='学年',
        widget=forms.Select(attrs={'class': 'form-select', 'placeholder': '学年'})
    )
    date = forms.DateField(
        label='日付',
        widget=forms.DateInput(attrs={'class': 'form-control', 'placeholder': '日付', 'type': 'date'})
    )
    jap = forms.FloatField(
        label='国語',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '国語'})
    )
    mat = forms.FloatField(
        label='数学',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '数学'})
    )
    soc = forms.FloatField(
        label='社会',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '社会'})
    )
    sci = forms.FloatField(
        label='理科',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '理科'})
    )
    eng = forms.FloatField(
        label='英語',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '英語'})
    )
    five_total = forms.FloatField(
        label='5科目合計',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5科目合計'})
    )
    mus = forms.FloatField(
        label='音楽',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '音楽'})
    )
    art = forms.FloatField(
        label='美術',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '美術'})
    )
    phy = forms.FloatField(
        label='体育',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '体育'})
    )
    tec = forms.FloatField(
        label='技術',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '技術'})
    )
    nine_total = forms.FloatField(
        label='9科目合計',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '9科目合計'})
    )

class AverageScoreUpdateForm(forms.ModelForm):
    class Meta:
        model = AverageScore
        fields = '__all__'
        labels = {
            'test_name': 'テスト名',
            'school': '学校',
            'grade': '学年',
            'date': '日付',
            'jap': '国語',
            'mat': '数学',
            'soc': '社会',
            'sci': '理科',
            'eng': '英語',
            'five_total': '5科目合計',
            'mus': '音楽',
            'art': '美術',
            'phy': '体育',
            'tec': '技術',
            'nine_total': '9科目合計',
        }
        widgets = {
            'test_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'テスト名'}),
            'school': forms.Select(attrs={'class': 'form-select', 'placeholder': '学校'}),
            'grade': forms.Select(attrs={'class': 'form-select', 'placeholder': '学年'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'jap': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '国語'}),
            'mat': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '数学'}),
            'soc': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '社会'}),
            'sci': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '理科'}),
            'eng': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '英語'}),
            'five_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5科目合計'}),
            'mus': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '音楽'}),
            'art': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '美術'}),
            'phy': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '体育'}),
            'tec': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '技術'}),
            'nine_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '9科目合計'}),
        }