"""
Активности для синхронизации с календарем
"""
import logging
from datetime import datetime, timedelta, timezone
from temporalio import activity
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.control_plane.db.repositories.reminder import ReminderRepository
from backend.control_plane.db.repositories.calendar import CalendarIntegrationRepository
from backend.control_plane.db.models.base import ReminderStatus
from backend.control_plane.db.repositories.user import UserRepository
from backend.data_plane.services.calendar_service import CalendarService
from backend.data_plane.services.telegram_service import TelegramService

logger = logging.getLogger("calendar_sync_activities")

SYNC_INTERVAL_MINUTES = 30

@activity.defn
async def get_users_for_calendar_sync() -> List[Dict[str, Any]]:
    """
    Получает список пользователей с активными интеграциями календаря для синхронизации
    """
    logger.info("Получение списка пользователей для синхронизации календаря")
    cal_integration_repo = CalendarIntegrationRepository()

    # Получаем все активные интеграции
    all_integrations = await cal_integration_repo.get_all_models(active=True)

    users_data = []
    for integration in all_integrations:
        # Проверяем, прошло ли достаточно времени с последней синхронизации
        should_sync = True
        if integration.last_sync:
            time_since_last_sync = datetime.now(timezone.utc) - integration.last_sync
            if time_since_last_sync < timedelta(minutes=SYNC_INTERVAL_MINUTES):
                should_sync = False

        if should_sync:
            users_data.append({
                "user_id": str(integration.user_id),
                "integration_id": str(integration.id),
                "caldav_url": integration.caldav_url,
                "login": integration.login,
                "password": integration.password
            })

    return users_data


