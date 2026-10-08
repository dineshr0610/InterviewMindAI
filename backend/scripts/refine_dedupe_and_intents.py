import json
import os
import sys
import re
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.services.question_controller import detect_question_intent, INTENT_ARCHITECTURE, INTENT_DESIGN

CANDIDATES_FILE = os.path.join("reports", "question_bank_reconstruction_candidates.json")

def load_candidates():
    with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["candidates"]

def tokens(s):
    return set(re.findall(r"\b[a-z0-9]+\b", s.lower()))

def main():
    cands = load_candidates()
    # Filter for conversational questions that are not already rejected
    conv_cands = [c for c in cands if c.get("pool") == "conversational"]
    
    # 1. Re-assign intents using actual detect_question_intent
    intent_counts = Counter()
    for c in conv_cands:
        intent = detect_question_intent(c["question_text"])
        c["actual_intent"] = intent
        intent_counts[intent] += 1
        
    print("Actual Intent Distribution:")
    for k, v in intent_counts.most_common():
        print(f"  {k}: {v}")
    
    # 2. Refined deduplication based on QuestionController logic
    # Sort candidates consistently
    conv_cands.sort(key=lambda c: (c["source"], c["candidate_id"]))
    
    kept = []
    dropped = []
    
    for c in conv_cands:
        q_text = c["question_text"].lower().strip()
        q_words = tokens(q_text)
        cand_intent = c["actual_intent"]
        c_skill = c["skill"]
        
        is_dup = False
        dup_reason = None
        dup_of = None
        
        for p in kept:
            p_text = p["question_text"].lower().strip()
            
            p_words = tokens(p_text)
            if not q_words or not p_words:
                continue
                
            # Only compare for deduplication within the same skill
            if c_skill != p["skill"]:
                continue
                
            # Exact match
            if q_text == p_text:
                is_dup = True
                dup_reason = "exact_match"
                dup_of = p["candidate_id"]
                break
                
            # Token overlap similarity >= 0.70
            similarity = len(q_words & p_words) / max(1, len(q_words | p_words))
            if similarity >= 0.70:
                is_dup = True
                dup_reason = "near_duplicate"
                dup_of = p["candidate_id"]
                break
                
            # Semantic repetition check
            prev_intent = p["actual_intent"]
            intents_match = (
                cand_intent == prev_intent
                or {cand_intent, prev_intent} <= {INTENT_ARCHITECTURE, INTENT_DESIGN}
            )
            
            structural = {INTENT_ARCHITECTURE, INTENT_DESIGN, "justify", "tradeoff", "debug"}
            
            if intents_match and (cand_intent in structural or prev_intent in structural):
                sim = len(q_words & p_words) / max(1, len(q_words | p_words))
                if sim >= 0.35:
                    is_dup = True
                    dup_reason = "semantic_repetition"
                    dup_of = p["candidate_id"]
                    break
        
        if is_dup:
            dropped.append({
                "cand": c,
                "reason": dup_reason,
                "dup_of": dup_of
            })
        else:
            kept.append(c)
            
    print(f"\nTotal Conversational: {len(conv_cands)}")
    print(f"Kept after refinement: {len(kept)}")
    print(f"Dropped: {len(dropped)}")
    
    reasons = Counter(d["reason"] for d in dropped)
    print("\nDrop reasons:")
    for k, v in reasons.most_common():
        print(f"  {k}: {v}")
    
    report = {
        "intent_distribution": dict(intent_counts),
        "total_conversational": len(conv_cands),
        "kept_count": len(kept),
        "dropped_count": len(dropped),
        "drop_reasons": dict(reasons),
        "dropped_samples": [
            {
                "question": d["cand"]["question_text"],
                "dup_of": [k["question_text"] for k in kept if k["candidate_id"] == d["dup_of"]][0],
                "reason": d["reason"],
                "intent": d["cand"]["actual_intent"],
                "skill": d["cand"]["skill"]
            }
            for d in dropped[:30]
        ]
    }
    
    with open(os.path.join("reports", "dedupe_refinement_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print("Report saved to reports/dedupe_refinement_report.json")

if __name__ == "__main__":
    main()
