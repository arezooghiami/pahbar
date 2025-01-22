import logging

import jdatetime
from beartype import beartype
from beartype.typing import Optional
from fastapi import APIRouter, Depends
from fastapi import exceptions, status

from pahbar.prediction.services.auth.db import UserQueries
from pahbar.prediction.services.auth.model import User
from pahbar.prediction.services.auth.utils.get_current_user import get_current_user
from pahbar.prediction.services.featureBuilder.exc import APIException
from pahbar.prediction.services.util import DatabaseUtils
from .models import RealLoadNextDates
from ...db.load import RealLoadDatesQueries

END_POINT = "/realLoad/nextDates"

route_realLoad_nextDates = APIRouter()

DB_ENGINE = DatabaseUtils.createEngine()
DB_METADATA = DatabaseUtils.createMetdata()

extra_responses = {
    500: {
        "model": APIException,
        "description": "مشکلی وجود دارد. دوباره تلاش کنید."},
}


@route_realLoad_nextDates.get(
    END_POINT, response_model=Optional[RealLoadNextDates],
    responses=extra_responses)
async def getRealLoadNextDates(
        user: User = Depends(get_current_user)) -> Optional[RealLoadNextDates]:
    """Returns the 'next' dates for which we're allowed to define real load. That is, if real load is not available from some date in the past, this function returns an interval from that day up until yesterday. These date ranges are used by the front end to present a possible range of dates for defining real load. The dates comply to the following logic:

    -   First day with missing load is potentially the next date after last available day in db.
        If load is already provided up until yesterday, then we needn't go a day further
    -   Defaults are naturally set to first_missing_load_date for 'from' and yesterday for 'to'. Of course, these two could be equal.
    -   End dates are naturally yesterday for both 'to' and 'from'.
    """
    user_obj = UserQueries(DB_ENGINE, DB_METADATA)
    user_db = user_obj.get_user_by_username(user.username)
    loc_id = user_db.location
    return generateNextDate(loc_id)


@beartype
def generateNextDate(location: int) -> Optional[RealLoadNextDates]:
    """Generate dates with the following logic:

        -   First day with missing load is potentially the next date after last available day in db.
        If load is already provided up until yesterday, then we needn't go a day further
        -   Defaults are naturally set to first_missing_load_date for 'from' and yesterday for 'to'. Of course, these two could be equal.
        -   End dates are naturally yesterday for both 'to' and 'from'.

    Raises:
        sqlAlchemy.exceptions.HTTPException: In case something goes wrong.
    """
    try:
        with RealLoadDatesQueries(DB_ENGINE, DB_METADATA) as q:
            disco_dates = q.select(location)

    except Exception as e:
        logging.error(f"Cound not fetch dates from db: {e}")
        raise exceptions.HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "مشکلی وجود دارد. دوباره تلاش کنید.")

    if disco_dates is None:
        return None

    # First day with missing load is potentially the next date after last available day in db.
    first_missing_load_date = (jdatetime.datetime.fromgregorian(
        datetime=disco_dates.last_date) + jdatetime.timedelta(days=1))
    yesterday = jdatetime.datetime.now() + jdatetime.timedelta(days=-1)

    # If load is already provided up until yesterday, then we needn't go a day further.
    if yesterday < first_missing_load_date:
        first_missing_load_date = yesterday

    to_start = from_start = jdatetime.date.fromgregorian(
        date=disco_dates.first_date)

    # Defaults are naturally set to first_missing_load_date for 'from' and yesterday for 'to'. Of course, these two could be equal.
    from_default = first_missing_load_date.date()
    to_default = yesterday.date()

    # End dates are naturally yesterday for both 'to' and 'from'
    from_end = yesterday.date()
    to_end = yesterday.date()

    try:
        return RealLoadNextDates.create(
            from_start=from_start, from_default=from_default, from_end=from_end,
            to_start=to_start, to_default=to_default, to_end=to_end)

    except ValueError as e:
        # We expect the above process to not raise. But, perhaps it will for some unknown reason!
        logging.error(f"Cound create date model: {e}")
        raise exceptions.HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "!مشکلی وجود دارد. مجددا تلاش کنید.")
