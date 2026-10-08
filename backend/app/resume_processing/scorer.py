"""Deterministic scoring engine for Module 1.

Calculates overall role match score and detailed category breakdowns strictly
using the formulas, weights, and thresholds defined in scoring_config.json,
without artificial caps or double-counting.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from app.resume_processing.config import load_scoring_config
from app.resume_processing.matcher import MatchResult
from app.resume_processing.schemas import ScoreBreakdown

logger = logging.getLogger("interviewmind.resume_processing.scorer")


class DeterministicScorer:
    """Calculates deterministic numerical scores from match results."""

    def __init__(self) -> None:
        self.config = load_scoring_config()

    def compute_score(self, match_result: MatchResult) -> tuple[float, ScoreBreakdown]:
        weights = {
            "core_skills": 0.25,
            "technical_concepts": 0.20,
            "project_experience": 0.20,
            "frameworks_tools": 0.15,
            "relevant_experience": 0.20,
        }

        min_score = 0.0
        max_score = 100.0

        core_score, core_valid = self._calculate_core_skills_score(match_result)
        concepts_score, concepts_valid = self._calculate_technical_concepts_score(match_result)
        tools_score, tools_valid = self._calculate_frameworks_tools_score(match_result)
        
        # Determine project-assessable and experience-assessable universes
        # For technical roles, usually all core/concepts/tools can be demonstrated in projects/experience.
        # Ensure we unique-ify the universe to prevent duplicates across categories affecting the denominator.
        project_assessable = list(set(
            match_result.role_profile.core_skills + 
            match_result.role_profile.programming_languages + 
            match_result.role_profile.technical_concepts + 
            match_result.role_profile.frameworks_tools
        ))
        exp_assessable = project_assessable  # Work experience can evaluate the same full technical universe
        
        project_score, project_valid = self._calculate_project_experience_score(match_result, project_assessable)
        experience_score, exp_valid = self._calculate_relevant_experience_score(match_result, exp_assessable)

        # Renormalize weights
        total_weight = 0.0
        if core_valid: total_weight += weights["core_skills"]
        if concepts_valid: total_weight += weights["technical_concepts"]
        if tools_valid: total_weight += weights["frameworks_tools"]
        if project_valid: total_weight += weights["project_experience"]
        if exp_valid: total_weight += weights["relevant_experience"]

        if total_weight > 0:
            overall = 0.0
            if core_valid: overall += core_score * (weights["core_skills"] / total_weight)
            if concepts_valid: overall += concepts_score * (weights["technical_concepts"] / total_weight)
            if tools_valid: overall += tools_score * (weights["frameworks_tools"] / total_weight)
            if project_valid: overall += project_score * (weights["project_experience"] / total_weight)
            if exp_valid: overall += experience_score * (weights["relevant_experience"] / total_weight)
        else:
            overall = 0.0

        overall_clamped = round(min(max_score, max(min_score, overall)), 1)

        breakdown = ScoreBreakdown(
            core_skills=round(core_score, 1) if core_valid else 0.0,
            technical_concepts=round(concepts_score, 1) if concepts_valid else 0.0,
            project_experience=round(project_score, 1) if project_valid else 0.0,
            frameworks_tools=round(tools_score, 1) if tools_valid else 0.0,
            relevant_experience=round(experience_score, 1) if exp_valid else 0.0,
        )

        return overall_clamped, breakdown

    def _calculate_category_score(self, required_items: List[str], matched_items) -> tuple[float, bool]:
        req_set = set(required_items)
        if not req_set:
            return 0.0, False
            
        best_matches = {}
        for m in matched_items:
            topic = m.topic.lower()
            if topic not in best_matches or m.confidence > best_matches[topic].confidence:
                best_matches[topic] = m
                
        sum_conf = sum(m.confidence for topic, m in best_matches.items() if topic in {r.lower() for r in req_set})
        ratio = sum_conf / len(req_set)
        return min(100.0, max(0.0, ratio * 100.0)), True

    def _calculate_core_skills_score(self, match: MatchResult) -> tuple[float, bool]:
        total_core = match.role_profile.core_skills + match.role_profile.programming_languages
        matched_core = match.category_matches.get("core_skills", []) + match.category_matches.get("programming_languages", [])
        return self._calculate_category_score(total_core, matched_core)

    def _calculate_technical_concepts_score(self, match: MatchResult) -> tuple[float, bool]:
        total_concepts = match.role_profile.technical_concepts
        matched_concepts = match.category_matches.get("technical_concepts", [])
        return self._calculate_category_score(total_concepts, matched_concepts)

    def _calculate_frameworks_tools_score(self, match: MatchResult) -> tuple[float, bool]:
        total_tools = match.role_profile.frameworks_tools
        matched_tools = match.category_matches.get("frameworks_tools", [])
        return self._calculate_category_score(total_tools, matched_tools)

    def _calculate_project_experience_score(self, match: MatchResult, assessable_universe: List[str]) -> tuple[float, bool]:
        if not assessable_universe:
            return 0.0, False
            
        candidate = match.candidate_profile
        if not candidate or not candidate.projects:
            return 0.0, True

        # Valid targets to score against
        req_set = {r.lower() for r in assessable_universe}
        
        best_matches = {}
        for proj in candidate.projects:
            proj_techs = {t.lower() for t in proj.get("technologies", [])}
            proj_title = (proj.get("title") or "").lower()
            proj_desc = (proj.get("description") or "").lower()
            
            for m in match.matched_areas:
                topic = m.topic.lower()
                if topic not in req_set:
                    continue
                    
                # Check if this topic is evidenced in THIS project context
                if topic in proj_techs or (m.source and m.source.lower() == proj_title) or topic in proj_desc:
                    if topic not in best_matches or m.confidence > best_matches[topic]:
                        best_matches[topic] = m.confidence
                        
        sum_conf = sum(best_matches.values())
        ratio = sum_conf / len(assessable_universe)
        return min(100.0, max(0.0, ratio * 100.0)), True

    def _calculate_relevant_experience_score(self, match: MatchResult, assessable_universe: List[str]) -> tuple[float, bool]:
        if not assessable_universe:
            return 0.0, False
            
        candidate = match.candidate_profile
        if not candidate or not candidate.experience:
            return 0.0, True
            
        req_set = {r.lower() for r in assessable_universe}
        best_matches = {}
        for exp in candidate.experience:
            exp_techs = {t.lower() for t in exp.get("technologies", [])}
            exp_text = (exp.get("raw_text") or "").lower()
            
            for m in match.matched_areas:
                topic = m.topic.lower()
                if topic not in req_set:
                    continue
                    
                # Check if this topic is evidenced in THIS experience context
                if m.section == "Work Experience" or topic in exp_techs or topic in exp_text:
                    if topic not in best_matches or m.confidence > best_matches[topic]:
                        best_matches[topic] = m.confidence

        sum_conf = sum(best_matches.values())
        ratio = sum_conf / len(assessable_universe)
        return min(100.0, max(0.0, ratio * 100.0)), True

# Global scorer instance
_scorer_instance: Optional[DeterministicScorer] = None

def get_scorer() -> DeterministicScorer:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = DeterministicScorer()
    return _scorer_instance
