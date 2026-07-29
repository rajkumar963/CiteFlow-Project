"""Tests for `app.services.chat_service.ChatService`."""

from langchain_core.documents import Document

from app.models.chat import ChatMessage
from app.services.chat_service import ChatService, FALLBACK_ANSWER


def test_build_messages_includes_system_prompt_history_and_context() -> None:
    doc = Document(page_content="RAG grounds LLMs in retrieved data.", metadata={"source_title": "RAG Explainer"})
    history = [
        ChatMessage(role="user", content="What is RAG?"),
        ChatMessage(role="assistant", content="Retrieval-augmented generation."),
    ]

    messages = ChatService._build_messages("Why use it?", [(doc, 0.7)], history)

    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "What is RAG?"}
    assert messages[2] == {"role": "assistant", "content": "Retrieval-augmented generation."}
    assert messages[-1]["role"] == "user"
    assert "RAG grounds LLMs in retrieved data." in messages[-1]["content"]
    assert "Why use it?" in messages[-1]["content"]


def test_ask_returns_fallback_when_llm_returns_blank(mocker) -> None:
    fake_llm = mocker.Mock()
    fake_llm.generate_chat.return_value = "   "
    service = ChatService(llm_service=fake_llm)

    answer = service.ask("Any question?", [], [])

    assert answer == FALLBACK_ANSWER


def test_ask_strips_and_returns_llm_answer(mocker) -> None:
    fake_llm = mocker.Mock()
    fake_llm.generate_chat.return_value = "  RAG combines retrieval and generation.  "
    service = ChatService(llm_service=fake_llm)

    answer = service.ask("What is RAG?", [], [])

    assert answer == "RAG combines retrieval and generation."
