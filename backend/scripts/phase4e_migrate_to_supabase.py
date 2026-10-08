import asyncio
import json
import os
import sys
import hashlib
import time
from collections import Counter
from dotenv import load_dotenv
import asyncpg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
MANIFEST = os.path.join(REPORTS_DIR, "phase4e_migration_manifest_v1.json")

def hash_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest(), os.path.getsize(filepath)

def format_content(r):
    # Standard format compatible with test_question_extraction.py
    return f"**Question**: {r['question']}\n\n**Ideal Answer**: {r['expected_answer']}"

async def run_migration():
    start_time = time.time()
    print("Starting Phase 4E Migration...")
    
    file_hash, file_size = hash_file(OUT)
    if file_hash != "9a86edca07bc1b195de88b601345a55b45773602907c383e0ad630aff3e41092":
        print(f"ERROR: File hash mismatch! Expected 9a86edca07bc1b195de88b601345a55b45773602907c383e0ad630aff3e41092, got {file_hash}")
        sys.exit(1)
        
    with open(OUT, 'r', encoding='utf-8') as f:
        new_records = [json.loads(line) for line in f if line.strip()]
        
    if len(new_records) != 2492:
        print(f"ERROR: Total NEW records is {len(new_records)}, expected 2492.")
        sys.exit(1)
        
    # Validation
    id_set = set()
    role_counts = Counter()
    for r in new_records:
        if r['id'] in id_set:
            print(f"ERROR: Duplicate ID {r['id']}")
            sys.exit(1)
        id_set.add(r['id'])
        if not r.get('question') or not r.get('expected_answer'):
            print(f"ERROR: Missing question/answer in {r['id']}")
            sys.exit(1)
        role = r.get('primary_role')
        role_counts[role] += 1
        
    expected_roles = {
        "Python Developer": 250,
        "Frontend Developer": 250,
        "Java Developer": 250,
        "Database Developer": 250,
        "DevOps / Cloud Engineer": 245,
        "Backend Developer": 247,
        "Data Analyst": 250,
        "AI Engineer": 250,
        "ML Engineer": 250,
        "Full Stack Developer": 250
    }
    
    for k, v in expected_roles.items():
        if role_counts[k] != v:
            print(f"ERROR: Role count mismatch for {k}. Expected {v}, got {role_counts[k]}")
            sys.exit(1)
            
    print("Validation passed.")
    
    db_url = os.environ.get("DIRECT_URL")
    if not db_url:
        print("ERROR: DIRECT_URL not found.")
        sys.exit(1)
        
    conn = await asyncpg.connect(db_url)
    
    # 1. Pre-migration db state
    pre_count = await conn.fetchval("SELECT count(*) FROM document_embeddings")
    pre_active = await conn.fetchval("SELECT count(*) FROM document_embeddings WHERE metadata->>'status' = 'active'")
    pre_inactive = await conn.fetchval("SELECT count(*) FROM document_embeddings WHERE metadata->>'status' = 'inactive'")
    pre_populated = await conn.fetchval("SELECT count(*) FROM document_embeddings WHERE embedding IS NOT NULL")
    pre_null = await conn.fetchval("SELECT count(*) FROM document_embeddings WHERE embedding IS NULL")
    pre_ids = set(r['id'] for r in await conn.fetch("SELECT id FROM document_embeddings"))

    print(f"Pre-migration row count: {pre_count}")
    
    # Check if migration already happened
    existing_migration = await conn.fetchval(
        "SELECT count(*) FROM document_embeddings WHERE metadata->>'migration_batch' = 'phase4d_final_2492'"
    )
    if existing_migration > 0:
        print(f"ERROR: Found {existing_migration} rows with migration_batch='phase4d_final_2492'. Migration already ran.")
        await conn.close()
        sys.exit(1)
        
    # Create manifest
    manifest_records = []
    insert_params = []
    
    for r in new_records:
        meta = {
            "primary_role": r.get("primary_role"),
            "role": r.get("primary_role"),  # using primary_role to match legacy style
            "skill": r.get("primary_skill"),
            "technology": r.get("technology"),
            "topic": r.get("topic"),
            "intent": r.get("intent"),
            "difficulty": r.get("difficulty"),
            "question_type": r.get("question_type"),
            "source": "InterviewMind Phase 4D",
            "dataset_type": "curated_new",
            "migration_batch": "phase4d_final_2492",
            "source_question_id": r["id"],
            "status": "active"
        }
        content = format_content(r)
        
        manifest_records.append({
            "source_question_id": r["id"],
            "question": r["question"],
            "answer": r["expected_answer"],
            "metadata": meta
        })
        
        insert_params.append((content, json.dumps(meta)))
        
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump({
            "source_file_sha256": file_hash,
            "source_file_size": file_size,
            "source_record_count": len(new_records),
            "pre_migration_supabase_count": pre_count,
            "records": manifest_records
        }, f, indent=2)
        
    print("Manifest created. Starting transaction...")
    
    # Transactional Insert
    async with conn.transaction():
        await conn.executemany(
            "INSERT INTO document_embeddings (content, metadata, embedding) VALUES ($1, $2::jsonb, NULL)",
            insert_params
        )
        
    print("Insertion complete. Verifying...")
    
    # Post-migration checks
    post_count = await conn.fetchval("SELECT count(*) FROM document_embeddings")
    if post_count != pre_count + 2492:
        print(f"CRITICAL ERROR: Post count is {post_count}, expected {pre_count + 2492}")
        sys.exit(1)
        
    migrated_rows = await conn.fetch("SELECT id, content, metadata, embedding IS NULL as is_null FROM document_embeddings WHERE metadata->>'migration_batch' = 'phase4d_final_2492'")
    
    if len(migrated_rows) != 2492:
        print(f"CRITICAL ERROR: Found {len(migrated_rows)} migrated rows, expected 2492.")
        sys.exit(1)
        
    validation_errors = []
    seen_source_ids = set()
    post_role_counts = Counter()
    
    for row in migrated_rows:
        meta = json.loads(row['metadata'])
        if not row['is_null']:
            validation_errors.append(f"Row {row['id']} has an embedding!")
        if meta.get("status") != "active":
            validation_errors.append(f"Row {row['id']} status is not active")
        if meta.get("source") != "InterviewMind Phase 4D":
            validation_errors.append(f"Row {row['id']} source is wrong")
        if meta.get("dataset_type") != "curated_new":
            validation_errors.append(f"Row {row['id']} dataset_type is wrong")
            
        src_id = meta.get("source_question_id")
        if src_id in seen_source_ids:
            validation_errors.append(f"Duplicate source ID {src_id}")
        seen_source_ids.add(src_id)
        
        post_role_counts[meta.get("primary_role")] += 1
        
        if not row['content']:
            validation_errors.append(f"Row {row['id']} has empty content")
            
    for k, v in expected_roles.items():
        if post_role_counts[k] != v:
            validation_errors.append(f"Role count mismatch after insert for {k}. Expected {v}, got {post_role_counts[k]}")
            
    # Legacy preservation check
    post_ids = set(r['id'] for r in await conn.fetch("SELECT id FROM document_embeddings"))
    if not pre_ids.issubset(post_ids):
        validation_errors.append("CRITICAL ERROR: Some legacy IDs are missing!")
        
    if validation_errors:
        print("MIGRATION FAILED POST-VALIDATION:")
        for e in validation_errors:
            print(e)
        sys.exit(1)
        
    print("All post-migration verification checks passed!")
    
    # Determine RAG compatibility warning
    # Application often expects snake_case roles like backend_developer
    # We inserted Title Case "Backend Developer"
    rag_warning = "Legacy DB metadata uses Title Case for roles (e.g. 'Backend Developer'), which we preserved per instructions. However, the application code may use snake_case filtering (e.g. 'backend_developer'). This represents a potential compatibility issue."

    # Final reports
    verification = {
        "source_sha256": file_hash,
        "source_size": file_size,
        "source_count": len(new_records),
        "pre_migration_db_count": pre_count,
        "inserted_count": 2492,
        "post_migration_db_count": post_count,
        "new_migration_batch_count": len(migrated_rows),
        "role_counts": dict(post_role_counts),
        "status_counts": {"active": len(migrated_rows)},
        "embedding_null_count": len(migrated_rows),
        "legacy_preservation": "SUCCESS - All legacy IDs preserved",
        "metadata_validation": "SUCCESS",
        "duplicate_checks": "SUCCESS - 0 duplicates",
        "transaction_status": "COMMITTED",
        "migration_duration_seconds": round(time.time() - start_time, 2),
        "warnings": [rag_warning]
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4e_migration_verification_v1.json"), "w") as f:
        json.dump(verification, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4e_migration_report_v1.json"), "w") as f:
        json.dump(verification, f, indent=2)
        
    md = [
        "# Phase 4E - Migration Report",
        "",
        "### Overview",
        "- **Status**: SUCCESS",
        "- **Migrated Records**: 2,492",
        f"- **Time**: {verification['migration_duration_seconds']}s",
        "",
        "### Database Changes",
        f"- **Pre-Migration Rows**: {pre_count}",
        f"- **Post-Migration Rows**: {post_count}",
        "- **Legacy Rows Modified**: 0",
        "",
        "### New Record State",
        "- **Status**: `active`",
        "- **Embeddings**: `NULL` (Intentional)",
        "- **Migration Batch**: `phase4d_final_2492`",
        "- **Source**: `InterviewMind Phase 4D`",
        "",
        "### Role Breakdown",
        *[f"- {k}: {v}" for k, v in expected_roles.items()],
        "",
        "### Pre-Migration Legacy State (For Reference)",
        f"- **Active Rows**: {pre_active}",
        f"- **Inactive Rows**: {pre_inactive}",
        f"- **Null Embeddings**: {pre_null}",
        f"- **Populated Embeddings**: {pre_populated}",
        "",
        "### Warnings & Observations",
        f"- {rag_warning}"
    ]
    with open(os.path.join(REPORTS_DIR, "phase4e_migration_report_v1.md"), "w") as f:
        f.write("\n".join(md))

    await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
