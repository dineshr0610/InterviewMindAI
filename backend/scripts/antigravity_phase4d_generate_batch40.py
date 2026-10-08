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

from phase4d_diversity_audit import fetch_all_supabase, normalize_text
from antigravity_phase4d_generate_batch40_data import Q as Q1, BUCKET_KEYS as BK1, ROLE
from antigravity_phase4d_generate_batch40_part2_data import Q as Q2, BUCKET_KEYS as BK2
from antigravity_phase4d_generate_batch40_part3_data import Q as Q3, BUCKET_KEYS as BK3

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
            q = meta.get("question", c[:200])
            a = meta.get("expected_answer", "")
        if len(set(re.findall(r"[a-z0-9]+", q.lower()))) < 3:
            continue
        SUP_ROLES[meta.get("role")] += 1
        out.append((q, a))
    return out


def opening(q, n=3):
    return " ".join(normalize_text(q).split()[:n])


def pct(counter, total):
    return {k: [v, round(100 * v / total, 1)] for k, v in counter.items()}


def main(dry_run=False):
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
        cands.append({
            "primary_role": ROLE,
            "applicable_roles": roles,
            "primary_skill": skill,
            "secondary_skills": sec,
            "technology": tech,
            "topic": topic,
            "category": "AI/ML",
            "intent": intent,
            "difficulty": diff,
            "question_type": qt,
            "question": q,
            "expected_answer": a,
            "evaluation_rubric": {"strong_indicators": strong, "weak_indicators": weak}
        })

    corpus = staged_q + staged_a + [c["question"] for c in cands] + [c["expected_answer"] for c in cands]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit(corpus)
    SQ, SA = vec.transform(staged_q), vec.transform(staged_a)
    SC = vec.transform([x + " " + y for x, y in zip(staged_q, staged_a)])
    seen_norm = {normalize_text(q) for q in staged_q}

    rej = Counter()
    stats = Counter()
    accepted, details, ans_flags = [], [], []
    for idx, c in enumerate(cands):
        nq = normalize_text(c["question"])
        reason = None
        if nq in seen_norm:
            reason = "exact_duplicate"
            stats["exact"] += 1
        else:
            qs = cosine_similarity(vec.transform([c["question"]]), SQ)[0]
            as_ = cosine_similarity(vec.transform([c["expected_answer"]]), SA)[0]
            comp = cosine_similarity(vec.transform([c["question"] + " " + c["expected_answer"]]), SC)[0]
            details.append((float(qs.max()), float(as_.max()), float(comp.max())))
            if as_.max() >= 0.5:
                ans_flags.append((c["question"][:70], round(float(as_.max()), 3)))
            if qs.max() >= 0.80:
                reason = "near_duplicate"
                stats["near"] += 1
            elif comp.max() >= 0.60:
                reason = "semantic_competency_duplicate"
                stats["semantic"] += 1
                print(f"[REJECT SEMANTIC] Q{idx+1}: qs={qs.max():.3f}, as={as_.max():.3f}, comp={comp.max():.3f}")
                print(f"  Q: {c['question']}")
                match_idx = comp.argmax()
                print(f"  Matched against: {staged_q[match_idx][:100]} | {staged_a[match_idx][:100]}")
            elif as_.max() >= 0.70:
                reason = "expected_answer_overlap"
                stats["answer_overlap"] += 1
                print(f"[REJECT ANSWER] Q{idx+1}: as={as_.max():.3f}")
        if not reason and LEAK.search(c["question"] + " " + c["expected_answer"]):
            reason = "prompt_leakage"
            stats["leak"] += 1
            print(f"[REJECT LEAK] Q{idx+1}")
        if not reason and (c["intent"] not in VALID_INTENTS or c["difficulty"] not in ("easy", "medium", "hard")
                           or not c["question"].strip().endswith(("?", ".")) or len(c["expected_answer"]) < 80
                           or len(c["evaluation_rubric"]["strong_indicators"]) < 2):
            reason = "taxonomy_or_metadata"
            stats["taxonomy"] += 1
            print(f"[REJECT TAXONOMY] Q{idx+1}")
        if reason:
            rej[reason] += 1
            continue
        seen_norm.add(nq)
        accepted.append(c)

    print(f"Attempted: {len(cands)}, Accepted: {len(accepted)}, Rejected: {sum(rej.values())}, Rejections: {dict(rej)}")

    if dry_run or len(accepted) != 50:
        print(f"Dry run or not exactly 50 accepted ({len(accepted)}). Not appending.")
        return len(accepted)

    bq = [c["question"] for c in accepted]
    M = cosine_similarity(vec.transform(bq)) if bq else [[0]]
    intra = [(i, j, round(float(M[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if M[i][j] >= 0.6]
    intra_qa = cosine_similarity(vec.transform([c["expected_answer"] for c in accepted])) if bq else [[0]]
    intra_ans = [(i, j, round(float(intra_qa[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if intra_qa[i][j] >= 0.5]

    for c in accepted:
        c["id"] = "gen_" + str(uuid.uuid4())
        c["generation_batch"] = "batch_40_ai_engineer"

    with open(OUT, "a", encoding="utf-8") as f:
        for c in accepted:
            f.write(json.dumps(c) + "\n")
    print(f"Successfully appended {len(accepted)} records.")

    final_staging_total = len(prior) + len(accepted)
    role_counts = Counter(p["primary_role"] for p in prior)
    role_counts[ROLE] += len(accepted)

    diff_counts = Counter(c["difficulty"] for c in accepted)
    intent_counts = Counter(c["intent"] for c in accepted)
    skill_counts = Counter(c["primary_skill"] for c in accepted)
    tech_counts = Counter(c["technology"] for c in accepted)
    topic_counts = Counter(c["topic"] for c in accepted)
    openings = Counter(opening(c["question"], 3) for c in accepted)

    # Write report
    report = {
        "batch": "batch_40_ai_engineer",
        "role": ROLE,
        "records_attempted": len(cands),
        "records_accepted": len(accepted),
        "records_rejected": sum(rej.values()),
        "rejection_reasons": dict(rej),
        "max_similarity_scores": {
            "question": round(max((d[0] for d in details), default=0), 3),
            "answer": round(max((d[1] for d in details), default=0), 3),
            "combined": round(max((d[2] for d in details), default=0), 3)
        },
        "intra_batch_overlaps": len(intra),
        "intra_batch_answer_overlaps": len(intra_ans),
        "answer_flags_gt_50": len(ans_flags),
        "staging_metrics": {
            "previous_staging_total": len(prior),
            "final_staging_total": final_staging_total,
            "role_total": role_counts[ROLE],
            "remaining_to_500": max(0, 500 - role_counts[ROLE])
        },
        "distributions": {
            "difficulty": dict(diff_counts),
            "intent": dict(intent_counts),
            "primary_skill": dict(skill_counts),
            "technology": dict(tech_counts),
            "topic": dict(topic_counts),
            "opening_diversity": dict(openings.most_common(10))
        }
    }
    with open(os.path.join(REPORTS_DIR, "phase4d_batch40_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with open(os.path.join(REPORTS_DIR, "phase4d_batch40_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Phase 4D - Batch 40 ({ROLE})\n\n")
        f.write(f"- **Attempted**: {len(cands)}\n")
        f.write(f"- **Accepted**: {len(accepted)}\n")
        f.write(f"- **Rejected**: {sum(rej.values())}\n")
        f.write(f"- **Rejections**: {dict(rej)}\n\n")
        f.write("### Staging Totals\n")
        f.write(f"- **Previous Staging Total**: {len(prior)}\n")
        f.write(f"- **Final Staging Total**: {final_staging_total}\n")
        f.write(f"- **AI Engineer Role Total**: {role_counts[ROLE]}\n")
        f.write(f"- **Remaining to 500 Target**: {report['staging_metrics']['remaining_to_500']}\n\n")
        f.write("### Similarity\n")
        f.write(f"- **Max Question Sim**: {report['max_similarity_scores']['question']}\n")
        f.write(f"- **Max Answer Sim**: {report['max_similarity_scores']['answer']}\n")
        f.write(f"- **Max Combined Sim**: {report['max_similarity_scores']['combined']}\n")
        f.write(f"- **Intra-batch Overlaps**: {len(intra)}\n")
        f.write(f"- **Answer Overlaps (>0.5)**: {len(ans_flags)}\n\n")
        f.write("### Distributions\n")
        f.write(f"- **Difficulty**: {dict(diff_counts)}\n")
        f.write(f"- **Intent**: {dict(intent_counts)}\n")
        f.write(f"- **Primary Skill**: {dict(skill_counts)}\n")
        f.write(f"- **Technology**: {dict(tech_counts)}\n")
        f.write(f"- **Topic**: {dict(topic_counts)}\n\n")
        f.write("### Top Openings\n")
        for op, count in openings.most_common(8):
            f.write(f"- `{op}`: {count}\n")

    return len(accepted)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
