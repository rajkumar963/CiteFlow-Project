"""Sentence-embedding model used to power semantic search."""

import logging
from functools import lru_cache

from langchain_community.embeddings import HuggingFaceEmbeddings

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a cached `HuggingFaceEmbeddings` instance.

    Loading `sentence-transformers/all-MiniLM-L6-v2` involves downloading
    and initializing a PyTorch model, so it is loaded once per process
    and reused across requests.

    Returns:
        HuggingFaceEmbeddings: The shared embedding model wrapper.
    """
    settings = get_settings()
    logger.info("Loading embedding model %s", settings.embedding_model)
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)
