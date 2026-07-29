"""Tests for `app.services.chat_store.ChatStore`."""

from app.services.chat_store import ChatStore


def test_get_history_returns_empty_list_for_unknown_search_id() -> None:
    assert ChatStore().get_history("unknown") == []


def test_append_turn_accumulates_history_in_order() -> None:
    store = ChatStore()

    store.append_turn("sid", "What is RAG?", "RAG is retrieval-augmented generation.")
    history = store.append_turn("sid", "Why use it?", "It grounds answers in real data.")

    assert [(turn.role, turn.content) for turn in history] == [
        ("user", "What is RAG?"),
        ("assistant", "RAG is retrieval-augmented generation."),
        ("user", "Why use it?"),
        ("assistant", "It grounds answers in real data."),
    ]


def test_conversations_are_isolated_per_search_id() -> None:
    store = ChatStore()

    store.append_turn("sid-a", "Question A", "Answer A")
    store.append_turn("sid-b", "Question B", "Answer B")

    assert len(store.get_history("sid-a")) == 2
    assert store.get_history("sid-a")[0].content == "Question A"
    assert store.get_history("sid-b")[0].content == "Question B"
