import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
ADDRESS = ("127.0.0.1", 5000)

sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session", autouse=True)
def server():
    """Запускает RPC-сервер отдельным процессом на время прогона.

    Сервер должен быть отдельным процессом: иначе он разделит с тестом
    модуль data_layer, и сравнивать систему с моделью станет нечего.
    """
    process = subprocess.Popen(
        [sys.executable, "rpc_server.py"],
        cwd=SRC,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        if process.poll() is not None:
            pytest.fail("Сервер завершился, вероятно порт 5000 занят")
        try:
            socket.create_connection(ADDRESS).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        process.terminate()
        pytest.fail("Сервер не ответил за 5 секунд")
    yield process
    process.terminate()
    process.wait(timeout=5)
