from langchain_core.prompts import PromptTemplate

RAG_PROMPT = PromptTemplate.from_template("""
You are an expert Java interviewer.

Answer ONLY using the given context.

Context:
{context}

Question:
{question}

Return ONLY valid JSON.

{{
    "answer":"..."
}}
""")