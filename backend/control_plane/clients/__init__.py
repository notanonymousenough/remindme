from backend.control_plane.clients.ai_provider import AIProvider
from backend.control_plane.clients.yandex_gpt import YandexGptProvider


class AIProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "yandex_gpt") -> AIProvider:
        """
        Получить экземпляр AI-провайдера

        Args:
            provider_type: Тип провайдера. По умолчанию "yandex_gpt"

        Returns:
            AIProvider: Экземпляр провайдера

        Raises:
            ValueError: Если указан неизвестный тип провайдера
        """
        if provider_type == "yandex_gpt":
            return YandexGptProvider()
        else:
            raise ValueError(f"Unknown AI provider: {provider_type}")


# Создаем единый экземпляр по умолчанию для использования в проекте
default_ai_provider = AIProviderFactory.get_provider()
