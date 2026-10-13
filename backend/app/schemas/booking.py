from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PassengerIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    age: int = Field(ge=1, le=120)
    gender: Literal["M", "F", "O"]
    berth_preference: Literal["LOWER", "MIDDLE", "UPPER", "SIDE_LOWER", "SIDE_UPPER", "NO_PREF"] = "NO_PREF"


class PassengerOut(ORMModel):
    name: str
    age: int
    gender: str
    berth_preference: str
    seat_number: str | None
    status: str


class BookingCreate(BaseModel):
    train_number: str = Field(min_length=1, max_length=10)
    source: str = Field(min_length=2, max_length=10)
    destination: str = Field(min_length=2, max_length=10)
    travel_date: date
    class_code: Literal["SL", "3A", "2A", "1A", "CC"]
    passengers: list[PassengerIn] = Field(min_length=1, max_length=6)


class BookingOut(ORMModel):
    pnr: str
    train_number: str
    source_code: str
    destination_code: str
    travel_date: date
    class_code: str
    total_fare: float
    status: str
    payment_status: str
    created_at: datetime
    passengers: list[PassengerOut]


class CancelOut(BaseModel):
    pnr: str
    status: str
    refund_amount: float
