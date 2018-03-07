from django.db import models
from data.tools import valid_float
from pyEQL import chemical_formula
from pyEQL import elements as Elements


# SQL database schema: Material <-- [Property, Property, ...]

class Material(models.Model):
    '''
    Material in the database
    '''
    compound = models.CharField('Compound',max_length=100)
    elements = models.CharField('Elements', max_length=100, blank=True)
    periods = models.CharField('Periods', max_length=100, blank=True)
    groups = models.CharField('Groups, CAS', max_length=100, blank=True)
    csv = models.CharField('CSV', max_length=300, blank=True)

    class Meta:
        verbose_name_plural = "Materials"

    def __str__(self):
        return self.compound

    # Generate a csv field corresponding to this material entry
    # Used to create search index, but also for possible export
    def to_csv(self):
        csv = []
        csv.append(self.compound)
        if self.properties.all():
            for material_property in self.properties.all():
                csv.append(material_property.propertyName)
                csv.append(material_property.propertyValue)
        return ",".join(csv)

    # Modify the standard save method to create attributes of the models
    # containing csv of elements in the compound, as well as groups and periods they belong to
    def save(self, *args, **kwargs):
        # Obtain elements, groups, and periods, and save them to the model
        elements = chemical_formula.get_elements(self.compound)
        periods = set()
        groups = set()
        for element in elements:
            periods.add(str(Elements.ELEMENTS[element].period))
            groups.add(str(Elements.ELEMENTS[element].group))
        self.elements = ",".join(elements)
        self.groups = ",".join(groups)
        self.periods = ",".join(periods)
        self.csv = self.to_csv()
        super(Material, self).save(*args, **kwargs)


class Property(models.Model):
    '''
    Property of the material
    '''
    compound = models.ForeignKey(Material, related_name='properties', on_delete=models.CASCADE)
    propertyName = models.CharField('Property name', max_length=100)
    propertyValue = models.CharField('Property value', max_length=100)
    # Store the numerical value of the property if it is representable as a number
    propertyValueFloat = models.FloatField(default=None, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Properties"

    def __str__(self):
        return "{} of {}".format(self.propertyName,self.compound)

    def save(self, *args, **kwargs):
        # Check if the propertyValue can be converted to string and store it as a number
        if valid_float(self.propertyValue):
            self.propertyValueFloat = float(self.propertyValue)
        super(Property, self).save(*args, **kwargs)
