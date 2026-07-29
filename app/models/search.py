"""Schemas for the web search / scraping pipeline (`POST /api/search`)."""

from datetime import datetime

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Payload for `POST /api/search`."""

    query: str = Field(..., min_length=3, max_length=500, description="Research question or topic to look up.")
    max_results: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Number of web pages to search and scrape. Defaults to `SEARCH_MAX_RESULTS`.",
    )


class SourceDocument(BaseModel):
    """A single scraped web page returned as part of a search."""

    url: str = Field(..., description="Source page URL, used for citations.")
    title: str = Field(..., description="Page title as reported by the search engine.")
    snippet: str = Field(default="", description="Short snippet returned by the search engine.")
    content: str = Field(default="", description="Cleaned article text extracted from the page.")
    word_count: int = Field(default=0, description="Word count of the cleaned content.")
    scraped: bool = Field(default=False, description="Whether the page was successfully scraped.")


class SearchResponse(BaseModel):
    """Response payload for `POST /api/search`."""

    search_id: str = Field(..., description="Identifier for this search, reused by /summary and /chat.")
    query: str
    created_at: datetime
    total_sources: int
    sources: list[SourceDocument]
