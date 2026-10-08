"""
LOCAL / READ-ONLY: run all per-source extractors over the snapshot and compute reconstruction statistics.
No DB access, no Gemini, no network.
Outputs (analysis artifacts only):
  reports/question_bank_reconstruction_candidates.json   (extracted, verbatim candidates + verdicts)
  reports/_scratch_analysis.json                          (statistics used to build the final reports)
"""
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recon_lib import *  # noqa

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(BACKEND, "reports")
rows = json.load(open(os.path.join(REP, "_scratch_snapshot.json"), encoding="utf-8"))

# ---------------------------------------------------------------- helpers
def is_active(meta):  # same semantics as match_document_embeddings_filtered
    return (meta or {}).get("status") != "inactive"


def cid(source, row_id, idx):
    return hashlib.sha1(f"{source}|{row_id}|{idx}".encode()).hexdigest()[:16]


LEGACY_DIFF = {"Easy": 1, "Medium": 2, "Hard": 3}


def count_concepts(q):
    bt = set(re.findall(r"`([^`]+)`", q))
    camel = set(re.findall(r"\b[a-z]+[A-Z][A-Za-z]+\b|\b[A-Z][a-z]+[A-Z][A-Za-z]*\b", q))
    return len(bt | camel)


def rubric_level(q, qtype):
    t = q.lower().strip()
    base = {"concept": 1, "true_false": 1, "how_to": 2, "hands_on_task": 2, "compare": 2,
            "scenario": 3, "design_prompt": 3, "code_output_quiz": 2}.get(qtype, 1)
    if qtype == "concept":
        if re.match(r"(what (is|are|does)|define|list|name|who|which|mention|state)\b", t):
            base = 1
        else:
            base = 2
    mods = 0
    if re.search(r"trade-?off|edge case|failure|scal(e|ing|ability)|concurren|race condition|consisten|idempot|"
                 r"memory leak|security|performance|optimi|production|fault|resilien|bottleneck|distributed", t):
        mods += 1
    if count_concepts(q) >= 3 or len(re.findall(r"\band\b|,", t)) >= 3:
        mods += 1
    return min(3, base + (1 if mods >= 1 else 0) + (1 if (mods >= 2 and base == 1) else 0))


def infer_intent(q, qtype):
    t = q.lower()
    if qtype == "design_prompt":
        return "design"
    if qtype == "code_output_quiz":
        return "predict"
    if re.search(r"troubleshoot|debug|\bfix\b|why (is|isn't|doesn't|won't|can't|does not)|not working|\bfails?\b|error", t):
        return "debug"
    if re.search(r"trade-?off|pros and cons|advantages and disadvantages|drawbacks", t):
        return "tradeoff"
    if qtype == "compare":
        return "compare"
    if qtype == "scenario":
        return "scenario"
    if re.search(r"optimi|improve performance|speed up|reduce latency", t):
        return "optimize"
    if qtype in ("how_to", "hands_on_task"):
        return "implement"
    if re.match(r"why\b", t):
        return "reasoning"
    if qtype == "true_false":
        return "fundamentals"
    if re.match(r"(what (is|are)|define|describe|explain|list|name)\b", t):
        return "explain"
    return "unassigned"


def category_hits(q):
    return [c for c, pat in CATEGORY_RULES.items() if re.search(pat, q.lower())]


# ---------------------------------------------------------------- per-source extraction
cands = []                    # verbatim question candidates
row_verdicts = {}            # db row id -> verdict dict
stats = defaultdict(lambda: defaultdict(int))
samples = defaultdict(list)


def add_sample(key, val, n=8):
    if len(samples[key]) < n:
        samples[key].append(val)


by_src = defaultdict(list)
for r in rows:
    by_src[source_of(r["metadata"])].append(r)

