"""Tests for `app.services.web_search.WebSearchService`."""

from ddgs.exceptions import DDGSException

from app.services.web_search import WebSearchService


def test_search_maps_ddgs_fields(mocker) -> None:
    mock_ddgs = mocker.MagicMock()
    mock_ddgs.__enter__.return_value.text.return_value = [
        {"title": " RAG Explained ", "href": "https://example.com/rag", "body": " A short snippet. "},
        {"title": "No URL", "body": "Should be dropped"},
    ]
    mocker.patch("app.services.web_search.DDGS", return_value=mock_ddgs)

    results = WebSearchService().search("what is RAG", max_results=5)

    assert results == [{"title": "RAG Explained", "url": "https://example.com/rag", "snippet": "A short snippet."}]


def test_search_returns_empty_list_on_failure(mocker) -> None:
    mock_ddgs = mocker.MagicMock()
    mock_ddgs.__enter__.return_value.text.side_effect = DDGSException("rate limited")
    mocker.patch("app.services.web_search.DDGS", return_value=mock_ddgs)

    assert WebSearchService().search("anything") == []
