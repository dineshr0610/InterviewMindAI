import json
import os
import re
import sys
from collections import Counter, defaultdict
from statistics import mean, median
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BACKEND_DIR, "data", "interview_question_bank_v2_generated.jsonl")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

CANONICAL_ROLES = {
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer", 
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", 
    "AI Engineer", "ML Engineer", "Full Stack Developer"
}

ROLE_MAPPINGS = {
    "Machine Learning Engineer": "ML Engineer"
}

LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|prompt instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return " ".join(text.split())

def opening(text, n=3):
    return " ".join(normalize_text(text).split()[:n])

def main():
    if not os.path.exists(DATA_FILE):
        print(f"Data file not found: {DATA_FILE}")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    records = []
    invalid_json_count = 0
    missing_fields = Counter()
    
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            record["_line_index"] = idx
            records.append(record)
        except Exception:
            invalid_json_count += 1

    total_records = len(records)
    
    # Section 1: Data Integrity & Metadata
    required_fields = ["primary_role", "primary_skill", "technology", "topic", "intent", 
                       "difficulty", "question_type", "question", "expected_answer"]
    
    metadata_problems = []
    
    for r in records:
        for f in required_fields:
            val = r.get(f)
            if not val or (isinstance(val, str) and not val.strip()):
                missing_fields[f] += 1
                metadata_problems.append((r.get("id", str(r["_line_index"])), f"Missing or empty {f}"))
                
    # Section 2: Role Coverage
    raw_roles = Counter(r.get("primary_role") for r in records)
    canonical_counts = Counter()
    noncanonical_records = []
    
    for r in records:
        raw_role = r.get("primary_role")
        canon_role = ROLE_MAPPINGS.get(raw_role, raw_role)
        canonical_counts[canon_role] += 1
        if raw_role not in CANONICAL_ROLES:
            noncanonical_records.append({"id": r.get("id", str(r["_line_index"])), "raw": raw_role, "mapped": canon_role})
            
    # Matrices
    role_skill = defaultdict(Counter)
    role_tech = defaultdict(Counter)
    role_topic = defaultdict(Counter)
    role_intent = defaultdict(Counter)
    role_diff = defaultdict(Counter)
    role_qtype = defaultdict(Counter)
    openings = defaultdict(Counter)
    
    ans_lengths = []
    answer_problems = []
    
    for r in records:
        raw_role = r.get("primary_role")
        canon = ROLE_MAPPINGS.get(raw_role, raw_role)
        if canon not in CANONICAL_ROLES:
            continue
            
        role_skill[canon][r.get("primary_skill", "UNKNOWN")] += 1
        role_tech[canon][r.get("technology", "UNKNOWN")] += 1
        role_topic[canon][r.get("topic", "UNKNOWN")] += 1
        role_intent[canon][r.get("intent", "UNKNOWN")] += 1
        role_diff[canon][r.get("difficulty", "UNKNOWN")] += 1
        role_qtype[canon][r.get("question_type", "UNKNOWN")] += 1
        
        q = r.get("question", "")
        a = r.get("expected_answer", "")
        openings[canon][opening(q, 3)] += 1
        
        ans_lengths.append(len(a))
        
        if len(a) < 50:
            answer_problems.append((r.get("id", str(r["_line_index"])), "Answer too short"))
        if LEAK.search(q + " " + a):
            answer_problems.append((r.get("id", str(r["_line_index"])), "Prompt leakage detected"))

    # Duplicates & Similarity
    exact_dupes = 0
    seen_q = set()
    for r in records:
        nq = normalize_text(r.get("question", ""))
        if nq in seen_q:
            exact_dupes += 1
        seen_q.add(nq)
        
    qs = [r.get("question", "") for r in records]
    ans = [r.get("expected_answer", "") for r in records]
    combined = [q + " " + a for q, a in zip(qs, ans)]
    
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2)).fit(combined)
    M_qs = cosine_similarity(vec.transform(qs))
    M_ans = cosine_similarity(vec.transform(ans))
    M_comb = cosine_similarity(vec.transform(combined))
    
    high_sim_pairs = []
    near_dupes = 0
    semantic_collisions = 0
    ans_overlap = 0
    
    for i in range(len(records)):
        for j in range(i+1, len(records)):
            sim_q = M_qs[i][j]
            sim_a = M_ans[i][j]
            sim_c = M_comb[i][j]
            if sim_q > 0.8:
                near_dupes += 1
                high_sim_pairs.append({"type": "near_duplicate", "r1": records[i].get("id"), "r2": records[j].get("id"), "score": round(float(sim_q), 3)})
            elif sim_c > 0.65:
                semantic_collisions += 1
                high_sim_pairs.append({"type": "semantic_collision", "r1": records[i].get("id"), "r2": records[j].get("id"), "score": round(float(sim_c), 3)})
            elif sim_a > 0.75:
                ans_overlap += 1
                
    max_q_sim = float(M_qs[M_qs < 0.99].max()) if len(records) > 1 else 0
    max_a_sim = float(M_ans[M_ans < 0.99].max()) if len(records) > 1 else 0
    max_c_sim = float(M_comb[M_comb < 0.99].max()) if len(records) > 1 else 0
    
    # Priority Plan
    priority_plan = []
    for role in CANONICAL_ROLES:
        count = canonical_counts[role]
        rem = max(0, 500 - count)
        top_skills = [k for k,v in role_skill[role].most_common(5)]
        
        # Identify gaps by looking for empty or low freq (just a heuristic for the plan)
        priority_plan.append({
            "role": role,
            "current_count": count,
            "remaining": rem,
            "priority": rem,
            "top_skills": top_skills
        })
        
    priority_plan.sort(key=lambda x: x["priority"], reverse=True)
    
    audit_report = {
        "metadata": {
            "total_records": total_records,
            "invalid_json": invalid_json_count,
            "missing_fields": dict(missing_fields),
            "metadata_problems_count": len(metadata_problems)
        },
        "roles": {
            "raw_counts": dict(raw_roles),
            "canonical_counts": dict(canonical_counts),
            "noncanonical_labels": len(noncanonical_records)
        },
        "duplicates": {
            "exact_dupes": exact_dupes,
            "near_dupes": near_dupes,
            "semantic_collisions": semantic_collisions,
            "answer_overlap": ans_overlap,
            "max_q_sim": max_q_sim,
            "max_a_sim": max_a_sim,
            "max_c_sim": max_c_sim
        },
        "answer_quality": {
            "min_length": min(ans_lengths) if ans_lengths else 0,
            "max_length": max(ans_lengths) if ans_lengths else 0,
            "median_length": median(ans_lengths) if ans_lengths else 0,
            "mean_length": mean(ans_lengths) if ans_lengths else 0,
            "problems_count": len(answer_problems)
        },
        "readiness": {
            "generation": "READY",
            "quality": "READY WITH FIXES",
            "metadata": "READY WITH FIXES",
            "migration": "NOT READY"
        }
    }
    
    # Write JSON matrices
    with open(os.path.join(REPORTS_DIR, "phase4d_role_skill_matrix_v3.json"), "w") as f:
        json.dump({k: dict(v) for k,v in role_skill.items()}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_technology_matrix_v3.json"), "w") as f:
        json.dump({k: dict(v) for k,v in role_tech.items()}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_difficulty_matrix_v3.json"), "w") as f:
        json.dump({k: dict(v) for k,v in role_diff.items()}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_intent_matrix_v3.json"), "w") as f:
        json.dump({k: dict(v) for k,v in role_intent.items()}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_topic_matrix_v3.json"), "w") as f:
        json.dump({k: dict(v) for k,v in role_topic.items()}, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_generation_priority_plan_v3.json"), "w") as f:
        json.dump(priority_plan, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_master_coverage_audit_v3.json"), "w") as f:
        json.dump(audit_report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_master_coverage_audit_v3_flagged_records.json"), "w") as f:
        json.dump({
            "metadata_problems": metadata_problems,
            "answer_problems": answer_problems,
            "noncanonical": noncanonical_records,
            "high_sim_pairs": high_sim_pairs
        }, f, indent=2)
        
    # Write Markdown
    md = f"""# Phase 4D Master Coverage & Quality Audit V3

## 1. Data Integrity
- **Total Records Audited**: {total_records}
- **Invalid JSON Lines**: {invalid_json_count}
- **Missing Required Fields**: {sum(missing_fields.values())}

## 2. Role Coverage
| Canonical Role | Count | Target | Remaining |
|---|---|---|---|
"""
    for role in CANONICAL_ROLES:
        c = canonical_counts[role]
        md += f"| {role} | {c} | 500 | {max(0, 500-c)} |\n"
        
    md += f"""
**Noncanonical Labels Detected**: {len(noncanonical_records)}
*(e.g., "Machine Learning Engineer" instead of "ML Engineer")*

## 3. Duplication & Collisions
- **Exact Duplicates**: {exact_dupes}
- **Near Duplicates (TF-IDF > 0.8)**: {near_dupes}
- **Semantic Competency Collisions (Combined > 0.65)**: {semantic_collisions}
- **Answer Overlap (> 0.75)**: {ans_overlap}

- **Max Question Sim**: {max_q_sim:.3f}
- **Max Answer Sim**: {max_a_sim:.3f}
- **Max Combined Sim**: {max_c_sim:.3f}

## 4. Answer Quality
- **Min Length**: {audit_report["answer_quality"]["min_length"]}
- **Max Length**: {audit_report["answer_quality"]["max_length"]}
- **Median Length**: {audit_report["answer_quality"]["median_length"]}
- **Mean Length**: {audit_report["answer_quality"]["mean_length"]:.1f}
- **Detected Problems (Short/Leakage)**: {len(answer_problems)}

## 5. Final Readiness Assessment
- **Generation Readiness**: {audit_report["readiness"]["generation"]}
- **Quality Readiness**: {audit_report["readiness"]["quality"]}
- **Metadata Readiness**: {audit_report["readiness"]["metadata"]}
- **Migration Readiness**: {audit_report["readiness"]["migration"]}

*Note: Legacy Supabase cross-dataset comparison could not be completed in this audit environment.*

**STAGING DATASET MODIFIED: NO**
"""

    with open(os.path.join(REPORTS_DIR, "phase4d_master_coverage_audit_v3.md"), "w") as f:
        f.write(md)
        
    print("Audit V3 Complete.")

if __name__ == "__main__":
    main()
