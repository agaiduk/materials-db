import csv
import json
import tempfile
from data.models import Material
from data.tools import valid_float, operator_type, valid_operator_type
from haystack.query import SearchQuerySet
from data.serializers import MaterialSerializer
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from data.schemas import schemas


def db_from_csv(csv_file):
    '''
    Load in-memory file csv_file into materials database
    This function does simple checks for the csv data file format but be careful using it
    (This functionality was adeed to populate the database quickly)

    Parameters
    ----------
    csv_file : in-memory file, required
                each line of this file should contain the compound name,
                and compound proprty names/values pairs

    Returns
    -------
    int
                Exit codes:
                0 : success
                1 : first line of the csv does not start with "Chemical formula"
    '''
    # Create temporary file and fill it with the uploaded csv data
    with tempfile.TemporaryFile() as f_byte:
        fname = f_byte.name

        for chunk in csv_file.chunks():
            f_byte.write(chunk)

        # Now open the file for reading and parse it into csv
        f_byte.seek(0)
        f = open(fname, "r")
        reader = csv.reader(f)
        row = next(reader)
        # Check if we have correct header
        if not row[0] == "Chemical formula":
            return "Incorrect csv file format"
        for row in reader:
            n_fields = len(row)
            # Skip the record if the total number of fields is odd:
            # Supposed to be one compound name & n properties (2*n + 1)
            if n_fields % 2 == 0:
                continue
            material = Material(compound=row[0])
            try:
                material.save()
            except ValueError:
                return "You provided an incorrect chemical formula of the compound"
            [material.properties.create(propertyName=row[n], propertyValue=row[n+1]) for n in range(1,n_fields-1,2)]
        return


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
    # Since input json conforms to the schema, parse it without looking back...
    query = Material.objects
    if "search" in query_dictionary:
        haystack_query_compound = SearchQuerySet().raw_search(query_dictionary["search"])
        query_compound = Material.objects.filter(pk__in=[material.object.pk for material in haystack_query_compound])
    if "properties" in query_dictionary:
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
    return query.intersection(query_compound)


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
