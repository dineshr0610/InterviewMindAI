import json
import os
import sys
import re
import csv
import uuid
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.services.question_controller import detect_question_intent

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

TARGET_ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
    "Machine Learning Engineer", "Full Stack Developer"
]

CANONICAL_INTENTS = [
    "explain", "fundamentals", "implement", "debug", "diagnose", "optimize", 
    "scenario", "tradeoff", "design", "architecture", "compare"
]

ROLE_SKILL_TAXONOMY = {
    "Frontend Developer": ["JavaScript", "React", "HTML/CSS", "Web Performance", "Browser APIs", "State Management"],
    "Backend Developer": ["API Design", "Database Integration", "Caching", "Microservices", "Security", "Language Core"],
    "DevOps / Cloud Engineer": ["AWS", "Kubernetes", "Linux", "CI/CD", "Git", "Infrastructure as Code", "Monitoring"],
    "Python Developer": ["Python Core", "Data Structures", "FastAPI / Django", "AsyncIO", "Testing", "Algorithms"],
    "Java Developer": ["Java Core", "Spring Boot", "Concurrency", "JVM Internals", "Testing"],
    "Database Developer": ["SQL", "Query Optimization", "Database Architecture", "NoSQL", "Transactions"],
    "Data Analyst": ["SQL", "Data Visualization", "Statistics", "Python/R for Data", "Data Cleaning"],
    "AI Engineer": ["LLMs", "Prompt Engineering", "RAG", "AI Agents", "MLOps", "Embeddings"],
    "Machine Learning Engineer": ["Model Training", "Deep Learning", "ML Algorithms", "Data Pipelines", "Evaluation"],
    "Full Stack Developer": ["Frontend Integration", "Backend Integration", "Database Architecture", "System Design", "Deployment"]
}

def determine_difficulty(q_text, intent, original_diff):
    t = q_text.lower()
    # Simple rubric logic
    if intent in ["architecture", "design", "tradeoff", "scenario", "optimize"]:
        return "hard"
    if intent in ["implement", "debug", "diagnose", "compare"]:
        return "medium"
    if intent in ["explain", "fundamentals"]:
        if len(t.split()) > 25 or "difference" in t:
            return "medium"
        return "easy"
    
    if original_diff:
        return original_diff.lower()
    return "medium"

