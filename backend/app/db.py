from datetime import date

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Float, func, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

from app.config import settings

Base = declarative_base()
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)


class Train(Base):
    __tablename__ = "trains"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    source_code = Column(String(10), nullable=False, index=True)
    destination_code = Column(String(10), nullable=False, index=True)
    departure_time = Column(String(5), nullable=False)   # HH:MM
    arrival_time = Column(String(5), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    runs_on = Column(String(20), default="MTWTFSS")      # which weekdays


class Coach(Base):
    __tablename__ = "coaches"
    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String(10), ForeignKey("trains.number"), nullable=False, index=True)
    class_code = Column(String(5), nullable=False)       # SL, 3A, 2A, 1A, CC
    total_seats = Column(Integer, nullable=False)
    base_fare = Column(Float, nullable=False)


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    pnr = Column(String(15), unique=True, index=True, nullable=False)
    train_number = Column(String(10), nullable=False, index=True)
    source_code = Column(String(10), nullable=False)
    destination_code = Column(String(10), nullable=False)
    travel_date = Column(Date, nullable=False, index=True)
    class_code = Column(String(5), nullable=False)
    total_fare = Column(Float, nullable=False)
    status = Column(String(20), default="CONFIRMED")      # CONFIRMED, RAC, WL, CANCELLED
    payment_status = Column(String(20), default="PAID")   # PAID, REFUNDED, PENDING
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    passengers = relationship("Passenger", back_populates="booking", cascade="all, delete-orphan")


class Passenger(Base):
    __tablename__ = "passengers"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(1), nullable=False)            # M, F, O
    berth_preference = Column(String(10), default="NO_PREF")
    seat_number = Column(String(10), nullable=True)
    status = Column(String(10), default="CNF")            # CNF, RAC, WL, CAN

    booking = relationship("Booking", back_populates="passengers")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    phone = Column(String(15), nullable=True)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


Index("ix_bookings_train_date", Booking.train_number, Booking.travel_date, Booking.class_code)


Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
