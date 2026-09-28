"""
Document Ingestion & Indexing Service for InterviewMind AI RAG Pipeline.
Embeds technical reference documents using Gemini Embedding Provider (1536-dim)
and stores them in Supabase pgvector document_embeddings table.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
import requests

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

load_dotenv(backend_dir / ".env")

from ai_engine.embeddings.embedding_provider import embedding_provider

logger = logging.getLogger("interviewmind.rag.ingest")

SEED_DOCUMENTS = [
    {
        "content": "Binary Search algorithm requires sorted data and repeatedly divides the search space in half. Time complexity is O(log N) and space complexity is O(1) iterative or O(log N) recursive.",
        "metadata": {"topic": "Binary Search", "category": "Data Structures & Algorithms"}
    },
    {
        "content": "Python FastAPI is a high-performance web framework for building RESTful APIs using Python 3.8+ typing, Pydantic data validation, OpenAPI specs, and Starlette async ASGI features.",
        "metadata": {"topic": "Python FastAPI", "category": "Backend Web Frameworks"}
    },
    {
        "content": "SQL INNER JOIN returns rows with matching key values in both tables. LEFT JOIN returns all records from the left table along with matching records from the right table.",
        "metadata": {"topic": "SQL Joins", "category": "Databases"}
    },
    {
        "content": "REST APIs operate over HTTP using standard methods GET, POST, PUT, DELETE for stateless client-server resource manipulation with structured JSON data representations.",
        "metadata": {"topic": "REST APIs", "category": "Web Architecture"}
    },
    {
        "content": "Java OOP principles comprise Encapsulation, Inheritance, Polymorphism, and Abstraction to structure modular, reusable object-oriented software components.",
        "metadata": {"topic": "Java OOP", "category": "Programming Languages"}
    }
]

def seed_documents() -> int:
    """
    Embed and insert seed technical documents into Supabase document_embeddings table.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")
    db_url = os.getenv("DATABASE_URL")

    inserted_count = 0

    session = requests.Session()
    from urllib3.util import Retry
    from requests.adapters import HTTPAdapter

    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }

    url = f"{supabase_url.rstrip('/')}/rest/v1/document_embeddings" if supabase_url else None

    for doc in SEED_DOCUMENTS:
        content = doc["content"]
        meta = doc["metadata"]

        try:
            embedding = embedding_provider.embed_document(content)
            payload = {
                "content": content,
                "metadata": meta,
                "embedding": embedding
            }

            success = False
            if url and supabase_key:
                try:
                    res = session.post(url, headers=headers, json=payload, timeout=15)
                    if res.status_code in (200, 201):
                        success = True
                        inserted_count += 1
                        logger.info("Successfully ingested document via REST: %s", meta.get("topic"))
                except Exception as rest_err:
                    logger.warning("REST ingestion failed for %s, trying direct DB: %s", meta.get("topic"), rest_err)

            if not success and db_url:
                import json
                import asyncio
                from sqlalchemy.ext.asyncio import create_async_engine
                from sqlalchemy import text as sql_text

                async def _db_insert():
                    clean_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://") if not db_url.startswith("postgresql+asyncpg") else db_url
                    engine = create_async_engine(clean_db_url)
                    emb_str = "[" + ",".join(str(f) for f in embedding) + "]"
                    async with engine.connect() as conn:
                        await conn.execute(sql_text(
                            "INSERT INTO public.document_embeddings (content, metadata, embedding) VALUES (:content, CAST(:meta AS jsonb), CAST(:emb AS vector))"
                        ), {"content": content, "meta": json.dumps(meta), "emb": emb_str})
                        await conn.commit()
                    await engine.dispose()

                asyncio.run(_db_insert())
                inserted_count += 1
                logger.info("Successfully ingested document via direct DB: %s", meta.get("topic"))

        except Exception as exc:
            logger.error("Error ingesting document for topic %s: %s", meta.get("topic"), exc)

    return inserted_count

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = seed_documents()
    print(f"Successfully seeded {count} technical documents into Supabase pgvector!")
