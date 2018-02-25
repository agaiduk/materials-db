from django.db import models

# Create your models here.

class Material(models.Model):
    chemical_formula = models.CharField('chemical formula',max_length=50)
    property1_name = models.CharField('Property 1 name',max_length=50)
    property1_value = models.FloatField('Property 1 value')
    property2_name = models.CharField('Property 2 name',max_length=50)
    property2_value = models.CharField('Property 2 value',max_length=50)

    def __str__(self):
        return self.chemical_formula

    def material_output(self):
        return 'Material {} with {} of {} and {} of {}'.format(self.chemical_formula, self.property1_name, self.property1_value, self.property2_name, self.property2_value)


class DataFile(models.Model):
    folder = 'csv/'
    description = models.CharField(max_length=255, blank=True)
    data_file = models.FileField(upload_to=folder)
