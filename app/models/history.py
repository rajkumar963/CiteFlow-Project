"""Schemas for the search history endpoint (`GET /api/history`)."""

from datetime import datetime

from pydantic import BaseModel


class HistoryItem(BaseModel):
    """Summary of a single past search session."""

    search_id: str
    query: str
    created_at: datetime
    total_sources: int
    scraped_sources: int


class HistoryResponse(BaseModel):
    """Response payload for `GET /api/history`."""

    items: list[HistoryItem]
    total: int
