from django import forms


class LookupForm(forms.Form):
    msisdn = forms.CharField(label="Введите номер", max_length=12)
