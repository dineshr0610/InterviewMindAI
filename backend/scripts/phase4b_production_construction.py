import json
import os
import sys
import re
import csv
import uuid
from collections import defaultdict, Counter
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.services.question_controller import detect_question_intent
from supabase import create_client

load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

TARGET_ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer", "Database Developer",
    "DevOps / Cloud Engineer", "Backend Developer", "Data Analyst", "AI Engineer",
    "Machine Learning Engineer", "Full Stack Developer"
]

DEEP_TAXONOMY = {
    "Python Developer": {
        "Python Fundamentals": {"priority": "CORE", "tech": ["Python"], "topics": ["Data Types", "Variables"]},
        "Functions & Functional Programming": {"priority": "CORE", "tech": ["Python"], "topics": ["Closures", "Decorators"]},
        "OOP": {"priority": "CORE", "tech": ["Python"], "topics": ["Inheritance", "Metaclasses"]},
        "Data Structures": {"priority": "CORE", "tech": ["Python"], "topics": ["Lists", "Dicts", "Sets"]},
        "Algorithms": {"priority": "IMPORTANT", "tech": ["Python"], "topics": ["Sorting", "Graph"]},
        "Iterators & Generators": {"priority": "IMPORTANT", "tech": ["Python"], "topics": ["yield", "itertools"]},
        "Exceptions": {"priority": "IMPORTANT", "tech": ["Python"], "topics": ["Custom Exceptions", "Handling"]},
        "Modules & Packaging": {"priority": "SECONDARY", "tech": ["Python"], "topics": ["pip", "venv"]},
        "Memory Management": {"priority": "CORE", "tech": ["Python"], "topics": ["GC", "GIL"]},
        "Concurrency": {"priority": "CORE", "tech": ["Python"], "topics": ["Multithreading", "Multiprocessing"]},
        "AsyncIO": {"priority": "CORE", "tech": ["Python"], "topics": ["Event Loop", "Coroutines"]},
        "Testing": {"priority": "IMPORTANT", "tech": ["pytest"], "topics": ["Mocking", "Fixtures"]},
        "Performance": {"priority": "IMPORTANT", "tech": ["Python"], "topics": ["Profiling", "Cython"]},
        "APIs": {"priority": "IMPORTANT", "tech": ["REST"], "topics": ["Design"]},
        "FastAPI": {"priority": "IMPORTANT", "tech": ["FastAPI"], "topics": ["Dependency Injection"]},
        "Django": {"priority": "SECONDARY", "tech": ["Django"], "topics": ["ORM", "Middleware"]},
        "SQL": {"priority": "IMPORTANT", "tech": ["SQL"], "topics": ["Queries"]},
        "PostgreSQL": {"priority": "SECONDARY", "tech": ["PostgreSQL"], "topics": ["Indexing"]},
        "ORMs": {"priority": "IMPORTANT", "tech": ["SQLAlchemy"], "topics": ["Sessions"]},
        "Security": {"priority": "IMPORTANT", "tech": ["Python"], "topics": ["Injection", "Auth"]},
        "Deployment": {"priority": "SECONDARY", "tech": ["Docker"], "topics": ["Containers"]},
        "Observability": {"priority": "SECONDARY", "tech": ["Prometheus"], "topics": ["Metrics"]},
        "Architecture": {"priority": "CORE", "tech": ["Python"], "topics": ["Microservices"]},
        "System Design": {"priority": "IMPORTANT", "tech": ["Python"], "topics": ["Scalability"]},
        "Debugging": {"priority": "CORE", "tech": ["Python"], "topics": ["pdb", "Tracing"]}
    },
    "Frontend Developer": {
        "HTML/DOM": {"priority": "CORE", "tech": ["HTML"], "topics": ["Semantics", "Accessibility"]},
        "CSS & Styling": {"priority": "CORE", "tech": ["CSS"], "topics": ["Flexbox", "Grid"]},
        "Core JavaScript": {"priority": "CORE", "tech": ["JavaScript"], "topics": ["Closures", "Event Loop"]},
        "Browser APIs": {"priority": "IMPORTANT", "tech": ["JavaScript"], "topics": ["Storage", "Workers"]},
        "React Fundamentals": {"priority": "CORE", "tech": ["React"], "topics": ["JSX", "Components"]},
        "React Hooks": {"priority": "CORE", "tech": ["React"], "topics": ["useEffect", "Custom Hooks"]},
        "State Management": {"priority": "CORE", "tech": ["Redux", "Context"], "topics": ["Global State"]},
        "Component Architecture": {"priority": "IMPORTANT", "tech": ["React"], "topics": ["Design Patterns"]},
        "Performance Optimization": {"priority": "CORE", "tech": ["JavaScript", "React"], "topics": ["Memoization", "Code Splitting"]},
        "Web Security": {"priority": "CORE", "tech": ["Security"], "topics": ["XSS", "CSRF", "CORS"]},
        "Testing (Jest/RTL)": {"priority": "IMPORTANT", "tech": ["Jest"], "topics": ["Unit", "E2E"]},
        "Build Tools": {"priority": "SECONDARY", "tech": ["Webpack", "Vite"], "topics": ["Bundling"]},
        "TypeScript": {"priority": "IMPORTANT", "tech": ["TypeScript"], "topics": ["Types", "Interfaces"]},
        "Network Requests": {"priority": "IMPORTANT", "tech": ["JavaScript"], "topics": ["Fetch", "Axios"]},
        "Routing": {"priority": "SECONDARY", "tech": ["React Router"], "topics": ["SPA Routing"]},
        "SSR / SSG": {"priority": "IMPORTANT", "tech": ["Next.js"], "topics": ["Server Rendering"]},
        "PWA": {"priority": "SECONDARY", "tech": ["Web"], "topics": ["Service Workers"]},
        "Debugging Tools": {"priority": "CORE", "tech": ["DevTools"], "topics": ["Profiling", "Network"]}
    },
    "Java Developer": {
        "Java Core": {"priority": "CORE", "tech": ["Java"], "topics": ["Types", "OOP"]},
        "Collections Framework": {"priority": "CORE", "tech": ["Java"], "topics": ["Map", "List"]},
        "Memory Management": {"priority": "CORE", "tech": ["Java"], "topics": ["GC", "JVM"]},
        "Concurrency": {"priority": "CORE", "tech": ["Java"], "topics": ["Threads", "Executors"]},
        "Streams API": {"priority": "IMPORTANT", "tech": ["Java"], "topics": ["Lambdas", "Streams"]},
        "Spring Core": {"priority": "CORE", "tech": ["Spring"], "topics": ["IoC", "AOP"]},
        "Spring Boot": {"priority": "CORE", "tech": ["Spring Boot"], "topics": ["Auto-config"]},
        "Spring Data JPA": {"priority": "IMPORTANT", "tech": ["Hibernate"], "topics": ["Entities", "Transactions"]},
        "Spring Security": {"priority": "IMPORTANT", "tech": ["Spring Security"], "topics": ["Auth", "OAuth2"]},
        "Microservices": {"priority": "IMPORTANT", "tech": ["Java"], "topics": ["Service Discovery"]},
        "Testing": {"priority": "IMPORTANT", "tech": ["JUnit", "Mockito"], "topics": ["Unit Testing"]},
        "Build Tools": {"priority": "SECONDARY", "tech": ["Maven", "Gradle"], "topics": ["Dependencies"]},
        "Design Patterns": {"priority": "IMPORTANT", "tech": ["Java"], "topics": ["Singleton", "Factory"]},
        "Performance Tuning": {"priority": "IMPORTANT", "tech": ["Java"], "topics": ["JProfiler", "GC Tuning"]},
        "Debugging": {"priority": "CORE", "tech": ["Java"], "topics": ["Heap Dumps", "Thread Dumps"]}
    },
    "Database Developer": {
        "SQL Fundamentals": {"priority": "CORE", "tech": ["SQL"], "topics": ["Queries", "Joins"]},
        "Advanced SQL": {"priority": "CORE", "tech": ["SQL"], "topics": ["Window Functions", "CTEs"]},
        "Relational Theory": {"priority": "CORE", "tech": ["RDBMS"], "topics": ["Normalization"]},
        "Indexing": {"priority": "CORE", "tech": ["SQL"], "topics": ["B-Trees", "Hash"]},
        "Query Optimization": {"priority": "CORE", "tech": ["SQL"], "topics": ["Execution Plans", "EXPLAIN"]},
        "Transactions": {"priority": "CORE", "tech": ["SQL"], "topics": ["ACID", "Isolation Levels"]},
        "PostgreSQL": {"priority": "IMPORTANT", "tech": ["PostgreSQL"], "topics": ["MVCC", "VACUUM"]},
        "MySQL": {"priority": "IMPORTANT", "tech": ["MySQL"], "topics": ["InnoDB"]},
        "NoSQL Concepts": {"priority": "IMPORTANT", "tech": ["NoSQL"], "topics": ["CAP Theorem"]},
        "MongoDB": {"priority": "SECONDARY", "tech": ["MongoDB"], "topics": ["Aggregation"]},
        "Redis": {"priority": "SECONDARY", "tech": ["Redis"], "topics": ["Data Structures", "Caching"]},
        "Data Modeling": {"priority": "CORE", "tech": ["DB Design"], "topics": ["Schemas"]},
        "Scaling Databases": {"priority": "IMPORTANT", "tech": ["Architecture"], "topics": ["Sharding", "Replication"]},
        "Security": {"priority": "IMPORTANT", "tech": ["SQL"], "topics": ["SQL Injection", "Roles"]},
        "Backups & Recovery": {"priority": "SECONDARY", "tech": ["SQL"], "topics": ["WAL", "PITR"]}
    },
    "DevOps / Cloud Engineer": {
        "Linux Core": {"priority": "CORE", "tech": ["Linux"], "topics": ["Processes", "File Systems"]},
        "Bash Scripting": {"priority": "IMPORTANT", "tech": ["Bash"], "topics": ["Scripts", "Pipes"]},
        "Networking": {"priority": "CORE", "tech": ["Networking"], "topics": ["TCP/IP", "DNS", "Load Balancing"]},
        "Docker": {"priority": "CORE", "tech": ["Docker"], "topics": ["Images", "Containers", "Networks"]},
        "Kubernetes Core": {"priority": "CORE", "tech": ["Kubernetes"], "topics": ["Pods", "Deployments", "Services"]},
        "Kubernetes Adv": {"priority": "IMPORTANT", "tech": ["Kubernetes"], "topics": ["StatefulSets", "Operators", "RBAC"]},
        "AWS Compute": {"priority": "CORE", "tech": ["AWS"], "topics": ["EC2", "Lambda"]},
        "AWS Networking": {"priority": "CORE", "tech": ["AWS"], "topics": ["VPC", "Route53"]},
        "AWS Storage": {"priority": "IMPORTANT", "tech": ["AWS"], "topics": ["S3", "EBS"]},
        "AWS IAM": {"priority": "CORE", "tech": ["AWS"], "topics": ["Policies", "Roles"]},
        "Terraform": {"priority": "CORE", "tech": ["Terraform"], "topics": ["State", "Modules"]},
        "CI/CD Pipelines": {"priority": "CORE", "tech": ["CI/CD"], "topics": ["GitHub Actions", "GitLab"]},
        "Jenkins": {"priority": "SECONDARY", "tech": ["Jenkins"], "topics": ["Pipelines"]},
        "Git": {"priority": "IMPORTANT", "tech": ["Git"], "topics": ["Workflows", "Hooks"]},
        "Monitoring": {"priority": "CORE", "tech": ["Prometheus", "Grafana"], "topics": ["Metrics", "Alerting"]},
        "Logging": {"priority": "IMPORTANT", "tech": ["ELK", "Splunk"], "topics": ["Aggregation"]},
        "Security": {"priority": "IMPORTANT", "tech": ["Security"], "topics": ["Secrets Management"]}
    },
    "Backend Developer": {
        "API Design": {"priority": "CORE", "tech": ["REST"], "topics": ["Endpoints", "Status Codes"]},
        "GraphQL": {"priority": "IMPORTANT", "tech": ["GraphQL"], "topics": ["Resolvers", "Schemas"]},
        "Language Core": {"priority": "CORE", "tech": ["Python", "Java", "Go"], "topics": ["Concurrency", "OOP"]},
        "Database Integration": {"priority": "CORE", "tech": ["SQL"], "topics": ["ORMs", "Connection Pooling"]},
        "Caching Strategies": {"priority": "CORE", "tech": ["Redis", "Memcached"], "topics": ["Eviction", "Write-through"]},
        "Microservices": {"priority": "CORE", "tech": ["Architecture"], "topics": ["Service Discovery", "Resilience"]},
        "Message Queues": {"priority": "IMPORTANT", "tech": ["RabbitMQ", "Kafka"], "topics": ["Pub/Sub", "Event Sourcing"]},
        "Authentication": {"priority": "CORE", "tech": ["Security"], "topics": ["JWT", "OAuth2", "Sessions"]},
        "Authorization": {"priority": "CORE", "tech": ["Security"], "topics": ["RBAC", "ABAC"]},
        "Performance": {"priority": "IMPORTANT", "tech": ["Backend"], "topics": ["Profiling", "Load Testing"]},
        "Security": {"priority": "IMPORTANT", "tech": ["Security"], "topics": ["OWASP", "Encryption"]},
        "Testing": {"priority": "IMPORTANT", "tech": ["Testing"], "topics": ["Integration", "Unit"]},
        "Deployment": {"priority": "SECONDARY", "tech": ["Docker"], "topics": ["Containers"]},
        "System Design": {"priority": "CORE", "tech": ["Architecture"], "topics": ["Scalability", "CAP Theorem"]},
        "Debugging": {"priority": "CORE", "tech": ["Backend"], "topics": ["Log Analysis", "Tracing"]}
    },
    "Data Analyst": {
        "SQL Basics": {"priority": "CORE", "tech": ["SQL"], "topics": ["Selects", "Joins"]},
        "SQL Advanced": {"priority": "CORE", "tech": ["SQL"], "topics": ["Window Functions", "CTEs"]},
        "Data Visualization": {"priority": "CORE", "tech": ["Tableau", "PowerBI"], "topics": ["Dashboards", "Chart Types"]},
        "Statistics Basics": {"priority": "CORE", "tech": ["Statistics"], "topics": ["Mean", "Median", "Variance"]},
        "Probability": {"priority": "IMPORTANT", "tech": ["Statistics"], "topics": ["Distributions", "Bayes"]},
        "A/B Testing": {"priority": "IMPORTANT", "tech": ["Statistics"], "topics": ["Hypothesis Testing", "P-values"]},
        "Python Pandas": {"priority": "CORE", "tech": ["Python"], "topics": ["DataFrames", "Aggregation"]},
        "Python Data Viz": {"priority": "IMPORTANT", "tech": ["Matplotlib", "Seaborn"], "topics": ["Plotting"]},
        "Data Cleaning": {"priority": "CORE", "tech": ["Data"], "topics": ["Missing Values", "Outliers"]},
        "ETL Concepts": {"priority": "SECONDARY", "tech": ["ETL"], "topics": ["Pipelines"]},
        "Data Modeling": {"priority": "IMPORTANT", "tech": ["Data Warehouse"], "topics": ["Star Schema", "Snowflake"]},
        "Business Intelligence": {"priority": "IMPORTANT", "tech": ["BI"], "topics": ["KPIs", "Metrics"]},
        "Spreadsheets": {"priority": "SECONDARY", "tech": ["Excel"], "topics": ["Pivot Tables", "VLOOKUP"]},
        "Communication": {"priority": "IMPORTANT", "tech": ["Soft Skills"], "topics": ["Storytelling with Data"]},
        "Debugging": {"priority": "IMPORTANT", "tech": ["Data"], "topics": ["Data Quality Audits"]}
    },
    "AI Engineer": {
        "LLM Architecture": {"priority": "CORE", "tech": ["LLMs"], "topics": ["Transformers", "Attention"]},
        "Prompt Engineering": {"priority": "CORE", "tech": ["LLMs"], "topics": ["Zero-shot", "CoT"]},
        "RAG Core": {"priority": "CORE", "tech": ["RAG"], "topics": ["Vector DBs", "Embeddings"]},
        "RAG Advanced": {"priority": "IMPORTANT", "tech": ["RAG"], "topics": ["Re-ranking", "Chunking Strategies"]},
        "AI Agents": {"priority": "CORE", "tech": ["Agents"], "topics": ["Tool Use", "Reasoning Loops"]},
        "LangChain / LlamaIndex": {"priority": "IMPORTANT", "tech": ["LangChain"], "topics": ["Chains", "Memory"]},
        "Fine-tuning": {"priority": "IMPORTANT", "tech": ["LLMs"], "topics": ["PEFT", "LoRA"]},
        "Model Evaluation": {"priority": "CORE", "tech": ["Evaluation"], "topics": ["BLEU", "ROUGE", "LLM-as-a-Judge"]},
        "Vector Databases": {"priority": "IMPORTANT", "tech": ["Pinecone", "Milvus", "pgvector"], "topics": ["Index Types"]},
        "MLOps for LLMs": {"priority": "IMPORTANT", "tech": ["MLOps"], "topics": ["Prompt Management", "Monitoring"]},
        "Deployment": {"priority": "SECONDARY", "tech": ["Serving"], "topics": ["vLLM", "TGI"]},
        "Python": {"priority": "CORE", "tech": ["Python"], "topics": ["API Integrations", "Async"]},
        "Security": {"priority": "IMPORTANT", "tech": ["AI Security"], "topics": ["Prompt Injection", "Jailbreaks"]},
        "Ethics & Bias": {"priority": "SECONDARY", "tech": ["Ethics"], "topics": ["Fairness", "Safety"]},
        "Debugging": {"priority": "CORE", "tech": ["AI"], "topics": ["Hallucination Mitigation"]}
    },
    "Machine Learning Engineer": {
        "Supervised Learning": {"priority": "CORE", "tech": ["ML"], "topics": ["Linear Regression", "Trees", "SVM"]},
        "Unsupervised Learning": {"priority": "CORE", "tech": ["ML"], "topics": ["Clustering", "PCA"]},
        "Deep Learning Fundamentals": {"priority": "CORE", "tech": ["Deep Learning"], "topics": ["Neural Networks", "Backpropagation"]},
        "Computer Vision": {"priority": "IMPORTANT", "tech": ["Deep Learning"], "topics": ["CNNs", "Object Detection"]},
        "NLP": {"priority": "IMPORTANT", "tech": ["NLP"], "topics": ["Word Embeddings", "RNNs"]},
        "Model Evaluation": {"priority": "CORE", "tech": ["ML"], "topics": ["Precision", "Recall", "ROC-AUC"]},
        "Hyperparameter Tuning": {"priority": "IMPORTANT", "tech": ["ML"], "topics": ["Grid Search", "Bayesian Optimization"]},
        "Data Preprocessing": {"priority": "CORE", "tech": ["ML"], "topics": ["Feature Engineering", "Scaling"]},
        "Python ML Ecosystem": {"priority": "CORE", "tech": ["Scikit-learn", "Pandas"], "topics": ["Pipelines"]},
        "Deep Learning Frameworks": {"priority": "IMPORTANT", "tech": ["PyTorch", "TensorFlow"], "topics": ["Tensors", "Training Loops"]},
        "MLOps": {"priority": "CORE", "tech": ["MLOps"], "topics": ["Model Registry", "Data Drift"]},
        "Model Serving": {"priority": "IMPORTANT", "tech": ["Deployment"], "topics": ["ONNX", "TF Serving", "TorchServe"]},
        "Feature Stores": {"priority": "SECONDARY", "tech": ["Architecture"], "topics": ["Online vs Offline"]},
        "Distributed Training": {"priority": "SECONDARY", "tech": ["Architecture"], "topics": ["Data Parallelism"]},
        "Debugging": {"priority": "CORE", "tech": ["ML"], "topics": ["Overfitting", "Vanishing Gradients"]}
    },
    "Full Stack Developer": {
        "Frontend Frameworks": {"priority": "CORE", "tech": ["React", "Vue", "Angular"], "topics": ["Components", "State"]},
        "HTML/CSS/JS": {"priority": "CORE", "tech": ["Web"], "topics": ["DOM", "Styling", "ES6+"]},
        "Backend Frameworks": {"priority": "CORE", "tech": ["Node.js", "Python", "Java"], "topics": ["Routing", "Middleware"]},
        "API Design": {"priority": "CORE", "tech": ["REST", "GraphQL"], "topics": ["Endpoints"]},
        "Databases (SQL)": {"priority": "CORE", "tech": ["SQL"], "topics": ["Queries", "Modeling"]},
        "Databases (NoSQL)": {"priority": "IMPORTANT", "tech": ["MongoDB", "Redis"], "topics": ["Documents", "Caching"]},
        "Authentication": {"priority": "CORE", "tech": ["Security"], "topics": ["JWT", "OAuth"]},
        "Web Security": {"priority": "IMPORTANT", "tech": ["Security"], "topics": ["XSS", "CSRF"]},
        "Deployment": {"priority": "IMPORTANT", "tech": ["Docker", "AWS", "Vercel"], "topics": ["Hosting", "CI/CD"]},
        "System Architecture": {"priority": "CORE", "tech": ["Architecture"], "topics": ["Monolith vs Microservices"]},
        "Performance": {"priority": "IMPORTANT", "tech": ["Full Stack"], "topics": ["Load Time", "Database Indexes"]},
        "Testing": {"priority": "IMPORTANT", "tech": ["Testing"], "topics": ["E2E", "Unit"]},
        "Version Control": {"priority": "IMPORTANT", "tech": ["Git"], "topics": ["Workflows"]},
        "WebSockets": {"priority": "SECONDARY", "tech": ["WebSockets"], "topics": ["Real-time"]},
        "Debugging": {"priority": "CORE", "tech": ["Full Stack"], "topics": ["Network Tab", "Server Logs"]}
    }
}

