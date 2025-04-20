import datetime
import pytz

# Форматы для преобразования строк в даты и обратно
DEFAULT_DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
USER_FRIENDLY_FORMAT: str = "%d.%m.%Y %H:%M"
LOG_FORMAT: str = "%Y-%m-%d %H:%M:%S.%f %Z"


def get_utc_now() -> datetime.datetime:
    """
    Получение текущего datetime в UTC

    Returns:
        datetime.datetime: Текущее время в UTC с timezone info
    """
    return datetime.datetime.now(pytz.UTC)


def convert_utc_to_user_timezone(
        dt: datetime.datetime,
        timezone_offset: int
) -> datetime.datetime:
    """
    Преобразование datetime с UTC в user timezone

    Args:
        dt: datetime объект в UTC (должен иметь tzinfo)
        timezone_offset: смещение в минутах от UTC (например, 180 для UTC+3)

    Returns:
        datetime.datetime: время с учетом смещения пользователя
    """
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    elif dt.tzinfo != pytz.UTC:
        dt = dt.astimezone(pytz.UTC)

    # Создаем timezone с указанным смещением
    offset: datetime.timedelta = datetime.timedelta(minutes=timezone_offset)
    user_timezone: datetime.timezone = datetime.timezone(offset)

    return dt.astimezone(user_timezone)


def convert_user_timezone_to_utc(
        dt: datetime.datetime,
        timezone_offset: int
) -> datetime.datetime:
    """
    Преобразование datetime с user timezone в UTC

    Args:
        dt: datetime объект в пользовательской timezone (может быть naive)
        timezone_offset: смещение в минутах от UTC

    Returns:
        datetime.datetime: время в UTC
    """
    offset: datetime.timedelta = datetime.timedelta(minutes=timezone_offset)
    user_timezone: datetime.timezone = datetime.timezone(offset)

    # Если datetime наивный (без timezone info)
    if dt.tzinfo is None:
        # Создаем datetime с пользовательским timezone
        dt = dt.replace(tzinfo=user_timezone)
    # Если datetime уже имеет timezone, но не совпадает с указанным смещением
    elif dt.utcoffset().total_seconds() != offset.total_seconds():
        # Считаем, что время уже в указанной timezone, просто меняем timezone info
        dt = dt.replace(tzinfo=user_timezone)

    return dt.astimezone(pytz.UTC)


def parse_string_in_user_timezone(
        date_string: str,
        timezone_offset: int,
        format: str = DEFAULT_DATETIME_FORMAT
) -> datetime.datetime:
    """
    Преобразование строкового представления с user timezone в datetime UTC

    Args:
        date_string: строка с датой/временем
        timezone_offset: смещение в минутах от UTC
        format: формат строки с датой (по умолчанию '%Y-%m-%d %H:%M:%S')

    Returns:
        datetime.datetime: время в UTC
    """
    naive_dt: datetime.datetime = datetime.datetime.strptime(date_string, format)
    offset: datetime.timedelta = datetime.timedelta(minutes=timezone_offset)
    user_timezone: datetime.timezone = datetime.timezone(offset)

    # Добавляем информацию о timezone
    local_dt: datetime.datetime = naive_dt.replace(tzinfo=user_timezone)

    return local_dt.astimezone(pytz.UTC)


def parse_utc_string_to_user_timezone(
        date_string: str,
        timezone_offset: int,
        format: str = DEFAULT_DATETIME_FORMAT
) -> datetime.datetime:
    """
    Преобразование строкового представления с UTC в datetime user timezone

    Args:
        date_string: строка с датой/временем в UTC
        timezone_offset: смещение в минутах от UTC
        format: формат строки с датой (по умолчанию '%Y-%m-%d %H:%M:%S')

    Returns:
        datetime.datetime: время в timezone пользователя
    """
    naive_dt: datetime.datetime = datetime.datetime.strptime(date_string, format)
    utc_dt: datetime.datetime = naive_dt.replace(tzinfo=pytz.UTC)

    offset: datetime.timedelta = datetime.timedelta(minutes=timezone_offset)
    user_timezone: datetime.timezone = datetime.timezone(offset)

    return utc_dt.astimezone(user_timezone)


