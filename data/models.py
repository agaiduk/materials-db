from django.db import models
from rest_framework import serializers

# Create your models here.

class Material(models.Model):
    compound = models.CharField('Compound',max_length=100)

    class Meta:
        verbose_name_plural = "Materials"

    def __str__(self):
        return self.compound


class Property(models.Model):
    compound = models.ForeignKey(Material, related_name='properties', on_delete=models.CASCADE)
    propertyName = models.CharField('Property name',max_length=100)
    propertyValue = models.CharField('Property value',max_length=100)

    class Meta:
        verbose_name_plural = "Properties"

    def __str__(self):
        return "{} of {}".format(self.propertyName,self.compound)


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('propertyName', 'propertyValue')


class MaterialSerializer(serializers.ModelSerializer):
    properties = PropertySerializer(many=True)

    class Meta:
        model = Material
        fields = ('compound', 'properties')
