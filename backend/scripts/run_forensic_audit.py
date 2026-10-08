import asyncio
import os
import sys
import json
from collections import Counter, defaultdict
import re
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

def clean_for_json(obj):
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    elif isinstance(obj, dict):
        return {str(k): clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [clean_for_json(v) for v in obj]
    else:
        return str(obj)

async def audit_schema(conn):
    print("--- Auditing Schema & Tables ---")
    tables = ['alembic_version', 'code_submissions', 'document_embeddings', 'interview_messages', 'interviews']
    schema_info = {}
    
    for tbl in tables:
        # Row count
        cnt_res = await conn.execute(sql_text(f"SELECT count(*) FROM public.{tbl}"))
        row_count = cnt_res.scalar()
        
        # Columns
        cols_res = await conn.execute(sql_text("""
            SELECT column_name, data_type, udt_name, is_nullable, column_default, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :tbl
            ORDER BY ordinal_position;
        """), {"tbl": tbl})
        columns = [dict(r) for r in cols_res.mappings()]
        
        # Primary Key
        pk_res = await conn.execute(sql_text("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = :tbl;
        """), {"tbl": tbl})
        pk = [r.column_name for r in pk_res]
        
        # Foreign Keys
        fk_res = await conn.execute(sql_text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.update_rule,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.referential_constraints AS rc
              ON tc.constraint_name = rc.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = :tbl;
        """), {"tbl": tbl})
        fks = [dict(r) for r in fk_res.mappings()]
        
        # Unique Constraints
        uniq_res = await conn.execute(sql_text("""
            SELECT tc.constraint_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'UNIQUE'
              AND tc.table_schema = 'public'
              AND tc.table_name = :tbl;
        """), {"tbl": tbl})
        unique_constraints = [dict(r) for r in uniq_res.mappings()]
        
        # Check Constraints
        check_res = await conn.execute(sql_text("""
            SELECT tc.constraint_name, cc.check_clause
            FROM information_schema.table_constraints tc
            JOIN information_schema.check_constraints cc
              ON tc.constraint_name = cc.constraint_name
              AND tc.table_schema = cc.constraint_schema
            WHERE tc.constraint_type = 'CHECK'
              AND tc.table_schema = 'public'
              AND tc.table_name = :tbl;
        """), {"tbl": tbl})
        check_constraints = [dict(r) for r in check_res.mappings()]
        
        # Indexes
        idx_res = await conn.execute(sql_text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = :tbl;
        """), {"tbl": tbl})
        indexes = [dict(r) for r in idx_res.mappings()]
        
        # Triggers
        trig_res = await conn.execute(sql_text("""
            SELECT trigger_name, event_manipulation, action_statement, action_timing
            FROM information_schema.triggers
            WHERE event_object_schema = 'public' AND event_object_table = :tbl;
        """), {"tbl": tbl})
        triggers = [dict(r) for r in trig_res.mappings()]
        
        # RLS Enabled
        rls_res = await conn.execute(sql_text("""
            SELECT relrowsecurity, relforcerowsecurity
            FROM pg_class
            WHERE relname = :tbl AND relnamespace = 'public'::regnamespace;
        """), {"tbl": tbl})
        rls_row = rls_res.mappings().first()
        rls_enabled = rls_row["relrowsecurity"] if rls_row else False
        rls_forced = rls_row["relforcerowsecurity"] if rls_row else False
        
        # RLS Policies
        pol_res = await conn.execute(sql_text("""
            SELECT policyname, permissive, roles, cmd, qual, with_check
            FROM pg_policies
            WHERE schemaname = 'public' AND tablename = :tbl;
        """), {"tbl": tbl})
        policies = [dict(r) for r in pol_res.mappings()]
        
        schema_info[tbl] = {
            "schema_name": "public",
            "table_name": tbl,
            "row_count": row_count,
            "columns": columns,
            "primary_key": pk,
            "foreign_keys": fks,
            "unique_constraints": unique_constraints,
            "check_constraints": check_constraints,
            "indexes": indexes,
            "triggers": triggers,
            "rls_enabled": rls_enabled,
            "rls_forced": rls_forced,
            "rls_policies": policies
        }
    
    # RPC Functions
    rpc_res = await conn.execute(sql_text("""
        SELECT p.proname, pg_get_functiondef(p.oid) AS def
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
          AND (p.proname ILIKE '%embedding%' OR p.proname ILIKE '%document%' OR p.proname ILIKE '%match%');
    """))
    rpcs = [dict(r) for r in rpc_res.mappings()]
    
    return schema_info, rpcs

async def audit_interviews_and_other_tables(conn):
    print("--- Auditing interviews, interview_messages, code_submissions ---")
    other_tables_data = {}
    for tbl in ['interviews', 'interview_messages', 'code_submissions', 'alembic_version']:
        sample_res = await conn.execute(sql_text(f"SELECT * FROM public.{tbl} LIMIT 5"))
        samples = [dict(r) for r in sample_res.mappings()]
        
        # Mask sensitive fields in samples
        masked_samples = []
        for s in samples:
            ms = {}
            for k, v in s.items():
                if any(sec in k.lower() for sec in ['secret', 'token', 'key', 'password', 'auth']):
                    ms[k] = "[MASKED]"
                else:
                    ms[k] = clean_for_json(v)
            masked_samples.append(ms)
            
        other_tables_data[tbl] = {
            "sample_count": len(samples),
            "samples": masked_samples
        }
    return other_tables_data

async def audit_document_embeddings(conn):
    print("--- Auditing document_embeddings in depth ---")
    # Fetch all rows from document_embeddings
    query = sql_text("""
        SELECT id, content, metadata, created_at,
               CASE WHEN embedding IS NULL THEN 1 ELSE 0 END AS is_embedding_null,
               CASE WHEN embedding IS NOT NULL THEN vector_dims(embedding) ELSE NULL END AS emb_dim
        FROM public.document_embeddings;
    """)
    res = await conn.execute(query)
    rows = list(res.mappings())
    total_rows = len(rows)
    print(f"Total rows fetched: {total_rows}")
    
    null_embeddings = sum(1 for r in rows if r["is_embedding_null"] == 1)
    populated_embeddings = total_rows - null_embeddings
    
    dim_counter = Counter(r["emb_dim"] for r in rows if r["emb_dim"] is not None)
    
    # Metadata keys analysis
    metadata_keys_counter = Counter()
    metadata_null_count = 0
    metadata_empty_count = 0
    active_count = 0
    inactive_count = 0
    status_other_count = 0
    
    # Field distinct counters
    fields_counter = defaultdict(Counter)
    
    # Content quality counters
    ends_with_qmark = 0
    no_qmark = 0
    content_lengths_chars = []
    content_lengths_words = []
    
    has_markdown_code = 0
    has_markdown_header = 0
    has_markdown_bullet = 0
    has_markdown_bold = 0
    
    boilerplate_counter = Counter()
    template_counter = Counter()
    placeholder_counter = Counter()
    
    # Exact duplicate tracking
    raw_content_map = defaultdict(list)
    norm_content_map = defaultdict(list)
    
    # Quality classification counters
    classification_counts = Counter()
    classification_examples = defaultdict(list)
    
    for r in rows:
        rid = str(r["id"])
        c = r["content"] or ""
        meta = r["metadata"]
        
        # Content lengths
        c_chars = len(c)
        c_words = len(c.split())
        content_lengths_chars.append(c_chars)
        content_lengths_words.append(c_words)
        
        # Question mark
        c_stripped = c.strip()
        if c_stripped.endswith("?"):
            ends_with_qmark += 1
        else:
            no_qmark += 1
            
        # Markdown patterns
        if "```" in c:
            has_markdown_code += 1
        if re.search(r"^#{1,6}\s", c, re.MULTILINE):
            has_markdown_header += 1
        if re.search(r"^\s*[-*+]\s", c, re.MULTILINE):
            has_markdown_bullet += 1
        if "**" in c or "__" in c:
            has_markdown_bold += 1
            
        # Boilerplate / templates
        c_lower = c.lower()
        if re.search(r"explain\s+(?:how|what|why|the)\b", c_lower):
            boilerplate_counter["explain_template"] += 1
        if re.search(r"in\s+this\s+(?:article|tutorial|guide|section)\b", c_lower):
            boilerplate_counter["in_this_article"] += 1
        if re.search(r"write\s+a\s+(?:program|function|script|code)\b", c_lower):
            boilerplate_counter["write_a_program"] += 1
        if re.search(r"let's\s+(?:discuss|dive|explore|take a look)\b", c_lower):
            boilerplate_counter["lets_discuss"] += 1
        if re.search(r"table\s+of\s+contents", c_lower):
            boilerplate_counter["table_of_contents"] += 1
            
        # Placeholders
        if "{{" in c or "}}" in c or "<insert" in c_lower or "<your" in c_lower:
            placeholder_counter["curly_or_angle_brackets"] += 1
        if "..." in c or "…" in c:
            placeholder_counter["ellipsis"] += 1
            
        # Duplicates map
        raw_content_map[c_stripped].append(rid)
        # Normalized content: lowercase, alphanumeric + spaces only
        norm_c = re.sub(r"[^\w\s]", "", c_lower).strip()
        norm_c = re.sub(r"\s+", " ", norm_c)
        norm_content_map[norm_c].append(rid)
        
        # Metadata check
        if meta is None:
            metadata_null_count += 1
        elif not meta or meta == {}:
            metadata_empty_count += 1
        else:
            if isinstance(meta, dict):
                for k, v in meta.items():
                    metadata_keys_counter[k] += 1
                    if isinstance(v, (str, int, float, bool)):
                        fields_counter[k][str(v)] += 1
                    elif isinstance(v, list):
                        fields_counter[k][f"list_len_{len(v)}"] += 1
                    elif isinstance(v, dict):
                        fields_counter[k]["dict"] += 1
                        
                st = meta.get("status")
                if st == "active":
                    active_count += 1
                elif st == "inactive":
                    inactive_count += 1
                elif st is not None:
                    status_other_count += 1
            else:
                metadata_empty_count += 1
                
        # 11-category heuristic audit classification
        # Categories:
        # 1. CLEAN QUESTION
        # 2. QUESTION WITH METADATA
        # 3. QUESTION + ANSWER
        # 4. QUESTION + RUBRIC
        # 5. FULL TUTORIAL/ARTICLE
        # 6. EXPLANATION WITHOUT QUESTION
        # 7. CODE EXAMPLE WITHOUT QUESTION
        # 8. DUPLICATE QUESTION (marked in post-pass)
        # 9. NEAR-DUPLICATE QUESTION (marked in post-pass)
        # 10. MALFORMED RECORD
        # 11. UNKNOWN
        
        category = "UNKNOWN"
        if not c_stripped or len(c_stripped) < 10:
            category = "MALFORMED RECORD"
        elif c_words > 250 or ("#" in c and "```" in c and c_words > 150) or boilerplate_counter["table_of_contents"] and "table of contents" in c_lower:
            category = "FULL TUTORIAL/ARTICLE"
        elif "answer:" in c_lower or "solution:" in c_lower or "expected answer" in c_lower or "sample answer" in c_lower:
            category = "QUESTION + ANSWER"
        elif "rubric" in c_lower or "evaluation criteria" in c_lower or "scoring" in c_lower:
            category = "QUESTION + RUBRIC"
        elif "```" in c and "?" not in c and c_words < 150:
            category = "CODE EXAMPLE WITHOUT QUESTION"
        elif "?" not in c and not re.search(r"^(?:explain|describe|implement|design|write|discuss|compare|what|how|why)\b", c_lower):
            category = "EXPLANATION WITHOUT QUESTION"
        elif c_stripped.endswith("?") and c_words <= 60 and "```" not in c and "\n" not in c_stripped:
            category = "CLEAN QUESTION"
        elif "?" in c and c_words <= 120:
            category = "QUESTION WITH METADATA"
        elif re.search(r"^(?:explain|describe|implement|design|write|discuss|compare)\b", c_lower) and c_words <= 80:
            category = "QUESTION WITH METADATA"
        elif "?" not in c:
            category = "EXPLANATION WITHOUT QUESTION"
        else:
            category = "UNKNOWN"
            
        classification_counts[category] += 1
        if len(classification_examples[category]) < 5:
            classification_examples[category].append({
                "id": rid,
                "preview": c[:200] + ("..." if len(c) > 200 else ""),
                "word_count": c_words,
                "metadata": meta
            })
            
    # Post-process duplicates
    exact_dup_groups = {k: v for k, v in raw_content_map.items() if len(v) > 1}
    exact_dup_records = sum(len(v) for v in exact_dup_groups.values())
    
    norm_dup_groups = {k: v for k, v in norm_content_map.items() if len(v) > 1}
    norm_dup_records = sum(len(v) for v in norm_dup_groups.values())
    
    content_lengths_chars.sort()
    content_lengths_words.sort()
    
    def get_stats(arr):
        if not arr: return {}
        return {
            "min": arr[0],
            "max": arr[-1],
            "mean": round(sum(arr) / len(arr), 2),
            "median": arr[len(arr)//2],
            "p25": arr[int(len(arr)*0.25)],
            "p75": arr[int(len(arr)*0.75)],
            "p90": arr[int(len(arr)*0.90)],
            "p95": arr[int(len(arr)*0.95)],
            "p99": arr[int(len(arr)*0.99)],
        }
        
    doc_embeddings_stats = {
        "total_rows": total_rows,
        "populated_embeddings": populated_embeddings,
        "null_embeddings": null_embeddings,
        "dimensions": dict(dim_counter),
        "status": {
            "active": active_count,
            "inactive": inactive_count,
            "other_status": status_other_count,
            "no_status_in_meta": total_rows - (active_count + inactive_count + status_other_count)
        },
        "metadata_hygiene": {
            "null_metadata": metadata_null_count,
            "empty_metadata": metadata_empty_count,
            "distinct_keys": dict(metadata_keys_counter)
        },
        "content_length_stats_chars": get_stats(content_lengths_chars),
        "content_length_stats_words": get_stats(content_lengths_words),
        "syntax": {
            "ends_with_qmark": ends_with_qmark,
            "no_qmark": no_qmark,
            "has_markdown_code": has_markdown_code,
            "has_markdown_header": has_markdown_header,
            "has_markdown_bullet": has_markdown_bullet,
            "has_markdown_bold": has_markdown_bold,
            "boilerplate": dict(boilerplate_counter),
            "placeholders": dict(placeholder_counter)
        },
        "classification_breakdown": dict(classification_counts),
        "classification_examples": dict(classification_examples),
        "duplicates": {
            "exact_duplicate_groups": len(exact_dup_groups),
            "exact_duplicate_records": exact_dup_records,
            "normalized_duplicate_groups": len(norm_dup_groups),
            "normalized_duplicate_records": norm_dup_records,
            "top_exact_duplicates": sorted([{"count": len(v), "preview": k[:150], "ids": v[:3]} for k, v in exact_dup_groups.items()], key=lambda x: x["count"], reverse=True)[:10]
        },
        "fields_distribution": {k: dict(v.most_common(50)) for k, v in fields_counter.items()}
    }
    
    return doc_embeddings_stats

async def main():
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        schema_info, rpcs = await audit_schema(conn)
        other_tables_data = await audit_interviews_and_other_tables(conn)
        doc_stats = await audit_document_embeddings(conn)
        
    full_report = {
        "schema_inventory": schema_info,
        "rpcs": rpcs,
        "other_tables": other_tables_data,
        "document_embeddings_audit": doc_stats
    }
    
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "database_dataset_forensic_audit_raw.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clean_for_json(full_report), f, indent=2)
    print(f"Raw audit saved to {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
