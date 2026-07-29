"""Groq LLM client wrapper used for RAG summarization and chat."""

import logging

from groq import Groq, GroqError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMServiceError(RuntimeError):
    """Raised when the LLM is not configured or a completion request fails."""


class GroqLLMService:
    """Thin wrapper around the Groq chat completions API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.groq_model
        self._client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

    def _complete(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
    ) -> str:
        """Request a chat completion from Groq.

        Args:
            messages: Full message list (system/user/assistant turns).
            temperature: Sampling temperature; lower is more deterministic.
            max_tokens: Maximum tokens to generate.
            json_mode: If `True`, ask Groq to constrain output to a JSON object.

        Returns:
            str: The raw text content returned by the model.

        Raises:
            LLMServiceError: If `GROQ_API_KEY` is not configured or the request fails.
        """
        if self._client is None:
            raise LLMServiceError("GROQ_API_KEY is not configured. Set it in your .env file.")

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_mode else None,
            )
        except GroqError as exc:
            logger.exception("Groq completion request failed")
            raise LLMServiceError(f"LLM request failed: {exc}") from exc

        return completion.choices[0].message.content or ""

    def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """Request a JSON-formatted chat completion from Groq.

        Args:
            system_prompt: Instructions establishing the assistant's role and output schema.
            user_prompt: The task-specific prompt, including retrieved context.
            temperature: Sampling temperature; lower is more deterministic.
            max_tokens: Maximum tokens to generate.

        Returns:
            str: The raw JSON string returned by the model.

        Raises:
            LLMServiceError: If `GROQ_API_KEY` is not configured or the request fails.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._complete(messages, temperature, max_tokens, json_mode=True) or "{}"

    def generate_chat(self, messages: list[dict[str, str]], temperature: float = 0.4, max_tokens: int = 800) -> str:
        """Request a plain-text chat completion from Groq.

        Args:
            messages: Full conversation, including a leading system message.
            temperature: Sampling temperature; lower is more deterministic.
            max_tokens: Maximum tokens to generate.

        Returns:
            str: The model's reply text.

        Raises:
            LLMServiceError: If `GROQ_API_KEY` is not configured or the request fails.
        """
        return self._complete(messages, temperature, max_tokens, json_mode=False)
