import asyncio
import os
import json
import random
from collections import defaultdict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.utils.question_extractor import extract_and_normalize_question

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

async def run_audit():
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    
    print("Fetching records for dry-run extraction...")
    
    records = []
    
    async with engine.connect() as conn:
        db_res = await conn.execute(sql_text("""
            SELECT id, content, metadata, 
                   CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END as has_embedding
            FROM public.document_embeddings;
        """))
        for r in db_res.fetchall():
            records.append({
                "id": str(r[0]),
                "content": r[1] or "",
                "metadata": json.loads(r[2]) if isinstance(r[2], str) else (r[2] or {}),
                "has_embedding": bool(r[3])
            })
            
    await engine.dispose()
    
    print(f"Loaded {len(records)} records. Extracting...")
    
    # Classifications
    stats = {
        "VALID_EXTRACTED": 0,
        "ALREADY_CLEAN": 0,
        "AMBIGUOUS": 0,
        "NO_QUESTION_FOUND": 0,
        "MALFORMED": 0,
        "PLACEHOLDER": 0
    }
    
    embedding_present = 0
    embedding_null = 0
    
    # Store normalized questions for exact duplicate check
    normalized_counts = defaultdict(list)
    
    results = []
    samples = defaultdict(list)
    
    for row in records:
        content = row["content"]
        res = extract_and_normalize_question(content)
        
        classification = res["classification"]
        norm_q = res["normalized_question"]
        
        stats[classification] += 1
        
        if row["has_embedding"]:
            embedding_present += 1
        else:
            embedding_null += 1
            
        if norm_q:
            normalized_counts[norm_q.lower()].append(row["id"])
            
        # Add to sample (max 20 per classification)
        if len(samples[classification]) < 20:
            samples[classification].append({
                "id": row["id"],
                "preview": content[:150].replace("\n", " "),
                "normalized": norm_q,
                "reason": res["reason"],
                "flags": res["warning_flags"]
            })
            
        results.append({
            "id": row["id"],
            "classification": classification,
            "original_length": len(content),
            "normalized_question": norm_q,
            "role": row["metadata"].get("role"),
            "category": row["metadata"].get("category"),
            "difficulty": row["metadata"].get("difficulty"),
            "technology": row["metadata"].get("technology") or row["metadata"].get("topic"),
            "has_embedding": row["has_embedding"],
            "extraction_reason": res["reason"],
            "warning_flags": res["warning_flags"]
        })
        
    # Duplicate analysis
    duplicate_groups = {k: v for k, v in normalized_counts.items() if len(v) > 1}
    num_dup_groups = len(duplicate_groups)
    num_dup_records = sum(len(v) for v in duplicate_groups.values())
    
    # Write full JSON report
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "question_bank_cleanup_audit.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\n--- EXTRACTION SUMMARY ---")
    total = len(records)
    print(f"Total Records: {total}")
    for k, v in stats.items():
        print(f"  {k}: {v} ({(v/total)*100:.1f}%)")
        
    print(f"\nEmbedding Present: {embedding_present}")
    print(f"Embedding Null: {embedding_null}")
    
    print(f"\nExact Duplicate Groups (After Normalization): {num_dup_groups}")
    print(f"Exact Duplicated Records: {num_dup_records}")
    
    print(f"\nSafe to auto-normalize: {stats['VALID_EXTRACTED'] + stats['ALREADY_CLEAN']}")
    print(f"Require manual review: {stats['AMBIGUOUS']}")
    print(f"To be quarantined/deleted: {stats['NO_QUESTION_FOUND'] + stats['MALFORMED'] + stats['PLACEHOLDER']}")
    
    print("\n--- SAMPLES ---")
    for cls, samp_list in samples.items():
        print(f"\n=== {cls} Samples ===")
        for s in samp_list[:3]:  # print first 3 to console
            print(f"ID: {s['id']}")
            print(f"Preview: {s['preview']}")
            print(f"Normalized: {s['normalized']}")
            print(f"Reason: {s['reason']}")
            print("-" * 20)

    print(f"\nFull report saved to {out_path}")

if __name__ == "__main__":
    asyncio.run(run_audit())
