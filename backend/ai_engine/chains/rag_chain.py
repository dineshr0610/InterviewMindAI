from __future__ import annotations

import importlib
from typing import Any

try:
    parsers_mod = importlib.import_module("langchain_core.output_parsers")
    runnables_mod = importlib.import_module("langchain_core.runnables")
    JsonOutputParser = getattr(parsers_mod, "JsonOutputParser")
    RunnablePassthrough = getattr(runnables_mod, "RunnablePassthrough")
except ImportError:
    class JsonOutputParser:
        def invoke(self, input_val: Any) -> Any:
            return input_val

    class RunnablePassthrough:
        def invoke(self, input_val: Any) -> Any:
            return input_val

from ai_engine.prompts.prompt_template import RAG_PROMPT
from ai_engine.models.llm import llm
from ai_engine.vectorstores.supabase_store import retriever

parser = JsonOutputParser()


def format_docs(docs):
    if isinstance(docs, str):
        return docs
    return "\n\n".join(getattr(doc, 'page_content', str(doc)) for doc in docs)


try:
    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | RAG_PROMPT
        | llm
        | parser
    )
except Exception:
    class FallbackRAGChain:
        def invoke(self, question: str) -> dict:
            return {
                "question": f"Can you explain the core principles of {question}?",
                "answer": f"Question generated for {question}."
            }
    rag_chain = FallbackRAGChain()