# ---- JavaScript / React
for src in ("JavaScript", "React"):
    for r in by_src[src]:
        meta = r["metadata"] or {}
        header, body = split_tiq_row(r["content"])
        ans = clean_answer(body)
        cls = classify_tiq_header(header)
        sub = (meta.get("subtopic") or "")
        stats[src]["header_equals_subtopic" if header == sub else "header_differs_subtopic"] += 1
        stats[src]["rows"] += 1
        stats[src]["row_cls_" + cls] += 1
        verdict = {"source": src, "cls": cls}
        topic_rules = JS_TOPICS if src == "JavaScript" else REACT_TOPICS
        if cls in ("question", "code_output_quiz"):
            q = re.sub(r"^\s*(?:#+\s*)?\d+[\.\)]\s*", "", header.lstrip("# ").strip()) if cls == "code_output_quiz" else header.strip()
            qtype = classify_qtype(q) if cls == "question" else "code_output_quiz"
            reasons = []
            if cls == "question" and qtype == "unknown_form":
                reasons.append("unknown_question_form")
            if len(ans) < 20:
                reasons.append("no_answer_text")
            ctx = bool(CONTEXT_DEP_RE.search(q)) and cls == "question"
            if ctx:
                reasons.append("references_unseen_context")
            if has_mojibake(q):
                reasons.append("mojibake")
            if cls == "code_output_quiz":
                pool = "code_output_quiz"
            elif reasons and ("no_answer_text" in reasons or "unknown_question_form" in reasons):
                pool = "rejected"
            elif ctx:
                pool = "needs_context"
            elif qtype in CONVERSATIONAL_TYPES:
                pool = "conversational"
            elif qtype == "hands_on_task":
                pool = "hands_on_practical"
            elif qtype == "true_false":
                pool = "quiz_true_false"
            else:
                pool = "rejected"
            topics = multi_topics(q, topic_rules)
            cands.append({
                "candidate_id": cid(src, r["id"], 0), "source": src, "source_url": meta.get("source"),
                "source_row_id": r["id"], "role": meta.get("role"), "role_id": meta.get("role_id"),
                "skill": "JavaScript" if src == "JavaScript" else "React",
                "topic": topics[0] if topics else "unassigned", "topic_candidates": topics,
                "question_text": q, "question_raw": header, "question_type": qtype,
                "pool": pool, "reasons": reasons, "answer_text": ans,
                "legacy_difficulty": meta.get("difficulty"), "row_active": is_active(meta),
                "row_has_embedding": r["has_embedding"], "multi_question_row": False,
            })
            verdict["pool"] = pool
        else:
            reason = {"fragment_subheading": "markdown_subheading_promoted_to_question",
                      "fragment_answer_key": "answer_key_fragment_promoted_to_question",
                      "noun_heading": "noun_heading_not_a_question"}[cls]
            verdict["pool"] = "rejected"
            verdict["reason"] = reason
            add_sample(f"{src}_{cls}", header[:100])
        row_verdicts[r["id"]] = verdict