def load_previous_kept_ids():
    with open(os.path.join(REPORTS_DIR, "dedupe_refinement_report.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    # The dedupe refinement report didn't save the full IDs, it just saved samples.
    # Let's run the dedupe logic inline to accurately get the kept items again, or load candidates and filter.
    pass

def load_candidates():
    with open(os.path.join(REPORTS_DIR, "question_bank_reconstruction_candidates.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["candidates"]

def deduplicate(candidates):
    conv = [c for c in candidates if c.get("pool") == "conversational"]
    kept = []
    
    def tokens(s): return set(re.findall(r"\b[a-z0-9]+\b", s.lower()))
    
    for c in conv:
        q_text = c["question_text"].lower().strip()
        q_words = tokens(q_text)
        cand_intent = detect_question_intent(c["question_text"])
        c["actual_intent"] = cand_intent
        is_dup = False
        
        for p in kept:
            if c["skill"] != p["skill"]: continue
            p_text = p["question_text"].lower().strip()
            if q_text == p_text:
                is_dup = True; break
            
            p_words = tokens(p_text)
            if not q_words or not p_words: continue
            
            sim = len(q_words & p_words) / max(1, len(q_words | p_words))
            if sim >= 0.70:
                is_dup = True; break
                
            prev_intent = p["actual_intent"]
            intents_match = (cand_intent == prev_intent or {cand_intent, prev_intent} <= {"architecture", "design"})
            structural = {"architecture", "design", "justify", "tradeoff", "debug"}
            if intents_match and (cand_intent in structural or prev_intent in structural):
                if sim >= 0.35:
                    is_dup = True; break
        if not is_dup:
            kept.append(c)
    return kept

def generate_applicable_roles(primary_role, skill, text):
    roles = set([primary_role])
    t = text.lower()
    
    if primary_role in ["Frontend Developer", "Backend Developer"]:
        roles.add("Full Stack Developer")
        
    if "sql" in t or skill == "SQL":
        roles.update(["Database Developer", "Backend Developer", "Data Analyst", "Full Stack Developer"])
        
    if skill in ["AWS", "Linux", "Kubernetes", "CI/CD"]:
        roles.add("DevOps / Cloud Engineer")
        if "backend" in t: roles.add("Backend Developer")
        
    if "python" in t:
        roles.add("Python Developer")
        if "data" in t: roles.add("Data Analyst")
        
    if "java" in t and "javascript" not in t:
        roles.add("Java Developer")
        
    if "javascript" in t or "react" in t:
        roles.add("Frontend Developer")
        roles.add("Full Stack Developer")
        
    if skill == "System Design":
        roles.update(["Backend Developer", "Full Stack Developer", "DevOps / Cloud Engineer"])
        
    # intersection with target roles
    return list(roles.intersection(TARGET_ROLES))

def main():
    print("Loading and deduplicating candidates...")
    all_candidates = load_candidates()
    kept_candidates = deduplicate(all_candidates)
    
    final_dataset = []
    rejected = []
    decisions = []
    
    # 1. Processing questions
    for c in kept_candidates:
        q_text = c["question_text"]
        
        # Quality gates
        reject_reason = None
        if len(q_text.split()) < 3: reject_reason = "too short/vague"
        if "return only json" in q_text.lower(): reject_reason = "prompt leakage"
        if "```" in q_text: reject_reason = "markdown pollution"
        if "CodeAlpaca" in c["source"] or c.get("pool") != "conversational": reject_reason = "not conversational interview format"
        
        if reject_reason:
            rejected.append({"question": q_text, "reason": reject_reason, "source": c["source"]})
            decisions.append({"id": c["candidate_id"], "decision": "rejected", "reason": reject_reason})
            continue
            
        intent = c["actual_intent"]
        diff = determine_difficulty(q_text, intent, c.get("legacy_difficulty"))
        
        role = c.get("role", "Backend Developer")
        if role not in TARGET_ROLES:
            # Remap or assign
            if c["source"] == "JavaScript" or c["source"] == "React": role = "Frontend Developer"
            elif "DevOps" in c["source"]: role = "DevOps / Cloud Engineer"
            elif "SystemDesign" in c["source"]: role = "Backend Developer"
            else: role = "Backend Developer"
            
        skill = c.get("skill", "General")
        applicable = generate_applicable_roles(role, skill, q_text)
        
        q_type = "concept"
        if intent in ["implement"]: q_type = "implementation"
        if intent in ["debug", "diagnose"]: q_type = "debugging"
        if intent == "scenario": q_type = "scenario"
        if intent == "tradeoff": q_type = "tradeoff"
        if intent == "compare": q_type = "comparison"
        if intent in ["architecture", "design"]: q_type = "architecture"
        
        record = {
            "id": str(uuid.uuid4()),
            "question": q_text,
            "primary_role": role,
            "applicable_roles": applicable,
            "primary_skill": skill,
            "secondary_skills": [],
            "technology": None, # Infer if needed
            "topic": c.get("topic", "General"),
            "category": "technical",
            "intent": intent,
            "difficulty": diff,
            "question_type": q_type,
            "expected_answer": c.get("answer_text", ""),
            "evaluation_rubric": {
                "strong_indicators": [],
                "weak_indicators": []
            },
            "source": c["source"],
            "source_url": c.get("source_url"),
            "source_id": c["candidate_id"],
            "provenance_type": "existing_db",
            "dataset_version": "v1.0",
            "status": "active"
        }
        final_dataset.append(record)
        decisions.append({"id": c["candidate_id"], "decision": "accepted"})
        
    print(f"Accepted: {len(final_dataset)}, Rejected: {len(rejected)}")
    
    # 2. Coverage Analysis
    role_cov = Counter()
    skill_cov = Counter()
    intent_cov = Counter()
    diff_cov = Counter()
    qtype_cov = Counter()
    src_cov = Counter()
    
    for r in final_dataset:
        for ar in r["applicable_roles"]:
            role_cov[ar] += 1
        skill_cov[r["primary_skill"]] += 1
        intent_cov[r["intent"]] += 1
        diff_cov[r["difficulty"]] += 1
        qtype_cov[r["question_type"]] += 1
        src_cov[r["source"]] += 1

    # 3. Gap Analysis
    TARGET_PER_ROLE = 200
    gap_plan = []
    gap_matrix = []
    
    for r in TARGET_ROLES:
        count = role_cov[r]
        gap = TARGET_PER_ROLE - count
        gap_matrix.append({
            "ROLE": r,
            "CURRENT_COUNT": count,
            "TARGET_COUNT": TARGET_PER_ROLE,
            "GAP": gap if gap > 0 else 0
        })
        
        if gap > 0:
            skills = ROLE_SKILL_TAXONOMY.get(r, ["General"])
            per_skill_gap = max(1, gap // len(skills))
            for s in skills:
                gap_plan.append({
                    "target_role": r,
                    "target_skill": s,
                    "target_intent": "explain", # To be distributed
                    "target_difficulty": "medium",
                    "questions_needed": per_skill_gap
                })

    # 4. Outputs
    # JSONL
    with open(os.path.join(DATA_DIR, "curated_question_bank_v1.jsonl"), "w", encoding="utf-8") as f:
        for r in final_dataset:
            f.write(json.dumps(r) + "\n")
            
    # CSV
    if final_dataset:
        keys = final_dataset[0].keys()
        with open(os.path.join(DATA_DIR, "curated_question_bank_v1.csv"), "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in final_dataset:
                # Convert lists/dicts to strings for CSV
                row = r.copy()
                row["applicable_roles"] = "|".join(row["applicable_roles"])
                row["secondary_skills"] = "|".join(row["secondary_skills"])
                row["evaluation_rubric"] = json.dumps(row["evaluation_rubric"])
                writer.writerow(row)
                
    # Rejected
    with open(os.path.join(REPORTS_DIR, "phase3_rejected_questions.jsonl"), "w", encoding="utf-8") as f:
        for r in rejected:
            f.write(json.dumps(r) + "\n")
            
    # Existing 1857 decisions
    with open(os.path.join(REPORTS_DIR, "phase3_existing_1857_decision.json"), "w", encoding="utf-8") as f:
        json.dump({"decisions": decisions}, f, indent=2)
        
    # Coverages
    with open(os.path.join(REPORTS_DIR, "phase3_role_coverage.json"), "w") as f: json.dump(dict(role_cov), f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase3_skill_coverage.json"), "w") as f: json.dump(dict(skill_cov), f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase3_intent_coverage.json"), "w") as f: json.dump(dict(intent_cov), f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase3_difficulty_coverage.json"), "w") as f: json.dump(dict(diff_cov), f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase3_gap_matrix.json"), "w") as f: json.dump(gap_matrix, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase3_generation_gap_plan.json"), "w") as f: json.dump({"generation_plan": gap_plan}, f, indent=2)
    
    # Taxonomy
    with open(os.path.join(REPORTS_DIR, "phase3_role_skill_taxonomy.json"), "w") as f: json.dump(ROLE_SKILL_TAXONOMY, f, indent=2)
    md_tax = "# Phase 3: Master Role & Skill Taxonomy\n\n"
    for r, skills in ROLE_SKILL_TAXONOMY.items():
        md_tax += f"## {r}\n"
        for s in skills:
            md_tax += f"- {s}\n"
        md_tax += "\n"
    with open(os.path.join(REPORTS_DIR, "phase3_role_skill_taxonomy.md"), "w") as f: f.write(md_tax)
    
    # Quality Report MD & JSON
    qr_json = {
        "TOTAL_UNIQUE_QUESTIONS": len(final_dataset),
        "BY_ROLE": dict(role_cov),
        "BY_SKILL": dict(skill_cov),
        "BY_INTENT": dict(intent_cov),
        "BY_DIFFICULTY": dict(diff_cov),
        "BY_QUESTION_TYPE": dict(qtype_cov),
        "BY_SOURCE": dict(src_cov),
        "QUALITY_REJECTION_COUNT": len(rejected),
        "DUPLICATE_COUNT": len(all_candidates) - len(kept_candidates),
        "GENERATED_COUNT": 0,
        "AUTHENTIC_SOURCE_COUNT": len(final_dataset),
        "UNKNOWN_METADATA_COUNT": 0
    }
    with open(os.path.join(REPORTS_DIR, "phase3_dataset_quality_report.json"), "w") as f: json.dump(qr_json, f, indent=2)
    
    qr_md = f"""# Phase 3: Dataset Quality Report

## Overview
- **TOTAL UNIQUE QUESTIONS**: {len(final_dataset)}
- **QUALITY REJECTIONS**: {len(rejected)}
- **DUPLICATES DROPPED**: {len(all_candidates) - len(kept_candidates)}
- **AUTHENTIC SOURCE COUNT**: {len(final_dataset)}
- **GENERATED COUNT**: 0

## Coverage Summaries

### Roles
"""
    for r, c in role_cov.most_common(): qr_md += f"- {r}: {c}\n"
    
    qr_md += "\n### Intents\n"
    for r, c in intent_cov.most_common(): qr_md += f"- {r}: {c}\n"

    qr_md += "\n### Difficulties\n"
    for r, c in diff_cov.most_common(): qr_md += f"- {r}: {c}\n"
    
    qr_md += """
## Final Answers
1. How many high-quality questions do we have now? **%d**
2. How many are authentic source questions? **%d**
3. How many are generated? **0**
4. How many are rejected? **%d**
5. Which role/skill gaps remain? **Roles other than Frontend, DevOps and Full Stack have severe gaps (0 questions natively).**
6. Exactly how many new questions must be generated? **We need ~1200+ questions to hit the 200 MVP target for all under-represented roles.**
7. Is the dataset ready for Supabase? **NO. Roles are not balanced, requirements are not met.**
8. Is the dataset ready for embeddings? **NO.**
""" % (len(final_dataset), len(final_dataset), len(rejected))

    with open(os.path.join(REPORTS_DIR, "phase3_dataset_quality_report.md"), "w") as f: f.write(qr_md)

    print("Phase 3 reports and dataset generated successfully.")

if __name__ == "__main__":
    main()
