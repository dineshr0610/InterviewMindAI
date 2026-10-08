import pytest
from ai_engine.services.interview_service import parse_llm_question_json

def test_parse_llm_question_clean_json_accepted():
    raw_text = '{"question": "How would you manage shared state?"}'
    assert parse_llm_question_json(raw_text) == "How would you manage shared state?"

def test_parse_llm_question_json_fence_accepted():
    raw_text = '```json\n{"question": "React is great! But how does it work?"}\n```'
    assert parse_llm_question_json(raw_text) == "React is great! But how does it work?"

def test_parse_llm_question_conversational_prefix_with_fence_accepted():
    # Policy: if the model explicitly uses a markdown code fence, we extract it.
    raw_text = 'Here is the question you requested:\n```\n{"question": "What is React?"}\n```'
    assert parse_llm_question_json(raw_text) == "What is React?"

def test_parse_llm_question_conversational_prefix_raw_json_rejected():
    # Policy: if no code fence is used, we strictly require the entire string to be JSON.
    raw_text = 'Here is your question: {"question": "What is React?"}'
    assert parse_llm_question_json(raw_text) is None

def test_parse_llm_question_plain_conversational_rejected():
    raw_text = "Sure, here is your question: How does React work?"
    assert parse_llm_question_json(raw_text) is None

def test_parse_llm_question_malformed_json_rejected():
    raw_text = '{"question": "How does React work?"'
    assert parse_llm_question_json(raw_text) is None

def test_parse_llm_question_multiple_json_objects_rejected():
    # Without code fence
    raw_text = '{"question": "First?"}{"question": "Second?"}'
    assert parse_llm_question_json(raw_text) is None
    
    # With code fence (json.loads fails on multiple root objects)
    raw_text = '```json\n{"question": "First?"}\n{"question": "Second?"}\n```'
    assert parse_llm_question_json(raw_text) is None

def test_parse_llm_question_missing_question_rejected():
    raw_text = '{"answer": "How does React work?"}'
    assert parse_llm_question_json(raw_text) is None

def test_parse_llm_question_null_question_rejected():
    raw_text = '{"question": null}'
    assert parse_llm_question_json(raw_text) is None

def test_parse_llm_question_empty_question_rejected():
    raw_text = '{"question": ""}'
    assert parse_llm_question_json(raw_text) is None
    
    raw_text_whitespace = '{"question": "   "}'
    assert parse_llm_question_json(raw_text_whitespace) is None

def test_parse_llm_question_not_string_rejected():
    raw_text = '{"question": 12345}'
    assert parse_llm_question_json(raw_text) is None

def test_parse_llm_question_markdown_wrapped_invalid_rejected():
    raw_text = "```json\n{\n  \"something_else\": \"Test\"\n}\n```\nHere you go."
    assert parse_llm_question_json(raw_text) is None
