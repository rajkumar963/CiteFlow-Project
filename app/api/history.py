"""`GET /api/history` — recent search sessions."""

import logging

from fastapi import APIRouter, Query

from app.models.history import HistoryItem, HistoryResponse
from app.services.research_store import get_research_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["history"])


@router.get("/history", response_model=HistoryResponse, summary="List recent search sessions")
async def get_history(limit: int = Query(default=20, ge=1, le=100)) -> HistoryResponse:
    """Return recent search sessions, most recent first.

    Args:
        limit: Maximum number of sessions to return.

    Returns:
        HistoryResponse: Recent sessions with source counts.
    """
    sessions = get_research_store().list_recent(limit=limit)
    items = [
        HistoryItem(
            search_id=session.search_id,
            query=session.query,
            created_at=session.created_at,
            total_sources=session.total_sources,
            scraped_sources=sum(1 for source in session.sources if source.scraped),
        )
        for session in sessions
    ]
    return HistoryResponse(items=items, total=len(items))
