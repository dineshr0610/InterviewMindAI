from ai_engine.chains.evaluation_chain import evaluation_chain


class EvaluationService:

    def evaluate(self, question, answer, topic=None, difficulty="Easy"):
        # Removed duplicate answer in prompt. The evaluation_chain template expects
        # separate "question" and "answer" placeholders, not combined.
        # Passing combined text as "question" and then answer separately was causing answer duplication.

        return evaluation_chain.invoke(
            {
                "question": question,
                "answer": answer,
            }
        )
