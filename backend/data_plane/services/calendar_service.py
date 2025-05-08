"""
Сервис для работы с календарями через CalDAV протокол с поддержкой разных серверов
"""
import caldav
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend.config import get_settings

logger = logging.getLogger("caldav_calendar_service")


class CalendarService:
    """Сервис для получения событий из календаря через CalDAV протокол"""

    def __init__(self, caldav_url: str, username: str, password: str):
        """
        Инициализация сервиса для конкретного пользователя

        Args:
            caldav_url: URL CalDAV сервера пользователя
            username: Имя пользователя (обычно email)
            password: Пароль или токен для доступа
        """
        self.url = caldav_url
        self.username = username
        self.password = password
        self.client = None
        self._connect()

    def _connect(self):
        """Создание подключения к CalDAV серверу пользователя"""
        try:
            self.client = caldav.DAVClient(
                url=self.url,
                username=self.username,
                password=self.password
            )
            logger.info(f"Успешное подключение к CalDAV серверу {self.url} для пользователя {self.username}")
        except Exception as e:
            logger.error(f"Ошибка подключения к CalDAV серверу {self.url}: {str(e)}")
            raise

    async def get_calendars(self) -> List[Dict[str, Any]]:
        """
        Получает список доступных календарей пользователя

        Returns:
            List[Dict]: Список календарей с их информацией
        """
        try:
            principal = self.client.principal()
            calendars = principal.calendars()

            result = []
            for calendar in calendars:
                result.append({
                    "id": calendar.id,
                    "name": calendar.name,
                    "url": calendar.url,
                    "description": getattr(calendar, "description", "")
                })

            return result
        except Exception as e:
            logger.error(f"Ошибка получения списка календарей: {str(e)}")
            raise

    async def get_events(
            self,
            calendar_id: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает события из календаря за указанный период

        Args:
            calendar_id: ID календаря (если None, используется первый доступный)
            start_date: Начальная дата для выборки событий (если None, используется сегодня)
            end_date: Конечная дата для выборки событий (если None, используется неделя вперед)

        Returns:
            List[Dict]: Список событий календаря
        """
        try:
            if start_date is None:
                start_date = datetime.now()

            if end_date is None:
                end_date = start_date + timedelta(days=7)

            principal = self.client.principal()

            # Получаем нужный календарь
            if calendar_id:
                # Поиск календаря по ID
                calendars = principal.calendars()
                calendar = next((cal for cal in calendars if cal.id == calendar_id), None)
                if not calendar:
                    raise ValueError(f"Календарь с ID {calendar_id} не найден")
            else:
                # Если ID не указан, берем первый календарь
                calendars = principal.calendars()
                if not calendars:
                    raise ValueError("Доступные календари не найдены")
                calendar = calendars[0]

            # Получаем события за указанный период
            events = calendar.date_search(start=start_date, end=end_date)

            result = []
            for event in events:
                event_data = event.data
                vevents = event.vobject_instance.vevent_list

                for vevent in vevents:
                    event_info = {
                        "id": getattr(vevent, "uid", "").value if hasattr(vevent, "uid") else "",
                        "summary": getattr(vevent, "summary", "").value if hasattr(vevent, "summary") else "Без названия",
                        "start": getattr(vevent, "dtstart", None).value if hasattr(vevent, "dtstart") else None,
                        "end": getattr(vevent, "dtend", None).value if hasattr(vevent, "dtend") else None,
                        "location": getattr(vevent, "location", "").value if hasattr(vevent, "location") else "",
                        "description": getattr(vevent, "description", "").value if hasattr(vevent, "description") else "",
                        "url": event.url,
                    }
                    result.append(event_info)

            return result

        except Exception as e:
            logger.error(f"Ошибка получения событий из календаря: {str(e)}")
            raise

    async def get_event_details(self, calendar_id: str, event_id: str) -> Dict[str, Any]:
        """
        Получает детальную информацию о конкретном событии

        Args:
            calendar_id: ID календаря
            event_id: ID события

        Returns:
            Dict: Детали события
        """
        try:
            principal = self.client.principal()
            calendars = principal.calendars()
            calendar = next((cal for cal in calendars if cal.id == calendar_id), None)

            if not calendar:
                raise ValueError(f"Календарь с ID {calendar_id} не найден")

            # Поиск события по ID
            for event in calendar.events():
                vevent = event.vobject_instance.vevent
                if getattr(vevent, "uid", "").value == event_id:
                    # Если нашли нужное событие
                    attendees = []
                    if hasattr(vevent, "attendee_list"):
                        for attendee in vevent.attendee_list:
                            attendees.append({
                                "email": attendee.value.split(":")[-1],
                                "status": getattr(attendee, "partstat", "").value if hasattr(attendee, "partstat") else "unknown"
                            })

                    return {
                        "id": getattr(vevent, "uid", "").value if hasattr(vevent, "uid") else "",
                        "summary": getattr(vevent, "summary", "").value if hasattr(vevent, "summary") else "Без названия",
                        "start": getattr(vevent, "dtstart", None).value if hasattr(vevent, "dtstart") else None,
                        "end": getattr(vevent, "dtend", None).value if hasattr(vevent, "dtend") else None,
                        "location": getattr(vevent, "location", "").value if hasattr(vevent, "location") else "",
                        "description": getattr(vevent, "description", "").value if hasattr(vevent, "description") else "",
                        "organizer": getattr(vevent, "organizer", "").value if hasattr(vevent, "organizer") else "",
                        "status": getattr(vevent, "status", "").value if hasattr(vevent, "status") else "",
                        "url": event.url,
                        "created": getattr(vevent, "created", None).value if hasattr(vevent, "created") else None,
                        "last_modified": getattr(vevent, "last_modified", None).value if hasattr(vevent, "last_modified") else None,
                        "attendees": attendees
                    }

            raise ValueError(f"Событие с ID {event_id} не найдено")

        except Exception as e:
            logger.error(f"Ошибка получения деталей события: {str(e)}")
            raise
