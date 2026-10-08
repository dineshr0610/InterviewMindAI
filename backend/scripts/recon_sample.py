"""LOCAL ONLY: print structural samples per source from the snapshot."""
import json
import os
import re
import sys
from collections import Counter, defaultdict

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(BACKEND, "reports", "_scratch_snapshot.json"), encoding="utf-8"))


def src_key(meta):
    s = (meta or {}).get("source") or "NONE"
    if "codealpaca" in s: return "CodeAlpaca"
    if "InterviewMind" in s: return "Curated-v1"
    if "javascript-interview" in s: return "JavaScript"
    if "reactjs-interview" in s: return "React"
    if "system-design-primer" in s: return "SystemDesign"
    if "/aws/" in s: return "DevOps-AWS"
    if "/kubernetes/" in s: return "DevOps-K8s"
    if "/linux/" in s: return "DevOps-Linux"
    if "/git/" in s: return "DevOps-Git"
    if "/cicd/" in s: return "DevOps-CICD"
    return "OTHER:" + s[:60]


by = defaultdict(list)
for r in rows:
    by[src_key(r["metadata"])].append(r)

print({k: len(v) for k, v in by.items()})
which = sys.argv[1:] or list(by)
n = int(os.environ.get("N", "2"))
for k in which:
    print("=" * 100)
    print("SOURCE", k, len(by[k]))
    for r in by[k][:n]:
        print("-" * 60)
        print("META:", json.dumps(r["metadata"], ensure_ascii=False)[:400])
        print(r["content"][:1400])