@activity.defn
async def fetch_calendar_events(user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Получает события из календаря пользователя
    """
    logger.info(f"Получение событий календаря для пользователя {user_data['user_id']}")

    try:
        # Создаем сервис для работы с календарем
        calendar_service = CalendarService(
            caldav_url=user_data["caldav_url"],
            username=user_data["login"],
            password=user_data["password"]
        )

        # Определяем диапазон дат для синхронизации
        start_date = datetime.now(timezone.utc) - timedelta(days=7)  # Неделя назад
        end_date = datetime.now(timezone.utc) + timedelta(days=30)  # Месяц вперед

        # Получаем события из всех календарей пользователя
        # Не указываем calendar_id, чтобы сервис использовал первый доступный календарь
        events = await calendar_service.get_events(
            start_date=start_date,
            end_date=end_date
        )

        # Преобразуем объекты, которые не поддерживают JSON сериализацию
        serializable_events = []
        for event in events:
            # Копируем событие, чтобы не менять оригинал
            serialized_event = {}

            # Обрабатываем каждое поле
            for key, value in event.items():
                # Преобразуем datetime объекты в строки
                if isinstance(value, datetime):
                    serialized_event[key] = value.isoformat()
                # Преобразуем URL объекты в строки
                elif key == 'url' and hasattr(value, '__str__'):
                    serialized_event[key] = str(value)
                # Другие типы данных копируем как есть
                else:
                    serialized_event[key] = value

            # Добавляем информацию о пользователе и интеграции
            serialized_event["user_id"] = user_data["user_id"]
            serialized_event["integration_id"] = user_data["integration_id"]

            serializable_events.append(serialized_event)

        return serializable_events

    except Exception as e:
        logger.error(f"Ошибка при получении событий из календаря: {str(e)}")
        return []

@activity.defn
async def sync_calendar_events(
        user_id: str,
        integration_id: str,
        events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Синхронизирует события из календаря с напоминаниями
    """
    logger.info(f"Синхронизация {len(events)} событий календаря для пользователя {user_id}")

    reminder_repo = ReminderRepository()
    cal_integration_repo = CalendarIntegrationRepository()

    user_uuid = UUID(user_id)
    integration_uuid = UUID(integration_id)

    # Получаем все напоминания пользователя, связанные с календарем
    existing_reminders = await reminder_repo.get_models(
        user_id=user_uuid,
        calendar_integration_id=integration_uuid,
        removed=False
    )

    # Создаем словарь существующих напоминаний по ID события в календаре
    existing_by_event_id = {
        reminder.calendar_event_id: reminder
        for reminder in existing_reminders
        if reminder.calendar_event_id
    }

    results = {
        "created": 0,
        "updated": 0,
        "deleted": 0,
        "unchanged": 0,
        "errors": 0
    }

    # Множество ID событий из календаря для проверки удаленных напоминаний
    calendar_event_ids = set()

    # Обрабатываем полученные события
    for event in events:
        event_id = event.get("id")
        if not event_id:
            logger.warning(f"Событие без ID: {event}")
            continue

        calendar_event_ids.add(event_id)
        event_start = event.get("start")

        # Преобразуем строку ISO в datetime, если это строка
        if isinstance(event_start, str):
            try:
                event_start = datetime.fromisoformat(event_start)
            except ValueError as e:
                logger.error(f"Ошибка при преобразовании даты: {str(e)}")
                results["errors"] += 1
                continue

        # Если старт события не указан или в прошлом, пропускаем
        if not event_start or (isinstance(event_start, datetime) and event_start < datetime.now(timezone.utc)):
            continue

        # Формируем текст напоминания
        reminder_text = event.get("summary", "Событие из календаря")
        if event.get("location"):
            reminder_text += f" - {event['location']}"
        if event.get("description"):
            description = event.get("description")
            if len(description) > 100:  # Ограничиваем длину описания
                description = description[:97] + "..."
            reminder_text += f" ({description})"

        # Проверяем, существует ли напоминание для этого события
        if event_id in existing_by_event_id:
            # Обновляем существующее напоминание
            reminder = existing_by_event_id[event_id]

            # Проверяем, нужно ли обновление
            if (reminder.text != reminder_text or
                    (abs((reminder.time - event_start).total_seconds()) > 60 if isinstance(event_start,
                                                                                       datetime) else True)):

                try:
                    await reminder_repo.update_model(
                        model_id=reminder.id,
                        text=reminder_text,
                        time=event_start
                    )
                    results["updated"] += 1
                except Exception as e:
                    logger.error(f"Ошибка при обновлении напоминания: {str(e)}")
                    results["errors"] += 1
            else:
                results["unchanged"] += 1
        else:
            # Создаем новое напоминание
            try:
                await reminder_repo.create(
                    user_id=user_uuid,
                    text=reminder_text,
                    time=event_start,
                    status=ReminderStatus.ACTIVE,
                    calendar_event_id=event_id,
                    calendar_integration_id=integration_uuid
                )
                results["created"] += 1
            except Exception as e:
                logger.error(f"Ошибка при создании напоминания: {str(e)}")
                results["errors"] += 1

    # Проверяем напоминания, которых больше нет в календаре
    for reminder in existing_reminders:
        if reminder.calendar_event_id and reminder.calendar_event_id not in calendar_event_ids:
            try:
                # Помечаем напоминание как удаленное
                await reminder_repo.update_model(
                    model_id=reminder.id,
                    removed=True
                )
                results["deleted"] += 1
            except Exception as e:
                logger.error(f"Ошибка при удалении напоминания: {str(e)}")
                results["errors"] += 1

    # Обновляем время последней синхронизации в интеграции
    await cal_integration_repo.update_model(
        model_id=integration_uuid,
        last_sync=datetime.now(timezone.utc)
    )
    return results


@activity.defn
async def handle_sync_errors(user_id: str, integration_id: str, error: str) -> None:
    """
    Обрабатывает ошибки синхронизации календаря
    """
    logger.error(f"Ошибка синхронизации календаря для пользователя {user_id}: {error}")

    user_repo = UserRepository()
    cal_integration_repo = CalendarIntegrationRepository()
    integration_uuid = UUID(integration_id)

    # Обновляем время последней попытки синхронизации
    await cal_integration_repo.update_model(
        model_id=integration_uuid,
        last_sync=datetime.now(timezone.utc)
    )

    # Уведомляем пользователя об ошибке
    integration = await cal_integration_repo.get_by_model_id(integration_uuid)
    if not integration:
        return
    user = await user_repo.get_user(integration.user_id)
    if user and user.id:
        telegram_service = TelegramService()
        message = (
            f"⚠️ *Ошибка синхронизации календаря*\n\n"
            f"Не удалось синхронизировать календарь. Пожалуйста, проверьте настройки интеграции "
            f"в личном кабинете."
        )
        await telegram_service.send_message(
            integration.user.id,
            message,
            parse_mode="Markdown"
        )
