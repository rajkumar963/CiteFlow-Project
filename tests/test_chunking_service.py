"""Tests for `app.services.chunking_service.ChunkingService`."""

from app.models.search import SourceDocument
from app.services.chunking_service import ChunkingService


def test_chunk_sources_skips_unscraped_and_splits_long_text() -> None:
    sources = [
        SourceDocument(
            url="https://a.com", title="A", snippet="", content="Sentence one. " * 200, word_count=400, scraped=True
        ),
        SourceDocument(url="https://b.com", title="B", snippet="", content="", word_count=0, scraped=False),
    ]
    service = ChunkingService(chunk_size=200, chunk_overlap=20)
    chunks = service.chunk_sources(sources)

    assert len(chunks) > 1
    assert all(chunk.metadata["source_url"] == "https://a.com" for chunk in chunks)
    assert all(len(chunk.page_content) <= 220 for chunk in chunks)


def test_chunk_sources_returns_empty_for_no_scraped_sources() -> None:
    sources = [SourceDocument(url="https://b.com", title="B", snippet="", content="", word_count=0, scraped=False)]

    assert ChunkingService().chunk_sources(sources) == []
