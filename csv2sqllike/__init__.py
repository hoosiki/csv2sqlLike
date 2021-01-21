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
from .Transfer2SQLDB import Transfer2SQLDB


def get_data_from_csv(file_path, sep=',', type_dict=None, encoding='utf-8'):
    pseudo = PsuedoSQLFromCSV(file_path, sep, type_dict, encoding)
    return pseudo


def get_transfer(database_info_dict=None):
    transfer = Transfer2SQLDB(database_info_dict)
    return transfer
