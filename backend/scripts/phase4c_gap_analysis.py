import json
import os
import sys
import re
import csv
import asyncio
from collections import defaultdict, Counter
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.services.question_controller import detect_question_intent

load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

TARGET_ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
    "Machine Learning Engineer", "Full Stack Developer"
]

INTENTS = ["fundamentals", "explain", "implement", "compare", "tradeoff", "debug", "scenario", "design", "architecture", "optimize", "diagnose"]
DIFFICULTIES = ["easy", "medium", "hard"]

def assign_skill(taxonomy, role, text):
    t = text.lower()
    for skill, data in taxonomy.get(role, {}).items():
        for tech in data["tech"]:
            if tech.lower() in t:
                return skill
    return list(taxonomy.get(role, {}).keys())[0] if taxonomy.get(role) else "General"

def generate_applicable_roles(primary_role, skill, text):
    roles = set([primary_role])
    t = text.lower()
    if primary_role in ["Frontend Developer", "Backend Developer"]: roles.add("Full Stack Developer")
    if "sql" in t or skill == "SQL": roles.update(["Database Developer", "Backend Developer", "Data Analyst", "Full Stack Developer"])
    if skill in ["AWS", "Linux", "Kubernetes", "CI/CD"]: roles.add("DevOps / Cloud Engineer")
    if "python" in t: roles.add("Python Developer")
    if "java" in t and "javascript" not in t: roles.add("Java Developer")
    if "javascript" in t or "react" in t:
        roles.add("Frontend Developer")
        roles.add("Full Stack Developer")
    if skill == "System Design": roles.update(["Backend Developer", "Full Stack Developer", "DevOps / Cloud Engineer"])
    return list(roles.intersection(TARGET_ROLES))

def determine_difficulty(q_text, intent):
    t = q_text.lower()
    if intent in ["architecture", "design", "tradeoff", "scenario", "optimize"]: return "hard"
    if intent in ["implement", "debug", "diagnose", "compare"]: return "medium"
    if len(t.split()) > 25 or "difference" in t: return "medium"
    return "easy"

async def fetch_all_supabase():
    db_url = os.getenv("DATABASE_URL")
    clean_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://") if not db_url.startswith("postgresql+asyncpg") else db_url
    engine = create_async_engine(clean_db_url)
    out_rows = []
    async with engine.connect() as conn:
        res = await conn.execute(sql_text("SELECT id, content, metadata FROM public.document_embeddings;"))
        for r in res.fetchall():
            out_rows.append({"id": str(r[0]), "content": r[1], "metadata": r[2] if isinstance(r[2], dict) else json.loads(r[2] or "{}")})
    await engine.dispose()
    return out_rows

