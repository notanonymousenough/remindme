import logging
from typing import List, Dict, Union, Tuple, Optional, Any
import pathlib
import base64

from yandex_cloud_ml_sdk import YCloudML

from backend.config import get_settings
from backend.control_plane.ai_clients.ai_provider import AIArtProvider
from .costs import YandexArtCostCalculator

logger = logging.getLogger("yandex_art")


class YandexArtProvider(AIArtProvider):
    def __init__(self, folder_id=None, auth=None, model_name="yandex-art"):
        self.folder_id = folder_id or get_settings().YANDEX_CLOUD_FOLDER
        self.auth = auth or get_settings().YANDEX_CLOUD_AI_IAM_TOKEN
        self.model_name = model_name
        self.sdk = YCloudML(
            folder_id=self.folder_id,
            auth=self.auth,
        )
        self._cost_calculator = YandexArtCostCalculator(
            self.folder_id,
            self.auth,
            self.model_name,
            get_settings().YANDEX_ART_MODEL_COST
        )

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

    async def generate_habit_image(self, prompts, seed=0):
        return await self._generate_image(prompts, seed=seed)

