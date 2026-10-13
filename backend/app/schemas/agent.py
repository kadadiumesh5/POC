from typing import Any

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str | None = None


class AgentChatResponse(BaseModel):
    intent: str
    reply: str
    data: Any | None = None
    actions_taken: list[str] = []
    suggestions: list[str] = []


class AgentHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict] = []
    slots: dict[str, Any] = {}
