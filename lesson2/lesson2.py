# requires YAML external library
#   pip install pyyaml
import re
import csv
import json
import yaml

FILE_NAMES = ['info_1.txt', 'info_2.txt', 'info_3.txt']
CSV_FILE_NAME = 'main_data.csv'
JSON_FILE_NAME = 'main_data.json'
YAML_FILE_NAME = 'main_data.yaml'
ENCODING = 'cp1251'         # text files encoding
MATCH_SUFFIX = '.*\n'       # any characters until the end of the string
JSON_INDENT = 4             # Indentation level for JSON file


def get_data(file_names: [str]):
    parameters = {
        "Изготовитель системы": [],
        "Название ОС": [],
        "Код продукта": [],
        "Тип системы": []
    }
    # Собираем параметры из каждого файла в списки с соответствующими ключами
    for file_name in file_names:
        try:
            with open(file_name, 'r', encoding=ENCODING) as f:
                data = f.read()
            for key, list_for_key in parameters.items():
                search_obj = re.split(r':', re.search(key + MATCH_SUFFIX, data)[0], maxsplit=1)[1].strip()
                list_for_key.append(search_obj)
        except FileNotFoundError:
            print(f"File not found: {file_name}")
    # Возвращаем словарь
    return parameters


def write_to_csv(parameters, file_name: str):
    # собираем заголовки столбцов CSV из словаря
    data = [[key for key in parameters], ]
    # Перемешиваем (zip) массивы параметров в порядке следования столбцов
    data.extend(list(zip(*list(parameters.values()))))
    # Пишем файл
    with open(file_name, 'w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerows(data)


def write_to_json(parameters, file_name: str):
    # Собираем словари с параметрами из каждого из исходных файлов
    data = [dict(list(zip(parameters.keys(),
                          map(lambda value: value[count], parameters.values()))))
            for count in range(len(list(parameters.values())[0]))]
    # Пишем файл
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=JSON_INDENT)


def write_to_yaml(parameters, file_name: str):
    # Пишем файл
    with open(file_name, 'w') as f:
        yaml.dump(parameters, f, default_flow_style=False, allow_unicode=True)


if __name__ == "__main__":
    entireData = get_data(FILE_NAMES)
    write_to_csv(entireData, CSV_FILE_NAME)
    write_to_json(entireData, JSON_FILE_NAME)
    write_to_yaml(entireData, YAML_FILE_NAME)
