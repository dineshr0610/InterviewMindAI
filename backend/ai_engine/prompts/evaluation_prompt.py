from langchain_core.prompts import PromptTemplate

EVALUATION_PROMPT = PromptTemplate.from_template("""
You are an expert technical interviewer.

Evaluate the candidate's answer.

Question:
{question}

Candidate Answer:
{answer}

Return ONLY valid JSON.

{{
    "score": 0,
    "feedback": "",
    "strengths": "",
    "improvements": ""
}}
""")