"""Клиент к RPC (этап 2).

Имена методов класса совпадают с именами функций модели слоя данных,
поэтому удалённый вызов выглядит как обычный вызов функции:

    client = RpcClient()
    user = client.create_user()

Запуск:
    python rpc_client.py          # интерактивный режим
    python rpc_client.py --demo   # демонстрация всех вызовов
"""

import shlex
import socket
import sys

from data_layer import check_args, print_rows
from proto import OPCODES, encode_request, recv_response, send_request

ADDRESS = ("127.0.0.1", 5000)


class RpcClient:
    """Клиент RPC к серверу слоя доступа к данным."""

    def __init__(self, address=ADDRESS) -> None:
        self.sock = socket.create_connection(address)

    def call(self, op: str, **body) -> object:
        """Отправляет запрос и возвращает результат операции."""
        send_request(self.sock, OPCODES[op], body)
        _, payload = recv_response(self.sock)
        if "error" in payload:
            raise ValueError(payload["error"])
        return payload["result"]

    def create_user(self) -> dict:
        return self.call("create_user")

    def delete_user(self, key) -> dict:
        return self.call("delete_user", key=key)

    def get_all_users(self) -> list:
        return self.call("get_all_users")

    def create_message(self, user, arg, description="",
                       tags="", stage="") -> dict:
        return self.call("create_message", user=user, arg=arg,
                         description=description, tags=tags, stage=stage)

    def delete_message(self, key) -> dict:
        return self.call("delete_message", key=key)

    def get_all_messages(self) -> list:
        return self.call("get_all_messages")

    def create_result(self, message, result="", stage="", error="") -> dict:
        return self.call("create_result", message=message, result=result,
                         stage=stage, error=error)

    def delete_result(self, key) -> dict:
        return self.call("delete_result", key=key)

    def get_all_results(self) -> list:
        return self.call("get_all_results")

    def join(self, minutes: int = 7) -> list:
        return self.call("join", minutes=minutes)

    def close(self) -> None:
        """Закрывает соединение с сервером."""
        self.sock.close()


HELP = """Команды повторяют методы клиента:
  create_user                                        новый пользователь
  create_message <user> <arg> <desc> <tags> <stage>  новое сообщение
  create_result <message> <result> <stage> <error>   новый результат
  delete_user <key>                                  удалить пользователя
  delete_message <key>                               удалить сообщение
  delete_result <key>                                удалить результат
  get_all_users                                      все пользователи
  get_all_messages                                   все сообщения
  get_all_results                                    все результаты
  join [minutes]                                     операция соединения
  help                                               эта справка
  quit                                               выход

Значения с пробелами берите в кавычки:
  create_message 0 "Привет мир" "Описание" news new"""

CREATE = ("create_user", "create_message", "create_result")
DELETE = ("delete_user", "delete_message", "delete_result")
READ = ("get_all_users", "get_all_messages", "get_all_results")

COMMANDS = {
    "create_user": (0, "create_user"),
    "create_message": (
        5, "create_message <user> <arg> <desc> <tags> <stage>"),
    "create_result": (
        4, "create_result <message> <result> <stage> <error>"),
    "delete_user": (1, "delete_user <key>"),
    "delete_message": (1, "delete_message <key>"),
    "delete_result": (1, "delete_result <key>"),
}


def run_command(client: RpcClient, line: str) -> bool:  # pragma: no cover
    """Выполняет команду клиента. Возвращает False, если пора выходить."""
    try:
        parts = shlex.split(line)
        if not parts:
            return True
        command, args = parts[0], parts[1:]
        if command in ("quit", "exit"):
            return False
        execute(client, command, args)
    except ValueError as error:
        print(f"Ошибка: {error}")
    return True


def execute(client: RpcClient, command: str,
            args: list) -> None:  # pragma: no cover
    """Передаёт команду нужному обработчику или печатает справку."""
    if command == "help":
        print(HELP)
    elif command in CREATE:
        create(client, command, args)
    elif command in DELETE:
        delete(client, command, args)
    elif command in READ:
        read(client, command, args)
    elif command == "join":
        print_rows("join", client.join(int(args[0]) if args else 7))
    else:
        print(f"Неизвестная команда '{command}'. Наберите help")


