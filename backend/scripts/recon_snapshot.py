"""READ-ONLY: snapshot document_embeddings (id, content, metadata, has_embedding) to a local JSON file."""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BACKEND, ".env"))


async def main():
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        # SELECT only. Vectors are not fetched.
        res = await conn.execute(sql_text(
            "SELECT id::text AS id, content, metadata, (embedding IS NOT NULL) AS has_embedding "
            "FROM public.document_embeddings ORDER BY created_at, id"
        ))
        rows = [dict(r) for r in res.mappings()]
    out = os.path.join(BACKEND, "reports", "_scratch_snapshot.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f)
    print(f"snapshot rows: {len(rows)} -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
