"""In-memory store for completed searches.

Keeps scraped results addressable by `search_id` so later pipeline
stages (summary, chat) and the history endpoint can reuse them without
re-searching or re-scraping. A process-local dict is sufficient for a
single-instance demo deployment; swap for Redis/Postgres to persist
across restarts or scale horizontally.
"""

import logging
import threading

from app.models.search import SearchResponse

logger = logging.getLogger(__name__)


class ResearchStore:
    """Thread-safe, process-local store of search sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, SearchResponse] = {}
        self._lock = threading.Lock()

    def save(self, result: SearchResponse) -> None:
        """Persist a completed search session.

        Args:
            result: The search result to store, keyed by its `search_id`.
        """
        with self._lock:
            self._sessions[result.search_id] = result
        logger.debug("Stored search session %s (%d sources)", result.search_id, result.total_sources)

    def get(self, search_id: str) -> SearchResponse | None:
        """Look up a previously stored search session.

        Args:
            search_id: Identifier returned by `POST /api/search`.

        Returns:
            SearchResponse | None: The stored session, or `None` if unknown.
        """
        with self._lock:
            return self._sessions.get(search_id)

    def list_recent(self, limit: int = 20) -> list[SearchResponse]:
        """Return the most recent search sessions, newest first.

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            list[SearchResponse]: Recent sessions, newest first.
        """
        with self._lock:
            sessions = list(self._sessions.values())
        return sorted(sessions, key=lambda session: session.created_at, reverse=True)[:limit]


_research_store = ResearchStore()


def get_research_store() -> ResearchStore:
    """Return the process-wide `ResearchStore` singleton."""
    return _research_store
