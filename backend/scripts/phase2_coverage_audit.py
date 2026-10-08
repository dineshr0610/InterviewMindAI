import json
import os
import sys
import re
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.services.question_controller import detect_question_intent, INTENT_ARCHITECTURE, INTENT_DESIGN

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

TARGET_ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
    "Machine Learning Engineer", "Full Stack Developer"
]

def load_kept_candidates():
    cands_file = os.path.join(REPORTS_DIR, "question_bank_reconstruction_candidates.json")
    with open(cands_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    conv_cands = [c for c in data["candidates"] if c.get("pool") == "conversational"]
    for c in conv_cands:
        c["actual_intent"] = detect_question_intent(c["question_text"])
        
    conv_cands.sort(key=lambda c: (c["source"], c["candidate_id"]))
    
    def tokens(s): return set(re.findall(r"\b[a-z0-9]+\b", s.lower()))
    
    kept = []
    for c in conv_cands:
        q_text = c["question_text"].lower().strip()
        q_words = tokens(q_text)
        is_dup = False
        for p in kept:
            p_text = p["question_text"].lower().strip()
            if c["skill"] != p["skill"]:
                continue
            if q_text == p_text:
                is_dup = True; break
            p_words = tokens(p_text)
            if not q_words or not p_words: continue
            sim = len(q_words & p_words) / max(1, len(q_words | p_words))
            if sim >= 0.70:
                is_dup = True; break
            
            cand_intent = c["actual_intent"]
            prev_intent = p["actual_intent"]
            intents_match = (cand_intent == prev_intent or {cand_intent, prev_intent} <= {INTENT_ARCHITECTURE, INTENT_DESIGN})
            structural = {INTENT_ARCHITECTURE, INTENT_DESIGN, "justify", "tradeoff", "debug"}
            if intents_match and (cand_intent in structural or prev_intent in structural):
                if sim >= 0.35:
                    is_dup = True; break
        if not is_dup:
            kept.append(c)
    return kept

def scan_datasets():
    inventory = []
    exts = {".csv", ".json", ".jsonl", ".tsv", ".xlsx", ".xls", ".parquet", ".txt", ".md", ".sql", ".yaml", ".yml", ".xml", ".html"}
    skip_dirs = {".git", "node_modules", "venv", "__pycache__", ".next", "build", "dist"}
    
    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in exts:
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, ROOT_DIR)
                
                # Heuristics for dataset relevance
                lower_path = rel_path.lower()
                is_data_dir = any(x in lower_path for x in ["data/", "datasets/", "dataset/", "resources/", "seed/", "fixtures/"])
                is_data_file = any(x in lower_path for x in ["question", "dataset", "alpaca", "system design", "curated", "interview", "rubric", "answer"])
                
                if is_data_dir or is_data_file or ext in {".csv", ".jsonl", ".tsv", ".parquet"}:
                    try:
                        size = os.path.getsize(path)
                        if size > 1000: # Ignore tiny files
                            # Sample content
                            with open(path, "r", encoding="utf-8", errors="ignore") as f_obj:
                                preview = f_obj.read(5000)
                                if any(x in preview.lower() for x in ["question", "answer", "instruction", "difficulty", "skill", "role"]):
                                    row_count = preview.count("\n") if ext in {".csv", ".jsonl", ".tsv", ".txt", ".sql"} else "unknown"
                                    
                                    # Guess purpose
                                    purpose = "unknown"
                                    if "### Technical Interview Question" in preview: purpose = "Already-clean questions"
                                    elif "instruction" in preview and "output" in preview: purpose = "Raw source material (CodeAlpaca style)"
                                    elif "<details>" in preview: purpose = "Raw source material (DevOps style)"
                                    else: purpose = "Documentation/Tutorial or Raw Data"
                                    
                                    inventory.append({
                                        "FILE": rel_path,
                                        "FORMAT": ext,
                                        "SIZE_BYTES": size,
                                        "ROW_COUNT_ESTIMATE": row_count,
                                        "PURPOSE": purpose,
                                        "POTENTIAL_VALUE": "High" if "question" in preview.lower() else "Medium"
                                    })
                    except Exception:
                        pass
    return inventory

