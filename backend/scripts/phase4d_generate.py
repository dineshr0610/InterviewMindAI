import json
import os
import sys
import uuid
import asyncio
import google.generativeai as genai
from typing_extensions import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.key_pool import gemini_key_pool

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

class EvaluationRubric(TypedDict):
    strong_indicators: list[str]
    weak_indicators: list[str]

class QuestionResult(TypedDict):
    primary_role: str
    applicable_roles: list[str]
    primary_skill: str
    secondary_skills: list[str]
    technology: str
    topic: str
    intent: str
    difficulty: str
    question_type: str
    question: str
    expected_answer: str
    evaluation_rubric: EvaluationRubric

class QuestionList(TypedDict):
    questions: list[QuestionResult]

async def generate_questions_for_bucket(bucket):
    count = bucket['recommended_question_count']
    if count > 15: count = 15 # limit per prompt for stability
    
    prompt = f"""
We are building a production conversational technical interview dataset.
Generate exactly {count} highly specific, distinct technical interview questions for the following bucket:
Role: {bucket['role']}
Skill: {bucket['skill']}
Technology: {bucket['technology']}
Topic: {bucket['topic']}

Required Intents to cover: {", ".join(bucket['missing_intents']) if bucket['missing_intents'] else 'any'}
Required Difficulties to cover: {", ".join(bucket['missing_difficulties']) if bucket['missing_difficulties'] else 'medium/hard'}

Rules:
1. Provide realistic engineering questions.
2. Expected answer must be concise but technically deep.
3. Provide strong and weak evaluation indicators.
4. Do NOT include placeholder text.
"""

    async def _call(key: str):
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            "gemini-3.8-flash", 
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=QuestionList,
                temperature=0.7
            )
        )
        response = await asyncio.to_thread(model.generate_content, prompt)
        return json.loads(response.text)

    try:
        res = await gemini_key_pool.aexecute_with_fallback(_call, max_retries=10)
        return res, count
    except Exception as e:
        print(f"Failed to generate for bucket {bucket['skill']}: {e}")
        return {"questions": []}, count

async def process_batch():
    plan_path = os.path.join(REPORTS_DIR, "phase4c_generation_plan.json")
    if not os.path.exists(plan_path):
        print("Plan not found")
        return
        
    with open(plan_path, "r") as f:
        plan = json.load(f)
        
    # Pick a batch: say top 10 buckets (approx 50-100 questions)
    plan.sort(key=lambda x: x["priority"])
    batch = plan[:10]
    
    print(f"Processing {len(batch)} buckets for Phase 4D batch generation...")
    tasks = [generate_questions_for_bucket(b) for b in batch]
    results = await asyncio.gather(*tasks)
    
    generated_questions = []
    attempted = 0
    for res, c in results:
        attempted += c
        if "questions" in res:
            generated_questions.extend(res["questions"])
            
    # Save to JSONL
    out_path = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
    accepted = 0
    
    # Load existing to prevent duplicate exact strings
    existing_texts = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                existing_texts.add(json.loads(line)["question"].lower())
                
    role_dist = {}
    skill_dist = {}
    intent_dist = {}
    diff_dist = {}
    type_dist = {}
    tech_dist = {}
    topic_dist = {}
    
    with open(out_path, "a", encoding="utf-8") as f:
        for q in generated_questions:
            q_text = q.get("question", "").strip().lower()
            if not q_text or q_text in existing_texts:
                continue
            existing_texts.add(q_text)
            
            q["id"] = str(uuid.uuid4())
            q["source"] = "Gemini_Phase4D_Batch1"
            q["provenance_type"] = "researched_generated"
            q["dataset_version"] = "v2"
            q["status"] = "active"
            
            f.write(json.dumps(q) + "\n")
            accepted += 1
            
            r = q.get("primary_role", "Unknown")
            role_dist[r] = role_dist.get(r, 0) + 1
            s = q.get("primary_skill", "Unknown")
            skill_dist[s] = skill_dist.get(s, 0) + 1
            i = q.get("intent", "Unknown")
            intent_dist[i] = intent_dist.get(i, 0) + 1
            d = q.get("difficulty", "Unknown")
            diff_dist[d] = diff_dist.get(d, 0) + 1
            t = q.get("question_type", "Unknown")
            type_dist[t] = type_dist.get(t, 0) + 1
            tc = q.get("technology", "Unknown")
            tech_dist[tc] = tech_dist.get(tc, 0) + 1
            tp = q.get("topic", "Unknown")
            topic_dist[tp] = topic_dist.get(tp, 0) + 1

    rejected = len(generated_questions) - accepted

    # Update the remaining gaps metric from Phase 4c
    # We generated `accepted` questions, so the remaining gaps ideally decrease by `accepted`.
    remaining_count = 3711 - accepted

    report = {
        "Existing verified questions": 1730,
        "Generated questions attempted": attempted,
        "Generated questions accepted": accepted,
        "Generated questions rejected": rejected,
        "Final staged question count": 1730 + accepted,
        "Questions by role (New)": role_dist,
        "Questions by skill (New)": skill_dist,
        "Questions by technology (New)": tech_dist,
        "Questions by topic (New)": topic_dist,
        "Questions by intent (New)": intent_dist,
        "Questions by difficulty (New)": diff_dist,
        "Questions by question type (New)": type_dist,
        "Remaining gaps": "Updated in subsequent Phase 4C runs",
        "Remaining gap count": remaining_count,
        "Top remaining gaps": "Priority 2 and below",
        "API calls used": len(batch),
        "Failed API calls": sum(1 for res, c in results if not res.get("questions")),
        "Sources used": ["Gemini_Phase4D_Batch1"],
        "Duplicate count": rejected,
        "Technical rejection count": 0
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_quality_report.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    for k, v in report.items():
        print(f"{k}: {v}")

def main():
    asyncio.run(process_batch())

if __name__ == "__main__":
    main()
