import json
import os
import sys
from collections import defaultdict, Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

TARGET_ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
    "Machine Learning Engineer", "Full Stack Developer"
]

FINAL_TAXONOMY = {
    "Python Developer": {
        "Python Core": {"Data Structures": ["Lists vs Tuples", "Dicts", "Sets"], "Functions": ["Closures", "Decorators", "Generators"], "OOP": ["Inheritance", "Metaclasses", "Dunder Methods"], "Memory": ["GC", "GIL"]},
        "Concurrency": {"AsyncIO": ["Event Loop", "Coroutines"], "Multithreading": ["Threading", "Locks"], "Multiprocessing": ["Processes", "IPC"]},
        "Web Frameworks": {"FastAPI": ["Dependency Injection", "Pydantic", "Routers"], "Django": ["ORM", "Middleware", "Signals"], "Flask": ["Contexts", "Blueprints"]},
        "Testing & QA": {"pytest": ["Fixtures", "Mocking", "Parametrization"]},
        "Performance": {"Profiling": ["cProfile", "Memory Profiler"], "Optimization": ["Cython", "Vectorization"]}
    },
    "Frontend Developer": {
        "JavaScript": {"Core JS": ["Closures", "Event Loop", "Promises", "Types"], "Browser APIs": ["DOM", "Web Workers", "Storage"], "Performance": ["Debouncing", "Throttling"]},
        "React": {"State Management": ["Hooks", "Redux", "Context"], "Rendering": ["VDOM", "Concurrent Mode", "SSR"], "Performance": ["Memoization", "Code Splitting"]},
        "HTML/CSS": {"Layouts": ["Flexbox", "Grid"], "Accessibility": ["ARIA", "Semantics"], "Performance": ["Critical Rendering Path"]},
        "Web Security": {"Security": ["XSS", "CSRF", "CORS", "CSP"]},
        "Testing": {"Jest/RTL": ["Unit Tests", "Component Tests"]}
    },
    "Java Developer": {
        "Java Core": {"Collections": ["HashMap", "ConcurrentHashMap", "Lists"], "Memory": ["Garbage Collection", "JVM Internals"], "OOP": ["Interfaces", "Polymorphism"]},
        "Concurrency": {"Multithreading": ["Executors", "Locks", "ThreadLocal", "Volatile"]},
        "Spring Framework": {"Spring Boot": ["Auto-configuration", "Actuator"], "Spring MVC": ["Controllers", "Filters"], "Spring Data": ["JPA", "Transactions"]},
        "Testing": {"JUnit/Mockito": ["Unit Testing", "Mocking"]}
    },
    "Database Developer": {
        "Relational Databases": {"PostgreSQL": ["Indexing", "VACUUM", "MVCC"], "MySQL": ["InnoDB", "Replication"], "SQL": ["Window Functions", "Joins", "CTEs"]},
        "NoSQL Databases": {"MongoDB": ["Aggregation", "Sharding"], "Redis": ["Data Structures", "Persistence", "Eviction"]},
        "Architecture & Design": {"Data Modeling": ["Normalization", "Denormalization"], "Scaling": ["Sharding", "Replication", "Partitioning"]},
        "Optimization": {"Query Tuning": ["Execution Plans", "Index Strategies"]}
    },
    "DevOps / Cloud Engineer": {
        "Cloud Providers": {"AWS": ["EC2", "S3", "VPC", "IAM", "EKS", "Lambda"]},
        "Containerization": {"Docker": ["Images", "Networking", "Security"], "Kubernetes": ["Pods", "Deployments", "Services", "Ingress", "StatefulSets"]},
        "CI/CD": {"GitHub Actions / GitLab CI": ["Pipelines", "Runners"], "Jenkins": ["Declarative Pipelines"]},
        "Infrastructure as Code": {"Terraform": ["State", "Modules", "Providers"]},
        "Linux & Networking": {"Linux Core": ["Processes", "File Systems", "Permissions"], "Networking": ["TCP/IP", "DNS", "Load Balancing"]},
        "Observability": {"Monitoring": ["Prometheus", "Grafana", "Logging"]}
    },
    "Backend Developer": {
        "API Design": {"REST": ["Verbs", "Status Codes", "Pagination"], "GraphQL": ["Resolvers", "N+1 Problem"], "gRPC": ["Protobufs", "Streaming"]},
        "Microservices": {"Architecture": ["Saga Pattern", "Event Sourcing", "Service Discovery"], "Communication": ["Message Queues", "Event Driven"]},
        "Caching": {"Strategies": ["Write-through", "Cache Aside", "Eviction"], "Tools": ["Redis", "Memcached"]},
        "Databases": {"SQL & NoSQL": ["Transactions", "ACID", "CAP Theorem", "Connection Pooling"]},
        "Security": {"Authentication": ["JWT", "OAuth2", "Sessions"], "Authorization": ["RBAC", "ABAC"]}
    },
    "Data Analyst": {
        "SQL": {"Advanced Queries": ["Window Functions", "CTEs", "Subqueries"], "Performance": ["Query Tuning"]},
        "Data Visualization": {"Tools": ["Tableau", "PowerBI"], "Concepts": ["Chart Selection", "Dashboard Design"]},
        "Statistics": {"Probability": ["Distributions", "A/B Testing", "Hypothesis Testing"]},
        "Python/R": {"Pandas": ["Data Manipulation", "Aggregations", "Cleaning"]}
    },
    "AI Engineer": {
        "LLMs": {"Architecture": ["Transformers", "Attention"], "Prompting": ["Few-shot", "Chain of Thought", "Zero-shot"]},
        "RAG": {"Components": ["Vector DBs", "Embeddings", "Retrieval Strategies", "Chunking"]},
        "AI Agents": {"Orchestration": ["LangChain", "LlamaIndex", "Tool Use"]},
        "MLOps for LLMs": {"Deployment": ["Serving", "Quantization", "Monitoring"]}
    },
    "Machine Learning Engineer": {
        "ML Algorithms": {"Supervised": ["Trees", "Linear Models", "SVM"], "Unsupervised": ["Clustering", "PCA"]},
        "Deep Learning": {"Architectures": ["CNN", "RNN", "Transformers"], "Optimization": ["Gradient Descent", "Loss Functions", "Regularization"]},
        "Model Training": {"Process": ["Cross Validation", "Hyperparameter Tuning", "Overfitting"]},
        "MLOps": {"Pipelines": ["Data Drift", "Model Registry", "Feature Store", "Serving"]}
    },
    "Full Stack Developer": {
        "Frontend": {"Frameworks": ["React / Vue / Angular"], "Core": ["HTML/CSS/JS"]},
        "Backend": {"APIs": ["REST / GraphQL"], "Frameworks": ["Node.js / Python / Java"]},
        "Databases": {"SQL / NoSQL": ["Modeling", "Querying"]},
        "Architecture": {"System Design": ["Scalability", "Security", "Deployment"]}
    }
}

