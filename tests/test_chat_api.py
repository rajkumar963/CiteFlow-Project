"""Integration tests for `POST /api/chat`."""

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


def test_chat_endpoint_returns_answer_and_updates_history(mocker) -> None:
    _seed_search("chat-sid-1")
    doc = Document(
        page_content="RAG combines retrieval and generation.",
        metadata={"source_url": "https://example.com", "source_title": "RAG"},
    )
    mocker.patch("app.api.chat._chunking_service.chunk_sources", return_value=[doc])

    fake_registry = mocker.MagicMock()
    fake_registry.retrieve.return_value = [(doc, 0.9)]
    mocker.patch("app.api.chat.get_vector_store_registry", return_value=fake_registry)

    mocker.patch("app.api.chat._chat_service.ask", return_value="RAG grounds answers in retrieved documents.")

    response = client.post("/api/chat", json={"search_id": "chat-sid-1", "message": "What is RAG?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "RAG grounds answers in retrieved documents."
    assert body["citations"][0]["source_url"] == "https://example.com"
    assert [turn["role"] for turn in body["history"]] == ["user", "assistant"]

    # A second turn should carry forward the first exchange in its history.
    response2 = client.post("/api/chat", json={"search_id": "chat-sid-1", "message": "Why does that matter?"})
    assert response2.status_code == 200
    assert len(response2.json()["history"]) == 4


def test_chat_endpoint_404_for_unknown_search_id() -> None:
    response = client.post("/api/chat", json={"search_id": "does-not-exist", "message": "Hello?"})

    assert response.status_code == 404


def test_chat_endpoint_400_when_no_scraped_sources(mocker) -> None:
    _seed_search("chat-sid-2")
    mocker.patch("app.api.chat._chunking_service.chunk_sources", return_value=[])

    from app.services.vector_store_registry import get_vector_store_registry

    mocker.patch("app.api.chat.get_vector_store_registry", return_value=get_vector_store_registry())

    response = client.post("/api/chat", json={"search_id": "chat-sid-2", "message": "Hello?"})

    assert response.status_code == 400


def test_chat_endpoint_502_when_llm_fails(mocker) -> None:
    _seed_search("chat-sid-3")
    doc = Document(page_content="text", metadata={})
    mocker.patch("app.api.chat._chunking_service.chunk_sources", return_value=[doc])

    fake_registry = mocker.MagicMock()
    fake_registry.retrieve.return_value = [(doc, 0.5)]
    mocker.patch("app.api.chat.get_vector_store_registry", return_value=fake_registry)

    mocker.patch("app.api.chat._chat_service.ask", side_effect=LLMServiceError("no key"))

    response = client.post("/api/chat", json={"search_id": "chat-sid-3", "message": "Hello?"})

    assert response.status_code == 502


def test_chat_endpoint_rejects_empty_message() -> None:
    response = client.post("/api/chat", json={"search_id": "any", "message": ""})

    assert response.status_code == 422
