import csv
import datetime
import re
import copy
import statistics
from tqdm import tqdm
from dateutil.parser import parse


class PsuedoSQLFromCSV(object):
    
    def __init__(self, file_path: str, sep=",", dtype=None, encoding='utf-8'):
        if file_path == "":
            self.__header_data_type_dict = dict()
            self.__header = list()
            self.__data = list()
            self.__cache_data = self.__data
            self.__group_by_dict = dict()
            self.__where_conditions = ""
            self.__group_by_conditions = ""
            self.__aggregate_operation_dict = dict()
        else:
            if self.__check_shape(file_path, sep, encoding=encoding):
                self.__effective_header, header_num = self.__get_effective_headers_number(
                    file_path, sep)
            else:
                self.__effective_header = None

            with open(file_path, "r", encoding=encoding, newline="") as file:
                self.__original_data = list(csv.reader(file))
                self.__original_data[0] = list(
                    "_".join(x.lower().split(" ")) for x in self.__original_data[0])

            if dtype is None:
                self.__header_data_type_dict = self.__get_header_data_type_dict(
                    self.__effective_header)
            else:
                self.__header_data_type_dict = dtype
            self.__make_proper_type(self.__header_data_type_dict)
            self.__header = self.__original_data[0]
            self.__data = self.__original_data[1:]
            self.__cache_data = self.__data
            self.__group_by_dict = dict()
            self.__where_conditions = ""
            self.__group_by_conditions = ""
            self.__aggregate_operation_dict = dict()

            print("Data Loaded : ")
            for i in range(min(len(self.__original_data), 5)):
                print(self.__original_data[i])

    def save_data_to_csv(self, file_path: str, encoding='utf-8') -> None:
        tmp_file = open(file_path, "w", encoding=encoding)
        tmp_writer = csv.writer(tmp_file)
        tmp_writer.writerow(self.__header)
        tmp_writer.writerows(self.__data)
        tmp_file.close()

    @staticmethod
    def __get_effective_headers_number(file_path, sep=",", encoding='utf-8'):
        with open(file_path, "r", encoding=encoding) as file:
            tmp_list = list("_".join(x.lower().strip().split(" "))
                            for x in file.readline().split(sep) if x != "")
        return tmp_list, len(tmp_list)

    def __check_shape(self, file_path, sep=",", encoding='utf-8'):
        headers, num_headers = self.__get_effective_headers_number(
            file_path, sep)
        with open(file_path, "r", encoding=encoding) as file:
            for line, data in enumerate(file):
                if len(data.split(sep)) != num_headers:
                    regex = re.compile(r',"(.*?)",')
                    tmp_mo = regex.findall(data)
                    if len(tmp_mo) != 0:
                        for pattern in tmp_mo:
                            data = data.replace(pattern, "")

                    if len(data.split(sep)) != num_headers:
                        print("Line", line + 1, "does not have consistant columns with", num_headers, "headers.",
                              "This line has", len(data.split(sep)), "elements.")
                        return False
        return True

    def delete_head(self, head: str) -> None:
        tmp_head = "_".join(head.lower().split(" "))
        if tmp_head in self.__header:
            tmp_index = self.__header.index(tmp_head)
            for i in range(len(self.__data)):
                del self.__data[i][tmp_index]
            del self.__header[tmp_index]
            del self.__header_data_type_dict[tmp_head]
        else:
            print("No head called", tmp_head)

    def add_head(self, head: str) -> None:
        tmp_head = "_".join(head.lower().split(" "))
        if tmp_head not in self.__header:
            self.__header.append(tmp_head)
            for i in range(len(self.__data)):
                self.__data[i].append(None)

            tmp_type = input(
                tmp_head + '\'s type(default type is str. options[" ":str, "1":int, "2":float, "3":date] : ')
            if tmp_type == "":
                self.__header_data_type_dict[tmp_head] = "str"
            else:
                if tmp_type == "1" or tmp_type == "int":
                    self.__header_data_type_dict[tmp_head] = "int"
                elif tmp_type == "2" or tmp_type == "float":
                    self.__header_data_type_dict[tmp_head] = "float"
                elif tmp_type == "3" or tmp_type == "date":
                    self.__header_data_type_dict[tmp_head] = "date"

    def __get_header_data_type_dict(self, header_list):
        tmp_dict = dict()
        if header_list is None:
            return None
        for tmp_header in self.__effective_header:
            tmp_index = self.__original_data[0].index(tmp_header)

            if self.__original_data[1][tmp_index] != "":
                tmp_str = tmp_header.ljust(100)[:-len(self.__original_data[1][tmp_index])] + self.__original_data[1][
                    tmp_index]
            else:
                tmp_str = tmp_header.ljust(100)

            print(tmp_str)
            tmp_type = input(
                'insert type(default type is str. options[" ":str, "1":int, "2":float, "3":date] : ')
            if tmp_type == "":
                tmp_dict[tmp_header] = "str"
            else:
                if tmp_type == "1" or tmp_type == "int":
                    tmp_dict[tmp_header] = "int"
                elif tmp_type == "2" or tmp_type == "float":
                    tmp_dict[tmp_header] = "float"
                elif tmp_type == "3" or tmp_type == "date":
                    tmp_dict[tmp_header] = "date"
        return tmp_dict

    def __make_proper_type(self, input_dict):
        for key in tqdm(input_dict.keys()):
            if input_dict[key] == "str":
                continue
            tmp_index = self.__original_data[0].index(key)
            for line_num in range(1, len(self.__original_data)):
                if self.__original_data[line_num][tmp_index] == "":
                    self.__original_data[line_num][tmp_index] = None
                else:
                    try:
                        self.__original_data[line_num][tmp_index] = self.__switch_type(input_dict[key],
                                                                                       self.__original_data[line_num][
                                                                                           tmp_index])
                    except Exception as e:
                        print("Line", line_num + 1,
                              "seems no proper data type")
                        print(e)

    @staticmethod
    def __switch_type(input_type, ori_data):
        tmp_dict = dict(int=lambda x: int(x), float=lambda x: float(x), date=lambda x: parse(x),
                        str=lambda x: x)
        return tmp_dict[input_type](ori_data)

    def where(self, condition: str):
        if condition in self.__where_conditions:
            return self

        tmp_list = condition.split(" ")
        if len(tmp_list) < 3:
            print("Condition :", condition,
                  "is not proper format for where function.")
            pass
        tmp_header = tmp_list[0]
        tmp_operator = tmp_list[1]
        tmp_compared_obj = " ".join(tmp_list[2:])
        try:
            tmp_compared_obj = self.__switch_type(
                self.__header_data_type_dict[tmp_header], tmp_compared_obj)
        except Exception as e:
            print("Failed to convert condition :", condition)
            print(e)
        tmp_index = self.__header.index(tmp_header)
        tmp_data_list = list()
        for line_index in range(len(self.__cache_data)):
            if self.__cache_data[line_index][tmp_index] is None:
                continue
            if self.__operator(self.__cache_data[line_index][tmp_index], tmp_compared_obj, tmp_operator):
                tmp_data_list.append(self.__cache_data[line_index])
        self.__cache_data = tmp_data_list
        if self.__where_conditions == "":
            self.__where_conditions += condition
        else:
            self.__where_conditions += " AND " + condition
        return self

    def group_by(self, input_header: str):

        if input_header not in self.__header:
            print(input_header, "is not included in header")
            return self

        if input_header in self.__group_by_conditions:
            return self

        if self.__group_by_conditions == "":
            self.__group_by_conditions += input_header
        else:
            self.__group_by_conditions += " -> " + input_header
        tmp_index = self.__header.index(input_header)
        tmp_set = set()
        for line_index in range(len(self.__cache_data)):
            tmp_set.add(self.__cache_data[line_index][tmp_index])

        if len(self.__group_by_dict) == 0:
            for key in tmp_set:
                tmp_list = list(self.__cache_data[line_index] for line_index in range(len(self.__cache_data)) if
                                key == self.__cache_data[line_index][tmp_index])
                self.__group_by_dict[key] = tmp_list
        else:
            tmp_key_list = list(self.__group_by_dict.keys())
            for key1 in tmp_key_list:
                for key2 in tmp_set:
                    tmp_key = key1 + "->" + str(key2)
                    tmp_list = list(
                        self.__group_by_dict[key1][line_num] for line_num in range(len(self.__group_by_dict[key1])) if
                        self.__group_by_dict[key1][line_num][tmp_index] == key2)
                    if len(tmp_list) != 0:
                        self.__group_by_dict[tmp_key] = tmp_list

            for key in tmp_key_list:
                del self.__group_by_dict[key]
        return self

    def aggregate_sum(self, input_header: str) -> None:
        if input_header not in self.__header:
            print(input_header, "is not included header")
            return None

        tmp_str = "No grouped || SUM"
        self.__aggregate_operation_dict[tmp_str] = sum(
            self.__extract_list_specific_header(input_header, self.__cache_data))

        for key in self.__group_by_dict.keys():
            self.__aggregate_operation_dict[key + " || SUM"] = sum(
                self.__extract_list_specific_header(input_header, self.__group_by_dict[key]))

    def aggregate_count(self, input_header: str) -> None:
        if input_header not in self.__header:
            print(input_header, "is not included header")
            return None

        tmp_str = "No grouped || COUNT"
        self.__aggregate_operation_dict[tmp_str] = len(
            self.__extract_list_specific_header(input_header, self.__cache_data))

        for key in self.__group_by_dict.keys():
            self.__aggregate_operation_dict[key + " || COUNT"] = len(
                self.__extract_list_specific_header(input_header, self.__group_by_dict[key]))

    def aggregate_avg(self, input_header: str) -> None:
        if input_header not in self.__header:
            print(input_header, "is not included header")
            return None

        tmp_str = "No grouped || AVG"
        tmp_list = self.__extract_list_specific_header(
            input_header, self.__cache_data)
        if len(tmp_list) != 0:
            self.__aggregate_operation_dict[tmp_str] = statistics.mean(
                tmp_list)

        for key in self.__group_by_dict.keys():
            tmp_list = self.__extract_list_specific_header(
                input_header, self.__group_by_dict[key])
            if len(tmp_list) != 0:
                self.__aggregate_operation_dict[key
                                                + " || AVG"] = statistics.mean(tmp_list)

    def aggregate_std(self, input_header):
        if input_header not in self.__header:
            print(input_header, "is not included header")
            return None
        tmp_str = "No grouped || STD"
        tmp_list = self.__extract_list_specific_header(
            input_header, self.__cache_data)
        if len(tmp_list) != 0:
            self.__aggregate_operation_dict[tmp_str] = statistics.pstdev(
                tmp_list)

        for key in self.__group_by_dict.keys():
            tmp_list = self.__extract_list_specific_header(
                input_header, self.__group_by_dict[key])
            if len(tmp_list) != 0:
                self.__aggregate_operation_dict[key
                                                + " || STD"] = statistics.pstdev(tmp_list)

    def clear_cache_data(self) -> None:
        del self.__cache_data
        self.__cache_data = self.__data
        self.__where_conditions = ""
        self.__group_by_conditions = ""
        self.__group_by_dict.clear()
        self.__aggregate_operation_dict.clear()
    
    def retrieve_newline(self) -> None:
        target_index_list = list(self.__header.index(key) for key in self.__header_data_type_dict.keys() if self.__header_data_type_dict[key] == "str")
        for row_i in range(len(self.__data)):
            for col_i in target_index_list:
                self.__data[row_i][col_i] = self.__data[row_i][col_i].replace("<newline>", "\n")

    def __extract_list_specific_header(self, input_header, input_nested_list):
        tmp_index = self.__header.index(input_header)
        tmp_list = list(input_nested_list[line_num][tmp_index] for line_num in range(len(input_nested_list)) if
                        input_nested_list[line_num][tmp_index] is not None)
        return tmp_list

    @staticmethod
    def __operator(arg1, arg2, op):
        tmp_dict = {
            ">": lambda x, y: x > y,
            ">=": lambda x, y: x >= y,
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y
        }
        return tmp_dict[op](arg1, arg2)

    @property
    def header(self) -> list:
        return self.__header

    @header.setter
    def header(self, header):
        self.__header = header

    @property
    def data(self) -> list:
        return self.__data

    @data.setter
    def data(self, data):
        self.__data = data

    @property
    def original_data(self) -> list:
        return self.__original_data

    @property
    def cache_data(self) -> list:
        return self.__cache_data

    @property
    def dtype(self) -> dict:
        return self.__header_data_type_dict

    @dtype.setter
    def dtype(self, data_type):
        self.__header_data_type_dict = data_type

    @property
    def condition_where(self) -> str:
        return self.__where_conditions

    @property
    def condition_group_by(self) -> str:
        return self.__group_by_conditions

    @property
    def cache_dict(self) -> dict:
        return self.__group_by_dict

    @property
    def aggregate_operation_dict(self) -> dict:
        return self.__aggregate_operation_dict
