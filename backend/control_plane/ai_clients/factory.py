from backend.control_plane.ai_clients import YandexGptProvider, AIProvider, YandexArtProvider


class AIProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "yandex_gpt") -> YandexGptProvider | YandexArtProvider:
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
        elif provider_type == "yandex_art":
            return YandexArtProvider(default_llm_ai_provider)
        else:
            raise ValueError(f"Unknown AI provider: {provider_type}")


# Создаем экземпляры провайдеров для использования в проекте
default_llm_ai_provider = AIProviderFactory.get_provider("yandex_gpt")
default_art_ai_provider = AIProviderFactory.get_provider("yandex_art")
