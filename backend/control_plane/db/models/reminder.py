import uuid
from typing import List

from sqlalchemy import Column, Text, DateTime, Boolean, ForeignKey, Enum, Table, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.util import hybridproperty

from .base import BaseModel, ReminderStatus
from ...schemas.tag import TagSchema

# Связующая таблица для отношения многие-ко-многим между напоминаниями и тегами
reminder_tags = Table(
    'reminder_tags',
    BaseModel.metadata,
    Column('reminder_id', UUID(as_uuid=True), ForeignKey('reminders.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)


class Reminder(BaseModel):
    __tablename__ = "reminders"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    time = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(ReminderStatus), default=ReminderStatus.ACTIVE)
    removed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    notification_sent = Column(Boolean, default=False)
    calendar_event_id = Column(String(255), nullable=True)
    calendar_integration_id = Column(UUID(as_uuid=True), ForeignKey("calendar_integrations.id", ondelete="SET NULL"), nullable=True)

    # Отношения
    user = relationship("User", back_populates="reminders")
    _tags = relationship("Tag", secondary=reminder_tags, back_populates="reminders", lazy="selectin")
    neuro_images = relationship("NeuroImage", back_populates="reminder")
    calendar_integration = relationship("CalendarIntegration", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder {self.text[:20]}... ({self.id})>"

    @hybridproperty
    def tags(self) -> List[TagSchema]:
        return [TagSchema.model_validate(tag) for tag in self._tags]
