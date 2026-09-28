"""Smoke test proving the API provider's orchestration graph executes."""

from __future__ import annotations

from unittest.mock import patch

from ai_engine.graphs.interview_graph import interview_graph


def test_graph_runs_start_and_answer_turns() -> None:
    with patch("ai_engine.graphs.interview_nodes.service.generate_question") as generate, \
         patch("ai_engine.graphs.interview_nodes.evaluation_service.evaluate") as evaluate:
        generate.side_effect = [
            {"answer": "What is Binary Search?"},
            {"answer": "How does Binary Search reduce the search space?"},
        ]
        evaluate.return_value = {
            "score": 9,
            "feedback": "Correct and complete.",
            "strengths": ["Explained the invariant"],
            "improvements": ["Mention duplicate values"],
        }

        start = interview_graph.invoke({
            "mode": "start", "candidate_name": "Dinesh", "topic": "Binary Search",
            "difficulty": "Medium", "question": "", "answer": "", "score": 0,
            "feedback": "", "strengths": [], "improvements": [], "question_number": 0,
            "max_questions": 5, "interview_completed": False, "history": [],
        })
        assert start["question"] == "What is Binary Search?"

        answer = interview_graph.invoke({
            "mode": "answer", "candidate_name": "Dinesh", "topic": "Binary Search",
            "difficulty": "Medium", "question": start["question"],
            "answer": "It repeatedly halves a sorted search interval.", "score": 0,
            "feedback": "", "strengths": [], "improvements": [], "question_number": 0,
            "max_questions": 5, "interview_completed": False, "history": [],
        })

    assert evaluate.called
    assert answer["score"] == 9
    assert answer["difficulty"] == "Hard"
    assert answer["question"] == "How does Binary Search reduce the search space?"