def fetch_supabase_records():
    import requests
    import time
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")
    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials")
        return []
        
    all_data = []
    limit = 1000
    offset = 0
    url = f"{supabase_url}/rest/v1/document_embeddings?select=id,content,metadata"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }
    
    while True:
        try:
            print(f"Fetching offset {offset}...")
            res = None
            for attempt in range(5):
                try:
                    res = requests.get(url, headers=headers, params={"offset": offset, "limit": limit}, timeout=30)
                    break
                except requests.exceptions.ConnectionError as ce:
                    print(f"Connection error: {ce}. Retrying in 2s...")
                    time.sleep(2)
            if not res or res.status_code != 200:
                print(f"Error HTTP {res.status_code if res else 'N/A'}")
                break
            data = res.json()
            if not data:
                break
            all_data.extend(data)
            if len(data) < limit:
                break
            offset += limit
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching: {e}")
            break
            
    return all_data

def filter_and_dedupe(records):
    # Only pick conversational, active ones from the known dataset styles
    candidates = []
    for r in records:
        meta = r.get("metadata", {})
        if meta.get("status") == "inactive": continue
        
        # Determine if conversational. We reject CodeAlpaca style instructions unless it's genuinely conversational
        c = r.get("content", "")
        if "### Instruction:" in c and "### Output:" in c:
            # CodeAlpaca format
            q_text = c.split("### Instruction:")[1].split("### Output:")[0].strip()
            a_text = c.split("### Output:")[1].strip()
            # If it's pure code generation, reject
            if "write a program" in q_text.lower() or "implement a function" in q_text.lower():
                continue
            pool = "conversational"
        elif "### Technical Interview Question" in c:
            try:
                if "**Answer:**" in c:
                    q_text = c.split("**Answer:**")[0].replace("### Technical Interview Question", "").replace("**Question:**", "").strip()
                    a_text = c.split("**Answer:**")[1].strip()
                else:
                    q_text = meta.get("question", c[:200])
                    a_text = ""
            except Exception:
                q_text = meta.get("question", c[:200])
                a_text = ""
            pool = "conversational"
        else:
            q_text = meta.get("question", c[:200])
            a_text = ""
            pool = "conversational"
            
        candidates.append({
            "candidate_id": r["id"],
            "question_text": q_text,
            "answer_text": a_text,
            "source": meta.get("source", "unknown"),
            "skill": meta.get("skill", meta.get("topic", "General")),
            "role": meta.get("role", "Backend Developer")
        })
        
    # Deduplicate
    kept = []
    def tokens(s): return set(re.findall(r"\b[a-z0-9]+\b", s.lower()))
    for c in candidates:
        q_text = c["question_text"].lower().strip()
        q_words = tokens(q_text)
        if len(q_words) < 3: continue
        
        cand_intent = detect_question_intent(c["question_text"])
        c["actual_intent"] = cand_intent
        is_dup = False
        
        for p in kept:
            if c["skill"] != p["skill"]: continue
            p_text = p["question_text"].lower().strip()
            if q_text == p_text:
                is_dup = True; break
            
            p_words = tokens(p_text)
            if not q_words or not p_words: continue
            
            sim = len(q_words & p_words) / max(1, len(q_words | p_words))
            if sim >= 0.70:
                is_dup = True; break
                
            prev_intent = p["actual_intent"]
            intents_match = (cand_intent == prev_intent or {cand_intent, prev_intent} <= {"architecture", "design"})
            structural = {"architecture", "design", "justify", "tradeoff", "debug"}
            if intents_match and (cand_intent in structural or prev_intent in structural):
                if sim >= 0.35:
                    is_dup = True; break
        if not is_dup:
            kept.append(c)
            
    return kept

