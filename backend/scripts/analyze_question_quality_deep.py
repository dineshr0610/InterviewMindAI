import asyncio
import os
import sys
import json
import re
from collections import defaultdict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

async def inspect_questions():
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

    print(f"Total rows: {len(rows)}")
    
    # Categories of defects with concrete samples
    defects = {
        "no_question_mark": [],
        "very_short_lt_30_chars": [],
        "very_long_gt_1500_chars": [],
        "contains_answer_block": [],
        "contains_rubric_block": [],
        "contains_markdown_code_fences": [],
        "contains_markdown_headings": [],
        "explain_template_boilerplate": [],
        "write_a_program_template": [],
        "scenario_template_p99": [],
        "contains_placeholders": [],
        "tech_metadata_mismatch": []
    }
    
    tech_keywords = {
        "Python": ["python", "django", "fastapi", "flask", "pydantic"],
        "JavaScript": ["javascript", "js", "dom", "node", "typescript", "ts"],
        "React": ["react", "jsx", "hooks", "usestate", "useeffect"],
        "Java": ["java", "jvm", "spring", "hibernate"],
        "SQL": ["sql", "query", "database", "postgres", "rdbms", "table", "join"],
        "Kubernetes": ["kubernetes", "k8s", "pod", "kubectl", "cluster"],
        "Docker": ["docker", "container", "dockerfile", "image"]
    }
    
    for r in rows:
        rid = str(r["id"])
        c = (r["content"] or "").strip()
        c_lower = c.lower()
        meta = r["metadata"] or {}
        topic = str(meta.get("topic", ""))
        role = str(meta.get("role", ""))
        
        # 1. No question mark
        if "?" not in c:
            if len(defects["no_question_mark"]) < 5:
                defects["no_question_mark"].append({
                    "id": rid, "topic": topic, "content": c[:300]
                })
                
        # 2. Very short
        if len(c) < 30:
            if len(defects["very_short_lt_30_chars"]) < 5:
                defects["very_short_lt_30_chars"].append({
                    "id": rid, "topic": topic, "content": c
                })
                
        # 3. Very long
        if len(c) > 1500:
            if len(defects["very_long_gt_1500_chars"]) < 5:
                defects["very_long_gt_1500_chars"].append({
                    "id": rid, "topic": topic, "char_count": len(c), "content_preview": c[:300]
                })
                
        # 4. Answer block
        if any(m in c_lower for m in ["#### technical explanation & model answer", "**ideal model answer", "answer:"]):
            if len(defects["contains_answer_block"]) < 5:
                defects["contains_answer_block"].append({
                    "id": rid, "topic": topic, "content_preview": c[:300]
                })
                
        # 5. Rubric block
        if any(m in c_lower for m in ["**evaluation rubric**", "evaluation criteria", "- *strong candidate*"]):
            if len(defects["contains_rubric_block"]) < 5:
                defects["contains_rubric_block"].append({
                    "id": rid, "topic": topic, "content_preview": c[:300]
                })
                
        # 6. Markdown code fences
        if "```" in c:
            if len(defects["contains_markdown_code_fences"]) < 5:
                defects["contains_markdown_code_fences"].append({
                    "id": rid, "topic": topic, "content_preview": c[:300]
                })
                
        # 7. Markdown headings
        if c.startswith("### ") or c.startswith("## ") or "\n### " in c:
            if len(defects["contains_markdown_headings"]) < 5:
                defects["contains_markdown_headings"].append({
                    "id": rid, "topic": topic, "content_preview": c[:300]
                })
                
        # 8. Explain template boilerplate
        if "what are the primary trade-offs when choosing this approach over standard alternatives" in c_lower:
            if len(defects["explain_template_boilerplate"]) < 5:
                defects["explain_template_boilerplate"].append({
                    "id": rid, "topic": topic, "content_preview": c[:300]
                })
                
        # 9. Write a program template (CodeAlpaca style)
        if re.search(r"write a (?:python|java|javascript|bash)?\s*(?:program|script|function) to", c_lower):
            if len(defects["write_a_program_template"]) < 5:
                defects["write_a_program_template"].append({
                    "id": rid, "topic": topic, "content_preview": c[:300]
                })
                
        # 10. Scenario template p99
        if "p99 latency: reduced by 45%" in c_lower or "scaling" in c_lower and "production scenario:" in c_lower:
            if len(defects["scenario_template_p99"]) < 5:
                defects["scenario_template_p99"].append({
                    "id": rid, "topic": topic, "content_preview": c[:300]
                })
                
        # 11. Placeholders
        if "{{" in c or "<insert" in c_lower or "<your" in c_lower:
            if len(defects["contains_placeholders"]) < 5:
                defects["contains_placeholders"].append({
                    "id": rid, "topic": topic, "content_preview": c[:300]
                })
                
        # 12. Tech metadata mismatch
        # E.g. topic says Python, but content talks about Java or JavaScript exclusively
        if "python" in topic.lower() and "java" in c_lower and "python" not in c_lower:
            if len(defects["tech_metadata_mismatch"]) < 5:
                defects["tech_metadata_mismatch"].append({
                    "id": rid, "topic": topic, "role": role, "content_preview": c[:300]
                })
        elif "react" in topic.lower() and "python" in c_lower and "react" not in c_lower and "javascript" not in c_lower:
            if len(defects["tech_metadata_mismatch"]) < 5:
                defects["tech_metadata_mismatch"].append({
                    "id": rid, "topic": topic, "role": role, "content_preview": c[:300]
                })

    out_file = "reports/question_quality_defects_samples.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(defects, f, indent=2)
    print(f"Saved defects samples to {out_file}")

if __name__ == "__main__":
    asyncio.run(inspect_questions())
