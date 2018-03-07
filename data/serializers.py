from .models import Material, Property
from rest_framework import serializers

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('propertyName', 'propertyValue')


class MaterialSerializer(serializers.ModelSerializer):
    properties = PropertySerializer(many=True)

    class Meta:
        model = Material
        fields = ('compound', 'properties')
