"""
Comprehensive unit & integration tests for Phase 5:
- Local question bank loading and in-memory caching
- Canonical role normalization
- Role-aware deterministic local retrieval
- Difficulty and intent compatibility filtering
- Supabase-empty -> local question bank fallback
- Supabase-error -> local question bank fallback
- Resume + bank context reaching Gemini
- Bank-only generation
- Resume-only generation
- Follow-up generation
- Duplicate question prevention with retry
- Zero unrelated-role leakage
- Malformed local record resilience
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from ai_engine.vectorstores.supabase_store import SupabaseVectorRetriever
from ai_engine.services.question_bank_service import (
    QuestionBankService,
    get_question_bank_service,
    normalize_role,
    CANONICAL_ROLES,
    ROLE_BACKEND,
    ROLE_FRONTEND,
    ROLE_FULLSTACK,
    ROLE_PYTHON,
    ROLE_JAVA,
    ROLE_DEVOPS,
    ROLE_DATABASE,
    ROLE_DATA_ANALYST,
    ROLE_AI,
    ROLE_ML,
)
from ai_engine.services.rag_service import (
    RAGService,
    SOURCE_SUPABASE_VECTOR,
    SOURCE_LOCAL_BANK,
)
from ai_engine.services.interview_service import (
    InterviewService,
    SOURCE_SUPABASE_BANK,
    SOURCE_GEMINI_RESUME,
    SOURCE_FOLLOW_UP,
)


# ===========================================================================
# 1. Local Question Bank Service Tests
# ===========================================================================

class TestLocalQuestionBankService:
    """Tests for QuestionBankService loading, caching, and resilience."""

    def test_singleton_and_caching(self):
        """Service is a cached singleton that does not reparse on every call."""
        s1 = get_question_bank_service()
        s2 = get_question_bank_service()
        assert s1 is s2
        assert s1.count() >= 5000

    def test_malformed_record_handling(self, tmp_path):
        """Malformed or incomplete records in JSONL are safely skipped without crashing."""
        bad_jsonl = tmp_path / "corrupt_bank.jsonl"
        with open(bad_jsonl, "w", encoding="utf-8") as f:
            f.write('{"question": "How does the Python GIL affect threading performance in CPython?", "role": "Python Developer", "topic": "GIL"}\n')
            f.write('{"corrupt": true\n')  # JSON syntax error
            f.write('{"missing_question": true, "role": "Python Developer"}\n')  # Missing question
            f.write('{"question": "Too short", "role": "Python Developer"}\n')  # Question < 10 chars
            f.write('{"question": "What is the difference between asyncio and multiprocessing in Python?", "role": "Python Developer", "difficulty": "Hard"}\n')

        custom_service = QuestionBankService(jsonl_path=str(bad_jsonl))
        assert custom_service.count() == 2
        by_role = custom_service.get_by_role("Python Developer")
        assert len(by_role) == 2


# ===========================================================================
# 2. Role Normalization Tests
# ===========================================================================

class TestRoleNormalization:
    """Tests for single canonical role normalization function across variations."""

    @pytest.mark.parametrize(
        "raw_role, expected",
        [
            ("backend_developer", ROLE_BACKEND),
            ("Backend Developer", ROLE_BACKEND),
            ("backend developer", ROLE_BACKEND),
            ("FRONTEND_DEVELOPER", ROLE_FRONTEND),
            ("frontend developer", ROLE_FRONTEND),
            ("python_developer", ROLE_PYTHON),
            ("Python Developer", ROLE_PYTHON),
            ("full_stack_developer", ROLE_FULLSTACK),
            ("Full Stack Developer", ROLE_FULLSTACK),
            ("devops_engineer", ROLE_DEVOPS),
            ("DevOps Engineer", ROLE_DEVOPS),
            ("DevOps / Cloud Engineer", ROLE_DEVOPS),
            ("ai_engineer", ROLE_AI),
            ("AI Engineer", ROLE_AI),
            ("machine_learning_engineer", ROLE_ML),
            ("ml_engineer", ROLE_ML),
            ("ML Engineer", ROLE_ML),
            ("data_analyst", ROLE_DATA_ANALYST),
            ("Data Analyst", ROLE_DATA_ANALYST),
            ("database_developer", ROLE_DATABASE),
            ("Database Developer", ROLE_DATABASE),
            ("java_developer", ROLE_JAVA),
            ("Java Developer", ROLE_JAVA),
        ]
    )
    def test_canonical_role_normalization(self, raw_role: str, expected: str):
        assert normalize_role(raw_role) == expected

    def test_unknown_role_fallback(self):
        """Unrecognized roles fall back cleanly to Backend Developer."""
        assert normalize_role("unknown_custom_role") == ROLE_BACKEND
        assert normalize_role(None) == ROLE_BACKEND


# ===========================================================================
# 3. Retrieval Priority & Filtering Tests
# ===========================================================================

class TestLocalRetrievalFiltering:
    """Tests for role retrieval, technology/topic matching, and difficulty filtering."""

    @pytest.fixture
    def bank_service(self):
        return get_question_bank_service()

    def test_role_retrieval_all_ten_roles(self, bank_service):
        """Verify all 10 canonical roles have questions and can be retrieved."""
        for role in CANONICAL_ROLES:
            candidates = bank_service.retrieve_candidates(role=role, limit=5)
            assert len(candidates) > 0, f"Role {role} should have candidates"
            for c in candidates:
                assert normalize_role(c.get("role")) == role

    def test_no_unrelated_role_leakage(self, bank_service):
        """Never return questions from an unrelated role to fill candidate pool."""
        candidates = bank_service.retrieve_candidates(role=ROLE_DEVOPS, limit=10)
        assert len(candidates) > 0
        for c in candidates:
            assert normalize_role(c.get("role")) == ROLE_DEVOPS
            assert "React" not in c.get("question", "")

    def test_difficulty_filtering(self, bank_service):
        """Difficulty compatibility prioritization works."""
        hard_cands = bank_service.retrieve_candidates(
            role=ROLE_PYTHON,
            difficulty="Hard",
            limit=5,
        )
        assert len(hard_cands) > 0
        for c in hard_cands:
            assert c.get("difficulty", "").lower() == "hard"

    def test_skill_topic_retrieval(self, bank_service):
        """Technology / skill matching works deterministically."""
        cands = bank_service.retrieve_candidates(
            role=ROLE_BACKEND,
            technology="PostgreSQL",
            topic="Indexing",
            limit=5,
        )
        assert len(cands) > 0
        questions_text = " ".join(c.get("question", "").lower() for c in cands)
        assert "postgres" in questions_text or "index" in questions_text or "sql" in questions_text


# ===========================================================================
# 4. RAG Service Fallback Tests
# ===========================================================================

class TestRAGFallback:
    """Tests for Supabase-empty and Supabase-error fallback to local question bank."""

    def test_supabase_empty_triggers_local_fallback(self):
        """When Supabase vector search returns 0 documents, automatically fall back to local bank."""
        rag = RAGService()
        with patch.object(SupabaseVectorRetriever, "get_filtered_documents", return_value=[]):
            results = rag.ask(
                search_query="Python GIL and multiprocessing",
                role="Python Developer",
                technology="Python",
                limit=5,
            )
            assert len(results) > 0
            assert results[0]["source"] == SOURCE_LOCAL_BANK
            assert normalize_role(results[0]["metadata"]["role"]) == ROLE_PYTHON

    def test_supabase_error_triggers_local_fallback(self):
        """When Supabase raises an exception, automatically fall back to local bank without crashing."""
        rag = RAGService()
        with patch.object(SupabaseVectorRetriever, "get_filtered_documents", side_effect=RuntimeError("Supabase connection timeout")):
            results = rag.ask(
                search_query="Docker kubernetes deployments",
                role="DevOps Engineer",
                technology="Docker",
                limit=5,
            )
            assert len(results) > 0
            assert results[0]["source"] == SOURCE_LOCAL_BANK
            assert normalize_role(results[0]["metadata"]["role"]) == ROLE_DEVOPS

    def test_supabase_vector_used_when_available(self):
        """When Supabase returns usable documents, use Supabase vector retrieval."""
        rag = RAGService()
        mock_doc = SimpleNamespace(
            page_content="How does React Virtual DOM reconciliation work?",
            metadata={"role": "Frontend Developer", "similarity": 0.89},
        )
        with patch.object(SupabaseVectorRetriever, "get_filtered_documents", return_value=[mock_doc]):
            results = rag.ask(
                search_query="React reconciliation",
                role="Frontend Developer",
                limit=5,
            )
            assert len(results) == 1
            assert results[0]["source"] == SOURCE_SUPABASE_BANK
            assert "Virtual DOM" in results[0]["question"]


# ===========================================================================
# 5. Interview Service Generation Modes & Grounding Tests
# ===========================================================================

class TestInterviewServiceGeneration:
    """Tests for generation modes, resume grounding, duplicate prevention, and follow-ups."""

    def test_resume_plus_bank_context_reaches_gemini(self):
        """Retrieved bank context and resume facts reach Gemini prompt."""
        engine = InterviewService()
        sample_resume = "Alex Morgan\nBuilt real-time Kafka transaction processing pipeline with PostgreSQL."

        with patch("ai_engine.models.llm.llm") as mock_llm:
            mock_llm.invoke.return_value = SimpleNamespace(
                content='{"question": "In your Kafka transaction pipeline, how did you ensure exactly-once semantics with PostgreSQL?"}'
            )

            res = engine.generate_question(
                topic="Kafka",
                difficulty="Hard",
                role="Backend Developer",
                resume_text=sample_resume,
                interview_phase="resume_phase",
            )

            assert res is not None
            assert "Kafka" in res["answer"]
            assert res["source"] == SOURCE_GEMINI_RESUME
            prompt_called = mock_llm.invoke.call_args[0][0]
            assert "Kafka" in prompt_called
            assert "PostgreSQL" in prompt_called

    def test_bank_only_generation_without_resume(self):
        """When no resume is provided, bank-grounded generation functions smoothly."""
        engine = InterviewService()
        with patch("ai_engine.models.llm.llm") as mock_llm:
            mock_llm.invoke.return_value = SimpleNamespace(
                content='{"question": "How do you handle memory management and GIL in Python multi-threading?"}'
            )
            res = engine.generate_question(
                topic="Python Internals",
                difficulty="Hard",
                role="Python Developer",
                resume_text=None,
                interview_phase="role_phase",
            )
            assert res is not None
            assert len(res["answer"]) >= 15

    def test_follow_up_generation(self):
        """Candidate answer produces a targeted follow-up question."""
        engine = InterviewService()
        last_ans = "We used Redis cache with write-through pattern and 60-second TTL to reduce database query load."

        with patch("ai_engine.models.llm.llm") as mock_llm:
            mock_llm.invoke.return_value = SimpleNamespace(
                content='{"question": "With a write-through pattern in Redis, how did you handle cache invalidation during high concurrent writes?"}'
            )
            res = engine.generate_question(
                topic="Redis",
                difficulty="Hard",
                strategy="tradeoff",
                last_answer=last_ans,
                role="Backend Developer",
                previous_questions=["How did you optimize database queries?"],
            )
            assert res is not None
            assert res["source"] == SOURCE_FOLLOW_UP
            assert "Redis" in res["answer"] or "cache" in res["answer"].lower()

    def test_duplicate_prevention_triggers_retry(self):
        """Near-duplicate question triggers retry with alternate prompt."""
        engine = InterviewService()
        prev_q = "How does Python GIL affect multi-threading performance?"

        # First invoke returns duplicate, retry returns distinct question
        first_resp = SimpleNamespace(content='{"question": "How does Python GIL affect multi-threading performance?"}')
        retry_resp = SimpleNamespace(content='{"question": "What multiprocessing techniques can you use to bypass GIL limitations in CPU-bound Python tasks?"}')

        with patch("ai_engine.models.llm.llm") as mock_llm:
            mock_llm.invoke.side_effect = [first_resp, retry_resp]

            res = engine.generate_question(
                topic="Python GIL",
                difficulty="Medium",
                role="Python Developer",
                previous_questions=[prev_q],
                resume_text="Skills: Python",
                interview_phase="resume_phase",
            )

            assert res is not None
            # Verified that near duplicate was rejected and alternate question was chosen
            assert res["answer"] != prev_q
            assert mock_llm.invoke.call_count == 2
