from sqlalchemy import Column, Text, DateTime, Boolean, ForeignKey, Enum, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel, ReminderStatus

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

    # Отношения
    user = relationship("User", back_populates="reminders")
    tags = relationship("Tag", secondary=reminder_tags, back_populates="reminders")
    neuro_images = relationship("NeuroImage", back_populates="reminder")

    def __repr__(self):
        return f"<Reminder {self.text[:20]}... ({self.id})>"