def main():
    print("Loading kept candidates...")
    candidates = load_kept_candidates()
    print(f"Loaded {len(candidates)} candidates.")
    
    # 1. Scan datasets
    print("Scanning for datasets...")
    inventory = scan_datasets()
    with open(os.path.join(REPORTS_DIR, "phase2_repository_dataset_inventory.json"), "w") as f:
        json.dump({"inventory": inventory}, f, indent=2)
        
    # 2. Coverage Maps
    role_skill_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    role_counts = Counter()
    skill_counts = Counter()
    intent_counts = Counter()
    diff_counts = Counter()
    type_counts = Counter()
    
    # Track roles actually found
    actual_roles = set()
    
    for c in candidates:
        r = c.get("role", "UNKNOWN")
        if not r: r = "UNKNOWN"
        actual_roles.add(r)
        
        s = c.get("skill", "UNKNOWN")
        if not s: s = "UNKNOWN"
        
        # In InterviewMind, sometimes topic is technology, sometimes subtopic is topic.
        # We will use skill as the main branch, and topic as the sub-branch.
        t = c.get("topic", "UNKNOWN")
        if not t: t = "UNKNOWN"
        
        i = c.get("actual_intent", "explain")
        d = c.get("legacy_difficulty", "UNKNOWN")
        if not d: d = "UNKNOWN"
        
        role_counts[r] += 1
        skill_counts[s] += 1
        intent_counts[i] += 1
        diff_counts[d] += 1
        type_counts[c.get("question_type", "unknown")] += 1
        
        role_skill_map[r][s]["TECHNOLOGY_UNKNOWN"][t] += 1

    with open(os.path.join(REPORTS_DIR, "phase2_role_skill_matrix.json"), "w") as f:
        json.dump(role_skill_map, f, indent=2)

    # 3. Gap Matrix
    MVP_PER_ROLE = 200
    gap_matrix = []
    
    for role in TARGET_ROLES:
        count = role_counts.get(role, 0)
        gap = count - MVP_PER_ROLE
        
        # Find which skills exist for this role
        skills = list(role_skill_map.get(role, {}).keys())
        
        gap_matrix.append({
            "ROLE": role,
            "SKILLS_PRESENT": skills,
            "CURRENT_COUNT": count,
            "REQUIRED_COUNT": MVP_PER_ROLE,
            "GAP": gap,
            "STATUS": "GREEN" if gap >= 0 else ("YELLOW" if count > 50 else "RED")
        })

    with open(os.path.join(REPORTS_DIR, "phase2_gap_matrix.json"), "w") as f:
        json.dump({"MVP_TARGET": MVP_PER_ROLE, "gaps": gap_matrix}, f, indent=2)
        
    # 4. Coverage Audit JSON
    audit_json = {
        "total_canonical_questions": len(candidates),
        "target_roles_coverage": {r: role_counts.get(r, 0) for r in TARGET_ROLES},
        "other_roles_found": {r: role_counts[r] for r in actual_roles if r not in TARGET_ROLES},
        "intent_distribution": dict(intent_counts),
        "difficulty_distribution": dict(diff_counts),
        "question_type_distribution": dict(type_counts),
        "mvp_target_per_role": MVP_PER_ROLE,
        "production_target_per_role": 500,
        "large_target_per_role": 1000
    }
    with open(os.path.join(REPORTS_DIR, "phase2_dataset_coverage_audit.json"), "w") as f:
        json.dump(audit_json, f, indent=2)

    # 5. Markdown Report
    md_report = f"""# Phase 2: Dataset Coverage Audit

## 1. Overall Status
- **Current Canonical Questions**: {len(candidates)}
- **MVP Target per Role**: {MVP_PER_ROLE}
- **Production Target per Role**: 500

## 2. Role Coverage

| Role | Current Count | Status |
|------|---------------|--------|
"""
    for g in gap_matrix:
        md_report += f"| {g['ROLE']} | {g['CURRENT_COUNT']} | {g['STATUS']} |\n"

    md_report += """
## 3. Intent Coverage

The current dataset leans heavily towards conceptual explanation.

"""
    for k, v in intent_counts.most_common():
        md_report += f"- **{k}**: {v}\n"
        
    md_report += """
## 4. Gap Analysis & Quality Decisions
- **Is 1,857 enough for 10 roles?** No. Roles like Python Developer, Backend Developer, Data Analyst, etc. have ZERO valid conversational questions currently assigned to them.
- **Under-covered Roles**: Python, Java, Database, Backend, Data Analyst, AI, ML, Full Stack.
- **Under-covered Intents**: Tradeoff, architecture, design, debug, scenario.
- **Can existing Supabase records fill gaps?** Some records in `CodeAlpaca` might be adapted for coding questions, but conversational questions for missing roles must be sourced elsewhere.
- **Synthetic Question Policy**: We will reject the bad 'trade-offs' boilerplate template. High-quality generation can be used ONLY IF raw sources cannot be found.
"""
    with open(os.path.join(REPORTS_DIR, "phase2_dataset_coverage_audit.md"), "w") as f:
        f.write(md_report)

    # 6. Architecture Report
    arch_report = """# Phase 2: Recommended Dataset Architecture

## 1. Multi-Bank Logical Architecture

We should NOT force everything into one table.

### A. Conversational Technical Bank
- Purpose: Standard Q&A, deep dives, scenarios.
- Structure: Questions mapped to Role -> Skill -> Topic -> Intent -> Difficulty.

### B. Coding Tasks Bank
- Purpose: Hands-on code generation or modification (CodeAlpaca-style).
- Structure: Instruction -> Input Spec -> Reference Output -> Language.

### C. System Design Bank
- Purpose: Large, open-ended architecture scenarios.
- Structure: Prompt -> Constraints -> Expected Components -> Scaling requirements.

## 2. Supabase Target Structure

Instead of overloading `document_embeddings`, use:

- `question_sources`: Raw ingestion material (HTML, Markdown, links).
- `question_bank`: The canonical, clean dataset (one row = one question with metadata).
- `question_embeddings`: A 1:1 or 1:N mapping from `question_bank` storing the vector.

## 3. Quality Gates
1. Standalone / Technically meaningful.
2. Authentic or high-quality generation.
3. No markdown pollution or prompt leakage.
4. Valid Intent, Topic, Skill, Role.
"""
    with open(os.path.join(REPORTS_DIR, "phase2_recommended_dataset_architecture.md"), "w") as f:
        f.write(arch_report)

    print("Phase 2 reports generated.")

if __name__ == "__main__":
    main()
