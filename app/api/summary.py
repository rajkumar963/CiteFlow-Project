"""`POST /api/summary` — RAG summarization over a prior search's sources."""

import logging

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.models.summary import CitedPassage, SummaryRequest, SummaryResponse
from app.services.chunking_service import ChunkingService
from app.services.llm_service import LLMServiceError
from app.services.research_store import get_research_store
from app.services.summarization_service import SummarizationService
from app.services.vector_store_registry import get_vector_store_registry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["summary"])

_chunking_service = ChunkingService()
_summarization_service = SummarizationService()


@router.post("/summary", response_model=SummaryResponse, summary="Generate a cited AI summary from a search")
async def generate_summary(request: SummaryRequest) -> SummaryResponse:
    """Retrieve the most relevant passages from a prior search and summarize them.

    Chunks the scraped sources, embeds and indexes them in FAISS (cached
    per `search_id` for reuse by chat), retrieves the top-k passages for
    the query, and asks the LLM for a structured, citation-backed summary.

    Args:
        request: The search id, optional focus query, and optional top-k override.

    Returns:
        SummaryResponse: Summary, insights, facts, takeaways, and citations.

    Raises:
        HTTPException: 404 if the search id is unknown, 400 if it has no
            scraped sources, 502 if the LLM request fails.
    """
    search = get_research_store().get(request.search_id)
    if search is None:
        raise HTTPException(status_code=404, detail=f"No search found for search_id={request.search_id!r}")

    query = request.focus_query or search.query
    top_k = request.top_k or get_settings().summary_top_k

    registry = get_vector_store_registry()
    try:
        registry.get_or_build(request.search_id, _chunking_service.chunk_sources(search.sources))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    passages = registry.retrieve(request.search_id, query, k=top_k)
    logger.info("Retrieved %d passage(s) for search_id=%s query=%r", len(passages), request.search_id, query)

    try:
        summary_data = _summarization_service.summarize(query, passages)
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    citations = [
        CitedPassage(
            text=doc.page_content,
            source_url=doc.metadata.get("source_url", ""),
            source_title=doc.metadata.get("source_title", ""),
            relevance_score=round(score, 4),
        )
        for doc, score in passages
    ]

    return SummaryResponse(search_id=request.search_id, query=query, citations=citations, **summary_data)
