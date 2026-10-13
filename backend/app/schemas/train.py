from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StationOut(ORMModel):
    code: str
    name: str
    city: str


class CoachOut(ORMModel):
    class_code: str
    total_seats: int
    base_fare: float


class TrainOut(ORMModel):
    number: str
    name: str
    source_code: str
    destination_code: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    runs_on: str


class TrainSearchRequest(BaseModel):
    source: str = Field(min_length=2, max_length=10)
    destination: str = Field(min_length=2, max_length=10)
    travel_date: date


class AvailabilityOut(BaseModel):
    train_number: str
    class_code: str
    travel_date: date
    total_seats: int
    booked: int
    available: int
    status: str  # AVAILABLE / RAC / WL / NOT_FOUND
    fare: float
