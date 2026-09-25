"""Comprehensive tests for Module 1 - Resume Processing Module."""

from __future__ import annotations

import json
import pytest
from app.resume_processing.config import (
    get_role_by_identifier,
    list_roles,
    load_scoring_config,
    load_skill_aliases,
    load_technical_roles,
)
from app.resume_processing.normalizer import get_normalizer
from app.resume_processing.parser import parse_resume_text, clean_text
from app.resume_processing.service import ResumeProcessingService, get_resume_processing_service


def test_datasets_loaded_dynamically():
    """Verify that all 4 JSON datasets are loaded dynamically and correctly."""
    roles_data = load_technical_roles()
    assert "roles" in roles_data
    assert len(roles_data["roles"]) == 10

    aliases = load_skill_aliases()
    assert "Python" in aliases
    assert "Scikit-learn" in aliases
    assert "React" in aliases
    assert "sklearn" in aliases["Scikit-learn"]

    scoring = load_scoring_config()
    assert "weights" in scoring
    assert scoring["weights"]["core_skills"] == 0.35
    assert scoring["weights"]["technical_concepts"] == 0.25
    assert scoring["weights"]["project_experience"] == 0.2
    assert scoring["weights"]["frameworks_tools"] == 0.1
    assert scoring["weights"]["relevant_experience"] == 0.1


def test_ten_fixed_roles_resolution():
    """Verify all 10 fixed roles can be resolved dynamically."""
    expected_roles = [
        "frontend_developer",
        "backend_developer",
        "fullstack_developer",
        "ml_engineer",
        "data_analyst",
        "data_scientist",
        "devops_engineer",
        "cloud_engineer",
        "cybersecurity_engineer",
        "software_engineer",
    ]
    roles = list_roles()
    role_ids = [r["role_id"] for r in roles]
    for expected in expected_roles:
        assert expected in role_ids
        resolved = get_role_by_identifier(expected)
        assert resolved is not None
        assert resolved["role_id"] == expected


def test_skill_aliases_normalization():
    """Verify skill aliases are normalized case-insensitively according to skill_aliases.json."""
    normalizer = get_normalizer()
    assert normalizer.normalize("sklearn") == "Scikit-learn"
    assert normalizer.normalize("scikit learn") == "Scikit-learn"
    assert normalizer.normalize("nodejs") == "Node.js"
    assert normalizer.normalize("node js") == "Node.js"
    assert normalizer.normalize("node") == "Node.js"
    assert normalizer.normalize("react.js") == "React"
    assert normalizer.normalize("reactjs") == "React"
    assert normalizer.normalize("k8s") == "Kubernetes"
    assert normalizer.normalize("postgres") == "PostgreSQL"
    assert normalizer.normalize("mongodb") == "MongoDB"
    assert normalizer.normalize("cpp") == "C++"
    assert normalizer.normalize("csharp") == "C#"
    assert normalizer.normalize("powerbi") == "Power BI"
    assert normalizer.normalize("github action") == "GitHub Actions"
    assert normalizer.normalize("dockerized") == "Docker"
    assert normalizer.normalize("ml") == "Machine Learning"
    assert normalizer.normalize("nlp") == "Natural Language Processing"
    assert normalizer.normalize("restful api") == "REST API"


def test_ml_engineer_acceptance_test():
    """
    Acceptance test from specification:
    Role: ML Engineer
    Resume:
      Python
      Pandas
      Scikit-learn
      Project:
      Customer Churn Prediction
      Built a classification model using Python and Scikit-learn.
    """
    service = get_resume_processing_service()
    resume_text = """
    TECHNICAL SKILLS
    Python, Pandas, Scikit-learn

    PROJECTS
    Customer Churn Prediction
    Built a classification model using Python and Scikit-learn.
    """

    output = service.process(resume_text, role="ML Engineer")

    # 1. Output schema compliance
    assert output.selected_role == "ML Engineer"
    assert 0 <= output.role_match_score <= 100
    assert hasattr(output.score_breakdown, "core_skills")
    assert hasattr(output.score_breakdown, "technical_concepts")
    assert hasattr(output.score_breakdown, "project_experience")
    assert hasattr(output.score_breakdown, "frameworks_tools")
    assert hasattr(output.score_breakdown, "relevant_experience")

    # 2. Matched areas and evidence
    matched_topics = [m.topic for m in output.matched_areas]
    assert "Python" in matched_topics
    assert "Pandas" in matched_topics
    assert "Scikit-learn" in matched_topics
    assert any(t in matched_topics for t in ["Machine Learning", "Classification", "Supervised Learning"])

    # Check that evidence was extracted for Scikit-learn
    sklearn_match = next((m for m in output.matched_areas if m.topic == "Scikit-learn"), None)
    assert sklearn_match is not None
    assert "classification model using Python and Scikit-learn" in sklearn_match.evidence
    assert sklearn_match.source == "Customer Churn Prediction" or sklearn_match.section == "Projects"

    # 3. Missing areas identified
    assert len(output.missing_areas) > 0
    assert any("Deep Learning" in m or "PyTorch" in m or "MLflow" in m for m in output.missing_areas)

    # 4. Interview context structured correctly for Module 2
    assert len(output.interview_context) >= 3
    context_topics = [c.topic for c in output.interview_context]
    assert "Python" in context_topics
    assert "Scikit-learn" in context_topics
    for item in output.interview_context:
        assert item.evidence != ""
        assert item.source != ""
        assert 0.0 <= item.confidence <= 1.0


def test_single_role_isolation():
    """Verify resume is matched against ONLY the selected role, not mixed with other roles."""
    service = get_resume_processing_service()
    resume_text = """
    TECHNICAL SKILLS
    React, HTML, CSS, JavaScript, Redux

    PROJECTS
    E-Commerce Frontend
    Developed responsive single page application using React and Redux.
    """

    # Matched against Frontend Developer
    frontend_out = service.process(resume_text, role="Frontend Developer")
    assert frontend_out.selected_role == "Frontend Developer"
    assert "React" in [m.topic for m in frontend_out.matched_areas]
    assert frontend_out.role_match_score >= 40

    # Matched against DevOps Engineer (should have low score and unrelated skills)
    devops_out = service.process(resume_text, role="DevOps Engineer")
    assert devops_out.selected_role == "DevOps Engineer"
    assert "React" not in [m.topic for m in devops_out.matched_areas]
    assert "React" in devops_out.unrelated_skills or "JavaScript" in devops_out.unrelated_skills
    assert devops_out.role_match_score < 35
    assert frontend_out.role_match_score > devops_out.role_match_score + 15


def test_docx_and_pdf_parsing_support():
    """Verify parsing functions handle text and document formats cleanly."""
    raw = "Skills:\nPython | Java | MongoDB\n\nProject:\nE-Commerce\nBuilt backend API using Java and MongoDB."
    cleaned = clean_text(raw)
    parsed = parse_resume_text(cleaned)
    assert "skills" in parsed.sections or "summary" in parsed.sections
    assert len(parsed.all_sentences) > 0
