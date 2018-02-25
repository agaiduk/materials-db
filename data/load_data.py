import os
import csv
from .models import Material

def csv_to_db(fname):
    if os.path.isfile(fname) is False:
        print(fname, "File does not exist")
        print("Current path:", os.getcwd())
        return 1
    with open(fname) as f:
        reader = csv.reader(f)
        row = next(reader)
        if row[0] == "Chemical formula":
        # We have a correct header; process file further
            for row in reader:
                #if row[0] != "Chemical formula":
                _, created = Material.objects.get_or_create(
                    chemical_formula=row[0],
                    property1_name=row[1],
                    property1_value=row[2],
                    property2_name=row[3],
                    property2_value=row[4],
                    )
            return 0
        else:
            return 1
