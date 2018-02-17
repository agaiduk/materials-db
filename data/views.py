from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    return HttpResponse("This will be the front page of the materials database. Add some silly buttons pointing to add/search webpages.")


def add(request):
    return HttpResponse("This will be the form to add data to the materials database.")


def search(request):
    return HttpResponse("This will be the seacrh form for the materials database.")
