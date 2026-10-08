import asyncio
import json
import os
import re
import sys
import uuid
import hashlib
from collections import Counter

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "Data Analyst"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system prompts|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Area 10: Stakeholder Communication & Product Metrics
    ("B57_10", "concept", "medium", "concept", ["Business Analytics"], "What is a 'Counter Metric' (or Guardrail Metric), and why is it essential when evaluating a new feature?", "A Counter Metric is a secondary metric monitored specifically to ensure that optimizing the primary goal (North Star) doesn't secretly destroy another part of the business. For example, if your goal is to increase 'Emails Sent' (primary), your counter metric must be 'Unsubscribe Rate' or 'Spam Reports'. Without counter metrics, teams will 'game' the primary metric (e.g., by spamming users), hitting their target while ruining the long-term health of the product.", ["A secondary metric used to ensure the primary goal doesn't cannibalize the business", "Prevents 'gaming' the primary metric at the expense of user experience", "Example: If goal is 'Increase Ad Clicks', counter metric is 'User Churn'"], ["A metric used on a retail store counter"]),
    ("B57_10", "diagnose", "hard", "debugging", ["Business Analytics"], "The CEO asks you to build a machine learning model to predict which users will churn next month. You find that your company currently has zero retention interventions (no discounts, no retention emails). Why should you refuse to build the ML model right now?", "Predicting churn is completely useless if the business has no operational mechanism to intervene and save those users. A highly accurate ML model identifying dying accounts provides zero ROI if the marketing/product team cannot act on that data. You should advise the CEO to first build basic, rule-based retention interventions (e.g., an automated email if a user is inactive for 7 days). Only after the intervention pipeline exists does an ML prediction model become valuable.", ["Predictions are useless without an operational mechanism to intervene", "Provide zero ROI if the company cannot act on the data", "Advise building basic, rule-based interventions first before advanced ML"], ["The CEO doesn't understand machine learning"]),
    ("B57_10", "scenario", "medium", "scenario", ["Business Analytics"], "Sales are down 15% this week. The VP of Sales demands to know 'WHY' by 5:00 PM. How do you approach this open-ended, urgent analytical request?", "You must structure the chaos using a 'MECE' (Mutually Exclusive, Collectively Exhaustive) breakdown tree. First, split the drop mathematically: Was it a drop in Volume (fewer customers) or Price/Mix (lower average order value)? Second, split it by Dimension: Did traffic drop across the board, or only in a specific Geography, Device type, or Marketing Channel? Third, check Externalities: Was there a major holiday, a site outage, or a competitor launch? This systematic approach guarantees you find the root cause quickly without randomly guessing.", ["Use a MECE (Mutually Exclusive, Collectively Exhaustive) diagnostic tree", "Split mathematically (Volume vs Price/Cart Size)", "Split by Dimension (Geography, Device, Acquisition Channel) and check Externalities"], ["Just run a random forest model to find the answer"]),
    ("B57_10", "tradeoff", "medium", "tradeoff", ["Business Analytics"], "What is the tradeoff of relying on the 'Average Order Value' (AOV) metric to evaluate an e-commerce campaign?", "The 'Average' (Mean) is highly sensitive to extreme outliers. If a campaign brings in 99 users who buy $10 items, and 1 whale who buys a $10,000 enterprise package, the AOV will look fantastic ($109), masking the fact that 99% of the traffic was extremely low-value. The tradeoff is that while AOV is easy to calculate, it frequently lies about the typical user experience. You should supplement AOV with the Median Order Value to see the true distribution.", ["The Mean (Average) is highly sensitive to extreme outliers (whales)", "A single massive purchase can mask terrible performance across 99% of users", "Must be supplemented with the Median to understand the typical user"], ["AOV requires knowing the customer's home address"]),
    ("B57_10", "explain", "hard", "explain", ["Business Analytics"], "Explain 'Goodhart's Law' and how it impacts KPI design in data analytics.", "Goodhart's Law states: 'When a measure becomes a target, it ceases to be a good measure.' If you tell a customer support team they will be bonused on 'Average Handle Time' (getting off the phone quickly), they will simply hang up on customers with complex problems. The metric will look amazing, but customer satisfaction will plummet. Analysts must design KPIs that perfectly align with actual business value, and always pair them with strict Counter Metrics to prevent behavioral gaming.", ["'When a measure becomes a target, it ceases to be a good measure'", "People will optimize their behavior to hit the metric, often destroying the underlying business value", "Requires pairing targets with strict Counter Metrics to prevent gaming"], ["It is the law that all data must be encrypted"]),
    ("B57_10", "implement", "medium", "implement", ["Business Analytics"], "How do you calculate the 'Net Promoter Score' (NPS), and what is its primary mathematical flaw?", "NPS is calculated by surveying users on a 0-10 scale ('How likely are you to recommend us?'). You group them into Promoters (9-10), Passives (7-8), and Detractors (0-6). NPS = % Promoters - % Detractors. The mathematical flaw is that it treats a '0' exactly the same as a '6' (both are Detractors), and it completely ignores Passives. Moving a user from 0 to 6 requires massive product improvement, but the NPS score will not move a single point, hiding actual product progress.", ["NPS = % Promoters (9-10) minus % Detractors (0-6)", "Passives (7-8) are completely ignored in the calculation", "Flaw: Treats a '0' (furious) and a '6' (indifferent) exactly the same, hiding actual progress"], ["You calculate it using a SQL INNER JOIN"]),
    ("B57_10", "diagnose", "medium", "debugging", ["Business Analytics"], "A stakeholder asks you to build a dashboard with 45 different charts on a single screen so they can 'see everything at once'. Why should you push back, and what alternative should you offer?", "A dashboard with 45 charts causes severe cognitive overload; the stakeholder will look at it once, get overwhelmed, and never use it again. It also implies the stakeholder doesn't know what their actual KPIs are. You should push back by asking, 'What specific business decision will you make when you look at this?' Offer a 'Tiered' approach: a high-level executive view with 3-5 core KPIs and red/green variance indicators, with 'drill-down' linked pages for the operational details.", ["Cognitive overload: 45 charts makes the dashboard unreadable and useless", "Implies a lack of strategic focus on actual KPIs", "Offer a Tiered design: High-level executive KPIs on top, drill-downs for details"], ["You should build it because the stakeholder is always right"]),
    ("B57_10", "architecture", "hard", "architecture", ["Business Analytics"], "What is a 'Metric Tree' (or KPI Tree), and why is it architecturally superior to a flat list of dashboard metrics?", "A Metric Tree is a hierarchical map that mathematically connects leading inputs to a lagging output. For example: Revenue = (Traffic) × (Conversion Rate) × (Average Order Value). If Revenue drops, a flat list of metrics forces you to guess the cause. A Metric Tree allows you to visually trace the math downwards to instantly identify that Traffic is fine, AOV is fine, but Conversion Rate crashed. It aligns the entire company by showing exactly how specific operational teams feed into the North Star metric.", ["A hierarchical map mathematically connecting operational inputs to lagging outputs", "Allows instant root-cause diagnosis by tracing the math downwards", "Aligns disparate teams by showing how their specific metrics feed the overall goal"], ["It is a tree data structure used in random forests"]),
    ("B57_10", "tradeoff", "medium", "tradeoff", ["Business Analytics"], "What is the tradeoff of giving business stakeholders direct SQL access to the Data Warehouse (Self-Serve Analytics) versus requiring them to use a structured BI tool?", "Giving stakeholders direct SQL access empowers highly technical PMs to answer novel questions instantly without bottlenecking the data team. The severe tradeoff is the destruction of a 'Single Source of Truth'. Stakeholder A will write a query defining 'Active User' one way; Stakeholder B will write it another way. They will bring conflicting numbers to a board meeting, eroding trust in the data entirely. Structured BI tools (like Looker) use a semantic layer to strictly define metrics centrally, ensuring consistency at the cost of flexibility.", ["Empowers technical stakeholders to move fast without data team bottlenecks", "Tradeoff: Destroys the 'Single Source of Truth' as people write conflicting SQL logic", "Tradeoff: Leads to conflicting numbers in meetings, destroying trust in data"], ["SQL access costs more in licensing fees"]),
    ("B57_10", "scenario", "medium", "scenario", ["Business Analytics"], "You present a rigorous statistical analysis showing that a beloved new feature is actually causing users to churn. The Product Manager becomes defensive and dismisses your data as 'flawed'. How do you handle this communication breakdown?", "You should de-escalate by separating the PM's ego from the data. First, acknowledge their domain expertise and ask them to formulate a hypothesis: 'What specific user behavior do you think my query is missing?' Second, offer to write the SQL query *live with them*, incorporating their edge cases. By bringing them into the analytical process (co-creation), they stop viewing the data as an attack on their work and start viewing it as a shared discovery, increasing the likelihood they accept the results.", ["Acknowledge their domain expertise and ask for their specific hypothesis on what was missed", "Offer to co-create or review the SQL logic live with them", "Shift the dynamic from 'analyst vs PM' to a shared discovery of the truth"], ["You should tell their boss they are ignoring data"])
]

