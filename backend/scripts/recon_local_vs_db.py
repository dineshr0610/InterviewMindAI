"""LOCAL ONLY: compare local seed files with the DB snapshot."""
import json, os, re
from collections import Counter
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(BACKEND, "data", "knowledge_base")
db = json.load(open(os.path.join(BACKEND, "reports", "_scratch_snapshot.json"), encoding="utf-8"))
db_contents = set(r["content"] for r in db)
out = {}
for name in ["real_technical_dataset.json", "technical_knowledge_5000.json"]:
    data = json.load(open(os.path.join(KB, name), encoding="utf-8"))
    src = Counter((d.get("metadata") or {}).get("source", "NONE") for d in data)
    in_db = sum(1 for d in data if d["content"] in db_contents)
    out[name] = {"rows": len(data), "in_db_exact_content": in_db, "not_in_db": len(data) - in_db,
                 "by_source": src.most_common(), "keys": list(data[0].keys())}
    notdb = Counter((d.get("metadata") or {}).get("source", "NONE") for d in data if d["content"] not in db_contents)
    out[name]["not_in_db_by_source"] = notdb.most_common()
db_src = Counter((r["metadata"] or {}).get("source", "NONE") for r in db)
out["db_by_source"] = db_src.most_common()
json.dump(out, open(os.path.join(BACKEND, "reports", "_scratch_local_vs_db.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1)[:6000])
