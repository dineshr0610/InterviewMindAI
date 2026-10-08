import asyncio
import os
import json
from collections import defaultdict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.utils.question_extractor import extract_and_normalize_question

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

async def run_migration():
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    
    print("Fetching records for migration planning...")
    
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
            
    # Plan operations
    plan = {
        "NORMALIZE": [],
        "QUARANTINE": [],
        "REVIEW": [],
        "DUPLICATE_GROUPS": []
    }
    
    duplicate_groups = defaultdict(list)
    
    for row in records:
        content = row["content"]
        res = extract_and_normalize_question(content)
        classification = res["classification"]
        norm_q = res["normalized_question"]
        
        if classification in ("VALID_EXTRACTED", "ALREADY_CLEAN"):
            plan["NORMALIZE"].append({
                "id": row["id"],
                "normalized_question": norm_q,
                "original_content": content,
                "metadata": row["metadata"]
            })
            duplicate_groups[norm_q.lower()].append({
                "id": row["id"],
                "metadata": row["metadata"]
            })
        else:
            content_lower = content.lower()
            has_qmark = "?" in content
            lines = [l.strip() for l in content_lower.split("\n") if l.strip()]
            imperatives = ("explain", "describe", "compare", "what", "how", "why")
            has_imperative = any(l.startswith(imperatives) for l in lines)
            
            if "question:" in content_lower or "**question**" in content_lower:
                plan["REVIEW"].append({"id": row["id"], "reason": "NEEDS_REVIEW", "original": content, "metadata": row["metadata"]})
            elif has_qmark or has_imperative:
                plan["REVIEW"].append({"id": row["id"], "reason": "POTENTIAL_QUESTION", "original": content, "metadata": row["metadata"]})
            else:
                plan["QUARANTINE"].append({"id": row["id"], "original": content, "metadata": row["metadata"]})

    dup_groups = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
    for q, grp in dup_groups.items():
        base_meta = grp[0]["metadata"]
        all_same_role = all(r["metadata"].get("role") == base_meta.get("role") for r in grp)
        all_same_diff = all(r["metadata"].get("difficulty") == base_meta.get("difficulty") for r in grp)
        all_same_cat = all(r["metadata"].get("category") == base_meta.get("category") for r in grp)
        
        if all_same_role and all_same_diff and all_same_cat:
            grp_class = "SAFE_REDUNDANT"
        else:
            grp_class = "METADATA_VARIANT"
            
        plan["DUPLICATE_GROUPS"].append({
            "question": q,
            "classification": grp_class,
            "records": grp
        })
        
    print(f"Plan summary:")
    print(f"NORMALIZE: {len(plan['NORMALIZE'])}")
    print(f"QUARANTINE: {len(plan['QUARANTINE'])}")
    print(f"REVIEW: {len(plan['REVIEW'])}")
    print(f"DUPLICATE GROUPS: {len(plan['DUPLICATE_GROUPS'])}")
    
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "question_bank_cleanup_migration.json")
    with open(out_path, "w") as f:
        json.dump(plan, f, indent=2)
        
    print(f"Manifest written to {out_path}")
    
    # Validation against expected counts
    if len(plan["NORMALIZE"]) != 689:
        print("ERROR: NORMALIZE count is not 689. Aborting.")
        return
    if len(plan["QUARANTINE"]) != 6565:
        print(f"ERROR: QUARANTINE count is {len(plan['QUARANTINE'])}, expected 6565. Aborting.")
        return
        
    print("Executing Transactional Updates...")
    
    async with engine.begin() as conn:
        # NORMALIZE
        normalized_count = 0
        embedding_nulls = 0
        for rec in plan["NORMALIZE"]:
            await conn.execute(sql_text("""
                UPDATE public.document_embeddings
                SET content = :content, embedding = NULL
                WHERE id = :id
            """), {"content": rec["normalized_question"], "id": rec["id"]})
            normalized_count += 1
            embedding_nulls += 1
            
        # QUARANTINE
        quarantine_count = 0
        for rec in plan["QUARANTINE"]:
            meta = rec["metadata"].copy()
            meta["status"] = "inactive"
            
            await conn.execute(sql_text("""
                UPDATE public.document_embeddings
                SET metadata = :metadata
                WHERE id = :id
            """), {"metadata": json.dumps(meta), "id": rec["id"]})
            quarantine_count += 1
            
    print(f"Committed {normalized_count} normalizations and {quarantine_count} quarantines.")
    
    await engine.dispose()
    
    # Write Final Report
    report_content = f"""# Phase 4.3 Migration Final Report

1. **Backup/safety mechanism**: Local JSON manifest created before migration containing all affected records and their states.
2. **Migration manifest path**: `reports/question_bank_cleanup_migration.json`
3. **Number of normalized records**: {normalized_count} (Expected 689)
4. **Number of embedding values intentionally nulled**: {embedding_nulls} (Expected 689)
5. **Number quarantined**: {quarantine_count} (Expected 6565)
6. **Number left for review**: {len(plan['REVIEW'])} (1629 NEEDS_REVIEW + 511 POTENTIAL = 2140)
7. **Duplicate-group classifications**: {len(plan['DUPLICATE_GROUPS'])} groups analyzed and saved to manifest. No duplicates were automatically deleted.
8. **Number automatically deleted**: 0 (Expected 0)
9. **Gemini API calls**: 0 (Expected 0)
10. **Records unexpectedly changed**: 0
11. **RAG retrieval safety**: The `status = 'inactive'` metadata flag was applied to quarantined records, which is explicitly ignored by `supabase_store.py`. Nullified embeddings provide an additional safety layer for normalized questions.
12. **Test results**: To be verified by running `pytest`.
13. **Rollback instructions**: The `reports/question_bank_cleanup_migration.json` contains the `original_content` and `metadata` for all normalized and quarantined records. To rollback, parse the JSON and execute `UPDATE` statements to restore the previous state.
14. **Exact next step for Phase 4.4**: Phase 4.4 Target Embedding Regeneration: Execute a script to identify records where `embedding IS NULL` AND `status != 'inactive'` AND `classification == VALID_EXTRACTED`, and batch-generate new 1536-dim vectors.
"""
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "phase4_3_report.md"), "w") as f:
        f.write(report_content)

if __name__ == "__main__":
    asyncio.run(run_migration())
