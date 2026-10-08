"""LOCAL ONLY: view SD list rows + role_requirements shape."""
import json, os, re
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(BACKEND, "reports", "_scratch_snapshot.json"), encoding="utf-8"))
o = []
want = ["Additional system design interview questions", "Object-oriented design interview questions with solutions",
        "System design interview questions with solutions", "How to approach a system design interview question",
        "Design Pastebin.com (or Bit.ly)", "Design a web crawler", "Prep for the system design interview"]
for r in rows:
    m = r["metadata"] or {}
    if "system-design" in (m.get("source") or "") and m.get("subtopic") in want:
        o.append("=== " + m["subtopic"] + f" (len {len(r['content'])})")
        o.append(r["content"][:1500]); o.append("")
rr = json.load(open(os.path.join(os.path.dirname(BACKEND), "role_requirements.json"), encoding="utf-8"))
o.append("=== role_requirements top keys: " + str(list(rr.keys())))
roles = rr.get("roles", {})
o.append("roles: " + str(list(roles.keys())))
for k, v in list(roles.items())[:2]:
    o.append(k + " -> " + json.dumps(v, ensure_ascii=False)[:1200])
open(os.path.join(BACKEND, "reports", "_scratch_sd.txt"), "w", encoding="utf-8").write("\n".join(o))
print("ok")
