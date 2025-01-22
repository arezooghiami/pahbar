import logging
from collections import defaultdict
from datetime import datetime
from typing import List

import pytz
from fastapi import APIRouter
from fastapi import HTTPException, Depends, Query
from fastapi import status

from pahbar.prediction.services.auth.db import UserQueries
from pahbar.prediction.services.auth.model import User
from pahbar.prediction.services.auth.utils.get_current_user import get_current_user
from pahbar.prediction.services.util import DatabaseUtils
from ...db.load import RealHourlyLoadQueries
from ...exc import APIException
from ...model.location import DISCo

END_POINT = "/realLoad/fetchLoads"

route_realLoad_fetchLoads = APIRouter()

DB_ENGINE = DatabaseUtils.createEngine()
DB_METADATA = DatabaseUtils.createMetdata()

responses = {
    400: {
        "model": APIException,
        "description": "زمانهای ارسالی اشتباه هستند. دوباره تلاش کنید."},
    500: {
        "model": APIException,
        "description": "دریافت داده بار دچار مشکل شد. دوباره تلاش کنید."},
}


@route_realLoad_fetchLoads.get(
    END_POINT, description=(
            "Fetch the loads for the given timestamp. The timestamp should be provided in Unix format (seconds since the epoch). "
            "This endpoint uses the same date for both `fromDate` and `toDate`. Timestamps are truncated to the hour, ignoring minutes, seconds, and microseconds."
    ))
async def fetchRealLoads(
        dates: List[int]= Query(),
        user: User = Depends(get_current_user)):
    """
    Fetch the loads for a given timestamp. This assumes that both `fromDate` and `toDate` are derived
    from the same timestamp provided via `dates`. If no load exists for the given timestamp,
    the returned model has empty string for load of each hour.
    """
    try:
        # Iterate over dates
        formatted_loads = []
        for date in dates:
            date_datetime = datetime.utcfromtimestamp(date).replace(tzinfo=pytz.utc)
            iran_tz = pytz.timezone('Asia/Tehran')
            dt_local = date_datetime.astimezone(iran_tz)

            # Align to the start of the hour
            date_datetime = dt_local.replace(minute=0, second=0, microsecond=0)

            # Set the same timestamp for fromDate and toDate
            from_datetime = dt_local.replace(hour=0, minute=0, second=0, microsecond=0)

            # Align to the end of the day (23:59:59)
            to_datetime = date_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Query the database
            user_obj = UserQueries(DB_ENGINE, DB_METADATA)
            user_db = user_obj.get_user_by_username(user.username)
            loc_id = user_db.location

            loads = queryRealLoadsFromDB(loc_id, from_datetime, to_datetime)
            formatted_loads.extend(loads)

        if not formatted_loads:
            return {"ExpectedLoad": []}

        return formatted_loads

    except (ValueError, OverflowError):
        raise HTTPException(
            status_code=400,
            detail="Invalid Unix timestamp format."
        )


def queryRealLoadsFromDB(location: int, from_datetime: datetime, to_datetime: datetime):
    """Query loads from db. If no load exists for a given timestamp, then the returned model has empty string for load of each hour of that day."""
    try:
        with RealHourlyLoadQueries(DB_ENGINE, DB_METADATA) as q:
            db_records = q.selectByDate(location, from_datetime, to_datetime)
            if db_records:
                return format_loads(db_records)
            else:
                return []
    except Exception as e:
        logging.error(f"Could not read outages from DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e))


def format_loads(loads):
    # Initialize a dictionary to hold data by date, with all hours initially set to 0.0
    date_loads = defaultdict(lambda: {f"H{i}": 0.0 for i in range(0, 24)})

    for load in loads:
        # Ensure the outage has the expected fields
        if hasattr(load, 'datetime') and hasattr(load, 'load_MWh'):
            date = load.datetime[:10]  # Extract date
            hour = int(load.datetime[11:13])  # Extract hour (e.g., "14" -> Hour 14)

            # Only update if load_MWh is greater than 0
            if load.load_MWh > 0:
                date_loads[date][f"H{hour}"] = load.load_MWh

    # Create the final formatted list of loads
    formatted_loads = [
        {"date": date, **hours} for date, hours in date_loads.items()
    ]

    # Return sorted list by date
    return formatted_loads
