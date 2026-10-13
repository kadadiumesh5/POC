from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.exceptions import PlatformError
from app.schemas.booking import BookingCreate, BookingOut, CancelOut
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    try:
        return BookingService(db).book(payload)
    except PlatformError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{pnr}", response_model=BookingOut)
def get_booking(pnr: str, db: Session = Depends(get_db)):
    try:
        return BookingService(db).get(pnr)
    except PlatformError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/{pnr}/cancel", response_model=CancelOut)
def cancel_booking(pnr: str, db: Session = Depends(get_db)):
    try:
        return BookingService(db).cancel(pnr)
    except PlatformError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("", response_model=list[BookingOut])
def list_recent(limit: int = 20, db: Session = Depends(get_db)):
    return BookingService(db).recent(limit)
