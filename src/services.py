import json
import logging
import pandas as pd

logger = logging.getLogger('cashback_analyzer')

# Константы ставок кешбэка и игнорируемые категории
HIGH_CASHBACK_RATE = 0.05
TARGET_CURRENCY = 'RUB'
IGNORED_CATEGORIES = {'Переводы', 'Наличные'} # Категории, которые мы не учитываем в топе

def analyze_cashback_categories(data_df, year, month):
    """
    Анализирует данные о транзакциях из DataFrame за указанный месяц и год.
    Реализует логику: Топ-7 категорий + категория 'Остальное'.
    """
    logger.info(f"Начало анализа кешбэка за {month:02d}.{year}")

    if data_df.empty:
        logger.info("Данные для анализа отсутствуют.")
        return {}

    # 1. Базовая фильтрация по статусу, валюте и дате
    filtered_df = data_df[
        (data_df['Статус'] == 'OK') &
        (data_df['Валюта платежа'] == TARGET_CURRENCY)
    ]

    filtered_df = filtered_df[
        (pd.to_datetime(filtered_df['Дата платежа'], dayfirst=True, errors='coerce').dt.year == year) &
        (pd.to_datetime(filtered_df['Дата платежа'], dayfirst=True, errors='coerce').dt.month == month)
    ]

    if filtered_df.empty:
        logger.info("Нет подходящих транзакций за указанный период.")
        return {}

    # 2. Группировка по категориям и суммирование расходов (берем модуль суммы)
    category_sums = (
        filtered_df
        .groupby('Категория')['Сумма платежа']
        .apply(lambda x: abs(x.sum())) # Суммируем модули всех значений в группе
        .to_dict()
    )

    # 3. Логика "Топ-7 + Остальное"
    analysis_result = {}
    total_rest_amount = 0.0

    # Сортируем все категории по сумме трат
    sorted_cats = sorted(category_sums.items(), key=lambda item: item[1], reverse=True)

    # Добавляем в результат топ-7 категорий (пропуская переводы/наличные)
    added_count = 0
    for cat_name, amount in sorted_cats:
        if added_count >= 7:
            break
        if cat_name in IGNORED_CATEGORIES:
            continue
        analysis_result[cat_name] = round(amount * HIGH_CASHBACK_RATE, 2)
        added_count += 1

    # Агрегируем все остальные траты (включая переводы/наличные и то, что осталось после топ-7)
    rest_items = {
        k: v for k, v in category_sums.items() if k not in analysis_result
    }
    if rest_items:
        total_rest_amount = sum(rest_items.values())
        analysis_result["Остальное"] = round(total_rest_amount * HIGH_CASHBACK_RATE, 2)

    # Если в топ-7 попали не все возможные категории (например, всего было 5), но есть "Остальное",
    # или если "Остальное" сформировано из переводов, оно уже добавлено.

    logger.info(f"Анализ завершен. Найдено {len(analysis_result)} категорий (включая 'Остальное').")
    return analysis_result

def get_analysis_as_json(data_df, year, month):
    """
    Возвращает результат анализа в формате JSON-строки.
    Категории сортируются по сумме кешбэка.
    """
    analysis_dict = analyze_cashback_categories(data_df, year, month)

    sorted_analysis_dict = {}

    # Явная проверка на то, что анализ прошел успешно и вернул непустой словарь
    if analysis_dict and isinstance(analysis_dict, dict) and len(analysis_dict) > 0:
        # 1. Сортируем элементы словаря по значению (сумме кешбэка) по убыванию
        sorted_items = sorted(analysis_dict.items(), key=lambda item: item[1], reverse=True)
        # 2. Создаем новый словарь из отсортированного списка кортежей
        sorted_analysis_dict = dict(sorted_items)

    # Преобразуем итоговый словарь в JSON-строку.
    # Если данных нет, вернется "{}"
    return json.dumps(sorted_analysis_dict, ensure_ascii=False, indent=2)
