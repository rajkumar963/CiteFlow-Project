"""`POST /api/chat` — multi-turn RAG chat over a prior search's sources."""

import logging

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.models.chat import ChatRequest, ChatResponse
from app.models.summary import CitedPassage
from app.services.chat_service import ChatService
from app.services.chat_store import get_chat_store
from app.services.chunking_service import ChunkingService
from app.services.llm_service import LLMServiceError
from app.services.research_store import get_research_store
from app.services.vector_store_registry import get_vector_store_registry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

_chunking_service = ChunkingService()
_chat_service = ChatService()


@router.post("/chat", response_model=ChatResponse, summary="Ask a follow-up question grounded in a prior search")
async def chat(request: ChatRequest) -> ChatResponse:
    """Answer a follow-up question using passages retrieved from a prior search.

    Reuses (or lazily builds) the same FAISS index as `/summary`, retrieves
    passages relevant to the new question, and grounds the answer in both
    those passages and the conversation so far.

    Args:
        request: The search id, the user's message, and an optional top-k override.

    Returns:
        ChatResponse: The answer, its citations, and the full conversation so far.

    Raises:
        HTTPException: 404 if the search id is unknown, 400 if it has no
            scraped sources, 502 if the LLM request fails.
    """
    search = get_research_store().get(request.search_id)
    if search is None:
        raise HTTPException(status_code=404, detail=f"No search found for search_id={request.search_id!r}")

    top_k = request.top_k or get_settings().summary_top_k

    registry = get_vector_store_registry()
    try:
        registry.get_or_build(request.search_id, _chunking_service.chunk_sources(search.sources))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    passages = registry.retrieve(request.search_id, request.message, k=top_k)

    chat_store = get_chat_store()
    prior_history = chat_store.get_history(request.search_id)

    try:
        answer = _chat_service.ask(request.message, passages, prior_history)
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    updated_history = chat_store.append_turn(request.search_id, request.message, answer)

    citations = [
        CitedPassage(
            text=doc.page_content,
            source_url=doc.metadata.get("source_url", ""),
            source_title=doc.metadata.get("source_title", ""),
            relevance_score=round(score, 4),
        )
        for doc, score in passages
    ]

    return ChatResponse(search_id=request.search_id, answer=answer, citations=citations, history=updated_history)