def generate_applicable_roles(primary_role, skill, text):
    roles = set([primary_role])
    t = text.lower()
    
    if primary_role in ["Frontend Developer", "Backend Developer"]:
        roles.add("Full Stack Developer")
        
    if "sql" in t or skill == "SQL":
        roles.update(["Database Developer", "Backend Developer", "Data Analyst", "Full Stack Developer"])
        
    if skill in ["AWS", "Linux", "Kubernetes", "CI/CD"]:
        roles.add("DevOps / Cloud Engineer")
        if "backend" in t: roles.add("Backend Developer")
        
    if "python" in t:
        roles.add("Python Developer")
        if "data" in t: roles.add("Data Analyst")
        
    if "java" in t and "javascript" not in t:
        roles.add("Java Developer")
        
    if "javascript" in t or "react" in t:
        roles.add("Frontend Developer")
        roles.add("Full Stack Developer")
        
    if skill == "System Design":
        roles.update(["Backend Developer", "Full Stack Developer", "DevOps / Cloud Engineer"])
        
    # intersection with target roles
    return list(roles.intersection(TARGET_ROLES))
    
def determine_difficulty(q_text, intent):
    t = q_text.lower()
    if intent in ["architecture", "design", "tradeoff", "scenario", "optimize"]: return "hard"
    if intent in ["implement", "debug", "diagnose", "compare"]: return "medium"
    if len(t.split()) > 25 or "difference" in t: return "medium"
    return "easy"

