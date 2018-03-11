from haystack import indexes
from data.models import Material


class MaterialIndex(indexes.SearchIndex, indexes.Indexable):
    # Use Haystack templates with custom filters that convert commas in the fields to spaces
    text = indexes.CharField(document=True, use_template=True)
    compound = indexes.CharField(model_attr='compound')
    element = indexes.CharField(model_attr='elements', use_template=True)
    period = indexes.CharField(model_attr='periods', use_template=True)
    group = indexes.CharField(model_attr='groups', use_template=True)

    def get_model(self):
        return Material
