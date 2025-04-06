from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Tag(BaseModel):
    __tablename__ = "tags"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(7), default="#FFFFFF")
    emoji = Column(String(1), nullable=False)  # Арсен: добавил колонку с эмодзи, потому что для бота это важно

    # Отношения
    user = relationship("User", back_populates="tags")
    reminders = relationship("Reminder", secondary="reminder_tags", back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.name} ({self.id})>"
