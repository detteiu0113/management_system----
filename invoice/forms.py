from django import forms
from .models import Invoice

class InvoiceForm(forms.ModelForm):
    cost_name = forms.CharField(label='明細', widget=forms.TextInput(attrs={'class': 'form-control'}))
    price = forms.DecimalField(label='価格', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    date = forms.DateField(label='日付', widget=forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Date', 'type': 'date'}))

    class Meta:
        model = Invoice
        fields = ['cost_name', 'price', 'date']
