"""Splits scraped source documents into semantically coherent chunks."""

import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.models.search import SourceDocument

logger = logging.getLogger(__name__)


class ChunkingService:
    """Wraps `RecursiveCharacterTextSplitter` for scraped research sources."""

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        """Initialize the splitter using project defaults unless overridden.

        Args:
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Characters of overlap between consecutive chunks.
        """
        settings = get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_sources(self, sources: list[SourceDocument]) -> list[Document]:
        """Split successfully scraped sources into chunk-level `Document`s.

        Args:
            sources: Scraped search result sources.

        Returns:
            list[Document]: Chunks with `source_url` and `source_title` metadata.
            Sources that failed to scrape are skipped.
        """
        documents = [
            Document(page_content=source.content, metadata={"source_url": source.url, "source_title": source.title})
            for source in sources
            if source.scraped and source.content
        ]

        chunks = self._splitter.split_documents(documents)
        logger.info("Split %d source(s) into %d chunk(s)", len(documents), len(chunks))
        return chunks
