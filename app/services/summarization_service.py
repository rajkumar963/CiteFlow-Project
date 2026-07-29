"""RAG summarization: retrieve grounded passages, then prompt an LLM for a cited summary."""

import json
import logging

from langchain_core.documents import Document

from app.services.llm_service import GroqLLMService, LLMServiceError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a meticulous research assistant. You are given a user question and \
numbered source passages retrieved from the web. Using ONLY information found in the passages, \
respond with a single strict JSON object and nothing else, using exactly these keys:

- "summary": a concise 3-5 sentence overview answering the question.
- "key_insights": an array of short strings, the most important insights.
- "important_facts": an array of short strings, concrete facts/figures/definitions found in the passages.
- "actionable_takeaways": an array of short strings, practical actions or next steps a reader could take.

If the passages do not fully answer the question, say so within "summary" rather than inventing information. \
Do not fabricate facts that are not supported by the passages."""

REQUIRED_LIST_FIELDS = ("key_insights", "important_facts", "actionable_takeaways")


class SummarizationService:
    """Builds a RAG prompt from retrieved passages and summarizes it via Groq."""

    def __init__(self, llm_service: GroqLLMService | None = None) -> None:
        """Initialize with an injectable LLM service (defaults to a new `GroqLLMService`).

        Args:
            llm_service: Optional pre-built LLM client, mainly for testing.
        """
        self._llm = llm_service or GroqLLMService()

    def summarize(self, query: str, passages: list[tuple[Document, float]]) -> dict:
        """Generate a grounded, structured summary from retrieved passages.

        Args:
            query: The question the summary should answer.
            passages: Retrieved `(Document, relevance_score)` pairs, most
                relevant first.

        Returns:
            dict: Keys `summary`, `key_insights`, `important_facts`,
            `actionable_takeaways` — all present, with list fields
            defaulting to `[]` if the LLM response was malformed.

        Raises:
            LLMServiceError: If the underlying LLM request fails.
        """
        user_prompt = self._build_user_prompt(query, passages)

        raw_response = self._llm.generate_json(SYSTEM_PROMPT, user_prompt)
        return self._parse_response(raw_response)

    @staticmethod
    def _build_user_prompt(query: str, passages: list[tuple[Document, float]]) -> str:
        """Format retrieved passages into a numbered, citable prompt body."""
        sources_block = "\n\n".join(
            f"[{i}] Source: {doc.metadata.get('source_title', 'Unknown')} "
            f"({doc.metadata.get('source_url', 'unknown URL')})\n{doc.page_content}"
            for i, (doc, _score) in enumerate(passages, start=1)
        )
        return f"Question: {query}\n\nSource passages:\n\n{sources_block}"

    @staticmethod
    def _parse_response(raw_response: str) -> dict:
        """Parse the LLM's JSON response, tolerating minor schema drift.

        Args:
            raw_response: Raw JSON string returned by the LLM.

        Returns:
            dict: Normalized summary payload with all required keys present.
        """
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON output; falling back to raw text summary")
            parsed = {"summary": raw_response.strip()}

        summary = str(parsed.get("summary", "")).strip() or "No summary could be generated from the retrieved sources."

        result = {"summary": summary}
        for field in REQUIRED_LIST_FIELDS:
            value = parsed.get(field, [])
            result[field] = [str(item) for item in value] if isinstance(value, list) else []

        return result
