"""
Interview API routes.
Handles all interview lifecycle operations: start, answer, get details, history, end, resume upload.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.schemas.interview import (
    AnswerRequest,
    CodeSubmissionRequest,
    CodingProblemRequest,
    StartInterviewRequest,
)
from app.services.interview_service import InterviewService
from app.utils.response import success_response
from app.resume_processing import (
    Module1AnalysisRequest,
    Module1Output,
    get_resume_processing_service,
)
from app.utils.resume import (
    ALLOWED_MIME_TYPES,
    MAX_RESUME_SIZE_BYTES,
    extract_text_from_file,
    extract_text_from_pdf,
)

logger = logging.getLogger("interviewmind.routes.interview")
router = APIRouter(prefix="/api/interview", tags=["Interview"])


async def get_interview_service(
    db: AsyncSession = Depends(get_db_session),
) -> InterviewService:
    """Dependency that creates an InterviewService instance with an active DB session."""
    return InterviewService(session=db)


@router.get(
    "/roles",
    response_model=dict,
    summary="List configurable technical roles",
)
async def get_roles(
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Return role requirements used by resume matching and question selection."""
    return success_response({"roles": service.available_roles()})


@router.post(
    "/start",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new interview",
    description="Creates a new interview session and returns the initial question.",
)
async def start_interview(
    request: StartInterviewRequest,
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Start a new mock interview session."""
    result = await service.start_interview(
        candidate_name=request.candidate_name,
        role=request.role,
        topic=request.topic,
        difficulty=request.difficulty,
        resume_text=request.resume_text,
    )
    logger.info(
        "Interview started: id=%s, candidate=%s, role=%s, topic=%s, resume_used=%s",
        result.get("interview_id"),
        request.candidate_name,
        request.role,
        request.topic,
        bool(request.resume_text),
    )
    return success_response(result, status_code=status.HTTP_201_CREATED)


@router.post(
    "/resume/upload",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Upload and parse a resume (PDF or DOCX)",
    description="Accepts a PDF or DOCX resume, extracts and cleans its text, and optionally performs Module 1 analysis if role is provided.",
)
async def upload_resume(
    file: UploadFile = File(...),
) -> dict:
    """Upload a PDF or DOCX resume and extract its text for personalized interviews."""
    filename = file.filename or "resume.pdf"
    lower_fn = filename.lower()
    is_valid_ext = lower_fn.endswith(".pdf") or lower_fn.endswith(".docx") or lower_fn.endswith(".doc")
    
    if not is_valid_ext or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid PDF or DOCX resume.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="The resume file is too large. Maximum size is 5 MB.",
        )

    resume_text = extract_text_from_pdf(content)
    if not resume_text:
        resume_text = extract_text_from_file(content, filename=filename)
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Unable to read this resume. Please upload a valid text-based PDF or DOCX file.",
        )

    logger.info(
        "Resume uploaded and parsed: filename=%s, chars=%d",
        filename,
        len(resume_text),
    )

    return success_response(
        {
            "filename": filename,
            "resume_text": resume_text,
            "char_count": len(resume_text),
        }
    )


@router.post(
    "/resume/analyze",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Analyze resume against selected technical role (Module 1)",
    description="Performs deterministic scoring, multi-level matching, evidence extraction, and interview context generation.",
)
async def analyze_resume(
    request: Module1AnalysisRequest,
) -> dict:
    """Module 1 Endpoint: Analyze resume against a single selected role."""
    if not request.role or not request.role.strip():
        raise HTTPException(
            status_code=400,
            detail="Please select a target technical role.",
        )

    if not request.resume_text or not request.resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text is required for analysis.",
        )

    service = get_resume_processing_service()
    try:
        result = service.process(
            resume_data=request.resume_text,
            role=request.role,
            candidate_name=request.candidate_name,
        )
        res_dump = result.model_dump()
        import json
        with open("scratch/latest_analyze_response.json", "w") as f:
            json.dump(res_dump, f, indent=2)
        return success_response(res_dump)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Resume analysis failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during resume analysis: {str(exc)}",
        )


@router.post(
    "/answer",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Submit an answer and get evaluation",
    description="Submit an answer for evaluation and receive score, feedback, and the next question.",
)
async def submit_answer(
    request: AnswerRequest,
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Submit an answer for AI evaluation and receive follow-up question."""
    result = await service.submit_answer(
        interview_id=request.interview_id,
        answer=request.answer,
        idempotency_key=request.idempotency_key,
    )
    logger.info(
        "Answer evaluated: interview_id=%s, score=%d",
        request.interview_id,
        result.get("score", 0),
    )
    return success_response(result)


@router.get(
    "/candidate/{candidate_name}/progress",
    response_model=dict,
    summary="Get completed assessment history for a candidate",
)
async def get_candidate_progress(
    candidate_name: str,
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    return success_response(
        await service.get_candidate_progress(candidate_name=candidate_name)
    )


@router.get(
    "/{interview_id}/assessment",
    response_model=dict,
    summary="Get the stored final assessment",
)
async def get_final_assessment(
    interview_id: UUID = Path(..., description="UUID of the interview session"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    return success_response(
        await service.get_final_assessment(interview_id=interview_id)
    )


@router.post(
    "/{interview_id}/coding/problem",
    response_model=dict,
    summary="Get a role-specific coding assessment",
)
async def get_coding_problem(
    request: CodingProblemRequest,
    interview_id: UUID = Path(..., description="UUID of the completed interview"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    return success_response(
        await service.get_coding_problem(
            interview_id=interview_id,
            difficulty=request.difficulty,
            language=request.language,
        )
    )


@router.post(
    "/{interview_id}/coding/submit",
    response_model=dict,
    summary="Run and review a coding assessment submission",
)
async def submit_code(
    request: CodeSubmissionRequest,
    interview_id: UUID = Path(..., description="UUID of the completed interview"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    return success_response(
        await service.submit_code(
            interview_id=interview_id,
            problem_id=request.problem_id,
            source_code=request.source_code,
            language=request.language,
        )
    )


@router.get(
    "/{interview_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get interview details",
    description="Retrieve status and current state of a specific interview session by ID.",
)
async def get_interview(
    interview_id: UUID = Path(..., description="UUID of the interview session"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Get interview details by ID."""
    result = await service.get_interview(interview_id=interview_id)
    return success_response(result)


@router.get(
    "/{interview_id}/history",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get interview history",
    description="Retrieve the complete transcript of Q&As for a specific interview session.",
)
async def get_interview_history(
    interview_id: UUID = Path(..., description="UUID of the interview session"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Get full interview Q&A history transcript."""
    result = await service.get_interview_history(interview_id=interview_id)
    return success_response(result)


@router.post(
    "/{interview_id}/end",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="End an interview",
    description="Conclude an active interview session.",
)
async def end_interview(
    interview_id: UUID = Path(..., description="UUID of the interview session to end"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """End an active interview session."""
    result = await service.end_interview(interview_id=interview_id)
    logger.info("Interview ended: id=%s", interview_id)
    return success_response(result)
