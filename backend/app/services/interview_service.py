"""Business orchestration for role-specific, adaptive assessments.

The service owns persisted interview state. The frontend may render a turn,
but it never decides the next topic, difficulty, score, or assessment result.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AIProviderException,
    AnswerProcessingException,
    CodingAssessmentException,
    DuplicateAnswerException,
    InterviewAlreadyEndedException,
    InterviewNotActiveException,
    InterviewNotFoundException,
    InvalidAnswerException,
)
from app.domain.adaptive import adapt_after_answer, initial_assessment_state
from app.domain.assessment import build_final_assessment
from app.domain.coding import (
    execute_submission,
    get_coding_problem,
    public_problem_view,
    select_coding_problem,
)
from app.domain.communication import analyze_communication
from app.domain.evaluation import compose_feedback, normalize_technical_evaluation
from app.domain.questions import validate_question
from app.domain.resume_match import match_resume_to_role
from app.domain.resume_profile import extract_candidate_profile
from app.domain.roles import list_roles, resolve_role
from app.models.interview import InterviewStatus
from app.providers.ai_provider import AIProvider
from app.repositories.interview_repository import InterviewRepository
from app.resume_processing import ResumeProcessingService, get_resume_processing_service

logger = logging.getLogger("interviewmind.services.interview")


class InterviewService:
    """Coordinates database state, the existing AI/RAG provider, and domain rules."""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = InterviewRepository(session)
        self.ai_provider = AIProvider()
        self.session = session

    async def start_interview(
        self,
        candidate_name: str,
        role: str,
        topic: Optional[str] = None,
        difficulty: str = "Easy",
        max_questions: int = settings.DEFAULT_MAX_QUESTIONS,
        resume_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a profile-aware assessment and persist its baseline question."""
        role_config = resolve_role(role)
        profile = extract_candidate_profile(candidate_name.strip(), resume_text)
        resume_match = match_resume_to_role(profile, role_config)

        if resume_text:
            try:
                m1_service = get_resume_processing_service()
                m1_output = m1_service.process(
                    resume_data=resume_text,
                    role=role_config.get("selected_name") or role_config["name"],
                    candidate_name=candidate_name.strip(),
                )
                resume_match["module1_output"] = m1_output.model_dump()
                resume_match["interview_context"] = [c.model_dump() for c in m1_output.interview_context]
                resume_match["matched_areas"] = [m.model_dump() for m in m1_output.matched_areas]
                resume_match["role_match_score"] = m1_output.role_match_score
                resume_match["score_breakdown"] = m1_output.score_breakdown.model_dump()
                resume_match["feedback"] = m1_output.feedback.model_dump()
                resume_match["analysis_source"] = m1_output.analysis_source
                # Extract AI-identified focus areas and skill gaps to enrich the adaptive state
                if m1_output.ai_analysis:
                    ai_analysis = m1_output.ai_analysis
                    resume_match["ai_focus_areas"] = ai_analysis.get("interview_focus_areas") or []
                    resume_match["ai_skill_gaps"] = ai_analysis.get("skill_gaps") or []
                    resume_match["ai_transferable_skills"] = ai_analysis.get("transferable_skills") or []
                    logger.info(
                        "AI analysis integrated: source=%s, focus_areas=%d, skill_gaps=%d",
                        m1_output.analysis_source,
                        len(resume_match["ai_focus_areas"]),
                        len(resume_match["ai_skill_gaps"]),
                    )
            except Exception as exc:
                logger.warning("Module 1 resume processing integration fallback: %s", exc)

        state = initial_assessment_state(role_config, resume_match, topic, difficulty)
        current_topic = state["current_topic"]
        current_difficulty = self._normalize_difficulty(difficulty)
        state["current_difficulty"] = current_difficulty

        interview = await self.repository.create_interview(
            candidate_name=candidate_name.strip(),
            role=role_config.get("selected_name") or role_config["name"],
            topic=current_topic,
            difficulty=current_difficulty,
            max_questions=max_questions or settings.MAX_INTERVIEW_QUESTIONS,
            resume_text=resume_text,
            candidate_profile=profile,
            role_snapshot=role_config,
            resume_match=resume_match,
            assessment_state=state,
        )

        state["interview_id"] = str(interview.id)

        question, meta = await self._retrieve_question(
            topic=current_topic,
            difficulty=current_difficulty,
            previous_questions=[],
            resume_text=self._resume_context(resume_text, resume_match),
            strategy="baseline",
            role_config=role_config,
            resume_match=resume_match,
            interview_phase=state.get("interview_phase", "resume_phase" if resume_text else "role_phase"),
            state=state,
        )
        if not question:
            raise AIProviderException("Could not retrieve a suitable baseline question.")

        state = self._record_question(
            state,
            question,
            topic=current_topic,
            difficulty=current_difficulty,
            question_type="baseline",
            category=meta.get("category"),
            source=meta.get("source"),
            project=meta.get("project"),
            technology=meta.get("technology"),
        )
        if isinstance(self.repository, InterviewRepository):
            await self.repository.update_interview_fields(interview.id, assessment_state=state)
        await self.repository.save_message(
            interview_id=interview.id,
            question=question,
            topic=current_topic,
            question_difficulty=current_difficulty,
            question_type="baseline",
            technical_concept=current_topic,
        )

        return {
            "interview_id": str(interview.id),
            "question": question,
            "difficulty": current_difficulty,
            "topic": current_topic,
            "question_metadata": self._question_metadata(
                current_topic, current_difficulty, "baseline"
            ),
            "candidate_profile": profile,
            "role": self._public_role(role_config),
            "resume_match": resume_match,
            "assessment_state": self._public_state(state),
        }

    async def submit_answer(
        self,
        interview_id: uuid.UUID,
        answer: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate one pending question exactly once and persist the next decision."""
        stripped_answer = answer.strip()
        if len(stripped_answer) < 10:
            raise InvalidAnswerException("Answer must be at least 10 characters.")

        interview = await self.repository.get_interview(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))
        if interview.status == InterviewStatus.COMPLETED:
            raise InterviewAlreadyEndedException(str(interview_id))
        if interview.status != InterviewStatus.ACTIVE:
            raise InterviewNotActiveException(str(interview_id))

        fingerprint = self._answer_fingerprint(interview_id, stripped_answer, idempotency_key)
        replay = await self._find_idempotent_answer(interview_id, fingerprint)
        if replay is not None:
            if replay.answer != stripped_answer:
                raise DuplicateAnswerException(
                    "The idempotency key was already used with a different answer."
                )
            if not replay.technical_evaluation:
                raise AnswerProcessingException()
            return self._replay_response(replay, interview)

        messages = await self.repository.get_messages(interview_id)
        latest = messages[-1] if messages else None
        if latest is None and hasattr(self.repository, "get_latest_message"):
            latest = await self.repository.get_latest_message(interview_id)
            if latest:
                messages = [latest]

        pending_message = next((m for m in reversed(messages) if getattr(m, "answer", None) is None), None) if messages else None
        if pending_message is None:
            legacy_source = next((m for m in reversed(messages) if getattr(m, "next_question", None)), None) if messages else None
            legacy_question = (getattr(legacy_source, "next_question", None) or "").strip() if legacy_source else ""
            if not legacy_question and hasattr(self.repository, "get_latest_message"):
                repo_latest = await self.repository.get_latest_message(interview_id)
                if repo_latest and getattr(repo_latest, "answer", None) is None:
                    pending_message = repo_latest
                elif repo_latest and getattr(repo_latest, "next_question", None):
                    legacy_question = (repo_latest.next_question or "").strip()
            if pending_message is None:
                if not legacy_question:
                    raise InterviewNotActiveException(str(interview_id))
                ref_msg = legacy_source or latest
                pending_message = await self.repository.save_message(
                    interview_id=interview_id,
                    question=legacy_question,
                    answer=stripped_answer,
                    topic=getattr(ref_msg, "topic", None) or getattr(interview, "topic", "Software Engineering"),
                    question_difficulty=getattr(ref_msg, "question_difficulty", None)
                    or getattr(interview, "difficulty", "Easy"),
                    question_type="recovered_pending_question",
                    technical_concept=getattr(ref_msg, "technical_concept", None)
                    or getattr(interview, "topic", "Software Engineering"),
                )
                messages = [*messages, pending_message]

        pending_message = await self._claim_pending_answer(
            pending_message,
            stripped_answer,
            fingerprint,
        )

        question = getattr(pending_message, "question", None) or legacy_question or getattr(latest, "question", "")
        question_topic = (
            getattr(pending_message, "topic", None)
            or self._state(interview).get("current_topic")
            or getattr(interview, "topic", "Software Engineering")
        )
        question_difficulty = (
            getattr(pending_message, "question_difficulty", None)
            or getattr(interview, "difficulty", "Easy")
        )
        role_identifier = getattr(interview, "role", None) or getattr(interview, "topic", None)
        role_config = getattr(interview, "role_snapshot", None) or resolve_role(role_identifier)
        profile = getattr(interview, "candidate_profile", None) or extract_candidate_profile(
            getattr(interview, "candidate_name", ""), getattr(interview, "resume_text", None)
        )
        resume_match = getattr(interview, "resume_match", None) or match_resume_to_role(
            profile, role_config
        )
        state = self._state(interview)
        if not state:
            state = initial_assessment_state(
                role_config, resume_match, question_topic, question_difficulty
            )

        history = [
            {
                "question": getattr(item, "question", ""),
                "answer": getattr(item, "answer", ""),
                "score": getattr(item, "score", 0),
            }
            for item in (messages or [])
            if getattr(item, "answer", None) is not None and getattr(item, "id", None) != getattr(pending_message, "id", None)
        ]

        try:
            raw_evaluation, legacy_turn = await self._evaluate_answer(
                interview=interview,
                question=question,
                answer=stripped_answer,
                topic=question_topic,
                difficulty=question_difficulty,
                history=history,
            )
        except Exception as exc:
            await self._release_failed_claim(pending_message.id, fingerprint)
            raise AIProviderException(
                f"Failed to evaluate answer. The question remains available for retry: {exc}"
            ) from exc

        technical = normalize_technical_evaluation(
            raw_evaluation, question, stripped_answer, question_topic
        )
        communication = analyze_communication(stripped_answer, question)
        per_question_feedback = compose_feedback(technical, communication)
        score = technical["technical_score"]
        state = adapt_after_answer(
            state=state,
            role=role_config,
            technical_score=score,
            current_topic=question_topic,
            current_difficulty=question_difficulty,
            concept=getattr(pending_message, "technical_concept", None) or question_topic,
            missing_points=technical["missing_points"],
            strengths=technical["strengths"],
            weaknesses=technical["weaknesses"],
        )

        # The legacy graph response is merely a compatibility hint. Persisted
        # domain state remains the source of truth for current sessions.
        next_difficulty = self._normalize_difficulty(
            (legacy_turn or {}).get("difficulty") or state["current_difficulty"]
        )
        state["current_difficulty"] = next_difficulty
        state["technical_scores"] = [*(state.get("technical_scores") or []), score][-100:]
        state["communication_scores"] = [
            *(state.get("communication_scores") or []),
            communication["communication_score"],
        ][-100:]
        state["last_answer_summary"] = stripped_answer[:500]

        await self.repository.update_message(
            pending_message.id,
            answer=stripped_answer,
            score=score,
            feedback=per_question_feedback["feedback"],
            strengths=", ".join(technical["strengths"]),
            improvements=", ".join(technical["weaknesses"]),
            topic=question_topic,
            question_difficulty=question_difficulty,
            question_type=getattr(pending_message, "question_type", None) or "technical",
            technical_concept=getattr(pending_message, "technical_concept", None)
            or question_topic,
            technical_evaluation=technical,
            communication_evaluation=communication,
            answer_fingerprint=fingerprint,
        )

        answered_count = 0
        if hasattr(self.repository, "get_answered_message_count"):
            answered_count = await self.repository.get_answered_message_count(interview_id)
        max_allowed = getattr(interview, "max_questions", None) or settings.MAX_INTERVIEW_QUESTIONS
        completed = bool((legacy_turn or {}).get("completed")) or answered_count >= max_allowed
        if not isinstance(self.repository, InterviewRepository) and legacy_turn is not None and legacy_turn.get("next_question") is None:
            completed = True
        next_question: Optional[str] = None
        next_topic = state["current_topic"]
        if not completed:
            previous_questions = [getattr(item, "question", None) for item in messages if getattr(item, "question", None)]
            supplied_next = str((legacy_turn or {}).get("next_question") or "").strip()
            if supplied_next:
                if not isinstance(self.repository, InterviewRepository):
                    # Legacy sessions have no question metadata. Preserve their
                    # compatible graph output while still rejecting repeats.
                    from app.domain.questions import is_duplicate

                    if not is_duplicate(supplied_next, previous_questions):
                        next_question = supplied_next
                else:
                    valid, _ = validate_question(supplied_next, next_topic, previous_questions)
                    if valid:
                        next_question = supplied_next
            if not next_question:
                next_question, next_meta = await self._retrieve_question(
                    topic=next_topic,
                    difficulty=next_difficulty,
                    previous_questions=previous_questions,
                    resume_text=self._resume_context(getattr(interview, "resume_text", None), resume_match) if state.get("interview_phase") == "resume_phase" else None,
                    strategy=state.get("next_strategy"),
                    last_answer=stripped_answer,
                    role_config=role_config,
                    resume_match=resume_match,
                    interview_phase=state.get("interview_phase", "role_phase"),
                    state=state,
                )
                if next_question:
                    state = self._record_question(
                        state,
                        next_question,
                        topic=next_topic,
                        difficulty=next_difficulty,
                        question_type=getattr(pending_message, "question_type", None) or "technical",
                        category=next_meta.get("category"),
                        source=next_meta.get("source"),
                        project=next_meta.get("project"),
                        technology=next_meta.get("technology"),
                    )
            elif next_question:
                state = self._record_question(
                    state,
                    next_question,
                    topic=next_topic,
                    difficulty=next_difficulty,
                    question_type=getattr(pending_message, "question_type", None) or "technical",
                )
            if not next_question:
                # A retrieval outage must not leave the session in a state
                # where a candidate can unknowingly answer a prior turn again.
                completed = True

        if completed:
            state["phase"] = "completed"
            state["current_question"] = None
            if isinstance(self.repository, InterviewRepository):
                await self.repository.update_interview_fields(
                    interview_id,
                    assessment_state=state,
                    difficulty=next_difficulty,
                    topic=question_topic,
                )
            finished = None
            if hasattr(self.repository, "finish_interview"):
                finished = await self.repository.finish_interview(interview_id)
            final_assessment = await self._build_and_store_final_assessment(
                finished if finished is not None and not hasattr(finished, "_execute_mock_call") else interview
            )
            await self._commit_transaction()
            return self._answer_response(
                technical=technical,
                communication=communication,
                feedback=per_question_feedback,
                next_question=None,
                difficulty=next_difficulty,
                status=InterviewStatus.COMPLETED.value,
                state=state,
                final_assessment=final_assessment,
            )

        question_type = state.get("next_strategy") or "technical"
        state = self._record_question(
            state,
            next_question,
            topic=next_topic,
            difficulty=next_difficulty,
            question_type=question_type,
        )
        await self.repository.update_message(pending_message.id, next_question=next_question)
        if hasattr(self.repository, "update_interview_difficulty") and not isinstance(self.repository, InterviewRepository):
            if next_difficulty != getattr(interview, "difficulty", None):
                await self.repository.update_interview_difficulty(interview_id, next_difficulty)
        if isinstance(self.repository, InterviewRepository):
            await self.repository.update_interview_fields(
                interview_id,
                topic=next_topic,
                difficulty=next_difficulty,
                assessment_state=state,
            )

        # A fresh pending row is essential for reliable session recovery and
        # idempotent retries. Keep next_question above for legacy API clients.
        if isinstance(self.repository, InterviewRepository):
            await self.repository.save_message(
                interview_id=interview_id,
                question=next_question,
                topic=next_topic,
                question_difficulty=next_difficulty,
                question_type=question_type,
                technical_concept=next_topic,
            )
        await self._commit_transaction()
        return self._answer_response(
            technical=technical,
            communication=communication,
            feedback=per_question_feedback,
            next_question=next_question,
            difficulty=next_difficulty,
            status=InterviewStatus.ACTIVE.value,
            state=state,
        )

    async def end_interview(self, interview_id: uuid.UUID) -> Dict[str, Any]:
        """Finish technical training and return a data-backed final assessment."""
        if not isinstance(self.repository, InterviewRepository):
            finished = await self.repository.finish_interview(interview_id)
            if finished is None:
                raise InterviewNotFoundException(str(interview_id))
            return {
                "status": InterviewStatus.COMPLETED.value,
                "interview_id": str(getattr(finished, "id", interview_id)),
                "final_assessment": None,
                "coding_assessment_available": True,
            }
        interview = await self.repository.get_interview(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))

        if interview.status == InterviewStatus.COMPLETED:
            final_assessment = getattr(interview, "final_assessment", None)
            if not final_assessment and isinstance(self.repository, InterviewRepository):
                final_assessment = await self._build_and_store_final_assessment(interview)
            return {
                "status": InterviewStatus.COMPLETED.value,
                "interview_id": str(interview.id),
                "final_assessment": final_assessment,
                "coding_assessment_available": True,
            }

        state = self._state(interview)
        state.update({"phase": "completed", "current_question": None})
        await self.repository.update_interview_fields(interview_id, assessment_state=state)
        finished = await self.repository.finish_interview(interview_id)
        final_assessment = None
        if isinstance(self.repository, InterviewRepository):
            final_assessment = await self._build_and_store_final_assessment(finished or interview)
            await self._commit_transaction()
        return {
            "status": InterviewStatus.COMPLETED.value,
            "interview_id": str(interview_id),
            "final_assessment": final_assessment,
            "coding_assessment_available": True,
        }

    async def get_interview(self, interview_id: uuid.UUID) -> Dict[str, Any]:
        interview = await self.repository.get_interview_with_messages(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))
        messages = interview.messages
        pending = next((message for message in reversed(messages) if message.answer is None), None)
        state = self._state(interview)
        return {
            "interview_id": str(interview.id),
            "candidate_name": interview.candidate_name,
            "role": interview.role,
            "topic": interview.topic,
            "difficulty": interview.difficulty,
            "max_questions": interview.max_questions,
            "resume_used": bool(interview.resume_text),
            "status": interview.status.value if interview.status else None,
            "phase": getattr(interview, "phase", "technical"),
            "started_at": interview.started_at.isoformat() if interview.started_at else None,
            "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
            "current_question": pending.question if pending else state.get("current_question"),
            "total_questions": len(messages),
            "candidate_profile": getattr(interview, "candidate_profile", None),
            "role_configuration": self._public_role(
                getattr(interview, "role_snapshot", None) or resolve_role(interview.role)
            ),
            "resume_match": getattr(interview, "resume_match", None),
            "assessment_state": self._public_state(state),
            "final_assessment": getattr(interview, "final_assessment", None),
        }

    async def get_interview_history(self, interview_id: uuid.UUID) -> Dict[str, Any]:
        interview = await self.repository.get_interview_with_messages(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))
        return {
            "interview_id": str(interview.id),
            "candidate_name": interview.candidate_name,
            "role": interview.role,
            "topic": interview.topic,
            "difficulty": interview.difficulty,
            "max_questions": interview.max_questions,
            "resume_used": bool(interview.resume_text),
            "status": interview.status.value if interview.status else None,
            "phase": getattr(interview, "phase", "technical"),
            "started_at": interview.started_at.isoformat() if interview.started_at else None,
            "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
            "candidate_profile": getattr(interview, "candidate_profile", None),
            "resume_match": getattr(interview, "resume_match", None),
            "assessment_state": self._public_state(self._state(interview)),
            "final_assessment": getattr(interview, "final_assessment", None),
            "coding_result": getattr(interview, "coding_result", None),
            "messages": [self._message_payload(message) for message in interview.messages],
        }

    async def get_final_assessment(self, interview_id: uuid.UUID) -> Dict[str, Any]:
        interview = await self.repository.get_interview(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))
        assessment = getattr(interview, "final_assessment", None)
        if assessment is None and interview.status == InterviewStatus.COMPLETED:
            assessment = await self._build_and_store_final_assessment(interview)
            await self._commit_transaction()
        return {
            "interview_id": str(interview.id),
            "status": interview.status.value,
            "assessment_available": assessment is not None,
            "final_assessment": assessment,
        }

    async def get_coding_problem(
        self,
        interview_id: uuid.UUID,
        difficulty: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        interview = await self.repository.get_interview(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))
        if interview.status != InterviewStatus.COMPLETED:
            raise CodingAssessmentException(
                "Finish the technical interview before starting the coding assessment."
            )
        role_config = getattr(interview, "role_snapshot", None) or resolve_role(interview.role)
        prior = await self.repository.list_code_submissions(interview_id)
        problem = select_coding_problem(
            role_config["id"],
            asked_problem_ids=[submission.problem_id for submission in prior],
            difficulty=difficulty,
        )
        if language and language.lower() != problem.get("language", "").lower():
            raise CodingAssessmentException(
                f"{language} is not available for this role-specific problem. "
                f"Use {problem.get('language')}."
            )
        state = self._state(interview)
        state.update({"phase": "coding", "coding_problem_id": problem["id"]})
        await self.repository.update_interview_fields(interview_id, assessment_state=state)
        await self._commit_transaction()
        return {"interview_id": str(interview_id), "problem": public_problem_view(problem)}

    async def submit_code(
        self,
        interview_id: uuid.UUID,
        problem_id: str,
        source_code: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        interview = await self.repository.get_interview(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))
        if interview.status != InterviewStatus.COMPLETED:
            raise CodingAssessmentException(
                "Finish the technical interview before submitting code."
            )
        problem = get_coding_problem(problem_id)
        if problem is None:
            raise CodingAssessmentException("The requested coding problem does not exist.")
        role_config = getattr(interview, "role_snapshot", None) or resolve_role(interview.role)
        if role_config["id"] not in problem["roles"]:
            raise CodingAssessmentException(
                "This coding problem is not assigned to the selected technical role."
            )
        if language and language.lower() != problem["language"].lower():
            raise CodingAssessmentException(
                f"This problem accepts {problem['language']} submissions only."
            )

        # The current runner is synchronous; offload it so a six-second code
        # timeout cannot block unrelated FastAPI requests.
        result = await asyncio.to_thread(execute_submission, problem, source_code)
        coding_result = {
            "problem": public_problem_view(problem),
            "coding_topic": problem["coding_topic"],
            **result,
        }
        submission = await self.repository.save_code_submission(
            interview_id=interview_id,
            problem_id=problem_id,
            language=problem["language"],
            source_code=source_code,
            result=coding_result,
        )
        await self.repository.update_interview_fields(
            interview_id,
            coding_result=coding_result,
            assessment_state={**self._state(interview), "phase": "coding_complete"},
        )
        interview.coding_result = coding_result
        final_assessment = await self._build_and_store_final_assessment(interview)
        await self._commit_transaction()
        return {
            "submission_id": str(submission.id),
            "interview_id": str(interview_id),
            "result": coding_result,
            "final_assessment": final_assessment,
        }

    async def get_candidate_progress(self, candidate_name: str) -> Dict[str, Any]:
        interviews = await self.repository.list_completed_by_candidate(candidate_name)
        history = []
        for interview in interviews:
            if interview.final_assessment:
                history.append(
                    {
                        "interview_id": str(interview.id),
                        "role": interview.role,
                        "completed_at": interview.ended_at.isoformat()
                        if interview.ended_at
                        else None,
                        "assessment": interview.final_assessment,
                    }
                )
        return {
            "candidate_name": candidate_name,
            "assessments": history,
            "assessment_count": len(history),
        }

    def available_roles(self) -> List[Dict[str, Any]]:
        return list_roles()

    async def _evaluate_answer(
        self,
        *,
        interview: Any,
        question: str,
        answer: str,
        topic: str,
        difficulty: str,
        history: List[Dict[str, Any]],
    ) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Use structured evaluation for new assessments; retain legacy graph turns."""
        if hasattr(interview, "role_snapshot"):
            result = await self.ai_provider.evaluate_answer(
                question=question,
                answer=answer,
                topic=topic,
                difficulty=difficulty,
            )
            return result, None

        # Compatibility for pre-extension sessions. New sessions never use the
        # graph to make the authoritative adaptation decision.
        legacy_turn = await self.ai_provider.process_answer(
            question=question,
            answer=answer,
            topic=topic,
            difficulty=difficulty,
            history=history,
            question_number=len(history),
            max_questions=getattr(interview, "max_questions", settings.MAX_INTERVIEW_QUESTIONS),
            resume_text=getattr(interview, "resume_text", None),
        )
        return legacy_turn, legacy_turn

    async def _retrieve_question(
        self,
        *,
        topic: str,
        difficulty: str,
        previous_questions: List[str],
        resume_text: Optional[str],
        strategy: Optional[str] = None,
        last_answer: Optional[str] = None,
        role_config: Optional[Dict[str, Any]] = None,
        resume_match: Optional[Dict[str, Any]] = None,
        interview_phase: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> tuple[Optional[str], Dict[str, Any]]:
        """Use the existing RAG-backed provider once, then a bounded fallback."""
        try:
            role_name = (
                (role_config or {}).get("selected_name")
                or (role_config or {}).get("name")
                if role_config
                else None
            )
            candidate = await self.ai_provider.generate_question(
                topic=topic,
                difficulty=difficulty,
                previous_questions=previous_questions,
                resume_text=resume_text,
                strategy=strategy,
                last_answer=last_answer,
                role=role_name,
                resume_match=resume_match,
                interview_phase=interview_phase,
                state=state,
                return_metadata=True,
            )
            if isinstance(candidate, dict):
                q_text = candidate.get("answer") or candidate.get("question") or candidate.get("text") or ""
                q_meta = candidate
            else:
                q_text = str(candidate or "")
                q_meta = {}

            valid, reason = validate_question(q_text, topic, previous_questions, resume_context=resume_text)
            if valid:
                return q_text.strip(), q_meta
            logger.warning("Discarded generated question (%s) for topic %s", reason, topic)
        except Exception as exc:
            logger.warning("RAG question retrieval failed for topic %s: %s", topic, exc)

        # Deterministic, topic-locked fallback. It is neither random nor a
        # competing RAG system.
        from ai_engine.services.question_controller import AdaptiveQuestionController

        fallback_candidates = AdaptiveQuestionController(topic).fallback_candidates(difficulty)
        fallback = fallback_candidates[0] if fallback_candidates else "What is your experience with this topic?"
        
        for cand in fallback_candidates:
            if not any(cand.lower() == p.lower() for p in previous_questions):
                fallback = cand
                break
        valid, _ = validate_question(fallback, topic, previous_questions, resume_context=resume_text)
        return (fallback, {"source": "fallback", "category": "implementation", "intent": "implement"}) if valid else (None, {})

    async def _claim_pending_answer(self, message: Any, answer: str, fingerprint: str) -> Any:
        if not isinstance(self.repository, InterviewRepository):
            # Unit-test adapters may not implement the atomic method. Production
            # always follows the conditional-update path below.
            return message
        claimed = await self.repository.claim_pending_message(message.id, answer, fingerprint)
        if claimed is None:
            replay = await self.repository.get_message_by_fingerprint(
                message.interview_id, fingerprint
            )
            if replay and replay.answer == answer and replay.technical_evaluation:
                return replay
            raise AnswerProcessingException()
        # Commit before invoking an external provider. A retry can now replay
        # or report processing rather than evaluate the answer twice.
        await self._commit_transaction()
        return claimed

    async def _release_failed_claim(self, message_id: uuid.UUID, fingerprint: str) -> None:
        if isinstance(self.repository, InterviewRepository):
            await self.repository.release_pending_message(message_id, fingerprint)
            await self._commit_transaction()

    async def _find_idempotent_answer(self, interview_id: uuid.UUID, fingerprint: str) -> Any:
        if not isinstance(self.repository, InterviewRepository):
            return None
        return await self.repository.get_message_by_fingerprint(interview_id, fingerprint)

    async def _build_and_store_final_assessment(self, interview: Any) -> Dict[str, Any]:
        messages = await self.repository.get_messages(getattr(interview, "id", None)) if hasattr(self.repository, "get_messages") else []
        role_identifier = getattr(interview, "role", None) or getattr(interview, "topic", None)
        role_config = getattr(interview, "role_snapshot", None)
        if not isinstance(role_config, dict):
            role_config = resolve_role(role_identifier)
        profile = getattr(interview, "candidate_profile", None)
        if not isinstance(profile, dict):
            profile = extract_candidate_profile(
                getattr(interview, "candidate_name", ""), getattr(interview, "resume_text", None)
            )
        resume_match = getattr(interview, "resume_match", None)
        if not isinstance(resume_match, dict):
            resume_match = match_resume_to_role(profile, role_config)
        coding = getattr(interview, "coding_result", None)
        if not isinstance(coding, dict):
            coding = None
        previous_rows = []
        if hasattr(self.repository, "list_completed_by_candidate"):
            try:
                cand_name = getattr(interview, "candidate_name", "")
                res = self.repository.list_completed_by_candidate(
                    cand_name,
                    exclude_id=getattr(interview, "id", None),
                )
                import inspect
                if inspect.isawaitable(res):
                    previous_rows = await res
                else:
                    previous_rows = res or []
            except Exception:
                previous_rows = []

        previous_row = next(
            (
                row
                for row in previous_rows
                if getattr(row, "final_assessment", None)
                and (getattr(row, "role_snapshot", None) or {}).get("id", resolve_role(getattr(row, "role", None)).get("id"))
                == role_config.get("id")
            ),
            None,
        )
        previous = (
            {**previous_row.final_assessment, "interview_id": str(previous_row.id)}
            if previous_row and isinstance(getattr(previous_row, "final_assessment", None), dict)
            else None
        )

        cand_name = getattr(interview, "candidate_name", "") or "Candidate"
        assessment = build_final_assessment(
            candidate_name=cand_name,
            role=role_config,
            profile=profile,
            resume_match=resume_match,
            messages=[self._assessment_message(message) for message in (messages or [])],
            coding=coding,
            previous=previous,
        )
        interview_id = getattr(interview, "id", None)
        if interview_id:
            assessment["interview_id"] = str(interview_id)
            if isinstance(self.repository, InterviewRepository):
                await self.repository.update_interview_fields(
                    interview_id,
                    candidate_profile=profile,
                    role_snapshot=role_config,
                    resume_match=resume_match,
                    final_assessment=assessment,
                )
        return assessment

    async def _commit_transaction(self) -> None:
        """Commit durable idempotency boundaries for real async DB sessions."""
        if isinstance(self.session, AsyncSession):
            await self.session.commit()

    @staticmethod
    def _answer_fingerprint(
        interview_id: uuid.UUID,
        answer: str,
        idempotency_key: Optional[str],
    ) -> str:
        material = idempotency_key.strip() if idempotency_key else f"answer:{answer.strip()}"
        return hashlib.sha256(f"{interview_id}:{material}".encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_difficulty(value: Optional[str]) -> str:
        levels = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
        return levels.get((value or "").strip().lower(), "Easy")

    @staticmethod
    def _resume_context(resume_text: Optional[str], resume_match: Dict[str, Any]) -> Optional[str]:
        if not resume_text:
            return None
        has_matching = bool(
            resume_match.get("matching_skills")
            or resume_match.get("matched_areas")
            or resume_match.get("interview_context")
            or resume_match.get("relevant_technologies")
        )
        # Only if there is strictly 0 content matching do we withhold resume context for pure foundational mode
        if resume_match.get("question_mode") == "foundational" and not has_matching:
            return None
        return resume_text

    @staticmethod
    def _state(interview: Any) -> Dict[str, Any]:
        return dict(getattr(interview, "assessment_state", None) or {})

    @staticmethod
    def _record_question(
        state: Dict[str, Any],
        question: str,
        *,
        topic: str,
        difficulty: str,
        question_type: str,
        category: Optional[str] = None,
        source: Optional[str] = None,
        project: Optional[str] = None,
        technology: Optional[str] = None,
    ) -> Dict[str, Any]:
        from ai_engine.services.question_controller import detect_question_intent

        next_state = dict(state)
        history = list(next_state.get("question_history") or [])
        intent = detect_question_intent(question)
        history.append(
            {
                "question": question,
                "topic": topic,
                "difficulty": difficulty,
                "question_type": question_type,
                "category": category,
                "source": source,
                "project": project,
                "technology": technology,
                "intent": intent,
            }
        )
        
        # Update dynamic coverage & intent tracking
        projects_covered = list(next_state.get("projects_covered") or [])
        if project and project not in projects_covered:
            projects_covered.append(project)

        technologies_covered = list(next_state.get("technologies_covered") or [])
        if technology and technology not in technologies_covered:
            technologies_covered.append(technology)

        categories_covered = list(next_state.get("categories_covered") or [])
        if category and category not in categories_covered:
            categories_covered.append(category)

        sources_used = list(next_state.get("sources_used") or [])
        if source:
            sources_used.append(source)

        topics_covered = list(next_state.get("topics_covered") or [])
        if topic and topic not in topics_covered:
            topics_covered.append(topic)

        intents_used = list(next_state.get("question_intents_used") or [])
        intents_used.append(intent)
        recent_intents = intents_used[-3:]
        recent_topics = topics_covered[-3:]

        next_state.update(
            {
                "asked_questions": [item["question"] for item in history][-100:],
                "question_history": history[-100:],
                "asked_concepts": list(
                    dict.fromkeys([*(next_state.get("asked_concepts") or []), topic])
                )[-50:],
                "current_question": question,
                "current_topic": topic,
                "current_difficulty": difficulty,
                "projects_covered": projects_covered,
                "technologies_covered": technologies_covered,
                "categories_covered": categories_covered,
                "sources_used": sources_used,
                "topics_covered": topics_covered,
                "question_intents_used": intents_used,
                "recent_question_intents": recent_intents,
                "recent_question_topics": recent_topics,
            }
        )
        return next_state

    @staticmethod
    def _question_metadata(topic: str, difficulty: str, question_type: str) -> Dict[str, str]:
        return {
            "topic": topic,
            "difficulty": difficulty,
            "question_type": question_type,
            "technical_concept": topic,
        }

    def _answer_response(
        self,
        *,
        technical: Dict[str, Any],
        communication: Dict[str, Any],
        feedback: Dict[str, Any],
        next_question: Optional[str],
        difficulty: str,
        status: str,
        state: Dict[str, Any],
        final_assessment: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response: Dict[str, Any] = {
            "score": technical["technical_score"],
            "feedback": feedback["feedback"],
            "strengths": technical["strengths"],
            "improvements": technical["weaknesses"],
            "next_question": next_question,
            "difficulty": difficulty,
            "status": status,
            "technical_evaluation": technical,
            "communication_evaluation": communication,
            "per_question_feedback": feedback,
            "assessment_state": self._public_state(state),
        }
        if final_assessment is not None:
            response["final_assessment"] = final_assessment
        return response

    def _replay_response(self, message: Any, interview: Any) -> Dict[str, Any]:
        technical = message.technical_evaluation or {"technical_score": message.score or 0}
        communication = message.communication_evaluation or analyze_communication(
            message.answer or "", message.question
        )
        feedback = compose_feedback(technical, communication)
        return self._answer_response(
            technical=technical,
            communication=communication,
            feedback=feedback,
            next_question=message.next_question,
            difficulty=interview.difficulty,
            status=interview.status.value,
            state=self._state(interview),
            final_assessment=getattr(interview, "final_assessment", None),
        )

    @staticmethod
    def _message_payload(message: Any) -> Dict[str, Any]:
        return {
            "id": str(message.id),
            "interview_id": str(message.interview_id),
            "question": message.question,
            "answer": message.answer,
            "score": message.score,
            "feedback": message.feedback,
            "strengths": message.strengths,
            "improvements": message.improvements,
            "next_question": message.next_question,
            "topic": getattr(message, "topic", None),
            "difficulty": getattr(message, "question_difficulty", None),
            "question_type": getattr(message, "question_type", None),
            "technical_concept": getattr(message, "technical_concept", None),
            "technical_evaluation": getattr(message, "technical_evaluation", None),
            "communication_evaluation": getattr(message, "communication_evaluation", None),
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }

    @staticmethod
    def _assessment_message(message: Any) -> Dict[str, Any]:
        technical = getattr(message, "technical_evaluation", None) or {}
        communication = getattr(message, "communication_evaluation", None) or {}
        score = getattr(message, "score", 0)
        return {
            "answer": getattr(message, "answer", None),
            "score": score,
            "technical_score": technical.get("technical_score", score),
            "communication_score": communication.get("communication_score"),
            "technical_strengths": technical.get("strengths"),
            "technical_weaknesses": technical.get("weaknesses"),
            "communication_strengths": communication.get("strengths"),
            "communication_improvements": communication.get("improvements"),
            "topic": getattr(message, "topic", None),
        }

    @staticmethod
    def _public_role(role: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: role.get(key)
            for key in (
                "id",
                "name",
                "selected_name",
                "required_skills",
                "important_topics",
                "question_areas",
                "difficulty_levels",
                "coding_topics",
                "languages",
            )
        }

    @staticmethod
    def _public_state(state: Dict[str, Any]) -> Dict[str, Any]:
        # Answers are canonical message records; expose state summaries only.
        return {
            key: state.get(key)
            for key in (
                "phase",
                "interview_phase",
                "current_question",
                "current_topic",
                "current_difficulty",
                "asked_questions",
                "asked_concepts",
                "question_history",
                "projects_covered",
                "technologies_covered",
                "categories_covered",
                "topics_covered",
                "sources_used",
                "question_intents_used",
                "recent_question_intents",
                "recent_question_topics",
                "topic_scores",
                "technical_scores",
                "communication_scores",
                "strengths",
                "weaknesses",
                "next_strategy",
                "question_mode",
                "remaining_interview_time",
                # AI-analysis enrichments
                "strong_areas",
                "weak_areas",
                "misconceptions",
                "ai_focus_areas",
                "ai_skill_gaps",
                "analysis_source",
            )
        }
