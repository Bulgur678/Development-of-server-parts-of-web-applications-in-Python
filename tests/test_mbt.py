"""Тестирование RPC на основе модели (этап 3, MBT).

Десять правил — по одному на каждый метод клиента. Правило вызывает
операцию у клиента и у модели, сравнивая результат, а инвариант после
каждого шага сверяет состояние сервера с состоянием модели.

Условия применимости (precondition) не используются: hypothesis плохо
выбирает правила с условиями, и часть методов могла не попасть в прогон.
Вместо этого каждое правило всегда вызывает операцию, а если записи нет,
ошибка должна совпасть у сервера и у модели.
"""

import pytest

import data_layer
from hypothesis import settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule
from rpc_client import RpcClient


def fields(rows) -> list:
    """Записи без datetime: у модели и у сервера своё время."""
    if isinstance(rows, dict):
        rows = [rows]
    return [{k: v for k, v in row.items() if k != "datetime"}
            for row in rows]


def reset(client: RpcClient) -> None:
    """Опустошает сервер и модель перед каждым примером.

    Один и тот же пример hypothesis прогоняет несколько раз: генерация,
    повтор и сжатие. Без сброса состояние каждого прогона разное.
    """
    for row in client.get_all_results():
        client.delete_result(row["key"])
    for row in client.get_all_messages():
        client.delete_message(row["key"])
    for row in client.get_all_users():
        client.delete_user(row["key"])
    data_layer.results.clear()
    data_layer.messages.clear()
    data_layer.users.clear()


class RpcStateMachine(RuleBasedStateMachine):
    """Десять правил — десять методов клиента."""

    def __init__(self):
        super().__init__()
        self.client = RpcClient()
        reset(self.client)

    def teardown(self) -> None:
        self.client.close()

    def any_key(self, table: list, index: int) -> int:
        """Ключ случайной записи таблицы, а если таблица пуста — index."""
        if table:
            return table[index % len(table)]["key"]
        return index

    def both(self, op: str, *args) -> None:
        """Вызывает операцию у сервера и у модели, сравнивая результат.

        Совпадением считается и одинаковая ошибка: сервер возвращает её в
        JSON, клиент превращает в ValueError, модель бросает ValueError.
        """
        try:
            remote = getattr(self.client, op)(*args)
        except ValueError:
            with pytest.raises(ValueError):
                getattr(data_layer, op)(*args)
            return
        assert fields(remote) == fields(getattr(data_layer, op)(*args))

    # --- user ---

    @rule()
    def create_user(self):
        self.both("create_user")

    @rule(index=st.integers(min_value=0))
    def delete_user(self, index):
        self.both("delete_user", self.any_key(data_layer.users, index))

    @rule()
    def get_all_users(self):
        self.both("get_all_users")

    # --- message ---

    @rule(index=st.integers(min_value=0),
          arg=st.text(max_size=12),
          tags=st.sampled_from(["news", "chat", "net"]),
          stage=st.sampled_from(["new", "done"]))
    def create_message(self, index, arg, tags, stage):
        key = self.any_key(data_layer.users, index)
        self.both("create_message", key, arg, arg, tags, stage)

    @rule(index=st.integers(min_value=0))
    def delete_message(self, index):
        self.both("delete_message", self.any_key(data_layer.messages, index))

    @rule()
    def get_all_messages(self):
        self.both("get_all_messages")

    # --- result ---

    @rule(index=st.integers(min_value=0),
          result=st.text(max_size=12),
          stage=st.sampled_from(["final", "retry"]),
          error=st.sampled_from(["", "timeout"]))
    def create_result(self, index, result, stage, error):
        key = self.any_key(data_layer.messages, index)
        self.both("create_result", key, result, stage, error)

    @rule(index=st.integers(min_value=0))
    def delete_result(self, index):
        self.both("delete_result", self.any_key(data_layer.results, index))

    @rule()
    def get_all_results(self):
        self.both("get_all_results")

    # --- соединение ---

    @rule(minutes=st.integers(min_value=1, max_value=60))
    def join(self, minutes):
        self.both("join", minutes)

    @invariant()
    def same_state(self):
        """Состояние сервера совпадает с состоянием модели."""
        pairs = [
            (self.client.get_all_users(), data_layer.users),
            (self.client.get_all_messages(), data_layer.messages),
            (self.client.get_all_results(), data_layer.results),
        ]
        for actual, expected in pairs:
            assert fields(actual) == fields(expected)


TestRpcMbt = RpcStateMachine.TestCase
TestRpcMbt.settings = settings(max_examples=50, deadline=None)
