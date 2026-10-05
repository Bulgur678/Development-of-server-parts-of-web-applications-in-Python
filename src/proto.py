import json
import socket

VERSION = 1

# Смещения тел запроса и ответа
REQUEST_HEADER_SIZE = 6
RESPONSE_HEADER_SIZE = 7

# Коды операций, общие для клиента и сервера.
OPCODES = {
    "create_user": 1,
    "delete_user": 2,
    "get_all_users": 3,
    "create_message": 4,
    "delete_message": 5,
    "get_all_messages": 6,
    "create_result": 7,
    "delete_result": 8,
    "get_all_results": 9,
    "join": 10,
}

NAMES = {code: name for name, code in OPCODES.items()}


def check_version(version: int) -> None:
    """Проверяет версию протокола из заголовка запроса."""
    if version != VERSION:
        raise ValueError(
            f"Ожидалась версия протокола {VERSION}, получено {version}"
        )


# Запрос


def encode_request(op: int, body: dict) -> bytes:
    """Собирает запрос: версия, код операции, размер тела, тело."""
    data = json.dumps(body).encode("utf-8")
    return (VERSION.to_bytes(1, "big")
            + op.to_bytes(1, "big")
            + len(data).to_bytes(4, "big")
            + data)


def decode_request(data: bytes) -> tuple[int, int, dict]:
    """Разбирает запрос: версия, код операции, тело."""
    version = int.from_bytes(data[0:1], "big")
    op = int.from_bytes(data[1:2], "big")
    size = int.from_bytes(data[2:6], "big")
    return version, op, json.loads(data[6:6 + size].decode("utf-8"))


# Ответ


def encode_response(op: int, body: dict) -> bytes:
    """Собирает ответ: размер тела, код операции, тело."""
    data = json.dumps(body).encode("utf-8")
    return (len(data).to_bytes(5, "big")
            + op.to_bytes(2, "big")
            + data)


def decode_response(data: bytes) -> tuple[int, dict]:
    """Разбирает ответ: код операции, тело."""
    size = int.from_bytes(data[0:5], "big")
    op = int.from_bytes(data[5:7], "big")
    return op, json.loads(data[7:7 + size].decode("utf-8"))


# Передача по сокету


def recv_all(sock: socket.socket, size: int) -> bytes:
    """Читает из потока ровно size байт, b"" — соединение закрыто."""
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return b""
        data += chunk
    return data


def send_request(sock: socket.socket, op: int, body: dict) -> None:
    """Отправляет запрос."""
    sock.sendall(encode_request(op, body))


def recv_request(sock: socket.socket):
    """Возвращает запрос или None, если клиент отключился."""
    header = recv_all(sock, REQUEST_HEADER_SIZE)
    if not header:
        return None
    size = int.from_bytes(header[2:6], "big")
    body = recv_all(sock, size)
    if len(body) < size:
        return None
    return decode_request(header + body)


def send_response(sock: socket.socket, op: int, body: dict) -> None:
    """Отправляет ответ."""
    sock.sendall(encode_response(op, body))


def recv_response(sock: socket.socket) -> tuple[int, dict]:
    """Принимает ответ: код операции, тело."""
    header = recv_all(sock, RESPONSE_HEADER_SIZE)
    if not header:
        raise ConnectionError("Соединение закрыто до получения ответа")
    size = int.from_bytes(header[0:5], "big")
    return decode_response(header + recv_all(sock, size))