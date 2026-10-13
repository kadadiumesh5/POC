from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent import BookingAgent
from app.agent.session import store as session_store
from app.db import get_db
from app.exceptions import PlatformError
from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentHistoryResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
def chat(payload: AgentChatRequest, db: Session = Depends(get_db)):
    try:
        response = BookingAgent(db).chat(payload.message, payload.session_id)
        response.suggestions = _get_suggestions(response.intent)
        return response
    except PlatformError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/history/{session_id}", response_model=AgentHistoryResponse)
def get_history(session_id: str):
    session = session_store.get(session_id)
    return AgentHistoryResponse(
        session_id=session_id,
        messages=session.get_history_dicts(),
        slots=session.slots,
    )


def _get_suggestions(intent: str) -> list[str]:
    """Return contextual quick-action suggestions based on the current intent."""
    suggestions_map = {
        "greeting": [
            "Search trains",
            "Check PNR status",
            "Tatkal rules",
            "Help",
        ],
        "help": [
            "Trains from Delhi to Mumbai",
            "Check PNR status",
            "Cancellation policy",
            "Senior citizen discount",
        ],
        "search_trains": [
            "Check availability",
            "Book ticket",
            "Show another route",
        ],
        "check_availability": [
            "Book this train",
            "Check another class",
            "Search more trains",
        ],
        "book_ticket": [
            "Check PNR status",
            "Book another ticket",
            "My bookings",
        ],
        "cancel_booking": [
            "Check PNR status",
            "Book new ticket",
            "Refund policy",
        ],
        "pnr_status": [
            "Cancel booking",
            "Book another ticket",
            "Search trains",
        ],
        "faq": [
            "Tatkal rules",
            "Cancellation policy",
            "Berth types",
            "Search trains",
        ],
        "unknown": [
            "Help",
            "Search trains",
            "Check PNR",
            "Tatkal rules",
        ],
    }
    return suggestions_map.get(intent, ["Help", "Search trains", "PNR status"])
