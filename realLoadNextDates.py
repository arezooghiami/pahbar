from beartype.typing import ClassVar
from pydantic import BaseModel, Field
import jdatetime
from beartype import beartype


class RealLoadNextDates(BaseModel):
    """Defines the interval for which we're allowed to insert loads."""

    class Config:
        json_schema_extra = {
            "example": {
                "from_start": "1400/01/01",
                "from_default": "1401/01/01",
                "from_end": "1401/01/14",
                "to_start": "1400/01/01",
                "to_default": "1401/01/10",
                "to_end": "1401/01/14"
            },
        }
        
        frozen = True

    DATE_FORMAT: ClassVar[str] = "%Y/%m/%d"
    """The format of date string"""

    from_start: str = Field(
        ..., title="Jalai start date of 'from' interval as '%Y/%m/%d'")

    from_default: str = Field(
        ..., title="Jalai default value of 'from' interval as '%Y/%m/%d'")

    from_end: str = Field(
        ..., title="Jalai end date of 'to' interval as '%Y/%m/%d'")

    to_start: str = Field(
        ..., title="Jalai start date of 'to' interval as '%Y/%m/%d'")

    to_default: str = Field(
        ..., title="Jalai default value of 'to' interval as '%Y/%m/%d'")

    to_end: str = Field(
        ..., title="Jalai end date of 'to' interval as '%Y/%m/%d'")

    @beartype
    def create(
            from_start: jdatetime.date, from_default: jdatetime.date, from_end: jdatetime.date,
            to_start: jdatetime.date, to_default: jdatetime.date, to_end: jdatetime.date):
        """Create from actual datetimes."""
        if to_end < from_end:
            raise ValueError(
                "from end date can't be greater than to end date.")

        if not from_start <= from_default <= from_end:
            raise ValueError(
                "The condition 'from_start <= from_default <= from_end' is not satisfied. ")

        if not to_start <= to_default <= to_end:
            raise ValueError(
                "The condition 'to_start <= to_default <= to_end' is not satisfied. ")

        return RealLoadNextDates(
            from_start=from_start.strftime(
                RealLoadNextDates.DATE_FORMAT),
            from_default=from_default.strftime(
                RealLoadNextDates.DATE_FORMAT),
            from_end=from_end.strftime(RealLoadNextDates.DATE_FORMAT),
            to_start=to_start.strftime(RealLoadNextDates.DATE_FORMAT),
            to_default=to_default.strftime(
                RealLoadNextDates.DATE_FORMAT),
            to_end=to_end.strftime(RealLoadNextDates.DATE_FORMAT),
        )
