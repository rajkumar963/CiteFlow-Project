"""Centralized application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment variables / `.env`.

    Using `pydantic-settings` gives us type validation and a single
    source of truth for configuration across the API and frontend.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "Citeflow"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    cors_allowed_origins: str = "*"

    # Groq LLM API
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Web search
    search_max_results: int = 8

    # Vector store
    vector_db_dir: str = "vector_db"
    chunk_size: int = 1000
    chunk_overlap: int = 150

    # Summarization / retrieval
    summary_top_k: int = 6


@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance.

    `lru_cache` ensures the `.env` file is parsed only once per process.
    """
    return Settings()
