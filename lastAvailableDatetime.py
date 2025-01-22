from beartype.typing import ClassVar
from pydantic import BaseModel, Field


class LastAvailableDatetime(BaseModel):
    """Represents the last date for which a load exists."""
    class Config:
        json_schema_extras = {
            "example": {
                "date": "1401/01/23",
            }
        }
        
        frozen = True

    DATE_FORMAT: ClassVar[str] =  "%Y-%m-%d %H:%M:%S"

    date: str = Field(
        ...)
