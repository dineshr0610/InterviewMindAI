from ai_engine.chains.rag_chain import rag_chain


class RAGService:

    def ask(self, search_query: str, filters: dict = None):
        try:
            from ai_engine.vectorstores.supabase_store import retriever
            
            docs = retriever.get_filtered_documents(search_query, metadata_filter=filters)
            if docs:
                results = []
                for i, doc in enumerate(docs):
                    results.append({
                        "question": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": doc.metadata.get("similarity", 0.0),
                        "rank": i + 1
                    })
                return results
        except Exception as e:
            pass
        return []