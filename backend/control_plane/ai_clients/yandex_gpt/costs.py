from yandex_cloud_ml_sdk import YCloudML

from backend.control_plane.ai_clients.ai_provider import AIProviderCostCalculator
from ..prompts import RequestType, PromptRegistry

class YandexGptCostCalculator(AIProviderCostCalculator):
    def __init__(self, folder_id, auth, model_name, cost):
        self.sdk = YCloudML(
            folder_id=folder_id,
            auth=auth
        )
        self.model_name = model_name
        self.cost_per_1k_tokens = cost

    async def calc_cost(self, prompt: str, request_type: RequestType) -> float:
        """Calculate cost including system prompt"""
        system_text = PromptRegistry.get_prompt(request_type)
        combined_text = f"'role': 'system', 'text': '{system_text}'\ndelimiter\n'role': 'user', 'text': '{prompt}'"
        token_count = await self._count_tokens(combined_text)
        return await self.calc_cost_per_tokens(token_count)

    async def calc_cost_per_tokens(self, token_count: int) -> float:
        """Calculate cost per tokens"""
        return self.cost_per_1k_tokens * token_count / 1000

    async def _count_tokens(self, text: str) -> int:
        model = self.sdk.models.completions(self.model_name)
        result = model.tokenize(text)
        return len(result)