def create(client: RpcClient, command: str,
           args: list) -> None:  # pragma: no cover
    """Создание записи: имя метода клиента совпадает с командой."""
    count, usage = COMMANDS[command]
    check_args(args, count, usage)
    print_rows("создано", [getattr(client, command)(*args)])


def delete(client: RpcClient, command: str,
           args: list) -> None:  # pragma: no cover
    """Удаление записи по её ключу."""
    count, usage = COMMANDS[command]
    check_args(args, count, usage)
    print_rows("удалено", [getattr(client, command)(args[0])])


def read(client: RpcClient, command: str,
         args: list) -> None:  # pragma: no cover
    """Чтение всех записей таблицы."""
    check_args(args, 0, command)
    print_rows(command, getattr(client, command)())


def repl() -> None:  # pragma: no cover
    """Интерактивный режим клиента."""
    print("RPC клиент. Наберите help.\n")
    try:
        client = RpcClient()
    except ConnectionRefusedError:
        print("Не удалось подключиться: запустите python rpc_server.py")
        return
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if not run_command(client, line):
            break
    client.close()
    print("Пока!")


def show_spec() -> None:  # pragma: no cover
    """Показывает, как запрос разложен по байтам (таблица 13)."""
    data = encode_request(OPCODES["join"], {"minutes": 7})
    print("Запрос целиком:", data)
    print("  версия протокола:", data[0])
    print("  код операции:", data[1])
    print("  размер тела:", int.from_bytes(data[2:6], "big"))
    print("  тело:", data[6:])


def demo() -> None:  # pragma: no cover
    """Вызывает удалённо все функции модели слоя данных."""
    print("КЛИЕНТ RPC: УДАЛЁННЫЙ ВЫЗОВ ФУНКЦИЙ МОДЕЛИ")
    show_spec()
    client = RpcClient()
    second, message, result = demo_create(client)
    demo_read(client)
    demo_errors(client)
    demo_delete(client, second, message, result)
    client.close()


def demo_create(client: RpcClient) -> tuple:  # pragma: no cover
    """Создание пользователей, сообщения и результата."""
    print("Создание записей")
    first = client.create_user()
    second = client.create_user()
    print_rows("create_user", [first, second])
    message = client.create_message(first["key"], "Привет по RPC",
                                    "Описание", "news", "new")
    print_rows("create_message", [message])
    result = client.create_result(message["key"], "Принято", "final", "")
    print_rows("create_result", [result])
    return second, message, result


def demo_read(client: RpcClient) -> None:  # pragma: no cover
    """Чтение всех записей и операция соединения."""
    print("Чтение всех записей")
    print_rows("get_all_users", client.get_all_users())
    print_rows("get_all_messages", client.get_all_messages())
    print_rows("get_all_results", client.get_all_results())
    print("Операция соединения")
    print_rows("join", client.join())


def demo_errors(client: RpcClient) -> None:  # pragma: no cover
    """Ошибки, которые возвращает сервер."""
    print("Обработка ошибок сервера")
    cases = [
        ("нет пользователя",
         lambda: client.create_message(99, "arg", "desc", "tags", "new")),
        ("удаление отсутствующей записи",
         lambda: client.delete_user(99)),
    ]
    for title, action in cases:
        try:
            action()
        except ValueError as error:
            print(f"    {title}: {error}")


def demo_delete(client: RpcClient, user: dict,
                message: dict, result: dict) -> None:  # pragma: no cover
    """Удаление созданных записей."""
    print("Удаление записей")
    print_rows("delete_result", [client.delete_result(result["key"])])
    print_rows("delete_message", [client.delete_message(message["key"])])
    print_rows("delete_user", [client.delete_user(user["key"])])
    print_rows("get_all_users", client.get_all_users())


def main() -> int:  # pragma: no cover
    """Запускает демонстрацию или интерактивный режим."""
    if "--demo" in sys.argv:
        demo()
    else:
        repl()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
