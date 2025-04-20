import logging
from uuid import UUID

from backend.control_plane.db.repositories.quota import QuotaUsageRepository
from backend.control_plane.clients.yandex_gpt import yandex_gpt_cost_calculator, RequestType

logger = logging.getLogger("quota_service")


class QuotaService:
    def __init__(self):
        self.repo = QuotaUsageRepository()

    async def _check_resource_type_limit(self, user_id: UUID, resource_type: str, usage_diff: float = 1):
        return await self.repo.check_resource_limit(user_id, resource_type, usage_diff)

    async def _update_resource_type_usage(self, user_id: UUID, resource_type: str, usage_diff: float = 1):
        return await self.repo.update_resource_usage(user_id, resource_type, usage_diff)

    async def check_ai_request_limit(self, user_id: UUID, request_type: RequestType, prompt: str):
        request_cost = await yandex_gpt_cost_calculator.calc_cost(prompt, request_type)
        daily_quota_ok = self._check_resource_type_limit(user_id, f"ai_{request_type.value}_daily", request_cost)
        if not daily_quota_ok:
            raise ValueError("quota exceeded")
        monthly_quota_ok = self._check_resource_type_limit(user_id, f"ai_{request_type.value}_monthly", request_cost)
        if not monthly_quota_ok:
            raise ValueError("quota exceeded")

    async def update_ai_request_usage(self, user_id: UUID, request_type: RequestType, token_count: int):
        request_cost = await yandex_gpt_cost_calculator.calc_cost_per_tokens(token_count)
        await self._update_resource_type_usage(user_id, f"ai_{request_type.value}", request_cost)


_quota_service = QuotaService()

def get_quota_service():
    return _quota_service
