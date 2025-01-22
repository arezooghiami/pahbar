import jdatetime
from beartype import beartype
from jdatetime import datetime as jdatetime
from pydantic import BaseModel, Field, ValidationError

from pahbar.prediction.services.load.model.prediction.features.daily.load import RealLoadModel
from pahbar.prediction.services.load.model.prediction.features.daily.load import dailyRealLoad


class RealLoadAsString(BaseModel):
    """Daily real load represented as string per hour."""
    datetime: str = Field(..., description="نام datetime")
    load_MWh: float = Field(..., description="نام outage_MW")

    @beartype
    def fromDailyRealLoad(load: RealLoadModel, ndeciaml: int = 0):
        """Convert a `DailyRealLoad` core model to this class. This method does not raise

        Args:
            load (dailyRealLoad): Core's daily real load.
            ndeciaml (int, optional): Decimal places to keep after conversion to string. Defaults to 0.

        Returns:
            _type_: _description_
        """
        load_date = jdatetime.date.fromgregorian(
            date=load.date).strftime(RealLoadAsString.DATE_FORMAT)
        loadDict = {
            f"H{i}": round(load.loads[hour].load_MW, ndeciaml)
            for i, hour in enumerate(RealLoadModel.Hour, 1)}
        return RealLoadAsString(date=load_date, **loadDict)

    @beartype
    def toDailyRealLoad(self, location_id: int) -> RealLoadModel:
        try:
            datetime_jdatetime = jdatetime.strptime(self.datetime, "%Y/%m/%d %H:%M:%S")

            datetime = datetime_jdatetime.replace(minute=0, second=0)

            load_date = datetime.togregorian()

            to_datetime_formatted_str = datetime_jdatetime.strftime("%Y-%m-%d %H:%M:%S")


        except ValueError:
            raise ValueError("The given datetime string is not in the proper '1401/01/23 12:00:00' format")

        try:
            load_value = float(self.load_MWh)

        except ValueError:
            raise ValueError("The given load is not a proper number.")


        if load_date.year > 2100:
            raise ValueError("The given date for load is incorrect. Probably it's in Jalali format.")

        try:
            return RealLoadModel.create(location_id=location_id, datetime=to_datetime_formatted_str,
                                        load_MWh=load_value)
        except ValidationError as e:
            raise ValueError(f"Failed to create RealLoadModel: {e}")