# ---- DevOps
for src in sorted(DEVOPS_SOURCES):
    for r in by_src[src]:
        meta = r["metadata"] or {}
        header, body = split_tiq_row(r["content"])
        section = re.sub(r"^#+\s*", "", header).strip()
        items = extract_devops_items(body)
        stats[src]["rows"] += 1
        if not items:
            kind = "exercise_index_table" if re.search(r"\|\s*Name\s*\|.*Objective", body) or "[Exercise]" in body else "documentation_or_toc"
            stats[src]["rows_without_questions_" + kind] += 1
            row_verdicts[r["id"]] = {"source": src, "pool": "rejected", "reason": kind}
            add_sample(f"{src}_noq_{kind}", header[:80])
            continue
        stats[src]["rows_with_questions"] += 1
        if len(items) > 1:
            stats[src]["multi_question_rows"] += 1
        row_verdicts[r["id"]] = {"source": src, "pool": "multi", "n": len(items)}
        for i, it in enumerate(items):
            qtxt = html_to_text(it["question_raw"])
            ans = html_to_text(it["answer_raw"])
            reasons = []
            if not qtxt:
                reasons.append("empty_summary")
            qtype = classify_qtype(qtxt, raw=it["question_raw"] + "\n" + it["answer_raw"][:200]) if qtxt else "unknown_form"
            if not ans or len(ans) < 3:
                reasons.append("no_answer_text")
            if re.search(r"\bTODO\b|\bFIXME\b", ans):
                reasons.append("answer_has_TODO")
            if not it["closed"]:
                reasons.append("answer_not_closed_possible_truncation")
            if has_mojibake(qtxt):
                reasons.append("mojibake")
            ctx = bool(CONTEXT_DEP_RE.search(qtxt)) if qtxt else False
            if "empty_summary" in reasons or qtype in ("needs_visual", "unknown_form"):
                pool = "rejected"
                if qtype == "needs_visual":
                    reasons.append("requires_image_or_diagram")
                if qtype == "unknown_form":
                    reasons.append("unknown_question_form")
            elif qtype == "true_false":
                pool = "quiz_true_false"
            elif qtype == "hands_on_task":
                pool = "hands_on_practical"
            elif ctx:
                pool = "needs_context"
                reasons.append("references_unseen_context")
            elif qtype in CONVERSATIONAL_TYPES:
                pool = "conversational"
            else:
                pool = "rejected"
            cands.append({
                "candidate_id": cid(src, r["id"], i), "source": src, "source_url": meta.get("source"),
                "source_row_id": r["id"], "role": meta.get("role"), "role_id": meta.get("role_id"),
                "skill": DEVOPS_SKILL[src], "topic": section, "topic_candidates": [section],
                "question_text": qtxt, "question_raw": it["question_raw"], "question_type": qtype,
                "pool": pool, "reasons": reasons, "answer_text": ans,
                "legacy_difficulty": meta.get("difficulty"), "row_active": is_active(meta),
                "row_has_embedding": r["has_embedding"], "multi_question_row": len(items) > 1,
            })

# ---- System Design Primer
sd_standalone_design = 0
for r in by_src["SystemDesign"]:
    meta = r["metadata"] or {}
    header, body = split_tiq_row(r["content"])
    sub = (meta.get("subtopic") or "").strip()
    stats["SystemDesign"]["rows"] += 1
    if sub.lower() in SD_LIST_ROW_SUBTOPICS:
        qs = extract_sd_table_questions(body)
        stats["SystemDesign"]["list_rows"] += 1
        row_verdicts[r["id"]] = {"source": "SystemDesign", "pool": "multi", "n": len(qs)}
        for i, q in enumerate(qs):
            cands.append({
                "candidate_id": cid("SystemDesign", r["id"], i), "source": "SystemDesign", "source_url": meta.get("source"),
                "source_row_id": r["id"], "role": meta.get("role"), "role_id": meta.get("role_id"),
                "skill": "System Design", "topic": "design_case_study", "topic_candidates": ["design_case_study"],
                "question_text": q, "question_raw": q, "question_type": classify_qtype(q),
                "pool": "conversational" if classify_qtype(q) in CONVERSATIONAL_TYPES else "rejected",
                "reasons": [] if classify_qtype(q) in CONVERSATIONAL_TYPES else ["unknown_question_form"],
                "answer_text": "", "legacy_difficulty": meta.get("difficulty"),
                "row_active": is_active(meta), "row_has_embedding": r["has_embedding"], "multi_question_row": True,
                "source_kind": f"markdown_table:{sub}",
            })
    elif re.match(r"(?i)^design\b", sub) and "[View exercise and solution]" in body:
        sd_standalone_design += 1
        stats["SystemDesign"]["standalone_design_rows"] += 1
        q = sub
        cands.append({
            "candidate_id": cid("SystemDesign", r["id"], 0), "source": "SystemDesign", "source_url": meta.get("source"),
            "source_row_id": r["id"], "role": meta.get("role"), "role_id": meta.get("role_id"),
            "skill": "System Design", "topic": "design_case_study", "topic_candidates": ["design_case_study"],
            "question_text": q, "question_raw": header, "question_type": "design_prompt",
            "pool": "conversational", "reasons": [], "answer_text": "", "legacy_difficulty": meta.get("difficulty"),
            "row_active": is_active(meta), "row_has_embedding": r["has_embedding"], "multi_question_row": False,
            "source_kind": "standalone_design_row (solution is an external link)",
        })
        row_verdicts[r["id"]] = {"source": "SystemDesign", "pool": "conversational_single"}
    else:
        row_verdicts[r["id"]] = {"source": "SystemDesign", "pool": "rejected", "reason": "documentation_section"}
        stats["SystemDesign"]["documentation_rows"] += 1

