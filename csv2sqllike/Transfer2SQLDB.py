import pymysql
import pandas as pd
import os
import copy
from datetime import datetime
from .PseudoSQLFromCSV import PsuedoSQLFromCSV


class Transfer2SQLDB(object):

    def __init__(self, data_base_info=None):

        if data_base_info is None:
            self.__data_base_info = self.__set_data_base_info()
            if self.__data_base_info["charset"] == "":
                self.__data_base_info["charset"] = "UTF8MB4"
            if self.__data_base_info["port"] is None:
                self.__data_base_info["port"] = 3306
        else:
            self.__data_base_info = copy.deepcopy(data_base_info)

        self.__data_base_info["cursorclass"] = pymysql.cursors.DictCursor

        self.__data_base_info["autocommit"] = False

    def delete_table(self, table_name: str) -> None:
        tmp_connection = pymysql.connect(**(self.__data_base_info))
        try:
            with tmp_connection.cursor() as cursor:
                cursor.execute("drop table {}".format(table_name))
                print("Succeed to delete {}".format(table_name))
            tmp_connection.commit()
        finally:
            tmp_connection.close()

    def get_tables(self) -> list:
        tmp_list = list()
        tmp_connection = pymysql.connect(**(self.__data_base_info))
        try:
            with tmp_connection.cursor() as cursor:
                cursor.execute("show tables")
                tmp_list = list(x["Tables_in_{}".format(tmp_connection.db.decode("utf-8"))] for x in cursor.fetchall())
        finally:
            tmp_connection.close()
        return tmp_list

    def create_table(self, table_name: str, input_pseudosql_or_df: pd.DataFrame, backup=False, keys=None) -> None:

        if backup is True:
            self.backup_table(table_name)

        if type(input_pseudosql_or_df) == type(pd.DataFrame()):
            tmp_sql = PsuedoSQLFromCSV("")
            tmp_sql.header = list("_".join(key.lower().split()) for key in input_pseudosql_or_df.columns)
            tmp_sql.data = input_pseudosql_or_df.to_numpy().tolist()

        else:
            tmp_sql = input_pseudosql_or_df

        self.insert_head_dtypes(tmp_sql.header)

        tmp_connection = pymysql.connect(**(self.__data_base_info))
        try:
            with tmp_connection.cursor() as cursor:
                tmp_command = self.__get_create_table_command(table_name, tmp_sql.header, cursor, keys=keys)
                print(tmp_command)
                cursor.execute(tmp_command)
                self.__write_meta_table_meta_info(table_name, tmp_connection, cursor)
                self.__insert_data(table_name, tmp_sql, cursor)
            tmp_connection.commit()
        finally:
            tmp_connection.close()

    def bring_data_from_table(self, table_name: str) -> pd.DataFrame:

        tmp_connection = pymysql.connect(**(self.db_info_dict))

        try:
            with tmp_connection.cursor() as cursor:
                cursor.execute("select * from {}".format(table_name))
                tmp_df = pd.DataFrame(cursor.fetchall())
                cursor.execute("describe {}".format(table_name))
                tmp_dtype_df = pd.DataFrame(cursor.fetchall())
                for key in list(x.Field for x in tmp_dtype_df.itertuples() if x.Type == "datetime"):
                    tmp_df[key] = tmp_df[key].apply(pd._libs.tslibs.timestamps.Timestamp.date)
        finally:
            tmp_connection.close()

        return tmp_df

    def execute(self, command: str) -> pd.DataFrame:

        tmp_connection = pymysql.connect(**(self.__data_base_info))
        tmp_commands_list = command.replace("\n", "").split(";")

        try:
            with tmp_connection.cursor() as cursor:
                for command in tmp_commands_list:
                    if command == "":
                        continue
                    cursor.execute(command)
                tmp_df = pd.DataFrame(cursor.fetchall())
            tmp_connection.commit()
        finally:
            tmp_connection.close()

        return tmp_df

    def insert_data(self, table_name: str, input_pseudosql_or_df: pd.DataFrame, backup=False, exclude_history=False):

        if backup is True:
            self.backup_table(table_name)

        if type(input_pseudosql_or_df) == type(pd.DataFrame()):
            tmp_sql = PsuedoSQLFromCSV("")
            tmp_sql.header = list("_".join(key.lower().split()) for key in input_pseudosql_or_df.columns)
            tmp_sql.data = input_pseudosql_or_df.to_numpy().tolist()
        else:
            tmp_sql = input_pseudosql_or_df

        tmp_connection = pymysql.connect(**(self.__data_base_info))
        try:
            with tmp_connection.cursor() as cursor:
                if exclude_history is False:
                    self.__write_meta_table_meta_info(table_name, tmp_connection, cursor)
                self.__insert_data(table_name, tmp_sql, cursor)
            tmp_connection.commit()
        finally:
            tmp_connection.close()

    def backup_table(self, table_name: str) -> None:
        tmp_path = os.environ["DATA_BACKUP"] + "/" + table_name + \
                   datetime.now().strftime("%Y%m%d%H%M") + ".csv"
        self.bring_data_from_table(table_name).to_csv(tmp_path, index=False)

    def delete_head_dtype(self, keyword_list: list) -> None:
        tmp_connection = pymysql.connect(**(self.__data_base_info))
        try:
            with tmp_connection.cursor() as cursor:
                # for keyword in keyword_list:
                # cursor.executemany("delete from metainfo_share.head_dtype where keyword=\"{}\";".format(keyword))
                cursor.executemany("delete from metainfo_share.head_dtype where keyword=%s;", keyword_list)
            tmp_connection.commit()
        finally:
            tmp_connection.close()

    def __add_head_dtype(self, cursor, keyword: str, dtype: str) -> None:
        cursor.execute(
            "replace into metainfo_share.head_dtype(keyword, dtype) values(\"{}\", \"{}\")".format(keyword, dtype))

    def insert_head_dtypes(self, keyword_list: list):
        tmp_connection = pymysql.connect(**(self.__data_base_info))
        try:
            with tmp_connection.cursor() as cursor:
                cursor.execute("select * from metainfo_share.head_dtype;")
                tmp_res_key_set = set(keyword_list) - set(
                    keyword for keyword in pd.DataFrame(cursor.fetchall())["keyword"])

                if len(tmp_res_key_set) != 0:
                    for key in keyword_list:
                        if key not in tmp_res_key_set:
                            continue
                        tmp_input = input("chose proper data type for {}:\n 1-varchar(100), 2-text, 3-float, 4-double, "
                                          "5-bigint, 6-tinyint(1), 7-datetiem".format(key))
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
                        elif tmp_input == "7":
                            tmp_input = "datetime"
                        self.__add_head_dtype(cursor, key, tmp_input)
            tmp_connection.commit()
        finally:
            tmp_connection.close()

    def __get_create_table_command(self, table_name, head_list, cursor, keys=None) -> str:
        cursor.execute("select * from metainfo_share.head_dtype;")
        tmp_df = pd.DataFrame(cursor.fetchall())
        tmp_head_type_dict = dict((data.keyword, data.dtype) for data in tmp_df.itertuples())
        tmp_col_type_str = ", ".join(list("{} {}".format(head, tmp_head_type_dict[head]) for head in head_list))
        if keys is None:
            return "create table {0}({1}) DEFAULT CHARSET=UTF8MB4;".format(table_name, tmp_col_type_str)
        else:
            tmp_primary_key = "primary key({})".format(", ".join(keys))
            return "create table {0}({1}, {2}) DEFAULT CHARSET=UTF8MB4;".format(table_name, tmp_col_type_str,
                                                                                tmp_primary_key)

    def __insert_data(self, input_table_name, input_pseudosql, cursor):
        tmp_str_header = ", ".join(input_pseudosql.header)
        tmp_str_data = ", ".join(list("%s" for _ in input_pseudosql.header))
        result_str = "replace into {}({}) values({})".format(input_table_name, tmp_str_header, tmp_str_data)
        print(result_str)
        cursor.executemany(result_str, input_pseudosql.data)

    def __check_if_exist(self, table_name: str, connection, cursor) -> bool:
        cursor.execute("show tables")
        tmp_list = list(x["Tables_in_{}".format(connection.db.decode("utf-8"))] for x in cursor.fetchall())
        if table_name in tmp_list:
            return True
        else:
            return False

    def __make_table_history_table(self, cursor) -> None:
        cursor.execute(
            "create table table_history (time DATETIME, name VARCHAR(30), action VARCHAR(20)) DEFAULT CHARSET=UTF8MB4;")

    def __write_meta_table_meta_info(self, table_name: str, connection, cursor) -> None:
        if not self.__check_if_exist("table_history", connection, cursor):
            self.__make_table_history_table(cursor)

        tmp_now = datetime.now()
        if self.__check_if_exist(table_name, connection, cursor):
            tmp_action = "modify"
        else:
            tmp_action = "create"
        template_str = "insert into table_history(time, name, action) values (%s, %s, %s);"
        cursor.executemany(
            template_str, [[tmp_now, table_name, tmp_action]])


    @property
    def db_info_dict(self):
        return self.__data_base_info

    @db_info_dict.setter
    def db_info_dict(self, input_dict):
        self.__data_base_info = input_dict

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