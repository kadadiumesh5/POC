from datetime import date

from sqlalchemy.orm import Session

from app.db import Booking, Passenger
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository):
    model = Booking

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_pnr(self, pnr: str) -> Booking | None:
        return self.db.query(Booking).filter(Booking.pnr == pnr).first()

    def count_booked_seats(self, train_number: str, class_code: str, travel_date: date) -> int:
        bookings = (
            self.db.query(Booking)
            .filter(
                Booking.train_number == train_number,
                Booking.class_code == class_code.upper(),
                Booking.travel_date == travel_date,
                Booking.status != "CANCELLED",
            )
            .all()
        )
        return sum(len(b.passengers) for b in bookings)

    def next_seat_number(self, train_number: str, class_code: str, travel_date: date) -> int:
        return self.count_booked_seats(train_number, class_code, travel_date) + 1

    def list_recent(self, limit: int = 20) -> list[Booking]:
        return self.db.query(Booking).order_by(Booking.created_at.desc()).limit(limit).all()