# ---- Dedupe over all non-rejected candidates (report only)
pool_order = {"JavaScript": 0, "React": 1, "DevOps-AWS": 2, "DevOps-K8s": 3, "DevOps-Linux": 4, "DevOps-Git": 5, "DevOps-CICD": 6, "SystemDesign": 7}
live = [c for c in cands if c["pool"] != "rejected"]
live.sort(key=lambda c: (pool_order.get(c["source"], 9), c["source_row_id"], c["candidate_id"]))
exact = defaultdict(list)
for c in live:
    exact[norm_for_dedupe(c["question_text"])].append(c)
dup_groups = [g for g in exact.values() if len(g) > 1]
first_seen = {}
for key, g in exact.items():
    for c in g[1:]:
        c["dup_of"] = g[0]["candidate_id"]
        c["dup_kind"] = "exact_normalized"
exact_dup_records = sum(len(g) for g in dup_groups)
exact_dup_removable = sum(len(g) - 1 for g in dup_groups)
uniq = [g[0] for g in exact.values()]
toks = [(c, tokens(c["question_text"])) for c in uniq]
near_pairs_90, near_pairs_75 = [], []
for i in range(len(toks)):
    ci, ti = toks[i]
    if len(ti) < 3:
        continue
    for j in range(i + 1, len(toks)):
        cj, tj = toks[j]
        if len(tj) < 3:
            continue
        if len(ti & tj) == 0:
            continue
        s = jaccard(ti, tj)
        if s >= 0.9:
            near_pairs_90.append((ci, cj, s))
        elif s >= 0.75:
            near_pairs_75.append((ci, cj, s))
near_removed = set()
for ci, cj, s in near_pairs_90:
    if "dup_of" not in cj:
        cj["dup_of"] = ci["candidate_id"]
        cj["dup_kind"] = f"near_duplicate_jaccard>={0.9}"
        near_removed.add(cj["candidate_id"])
cross_source_dups = sum(1 for g in dup_groups if len({c["source"] for c in g}) > 1)
diff_meta_dups = sum(1 for g in dup_groups if len({c["legacy_difficulty"] for c in g}) > 1)

# ---- Curated
cur = by_src["Curated-v1"]
cur_types = Counter(); cur_active = Counter(); cur_emb = Counter(); cur_mojibake = 0
cur_bad_paren_sub = 0; cur_combo = Counter(); cur_template_q_regex = 0; cur_q_rows = 0; cur_content_groups = defaultdict(list)
cur_role = Counter()
for r in cur:
    t = classify_curated(r["content"])
    cur_types[t] += 1
    meta = r["metadata"] or {}
    if is_active(meta): cur_active[t] += 1
    if r["has_embedding"]: cur_emb[t] += 1
    if has_mojibake(r["content"]): cur_mojibake += 1
    if not balanced_parens(meta.get("subtopic") or ""): cur_bad_paren_sub += 1
    cur_combo[(meta.get("role"), meta.get("topic"), meta.get("subtopic"))] += 1
    cur_content_groups[r["content"].strip()].append(r["id"])
    cur_role[meta.get("role")] += 1
    if t == "template_interview_question":
        cur_q_rows += 1
        m = re.search(r"\*\*Question\*\*:\n(.*?)\n\n\*\*Ideal Model Answer", r["content"], re.S)
        if m and QUESTION_TEMPLATE_RE.match(m.group(1).strip()):
            cur_template_q_regex += 1
