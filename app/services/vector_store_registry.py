"""FAISS vector store registry, keyed by search session.

Building embeddings is the most expensive step in the pipeline, so each
search's FAISS index is built once and cached here. `POST /summary` and
the future `/chat` endpoint both retrieve from the same cached index
instead of re-embedding the same chunks.
"""

import logging
import threading

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.services.embedding_service import get_embeddings

logger = logging.getLogger(__name__)


class VectorStoreRegistry:
    """Thread-safe, process-local cache of per-search FAISS indexes."""

    def __init__(self) -> None:
        self._stores: dict[str, FAISS] = {}
        self._lock = threading.Lock()

    def get_or_build(self, search_id: str, chunks: list[Document]) -> FAISS:
        """Return the cached FAISS index for a search, building it if absent.

        Args:
            search_id: Identifier of the search session these chunks belong to.
            chunks: Chunk-level documents to embed and index, used only on
                first build.

        Returns:
            FAISS: The vector store for this search session.

        Raises:
            ValueError: If no cached index exists yet and `chunks` is empty.
        """
        with self._lock:
            store = self._stores.get(search_id)
        if store is not None:
            return store

        if not chunks:
            raise ValueError(f"No chunks available to build a vector store for search_id={search_id!r}")

        logger.info("Building FAISS index for search_id=%s from %d chunk(s)", search_id, len(chunks))
        store = FAISS.from_documents(chunks, get_embeddings())

        with self._lock:
            self._stores[search_id] = store
        return store

    def retrieve(self, search_id: str, query: str, k: int = 6) -> list[tuple[Document, float]]:
        """Retrieve the most relevant chunks for a query from a cached index.

        Args:
            search_id: Identifier of the search session to query.
            query: The natural-language query to embed and search with.
            k: Number of passages to retrieve.

        Returns:
            list[tuple[Document, float]]: Chunks paired with a relevance
            score in `[0, 1]` (higher is more relevant).

        Raises:
            KeyError: If no vector store has been built for `search_id`.
        """
        with self._lock:
            store = self._stores.get(search_id)
        if store is None:
            raise KeyError(f"No vector store found for search_id={search_id!r}")

        return store.similarity_search_with_relevance_scores(query, k=k)


_vector_store_registry = VectorStoreRegistry()


def get_vector_store_registry() -> VectorStoreRegistry:
    """Return the process-wide `VectorStoreRegistry` singleton."""
    return _vector_store_registry
