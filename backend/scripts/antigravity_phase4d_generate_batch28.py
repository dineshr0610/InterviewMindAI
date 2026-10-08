import asyncio
import json
import os
import re
import sys
import uuid
from collections import Counter

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from phase4d_diversity_audit import fetch_all_supabase, normalize_text  # noqa: E402
from antigravity_phase4d_generate_batch28_data import Q as Q1, BUCKET_KEYS as BK1, ROLE  # noqa: E402
from antigravity_phase4d_generate_batch28_part2_data import Q as Q2, BUCKET_KEYS as BK2  # noqa: E402
from antigravity_phase4d_generate_batch28_part3_data import Q as Q3, BUCKET_KEYS as BK3  # noqa: E402

Q = Q1 + Q2 + Q3
BUCKET_KEYS = {**BK1, **BK2, **BK3}

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

VALID_INTENTS = {"fundamentals", "explain", "implement", "tradeoff", "debug", "scenario", "compare",
                 "architecture", "optimize", "diagnose"}
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|prompt instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)
PREV_REMAINING = 303
SUP_ROLES = Counter()


def existing_supabase():
    out = []
    global SUP_ROLES
    SUP_ROLES = Counter()
    for r in asyncio.run(fetch_all_supabase()):
        meta = r.get("metadata", {})
        if meta.get("status") == "inactive":
            continue
        c = r.get("content", "")
        if "### Instruction:" in c and "### Output:" in c:
            q = c.split("### Instruction:")[1].split("### Output:")[0].strip()
            if "write a program" in q.lower() or "implement a function" in q.lower():
                continue
            a = c.split("### Output:")[1].strip()
        elif "**Answer:**" in c:
            q = c.split("**Answer:**")[0].replace("### Technical Interview Question", "").replace("**Question:**", "").strip()
            a = c.split("**Answer:**")[1].strip()
        else:
            q, a = meta.get("question", c[:200]), meta.get("expected_answer", "")
        if len(set(re.findall(r"[a-z0-9]+", q.lower()))) < 3:
            continue
        SUP_ROLES[meta.get("role")] += 1
        out.append((q, a))
    return out


def opening(q, n=3):
    return " ".join(normalize_text(q).split()[:n])


def pct(counter, total):
    return {k: [v, round(100 * v / total, 1)] for k, v in counter.items()}


