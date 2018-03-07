from haystack import indexes
from data.models import Material


class MaterialIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    compound = indexes.CharField(model_attr='compound')
    element = indexes.CharField(model_attr='elements')
    period = indexes.CharField(model_attr='periods')
    group = indexes.CharField(model_attr='groups')

    def get_model(self):
        return Material
