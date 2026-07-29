"""FastAPI application entrypoint for the Citeflow backend."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, history, search, summary
from app.core.config import get_settings
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Log application startup and shutdown."""
    settings = get_settings()
    logger.info("Starting %s (env=%s, debug=%s)", settings.app_name, settings.app_env, settings.debug)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory that builds and configures the FastAPI instance.

    Returns:
        FastAPI: The configured application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Citeflow searches the web, "
        "retrieves relevant passages via semantic search, and generates "
        "cited summaries using RAG.",
        version="0.1.0",
        lifespan=lifespan,
    )

    origins = (
        ["*"]
        if settings.cors_allowed_origins.strip() == "*"
        else [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(summary.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(history.router, prefix="/api")

    @app.get("/", tags=["root"], summary="API root")
    async def root() -> dict[str, str]:
        """Return a simple welcome payload pointing to the docs."""
        return {"message": f"{settings.app_name} API", "docs": "/docs"}

    return app


app = create_app()
