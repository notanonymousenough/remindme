from sqlalchemy import Column, String, Text, ForeignKey, Enum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel, ImageRate, ImageStatus


class NeuroImage(BaseModel):
    __tablename__ = "neuro_images"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    habit_id = Column(UUID(as_uuid=True), ForeignKey("habits.id", ondelete="SET NULL"), nullable=True)
    reminder_id = Column(UUID(as_uuid=True), ForeignKey("reminders.id", ondelete="SET NULL"), nullable=True)
    image_url = Column(String(512), nullable=False)
    thumbnail_url = Column(String(512))
    status = Column(Enum(ImageStatus))
    rate = Column(Enum(ImageRate))
    prompt = Column(Text)

    # Отношения
    user = relationship("User", back_populates="neuro_images")
    habit = relationship("Habit", back_populates="neuro_images")
    reminder = relationship("Reminder", back_populates="neuro_images")

    def __repr__(self):
        return f"<NeuroImage id={self.id}>"
