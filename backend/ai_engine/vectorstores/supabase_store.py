from __future__ import annotations

import logging
import os
from typing import List, Optional

import requests
from dotenv import load_dotenv
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from ai_engine.embeddings.embedding_provider import embedding_provider

load_dotenv()

logger = logging.getLogger("interviewmind.vectorstores.supabase")


class SupabaseVectorRetriever(BaseRetriever):
    k: int = 2
    similarity_threshold: float = 0.0

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SECRET_KEY")

        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is not configured.")
        if not supabase_key:
            raise RuntimeError("SUPABASE_SECRET_KEY is not configured.")

        query_embedding = embedding_provider.embed_query(query)

        if len(query_embedding) != 1536:
            raise RuntimeError(
                f"Expected 1536-dimensional query embedding, got {len(query_embedding)}"
            )

        rpc_url = (
            supabase_url.rstrip("/")
            + "/rest/v1/rpc/match_document_embeddings"
        )

        headers = {
            "apikey": supabase_key,
            "Authorization": "Bearer " + supabase_key,
            "Content-Type": "application/json",
        }

        payload = {
            "query_embedding": query_embedding,
            "match_threshold": self.similarity_threshold,
            "match_count": self.k,
        }

        response = requests.post(
            rpc_url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        rows = response.json() or []
        documents: List[Document] = []

        for row in rows:
            metadata = dict(row.get("metadata") or {})
            metadata["similarity"] = row.get("similarity")
            metadata["source"] = "supabase_pgvector"

            documents.append(
                Document(
                    page_content=row["content"],
                    metadata=metadata,
                )
            )

        logger.info("Retrieved %d documents from Supabase pgvector.", len(documents))
        return documents


retriever = SupabaseVectorRetriever()