cur_dup_groups = [v for v in cur_content_groups.values() if len(v) > 1]
cur_subtopics_clean = sum(1 for (ro, to, st), n in cur_combo.items() if balanced_parens(st or ""))

# ---- CodeAlpaca
ca = by_src["CodeAlpaca"]
ca_cat = Counter(); ca_verb = Counter(); ca_lang = Counter(); ca_role_lang = defaultdict(Counter)
ca_has_input = 0; ca_q_end = 0; ca_active = 0; ca_emb = 0; ca_mismatch = 0; ca_mismatch_base = 0
ca_instr_norm = defaultdict(list); ca_samples = defaultdict(list); ca_rubric_ident = 0
ROLE_LANG_OK = {"Python Developer": {"python"}, "Java Developer": {"java"}, "Frontend Developer": {"javascript", "typescript", "html/css"},
                "Database Developer": {"sql"}, "Data Analyst": {"python", "sql", "r"}, "Machine Learning Engineer": {"python", "r"},
                "AI Engineer": {"python"}, "Full Stack Developer": {"javascript", "typescript", "python", "java", "sql", "html/css"},
                "Backend Developer": {"python", "java", "javascript", "typescript", "go", "c#"}, "DevOps / Cloud Engineer": {"bash", "python"}}
for r in ca:
    meta = r["metadata"] or {}
    p = parse_codealpaca(r["content"])
    cat = classify_ca_instruction(p["instruction"])
    ca_cat[cat] += 1
    ca_verb[first_word(p["instruction"])] += 1
    lang = detect_language(p["instruction"], p["reference_output"])
    ca_lang[lang] += 1
    ca_role_lang[meta.get("role")][lang] += 1
    if p["input_spec"]: ca_has_input += 1
    if p["instruction"].rstrip().endswith("?"): ca_q_end += 1
    if is_active(meta): ca_active += 1
    if r["has_embedding"]: ca_emb += 1
    if lang != "unspecified":
        ca_mismatch_base += 1
        if lang not in ROLE_LANG_OK.get(meta.get("role"), set()):
            ca_mismatch += 1
    ca_instr_norm[norm_for_dedupe(p["instruction"])].append(r["id"])
    if "Handles nominal and boundary test cases" in r["content"]:
        ca_rubric_ident += 1
    if len(ca_samples[cat]) < 4:
        ca_samples[cat].append(p["instruction"][:140])
ca_dups = [v for v in ca_instr_norm.values() if len(v) > 1]

# ---- Exposure of the retrievable (active + embedded) rows
exposure = {}
for src, rs in by_src.items():
    act = [r for r in rs if is_active(r["metadata"])]
    emb = [r for r in act if r["has_embedding"]]
    detail = Counter()
    for r in emb:
        v = row_verdicts.get(r["id"])
        if src in ("JavaScript", "React", "SystemDesign") and v:
            detail[v.get("pool") + (":" + v["reason"] if v.get("reason") else "")] += 1
        elif src == "Curated-v1":
            detail[classify_curated(r["content"])] += 1
        elif src == "CodeAlpaca":
            detail["coding_task"] += 1
    exposure[src] = {"rows": len(rs), "active_status": len(act), "active_and_embedded(retrievable_now)": len(emb), "retrievable_breakdown": dict(detail),
                     "inactive": len(rs) - len(act), "embedded_total": sum(1 for r in rs if r["has_embedding"])}

