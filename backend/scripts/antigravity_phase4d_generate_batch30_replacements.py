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
from antigravity_phase4d_generate_batch30_replacements_data import Q, BUCKET_KEYS, ROLE  # noqa: E402

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


def main():
    with open(OUT, encoding="utf-8") as f:
        prior = [json.loads(l) for l in f if l.strip()]
    sup = existing_supabase()
    staged_q = [q for q, _ in sup] + [p["question"] for p in prior]
    staged_a = [a for _, a in sup] + [p["expected_answer"] for p in prior]

    cands = []
    for b, intent, diff, qt, sec, q, a, strong, weak in Q:
        skill, topic, tech, roles = BUCKET_KEYS[b]
        cands.append({"primary_role": ROLE, "applicable_roles": roles, "primary_skill": skill,
                      "secondary_skills": sec, "technology": tech, "topic": topic,
                      "category": "Artificial Intelligence", "intent": intent, "difficulty": diff, "question_type": qt,
                      "question": q, "expected_answer": a,
                      "evaluation_rubric": {"strong_indicators": strong, "weak_indicators": weak}})

    corpus = staged_q + staged_a + [c["question"] for c in cands] + [c["expected_answer"] for c in cands]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit(corpus)
    SQ, SA = vec.transform(staged_q), vec.transform(staged_a)
    SC = vec.transform([x + " " + y for x, y in zip(staged_q, staged_a)])
    seen_norm = {normalize_text(q) for q in staged_q}

    accepted = []
    for c in cands:
        nq = normalize_text(c["question"])
        if nq in seen_norm:
            continue
        qs = cosine_similarity(vec.transform([c["question"]]), SQ)[0]
        comp = cosine_similarity(vec.transform([c["question"] + " " + c["expected_answer"]]), SC)[0]
        if qs.max() >= 0.80 or comp.max() >= 0.60:
            continue
        if LEAK.search(c["question"] + " " + c["expected_answer"]):
            continue
        seen_norm.add(nq)
        accepted.append(c)

    for c in accepted:
        c.update({"id": str(uuid.uuid4()), "source": "Antigravity_Internal_Knowledge", "source_url": None,
                  "source_id": None, "provenance_type": "researched_generated", "dataset_version": "v2",
                  "status": "active"})
    n_before = len(prior)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write("".join(json.dumps(c) + "\n" for c in accepted))
        
    print(f"Attempted: {len(cands)}, Accepted: {len(accepted)}")
    print(f"Total lines now: {n_before + len(accepted)}")

if __name__ == "__main__":
    main()
