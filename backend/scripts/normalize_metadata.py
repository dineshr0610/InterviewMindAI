import json
import os

def normalize_file(filepath):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return
        
    print(f"Normalizing {filepath}...")
    normalized_lines = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            
            # Normalize difficulty
            if 'difficulty' in record and isinstance(record['difficulty'], str):
                record['difficulty'] = record['difficulty'].lower()
                
            # Normalize intent
            if 'intent' in record and isinstance(record['intent'], str):
                record['intent'] = record['intent'].lower()
                
            normalized_lines.append(json.dumps(record))
            
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in normalized_lines:
            f.write(line + '\n')
            
    print(f"Normalized {len(normalized_lines)} records in {filepath}.")

if __name__ == "__main__":
    v3_dir = os.path.join("data", "question_bank_v3")
    canonical_path = os.path.join(v3_dir, "canonical_questions.jsonl")
    quarantine_path = os.path.join(v3_dir, "quarantine_questions.jsonl")
    
    normalize_file(canonical_path)
    normalize_file(quarantine_path)
    print("Metadata normalization complete.")
