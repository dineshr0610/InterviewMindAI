import pytest
from ai_engine.utils.question_extractor import extract_and_normalize_question
from scripts.audit_extraction_fidelity import check_verbatim

def test_verbatim_extraction_fidelty():
    original = """### Technical Interview Question
**Role**: Developer
**Question**: Explain how Redis caching works.
**Ideal Answer**: ..."""
    res = extract_and_normalize_question(original)
    assert check_verbatim(original, res["normalized_question"]) == "EXACT_EXTRACTION"
    
def test_markdown_only_normalization():
    original = "**Question**: What is **polymorphism**? \n\n**Scoring**:"
    res = extract_and_normalize_question(original)
    assert res["normalized_question"] == "What is **polymorphism**?"
    # It preserves internal markdown (like **polymorphism**) but stops correctly.
    
def test_no_synthetic_sentence_generation():
    # If the user provides a very short, non-templated question, it shouldn't add templates.
    original = "**Question**: How does garbage collection work?\n**Evaluation**:"
    res = extract_and_normalize_question(original)
    assert "Explain how" not in res["normalized_question"]
    assert res["normalized_question"] == "How does garbage collection work?"
    
def test_role_category_not_injected():
    original = """**Role**: DevOps Engineer
**Category**: CI/CD
**Question**: What is a Jenkins pipeline?
**Ideal Answer**: ..."""
    res = extract_and_normalize_question(original)
    assert "DevOps Engineer" not in res["normalized_question"]
    assert "CI/CD" not in res["normalized_question"]
    
def test_question_without_question_mark_is_valid():
    original = "**Question**: Explain the CAP theorem.\n**Evaluation**:"
    res = extract_and_normalize_question(original)
    assert res["classification"] == "VALID_EXTRACTED"
    assert res["normalized_question"] == "Explain the CAP theorem."
    
def test_tutorial_without_question_is_not_converted():
    original = "This is a tutorial on Binary Search. It is O(log n)."
    res = extract_and_normalize_question(original)
    assert res["classification"] == "NO_QUESTION_FOUND"
    
def test_original_wording_is_preserved():
    original = "**Question**:  What are the trade-offs of   microservices ?  \n**Evaluation Rubric**:"
    res = extract_and_normalize_question(original)
    assert res["normalized_question"] == "What are the trade-offs of microservices ?"
