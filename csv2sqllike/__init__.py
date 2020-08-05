import os
import sys
import datetime
import re
import pandas as pd

try:
    import csv
    import xlrd
    import encodings
except ImportError:
    print(ImportError)

from .info import __VERSION__, __version__
from .PseudoSQLFromCSV import PsuedoSQLFromCSV
from .Transfer2SQLDB import Transfer2SQLDB


def get_data_from_csv(file_path: str, sep=',', dtype=None, encoding='utf-8') -> PsuedoSQLFromCSV:
    pseudo = PsuedoSQLFromCSV(file_path, sep, dtype, encoding)
    return pseudo


def get_transfer(database_info_dict=None) -> Transfer2SQLDB:
    transfer = Transfer2SQLDB(database_info_dict)
    return transfer

def to_list_from_df(df: pd.DataFrame, sep=',', dtype=None, encoding='utf-8'):
    df.replace(to_replace=[r"\\t|\\n|\\r", "\t|\n|\r", "\n"], value=["<newline>","<newline>","<newline>"], regex=True).to_csv("./tmp_tmp.csv", index=False)
    #df.to_csv("./tmp_tmp.csv", index=False, line_terminator=";;;;;\n")
    print("finished output")
    tmp_pseudo_sql = get_data_from_csv("./tmp_tmp.csv", sep=sep, dtype=dtype, encoding=encoding)
    tmp_pseudo_sql.retrieve_newline()
    os.remove("./tmp_tmp.csv")
    return tmp_pseudo_sql
