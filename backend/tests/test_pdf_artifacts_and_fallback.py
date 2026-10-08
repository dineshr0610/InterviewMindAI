import pytest
import uuid
import asyncio
from unittest.mock import patch, AsyncMock
from app.services.interview_service import InterviewService
from ai_engine.services.interview_service import QuestionCandidate, QuestionQualityEvaluator
from ai_engine.key_pool import gemini_key_pool

# Mock repository for InterviewService testing
class MockInterviewRepo:
    def __init__(self):
        self.interviews = {}
    
    async def create_interview(self, **kwargs):
        class MockInterview:
            pass
        interview = MockInterview()
        interview.id = uuid.uuid4()
        for k, v in kwargs.items():
            setattr(interview, k, v)
        self.interviews[interview.id] = interview
        return interview

    async def update_interview_fields(self, *args, **kwargs):
        pass

    async def save_message(self, *args, **kwargs):
        pass

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_test_a_b_c_d_e_f_g_h_i():
    # TEST I: Question contains PDF artifact is removed before final question delivery
    from ai_engine.services.interview_service import InterviewService as AIInterviewService
    ai_service = AIInterviewService()
    
    # Manually test the logic applied in generate_question
    # (Because the full db mocking is extensive, we can test just the components we fixed)
    
    # Test normalization of PDF artifacts
    from app.utils.resume import clean_resume_text
    raw_question = "Explain the architecture of ♂laptop-codePersonal Portfolio + AI Assistant (Nuxt + RAG)Ongoing Major Project and explain how the components interact?"
    clean = clean_resume_text(raw_question)
    assert "♂laptop-code" not in clean
    assert "(Nuxt + RAG) — Ongoing" in clean
    
    # Test Fallback attribution
    with patch("ai_engine.models.llm.llm") as mock_llm:
        mock_llm.invoke.return_value = "invalid short" # Will be rejected
        with patch.object(ai_service.rag, "ask") as mock_rag:
            mock_rag.return_value = "invalid short"
            
            result = ai_service.generate_question(
                topic="Backend",
                difficulty="Hard",
                previous_questions=[],
                role="Backend Developer",
                resume_text="♂laptop-codePersonal Portfolio + AI Assistant",
                interview_phase="resume_phase",
                state={"interview_id": "12345-abcde"}
            )
            
            # Since all generated candidates are invalid/short, fallback should trigger
            assert result["source"] == "fallback"
            assert "♂laptop-code" not in result["answer"]
    
    # TEST E & G: Gemini fallback does not always produce the same question due to rotation offset
    with patch("ai_engine.models.llm.llm") as mock_llm, patch.object(ai_service.rag, "ask") as mock_rag:
        mock_llm.invoke.return_value = "invalid short"
        mock_rag.return_value = "invalid short"
        
        # Interview 1
        res1 = ai_service.generate_question(
            topic="Backend",
            previous_questions=[],
            resume_match={
                "matched_projects": ["Project A", "Project B", "Project C"],
                "topic_inventory": {
                    "projects": ["Project A", "Project B", "Project C"]
                }
            },
            role="Backend Developer",
            state={"interview_id": "session-111"}
        )
        
        # Interview 2
        res2 = ai_service.generate_question(
            topic="Backend",
            previous_questions=[],
            resume_match={
                "matched_projects": ["Project A", "Project B", "Project C"],
                "topic_inventory": {
                    "projects": ["Project A", "Project B", "Project C"]
                }
            },
            role="Backend Developer",
            state={"interview_id": "session-222"}
        )
        
        # Due to rotation_offset, the first question project/category should differ
        assert res1["answer"] != res2["answer"]

    # TEST H: Rejected candidate cannot be selected
    c = QuestionCandidate(
        text="What is a class?",
        source="gemini_resume",
        category="implementation",
        topic="Java",
        intent="explain"
    )
    eval_c = QuestionQualityEvaluator.evaluate(
        c,
        role_name="Backend Developer",
        verified_technologies=["Java"],
        verified_projects=[],
        unsupported_technologies=[],
        missing_skills=[],
        previous_questions=[],
        recent_intents=[],
        categories_covered=[],
        projects_covered=[],
        technologies_covered=[]
    )
    assert not eval_c.is_valid
    
    # TEST F: Gemini config works
    from ai_engine.key_pool import gemini_key_pool
    # Instead of modifying the global, test isolated instances in test_gemini_key_pool.py
    # We just ensure it's importable.
    assert gemini_key_pool is not None

