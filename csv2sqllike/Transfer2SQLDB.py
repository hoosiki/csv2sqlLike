import pymysql
import pandas as pd
import os
from datetime import datetime
from collections import defaultdict
from sqlalchemy import create_engine


class Transfer2SQLDB(object):

    def __init__(self, data_base_info=None):
        if data_base_info is None:
            self.__data_base_info = self.__set_data_base_info()
            if self.__data_base_info["charset"] == "":
                self.__data_base_info["charset"] = "UTF8MB4"
            if self.__data_base_info["port"] is None:
                self.__data_base_info["port"] = 3306
        else:
            self.__data_base_info = data_base_info
        if "autocommit" not in self.__data_base_info.keys():
            self.__data_base_info["autocommit"] = True
        self.__db = pymysql.connect(**self.__data_base_info)
        print("Succeed to connect to database")
        self.__cursor = self.__db.cursor(pymysql.cursors.DictCursor)
        self.__field_type_dict = None

        tmp_db_info = 'mysql+mysqlconnector://' + data_base_info["user"] + ':' + data_base_info["password"] + '@' + \
            data_base_info["host"] + ':' + \
            str(data_base_info["port"]) + '/' + \
            data_base_info["db"] + '?charset=utf8'
        self.__connect_for_pd = create_engine(tmp_db_info)

    def delete_table(self, table_name: str) -> None:
        tmp_command = "drop table " + table_name
        self.__cursor.execute(tmp_command)
        print("Succeed to delete", table_name)

    def get_tables(self) -> list:
        tmp_list = list()
        tmp_command = "show tables;"
        self.__cursor.execute(tmp_command)
        for x in self.__cursor.fetchall():
            tmp_list.append(x["Tables_in_" + self.__db.db.decode("utf-8")])
        return tmp_list

    def create_table(self, table_name: str, input_pseudosql_or_df: pd.DataFrame, if_exists="replace", index=False, dtype=None, backup=False, charlen=60) -> None:
        
        self.__write_meta_table_meta_info(table_name)

        if type(input_pseudosql_or_df) == type(pd.DataFrame()):
            input_pseudosql_or_df.to_sql(
                con=self.__connect_for_pd, name=table_name, if_exists=if_exists, index=index, dtype=dtype)

        else:
            if dtype is None:
                self.__set_field_type_dict(input_pseudosql_or_df, charlen=charlen)
            else:
                self.__field_type_dict = dtype

            tmp_command = self.__get_create_table_command(
                table_name, self.__field_type_dict)
            print(tmp_command)
            self.__cursor.execute(tmp_command)
            self.__insert_data(table_name, input_pseudosql_or_df)
            self.__db.commit()
        
        if backup is True:
            self.backup_table(table_name)

    def bring_data_from_table(self, table_name: str) -> pd.DataFrame:
        self.__get_data_type(table_name)
        if table_name is not None:
            self.__cursor.execute("select * from " + table_name)
        tmp_tuple = self.__cursor.fetchall()
        return pd.DataFrame(tmp_tuple)

    def execute(self, command: str) -> pd.DataFrame:
        self.__cursor.execute(command)
        tmp_list = self.__cursor.fetchall()
        return pd.DataFrame(tmp_list)

    def insert_data(self, table_name: str, input_pseudosql_or_df: pd.DataFrame, field_type_dict=None, if_exists="append", index=False, dtype=None, backup=False, exclude_history=False, keys=None):
        
        if exclude_history is False:
            self.__write_meta_table_meta_info(table_name)
        
        if backup is True:
            self.backup_table(table_name)
            
        if type(input_pseudosql_or_df) == type(pd.DataFrame()):
            input_pseudosql_or_df.to_sql(
                con=self.__connect_for_pd, name=table_name, if_exists=if_exists, index=index, dtype=dtype, keys=keys)
        else:
            self.__field_type_dict = self.__get_data_type(table_name)
            self.__insert_data(table_name, input_pseudosql_or_df)

    def __insert_data(self, input_table_name, input_pseudosql_or_df):

        # if len(self.__field_type_dict) == 0:
        #    self.__set_field_type_dict(input_pseudosql_or_df)

        tmp_char_type_list = [x for x in self.__field_type_dict.keys(
        ) if "CHAR" in self.__field_type_dict[x]]
        tmp_header_list = [x for x in self.__field_type_dict.keys()]

        tmp_str_header = ""
        tmp_str_data = ""
        for index, key in enumerate(tmp_header_list):
            tmp_str_header += tmp_header_list[index] + ", "
            tmp_str_data += "%s, "
        if tmp_str_header != "":
            tmp_str_header = tmp_str_header[:-2]
            tmp_str_data = tmp_str_data[:-2]
        result_str = "insert into " + input_table_name + \
            "(" + tmp_str_header + ") values (" + tmp_str_data + ");"

        print(result_str)

        self.__cursor.executemany(result_str, input_pseudosql_or_df.data)

    def __set_field_type_dict(self, input_pseudosql, charlen=60):
        if self.__field_type_dict is None or len(self.__field_type_dict) == 0:
            tmp_dict = dict()
            data_type_dict = input_pseudosql.dtype
            for key in data_type_dict.keys():
                if data_type_dict[key] == "str":
                    tmp_dict[key] = "VARCHAR(" + str(charlen) + ")"
                elif data_type_dict[key] == "float":
                    tpm_input = input(key + " float(1) or double(2)")
                    if tpm_input == "1":
                        tmp_dict[key] = "FLOAT"
                    elif tpm_input == "2":
                        tmp_dict[key] = "DOUBLE"
                elif data_type_dict[key] == "date":
                    tpm_input = input("DATE(1) or DATETIME(2)")
                    if tpm_input == "1":
                        tmp_dict[key] = "DATE"
                    elif tpm_input == "2":
                        tmp_dict[key] = "DATETIME"
                elif data_type_dict[key] == "int":
                    tmp_dict[key] = "INT"
            self.__field_type_dict = tmp_dict

    def __get_data_type(self, table_name):
        self.__cursor.execute("SHOW FIELDS FROM " + table_name)
        tmp_list = self.__cursor.fetchall()
        tmp_type_dict = dict()
        for tmp_dict in tmp_list:
            tmp_type_dict[tmp_dict["Field"]] = tmp_dict["Type"]

        return tmp_type_dict

    def __check_if_exist(self, table_name: str) -> bool:
        if table_name in self.get_tables():
            return True
        else:
            return False
    
    def __make_table_history_table(self) -> None:
        self.__cursor.execute("create table table_history (time DATETIME, name VARCHAR(30), action VARCHAR(20)) DEFAULT CHARSET=UTF8MB4;")
        #self.__cursor.execute("create table table_history (name VARCHAR(30), action VARCHAR(20)) DEFAULT CHARSET=UTF8MB4;")
        
    def __write_meta_table_meta_info(self, table_name: str) -> None:
        if not self.__check_if_exist("table_history"):
            self.__make_table_history_table()
            
        tmp_now = datetime.now()
        tmp_meta_info_table = "table_history"
        tmp_etc = ""
        if self.__check_if_exist(table_name):
            tmp_etc = "modify"
        else:
            tmp_etc = "create"
        template_str = "insert into table_history(time, name, action) values (%s, %s, %s);"
        #result_str = "insert into " + tmp_meta_info_table + "(name, action) values (\"test\", \"test\");"
        self.__cursor.executemany(template_str, [[tmp_now, table_name, tmp_etc]])
    
    def backup_table(self, table_name: str) -> None:
        tmp_path = os.environ["DATA_BACKUP"] + "/" + table_name + datetime.now().strftime("%Y%m%d%H%M") + ".csv"
        self.bring_data_from_table(table_name).to_csv(tmp_path, index=False)

    def get_heads_dtype(self, table_name: str) -> (list, list):
        tmp_df = self.execute("describe " + table_name)
        tmp_num = tmp_df.to_numpy()
        return [x[0] for x in tmp_num], [x[1] for x in tmp_num]


    @staticmethod
    def __get_create_table_command(table_name, header_type_dict):
        tmp_str = ""
        for key in header_type_dict.keys():
            tmp_str += "_".join(key.lower().split()) + \
                " " + header_type_dict[key] + ", "
        if tmp_str != "":
            tmp_str = tmp_str[:-2]
        return "create table " + table_name + " (" + tmp_str + ") DEFAULT CHARSET=UTF8MB4;"

    @staticmethod
    def __set_data_base_info():
        tmp_dict = {"user": "", "passwd": "", "host": "",
                    "db": "", "charset": "", "port": None}
        for key in tmp_dict.keys():
            tmp_str = input(key.ljust(20))
            if key == "port":
                tmp_dict[key] = int(tmp_str)
            else:
                tmp_dict[key] = tmp_str

        return tmp_dict

    @property
    def dtype(self) -> dict:
        return self.__field_type_dict

    @dtype.setter
    def dtype(self, input_dtype_dict):
        self.__field_type_dict = input_dtype_dict

    @property
    def data_base_info(self) -> dict:
        return self.__data_base_info

    @property
    def cursor(self):
        return self.__cursor
