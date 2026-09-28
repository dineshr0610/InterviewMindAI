"""Configurable technical role catalog.

Roles are data, not hardcoded interview scripts. Additional roles can be
added here without changing interview flow code.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _role(
    role_id: str,
    name: str,
    aliases: List[str],
    required_skills: List[str],
    important_topics: List[str],
    question_areas: List[str],
    coding_topics: List[str],
    languages: List[str],
) -> Dict[str, Any]:
    return {
        "id": role_id,
        "name": name,
        "aliases": aliases,
        "required_skills": required_skills,
        "important_topics": important_topics,
        "question_areas": question_areas,
        "difficulty_levels": ["Easy", "Medium", "Hard"],
        "coding_topics": coding_topics,
        "languages": languages,
    }


ROLE_CATALOG: List[Dict[str, Any]] = [
    _role(
        "frontend_developer",
        "Frontend Developer",
        ["frontend", "front-end", "front end", "ui developer", "react developer", "web developer"],
        ["HTML", "CSS", "JavaScript", "TypeScript", "React", "DOM", "APIs", "Browser concepts"],
        ["HTML", "CSS", "JavaScript", "DOM", "React", "APIs", "Browser concepts", "Responsive design", "Web performance"],
        ["HTML & CSS layout", "DOM manipulation", "React state & hooks", "API integration", "Browser rendering & storage"],
        ["JavaScript problems", "DOM manipulation", "React tasks", "Array transformation", "UI state logic"],
        ["JavaScript", "TypeScript"],
    ),
    _role(
        "backend_developer",
        "Backend Developer",
        ["backend", "back-end", "back end", "api developer", "server engineer", "backend engineer"],
        ["REST APIs", "Databases", "Authentication", "Server architecture", "HTTP", "SQL", "Caching"],
        ["REST APIs", "Databases", "Authentication", "Server architecture", "HTTP", "Query optimization", "Concurrency"],
        ["API design", "Database transactions", "JWT & OAuth", "Microservices vs monolith", "HTTP status codes & caching"],
        ["API logic", "CRUD operations", "Algorithms", "Database queries", "Hash maps", "Validation"],
        ["Python", "Java", "JavaScript", "TypeScript"],
    ),
    _role(
        "full_stack_developer",
        "Full Stack Developer",
        ["full stack", "full-stack", "fullstack", "fullstack developer"],
        ["Frontend", "Backend", "Databases", "APIs", "React", "Node.js", "SQL", "Authentication"],
        ["Frontend architecture", "Backend architecture", "Databases", "REST APIs", "End-to-end data flow", "Security"],
        ["Client-server interaction", "API design", "Database schema modeling", "State management", "Deployment"],
        ["Full-stack logic", "REST APIs", "SQL", "JavaScript problems", "Data flow synchronization"],
        ["JavaScript", "TypeScript", "Python", "Java", "SQL"],
    ),
    _role(
        "python_developer",
        "Python Developer",
        ["python", "python engineer", "django developer", "fastapi developer", "python programmer"],
        ["Python", "OOP", "Data structures", "Modules", "Exceptions", "APIs", "Generators", "Decorators"],
        ["Python internals", "Object-Oriented Programming (OOP)", "Built-in data structures", "Modules & packages", "Exception handling", "FastAPI & Django APIs"],
        ["Memory management & GIL", "Dunder methods", "Context managers", "Iterators & generators", "Type hinting"],
        ["Algorithms", "Strings", "Arrays", "Files", "OOP implementation", "Problem solving"],
        ["Python"],
    ),
    _role(
        "java_developer",
        "Java Developer",
        ["java", "java engineer", "spring boot developer", "core java developer"],
        ["Java", "OOP", "Collections", "Exceptions", "Multithreading", "JDBC", "Spring Boot", "JVM"],
        ["Java language fundamentals", "Object-Oriented Programming (OOP)", "Java Collections Framework", "Exception handling", "Multithreading & Concurrency", "JDBC & JPA/Hibernate"],
        ["JVM architecture & Garbage Collection", "Generics", "Lambda expressions & Streams", "Synchronization", "Spring framework"],
        ["DSA", "OOP design", "Collections manipulation", "Problem solving", "Recursion & Trees"],
        ["Java"],
    ),
    _role(
        "data_analyst",
        "Data Analyst",
        ["data analyst", "bi analyst", "business intelligence", "analytics engineer"],
        ["Statistics", "SQL", "Data cleaning", "Excel concepts", "Visualization", "Pandas", "Power BI", "Tableau"],
        ["Descriptive & inferential statistics", "Advanced SQL", "Data cleaning & preprocessing", "Excel concepts & pivot tables", "Data visualization & storytelling"],
        ["Window functions & CTEs", "A/B testing interpretation", "Metrics definition", "Missing value imputation", "Dashboard design"],
        ["SQL queries", "Data manipulation", "Python/Pandas", "Aggregations", "Data transformation"],
        ["SQL", "Python"],
    ),
    _role(
        "machine_learning_engineer",
        "Machine Learning Engineer",
        ["machine learning", "ml engineer", "mle", "applied ml engineer"],
        ["ML algorithms", "Preprocessing", "Evaluation", "Regression", "Classification", "Feature engineering", "Scikit-Learn", "Model deployment"],
        ["Machine learning algorithms", "Data preprocessing & feature scaling", "Model evaluation metrics", "Regression techniques", "Classification models", "Overfitting & regularization"],
        ["Supervised & unsupervised learning", "Hyperparameter tuning", "Cross-validation", "Bias-variance tradeoff", "MLOps & model serving"],
        ["Python ML problems", "Data-processing pipelines", "Feature engineering scripts", "Matrix & vector math", "Evaluation metrics calculation"],
        ["Python"],
    ),
    _role(
        "ai_engineer",
        "AI Engineer",
        ["ai engineer", "artificial intelligence", "genai", "llm engineer", "deep learning engineer"],
        ["AI fundamentals", "ML", "NLP", "Neural networks", "Model evaluation", "LLMs", "RAG", "Prompt engineering"],
        ["Artificial intelligence fundamentals", "Deep learning & neural networks", "Natural Language Processing (NLP)", "Large Language Models (LLMs)", "Retrieval-Augmented Generation (RAG)", "Model evaluation & benchmarking"],
        ["Transformers architecture", "Embeddings & vector stores", "Fine-tuning vs prompting", "Attention mechanism", "Agent workflows"],
        ["Python algorithms", "ML/NLP implementation", "Tokenization & embeddings", "LangChain/LangGraph pipelines", "Prompt optimization"],
        ["Python"],
    ),
    _role(
        "database_developer",
        "Database Developer",
        ["database developer", "database engineer", "sql developer", "dba", "database administrator"],
        ["SQL", "DBMS", "Normalization", "Indexing", "Transactions", "Joins", "PostgreSQL", "Query optimization"],
        ["SQL syntax & standards", "DBMS architecture", "Database normalization (1NF-BCNF)", "Indexing strategies (B-Tree, Hash, GIN)", "ACID transactions & isolation levels", "Complex joins & aggregations"],
        ["Stored procedures & triggers", "Deadlock resolution", "Query execution plans & EXPLAIN", "Partitioning & sharding", "Schema migration"],
        ["SQL query problems", "Database logic", "Complex JOINs & subqueries", "Window functions", "Trigger & function implementation"],
        ["SQL"],
    ),
    _role(
        "devops_cloud_engineer",
        "DevOps / Cloud Engineer",
        ["devops", "cloud engineer", "devops engineer", "sre", "platform engineer", "cloud architect"],
        ["Linux", "Git", "CI/CD", "Docker", "Cloud", "Networking", "Kubernetes", "Terraform", "AWS"],
        ["Linux system administration", "Git version control & workflows", "CI/CD pipelines (GitHub Actions, GitLab, Jenkins)", "Docker containerization", "Cloud computing (AWS/Azure/GCP)", "Computer networking (TCP/IP, DNS, VPC)"],
        ["Container orchestration (Kubernetes)", "Infrastructure as Code (Terraform)", "Monitoring & observability (Prometheus/Grafana)", "Load balancers & reverse proxies", "Security & IAM"],
        ["Shell scripting", "Python automation", "Configuration tasks", "Dockerfile creation", "CI/CD pipeline scripts"],
        ["Bash", "Python"],
    ),
]


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def list_roles() -> List[Dict[str, Any]]:
    return [
        {
            "id": role["id"],
            "name": role["name"],
            "required_skills": role["required_skills"],
            "important_topics": role["important_topics"],
            "question_areas": role["question_areas"],
            "difficulty_levels": role["difficulty_levels"],
            "coding_topics": role["coding_topics"],
            "languages": role["languages"],
        }
        for role in ROLE_CATALOG
    ]


def resolve_role(name: Optional[str]) -> Dict[str, Any]:
    """Resolve a candidate-selected role name to a catalog entry."""
    raw = (name or "").strip() or "Software Engineer"
    needle = _normalize(raw)

    for role in ROLE_CATALOG:
        candidates = [_normalize(role["name"]), role["id"].replace("_", " ")]
        candidates.extend(_normalize(alias) for alias in role["aliases"])
        if needle in candidates or any(alias and alias in needle for alias in candidates):
            resolved = dict(role)
            resolved["selected_name"] = raw
            return resolved

    slug = re.sub(r"[^a-z0-9]+", "_", needle).strip("_") or "custom_role"
    return {
        "id": slug,
        "name": raw,
        "selected_name": raw,
        "aliases": [],
        "required_skills": [],
        "important_topics": [
            f"{raw} fundamentals",
            "Data structures",
            "Algorithms",
            "Debugging",
            "System design",
        ],
        "question_areas": ["fundamentals", "problem solving", "trade-offs"],
        "difficulty_levels": ["Easy", "Medium", "Hard"],
        "coding_topics": ["arrays", "hash maps", "strings"],
        "languages": ["python"],
        "custom": True,
    }
