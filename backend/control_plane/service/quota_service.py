import logging
from uuid import UUID

from backend.control_plane.ai_clients import default_llm_ai_provider, default_art_ai_provider, AIProvider
from backend.control_plane.ai_clients.prompts import RequestType
from backend.control_plane.db.repositories.quota import QuotaUsageRepository
from backend.control_plane.db.types.quotas import get_quotas_for_request_type
from backend.control_plane.exceptions.quota import QuotaExceededException

logger = logging.getLogger("quota_service")


class QuotaService:
    def __init__(self):
        self.repo = QuotaUsageRepository()
        self.ai_llm_provider = default_llm_ai_provider
        self.ai_art_provider = default_art_ai_provider

    async def _check_resource_type_limit(self, user_id: UUID, resource_type: str, usage_diff: float = 1):
        """
        Проверяет, не превышен ли лимит для заданного типа ресурса

        Args:
            user_id: ID пользователя
            resource_type: Тип ресурса
            usage_diff: Разница в использовании (сколько хотим использовать)

        Returns:
            bool: True, если лимит не превышен, иначе False
        """
        return await self.repo.check_resource_limit(user_id, resource_type, usage_diff)

    async def _update_resource_type_usage(self, user_id: UUID, resource_type: str, usage_diff: float = 1):
        """
        Обновляет использование заданного типа ресурса

        Args:
            user_id: ID пользователя
            resource_type: Тип ресурса
            usage_diff: Разница в использовании (сколько хотим использовать)

        Returns:
            bool: True, если обновление прошло успешно
        """
        return await self.repo.update_resource_usage(user_id, resource_type, usage_diff)

    async def check_ai_llm_request_limit(self, user_id: UUID, request_type: RequestType, prompt: str):
        """
        Проверяет, не превышены ли лимиты для запроса к ИИ

        Args:
            user_id: ID пользователя
            request_type: Тип запроса
            prompt: Текст запроса

        Raises:
            QuotaExceededException: Если хотя бы один лимит превышен
        """
        request_cost = await self.ai_llm_provider.cost_calculator.calc_cost(prompt, request_type)

        # Получаем список типов ресурсов для проверки
        resource_types = get_quotas_for_request_type(request_type)

        for resource_type in resource_types:
            quota_ok = await self._check_resource_type_limit(user_id, resource_type.value, request_cost)
            if not quota_ok:
                # Здесь можно получить текущие значения из репозитория для более детальной информации
                raise QuotaExceededException(
                    quota_type=resource_type.value,
                    user_id=user_id,
                    requested_value=request_cost
                )

    async def update_ai_llm_request_usage(self, user_id: UUID, request_type: RequestType, token_count: int, custom_ai_provider: AIProvider = None):
        """
        Обновляет использование ресурсов после запроса к ИИ

        Args:
            user_id: ID пользователя
            request_type: Тип запроса
            token_count: Количество использованных токенов
        """
        cost_calculator = self.ai_llm_provider.cost_calculator
        if custom_ai_provider is not None:
            cost_calculator = custom_ai_provider.cost_calculator
        request_cost = await cost_calculator.calc_cost_per_tokens(token_count)
        resource_types = get_quotas_for_request_type(request_type)

        for resource_type in resource_types:
            await self._update_resource_type_usage(user_id, resource_type.value, request_cost)


    async def check_and_increment_resource(self, user_id: UUID, resource_type: str, increment: int = 1) -> bool:
        """
        Атомарно проверяет и увеличивает счетчик использования ресурса.

        Args:
            user_id: ID пользователя
            resource_type: Тип ресурса
            increment: Количество добавляемых ресурсов

        Returns:
            bool: True, если операция выполнена успешно

        Raises:
            QuotaExceededException: Если превышен лимит ресурса
        """
        result = await self.repo.check_and_increment_resource_count(user_id, resource_type, increment)
        if not result:
            current_usage = await self.repo.get_current_resource_count(user_id, resource_type)
            raise QuotaExceededException(
                quota_type=resource_type,
                user_id=user_id,
                requested_value=increment,
                current_usage=current_usage
            )
        return True


    async def check_and_increment_ai_art_usage(self, user_id: UUID, request_type: RequestType) -> bool:
        request_cost = await self.ai_art_provider.cost_calculator.calc_cost(request_type)
        resource_types = get_quotas_for_request_type(request_type)
        for resource_type in resource_types:
            result = await self.repo.check_and_increment_resource_count(user_id, resource_type.value, request_cost)
            if not result:
                current_usage = await self.repo.get_current_resource_count(user_id, resource_type.value)
                raise QuotaExceededException(
                    quota_type=resource_type.value,
                    user_id=user_id,
                    requested_value=request_cost,
                    current_usage=current_usage
                )
            return True


    async def decrement_resource(self, user_id: UUID, resource_type: str, decrement: int = 1) -> bool:
        """
        Уменьшает счетчик использования ресурса.

        Args:
            user_id: ID пользователя
            resource_type: Тип ресурса
            decrement: Количество удаляемых ресурсов

        Returns:
            bool: True, если операция выполнена успешно
        """
        return await self.repo.check_and_decrement_resource_count(user_id, resource_type, decrement)


_quota_service = QuotaService()


def get_quota_service():
    return _quota_service
