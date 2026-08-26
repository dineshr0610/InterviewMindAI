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
