"""Extract a usable candidate profile from resume text."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "kotlin", "swift", "ruby", "php", "sql", "html", "css", "react",
    "angular", "vue", "next.js", "node.js", "nodejs", "express", "fastapi",
    "django", "flask", "spring", "postgresql", "mysql", "mongodb", "redis",
    "elasticsearch", "kafka", "rabbitmq", "docker", "kubernetes", "aws",
    "gcp", "azure", "terraform", "linux", "git", "graphql", "rest", "grpc",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "spark",
    "airflow", "dbt", "hadoop", "ci/cd", "pytest", "jest", "selenium",
    "oauth", "jwt", "microservices", "system design", "machine learning",
    "deep learning", "nlp", "llm", "rag", "prompt engineering", "redux",
    "tailwind", "sass", "webpack", "nginx", "prometheus", "grafana",
    "hibernate", "jpa", "s3", "lambda", "ec2", "rds",
]


def extract_candidate_profile(
    candidate_name: str,
    resume_text: Optional[str],
) -> Dict[str, Any]:
    text = (resume_text or "").strip()
    skills = _extract_skills(text)
    technologies = _extract_technologies(text, skills)
    projects = _extract_section_items(text, ["project", "projects", "personal projects"])
    experience = _extract_section_items(text, ["experience", "work experience", "employment"])
    years = _estimate_years(text)

    return {
        "candidate_name": candidate_name,
        "resume_present": bool(text),
        "skills": skills,
        "technologies": technologies,
        "projects": projects[:8],
        "experience": experience[:8],
        "years_experience": years,
        "summary": _summary(text),
        "raw_char_count": len(text),
    }


def _extract_skills(text: str) -> List[str]:
    if not text:
        return []
    found: List[str] = []
    lower = text.lower()
    for skill in KNOWN_SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, lower):
            found.append(_display_skill(skill))
    section = _section_text(text, ["skills", "technical skills", "tech stack"])
    if section:
        extras = re.split(r"[,;/|•\n]", section)
        for extra in extras:
            cleaned = extra.strip(" -:\t")
            if 1 < len(cleaned) <= 40 and cleaned.lower() not in {s.lower() for s in found}:
                if re.search(r"[a-zA-Z]", cleaned):
                    found.append(cleaned)
    return found[:40]


def _extract_technologies(text: str, skills: List[str]) -> List[str]:
    tech_keys = {
        "python", "java", "javascript", "typescript", "react", "node.js",
        "fastapi", "django", "flask", "spring", "postgresql", "mysql",
        "mongodb", "redis", "docker", "kubernetes", "aws", "gcp", "azure",
        "kafka", "spark", "airflow",
    }
    techs = [s for s in skills if s.lower().replace("nodejs", "node.js") in tech_keys or s.lower() in tech_keys]
    return techs or skills[:12]


def _extract_section_items(text: str, headings: List[str]) -> List[str]:
    section = _section_text(text, headings)
    if not section:
        return []
    items: List[str] = []
    for raw in re.split(r"\n+", section):
        line = re.sub(r"^[\-\*\u2022\d\.\)]\s*", "", raw).strip()
        if len(line) >= 20:
            items.append(line[:240])
    return items


def _section_text(text: str, headings: List[str]) -> str:
    if not text:
        return ""
    heading = "|".join(re.escape(h) for h in headings)
    match = re.search(
        rf"(?im)^(?:{heading})\s*:?\s*\n(.*?)(?=\n[A-Z][A-Za-z /]{{2,40}}\s*:?\s*$|\Z)",
        text,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    # Fallback: same-line skills lists.
    match = re.search(rf"(?im)(?:{heading})\s*:\s*(.+)", text)
    return match.group(1).strip() if match else ""


def _estimate_years(text: str) -> Optional[float]:
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", text, re.I)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _summary(text: str) -> str:
    if not text:
        return ""
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:400]


def _display_skill(skill: str) -> str:
    mapping = {
        "nodejs": "Node.js",
        "node.js": "Node.js",
        "next.js": "Next.js",
        "ci/cd": "CI/CD",
        "c++": "C++",
        "c#": "C#",
        "sql": "SQL",
        "html": "HTML",
        "css": "CSS",
        "aws": "AWS",
        "gcp": "GCP",
        "rest": "REST",
        "jwt": "JWT",
        "nlp": "NLP",
        "llm": "LLM",
        "rag": "RAG",
    }
    return mapping.get(skill.lower(), skill.title() if skill.islower() else skill)