# ---- Summaries
def pool_counts(filter_fn=lambda c: True):
    return Counter(c["pool"] for c in cands if filter_fn(c))

per_src = {}
for src in ["JavaScript", "React", "DevOps-AWS", "DevOps-K8s", "DevOps-Linux", "DevOps-Git", "DevOps-CICD", "SystemDesign"]:
    cs = [c for c in cands if c["source"] == src]
    per_src[src] = {
        "raw_rows": len(by_src[src]), "candidates_extracted": len(cs), "pools": dict(Counter(c["pool"] for c in cs)),
        "qtypes": dict(Counter(c["question_type"] for c in cs)),
        "multi_question_rows": stats[src].get("multi_question_rows", 0),
        "reject_reasons": dict(Counter(r for c in cs for r in c["reasons"])),
        "non_question_rows": sum(1 for r in by_src[src] if row_verdicts.get(r["id"], {}).get("pool") == "rejected"),
        "row_reject_reasons": dict(Counter(row_verdicts[r["id"]].get("reason") for r in by_src[src] if row_verdicts.get(r["id"], {}).get("pool") == "rejected")),
        "dup_flagged": sum(1 for c in cs if c.get("dup_of")),
        "mojibake": sum(1 for c in cs if "mojibake" in c["reasons"]),
        "row_stats": dict(stats[src]),
    }

conv = [c for c in cands if c["pool"] == "conversational" and not c.get("dup_of")]
conv_all = [c for c in cands if c["pool"] == "conversational"]
# enrich conv with rubric/intent/category
for c in cands:
    if c["pool"] != "rejected":
        c["rubric_level_preview"] = rubric_level(c["question_text"], c["question_type"])
        c["intent_preview"] = infer_intent(c["question_text"], c["question_type"])
        c["category_hits_preview"] = category_hits(c["question_text"])
        ld = LEGACY_DIFF.get(c["legacy_difficulty"] or "", 0)
        c["legacy_vs_rubric"] = "agree" if ld == c["rubric_level_preview"] else "differ"

def dist(items, key):
    return dict(Counter(key(c) for c in items).most_common())

