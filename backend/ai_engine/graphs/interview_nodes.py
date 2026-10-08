from ai_engine.graphs.interview_state import InterviewState

from ai_engine.services.interview_service import InterviewService
from ai_engine.services.evaluation_service import EvaluationService
from ai_engine.services.question_controller import (
    DEEPENING_STRATEGIES,
    choose_next_strategy,
)


service = InterviewService()
evaluation_service = EvaluationService()


def generate_question(state: InterviewState):

    history = state.get("history", [])
    response = service.generate_question(
        state.get("topic", ""),
        state.get("difficulty", "Medium"),
        [entry["question"] for entry in history if entry.get("question")],
        resume_text=state.get("resume_text"),
        strategy=state.get("next_strategy"),
        last_answer=state.get("answer"),
        state=state,
    )

    state["question"] = response.get("answer", "")

    return state


def evaluate_answer(state: InterviewState):

    result = evaluation_service.evaluate(
        state["question"],
        state["answer"],
        state["topic"],
        state["difficulty"],
    )

    state["score"] = result.get("score", 0)
    state["feedback"] = result.get("feedback", "")
    state["strengths"] = result.get("strengths", [])
    state["improvements"] = result.get("improvements", [])
    
    demonstrated = result.get("demonstrated_concepts", [])
    missing = result.get("missing_concepts", [])
    misconceptions = result.get("misconceptions", [])
    
    state["demonstrated_competencies"] = state.get("demonstrated_competencies", []) + demonstrated
    state["weak_competencies"] = state.get("weak_competencies", []) + missing
    state["misconceptions"] = state.get("misconceptions", []) + misconceptions

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

    max_questions = state.get("max_questions") or 0
    if max_questions and state["question_number"] >= max_questions:
        state["interview_completed"] = True

    difficulty_order = ["Easy", "Medium", "Hard"]
    current_index = difficulty_order.index(state["difficulty"])
    if state["score"] >= 8:
        state["difficulty"] = difficulty_order[min(current_index + 1, 2)]
    elif state["score"] <= 4:
        state["difficulty"] = difficulty_order[max(current_index - 1, 0)]

    # Decide what a real interviewer would ask next based on the candidate's
    # last answer (score) and how deeply we have already probed this subject.
    follow_up_depth = state.get("follow_up_depth") or 0
    has_misconception = bool(state.get("misconceptions"))
    strategy = choose_next_strategy(state["score"], follow_up_depth, has_misconception)

    # Track and cap how many consecutive related questions we ask so the
    # interview stays balanced and eventually transitions topics.
    if strategy in DEEPENING_STRATEGIES:
        follow_up_depth += 1
    else:
        follow_up_depth = 0
        state["misconceptions"] = [] # Clear misconceptions when changing topics

    state["follow_up_depth"] = follow_up_depth
    state["next_strategy"] = strategy
    
    # Sync Aliases for Adaptive Strategy Context
    state["current_strategy"] = strategy
    state["current_difficulty"] = state["difficulty"]
    state["recent_questions"] = [entry["question"] for entry in history][-3:] if history else []
    state["recent_answers"] = [entry["answer"] for entry in history][-3:] if history else []
    state["recent_evaluations"] = [f"Score: {entry['score']}" for entry in history][-3:] if history else []

    return state


def should_continue(state: InterviewState):

    if state["interview_completed"]:
        return "finish"

    return "continue"
