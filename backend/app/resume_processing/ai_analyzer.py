"""AI (Gemini) qualitative resume-vs-role analysis for Module 1.

Design contract
---------------
* The deterministic pipeline (match -> score -> feedback -> interview_context) is computed
  FIRST and is never modified by anything in this module. The deterministic score is authoritative.
* Gemini output is treated as untrusted. ``sanitize_ai_analysis`` validates every item against
  (a) the authoritative role requirements used by the backend and (b) the candidate's resume text,
  and silently drops anything that is null, malformed, off-role, or not grounded in the resume.
* The sanitized block is returned as a separate ``ai_analysis`` object. It is never merged into
  ``matched_areas`` / ``partial_matches`` / ``missing_areas``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, Iterable, List, Optional, Set

from langchain_core.messages import HumanMessage, SystemMessage

from ai_engine.models.llm import llm
from app.resume_processing.extractor import ExtractedCandidateProfile
from app.resume_processing.matcher import RoleProfile
from app.resume_processing.normalizer import get_normalizer
from app.resume_processing.schemas import AIResumeAnalysisOutput

logger = logging.getLogger("interviewmind.resume_processing.ai_analyzer")

AI_ANALYSIS_TIMEOUT_SECONDS = float(os.getenv("RESUME_AI_TIMEOUT_SECONDS", "45"))

VALID_STATUSES = ("strong_match", "partial_match", "missing_evidence")
MAX_ITEMS = 15
MAX_TEXT_CHARS = 300
MAX_SUMMARY_CHARS = 900

_NULLISH = {
    "", "null", "none", "nil", "unknown", "n/a", "na", "undefined", "not specified",
    "not available", "not provided", "-", "--",
}
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has", "was", "were", "are",
    "using", "used", "use", "into", "over", "such", "their", "they", "your", "will", "also",
    "than", "then", "been", "being", "which", "while", "within", "across", "about", "more",
    "most", "some", "any", "all", "its", "our", "his", "her", "per", "via", "etc",
}

SYSTEM_PROMPT = """You are an expert technical recruiter and resume analyzer.
Your task is to analyze a candidate's resume evidence against an authoritative role requirement definition.

IMPORTANT RULES:
1. Do NOT invent or assume role requirements. Every "requirement" / "technology" / gap / missing item MUST be copied
   verbatim from the provided ROLE REQUIREMENTS lists.
2. NEVER claim a candidate has experience that is not supported by their resume evidence. The DETERMINISTIC COMPETENCY MATRIX
   contains verified evidence found by the system. Use this as your primary source of truth for what the candidate has and hasn't done.
3. Only list a project in "relevant_projects" if it appears by name in the candidate's projects/resume.
4. Distinguish between:
   - "strong_match": explicitly demonstrated in projects or long-term experience (needs a quote)
   - "partial_match": mentioned in skills or weakly inferred (needs a quote)
   - "missing_evidence": not mentioned at all (use an empty evidence list). If it's missing in the COMPETENCY MATRIX, it MUST be missing.
