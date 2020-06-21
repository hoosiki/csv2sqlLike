import os
import sys
import datetime
import re

try:
    import csv
    import xlrd
    import encodings
except ImportError:
    print(ImportError)

from .info import __VERSION__, __version__
from .PseudoSQLFromCSV import PsuedoSQLFromCSV

def is_proper_table(file_path):
    regex = re.compile(r',"(.*)",')
    with open(file_path) as file:
        tmp_set = set()
        for line_number, line in enumerate(file):
            if line_number == 0:
                header_numer = line.count(",")
                tmp_set.add(header_numer)
            else:
                tmp_mo = regex.findall(line)
                if len(tmp_mo) != 0:
                    for pattern in tmp_mo:
                        line = line.replace(pattern, "")
                if line.count(",") > header_numer:
                    print("Warning! : " + str(line_number + 1) + " line does not have same formate: " )
                    print(line)
                    tmp_set.add(line.count(","))
    if 0 in tmp_set:
        tmp_set.remove(0)
    if len(tmp_set) == 1:
        return True
    else:
        return False

def get_data_from_csv(file_path):
    if is_proper_table(file_path) != True:
        print(file_path + " is not proper csv file")
        return None
    else:
        psuedosql = PsuedoSQLFromCSV(file_path)
        return psuedosql



