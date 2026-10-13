"""Local provider — backed by the SQLite seed data."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.providers.base import TrainDataProvider
from app.repositories.booking_repository import BookingRepository
from app.repositories.train_repository import TrainRepository


class LocalProvider(TrainDataProvider):
    name = "local"

    def __init__(self, db: Session):
        self.trains = TrainRepository(db)
        self.bookings = BookingRepository(db)

    def search_stations(self, query: str) -> list[dict]:
        station = self.trains.resolve_station(query)
        return [{"code": station.code, "name": station.name, "city": station.city}] if station else []

    def search_trains(self, source_code: str, destination_code: str, travel_date: date) -> list[dict]:
        trains = self.trains.search([source_code], [destination_code], travel_date)
        return [
            {
                "number": t.number,
                "name": t.name,
                "source_code": t.source_code,
                "destination_code": t.destination_code,
                "departure_time": t.departure_time,
                "arrival_time": t.arrival_time,
                "duration_minutes": t.duration_minutes,
            }
            for t in trains
        ]

    def check_availability(self, train_number: str, class_code: str, travel_date: date) -> dict:
        coach = self.trains.get_coach(train_number, class_code)
        if coach is None:
            return {"train_number": train_number, "class_code": class_code, "available": 0, "status": "NOT_FOUND"}
        booked = self.bookings.count_booked_seats(train_number, class_code, travel_date)
        return {
            "train_number": train_number,
            "class_code": class_code.upper(),
            "travel_date": travel_date,
            "total_seats": coach.total_seats,
            "booked": booked,
            "available": max(coach.total_seats - booked, 0),
            "fare": coach.base_fare,
            "status": "AVAILABLE" if coach.total_seats - booked > 0 else "WL",
        }

    def pnr_status(self, pnr: str) -> dict:
        booking = self.bookings.get_by_pnr(pnr)
        if booking is None:
            return {"pnr": pnr, "status": "NOT_FOUND"}
        return {
            "pnr": booking.pnr,
            "status": booking.status,
            "train_number": booking.train_number,
            "travel_date": booking.travel_date.isoformat(),
            "source_code": booking.source_code,
            "destination_code": booking.destination_code,
            "class_code": booking.class_code,
            "passengers": [
                {"name": p.name, "age": p.age, "seat": p.seat_number, "status": p.status}
                for p in booking.passengers
            ],
        }
