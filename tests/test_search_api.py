"""Integration tests for `POST /api/search`."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_endpoint_returns_sources(mocker) -> None:
    mocker.patch(
        "app.api.search._search_service.search",
        return_value=[{"title": "RAG Explained", "url": "https://example.com/rag", "snippet": "A snippet."}],
    )
    mocker.patch(
        "app.api.search._scraper_service.scrape",
        return_value="RAG combines retrieval with generation. " * 10,
    )

    response = client.post("/api/search", json={"query": "what is retrieval augmented generation"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_sources"] == 1
    assert body["sources"][0]["scraped"] is True
    assert body["sources"][0]["url"] == "https://example.com/rag"
    assert "search_id" in body


def test_search_endpoint_returns_502_when_no_results(mocker) -> None:
    mocker.patch("app.api.search._search_service.search", return_value=[])

    response = client.post("/api/search", json={"query": "an unanswerable query"})

    assert response.status_code == 502


def test_search_endpoint_rejects_short_query() -> None:
    response = client.post("/api/search", json={"query": "ab"})

    assert response.status_code == 422
