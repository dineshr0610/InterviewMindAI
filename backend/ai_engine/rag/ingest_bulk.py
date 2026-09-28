"""
Bulk Ingestion Script for InterviewMind AI Technical Knowledge Dataset.
Reads backend/data/knowledge_base/technical_knowledge_5000.json and batch-inserts
records into Supabase `document_embeddings` table.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
import requests

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

load_dotenv(backend_dir / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("interviewmind.rag.ingest_bulk")


def load_dataset_file(filename: str = "real_technical_dataset.json") -> List[Dict[str, Any]]:
    json_path = backend_dir / "data" / "knowledge_base" / filename
    if not json_path.exists():
        # Fallback to technical_knowledge_5000.json
        json_path = backend_dir / "data" / "knowledge_base" / "technical_knowledge_5000.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Dataset file not found at {json_path}.")

    logger.info("Loading dataset from %s", json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ingest_via_rest_batches(entries: List[Dict[str, Any]], batch_size: int = 100) -> int:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("SUPABASE_URL or SUPABASE_SECRET_KEY not set. Cannot use REST ingestion.")
        return 0

    url = f"{supabase_url.rstrip('/')}/rest/v1/document_embeddings"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    session = requests.Session()
    total_inserted = 0

    for i in range(0, len(entries), batch_size):
        batch = entries[i : i + batch_size]
        payload = [
            {
                "content": item["content"],
                "metadata": item["metadata"],
            }
            for item in batch
        ]

        try:
            res = session.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code in (200, 201):
                total_inserted += len(batch)
                logger.info("Batch [%d / %d] inserted (%d rows)", i + len(batch), len(entries), len(batch))
            else:
                logger.warning("Batch insert status %s: %s", res.status_code, res.text)
        except Exception as exc:
            logger.error("Failed to insert batch at index %d: %s", i, exc)

    return total_inserted


async def ingest_via_direct_db_async(entries: List[Dict[str, Any]], batch_size: int = 250) -> int:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not set. Skipping direct DB ingestion.")
        return 0

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text as sql_text

    clean_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://") if not db_url.startswith("postgresql+asyncpg") else db_url
    engine = create_async_engine(clean_db_url)
    total_inserted = 0

    async with engine.connect() as conn:
        for i in range(0, len(entries), batch_size):
            batch = entries[i : i + batch_size]
            params = [
                {
                    "content": item["content"],
                    "meta": json.dumps(item["metadata"]),
                }
                for item in batch
            ]

            stmt = sql_text(
                "INSERT INTO public.document_embeddings (content, metadata) "
                "VALUES (:content, CAST(:meta AS jsonb))"
            )

            try:
                await conn.execute(stmt, params)
                await conn.commit()
                total_inserted += len(batch)
                logger.info("Direct DB Batch [%d / %d] inserted (%d rows)", i + len(batch), len(entries), len(batch))
            except Exception as exc:
                logger.error("DB batch execution error at index %d: %s", i, exc)

    await engine.dispose()
    return total_inserted


def main():
    logger.info("Starting InterviewMind AI Bulk Dataset Ingestion...")
    entries = load_dataset_file()
    logger.info("Loaded %d dataset records from local storage.", len(entries))

    # Try REST ingestion first
    inserted = ingest_via_rest_batches(entries)
    if inserted == 0:
        logger.info("Attempting direct PostgreSQL DB ingestion...")
        inserted = asyncio.run(ingest_via_direct_db_async(entries))

    logger.info("Bulk Ingestion Finished! Successfully processed %d / %d records.", inserted, len(entries))


if __name__ == "__main__":
    main()
