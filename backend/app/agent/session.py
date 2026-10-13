"""Per-session slot store and conversation history for the booking agent.

Tracks remembered slots (source, destination, train_number, etc.) and
maintains a message history for contextual follow-ups.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any


_REMEMBERED_KEYS = {
    "source",
    "destination",
    "travel_date",
    "train_number",
    "class_code",
    "pnr",
}

_SESSION_TTL_SECONDS = 1800
_MAX_HISTORY = 50


@dataclass
class ChatMessage:
    role: str
    text: str
    intent: str | None = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class SessionState:
    slots: dict[str, Any] = field(default_factory=dict)
    history: list[ChatMessage] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    last_intent: str | None = None

    def add_message(self, role: str, text: str, intent: str | None = None):
        self.history.append(ChatMessage(role=role, text=text, intent=intent))
        if len(self.history) > _MAX_HISTORY:
            self.history = self.history[-_MAX_HISTORY:]

    def get_history_dicts(self) -> list[dict]:
        return [
            {"role": m.role, "text": m.text, "intent": m.intent, "timestamp": m.timestamp}
            for m in self.history
        ]


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = Lock()

    def get(self, session_id: str | None) -> SessionState:
        if not session_id:
            return SessionState()
        with self._lock:
            self._gc()
            state = self._sessions.get(session_id)
            if state is None:
                state = SessionState()
                self._sessions[session_id] = state
            state.last_seen = datetime.utcnow()
            return state

    def merge(self, session_id: str | None, new_slots: dict[str, Any]) -> None:
        if not session_id:
            return
        with self._lock:
            state = self._sessions.setdefault(session_id, SessionState())
            for key, value in new_slots.items():
                if key in _REMEMBERED_KEYS and value is not None:
                    state.slots[key] = value
            state.last_seen = datetime.utcnow()

    def set_last_intent(self, session_id: str | None, intent: str) -> None:
        if not session_id:
            return
        with self._lock:
            state = self._sessions.get(session_id)
            if state:
                state.last_intent = intent

    def add_message(self, session_id: str | None, role: str, text: str, intent: str | None = None) -> None:
        if not session_id:
            return
        with self._lock:
            state = self._sessions.setdefault(session_id, SessionState())
            state.add_message(role, text, intent)

    def forget(self, session_id: str | None) -> None:
        if not session_id:
            return
        with self._lock:
            self._sessions.pop(session_id, None)

    def _gc(self) -> None:
        now = datetime.utcnow()
        stale = [
            sid for sid, state in self._sessions.items()
            if (now - state.last_seen).total_seconds() > _SESSION_TTL_SECONDS
        ]
        for sid in stale:
            self._sessions.pop(sid, None)


store = SessionStore()
