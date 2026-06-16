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
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
def analyze_spending_by_weekday(file_path='data/operations.xlsx', date_str=None) -> object:
    """
    Загружает транзакции из Excel-файла и рассчитывает средние траты по дням недели.
    Анализирует весь период данных внутри переданного файла.
    """
    try:
        df = pd.read_excel(file_path)

        # Проверка наличия ключевых столбцов
        required_cols = {'Дата операции', 'Сумма операции'}
        if not all(col in df.columns for col in required_cols):
            missing = ', '.join(required_cols - set(df.columns))
            raise ValueError(f"В файле отсутствуют необходимые столбцы: {missing}")

        # Приведение данных к нужному типу
        df['Дата операции'] = pd.to_datetime(df['Дата операции'], dayfirst=True, errors='coerce')
        df['Сумма операции'] = pd.to_numeric(
            df['Сумма операции'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )

        # --- ГЛАВНОЕ ИЗМЕНЕНИЕ ---
        # Теперь диапазон дат определяется ТОЛЬКО по данным внутри загруженного DataFrame
        start_date = df['Дата операции'].min()
        end_date = df['Дата операции'].max()

        # Если в файле вообще нет дат или они некорректны, возвращаем пустой результат
        if pd.isna(start_date) or pd.isna(end_date):
            logging.warning("Нет корректных дат в файле.")
            return pd.DataFrame({'День недели': [], 'Средняя трата': []})

        logging.info(f"Анализируются данные из файла за период с {start_date.date()} по {end_date.date()}")

        # Фильтрация данных за определенный период (весь период в данном случае)
        mask = (
                (df['Дата операции'] >= start_date) &
                (df['Дата операции'] <= end_date) &
                (df['Дата операции'].notna())
        )
        filtered_df = df.loc[mask]
        # -------------------

        if filtered_df.empty or filtered_df['Сумма операции'].isna().all():
            logging.warning("Нет данных о транзакциях за указанный период.")
            return pd.DataFrame({'День недели': [], 'Средняя трата': []})

        # Группировка по дню недели и расчет среднего
        report_df = (
            filtered_df.groupby(filtered_df['Дата операции'].dt.dayofweek)['Сумма операции']
            .mean()
            .round(2)
            .reset_index()
        )

        weekday_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        report_df['День недели'] = report_df['Дата операции'].map(lambda x: weekday_names[x])

        final_report = report_df.rename(columns={'Сумма операции': 'Средняя трата'})[
            ['День недели', 'Средняя трата']
        ]

        logging.info("Анализ завершен успешно.")
        return final_report

    except FileNotFoundError:
        logging.error(f"Файл '{file_path}' не найден.")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")

    return pd.DataFrame()
