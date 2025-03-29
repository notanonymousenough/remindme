from sqlalchemy import Column, String, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel, ImageStatus


class NeuroImage(BaseModel):
    __tablename__ = "neuro_images"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    habit_id = Column(UUID(as_uuid=True), ForeignKey("habits.id", ondelete="SET NULL"), nullable=True)
    reminder_id = Column(UUID(as_uuid=True), ForeignKey("reminders.id", ondelete="SET NULL"), nullable=True)
    image_url = Column(String(512), nullable=False)
    thumbnail_url = Column(String(512))
    prompt = Column(Text)
    status = Column(Enum(ImageStatus))

    # Отношения
    #user = relationship("User", back_populates="neuro_images")
    #habit = relationship("Habit", back_populates="neuro_images")
    #reminder = relationship("Reminder", back_populates="neuro_images")

    def __repr__(self):
        return f"<NeuroImage id={self.id}>"
