"""Application-wide logging configuration."""

import logging
import sys

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure the root logger with a consistent format.

    Called once at application startup (FastAPI lifespan / Streamlit
    entrypoint) so every module's `logging.getLogger(__name__)` inherits
    the same handlers and level.
    """
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Third-party libraries are noisy at INFO/DEBUG; keep them quieter.
    for noisy_logger in ("httpx", "urllib3", "sentence_transformers"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
