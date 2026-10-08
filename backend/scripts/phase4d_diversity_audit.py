import json
import os
import sys
import re
import csv
import asyncio
from collections import defaultdict, Counter
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.services.question_controller import detect_question_intent

load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
DATA_DIR = os.path.join(BACKEND_DIR, "data")

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def fetch_all_supabase():
    db_url = os.getenv("DATABASE_URL")
    clean_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://") if not db_url.startswith("postgresql+asyncpg") else db_url
    engine = create_async_engine(clean_db_url)
    out_rows = []
    async with engine.connect() as conn:
        res = await conn.execute(sql_text("SELECT id, content, metadata FROM public.document_embeddings;"))
        for r in res.fetchall():
            out_rows.append({"id": str(r[0]), "content": r[1], "metadata": r[2] if isinstance(r[2], dict) else json.loads(r[2] or "{}")})
    await engine.dispose()
    return out_rows

def main():
    print("Fetching existing from Supabase...")
    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_running_loop()
        records = loop.run_until_complete(fetch_all_supabase())
    except Exception:
        records = asyncio.run(fetch_all_supabase())
        
    all_qs = []
    
    # Process Supabase
    for r in records:
        meta = r.get("metadata", {})
        if meta.get("status") == "inactive": continue
        c = r.get("content", "")
        if "### Instruction:" in c and "### Output:" in c:
            q_text = c.split("### Instruction:")[1].split("### Output:")[0].strip()
            if "write a program" in q_text.lower() or "implement a function" in q_text.lower(): continue
        elif "### Technical Interview Question" in c:
            try:
                if "**Answer:**" in c:
                    q_text = c.split("**Answer:**")[0].replace("### Technical Interview Question", "").replace("**Question:**", "").strip()
                    ans_text = c.split("**Answer:**")[1].strip()
                else:
                    q_text = meta.get("question", c[:200])
                    ans_text = meta.get("expected_answer", "")
            except Exception:
                q_text = meta.get("question", c[:200])
                ans_text = meta.get("expected_answer", "")
        else:
            q_text = meta.get("question", c[:200])
            ans_text = meta.get("expected_answer", "")
            
        words = set(re.findall(r"\b[a-z0-9]+\b", q_text.lower()))
        if len(words) < 3: continue
        
        intent = detect_question_intent(q_text)
        
        all_qs.append({
            "id": r["id"],
            "batch": "Existing",
            "question": q_text,
            "normalized_question": normalize_text(q_text),
            "expected_answer": ans_text,
            "normalized_answer": normalize_text(ans_text),
            "role": meta.get("role", "Backend Developer"),
            "skill": meta.get("skill", "General"),
            "technology": meta.get("technology", "Gen"),
            "topic": meta.get("topic", "Gen"),
            "intent": intent,
            "difficulty": "medium",
            "question_type": "concept"
        })
        
    # Process Local Batches
    batch_map = {
        0: "Batch 1", 50: "Batch 2", 100: "Batch 3", 150: "Batch 4", 200: "Batch 5"
    }
    
    gen_file = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
    idx = 0
    if os.path.exists(gen_file):
        with open(gen_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                q = json.loads(line)
                batch_name = batch_map.get((idx // 50) * 50, "Batch 5")
                idx += 1
                q_text = q.get("question", "")
                ans_text = q.get("expected_answer", "")
                all_qs.append({
                    "id": q.get("id", f"gen_{idx}"),
                    "batch": batch_name,
                    "question": q_text,
                    "normalized_question": normalize_text(q_text),
                    "expected_answer": ans_text,
                    "normalized_answer": normalize_text(ans_text),
                    "role": q.get("primary_role", "Unknown"),
                    "skill": q.get("primary_skill", "Unknown"),
                    "technology": q.get("technology", "Unknown"),
                    "topic": q.get("topic", "Unknown"),
                    "intent": q.get("intent", "Unknown"),
                    "difficulty": q.get("difficulty", "Unknown"),
                    "question_type": q.get("question_type", "Unknown")
                })
                
    print(f"Total questions loaded: {len(all_qs)}")
    
    # EXACT DUPLICATES
    norm_map = defaultdict(list)
    for q in all_qs:
        norm_map[q["normalized_question"]].append(q)
        
    exact_duplicate_groups = []
    for k, v in norm_map.items():
        if len(v) > 1:
            exact_duplicate_groups.append(v)
            
    # TF-IDF for similarities
    q_texts = [q["normalized_question"] for q in all_qs]
    ans_texts = [q["normalized_answer"] for q in all_qs]
    
    q_vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    q_tfidf = q_vectorizer.fit_transform(q_texts)
    
    ans_vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    ans_tfidf = ans_vectorizer.fit_transform(ans_texts)
    
    q_sims = cosine_similarity(q_tfidf)
    ans_sims = cosine_similarity(ans_tfidf)
    
    near_dupes = []
    semantic_dupes = []
    likely_dupes = []
    possible_dupes = []
    batch_collisions = []
    
    visited_pairs = set()
    
    for i in range(len(all_qs)):
        for j in range(i + 1, len(all_qs)):
            if (i, j) in visited_pairs: continue
            
            qi = all_qs[i]
            qj = all_qs[j]
            
            # Avoid comparing existing with existing to speed up if needed, but the prompt says ALL against ALL.
            # We'll just take high similarity ones.
            q_sim = q_sims[i][j]
            ans_sim = ans_sims[i][j]
            
            if q_sim < 0.6 and ans_sim < 0.6: continue
            
            is_cross_batch = qi["batch"] != qj["batch"] and not (qi["batch"] == "Existing" and qj["batch"] == "Existing")
            
            if is_cross_batch and (q_sim > 0.6 or ans_sim > 0.6):
                batch_collisions.append((qi, qj, q_sim, ans_sim))
            
            if q_sim > 0.95 or (q_sim > 0.85 and ans_sim > 0.8):
                near_dupes.append((qi, qj, q_sim, ans_sim, "DUPLICATE"))
            elif ans_sim > 0.85 and qi["topic"] == qj["topic"]:
                semantic_dupes.append((qi, qj, q_sim, ans_sim, "LIKELY_DUPLICATE"))
            elif q_sim > 0.80:
                likely_dupes.append((qi, qj, q_sim, ans_sim, "LIKELY_DUPLICATE"))
            elif q_sim > 0.70 and qi["intent"] == qj["intent"]:
                possible_dupes.append((qi, qj, q_sim, ans_sim, "POSSIBLE_DUPLICATE"))
            
            visited_pairs.add((i, j))
            
    # Pattern Audit
    pattern_counts = Counter()
    for q in all_qs:
        if q["batch"] != "Existing":
            first_words = " ".join(q["normalized_question"].split()[:3])
            pattern_counts[first_words] += 1
            
    generator_patterns = [{"pattern": k, "count": v} for k, v in pattern_counts.most_common(10) if v > 5]
    
    intent_dist = Counter([q["intent"] for q in all_qs])
    diff_dist = Counter([q["difficulty"] for q in all_qs])
    role_dist = Counter([q["role"] for q in all_qs])
    skill_dist = Counter([q["skill"] for q in all_qs])
    tech_dist = Counter([q["technology"] for q in all_qs])
    topic_dist = Counter([q["topic"] for q in all_qs])
    type_dist = Counter([q["question_type"] for q in all_qs])
    
    highest_risk = []
    for pair in (near_dupes + semantic_dupes)[:50]:
        qi, qj, qs, asim, class_val = pair
        highest_risk.append({
            "classification": class_val,
            "q1_id": qi["id"], "q2_id": qj["id"],
            "q1_text": qi["question"], "q2_text": qj["question"],
            "q1_role": qi["role"], "q2_role": qj["role"],
            "q1_skill": qi["skill"], "q2_skill": qj["skill"],
            "q1_tech": qi["technology"], "q2_tech": qj["technology"],
            "q1_topic": qi["topic"], "q2_topic": qj["topic"],
            "q1_intent": qi["intent"], "q2_intent": qj["intent"],
            "q1_diff": qi["difficulty"], "q2_diff": qj["difficulty"],
            "reason": f"Q_Sim: {qs:.2f}, A_Sim: {asim:.2f}",
            "expected_answer_overlap": asim
        })
        
    rec = "SAFE_TO_CONTINUE"
    if len(near_dupes) > 10 or len(semantic_dupes) > 20:
        rec = "FIX_GENERATOR_BEFORE_CONTINUING"
    elif len(likely_dupes) > 30:
        rec = "MANUAL_REVIEW_REQUIRED"
        
    report = {
        "total_questions": len(all_qs),
        "exact_duplicate_groups": len(exact_duplicate_groups),
        "near_duplicate_groups": len(near_dupes),
        "semantic_duplicate_groups": len(semantic_dupes),
        "likely_duplicate_groups": len(likely_dupes),
        "possible_duplicate_groups": len(possible_dupes),
        "keep_separate_count": len(visited_pairs) - len(near_dupes) - len(semantic_dupes) - len(likely_dupes) - len(possible_dupes),
        "affected_question_count": len(set([q["id"] for group in exact_duplicate_groups for q in group] + [p[0]["id"] for p in near_dupes] + [p[1]["id"] for p in near_dupes])),
        "batch_collision_count": len(batch_collisions),
        "intent_distribution": dict(intent_dist),
        "difficulty_distribution": dict(diff_dist),
        "role_distribution": dict(role_dist),
        "skill_distribution": dict(skill_dist),
        "technology_distribution": dict(tech_dist),
        "topic_distribution": dict(topic_dist),
        "question_type_distribution": dict(type_dist),
        "generator_pattern_findings": generator_patterns,
        "highest_risk_duplicate_groups": highest_risk,
        "recommendation": rec
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_diversity_audit.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_diversity_audit.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["classification", "q1_id", "q2_id", "q1_text", "q2_text", "reason", "answer_sim"])
        for hr in highest_risk:
            writer.writerow([hr["classification"], hr["q1_id"], hr["q2_id"], hr["q1_text"], hr["q2_text"], hr["reason"], hr["expected_answer_overlap"]])

    print("Audit Complete.")
    print(f"Exact Duplicates: {len(exact_duplicate_groups)}")
    print(f"Near Duplicates: {len(near_dupes)}")
    print(f"Semantic Duplicates: {len(semantic_dupes)}")
    print(f"Batch Collisions: {len(batch_collisions)}")
    print(f"Recommendation: {rec}")

if __name__ == "__main__":
    main()
