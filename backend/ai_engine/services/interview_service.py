from ai_engine.services.rag_service import RAGService


class InterviewService:

    def __init__(self):
        self.rag = RAGService()

    def generate_question(self, topic, difficulty):

        prompt = f"""
Generate one {difficulty} level interview question
on {topic}.

Return only JSON.
"""

        return self.rag.ask(prompt)