5. Provide QUALITATIVE insight (summary, reasoning, interview focus areas); do not just restate a keyword list.
6. Never output null. Use empty strings or empty lists instead.
7. Produce a strict JSON object exactly matching the requested schema. Do not output markdown code blocks or text outside the JSON.
8. Calculate an ai_match_score (0-100) based ONLY on provided evidence vs authoritative role requirements. Do NOT score based on assumptions, invented experience, or missing evidence (which is not automatically proof of inability).
9. The summary must be strictly evidence-based and objective. Do not use exaggerated language like "exceptionally strong fit". Use balanced phrasing like "Strong alignment" or "Limited evidence".
10. If a technology (e.g., npm) is highly implied by other skills but not explicitly written, omit it from the missing skills/gaps lists. Do not group implied skills with completely missing skills.
"""

SCHEMA_INSTRUCTION = """
You MUST return a JSON object with this exact structure:
{
  "target_role": "String (verbatim role name)",
  "summary": "Qualitative summary of fit...",
  "ai_match_score": 85,
  "ai_score_breakdown": {
    "core_requirements": 80,
    "supporting_requirements": 90,
    "technology_alignment": 85,
    "project_relevance": 70,
    "experience_relevance": 95
  },
  "core_requirements": [
    {
      "requirement": "string (verbatim from role requirements)",
      "importance": "core",
      "status": "strong_match|partial_match|missing_evidence",
      "evidence": ["exact quote from resume"],
      "confidence": 0.0-1.0
    }
  ],
  "supporting_requirements": [ ... same structure as core_requirements but for non-core concepts/tools ... ],
  "technology_matches": [
    {
      "technology": "string (verbatim from role requirements)",
      "status": "strong_match|partial_match|missing_evidence",
      "evidence": ["exact quote from resume"],
      "confidence": 0.0-1.0
    }
  ],
  "strong_matches": ["skill 1", "skill 2"],
  "partial_matches": ["skill 3"],
  "missing_or_unverified": ["skill 4"],
  "relevant_projects": [
    {
      "project": "project name exactly as in resume",
      "relevance": "string explanation",
      "evidence": ["exact quote from resume"]
    }
  ],
  "skill_gaps": ["gap 1"],
  "transferable_skills": ["skill 1"],
  "interview_focus_areas": ["area to probe 1", "area to probe 2"]
}
"""


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _clean_text(value: Any, max_chars: int = MAX_TEXT_CHARS) -> Optional[str]:
    """Return a trimmed string, or None for non-strings / null-like placeholders."""
    if not isinstance(value, str):
        return None
    text = re.sub(r"\s+", " ", value).strip()
    if text.lower() in _NULLISH:
        return None
    return text[:max_chars]


def _norm(text: str) -> str:
    text = re.sub(r"[^a-z0-9+#./ ]+", " ", (text or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def _word_in(needle: str, haystack: str) -> bool:
    """Word-bounded containment (tolerates a plural 's')."""
    if not needle or not haystack:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(needle)}s?(?![a-z0-9])"
    return re.search(pattern, haystack) is not None


def _content_tokens(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9+#.]{4,}", text) if t not in _STOPWORDS]


def _flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _flatten_strings(item)


class _GroundingContext:
    """Authoritative role requirements + resume text used to validate Gemini output."""

    def __init__(self, profile: ExtractedCandidateProfile, role: RoleProfile) -> None:
        self.normalizer = get_normalizer()
        self.raw_text: str = profile.raw_text or ""
        self.norm_text: str = _norm(self.raw_text)
        self.text_tokens: Set[str] = set(re.findall(r"[a-z0-9+#.]{2,}", self.norm_text))
        self.profile_skills = [s for s in (profile.all_skills or set()) if isinstance(s, str) and s.strip()]
        self.project_names: List[str] = []
        for proj in profile.projects or []:
            if isinstance(proj, dict):
                for key in ("title", "name"):
                    name = _clean_text(proj.get(key))
                    if name:
                        self.project_names.append(name)
                        break

        # role term (canonical spelling) keyed by normalized text
        self.role_terms: Dict[str, str] = {}
        role_lists = [
            role.core_skills, role.programming_languages, role.technical_concepts, role.frameworks_tools,
        ]
        for lst in role_lists:
            for term in lst or []:
                self._add_role_term(term)
        for raw in _flatten_strings(role.raw_role_data or {}):
            # only short list-like entries are requirements (skip descriptions / ids / names)
            if len(raw) <= 60:
                self._add_role_term(raw)

    def _add_role_term(self, term: Any) -> None:
        cleaned = _clean_text(term, 80)
        if cleaned:
            self.role_terms.setdefault(_norm(self.normalizer.normalize(cleaned)), cleaned)
            self.role_terms.setdefault(_norm(cleaned), cleaned)

    # -- role requirements -------------------------------------------------
    def match_role_term(self, text: str, allow_contains: bool = False) -> Optional[str]:
        """Return the role's own spelling of the requirement ``text`` refers to, else None."""
        norm = _norm(text)
        if not norm:
            return None
        canonical_norm = _norm(self.normalizer.normalize(text))
        for candidate in (norm, canonical_norm):
            if candidate in self.role_terms:
                return self.role_terms[candidate]
        # plural / minor variation, whole-word only
        for key, original in self.role_terms.items():
            if len(key) >= 3 and (key == norm + "s" or norm == key + "s"):
                return original
        if allow_contains:
            # longest role term that appears as a whole word inside the text
            for key in sorted(self.role_terms, key=len, reverse=True):
                if len(key) >= 3 and _word_in(key, norm):
                    return self.role_terms[key]
        return None

    # -- resume grounding --------------------------------------------------
    def in_resume(self, term: str) -> bool:
        if not term:
            return False
        if self.normalizer.find_in_text(self.raw_text, term):
            return True
        return _word_in(_norm(term), self.norm_text)

    def mentions_candidate_skill(self, text: str) -> bool:
        norm = _norm(text)
        return any(_word_in(_norm(s), norm) for s in self.profile_skills)

    def evidence_grounded(self, snippet: str) -> bool:
        norm = _norm(snippet)
        if len(norm) < 4:
            return False
        if norm in self.norm_text:
            return True
        tokens = _content_tokens(norm)
        if len(tokens) < 3:
            return False
        covered = sum(1 for t in tokens if t in self.text_tokens)
        return covered / len(tokens) >= 0.8

    def match_project(self, name: str) -> Optional[str]:
        norm = _norm(name)
        if not norm:
            return None
        for known in self.project_names:
            known_norm = _norm(known)
            if known_norm and (norm in known_norm or known_norm in norm):
                return known
        if len(norm) >= 4 and norm in self.norm_text:
            return name
        return None


