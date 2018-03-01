from django import forms


class JSONForm(forms.Form):
     entry = forms.CharField(label="", widget=forms.Textarea(attrs={'rows':30, 'cols':60}))

class DataUploadForm(forms.Form):
    file = forms.FileField(label="")
