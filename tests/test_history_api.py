"""Integration tests for `GET /api/history`."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models.search import SearchResponse, SourceDocument
from app.services.research_store import get_research_store

client = TestClient(app)


def test_history_returns_most_recent_first() -> None:
    store = get_research_store()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ids = ["hist-1", "hist-2", "hist-3"]
    for i, search_id in enumerate(ids):
        store.save(
            SearchResponse(
                search_id=search_id,
                query=f"query {i}",
                created_at=base + timedelta(minutes=i),
                total_sources=1,
                sources=[SourceDocument(url="https://a.com", title="A", content="c", word_count=1, scraped=True)],
            )
        )

    response = client.get("/api/history", params={"limit": 100})

    assert response.status_code == 200
    my_items = [item for item in response.json()["items"] if item["search_id"] in ids]
    assert [item["search_id"] for item in my_items] == ["hist-3", "hist-2", "hist-1"]


def test_history_respects_limit() -> None:
    response = client.get("/api/history", params={"limit": 1})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["total"] == 1


def test_history_reports_scraped_source_count() -> None:
    store = get_research_store()
    store.save(
        SearchResponse(
            search_id="hist-scrape-test",
            query="q",
            created_at=datetime.now(timezone.utc),
            total_sources=2,
            sources=[
                SourceDocument(url="https://a.com", title="A", content="c", word_count=1, scraped=True),
                SourceDocument(url="https://b.com", title="B", content="", word_count=0, scraped=False),
            ],
        )
    )

    response = client.get("/api/history", params={"limit": 100})

    item = next(i for i in response.json()["items"] if i["search_id"] == "hist-scrape-test")
    assert item["total_sources"] == 2
    assert item["scraped_sources"] == 1


def test_history_rejects_limit_out_of_range() -> None:
    response = client.get("/api/history", params={"limit": 0})

    assert response.status_code == 422
