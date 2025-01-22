import datetime
import logging
from beartype.typing import Dict
from beartype.typing import List

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile
from fastapi import HTTPException

from pahbar.prediction.services.auth.db import UserQueries
from pahbar.prediction.services.auth.model import User
from pahbar.prediction.services.auth.utils.get_current_user import get_current_user
from pahbar.prediction.services.load.api.realLoad.route_defineLoads import writeLoadsToDB
from pahbar.prediction.services.load.exc import APIException
from pahbar.prediction.services.load.model.prediction.features.daily.load import RealLoadModel
from pahbar.prediction.services.util import DatabaseUtils

END_POINT = "/realLoad/defineLoadsAsExcel"
route_realLoad_defineLoadsAsExcel = APIRouter()

DB_ENGINE = DatabaseUtils.createEngine()
DB_METADATA = DatabaseUtils.createMetdata()

extra_responses = {
    400: {
        "model": APIException,
        "description": "داده بار ارسالی به صورت قابل قبول نیست."},
    500: {
        "model": APIException,
        "description": "داده بار ثبت نشد. دوباره تلاش کنید."},
}


@route_realLoad_defineLoadsAsExcel.post(
    END_POINT, response_model=Dict[str, List], responses=extra_responses)
async def defineRealLoadAsExcelFile(
        file: UploadFile, user: User = Depends(get_current_user)) -> dict[str, List[str]]:
    """Set or replace real loads, using an excel file format. The excel file must contain a column, with name "تاریخ" together with 24 other columns named H1 to H24, each of which represent the load of a particular hour. Note that the dates have to be consecutive and no date must be missing in between, otherwise a '400' error is returned.
    """
    user_obj = UserQueries(DB_ENGINE, DB_METADATA)
    user_db = user_obj.get_user_by_username(user.username)
    loc_id = user_db.location

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        logging.error(f"Could not read Excel file: {e}")
        raise HTTPException(
            status_code=400, detail="Error reading Excel file.")

        # Convert Excel data to loadCorrection objects
    try:
        loads = []
        for index, row in df.iterrows():
            date = str(row["date"])
            for hour in range(0, 24):
                time = datetime.time(hour=hour, minute=0, second=0)
                datetime_str = f"{date} {time.strftime('%H:%M:%S')}"
                load = row[f"H{hour}"]
                if pd.isna(load):
                    continue
                load = RealLoadModel(
                    datetime=datetime_str,
                    load_MWh=float(load),
                    source="manual"
                )
                loads.append(load)
    except Exception as e:
        logging.error(f"Could not convert Excel data to loadCorrection objects: {e}")
        raise HTTPException(
            status_code=400, detail=str(e))
        # Write loads to the database
    try:
        await writeLoadsToDB(loc_id, loads)
    except Exception as e:
        logging.error(f"Could not write loads to the database: {e}")
        raise HTTPException(
            status_code=500, detail=str(e))

    return {"message": ["داده بار با موفقیت ثبت شد"]}
