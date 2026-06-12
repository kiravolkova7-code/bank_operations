import pandas as pd
import pytest
import os
import requests
from unittest.mock import patch, MagicMock
from src.utils import load_transactions_from_xlsx, get_currency_rates, get_stock_prices


# Тесты для load_transactions_from_xlsx
def test_load_transactions_from_xlsx_success(tmp_path):
    """
    Тест на успешную загрузку транзакций из .xlsx файла.
    """
    data = {
        'Дата операции': ['10.06.2026', '11.06.2026'],
        'Сумма платежа': [1000, -500]
    }
    df_expected = pd.DataFrame(data)
    df_expected['Дата операции'] = pd.to_datetime(df_expected['Дата операции'], dayfirst=True)

    file_path = tmp_path / "test_operations.xlsx"
    df_expected.to_excel(file_path, index=False)

    df_result = load_transactions_from_xlsx(str(file_path))

    assert not df_result.empty
    pd.testing.assert_frame_equal(df_result, df_expected)


def test_load_transactions_from_xlsx_file_not_found(caplog):
    """
    Тест на обработку ошибки, когда файл не найден.
    """
    non_existent_path = "data/non_existent_file.xlsx"
    df_result = load_transactions_from_xlsx(non_existent_path)

    assert df_result.empty
    assert f"Файл {non_existent_path} не найден." in caplog.text


# Тесты для get_currency_rates
def test_get_currency_rates_success(requests_mock, monkeypatch):
    """
    Тест на успешный запрос курсов валют.
    """
    currencies = ['USD', 'EUR', 'RUB']
    monkeypatch.setenv('EXCHANGERATE_API_KEY', 'FAKE_API_KEY')

    mock_response = {
        "conversion_rates": {
            "USD": 92.5,
            "EUR": 101.2,
            "RUB": 1.0,
            "JPY": 0.65
        }
    }

    requests_mock.get(
        "https://v6.exchangerate-api.com/v6/FAKE_API_KEY/latest/RUB",
        json=mock_response,
        status_code=200
    )

    rates = get_currency_rates(currencies)

    # ИСПРАВЛЕНИЕ: Курс USD (92.5) больше 1, поэтому он НЕ должен инвертироваться.
    # Ожидание в предыдущем тесте было неверным.
    expected_rates = [
        {"currency": "USD", "rate": 92.5},
        {"currency": "EUR", "rate": 101.2},
        {"currency": "RUB", "rate": 1.0}
    ]

    assert rates == expected_rates


def test_get_currency_rates_network_error(requests_mock, monkeypatch):
    """
    Тест на обработку сетевой ошибки (например, нет интернета).
    """
    monkeypatch.setenv('EXCHANGERATE_API_KEY', 'FAKE_API_KEY')

    requests_mock.get(
        "https://v6.exchangerate-api.com/v6/FAKE_API_KEY/latest/RUB",
        exc=requests.exceptions.ConnectionError("Failed to connect")
    )

    rates = get_currency_rates(['USD'])

    assert rates == []


# Тесты для get_stock_prices
@pytest.fixture(autouse=True)
def mock_env_token():
    """Фикстура для очистки переменной окружения перед каждым тестом."""
    with patch.dict(os.environ, {}, clear=True):
        yield


@patch('src.utils.requests.get')
def test_successful_api_response(mock_get):
    """
    Тест успешного сценария: валидный токен, успешный ответ API,
    корректная обработка данных и возврат цен.
    """
    stocks = ['AAPL', 'MSFT']
    api_token = 'fake-token-123'
    os.environ['TWELVEDATA_API_TOKEN'] = api_token

    mock_response = MagicMock()
    mock_response.status_code = 200
    # Структура JSON-ответа согласно коду функции
    mock_data = {
        "AAPL": {"symbol": "AAPL", "close": 175.456},
        "MSFT": {"symbol": "MSFT", "close": "420.98"}
    }
    mock_response.json.return_value = mock_data
    mock_response.text = str(mock_data)
    mock_get.return_value = mock_response

    result = get_stock_prices(stocks)

    assert result == [
        {"stock": "AAPL", "price": 175.46},
        {"stock": "MSFT", "price": 420.98}
    ]
    mock_get.assert_called_once_with(
        'https://api.twelvedata.com/quote',
        params={'symbol': 'AAPL,MSFT', 'apikey': api_token}
    )


@patch('src.utils.requests.get')
def test_network_error(mock_get):
    """
    Тест обработки сетевой ошибки (например, нет интернета).
    """
    stocks = ['TSLA']
    os.environ['TWELVEDATA_API_TOKEN'] = 'token'

    mock_get.side_effect = requests.exceptions.RequestException("Connection timed out")

    result = get_stock_prices(stocks)

    assert result == []
    mock_get.assert_called()


@patch('src.utils.requests.get')
def test_invalid_json_response(mock_get):
    """
    Тест обработки ситуации, когда API возвращает невалидный JSON.
    """
    stocks = ['AMZN']
    os.environ['TWELVEDATA_API_TOKEN'] = 'token'

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.text = "{not a json}"
    mock_get.return_value = mock_response

    result = get_stock_prices(stocks)

    assert result == []
