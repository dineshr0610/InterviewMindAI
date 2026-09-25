"""Technical information and evidence extraction engine.

Extracts technical skills, frameworks, libraries, tools, and concepts across all
resume sections (Skills, Projects, Experience, Certifications, etc.), preserving
traceable evidence, section metadata, and project/source contexts.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from app.resume_processing.normalizer import get_normalizer
from app.resume_processing.parser import ParsedResume, ResumeItem, parse_resume_text

logger = logging.getLogger("interviewmind.resume_processing.extractor")


@dataclass
class ExtractedEvidence:
    """Evidence occurrence of a technical topic within the resume."""
    topic: str
    section: str
    source: str
    evidence: str
    raw_match: str


@dataclass
class ExtractedCandidateProfile:
    """Structured extraction of candidate technical competencies and evidence."""
    candidate_name: Optional[str] = None
    all_skills: Set[str] = field(default_factory=set)
    evidence_by_topic: Dict[str, List[ExtractedEvidence]] = field(default_factory=dict)
    projects: List[Dict[str, any]] = field(default_factory=list)
    experience: List[Dict[str, any]] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    raw_text: str = ""
    parsed_resume: Optional[ParsedResume] = None


class TechnicalExtractor:
    """Extracts technical topics and associated evidence from parsed resume blocks."""

    def __init__(self) -> None:
        self.normalizer = get_normalizer()

    def extract(
        self,
        resume: ParsedResume | str,
        candidate_name: Optional[str] = None,
    ) -> ExtractedCandidateProfile:
        if isinstance(resume, str):
            parsed = parse_resume_text(resume)
        else:
            parsed = resume

        profile = ExtractedCandidateProfile(
            candidate_name=candidate_name,
            raw_text=parsed.cleaned_text,
            parsed_resume=parsed,
        )

        # 1. Traverse each section
        for sec_name, section in parsed.sections.items():
            sec_display = self._format_section_name(sec_name)

            for item in section.items:
                source_title = item.title if item.title and item.title.lower() != sec_name.lower() else sec_display

                # Search within bullet points / description
                sentences = item.bullet_points or [item.description]
                for sentence in sentences:
                    clean_s = sentence.strip()
                    if not clean_s:
                        continue

                    matches = self._find_topics_in_text(clean_s)
                    for canonical_topic, matched_str in matches:
                        profile.all_skills.add(canonical_topic)
                        evidence = ExtractedEvidence(
                            topic=canonical_topic,
                            section=sec_display,
                            source=source_title,
                            evidence=clean_s,
                            raw_match=matched_str,
                        )
                        if canonical_topic not in profile.evidence_by_topic:
                            profile.evidence_by_topic[canonical_topic] = []
                        profile.evidence_by_topic[canonical_topic].append(evidence)

                # Record structured projects
                if sec_name == "projects":
                    proj_topics = {
                        top for top, _ in self._find_topics_in_text(item.raw_text)
                    }
                    profile.projects.append(
                        {
                            "title": item.title,
                            "description": item.description,
                            "bullet_points": item.bullet_points,
                            "technologies": sorted(proj_topics),
                            "raw_text": item.raw_text,
                        }
                    )

                # Record structured experience
                elif sec_name == "experience":
                    exp_topics = {
                        top for top, _ in self._find_topics_in_text(item.raw_text)
                    }
                    profile.experience.append(
                        {
                            "title": item.title,
                            "organization": item.organization,
                            "description": item.description,
                            "bullet_points": item.bullet_points,
                            "technologies": sorted(exp_topics),
                            "raw_text": item.raw_text,
                        }
                    )

                elif sec_name == "certifications":
                    profile.certifications.extend(item.bullet_points or [item.description])

        # 2. Also scan entire text for any topics that might have been in unsectioned blocks
        for sentence in parsed.all_sentences:
            matches = self._find_topics_in_text(sentence)
            for canonical_topic, matched_str in matches:
                if canonical_topic not in profile.evidence_by_topic:
                    profile.all_skills.add(canonical_topic)
                    profile.evidence_by_topic[canonical_topic] = [
                        ExtractedEvidence(
                            topic=canonical_topic,
                            section="General Resume",
                            source="Resume Content",
                            evidence=sentence,
                            raw_match=matched_str,
                        )
                    ]

        return profile

    def _find_topics_in_text(self, text: str) -> List[Tuple[str, str]]:
        """Find all canonical skills present in the given text snippet."""
        if not text:
            return []

        results: List[Tuple[str, str]] = []
        seen: Set[str] = set()

        # Check canonical aliases map
        for canonical, aliases in self.normalizer._canonical_to_aliases.items():
            for alias in aliases:
                escaped = re.escape(alias)
                prefix = r"(?<![a-zA-Z0-9])" if alias[0].isalnum() else r""
                suffix = r"(?![a-zA-Z0-9])" if alias[-1].isalnum() else r""
                pattern = rf"{prefix}{escaped}{suffix}"

                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    if canonical not in seen:
                        seen.add(canonical)
                        results.append((canonical, m.group(0)))
                    break

        return results

    @staticmethod
    def _format_section_name(name: str) -> str:
        mapping = {
            "skills": "Skills",
            "projects": "Projects",
            "experience": "Work Experience",
            "certifications": "Certifications",
            "education": "Education",
            "summary": "Summary",
            "achievements": "Achievements",
        }
        return mapping.get(name.lower(), name.title())


# Global extractor instance
_extractor_instance: Optional[TechnicalExtractor] = None


def get_extractor() -> TechnicalExtractor:
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = TechnicalExtractor()
    return _extractor_instance
