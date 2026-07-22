from ai_engine.graphs.interview_state import InterviewState

from ai_engine.services.interview_service import InterviewService
from ai_engine.services.evaluation_service import EvaluationService


service = InterviewService()
evaluation_service = EvaluationService()


def generate_question(state: InterviewState):

    response = service.generate_question(
        state["topic"],
        state["difficulty"]
    )

    state["question"] = response["answer"]

    return state


def evaluate_answer(state: InterviewState):

    result = evaluation_service.evaluate(
        state["question"],
        state["answer"]
    )

    state["score"] = result["score"]
    state["feedback"] = result["feedback"]
    state["strengths"] = result["strengths"]
    state["improvements"] = result["improvements"]

    return state


def update_interview_state(state: InterviewState):

    history = state["history"]

    history.append(
        {
            "question": state["question"],
            "answer": state["answer"],
            "score": state["score"]
        }
    )

    state["history"] = history

    state["question_number"] += 1

    if state["question_number"] > state["max_questions"]:
        state["interview_completed"] = True

    if state["score"] >= 8:
        state["difficulty"] = "Medium"

    elif state["score"] <= 4:
        state["difficulty"] = "Easy"

    return state


def should_continue(state: InterviewState):

    if state["interview_completed"]:
        return "finish"

    return "continue"