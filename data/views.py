from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from .models import Material
from .forms import MaterialSearchForm, MaterialAddForm
#from .forms import DataUploadForm  # For loading data from a csv file
from .load_data import csv_to_db

# Create your views here.

csv_file = 'data.csv'

def index(request):
    search_form = MaterialSearchForm()
    add_form = MaterialAddForm()
    #data_upload_form = DataUploadForm()
    #return render(request, 'data/index.html', {'search_form': search_form, 'add_form': add_form, 'csv_form': data_upload_form})
    return render(request, 'data/index.html', {'search_form': search_form, 'add_form': add_form})


def add(request):
    if request.method == 'POST':
        form = MaterialAddForm(request.POST)
        ## check whether it's valid:
        if form.is_valid():
            print("The form is valid")
            print(form)
            form.save()
            return HttpResponseRedirect(reverse('index'))
        else:
            print("The form is invalid")
            return HttpResponse("POST request to /data/add/ successful but the form is invalid.")
    else:
        # Actually can serve a webpage with add form for GET request
        return HttpResponseRedirect(reverse('index'))


def upload(request):
    if request.method == 'GET':
        return HttpResponseRedirect(reverse('index'))
    elif request.method == 'POST':
        csv_exit_code = csv_to_db(csv_file)
        if csv_exit_code == 0:
            print("File successfully loaded into the database")
        else:
            print("Something went wrong - error reading file")
        return HttpResponse("POST request to /data/upload/ successful, the data.csv file was uploaded.")


def search(request):
    if request.method == 'POST':
        print(request)
        form = MaterialSearchForm(request.POST)
        ## check whether it's valid:
        if form.is_valid():
            print("The form is valid")
            f = form.cleaned_data
            print(f)
            query = Material.objects.all()
            # Filter by the compound name
            if f["chemical_formula"]:
                value = f["chemical_formula"]
                logic = f["compound_logic"]
                if logic == "match":
                    query = query.filter(chemical_formula__iexact=value)
                elif logic == "contains":
                    query = query.filter(chemical_formula__icontains=value)
            # Filter by the property1 value
            if f["property1_value"]:
                value = f["property1_value"]
                logic = f["property1_logic"]
                if logic == "eq":
                    query = query.filter(property1_value=value)
                elif logic == "gt":
                    query = query.filter(property1_value__gt=value)
                elif logic == "ge":
                    query = query.filter(property1_value__ge=value)
                elif logic == "lt":
                    query = query.filter(property1_value__lt=value)
            # Filter by the property1 value
            if f["property2_value"]:
                value = f["property2_value"]
                logic = f["property2_logic"]
                if logic == "match":
                    query = query.filter(property2_value__iexact=value)
                elif logic == "contains":
                    query = query.filter(property2_value__icontains=value)
            return render(request, 'data/search_results.html', {'query': query})
        else:
            print("The form is invalid")
            return HttpResponse("POST request to /data/search/ successful but the form is invalid.")
    else:
        # Actually can serve a webpage with add form for GET request
        return HttpResponseRedirect(reverse('index'))
