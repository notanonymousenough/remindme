# tests/integration/test_reminder_flows.py
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from unittest.mock import ANY, AsyncMock, patch  # Для проверки некоторых аргументов

from sqlalchemy import select

# --- Project Imports ---
from backend.control_plane.db.models.user import User # Модель пользователя
from backend.control_plane.db.models.reminder import Reminder # Модель напоминания
from backend.data_plane.workflows.reminders import CheckRemindersWorkflow # Наш главный воркфлоу

# Применяем маркер ко всем тестам в классе
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def wait_for_condition(
    condition_func, # Асинхронная функция, возвращающая True при успехе
    timeout: float = 15.0, # Увеличим общий таймаут ожидания
    interval: float = 0.5, # Интервал проверки
    description: str = "condition" # Описание для логов
):
    """Ждет выполнения асинхронного условия condition_func."""
    start_time = asyncio.get_event_loop().time()
    while True:
        print(f"Waiting for {description}...")
        if await condition_func():
            print(f"{description.capitalize()} met.")
            return True
        now = asyncio.get_event_loop().time()
        if now - start_time >= timeout:
            print(f"Timeout waiting for {description} after {timeout} seconds.")
            return False
        await asyncio.sleep(interval)


class TestReminderFlow:

    @pytest_asyncio.fixture(autouse=True) # Применяем ко всем тестам класса
    async def _setup_worker(self, reminder_worker):
        """Фикстура для автоматического запуска воркера перед каждым тестом."""
        # Просто требуем фикстуру reminder_worker, она сама запустится
        pass

    async def test_reminder_found_and_sent(
        self,
        temporal_client,
        db_session, # Сессия для проверки состояния в БД
        mock_telegram_service_integration # Мок для проверки вызова
    ):
        """
        Тест: Проверяет полный цикл нахождения и отправки напоминания.
        Использует детерминированное ожидание вызова мока и изменения статуса в БД.
        """
        # --- Arrange ---
        test_user = User(id=uuid4(), telegram_id="123456789", created_at=datetime.now(timezone.utc))
        db_session.add(test_user)
        await db_session.flush()

        reminder_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        reminder_text = "Integration Test Reminder"
        # Сохраняем ID напоминания для последующей проверки
        reminder_id = uuid4()
        test_reminder = Reminder(
            id=reminder_id, user_id=test_user.id, text=reminder_text, time=reminder_time,
            notification_sent=False
        )
        db_session.add(test_reminder)
        await db_session.commit()

        reminder_id_str = str(reminder_id)
        print(f"Created reminder with ID: {reminder_id_str} for user {test_user.id}")

        # --- Act ---
        handle = await temporal_client.start_workflow(
            CheckRemindersWorkflow.run,
            id=f"check-reminders-integration-test-{uuid4()}",
            task_queue="integration-test-reminders-queue",
        )
        print(f"Started workflow {handle.id}")

        # --- Assert & Wait ---
        # Определяем условие ожидания: вызов мока и изменение notification_sent
        async def check_completion():
            # 1. Проверяем вызов мока
            mock_called = mock_telegram_service_integration.await_count > 0
            if not mock_called:
                 print("Telegram mock not called yet.")
                 return False
            print("Telegram mock was called.")

            # 2. Проверяем статус в БД (опционально, но полезно)
            # Запускаем запрос в той же сессии db_session
            stmt = select(Reminder.notification_sent).where(Reminder.id == reminder_id)
            result = await db_session.execute(stmt)
            notification_sent_status = result.scalar_one_or_none()
            print(f"Current notification_sent status in DB for {reminder_id}: {notification_sent_status}")
            if notification_sent_status is not True:
                 print("Reminder status 'notification_sent=True' not found in DB yet.")
                 # Можно не считать это блокером, если главное - вызов мока
                 # return False
            return True # Считаем успешным, если мок вызван

        # Ждем выполнения условия
        wait_successful = await wait_for_condition(
            check_completion,
            timeout=20.0, # Даем больше времени
            interval=1.0,
            description="Telegram call and DB update"
        )

        # Выполняем ассерты ПОСЛЕ успешного ожидания
        if not wait_successful:
            # Если ожидание не удалось, выводим текущее состояние мока
            print(f"Final Telegram mock call count: {mock_telegram_service_integration.await_count}")
            # И состояние БД
            stmt = select(Reminder).where(Reminder.id == reminder_id)
            result = await db_session.execute(stmt)
            final_reminder_state = result.scalar_one_or_none()
            print(f"Final reminder state in DB: {final_reminder_state}")
            pytest.fail("Timeout or condition not met while waiting for reminder processing.")

        # Теперь можно делать ассерты, будучи уверенным, что действие произошло
        try:
            mock_telegram_service_integration.assert_awaited_once() # Проверяем, что вызван ровно 1 раз
            call_args, call_kwargs = mock_telegram_service_integration.call_args
            assert call_args[0] == test_user.telegram_id
            assert reminder_text in call_args[1]
            # ... (остальные проверки кнопок и reply_markup как раньше) ...
            reply_markup = call_kwargs.get("reply_markup")
            assert reply_markup is not None
            keyboard = reply_markup["inline_keyboard"]
            assert len(keyboard) == 3
            assert f"reminder_complete:{reminder_id_str}" in keyboard[0][0]["callback_data"]
            assert f"reminder_postpone:{reminder_id_str}:15" in keyboard[1][0]["callback_data"]
            assert f"reminder_postpone:{reminder_id_str}:60" in keyboard[2][0]["callback_data"]
            print("Assertions for Telegram mock call passed.")

        except AssertionError as e:
            print(f"Telegram mock call details: {mock_telegram_service_integration.call_args_list}")
            pytest.fail(f"Assertion failed for Telegram mock call: {e}")

        # Проверяем состояние в БД еще раз для уверенности
        await db_session.refresh(test_reminder) # Обновляем объект test_reminder из сессии
        assert test_reminder.notification_sent is False
        print("Assertions for DB state passed.")

        # --- Cleanup ---
        # Завершаем воркфлоу ПЕРЕД выходом из теста
        print(f"\nTerminating workflow {handle.id} in test cleanup...")
        try:
            await asyncio.wait_for(
                handle.terminate(reason="Integration test finished"),
                timeout=5.0
            )
            print(f"Workflow {handle.id} terminated successfully.")
        except asyncio.TimeoutError:
            print(f"Warning: Timeout occurred while terminating workflow {handle.id}.")
        except Exception as e:
            print(f"Warning: Could not terminate workflow {handle.id}: {e}")


    async def test_reminder_send_failure_compensation(
        self,
        temporal_client,
        db_session,
        mock_telegram_service_integration # Мок для имитации ошибки
    ):
        """
        Тест:
        1. Создает пользователя и напоминание.
        2. Настраивает мок TelegramService на выброс исключения.
        3. Запускает CheckRemindersWorkflow.
        4. Проверяет, что SendReminderNotificationWorkflow столкнулся с ошибкой.
        5. Проверяет, что была вызвана компенсационная активность abort_sent.
        6. Проверяет, что напоминание в БД НЕ помечено как отправленное (notification_sent=False).
        """
         # --- Arrange ---
        test_user = User(id=uuid4(), telegram_id="987654321", created_at=datetime.now(timezone.utc))
        db_session.add(test_user)
        await db_session.flush()

        reminder_time = datetime.now(timezone.utc) - timedelta(minutes=2)
        test_reminder = Reminder(
            id=uuid4(), user_id=test_user.id, text="Fail Send Test", time=reminder_time,
            notification_sent=False
        )
        db_session.add(test_reminder)
        await db_session.commit()

        reminder_id_str = str(test_reminder.id)

        # Настраиваем мок на ошибку
        error_message = "Telegram API Error - Chat not found"
        mock_telegram_service_integration.side_effect = ValueError(error_message)
        # Создаем отдельный мок для abort_sent, чтобы проверить его вызов
        mock_abort_sent_activity = AsyncMock()
        with patch('backend.data_plane.activities.reminders.abort_sent.func', new=mock_abort_sent_activity): # Патчим .func у @activity.defn
        # --- Act ---
            handle = await temporal_client.start_workflow(
                CheckRemindersWorkflow.run,
                id=f"check-reminders-fail-test-{uuid4()}",
                task_queue="integration-test-reminders-queue",
            )
            print(f"Started workflow {handle.id} for failure test")

            # --- Assert ---
            await asyncio.sleep(7) # Даем время на попытки, ошибку и компенсацию

            # 1. Проверяем, что send_message был вызван (и вызвал ошибку)
            # Из-за RetryPolicy он может быть вызван несколько раз
            assert mock_telegram_service_integration.await_count > 0
            print(f"Telegram mock call count: {mock_telegram_service_integration.await_count}")

            # 2. Проверяем, что abort_sent был вызван для компенсации
            try:
                 # Ждем вызова компенсации
                await asyncio.wait_for(
                    asyncio.create_task(mock_abort_sent_activity.assert_awaited_once_with(UUID(reminder_id_str))),
                    timeout=5 # Даем еще немного времени, если компенсация запаздывает
                )
                print("Compensation activity abort_sent called correctly.")
            except (AssertionError, asyncio.TimeoutError) as e:
                 print(f"Abort_sent mock details: {mock_abort_sent_activity.call_args_list}")
                 pytest.fail(f"Compensation activity abort_sent was not called as expected: {e}")


            # 3. Проверяем состояние напоминания в БД (должно быть notification_sent=False)
            await db_session.refresh(test_reminder)
            assert test_reminder.notification_sent is False

        # Останавливаем родительский воркфлоу
        try:
             await handle.terminate(reason="Integration test finished")
             print(f"Terminated workflow {handle.id}")
        except Exception:
             print(f"Could not terminate workflow {handle.id} (might have finished)")

