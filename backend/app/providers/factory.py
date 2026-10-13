"""Provider factory — picks local vs remote based on env.

Falls back to local on any remote-provider construction failure, so running
without a RapidAPI key just works for the demo.
"""

from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session

from app.providers.base import ProviderUnavailable, TrainDataProvider
from app.providers.local_provider import LocalProvider

logger = logging.getLogger("irctc-platform.providers")


def build_provider(db: Session) -> TrainDataProvider:
    choice = os.getenv("IRCTC_PROVIDER", "local").lower()
    if choice == "rapidapi":
        try:
            from app.providers.rapidapi_provider import RapidAPIProvider
            return RapidAPIProvider()
        except ProviderUnavailable as exc:
            logger.warning("falling back to local provider: %s", exc)
    return LocalProvider(db)
