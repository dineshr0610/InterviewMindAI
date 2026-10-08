import json
import os
import re
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from phase4d_diversity_audit import normalize_text

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
IN_FILE = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
    "Machine Learning Engineer", "Full Stack Developer", "ML Engineer"
]

def analyze_dataset():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
        
    for r in records:
        if r.get("primary_role") == "ML Engineer":
            r["primary_role"] = "Machine Learning Engineer"

    n_total = len(records)
    print(f"Total records: {n_total}")
    
    # 1. Dataset Integrity
    ids = [r.get("id") for r in records]
    unique_ids = len(set(ids))
    unique_questions = len(set([normalize_text(r.get("question", "")) for r in records]))
    
    anomalies = []
    missing_fields = Counter()
    
    for i, r in enumerate(records):
        for field in ["primary_role", "primary_skill", "technology", "topic", "difficulty", "intent", "question_type", "question", "expected_answer"]:
            if not r.get(field):
                missing_fields[field] += 1
                anomalies.append({"id": r.get("id"), "issue": f"missing {field}"})
                
    # 2. Role Coverage
    role_counts = Counter(r.get("primary_role") for r in records)
    
    # 3. Role x Skill Matrix
    role_skill = defaultdict(Counter)
    for r in records:
        role_skill[r.get("primary_role")][r.get("primary_skill")] += 1
        
    # 4. Role x Technology Matrix
    role_tech = defaultdict(Counter)
    for r in records:
        role_tech[r.get("primary_role")][r.get("technology")] += 1

    # 5. Role x Topic Matrix
    role_topic = defaultdict(Counter)
    for r in records:
        role_topic[r.get("primary_role")][r.get("topic")] += 1

    # 6. Difficulty
    role_diff = defaultdict(Counter)
    diff_total = Counter()
    for r in records:
        role_diff[r.get("primary_role")][r.get("difficulty")] += 1
        diff_total[r.get("difficulty")] += 1
        
    # 7. Intent
    role_intent = defaultdict(Counter)
    for r in records:
        role_intent[r.get("primary_role")][r.get("intent")] += 1
        
    # 8. Question-type
    role_qtype = defaultdict(Counter)
    for r in records:
        role_qtype[r.get("primary_role")][r.get("question_type")] += 1

    # 9. Openings
    openings = Counter(" ".join(normalize_text(r.get("question", "")).split()[:4]) for r in records)
    
    # Write out matrices
    with open(os.path.join(REPORTS_DIR, "phase4d_role_skill_matrix_v2.json"), "w") as f:
        json.dump({k: dict(v) for k, v in role_skill.items()}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_technology_matrix_v2.json"), "w") as f:
        json.dump({k: dict(v) for k, v in role_tech.items()}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_topic_matrix_v2.json"), "w") as f:
        json.dump({k: dict(v) for k, v in role_topic.items()}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_difficulty_matrix_v2.json"), "w") as f:
        json.dump({k: dict(v) for k, v in role_diff.items()}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_intent_matrix_v2.json"), "w") as f:
        json.dump({k: dict(v) for k, v in role_intent.items()}, f, indent=2)

    # 10, 11, 12, 13, 14, 15
    q_texts = [r["question"] for r in records]
    a_texts = [r["expected_answer"] for r in records]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    Q_mat = vec.fit_transform(q_texts)
    A_mat = vec.transform(a_texts)
    Q_sim = cosine_similarity(Q_mat)
    A_sim = cosine_similarity(A_mat)

    exact_dups = []
    near_dups = []
    semantic_dups = []
    cross_collisions = []
    ans_overlaps = []
    
    seen = set()
    for i in range(len(records)):
        for j in range(i+1, len(records)):
            qs = float(Q_sim[i][j])
            if qs >= 0.95:
                exact_dups.append((i, j, qs))
            elif qs >= 0.85:
                near_dups.append((i, j, qs))
            elif qs >= 0.70:
                semantic_dups.append((i, j, qs))
                
            a_s = float(A_sim[i][j])
            if a_s >= 0.85:
                ans_overlaps.append((i, j, a_s))
                
            if qs >= 0.65 and records[i].get("primary_role") != records[j].get("primary_role"):
                cross_collisions.append({
                    "q1": records[i]["question"][:100],
                    "role1": records[i].get("primary_role"),
                    "q2": records[j]["question"][:100],
                    "role2": records[j].get("primary_role"),
                    "similarity": round(qs, 3)
                })

    leak_re = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|prompt instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)
    
    leaks = []
    for r in records:
        if leak_re.search(r["question"] + " " + r["expected_answer"]):
            leaks.append(r["id"])

    # Priority Plan
    plan = {}
    for role in [
        "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
        "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
        "Machine Learning Engineer", "Full Stack Developer"
    ]:
        cnt = role_counts.get(role, 0)
        remaining = max(0, 500 - cnt)
        skills = role_skill.get(role, {})
        topics = role_topic.get(role, {})
        techs = role_tech.get(role, {})
        
        sorted_skills = sorted(skills.items(), key=lambda x: x[1])
        sorted_topics = sorted(topics.items(), key=lambda x: x[1])
        
        plan[role] = {
            "current_count": cnt,
            "remaining_to_500": remaining,
            "top_covered_skills": dict(sorted(skills.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_skill_gaps_to_target": [k for k,v in sorted_skills[:10]],
            "top_topic_gaps": [k for k,v in sorted_topics[:10]],
            "recommended_next_batch": "Target top gaps if remaining > 0, otherwise explore advanced secondary areas"
        }

    with open(os.path.join(REPORTS_DIR, "phase4d_generation_priority_plan_v2.json"), "w") as f:
        json.dump(plan, f, indent=2)

    master = {
        "dataset_integrity": {
            "total_records": n_total,
            "unique_ids": unique_ids,
            "unique_questions_normalized": unique_questions,
            "missing_fields": dict(missing_fields),
            "anomalies": anomalies
        },
        "role_counts": dict(role_counts),
        "difficulty_distribution": {
            "counts": dict(diff_total),
            "percentages": {k: round(v*100/n_total, 1) for k,v in diff_total.items()}
        },
        "openings_top_30": openings.most_common(30),
        "duplications": {
            "exact_duplicate_pairs": len(exact_dups),
            "near_duplicate_pairs": len(near_dups),
            "semantic_duplicate_pairs": len(semantic_dups),
            "cross_role_collisions_gt_0.65": cross_collisions[:20],
            "answer_overlaps_gt_0.85": len(ans_overlaps)
        },
        "prompt_leakage": leaks
    }

    with open(os.path.join(REPORTS_DIR, "phase4d_master_coverage_audit_v2.json"), "w") as f:
        json.dump(master, f, indent=2)

    md = f"""# Phase 4D Master Coverage & Quality Audit V2

## Dataset Integrity
- **Total Records Expected**: 1592
- **Total Records Found**: {n_total}
- **Unique Questions**: {unique_questions}
- **Missing Fields**: {dict(missing_fields)}

## Role Coverage
"""
    for role, cnt in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
        md += f"- **{role}**: {cnt} (Remaining: {max(0, 500 - cnt)})\n"

    md += f"""
## Difficulty Distribution (Global)
- Easy: {diff_total.get('easy', 0)} ({round(diff_total.get('easy', 0)*100/n_total, 1)}%)
- Medium: {diff_total.get('medium', 0)} ({round(diff_total.get('medium', 0)*100/n_total, 1)}%)
- Hard: {diff_total.get('hard', 0)} ({round(diff_total.get('hard', 0)*100/n_total, 1)}%)

## Duplication & Quality
- **Exact Duplicates (>=0.95)**: {len(exact_dups)}
- **Near Duplicates (>=0.85)**: {len(near_dups)}
- **Semantic Duplicates (>=0.70)**: {len(semantic_dups)}
- **Cross-Role Collisions**: {len(cross_collisions)}
- **Answer Overlaps (>=0.85)**: {len(ans_overlaps)}
- **Prompt Leakage Detected**: {len(leaks)}

## Priority Plan Summary
"""
    for role, data in plan.items():
        md += f"\n### {role}\n"
        md += f"- Current: {data['current_count']} | Remaining: {data['remaining_to_500']}\n"
        md += f"- Top Gaps to Target: {data['top_skill_gaps_to_target'][:3]}\n"

    md += """
## Role Balance Recommendation
Given that all canonical roles are sitting at exactly 150 questions (except DevOps at 195 and Backend at 197), future generation should proceed in an even round-robin approach. Every role needs ~350 more questions to hit the 500 minimum. 

No role has achieved saturation to the point of justifying halting generation for it, and no role is lagging so far behind to justify an exclusive sprint. We recommend continuing 50-question batches across each role sequentially (e.g. 10-role cycle).
"""

    with open(os.path.join(REPORTS_DIR, "phase4d_master_coverage_audit_v2.md"), "w") as f:
        f.write(md)
        
    print("Audit V2 Complete")

if __name__ == "__main__":
    analyze_dataset()
