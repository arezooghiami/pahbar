import pydantic
from beartype.typing import ClassVar
from pydantic import BaseModel


class InterpolatedDate(BaseModel):
    """Represents the dates for which real load was interpolated."""

    class Config:
        json_schema_extras = {
            "example": {
                "date": "1401/01/23 12:00:00",
            }
        }
        
        frozen = True

    DATE_FORMAT: ClassVar[str] = "%Y-%m-%d %H:%M:%S"

    datetime: str = pydantic.Field(
        ...)
