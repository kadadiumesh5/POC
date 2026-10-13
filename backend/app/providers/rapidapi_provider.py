"""RapidAPI-style IRCTC provider.

Reads train / station / PNR data from a third-party HTTP API that follows the
`irctc1.p.rapidapi.com` family of endpoints (there are several providers on
RapidAPI with very similar shapes — `IRCTC`, `IRCTC1`, `IndianRailways`, etc.).

The URL paths are configurable so swapping between providers is just env vars.

Required env vars:
    IRCTC_PROVIDER=rapidapi
    IRCTC_API_HOST=irctc1.p.rapidapi.com
    IRCTC_API_KEY=<your rapidapi key>

Optional overrides for path templates:
    IRCTC_PATH_SEARCH_STATIONS   default: /api/v1/searchStation?query={query}
    IRCTC_PATH_SEARCH_TRAINS     default: /api/v3/trainBetweenStations?fromStationCode={src}&toStationCode={dst}&dateOfJourney={date}
    IRCTC_PATH_AVAILABILITY      default: /api/v1/checkSeatAvailability?classType={cls}&fromStationCode={src}&quota=GN&toStationCode={dst}&trainNo={train}&date={date}
    IRCTC_PATH_PNR               default: /api/v3/getPNRStatus?pnrNumber={pnr}
    IRCTC_PATH_LIVE_STATUS       default: /api/v1/liveTrainStatus?trainNo={train}&startDay=1
"""

from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any

import httpx

from app.providers.base import ProviderUnavailable, TrainDataProvider


logger = logging.getLogger("irctc-platform.rapidapi")


class RapidAPIProvider(TrainDataProvider):
    name = "rapidapi"

    def __init__(self):
        self.host = os.getenv("IRCTC_API_HOST", "irctc1.p.rapidapi.com")
        self.key = os.getenv("IRCTC_API_KEY", "")
        if not self.key:
            raise ProviderUnavailable("IRCTC_API_KEY not configured")

        self.base_url = f"https://{self.host}"
        self.timeout = float(os.getenv("IRCTC_API_TIMEOUT", "10"))

        self.p_stations = os.getenv(
            "IRCTC_PATH_SEARCH_STATIONS",
            "/api/v1/searchStation?query={query}",
        )
        self.p_trains = os.getenv(
            "IRCTC_PATH_SEARCH_TRAINS",
            "/api/v3/trainBetweenStations?fromStationCode={src}&toStationCode={dst}&dateOfJourney={date}",
        )
        self.p_avail = os.getenv(
            "IRCTC_PATH_AVAILABILITY",
            "/api/v1/checkSeatAvailability?classType={cls}&fromStationCode={src}&quota=GN&toStationCode={dst}&trainNo={train}&date={date}",
        )
        self.p_pnr = os.getenv(
            "IRCTC_PATH_PNR",
            "/api/v3/getPNRStatus?pnrNumber={pnr}",
        )
        self.p_live = os.getenv(
            "IRCTC_PATH_LIVE_STATUS",
            "/api/v1/liveTrainStatus?trainNo={train}&startDay=1",
        )

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------
    def _get(self, path: str) -> dict:
        url = self.base_url + path
        headers = {
            "x-rapidapi-key": self.key,
            "x-rapidapi-host": self.host,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            logger.warning("rapidapi call failed path=%s err=%s", path, exc)
            raise ProviderUnavailable(f"Upstream IRCTC API error: {exc}") from exc

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def search_stations(self, query: str) -> list[dict]:
        body = self._get(self.p_stations.format(query=query))
        data = _extract_list(body)
        return [
            {
                "code": item.get("stationCode") or item.get("code"),
                "name": item.get("stationName") or item.get("name"),
                "city": item.get("city") or item.get("stationCity") or "",
            }
            for item in data
        ]

    def search_trains(self, source_code: str, destination_code: str, travel_date: date) -> list[dict]:
        body = self._get(
            self.p_trains.format(src=source_code, dst=destination_code, date=travel_date.strftime("%Y-%m-%d"))
        )
        data = _extract_list(body)
        return [
            {
                "number": str(t.get("train_number") or t.get("trainNumber") or t.get("trainNo") or ""),
                "name": t.get("train_name") or t.get("trainName") or "",
                "source_code": t.get("from_station_code") or source_code,
                "destination_code": t.get("to_station_code") or destination_code,
                "departure_time": (t.get("from_std") or t.get("departureTime") or "")[:5],
                "arrival_time": (t.get("to_sta") or t.get("arrivalTime") or "")[:5],
                "duration_minutes": _parse_duration(t.get("duration") or t.get("travelTime")),
            }
            for t in data
        ]

    def check_availability(self, train_number: str, class_code: str, travel_date: date) -> dict:
        body = self._get(
            self.p_avail.format(
                train=train_number, cls=class_code,
                src=os.getenv("IRCTC_DEFAULT_FROM", ""),
                dst=os.getenv("IRCTC_DEFAULT_TO", ""),
                date=travel_date.strftime("%Y-%m-%d"),
            )
        )
        data = _extract_dict(body)
        return {
            "train_number": train_number,
            "class_code": class_code,
            "travel_date": travel_date,
            "status": data.get("availabilityStatus") or data.get("status") or "UNKNOWN",
            "available": _parse_int(data.get("availableSeats") or data.get("confirmTktStatus")),
            "fare": _parse_float(data.get("fare") or data.get("totalFare")),
            "raw": data,
        }

    def pnr_status(self, pnr: str) -> dict:
        body = self._get(self.p_pnr.format(pnr=pnr))
        data = _extract_dict(body)
        return {
            "pnr": pnr,
            "status": data.get("bookingStatus") or data.get("ReservationStatus") or "UNKNOWN",
            "train_number": data.get("trainNumber") or data.get("TrainNo"),
            "travel_date": data.get("dateOfJourney") or data.get("Doj"),
            "source_code": data.get("boardingPoint") or data.get("From"),
            "destination_code": data.get("reservationUpto") or data.get("To"),
            "class_code": data.get("journeyClass") or data.get("Class"),
            "passengers": data.get("passengerList") or data.get("Passengers") or [],
            "raw": data,
        }

    def live_status(self, train_number: str) -> dict:
        return self._get(self.p_live.format(train=train_number))


# ---- helpers ----------------------------------------------------------

def _extract_list(body: Any) -> list[dict]:
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for key in ("data", "result", "trains", "stations"):
            v = body.get(key)
            if isinstance(v, list):
                return v
        if isinstance(body.get("data"), dict):
            for key in ("trains", "stations", "list"):
                v = body["data"].get(key)
                if isinstance(v, list):
                    return v
    return []


def _extract_dict(body: Any) -> dict:
    if isinstance(body, dict):
        if isinstance(body.get("data"), dict):
            return body["data"]
        return body
    return {}


def _parse_duration(value: Any) -> int:
    if not value:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).lower().replace("hrs", "h").replace("min", "m")
    hours = minutes = 0
    import re
    h = re.search(r"(\d+)\s*h", s)
    m = re.search(r"(\d+)\s*m", s)
    if h:
        hours = int(h.group(1))
    if m:
        minutes = int(m.group(1))
    if not hours and not minutes and ":" in s:
        parts = s.split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
    return hours * 60 + minutes


def _parse_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _parse_float(value: Any) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0
