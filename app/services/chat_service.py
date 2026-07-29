"""RAG-grounded multi-turn chat: retrieved passages + prior turns -> an answer."""

import logging

from langchain_core.documents import Document

from app.models.chat import ChatMessage
from app.services.llm_service import GroqLLMService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful research assistant answering follow-up questions about previously \
retrieved web research. Answer the user's question using ONLY the provided context passages and the \
conversation so far. If the passages do not contain the answer, say so honestly instead of guessing. \
Keep answers concise and conversational."""

FALLBACK_ANSWER = "I couldn't generate a response from the retrieved sources. Please try rephrasing your question."


class ChatService:
    """Builds a grounded multi-turn chat prompt and asks Groq for a reply."""

    def __init__(self, llm_service: GroqLLMService | None = None) -> None:
        """Initialize with an injectable LLM service (defaults to a new `GroqLLMService`).

        Args:
            llm_service: Optional pre-built LLM client, mainly for testing.
        """
        self._llm = llm_service or GroqLLMService()

    def ask(self, message: str, passages: list[tuple[Document, float]], history: list[ChatMessage]) -> str:
        """Answer a follow-up question grounded in retrieved passages and prior turns.

        Args:
            message: The user's latest question.
            passages: Retrieved `(Document, relevance_score)` pairs for this question.
            history: Prior conversation turns for this search session, oldest first.

        Returns:
            str: The assistant's answer.

        Raises:
            LLMServiceError: If the underlying LLM request fails.
        """
        messages = self._build_messages(message, passages, history)
        answer = self._llm.generate_chat(messages)
        return answer.strip() or FALLBACK_ANSWER

    @staticmethod
    def _build_messages(
        message: str, passages: list[tuple[Document, float]], history: list[ChatMessage]
    ) -> list[dict[str, str]]:
        """Assemble the full message list sent to the LLM.

        Args:
            message: The user's latest question.
            passages: Retrieved passages to ground the answer in.
            history: Prior conversation turns, oldest first.

        Returns:
            list[dict[str, str]]: System prompt, prior turns, then the new
            user turn with freshly retrieved context inlined.
        """
        context_block = "\n\n".join(
            f"[{i}] ({doc.metadata.get('source_title', 'Unknown')}): {doc.page_content}"
            for i, (doc, _score) in enumerate(passages, start=1)
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend({"role": turn.role, "content": turn.content} for turn in history)
        messages.append({"role": "user", "content": f"Context passages:\n{context_block}\n\nQuestion: {message}"})
        return messages
