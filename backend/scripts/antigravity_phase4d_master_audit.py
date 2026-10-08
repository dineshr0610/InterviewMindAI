import json
import os
import re
import sys
from collections import Counter, defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
IN_FILE = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

EXPECTED_ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
    "Machine Learning Engineer", "Full Stack Developer"
]
TARGET_DIFF = {"easy": 30.0, "medium": 45.0, "hard": 25.0}


def normalize_text(text):
    return re.sub(r'[^a-z0-9\s]', '', text.lower()).strip()


def opening(text, n=4):
    return " ".join(normalize_text(text).split()[:n])


def main():
    if not os.path.exists(IN_FILE):
        print(f"Error: {IN_FILE} not found.")
        return

    records = []
    with open(IN_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    tot = len(records)
    print(f"Loaded {tot} records.")

    # 1. Role Coverage
    role_counts = Counter(r.get("primary_role") for r in records)
    missing_roles = [r for r in EXPECTED_ROLES if r not in role_counts]
    unexpected_roles = [r for r in role_counts if r not in EXPECTED_ROLES]

    # Aggregations
    by_role = defaultdict(list)
    for r in records:
        by_role[r.get("primary_role", "UNKNOWN")].append(r)

    role_skill = defaultdict(Counter)
    role_tech = defaultdict(Counter)
    role_topic = defaultdict(Counter)
    role_intent = defaultdict(Counter)
    role_diff = defaultdict(Counter)
    role_qtype = defaultdict(Counter)
    role_openings = defaultdict(Counter)
    metadata_anomalies = []
    answer_lengths = defaultdict(list)

    leak_pattern = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|generation batch|candidate generation|prompt instructions|do not proceed|awaiting authorization|minimum target|generation pipeline|batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|here is the question|\bprompt text\b)", re.I)
    leak_flags = []

    corpus_q = []
    corpus_a = []
    role_labels = []
    id_labels = []

    for i, r in enumerate(records):
        role = r.get("primary_role")
        role_labels.append(role)
        id_labels.append(r.get("id", f"idx_{i}"))

        q = r.get("question", "")
        a = r.get("expected_answer", "")
        corpus_q.append(q)
        corpus_a.append(a)

        ans_words = len(a.split())
        answer_lengths[role].append(ans_words)
        role_openings[role][opening(q)] += 1

        skill = r.get("primary_skill")
        tech = r.get("technology")
        topic = r.get("topic")
        intent = r.get("intent")
        diff = r.get("difficulty")
        qt = r.get("question_type")

        role_skill[role][skill] += 1
        role_tech[role][tech] += 1
        role_topic[role][topic] += 1
        role_intent[role][intent] += 1
        role_diff[role][diff] += 1
        role_qtype[role][qt] += 1

        # Meta validation
        required_fields = ["question", "expected_answer", "primary_role", "primary_skill", "technology", "topic", "difficulty", "intent", "question_type"]
        missing = [f for f in required_fields if not r.get(f)]
        if missing:
            metadata_anomalies.append({"id": r.get("id"), "issue": "missing_fields", "fields": missing})
        
        if diff not in ("easy", "medium", "hard"):
            metadata_anomalies.append({"id": r.get("id"), "issue": "invalid_difficulty", "value": diff})
        
        if leak_pattern.search(q + " " + a):
            leak_flags.append(r.get("id"))

    # Vectorization for dups and semantic collision
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    corpus_combined = [q + " " + a for q, a in zip(corpus_q, corpus_a)]
    X_comb = vec.fit_transform(corpus_combined)
    sim_matrix = cosine_similarity(X_comb)

    duplicate_groups = []
    cross_role_collisions = defaultdict(list)
    seen_pairs = set()

    for i in range(tot):
        for j in range(i + 1, tot):
            if sim_matrix[i][j] >= 0.70:  # High threshold for true duplicates/competency collision
                pair_key = tuple(sorted([id_labels[i], id_labels[j]]))
                if pair_key in seen_pairs: continue
                seen_pairs.add(pair_key)
                
                r1, r2 = role_labels[i], role_labels[j]
                if r1 == r2:
                    duplicate_groups.append({
                        "role": r1, "score": float(sim_matrix[i][j]),
                        "id1": id_labels[i], "id2": id_labels[j],
                        "q1": corpus_q[i][:100], "q2": corpus_q[j][:100]
                    })
                else:
                    cross_role_collisions[f"{r1} <-> {r2}"].append({
                        "score": float(sim_matrix[i][j]),
                        "q1_role": r1, "q2_role": r2,
                        "q1": corpus_q[i][:100], "q2": corpus_q[j][:100]
                    })

    # Stats preparation
    def pct_dict(c, total):
        return {k: round(100 * v / total, 1) for k, v in c.items()}

    role_stats = {}
    gap_analysis = {}
    for role in EXPECTED_ROLES:
        count = role_counts.get(role, 0)
        if count == 0:
            continue
        
        lens = answer_lengths[role]
        avg_len = sum(lens) / count
        med_len = float(np.median(lens))
        
        diff_pct = pct_dict(role_diff[role], count)
        diff_dev = {k: round(diff_pct.get(k, 0) - TARGET_DIFF[k], 1) for k in TARGET_DIFF}
        
        role_stats[role] = {
            "count": count,
            "skills": {"unique": len(role_skill[role]), "top": role_skill[role].most_common(5)},
            "technologies": {"unique": len(role_tech[role]), "top": role_tech[role].most_common(5)},
            "topics": {"unique": len(role_topic[role]), "top": role_topic[role].most_common(5)},
            "intents": pct_dict(role_intent[role], count),
            "difficulties": diff_pct,
            "difficulty_deviations_from_target": diff_dev,
            "question_types": pct_dict(role_qtype[role], count),
            "top_openings": pct_dict(dict(role_openings[role].most_common(5)), count),
            "answer_lengths_words": {"min": min(lens), "max": max(lens), "avg": round(avg_len, 1), "median": med_len}
        }
        
        # Gap analysis
        skills = role_skill[role]
        strongest = [k for k, v in skills.most_common(3)]
        weakest = [k for k, v in skills.most_common()[-3:]]
        gap_analysis[role] = {"strongest_covered": strongest, "weakest_covered": weakest}

    # Next generation plan
    next_plan = {}
    for role in EXPECTED_ROLES:
        c = role_counts.get(role, 0)
        if c < 500:
            next_plan[role] = {
                "remaining_to_500": 500 - c,
                "recommended_batch_size": 50,
                "prioritize_skills": gap_analysis.get(role, {}).get("weakest_covered", []),
                "avoid_skills": gap_analysis.get(role, {}).get("strongest_covered", []),
            }

    audit_report = {
        "summary": {
            "total_new_questions": tot,
            "roles_present": len(role_counts),
            "missing_roles": missing_roles,
            "unexpected_roles": unexpected_roles,
            "total_duplicates_flagged": len(duplicate_groups),
            "total_cross_role_collisions": sum(len(v) for v in cross_role_collisions.values()),
            "total_metadata_anomalies": len(metadata_anomalies),
            "prompt_leakage_flags": len(leak_flags)
        },
        "role_counts": dict(role_counts),
        "role_statistics": role_stats,
        "duplicate_groups_intra_role": duplicate_groups,
        "cross_role_collisions": dict(cross_role_collisions),
        "metadata_anomalies": metadata_anomalies,
        "prompt_leakage_flags": leak_flags,
        "gap_analysis": gap_analysis,
        "next_generation_plan": next_plan
    }

    with open(os.path.join(REPORTS_DIR, "phase4d_master_coverage_audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    with open(os.path.join(REPORTS_DIR, "phase4d_role_skill_matrix.json"), "w") as f:
        json.dump({r: dict(role_skill[r]) for r in role_skill}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_technology_matrix.json"), "w") as f:
        json.dump({r: dict(role_tech[r]) for r in role_tech}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_difficulty_matrix.json"), "w") as f:
        json.dump({r: dict(role_diff[r]) for r in role_diff}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_role_intent_matrix.json"), "w") as f:
        json.dump({r: dict(role_intent[r]) for r in role_intent}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4d_generation_priority_plan.json"), "w") as f:
        json.dump(next_plan, f, indent=2)

    # Markdown Report
    with open(os.path.join(REPORTS_DIR, "phase4d_master_coverage_audit.md"), "w", encoding="utf-8") as f:
        f.write("# Phase 4D Master Coverage & Quality Audit\n\n")
        f.write(f"**Total NEW Generated Questions:** {tot}\n\n")
        
        f.write("## 1. Role Coverage\n")
        for role, count in role_counts.most_common():
            f.write(f"- **{role}**: {count}\n")
        if missing_roles:
            f.write(f"\n**Missing Roles:** {', '.join(missing_roles)}\n")
        
        f.write("\n## 2. Integrity & Duplication\n")
        f.write(f"- **Metadata Anomalies:** {len(metadata_anomalies)}\n")
        f.write(f"- **Prompt Leakage Flags:** {len(leak_flags)}\n")
        f.write(f"- **Intra-Role High Similarity / Duplicates (>= 0.70):** {len(duplicate_groups)}\n")
        f.write(f"- **Cross-Role Semantic Collisions (>= 0.70):** {sum(len(v) for v in cross_role_collisions.values())}\n")
        
        f.write("\n## 3. Next Generation Plan Summary\n")
        for role, plan in next_plan.items():
            f.write(f"### {role}\n")
            f.write(f"- **Remaining to 500:** {plan['remaining_to_500']}\n")
            f.write(f"- **Recommended Next Batch:** {plan['recommended_batch_size']}\n")
            f.write(f"- **Prioritize:** {', '.join(plan['prioritize_skills'])}\n")
            f.write(f"- **Avoid / Saturated:** {', '.join(plan['avoid_skills'])}\n\n")

    print("Audit complete. Reports saved.")


if __name__ == "__main__":
    main()
