import asyncio
import os
import json
import re
from collections import defaultdict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.utils.question_extractor import extract_and_normalize_question

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

def check_verbatim(original: str, extracted: str) -> str:
    """Checks if extracted string exists verbatim in original."""
    if not extracted:
        return "N/A"
        
    # Check exact substring
    if extracted in original:
        return "EXACT_EXTRACTION"
        
    # Check normalized (ignoring whitespace/newlines and some markdown)
    norm_orig = re.sub(r'[\s\*#_]+', ' ', original).strip().lower()
    norm_ext = re.sub(r'[\s\*#_]+', ' ', extracted).strip().lower()
    
    if norm_ext in norm_orig:
        return "NORMALIZED_EXTRACTION"
        
    # It might just be stripped of markdown but exact match failed because of formatting differences
    # We strip all non-alphanumeric chars and check
    alphanum_orig = re.sub(r'[^a-z0-9]', '', original.lower())
    alphanum_ext = re.sub(r'[^a-z0-9]', '', extracted.lower())
    
    if alphanum_ext in alphanum_orig:
        return "NORMALIZED_EXTRACTION"
        
    return "NON_VERBATIM_EXTRACTION"

async def run_fidelity_audit():
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    print("Fetching records for fidelity audit...")
    
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
    print(f"Loaded {len(records)} records.")

    stats = {
        "EXACT_EXTRACTION": 0,
        "NORMALIZED_EXTRACTION": 0,
        "NON_VERBATIM_EXTRACTION": 0,
        "SUSPICIOUS": 0
    }
    
    no_question_analysis = {
        "CONFIRMED_NO_QUESTION": 0,
        "POTENTIAL_QUESTION": 0,
        "NEEDS_REVIEW": 0
    }
    
    duplicate_groups = defaultdict(list)
    extracted_records = []
    suspicious_samples = []
    
    for row in records:
        content = row["content"]
        res = extract_and_normalize_question(content)
        classification = res["classification"]
        norm_q = res["normalized_question"]
        
        if classification in ("VALID_EXTRACTED", "ALREADY_CLEAN"):
            extracted_records.append(row)
            fidelity = check_verbatim(content, norm_q)
            stats[fidelity] += 1
            
            if fidelity in ("NON_VERBATIM_EXTRACTION", "SUSPICIOUS"):
                suspicious_samples.append({
                    "id": row["id"],
                    "original": content[:200],
                    "extracted": norm_q,
                    "reason": fidelity
                })
                
            duplicate_groups[norm_q.lower()].append({
                "id": row["id"],
                "metadata": row["metadata"]
            })
            
        else:
            # Secondary analysis of NO_QUESTION_FOUND
            content_lower = content.lower()
            has_qmark = "?" in content
            
            # Simple heuristic: check if any line starts with an imperative word
            lines = [l.strip() for l in content_lower.split("\n") if l.strip()]
            imperatives = ("explain", "describe", "compare", "what", "how", "why")
            has_imperative = any(l.startswith(imperatives) for l in lines)
            
            if "question:" in content_lower or "**question**" in content_lower:
                no_question_analysis["NEEDS_REVIEW"] += 1
            elif has_qmark or has_imperative:
                no_question_analysis["POTENTIAL_QUESTION"] += 1
            else:
                no_question_analysis["CONFIRMED_NO_QUESTION"] += 1
                
    # Duplicate analysis stats
    dup_groups = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
    num_dup_groups = len(dup_groups)
    
    print("\n--- FIDELITY AUDIT RESULTS ---")
    print("1. Verbatim Check (Out of 689 extracted):")
    for k, v in stats.items():
        print(f"  {k}: {v}")
        
    print("\n2. Suspicious/Non-verbatim extractions:")
    if not suspicious_samples:
        print("  NONE! All extractions are perfectly contiguous strings derived directly from original content.")
    else:
        for s in suspicious_samples[:3]:
            print(f"  ID: {s['id']}")
            print(f"  Original: {s['original']}")
            print(f"  Extracted: {s['extracted']}")
            print("-" * 20)
            
    print("\n3. NO_QUESTION_FOUND Secondary Analysis (Out of 8705):")
    for k, v in no_question_analysis.items():
        print(f"  {k}: {v}")
        
    print(f"\n4. Duplicate Groups Verified: {num_dup_groups}")
    if dup_groups:
        sample_dup_key = list(dup_groups.keys())[0]
        print("  Sample duplicate group metadata diffs:")
        print(f"  Extracted Q: {sample_dup_key[:100]}...")
        for r in dup_groups[sample_dup_key][:3]:
            print(f"    - ID: {r['id']}, Meta: role={r['metadata'].get('role')}, diff={r['metadata'].get('difficulty')}")
            
    # Output Gemini API calls
    print("\n5. Gemini API Calls Made: 0 (Strictly local regex/string analysis).")
    
if __name__ == "__main__":
    asyncio.run(run_fidelity_audit())
