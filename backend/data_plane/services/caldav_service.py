"""
Сервис для работы с CalDAV
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
import caldav
from caldav.elements import dav, cdav

logger = logging.getLogger("caldav_service")


class CalDAVService:
    """Сервис для синхронизации с CalDAV календарями"""

    def __init__(self, integration_key: str):
        """
        Инициализация сервиса

        Args:
            integration_key: Ключ интеграции с календарем (JSON-строка с параметрами подключения)
        """
        import json
        self.config = json.loads(integration_key)
        self._client = None

    async def _get_client(self):
        """Получает клиента CalDAV"""
        if self._client is None:
            try:
                # CalDAV клиент не асинхронный, поэтому используем run_in_executor
                import asyncio
                loop = asyncio.get_event_loop()

                # Создаем клиента в отдельном потоке
                self._client = await loop.run_in_executor(None, caldav.DAVClient,
                                                          url=self.config.get("url"),
                                                          username=self.config.get("username"),
                                                          password=self.config.get("password")
                                                          )
            except Exception as e:
                logger.error(f"Ошибка при создании CalDAV клиента: {str(e)}")
                raise

        return self._client

    async def _get_calendar(self):
        """Получает календарь пользователя"""
        client = await self._get_client()

        try:
            import asyncio
            loop = asyncio.get_event_loop()

            # Получаем основной календарь пользователя
            principal = await loop.run_in_executor(None, client.principal)
            calendars = await loop.run_in_executor(None, principal.calendars)

            if not calendars:
                raise ValueError("No calendars found")

            # Выбираем календарь по имени или первый доступный
            target_calendar_name = self.config.get("calendar_name")

            if target_calendar_name:
                for calendar in calendars:
                    cal_name = await loop.run_in_executor(None, getattr, calendar, "name")
                    if cal_name == target_calendar_name:
                        return calendar

            # Если не нашли календарь по имени или имя не указано, берем первый
            return calendars[0]

        except Exception as e:
            logger.error(f"Ошибка при получении календаря: {str(e)}")
            raise

    async def sync_reminders(self, reminders: List[Any]) -> List[Dict[str, Any]]:
        """
        Синхронизирует напоминания с календарем

        Args:
            reminders: Список объектов напоминаний

        Returns:
            List: Список результатов синхронизации
        """
        import asyncio
        from datetime import timedelta

        try:
            calendar = await self._get_calendar()
            loop = asyncio.get_event_loop()

            # Получаем существующие события
            events = await loop.run_in_executor(None, calendar.events)

            # Преобразуем в словарь для быстрого поиска
            events_dict = {}
            for event in events:
                event_data = await loop.run_in_executor(None, event.data)
                events_dict[event_data.get("uid")] = event

            synced_events = []

            # Обрабатываем каждое напоминание
            for reminder in reminders:
                reminder_id = str(reminder.id)
                reminder_uid = f"reminder-{reminder_id}"

                # Проверяем, существует ли событие для этого напоминания
                if reminder_uid in events_dict:
                    # Обновляем существующее событие
                    event = events_dict[reminder_uid]
                    event_data = {
                        "summary": reminder.text,
                        "dtstart": reminder.time,
                        "dtend": reminder.time + timedelta(minutes=30),  # Длительность по умолчанию 30 минут
                        "description": f"Напоминание из Remind Me (ID: {reminder_id})"
                    }

                    await loop.run_in_executor(None, event.save, event_data)
                else:
                    # Создаем новое событие
                    from icalendar import Event as iCalEvent

                    ical_event = iCalEvent()
                    ical_event.add("summary", reminder.text)
                    ical_event.add("dtstart", reminder.time)
                    ical_event.add("dtend", reminder.time + timedelta(minutes=30))
                    ical_event.add("description", f"Напоминание из Remind Me (ID: {reminder_id})")
                    ical_event.add("uid", reminder_uid)

                    await loop.run_in_executor(None, calendar.save_event, ical_event.to_ical())

                synced_events.append({
                    "reminder_id": reminder_id,
                    "event_uid": reminder_uid,
                    "synced": True
                })

            return synced_events

        except Exception as e:
            logger.error(f"Ошибка при синхронизации с календарем: {str(e)}")
            return []
