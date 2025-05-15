from datetime import datetime, timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.db.models import Reminder
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.requests.reminder import ReminderCompleteRequest, ReminderEditTimeRequest


@pytest.mark.usefixtures("TestReminder")
class TestReminderAPI:
    @pytest.mark.asyncio
    async def test_reminder_post(
            self,
            session: AsyncSession,
            auth_user: dict,
            client: httpx.AsyncClient
    ):
        reminder_text = "Напоминание тестовое 1"
        request_body = {
            "text": reminder_text,
            "time": str((datetime.now() + timedelta(hours=10)).isoformat()),
            "tags": []
        }

        response = await client.post(
            f"/v1/reminder/",
            json=request_body,
            headers=auth_user
        )

        assert response.status_code == 200

        data = response.json()
        assert data["text"] == reminder_text
        assert data["updated_at"] is not None  # Проверяем, что поле обновилось

        async with await session as session:
            assert ReminderSchema.model_validate(await session.get(Reminder, data["id"]))
            print("\nINFO: ВАЛИДАЦИЯ СХЕМЫ ReminderSchema МОДЕЛИ Reminder ИЗ БД")

            session.close()

    @pytest.mark.asyncio
    async def test_get_active_reminders(self,
                                        session: AsyncSession,
                                        auth_user: dict,
                                        client: httpx.AsyncClient):
        response = await client.get("/v1/reminder/", headers=auth_user)
        assert response.status_code == 200
        reminders = [ReminderSchema.model_validate(reminder_model) for reminder_model in response.json()]
        assert reminders

    @pytest.mark.asyncio
    async def test_reminder_edit(self,
                                 session: AsyncSession,  # Получаем сессию БД из фикстуры
                                 auth_user: dict,
                                 client: httpx.AsyncClient,  # Получаем клиента из фикстуры
                                 TestReminder: ReminderSchema  # случайное напоминание из БД
                                 ):
        reminder_id = str(TestReminder.id)
        updated_text = "Текст напоминания обновлен по-братски"

        request_body = {
            "id": reminder_id,
            "text": updated_text
        }
        response = await client.put(
            f"/v1/reminder/{reminder_id}",
            json=request_body,
            headers=auth_user
        )

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == reminder_id
        assert data["text"] == updated_text
        assert data["updated_at"] is not None  # Проверяем, что поле обновилось
        # assert datetime.fromisoformat(data["updated_at"].replace('Z',
        #                                                         '+00:00')) > test_reminder.updated_at  # Более точная проверка времени, если часовые пояса ровно обрабатываются

        # Проверяем, что данные действительно обновились в базе
        async with await session as session:
            updated_reminder_in_db = await session.get(Reminder, TestReminder.id)
            assert updated_reminder_in_db is not None
            assert updated_reminder_in_db.text == updated_text
            assert updated_reminder_in_db.updated_at > TestReminder.updated_at

    @pytest.mark.asyncio
    async def test_reminder_delete(self,
                                   client: httpx.AsyncClient,
                                   auth_user: dict,
                                   session: AsyncSession,
                                   TestReminder: Reminder
                                   ):
        response = await client.delete(f"/v1/reminder/{TestReminder.id}", headers=auth_user)

        assert response.status_code == 200

        async with await session as session:
            deleted_reminder_in_db = await session.get(Reminder, TestReminder.id)
            assert deleted_reminder_in_db is None

    @pytest.mark.asyncio
    async def test_reminder_to_complete(self,
                                        client: httpx.AsyncClient,
                                        session: AsyncSession,
                                        TestReminder: ReminderSchema,
                                        auth_user: dict
                                        ):
        request = ReminderCompleteRequest.model_validate({"id": TestReminder.id}).model_dump_json()

        response = await client.put(
            url=f"/v1/reminder/{TestReminder.id}/complete",
            headers=auth_user,
            data=request
        )

        assert response.status_code == 200

        data = response.json()
        print("INFO: СВЕРЯЕМ RESPONSE")
        assert data["id"] == str(TestReminder.id)
        assert data["status"] == "completed"
        assert data["updated_at"] is not None  # Поле обновления должно измениться

        # Проверяем, что статус действительно обновился в базе
        async with await session as session:
            print("INFO: ПОЛУЧАЕМ ИЗ БД")
            completed_reminder_in_db = await session.get(Reminder, TestReminder.id)

        assert completed_reminder_in_db is not None
        assert completed_reminder_in_db.status.value == "completed"
        assert completed_reminder_in_db.updated_at - TestReminder.updated_at

    @pytest.mark.asyncio
    async def test_reminder_postpone(self,
                                     client: httpx.AsyncClient,
                                     session: AsyncSession,
                                     TestReminder: ReminderSchema,
                                     auth_user: dict
                                     ):
        expect_changed_time = TestReminder.time + timedelta(hours=1)  # Отложить на 1 час

        request_body = ReminderEditTimeRequest.model_validate(
            {
                "id": TestReminder.id,
                "time": expect_changed_time
            }
        )

        response = await client.put(
            f"/v1/reminder/{TestReminder.id}/postpone",
            data=request_body.model_dump_json(),
            headers=auth_user,
        )

        assert response.status_code == 200

        # Проверяем данные в ответе API
        data = response.json()
        assert data["id"] == str(TestReminder.id)
        assert data["updated_at"] is not None  # Поле обновления должно измениться

        assert expect_changed_time == datetime.fromisoformat(data["time"])

        # Проверяем, что данные действительно обновились в базе
        async with await session as session:
            postponed_reminder_in_db = await session.get(Reminder, TestReminder.id)

        assert postponed_reminder_in_db is not None
        assert postponed_reminder_in_db.time == datetime.fromisoformat(data["time"])
        assert postponed_reminder_in_db.updated_at - TestReminder.updated_at

    # Добавь тесты для случаев ошибок, например, напоминание не найдено (404)
    @pytest.mark.asyncio
    async def test_reminder_not_found(self,
                                      client: httpx.AsyncClient):
        """Тест на случай, когда напоминание не найдено (например, при редактировании)."""
        non_existent_id = "non_existent_reminder_id"
        response = await client.post(
            f"/reminder/{non_existent_id}/",
            json={"text": "Trying to update non-existent"}
        )
        assert response.status_code == 404  # Или какой у тебя код для Not Found

        response = await client.delete(f"/reminder/{non_existent_id}")
        assert response.status_code == 404

        response = await client.post(f"/reminder/{non_existent_id}/complete")
        assert response.status_code == 404

        response = await client.post(
            f"/reminder/{non_existent_id}/postpone",
            json={"time_delta": 3600}
        )
        assert response.status_code == 404
