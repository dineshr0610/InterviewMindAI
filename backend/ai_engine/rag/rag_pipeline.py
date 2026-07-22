from ai_engine.chains.rag_chain import rag_chain

class RAGPipeline:

    def ask(self, question):
        return rag_chain.invoke(question)