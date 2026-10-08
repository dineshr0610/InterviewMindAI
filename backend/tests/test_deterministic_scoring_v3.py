import pytest
from app.resume_processing.scorer import DeterministicScorer
from app.resume_processing.matcher import MatchResult, RoleProfile
from app.resume_processing.extractor import ExtractedCandidateProfile
from app.resume_processing.schemas import MatchedArea

def create_mock_role(core=None, lang=None, concepts=None, tools=None):
    return RoleProfile(
        role_id="test_role",
        role_name="Test Role",
        core_skills=core or [],
        programming_languages=lang or [],
        technical_concepts=concepts or [],
        frameworks_tools=tools or [],
        raw_role_data={}
    )

def create_mock_candidate(skills=None, projects=None, experience=None):
    return ExtractedCandidateProfile(
        raw_text="Mock resume text",
        projects=projects or [],
        experience=experience or [],
        all_skills=set(skills) if skills else set()
    )

def create_match_result(role, candidate, matched_areas=None, category_matches=None):
    return MatchResult(
        candidate_profile=candidate,
        role_profile=role,
        matched_areas=matched_areas or [],
        partial_matches=[],
        missing_areas=[],
        unrelated_skills=[],
        category_matches=category_matches or {},
        selected_role="test_role"
    )

def test_a_all_requirements_strongly_evidenced():
    scorer = DeterministicScorer()
    role = create_mock_role(core=["Python"], concepts=["Agile"], tools=["Git"])
    candidate = create_mock_candidate(
        projects=[{"title": "Proj", "technologies": ["Python", "Agile", "Git"]}],
        experience=[{"raw_text": "Used Python Agile Git", "technologies": ["Python", "Agile", "Git"]}]
    )
    
    matches = [
        MatchedArea(topic="Python", category="core_skills", confidence=1.0, section="Projects", source="test", evidence="test"),
        MatchedArea(topic="Agile", category="technical_concepts", confidence=1.0, section="Projects", source="Proj", evidence="used agile"),
        MatchedArea(topic="Git", category="frameworks_tools", confidence=1.0, section="Projects", source="Proj", evidence="used git"),
    ]
    
    cat_matches = {
        "core_skills": [matches[0]],
        "technical_concepts": [matches[1]],
        "frameworks_tools": [matches[2]],
    }
    
    res = create_match_result(role, candidate, matches, cat_matches)
    overall, breakdown = scorer.compute_score(res)
    assert overall == 100.0
    assert breakdown.core_skills == 100.0
    assert breakdown.technical_concepts == 100.0
    assert breakdown.project_experience == 100.0
    assert breakdown.frameworks_tools == 100.0
    assert breakdown.relevant_experience == 100.0

def test_b_half_requirements():
    scorer = DeterministicScorer()
    role = create_mock_role(core=["Python", "Java"], concepts=["Agile", "Scrum"], tools=["Git", "Docker"])
    candidate = create_mock_candidate(
        projects=[{"title": "Proj", "technologies": ["Python", "Agile", "Git"]}],
        experience=[{"raw_text": "Used Python Agile Git", "technologies": ["Python", "Agile", "Git"]}]
    )
    
    matches = [
        MatchedArea(topic="Python", category="core_skills", confidence=1.0, section="Projects", source="test", evidence="test"),
        MatchedArea(topic="Agile", category="technical_concepts", confidence=1.0, section="Projects", source="Proj", evidence="used agile"),
        MatchedArea(topic="Git", category="frameworks_tools", confidence=1.0, section="Projects", source="Proj", evidence="used git"),
    ]
    
    cat_matches = {
        "core_skills": [matches[0]],
        "technical_concepts": [matches[1]],
        "frameworks_tools": [matches[2]],
    }
    
    res = create_match_result(role, candidate, matches, cat_matches)
    overall, breakdown = scorer.compute_score(res)
    assert breakdown.core_skills == 50.0
    assert breakdown.technical_concepts == 50.0
    assert breakdown.frameworks_tools == 50.0
    assert breakdown.project_experience == 50.0
    assert breakdown.relevant_experience == 50.0
    assert overall == 50.0

def test_c_10_of_40_requirements_not_100_percent():
    scorer = DeterministicScorer()
    # 40 items total
    core = [f"Skill{i}" for i in range(10)]
    concepts = [f"Concept{i}" for i in range(10)]
    tools = [f"Tool{i}" for i in range(20)]
    role = create_mock_role(core=core, concepts=concepts, tools=tools)
    
    candidate = create_mock_candidate(
        projects=[{"title": "Proj", "technologies": core}]
    )
    
    matches = [
        MatchedArea(topic=c, category="core_skills", confidence=1.0, section="Projects", source="Proj", evidence="used skill") for c in core
    ]
    
    cat_matches = {
        "core_skills": matches
    }
    
    res = create_match_result(role, candidate, matches, cat_matches)
    overall, breakdown = scorer.compute_score(res)
    assert breakdown.core_skills == 100.0
    assert breakdown.technical_concepts == 0.0
    assert breakdown.frameworks_tools == 0.0
    assert breakdown.project_experience == 25.0  # 10 out of 40 = 25%
    
