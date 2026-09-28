"""Skill normalization engine for Module 1.

Maps raw terms, aliases, and variations to canonical skill names using skill_aliases.json.
Supports punctuation-aware and case-insensitive matching.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from app.resume_processing.config import load_skill_aliases


class SkillNormalizer:
    """Normalizes candidate skill tokens and phrases to canonical knowledge base terms."""

    def __init__(self) -> None:
        self._alias_to_canonical: Dict[str, str] = {}
        self._canonical_to_aliases: Dict[str, Set[str]] = {}
        self._build_maps()

    def _build_maps(self) -> None:
        alias_data = load_skill_aliases()
        self._alias_to_canonical.clear()
        self._canonical_to_aliases.clear()

        for canonical, aliases in alias_data.items():
            canonical_clean = canonical.strip()
            aliases_set = set()

            # Canonical itself in lowercase
            aliases_set.add(canonical_clean.lower())
            self._alias_to_canonical[canonical_clean.lower()] = canonical_clean

            for alias in aliases:
                alias_clean = alias.strip().lower()
                if alias_clean:
                    aliases_set.add(alias_clean)
                    self._alias_to_canonical[alias_clean] = canonical_clean

            self._canonical_to_aliases[canonical_clean] = aliases_set

    def normalize(self, term: str) -> str:
        """Return the canonical skill name if known, else return cleaned title-cased term."""
        if not term:
            return ""

        clean = term.strip()
        lower = clean.lower()

        # Direct alias lookup
        if lower in self._alias_to_canonical:
            return self._alias_to_canonical[lower]

        # Normalized without punctuation (e.g. "scikit learn" vs "scikit-learn")
        normalized_str = re.sub(r"[\s\-_.]+", " ", lower).strip()
        for alias_key, canonical in self._alias_to_canonical.items():
            alias_norm = re.sub(r"[\s\-_.]+", " ", alias_key).strip()
            if normalized_str == alias_norm:
                return canonical

        # Default: keep clean original
        return clean

    def is_alias_match(self, term: str, canonical_target: str) -> bool:
        """Check if a given term matches a canonical target or any of its aliases."""
        if not term or not canonical_target:
            return False

        norm_term = self.normalize(term).lower()
        norm_target = canonical_target.strip().lower()
        if norm_term == norm_target:
            return True

        target_aliases = self._canonical_to_aliases.get(canonical_target, set())
        if term.strip().lower() in target_aliases:
            return True

        return False

    def find_in_text(self, text: str, canonical_or_term: str) -> Optional[Tuple[str, str]]:
        """
        Search for canonical_or_term or any of its aliases within text.
        Returns (canonical_name, matched_substring) or None if not found.
        """
        if not text or not canonical_or_term:
            return None

        # Identify canonical name and its aliases
        canonical = self.normalize(canonical_or_term)
        aliases = list(self._canonical_to_aliases.get(canonical, {canonical_or_term.lower()}))
        if canonical.lower() not in aliases:
            aliases.append(canonical.lower())

        # Sort aliases by length descending so longer phrases match before subwords
        aliases.sort(key=len, reverse=True)

        for alias in aliases:
            # Punctuation-safe regex pattern
            # For words containing symbols like ++, #, ., -, handle boundaries carefully
            escaped = re.escape(alias)
            # If starts/ends with alphanumeric, require word boundary
            prefix = r"(?<![a-zA-Z0-9])" if alias[0].isalnum() else r""
            suffix = r"(?![a-zA-Z0-9])" if alias[-1].isalnum() else r""
            pattern = rf"{prefix}{escaped}{suffix}"

            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return canonical, match.group(0)

        return None


# Global normalizer instance
_normalizer_instance: Optional[SkillNormalizer] = None


def get_normalizer() -> SkillNormalizer:
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = SkillNormalizer()
    return _normalizer_instance
