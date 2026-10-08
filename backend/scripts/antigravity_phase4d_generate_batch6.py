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

from antigravity_phase4d_generate_batch6_data import Q, BUCKETS, ROLE  # noqa: E402
from phase4d_diversity_audit import fetch_all_supabase, normalize_text  # noqa: E402

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

VALID_INTENTS = {"fundamentals", "explain", "implement", "tradeoff", "debug", "scenario", "compare",
                 "architecture", "optimize", "diagnose"}
LEAK = re.compile(r"(expected answer|rubric|strong indicator|weak indicator|as an ai|bucket|batch \d|"
                  r"gap plan|here is the question|\bprompt\b)", re.I)


def existing_supabase():
    out = []
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
        out.append((q, a))
    return out


def opening(q, n=3):
    return " ".join(normalize_text(q).split()[:n])


def main():
    prior = []
    with open(OUT, encoding="utf-8") as f:
        prior = [json.loads(l) for l in f if l.strip()]
    sup = existing_supabase()
    staged_q = [q for q, _ in sup] + [p["question"] for p in prior]
    staged_a = [a for _, a in sup] + [p["expected_answer"] for p in prior]
    before = len(staged_q)
    print("staged before:", before, "(supabase", len(sup), "+ generated", len(prior), ")")

    cands = []
    for b, intent, diff, qt, sec, q, a, strong, weak in Q:
        skill, tech, topic, cat, roles = BUCKETS[b]
        cands.append({"primary_role": ROLE, "applicable_roles": roles, "primary_skill": skill,
                      "secondary_skills": sec, "technology": tech, "topic": topic, "category": cat,
                      "intent": intent, "difficulty": diff, "question_type": qt, "question": q,
                      "expected_answer": a, "evaluation_rubric": {"strong_indicators": strong, "weak_indicators": weak}})

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit(staged_q + staged_a + [c["question"] for c in cands] + [c["expected_answer"] for c in cands])
    SQ, SA = vec.transform(staged_q), vec.transform(staged_a)
    seen_norm = {normalize_text(q) for q in staged_q}

    rej = Counter()
    details = []
    accepted = []
    stats = {"exact": 0, "near": 0, "semantic": 0, "answer_overlap": 0, "leak": 0, "technical": 0, "taxonomy": 0}
    near_pairs, ans_pairs = [], []
    for c in cands:
        nq = normalize_text(c["question"])
        reason = None
        if nq in seen_norm:
            reason = "exact_duplicate"; stats["exact"] += 1
        else:
            cq = vec.transform([c["question"]]); ca = vec.transform([c["expected_answer"]])
            qs = cosine_similarity(cq, SQ)[0]; as_ = cosine_similarity(ca, SA)[0]
            ans_c = cosine_similarity(ca, SQ)[0]
            qi, ai = int(qs.argmax()), int(as_.argmax())
            comp = cosine_similarity(vec.transform([c["question"] + " " + c["expected_answer"]]),
                                     vec.transform([x + " " + y for x, y in zip(staged_q, staged_a)]))[0]
            if qs[qi] >= 0.80:
                reason = "near_duplicate"; stats["near"] += 1
                near_pairs.append((c["question"], staged_q[qi], round(float(qs[qi]), 3)))
            elif comp.max() >= 0.60:
                reason = "semantic_competency_duplicate"; stats["semantic"] += 1
            elif as_[ai] >= 0.70:
                reason = "expected_answer_overlap"; stats["answer_overlap"] += 1
            details.append((round(float(qs[qi]), 3), round(float(as_[ai]), 3), round(float(comp.max()), 3)))
            if as_[ai] >= 0.5:
                ans_pairs.append((c["question"][:70], round(float(as_[ai]), 3)))
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

    # intra-batch near dup check
    bq = [c["question"] for c in accepted]
    M = cosine_similarity(vec.transform(bq))
    intra = [(i, j, round(float(M[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if M[i][j] >= 0.6]

    for c in accepted:
        c.update({"id": str(uuid.uuid4()), "source": "Antigravity_Internal_Knowledge", "source_url": None,
                  "source_id": None, "provenance_type": "researched_generated", "dataset_version": "v2",
                  "status": "active"})
    with open(OUT, "a", encoding="utf-8") as f:
        for c in accepted:
            f.write(json.dumps(c) + "\n")

    allgen = prior + accepted
    all_openings = Counter(opening(q) for q in staged_q + bq)
    new_openings = Counter(opening(q) for q in bq)
    gen_diff = Counter(g["difficulty"] for g in allgen)
    tot = len(allgen)
    d = lambda k: dict(Counter(c[k] for c in accepted))
    prev_remaining = 3461
    plan_left = {}
    for b, (skill, tech, topic, *_r) in BUCKETS.items():
        n = sum(1 for c in accepted if c["topic"] == topic)
        plan_left[f"{skill} | {topic}"] = {"generated_now": n}
    report = {
        "total_staged_before_batch6": before,
        "attempted": len(cands), "accepted": len(accepted), "rejected": sum(rej.values()),
        "rejection_reasons": dict(rej),
        "exact_duplicates": stats["exact"], "near_duplicates": stats["near"],
        "semantic_competency_duplicates": stats["semantic"],
        "expected_answer_overlap_rejections": stats["answer_overlap"],
        "answer_overlap_flags_ge_0.5": ans_pairs,
        "intra_batch_pairs_ge_0.6": intra,
        "max_similarity_vs_staging": {"question": max(x[0] for x in details), "answer": max(x[1] for x in details),
                                      "question+answer": max(x[2] for x in details)},
        "prompt_leakage": stats["leak"], "technical_rejections": 0, "taxonomy_rejections": stats["taxonomy"],
        "top20_openings_new_batch": new_openings.most_common(20),
        "top20_openings_entire_staging": all_openings.most_common(20),
        "top_opening_share_new_batch": round(new_openings.most_common(1)[0][1] / len(bq), 3),
        "distinct_openings_new_batch": len(new_openings),
        "role_distribution": d("primary_role"), "skill_distribution": d("primary_skill"),
        "technology_distribution": d("technology"), "topic_distribution": d("topic"),
        "intent_distribution": d("intent"), "difficulty_distribution": d("difficulty"),
        "question_type_distribution": d("question_type"),
        "bucket_progress": plan_left,
        "cumulative_generated_production": tot,
        "cumulative_staging_total": before + len(accepted),
        "cumulative_generated_by_role": dict(Counter(g["primary_role"] for g in allgen)),
        "cumulative_generated_by_difficulty": dict(gen_diff),
        "cumulative_generated_difficulty_pct": {k: round(100 * v / tot, 1) for k, v in gen_diff.items()},
        "cumulative_generated_by_intent": dict(Counter(g["intent"] for g in allgen)),
        "remaining_gap_count": prev_remaining - len(accepted),
        "supabase_modifications": 0, "embeddings": 0, "gemini_api_calls": 0,
    }
    with open(os.path.join(REPORTS_DIR, "phase4d_quality_report_batch6.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
