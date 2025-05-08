from typing import Optional
from uuid import UUID

from pydantic import Field, BaseModel

from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.habit import HabitSchemaResponse


class RemovedEntities(BaseModel):
    reminder: Optional[ReminderSchema] = Field(None)
    habit: Optional[HabitSchemaResponse] = Field(None)


class RemovedEntitiesIDs(BaseModel):
    reminder_id: Optional[UUID] = Field(None, description="reminder id to change status")
    habit_id: Optional[UUID] = Field(None, description="habit id to change status")
