import csv
import datetime
class PsuedoSQLFromCSV(object):

    def __init__(self, file_path):

        with open(file_path) as file:
            data = list(csv.reader(file))
            self.__header = [x for x in data[0] if x != ""]
            if len(self.__header) != len(data[1]):
                tmp_length = len(self.__header)
                tmp_data = [x[:tmp_length] for x in data[1:]]
                self.__data = tmp_data
            else:
                self.__data = data[1:]
        self.__set_header_data_type()
        for i, header in enumerate(self.__header):
            if self.__data_type_dict[header] != "str":
                for line in self.__data:
                    if line[i] != "":
                        line[i] = self.__switch_type(self.__data_type_dict[header], line[i])
                    else:
                        line[i] = None


    def __set_header_data_type(self):
        self.__data_type_dict = dict()
        for i in range(len(self.header)):
            tmp_str = self.__header[i].ljust(100)[:-len(self.__data[1][i])] + self.__data[1][i]
            print(tmp_str)
            tmp_type = input("insert type(default type is str. options:str, int, float, date) : ")
            if tmp_type == "":
                self.__data_type_dict[self.__header[i]] = "str"
            else:
                self.__data_type_dict[self.__header[i]] = tmp_type
    
    def __make_proper_type(self):
        for key in self.__header:
            if self.__data_type_dict[key] == "str":
                continue
    
    def __switch_type(self, input_type, ori_data):

        tmp_dict = {\
                    "int":lambda x:int(x),\
                    "float":lambda x:float(x),\
                    "date":lambda x:datetime.datetime(x)\
                   }

        return tmp_dict[input_type](ori_data)
    
    def where(self, condition):
        tmp_data_list = list()
        args = condition.split(" ")
                
    @property
    def header(self):
        return self.__header
    
    @property
    def data(self):
        return self.__data
    
    @property
    def data_types_dict(self):
        return self.__data_type_dict
            
            