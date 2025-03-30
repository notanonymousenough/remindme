from sqlalchemy import Column, String, Text, ForeignKey, Enum, Integer, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel, AchievementCategory


class AchievementTemplate(BaseModel):
    __tablename__ = "achievement_templates"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon_url = Column(String(512))
    condition = Column(Text, nullable=False)
    category = Column(Enum(AchievementCategory), nullable=False)

    # Отношения
    user_achievements = relationship("UserAchievement", back_populates="template")

    def __repr__(self):
        return f"<AchievementTemplate {self.name} ({self.id})>"


class UserAchievement(BaseModel):
    __tablename__ = "user_achievements"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("achievement_templates.id"), nullable=False)
    unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime(timezone=True))
    progress = Column(Integer, default=0)

    # Отношения
    user = relationship("User", back_populates="achievements")
    template = relationship("AchievementTemplate", back_populates="user_achievements")

    # Ограничения
    __table_args__ = (
        UniqueConstraint('user_id', 'template_id', name='uq_user_achievement'),
    )

    def __repr__(self):
        return f"<UserAchievement user={self.user_id} template={self.template_id}>"
