from ai_engine.chains.rag_chain import rag_chain


class RAGService:

    def ask(self, question: str):
        return rag_chain.invoke(question)