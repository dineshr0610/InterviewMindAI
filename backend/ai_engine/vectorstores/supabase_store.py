"""
Supabase PostgreSQL Vector Store integration using pgvector.
Retrieves semantically similar documents from Supabase.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from ai_engine.embeddings.embedding_provider import embedding_provider

load_dotenv()

logger = logging.getLogger("interviewmind.vectorstores.supabase")


class SupabaseVectorRetriever(BaseRetriever):
    """
    Retriever using Supabase PostgreSQL + pgvector.
    """

    k: int = 2
    similarity_threshold: float = 0.0

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:

        logger.info(
            "Executing Supabase pgvector retrieval for query: '%s'",
            query[:60],
        )

        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SECRET_KEY")

        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is not configured.")

        if not supabase_key:
            raise RuntimeError("SUPABASE_SECRET_KEY is not configured.")

        client = create_client(
            supabase_url,
            supabase_key,
        )

        # Generate a 1536-dimensional embedding for the query.
        query_embedding = embedding_provider.embed_query(query)

        # Search Supabase pgvector using the PostgreSQL RPC function.
        response = client.rpc(
            "match_document_embeddings",
            {
                "query_embedding": query_embedding,
                "match_threshold": self.similarity_threshold,
                "match_count": self.k,
            },
        ).execute()

        documents = []

        for row in response.data or []:
            metadata = row.get("metadata") or {}

            metadata["similarity"] = row.get("similarity")
            metadata["source"] = "supabase_pgvector"

            documents.append(
                Document(
                    page_content=row["content"],
                    metadata=metadata,
                )
            )

        logger.info(
            "Retrieved %d documents from Supabase pgvector.",
            len(documents),
        )

        return documents


retriever = SupabaseVectorRetriever()