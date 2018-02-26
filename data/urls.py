from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add', views.add, name='add'),
    path('search', views.search, name='search'),
    path('upload', views.upload, name='upload')
]
