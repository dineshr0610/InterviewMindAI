from typing import TypedDict


class InterviewState(TypedDict):

    candidate_name: str

    topic: str

    difficulty: str

    question: str

    answer: str

    score: int

    feedback: str

    strengths: str

    improvements: str

    question_number: int

    max_questions: int

    interview_completed: bool

    history: list