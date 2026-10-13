"""Thin tool wrappers that the BookingAgent calls into.

Each tool is a pure function receiving services + validated inputs, so tools stay
decoupled from how the agent interprets user text.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.providers import build_provider
from app.schemas.booking import BookingCreate, PassengerIn
from app.services.booking_service import BookingService
from app.services.train_service import TrainService


def tool_search_trains(db: Session, source: str, destination: str, travel_date: date):
    return TrainService(db).search(source, destination, travel_date)


def tool_check_availability(db: Session, train_number: str, class_code: str, travel_date: date):
    return TrainService(db).check_availability(train_number, class_code, travel_date)


def tool_book_ticket(
    db: Session,
    train_number: str,
    source: str,
    destination: str,
    travel_date: date,
    class_code: str,
    passengers: list[dict],
):
    payload = BookingCreate(
        train_number=train_number,
        source=source,
        destination=destination,
        travel_date=travel_date,
        class_code=class_code,
        passengers=[PassengerIn(**p) for p in passengers],
    )
    return BookingService(db).book(payload)


def tool_cancel_booking(db: Session, pnr: str):
    return BookingService(db).cancel(pnr)


def tool_get_booking(db: Session, pnr: str):
    return BookingService(db).get(pnr)


# ---- provider-backed tools (local DB OR remote IRCTC API via env) ----

def tool_pnr_status(db: Session, pnr: str) -> dict:
    """Fetches PNR status. Uses live IRCTC API if configured, else local DB."""
    return build_provider(db).pnr_status(pnr)


def tool_live_status(db: Session, train_number: str) -> dict:
    """Live running status — remote-only; returns a hint if provider is local."""
    return build_provider(db).live_status(train_number)
