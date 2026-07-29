"""Web search service backed by DuckDuckGo."""

import logging

from ddgs import DDGS
from ddgs.exceptions import DDGSException

logger = logging.getLogger(__name__)


class WebSearchService:
    """Thin wrapper around `ddgs` for text search."""

    def search(self, query: str, max_results: int = 8) -> list[dict[str, str]]:
        """Search DuckDuckGo for a query and return the top results.

        Args:
            query: The search query.
            max_results: Maximum number of results to return.

        Returns:
            list[dict[str, str]]: Each dict has `title`, `url`, and `snippet` keys.
            Returns an empty list if the search fails.
        """
        logger.info("Searching web for query=%r (max_results=%d)", query, max_results)
        try:
            with DDGS() as ddgs:
                raw_results = ddgs.text(query, max_results=max_results)
        except DDGSException:
            logger.exception("DuckDuckGo search failed for query=%r", query)
            return []

        results = [
            {
                "title": item.get("title", "").strip(),
                "url": item.get("href", "").strip(),
                "snippet": item.get("body", "").strip(),
            }
            for item in raw_results
            if item.get("href")
        ]
        logger.info("Web search returned %d results for query=%r", len(results), query)
        return results