def assign_skill(role, text):
    t = text.lower()
    for skill, data in DEEP_TAXONOMY.get(role, {}).items():
        for tech in data["tech"]:
            if tech.lower() in t:
                return skill
    return list(DEEP_TAXONOMY.get(role, {}).keys())[0] if DEEP_TAXONOMY.get(role) else "General"

def main():
    print("Fetching Supabase records...")
    records = fetch_supabase_records()
    print(f"Total rows fetched: {len(records)}")
    
    kept = filter_and_dedupe(records)
    print(f"Accepted canonical questions from DB: {len(kept)}")
    
    final_dataset = []
    
    for c in kept:
        q_text = c["question_text"]
        intent = c["actual_intent"]
        diff = determine_difficulty(q_text, intent)
        
        role = c.get("role", "Backend Developer")
        if role not in TARGET_ROLES:
            if c["source"] == "JavaScript" or c["source"] == "React": role = "Frontend Developer"
            elif "DevOps" in c["source"]: role = "DevOps / Cloud Engineer"
            elif "SystemDesign" in c["source"]: role = "Backend Developer"
            else: role = "Backend Developer"
            
        # deep map skill
        deep_skill = assign_skill(role, q_text)
        
        applicable = generate_applicable_roles(role, deep_skill, q_text)
        
        q_type = "concept"
        if intent in ["implement"]: q_type = "implementation"
        if intent in ["debug", "diagnose"]: q_type = "debugging"
        if intent == "scenario": q_type = "scenario"
        if intent == "tradeoff": q_type = "tradeoff"
        if intent == "compare": q_type = "comparison"
        if intent in ["architecture", "design"]: q_type = "architecture"
        
        record = {
            "id": str(uuid.uuid4()),
            "question": q_text,
            "primary_role": role,
            "applicable_roles": applicable,
            "primary_skill": deep_skill,
            "secondary_skills": [],
            "technology": DEEP_TAXONOMY.get(role, {}).get(deep_skill, {}).get("tech", [None])[0],
            "topic": DEEP_TAXONOMY.get(role, {}).get(deep_skill, {}).get("topics", ["General"])[0],
            "category": "technical",
            "intent": intent,
            "difficulty": diff,
            "question_type": q_type,
            "expected_answer": c.get("answer_text", ""),
            "evaluation_rubric": {
                "strong_indicators": [],
                "weak_indicators": []
            },
            "source": c["source"],
            "source_url": None,
            "source_id": c["candidate_id"],
            "provenance_type": "existing_db",
            "dataset_version": "v2",
            "status": "active"
        }
        final_dataset.append(record)
        
    # Write Dataset JSONL and CSV
    with open(os.path.join(DATA_DIR, "interview_question_bank_v2.jsonl"), "w", encoding="utf-8") as f:
        for r in final_dataset:
            f.write(json.dumps(r) + "\n")
            
    if final_dataset:
        keys = final_dataset[0].keys()
        with open(os.path.join(DATA_DIR, "interview_question_bank_v2.csv"), "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in final_dataset:
                row = r.copy()
                row["applicable_roles"] = "|".join(row["applicable_roles"])
                row["secondary_skills"] = "|".join(row["secondary_skills"])
                row["evaluation_rubric"] = json.dumps(row["evaluation_rubric"])
                writer.writerow(row)
                
    # Generate coverage & gap reports
    role_counts = Counter()
    skill_counts = Counter()
    intent_counts = Counter()
    diff_counts = Counter()
    qtype_counts = Counter()
    src_counts = Counter()
    
    for r in final_dataset:
        for ar in r["applicable_roles"]:
            role_counts[ar] += 1
        skill_counts[r["primary_skill"]] += 1
        intent_counts[r["intent"]] += 1
        diff_counts[r["difficulty"]] += 1
        qtype_counts[r["question_type"]] += 1
        src_counts[r["source"]] += 1

    TARGET_PER_ROLE = 500
    gap_matrix = []
    
    for role, data in DEEP_TAXONOMY.items():
        curr_role_count = role_counts[role]
        for skill, meta in data.items():
            gap_matrix.append({
                "ROLE": role,
                "SKILL": skill,
                "PRIORITY": meta["priority"],
                "CURRENT": skill_counts.get(skill, 0),
                "TARGET": 30 if meta["priority"] == "CORE" else (20 if meta["priority"] == "IMPORTANT" else 10),
                "GAP": max(0, (30 if meta["priority"] == "CORE" else (20 if meta["priority"] == "IMPORTANT" else 10)) - skill_counts.get(skill, 0))
            })

    # Saving reports
    with open(os.path.join(REPORTS_DIR, "phase4b_final_taxonomy.json"), "w") as f:
        json.dump(DEEP_TAXONOMY, f, indent=2)
        
    tax_md = "# Phase 4B Final Taxonomy\\n"
    for r, d in DEEP_TAXONOMY.items():
        tax_md += f"\\n## {r}\\n"
        for s, meta in d.items():
            tax_md += f"- **{s}** [{meta['priority']}] (Tech: {', '.join(meta['tech'])})\\n"
    with open(os.path.join(REPORTS_DIR, "phase4b_final_taxonomy.md"), "w") as f:
        f.write(tax_md)
        
    with open(os.path.join(REPORTS_DIR, "phase4b_role_skill_matrix.json"), "w") as f: json.dump(gap_matrix, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4b_question_coverage.json"), "w") as f: json.dump({"roles": dict(role_counts), "skills": dict(skill_counts), "intents": dict(intent_counts), "difficulty": dict(diff_counts), "types": dict(qtype_counts)}, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4b_source_inventory.json"), "w") as f: json.dump(dict(src_counts), f, indent=2)
    
    qr = {
        "1. Number of roles": len(TARGET_ROLES),
        "2. Number of skills per role": {r: len(DEEP_TAXONOMY[r]) for r in TARGET_ROLES},
        "3. Number of technologies per role": {r: len(set(x for s in DEEP_TAXONOMY[r].values() for x in s["tech"])) for r in TARGET_ROLES},
        "4. Number of topics": sum(len(s["topics"]) for r in DEEP_TAXONOMY.values() for s in r.values()),
        "5. Current questions": len(final_dataset),
        "6. New authentic questions found": 0,
        "7. New generated questions": 0,
        "8. Final unique question count": len(final_dataset),
        "9. Questions per role": dict(role_counts),
        "10. Questions per skill": dict(skill_counts),
        "11. Questions per intent": dict(intent_counts),
        "12. Questions per difficulty": dict(diff_counts),
        "13. Questions per question type": dict(qtype_counts),
        "14. Source distribution": dict(src_counts),
        "15. Generated distribution": {"generated": 0},
        "16. Remaining gaps": sum(g["GAP"] for g in gap_matrix),
        "17. Quality rejection count": len(records) - len(final_dataset),
        "18. Duplicate count": "accounted in rejections",
        "19. Whether the dataset meets production quality": "NO"
    }
    with open(os.path.join(REPORTS_DIR, "phase4b_quality_report.json"), "w") as f: json.dump(qr, f, indent=2)
    with open(os.path.join(REPORTS_DIR, "phase4b_quality_report.md"), "w") as f:
        f.write("# Phase 4B Quality Report\n\n")
        for k, v in qr.items(): f.write(f"**{k}**: {v}\n")
        
    print("Phase 4B successfully completed. Generated local dataset V2 and reports.")

if __name__ == "__main__":
    main()
