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
from antigravity_phase4d_generate_batch26_supplemental_data import Q, BUCKET_KEYS, ROLE  # noqa: E402

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
PREV_REMAINING = 350
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
    targets = {"easy": 30, "medium": 45, "hard": 25}
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

    # read previous report
    with open(os.path.join(REPORTS_DIR, "phase4d_batch26_report.json"), "r") as f:
        prev_report = json.load(f)

    # combine stats
    prev_report["attempted"] += len(cands)
    prev_report["accepted"] += len(accepted)
    prev_report["records_appended"] += len(accepted)
    prev_report["final_file_line_count"] = len(lines)
    prev_report["cumulative_generated_production"] = tot
    prev_report["remaining_new_questions_to_minimum_500_for_each_role"]["Database Developer"] = max(0, 500 - sum(1 for g in allgen if g["primary_role"] == ROLE))

    with open(os.path.join(REPORTS_DIR, "phase4d_batch26_report.json"), "w") as f:
        json.dump(prev_report, f, indent=2)

    with open(os.path.join(REPORTS_DIR, "phase4d_batch26_report.md"), "w") as f:
        f.write("# Phase 4D - Batch 26 Report\n\n")
        f.write(f"- **Attempted**: {prev_report['attempted']}\n")
        f.write(f"- **Accepted**: {prev_report['accepted']}\n")
        f.write(f"- **Rejected**: {prev_report['rejected']} (Reasons: {prev_report['rejection_reasons']})\n")
        f.write(f"- **Difficulty Distribution**: {prev_report['difficulty_distribution']}\n")
        f.write(f"- **Intent Distribution**: {prev_report['intent_distribution']}\n")
        f.write(f"- **Cumulative NEW Generated Count**: {prev_report['cumulative_generated_production']}\n")
        f.write(f"- **Database Developer Remaining**: {prev_report['remaining_new_questions_to_minimum_500_for_each_role']['Database Developer']}\n")

    print(f"Appended {len(accepted)} questions. Total DB Developer: {sum(1 for g in allgen if g['primary_role'] == ROLE)}")

if __name__ == "__main__":
    main()