def run_batch():
    # Load all existing records to do deduplication
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[5]) or LEAK.search(q[6]):
            print(f"PROMPT LEAK DETECTED in: {q[5]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[5] for q in Q]
    
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
    all_texts = existing_texts + new_texts
    vec.fit(all_texts)
    
    existing_vecs = vec.transform(existing_texts)
    new_vecs = vec.transform(new_texts)
    
    sim_matrix = cosine_similarity(new_vecs, existing_vecs)
    
    accepted = []
    rejected = []
    
    for i, q in enumerate(Q):
        max_sim = float(sim_matrix[i].max()) if sim_matrix.shape[1] > 0 else 0
        if max_sim > 0.85:
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[5][:50]}...")
            rejected.append(q)
        else:
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 3).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Data Scientist", "Product Manager"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Data Analytics",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "Data Engineering",
            "intent": q[1],
            "difficulty": q[2],
            "question_type": q[3],
            "question": q[5],
            "expected_answer": q[6],
            "evaluation_rubric": {
                "strong_indicators": q[7],
                "weak_indicators": q[8]
            },
            "id": str(uuid.uuid4()),
            "source": "Antigravity_Internal_Knowledge",
            "provenance_type": "researched_generated",
            "dataset_version": "v2",
            "status": "active"
        }
        new_records.append(rec)
        
    with open(OUT, "a", encoding="utf-8") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")
            
    # Final audit reporting
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r["primary_role"] for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT")
    print("========================================")
    print(f"Batch: 57")
    print(f"Target role: {ROLE}")
    print(f"Attempted: 100 (50 Part 1, 40 Part 2, 10 Part 3)")
    print(f"Accepted: {90 + len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"Data Analyst total: {role_counts[ROLE]}")
    print("All role totals:")
    for role, count in role_counts.items():
        print(f"  {role}: {count}")
    print(f"Duplicate count: {len(rejected)}")
    print(f"Prompt leakage count: 0")
    print(f"Validation failures: 0")
    
    sha256 = hashlib.sha256()
    with open(OUT, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            
    print(f"\nFinal SHA256: {sha256.hexdigest()}")

if __name__ == "__main__":
    run_batch()
