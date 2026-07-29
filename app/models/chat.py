"""Schemas for the RAG chat pipeline (`POST /api/chat`)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.summary import CitedPassage


class ChatMessage(BaseModel):
    """A single turn in a chat conversation."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Payload for `POST /api/chat`."""

    search_id: str = Field(..., description="Identifier returned by a prior `POST /api/search` call.")
    message: str = Field(..., min_length=1, max_length=1000, description="The user's follow-up question.")
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of passages to retrieve for grounding the answer.",
    )


class ChatResponse(BaseModel):
    """Response payload for `POST /api/chat`."""

    search_id: str
    answer: str
    citations: list[CitedPassage] = Field(default_factory=list)
    history: list[ChatMessage] = Field(default_factory=list, description="Full conversation so far, oldest first.")
