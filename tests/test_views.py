import pytest
from freezegun import freeze_time
from src.views import get_greeting, process_transactions, load_user_settings
import pandas as pd
import json


# Тесты для get_greeting с использованием фикстуры freeze_time
@freeze_time("2026-06-12 08:30:00")  # Утро
def test_get_greeting_morning():
    assert get_greeting() == "Доброе утро"


@freeze_time("2026-06-12 14:00:00")  # День
def test_get_greeting_day():
    assert get_greeting() == "Добрый день"


@freeze_time("2026-06-12 20:15:00")  # Вечер
def test_get_greeting_evening():
    assert get_greeting() == "Добрый вечер"


@freeze_time("2026-06-12 03:45:00")  # Ночь
def test_get_greeting_night():
    assert get_greeting() == "Доброй ночи"


# Тесты для process_transactions
# Фикстура для создания DataFrame с транзакциями
@pytest.fixture
def sample_transactions_df():
    data = {
        'Дата операции': ['10.06.2026', '11.06.2026', '12.06.2026', '15.06.2026'],
        'Номер карты': ['4444********1111', '5555********2222', '4444********1111', '6666********3333'],
        'Сумма платежа': ['1500,55', '-250,10', '300,75', '9999,99'],
        'Категория': ['Супермаркеты', 'Рестораны', 'Транспорт', 'Развлечения'],
        'Описание': ['Покупка продуктов', 'Ужин в кафе', 'Билет на автобус', 'Билет в кино']
    }
    df = pd.DataFrame(data)
    # Приводим колонку с датой к datetime
    df['Дата операции'] = pd.to_datetime(df['Дата операции'], dayfirst=True)
    return df


def test_process_transactions_empty_df(caplog):
    """Тест на пустой DataFrame."""
    cards_info, top_transactions = process_transactions("12.06.2026", pd.DataFrame())
    assert cards_info == []
    assert top_transactions == []
    assert "Пустой DataFrame передан в обработку" in caplog.text


def test_process_transactions_valid(sample_transactions_df):
    """Тест на корректную обработку данных."""
    input_date = "12.06.2026"
    cards_info, top_transactions = process_transactions(input_date, sample_transactions_df)

    # Проверка агрегации по картам
    assert len(cards_info) == 2
    # Проверка суммы для карты 1111 (1500,55 + 300,75)
    card_1111 = next(item for item in cards_info if item["last_digits"] == "1111")
    assert card_1111["total_spent"] == 1801.3

    # Проверка топ-5 транзакций (в нашем случае их всего 4)
    assert len(top_transactions) == 3
    # Проверка, что транзакции отсортированы по абсолютному значению суммы
    amounts = [t["amount"] for t in top_transactions]
    assert amounts == sorted(amounts, key=abs, reverse=True)


# tests/test_views.py
def test_process_transactions_no_required_columns():
    """Тест на отсутствие данных для обработки при наличии нужных колонок."""
    # Создаем DataFrame с нужными колонками, но без строк данных
    df = pd.DataFrame(columns=['Дата операции', 'Номер карты', 'Сумма платежа'])

    cards_info, top_transactions = process_transactions("12.06.2026", df)
    assert cards_info == []
    assert top_transactions == []


# Тесты для load_user_settings
def test_load_user_settings_file_not_found(monkeypatch):
    """Тест на случай, когда файл не найден."""
    def mock_open_file_not_found(*args, **kwargs):
        if args[0] == 'data/user_settings.json':
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{args[0]}'")
        return builtins.open(*args, **kwargs)

    monkeypatch.setattr('builtins.open', mock_open_file_not_found)

    currencies, stocks = load_user_settings()

    assert currencies == []
    assert stocks == []


def test_load_user_settings_valid_file(tmp_path):
    """Тест на корректную загрузку данных из файла."""
    # Создаем временный файл с нужной структурой
    settings_data = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["SBER", "GAZP"]
    }

    file_path = tmp_path / "user_settings.json"
    with open(file_path, 'w') as f:
        json.dump(settings_data, f)

    # На время теста подменяем путь к файлу
    import builtins
    original_open = builtins.open

    def mock_open(*args, **kwargs):
        if args and args[0] == 'data/user_settings.json':
            return open(file_path, *args[1:], **kwargs)
        return original_open(*args, **kwargs)

    builtins.open = mock_open

    currencies, stocks = load_user_settings()

    builtins.open = original_open

    # Проверяем результат
    assert currencies == ["USD", "EUR"]
    assert stocks == ["SBER", "GAZP"]
