from django import forms
from .models import Notification

class NotificationForm(forms.ModelForm):
    # 送信先の選択肢
    SEND_CHOICES = [
        ('teacher', '講師'),
        ('parent', '保護者'),
        ('all', '全員'),
    ]
    
    send_to = forms.ChoiceField(
        choices=SEND_CHOICES,
        label='送信先',  # ラベルを日本語に変更
        widget=forms.Select(attrs={'class': 'form-select'})  # BootstrapのSelectクラスを追加
    )

    class Meta:
        model = Notification
        fields = ['send_to', 'message', 'is_priority']

        labels = {  # フィールドのラベルを日本語に変更
            'message': 'メッセージ',
            'is_priority': '重要',
        }

        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'resize: none; height: 200px;'}),  # BootstrapのTextAreaクラスを追加
            'is_priority': forms.CheckboxInput(attrs={'class': 'form-check-input'})  # BootstrapのCheckboxInputクラスを追加
        }
