from sqlalchemy import Column, String, Date, Integer, Enum, DateTime, func, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class CalendarIntegration(BaseModel):
    __tablename__ = "calendar_integrations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    active = Column(Boolean, default=True)
    caldav_url = Column(Text)
    login = Column(String(255))
    password = Column(String(255))
    last_sync = Column(DateTime(timezone=True), nullable=True)

    # Отношения
    user = relationship("User", back_populates="calendar_integrations")
    reminders = relationship("Reminder", back_populates="calendar_integration")

    def __repr__(self):
        return f"<CalendarIntegration {self.caldav_url[:20]}... ({self.id})>"
