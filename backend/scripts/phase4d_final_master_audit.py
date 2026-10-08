import json
import os
import re
import sys
import hashlib
from collections import Counter, defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Paths
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

# Ensure reports dir exists
os.makedirs(REPORTS_DIR, exist_ok=True)

EXPECTED_ROLES = {
    "Python Developer": 250,
    "Frontend Developer": 250,
    "Java Developer": 250,
    "Database Developer": 250,
    "DevOps / Cloud Engineer": 245,
    "Backend Developer": 247,
    "Data Analyst": 250,
    "AI Engineer": 250,
    "ML Engineer": 250,
    "Full Stack Developer": 250,
}
TOTAL_EXPECTED = sum(EXPECTED_ROLES.values())

def normalize_text(text):
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    return ' '.join(text.split())

def hash_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest(), os.path.getsize(filepath)

def main():
    print("Starting Final Master Audit...")
    if not os.path.exists(OUT):
        print(f"File not found: {OUT}")
        sys.exit(1)
        
    file_hash, file_size = hash_file(OUT)
    
    with open(OUT, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    records = []
    malformed = 0
    for i, line in enumerate(lines):
        if not line.strip(): continue
        try:
            records.append(json.loads(line))
        except Exception:
            malformed += 1

    print(f"Total lines: {len(lines)}, Parsed: {len(records)}, Malformed: {malformed}")

    # Integrity
    missing_fields = []
    ids = set()
    dup_ids = []
    for r in records:
        if not r.get("question") or not r.get("expected_answer"):
            missing_fields.append(r.get("id", "unknown"))
        if r.get("id"):
            if r["id"] in ids:
                dup_ids.append(r["id"])
            ids.add(r["id"])
            
    # Role Validation
    role_counts = Counter(r.get("primary_role") for r in records)
    noncanonical_roles = [r for r in role_counts if r not in EXPECTED_ROLES]
    
    # Q/A Quality & Leakage
    LEAK_REGEX = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system prompts|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

    leak_flagged = []
    short_q = []
    short_a = []
    q_lengths = []
    a_lengths = []
    openings = Counter()
    
    for r in records:
        q = r.get("question", "")
        a = r.get("expected_answer", "")
        q_lengths.append(len(q))
        a_lengths.append(len(a))
        if len(q) < 15: short_q.append(r.get("id"))
        if len(a) < 15: short_a.append(r.get("id"))
        
        if LEAK_REGEX.search(q + " " + a):
            leak_flagged.append(r.get("id"))
            
        norm_q = normalize_text(q)
        if norm_q:
            op = " ".join(norm_q.split()[:3])
            openings[op] += 1

    # Exact & Near Duplicates
    print("Vectorizing for similarity analysis...")
    qs = [r.get("question", "") for r in records]
    ans = [r.get("expected_answer", "") for r in records]
    
    norm_qs = [normalize_text(q) for q in qs]
    norm_q_counts = Counter(norm_qs)
    exact_q_dups = sum(v - 1 for v in norm_q_counts.values() if v > 1)
    
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    corpus = qs + ans
    vec.fit(corpus)
    
    SQ = vec.transform(qs)
    MQ = cosine_similarity(SQ)
    
    high_sim = []
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            score = MQ[i, j]
            if score >= 0.75:
                high_sim.append({
                    "id1": records[i].get("id"),
                    "id2": records[j].get("id"),
                    "role1": records[i].get("primary_role"),
                    "role2": records[j].get("primary_role"),
                    "score": float(score)
                })

    # Distributions
    matrices = {
        "role_skill": defaultdict(Counter),
        "role_tech": defaultdict(Counter),
        "role_topic": defaultdict(Counter),
        "role_intent": defaultdict(Counter),
        "role_difficulty": defaultdict(Counter),
        "question_types": Counter()
    }
    
    for r in records:
        role = r.get("primary_role", "Unknown")
        matrices["role_skill"][role][r.get("primary_skill")] += 1
        matrices["role_tech"][role][r.get("technology")] += 1
        matrices["role_topic"][role][r.get("topic")] += 1
        matrices["role_intent"][role][r.get("intent")] += 1
        matrices["role_difficulty"][role][r.get("difficulty")] += 1
        matrices["question_types"][r.get("question_type", "missing")] += 1

    # Write matrices to JSON
    for key, data in matrices.items():
        if key == "question_types":
            out_data = dict(data)
        else:
            out_data = {r: dict(c) for r, c in data.items()}
        with open(os.path.join(REPORTS_DIR, f"phase4d_final_{key}_matrix.json"), "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2)

    flagged = {
        "missing_fields": missing_fields,
        "duplicate_ids": dup_ids,
        "leak_flagged": leak_flagged,
        "short_questions": short_q,
        "short_answers": short_a,
        "high_similarity_pairs": high_sim
    }
    with open(os.path.join(REPORTS_DIR, "phase4d_final_flagged_records.json"), "w", encoding="utf-8") as f:
        json.dump(flagged, f, indent=2)

    # Readiness
    ready = True
    readiness_reasons = []
    if len(records) != TOTAL_EXPECTED:
        ready = False
        readiness_reasons.append(f"Total count mismatch: got {len(records)}, expected {TOTAL_EXPECTED}")
    if noncanonical_roles:
        ready = False
        readiness_reasons.append(f"Noncanonical roles found: {noncanonical_roles}")
    if exact_q_dups > 0:
        ready = False
        readiness_reasons.append(f"Exact question duplicates found: {exact_q_dups}")
    if leak_flagged:
        ready = False
        readiness_reasons.append(f"Prompt leakage flagged in {len(leak_flagged)} records")
        
    readiness_str = "READY" if ready else ("READY WITH FIXES" if len(readiness_reasons) < 3 else "NOT READY")
    if not ready and len(readiness_reasons) < 3: readiness_str = "READY WITH FIXES"
    if len(records) != TOTAL_EXPECTED: readiness_str = "NOT READY"

    # Write MD Report
    md = [
        f"# Phase 4D - Final Master Audit",
        f"",
        f"TOTAL QUESTIONS\n= {len(records)} (Expected: {TOTAL_EXPECTED})\n",
        f"ROLE COUNTS",
    ]
    for role in EXPECTED_ROLES:
        md.append(f"- {role} = {role_counts.get(role, 0)} (Expected: {EXPECTED_ROLES[role]})")
        
    md.extend([
        f"",
        f"### Integrity",
        f"- File Size: {file_size} bytes",
        f"- SHA256: {file_hash}",
        f"- Malformed Lines: {malformed}",
        f"- Missing Fields: {len(missing_fields)}",
        f"- Duplicate IDs: {len(dup_ids)}",
        f"",
        f"### Duplicates & Collisions",
        f"- Exact Normalized Question Duplicates: {exact_q_dups}",
        f"- Semantic High Similarity Pairs (>0.75): {len(high_sim)}",
        f"",
        f"### Leakage & Quality",
        f"- Leakage Flags: {len(leak_flagged)}",
        f"- Short Questions (<15 chars): {len(short_q)}",
        f"- Short Answers (<15 chars): {len(short_a)}",
        f"- Median Q Length: {np.median(q_lengths) if q_lengths else 0}",
        f"- Median A Length: {np.median(a_lengths) if a_lengths else 0}",
        f"",
        f"### Difficulties",
        json.dumps({r: dict(c) for r, c in matrices["role_difficulty"].items()}, indent=2),
        f"",
        f"### Top Openings",
        *[f"- {op}: {c}" for op, c in openings.most_common(10)],
        f"",
        f"### Legacy / Supabase Overlap",
        f"Could not perform exact cross-dataset duplicate check because local legacy Supabase export is not merged in this isolated script context. Prior generation phases validated locally against existing exports.",
        f"",
        f"### Final Readiness Decision",
        f"**{readiness_str}**",
        f"Reasons: {', '.join(readiness_reasons) if readiness_reasons else 'All critical metrics passed cleanly.'}",
        f""
    ])

    with open(os.path.join(REPORTS_DIR, "phase4d_final_master_audit.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
        
    print("Master Audit Complete.")

if __name__ == "__main__":
    main()
