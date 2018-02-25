from django import forms
from .models import Material, DataFile


class MaterialAddForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = '__all__'


class DataUploadForm(forms.ModelForm):
    class Meta:
        model = DataFile
        fields = ('description', 'data_file', )


class MaterialSearchForm(forms.ModelForm):
    string_options = (
        ("match", "Matches"),
        ("contains", "Contains"),
    )
    float_options = (
        ("eq", "=="),
        ("gt", ">"),
        ("ge", ">="),
        ("lt", "<"),
        ("le", "<="),
    )
    chemical_formula = forms.CharField(label='Formula', max_length=50, required = False)
    compound_logic = forms.ChoiceField(label="Compound logic", widget=forms.Select, required = False, choices = string_options)
    property1_value = forms.FloatField(label='Property 1 value', required = False)
    property1_logic = forms.ChoiceField(label="Property 1 logic", widget=forms.Select, required = False, choices = float_options)
    property2_value = forms.CharField(label='Property 2 value', max_length=50, required = False)
    property2_logic = forms.ChoiceField(label="Property 2 logic", widget=forms.Select, required = False, choices = string_options)
    class Meta:
        model = Material
        exclude = ('property1_name', 'property2_name', )
        fields = ('chemical_formula', 'compound_logic', 'property1_value', 'property1_logic', 'property2_value', 'property2_logic', )


#    class PropertyChar():
#        name = forms.CharField(label='Property name', max_length=50, required = False)
#        value = forms.CharField(label='Property value', max_length=50, required = False)
#        logic = forms.ChoiceField(label="Property logic", widget=forms.Select, required = False, choices = MaterialSearchForm.string_options)
#
#
#    class PropertyFloat():
#        name = forms.CharField(label='Property name', max_length=50, required = False)
#        value = forms.FloatField(label='Property value', max_length=50, required = False)
#        logic = forms.ChoiceField(label="Property logic", widget=forms.Select, required = False, choices = MaterialSearchForm.string_options)
