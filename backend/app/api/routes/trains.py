from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.exceptions import PlatformError
from app.schemas.train import AvailabilityOut, StationOut, TrainOut
from app.services.train_service import TrainService

router = APIRouter(prefix="/trains", tags=["trains"])


@router.get("/stations", response_model=list[StationOut])
def list_stations(db: Session = Depends(get_db)):
    return TrainService(db).list_stations()


@router.get("/search", response_model=list[TrainOut])
def search(
    source: str = Query(..., min_length=2, max_length=10),
    destination: str = Query(..., min_length=2, max_length=10),
    travel_date: date = Query(...),
    db: Session = Depends(get_db),
):
    try:
        return TrainService(db).search(source, destination, travel_date)
    except PlatformError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{train_number}/availability", response_model=AvailabilityOut)
def availability(
    train_number: str,
    class_code: str = Query(..., min_length=2, max_length=5),
    travel_date: date = Query(...),
    db: Session = Depends(get_db),
):
    try:
        return TrainService(db).check_availability(train_number, class_code, travel_date)
    except PlatformError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
