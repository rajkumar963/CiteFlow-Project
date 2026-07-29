"""Schemas for the RAG summarization pipeline (`POST /api/summary`)."""

from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    """Payload for `POST /api/summary`."""

    search_id: str = Field(..., description="Identifier returned by a prior `POST /api/search` call.")
    focus_query: str | None = Field(
        default=None,
        min_length=3,
        max_length=500,
        description="Optional narrower question to focus the summary on. Defaults to the original search query.",
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of passages to retrieve for grounding the summary.",
    )


class CitedPassage(BaseModel):
    """A retrieved passage used to ground the summary, with its source."""

    text: str
    source_url: str
    source_title: str
    relevance_score: float = Field(..., description="Similarity score (higher is more relevant).")


class SummaryResponse(BaseModel):
    """Response payload for `POST /api/summary`."""

    search_id: str
    query: str
    summary: str = Field(..., description="Concise overview of the research findings.")
    key_insights: list[str] = Field(default_factory=list)
    important_facts: list[str] = Field(default_factory=list)
    actionable_takeaways: list[str] = Field(default_factory=list)
    citations: list[CitedPassage] = Field(default_factory=list)
