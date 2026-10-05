import shlex
import time

# Таблицы в памяти.
users: list[dict] = []
messages: list[dict] = []
results: list[dict] = []


# Общие помощники


def now() -> int:
    """Возвращает текущее время в секундах."""
    return int(time.time())


def get_next_key(table: list[dict]) -> int:
    """Возвращает ключ для новой записи таблицы."""
    if not table:
        return 0
    return max(row["key"] for row in table) + 1


def get_row(table: list[dict], key, name: str) -> dict:
    """Возвращает запись таблицы по ключу."""
    for row in table:
        if row["key"] == int(key):
            return row
    raise ValueError(f"В таблице '{name}' нет записи с key={key}")


def print_rows(title: str, rows: list[dict]) -> None:
    """Печатает заголовок и список записей."""
    print(f"--- {title} ({len(rows)}) ---")
    for row in rows:
        print("   ", row)
    if not rows:
        print("    (пусто)")


# Таблица user


def create_user() -> dict:
    """Создаёт запись в таблице user."""
    user = {
        "key": get_next_key(users),
        "datetime": now(),
    }
    users.append(user)
    return user


def delete_user(key) -> dict:
    """Удаляет запись из таблицы user."""
    row = get_row(users, key, "user")
    users.remove(row)
    return row


def get_all_users() -> list[dict]:
    """Возвращает все записи таблицы user."""
    return users


# Таблица message


def create_message(user, arg, description="", tags="", stage="") -> dict:
    """Создаёт запись в таблице message для указанного пользователя."""
    owner = get_row(users, user, "user")
    message = {
        "key": get_next_key(messages),
        "datetime": now(),
        "arg": arg,
        "user": owner["key"],
        "description": description,
        "tags": tags,
        "stage": stage,
    }
    messages.append(message)
    return message


def delete_message(key) -> dict:
    """Удаляет запись из таблицы message."""
    row = get_row(messages, key, "message")
    messages.remove(row)
    return row


def get_all_messages() -> list[dict]:
    """Возвращает все записи таблицы message."""
    return messages


# Таблица result


def create_result(message, result="", stage="", error="") -> dict:
    """Создаёт запись в таблице result для указанного сообщения."""
    source = get_row(messages, message, "message")
    row = {
        "key": get_next_key(results),
        "datetime": now(),
        "result": result,
        "stage": stage,
        "error": error,
        "message": source["key"],
    }
    results.append(row)
    return row


def delete_result(key) -> dict:
    """Удаляет запись из таблицы result."""
    row = get_row(results, key, "result")
    results.remove(row)
    return row


def get_all_results() -> list[dict]:
    """Возвращает все записи таблицы result."""
    return results


# Операция соединения


def join(minutes: int = 7) -> list[dict]:
    """Выборка: pi M.tags, R.error, R.result
    (sigma M.datetime >= now - 7 min (M join M.key = R.message R)).
    """
    threshold = now() - minutes * 60
    rows = []
    for message in messages:
        if message["datetime"] < threshold:
            continue
        for result in results:
            if result["message"] == message["key"]:
                rows.append({
                    "tags": message["tags"],
                    "error": result["error"],
                    "result": result["result"],
                })
    return rows


# Операции таблиц для команд REPL.
TABLES = {
    "user": {"get_all": get_all_users, "delete": delete_user},
    "message": {"get_all": get_all_messages, "delete": delete_message},
    "result": {"get_all": get_all_results, "delete": delete_result},
}


def get_ops(name: str) -> dict:
    """Возвращает операции таблицы по её имени."""
    if name not in TABLES:
        raise ValueError(
            f"Неизвестная таблица '{name}'. Доступны: {', '.join(TABLES)}"
        )
    return TABLES[name]


# REPL

