import os
import json
import hashlib
import re
import datetime
from collections import defaultdict
from typing import Dict, Any, List

# Add path so we can import internal modules if necessary, though we can do it independently
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def normalize_role(role: str) -> str:
    role_map = {
        "python developer": "Python Developer",
        "frontend developer": "Frontend Developer",
        "java developer": "Java Developer",
        "database developer": "Database Developer",
        "devops / cloud engineer": "DevOps / Cloud Engineer",
        "backend developer": "Backend Developer",
        "data analyst": "Data Analyst",
        "ai engineer": "AI Engineer",
        "ml engineer": "ML Engineer",
        "full stack developer": "Full Stack Developer"
    }
    return role_map.get(str(role).lower().strip(), "Unknown")

CANONICAL_ROLES = {
    "Python Developer", "Frontend Developer", "Java Developer",
    "Database Developer", "DevOps / Cloud Engineer", "Backend Developer",
    "Data Analyst", "AI Engineer", "ML Engineer", "Full Stack Developer"
}

CANONICAL_DIFFICULTIES = {"easy", "medium", "hard"}

def calc_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_hash(record_str: str) -> str:
    return hashlib.sha256(record_str.encode('utf-8')).hexdigest()

def normalize_difficulty(diff: str) -> str:
    if not diff or not isinstance(diff, str):
        return "unknown"
    return diff.strip().lower()

def is_generic_question(question: str) -> bool:
    generic_patterns = [
        r"^tell me about your experience\.?$",
        r"^what is your favorite technology\??$",
        r"^explain programming\.?$",
        r"^how do you handle conflict\??$",
        r"^tell me about yourself\.?$",
        r"^what are your strengths\??$"
    ]
    q_lower = question.lower().strip()
    for pattern in generic_patterns:
        if re.search(pattern, q_lower):
            return True
    # Length based check for extreme generic
    if len(q_lower.split()) < 4:
        return True
    return False

def has_prompt_leakage(question: str) -> bool:
    leak_patterns = [
        "ignore previous instructions",
        "system prompt",
        "you are chatgpt",
        "return json",
        "do not reveal",
        "developer message",
        "assistant response",
        "as an ai",
        "as a large language model"
    ]
    q_lower = question.lower()
    for pattern in leak_patterns:
        if pattern in q_lower:
            return True
    return False

def validate_text(text: str) -> str | None:
    if not isinstance(text, str):
        return "non-string question"
    text = text.strip()
    if not text:
        return "empty question"
    if len(text) < 5:
        return "extremely short question"
    if len(text) > 4000:
        return "extremely long content"
    if "rubric:" in text.lower() or "expected answer:" in text.lower():
        return "rubric text embedded"
    return None

def role_alignment_check(role: str, question: str) -> bool:
    # A basic keyword check. This isn't perfect, so if uncertain, we flag.
    # In this phase, we won't strictly quarantine based solely on this unless obvious,
    # but the prompt says: "If role alignment is uncertain: flag for review."
    
    keywords = {
        "Python Developer": ["python", "fastapi", "django", "asyncio", "gil", "pip", "pytest"],
        "Frontend Developer": ["react", "typescript", "browser", "css", "html", "dom", "vue", "angular", "js", "javascript"],
        "Database Developer": ["sql", "index", "transaction", "postgresql", "mysql", "nosql", "query", "acid"],
        "DevOps / Cloud Engineer": ["aws", "docker", "kubernetes", "ci/cd", "terraform", "linux", "cloud", "pipeline"],
        "Java Developer": ["java", "spring", "jvm", "maven", "gradle", "garbage collection"],
        "Data Analyst": ["sql", "pandas", "tableau", "visualization", "excel", "metrics", "dashboard"],
        "AI Engineer": ["llm", "prompt", "transformer", "genai", "rag", "langchain", "openai"],
        "ML Engineer": ["pytorch", "tensorflow", "model", "training", "dataset", "sklearn", "deep learning"],
        "Backend Developer": ["api", "rest", "microservice", "database", "node", "caching", "architecture", "system design", "scale", "performance", "thread"],
        "Full Stack Developer": ["api", "react", "database", "node", "frontend", "backend", "full stack"]
    }
    
    if role not in keywords:
        return True # Cannot check
    
    q_lower = question.lower()
    for kw in keywords[role]:
        if kw in q_lower:
            return True
            
    # if no explicit keywords are found, it might still be a valid conceptual question
    # We will flag it as uncertain.
    return False

