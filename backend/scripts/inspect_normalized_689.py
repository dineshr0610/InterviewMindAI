import json
import re
from collections import Counter

with open("reports/question_bank_cleanup_migration.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

normalized_records = manifest.get("NORMALIZE", [])
print(f"Total normalized records in manifest: {len(normalized_records)}")

sources = Counter()
roles = Counter()
topics = Counter()
template_matches = Counter()

questions = []
for r in normalized_records:
    q = r.get("normalized_question", "")
    questions.append(q)
    meta = r.get("metadata", {})
    sources[meta.get("source", "Unknown")] += 1
    roles[meta.get("role", "Unknown")] += 1
    topics[meta.get("topic", "Unknown")] += 1
    
    if "primary trade-offs when choosing this approach over standard alternatives" in q:
        template_matches["synthetic_tradeoffs_template"] += 1
    elif re.match(r"^Explain how [^.]+ operates in the context of", q):
        template_matches["explain_how_operates"] += 1
    elif "Write a " in q:
        template_matches["write_a"] += 1
    else:
        template_matches["other"] += 1

print("\n--- SOURCES OF 689 NORMALIZED QUESTIONS ---")
for s, c in sources.most_common():
    print(f"  {c:4d} : {s}")

print("\n--- ROLES OF 689 NORMALIZED QUESTIONS ---")
for ro, c in roles.most_common():
    print(f"  {c:4d} : {ro}")

print("\n--- TEMPLATE MATCHES IN 689 NORMALIZED QUESTIONS ---")
for t, c in template_matches.items():
    print(f"  {c:4d} : {t}")

print("\n--- SAMPLE NORMALIZED QUESTIONS (first 10) ---")
for i, q in enumerate(questions[:10], 1):
    print(f"{i}. {q}\n")
