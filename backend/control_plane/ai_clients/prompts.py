from datetime import date, timedelta
from enum import Enum
from textwrap import dedent
from typing import Dict, Callable, List

from backend.control_plane.db.models import HabitInterval, Habit
from backend.control_plane.utils import timeutils


class RequestType(Enum):
    PREDICT_REMINDER_TIME = "predict_reminder_time"
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


@PromptRegistry.register(RequestType.ILLUSTRATE_HABIT)
def habit_illustration_prompt(
        habit_text: str = "заниматься йогой",
        progress: List[date] = None,
        interval: HabitInterval = HabitInterval.DAILY
) -> list:
    today = date.today()
    first_of_month = today.replace(day=1)
    if progress is None:
        progress = []

    # Расчет частоты и прогресса
    if interval == HabitInterval.DAILY:
        expected = (today - first_of_month).days + 1
        done = sum(1 for d in progress if first_of_month <= d <= today)
        frequency = f"ежедневно ({done}/{expected} дней выполнения)"
    elif interval == HabitInterval.WEEKLY:
        week_starts = [first_of_month + timedelta(days=i) for i in range(0, (today - first_of_month).days + 1) if
                       (first_of_month + timedelta(days=i)).weekday() == 0]
        expected = len(week_starts)
        done = sum(1 for d in progress if first_of_month <= d <= today)
        frequency = f"еженедельно ({done}/{expected} недель выполнения)"
    else:
        expected = 1
        done = sum(1 for d in progress if first_of_month <= d <= today)
        frequency = f"ежемесячно ({done}/{expected} выполнение)"

    completion_rate = done / expected if expected else 0

    # Выбор животного на основе привычки
    animal = "кот"  # универсальное животное по умолчанию
    # if "читать" in habit_text or "книг" in habit_text:
    #     animal = "сова"
    # elif "бег" in habit_text or "трениров" in habit_text or "спорт" in habit_text:
    #     animal = "заяц"
    # elif "медит" in habit_text or "йог" in habit_text:
    #     animal = "хомяк"
    # elif "зубы" in habit_text or "чист" in habit_text:
    #     animal = "бобер"
    # elif "писать" in habit_text or "рисова" in habit_text:
    #     animal = "енот"
    # elif "учить" in habit_text or "изуча" in habit_text:
    #     animal = "лисица"

    # Сверх-конкретная инструкция с очень высоким весом
    main_action = {
        "text": f"СЦЕНА: {animal} активно {habit_text}. НА ИЗОБРАЖЕНИИ ОБЯЗАТЕЛЬНО ДОЛЖНО БЫТЬ ВИДНО: 1) {animal}а; 2) как он физически выполняет действие '{habit_text}'; 3) все необходимые для этого действия предметы. ДЕЙСТВИЕ ДОЛЖНО ПРОИСХОДИТЬ В НАСТОЯЩИЙ МОМЕНТ, а не до или после.",
        "weight": 5
    }

    if completion_rate == 0:
        mood_description = f"Настроение: {animal} недовольный, но всё равно выполняет действие."
    elif completion_rate < 0.5:
        mood_description = f"Настроение: {animal} неуверенный, но старается правильно выполнить действие."
    elif completion_rate < 0.8:
        mood_description = f"Настроение: {animal} довольный и милый, выполняет действие с удовольствием."
    else:
        mood_description = f"Настроение: {animal} как профессионал, очень миловидный, выполняет действие идеально и с энтузиазмом."

    # Вторичные инструкции с улучшенным описанием стиля
    secondary_instruction = f"""
{mood_description}

Стиль: высококачественная цифровая иллюстрация в стиле Pixar/Disney. Плавные линии, правильные пропорции, реалистичная анатомия животного с легкой стилизацией. Детализированная текстура шерсти. Мягкое объемное освещение с легкими тенями. Яркие, но гармоничные цвета. Четкая композиция с фокусом на действии.

НЕ ПОКАЗЫВАТЬ: просто портрет {animal}а без действия; {animal}а, который смотрит на предметы, но не использует их; {animal}а в человеческой одежде; кривые или диспропорциональные изображения.
"""

    return [main_action, secondary_instruction]