def format_datetime_for_user(
        dt: datetime.datetime,
        timezone_offset: int,
        format: str = USER_FRIENDLY_FORMAT
) -> str:
    """
    Преобразование datetime в строковое представление timezone пользователя

    Args:
        dt: datetime объект (в любой timezone)
        timezone_offset: смещение в минутах от UTC
        format: формат вывода (по умолчанию '%d.%m.%Y %H:%M')

    Returns:
        str: отформатированная строка в timezone пользователя
    """
    dt_in_user_tz: datetime.datetime = convert_utc_to_user_timezone(dt, timezone_offset)
    return dt_in_user_tz.strftime(format)


def format_user_datetime_to_utc_string(
        dt: datetime.datetime,
        timezone_offset: int,
        format: str = DEFAULT_DATETIME_FORMAT
) -> str:
    """
    Преобразование datetime из user timezone в строковое представление в UTC

    Args:
        dt: datetime объект в timezone пользователя
        timezone_offset: смещение в минутах от UTC
        format: формат вывода (по умолчанию '%Y-%m-%d %H:%M:%S')

    Returns:
        str: отформатированная строка в UTC
    """
    utc_dt: datetime.datetime = convert_user_timezone_to_utc(dt, timezone_offset)
    return utc_dt.strftime(format)


def format_for_logging(dt: datetime.datetime) -> str:
    """
    Преобразование любого datetime в отображение для логов/админов

    Args:
        dt: datetime объект в любой timezone

    Returns:
        str: форматированная строка с timezone информацией для логов
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)

    return dt.strftime(LOG_FORMAT)


def offset_to_timezone_string(offset_minutes: int) -> str:
    """
    Преобразует смещение в минутах в строковое представление UTC±X

    Args:
        offset_minutes: смещение в минутах от UTC

    Returns:
        str: Строковое представление в формате UTC±X или UTC±X:YY
    """
    sign: str = '+' if offset_minutes >= 0 else '-'
    hours: int = abs(offset_minutes) // 60
    minutes: int = abs(offset_minutes) % 60

    if minutes == 0:
        return f"UTC{sign}{hours}"
    else:
        return f"UTC{sign}{hours}:{minutes:02d}"


def create_timezone_from_offset(offset_minutes: int) -> datetime.timezone:
    """
    Создает объект timezone из смещения в минутах

    Args:
        offset_minutes: смещение в минутах от UTC

    Returns:
        datetime.timezone: Объект timezone
    """
    offset: datetime.timedelta = datetime.timedelta(minutes=offset_minutes)
    return datetime.timezone(offset)


# Примеры использования:
if __name__ == "__main__":
    now_utc: datetime.datetime = get_utc_now()
    print(f"Текущее время UTC: {now_utc}")

    # Смещение для часового пояса Москвы (UTC+3 = 180 минут)
    user_timezone_offset: int = 180

    now_in_user_tz: datetime.datetime = convert_utc_to_user_timezone(now_utc, user_timezone_offset)
    print(f"Текущее время в часовом поясе UTC+{user_timezone_offset // 60}: {now_in_user_tz}")

    back_to_utc: datetime.datetime = convert_user_timezone_to_utc(now_in_user_tz, user_timezone_offset)
    print(f"Обратно в UTC: {back_to_utc}")

    date_string: str = "2023-05-15 18:30:00"
    parsed_utc: datetime.datetime = parse_string_in_user_timezone(date_string, user_timezone_offset)
    print(f"Строка '{date_string}' из часового пояса UTC+{user_timezone_offset // 60} в UTC: {parsed_utc}")

    user_friendly: str = format_datetime_for_user(now_utc, user_timezone_offset)
    print(f"Для отображения пользователю: {user_friendly}")

    log_format: str = format_for_logging(now_utc)
    print(f"Для логов: {log_format}")

    tz_string: str = offset_to_timezone_string(user_timezone_offset)
    print(f"Строковое представление: {tz_string}")
