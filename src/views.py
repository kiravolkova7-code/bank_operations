import datetime
import json
import pandas as pd
import logging


def get_greeting():
    """Возвращает приветствие в зависимости от текущего времени."""
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def process_transactions(input_datetime_str, transactions_df):
    """
    Обрабатывает транзакции за период с начала месяца по заданную дату.
    Возвращает список карт (с расходами) и ТОП-5 транзакций по расходам.
    """
    if not isinstance(transactions_df, pd.DataFrame) or transactions_df.empty:
        logging.warning("Пустой DataFrame передан в обработку. Возвращение пустых списков.")
        return [], []

    # Парсинг входной даты
    input_date = pd.to_datetime(input_datetime_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')

    top_transactions = []  # Инициализируем пустой список на случай ошибок

    try:
        if pd.isnull(input_date):
            raise ValueError(f"Не удалось распарсить входную дату: {input_datetime_str}")

        start_period = input_date.replace(day=1)

        # --- НОВАЯ ЛОГИКА ДЛЯ КРИТЕРИЯ 3 ---
        # Фильтруем данные за нужный период
        mask_period = (
                (transactions_df['Дата операции'] >= start_period) &
                (transactions_df['Дата операции'] <= input_date)
        )
        df_period = transactions_df.loc[mask_period]

        # Проверяем наличие необходимых столбцов перед работой
        required_cols_top = ['Дата операции', 'Сумма платежа', 'Категория', 'Описание']
        if all(col in df_period.columns for col in required_cols_top):

            # Конвертируем сумму к числу
            df_period['Сумма платежа'] = pd.to_numeric(
                df_period['Сумма платежа'].astype(str).str.replace(',', '.'),
                errors='coerce'
            )

            # Оставляем только расходы (сумма < 0)
            df_expenses = df_period[df_period['Сумма платежа'] < 0].copy()

            # Сортируем по убыванию расхода (берем модуль суммы)
            df_sorted = df_expenses.sort_values(by='Сумма платежа', key=abs, ascending=False)

            # Берем ровно 5 транзакций
            top_5 = df_sorted.head(5)

            # Формируем итоговый список словарей
            for _, row in top_5.iterrows():
                top_transactions.append({
                    "date": row.get('Дата операции').strftime('%d.%m.%Y'),  # Формат dd.mm.yyyy
                    "amount": float(row.get('Сумма платежа', 0)),
                    "category": row.get('Категория', ''),
                    "description": row.get('Описание', '')
                })
        else:
            logging.error(f"В данных для топ-транзакций отсутствуют необходимые колонки: {required_cols_top}")

    except Exception as e:
        logging.error(f"Ошибка при формировании топ-транзакций: {e}")

    # Остальная логика для агрегации по картам остается без изменений
    cards_info = []
    required_cols_cards = ['Номер карты', 'Сумма платежа']

    if not df_period.empty and all(col in df_period.columns for col in required_cols_cards):
        df_period['last_4_digits'] = df_period['Номер карты'].astype(str).str.replace(r'\D', '', regex=True).str[-4:]
        df_period['Сумма платежа'] = pd.to_numeric(
            df_period['Сумма платежа'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )

        grouped = df_period.groupby('last_4_digits')['Сумма платежа'].sum().reset_index()

        for _, row in grouped.iterrows():
            sum_value = row.get('Сумма платежа')
            if pd.notnull(sum_value):
                try:
                    sum_as_float = float(sum_value)
                    cards_info.append({
                        "last_digits": row['last_4_digits'],
                        "total_spent": round(abs(sum_as_float), 2),
                        "cashback": round(abs(sum_as_float) / 100, 2)  # Расчет кешбэка 1%
                    })
                except (ValueError, TypeError):
                    logging.warning(f"Некорректное значение суммы: {sum_value}. Строка пропущена.")

    return cards_info, top_transactions


def load_user_settings():
    """Загружает пользовательские настройки валют и акций."""
    try:
        with open('data/user_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get('user_currencies', []), settings.get('user_stocks', [])
    except FileNotFoundError:
        logging.error("Файл user_settings.json не найден.")
        return [], []
