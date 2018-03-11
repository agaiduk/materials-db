import json
from data.models import Material
from data.tools import valid_float, operator_type, valid_operator_type
from haystack.query import SearchQuerySet
from data.serializers import MaterialSerializer
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from data.schemas import schemas


def save_to_db(instance):
    '''
    bool function to save an instance of the model class to the database

    Parameters
    ----------
    instance : instance of a model class, required

    Returns
    -------
    bool
            True : the instance has been added to the db
            False : exceptions were raised for whatever reason
    '''
    try:
        instance.save()
        return True
    # If the compound cannot be added (e.g. pyEQL)
    except (ValueError, IndexError):
        return False


def db_from_csv(csv_file):
    '''
    Load in-memory file csv_file into materials database
    This function does simple checks for the csv data file format

    Parameters
    ----------
    csv_file : in-memory file, required
                each line of this file should contain the compound name,
                and compound proprty names/values pairs

    Returns
    -------
    (str, int)
                Tuple consisting of the exit message & Http status code
    '''
    if csv_file.multiple_chunks():
        return "Uploaded file size ({:.2f} Mb) is too large - should be less than 2.5 Mb.".format(csv_file.size/(1024*1024))

    try:
        f = csv_file.read().decode("utf-8")
    except UnicodeDecodeError:
        return "Incorrect file format", 400
    lines = f.split('\n')

    # Check if we have correct header; delete it if we do; return an error if we don't
    if not lines[0].startswith("Chemical formula,"):
        return "Incorrect csv file format; first line is: \"{}\"".format(lines[0]), 400
    else:
        del lines[0]

    materials_added = 0
    for line in lines:
        fields = line.strip().split(',')

        n_fields = len(fields)
        # Skip the record if the total number of fields is odd:
        # Supposed to be one compound name & n properties (2*n + 1)
        # "n_fields < 2" takes care of possible dos line endings when you end up with an empty string
        if n_fields < 2 or n_fields % 2 == 0:
            continue
        material = Material(compound=fields[0])
        material_saved = save_to_db(material)
        if not material_saved:
            continue
        [material.properties.create(propertyName=fields[n], propertyValue=fields[n+1]) for n in range(1,n_fields-1,2)]
        # Save the material again to update the csv field, needed for search indexing
        material_saved = save_to_db(material)
        if not material_saved:
            continue
        materials_added += 1
    return "{} out of {} materials added to the database".format(materials_added, len(lines)), 200


def json_to_dictionary(request_body, request_type):
    '''
    Convert string containing a json file to a dictionary

    Parameters
    ----------
    request_body : string, required
                        String provided by the user, containing a json object (or array of json objects)
    request_type : string, required
                        String corresponding to the type of the request - currently add or search

    Returns
    -------
    dict
            dictionary or list of dictionaries from json
    string
            error message, if input is not a json or if json is not consistent with the schema
    '''
    def valid_json(dictionary, schema_key):
        '''
        This function checks that the dictionary conforms to
        the schema defined by the schema_key name (add, search)

        Parameters
        ----------
        dictionary : dict, required
                        Contains the dictionary to be validated
        schema_key : string, required
                        A key in the dictionary of schemes

        Returns
        -------
        bool
                    True/False

        Depends
        -------
        schemas : dict
                    Dictionary containing schemas of json objects to be validated
        '''
        try:
            validate(instance=dictionary, schema=schemas[schema_key])
            return True
        except ValidationError:
            return False

    # Check that there is a schema corresponding to the request type
    if request_type not in schemas:
        return "There is no schema corresponding to {}".format(request_type)

    # Try serializing string; if this doesn't work, return an error message
    try:
        dictionary = json.loads(request_body)
    except:
        return "The text you provided is not a json"

    # If the string is a valid json, check if it conforms to the request_type schema
    if not valid_json(dictionary=dictionary, schema_key=request_type):
        return "The json you provided does not conform to the {} schema".format(request_type)

    # All checks passed, now return the dictionary
    return dictionary


def query_from_dictionary(query_dictionary):
    '''
    Create db query from a dictionary

    Parameters
    ----------
    query_dictionary : dict, required
                        Query represented by a dictionary, obtained from user's json

    Returns
    -------
    QuerySet
                QuerySet object obtained by applying filters in dictionary to database
    OR:
    string
                Error message if there were any errors

    Depends
    -------
    Material model class
    '''
    query = Material.objects
    # First, apply the raw search filter through haystack API
    # Since input json conforms to the schema, parse it without further checks
    if "search" in query_dictionary:
        search_query = SearchQuerySet().raw_search(query_dictionary["search"])
        # Convert haystack search query to django search query
        try:
            query = Material.objects.filter(pk__in=[material.object.pk for material in search_query])
        except AttributeError:  # compounds were found in the index but not in database
            return "Search index is out of sync with the database"
    if "properties" in query_dictionary:
        # Now filter by property values
        for compound_property in query_dictionary["properties"]:
            property_name = compound_property["name"]
            property_value = compound_property["value"]
            property_logic = compound_property["logic"]
            operator = operator_type(property_logic)
            # Process requests that are floats
            if valid_float(property_value) and valid_operator_type(operator, data_type=float):
                query = query.filter(properties__propertyName__icontains=property_name,
                    **{'properties__propertyValueFloat__' + operator: float(property_value)}
                    )
            # Process requests that are strings
            elif not valid_float(property_value) and valid_operator_type(operator, data_type=str):
                query = query.filter(properties__propertyName__icontains=property_name,
                    **{'properties__propertyValue__' + operator: property_value}
                    )
            elif operator == None:
                return "Incorrect search operator"
            else:
                return "Incorrect combination of the property value and operator"
    return query


def query_to_dictionary(query):
    '''
    Return materials satisfying the search query

    Parameters
    ----------
    query : QuerySet object, required
            QuerySet corresponding to the materials filtered by their name and/or properties

    Returns
    -------
    list
            List of dictionaries, each of each matches the material specification (Material model)
    '''
    return [MaterialSerializer(instance=material).data for material in query]