HELP = """Команды:
  show <table>                                       все записи таблицы
  create_user                                        новый пользователь
  create_message <user> <arg> <desc> <tags> <stage>  новое сообщение
  create_result <message> <result> <stage> <error>   новый результат
  delete <table> <key>                               удалить запись
  join [minutes]                                     операция соединения
  demo                                               загрузить пример данных
  help                                               эта справка
  quit                                               выход

Таблицы: user, message, result.
Значения с пробелами берите в кавычках:
  create_message 0 "Привет мир" "Описание" news new"""


def check_args(args: list[str], count: int, usage: str) -> None:
    """Проверяет количество аргументов команды."""
    if len(args) != count:
        raise ValueError(
            f"Ожидалось {count} аргументов. Использование: {usage}"
        )


def run_command(line: str) -> bool:
    """Выполняет команду. Возвращает False, если пора выходить."""
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
            case "show":
                check_args(args, 1, "show <table>")
                print_rows(args[0], get_ops(args[0])["get_all"]())
            case "create_user":
                check_args(args, 0, "create_user")
                print("создано:", create_user())
            case "create_message":
                usage = "create_message <user> <arg> <desc> <tags> <stage>"
                check_args(args, 5, usage)
                print("создано:", create_message(*args))
            case "create_result":
                usage = "create_result <message> <result> <stage> <error>"
                check_args(args, 4, usage)
                print("создано:", create_result(*args))
            case "delete":
                check_args(args, 2, "delete <table> <key>")
                table, key = args
                print("удалено:", get_ops(table)["delete"](key))
            case "join":
                print_rows("join", join(int(args[0]) if args else 7))
            case "demo":
                load_demo_data()
            case _:
                print(f"Неизвестная команда '{command}'. Наберите help")
    except ValueError as error:
        print(f"Ошибка: {error}")
    return True


def repl() -> None:
    """Интерактивный режим работы со слоем данных."""
    print("Слой доступа к данным. Наберите help.\n")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nПока!")
            return
        if not run_command(line):
            print("Пока!")
            return


# Демонстрация


def load_demo_data() -> None:
    """Заполняет таблицы примерами данных."""
    users.clear()
    messages.clear()
    results.clear()

    first = create_user()
    second = create_user()

    one = create_message(first["key"], "Привет мир", "Первое",
                         "news", "new")
    two = create_message(second["key"], "Пока мир", "Второе",
                         "chat", "new")
    old = create_message(first["key"], "Старое", "Не попадёт в выборку",
                         "news", "done")
    old["datetime"] = now() - 3600

    create_result(one["key"], "Принято", "final", "")
    create_result(two["key"], "Не обработано", "final", "timeout")
    create_result(old["key"], "Устаревшая обработка", "final", "")


def demo() -> None:
    """Показывает работу всех операций слоя."""
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ СЛОЯ ДОСТУПА К ДАННЫМ")
    print("=" * 60)

    load_demo_data()
    print("Чтение всех записей")
    print_rows("user", get_all_users())
    print_rows("message", get_all_messages())
    print_rows("result", get_all_results())

    print("Создание записи (key и datetime заполняются автоматически)")
    message = create_message(0, "Новое сообщение", "Создано в демонстрации",
                             "demo", "new")
    print("   ", message)
    create_result(message["key"], "Готово", "final", "")

    print("Удаление записи")
    print("   удалено:", delete_message(1))
    print_rows("message", get_all_messages())

    print("Соединение: pi M.tags, R.error, R.result "
          "(sigma M.datetime >= now - 7 min (M join M.key = R.message R))")
    print_rows("join за 7 минут", join())
    print_rows("join за 120 минут", join(120))

    print("Обработка ошибок")
    cases = [
        ("неизвестная таблица", lambda: get_ops("unknown")),
        ("неверный тип ключа", lambda: delete_user("не число")),
        ("нет пользователя", lambda: create_message(99, "arg", "d", "t", "s")),
        ("нет сообщения", lambda: create_result(99, "res", "final", "")),
        ("удаление отсутствующей записи", lambda: delete_result(99)),
    ]
    for title, action in cases:
        try:
            action()
        except ValueError as error:
            print(f"    {title}: ValueError: {error}")


if __name__ == "__main__":
    # demo()
    repl()