def main():
    with open(os.path.join(REPORTS_DIR, "phase4b_final_taxonomy.json"), "r") as f:
        taxonomy = json.load(f)
        
    print("Fetching directly from DB via asyncpg...")
    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_running_loop()
        records = loop.run_until_complete(fetch_all_supabase())
    except Exception:
        records = asyncio.run(fetch_all_supabase())
        
    print(f"Total rows fetched: {len(records)}")
    
    verified = []
    role_counts = Counter()
    skill_counts = Counter()
    topic_counts = Counter()
    tech_counts = Counter()
    intent_counts = Counter()
    diff_counts = Counter()
    
    for r in records:
        meta = r.get("metadata", {})
        if meta.get("status") == "inactive": continue
        c = r.get("content", "")
        if "### Instruction:" in c and "### Output:" in c:
            q_text = c.split("### Instruction:")[1].split("### Output:")[0].strip()
            if "write a program" in q_text.lower() or "implement a function" in q_text.lower(): continue
        elif "### Technical Interview Question" in c:
            try:
                if "**Answer:**" in c:
                    q_text = c.split("**Answer:**")[0].replace("### Technical Interview Question", "").replace("**Question:**", "").strip()
                else:
                    q_text = meta.get("question", c[:200])
            except Exception:
                q_text = meta.get("question", c[:200])
        else:
            q_text = meta.get("question", c[:200])
            
        words = set(re.findall(r"\b[a-z0-9]+\b", q_text.lower()))
        if len(words) < 3: continue
        
        intent = detect_question_intent(q_text)
        diff = determine_difficulty(q_text, intent)
        
        role = meta.get("role", "Backend Developer")
        if role not in TARGET_ROLES:
            if meta.get("source") == "JavaScript" or meta.get("source") == "React": role = "Frontend Developer"
            elif "DevOps" in meta.get("source", ""): role = "DevOps / Cloud Engineer"
            else: role = "Backend Developer"
            
        deep_skill = assign_skill(taxonomy, role, q_text)
        applicable = generate_applicable_roles(role, deep_skill, q_text)
        
        q_type = "concept"
        if intent in ["implement"]: q_type = "implementation"
        if intent in ["debug", "diagnose"]: q_type = "debugging"
        if intent == "scenario": q_type = "scenario"
        if intent == "tradeoff": q_type = "tradeoff"
        if intent == "compare": q_type = "comparison"
        if intent in ["architecture", "design"]: q_type = "architecture"
        
        tech = taxonomy.get(role, {}).get(deep_skill, {}).get("tech", ["Gen"])[0]
        topic = taxonomy.get(role, {}).get(deep_skill, {}).get("topics", ["Gen"])[0]
        
        verified.append({
            "id": r["id"],
            "question": q_text,
            "primary_role": role,
            "applicable_roles": applicable,
            "primary_skill": deep_skill,
            "technology": tech,
            "topic": topic,
            "intent": intent,
            "difficulty": diff,
            "question_type": q_type
        })
        
        for ar in applicable: role_counts[ar] += 1
        skill_counts[deep_skill] += 1
        tech_counts[tech] += 1
        topic_counts[topic] += 1
        intent_counts[intent] += 1
        diff_counts[diff] += 1

    coverage = defaultdict(lambda: {"existing": 0, "intents": Counter(), "difficulties": Counter(), "types": Counter()})
    
    for v in verified:
        for r in v["applicable_roles"]:
            key = (r, v["primary_skill"], v["technology"], v["topic"])
            coverage[key]["existing"] += 1
            coverage[key]["intents"][v["intent"]] += 1
            coverage[key]["difficulties"][v["difficulty"]] += 1
            coverage[key]["types"][v["question_type"]] += 1

    gap_matrix_list = []
    generation_plan = []
    total_recs = 0
    top_100_buckets = []

    for role, data in taxonomy.items():
        for skill, meta in data.items():
            for topic in meta["topics"]:
                tech = meta["tech"][0]
                key = (role, skill, tech, topic)
                cov = coverage[key]
                
                target = 30 if meta["priority"] == "CORE" else (20 if meta["priority"] == "IMPORTANT" else 10)
                target = target // len(meta["topics"])
                if target < 3: target = 3
                
                missing_intents = []
                for i in INTENTS:
                    if i in ["explain", "fundamentals", "implement"] and cov["intents"][i] == 0: missing_intents.append(i)
                    elif i in ["debug", "architecture", "tradeoff", "scenario"] and meta["priority"] == "CORE" and cov["intents"][i] == 0: missing_intents.append(i)
                
                missing_difficulties = []
                for d in DIFFICULTIES:
                    if cov["difficulties"][d] == 0: missing_difficulties.append(d)
                    
                gap = max(0, target - cov["existing"])
                
                prio = 4
                if cov["existing"] == 0 and meta["priority"] == "CORE": prio = 1
                elif meta["priority"] == "CORE" and len(missing_intents) > 3: prio = 2
                elif meta["priority"] == "CORE" and len(missing_difficulties) > 1: prio = 3
                
                gap_matrix_list.append({
                    "ROLE": role,
                    "SKILL": skill,
                    "TECHNOLOGY": tech,
                    "TOPIC": topic,
                    "PRIORITY": meta["priority"],
                    "EXISTING": cov["existing"],
                    "TARGET": target,
                    "GAP": gap,
                    "MISSING_INTENTS": missing_intents,
                    "MISSING_DIFFICULTIES": missing_difficulties
                })
                
                if gap > 0:
                    plan = {
                        "role": role,
                        "skill": skill,
                        "technology": tech,
                        "topic": topic,
                        "missing_intents": missing_intents,
                        "missing_difficulties": missing_difficulties,
                        "recommended_question_count": gap,
                        "priority": prio
                    }
                    generation_plan.append(plan)
                    total_recs += gap
                    top_100_buckets.append(plan)
                    
    top_100_buckets.sort(key=lambda x: (x["priority"], -x["recommended_question_count"]))
    top_100_buckets = top_100_buckets[:100]

    with open(os.path.join(REPORTS_DIR, "phase4c_gap_matrix.json"), "w") as f: json.dump(gap_matrix_list, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4c_generation_plan.json"), "w") as f: json.dump(generation_plan, f, indent=2)
    
    with open(os.path.join(REPORTS_DIR, "phase4c_gap_matrix.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=gap_matrix_list[0].keys())
        writer.writeheader()
        writer.writerows([{**row, "MISSING_INTENTS": "|".join(row["MISSING_INTENTS"]), "MISSING_DIFFICULTIES": "|".join(row["MISSING_DIFFICULTIES"])} for row in gap_matrix_list])
        
    with open(os.path.join(REPORTS_DIR, "phase4c_role_coverage.json"), "w") as f: json.dump(dict(role_counts), f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4c_intent_coverage.json"), "w") as f: json.dump(dict(intent_counts), f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4c_difficulty_coverage.json"), "w") as f: json.dump(dict(diff_counts), f, indent=2)

    print(f"Total verified existing questions: {len(verified)}")
    print(f"Coverage by role: {dict(role_counts)}")
    print(f"Coverage by skill: {dict(skill_counts)}")
    print(f"Coverage by technology: {dict(tech_counts)}")
    print(f"Coverage by topic: {dict(topic_counts)}")
    print(f"Intent imbalance: {dict(intent_counts)}")
    print(f"Difficulty imbalance: {dict(diff_counts)}")
    print(f"Exact missing buckets: {len(generation_plan)}")
    print(f"Total recommended generation count: {total_recs}")
    print(f"Top 100 highest-priority missing buckets saved to phase4c_generation_plan.json")

if __name__ == "__main__":
    main()
