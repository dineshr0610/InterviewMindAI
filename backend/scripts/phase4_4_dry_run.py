import asyncio
import os
import sys
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

async def run_dry_run():
    # Load manifest
    manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "question_bank_cleanup_migration.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    target_ids = set(r["id"] for r in manifest.get("NORMALIZE", []))

    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        db_res = await conn.execute(sql_text("""
            SELECT id, content, metadata, 
                   CASE WHEN embedding IS NULL THEN 1 ELSE 0 END as is_null
            FROM public.document_embeddings;
        """))
        rows = list(db_res.mappings())
    
    target_rows_null = []
    target_rows_non_null = []
    
    for row in rows:
        if str(row["id"]) in target_ids:
            if row["is_null"] == 1:
                target_rows_null.append(row)
            else:
                target_rows_non_null.append(row)
            
    print(f"Manifest target IDs total: {len(target_ids)}")
    print(f"Target IDs found in DB with NULL embedding: {len(target_rows_null)}")
    print(f"Target IDs found in DB with NON-NULL embedding: {len(target_rows_non_null)}")
    
if __name__ == "__main__":
    asyncio.run(run_dry_run())
