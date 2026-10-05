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



def main() -> None:
    pass
