"""`POST /api/search` — web search + scraping pipeline."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.models.search import SearchRequest, SearchResponse, SourceDocument
from app.services.research_store import get_research_store
from app.services.web_scraper import WebScraperService
from app.services.web_search import WebSearchService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])

_search_service = WebSearchService()
_scraper_service = WebScraperService()


@router.post("/search", response_model=SearchResponse, summary="Search the web and scrape top results")
async def search(request: SearchRequest) -> SearchResponse:
    """Search the web for a query and scrape clean article text from each result.

    The resulting sources are cached under a `search_id` so later stages
    (AI summary, chat) can reuse them without re-fetching.

    Args:
        request: The search query and optional result count override.

    Returns:
        SearchResponse: The search id, sources, and their scraped content.

    Raises:
        HTTPException: 502 if the web search itself returns no results.
    """
    settings = get_settings()
    max_results = request.max_results or settings.search_max_results

    results = _search_service.search(request.query, max_results=max_results)
    if not results:
        raise HTTPException(
            status_code=502,
            detail="Web search returned no results. Try rephrasing the query.",
        )

    scraped_contents = await asyncio.gather(
        *(asyncio.to_thread(_scraper_service.scrape, result["url"]) for result in results)
    )

    sources = [
        SourceDocument(
            url=result["url"],
            title=result["title"] or result["url"],
            snippet=result["snippet"],
            content=content or "",
            word_count=len((content or "").split()),
            scraped=content is not None,
        )
        for result, content in zip(results, scraped_contents)
    ]

    scraped_count = sum(1 for source in sources if source.scraped)
    logger.info("Scraped %d/%d sources successfully for query=%r", scraped_count, len(sources), request.query)

    response = SearchResponse(
        search_id=uuid.uuid4().hex,
        query=request.query,
        created_at=datetime.now(timezone.utc),
        total_sources=len(sources),
        sources=sources,
    )
    get_research_store().save(response)
    return response
