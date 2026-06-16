import pandas as pd
import pytest
from src.services import analyze_cashback_categories


@pytest.fixture
def sample_data():
    """
    Создает DataFrame с тестовыми транзакциями.
    """
    data = {
        'Дата платежа': ['01.06.2025', '15.06.2025', '20.06.2025', '10.05.2025', '01.06.2025'],
        'Статус': ['OK', 'OK', 'FAILED', 'OK', 'OK'],
        'Валюта платежа': ['RUB', 'RUB', 'RUB', 'USD', 'RUB'],
        'Категория': ['Супермаркеты', 'Рестораны', 'Супермаркеты', 'Рестораны', 'Кино'],
        'Сумма платежа': [-1000, -500, -600, -400, -150]
    }
    return pd.DataFrame(data)


def test_analyze_cashback_categories(sample_data):
    """
    Проверяет, что функция корректно фильтрует данные и считает кешбэк.
    """
    result = analyze_cashback_categories(sample_data, 2025, 6)
    expected = {
        "Супермаркеты": 50.0,
        "Рестораны": 25.0,
        "Кино": 7.5
    }

    assert result == expected, f"Ожидаемый результат {expected}, а получили {result}"


def test_analyze_with_empty_data():
    """
    Проверяет, что функция корректно обрабатывает пустой DataFrame.
    """
    empty_df = pd.DataFrame()

    result = analyze_cashback_categories(empty_df, 2025, 6)

    assert result == {}, "Функция должна возвращать пустой словарь для пустого DataFrame"


def test_no_transactions_in_period(sample_data):
    """
    Проверяет, что функция возвращает пустой результат,
    если нет транзакций за указанный месяц/год.
    """
    result = analyze_cashback_categories(sample_data, 2025, 7)

    assert result == {}, "Функция должна возвращать пустой словарь, если данных за период нет"
