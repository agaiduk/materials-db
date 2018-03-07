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