def main():
    source_file = os.path.join("data", "interview_question_bank_v2_generated.jsonl")
    out_dir = os.path.join("data", "question_bank_v3")
    os.makedirs(out_dir, exist_ok=True)
    
    canonical_file = os.path.join(out_dir, "canonical_questions.jsonl")
    quarantine_file = os.path.join(out_dir, "quarantine_questions.jsonl")
    report_file = os.path.join(out_dir, "quality_report.md")
    stats_file = os.path.join(out_dir, "statistics.json")
    manifest_file = os.path.join(out_dir, "manifest.json")
    
    source_sha = calc_sha256(source_file)
    
    stats = {
        "raw_count": 0,
        "canonical_count": 0,
        "quarantined_count": 0,
        "exact_duplicates": 0,
        "prompt_leakage": 0,
        "malformed": 0,
        "fields_present": defaultdict(int),
        "role_distribution": defaultdict(int),
        "difficulty_distribution": defaultdict(int),
        "intent_distribution": defaultdict(int),
        "quarantine_reasons": defaultdict(int),
        "role_counts": defaultdict(int),
    }
    
    records = []
    with open(source_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stats["raw_count"] += 1
            try:
                record = json.loads(line)
                records.append(record)
                for k in record.keys():
                    stats["fields_present"][k] += 1
            except json.JSONDecodeError:
                stats["malformed"] += 1
                stats["quarantine_reasons"]["json_decode_error"] += 1

    # 1. Exact Duplicate ID and Text tracking
    seen_ids = set()
    seen_texts = set()
    
    canonical_records = []
    quarantined_records = []
    
    # 2. Process records deterministically (they are in order from the file)
    for i, r in enumerate(records):
        quarantine_reasons = []
        
        # ID check
        q_id = r.get("id") or r.get("question_id")
        if not q_id:
            # Try to build deterministic ID
            q_id = f"gen_q_{i}"
        
        if q_id in seen_ids:
            quarantine_reasons.append("duplicate_id")
        
        # Canonical schema fields
        question = r.get("question")
        role = r.get("role") or r.get("role_name")
        difficulty = r.get("difficulty")
        intent = r.get("intent") or r.get("category") or "General"
        topic = r.get("topic") or "General"
        provenance = r.get("provenance") or r.get("source") or "unknown"
        
        # Validation: Text
        text_err = validate_text(question) if question else "missing question field"
        if text_err:
            quarantine_reasons.append(text_err)
        
        # Validation: Leakage
        if question and has_prompt_leakage(question):
            quarantine_reasons.append("prompt_leakage")
            stats["prompt_leakage"] += 1
            
        # Validation: Generic
        if question and is_generic_question(question):
            quarantine_reasons.append("generic_question")
            
        # Validation: Exact text duplicate (normalized)
        if question:
            norm_q = re.sub(r'\W+', '', question.lower())
            if norm_q in seen_texts:
                quarantine_reasons.append("exact_duplicate")
                stats["exact_duplicates"] += 1
            else:
                seen_texts.add(norm_q)
                
        # Normalization: Role
        norm_role = normalize_role(role)
        if norm_role not in CANONICAL_ROLES:
            quarantine_reasons.append(f"unmapped_role: {role}")
            norm_role = "Unknown"
            
        # Normalization: Difficulty
        norm_diff = normalize_difficulty(difficulty)
        if norm_diff not in CANONICAL_DIFFICULTIES:
            quarantine_reasons.append(f"invalid_difficulty: {difficulty}")
            norm_diff = "unknown"
            
        # Validation: Role alignment
        if question and norm_role in CANONICAL_ROLES:
            if not role_alignment_check(norm_role, question):
                quarantine_reasons.append("uncertain_role_alignment")
        
        # Create canonical record
        canonical_r = {
            "id": q_id,
            "question": question,
            "role": norm_role,
            "difficulty": norm_diff,
            "intent": str(intent).strip().title() if intent else "Unknown",
            "topic": str(topic).strip(),
            "provenance": provenance
        }
        
        if quarantine_reasons:
            canonical_r["_quarantine_reasons"] = quarantine_reasons
            quarantined_records.append(canonical_r)
            stats["quarantined_count"] += 1
            for req in quarantine_reasons:
                stats["quarantine_reasons"][req] += 1
        else:
            canonical_records.append(canonical_r)
            stats["canonical_count"] += 1
            seen_ids.add(q_id)
            stats["role_counts"][norm_role] += 1
            stats["difficulty_distribution"][norm_diff] += 1
            stats["intent_distribution"][canonical_r["intent"]] += 1
            
    # Write canonical
    with open(canonical_file, "w", encoding="utf-8") as f:
        for r in canonical_records:
            f.write(json.dumps(r) + "\n")
            
    # Write quarantined
    with open(quarantine_file, "w", encoding="utf-8") as f:
        for r in quarantined_records:
            f.write(json.dumps(r) + "\n")
            
    # Post compute hashes
    canonical_sha = calc_sha256(canonical_file)
    quarantine_sha = calc_sha256(quarantine_file)
    
    # Manifest
    manifest = {
        "pipeline_version": "1.0.0",
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "source_sha256": source_sha,
        "canonical_sha256": canonical_sha,
        "quarantine_sha256": quarantine_sha,
        "counts": {
            "raw": stats["raw_count"],
            "canonical": stats["canonical_count"],
            "quarantined": stats["quarantined_count"]
        },
        "normalization_rules": {
            "role": "Mapped to 10 canonical roles. Unmapped quarantined.",
            "difficulty": "Lowercased, mapped to easy/medium/hard. Others quarantined."
        }
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    with open(stats_file, "w", encoding="utf-8") as f:
        # Convert defaultdicts to dicts
        for k in stats:
            if isinstance(stats[k], defaultdict):
                stats[k] = dict(stats[k])
        json.dump(stats, f, indent=2)
        
    # Quality Report Markdown
    report_md = f"""# Phase 8C Quality Pipeline Report\n
## Overview
- **Source SHA-256**: `{source_sha}`
- **Output SHA-256 (Canonical)**: `{canonical_sha}`
- **Total Raw Records**: {stats["raw_count"]}
- **Total Canonical Valid**: {stats["canonical_count"]}
- **Total Quarantined**: {stats["quarantined_count"]}

## Quality Issues Detected
- **Exact Duplicates**: {stats["exact_duplicates"]}
- **Prompt Leakage**: {stats["prompt_leakage"]}
- **Malformed JSON**: {stats["malformed"]}

### Quarantine Reasons Breakdown
"""
    for reason, count in sorted(stats["quarantine_reasons"].items(), key=lambda x: -x[1]):
        report_md += f"- {reason}: {count}\n"

    report_md += """\n## Schema Discovery\nFields present in raw data:\n"""
    for field, count in sorted(stats["fields_present"].items(), key=lambda x: -x[1]):
        report_md += f"- `{field}`: {count} ({count/stats['raw_count']*100:.1f}%)\n"

    report_md += """\n## Role Coverage (Valid)\n"""
    for role, count in sorted(stats["role_counts"].items(), key=lambda x: -x[1]):
        report_md += f"- **{role}**: {count}\n"

    report_md += """\n## Difficulty Distribution (Valid)\n"""
    for diff, count in sorted(stats["difficulty_distribution"].items(), key=lambda x: -x[1]):
        report_md += f"- **{diff}**: {count} ({(count/max(1, stats['canonical_count']))*100:.1f}%)\n"

    report_md += """\n## Intent Distribution (Valid)\n"""
    for intent, count in sorted(stats["intent_distribution"].items(), key=lambda x: -x[1])[:15]:
        report_md += f"- **{intent}**: {count}\n"
    if len(stats["intent_distribution"]) > 15:
        report_md += f"- *(and {len(stats['intent_distribution']) - 15} more)*\n"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)

    print("Pipeline complete.")

if __name__ == "__main__":
    main()
