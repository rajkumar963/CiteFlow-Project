"""Integration tests for `POST /api/summary`."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.main import app
from app.models.search import SearchResponse, SourceDocument
from app.services.llm_service import LLMServiceError
from app.services.research_store import get_research_store

client = TestClient(app)


def _seed_search(search_id: str) -> SearchResponse:
    search = SearchResponse(
        search_id=search_id,
        query="what is RAG",
        created_at=datetime.now(timezone.utc),
        total_sources=1,
        sources=[
            SourceDocument(
                url="https://example.com",
                title="RAG",
                snippet="s",
                content="RAG combines retrieval and generation. " * 20,
                word_count=100,
                scraped=True,
            )
        ],
    )
    get_research_store().save(search)
    return search


def test_summary_endpoint_returns_structured_summary(mocker) -> None:
    _seed_search("sid-1")
    doc = Document(
        page_content="RAG combines retrieval and generation.",
        metadata={"source_url": "https://example.com", "source_title": "RAG"},
    )
    mocker.patch("app.api.summary._chunking_service.chunk_sources", return_value=[doc])

    fake_registry = mocker.MagicMock()
    fake_registry.retrieve.return_value = [(doc, 0.9)]
    mocker.patch("app.api.summary.get_vector_store_registry", return_value=fake_registry)

    mocker.patch(
        "app.api.summary._summarization_service.summarize",
        return_value={
            "summary": "RAG combines retrieval with generation.",
            "key_insights": ["Improves factuality"],
            "important_facts": ["Uses external documents"],
            "actionable_takeaways": ["Use RAG for grounded QA"],
        },
    )

    response = client.post("/api/summary", json={"search_id": "sid-1"})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == "RAG combines retrieval with generation."
    assert body["citations"][0]["source_url"] == "https://example.com"
    fake_registry.get_or_build.assert_called_once()


def test_summary_endpoint_404_for_unknown_search_id() -> None:
    response = client.post("/api/summary", json={"search_id": "does-not-exist"})

    assert response.status_code == 404


def test_summary_endpoint_400_when_no_scraped_sources(mocker) -> None:
    _seed_search("sid-2")
    mocker.patch("app.api.summary._chunking_service.chunk_sources", return_value=[])

    from app.services.vector_store_registry import get_vector_store_registry

    mocker.patch("app.api.summary.get_vector_store_registry", return_value=get_vector_store_registry())

    response = client.post("/api/summary", json={"search_id": "sid-2"})

    assert response.status_code == 400


def test_summary_endpoint_502_when_llm_fails(mocker) -> None:
    _seed_search("sid-3")
    doc = Document(page_content="text", metadata={})
    mocker.patch("app.api.summary._chunking_service.chunk_sources", return_value=[doc])

    fake_registry = mocker.MagicMock()
    fake_registry.retrieve.return_value = [(doc, 0.5)]
    mocker.patch("app.api.summary.get_vector_store_registry", return_value=fake_registry)

    mocker.patch("app.api.summary._summarization_service.summarize", side_effect=LLMServiceError("no key"))

    response = client.post("/api/summary", json={"search_id": "sid-3"})

    assert response.status_code == 502
