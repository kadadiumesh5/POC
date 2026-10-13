import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.providers import build_provider

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
def active_provider(db: Session = Depends(get_db)):
    provider = build_provider(db)
    return {
        "active": provider.name,
        "configured_choice": os.getenv("IRCTC_PROVIDER", "local"),
        "has_api_key": bool(os.getenv("IRCTC_API_KEY")),
        "api_host": os.getenv("IRCTC_API_HOST", ""),
    }
