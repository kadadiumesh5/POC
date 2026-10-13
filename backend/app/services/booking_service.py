from datetime import date, datetime
from itertools import count
from threading import Lock

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Booking, Passenger
from app.exceptions import ConflictError, NotFoundError, ValidationFailure
from app.repositories.booking_repository import BookingRepository
from app.repositories.train_repository import TrainRepository
from app.services.payment_service import PaymentService
from app.services.train_service import TrainService


_pnr_counter: count | None = None
_pnr_lock = Lock()


def _next_pnr(db: Session) -> str:
    global _pnr_counter
    with _pnr_lock:
        if _pnr_counter is None:
            max_pnr = db.query(func.max(Booking.pnr)).scalar()
            start = max(int(max_pnr) if max_pnr else 0, settings.pnr_seed)
            _pnr_counter = count(start + 1)
        return str(next(_pnr_counter))


# Simple age-based fare multipliers.
_AGE_DISCOUNT = {"child": 0.5, "senior": 0.6}


def _fare_for(age: int, base_fare: float) -> float:
    if age < 12:
        return round(base_fare * _AGE_DISCOUNT["child"], 2)
    if age >= 60:
        return round(base_fare * _AGE_DISCOUNT["senior"], 2)
    return base_fare


class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BookingRepository(db)
        self.trains = TrainRepository(db)
        self.train_service = TrainService(db)
        self.payments = PaymentService()

    def _validate_route(self, train_number: str, source: str, destination: str) -> tuple[str, str]:
        train = self.trains.get_train(train_number)
        if train is None:
            raise NotFoundError(f"Train {train_number} not found")
        src_candidates = self.train_service.resolve_station_codes(source)
        dst_candidates = self.train_service.resolve_station_codes(destination)
        if train.source_code not in src_candidates or train.destination_code not in dst_candidates:
            raise ValidationFailure(
                f"Train {train_number} runs {train.source_code} → {train.destination_code}, "
                f"not {source} → {destination}"
            )
        return train.source_code, train.destination_code

    def book(self, data) -> Booking:
        if data.travel_date < date.today():
            raise ValidationFailure("Travel date is in the past")

        src, dst = self._validate_route(data.train_number, data.source, data.destination)

        availability = self.train_service.check_availability(
            data.train_number, data.class_code, data.travel_date
        )

        requested = len(data.passengers)
        if availability["available"] < requested:
            raise ConflictError(
                f"Only {availability['available']} seats available in {data.class_code} "
                f"on {data.train_number} for {data.travel_date}"
            )

        total_fare = round(sum(_fare_for(p.age, availability["fare"]) for p in data.passengers), 2)
        pnr = _next_pnr(self.db)

        booking = Booking(
            pnr=pnr,
            train_number=data.train_number,
            source_code=src,
            destination_code=dst,
            travel_date=data.travel_date,
            class_code=data.class_code.upper(),
            total_fare=total_fare,
            status="CONFIRMED",
            payment_status="PAID",
        )
        next_seat = self.repo.next_seat_number(data.train_number, data.class_code, data.travel_date)
        for index, p in enumerate(data.passengers):
            booking.passengers.append(
                Passenger(
                    name=p.name,
                    age=p.age,
                    gender=p.gender,
                    berth_preference=p.berth_preference,
                    seat_number=f"{data.class_code.upper()}-{next_seat + index}",
                    status="CNF",
                )
            )

        self.repo.add(booking)
        self.payments.charge(total_fare, pnr)
        return booking

    def get(self, pnr: str) -> Booking:
        booking = self.repo.get_by_pnr(pnr)
        if booking is None:
            raise NotFoundError(f"PNR {pnr} not found")
        return booking

    def cancel(self, pnr: str) -> dict:
        booking = self.get(pnr)
        if booking.status == "CANCELLED":
            raise ConflictError(f"PNR {pnr} is already cancelled")

        refund_pct = self._refund_percent(booking.travel_date)
        refund = round(booking.total_fare * refund_pct, 2)

        booking.status = "CANCELLED"
        booking.payment_status = "REFUNDED"
        for p in booking.passengers:
            p.status = "CAN"
        self.db.commit()
        self.payments.refund(refund, booking.pnr)

        return {"pnr": pnr, "status": "CANCELLED", "refund_amount": refund}

    @staticmethod
    def _refund_percent(travel_date: date) -> float:
        hours_to_go = (datetime.combine(travel_date, datetime.min.time()) - datetime.now()).total_seconds() / 3600
        if hours_to_go > 48:
            return 0.9
        if hours_to_go > 12:
            return 0.5
        if hours_to_go > 4:
            return 0.25
        return 0.0

    def recent(self, limit: int = 20):
        return self.repo.list_recent(limit)
