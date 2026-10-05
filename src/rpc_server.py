import datetime
import json
import socket

import data_layer
from proto import NAMES, check_version, recv_request, send_response

ADDRESS = ("127.0.0.1", 5000)
JOURNAL = "journal.log"

# Код операции -> функция модели слоя данных.
FUNCTIONS = {
    "create_user": data_layer.create_user,
    "delete_user": data_layer.delete_user,
    "get_all_users": data_layer.get_all_users,
    "create_message": data_layer.create_message,
    "delete_message": data_layer.delete_message,
    "get_all_messages": data_layer.get_all_messages,
    "create_result": data_layer.create_result,
    "delete_result": data_layer.delete_result,
    "get_all_results": data_layer.get_all_results,
    "join": data_layer.join,
}


def write_journal(op: str, body: dict, payload: dict) -> None:
    """Дописывает в журнал запись о запросе и его результате."""
    entry = {
        "datetime": f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
        "op": op,
        "body": body,
        "status": "error" if "error" in payload else "ok",
        "payload": payload,
    }
    with open(JOURNAL, "a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def proc(client: socket.socket, address: tuple) -> None:
    """Читает и выполняет запросы одного клиента по очереди."""
    print(f"подключился клиент {address[0]}:{address[1]}")
    while True:
        request = recv_request(client)
        if request is None:
            print(f"клиент {address[0]}:{address[1]} отключился")
            return
        version, op, body = request
        name = NAMES.get(op, f"unknown-{op}")
        try:
            check_version(version)
            payload = {"result": FUNCTIONS[name](**body)}
        except (KeyError, TypeError, ValueError) as error:
            payload = {"error": f"{type(error).__name__}: {error}"}
        write_journal(name, body, payload)
        send_response(client, op, payload)


def loop(sock: socket.socket) -> None:
    """Принимает клиентов по одному, однопоточный режим."""
    while True:
        client, address = sock.accept()
        try:
            proc(client, address)
        except ConnectionError:
            continue
        finally:
            client.close()


def serve(address=ADDRESS) -> None:
    """Создаёт сокет и запускает цикл обработки клиентов."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(address)
    sock.listen()
    print(f"RPC сервер слушает {address[0]}:{address[1]}")
    loop(sock)


if __name__ == "__main__":
    serve()