def test_d_many_techs_little_project_evidence():
    scorer = DeterministicScorer()
    role = create_mock_role(core=["Python", "Java", "C++"])
    candidate = create_mock_candidate(
        projects=[{"title": "Small Proj", "technologies": ["Python"]}]
    )
    
    matches = [
        MatchedArea(topic="Python", category="core_skills", confidence=1.0, section="Projects", source="Small Proj", evidence="used python"),
        MatchedArea(topic="Java", category="core_skills", confidence=1.0, section="Skills", source="Skills", evidence="java"),
        MatchedArea(topic="C++", category="core_skills", confidence=1.0, section="Skills", source="Skills", evidence="c++")
    ]
    
    res = create_match_result(role, candidate, matches, {"core_skills": matches})
    _, breakdown = scorer.compute_score(res)
    assert breakdown.core_skills == 100.0  # All 3 matched somewhere
    assert breakdown.project_experience == pytest.approx(33.3, abs=0.1)  # Only 1 of 3 in project

def test_k_category_zero_requirements():
    scorer = DeterministicScorer()
    role = create_mock_role(core=["Python"], concepts=[], tools=["Git"])
    candidate = create_mock_candidate(projects=[{"title": "Proj", "technologies": ["Python", "Git"]}])
    matches = [
        MatchedArea(topic="Python", category="core_skills", confidence=1.0, section="Projects", source="test", evidence="test"),
        MatchedArea(topic="Git", category="frameworks_tools", confidence=1.0, section="Projects", source="Proj", evidence="used git")
    ]
    res = create_match_result(role, candidate, matches, {"core_skills": [matches[0]], "frameworks_tools": [matches[1]]})
    overall, breakdown = scorer.compute_score(res)
    
    assert breakdown.technical_concepts == 0.0
    assert breakdown.core_skills == 100.0
    assert breakdown.frameworks_tools == 100.0
    # Weights: Core(25) + Tools(15) + Proj(20) + Exp(20) = 80 total available
    # Overall = (100*25 + 100*15 + 100*20 + 0*20) / 80 = 75.0
    assert overall == 75.0

def test_p_duplicate_evidence():
    scorer = DeterministicScorer()
    role = create_mock_role(core=["Python"])
    candidate = create_mock_candidate(projects=[{"title": "Proj", "technologies": ["Python"]}])
    matches = [
        MatchedArea(topic="Python", category="core_skills", confidence=1.0, section="Projects", source="test", evidence="test"),
        MatchedArea(topic="Python", category="core_skills", confidence=0.5, section="Skills", source="Skills", evidence="python"),
        MatchedArea(topic="Python", category="core_skills", confidence=1.0, section="Experience", source="Exp", evidence="used python")
    ]
    res = create_match_result(role, candidate, matches, {"core_skills": matches})
    _, breakdown = scorer.compute_score(res)
    # Should not be 300%
    assert breakdown.core_skills == 100.0

def test_r_partial_evidence():
    scorer = DeterministicScorer()
    role = create_mock_role(core=["Python"])
    candidate = create_mock_candidate()
    matches = [
        MatchedArea(topic="Python", category="core_skills", confidence=0.5, section="Skills", source="Skills", evidence="python")
    ]
    res = create_match_result(role, candidate, matches, {"core_skills": matches})
    _, breakdown = scorer.compute_score(res)
    assert breakdown.core_skills == 50.0
    
def test_n_empty_resume():
    scorer = DeterministicScorer()
    role = create_mock_role(core=["Python"])
    candidate = create_mock_candidate()
    res = create_match_result(role, candidate, [], {})
    overall, breakdown = scorer.compute_score(res)
    assert overall == 0.0
    assert breakdown.core_skills == 0.0

def test_o_empty_role():
    scorer = DeterministicScorer()
    role = create_mock_role()
    candidate = create_mock_candidate(projects=[{"title": "Proj", "technologies": ["Python"]}])
    matches = [MatchedArea(topic="Python", category="core_skills", confidence=1.0, section="Projects", source="test", evidence="test")]
    res = create_match_result(role, candidate, matches, {"core_skills": matches})
    overall, breakdown = scorer.compute_score(res)
    assert overall == 0.0
