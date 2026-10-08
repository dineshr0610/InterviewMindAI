import json
from collections import Counter, defaultdict
import re

with open("reports/deep_metadata_audit.json", "r", encoding="utf-8") as f:
    d = json.load(f)

topics = d["topic_distribution"]
categories = d["category_distribution"]
roles = d["role_distribution"]
languages = d["languages_distribution"]

print(f"Total topics: {len(topics)}")

# Group by lowercase
lower_to_orig = defaultdict(list)
for t, cnt in topics.items():
    lower_to_orig[t.lower().strip()].append((t, cnt))

print(f"Case-insensitive distinct topics: {len(lower_to_orig)}")

# Identify spelling variants or near duplicates
similar_pairs = []
topic_keys = list(topics.keys())
for i in range(len(topic_keys)):
    for j in range(i + 1, len(topic_keys)):
        t1, t2 = topic_keys[i], topic_keys[j]
        # check token overlap or substring
        words1 = set(re.findall(r"\w+", t1.lower()))
        words2 = set(re.findall(r"\w+", t2.lower()))
        overlap = len(words1 & words2)
        if overlap >= 2 and (len(words1) <= 3 or len(words2) <= 3):
            similar_pairs.append((t1, t2, overlap))

print(f"\nPotential overlapping/duplicate topic concepts ({len(similar_pairs)}):")
for t1, t2, ov in similar_pairs[:30]:
    print(f"  - '{t1}' ({topics[t1]}) <--> '{t2}' ({topics[t2]})")

# Analyze broadness vs narrowness
# E.g. 'Python Algorithms & Data Structures' (2272 records!) vs 'CI/CD Pipelines' (5 records!)
sorted_by_freq = sorted(topics.items(), key=lambda x: x[1], reverse=True)
print("\nTop 15 most frequent topics (Overly broad?):")
for t, cnt in sorted_by_freq[:15]:
    print(f"  {cnt:4d} : {t}")

print("\nBottom 15 least frequent topics (Overly narrow/tail?):")
for t, cnt in sorted_by_freq[-15:]:
    print(f"  {cnt:4d} : {t}")
