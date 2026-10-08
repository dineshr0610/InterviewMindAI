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
    projects = _extract_section_items(text, ["project", "projects", "personal projects", "academic projects"])
    experience = _extract_section_items(text, ["experience", "work experience", "employment", "internships"])
    education = _extract_section_items(text, ["education", "academic background", "qualifications", "academics"])
    certifications = _extract_section_items(text, ["certifications", "certificates", "credentials", "licenses"])
    years = _estimate_years(text)

    return {
        "candidate_name": candidate_name,
        "resume_present": bool(text),
        "skills": skills,
        "technologies": technologies,
        "projects": projects[:8],
        "experience": experience[:8],
        "education": education[:6],
        "certifications": certifications[:6],
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
    from app.resume_processing.parser import parse_resume_text
    
    parsed = parse_resume_text(text)
    
    # Map the headings to canonical names based on parser.py
    target_canonical = None
    if "project" in headings[0].lower() or "projects" in headings[0].lower():
        target_canonical = "projects"
    elif "experience" in headings[0].lower() or "employment" in headings[0].lower():
        target_canonical = "experience"
    elif "education" in headings[0].lower() or "academic" in headings[0].lower():
        target_canonical = "education"
    elif "certifications" in headings[0].lower() or "certificates" in headings[0].lower():
        target_canonical = "certifications"
        
    items = []
    if target_canonical and target_canonical in parsed.sections:
        for item in parsed.sections[target_canonical].items:
            # Filter out non-project lines and section sub-labels
            title_lower = item.title.lower()
            if len(item.title) > 120 or ":" in item.title:
                continue
            if title_lower in {"tech stack", "technologies", "environment", "tools", "skills", "dynamic pages", "key features"}:
                continue
                
            content = f"{item.title} - {item.description}" if item.description else item.title
            if len(content) > 20:
                items.append(content[:240])
                
    if not items:
        # Fallback to the old logic if parsing fails to find anything
        section = _section_text(text, headings)
        if not section:
            return []
        for raw in re.split(r"\n+", section):
            line = re.sub(r"^[\-\*\u2022\d\.\)]\s*", "", raw).strip()
            if len(line) >= 20 and ":" not in line and line.lower() not in {"tech stack", "technologies", "environment", "dynamic pages", "key features"}:
                items.append(line[:240])
                
    return items


KNOWN_SECTION_HEADINGS = [
    "skills", "technical skills", "tech stack", "core competencies",
    "projects", "personal projects", "academic projects", "project experience",
    "work experience", "experience", "employment", "internships",
    "education", "academic history", "academic background", "academics",
    "certifications", "certificates", "credentials", "licenses",
    "summary", "professional summary", "profile", "objective",
    "achievements", "awards", "publications", "languages"
]


def _section_text(text: str, headings: List[str]) -> str:
    if not text:
        return ""
    heading = "|".join(re.escape(h) for h in headings)
    all_headings = "|".join(re.escape(h) for h in KNOWN_SECTION_HEADINGS)
    match = re.search(
        rf"(?im)^\s*(?:{heading})\s*:?\s*\n(.*?)(?=\n\s*(?:{all_headings})\s*:?\s*$|\Z)",
        text,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    # Fallback: same-line skills lists.
    match = re.search(rf"(?im)^\s*(?:{heading})\s*:\s*(.+)", text)
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
        "javascript": "JavaScript",
        "typescript": "TypeScript",
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
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "fastapi": "FastAPI",
        "graphql": "GraphQL",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "redis": "Redis",
        "django": "Django",
        "flask": "Flask",
        "react": "React",
        "angular": "Angular",
        "vue": "Vue",
        "spring": "Spring",
        "git": "Git",
        "linux": "Linux",
    }
    return mapping.get(skill.lower(), skill.title() if skill.islower() else skill)
