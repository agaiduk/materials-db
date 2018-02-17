from django.db import models

# Create your models here.

class Material(models.Model):
    chemical_formula = models.CharField('chemical formula',max_length=50)
    property1_name = models.CharField('Property 1 name',max_length=50)
    property1_value = models.FloatField('Property 1 value')
    property2_name = models.CharField('Property 2 name',max_length=50)
    property2_value = models.FloatField('Property 2 value')
