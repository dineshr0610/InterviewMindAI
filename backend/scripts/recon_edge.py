"""LOCAL ONLY: targeted edge-case viewer."""
import json, os, re, sys
from collections import Counter, defaultdict
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(BACKEND, "reports", "_scratch_snapshot.json"), encoding="utf-8"))
def src(m):
    s = (m or {}).get("source") or ""
    for n, k in [("codealpaca","CA"),("InterviewMind","CUR"),("javascript-interview","JS"),("reactjs-interview","RE"),("system-design","SD"),("/aws/","AWS"),("/kubernetes/","K8S"),("/linux/","LIN"),("/git/","GIT"),("/cicd/","CICD")]:
        if n in s: return k
    return "NONE"
by = defaultdict(list)
for r in rows: by[src(r["metadata"])].append(r)
o = []
def p(*a): o.append(" ".join(str(x) for x in a))

p("### JS rows with '## Answer' (first 2)")
for r in [r for r in by["JS"] if "## Answer" in r["content"]][:2]:
    p(json.dumps(r["metadata"], ensure_ascii=False)[:300]); p(r["content"][:900]); p("-----")
p("### JS rows with <summary> (first 2)")
for r in [r for r in by["JS"] if "<summary>" in r["content"]][:2]:
    p(json.dumps(r["metadata"], ensure_ascii=False)[:300]); p(r["content"][:900]); p("-----")
p("### SD subtopics (all)")
p(" | ".join(r["metadata"]["subtopic"] for r in by["SD"]))
p("### JS subtopics sample non-question-form")
qf = re.compile(r"^(what|how|why|when|which|where|who|explain|describe|can|does|do|is|are|should|list|name|define|compare|difference|give|write|tell|state)\b", re.I)
nq = [r["metadata"]["subtopic"] for r in by["JS"] if not (qf.match(r["metadata"]["subtopic"].strip()) or r["metadata"]["subtopic"].strip().endswith("?"))]
p(len(nq), nq[:60])
p("### RE non-question-form")
nq = [r["metadata"]["subtopic"] for r in by["RE"] if not (qf.match(r["metadata"]["subtopic"].strip()) or r["metadata"]["subtopic"].strip().endswith("?"))]
p(len(nq), nq[:60])
p("### CodeAlpaca samples")
for r in by["CA"][:3]:
    p(json.dumps(r["metadata"], ensure_ascii=False)[:400]); p(r["content"][:700]); p("-----")
p("### CodeAlpaca topic/role/category/difficulty counters")
for key in ["topic","role","category","difficulty"]:
    p(key, Counter(r["metadata"].get(key) for r in by["CA"]).most_common(15))
p("### CodeAlpaca subtopic sample"); p([r["metadata"]["subtopic"] for r in by["CA"][:15]])
p("### CUR sample per first-line type")
seen = set()
for r in by["CUR"]:
    c = r["content"]
    t = "Q" if "**Question**:" in c else "SCEN" if c.startswith("### Production Scenario") else "PIT" if c.startswith("### Pitfalls") else "CODE" if c.startswith("### Code Implementation") else "CORE"
    if t in seen: continue
    seen.add(t); p("TYPE", t, json.dumps(r["metadata"], ensure_ascii=False)[:300]); p(c[:600]); p("-----")
p("### NONE rows"); 
for r in by["NONE"]: p(json.dumps(r["metadata"], ensure_ascii=False)[:200], "|", r["content"][:200].replace("\n"," "))
open(os.path.join(BACKEND, "reports", "_scratch_edge.txt"), "w", encoding="utf-8").write("\n".join(o))
print("ok")
