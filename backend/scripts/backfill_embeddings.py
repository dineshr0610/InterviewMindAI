import argparse
import asyncio
import os
import sys
import logging

# Ensure absolute paths resolve correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import asyncpg
from ai_engine.embeddings.embedding_provider import embedding_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

async def backfill(limit: int, batch_size: int, status_only: bool = False):
    conn_str = os.getenv("DATABASE_URL")
    if not conn_str:
        logger.error("DATABASE_URL not found.")
        return

    conn = await asyncpg.connect(conn_str)
    
    if status_only:
        total_rows = await conn.fetchval("SELECT count(*) FROM document_embeddings")
        embedded = await conn.fetchval("SELECT count(*) FROM document_embeddings WHERE embedding IS NOT NULL")
        missing = await conn.fetchval("SELECT count(*) FROM document_embeddings WHERE embedding IS NULL")
        invalid = await conn.fetchval("SELECT count(*) FROM document_embeddings WHERE embedding IS NOT NULL AND vector_dims(embedding) != 1536")
        
        print("\n=== EMBEDDING BACKFILL STATUS ===")
        print(f"Total rows: {total_rows}")
        print(f"Embedded: {embedded}")
        print(f"Missing: {missing}")
        print(f"Invalid Dimensions: {invalid}")
        print("=================================\n")
        await conn.close()
        return
    
    # Check remaining count
    total_remaining = await conn.fetchval("SELECT count(*) FROM document_embeddings WHERE embedding IS NULL")
    logger.info(f"Total rows missing embeddings: {total_remaining}")
    
    if total_remaining == 0:
        logger.info("No missing embeddings found. Exiting.")
        await conn.close()
        return

    target_count = min(total_remaining, limit)
    logger.info(f"Targeting to backfill {target_count} rows in batches of {batch_size}...")

    processed = 0
    while processed < target_count:
        current_batch_size = min(batch_size, target_count - processed)
        
        # Fetch a batch
        rows = await conn.fetch('''
            SELECT id, content FROM document_embeddings 
            WHERE embedding IS NULL 
            ORDER BY id
            LIMIT $1
        ''', current_batch_size)
        
        if not rows:
            break
            
        ids = [row['id'] for row in rows]
        texts = [row['content'] for row in rows]
        
        try:
            logger.info(f"Requesting embeddings for batch of {len(texts)}...")
            embeddings = embedding_provider.embed_documents(texts)
            
            if len(embeddings) != len(ids):
                logger.error(f"Mismatch! Got {len(embeddings)} embeddings for {len(ids)} inputs.")
                break
                
            # Update database
            async with conn.transaction():
                for i, row_id in enumerate(ids):
                    emb = embeddings[i]
                    emb_str = "[" + ",".join(str(f) for f in emb) + "]"
                    await conn.execute("UPDATE document_embeddings SET embedding = $1::vector WHERE id = $2", emb_str, row_id)
            
            processed += len(ids)
            logger.info(f"Successfully processed batch. Total processed: {processed}/{target_count}")
            
            # Small delay to respect rate limits
            await asyncio.sleep(1.0)
            
        except Exception as e:
            logger.error(f"Error during embedding generation or database update: {e}")
            break

    logger.info(f"Backfill complete. Processed {processed} rows.")
    await conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill missing embeddings safely.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of rows to process.")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for API requests.")
    parser.add_argument("--status", action="store_true", help="Print current embedding status and exit.")
    args = parser.parse_args()
    
    asyncio.run(backfill(args.limit, args.batch_size, args.status))
