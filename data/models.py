from django.db import models

# Create your models here.

class Material(models.Model):
    '''
    This class defines a material in the database
    '''
    compound = models.CharField('Compound',max_length=100)

    class Meta:
        verbose_name_plural = "Materials"

    def __str__(self):
        return self.compound


class Property(models.Model):
    '''
    This class defines material property
    CharField is used for both non-numerical and numerical properties,
    thanks to django being able to do numerical comparisons in text fields
    '''
    compound = models.ForeignKey(Material, related_name='properties', on_delete=models.CASCADE)
    propertyName = models.CharField('Property name',max_length=100)
    propertyValue = models.CharField('Property value',max_length=100)

    class Meta:
        verbose_name_plural = "Properties"

    def __str__(self):
        return "{} of {}".format(self.propertyName,self.compound)
