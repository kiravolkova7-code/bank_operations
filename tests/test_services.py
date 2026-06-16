# tests/test_services.py

import json
import pandas as pd
import pytest
from src.services import analyze_cashback_categories, get_analysis_as_json


# --- Фикстура: Подготовка тестовых данных ---
@pytest.fixture
def sample_data():
    """
    Создает DataFrame с тестовыми транзакциями.
    Данные из вашего лога pytest.
    """
    data = {
        'Дата платежа': ['01.06.2025', '15.06.2025', '20.06.2025', '10.05.2025', '01.06.2025'],
        'Статус': ['OK', 'OK', 'FAILED', 'OK', 'OK'],
        'Валюта платежа': ['RUB', 'RUB', 'RUB', 'USD', 'RUB'],
        'Категория': ['Супермаркеты', 'Рестораны', 'Супермаркеты', 'Рестораны', 'Кино'],
        # Сумма из вашего лога: для Супермаркетов это -1000 и -600 (FAILED)
        'Сумма платежа': [-1000, -500, -600, -400, -150]
    }
    return pd.DataFrame(data)
# ---------------------------------------------------


# --- Тест 1: Проверка основной логики анализа ---
def test_analyze_cashback_categories(sample_data):
    """
    Проверяет, что функция корректно фильтрует данные и считает кешбэк.
    """
    # Анализируем июнь 2025 года
    result = analyze_cashback_categories(sample_data, 2025, 6)

    # --- ИСПРАВЛЕННЫЙ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ---
    # Супермаркеты: только строка с индексом 0 (статус OK), т.к. строка 2 имеет статус FAILED.
    # (1000) * 5% = 50.0
    # Рестораны: (500) * 5% = 25.0
    # Кино: (150) * 5% = 7.5
    expected = {
        "Супермаркеты": 50.0,
        "Рестораны": 25.0,
        "Кино": 7.5
    }

    assert result == expected, f"Ожидаемый результат {expected}, а получили {result}"


# --- Тест 3: Проверка работы с пустыми данными ---
def test_analyze_with_empty_data():
    """
    Проверяет, что функция корректно обрабатывает пустой DataFrame.
    """
    empty_df = pd.DataFrame()

    result = analyze_cashback_categories(empty_df, 2025, 6)

    assert result == {}, "Функция должна возвращать пустой словарь для пустого DataFrame"


# --- Тест 4: Проверка отсутствия данных за период ---
def test_no_transactions_in_period(sample_data):
    """
    Проверяет, что функция возвращает пустой результат,
    если нет транзакций за указанный месяц/год.
    """
    # В sample_data нет транзакций за июль 2025 года
    result = analyze_cashback_categories(sample_data, 2025, 7)

    assert result == {}, "Функция должна возвращать пустой словарь, если данных за период нет"