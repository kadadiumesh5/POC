"""Intent + slot extraction for the IRCTC booking agent.

Supports:
  - station codes (NDLS) OR multi-word city/station names
  - relative dates ("tomorrow", "day after tomorrow", "next monday")
  - any number of passengers: "for Umesh M 32, Priya F 28"
  - greetings, FAQ, fare enquiry, platform info, and general queries
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any


# --- Intent constants ---
INTENT_SEARCH = "search_trains"
INTENT_AVAILABILITY = "check_availability"
INTENT_BOOK = "book_ticket"
INTENT_CANCEL = "cancel_booking"
INTENT_GET = "get_booking"
INTENT_PNR_STATUS = "pnr_status"
INTENT_LIVE_STATUS = "live_status"
INTENT_FARE_ENQUIRY = "fare_enquiry"
INTENT_STATION_INFO = "station_info"
INTENT_TRAIN_INFO = "train_info"
INTENT_HELP = "help"
INTENT_GREETING = "greeting"
INTENT_FAQ = "faq"
INTENT_THANKS = "thanks"
INTENT_UNKNOWN = "unknown"


# --- Regex patterns ---
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

_STATION_PAIR_RE = re.compile(
    r"\bfrom\s+([A-Za-z][A-Za-z\s]*?)\s+to\s+([A-Za-z][A-Za-z\s]*?)"
    r"(?=\s+on\b|\s+in\b|\s+for\b|\s+at\b|\s*[,.]|\s+tomorrow|\s+today|\s+next|$)",
    re.I,
)

_STATION_PAIR_ALT_RE = re.compile(
    r"([A-Za-z][A-Za-z\s]*?)\s+to\s+([A-Za-z][A-Za-z\s]*?)"
    r"(?=\s+train|\s+on\b|\s+in\b|\s+for\b|\s+at\b|\s*[,.]|\s+tomorrow|\s+today|$)",
    re.I,
)

_TRAIN_NUMBER_RE = re.compile(r"\b(\d{5})\b")
_CLASS_RE = re.compile(r"\b(SL|1A|2A|3A|CC|EC|2S)\b", re.I)
_PNR_RE = re.compile(r"\b(?:pnr\s*)?(\d{10,})\b", re.I)

_PASSENGER_TOKEN_RE = re.compile(
    r"([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+)*)\s+(M|F|O)\s*/?\s*(\d{1,3})\b"
)

_DAY_NAMES = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}

# --- Keyword groups ---
_GREETING_KW = (
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    "namaste", "namaskar", "howdy", "greetings",
)

_THANKS_KW = (
    "thank", "thanks", "thank you", "dhanyawad", "shukriya", "appreciated",
)

_FAQ_PATTERNS = {
    "tatkal": "tatkal",
    "tatkal timing": "tatkal",
    "tatkal rules": "tatkal",
    "when does tatkal": "tatkal",
    "senior citizen": "senior_discount",
    "senior discount": "senior_discount",
    "child fare": "child_discount",
    "child discount": "child_discount",
    "children fare": "child_discount",
    "cancellation charge": "cancellation",
    "refund policy": "cancellation",
    "cancellation policy": "cancellation",
    "refund": "cancellation",
    "how to cancel": "cancellation",
    "rac": "rac_wl",
    "waiting list": "rac_wl",
    "waitlist": "rac_wl",
    "what is rac": "rac_wl",
    "what is wl": "rac_wl",
    "berth": "berth",
    "lower berth": "berth",
    "upper berth": "berth",
    "side lower": "berth",
    "berth preference": "berth",
    "id proof": "id_proof",
    "identity": "id_proof",
    "document": "id_proof",
    "e-ticket": "eticket",
    "e ticket": "eticket",
    "how to book": "how_to_book",
    "booking process": "how_to_book",
    "how do i book": "how_to_book",
    "payment": "payment",
    "payment method": "payment",
    "upi": "payment",
    "net banking": "payment",
    "food": "catering",
    "catering": "catering",
    "meal": "catering",
    "pantry": "catering",
    "e-catering": "catering",
    "platform": "platform_info",
    "which platform": "platform_info",
    "coach position": "platform_info",
    "luggage": "luggage",
    "baggage": "luggage",
    "luggage limit": "luggage",
}


@dataclass
class Intent:
    name: str
    slots: dict[str, Any] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)


def _extract_date(text: str) -> date | None:
    m = _DATE_RE.search(text)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass

    lowered = text.lower()
    today = date.today()

    if "today" in lowered:
        return today
    if "day after tomorrow" in lowered:
        return today + timedelta(days=2)
    if "tomorrow" in lowered:
        return today + timedelta(days=1)

    for day_name, weekday_num in _DAY_NAMES.items():
        pattern = rf"\bnext\s+{day_name}\b"
        if re.search(pattern, lowered):
            days_ahead = (weekday_num - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return today + timedelta(days=days_ahead)

    return None


def _extract_passengers(text: str) -> list[dict]:
    m = re.search(r"\bfor\b\s+(.+)", text, flags=re.I)
    segment = m.group(1) if m else text
    passengers = []
    for name, gender, age in _PASSENGER_TOKEN_RE.findall(segment):
        passengers.append({
            "name": name.strip().title(),
            "gender": gender.upper(),
            "age": int(age),
            "berth_preference": "NO_PREF",
        })
    return passengers


def _station_token(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_station_pair(text: str) -> tuple[str | None, str | None]:
    pair = _STATION_PAIR_RE.search(text)
    if pair:
        return _station_token(pair.group(1)), _station_token(pair.group(2))
    pair = _STATION_PAIR_ALT_RE.search(text)
    if pair:
        return _station_token(pair.group(1)), _station_token(pair.group(2))
    return None, None


def parse(text: str) -> Intent:
    lowered = text.lower().strip()

    # Greetings
    if any(lowered.startswith(kw) or lowered == kw for kw in _GREETING_KW):
        return Intent(INTENT_GREETING)

    # Thanks
    if any(kw in lowered for kw in _THANKS_KW):
        return Intent(INTENT_THANKS)

    # Help
    if any(kw in lowered for kw in ("help", "what can you do", "capabilities", "menu", "options")):
        return Intent(INTENT_HELP)

    # FAQ detection
    for pattern, faq_key in _FAQ_PATTERNS.items():
        if pattern in lowered:
            return Intent(INTENT_FAQ, {"faq_key": faq_key})

    # Cancel
    if "cancel" in lowered:
        pnr = _PNR_RE.search(text)
        slots = {"pnr": pnr.group(1)} if pnr else {}
        missing = [] if "pnr" in slots else ["pnr"]
        return Intent(INTENT_CANCEL, slots, missing)

    # PNR status
    if any(kw in lowered for kw in ("pnr status", "status of pnr", "check pnr", "pnr enquiry", "pnr inquiry")):
        pnr = _PNR_RE.search(text)
        slots = {"pnr": pnr.group(1)} if pnr else {}
        missing = [] if "pnr" in slots else ["pnr"]
        return Intent(INTENT_PNR_STATUS, slots, missing)

    # Live status
    if any(kw in lowered for kw in ("live status", "running status", "where is train", "live train", "train running")):
        train = _TRAIN_NUMBER_RE.search(text)
        slots = {"train_number": train.group(1)} if train else {}
        missing = [] if "train_number" in slots else ["train_number"]
        return Intent(INTENT_LIVE_STATUS, slots, missing)

    # Get/show booking
    if any(kw in lowered for kw in ("show pnr", "get pnr", "show booking", "my booking", "booking details")):
        pnr = _PNR_RE.search(text)
        slots = {"pnr": pnr.group(1)} if pnr else {}
        missing = [] if "pnr" in slots else ["pnr"]
        return Intent(INTENT_GET, slots, missing)

    # Fare enquiry
    if any(kw in lowered for kw in ("fare", "price", "cost", "how much", "ticket price", "ticket cost")):
        slots: dict[str, Any] = {}
        missing: list[str] = []
        train = _TRAIN_NUMBER_RE.search(text)
        if train:
            slots["train_number"] = train.group(1)
        else:
            missing.append("train_number")
        cls = _CLASS_RE.search(text)
        if cls:
            slots["class_code"] = cls.group(1).upper()
        else:
            missing.append("class_code")
        return Intent(INTENT_FARE_ENQUIRY, slots, missing)

    # Station info
    if any(kw in lowered for kw in ("station code", "station info", "stations in", "which station", "list stations")):
        return Intent(INTENT_STATION_INFO, {"query": text})

    # Train info
    if any(kw in lowered for kw in ("train info", "train details", "about train", "train schedule", "train route")):
        train = _TRAIN_NUMBER_RE.search(text)
        slots = {"train_number": train.group(1)} if train else {}
        missing = [] if "train_number" in slots else ["train_number"]
        return Intent(INTENT_TRAIN_INFO, slots, missing)

    # Book ticket
    if "book" in lowered:
        slots = {}
        missing = []

        src, dst = _extract_station_pair(text)
        if src and dst:
            slots["source"] = src
            slots["destination"] = dst
        else:
            missing.extend(["source", "destination"])

        train = _TRAIN_NUMBER_RE.search(text)
        if train:
            slots["train_number"] = train.group(1)
        else:
            missing.append("train_number")

        cls = _CLASS_RE.search(text)
        slots["class_code"] = cls.group(1).upper() if cls else "SL"

        travel = _extract_date(text)
        if travel:
            slots["travel_date"] = travel
        else:
            missing.append("travel_date")

        passengers = _extract_passengers(text)
        if passengers:
            slots["passengers"] = passengers
        else:
            missing.append("passenger")

        return Intent(INTENT_BOOK, slots, missing)

    # Availability
    if any(kw in lowered for kw in ("availability", "available", "seats left", "is seat", "seat available", "vacant")):
        slots = {}
        missing = []
        train = _TRAIN_NUMBER_RE.search(text)
        if train:
            slots["train_number"] = train.group(1)
        else:
            missing.append("train_number")
        cls = _CLASS_RE.search(text)
        slots["class_code"] = cls.group(1).upper() if cls else "SL"
        travel = _extract_date(text)
        if travel:
            slots["travel_date"] = travel
        else:
            missing.append("travel_date")
        return Intent(INTENT_AVAILABILITY, slots, missing)

    # Search trains — broader keyword matching
    if any(kw in lowered for kw in (
        "find train", "search train", "trains from", "find trains", "trains between",
        "show trains", "train from", "trains to", "trains on", "which train",
        "any train", "direct train",
    )):
        slots = {}
        missing = []
        src, dst = _extract_station_pair(text)
        if src and dst:
            slots["source"] = src
            slots["destination"] = dst
        else:
            missing.extend(["source", "destination"])
        travel = _extract_date(text)
        if travel:
            slots["travel_date"] = travel
        else:
            missing.append("travel_date")
        return Intent(INTENT_SEARCH, slots, missing)

    # Fallback: if there's a station pair, treat it as a search
    src, dst = _extract_station_pair(text)
    if src and dst:
        slots = {"source": src, "destination": dst}
        travel = _extract_date(text)
        if travel:
            slots["travel_date"] = travel
            missing = []
        else:
            missing = ["travel_date"]
        return Intent(INTENT_SEARCH, slots, missing)

    # Bare PNR number
    pnr = _PNR_RE.search(text)
    if pnr and len(text.strip()) <= 15:
        return Intent(INTENT_PNR_STATUS, {"pnr": pnr.group(1)}, [])

    return Intent(INTENT_UNKNOWN)
