import os
from dotenv import load_dotenv
import logging
import requests
import pandas as pd

load_dotenv()


def load_transactions_from_xlsx(file_path='data/operations.xlsx'):
    """
    Загружает данные о транзакциях из .xlsx файла.
    """
    try:
        df = pd.read_excel(file_path,)

        # Если столбец 'Дата операции' существует, преобразуем его вручную
        if 'Дата операции' in df.columns:
            df['Дата операции'] = pd.to_datetime(df['Дата операции'], dayfirst=True, errors='coerce')
        logging.info(f"Данные успешно загружены из {file_path}.")
        return df
    except FileNotFoundError:
        logging.error(f"Файл {file_path} не найден.")
    except Exception as e:
        logging.error(f"Произошла ошибка при чтении файла {file_path}: {e}")

    return pd.DataFrame()

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С API ---


def get_currency_rates(currencies):
    """
    Запрашивает текущие курсы валют к RUB через ExchangeRate-API.
    """
    api_key = os.getenv('EXCHANGERATE_API_KEY')
    rates = []

    if not api_key:
        logging.warning("API-ключ EXCHANGERATE_API_KEY не найден в .env файле.")
        return rates

    try:
        # Параметр 'base' говорит сервису, что мы хотим курсы К РУБЛЮ.
        response = requests.get(
            f"https://v6.exchangerate-api.com/v6/{api_key}/latest/RUB",
        )
        response.raise_for_status()

        data = response.json()
        logging.debug(f"Ответ от ExchangeRate-API: {data}")

        all_rates = data.get('conversion_rates', {})

        for currency in currencies:
            rate = all_rates.get(currency)
            if rate is not None:
                try:
                    rate_float = float(rate)

                    # Инвертируем курс, если он меньше 1 (и это не сам RUB)
                    if currency != 'RUB' and rate_float < 1.0:
                        calculated_rate = 1 / rate_float
                    else:
                        calculated_rate = rate_float

                    rounded_rate = round(calculated_rate, 4)
                    rates.append({"currency": currency, "rate": rounded_rate})
                except (TypeError, ValueError) as e:
                    logging.error(f"Ошибка преобразования курса {currency}: {e}")
            else:
                logging.warning(f"Курс для {currency} не найден в ответе.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка сети при запросе курсов: {e}")

    return rates


def get_stock_prices(stocks):
    """
    Запрашивает текущие цены акций через API Twelve Data,
    используя токен из переменной окружения.
    """
    api_token = os.getenv('TWELVEDATA_API_TOKEN')
    prices = []
    if not api_token:
        logging.warning("API-токен TWELVEDATA_API_TOKEN не найден в .env файле.")
        return prices

    symbols_str = ','.join(stocks)
    logging.debug(f"Запрос цен на акции для тикеров: {symbols_str}")

    params = {
        'symbol': symbols_str,
        'apikey': api_token
    }

    try:
        response = requests.get('https://api.twelvedata.com/quote', params=params)
        logging.debug(f"Ответ от сервера акций (код): {response.status_code}")
        logging.debug(f"Ответ от сервера акций (текст): {response.text}")

        data = response.json()
        logging.debug(f"Полный JSON-ответ по акциям: {data}")

        # Унифицируем ответ в список 'results'
        if isinstance(data, list):
            if data:
                results = data[0]
            else:
                results = {}
        elif isinstance(data, dict):
            results = data
        else:
            logging.warning(f"Неожиданный формат ответа от API: {type(data)}")
            results = {}
        for ticker in stocks:
            # Пытаемся достать вложенный словарь с данными по конкретному тикеру
            stock_data = results.get(ticker)

            if stock_data and isinstance(stock_data, dict):
                # Теперь нужные нам данные находятся в stock_data
                price = stock_data.get('close')
                stock_symbol = stock_data.get('symbol')

                if price is not None and stock_symbol is not None:
                    try:
                        price_float = float(price)
                        prices.append({"stock": stock_symbol, "price": round(price_float, 2)})
                    except (ValueError, TypeError):
                        logging.warning(f"Не удалось преобразовать цену '{price}' для тикера {ticker} в число.")

        logging.debug(f"Успешно получены цены: {prices}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка сети при запросе цен на акции: {e}")
    except Exception as e:
        logging.error(f"Критическая ошибка при обработке ответа от API акций: {type(e).__name__} - {e}")

    return prices
