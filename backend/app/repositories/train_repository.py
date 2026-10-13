from datetime import date

from sqlalchemy.orm import Session

from app.db import Coach, Station, Train
from app.repositories.base import BaseRepository


WEEKDAY_LETTERS = "MTWTFSS"


# Historical / alternate names for Indian cities — maps to canonical city label
# used in the Station table. Lowercased on both sides for case-insensitive match.
CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru city": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "trivandrum": "Thiruvananthapuram",
    "cochin": "Kochi",
    "mysore": "Mysuru",
    "mangalore": "Mangaluru",
    "poona": "Pune",
    "baroda": "Vadodara",
    "allahabad": "Prayagraj",
    "banaras": "Varanasi",
    "benares": "Varanasi",
    "waltair": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "gauhati": "Guwahati",
    "secunderabad": "Hyderabad",
    "new delhi": "Delhi",
}


class TrainRepository(BaseRepository):
    model = Train

    def __init__(self, db: Session):
        super().__init__(db)

    def list_stations(self) -> list[Station]:
        return self.db.query(Station).order_by(Station.code).all()

    def get_station(self, code: str) -> Station | None:
        return self.db.query(Station).filter(Station.code == code.upper()).first()

    def resolve_station(self, token: str) -> Station | None:
        """Resolve a user token (code, station name, or city) to a Station.

        Matching order: exact code → exact city (case-insensitive) → exact station
        name → startswith on city → startswith on station name. Returns None if
        no match or ambiguous (multiple cities match the prefix).
        """
        if not token:
            return None
        value = token.strip()
        upper = value.upper()
        canonical = CITY_ALIASES.get(value.lower(), value)

        exact_code = self.db.query(Station).filter(Station.code == upper).first()
        if exact_code:
            return exact_code

        from sqlalchemy import func
        exact_city = (
            self.db.query(Station).filter(func.lower(Station.city) == canonical.lower()).all()
        )
        if len(exact_city) == 1:
            return exact_city[0]
        if len(exact_city) > 1:
            return exact_city[0]

        exact_name = (
            self.db.query(Station).filter(func.lower(Station.name) == canonical.lower()).first()
        )
        if exact_name:
            return exact_name

        like = f"{canonical.lower()}%"
        prefix_city = (
            self.db.query(Station).filter(func.lower(Station.city).like(like)).all()
        )
        if len(prefix_city) == 1:
            return prefix_city[0]

        prefix_name = (
            self.db.query(Station).filter(func.lower(Station.name).like(like)).first()
        )
        return prefix_name

    def get_train(self, number: str) -> Train | None:
        return self.db.query(Train).filter(Train.number == number).first()

    def search(
        self,
        source_codes: list[str],
        destination_codes: list[str],
        travel_date: date,
    ) -> list[Train]:
        day_letter = WEEKDAY_LETTERS[travel_date.weekday()]
        src = [c.upper() for c in source_codes]
        dst = [c.upper() for c in destination_codes]
        query = (
            self.db.query(Train)
            .filter(Train.source_code.in_(src))
            .filter(Train.destination_code.in_(dst))
        )
        return [t for t in query.all() if day_letter in t.runs_on]

    def stations_for_city(self, city: str) -> list[Station]:
        from sqlalchemy import func
        return self.db.query(Station).filter(func.lower(Station.city) == city.lower()).all()

    def get_coach(self, train_number: str, class_code: str) -> Coach | None:
        return (
            self.db.query(Coach)
            .filter(Coach.train_number == train_number, Coach.class_code == class_code.upper())
            .first()
        )

    def list_coaches(self, train_number: str) -> list[Coach]:
        return self.db.query(Coach).filter(Coach.train_number == train_number).all()
