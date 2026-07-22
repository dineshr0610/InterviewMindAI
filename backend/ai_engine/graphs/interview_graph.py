from langgraph.graph import StateGraph, START, END

from ai_engine.graphs.interview_state import InterviewState
from ai_engine.graphs.interview_nodes import (
    generate_question,
    evaluate_answer,
    update_interview_state,
    should_continue
)

graph = StateGraph(InterviewState)

# Nodes
graph.add_node(
    "generate_question",
    generate_question
)

graph.add_node(
    "evaluate_answer",
    evaluate_answer
)

graph.add_node(
    "update_interview_state",
    update_interview_state
)

# Edges
graph.add_edge(
    START,
    "generate_question"
)

graph.add_edge(
    "generate_question",
    "evaluate_answer"
)

graph.add_edge(
    "evaluate_answer",
    "update_interview_state"
)

# Conditional Edge
graph.add_conditional_edges(
    "update_interview_state",
    should_continue,
    {
        "continue": "generate_question",
        "finish": END
    }
)

interview_graph = graph.compile()