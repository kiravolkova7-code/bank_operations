import json
import logging
import pandas as pd

logger = logging.getLogger('cashback_analyzer')

# Константы ставок кешбэка
HIGH_CASHBACK_RATE = 0.05
TARGET_CURRENCY = 'RUB'


def analyze_cashback_categories(data_df, year, month):
    """
    Анализирует данные о транзакциях из DataFrame за указанный месяц и год.
    """
    logger.info(f"Начало анализа кешбэка за {month:02d}.{year}")

    # Проверяем, что DataFrame не пустой
    if data_df.empty:
        logger.info("Данные для анализа отсутствуют.")
        return {}

    # 1. Фильтрация по статусу и валюте
    filtered_df = data_df[
        (data_df['Статус'] == 'OK')
        and (data_df['Валюта платежа'] == TARGET_CURRENCY)
    ]

    # 2. Фильтрация по дате (используем 'Дата платежа')
    filtered_df = filtered_df[pd.to_datetime(filtered_df['Дата платежа'],
                                             dayfirst=True, errors='coerce').dt.year == year]
    filtered_df = filtered_df[pd.to_datetime(filtered_df['Дата платежа'],
                                             dayfirst=True, errors='coerce').dt.month == month]

    if filtered_df.empty:
        logger.info("Нет подходящих транзакций за указанный период.")
        return {}

    # 3. Группировка по категориям и суммирование абсолютных значений 'Сумма платежа'
    # abs() используется, так как расходы могут быть отрицательными
    category_sums = (
        filtered_df
        .groupby('Категория')['Сумма платежа']
        .sum()
        .apply(abs)
        .to_dict()
    )

    # 4. Расчет итогового кешбэка по категориям
    analysis_result = {
        category: round(total_sum * HIGH_CASHBACK_RATE, 2)
        for category, total_sum in category_sums.items()
    }

    logger.info(f"Анализ завершен. Найдено {len(analysis_result)} категорий.")
    return analysis_result


def get_analysis_as_json(data_df, year, month):
    """
    Возвращает результат анализа в формате JSON-строки.
    Категории в JSON сортируются по сумме кешбэка в порядке убывания.
    """
    analysis_dict = analyze_cashback_categories(data_df, year, month)

    # Проверяем, что словарь не пустой, чтобы не сортировать пустые данные
    if analysis_dict:
        # 1. Сортируем элементы словаря по значению (сумме кешбэка) по убыванию
        sorted_items = sorted(analysis_dict.items(), key=lambda item: item[1], reverse=True)

        # 2. Создаем новый словарь из отсортированного списка кортежей
        sorted_analysis_dict = dict(sorted_items)
    else:
        # Если данных нет, просто используем пустой словарь
        sorted_analysis_dict = analysis_dict

    # Преобразуем отсортированный словарь в JSON-строку
    return json.dumps(sorted_analysis_dict, ensure_ascii=False, indent=2)
