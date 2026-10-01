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
        db_url = os.getenv("DATABASE_URL")

        if not supabase_url and not db_url:
            logger.warning("Neither SUPABASE_URL nor DATABASE_URL is configured.")
            return []

        try:
            query_embedding = embedding_provider.embed_query(query)
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            return []

        if len(query_embedding) != 1536:
            logger.error(
                "Expected 1536-dimensional query embedding, got %d", len(query_embedding)
            )
            return []

        rows = []
        if supabase_url and supabase_key:
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

            try:
                session = requests.Session()
                from urllib3.util import Retry
                from requests.adapters import HTTPAdapter

                retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
                session.mount("https://", HTTPAdapter(max_retries=retries))

                response = session.post(
                    rpc_url,
                    headers=headers,
                    json=payload,
                    timeout=3,
                )
                if response.status_code == 200:
                    rows = response.json() or []
            except Exception as rest_exc:
                logger.warning("Supabase REST RPC retrieval failed, trying direct DB: %s", rest_exc)

        if not rows and db_url and "postgres" in db_url.lower():
            try:
                import json
                import asyncio
                from sqlalchemy.ext.asyncio import create_async_engine
                from sqlalchemy import text as sql_text

                async def _query_db():
                    clean_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://") if not db_url.startswith("postgresql+asyncpg") else db_url
                    engine = create_async_engine(clean_db_url)
                    emb_str = "[" + ",".join(str(f) for f in query_embedding) + "]"
                    out_rows = []
                    async with engine.connect() as conn:
                        db_res = await conn.execute(
                            sql_text("""
                                SELECT id, content, metadata, (1 - (embedding <=> CAST(:emb AS vector))) AS similarity
                                FROM public.document_embeddings
                                WHERE embedding IS NOT NULL
                                  AND (1 - (embedding <=> CAST(:emb AS vector))) >= :thresh
                                ORDER BY similarity DESC
                                LIMIT :k;
                            """),
                            {"emb": emb_str, "thresh": self.similarity_threshold, "k": self.k}
                        )
                        for r in db_res.fetchall():
                            meta = r[2] if isinstance(r[2], dict) else json.loads(r[2] or "{}")
                            out_rows.append({
                                "id": str(r[0]),
                                "content": r[1],
                                "metadata": meta,
                                "similarity": float(r[3]) if r[3] is not None else 0.0
                            })
                    await engine.dispose()
                    return out_rows

                try:
                    loop = asyncio.get_running_loop()
                    import nest_asyncio
                    nest_asyncio.apply()
                    rows = loop.run_until_complete(_query_db())
                except RuntimeError:
                    rows = asyncio.run(_query_db())

            except Exception as db_exc:
                logger.error("Direct DB vector search failed: %s", db_exc)

        documents: List[Document] = []
        for row in rows:
            metadata = dict(row.get("metadata") or {})
            metadata["similarity"] = row.get("similarity")
            metadata["source"] = "supabase_pgvector"

            documents.append(
                Document(
                    page_content=row.get("content", ""),
                    metadata=metadata,
                )
            )

        logger.info("Retrieved %d documents from Supabase pgvector.", len(documents))
        return documents


retriever = SupabaseVectorRetriever()
