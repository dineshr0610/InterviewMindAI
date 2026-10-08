import asyncio
import os
import sys
import json
from collections import defaultdict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

async def inspect_duplicates():
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        res = await conn.execute(sql_text("""
            SELECT id, content, metadata
            FROM public.document_embeddings;
        """))
        rows = list(res.mappings())

    content_groups = defaultdict(list)
    for r in rows:
        c = (r["content"] or "").strip()
        content_groups[c].append(r)
        
    dups = {k: v for k, v in content_groups.items() if len(v) > 1}
    print(f"Total duplicate groups: {len(dups)}")
    total_records = sum(len(v) for v in dups.values())
    print(f"Total records in duplicate groups: {total_records}")
    
    # Analyze differences within duplicate groups (metadata vs content)
    dup_details = []
    diff_roles = 0
    diff_topics = 0
    diff_difficulty = 0
    identical_meta = 0
    
    for c, r_list in dups.items():
        roles = set(r["metadata"].get("role") for r in r_list if r["metadata"])
        topics = set(r["metadata"].get("topic") for r in r_list if r["metadata"])
        diffs = set(r["metadata"].get("difficulty") for r in r_list if r["metadata"])
        
        if len(roles) > 1: diff_roles += 1
        if len(topics) > 1: diff_topics += 1
        if len(diffs) > 1: diff_difficulty += 1
        if len(roles) == 1 and len(topics) == 1 and len(diffs) == 1:
            identical_meta += 1
            
        dup_details.append({
            "content_preview": c[:150],
            "count": len(r_list),
            "roles": list(roles),
            "topics": list(topics),
            "difficulties": list(diffs),
            "ids": [str(r["id"]) for r in r_list]
        })
        
    dup_details.sort(key=lambda x: x["count"], reverse=True)
    
    print(f"Groups with different roles: {diff_roles}")
    print(f"Groups with different topics: {diff_topics}")
    print(f"Groups with different difficulties: {diff_difficulty}")
    print(f"Groups with 100% identical metadata: {identical_meta}")
    
    with open("reports/duplicates_analysis.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_duplicate_groups": len(dups),
            "total_affected_records": total_records,
            "groups_with_diff_roles": diff_roles,
            "groups_with_diff_topics": diff_topics,
            "groups_with_diff_difficulty": diff_difficulty,
            "groups_with_identical_meta": identical_meta,
            "top_duplicate_groups": dup_details[:20]
        }, f, indent=2)
    print("Saved duplicates analysis to reports/duplicates_analysis.json")

if __name__ == "__main__":
    asyncio.run(inspect_duplicates())
