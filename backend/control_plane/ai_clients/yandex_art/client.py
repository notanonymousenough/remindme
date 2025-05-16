import logging
from datetime import datetime
from typing import List, Dict, Union, Tuple, Optional, Any
import pathlib
import base64

from yandex_cloud_ml_sdk import YCloudML

from backend.config import get_settings
from backend.control_plane.ai_clients.ai_provider import AIArtProvider, AILLMProvider
from .costs import YandexArtCostCalculator
from ..prompts import PromptRegistry, RequestType
from ...db.models import HabitInterval

logger = logging.getLogger("yandex_art")


class YandexArtProvider(AIArtProvider):
    def __init__(self, llm_model: AILLMProvider, folder_id=None, auth=None, model_name="yandex-art"):
        self.folder_id = folder_id or get_settings().YANDEX_CLOUD_FOLDER
        self.auth = auth or get_settings().YANDEX_CLOUD_AI_SECRET
        self.model_name = model_name
        self.sdk = YCloudML(
            folder_id=self.folder_id,
            auth=self.auth,
        )
        self._cost_calculator = YandexArtCostCalculator(
            llm_model,
            self.folder_id,
            self.auth,
            self.model_name,
            get_settings().YANDEX_ART_MODEL_COST
        )
        self.llm_model = llm_model

    @property
    def cost_calculator(self) -> YandexArtCostCalculator:
        return self._cost_calculator

    async def _generate_image(
            self,
            prompts: Union[str, List[Union[str, Dict[str, Any]]]],
            width_ratio: int = 1,
            height_ratio: int = 1,
            seed: Optional[int] = None
    ) -> bytes:
        """
        Генерирует изображение на основе промпта

        Args:
            prompts: Строка или список промптов (строк или словарей с текстом и весом)
            width_ratio: Соотношение ширины (пропорция)
            height_ratio: Соотношение высоты (пропорция)
            seed: Сид для детерминированной генерации

        Returns:
            bytes: Байты изображения
        """
        model = self.sdk.models.image_generation(self.model_name)

        # Настраиваем модель
        model = model.configure(width_ratio=width_ratio, height_ratio=height_ratio)
        if seed is not None:
            model = model.configure(seed=seed)

        # Запускаем генерацию изображения
        operation = model.run_deferred(prompts)
        result = operation.wait()

        # Возвращаем байты изображения и фиктивное количество "токенов" (стоимость всегда фиксирована)
        return result.image_bytes

    async def generate_habit_image(self, character: str, habit_text: str, completion_rate: float, seed=0) -> Tuple[bytes, int]:
        described_habit, count_tokens = await self.llm_model.describe_habit_text(habit_text[:100], character)
        # TODO: в случае цензуры не генерировать совсем?
        if "В интернете есть много сайтов с информацией на эту тему" in described_habit:
            described_habit = "стоит"
        habit_prompts = PromptRegistry.get_prompt(RequestType.ILLUSTRATE_HABIT, character=character, habit_text=described_habit, completion_rate=completion_rate)
        return await self._generate_image(habit_prompts, seed=seed), count_tokens
