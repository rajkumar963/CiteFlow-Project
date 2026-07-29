"""Tests for `app.services.web_scraper.WebScraperService`."""

from app.services.web_scraper import WebScraperService

SAMPLE_HTML = """
<html>
  <head><script>trackPageView();</script></head>
  <body>
    <nav>Home | About | Contact</nav>
    <header>Site Header</header>
    <div class="ad-banner">Buy now!</div>
    <article>
      <h1>Retrieval-Augmented Generation</h1>
      <p>RAG combines retrieval systems with generative language models.</p>
      <p>It grounds responses in retrieved evidence to reduce hallucination.</p>
    </article>
    <footer>Copyright 2026</footer>
  </body>
</html>
"""


def test_extract_text_removes_boilerplate() -> None:
    scraper = WebScraperService()
    text = scraper._extract_text(SAMPLE_HTML)

    assert "Retrieval-Augmented Generation" in text
    assert "grounds responses in retrieved evidence" in text
    assert "trackPageView" not in text
    assert "Home | About | Contact" not in text
    assert "Buy now!" not in text
    assert "Copyright 2026" not in text


def test_normalize_whitespace_collapses_blank_lines() -> None:
    raw = "Line one\n\n\n   \nLine two   with   spaces"
    normalized = WebScraperService._normalize_whitespace(raw)

    assert normalized == "Line one\nLine two with spaces"


def test_scrape_returns_none_for_unreachable_url(mocker) -> None:
    import requests

    mocker.patch("app.services.web_scraper.requests.get", side_effect=requests.RequestException("boom"))
    scraper = WebScraperService()

    assert scraper.scrape("https://unreachable.example.com") is None


def test_scrape_discards_short_content(mocker) -> None:
    mock_response = mocker.Mock()
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = "<html><body><p>Too short.</p></body></html>"
    mock_response.raise_for_status = mocker.Mock()
    mocker.patch("app.services.web_scraper.requests.get", return_value=mock_response)

    scraper = WebScraperService()

    assert scraper.scrape("https://example.com/short") is None
