from datetime import date, timedelta
from django import forms

from utils.helpers import get_today

class PrintMonthScheduleForm(forms.Form):
    year = forms.IntegerField(label='年')
    month = forms.IntegerField(label='月')

    def __init__(self, *args, **kwargs):
        super(PrintMonthScheduleForm, self).__init__(*args, **kwargs)
        # Bootstrap クラスをフィールドに適用
        self.fields['year'].widget.attrs.update({'class': 'form-control'})
        self.fields['month'].widget.attrs.update({'class': 'form-control'})
        
        # デフォルト値を来月に設定
        next_month = get_today() + timedelta(days=31)
        self.fields['year'].initial = next_month.year
        self.fields['month'].initial = next_month.month % 12 or 12