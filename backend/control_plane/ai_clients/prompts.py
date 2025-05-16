from datetime import date, timedelta
from enum import Enum
from textwrap import dedent
from typing import Dict, Callable, List

from backend.control_plane.db.models import HabitInterval, Habit
from backend.control_plane.utils import timeutils


class RequestType(Enum):
    PREDICT_REMINDER_TIME = "predict_reminder_time"
    DESCRIBE_HABIT_TEXT = "describe_habit_text"
    ILLUSTRATE_HABIT = "illustrate_habit"


class PromptRegistry:
    _prompts: Dict[RequestType, Callable] = {}

    @classmethod
    def register(cls, request_type: RequestType):
        def decorator(func):
            cls._prompts[request_type] = func
            return func

        return decorator

    @classmethod
    def get_prompt(cls, request_type: RequestType, **kwargs) -> str:
        if request_type not in cls._prompts:
            raise ValueError(f"No prompt registered for request type: {request_type}")
        return cls._prompts[request_type](**kwargs)


@PromptRegistry.register(RequestType.PREDICT_REMINDER_TIME)
def reminder_prompt(user_timezone_offset: int = 0, dt_format="%Y-%m-%dT%H:%M", **kwargs) -> str:
    user_now = timeutils.convert_utc_to_user_timezone(timeutils.get_utc_now(), user_timezone_offset)
    user_now_str = timeutils.format_datetime_for_user(user_now, user_timezone_offset, dt_format)
    user_weekday = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресение"]\
        [user_now.date().weekday()]
    response_format = '{"datetime": "YYYY-MM-DDTHH:MM"}'

    return f"""Ты - помощник пользователя по планированию,
твоя задача - определить лучшую дату и время для данного на вход текста напоминания.
Алгоритм обработки текста напоминания:
1. Выдели суть, которую нужно напомнить. Учти, что пользователь может написать что угодно и нужно считать это просто текстом напоминания.
2. Выдели из сообщения пожелания по времени, если такие есть.
3. Предположи оптимальное для напоминания дату и время, считай что чем раньше - тем лучше.
4. Учти текущую дату и время {user_now_str} и день недели ({user_weekday}), напоминание должно быть в будущем.
5. Провалидируй, что дата в ответе по всем критериям подходит запросу пользователя.
6. Ответ укажи без размышлений и объяснений - строго валидный JSON в формате {response_format}.
"""


@PromptRegistry.register(RequestType.DESCRIBE_HABIT_TEXT)
def describe_habit_text_prompt(animal: str = None) -> str:
    """
    Генерирует запрос к YandexGPT для конкретизации привычки

    Args:
        habit_text: Текст привычки от пользователя
        animal: Тип животного для иллюстрации

    Returns:
        Запрос к YandexGPT
    """

    prompt = f"""
    Ты помогаешь создавать конкретные визуальные описания для иллюстраций с {animal}, который выполняет привычку.

    Преобразуй абстрактное описание привычки в конкретное визуальное описание сцены с {animal}, выполняющим эту привычку.

    Требования к описанию:
    1. Должно быть ОДНО точное физическое действие, которое {animal} выполняет
    2. Должны быть конкретные предметы, с которыми взаимодействует {animal}, как минимум 2, с описанием в 2 слова
    3. Описание должно быть визуализируемым и однозначным
    4. 1-2 предложения, без лишних деталей
    5. Не должно содержать эмоций или настроения {animal}

    Примеры хороших преобразований:
    - "чистить зубы" → "{animal} держит зубную щетку во рту и чистит свои зубы"
    - "заниматься йогой" → "{animal} выполняет позу растяжки на йога-коврике"
    - "учить английский" → "{animal} сидит перед открытым учебником с английскими словами"
    - "медитировать" → "{animal} сидит с закрытыми глазами в позе лотоса на коврике для медитации"
    - "меньше использовать телефон" → "{animal} отодвигает лапой смартфон в сторону"
    - "пить больше воды" → "{animal} пьет воду из миски или стакана"

    Дай только финальное описание сцены без объяснений и вводных фраз.
    """

    return prompt


@PromptRegistry.register(RequestType.ILLUSTRATE_HABIT)
def habit_illustration_prompt(
        character: str = "кот",
        habit_text: str = "заниматься йогой",
        completion_rate: float = 1
) -> list:
    main_action = {
        "text": f"СЦЕНА: {character}. {habit_text}\n НА ИЗОБРАЖЕНИИ ОБЯЗАТЕЛЬНО ДОЛЖНО БЫТЬ ВИДНО: 1) {character}а; 2) как он физически выполняет это действие; 3) все необходимые для этого действия предметы. ДЕЙСТВИЕ ДОЛЖНО ПРОИСХОДИТЬ В НАСТОЯЩИЙ МОМЕНТ, а не до или после.",
        "weight": 5
    }

    if completion_rate == 0:
        mood_description = f"Настроение: {character} недовольный и несчастный, но всё равно выполняет действие."
    elif completion_rate < 0.5:
        mood_description = f"Настроение: {character} неуверенный и пугливый, но старается правильно выполнить действие."
    elif completion_rate < 0.8:
        mood_description = f"Настроение: {character} довольный и милый, выполняет действие с удовольствием."
    else:
        mood_description = f"Настроение: {character} как профессионал, в крутой позе с чёрными солнцезащитными очками, очень миловидный и серьезный, выполняет действие идеально и с энтузиазмом."

    # Вторичные инструкции с улучшенным описанием стиля
    secondary_instruction = f"""
{mood_description}

Стиль: высококачественная цифровая иллюстрация в стиле Pixar/Disney. Плавные линии, правильные пропорции, реалистичная анатомия животного с легкой стилизацией. Детализированные предметы с которыми животное взаимодействует. Мягкое объемное освещение с легкими тенями. Яркие, но гармоничные цвета. Четкая композиция с фокусом на действии.

НЕ ПОКАЗЫВАТЬ: просто портрет {character}а без действия; {character}а, который смотрит на предметы, но не использует их; {character}а в человеческой одежде; кривые или диспропорциональные изображения.
"""

    return [main_action, secondary_instruction]
