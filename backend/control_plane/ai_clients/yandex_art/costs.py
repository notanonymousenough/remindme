from backend.control_plane.ai_clients.ai_provider import AIProviderCostCalculator
from backend.control_plane.ai_clients.prompts import RequestType
from backend.config import get_settings


class YandexArtCostCalculator(AIProviderCostCalculator):
    def __init__(self, folder_id, auth, model_name="yandex-art", cost_per_image=10.0):
        self.folder_id = folder_id
        self.auth = auth
        self.model_name = model_name
        self.cost_per_image = cost_per_image  # Стоимость генерации одного изображения в рублях

    async def calc_cost(self, prompt: str, request_type: RequestType) -> float:
        """Рассчитать стоимость запроса на генерацию изображения"""
        # Для простоты, у нас фиксированная стоимость за одно изображение
        if request_type == RequestType.GENERATE_IMAGE:
            return self.cost_per_image
        raise ValueError(f"Unsupported request type for YandexArtCostCalculator: {request_type}")

    async def calc_cost_per_tokens(self, token_count: int) -> float:
        """В контексте YandexArt мы не используем токены, но метод должен быть реализован"""
        return self.cost_per_image