def main():
    with open(OUT, encoding="utf-8") as f:
        prior = [json.loads(l) for l in f if l.strip()]
    sup = existing_supabase()
    staged_q = [q for q, _ in sup] + [p["question"] for p in prior]
    staged_a = [a for _, a in sup] + [p["expected_answer"] for p in prior]
    before = len(staged_q)
    prior_diff = Counter(p["difficulty"] for p in prior)
    print("staged before:", before, "| supabase", len(sup), "| generated", len(prior), dict(prior_diff))

    cands = []
    for b, intent, diff, qt, sec, q, a, strong, weak in Q:
        skill, topic, tech, roles = BUCKET_KEYS[b]
        cands.append({"primary_role": ROLE, "applicable_roles": roles, "primary_skill": skill,
                      "secondary_skills": sec, "technology": tech, "topic": topic,
                      "category": "Backend", "intent": intent, "difficulty": diff, "question_type": qt,
                      "question": q, "expected_answer": a,
                      "evaluation_rubric": {"strong_indicators": strong, "weak_indicators": weak}})

    corpus = staged_q + staged_a + [c["question"] for c in cands] + [c["expected_answer"] for c in cands]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit(corpus)
    SQ, SA = vec.transform(staged_q), vec.transform(staged_a)
    SC = vec.transform([x + " " + y for x, y in zip(staged_q, staged_a)])
    seen_norm = {normalize_text(q) for q in staged_q}

    rej = Counter()
    stats = Counter()
    accepted, details, ans_flags = [], [], []
    for c in cands:
        nq = normalize_text(c["question"])
        reason = None
        if nq in seen_norm:
            reason = "exact_duplicate"; stats["exact"] += 1
        else:
            qs = cosine_similarity(vec.transform([c["question"]]), SQ)[0]
            as_ = cosine_similarity(vec.transform([c["expected_answer"]]), SA)[0]
            comp = cosine_similarity(vec.transform([c["question"] + " " + c["expected_answer"]]), SC)[0]
            details.append((float(qs.max()), float(as_.max()), float(comp.max())))
            if as_.max() >= 0.5:
                ans_flags.append((c["question"][:70], round(float(as_.max()), 3)))
            if qs.max() >= 0.80:
                reason = "near_duplicate"; stats["near"] += 1
            elif comp.max() >= 0.60:
                reason = "semantic_competency_duplicate"; stats["semantic"] += 1
            elif as_.max() >= 0.70:
                reason = "expected_answer_overlap"; stats["answer_overlap"] += 1
        if not reason and LEAK.search(c["question"] + " " + c["expected_answer"]):
            reason = "prompt_leakage"; stats["leak"] += 1
        if not reason and (c["intent"] not in VALID_INTENTS or c["difficulty"] not in ("easy", "medium", "hard")
                           or not c["question"].strip().endswith(("?", ".")) or len(c["expected_answer"]) < 80
                           or len(c["evaluation_rubric"]["strong_indicators"]) < 2):
            reason = "taxonomy_or_metadata"; stats["taxonomy"] += 1
        if reason:
            rej[reason] += 1
            continue
        seen_norm.add(nq)
        accepted.append(c)

    bq = [c["question"] for c in accepted]
    M = cosine_similarity(vec.transform(bq)) if bq else [[0]]
    intra = [(i, j, round(float(M[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if M[i][j] >= 0.6]
    intra_qa = cosine_similarity(vec.transform([c["expected_answer"] for c in accepted])) if bq else [[0]]
    intra_ans = [(i, j, round(float(intra_qa[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if intra_qa[i][j] >= 0.5]

    for c in accepted:
        c.update({"id": str(uuid.uuid4()), "source": "Antigravity_Internal_Knowledge", "source_url": None,
                  "source_id": None, "provenance_type": "researched_generated", "dataset_version": "v2",
                  "status": "active"})
    n_before = len(prior)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write("".join(json.dumps(c) + "\n" for c in accepted))
    with open(OUT, encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    ids = [x["id"] for x in lines]
    assert len(lines) == n_before + len(accepted) and len(set(ids)) == len(ids), "append verification failed"
    nt = [normalize_text(x["question"]) for x in lines]
    assert len(set(nt[n_before:])) == len(accepted)

    allgen = lines
    tot = len(allgen)
    gd = Counter(g["difficulty"] for g in allgen)
    targets = {"easy": 20, "medium": 50, "hard": 30}
    pre_tot = len(prior)
    gap_before = {k: round(100 * prior_diff[k] / pre_tot - targets[k], 1) for k in targets} if pre_tot > 0 else {k: 0 for k in targets}
    gap_after = {k: round(100 * gd[k] / tot - targets[k], 1) for k in targets} if tot > 0 else {k: 0 for k in targets}
    all_open = Counter(opening(q) for q in staged_q + bq)
    new_open = Counter(opening(q) for q in bq)
    d = lambda k: dict(Counter(c[k] for c in accepted))
    plan_prog = {}
    for b, (skill, topic, tech, _r) in BUCKET_KEYS.items():
        n = sum(1 for c in accepted if c["topic"] == topic)
        plan_prog[f"{skill} | {topic}"] = {"generated_now": n}

    report = {
        "role_selected": ROLE,
        "total_staged_before_batch28": before,
        "cumulative_difficulty_before": {k: [prior_diff[k], round(100 * prior_diff[k] / pre_tot, 1)] for k in targets} if pre_tot > 0 else {},
        "attempted": len(cands), "accepted": len(accepted), "rejected": sum(rej.values()),
        "rejection_reasons": dict(rej),
        "exact_duplicates": stats["exact"], "near_duplicates": stats["near"],
        "semantic_competency_duplicates": stats["semantic"],
        "expected_answer_overlap_rejections": stats["answer_overlap"],
        "answer_overlap_flags_ge_0.5_vs_staging": ans_flags,
        "intra_batch_question_pairs_ge_0.6": intra, "intra_batch_answer_pairs_ge_0.5": intra_ans,
        "max_similarity_vs_staging": {"question": round(max(x[0] for x in details), 3) if details else 0,
                                      "answer": round(max(x[1] for x in details), 3) if details else 0,
                                      "question+answer": round(max(x[2] for x in details), 3) if details else 0},
        "prompt_leakage": stats["leak"], "technical_rejections": 0, "taxonomy_rejections": stats["taxonomy"],
        "top20_openings_new_batch": new_open.most_common(20),
        "top20_openings_entire_staging": all_open.most_common(20),
        "top_opening_share_new_batch": round(new_open.most_common(1)[0][1] / len(bq), 3) if bq else 0,
        "distinct_openings_new_batch": len(new_open),
        "role_distribution": d("primary_role"), "skill_distribution": d("primary_skill"),
        "technology_distribution": d("technology"), "topic_distribution": d("topic"),
        "intent_distribution": d("intent"), "difficulty_distribution": d("difficulty"),
        "question_type_distribution": d("question_type"),
        "bucket_progress": plan_prog,
        "cumulative_generated_production": tot,
        "cumulative_staging_total": before + len(accepted),
        "cumulative_generated_by_role": dict(Counter(g["primary_role"] for g in allgen)),
        "cumulative_generated_difficulty": pct(gd, tot),
        "target_gap_pct_points_before": gap_before,
        "target_gap_pct_points_after": gap_after,
        "remaining_new_questions_to_minimum_500_for_each_role": {
            r: max(0, 500 - sum(1 for g in allgen if g["primary_role"] == r))
            for r in ["Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
                      "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
                      "Machine Learning Engineer", "Full Stack Developer"]
        },
        "role_coverage": {
            "A_existing_supabase_by_metadata_role": dict(SUP_ROLES),
            "B_generated_by_role": dict(Counter(g["primary_role"] for g in allgen)),
            "generated_mentioning_role_as_applicable": dict(Counter(r for g in allgen for r in g.get("applicable_roles", []))),
        },
        "applicable_roles_this_batch": dict(Counter(r for c in accepted for r in c["applicable_roles"])),
        "records_appended": len(lines) - n_before, "final_file_line_count": len(lines),
        "supabase_modifications": 0, "embeddings": 0, "gemini_api_calls": 0,
    }
    with open(os.path.join(REPORTS_DIR, "phase4d_batch28_report.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_batch28_report.md"), "w") as f:
        f.write("# Phase 4D - Batch 28 Report\n\n")
        f.write(f"- **Attempted**: {report['attempted']}\n")
        f.write(f"- **Accepted**: {report['accepted']}\n")
        f.write(f"- **Rejected**: {report['rejected']} (Reasons: {report['rejection_reasons']})\n")
        f.write(f"- **Exact Duplicates**: {report['exact_duplicates']}\n")
        f.write(f"- **Near Duplicates**: {report['near_duplicates']}\n")
        f.write(f"- **Semantic Duplicates**: {report['semantic_competency_duplicates']}\n")
        f.write(f"- **Answer Overlap**: {report['expected_answer_overlap_rejections']}\n")
        f.write(f"- **Prompt Leakage**: {report['prompt_leakage']}\n")
        f.write(f"- **Difficulty Distribution**: {report['difficulty_distribution']}\n")
        f.write(f"- **Intent Distribution**: {report['intent_distribution']}\n")
        f.write(f"- **Cumulative NEW Generated Count**: {report['cumulative_generated_production']}\n")
        f.write(f"- **Backend Developer Remaining**: {report['remaining_new_questions_to_minimum_500_for_each_role']['Backend Developer']}\n")

    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
