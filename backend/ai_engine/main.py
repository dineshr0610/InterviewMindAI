from ai_engine.graphs.interview_graph import interview_graph

state = {
    "candidate_name": "Gunal",

    "topic": "Arrays",

    "difficulty": "Easy",

    "question": "",

    "answer": "Binary Search works only on sorted arrays.",

    "score": 0,

    "feedback": "",

    "strengths": "",

    "improvements": "",

    "question_number": 1,

    "max_questions": 3,

    "history": [],

    "interview_completed": False
}

result = interview_graph.invoke(state)

print(result)