import pandas as pd
from src.reports import analyze_spending_by_weekday


def test_analyze_success(mocker):
    """Тест успешного анализа при наличии корректных данных."""
    data = {
        'Дата операции': ['01.06.2026', '02.06.2026', '03.06.2026', '04.06.2026'],
        'Сумма операции': [100, 200, 300, 400]
    }
    df = pd.DataFrame(data)
    mocker.patch('pandas.read_excel', return_value=df)
    mocker.patch('os.makedirs')  # Избегаем создания папок

    result = analyze_spending_by_weekday(file_path='data/operations.xlsx')

    expected_data = {
        'День недели': ['Пн', 'Вт', 'Ср', 'Чт'],
        'Средняя трата': [100.0, 200.0, 300.0, 400.0]
    }
    expected_df = pd.DataFrame(expected_data)

    pd.testing.assert_frame_equal(result, expected_df)


def test_analyze_missing_columns(mocker):
    """Тест на ошибку при отсутствии необходимых столбцов."""
    df = pd.DataFrame({'Дата': ['01.06.2026'], 'Сумма': [100]})
    mocker.patch('pandas.read_excel', return_value=df)

    result = analyze_spending_by_weekday(file_path='data/operations.xlsx')

    assert result.empty is True


def test_analyze_file_not_found(mocker):
    """Тест на обработку ошибки FileNotFoundError."""
    mocker.patch('pandas.read_excel', side_effect=FileNotFoundError("Файл не найден"))

    result = analyze_spending_by_weekday(file_path='data/missing.xlsx')

    assert result.empty is True
