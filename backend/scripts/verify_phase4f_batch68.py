import hashlib
import json
import os
import re
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

with open(OUT, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

records = [json.loads(line) for line in lines]
print(f"Total records in corpus: {len(records)}")

batch68_records = records[-100:]
print(f"Batch 68 records: {len(batch68_records)}")

# Role counts
role_counter = Counter(r.get("primary_role") or r.get("role") for r in records)
print("Role counts across entire corpus:")
for role, cnt in role_counter.most_common():
    print(f"  {role}: {cnt}")

# Difficulty distribution in Batch 68
diff_counter = Counter(r["difficulty"] for r in batch68_records)
print("\nBatch 68 Difficulty distribution:")
for diff, cnt in diff_counter.items():
    print(f"  {diff}: {cnt} ({cnt/len(batch68_records)*100:.1f}%)")

# Intent distribution in Batch 68
intent_counter = Counter(r["intent"] for r in batch68_records)
print("\nBatch 68 Intent distribution:")
for intent, cnt in intent_counter.items():
    print(f"  {intent}: {cnt}")

# Technologies in Batch 68
tech_counter = Counter(r["technology"] for r in batch68_records)
print(f"\nBatch 68 Technologies ({len(tech_counter)} unique):")
for tech, cnt in tech_counter.most_common():
    print(f"  {tech}: {cnt}")

# Primary skills in Batch 68
skill_counter = Counter(r.get("primary_skill") or r.get("skill") for r in batch68_records)
print(f"\nBatch 68 Primary Skills ({len(skill_counter)} unique):")
for skill, cnt in skill_counter.most_common():
    print(f"  {skill}: {cnt}")

# Topics in Batch 68
topic_counter = Counter(r["topic"] for r in batch68_records)
print(f"\nBatch 68 Topics ({len(topic_counter)} unique):")

# Duplicate check within batch and corpus
questions = [r["question"].strip().lower() for r in records]
q_counter = Counter(questions)
dupes = [q for q, c in q_counter.items() if c > 1]
print(f"\nExact duplicate questions in full corpus: {len(dupes)}")

# Leak check
leaks = []
for idx, r in enumerate(batch68_records):
    q_txt = r["question"]
    a_txt = r.get("ideal_answer") or r.get("expected_answer") or ""
    if LEAK.search(q_txt) or LEAK.search(a_txt):
        leaks.append((idx, q_txt))
print(f"Prompt leaks detected in Batch 68: {len(leaks)}")

# SHA256
sha256 = hashlib.sha256()
with open(OUT, "rb") as f:
    while chunk := f.read(8192):
        sha256.update(chunk)
corpus_hash = sha256.hexdigest()
print(f"\nFinal Corpus SHA256: {corpus_hash}")
