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
        ["frontend", "front-end", "front end", "ui developer", "react developer"],
        ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Responsive design", "Web performance", "Accessibility"],
        ["JavaScript fundamentals", "React component model", "State management", "Browser rendering", "Web performance", "Accessibility"],
        ["DOM", "hooks", "routing", "testing", "CSS layout", "network requests"],
        ["array transformation", "string parsing", "ui state"],
        ["javascript", "typescript", "python"],
    ),
    _role(
        "backend_developer",
        "Backend Developer",
        ["backend", "back-end", "back end", "api developer", "server engineer"],
        ["REST APIs", "Databases", "SQL", "Authentication", "Caching", "Concurrency", "Error handling"],
        ["REST API design", "Relational databases", "Indexing and query optimization", "Caching", "Authentication and authorization", "Concurrency"],
        ["HTTP", "transactions", "ORMs", "message queues", "observability"],
        ["hash maps", "arrays", "string processing", "api validation"],
        ["python", "javascript", "java"],
    ),
    _role(
        "full_stack_developer",
        "Full Stack Developer",
        ["full stack", "full-stack", "fullstack"],
        ["JavaScript", "REST APIs", "SQL", "React", "Authentication", "System design"],
        ["API design", "Frontend state", "Database modeling", "Authentication", "End-to-end data flow"],
        ["CRUD", "caching", "deployment", "testing"],
        ["arrays", "hash maps", "string parsing"],
        ["python", "javascript", "typescript"],
    ),
    _role(
        "software_engineer",
        "Software Engineer",
        ["software developer", "swe", "programmer"],
        ["Data structures", "Algorithms", "Testing", "Debugging", "System design", "Version control"],
        ["Data structures", "Algorithms", "Object-oriented design", "Testing", "Debugging", "Complexity analysis"],
        ["arrays", "trees", "hash maps", "concurrency", "APIs"],
        ["arrays", "hash maps", "two pointers", "strings"],
        ["python", "javascript", "java"],
    ),
    _role(
        "devops_engineer",
        "DevOps Engineer",
        ["devops", "sre", "platform engineer"],
        ["CI/CD", "Containers", "Linux", "Cloud", "Monitoring", "Infrastructure as code"],
        ["CI/CD pipelines", "Containers and orchestration", "Cloud networking", "Observability", "Infrastructure as code"],
        ["Docker", "Kubernetes", "Terraform", "incident response"],
        ["log parsing", "string processing", "scheduling"],
        ["python", "bash"],
    ),
    _role(
        "data_scientist",
        "Data Scientist",
        ["data science"],
        ["Python", "Statistics", "SQL", "Machine learning", "Feature engineering", "Experimentation"],
        ["Statistics", "Supervised learning", "Feature engineering", "Model evaluation", "SQL for analysis"],
        ["overfitting", "metrics", "data leakage", "visualization"],
        ["arrays", "statistics", "string parsing"],
        ["python"],
    ),
    _role(
        "data_analyst",
        "Data Analyst",
        ["analyst", "bi analyst"],
        ["SQL", "Data cleaning", "Aggregation", "Visualization", "Statistics"],
        ["SQL joins and aggregations", "Data cleaning", "Metrics definition", "Visualization"],
        ["window functions", "dashboards", "A/B interpretation"],
        ["aggregation", "string parsing"],
        ["python", "sql"],
    ),
    _role(
        "machine_learning_engineer",
        "Machine Learning Engineer",
        ["ml engineer", "mle", "machine learning"],
        ["Python", "Machine learning", "Model serving", "Feature stores", "Evaluation metrics", "Data pipelines"],
        ["Supervised learning", "Model evaluation", "Feature engineering", "Training vs serving", "ML system design"],
        ["overfitting", "latency", "data drift", "pipelines"],
        ["arrays", "hash maps", "vector math"],
        ["python"],
    ),
    _role(
        "ai_engineer",
        "AI Engineer",
        ["genai", "llm engineer", "artificial intelligence"],
        ["Python", "LLMs", "Prompting", "RAG", "Evaluation", "APIs"],
        ["LLM application design", "Retrieval-augmented generation", "Prompt design", "Evaluation of generated output"],
        ["chunking", "embeddings", "hallucinations", "latency"],
        ["string processing", "hash maps"],
        ["python"],
    ),
    _role(
        "data_engineer",
        "Data Engineer",
        ["data engineering", "etl engineer"],
        ["SQL", "ETL", "Data modeling", "Warehouses", "Pipelines", "Python"],
        ["ETL design", "Data modeling", "Warehouse performance", "Pipeline reliability"],
        ["partitioning", "idempotency", "schema evolution"],
        ["arrays", "hash maps", "string parsing"],
        ["python", "sql"],
    ),
    _role(
        "mobile_developer",
        "Mobile Developer",
        ["android", "ios", "mobile", "react native", "flutter"],
        ["Mobile UI", "State management", "Networking", "Offline storage", "Performance"],
        ["Mobile app architecture", "Navigation and state", "Networking", "Offline-first design"],
        ["lifecycle", "lists", "caching"],
        ["arrays", "string parsing"],
        ["python", "javascript"],
    ),
    _role(
        "qa_engineer",
        "QA / Test Engineer",
        ["qa", "test engineer", "sdet", "quality"],
        ["Test design", "Automation", "API testing", "Debugging", "CI"],
        ["Test strategy", "Automation frameworks", "API testing", "Flaky tests"],
        ["coverage", "fixtures", "assertions"],
        ["string matching", "arrays"],
        ["python", "javascript"],
    ),
    _role(
        "cloud_engineer",
        "Cloud Engineer",
        ["cloud", "aws", "gcp", "azure"],
        ["Cloud networking", "IAM", "Compute", "Storage", "Infrastructure as code"],
        ["Cloud architecture", "Identity and access", "Networking", "Cost and reliability"],
        ["VPC", "load balancing", "autoscaling"],
        ["string processing", "scheduling"],
        ["python"],
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
