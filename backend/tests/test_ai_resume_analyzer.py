import pytest
from app.resume_processing.ai_analyzer import sanitize_ai_analysis, AIResumeAnalyzer
from app.resume_processing.matcher import RoleProfile
from app.resume_processing.extractor import ExtractedCandidateProfile
from app.resume_processing.schemas import MatchedArea

def _get_dummy_profile():
    return ExtractedCandidateProfile(
        candidate_name="Test",
        all_skills={"python", "django"},
        projects=[{"name": "E-Commerce App"}],
        raw_text="I am a developer using Python and Django. I built an E-Commerce App."
    )

def _get_dummy_role():
    return RoleProfile(
        role_id="backend",
        role_name="Backend",
        core_skills=["python", "docker", "kubernetes"],
        programming_languages=["python"],
        technical_concepts=["api"],
        frameworks_tools=["django"],
        raw_role_data={"name": "Backend"}
    )

def test_hallucinated_evidence_rejected():
    profile = _get_dummy_profile()
    role = _get_dummy_role()
    ai_data = {
        "core_requirements": [
            {"requirement": "kubernetes", "status": "strong_match", "evidence": ["I used kubernetes"], "confidence": 0.9}
        ]
    }
    sanitized = sanitize_ai_analysis(ai_data, profile, role)
    # Since "I used kubernetes" is not in the raw_text, it should be rejected.
    # Therefore, the core_requirements list should be empty.
    # Actually, sanitize_ai_analysis returns None if there is no valid content left.
    assert sanitized is None or len(sanitized.get("core_requirements", [])) == 0

def test_confidence_clamped():
    profile = _get_dummy_profile()
    role = _get_dummy_role()
    # Add django to raw_text
    profile.raw_text += " I used django."
    ai_data = {
        "technology_matches": [
            {"technology": "django", "status": "strong_match", "evidence": ["I used django"], "confidence": 5.0},
        ]
    }
    sanitized = sanitize_ai_analysis(ai_data, profile, role)
    assert sanitized is not None
    assert sanitized["technology_matches"][0]["confidence"] == 1.0

def test_malformed_confidence():
    profile = _get_dummy_profile()
    role = _get_dummy_role()
    profile.raw_text += " I used django."
    ai_data = {
        "technology_matches": [
            {"technology": "django", "status": "strong_match", "evidence": ["I used django"], "confidence": "invalid"}
        ]
    }
    sanitized = sanitize_ai_analysis(ai_data, profile, role)
    assert sanitized is not None
    assert sanitized["technology_matches"][0]["confidence"] == 0.0

def test_multimodal_content_fix(monkeypatch):
    analyzer = AIResumeAnalyzer()
    
    class MockResponse:
        def __init__(self):
            self.content = [{"type": "text", "text": '```json\n{"summary": "test"}\n```'}]
    
    def mock_invoke(*args, **kwargs):
        return MockResponse()
        
    try:
        from ai_engine.models.llm import PoolableLLM
        monkeypatch.setattr(PoolableLLM, "invoke", mock_invoke)
    except ImportError:
        pass
        
    result = analyzer.analyze({}, _get_dummy_profile(), _get_dummy_role())
    assert result is not None
    assert result["summary"] == "test"

def test_malformed_json(monkeypatch):
    analyzer = AIResumeAnalyzer()
    class MockResponse:
        content = "This is not JSON"
    
    def mock_invoke(*args, **kwargs):
        return MockResponse()
        
    try:
        from ai_engine.models.llm import PoolableLLM
        monkeypatch.setattr(PoolableLLM, "invoke", mock_invoke)
    except ImportError:
        pass
        
    result = analyzer.analyze({}, _get_dummy_profile(), _get_dummy_role())
    assert result is None

def test_malformed_fields_validation(monkeypatch):
    analyzer = AIResumeAnalyzer()
    class MockResponse:
        content = '{"missing_summary": "test", "core_requirements": [{"status": "strong_match"}]}' # Missing fields will fail Pydantic
    
    def mock_invoke(*args, **kwargs):
        return MockResponse()
        
    try:
        from ai_engine.models.llm import PoolableLLM
        monkeypatch.setattr(PoolableLLM, "invoke", mock_invoke)
    except ImportError:
        pass
        
    result = analyzer.analyze({}, _get_dummy_profile(), _get_dummy_role())
    # Malformed data missing the 'requirement' key gets stripped, leaving core_requirements empty.
    # Since summary is missing, no content remains, and sanitize_ai_analysis returns None.
    assert result is None
