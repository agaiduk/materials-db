from django import forms


class JSONForm(forms.Form):
     entry = forms.CharField(label="", widget=forms.Textarea)
