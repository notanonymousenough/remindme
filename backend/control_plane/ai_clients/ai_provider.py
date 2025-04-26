from abc import ABC, abstractmethod
from typing import Tuple, Any, List
import datetime

from backend.control_plane.db.models import HabitInterval


class AIProviderCostCalculator(ABC):
    """Абстрактный класс для расчета стоимости запросов к AI-провайдеру"""

    @abstractmethod
    async def calc_cost(self, prompt: str, request_type: Any) -> float:
        """Рассчитать стоимость запроса, включая системный промпт"""
        pass

    @abstractmethod
    async def calc_cost_per_tokens(self, token_count: int) -> float:
        """Рассчитать стоимость по количеству токенов"""
        pass


class AIProvider(ABC):
    """Абстрактный класс для AI-провайдера"""

    @property
    @abstractmethod
    def cost_calculator(self) -> AIProviderCostCalculator:
        """Получить калькулятор стоимости для этого провайдера"""
        pass


class AILLMProvider(AIProvider):
    """Абстрактный класс для AI-LLM-провайдера"""

    @abstractmethod
    async def predict_reminder_time(self, timezone_offset: int, query: str) -> Tuple[datetime.datetime, int]:
        """
        Предсказать время напоминания

        Returns:
            Tuple[datetime, int]: Предсказанное время и количество использованных токенов
        """
        pass

    @abstractmethod
    async def describe_habit_text(self, habit_text: str, animal: str) -> Tuple[str, int]:
        """
        Генерирует запрос к YandexGPT для конкретизации привычки
        """
        pass


class AIArtProvider(AIProvider):
    """Абстрактный класс для AI-Art-провайдера"""

    @abstractmethod
    async def generate_habit_image(self, habit_text: str, progress: List[datetime.date], interval: HabitInterval) -> Tuple[bytes, int]:
        """
        Сгенерировать картинку для привычки

        Returns:
            bytes: Изображение в байтовом формате
        """
        pass