# ---------------------------------------------------------------------------
# Sanitizer
# ---------------------------------------------------------------------------

def _grounded_evidence(raw: Any, ctx: _GroundingContext) -> List[str]:
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        text = _clean_text(item)
        if text and ctx.evidence_grounded(text) and text not in out:
            out.append(text)
    return out[:3]


def _clamp_confidence(value: Any) -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return 0.0
    if conf != conf:  # NaN
        return 0.0
    return round(max(0.0, min(1.0, conf)), 2)


def _clean_assessments(
    items: Any,
    name_key: str,
    importance: Optional[str],
    ctx: _GroundingContext,
    rejected: Dict[str, int],
) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []
    cleaned: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            rejected["malformed_item"] = rejected.get("malformed_item", 0) + 1
            continue
        raw_name = _clean_text(item.get(name_key)) or _clean_text(
            item.get("technology" if name_key == "requirement" else "requirement")
        )
        if not raw_name:
            rejected["null_requirement"] = rejected.get("null_requirement", 0) + 1
            continue
        canonical = ctx.match_role_term(raw_name)
        if not canonical:
            rejected["not_a_role_requirement"] = rejected.get("not_a_role_requirement", 0) + 1
            continue
        status = item.get("status")
        status = status.strip().lower() if isinstance(status, str) else None
        if status not in VALID_STATUSES:
            rejected["invalid_status"] = rejected.get("invalid_status", 0) + 1
            continue
        evidence = _grounded_evidence(item.get("evidence"), ctx)
        if status in ("strong_match", "partial_match"):
            if not evidence:
                rejected["unsupported_evidence"] = rejected.get("unsupported_evidence", 0) + 1
                continue
            if name_key == "technology" and not ctx.in_resume(canonical):
                rejected["technology_not_in_resume"] = rejected.get("technology_not_in_resume", 0) + 1
                continue
            confidence = _clamp_confidence(item.get("confidence"))
        else:
            evidence = []
            confidence = 0.0
        key = canonical.lower()
        if key in seen:
            continue
        seen.add(key)
        entry: Dict[str, Any] = {name_key: canonical, "status": status, "evidence": evidence, "confidence": confidence}
        if importance is not None:
            entry["importance"] = importance
        cleaned.append(entry)
        if len(cleaned) >= MAX_ITEMS:
            break
    return cleaned


