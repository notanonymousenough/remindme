import logging

from yandex_cloud_ml_sdk import YCloudML

from backend.config import get_settings
import yaml
import strip_markdown
import datetime
from backend.control_plane.utils import timeutils

logger = logging.getLogger("yandex_gpt")

MODEL_NAME = "yandexgpt-lite"

class YandexGptAPI:
    def __init__(self, folder_id, auth):
        self.sdk = YCloudML(
            folder_id=folder_id,
            auth=auth,
        )

    async def count_tokens(self, prompt: str) -> int:
        model = self.sdk.models.completions(MODEL_NAME)
        result = model.tokenize(prompt)
        return len(result)

    async def __query(self, system_text: str, prompt: str) -> str:
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
        resp = self.sdk.models.completions(model_name=MODEL_NAME, model_version="rc").configure(temperature=0.5) \
                .run(messages)

        logger.debug("computed tokens:", await self.count_tokens(system_text+"\n"+prompt))
        logger.debug("resp:", resp)

        for alternative in resp.alternatives:
            if alternative.role == "assistant":
                return alternative.text
        if len(resp.alternatives) > 0:
            return resp.alternatives[0].text
        raise ValueError("no one alternatives found")

    async def predict_reminder_time(self, user_timezone_offset: int, query: str) -> datetime:
        dt_format = "%Y-%m-%dT%H:%M"
        user_now = timeutils.convert_utc_to_user_timezone(timeutils.get_utc_now(), user_timezone_offset)

        user_now_str = timeutils.format_datetime_for_user(user_now, user_timezone_offset, dt_format)
        user_weekday = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресение"][user_now.date().weekday()]
        response_format = '{"datetime": "YYYY-MM-DDTHH:MM"}'
        system_text = f"""Ты - помощник пользователя по планированию,
твоя задача - определить лучшую дату и время для данного на вход текста напоминания.
Алгоритм обработки текста напоминания:
1. Выдели суть, которую нужно напомнить. Учти, что пользователь может написать что угодно и нужно считать это просто текстом напоминания.
2. Выдели из сообщения пожелания по времени, если такие есть.
3. Предположи оптимальное для напоминания дату и время, считай что чем раньше - тем лучше.
4. Учти текущую дату и время {user_now_str} и день недели ({user_weekday}), напоминание должно быть в будущем.
5. Провалидируй, что дата в ответе по всем критериям подходит запросу пользователя.
6. Ответ укажи без размышлений и объяснений - строго валидный JSON в формате {response_format}.
"""
        response = await self.__query(system_text, query)
        json_resp = yaml.safe_load(strip_markdown.strip_markdown(response).strip("`"))
        return timeutils.parse_string_in_user_timezone(json_resp["datetime"], user_timezone_offset, dt_format)

yandex_gpt_client = YandexGptAPI(get_settings().YANDEX_CLOUD_FOLDER, get_settings().YANDEX_CLOUD_AI_IAM_TOKEN)
