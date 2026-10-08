import pytest
from ai_engine.services.interview_service import QuestionQualityEvaluator, QuestionCandidate

def test_duplicate_prevention():
    cand = QuestionCandidate(
        text="How did you structure your backend Dockerfile?",
        source="follow_up",
        category="architecture",
        topic="Docker",
        intent="architecture",
        difficulty="Medium"
    )
    
    # Exact duplicate
    result = QuestionQualityEvaluator.evaluate(
        cand,
        role_name="Backend Developer",
        verified_technologies=["Docker"],
        verified_projects=["Project X"],
        unsupported_technologies=[],
        missing_skills=[],
        previous_questions=["How did you structure your backend Dockerfile?"],
        recent_intents=["architecture"],
        categories_covered=["architecture"],
        projects_covered=["Project X"],
        technologies_covered=["Docker"],
        last_answer="I used a multi-stage build.",
        strategy="follow_up",
        target_difficulty="Medium",
    )
    
    assert not result.is_valid
    assert "duplicate" in result.rejection_reason.lower()

def test_semantic_duplicate_rejection():
    # Same technology + Same intent should be rejected
    cand = QuestionCandidate(
        text="What was the architecture of your Docker setup?",
        source="follow_up",
        category="architecture",
        topic="Docker",
        intent="architecture",
        project="Project X",
        technology="Docker",
        difficulty="Medium"
    )
    
    result = QuestionQualityEvaluator.evaluate(
        cand,
        role_name="Backend Developer",
        verified_technologies=["Docker"],
        verified_projects=["Project X"],
        unsupported_technologies=[],
        missing_skills=[],
        previous_questions=["What is the architecture of your Docker setup?"],
        recent_intents=["architecture"],
        categories_covered=["architecture"],
        projects_covered=["Project X"],
        technologies_covered=["Docker"],
        last_answer="I used a multi-stage build.",
        strategy="follow_up",
        target_difficulty="Medium",
    )
    
    assert not result.is_valid
    assert "near duplicate" in result.rejection_reason.lower()

def test_same_technology_different_intent_allowed():
    # Same technology but different intent (e.g. debugging instead of architecture)
    cand = QuestionCandidate(
        text="What was the hardest bug you faced with Docker?",
        source="follow_up",
        category="debugging",
        topic="Docker",
        intent="debug",
        project="Project X",
        technology="Docker",
        difficulty="Medium"
    )
    
    result = QuestionQualityEvaluator.evaluate(
        cand,
        role_name="Backend Developer",
        verified_technologies=["Docker"],
        verified_projects=["Project X"],
        unsupported_technologies=[],
        missing_skills=[],
        previous_questions=["How did you structure your backend Dockerfile?"],
        recent_intents=["architecture"],
        categories_covered=["architecture"],
        projects_covered=["Project X"],
        technologies_covered=["Docker"],
        last_answer="I used a multi-stage build.",
        strategy="follow_up",
        target_difficulty="Medium",
    )
    
    assert result.is_valid

def test_hallucination_penalty():
    cand = QuestionCandidate(
        text="In your Kubernetes project, how did you handle pods?",
        source="gemini_resume",
        category="architecture",
        topic="Kubernetes",
        intent="architecture",
        difficulty="Medium"
    )
    
    result = QuestionQualityEvaluator.evaluate(
        cand,
        role_name="Backend Developer",
        verified_technologies=["Docker"],
        verified_projects=[],
        unsupported_technologies=["Kubernetes"], # Kubernetes is unsupported
        missing_skills=["Kubernetes"],
        previous_questions=[],
        recent_intents=[],
        categories_covered=[],
        projects_covered=[],
        technologies_covered=[],
        last_answer="",
        strategy="gemini_resume",
        target_difficulty="Medium",
    )
    
    assert not result.is_valid
    assert "unsupported claim" in result.rejection_reason.lower()

def test_hypothetical_missing_skill_allowed():
    cand = QuestionCandidate(
        text="If you needed to scale this with Kubernetes, how would you do it?",
        source="missing_skill",
        category="architecture",
        topic="Kubernetes",
        intent="architecture",
        difficulty="Medium"
    )
    
    result = QuestionQualityEvaluator.evaluate(
        cand,
        role_name="Backend Developer",
        verified_technologies=["Docker"],
        verified_projects=[],
        unsupported_technologies=["Kubernetes"],
        missing_skills=["Kubernetes"],
        previous_questions=[],
        recent_intents=[],
        categories_covered=[],
        projects_covered=[],
        technologies_covered=[],
        last_answer="",
        strategy="missing_skill",
        target_difficulty="Medium",
    )
    
    assert result.is_valid

def test_score_components():
    cand = QuestionCandidate(
        text="Can you explain your database indexing strategy?",
        source="gemini_resume",
        category="database",
        topic="PostgreSQL",
        intent="design",
        project="Project Y",
        technology="PostgreSQL",
        difficulty="Medium"
    )
    
    result = QuestionQualityEvaluator.evaluate(
        cand,
        role_name="Backend Developer",
        verified_technologies=["PostgreSQL"],
        verified_projects=["Project Y"],
        unsupported_technologies=[],
        missing_skills=[],
        previous_questions=[],
        recent_intents=[],
        categories_covered=[],
        projects_covered=[],
        technologies_covered=[],
        last_answer="",
        strategy="",
        target_difficulty="Medium",
        total_projects=1,
        total_technologies=1,
    )
    
    assert result.is_valid
    assert result.role_relevance > 0.0
    assert result.resume_relevance > 0.0
    assert result.interview_value > 0.0
    assert result.novelty > 0.0
    assert result.coverage_value > 0.0
    assert result.score > 0.0
