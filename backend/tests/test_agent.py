from datetime import date, timedelta

import pytest

from app.agent import BookingAgent
from app.agent import intents
from app.db import SessionLocal
from app.seed import seed


@pytest.fixture(scope="module")
def db():
    seed()
    session = SessionLocal()
    yield session
    session.close()


def test_help(db):
    reply = BookingAgent(db).chat("help")
    assert reply.intent == intents.INTENT_HELP
    assert "find trains" in reply.reply


def test_search(db):
    future = (date.today() + timedelta(days=30)).isoformat()
    reply = BookingAgent(db).chat(f"find trains from NDLS to BCT on {future}")
    assert reply.intent == intents.INTENT_SEARCH
    assert any(t["number"] == "12951" for t in reply.data)


def test_availability_then_book_then_cancel(db):
    future = (date.today() + timedelta(days=30)).isoformat()

    av = BookingAgent(db).chat(f"availability on 12951 in 3A on {future}")
    assert av.intent == intents.INTENT_AVAILABILITY
    assert av.data["status"] in {"AVAILABLE", "RAC", "WL"}

    booking = BookingAgent(db).chat(
        f"book 12951 from NDLS to BCT on {future} in 3A for Alice F 28"
    )
    assert booking.intent == intents.INTENT_BOOK
    pnr = booking.data["pnr"]

    show = BookingAgent(db).chat(f"show PNR {pnr}")
    assert show.data["pnr"] == pnr

    cancel = BookingAgent(db).chat(f"cancel PNR {pnr}")
    assert cancel.data["status"] == "CANCELLED"


def test_missing_slots(db):
    reply = BookingAgent(db).chat("book a train please")
    assert reply.intent == intents.INTENT_BOOK
    assert "travel_date" in reply.data["missing"]
