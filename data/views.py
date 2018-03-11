from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
import requests

from data.models import Material
from data.forms import JSONForm, DataUploadForm
import data.db as db


def index(request):
    '''
    Web interface to the materials database API
    '''
    def render_index(message=None, status=None):
        '''
        Serve the index webpage with an optional message

        Parameters
        ----------
        message : str, optional
                    Generate an index webpage with a message
        status  : int, optional
                    status of the request, for generating errors

        Returns
        -------
        response object
                    An index webpage with an optional message
        '''
        search_form = JSONForm()
        add_form = JSONForm()
        file_form = DataUploadForm()
        return render(request, 'data/index.html', {'search_form': search_form, 'add_form': add_form, 'file_form': file_form, 'message': message}, status=status)

    if request.method == 'GET':
        # Render the webpage with empty search and add forms, and a file upload button
        return render_index()

    elif request.method == 'POST':
        # Process the form and send JSON POST request to /data/add or /data/search
        query_type = request.POST['entry_type']

        # Process add and search requests
        if query_type in ['add', 'search']:
            form = JSONForm(request.POST)
            # Serve the main webpage again, with the error message
            if not form.is_valid():
                return render_index('The form for {} request is invalid.'.format(query_type))
            # Prepare and submit POST request to /data/add or /data/search
            query = form.cleaned_data['entry']
            hostname = request.get_host()
            url = request.scheme + '://' + hostname + reverse(query_type)
            response = requests.post(url, data=query)
            # Check if the response was successful, then serve
            # the main page again or display the search results
            if not response.ok:
                return render_index(response.json()['error'])
            if query_type == 'add':
                return render_index('Materials added successfully.'.format(query))
            elif query_type == 'search':
                return JsonResponse(response.json(), json_dumps_params={'indent': 2}, safe=False)

        # Handle file uploads
        elif query_type == 'upload':
            # Populate database from the csv file
            form = DataUploadForm(request.POST, request.FILES)
            if not form.is_valid():
                return render_index('Upload failed.')
            message, status = db.db_from_csv(request.FILES['file'])
            return render_index(message=message, status=status)

        # This shouldn't normally happen, unless there's a bug in the code...
        else:
            return render_index('Incorrect request: {}'.format(query_type))


def add(request):
    '''
    API for adding material to the database

    Parameters
    ----------
    request : Http request
                Request containing json for adding materials to the database

    Returns
    -------
    JsonResponse
                The materials just added or error message if something went wrong
    '''
    if request.method == 'POST':
        # Load request body, check it & make sure it conforms to schema
        query_dictionary = db.json_to_dictionary(request.body, request_type='add')

        # If the result of the last operation is a string (error message),
        # send a JsonResoponse containing the string
        if isinstance(query_dictionary, str):
            return JsonResponse({"error": query_dictionary}, status=400)

        for alloy in query_dictionary:  # query_dictionary is a list of materials
            # Initialize a material
            material = Material(compound=alloy["compound"])
            material_saved = db.save_to_db(material)
            if not material_saved:
                return JsonResponse({"error": "Chemical formula \"{}\" is incorrect (must follow pyEQL syntax)".format(alloy["compound"])}, status=400)
            [material.properties.create(
                propertyName=compound_property["propertyName"], propertyValue=compound_property["propertyValue"])
                for compound_property in alloy["properties"]]
            # Save the material again to update the csv field, needed for search indexing
            material_saved = db.save_to_db(material)
            if not material_saved:
                return JsonResponse({"error": "Chemical formula \"{}\" is incorrect (must follow pyEQL syntax)".format(alloy["compound"])}, status=400)

        # If success, return just added materials as a json
        return JsonResponse(query_dictionary, safe=False)
    else:
        return JsonResponse({"error": "Only POST method supported"}, status=405)


def search(request):
    '''
    API for searching material in the database

    Parameters
    ----------
    request : Http request
                Request containing json for querying the database

    Returns
    -------
    JsonResponse
                Search result or error message if something went wrong
    '''
    if request.method == 'POST':
        # Load request body, check it & make sure it conforms to schema
        query_dictionary = db.json_to_dictionary(request.body, request_type='search')
        # If the result of the last operation is a string rather than dict
        # (error message), send a JsonResoponse containing this string
        if isinstance(query_dictionary, str):
            return JsonResponse({"error": query_dictionary}, status=400)

        # If everything went well, serialize the json, compile the search query,
        # and make the list of materials matching the request
        query = db.query_from_dictionary(query_dictionary)
        if isinstance(query, str):
            return JsonResponse({"error": query}, status=400)

        search_result = db.query_to_dictionary(query)
        # Output the list of materials as a Json
        return JsonResponse(search_result, safe=False)
    else:
        return JsonResponse({"error": "Only POST method supported"}, status=405)
