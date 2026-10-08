import json
import os
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BACKEND_DIR, "data", "interview_question_bank_v2_generated.jsonl")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

CANONICAL_ROLES = {
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst",
    "AI Engineer", "ML Engineer", "Full Stack Developer"
}

def is_ml_question(record):
    # Heuristics to check if it's an ML question
    ml_keywords = ['model', 'learning', 'training', 'data', 'feature', 'gradient', 'neural', 'hyperparameter']
    q = record.get('question', '').lower()
    a = record.get('expected_answer', '').lower()
    topic = record.get('topic', '').lower()
    skill = record.get('primary_skill', '').lower()
    
    combined = q + " " + a + " " + topic + " " + skill
    if any(k in combined for k in ml_keywords):
        return True
    return False

def main():
    if not os.path.exists(DATA_FILE):
        print("Data file not found!")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        records = [json.loads(line.strip()) for line in f if line.strip()]

    # TASK 1: Short Answer Review
    short_answer_record = None
    for idx, r in enumerate(records):
        ans = r.get("expected_answer", "")
        if len(ans) < 50:
            short_answer_record = r
            short_answer_record["_line_index"] = idx
            break
            
    if short_answer_record:
        ans = short_answer_record.get("expected_answer", "")
        q = short_answer_record.get("question", "")
        
        # Classification heuristic
        if "yes" in ans.lower() or "no" in ans.lower() or len(ans.split()) < 3:
            classification = "INCOMPLETE_ANSWER"
            action = "Regenerate or expand answer"
            reason = "Answer is too short to demonstrate competence."
        else:
            classification = "ACCEPTABLE — NO CHANGE REQUIRED"
            action = "Keep as-is"
            reason = "Answer is concise but technically valid."
            
        short_answer_report = {
            "record_id": short_answer_record.get("id", str(short_answer_record["_line_index"])),
            "question": q,
            "current_answer": ans,
            "role": short_answer_record.get("primary_role"),
            "skill": short_answer_record.get("primary_skill"),
            "technology": short_answer_record.get("technology"),
            "topic": short_answer_record.get("topic"),
            "intent": short_answer_record.get("intent"),
            "difficulty": short_answer_record.get("difficulty"),
            "question_type": short_answer_record.get("question_type"),
            "issue_classification": classification,
            "explanation": reason,
            "recommended_action": action
        }
        
        with open(os.path.join(REPORTS_DIR, "phase4d_short_answer_review_v1.json"), "w", encoding='utf-8') as f:
            json.dump(short_answer_report, f, indent=2)
            
        with open(os.path.join(REPORTS_DIR, "phase4d_short_answer_review_v1.md"), "w", encoding='utf-8') as f:
            md = f"# Phase 4D Short Answer Review V1\n\n"
            md += f"- **Record ID**: {short_answer_report['record_id']}\n"
            md += f"- **Question**: {q}\n"
            md += f"- **Answer**: {ans}\n"
            md += f"- **Classification**: {classification}\n"
            md += f"- **Reasoning**: {reason}\n"
            md += f"- **Recommended Action**: {action}\n"
            f.write(md)

    # TASK 2, 3, 4, 5, 6, 7, 9
    raw_roles = Counter()
    role_conflicts = []
    authoritative_field = "primary_role"
    
    normalization_manifest = {
        "canonical_roles": list(CANONICAL_ROLES),
        "role_mappings": [],
        "records": [],
        "safe_to_normalize_count": 0,
        "review_required_count": 0,
        "do_not_normalize_count": 0
    }
    
    # Check consistency between role and primary_role
    has_role = sum(1 for r in records if "role" in r)
    has_primary = sum(1 for r in records if "primary_role" in r)
    if has_primary >= has_role:
        authoritative_field = "primary_role"
    else:
        authoritative_field = "role"

    for idx, r in enumerate(records):
        role_val = r.get("role")
        primary_val = r.get("primary_role")
        
        if role_val and primary_val and role_val != primary_val:
            role_conflicts.append({
                "id": r.get("id", str(idx)),
                "role": role_val,
                "primary_role": primary_val
            })
            
        r_role = primary_val if primary_val else role_val
        raw_roles[r_role] += 1
        
        if r_role == "Machine Learning Engineer":
            rec = {
                "record_index": r.get("id", str(idx)),
                "current_role": r_role,
                "proposed_role": "ML Engineer",
            }
            if is_ml_question(r):
                rec["classification"] = "SAFE_TO_NORMALIZE"
                rec["confidence"] = 1.0
                rec["reason"] = "Question clearly tests machine learning engineering competency."
                normalization_manifest["safe_to_normalize_count"] += 1
            else:
                rec["classification"] = "REVIEW_REQUIRED"
                rec["confidence"] = 0.5
                rec["reason"] = "Question content does not strongly indicate ML competency."
                normalization_manifest["review_required_count"] += 1
            normalization_manifest["records"].append(rec)
            
    # Compile role inventory
    role_inventory = []
    for raw_r, count in raw_roles.items():
        if raw_r in CANONICAL_ROLES:
            canon = raw_r
            conf = 1.0
            status = "ALREADY_CANONICAL"
        elif raw_r == "Machine Learning Engineer":
            canon = "ML Engineer"
            conf = 1.0
            status = "REQUIRES_NORMALIZATION"
        else:
            canon = "UNKNOWN"
            conf = 0.0
            status = "REVIEW_REQUIRED"
            
        role_inventory.append({
            "raw_role": raw_r,
            "count": count,
            "canonical_mapping": canon,
            "confidence": conf,
            "normalization_status": status
        })
        
    with open(os.path.join(REPORTS_DIR, "phase4d_role_inventory_v3.json"), "w", encoding='utf-8') as f:
        json.dump(role_inventory, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_role_normalization_manifest_v1.json"), "w", encoding='utf-8') as f:
        json.dump(normalization_manifest, f, indent=2)
        
    # Check ML counts
    raw_ml = raw_roles.get("ML Engineer", 0)
    safe_ml = normalization_manifest["safe_to_normalize_count"]
    canonical_ml_count = raw_ml + safe_ml
    
    print(f"Total Staging Records: {len(records)}")
    print(f"Short Answer Classified: {short_answer_report['issue_classification'] if short_answer_record else 'None'}")
    print(f"Machine Learning Engineer Records: {raw_roles.get('Machine Learning Engineer', 0)}")
    print(f"SAFE_TO_NORMALIZE: {normalization_manifest['safe_to_normalize_count']}")
    print(f"REVIEW_REQUIRED: {normalization_manifest['review_required_count']}")
    print(f"DO_NOT_NORMALIZE: {normalization_manifest['do_not_normalize_count']}")
    print(f"Other Noncanonical Roles: {sum(1 for r in role_inventory if r['normalization_status'] == 'REVIEW_REQUIRED')}")
    print(f"Canonical ML Engineer Count: {canonical_ml_count}")
    print(f"Remaining ML Engineer to 500: {max(0, 500 - canonical_ml_count)}")
    print(f"Role Conflicts: {len(role_conflicts)}")
    print("STAGING DATASET MODIFIED: NO")

if __name__ == "__main__":
    main()
