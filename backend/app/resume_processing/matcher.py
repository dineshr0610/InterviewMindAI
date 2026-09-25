"""Selected-role matching engine for Module 1.

Performs multi-level matching (exact, semantic, evidence-based) against ONLY
the user-selected role profile dynamically loaded from technical_roles.json.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from app.resume_processing.config import get_role_by_identifier, load_scoring_config
from app.resume_processing.extractor import ExtractedCandidateProfile, ExtractedEvidence
from app.resume_processing.normalizer import get_normalizer
from app.resume_processing.schemas import MatchedArea

logger = logging.getLogger("interviewmind.resume_processing.matcher")


@dataclass
class RoleSkillCategory:
    category_name: str
    skills: List[str]


@dataclass
class RoleProfile:
    role_id: str
    role_name: str
    core_skills: List[str]
    programming_languages: List[str]
    technical_concepts: List[str]
    frameworks_tools: List[str]
    raw_role_data: Dict[str, Any]


@dataclass
class MatchResult:
    selected_role: str
    role_profile: RoleProfile
    matched_areas: List[MatchedArea]
    partial_matches: List[MatchedArea]
    missing_areas: List[str]
    unrelated_skills: List[str]
    category_matches: Dict[str, List[MatchedArea]] = field(default_factory=dict)
    candidate_profile: Optional[ExtractedCandidateProfile] = None


class RoleMatcher:
    """Matches a candidate profile strictly against one selected technical role."""

    def __init__(self) -> None:
        self.normalizer = get_normalizer()
        self.scoring_config = load_scoring_config()

    def build_role_profile(self, role_dict: Dict[str, Any]) -> RoleProfile:
        """Parse role definition JSON dynamically into structured categories."""
        role_id = role_dict.get("role_id", "custom_role")
        role_name = role_dict.get("role_name", "Technical Role")

        core = list(role_dict.get("core_skills", []))
        languages = list(role_dict.get("programming_languages", []))

        # Identify concepts from various domain keys in technical_roles.json
        concept_keys = [
            "concepts",
            "core_concepts",
            "machine_learning",
            "deep_learning",
            "statistics",
            "specializations",
            "security",
            "cloud_platforms",
            "core_services",
            "networking",
            "software_engineering",
            "advanced",
        ]
        concepts: List[str] = []
        for key in concept_keys:
            if key in role_dict and isinstance(role_dict[key], list):
                concepts.extend(role_dict[key])

        # Identify frameworks, libraries, databases, and tools
        tools_keys = [
            "frameworks",
            "libraries",
            "databases",
            "tools",
            "mlops",
            "containers",
            "infrastructure",
            "visualization",
            "testing",
            "devops",
            "development",
            "cloud_security",
        ]
        tools: List[str] = []
        for key in tools_keys:
            if key in role_dict and isinstance(role_dict[key], list):
                tools.extend(role_dict[key])

        return RoleProfile(
            role_id=role_id,
            role_name=role_name,
            core_skills=self._dedup(core),
            programming_languages=self._dedup(languages),
            technical_concepts=self._dedup(concepts),
            frameworks_tools=self._dedup(tools),
            raw_role_data=role_dict,
        )

    def match(
        self,
        candidate: ExtractedCandidateProfile,
        selected_role_identifier: str,
    ) -> MatchResult:
        role_dict = get_role_by_identifier(selected_role_identifier)
        if not role_dict:
            raise ValueError(f"Role '{selected_role_identifier}' not found in technical_roles.json knowledge base.")

        role_profile = self.build_role_profile(role_dict)
        matching_rules = self.scoring_config.get("matching", {})
        semantic_threshold = float(matching_rules.get("semantic_match_threshold", 0.72))
        partial_threshold = float(matching_rules.get("partial_match_threshold", 0.55))

        all_role_skills_map: Dict[str, str] = {}
        for s in role_profile.core_skills:
            all_role_skills_map[s] = "core_skills"
        for s in role_profile.programming_languages:
            all_role_skills_map[s] = "programming_languages"
        for s in role_profile.technical_concepts:
            all_role_skills_map[s] = "technical_concepts"
        for s in role_profile.frameworks_tools:
            all_role_skills_map[s] = "frameworks_tools"

        matched_areas: List[MatchedArea] = []
        partial_matches: List[MatchedArea] = []
        missing_areas: List[str] = []
        matched_role_skills: Set[str] = set()
        category_matches: Dict[str, List[MatchedArea]] = {
            "core_skills": [],
            "programming_languages": [],
            "technical_concepts": [],
            "frameworks_tools": [],
        }

        # Check each role skill
        for role_skill, category in all_role_skills_map.items():
            match = self._match_single_skill(
                role_skill=role_skill,
                category=category,
                candidate=candidate,
                semantic_threshold=semantic_threshold,
                partial_threshold=partial_threshold,
            )

            if match:
                matched_role_skills.add(role_skill)
                if match.confidence >= semantic_threshold:
                    matched_areas.append(match)
                    category_matches[category].append(match)
                elif match.confidence >= partial_threshold:
                    partial_matches.append(match)
            else:
                missing_areas.append(role_skill)

        # Identify unrelated skills (skills present on resume but outside selected role)
        unrelated_skills: List[str] = []
        normalized_role_skills = {
            self.normalizer.normalize(s).lower() for s in all_role_skills_map.keys()
        }
        for cand_skill in candidate.all_skills:
            norm_cand = self.normalizer.normalize(cand_skill).lower()
            if norm_cand not in normalized_role_skills:
                unrelated_skills.append(cand_skill)

        return MatchResult(
            selected_role=role_profile.role_name,
            role_profile=role_profile,
            matched_areas=matched_areas,
            partial_matches=partial_matches,
            missing_areas=missing_areas,
            unrelated_skills=unrelated_skills,
            category_matches=category_matches,
            candidate_profile=candidate,
        )

    def _match_single_skill(
        self,
        role_skill: str,
        category: str,
        candidate: ExtractedCandidateProfile,
        semantic_threshold: float,
        partial_threshold: float,
    ) -> Optional[MatchedArea]:
        """Multi-level matching: Level 1 exact/normalized, Level 2 semantic, Level 3 evidence."""
        canonical_target = self.normalizer.normalize(role_skill)

        # Level 1: Exact / normalized alias match in extracted profile evidence
        for cand_topic, evidence_list in candidate.evidence_by_topic.items():
            if self.normalizer.is_alias_match(cand_topic, canonical_target):
                best_ev = self._select_best_evidence(evidence_list)
                confidence = self._calculate_evidence_confidence(best_ev, exact=True)
                return MatchedArea(
                    topic=role_skill,
                    category=category,
                    confidence=round(confidence, 2),
                    section=best_ev.section,
                    source=best_ev.source,
                    evidence=best_ev.evidence,
                )

        # Also search raw resume text for any occurrence of the target role skill or its aliases
        found = self.normalizer.find_in_text(candidate.raw_text, role_skill)
        if found:
            _, raw_match = found
            # Locate snippet
            evidence_snippet, section_name, source_name = self._find_context_snippet(
                candidate, role_skill, raw_match
            )
            confidence = 0.90 if section_name in ("Projects", "Work Experience") else 0.85
            return MatchedArea(
                topic=role_skill,
                category=category,
                confidence=round(confidence, 2),
                section=section_name,
                source=source_name,
                evidence=evidence_snippet,
            )

        # Level 2: Semantic conceptual matching (e.g. "Customer Churn Prediction" -> "Classification")
        semantic_match = self._semantic_concept_match(role_skill, candidate)
        if semantic_match:
            score, snippet, sec, src = semantic_match
            if score >= partial_threshold:
                return MatchedArea(
                    topic=role_skill,
                    category=category,
                    confidence=round(score, 2),
                    section=sec,
                    source=src,
                    evidence=snippet,
                )

        return None

    def _select_best_evidence(self, evidence_list: List[ExtractedEvidence]) -> ExtractedEvidence:
        """Prioritize concrete project/work experience evidence over plain skill list mentions."""
        if not evidence_list:
            return ExtractedEvidence(
                topic="",
                section="Resume",
                source="Resume",
                evidence="Demonstrated in resume.",
                raw_match="",
            )

        def score_ev(ev: ExtractedEvidence) -> int:
            score = 0
            if ev.section in ("Projects", "Work Experience"):
                score += 50
            if len(ev.evidence) > 30:
                score += 20
            # Action verbs indicate practical application
            action_verbs = ["built", "developed", "created", "implemented", "designed", "trained", "deployed", "optimized"]
            if any(v in ev.evidence.lower() for v in action_verbs):
                score += 30
            return score

        return max(evidence_list, key=score_ev)

    def _calculate_evidence_confidence(self, ev: ExtractedEvidence, exact: bool) -> float:
        """Calculate confidence based on evidence quality and section."""
        base = 0.95 if exact else 0.80
        if ev.section == "Projects":
            base += 0.03
        elif ev.section == "Work Experience":
            base += 0.04
        elif ev.section == "Skills":
            base -= 0.05
        return min(1.0, max(0.5, base))

    def _find_context_snippet(
        self,
        candidate: ExtractedCandidateProfile,
        skill: str,
        raw_match: str,
    ) -> Tuple[str, str, str]:
        """Find the sentence and section where a raw match appears."""
        if candidate.parsed_resume:
            for sec_name, sec in candidate.parsed_resume.sections.items():
                sec_disp = self.normalizer.normalize(sec_name).title()
                for item in sec.items:
                    for bullet in item.bullet_points or [item.description]:
                        if re.search(rf"\b{re.escape(raw_match)}\b", bullet, re.IGNORECASE):
                            return bullet.strip(), sec_disp, item.title or sec_disp
                    if re.search(rf"\b{re.escape(raw_match)}\b", item.raw_text, re.IGNORECASE):
                        return item.raw_text[:200].strip(), sec_disp, item.title or sec_disp

        # Fallback to sentence search
        if candidate.parsed_resume:
            for sentence in candidate.parsed_resume.all_sentences:
                if re.search(rf"\b{re.escape(raw_match)}\b", sentence, re.IGNORECASE):
                    return sentence.strip(), "General Resume", "Resume"

        return f"Demonstrated knowledge of {skill}.", "Resume", "Resume"

    def _semantic_concept_match(
        self,
        role_concept: str,
        candidate: ExtractedCandidateProfile,
    ) -> Optional[Tuple[float, str, str, str]]:
        """
        Semantic matching rule: Relates conceptual terms (like Classification, Supervised Learning,
        REST API, Microservices, CI/CD) to contextual phrases in projects and experience.
        """
        concept_lower = role_concept.lower()

        CONCEPT_ASSOCIATIONS: Dict[str, List[Tuple[str, float]]] = {
            "machine learning": [
                ("classification model", 0.94),
                ("regression model", 0.94),
                ("predictive model", 0.92),
                ("trained model", 0.90),
                ("xgboost", 0.93),
                ("random forest", 0.93),
                ("scikit-learn", 0.92),
                ("churn prediction", 0.90),
            ],
            "supervised learning": [
                ("classification", 0.90),
                ("regression", 0.90),
                ("labeled data", 0.85),
                ("supervised", 0.95),
            ],
            "unsupervised learning": [
                ("clustering", 0.92),
                ("k-means", 0.92),
                ("pca", 0.90),
                ("dimensionality reduction", 0.90),
            ],
            "classification": [
                ("classification", 0.95),
                ("classifier", 0.95),
                ("churn prediction", 0.88),
                ("fraud detection", 0.88),
                ("sentiment analysis", 0.85),
                ("logistic regression", 0.90),
                ("xgboost", 0.85),
            ],
            "regression": [
                ("regression", 0.95),
                ("price prediction", 0.85),
                ("forecasting", 0.85),
                ("linear regression", 0.90),
            ],
            "deep learning": [
                ("neural network", 0.92),
                ("cnn", 0.90),
                ("rnn", 0.90),
                ("lstm", 0.90),
                ("transformer", 0.92),
                ("pytorch", 0.93),
                ("tensorflow", 0.93),
            ],
            "feature engineering": [
                ("feature engineering", 0.95),
                ("feature extraction", 0.92),
                ("preprocessing", 0.85),
                ("data normalization", 0.85),
                ("one-hot encoding", 0.90),
            ],
            "model training": [
                ("model training", 0.95),
                ("trained a", 0.90),
                ("trained model", 0.92),
                ("training model", 0.90),
                ("fine-tuned", 0.90),
                ("hyperparameter tuning", 0.88),
            ],
            "model evaluation": [
                ("roc-auc", 0.92),
                ("f1-score", 0.92),
                ("precision", 0.85),
                ("recall", 0.85),
                ("cross-validation", 0.90),
                ("accuracy of", 0.85),
                ("confusion matrix", 0.90),
            ],
            "data preprocessing": [
                ("preprocessing", 0.95),
                ("data cleaning", 0.92),
                ("cleaned data", 0.90),
                ("imputation", 0.88),
                ("data transformation", 0.88),
            ],
            "state management": [
                ("redux", 0.95),
                ("state management", 0.95),
                ("context api", 0.90),
                ("zustand", 0.90),
                ("vuex", 0.90),
                ("mobx", 0.90),
            ],
            "component architecture": [
                ("component", 0.92),
                ("components", 0.92),
                ("single page application", 0.90),
                ("spa", 0.88),
                ("reusable ui", 0.88),
                ("react", 0.85),
            ],
            "asynchronous javascript": [
                ("async", 0.92),
                ("await", 0.92),
                ("promises", 0.95),
                ("promises", 0.95),
                ("event loop", 0.95),
                ("fetch", 0.85),
                ("axios", 0.85),
            ],
            "dom": [
                ("dom", 0.95),
                ("document object model", 0.95),
                ("virtual dom", 0.92),
                ("event handling", 0.85),
            ],
            "responsive web design": [
                ("responsive", 0.95),
                ("mobile-first", 0.92),
                ("media queries", 0.90),
                ("tailwind", 0.85),
                ("flexbox", 0.88),
                ("grid layout", 0.88),
            ],
            "rest api": [
                ("rest api", 0.95),
                ("restful", 0.95),
                ("endpoints", 0.85),
                ("fastapi", 0.90),
                ("express", 0.90),
                ("postman", 0.85),
            ],
            "microservices": [
                ("microservice", 0.95),
                ("microservices", 0.95),
                ("distributed services", 0.88),
                ("event-driven", 0.85),
                ("grpc", 0.90),
                ("service-oriented", 0.85),
            ],
            "database management": [
                ("sql", 0.88),
                ("postgresql", 0.90),
                ("mongodb", 0.90),
                ("mysql", 0.90),
                ("database", 0.90),
                ("schema design", 0.92),
                ("indexing", 0.88),
            ],
            "authentication": [
                ("jwt", 0.92),
                ("oauth", 0.92),
                ("authentication", 0.95),
                ("auth", 0.90),
                ("login", 0.85),
            ],
            "authorization": [
                ("rbac", 0.92),
                ("authorization", 0.95),
                ("permissions", 0.88),
                ("roles and permissions", 0.90),
            ],
            "ci/cd": [
                ("ci/cd", 0.95),
                ("continuous integration", 0.95),
                ("continuous deployment", 0.95),
                ("pipeline", 0.85),
                ("github actions", 0.92),
                ("jenkins", 0.92),
            ],
            "containerization": [
                ("docker", 0.95),
                ("container", 0.92),
                ("containers", 0.92),
                ("kubernetes", 0.92),
                ("k8s", 0.90),
            ],
            "infrastructure as code": [
                ("terraform", 0.95),
                ("ansible", 0.92),
                ("cloudformation", 0.92),
                ("iac", 0.95),
            ],
            "data analysis": [
                ("data analysis", 0.95),
                ("exploratory data analysis", 0.95),
                ("eda", 0.92),
                ("analyzed data", 0.90),
                ("insights", 0.85),
            ],
            "data visualization": [
                ("visualization", 0.95),
                ("dashboard", 0.92),
                ("matplotlib", 0.92),
                ("seaborn", 0.92),
                ("power bi", 0.95),
                ("tableau", 0.95),
                ("charts", 0.85),
            ],
            "data structures": [
                ("data structures", 0.95),
                ("trees", 0.85),
                ("graphs", 0.85),
                ("hash tables", 0.88),
                ("leetcode", 0.85),
            ],
            "algorithms": [
                ("algorithms", 0.95),
                ("dynamic programming", 0.90),
                ("sorting", 0.85),
                ("time complexity", 0.88),
            ],
            "object oriented programming": [
                ("oop", 0.95),
                ("object-oriented", 0.95),
                ("object oriented", 0.95),
                ("classes and objects", 0.90),
                ("inheritance", 0.88),
                ("polymorphism", 0.88),
            ],
            "api design": [
                ("api design", 0.95),
                ("api-first", 0.95),
                ("modular, api-first", 0.95),
                ("rest apis", 0.90),
                ("rest api", 0.90),
                ("swagger", 0.90),
                ("openapi", 0.90),
            ],
            "problem solving": [
                ("problem solving", 0.95),
                ("leetcode", 0.92),
                ("data structures and algorithms", 0.92),
                ("coding interview", 0.90),
                ("solved 300+", 0.92),
                ("competitive programming", 0.92),
            ],
            "software development": [
                ("software development", 0.95),
                ("developing an", 0.90),
                ("developed", 0.88),
                ("application development", 0.92),
            ],
            "machine learning": [
                ("machine learning", 0.95),
                ("ml", 0.92),
                ("classification model", 0.95),
                ("rag", 0.92),
                ("retrieval-augmented generation", 0.95),
                ("embeddings", 0.92),
                ("chromadb", 0.90),
                ("hugging face", 0.92),
                ("langgraph", 0.92),
                ("scikit-learn", 0.92),
                ("xgboost", 0.92),
            ],
            "network security": [
                ("firewall", 0.90),
                ("ids", 0.90),
                ("ips", 0.90),
                ("network security", 0.95),
                ("vpn", 0.90),
            ],
            "threat detection": [
                ("threat detection", 0.95),
                ("vulnerability assessment", 0.95),
                ("penetration testing", 0.92),
                ("security audit", 0.88),
            ],
        }

        associations = CONCEPT_ASSOCIATIONS.get(concept_lower, [])
        if not associations:
            return None

        # Check candidate's parsed items and sentences
        if candidate.parsed_resume:
            for sec_name, sec in candidate.parsed_resume.sections.items():
                sec_disp = self.normalizer.normalize(sec_name).title()
                for item in sec.items:
                    for bullet in item.bullet_points or [item.description]:
                        b_lower = bullet.lower()
                        for assoc_phrase, conf in associations:
                            if assoc_phrase in b_lower:
                                return conf, bullet.strip(), sec_disp, item.title or sec_disp

        for sentence in (candidate.parsed_resume.all_sentences if candidate.parsed_resume else []):
            s_lower = sentence.lower()
            for assoc_phrase, conf in associations:
                if assoc_phrase in s_lower:
                    return conf, sentence.strip(), "General Resume", "Resume"

        return None

    @staticmethod
    def _dedup(items: List[str]) -> List[str]:
        seen = set()
        out = []
        for item in items:
            cleaned = item.strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                out.append(cleaned)
        return out


# Global matcher instance
_matcher_instance: Optional[RoleMatcher] = None


def get_matcher() -> RoleMatcher:
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = RoleMatcher()
    return _matcher_instance
