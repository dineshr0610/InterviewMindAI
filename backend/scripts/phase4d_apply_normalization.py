import json
import os
import shutil
from datetime import datetime
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

STAGING_FILE = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
BACKUP_FILE = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.pre_role_normalization.jsonl")
MANIFEST_FILE = os.path.join(REPORTS_DIR, "phase4d_role_normalization_manifest_v1.json")

def main():
    # 1. Load manifest and verify
    if not os.path.exists(MANIFEST_FILE):
        print("ERROR: Manifest file not found.")
        return

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if manifest.get("safe_to_normalize_count") != 100:
        print(f"ERROR: Expected exactly 100 SAFE_TO_NORMALIZE records in manifest, found {manifest.get('safe_to_normalize_count')}. Aborting.")
        return
        
    safe_ids = set()
    for rec in manifest.get("records", []):
        if rec.get("classification") == "SAFE_TO_NORMALIZE":
            safe_ids.add(rec.get("record_index"))
            
    if len(safe_ids) != 100:
        print(f"ERROR: Counted {len(safe_ids)} SAFE_TO_NORMALIZE records in manifest list. Aborting.")
        return

    # 2. Backup staging dataset
    if not os.path.exists(STAGING_FILE):
        print("ERROR: Staging file not found.")
        return
        
    shutil.copy2(STAGING_FILE, BACKUP_FILE)
    
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        backup_lines = f.readlines()
        
    if len(backup_lines) != 2092:
        print(f"ERROR: Backup has {len(backup_lines)} lines, expected 2092. Aborting.")
        return

    # 3. Apply normalization
    changed_records = []
    new_lines = []
    modified_count = 0
    
    for idx, line in enumerate(backup_lines):
        if not line.strip():
            continue
            
        record = json.loads(line)
        record_id = record.get("id", str(idx))
        
        if record_id in safe_ids:
            if record.get("primary_role") != "Machine Learning Engineer":
                print(f"ERROR: Record {record_id} does not have 'Machine Learning Engineer'. Found: {record.get('primary_role')}")
                return
                
            record["primary_role"] = "ML Engineer"
            changed_records.append(record_id)
            modified_count += 1
            
        new_lines.append(json.dumps(record) + "\n")
        
    if modified_count != 100:
        print(f"ERROR: Modified {modified_count} records, expected 100. Aborting write.")
        return
        
    if len(new_lines) != 2092:
        print(f"ERROR: Output lines {len(new_lines)} != 2092. Aborting write.")
        return

    # 4. Write back to staging
    with open(STAGING_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # 5. Validation
    with open(STAGING_FILE, "r", encoding="utf-8") as f:
        final_lines = f.readlines()
        
    if len(final_lines) != 2092:
        print("ERROR: Final validation failed on line count.")
        return
        
    final_roles = Counter(json.loads(line).get("primary_role") for line in final_lines if line.strip())
    
    if final_roles.get("Machine Learning Engineer", 0) != 0:
        print("ERROR: Machine Learning Engineer still exists.")
        return
        
    if final_roles.get("ML Engineer", 0) != 200:
        print("ERROR: ML Engineer count is not 200.")
        return

    # 6. Audit Trail
    exec_report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_file": STAGING_FILE,
        "backup_file": BACKUP_FILE,
        "manifest_file": MANIFEST_FILE,
        "records_before": 2092,
        "records_after": len(final_lines),
        "records_changed": modified_count,
        "records_added": 0,
        "records_deleted": 0,
        "old_role": "Machine Learning Engineer",
        "new_role": "ML Engineer",
        "validation_result": "SUCCESS",
        "changed_record_ids": changed_records,
        "final_role_counts": dict(final_roles)
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_role_normalization_execution_v1.json"), "w", encoding="utf-8") as f:
        json.dump(exec_report, f, indent=2)
        
    md = f"""# Phase 4D Role Normalization Execution V1

- **Timestamp**: {exec_report["timestamp"]}
- **Input File**: {exec_report["input_file"]}
- **Backup File**: {exec_report["backup_file"]}
- **Manifest File**: {exec_report["manifest_file"]}

### Execution Summary
- **Records Before**: {exec_report["records_before"]}
- **Records After**: {exec_report["records_after"]}
- **Records Changed**: {exec_report["records_changed"]}
- **Records Added**: {exec_report["records_added"]}
- **Records Deleted**: {exec_report["records_deleted"]}

### Changes
- **Old Role**: `{exec_report["old_role"]}`
- **New Role**: `{exec_report["new_role"]}`
- **Validation Result**: {exec_report["validation_result"]}

### Final Canonical Role Counts
"""
    for role, count in final_roles.items():
        md += f"- **{role}**: {count}\n"
        
    with open(os.path.join(REPORTS_DIR, "phase4d_role_normalization_execution_v1.md"), "w", encoding="utf-8") as f:
        f.write(md)

    print("Normalization execution complete.")
    print(f"Records before: 2092")
    print(f"Records after: {len(final_lines)}")
    print(f"Records normalized: {modified_count}")
    print(f"Old role ('Machine Learning Engineer') count: {final_roles.get('Machine Learning Engineer', 0)}")
    print(f"New ML Engineer count: {final_roles.get('ML Engineer', 0)}")
    print("Validation: SUCCESS")

if __name__ == "__main__":
    main()
