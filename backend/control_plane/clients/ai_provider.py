from abc import ABC, abstractmethod
from typing import Tuple, Any
import datetime


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

    @abstractmethod
    async def predict_reminder_time(self, timezone_offset: int, query: str) -> Tuple[datetime.datetime, int]:
        """
        Предсказать время напоминания

        Returns:
            Tuple[datetime, int]: Предсказанное время и количество использованных токенов
        """
        pass

