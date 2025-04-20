import logging
from typing import Tuple

from yandex_cloud_ml_sdk import YCloudML

from backend.config import get_settings
import yaml
import strip_markdown
import datetime

from .prompts import PromptRegistry, RequestType
from backend.control_plane.utils import timeutils

logger = logging.getLogger("yandex_gpt")


class YandexGptAPI:
    def __init__(self, folder_id, auth, model_name, model_version="rc"):
        self.sdk = YCloudML(
            folder_id=folder_id,
            auth=auth,
        )
        self.model_name = model_name
        self.model_version = model_version

    async def _query(self, system_text: str, prompt: str) -> Tuple[str, int]:
        messages = [
            {
                "role": "system",
                "text": system_text,
            },
            {
                "role": "user",
                "text": prompt,
            },
        ]
        resp = self.sdk.models.completions(model_name=self.model_name, model_version=self.model_version).configure(temperature=0.5) \
                .run(messages)
        logger.debug("resp:", resp)

        usage = resp.usage.total_tokens
        for alternative in resp.alternatives:
            if alternative.role == "assistant":
                return alternative.text, usage
        if len(resp.alternatives) > 0:
            return resp.alternatives[0].text, usage
        raise ValueError("no one alternatives found")

    async def predict_reminder_time(self, user_timezone_offset: int, query: str) -> Tuple[datetime, int]:
        system_prompt = PromptRegistry.get_prompt(
            RequestType.PREDICT_REMINDER_TIME,
            user_timezone_offset=user_timezone_offset
        )
        response, usage = await self._query(system_prompt, query)
        json_resp = yaml.safe_load(strip_markdown.strip_markdown(response).strip("`"))
        return timeutils.parse_string_in_user_timezone(json_resp["datetime"], user_timezone_offset, "%Y-%m-%dT%H:%M"), usage

yandex_gpt_client = YandexGptAPI(
    get_settings().YANDEX_CLOUD_FOLDER,
    get_settings().YANDEX_CLOUD_AI_IAM_TOKEN,
    get_settings().YANDEX_GPT_MODEL_NAME
)
