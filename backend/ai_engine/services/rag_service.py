from ai_engine.chains.rag_chain import rag_chain


class RAGService:

    def ask(self, question: str, search_query: str | None = None):
        if search_query:
            try:
                import json
                import re
                from ai_engine.vectorstores.supabase_store import retriever
                from ai_engine.chains.rag_chain import format_docs, parser
                from ai_engine.prompts.prompt_template import RAG_PROMPT
                from ai_engine.models.llm import llm

                docs = retriever.invoke(search_query) if hasattr(retriever, "invoke") else retriever.get_relevant_documents(search_query)
                context = format_docs(docs)
                if context and llm:
                    prompt_val = RAG_PROMPT.format(context=context, question=question)
                    resp = llm.invoke(prompt_val)
                    if hasattr(resp, "text") and isinstance(resp.text, str) and resp.text.strip():
                        raw = resp.text.strip()
                    else:
                        content = getattr(resp, "content", str(resp))
                        if isinstance(content, list):
                            parts = [p.get("text", "") if isinstance(p, dict) else str(getattr(p, "text", p)) for p in content]
                            raw = "".join(parts).strip()
                        else:
                            raw = str(content).strip()
                    match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
                    return {"answer": raw.strip()}
            except Exception:
                pass
        return rag_chain.invoke(question)