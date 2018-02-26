from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
import json
#import requests

from .models import Material, MaterialSerializer
from .forms import JSONForm
#from .forms import DataUploadForm  # Form for loading data from a csv file
from .load_data import csv_to_db, valid_float

# Create your views here.

csv_file = 'data.csv'

def index(request):
    search_form = JSONForm()
    add_form = JSONForm()
    return render(request, 'data/index.html', {'search_form': search_form, 'add_form': add_form})


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


def get_db_operator(string):
    logic_operators = {
        ("eq", "==", "=", "match", "matches"): "iexact",
        ("contain", "contains", "contained", "in"): "icontains",
        (">", "gt", "more"): "gt",
        (">=", "gte", "ge"): "gte",
        ("<", "lt", "less"): "lt",
        ("<=", "=<" "lte", "le"): "lte"
    }
    for key in logic_operators:
        if string in key:
            return logic_operators[key]
    return None


def check_db_operator_type(operator, data_type):
    """ Check if correct operator is used for a given data type """
    if data_type == str and operator not in ["iexact", "icontains"]:
        raise ValueError("{} is an incorrect logic operator for character data".format(operator))
    elif data_type == float and operator not in ["iexact", "gt", "gte", "lt", "lte"]:
        raise ValueError("{} is an incorrect logic operator for numerical data".format(operator))


def json_to_query(json_query):
    """ This function creates db query from a dictionary """
    db_query = Material.objects
    # Check JSON with respect to schema to make sure it's correct
    # Parse query into fields
    if "compound" in json_query:
        compound_name, compound_logic = json_query["compound"]["value"], json_query["compound"]["logic"]
        search_type = get_db_operator(compound_logic)
        check_db_operator_type(search_type, str)
        db_query = db_query.filter(**{'compound__' + search_type: compound_name})
    if "properties" in json_query:
        for compound_property in json_query["properties"]:
            compound_property_name = compound_property["name"]
            compound_property_value = compound_property["value"]
            compound_property_logic = compound_property["logic"]
            search_type = get_db_operator(compound_property_logic)
            # Process requests that are floats
            if valid_float(compound_property_value):
                check_db_operator_type(search_type, float)
                db_query = db_query.filter(properties__propertyName__iexact=compound_property_name,
                    **{'properties__propertyValue__' + search_type: compound_property_value}
                    )
            # Process requests that are strings
            else:
                check_db_operator_type(search_type, str)
                db_query = db_query.filter(properties__propertyName__iexact=compound_property_name,
                    **{'properties__propertyValue__' + search_type: compound_property_value}
                    )
    return db_query


def db_to_json(db_query):
    """ Takes in the QuerySet and returns a list of dictionaries """
    materials_found = []
    for material in db_query:
        materials_found.append(MaterialSerializer(instance=material).data)
    return materials_found


def add(request):  # Accepts JSON as a request
    if request.method == 'POST':
        alloys = json.loads(request.body)  # Convert JSON to dictionary
        # Check JSON with respect to the schema to make sure it's correct
        for alloy in alloys:
            material = Material(compound=alloy["compound"])
            material.save()
            for compound_property in alloy["properties"]:
                propertyName = compound_property["propertyName"]
                propertyValue = compound_property["propertyValue"]
                material.properties.create(propertyName=propertyName, propertyValue=propertyValue)
        return HttpResponse("POST request to /data/add successful.")
    else:
        # GET request to /data/add generates a form for adding the compounds to database
        #add_form = JSONForm()
        #return render(request, 'data/add.html', {'add_form': add_form})
        return HttpResponseRedirect(reverse('index'))


def search(request):
    if request.method == 'POST':
        json_query = json.loads(request.body)
        db_query = json_to_query(json_query)
        json_search_result = db_to_json(db_query)
        return JsonResponse(json_search_result, safe=False)
    else:
        # Actually can serve a webpage with add form for GET request
        return HttpResponseRedirect(reverse('index'))

''' Code I was playing with to implement POST requests from within the app
def input(request):
    """ Process the form and send JSON POST request to /data/add or /data/search """
    if request.method == 'POST':
        form = JSONForm(request.POST)
        # check whether the form is valid and extract clean data from it
        if form.is_valid():
            print("The form is valid")
            query = form.cleaned_data['entry']
            response = requests.post('http://127.0.0.1:8000/data/add', data=query)
            print(response)
            return HttpResponse("POST request to /data successful, the form is valid.")
        else:
            print("The form is invalid")
            return HttpResponse("POST request to /data/add/ successful but the form is invalid.")
    else:
        # Actually can serve a webpage with add form for GET request
        return HttpResponseRedirect(reverse('index'))
'''
