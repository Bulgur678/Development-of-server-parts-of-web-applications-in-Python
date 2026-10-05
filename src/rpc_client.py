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

    # Методы повторяют функции модели слоя данных.

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


def run_command(client: RpcClient, line: str) -> bool:
    """Выполняет команду клиента. Возвращает False, если пора выходить."""
    try:
        parts = shlex.split(line)
        if not parts:
            return True
        command, args = parts[0], parts[1:]

        match command:
            case "quit" | "exit":
                return False
            case "help":
                print(HELP)
            case "create_user":
                check_args(args, 0, "create_user")
                print_rows("создано", [client.create_user()])
            case "create_message":
                usage = "create_message <user> <arg> <desc> <tags> <stage>"
                check_args(args, 5, usage)
                print_rows("создано", [client.create_message(*args)])
            case "create_result":
                usage = "create_result <message> <result> <stage> <error>"
                check_args(args, 4, usage)
                print_rows("создано", [client.create_result(*args)])
            case "delete_user":
                check_args(args, 1, "delete_user <key>")
                print_rows("удалено", [client.delete_user(args[0])])
            case "delete_message":
                check_args(args, 1, "delete_message <key>")
                print_rows("удалено", [client.delete_message(args[0])])
            case "delete_result":
                check_args(args, 1, "delete_result <key>")
                print_rows("удалено", [client.delete_result(args[0])])
            case "get_all_users" | "get_all_messages" | "get_all_results":
                check_args(args, 0, command)
                print_rows(command, getattr(client, command)())
            case "join":
                print_rows("join", client.join(int(args[0]) if args else 7))
            case _:
                print(f"Неизвестная команда '{command}'. Наберите help")
    except ValueError as error:
        print(f"Ошибка: {error}")
    return True


def repl() -> None:
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


def show_spec() -> None:
    """Показывает, как запрос разложен по байтам (таблица 13)."""
    data = encode_request(OPCODES["join"], {"minutes": 7})
    print("Запрос целиком:", data)
    print("  версия протокола:", data[0])
    print("  код операции:", data[1])
    print("  размер тела:", int.from_bytes(data[2:6], "big"))
    print("  тело:", data[6:])


def demo() -> None:
    """Вызывает удалённо все функции модели слоя данных."""
    print("=" * 60)
    print("КЛИЕНТ RPC: УДАЛЁННЫЙ ВЫЗОВ ФУНКЦИЙ МОДЕЛИ")
    print("=" * 60)
    show_spec()

    client = RpcClient()

    print("Создание записей")
    first = client.create_user()
    second = client.create_user()
    print_rows("create_user", [first, second])
    message = client.create_message(first["key"], "Привет по RPC",
                                    "Описание", "news", "new")
    print_rows("create_message", [message])
    result = client.create_result(message["key"], "Принято", "final", "")
    print_rows("create_result", [result])

    print("Чтение всех записей")
    print_rows("get_all_users", client.get_all_users())
    print_rows("get_all_messages", client.get_all_messages())
    print_rows("get_all_results", client.get_all_results())

    print("Операция соединения")
    print_rows("join", client.join())

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

    print("Удаление записей")
    print_rows("delete_result", [client.delete_result(result["key"])])
    print_rows("delete_message", [client.delete_message(message["key"])])
    print_rows("delete_user", [client.delete_user(second["key"])])
    print_rows("get_all_users", client.get_all_users())
    client.close()


def main() -> int:
    """Запускает демонстрацию или интерактивный режим."""
    if "--demo" in sys.argv:
        demo()
    else:
        repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())