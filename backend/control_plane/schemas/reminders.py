from pydantic import BaseModel, Field
from typing_extensions import Annotated
from pydantic import AfterValidator, BaseModel, ValidationError


def is_date(value: int) -> int:
    if value % 2 == 1:
        raise ValueError(f'{value} is not an even number')
    return value

class RemindersGetRequest(BaseModel):
    date: Annotated[int, AfterValidator(is_date)] = Field(frozen=True)


