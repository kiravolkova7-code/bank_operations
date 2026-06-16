import logging
import json
import pandas as pd
from src.views import get_greeting, process_transactions, load_user_settings
from src.utils import load_transactions_from_xlsx, get_currency_rates, get_stock_prices
from src.services import get_analysis_as_json
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    filemode='w',
    encoding='UTF-8',
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def main(input_datetime_str):
    """
    Главная функция. Объединяет все элементы в единое целое.
    """

    '''
    # Начало страницы "Главная"
    logging.info(f"Запуск главной функции для даты: {input_datetime_str}")

    # 0. Приветствие
    greeting = get_greeting()

    # 1. Загрузка данных из файла
    transactions_dataframe = load_transactions_from_xlsx('data/operations.xlsx') # Можно передать другой путь, если нужно

    # 2. Проверка, что данные загрузились, и их обработка
    cards_info, top_transactions = process_transactions(
        input_datetime_str,
        transactions_dataframe
    )

    # 3. Пользовательские настройки
    user_currencies, user_stocks = load_user_settings()
    logging.info(f"Загруженные настройки: валюты={user_currencies}, акции={user_stocks}")

    # 4. Курсы валют и цены на акции (если есть что запрашивать)
    currency_rates = get_currency_rates(user_currencies) if user_currencies else []

    # Цены на акции запрашиваются только при наличии токена и списка акций
    stock_prices = get_stock_prices(user_stocks) if user_stocks else ['bebebe']

    # Сборка итогового JSON-ответа
    result = {
        "greeting": greeting,
        "cards": cards_info,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices
    }

    logging.info("Формирование JSON-ответа завершено.")

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Конец страницы "Главная"
    '''

    # Начало Выгодные категории кэшбека
file_path = 'data/operations.xlsx'
transactions_data = load_transactions_from_xlsx(file_path)

if not transactions_data.empty:
    year_to_analyze = 2021
    month_to_analyze = 4

    json_result = get_analysis_as_json(transactions_data, year_to_analyze, month_to_analyze)

    print("Выгодные категории повышенного кешбэка")
    print(f"Результат анализа за {month_to_analyze:02d}.{year_to_analyze}:")
    print(json_result)
else:
    print("Не удалось загрузить данные для анализа.")

    # Конец Выгодные категории кэшбека

# Пример вызова функции (для тестирования)
if __name__ == "__main__":
    main("31.12.2021 16:44:00")
