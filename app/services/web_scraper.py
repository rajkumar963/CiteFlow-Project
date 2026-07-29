"""Web scraping service that extracts clean article text from a URL."""

import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Tags that never contain article content: scripts, styles, navigation,
# ads, and other page chrome.
UNWANTED_TAGS = [
    "script",
    "style",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "iframe",
    "noscript",
    "svg",
    "button",
]

# Common ad / tracking / boilerplate container identifiers.
UNWANTED_SELECTORS = [
    "[class*='ad-']",
    "[class*='advert']",
    "[id*='ad-']",
    "[class*='cookie']",
    "[class*='banner']",
    "[class*='popup']",
    "[class*='newsletter']",
    "[class*='social']",
    "[class*='sidebar']",
    "[class*='comment']",
]

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

MIN_CONTENT_WORDS = 50


class WebScraperService:
    """Fetches a URL and extracts cleaned, readable article text."""

    def __init__(self, timeout: int = 10) -> None:
        """Initialize the scraper.

        Args:
            timeout: Per-request timeout, in seconds.
        """
        self.timeout = timeout

    def scrape(self, url: str) -> str | None:
        """Download a page and extract its main text content.

        Args:
            url: The page URL to scrape.

        Returns:
            str | None: Cleaned article text, or `None` if the page could
            not be fetched or yielded too little usable content.
        """
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Failed to fetch %s: %s", url, exc)
            return None

        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type:
            logger.warning("Skipping non-HTML content at %s (Content-Type=%s)", url, content_type)
            return None

        text = self._extract_text(response.text)
        if not text or len(text.split()) < MIN_CONTENT_WORDS:
            logger.warning("Scraped content from %s is too short, discarding", url)
            return None

        return text

    def _extract_text(self, html: str) -> str:
        """Parse raw HTML and return cleaned, whitespace-normalized text.

        Args:
            html: Raw HTML source of the page.

        Returns:
            str: Cleaned article text.
        """
        soup = BeautifulSoup(html, "html.parser")

        for tag_name in UNWANTED_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        for selector in UNWANTED_SELECTORS:
            for tag in soup.select(selector):
                tag.decompose()

        main = soup.find("article") or soup.find("main") or soup.body or soup
        raw_text = main.get_text(separator="\n")

        return self._normalize_whitespace(raw_text)

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Collapse repeated blank lines and trailing spaces.

        Args:
            text: Raw extracted text.

        Returns:
            str: Text with normalized line breaks and spacing.
        """
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        return re.sub(r" {2,}", " ", "\n".join(lines))
