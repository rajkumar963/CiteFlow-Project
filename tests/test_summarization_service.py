"""Tests for `app.services.summarization_service.SummarizationService`."""

from langchain_core.documents import Document

from app.services.summarization_service import SummarizationService


def test_parse_response_valid_json() -> None:
    raw = '{"summary": "S", "key_insights": ["a"], "important_facts": ["b"], "actionable_takeaways": ["c"]}'

    result = SummarizationService._parse_response(raw)

    assert result == {
        "summary": "S",
        "key_insights": ["a"],
        "important_facts": ["b"],
        "actionable_takeaways": ["c"],
    }


def test_parse_response_malformed_json_falls_back_to_raw_text() -> None:
    result = SummarizationService._parse_response("not json at all")

    assert result["summary"] == "not json at all"
    assert result["key_insights"] == []
    assert result["important_facts"] == []
    assert result["actionable_takeaways"] == []


def test_parse_response_missing_fields_default_to_empty_lists() -> None:
    result = SummarizationService._parse_response('{"summary": "Only summary present"}')

    assert result["summary"] == "Only summary present"
    assert result["key_insights"] == []
    assert result["important_facts"] == []
    assert result["actionable_takeaways"] == []


def test_build_user_prompt_includes_numbered_sources() -> None:
    doc = Document(page_content="Some passage text.", metadata={"source_title": "Title", "source_url": "https://x.com"})

    prompt = SummarizationService._build_user_prompt("What is X?", [(doc, 0.8)])

    assert "[1] Source: Title (https://x.com)" in prompt
    assert "Some passage text." in prompt
    assert "What is X?" in prompt
