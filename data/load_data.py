import os
import csv
import tempfile
import time
from .models import Material


def valid_float(string):
    ''' True for a string that represents a float (or an integer) '''
    try:
        float(string)
        return True
    except ValueError:
        return False


def csv_to_db(csv_file):
    """
    Load the in-memory file csv_file into the materials database
    """
    # Create temporary file and fill it with the uploaded csv data
    cwd = os.getcwd()
    with tempfile.TemporaryFile() as f_byte:
        fname = f_byte.name

        for chunk in csv_file.chunks():
            f_byte.write(chunk)

        # Now open the file and parse it into csv
        f_byte.seek(0)
        f = open(fname, "r")
        reader = csv.reader(f)
        row = next(reader)
        if row[0] == "Chemical formula":
            # We have a correct header; process file further
            for row in reader:
                n_fields = len(row)
                if n_fields % 2 == 0:  # Error exit if the total number of fields is odd: One compound name & n properties (2*n + 1)
                    return 1
                material = Material(compound=row[0])
                material.save()
                for n in range(1,n_fields-1,2):
                    material.properties.create(propertyName=row[n], propertyValue=row[n+1])
            return 0
        else:
            return 1
