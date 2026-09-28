from ai_engine.chains.evaluation_chain import evaluation_chain


class EvaluationService:

    def evaluate(self, question, answer, topic=None, difficulty="Easy"):

        prompt = (
            f"Topic: {topic or 'General'}\n"
            f"Difficulty: {difficulty}\n"
            f"Interview Question: {question}\n"
            f"Candidate Answer: {answer}"
        )

        return evaluation_chain.invoke(
            {
                "question": prompt,
                "answer": answer,
            }
        )
