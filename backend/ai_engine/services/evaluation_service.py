from ai_engine.chains.evaluation_chain import evaluation_chain


class EvaluationService:

    def evaluate(self, question, answer):

        return evaluation_chain.invoke(
            {
                "question": question,
                "answer": answer
            }
        )