SKILL_PRIORITIES = {}
for role, skills in FINAL_TAXONOMY.items():
    SKILL_PRIORITIES[role] = {}
    skill_list = list(skills.keys())
    for i, s in enumerate(skill_list):
        if i < 2: SKILL_PRIORITIES[role][s] = "CORE"
        elif i < 4: SKILL_PRIORITIES[role][s] = "IMPORTANT"
        else: SKILL_PRIORITIES[role][s] = "SECONDARY"

def main():
    dataset_file = os.path.join(DATA_DIR, "curated_question_bank_v1.jsonl")
    current_questions = []
    if os.path.exists(dataset_file):
        with open(dataset_file, "r", encoding="utf-8") as f:
            for line in f:
                current_questions.append(json.loads(line))
    
    role_counts = Counter()
    skill_counts = Counter()
    intent_counts = Counter()
    diff_counts = Counter()
    
    role_skill_topic_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    role_intent_counts = defaultdict(lambda: defaultdict(int))
    role_diff_counts = defaultdict(lambda: defaultdict(int))
    
    for q in current_questions:
        for r in q["applicable_roles"]:
            if r not in TARGET_ROLES: continue
            role_counts[r] += 1
            s = q["primary_skill"]
            skill_counts[s] += 1
            intent = q["intent"]
            diff = q["difficulty"]
            
            intent_counts[intent] += 1
            diff_counts[diff] += 1
            
            role_skill_topic_counts[r][s][q["topic"]] += 1
            role_intent_counts[r][intent] += 1
            role_diff_counts[r][diff] += 1
            
    TARGET_PER_ROLE = 500
    
    INTENT_TARGET_PCT = {
        "fundamentals": 0.15, "explain": 0.15, "implement": 0.15, "compare": 0.10,
        "debug": 0.10, "tradeoff": 0.10, "scenario": 0.10, "architecture": 0.05,
        "design": 0.05, "optimize": 0.03, "diagnose": 0.02
    }
    
    DIFF_TARGET_PCT = { "easy": 0.30, "medium": 0.45, "hard": 0.25 }
    
    generation_blueprint = []
    role_targets = []
    matrix = {}
    
    total_target_questions = 0
    
    for r in TARGET_ROLES:
        curr_role_count = role_counts[r]
        skills = FINAL_TAXONOMY[r]
        total_weight = sum([3 if SKILL_PRIORITIES[r][s] == "CORE" else (2 if SKILL_PRIORITIES[r][s] == "IMPORTANT" else 1) for s in skills])
        
        r_intent_gaps = {}
        for i, pct in INTENT_TARGET_PCT.items():
            t_count = int(TARGET_PER_ROLE * pct)
            c_count = role_intent_counts[r][i]
            r_intent_gaps[i] = max(0, t_count - c_count)
            
        r_diff_gaps = {}
        for d, pct in DIFF_TARGET_PCT.items():
            t_count = int(TARGET_PER_ROLE * pct)
            c_count = role_diff_counts[r][d]
            r_diff_gaps[d] = max(0, t_count - c_count)
            
        r_skill_gaps = {}
        matrix[r] = {}
        
        for s in skills:
            weight = 3 if SKILL_PRIORITIES[r][s] == "CORE" else (2 if SKILL_PRIORITIES[r][s] == "IMPORTANT" else 1)
            t_count = int(TARGET_PER_ROLE * (weight / total_weight))
            total_target_questions += t_count
            
            c_count = sum(role_skill_topic_counts[r][s].values()) if s in role_skill_topic_counts[r] else 0
            gap = max(0, t_count - c_count)
            r_skill_gaps[s] = gap
            
            matrix[r][s] = {
                "CURRENT": c_count, "TARGET": t_count, "GAP": gap,
                "EASY_TARGET": int(t_count * 0.30), "MEDIUM_TARGET": int(t_count * 0.45), "HARD_TARGET": int(t_count * 0.25),
                "INTENT_TARGETS": {k: int(t_count * v) for k, v in INTENT_TARGET_PCT.items()}
            }
            
            if gap > 0:
                generation_blueprint.append({
                    "role": r, "skill": s,
                    "technology": list(skills[s].keys())[0] if skills[s] else None,
                    "topic": "Assorted", "intent": "Assorted", "difficulty": "Assorted",
                    "question_type": "Assorted", "current_count": c_count, "target_count": t_count,
                    "generation_gap": gap,
                    "priority": "CRITICAL" if SKILL_PRIORITIES[r][s] == "CORE" and c_count < 10 else "HIGH",
                    "source_strategy": "open_source_first" if r in ["Frontend Developer", "DevOps / Cloud Engineer"] else "generation_if_needed"
                })

        role_targets.append({
            "ROLE": r, "CURRENT": curr_role_count, "TARGET": TARGET_PER_ROLE,
            "GAP": max(0, TARGET_PER_ROLE - curr_role_count),
            "CORE_SKILLS": [s for s, p in SKILL_PRIORITIES[r].items() if p == "CORE"],
            "CORE_SKILL_GAPS": {s: r_skill_gaps[s] for s, p in SKILL_PRIORITIES[r].items() if p == "CORE"},
            "INTENT_GAPS": r_intent_gaps, "DIFFICULTY_GAPS": r_diff_gaps
        })
        
    with open(os.path.join(REPORTS_DIR, "phase4_final_role_skill_taxonomy.json"), "w") as f: json.dump(FINAL_TAXONOMY, f, indent=2)
    tax_md = "# Phase 4: Final Role -> Skill -> Technology Taxonomy\n\n"
    for r, skills in FINAL_TAXONOMY.items():
        tax_md += f"## {r}\n"
        for s, techs in skills.items():
            tax_md += f"- **{s}** ({SKILL_PRIORITIES[r][s]})\n"
            for t, topics in techs.items(): tax_md += f"  - *{t}*: {', '.join(topics)}\n"
        tax_md += "\n"
    with open(os.path.join(REPORTS_DIR, "phase4_final_role_skill_taxonomy.md"), "w") as f: f.write(tax_md)
    
    with open(os.path.join(REPORTS_DIR, "phase4_role_targets.json"), "w") as f: json.dump(role_targets, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4_role_skill_question_matrix.json"), "w") as f: json.dump(matrix, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4_intent_targets.json"), "w") as f: json.dump(INTENT_TARGET_PCT, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4_difficulty_targets.json"), "w") as f: json.dump(DIFF_TARGET_PCT, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4_generation_blueprint.json"), "w") as f: json.dump({"blueprint": generation_blueprint}, f, indent=2)
    
    sac = {
        "sources": [
            {"name": "Existing Supabase dataset", "can_yield": len(current_questions), "status": "Acquired"},
            {"name": "OSS GitHub Repos (e.g. awesome-interview-questions)", "can_yield": 1500, "status": "To Scrape/Curate"},
            {"name": "Official Tech Documentation (AWS, React, etc.)", "can_yield": 500, "status": "To Extract"},
            {"name": "Generated Content (Gemini)", "can_yield": max(0, total_target_questions - len(current_questions) - 2000), "status": "Last Resort"}
        ]
    }
    with open(os.path.join(REPORTS_DIR, "phase4_source_acquisition_plan.json"), "w") as f: json.dump(sac, f, indent=2)
    
    expansion_md = f"# Phase 4 Dataset Expansion Plan\n\n## 1. Overview\nCurrent Accepted Questions: {len(current_questions)}\nTarget Canonical Questions: {total_target_questions}\nEstimated Gap: {max(0, total_target_questions - len(current_questions))}\n\n## 2. Source Strategy\nWe will NOT blindly generate questions.\n1. **Existing Source Extraction**: Fully utilized. Yielded {len(current_questions)}.\n2. **Open-Source Question Repositories**: Expected yield ~1500.\n3. **High-Quality Technical Documentation**: Expected yield ~500.\n4. **AI Generation**: Expected yield ~{max(0, total_target_questions - len(current_questions) - 2000)}.\n"
    with open(os.path.join(REPORTS_DIR, "phase4_dataset_expansion_plan.md"), "w") as f: f.write(expansion_md)
    
    # OUTPUT REPORTING FOR AGENT
    print(f"1. Final skill list for every role: {json.dumps({r: list(v.keys()) for r,v in FINAL_TAXONOMY.items()})}")
    print(f"2. Current questions per role: {json.dumps(dict(role_counts))}")
    print(f"3. Target questions per role: 500")
    print(f"4. Current questions per skill: {json.dumps(dict(skill_counts))}")
    # 5 is in matrix.json
    print(f"6. Current questions per intent: {json.dumps(dict(intent_counts))}")
    print(f"7. Target questions per intent: {json.dumps(INTENT_TARGET_PCT)}")
    print(f"8. Current questions per difficulty: {json.dumps(dict(diff_counts))}")
    print(f"9. Target questions per difficulty: {json.dumps(DIFF_TARGET_PCT)}")
    print(f"10. Questions recoverable from existing sources: {len(current_questions)}")
    print(f"11. Questions that should be obtained from new sources: ~2000")
    print(f"12. Questions that genuinely require generation: ~{max(0, total_target_questions - len(current_questions) - 2000)}")
    print(f"13. Estimated final dataset size: {total_target_questions}")
    print(f"14. Estimated generated-question count: ~{max(0, total_target_questions - len(current_questions) - 2000)}")

if __name__ == "__main__":
    main()
