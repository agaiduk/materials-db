import csv
import json
import tempfile
from data.models import Material
from data.serializers import MaterialSerializer
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from data.schemas import schemas


def db_from_csv(csv_file):
    '''
    Load in-memory file csv_file into materials database
    This function does not check for the csv data file format

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
        if row[0] == "Chemical formula":
            # We have a correct header; process file further
            for row in reader:
                n_fields = len(row)
                # Skip the record if the total number of fields is odd:
                # Supposed to be one compound name & n properties (2*n + 1)
                if n_fields % 2 == 0:
                    continue
                material = Material(compound=row[0])
                material.save()
                # Can we do the procedure below in a list-comprehension-style fashion?
                for n in range(1,n_fields-1,2):
                    material.properties.create(propertyName=row[n], propertyValue=row[n+1])
            return 0
        else:
            return 1


def valid_float(string):
    '''
    True for a string that represents a float (or an integer)

    Parameters
    ----------
    string : string, required
                String representing the property value

    Returns
    -------
    bool
            True (string can be represented as a valid float)
            False (string cannot be represented as a valid float)
    '''
    try:
        float(string)
        return True
    except ValueError:
        return False


def operator_type(operator):
    '''
    Simple function for parsing the search logic
    Can a given string be recognized as one of the known operators?

    Parameters
    ----------
    operator : string, required
                Operator for querying the database, from user's json

    Returns
    -------
    string
            One of the recognized db query operators
    None
            If the operator name obtained from user has not been recognized
    '''
    db_operators = {
        ("eq", "==", "=", "match", "matches"): "iexact",
        ("contain", "contains", "contained", "in"): "icontains",
        (">", "gt", "more"): "gt",
        (">=", "gte", "ge"): "gte",
        ("<", "lt", "less"): "lt",
        ("<=", "=<" "lte", "le"): "lte"
    }
    for key in db_operators:
        if operator in key:
            return db_operators[key]
    return None


def valid_operator_type(operator, data_type):
    '''
    Check if an operator is suitable for a given data type

    Parameters
    ----------
    operator : string, required
                Operator for querying database, obtained from operator_type function
    data_type : object type (float, string), required
                Type of the string property: can it be represented by a float or not?
                (i.e., is it numerical in its nature?)

    Returns
    -------
    bool
            True/False
    '''
    string_operators = ["iexact", "icontains"]
    float_operators = ["iexact", "gt", "gte", "lt", "lte"]
    # Check if the function is called properly
    if data_type not in [str, float]:
        return False
    # Now do the work
    if data_type == str and operator not in string_operators:
        return False
    elif data_type == float and operator not in float_operators:
        return False
    # In case the operator type was not recognized
    # (it would be OK not to do this check, but better safe than sorry)
    elif operator == None:
        return False
    # Looks like we're good
    else:
        return True


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
    # Since input json conforms to the schema, parse it without looking back...
    if "compound" in query_dictionary:
        compound_name = query_dictionary["compound"]["value"]
        compound_logic = query_dictionary["compound"]["logic"]
        operator = operator_type(compound_logic)
        if not valid_operator_type(operator, data_type=str):
            return "The operator \"{}\" for compound name you provided is inconsistent with textual data".format(operator)
        query = query.filter(**{'compound__' + operator: compound_name})
    if "properties" in query_dictionary:
        for compound_property in query_dictionary["properties"]:
            property_name = compound_property["name"]
            property_value = compound_property["value"]
            property_logic = compound_property["logic"]
            operator = operator_type(property_logic)
            # Process requests that are floats
            if valid_float(property_value) and valid_operator_type(operator, data_type=float):
                query = query.filter(properties__propertyName__icontains=property_name,
                    **{'properties__propertyValue__' + operator: property_value}
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
    materials_found = []
    for material in query:
        materials_found.append(MaterialSerializer(instance=material).data)
    return materials_found


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
