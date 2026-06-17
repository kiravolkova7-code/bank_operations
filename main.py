import logging
import json
import pandas as pd
import json
import logging
import argparse
from datetime import datetime
from src.views import get_greeting, process_transactions, load_user_settings
from src.utils import load_transactions_from_xlsx, get_currency_rates, get_stock_prices
from src.services import get_analysis_as_json
from src.reports import analyze_spending_by_weekday

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    filemode='w',
    encoding='UTF-8',
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def main():
    """
    Главная функция. Управляет выполнением всех блоков на основе входных аргументов.
    """
    logging.info("--- Запуск приложения ---")

    # 1. Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Финансовая аналитика")
    parser.add_argument('--datetime', type=str, required=True,
                        help="Дата и время для блока 'Главная' в формате YYYY-MM-DD HH:MM:SS")
    parser.add_argument('--run-cashback', action='store_true',
                        help="Запустить блок 'Выгодные категории кэшбека'")
    parser.add_argument('--year', type=int,
                        help="Год для анализа кэшбека")
    parser.add_argument('--month', type=int,
                        help="Месяц для анализа кэшбека")
    parser.add_argument('--run-weekdays', action='store_true',
                        help="Запустить блок 'Траты по дням недели'")
    parser.add_argument('--report-date', type=str,
                        help="Опорная дата для отчета по дням недели (формат DD.MM.YYYY). Если не указана, используется текущая дата.")

    args = parser.parse_args()

    # Единая точка загрузки данных
    file_path = 'data/operations.xlsx'
    try:
        transactions_data = load_transactions_from_xlsx(file_path)
        if transactions_data.empty:
            raise ValueError("Файл с транзакциями пуст.")
        logging.info("Данные из файла успешно загружены.")
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных из файла: {e}")
        print(json.dumps({"error": "Не удалось загрузить данные для анализа."}, ensure_ascii=False, indent=2))
        return

    final_result = {}

    # 2. Блок "Главная"
    if args.datetime:
        logging.info(f"--- Блок: Главная страница ---")
        main_result = {}
        try:
            # Валидация формата даты для блока "Главная"
            datetime.strptime(args.datetime, '%Y-%m-%d %H:%M:%S')

            greeting = get_greeting()
            main_result["greeting"] = greeting

            cards_info, top_transactions = process_transactions(args.datetime, transactions_data)
            main_result.update({
                "cards": cards_info,
                "top_transactions": top_transactions
            })
            logging.info("Транзакции и информация о картах обработаны.")

            user_currencies, user_stocks = load_user_settings()
            logging.info(f"Пользовательские настройки: валюты={user_currencies}, акции={user_stocks}")

            currency_rates = get_currency_rates(user_currencies) if user_currencies else []
            stock_prices = get_stock_prices(user_stocks) if user_stocks else []

            main_result.update({
                "currency_rates": currency_rates,
                "stock_prices": stock_prices
            })

            final_result["main_page"] = main_result

        except ValueError as ve:
            logging.error(f"Ошибка валидации даты/времени: {ve}")
        except Exception as e:
            logging.error(f"Ошибка в блоке 'Главная': {e}")

    # 3. Блок "Выгодные категории кэшбека"
    if args.run_cashback and args.year and args.month:
        logging.info(f"--- Блок: Выгодные категории кэшбека (год: {args.year}, месяц: {args.month}) ---")
        cashback_analysis = {}
        try:
            json_result = get_analysis_as_json(transactions_data, args.year, args.month)
            cashback_analysis = {
                "title": "Выгодные категории повышенного кешбэка",
                "period": f"{args.month:02d}.{args.year}",
                "result": json_result
            }
            logging.info("Анализ кэшбека завершен.")
            final_result["cashback_analysis"] = cashback_analysis
        except Exception as e:
            logging.error(f"Ошибка при анализе кэшбека: {e}")

    # 4. Блок "Траты по дням недели"
    if args.run_weekdays:
        logging.info("--- Блок: Траты по дням недели ---")
        spending_report = {}
        try:
            # Определяем опорную дату
            if args.report_date:
                # Валидация формата даты для отчета (российский формат)
                datetime.strptime(args.report_date, '%d.%m.%Y')
                report_date = args.report_date
            else:
                report_date = datetime.now().strftime('%d.%m.%Y')
                logging.info(f"Опорная дата не указана, используется текущая: {report_date}")

            spending_report_data = analyze_spending_by_weekday(transactions_data, report_date)

            # Проверяем, что данные не пустые, и преобразуем DataFrame в список словарей
            if not spending_report_data.empty:
                # Метод .to_dict('records') идеально подходит для JSON
                data_for_json = spending_report_data.to_dict('records')
            else:
                data_for_json = []

            spending_report = {
                "title": "Отчет о средних тратах по дням недели",
                "reference_date": report_date,
                "data": data_for_json  # <-- Теперь здесь список словарей
            }
            logging.info("Отчет по тратам по дням недели сформирован.")
            final_result["spending_by_weekday"] = spending_report
        except ValueError as ve:
            logging.error(f"Ошибка валидации опорной даты: {ve}")
        except Exception as e:
            logging.error(f"Ошибка при формировании отчета по дням недели: {e}")

    # Вывод финального результата в формате JSON
    if final_result:
        print(json.dumps(final_result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "Ни один из блоков анализа не был выполнен."}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()