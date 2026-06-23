import json
import pandas as pd
import logging
from datetime import datetime


def save_report(filename=None):
    """
    Декоратор для сохранения результата функции в JSON-файл.
    Если имя файла не передано, генерируется автоматически.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            try:
                if filename is None:
                    file_path = f"data/{func.__name__}.json"
                else:
                    file_path = filename

                from os import makedirs
                makedirs("data", exist_ok=True)

                data_to_save = {
                    "report_date": datetime.now().isoformat(),
                    "data": result.reset_index().to_dict(orient="records")
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=4)

                logging.info(f"Отчет успешно сохранен в файл: {file_path}")
            except Exception as e:
                logging.error(f"Ошибка при сохранении отчета: {e}")

            return result

        return wrapper

    return decorator


@save_report()
def analyze_spending_by_weekday(transactions_df, report_date=None):
    """
    Анализирует средние траты по дням недели за последние три месяца от указанной даты.
    Автоматически определяет имена столбцов 'дата' (например, 'Дата операции') и 'сумма' (например, 'Сумма операции').
    """
    # Логика для поддержки старого вызова (если передать путь к файлу)
    if isinstance(transactions_df, str):
        from src.utils import load_transactions_from_xlsx
        df = load_transactions_from_xlsx(transactions_df)
        if df.empty:
            return pd.DataFrame()
    else:
        df = transactions_df.copy()

    try:
        # --- Ищем столбец с датой ---
        date_col = None
        for col in df.columns:
            if 'дата' in col.lower():
                date_col = col
                break

        # --- Ищем столбец с суммой ---
        amount_col = None
        for col in df.columns:
            if 'сумм' in col.lower():  # Ищем по корню слова, чтобы найти и 'Сумма', и 'Сумма операции'
                amount_col = col
                break

        # Проверяем, что нашли нужные столбцы
        if not date_col or not amount_col:
            raise ValueError(f"Не найдены необходимые столбцы. Требуются: дата и сумма. Найдены: {df.columns}")

        # Устанавливаем опорную дату
        end_date = datetime.now() if report_date is None else datetime.strptime(report_date, '%d.%m.%Y')
        start_date = end_date - pd.DateOffset(months=3)

        # Фильтрация данных за период
        filtered_df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]

        if filtered_df.empty:
            logging.warning("Нет данных для анализа за выбранный период.")
            return pd.DataFrame()

        # Группировка и расчет среднего значения
        result = (
            filtered_df.groupby(filtered_df[date_col].dt.day_name())[amount_col]
            .mean()
            .round(2)
            .reset_index()
        )

        # Переименовываем столбцы для красивого вывода
        result.rename(columns={date_col: 'weekday', amount_col: 'avg_amount'}, inplace=True)

        logging.info(f"Анализ трат по дням недели завершен. Период: {start_date.date()} - {end_date.date()}")
        return result

    except Exception as e:
        logging.error(f"Произошла ошибка при анализе трат по дням недели: {e}")
        return pd.DataFrame()