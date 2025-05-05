import datetime
from typing import Union


def normalize_date_string(date_string) -> str:
    return date_string.lower().strip()


# дата вручную без Y_GPT
def parse_relative_date(date: str) -> Union[datetime, None]:
    """
    Пытается распознать относительную дату в строке и вернуть дату в формате ДД.ММ.ГГГГ.
    """
    date_string_normalized = normalize_date_string(date)
    words = date_string_normalized.split()
    today = datetime.datetime.now()

    relative_date_keywords = {
        "сегодня": datetime.timedelta(days=0),
        "завтра": datetime.timedelta(days=1),
        "послезавтра": datetime.timedelta(days=2)
    }

    time_units_keywords = {
        "недел": datetime.timedelta(weeks=1),  # "недел" чтобы покрыть "неделю" и "недели"
        "месяц": datetime.timedelta(days=30),  # Приближение, можно уточнить для разных месяцев
        "год": datetime.timedelta(days=365),  # Приближение, можно учитывать високосные годы
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


def get_correct_time(text: str):
    # TODO yandex gpt
    time = datetime.time(*map(int, text.split(":")), second=0)  # сейчас только так
    return time


def get_russian_date(datetime_object: datetime):
    russian_months_genitive = [
        None,  # Месяцы нумеруются с 1, так что 0-й индекс не используем
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]

    # Получаем компоненты даты и времени из объекта
    day = datetime_object.day
    month_name = russian_months_genitive[datetime_object.month]
    hour = datetime_object.hour
    minute = datetime_object.minute

    formatted_time_str = f"{day} {month_name} {hour:02d}:{minute:02d}"
    return formatted_time_str
