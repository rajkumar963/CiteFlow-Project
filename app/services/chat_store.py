"""In-memory store of chat conversation history, keyed by search session."""

import logging
import threading

from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class ChatStore:
    """Thread-safe, process-local store of per-search chat conversations."""

    def __init__(self) -> None:
        self._conversations: dict[str, list[ChatMessage]] = {}
        self._lock = threading.Lock()

    def get_history(self, search_id: str) -> list[ChatMessage]:
        """Return the conversation so far for a search session.

        Args:
            search_id: Identifier of the search session.

        Returns:
            list[ChatMessage]: Prior turns, oldest first. Empty if none yet.
        """
        with self._lock:
            return list(self._conversations.get(search_id, []))

    def append_turn(self, search_id: str, user_message: str, assistant_message: str) -> list[ChatMessage]:
        """Append a user/assistant exchange and return the updated history.

        Args:
            search_id: Identifier of the search session.
            user_message: The user's question.
            assistant_message: The generated answer.

        Returns:
            list[ChatMessage]: The full, updated conversation.
        """
        with self._lock:
            history = self._conversations.setdefault(search_id, [])
            history.append(ChatMessage(role="user", content=user_message))
            history.append(ChatMessage(role="assistant", content=assistant_message))
            return list(history)


_chat_store = ChatStore()


def get_chat_store() -> ChatStore:
    """Return the process-wide `ChatStore` singleton."""
    return _chat_store
