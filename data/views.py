from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
import json
import requests

from .models import Material
from .serializers import MaterialSerializer
from .forms import JSONForm
from .forms import DataUploadForm  # Form for loading data from a csv file
from .load_data import csv_to_db, valid_float


def index(request):
    """
    This view provides Web access to the materials database API
    """
    def render_index(message=None):
        """
        Serve the index webpage with an optional message
        """
        search_form = JSONForm()
        add_form = JSONForm()
        file_form = DataUploadForm()
        return render(request, 'data/index.html', {'search_form': search_form, 'add_form': add_form, 'file_form': file_form, 'message': message})

    if request.method == 'GET':
        """
        Render the webpage with empty search and add forms, and a file upload button
        """
        return render_index()

    elif request.method == 'POST':
        """
        Process the form and send JSON POST request to /data/add or /data/search
        """
        query_type = request.POST['entry_type']
        
        # Process three types of queries - add, search, or upload
        if query_type in ["add", "search"]:
            form = JSONForm(request.POST)
            if not form.is_valid():  # Serve the main webpage again, with the error message
                return render_index('The form for {} request is invalid.'.format(query_type))
            hostname = request.get_host()
            query = form.cleaned_data['entry']
            # Submit POST request to /data/add or /data/search
            url = request.scheme + "://" + hostname + reverse(query_type)
            response = requests.post(url, data=query)
            if not response.ok:
                return render_index('The {} operation was not successful.'.format(query_type))
            if query_type == "add":
                return render_index('Materials successfully added.'.format(query))
            elif query_type == "search":
                return JsonResponse(response.json(), json_dumps_params={'indent': 2}, safe=False)

        # Handle file uploads
        elif query_type == "upload":
            # Populate database from the csv file
            form = DataUploadForm(request.POST, request.FILES)
            if not form.is_valid():
                return render_index('Upload failed.')
            csv_exit_code = csv_to_db(request.FILES['file'])
            if csv_exit_code == 0:
                return render_index('File successfully loaded into the database.')
            else:
                return render_index('Error reading file into the database.')


def get_db_operator(string):
    """ Simple function for parsing the search logic """
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
    string_operators = ["iexact", "icontains"]
    float_operators = ["iexact", "gt", "gte", "lt", "lte"]
    if data_type == str and operator not in string_operators:
        raise ValueError("{} is an incorrect logic operator for character data".format(operator))
    elif data_type == float and operator not in float_operators:
        raise ValueError("{} is an incorrect logic operator for numerical data".format(operator))


def json_to_query(json_query):
    '''
    This function creates db query from a dictionary

    '''
    db_query = Material.objects
    # Check JSON with respect to schema to make sure it's correct
    # Parse query into fields
    if "compound" in json_query:
        #for compound_property in json_query["properties"]:
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
    '''
    Return materials satisfying the search query

    Parameters
    ----------
    db_query : QuerySet object, required
               QuerySet corresponding to the materials filtered by their name and/or properties

    Returns
    -------
    list
               List of dictionaries, each of each matches the material specification (Material model)
    '''
    materials_found = []
    for material in db_query:
        materials_found.append(MaterialSerializer(instance=material).data)
    return materials_found


def add(request):
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
        return JsonResponse(alloys, safe=False)
    else:
        return HttpResponseRedirect(reverse('index'))


def search(request):
    if request.method == 'POST':
        json_query = json.loads(request.body)
        db_query = json_to_query(json_query)
        json_search_result = db_to_json(db_query)
        return JsonResponse(json_search_result, safe=False)
    else:
        return HttpResponseRedirect(reverse('index'))
