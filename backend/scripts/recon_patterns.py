"""LOCAL ONLY: header/marker pattern statistics per source."""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(BACKEND, "reports", "_scratch_snapshot.json"), encoding="utf-8"))


def src_key(meta):
    s = (meta or {}).get("source") or "NONE"
    for needle, name in [("codealpaca", "CodeAlpaca"), ("InterviewMind", "Curated-v1"), ("javascript-interview", "JavaScript"),
                         ("reactjs-interview", "React"), ("system-design-primer", "SystemDesign"), ("/aws/", "DevOps-AWS"),
                         ("/kubernetes/", "DevOps-K8s"), ("/linux/", "DevOps-Linux"), ("/git/", "DevOps-Git"), ("/cicd/", "DevOps-CICD")]:
        if needle in s:
            return name
    return "NONE"


by = defaultdict(list)
for r in rows:
    by[src_key(r["metadata"])].append(r)

out = {}
for k, rs in by.items():
    hdr = Counter()
    for r in rs:
        first = r["content"].strip().split("\n", 1)[0]
        first = re.sub(r":.*$", ":", first)[:60]
        hdr[first] += 1
    markers = Counter()
    for r in rs:
        c = r["content"]
        for name, pat in [("**Question**:", r"\*\*Question\*\*:"), ("<summary>", r"<summary>"), ("<details>", r"<details>"),
                          ("#### Technical Explanation", r"#### Technical Explanation"), ("**Evaluation Rubric**", r"\*\*Evaluation Rubric\*\*"),
                          ("```", r"```"), ("**Ideal Model Answer", r"\*\*Ideal Model Answer"), ("Back to Top", r"Back to Top"),
                          ("Instruction/Input/Output", r"(?i)\*\*(instruction|input|output)\*\*|### (instruction|input|output)"),
                          ("##Answer", r"## Answer")]:
            if re.search(pat, c):
                markers[name] += 1
    out[k] = {"rows": len(rs), "first_line_patterns": hdr.most_common(12), "markers": dict(markers),
              "char_len_median": sorted(len(r["content"]) for r in rs)[len(rs) // 2],
              "char_len_max": max(len(r["content"]) for r in rs),
              "metadata_keys": Counter(k2 for r in rs for k2 in (r["metadata"] or {})).most_common(),
              "status_inactive": sum(1 for r in rs if (r["metadata"] or {}).get("status") == "inactive"),
              "has_embedding": sum(1 for r in rs if r["has_embedding"])}
with open(os.path.join(BACKEND, "reports", "_scratch_patterns.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print("ok")
