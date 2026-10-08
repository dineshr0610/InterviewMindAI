from typing import TypedDict


class InterviewState(TypedDict):

    mode: str

    candidate_name: str

    topic: str

    difficulty: str

    question: str

    answer: str

    score: int

    feedback: str

    strengths: list[str]

    improvements: list[str]

    question_number: int

    max_questions: int

    interview_completed: bool

    history: list

    resume_text: str | None

    # Conversational-interviewer state used to decide what a real
    # interviewer would ask next, based on the candidate's last answer.
    next_strategy: str

    follow_up_depth: int

    # Adaptive Strategy State
    target_role: str
    demonstrated_competencies: list[str]
    weak_competencies: list[str]
    missing_resume_evidence: list[str]
    untested_competencies: list[str]
    recent_questions: list[str]
    recent_answers: list[str]
    recent_evaluations: list[str]
    current_strategy: str
    current_difficulty: str
    recent_rag_context: list[str]
    misconceptions: list[str]
