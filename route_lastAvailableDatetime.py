import jdatetime
from beartype import beartype
from beartype.typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from pahbar.prediction.services.auth.db import UserQueries
from pahbar.prediction.services.auth.model import User
from pahbar.prediction.services.auth.utils.get_current_user import get_current_user
from pahbar.prediction.services.load.exc import APIException
from pahbar.prediction.services.util import DatabaseUtils
from .models import LastAvailableDatetime
from ...db.load import RealLoadDatesQueries

END_POINT = "/realLoad/lastAvailableDatetime"

route_realLoad_lastAvailableDatetime = APIRouter()

DB_ENGINE = DatabaseUtils.createEngine()
DB_METADATA = DatabaseUtils.createMetdata()

extra_responses = {
    500: {
        "model": APIException,
        "description": "مشکلی وجود دارد. دوباره تلاش کنید."},
}


@route_realLoad_lastAvailableDatetime.get(
    END_POINT, response_model=Optional[LastAvailableDatetime], responses=extra_responses
)
async def getLastAvailableLoadDatetime(
        user: User = Depends(get_current_user)) -> Optional[LastAvailableDatetime]:
    """Returns the last date for which a load exists for this user.  
    """

    user_obj = UserQueries(DB_ENGINE, DB_METADATA)
    user_db = user_obj.get_user_by_username(user.username)
    loc_id = user_db.location

    return generateLastAvailableDatetime(loc_id)


@beartype
def generateLastAvailableDatetime(location: int) -> Optional[LastAvailableDatetime]:
    """Checks the library for last date of real load for this disco.
    Raises:
        sqlAlchemy.exceptions.HTTPException: In case something goes wrong.
    """
    try:
        with RealLoadDatesQueries(DB_ENGINE, DB_METADATA) as q:
            disco_dates = q.select(location)
        return LastAvailableDatetime(
            date=jdatetime.datetime.fromgregorian(datetime=disco_dates.last_date).strftime(
                LastAvailableDatetime.DATE_FORMAT))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="آخرین زمان مجاز یافت نشد")
