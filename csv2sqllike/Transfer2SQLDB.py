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

    def create_table(self, table_name: str, input_pseudosql_or_df: pd.DataFrame, if_exists="replace", index=False, dtype=None, backup=False, keys=list()) -> None:
        
        self.__write_meta_table_meta_info(table_name)


        if type(input_pseudosql_or_df) == type(pd.DataFrame()):
            tmp_head_list = list(input_pseudosql_or_df.columns)
            self.insert_head_dtypes(tmp_head_list)
            tmp_command = self.__get_create_table_command(
                table_name, input_pseudosql_or_df.columns, keys=keys)
            print(tmp_command)
            self.__cursor.execute(tmp_command)
            input_pseudosql_or_df.to_sql(
                con=self.__connect_for_pd, name=table_name, if_exists=if_exists, index=index, dtype=dtype)

        else:
            self.insert_head_dtypes(input_pseudosql_or_df.header)
            tmp_command = self.__get_create_table_command(table_name, input_pseudosql_or_df.header, keys=keys)
            print(tmp_command)
            self.__cursor.execute(tmp_command)
            self.__insert_data(table_name, input_pseudosql_or_df)
            self.__db.commit()
        
        if backup is True:
            self.backup_table(table_name)

    def bring_data_from_table(self, table_name: str) -> pd.DataFrame:
        if table_name is not None:
            self.__cursor.execute("select * from " + table_name)
        tmp_tuple = self.__cursor.fetchall()
        return pd.DataFrame(tmp_tuple)

    def execute(self, command: str) -> pd.DataFrame:
        self.__cursor.execute(command)
        tmp_list = self.__cursor.fetchall()
        return pd.DataFrame(tmp_list)

    def insert_data(self, table_name: str, input_pseudosql_or_df: pd.DataFrame, field_type_dict=None, if_exists="append", index=False, dtype=None, backup=False, exclude_history=False):
        
        if exclude_history is False:
            self.__write_meta_table_meta_info(table_name)
        
        if backup is True:
            self.backup_table(table_name)
            
        if type(input_pseudosql_or_df) == type(pd.DataFrame()):
            input_pseudosql_or_df.to_sql(
                con=self.__connect_for_pd, name=table_name, if_exists=if_exists, index=index, dtype=dtype)
        else:
            self.__insert_data(table_name, input_pseudosql_or_df)

    def __insert_data(self, input_table_name, input_pseudosql_or_df):
        tmp_header_list = input_pseudosql_or_df.header
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
    
    def delete_head_dtype(self, keyword_list: str) -> None:
        for keyword in keyword_list:
            self.execute("delete from metainfo_share.head_dtype where keyword=\"{}\"".format(keyword))

    def add_head_dtype(self, keyword: str, dtype: str) -> None:
        self.execute("insert into metainfo_share.head_dtype(keyword, dtype) values(\"{}\", \"{}\")".format(keyword, dtype))

    def insert_head_dtypes(self, keyword_list:list):
        tmp_df = self.bring_data_from_table("metainfo_share.head_dtype")
        tmp_df = tmp_df.to_numpy()
        tmp_key_set = set(data[0] for data in tmp_df)
        tmp_res_set = set(keyword_list) - tmp_key_set
        if len(tmp_res_set) != 0:
            for key in keyword_list:
                if key not in tmp_res_set:
                    continue
                tmp_input = input("chose proper data type for {}: 1 - varchar(100), 2 - text, 3 - float, 4 - double, 5 - bigint, 6 - tinyint(1)".format(key))
                if tmp_input == "1" or tmp_input == "":
                    tmp_input = "varchar(100)"
                elif tmp_input == "2":
                    tmp_input = "text"
                elif tmp_input == "3":
                    tmp_input = "float"
                elif tmp_input == "4":
                    tmp_input = "double"
                elif tmp_input == "5":
                    tmp_input = "bigint"
                elif tmp_input == "6":
                    tmp_input = "tinyint(1)"
                self.add_head_dtype(key, tmp_input)

    def __get_create_table_command(self, table_name, head_list, keys=list()):
        tmp_df = self.bring_data_from_table("metainfo_share.head_dtype")
        tmp_df = tmp_df.to_numpy()
        tmp_head_type_dict =  {data[0]:data[1] for data in tmp_df}
        tmp_str = ""
        for key in head_list:
            tmp_str += "_".join(key.lower().split()) + \
                " " + tmp_head_type_dict[key] + ", "
            if key in keys:
                tmp_str = tmp_str[:-2] + " primary key, "
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
