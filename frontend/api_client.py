"""Thin HTTP client for the FastAPI backend, shared across Streamlit pages."""

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 60


class ApiError(Exception):
    """Raised when the backend is unreachable or returns an error response."""


def get_health() -> dict[str, Any]:
    """Call `GET /api/health`.

    Returns:
        dict[str, Any]: The health payload.

    Raises:
        ApiError: If the backend cannot be reached or returns an error.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("Backend health check failed: %s", exc)
        raise ApiError(str(exc)) from exc


def _post(path: str, payload: dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """POST JSON to the backend and return the decoded response.

    Args:
        path: API path, e.g. `/api/search`.
        payload: JSON-serializable request body.
        timeout: Request timeout, in seconds.

    Returns:
        dict[str, Any]: The decoded JSON response.

    Raises:
        ApiError: If the backend cannot be reached or returns an error.
    """
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        detail = exc.response.json().get("detail", str(exc)) if exc.response is not None else str(exc)
        logger.warning("Request to %s failed: %s", path, detail)
        raise ApiError(detail) from exc
    except requests.RequestException as exc:
        logger.warning("Request to %s failed: %s", path, exc)
        raise ApiError(str(exc)) from exc


def get_history(limit: int = 20) -> dict[str, Any]:
    """Call `GET /api/history`.

    Args:
        limit: Maximum number of recent search sessions to return.

    Returns:
        dict[str, Any]: The history payload (`items`, `total`).

    Raises:
        ApiError: If the backend cannot be reached or returns an error.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/api/history", params={"limit": limit}, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("Request to /api/history failed: %s", exc)
        raise ApiError(str(exc)) from exc


def run_search(query: str, max_results: int | None = None) -> dict[str, Any]:
    """Call `POST /api/search`.

    Args:
        query: The research question or topic.
        max_results: Optional override for the number of sources to retrieve.

    Returns:
        dict[str, Any]: The search response payload (search_id, sources, ...).

    Raises:
        ApiError: If the backend cannot be reached or returns an error.
    """
    payload: dict[str, Any] = {"query": query}
    if max_results is not None:
        payload["max_results"] = max_results
    return _post("/api/search", payload)


def run_summary(search_id: str, focus_query: str | None = None, top_k: int | None = None) -> dict[str, Any]:
    """Call `POST /api/summary`.

    Args:
        search_id: Identifier returned by a prior `run_search` call.
        focus_query: Optional narrower question to focus the summary on.
        top_k: Optional override for the number of passages to retrieve.

    Returns:
        dict[str, Any]: The summary response payload.

    Raises:
        ApiError: If the backend cannot be reached or returns an error.
    """
    payload: dict[str, Any] = {"search_id": search_id}
    if focus_query is not None:
        payload["focus_query"] = focus_query
    if top_k is not None:
        payload["top_k"] = top_k
    return _post("/api/summary", payload, timeout=120)


def run_chat(search_id: str, message: str, top_k: int | None = None) -> dict[str, Any]:
    """Call `POST /api/chat`.

    Args:
        search_id: Identifier returned by a prior `run_search` call.
        message: The user's follow-up question.
        top_k: Optional override for the number of passages to retrieve.

    Returns:
        dict[str, Any]: The chat response payload (answer, citations, history).

    Raises:
        ApiError: If the backend cannot be reached or returns an error.
    """
    payload: dict[str, Any] = {"search_id": search_id, "message": message}
    if top_k is not None:
        payload["top_k"] = top_k
    return _post("/api/chat", payload, timeout=120)
