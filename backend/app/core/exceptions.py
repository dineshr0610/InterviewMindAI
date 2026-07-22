"""
Custom exception classes for the application.
Provides semantic error types with HTTP status codes and error codes for structured error responses.
"""

from __future__ import annotations


class BaseInterviewException(Exception):
    """Base exception for all custom interview domain exceptions."""

    def __init__(
        self,
        message: str = "An application error occurred.",
        error_code: str = "UNKNOWN_ERROR",
        status_code: int = 400,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class InterviewNotFoundException(BaseInterviewException):
    """Raised when an interview ID is not found in the database."""

    def __init__(self, interview_id: str) -> None:
        super().__init__(
            message=f"Interview not found: {interview_id}",
            error_code="INTERVIEW_NOT_FOUND",
            status_code=404,
        )
        self.interview_id = interview_id


class InterviewNotActiveException(BaseInterviewException):
    """Raised when trying to interact with an interview that is not active."""

    def __init__(self, interview_id: str) -> None:
        super().__init__(
            message=f"Interview is not active: {interview_id}",
            error_code="INTERVIEW_NOT_ACTIVE",
            status_code=400,
        )
        self.interview_id = interview_id


class InterviewAlreadyEndedException(BaseInterviewException):
    """Raised when trying to end or modify an already-completed interview."""

    def __init__(self, interview_id: str) -> None:
        super().__init__(
            message=f"Interview already ended: {interview_id}",
            error_code="INTERVIEW_ALREADY_ENDED",
            status_code=400,
        )
        self.interview_id = interview_id


class InvalidAnswerException(BaseInterviewException):
    """Raised when the submitted answer fails validation rules."""

    def __init__(self, message: str = "Invalid answer provided.") -> None:
        super().__init__(
            message=message,
            error_code="INVALID_ANSWER",
            status_code=422,
        )


class AIProviderException(BaseInterviewException):
    """Raised when the AI provider or engine fails to generate a response."""

    def __init__(self, message: str = "AI service is currently unavailable.") -> None:
        super().__init__(
            message=message,
            error_code="AI_UNAVAILABLE",
            status_code=503,
        )


class DatabaseException(BaseInterviewException):
    """Raised on database connection or execution failures."""

    def __init__(self, message: str = "Database operation failed.") -> None:
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
        )
