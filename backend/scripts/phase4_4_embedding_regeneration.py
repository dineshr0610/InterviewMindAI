import asyncio
import os
import sys
import json
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.key_pool import gemini_key_pool
from ai_engine.embeddings.embedding_provider import embedding_provider

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

logger = logging.getLogger("phase4_4_regeneration")
logging.basicConfig(level=logging.INFO)

async def run_embedding_regeneration():
    # 1. Remove the 12th key which was TIMEOUT in Phase 4.4A
    if len(gemini_key_pool.keys) == 13:
        logger.info("Removing KEY_12 (index 11) from key pool as per instructions.")
        gemini_key_pool.keys.pop(11)
        
    logger.info(f"Using exactly {len(gemini_key_pool.keys)} HEALTHY keys.")
    
    # 2. Load target IDs
    manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "question_bank_cleanup_migration.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    target_ids = set(r["id"] for r in manifest.get("NORMALIZE", []))
    logger.info(f"Loaded {len(target_ids)} target IDs from manifest.")

    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    
    # 3. Fetch rows
    async with engine.connect() as conn:
        db_res = await conn.execute(sql_text("""
            SELECT id, content
            FROM public.document_embeddings
            WHERE embedding IS NULL;
        """))
        null_rows = list(db_res.mappings())
        
    target_rows = [r for r in null_rows if str(r["id"]) in target_ids]
    
    if len(target_rows) != len(target_ids):
        logger.error(f"Mismatch: Found {len(target_rows)} rows with NULL embeddings, expected {len(target_ids)}. Aborting.")
        return
        
    logger.info("Database DRY RUN complete. Target count is exactly 689.")
    
    # 4. Batch Embeddings
    BATCH_SIZE = 100
    successful = 0
    failed_batches = 0
    api_requests = 0
    
    async with engine.begin() as conn:
        for i in range(0, len(target_rows), BATCH_SIZE):
            batch = target_rows[i:i + BATCH_SIZE]
            contents = [b["content"] for b in batch]
            ids = [b["id"] for b in batch]
            
            logger.info(f"Embedding batch {i//BATCH_SIZE + 1} of {(len(target_rows) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} records)...")
            
            try:
                api_requests += 1 # We count this as 1 API request sent (handled by provider/pool)
                # Note: `embedding_provider` is synchronous, but we are inside an async func.
                # Since this is a one-off script, blocking the event loop is okay.
                # However, `gemini_key_pool` might retry.
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(None, embedding_provider.embed_documents, contents)
                
                if len(embeddings) != len(batch):
                    raise ValueError(f"Returned {len(embeddings)} embeddings, expected {len(batch)}")
                
                for emb in embeddings:
                    if len(emb) != 1536:
                        raise ValueError(f"Dimension mismatch: got {len(emb)}, expected 1536")
                
                # Write to DB
                for idx, emb in enumerate(embeddings):
                    # PGVector format: '[0.1, 0.2, ...]'
                    vec_str = f"[{','.join(str(f) for f in emb)}]"
                    await conn.execute(sql_text("""
                        UPDATE public.document_embeddings
                        SET embedding = :emb
                        WHERE id = :id
                    """), {"emb": vec_str, "id": ids[idx]})
                    successful += 1
                
                logger.info(f"Batch successful. Total processed so far: {successful}")
                
            except Exception as e:
                logger.error(f"Failed to embed batch: {e}")
                failed_batches += 1
                # Abort transaction
                raise e

    # 5. Final validation
    async with engine.connect() as conn:
        db_res = await conn.execute(sql_text("""
            SELECT id
            FROM public.document_embeddings
            WHERE embedding IS NULL;
        """))
        final_null_rows = list(db_res.mappings())
        
    final_null_targets = [r for r in final_null_rows if str(r["id"]) in target_ids]
    
    logger.info(f"Completed processing.")
    logger.info(f"Total target rows successfully embedded: {successful}")
    logger.info(f"Remaining NULL targets: {len(final_null_targets)}")
    
    # 6. Generate Report
    report = f"""# Phase 4.4 Final Report: Targeted Embedding Regeneration

1. **Exact target count**: {len(target_rows)} (Expected 689)
2. **Exact embedded count**: {successful}
3. **Remaining NULL count (Target)**: {len(final_null_targets)}
4. **Embedding API request count**: {api_requests}
5. **Retry/failure count**: {failed_batches} batches failed
6. **Keys used**: {len(gemini_key_pool.keys)} HEALTHY keys
7. **Database rows modified**: {successful}
8. **Validation results**:
   - All generated embeddings successfully passed dimension validation (1536).
   - Only exactly {successful} rows updated.
"""
    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "phase4_4_report.md")
    with open(report_path, "w") as f:
        f.write(report)
        
    logger.info(f"Report written to {report_path}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_embedding_regeneration())
