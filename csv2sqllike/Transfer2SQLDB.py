import pymysql
from collections import defaultdict


class Transfer2SQLDB(object):

    def __init__(self, data_base_info=None):
        if data_base_info is None:
            self.__data_base_info = self.__set_data_base_info()
            if self.__data_base_info["charset"] == "":
                self.__data_base_info["charset"] = "utf8"
            if self.__data_base_info["port"] is None:
                self.__data_base_info["port"] = 3306
        else:
            self.__data_base_info = data_base_info
        self.__db = pymysql.connect(**self.__data_base_info)
        print("Succeed to connect to database")
        self.__cursor = self.__db.cursor(pymysql.cursors.DictCursor)
        self.__field_type_dict = None

    def delete_table(self, table_name):
        tmp_command = "drop table " + table_name
        self.__cursor.execute(tmp_command)
        print("Succeed to delete", table_name)

    def show_tables(self):
        tmp_command = "show tables;"
        self.__cursor.execute(tmp_command)
        for x in self.__cursor.fetchall():
            print(x["Tables_in_" + self.__db.db.decode("utf-8")])

    def create_table(self, table_name, input_pseudosql, field_type_dict=None):

        if field_type_dict is None:
            self.__set_field_type_dict(input_pseudosql)
        else:
            self.__field_type_dict = field_type_dict

        tmp_command = self.__get_create_table_command(table_name, self.__field_type_dict)
        print(tmp_command)
        self.__cursor.execute(tmp_command)
        self.__insert_data(table_name, input_pseudosql.data)
        self.__db.commit()

    def bring_data_from_table(self, table_name):
        self.__cursor.execute("select * from " + table_name)
        tmp_tuple = self.__cursor.fetchall()
        tmp_list = list()
        tmp_list.append([key for key in tmp_tuple[0].keys()])
        for x in tmp_tuple:
            tmp_list.append([value for value in x.values()])

        return tmp_list


    def __insert_data(self, input_table_name, data_list):
        tmp_char_type_list = [x for x in self.__field_type_dict.keys() if "CHAR" in self.__field_type_dict[x]]
        tmp_header_list = [x for x in self.__field_type_dict.keys()]

        tmp_str_header = ""
        tmp_str_data = ""
        for index, key in enumerate(tmp_header_list):
            tmp_str_header += tmp_header_list[index] + ", "
            tmp_str_data += "%s, "
        if tmp_str_header != "":
            tmp_str_header = tmp_str_header[:-2]
            tmp_str_data = tmp_str_data[:-2]
        result_str = "insert into " + input_table_name + "(" + tmp_str_header + ") values (" + tmp_str_data + ");"

        print(result_str)

        self.__cursor.executemany(result_str, data_list)

    def __set_field_type_dict(self, input_pseudosql):
        if self.__field_type_dict is None:
            tmp_dict = dict()
            data_type_dict = input_pseudosql.data_type
            for key in data_type_dict.keys():
                if data_type_dict[key] == "str":
                    tmp_dict[key] = "VARCHAR(60)"
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

    @staticmethod
    def __get_create_table_command(table_name, header_type_dict):
        tmp_str = ""
        for key in header_type_dict.keys():
            tmp_str += "_".join(key.lower().split()) + " " + header_type_dict[key] + ", "
        if tmp_str != "":
            tmp_str = tmp_str[:-2]
        return "create table " + table_name + " (" + tmp_str + ") DEFAULT CHARSET=utf8;"

    @staticmethod
    def __set_data_base_info():
        tmp_dict = {"user": "", "passwd": "", "host": "", "db": "", "charset": "", "port": None}
        for key in tmp_dict.keys():
            tmp_str = input(key.ljust(20))
            if key == "port":
                tmp_dict[key] = int(tmp_str)
            else:
                tmp_dict[key] = tmp_str

        return tmp_dict

    @property
    def field_type(self):
        return self.__field_type_dict

    @property
    def data_base_info(self):
        return self.__data_base_info

    @property
    def db(self):
        return self.db

