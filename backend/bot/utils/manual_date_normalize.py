from datetime import datetime, timedelta
import re
from typing import Union


def normalize_date_string(date_string) -> str:
    return date_string.lower().strip()


def parse_relative_date(date: str) -> Union[datetime, None]:
    """
    Пытается распознать относительную дату в строке и вернуть дату в формате ДД.ММ.ГГГГ.
    """
    date_string_normalized = normalize_date_string(date)
    words = date_string_normalized.split()
    today = datetime.now()

    relative_date_keywords = {
        "сегодня": timedelta(days=0),
        "завтра": timedelta(days=1),
        "послезавтра": timedelta(days=2)
    }

    time_units_keywords = {
        "недел": timedelta(weeks=1),  # "недел" чтобы покрыть "неделю" и "недели"
        "месяц": timedelta(days=30),  # Приближение, можно уточнить для разных месяцев
        "год": timedelta(days=365),  # Приближение, можно учитывать високосные годы
    }

    for i, word in enumerate(words):
        if word in relative_date_keywords:
            return today + relative_date_keywords[word]

    for i, word in enumerate(words):
        if word == "через" and i + 2 < len(words):  # Проверяем, есть ли число и единица времени после "через"
            try:
                number = int(words[i + 1])
                unit_word = words[i + 2]
                for unit_keyword, time_delta in time_units_keywords.items():
                    if unit_word.startswith(
                            unit_keyword):  # Проверяем начало слова, чтобы покрыть "недели", "месяца" и т.д.
                        return today + time_delta * number
            except ValueError:
                continue  # Если не число, игнорируем

    return None  # Если не распознано
