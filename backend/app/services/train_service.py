from datetime import date

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.repositories.booking_repository import BookingRepository
from app.repositories.train_repository import TrainRepository


class TrainService:
    def __init__(self, db: Session):
        self.db = db
        self.trains = TrainRepository(db)
        self.bookings = BookingRepository(db)

    def list_stations(self):
        return self.trains.list_stations()

    def resolve_station_code(self, token: str) -> str:
        """Accept a code / city / station name and return the canonical station code."""
        station = self.trains.resolve_station(token)
        if station is None:
            raise NotFoundError(f"Station '{token}' not found")
        return station.code

    def resolve_station_codes(self, token: str) -> list[str]:
        """Return ALL station codes for a given token.

        If the token names a city with multiple stations (e.g. "Mumbai" → BCT, CSMT),
        return all of them. Falls back to a single code via `resolve_station_code`.
        """
        anchor = self.trains.resolve_station(token)
        if anchor is None:
            raise NotFoundError(f"Station '{token}' not found")
        city_stations = self.trains.stations_for_city(anchor.city)
        codes = sorted({s.code for s in city_stations} | {anchor.code})
        return codes

    def search(self, source: str, destination: str, travel_date: date):
        src = self.resolve_station_codes(source)
        dst = self.resolve_station_codes(destination)
        return self.trains.search(src, dst, travel_date)

    def check_availability(self, train_number: str, class_code: str, travel_date: date):
        train = self.trains.get_train(train_number)
        if train is None:
            raise NotFoundError(f"Train {train_number} not found")

        coach = self.trains.get_coach(train_number, class_code)
        if coach is None:
            raise NotFoundError(f"Class {class_code} not offered on train {train_number}")

        booked = self.bookings.count_booked_seats(train_number, class_code, travel_date)
        available = max(coach.total_seats - booked, 0)

        if available > 0:
            status = "AVAILABLE"
        elif booked - coach.total_seats < 10:
            status = "RAC"
        else:
            status = "WL"

        return {
            "train_number": train_number,
            "class_code": class_code.upper(),
            "travel_date": travel_date,
            "total_seats": coach.total_seats,
            "booked": booked,
            "available": available,
            "status": status,
            "fare": coach.base_fare,
        }
