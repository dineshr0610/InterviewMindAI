import pytest
from unittest.mock import patch, MagicMock

from ai_engine.services.semantic_duplicate_detector import SemanticDuplicateDetector
from ai_engine.services.interview_service import QuestionCandidate, QuestionQualityEvaluator

# Mock embeddings:
# Suppose dimension is 3
# "React race condition" = [1, 0, 0]
# "Concurrent React state updates" = [0.99, 0.1, 0] -> high sim
# "React reconciliation" = [0, 1, 0]
# "Vue reactivity" = [0, 0, 1]

def mock_embed_document(text):
    text = text.lower()
    if "race condition" in text or "concurrently" in text:
        return [1.0, 0.0, 0.0]
    elif "reconciliation" in text:
        return [0.0, 1.0, 0.0]
    elif "vue" in text:
        return [0.0, 0.0, 1.0]
    return [0.5, 0.5, 0.5]

def mock_embed_documents(texts):
    return [mock_embed_document(t) for t in texts]

@patch("ai_engine.embeddings.embedding_provider.embedding_provider.embed_documents", side_effect=mock_embed_documents)
@patch("ai_engine.embeddings.embedding_provider.embedding_provider.embed_document", side_effect=mock_embed_document)
def test_semantic_duplicate_detected(mock_doc, mock_docs):
    previous = ["What problems can occur when multiple React state updates happen concurrently?"]
    detector = SemanticDuplicateDetector(previous)
    
    cand = QuestionCandidate(
        text="How would you handle race conditions when updating React state?",
        source="gemini",
        category="implementation",
        topic="React",
        intent="implementation" # Same intent
    )
    detector.prefetch_candidate_embeddings([cand.text])
    
    with patch("ai_engine.services.interview_service.detect_question_intent", return_value="implementation"):
        eval_cand = QuestionQualityEvaluator.evaluate(
            cand,
            role_name="Frontend",
            verified_technologies=["React"],
            verified_projects=[],
            unsupported_technologies=[],
            missing_skills=[],
            previous_questions=previous,
            recent_intents=[],
            categories_covered=[],
            projects_covered=[],
            technologies_covered=[],
            semantic_detector=detector
        )
    
    assert not eval_cand.is_valid
    assert "semantic_duplicate" in eval_cand.rejection_reason

@patch("ai_engine.embeddings.embedding_provider.embedding_provider.embed_documents", side_effect=mock_embed_documents)
@patch("ai_engine.embeddings.embedding_provider.embedding_provider.embed_document", side_effect=mock_embed_document)
def test_different_intent_not_rejected(mock_doc, mock_docs):
    # Same topic but different question intent
    previous = ["How does React reconciliation work?"]
    detector = SemanticDuplicateDetector(previous)
    
    cand = QuestionCandidate(
        text="Why can React reconciliation become expensive for large component trees?", # Semantic dup but...
        source="gemini",
        category="performance",
        topic="React",
        intent="performance" # Different intent
    )
    detector.prefetch_candidate_embeddings([cand.text])
    
    # We must patch detect_question_intent to return 'architecture' for previous question and 'performance' for candidate
    with patch("ai_engine.services.interview_service.detect_question_intent", side_effect=lambda x: "architecture" if "work" in x else "performance"):
        eval_cand = QuestionQualityEvaluator.evaluate(
            cand,
            role_name="Frontend",
            verified_technologies=["React"],
            verified_projects=[],
            unsupported_technologies=[],
            missing_skills=[],
            previous_questions=previous,
            recent_intents=[],
            categories_covered=[],
            projects_covered=[],
            technologies_covered=[],
            semantic_detector=detector
        )
    
    # Should NOT be rejected because intent differs
    assert eval_cand.is_valid
    assert eval_cand.generic_penalty > 0 # Got the penalty though

@patch("ai_engine.embeddings.embedding_provider.embedding_provider.embed_documents", side_effect=Exception("API Down"))
def test_embedding_failure_handled_safely(mock_docs):
    previous = ["How does React reconciliation work?"]
    detector = SemanticDuplicateDetector(previous)
    
    assert len(detector.previous_embeddings) == 0
    
    cand = QuestionCandidate(
        text="Can you explain how React hooks work and their use cases?",
        source="gemini",
        category="implementation",
        topic="React",
        intent="implementation"
    )
    detector.prefetch_candidate_embeddings([cand.text])
    
    eval_cand = QuestionQualityEvaluator.evaluate(
        cand,
        role_name="Frontend",
        verified_technologies=["React"],
        verified_projects=[],
        unsupported_technologies=[],
        missing_skills=[],
        previous_questions=previous,
        recent_intents=[],
        categories_covered=[],
        projects_covered=[],
        technologies_covered=[],
        semantic_detector=detector
    )
    
    # Still works, just skipped semantic dup check
    assert eval_cand.is_valid
