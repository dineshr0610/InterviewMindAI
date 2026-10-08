import pytest
from ai_engine.utils.question_extractor import extract_and_normalize_question

def test_extract_standard_markdown():
    content = """### Technical Interview Question: Java Collections Framework
**Role**: Java Developer
**Difficulty**: Medium
**Question**: Explain how ArrayList differs from LinkedList and when you would choose each.
**Ideal Model Answer**:
Blah blah..."""
    res = extract_and_normalize_question(content)
    assert res["classification"] == "VALID_EXTRACTED"
    assert res["normalized_question"] == "Explain how ArrayList differs from LinkedList and when you would choose each."

def test_extract_question_followed_by_ideal_answer():
    content = "**Question**: What is a race condition?\n\n**Ideal Answer**: When two threads..."
    res = extract_and_normalize_question(content)
    assert res["classification"] == "VALID_EXTRACTED"
    assert res["normalized_question"] == "What is a race condition?"

def test_extract_question_followed_by_evaluation_rubric():
    content = "**Question**: What is a race condition?\n\n**Evaluation Rubric**: 10/10..."
    res = extract_and_normalize_question(content)
    assert res["classification"] == "VALID_EXTRACTED"
    assert res["normalized_question"] == "What is a race condition?"

def test_extract_question_without_question_mark():
    content = "**Question**: Explain how garbage collection works in Java.\n**Ideal Answer**: ..."
    res = extract_and_normalize_question(content)
    assert res["classification"] == "VALID_EXTRACTED"
    assert res["normalized_question"] == "Explain how garbage collection works in Java."

def test_clean_question():
    content = "Explain how garbage collection works in Java."
    res = extract_and_normalize_question(content)
    assert res["classification"] == "ALREADY_CLEAN"
    assert res["normalized_question"] == "Explain how garbage collection works in Java."

def test_malformed_content():
    content = "Binary Search requires sorted data and repeatedly divides the search space."
    res = extract_and_normalize_question(content)
    assert res["classification"] == "NO_QUESTION_FOUND"
    assert res["normalized_question"] is None

def test_placeholder():
    content = "**Question**: How does {technology} work?\n**Ideal Answer**: ..."
    res = extract_and_normalize_question(content)
    assert res["classification"] == "PLACEHOLDER"
    assert res["normalized_question"] == "How does {technology} work?"

def test_multiline_question():
    content = "**Question**: Here is a scenario:\n\nYou are building a chat app.\nHow do you scale it?\n**Ideal Answer**: ..."
    res = extract_and_normalize_question(content)
    assert res["classification"] == "VALID_EXTRACTED"
    assert res["normalized_question"] == "Here is a scenario: You are building a chat app. How do you scale it?"

def test_technical_punctuation():
    content = "**Question**: What does the `__init__` method do in Python?\n**Ideal Answer**: ..."
    res = extract_and_normalize_question(content)
    assert res["classification"] == "VALID_EXTRACTED"
    assert res["normalized_question"] == "What does the `__init__` method do in Python?"

def test_multiple_possible_question_sections():
    content = "**Question**: First question?\n**Ideal Answer**: Answer.\n**Question**: Second question?\n**Scoring**: ..."
    res = extract_and_normalize_question(content)
    # Should probably just extract the first one, or flag as ambiguous/malformed
    assert res["classification"] == "VALID_EXTRACTED"
    assert res["normalized_question"] == "First question?"

def test_empty_content():
    res = extract_and_normalize_question("   \n   ")
    assert res["classification"] == "NO_QUESTION_FOUND"
    assert res["normalized_question"] is None
