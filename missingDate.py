from beartype.typing import ClassVar
from pydantic import BaseModel
import pydantic


class MissingDate(BaseModel):
    """Represents the dates for which real load is missing."""
    class Config:
        json_schema_extras = {
            "example": {
                "date": "1401/01/23",
            }
        }
        
        frozen = True

    DATE_FORMAT: ClassVar[str] = "%Y/%m/%d"

    date: str = pydantic.Field(
        ..., title="The Jalali date as '%Y/%m/%d', such as 1401/02/31")
