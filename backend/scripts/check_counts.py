import json
from collections import Counter

file_path = "e:/interview/backend/data/interview_question_bank_v2_generated.jsonl"
role_counts = Counter()
total = 0

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            q = json.loads(line)
            role_counts[q.get("primary_role", "UNKNOWN")] += 1
            total += 1
        except json.JSONDecodeError:
            pass

print(f"Total questions: {total}")
print("Role counts:")
for role, count in sorted(role_counts.items()):
    print(f"  {role}: {count}")
