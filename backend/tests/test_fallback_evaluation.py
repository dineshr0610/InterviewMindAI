import pytest
import asyncio
from app.providers.ai_provider import AIProvider
from unittest.mock import patch, MagicMock

@pytest.fixture
def provider():
    # Force AI_ENGINE_AVAILABLE to True for tests, but mock the underlying service
    with patch("app.providers.ai_provider.AI_ENGINE_AVAILABLE", True):
        provider = AIProvider()
        # Mock eval_service to trigger timeouts or malformed JSON
        eval_mock = MagicMock()
        provider.eval_service = eval_mock
        yield provider

@pytest.mark.asyncio
async def test_empty_answer_fallback(provider):
    # Simulate eval_service throwing a TimeoutError
    provider.eval_service.evaluate.side_effect = TimeoutError("Simulated timeout")
    
    question = "Explain database indexing and how it improves lookup performance."
    answer = "   "
    
    result = await provider.evaluate_answer(question, answer, topic="database")
    
    assert result["score"] == 0.0

@pytest.mark.asyncio
async def test_lorem_ipsum_fallback(provider):
    provider.eval_service.evaluate.side_effect = TimeoutError()
    
    question = "What are the benefits and trade-offs of Redis caching?"
    answer = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit."
    
    result = await provider.evaluate_answer(question, answer, topic="caching")
    
    # Expected low score, not 8!
    assert result["score"] <= 1.0

@pytest.mark.asyncio
async def test_long_irrelevant_answer_fallback(provider):
    provider.eval_service.evaluate.side_effect = TimeoutError()
    
    question = "Explain database indexing."
    answer = "React is a great frontend library that uses components and state to render the DOM. Redis is also very fast and handles strings, lists, sets, and hashes. Concurrency in Go is handled by goroutines and channels."
    
    result = await provider.evaluate_answer(question, answer, topic="database")
    
    # Answer has tech words but not "database" or "indexing"
    assert result["score"] <= 2.0

@pytest.mark.asyncio
async def test_short_correct_answer_fallback(provider):
    provider.eval_service.evaluate.side_effect = TimeoutError()
    
    question = "Explain database indexing."
    answer = "Indexes improve lookup speed by using data structures like B-trees."
    
    result = await provider.evaluate_answer(question, answer, topic="database")
    
    assert result["score"] >= 4.0 # Should get a meaningful score

@pytest.mark.asyncio
async def test_partially_correct_answer_fallback(provider):
    provider.eval_service.evaluate.side_effect = TimeoutError()
    
    question = "Explain the differences between SQL and NoSQL databases."
    answer = "SQL is relational and uses tables. NoSQL is not."
    
    result = await provider.evaluate_answer(question, answer, topic="database")
    
    assert result["score"] >= 2.0
    assert result["score"] <= 6.0

@pytest.mark.asyncio
async def test_strong_technically_relevant_answer_fallback(provider):
    provider.eval_service.evaluate.side_effect = TimeoutError()
    
    question = "What are the benefits and trade-offs of Redis caching?"
    answer = "Redis caching benefits include ultra-fast in-memory data access, reducing load on primary databases, and supporting complex data structures. Trade-offs include increased memory costs, potential data staleness, and the complexity of managing cache invalidation."
    
    result = await provider.evaluate_answer(question, answer, topic="caching")
    
    assert result["score"] >= 7.0

@pytest.mark.asyncio
async def test_anti_gaming_property(provider):
    provider.eval_service.evaluate.side_effect = TimeoutError()
    
    question = "Explain database indexing."
    
    answer_a = "Indexing improves database lookup performance."
    result_a = await provider.evaluate_answer(question, answer_a, topic="database")
    
    answer_b = answer_a + " " + "Lorem ipsum dolor sit amet " * 50
    result_b = await provider.evaluate_answer(question, answer_b, topic="database")
    
    # Adding meaningless characters should not substantially increase score
    # Score might go up by at most 1 point if it crosses a length threshold incidentally,
    # but since lorem ipsum has no tech vocab, tech_vocab_count won't increase much
    assert result_b["score"] - result_a["score"] <= 1.0

@pytest.mark.asyncio
async def test_gemini_malformed_json_fallback(provider):
    # Simulate eval_service throwing ValueError
    provider.eval_service.evaluate.side_effect = ValueError("Malformed JSON")
    
    question = "What is HTTP?"
    answer = "Hypertext transfer protocol."
    
    result = await provider.evaluate_answer(question, answer, topic="networking")
    
    assert "score" in result
    assert result["score"] >= 2.0

@pytest.mark.asyncio
async def test_gemini_valid_evaluation(provider):
    # Simulate a successful LLM evaluation
    provider.eval_service.evaluate.return_value = {
        "score": 9.0,
        "feedback": "Excellent answer.",
        "strengths": ["Clear"],
        "improvements": ["None"]
    }
    
    question = "What is HTTP?"
    answer = "Hypertext transfer protocol."
    
    result = await provider.evaluate_answer(question, answer, topic="networking")
    
    assert result["score"] == 9.0
    assert result["feedback"] == "Excellent answer."
