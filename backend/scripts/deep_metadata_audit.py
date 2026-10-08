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

async def deep_audit():
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        res = await conn.execute(sql_text("""
            SELECT id, content, metadata, 
                   CASE WHEN embedding IS NULL THEN 1 ELSE 0 END AS is_null,
                   created_at
            FROM public.document_embeddings;
        """))
        rows = list(res.mappings())
        
    print(f"Total rows fetched: {len(rows)}")
    
    # Metadata fields distribution
    meta_keys = Counter()
    field_values = defaultdict(Counter)
    
    # Let's inspect fields of interest:
    # skill, technology, topic, subtopic, category, role, role_id, difficulty, strategy, intent,
    # answer, explanation, evaluation rubric, tags, source, status, languages, dataset_type
    
    all_possible_fields = [
        "question", "skill", "technology", "topic", "subtopic", "category",
        "role", "role_id", "difficulty", "strategy", "intent", "answer",
        "explanation", "rubric", "evaluation_rubric", "tags", "source",
        "metadata", "status", "languages", "dataset_type"
    ]
    
    field_stats = {}
    for fld in all_possible_fields:
        field_stats[fld] = {
            "present_count": 0,
            "null_or_empty_count": 0,
            "distinct_values": 0,
            "sample_values": [],
            "top_values": []
        }
        
    for r in rows:
        meta = r["metadata"] or {}
        for fld in all_possible_fields:
            val = meta.get(fld)
            if val is not None and val != "" and val != [] and val != {}:
                field_stats[fld]["present_count"] += 1
                if isinstance(val, list):
                    field_values[fld][f"list:{','.join(str(x) for x in val[:3])}"] += 1
                elif isinstance(val, dict):
                    field_values[fld]["dict"] += 1
                else:
                    field_values[fld][str(val)] += 1
            else:
                field_stats[fld]["null_or_empty_count"] += 1
                
    for fld in all_possible_fields:
        c = field_values[fld]
        field_stats[fld]["distinct_values"] = len(c)
        field_stats[fld]["top_values"] = c.most_common(20)
        field_stats[fld]["sample_values"] = [k for k, _ in c.most_common(5)]
        
    # Analyze topic vs subtopic vs category vs role vs difficulty
    topic_counter = field_values["topic"]
    category_counter = field_values["category"]
    role_counter = field_values["role"]
    difficulty_counter = field_values["difficulty"]
    status_counter = field_values["status"]
    source_counter = field_values["source"]
    languages_counter = field_values["languages"]
    
    # Inspect content text patterns in detail
    total_records = len(rows)
    ends_qmark = []
    has_qmark_somewhere = []
    no_qmark_anywhere = []
    
    short_records = []      # < 50 chars
    very_long_records = []  # > 1000 chars
    
    has_answer_marker = []
    has_rubric_marker = []
    has_markdown_code = []
    has_markdown_header = []
    has_template_explain = []
    has_placeholder = []
    
    for r in rows:
        rid = str(r["id"])
        c = (r["content"] or "").strip()
        c_lower = c.lower()
        
        if c.endswith("?"):
            ends_qmark.append(rid)
        elif "?" in c:
            has_qmark_somewhere.append(rid)
        else:
            no_qmark_anywhere.append(rid)
            
        if len(c) < 50:
            short_records.append({"id": rid, "content": c, "meta": r["metadata"]})
        if len(c) > 1000:
            very_long_records.append(rid)
            
        if any(w in c_lower for w in ["answer:", "solution:", "sample answer:", "expected output:", "answer :"]):
            has_answer_marker.append(rid)
            
        if any(w in c_lower for w in ["rubric", "evaluation criteria", "scoring criteria", "points:"]):
            has_rubric_marker.append(rid)
            
        if "```" in c:
            has_markdown_code.append(rid)
            
        if re.search(r"^#{1,6}\s", c, re.MULTILINE):
            has_markdown_header.append(rid)
            
        if re.search(r"^(?:explain|describe|what is|how does|what are)\b", c_lower):
            has_template_explain.append(rid)
            
        if any(p in c for p in ["{{", "}}", "<insert", "<your", "..."]):
            has_placeholder.append(rid)
            
    # Audit status distribution
    print("\n--- STATUS COUNTER ---")
    print(dict(status_counter))
    
    # Audit source distribution
    print("\n--- SOURCE COUNTER ---")
    print(dict(source_counter.most_common(10)))
    
    # Audit topic distribution
    print(f"\n--- TOPICS: {len(topic_counter)} distinct ---")
    print(topic_counter.most_common(25))
    
    # Audit categories
    print(f"\n--- CATEGORIES: {len(category_counter)} distinct ---")
    print(category_counter.most_common(25))
    
    # Audit roles
    print(f"\n--- ROLES: {len(role_counter)} distinct ---")
    print(role_counter.most_common(25))
    
    # Audit difficulty
    print(f"\n--- DIFFICULTY: {len(difficulty_counter)} distinct ---")
    print(dict(difficulty_counter))
    
    # Audit languages
    print(f"\n--- LANGUAGES: {len(languages_counter)} distinct ---")
    print(languages_counter.most_common(15))
    
    # Dump full details to json
    detailed_report = {
        "field_stats": field_stats,
        "topic_distribution": dict(topic_counter.most_common(100)),
        "category_distribution": dict(category_counter.most_common(100)),
        "role_distribution": dict(role_counter.most_common(100)),
        "difficulty_distribution": dict(difficulty_counter),
        "status_distribution": dict(status_counter),
        "languages_distribution": dict(languages_counter.most_common(50)),
        "source_distribution": dict(source_counter.most_common(50)),
        "text_patterns": {
            "total_records": total_records,
            "ends_with_question_mark": len(ends_qmark),
            "contains_question_mark_not_at_end": len(has_qmark_somewhere),
            "no_question_mark_anywhere": len(no_qmark_anywhere),
            "short_records_lt_50_chars": len(short_records),
            "very_long_records_gt_1000_chars": len(very_long_records),
            "has_answer_marker": len(has_answer_marker),
            "has_rubric_marker": len(has_rubric_marker),
            "has_markdown_code": len(has_markdown_code),
            "has_markdown_header": len(has_markdown_header),
            "has_template_explain": len(has_template_explain),
            "has_placeholder": len(has_placeholder)
        },
        "sample_short_records": short_records[:10]
    }
    
    with open("reports/deep_metadata_audit.json", "w", encoding="utf-8") as f:
        json.dump(detailed_report, f, indent=2)
    print("Saved deep metadata audit to reports/deep_metadata_audit.json")

if __name__ == "__main__":
    asyncio.run(deep_audit())
