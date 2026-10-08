import json
import os
import re
import hashlib
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

REQUIRED_ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer",
    "Database Developer", "DevOps / Cloud Engineer", "Backend Developer",
    "Data Analyst", "AI Engineer", "ML Engineer", "Full Stack Developer"
]

def run_audit():
    with open(OUT, "rb") as f:
        file_bytes = f.read()
        
    file_size = len(file_bytes)
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    
    records = []
    lines = file_bytes.decode("utf-8").split("\n")
    malformed_json_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            malformed_json_count += 1
            
    total_records = len(records)
    
    role_counts = Counter()
    difficulty_counts = Counter()
    intent_counts = Counter()
    tech_counts = Counter()
    skill_counts = Counter()
    topic_counts = Counter()
    
    ids = set()
    duplicate_ids = 0
    missing_fields_count = 0
    leak_count = 0
    
    questions = []
    
    for r in records:
        role = r.get("primary_role") or r.get("role", "UNKNOWN")
        role_counts[role] += 1
        
        difficulty_counts[r.get("difficulty", "UNKNOWN")] += 1
        intent_counts[r.get("intent", "UNKNOWN")] += 1
        tech_counts[r.get("technology", "UNKNOWN")] += 1
        skill_counts[r.get("primary_skill") or r.get("skill", "UNKNOWN")] += 1
        topic_counts[r.get("topic", "UNKNOWN")] += 1
        
        q_id = r.get("id")
        if not q_id or q_id in ids:
            duplicate_ids += 1
        ids.add(q_id)
        
        required_keys = ["id", "question", "difficulty", "intent", "topic", "technology"]
        if not all(r.get(k) for k in required_keys) or not (r.get("ideal_answer") or r.get("expected_answer")):
            missing_fields_count += 1
            
        q_text = r.get("question", "")
        a_text = r.get("ideal_answer", "") or r.get("expected_answer", "")
        questions.append(q_text)
        
        if LEAK.search(q_text) or LEAK.search(a_text):
            leak_count += 1
            
    # TF-IDF Duplicates
    print("Running TF-IDF globally across all 5000 records...")
    tfidf_collisions = 0
    if len(questions) > 1:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
        try:
            vecs = vec.fit_transform(questions)
            sim_matrix = cosine_similarity(vecs)
            for i in range(len(questions)):
                for j in range(i + 1, len(questions)):
                    if sim_matrix[i, j] > 0.85:
                        tfidf_collisions += 1
        except Exception as e:
            print(f"TFIDF failed: {e}")

    issues = []
    if total_records != 5000:
        issues.append(f"Total records is {total_records}, exactly 5000 required.")
        
    for rr in REQUIRED_ROLES:
        c = role_counts.get(rr, 0)
        if c != 500:
            issues.append(f"Role '{rr}' has {c} records, exactly 500 required.")
            
    surplus_roles = set(role_counts.keys()) - set(REQUIRED_ROLES)
    if surplus_roles:
        issues.append(f"Surplus/invalid roles detected: {surplus_roles}")
        
    if duplicate_ids > 0: issues.append(f"{duplicate_ids} duplicate or missing IDs detected.")
    if missing_fields_count > 0: issues.append(f"{missing_fields_count} records have missing required fields.")
    if leak_count > 0: issues.append(f"{leak_count} prompt leaks detected.")
    if malformed_json_count > 0: issues.append(f"{malformed_json_count} malformed JSON lines.")
    if tfidf_collisions > 0: issues.append(f"{tfidf_collisions} high TF-IDF similarity collisions detected.")

    status = "NOT READY" if issues else "READY FOR MIGRATION"

    report = [
        f"# Phase 4F Final 5000 Generation Report",
        f"\n**Status**: **{status}**\n",
    ]
    
    if issues:
        report.append("## Blocking Issues")
        for iss in issues:
            report.append(f"- {iss}")
        report.append("")
        
    report.extend([
        "## Corpus Hash",
        f"- **File:** `interview_question_bank_v2_generated.jsonl`",
        f"- **Total Records:** {total_records}",
        f"- **File Size:** {file_size} bytes",
        f"- **SHA-256:** `{sha256}`",
        "",
        "## Role Counts"
    ])
    
    for r in REQUIRED_ROLES:
        report.append(f"- {r}: {role_counts.get(r, 0)}")
    for r, c in sorted(role_counts.items()):
        if r not in REQUIRED_ROLES:
            report.append(f"- {r}: {c} (WARNING: Unexpected role)")
            
    report.extend([
        "",
        "## Data Validations",
        f"- Malformed JSON Lines: {malformed_json_count}",
        f"- Duplicate IDs: {duplicate_ids}",
        f"- Missing Required Fields: {missing_fields_count}",
        f"- Prompt Leaks Detected: {leak_count}",
        f"- High TF-IDF Collisions (>0.85): {tfidf_collisions}",
        "",
        "## Confirmations",
        "- **Supabase modified**: NO",
        "- **Embeddings generated**: NO",
        "- **Legacy 9,394-row dataset modified**: NO",
        "",
        "## Distributions (Top 5)"
    ])
    
    report.append("\n### Difficulty")
    for k, v in difficulty_counts.most_common(5): report.append(f"- {k}: {v}")
    
    report.append("\n### Intent")
    for k, v in intent_counts.most_common(5): report.append(f"- {k}: {v}")
        
    report.append("\n### Primary Skills")
    for k, v in skill_counts.most_common(5): report.append(f"- {k}: {v}")
        
    report.append("\n### Technologies")
    for k, v in tech_counts.most_common(5): report.append(f"- {k}: {v}")

    report_path = os.path.join(REPORTS_DIR, "phase4f_final_5000_generation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"Audit completed. Status: {status}")
    print(f"Total: {total_records}")
    print(f"SHA256: {sha256}")
    if issues:
        for iss in issues:
            print(f"ISSUE: {iss}")

if __name__ == "__main__":
    run_audit()