def _clean_string_list(
    raw: Any,
    validator,
    rejected: Dict[str, int],
    reason: str,
    exclude: Optional[Set[str]] = None,
) -> List[str]:
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    seen: Set[str] = set(exclude or set())
    for item in raw:
        text = _clean_text(item)
        if not text:
            rejected[reason] = rejected.get(reason, 0) + 1
            continue
        resolved = validator(text)
        if not resolved:
            rejected[reason] = rejected.get(reason, 0) + 1
            continue
        key = resolved.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(resolved)
        if len(out) >= MAX_ITEMS:
            break
    return out


def sanitize_ai_analysis(
    ai_data: Any,
    profile: ExtractedCandidateProfile,
    role: RoleProfile,
) -> Optional[Dict[str, Any]]:
    """Validate raw Gemini output; return a clean ai_analysis dict or None if nothing usable remains."""
    if not isinstance(ai_data, dict):
        return None

    ctx = _GroundingContext(profile, role)
    rejected: Dict[str, int] = {}

    summary = _clean_text(ai_data.get("summary"), MAX_SUMMARY_CHARS) or ""

    core = _clean_assessments(ai_data.get("core_requirements"), "requirement", "core", ctx, rejected)
    supporting = _clean_assessments(ai_data.get("supporting_requirements"), "requirement", "supporting", ctx, rejected)
    tech = _clean_assessments(ai_data.get("technology_matches"), "technology", None, ctx, rejected)

    structured = core + supporting + tech
    verified_names = {
        s: {(e.get("requirement") or e.get("technology")).lower() for e in structured if e["status"] == s}
        for s in VALID_STATUSES
    }

    def _role_and_supported(text: str) -> Optional[str]:
        canonical = ctx.match_role_term(text)
        if not canonical:
            return None
        if canonical.lower() in verified_names["strong_match"] | verified_names["partial_match"]:
            return canonical
        return canonical if ctx.in_resume(canonical) else None

    strong = _clean_string_list(ai_data.get("strong_matches"), _role_and_supported, rejected, "unsupported_strong_match")
    partial = _clean_string_list(
        ai_data.get("partial_matches"), _role_and_supported, rejected, "unsupported_partial_match",
        exclude={s.lower() for s in strong},
    )
    claimed = {s.lower() for s in strong + partial}
    missing = _clean_string_list(
        ai_data.get("missing_or_unverified"), lambda t: ctx.match_role_term(t), rejected, "not_a_role_requirement",
        exclude=claimed,
    )
    gaps = _clean_string_list(
        ai_data.get("skill_gaps"), lambda t: t if ctx.match_role_term(t, allow_contains=True) else None,
        rejected, "not_a_role_requirement",
    )
    # A requirement that is verified as strong/partial must not also be listed as a gap.
    gaps = [g for g in gaps if (ctx.match_role_term(g, allow_contains=False) or "").lower() not in claimed]
    transferable = _clean_string_list(
        ai_data.get("transferable_skills"),
        lambda t: t if (ctx.in_resume(t) or ctx.mentions_candidate_skill(t) or ctx.evidence_grounded(t)) else None,
        rejected, "unsupported_transferable_skill",
    )
    focus = _clean_string_list(
        ai_data.get("interview_focus_areas"),
        lambda t: t if (
            ctx.match_role_term(t, allow_contains=True) or ctx.mentions_candidate_skill(t) or ctx.in_resume(t)
        ) else None,
        rejected, "ungrounded_focus_area",
    )

    projects: List[Dict[str, Any]] = []
    seen_projects: Set[str] = set()
    raw_projects = ai_data.get("relevant_projects")
    if isinstance(raw_projects, list):
        for proj in raw_projects:
            if not isinstance(proj, dict):
                rejected["malformed_item"] = rejected.get("malformed_item", 0) + 1
                continue
            name = _clean_text(proj.get("project"))
            known = ctx.match_project(name) if name else None
            if not known:
                rejected["unknown_project"] = rejected.get("unknown_project", 0) + 1
                continue
            evidence = _grounded_evidence(proj.get("evidence"), ctx)
            if not evidence:
                rejected["unsupported_evidence"] = rejected.get("unsupported_evidence", 0) + 1
                continue
            if known.lower() in seen_projects:
                continue
            seen_projects.add(known.lower())
            projects.append({
                "project": known,
                "relevance": _clean_text(proj.get("relevance"), 500) or "",
                "evidence": evidence,
            })
            if len(projects) >= MAX_ITEMS:
                break

    ai_match_score = None
    try:
        val = ai_data.get("ai_match_score")
        if val is not None:
            ai_match_score = float(val)
    except (TypeError, ValueError):
        pass

    ai_score_breakdown = ai_data.get("ai_score_breakdown")
    if not isinstance(ai_score_breakdown, dict):
        ai_score_breakdown = None

    result = {
        "target_role": role.role_name,
        "summary": summary,
        "ai_match_score": ai_match_score,
        "ai_score_breakdown": ai_score_breakdown,
        "core_requirements": core,
        "supporting_requirements": supporting,
        "technology_matches": tech,
        "strong_matches": strong,
        "partial_matches": partial,
        "missing_or_unverified": missing,
        "relevant_projects": projects,
        "skill_gaps": gaps,
        "transferable_skills": transferable,
        "interview_focus_areas": focus,
    }

    if rejected:
        logger.info("AI resume analysis: filtered unsupported items: %s", rejected)

    has_content = bool(summary) or any(result[k] for k in result if k not in ("summary", "target_role"))
    if not has_content:
        return None

    try:
        return AIResumeAnalysisOutput(**result).model_dump()
    except Exception as exc:  # defensive: sanitizer output should always validate
        logger.error("Sanitized AI analysis failed schema validation: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

def _extract_json_object(content: str) -> Any:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


class AIResumeAnalyzer:
    def __init__(self):
        pass

    def analyze(self, competency_matrix: Any, profile: ExtractedCandidateProfile, role: RoleProfile) -> Optional[Dict[str, Any]]:
        """Return a sanitized ai_analysis dict, or None if Gemini is unavailable / output unusable."""
        resume_data = {
            "skills": sorted(profile.all_skills),
            "projects": profile.projects,
            "experience": profile.experience,
            "raw_text": profile.raw_text[:5000] if profile.raw_text else "",
        }

        role_data = {
            "role_name": role.role_name,
            "core_skills": role.core_skills,
            "programming_languages": role.programming_languages,
            "technical_concepts": role.technical_concepts,
            "frameworks_tools": role.frameworks_tools,
            "role_details": role.raw_role_data,
        }

        matrix_data = competency_matrix.model_dump() if hasattr(competency_matrix, 'model_dump') else competency_matrix

        prompt = f"""
ROLE REQUIREMENTS:
{json.dumps(role_data, indent=2)}

CANDIDATE RESUME EVIDENCE:
{json.dumps(resume_data, indent=2)}

DETERMINISTIC COMPETENCY MATRIX (Verified Evidence):
{json.dumps(matrix_data, indent=2)}

{SCHEMA_INSTRUCTION}
"""
        try:
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
            start_time = time.time()
            from ai_engine.key_pool import gemini_key_pool
            max_keys = len(gemini_key_pool.keys) if gemini_key_pool.keys else 1
            response = llm.invoke(
                messages,
                timeout=AI_ANALYSIS_TIMEOUT_SECONDS,
                pool_max_retries=max_keys,
                fail_fast=True,
            )
            elapsed = time.time() - start_time
            logger.info("Gemini resume analysis completed in %.2f seconds.", elapsed)

            content_obj = response.content
            if isinstance(content_obj, list):
                # Handle multimodal list format from LangChain
                content_parts = []
                for part in content_obj:
                    if isinstance(part, str):
                        content_parts.append(part)
                    elif isinstance(part, dict) and "text" in part:
                        content_parts.append(part["text"])
                content = "".join(content_parts).strip()
            else:
                content = str(content_obj).strip()

            parsed = _extract_json_object(content)
            return sanitize_ai_analysis(parsed, profile, role)
        except Exception as e:
            logger.error(f"AI Resume Analysis failed: {e}")
            return None


def get_ai_analyzer() -> AIResumeAnalyzer:
    return AIResumeAnalyzer()