analysis = {
    "totals": {"rows": len(rows), "candidates_all": len(cands), "pool_counts_all": dict(pool_counts()),
               "pool_counts_after_dedupe": dict(Counter(c["pool"] for c in cands if not c.get("dup_of") and c["pool"] != "rejected"))},
    "per_source": per_src,
    "dedupe": {"scope": "all non-rejected candidates (JS, React, DevOps, SD)", "live_candidates": len(live),
               "exact_normalized_groups": len(dup_groups), "exact_dup_records": exact_dup_records, "exact_removable": exact_dup_removable,
               "cross_source_groups": cross_source_dups, "groups_differing_only_in_legacy_difficulty": diff_meta_dups,
               "near_dup_pairs_ge_0.90": len(near_pairs_90), "near_removable_ge_0.90": len(near_removed),
               "related_pairs_0.75_to_0.90": len(near_pairs_75),
               "near_samples": [[a["question_text"][:110], b["question_text"][:110], round(s, 2), a["source"], b["source"]] for a, b, s in near_pairs_90[:12]],
               "related_samples": [[a["question_text"][:110], b["question_text"][:110], round(s, 2), a["source"], b["source"]] for a, b, s in near_pairs_75[:12]],
               "exact_samples": [[g[0]["question_text"][:120], [c["source"] for c in g], [c["legacy_difficulty"] for c in g]] for g in dup_groups[:12]]},
    "conversational_unique": len(conv),
    "conversational_before_dedupe": len(conv_all),
    "conv_by_role": dist(conv, lambda c: c["role"]),
    "conv_by_skill": dist(conv, lambda c: (c["role"], c["skill"])) and {f"{k[0]} | {k[1]}": v for k, v in dist(conv, lambda c: (c["role"], c["skill"])).items()},
    "conv_by_qtype": dist(conv, lambda c: c["question_type"]),
    "conv_by_rubric": dist(conv, lambda c: c["rubric_level_preview"]),
    "conv_by_intent": dist(conv, lambda c: c["intent_preview"]),
    "conv_by_legacy_difficulty": dist(conv, lambda c: c["legacy_difficulty"]),
    "conv_legacy_vs_rubric": dist(conv, lambda c: c["legacy_vs_rubric"]),
    "conv_category_hits": dist(conv, lambda c: len(c["category_hits_preview"])),
    "conv_category_counts": dict(Counter(h for c in conv for h in c["category_hits_preview"]).most_common()),
    "conv_topic_unassigned": sum(1 for c in conv if c["topic"] == "unassigned"),
    "conv_topic_dist": {f"{k[0]} | {k[1]} | {k[2]}": v for k, v in Counter((c["role"], c["skill"], c["topic"]) for c in conv).most_common()},
    "pools_by_role": {role: dict(Counter(c["pool"] for c in cands if c["role"] == role and not c.get("dup_of") and c["pool"] != "rejected")) for role in sorted({c["role"] for c in cands})},
    "devops_inactive_authentic": sum(1 for c in cands if c["source"] in DEVOPS_SOURCES and c["pool"] != "rejected" and not c["row_active"]),
    "fidelity": {"devops_question_text_equals_html_stripped_raw": sum(1 for c in cands if c["source"] in DEVOPS_SOURCES and html_to_text(c["question_raw"]) == c["question_text"]),
                 "devops_total": sum(1 for c in cands if c["source"] in DEVOPS_SOURCES),
                 "jsreact_question_text_equals_header": sum(1 for c in cands if c["source"] in ("JavaScript", "React") and c["question_raw"].strip().lstrip("# ").strip() .endswith(c["question_text"][-20:])),
                 "jsreact_total": sum(1 for c in cands if c["source"] in ("JavaScript", "React"))},
    "samples": dict(samples),
    "curated": {"rows": len(cur), "types": dict(cur_types), "active_by_type": dict(cur_active), "embedded_by_type": dict(cur_emb),
                "mojibake_rows": cur_mojibake, "subtopic_unbalanced_parens_rows": cur_bad_paren_sub,
                "distinct_role_topic_subtopic": len(cur_combo), "distinct_with_balanced_parens": cur_subtopics_clean,
                "template_question_rows": cur_q_rows, "template_question_regex_exact_matches": cur_template_q_regex,
                "exact_duplicate_content_groups": len(cur_dup_groups), "exact_duplicate_records": sum(len(v) for v in cur_dup_groups),
                "role_dist": dict(cur_role)},
    "codealpaca": {"rows": len(ca), "categories": dict(ca_cat), "top_verbs": ca_verb.most_common(25), "languages": dict(ca_lang.most_common()),
                   "has_input_spec": ca_has_input, "instruction_ends_with_qmark": ca_q_end, "active_status": ca_active, "embedded": ca_emb,
                   "role_language_mismatch": ca_mismatch, "role_language_checked": ca_mismatch_base,
                   "dup_instruction_groups": len(ca_dups), "dup_instruction_records": sum(len(v) for v in ca_dups),
                   "boilerplate_rubric_rows": ca_rubric_ident, "samples": dict(ca_samples),
                   "role_x_language": {k: dict(v.most_common(6)) for k, v in ca_role_lang.items()}},
    "exposure": exposure,
    "unsourced_rows": len(by_src["UNSOURCED"]),
}
json.dump(analysis, open(os.path.join(REP, "_scratch_analysis.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
json.dump({"_note": "READ-ONLY analysis artifact: verbatim extraction candidates with verdicts. NOT loaded anywhere. No DB writes.",
           "count": len(cands), "candidates": cands},
          open(os.path.join(REP, "question_bank_reconstruction_candidates.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print("done", len(cands))
