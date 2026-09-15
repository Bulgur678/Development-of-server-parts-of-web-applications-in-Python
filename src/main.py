import time 
import os
from typing import Any
from types import NoneType

user = {}
message = {}
result = {}

SCHEMA: dict[str, dict[str, type | tuple[type, ...]]] = {
    "user":{
        "key": int,
        "datetime": (int, NoneType)
    },
    "message":{
        "key": int,
        "datetime": (int, NoneType),
        "arg": str,
        "user": int,
        "description": str,
        "tags": str,
        "stage": str
    },
    "result":{
        "key": int,
        "datetime": (int, NoneType),
        "result": str,
        "stage": str,
        "error": str,
        "message": int
    },
}

def get_table_name(table: dict) -> str | None:
    if table is user:
        return "user"
    elif table is message:
        return "message"
    elif table is result:
        return "result"
    else:
        return None

def validate_kwargs(table_name: str, **kwargs: Any) -> None:
    """Проверяет передаваемые аргументы по схеме таблицы."""

    if table_name not in SCHEMA:
        raise ValueError(f"Таблица '{table_name}' отсутствует в SCHEMA.")

    table_schema = SCHEMA[table_name]

    for key, value in kwargs.items():
        # Проверяем, существует ли такое поле в таблице
        if key not in table_schema:
            raise KeyError(f"Поле '{key}' не существует в таблице '{table_name}' {SCHEMA[table_name]}")


        expected_type = table_schema[key]

        # Проверяем тип данных
        if not isinstance(value, expected_type):
            raise TypeError(
                f"В таблице '{table_name}' для поля '{key}' ожидался тип {expected_type}, но получен {type(value).__name__} ({value!r})."
            )


def parsing(kwargs: dict) -> dict:
    for key, value in kwargs.items:
        if value.isdigit():
            kwargs[key] = int(value)
    return kwargs



def create_table(table: dict, **kwargs) -> None:
    """Универсальный конструктор таблиц"""

    table_name = get_table_name(table)

    kwargs = parsing(kwargs)

    validate_kwargs(table_name, **kwargs)

    if "key" not in kwargs:
        raise KeyError (f"Отсутвует индекс key = ")
    
    key_index = kwargs["key"]
    if key_index in table:
        raise ValueError(f"Индекс {kwargs[key_index]} уже существует")

    if "datetime" not in kwargs:
        kwargs["datetime"] = int(time.time())

    return_table = {}    

    for schema_key in SCHEMA[table_name].keys():
        # Создаем таблицы

        # if schema_key == "key":
        #     continue

        if schema_key in kwargs:
            if schema_key in SCHEMA and kwargs[schema_key] is int and kwargs[schema_key] not in globals()[schema_key]:
                raise ValueError(f"Новозможно добавить объект из таблицы {schema_key} с индексом {kwargs[schema_key]} в таблицу {table_name}")

            return_table[schema_key] = kwargs[schema_key]
        else:
            return_table[schema_key] = None

    table[kwargs["key"]] = return_table


def delete_table(table: dict, key: int) -> None:
    table.pop(key)


def print_table(table: dict) -> None:
    for key, inner_table in table.items():
        print(f"key: {key}")
        for inner_key, value in inner_table.items():
            print(f"    {inner_key}: {value}")


def table_join() -> dict:
    """SELECT M.tags, R.error, R.result
    FROM Message M
    JOIN Result R ON M.key = R.message
    WHERE M.datetime >= NOW() - INTERVAL 7 MINUTE;"""

    current_time = int(time.time())

    joined = [
    {**msg, **res}
    for res in result.values()
    for msg_id, msg in message.items()
    if msg_id == res["message"] and res["datetime"] >= current_time - 7 * 60
    ]

    return_dict = {}
    for dic in joined:
        key = dic["key"]
        return_dict[key] = dic


    return return_dict


clear = lambda: os.system('cls')


def run():
    
    command = input(f"1: Создать таблицу\n2: Удалить таблицу\n3: Напечатать таблицу\nВыберите действие: ")
    clear()
    match command:
        # Создать тбалицу
        case "1":
            args = input("Ввидите таблицу, ключ, и данные для заполнения.\n@ ").split(","," ")
            
                

        
    




    

# print("User")
# create_table(user, key=2, datetime = 777777777)
# create_table(user, key=1)
# create_table(user, key=3, datetime = 333)
# print_table(user)
# print()

# print("Message")
# create_table(message, key = 1)
# create_table(message, key = 2, arg = "Привет мир", user = 1)
# print_table(message)
# print()

# print("Message")
# create_table(result, key = 1, message = 2, error = "Ошибка")
# print_table(result)

# print("\nУдаление данных \n")
# print("User")
# delete_table(user, 1)
# delete_table(user, 2)
# print_table(user)

"""==================================="""


# create_table(user, key=1)

# create_table(message, key = 1, arg = "Пока", datetime = 9999999999999999)
# create_table(message, key = 2, arg = "Привет мир", user = 1)

# create_table(result, key = 1, message = 1, error = "Ошибка")
# create_table(result, key = 2, message = 2, error = "Вторая ошибка", result = "Результат")
# create_table(result, key = 3, message = 2, error = "Всё хорошо", datetime = 1)
# print_table(table_join())




if __name__ == "__main__":
    clear()
    while True:
        run()












