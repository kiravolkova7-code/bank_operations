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
    Принимает на вход строку с датой и DataFrame с транзакциями.
    Возвращает список карт (с расходами) и топ-5 транзакций.
    """
    if not isinstance(transactions_df, pd.DataFrame) or transactions_df.empty:
        logging.warning("Пустой DataFrame передан в обработку. Возвращение пустых списков.")
        return [], []

    # Парсинг входной даты
    # Стало (явно указываем формат)
    input_date = pd.to_datetime(input_datetime_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')
    start_period = input_date.replace(day=1)

    # Фильтрация по периоду
    if pd.isnull(input_date):
        logging.error(f"Не удалось распарсить входную дату: {input_datetime_str}")
        df_period = pd.DataFrame()  # Создаем пустой DataFrame
    else:
        start_period = input_date.replace(day=1)
        mask = (transactions_df['Дата операции'] >= start_period) & \
               (transactions_df['Дата операции'] <= input_date)
        df_period = transactions_df.loc[mask]

    # Агрегация по картам (сумма расходов и кешбэк)
    cards_info = []
    required_cols = ['Номер карты', 'Сумма платежа']

    # Проверяем, что датафрейм не пуст и нужные колонки существуют
    if not df_period.empty and all(col in df_period.columns for col in required_cols):

        df_period['last_4_digits'] = df_period['Номер карты'].astype(str).str.replace(r'\D', '', regex=True).str[-4:]
        df_period['Сумма платежа'] = pd.to_numeric(
            df_period['Сумма платежа'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )

        # Группируем данные по последним 4 цифрам и суммируем расходы
        grouped = df_period.groupby('last_4_digits')['Сумма платежа'].sum().reset_index()

        for _, row in grouped.iterrows():
            # Получаем значение из текущей строки
            sum_value = row.get('Сумма платежа')

            # Проверяем, является ли значение числовым и не пустым (не NaN)
            if pd.notnull(sum_value):
                try:
                    sum_as_float = float(sum_value)
                    cards_info.append({
                        "last_digits": row['last_4_digits'],
                        "total_spent": round(sum_as_float, 2),
                        "cashback": round(abs(sum_as_float) / 100, 2)
                    })
                except (ValueError, TypeError):
                    logging.warning(f"Некорректное значение суммы: {sum_value}. Строка пропущена.")
            # Если значение пустое (NaN), мы его просто игнорируем

    # Топ-5 транзакций по сумме платежа
    top_transactions = []
    if not df_period.empty:
        top_5 = df_period.sort_values(by='Сумма платежа', key=abs, ascending=False).head(5)

        for _, row in top_5.iterrows():
            top_transactions.append({
                "date": row.get('Дата операции').strftime('%d.%m.%Y'),
                "amount": float(row.get('Сумма платежа', 0)),
                "category": row.get('Категория', ''),
                "description": row.get('Описание', '')
            })

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
