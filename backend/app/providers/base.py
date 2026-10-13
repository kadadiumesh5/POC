"""Abstract train-data provider interface.

Lets the agent + services talk to either the local SQLite seed or a real
third-party IRCTC-style API (RapidAPI aggregators, erail scrapers, etc.)
without changing business logic.

NOTE on real IRCTC: there is NO official public booking API. The real world
offers only READ-ONLY endpoints — schedule, availability, PNR status, live
status, station search. Booking has to stay local (or go through a licensed
B2B partner contract). The interface reflects that: `book_ticket` and
`cancel_booking` are not part of this provider; those stay in the DB-backed
BookingService.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class ProviderUnavailable(Exception):
    """Raised when a remote provider is unreachable / misconfigured."""


class TrainDataProvider(ABC):
    """Read-only train data source."""

    name: str = "abstract"

    @abstractmethod
    def search_stations(self, query: str) -> list[dict]:
        """Return [{code, name, city}, ...] matching the query."""

    @abstractmethod
    def search_trains(self, source_code: str, destination_code: str, travel_date: date) -> list[dict]:
        """Return trains between source and destination codes."""

    @abstractmethod
    def check_availability(self, train_number: str, class_code: str, travel_date: date) -> dict:
        """Return seat availability for a train/class/date."""

    @abstractmethod
    def pnr_status(self, pnr: str) -> dict:
        """Return current status of a PNR."""

    def live_status(self, train_number: str) -> dict:
        """Optional: current live running status. Default = not implemented."""
        raise ProviderUnavailable(f"{self.name} does not support live status")
