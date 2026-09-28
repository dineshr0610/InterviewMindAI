"""Configuration and dynamic dataset loader for Module 1.

Loads the role knowledge base, skill aliases, and scoring configuration
dynamically from JSON files so that data can be updated or expanded without
modifying application code.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("interviewmind.resume_processing.config")

# Candidate directories for locating dataset files
_DATA_DIR_CANDIDATES = [
    Path(__file__).resolve().parent / "data",
    Path(__file__).resolve().parents[3] / "module1_antigravity" / "data",
    Path(os.getcwd()) / "module1_antigravity" / "data",
    Path(os.getcwd()) / "backend" / "app" / "resume_processing" / "data",
]

_SCHEMA_DIR_CANDIDATES = [
    Path(__file__).resolve().parent / "schemas",
    Path(__file__).resolve().parents[3] / "module1_antigravity" / "schemas",
    Path(os.getcwd()) / "module1_antigravity" / "schemas",
    Path(os.getcwd()) / "backend" / "app" / "resume_processing" / "schemas",
]


def _find_file(filename: str, search_dirs: List[Path]) -> Path:
    for candidate in search_dirs:
        filepath = candidate / filename
        if filepath.is_file():
            return filepath
    # Default fallback
    return search_dirs[0] / filename


_TECHNICAL_ROLES_CACHE: Optional[Dict[str, Any]] = None
_SKILL_ALIASES_CACHE: Optional[Dict[str, List[str]]] = None
_SCORING_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def load_technical_roles(force_reload: bool = False) -> Dict[str, Any]:
    """Load role knowledge base from technical_roles.json dynamically."""
    global _TECHNICAL_ROLES_CACHE
    if _TECHNICAL_ROLES_CACHE is not None and not force_reload:
        return _TECHNICAL_ROLES_CACHE

    filepath = _find_file("technical_roles.json", _DATA_DIR_CANDIDATES)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        _TECHNICAL_ROLES_CACHE = data
        logger.info("Loaded technical roles from %s (%d roles)", filepath, len(data.get("roles", [])))
        return data
    except Exception as exc:
        logger.error("Failed to load technical_roles.json from %s: %s", filepath, exc)
        raise RuntimeError(f"Could not load technical_roles.json: {exc}") from exc


def load_skill_aliases(force_reload: bool = False) -> Dict[str, List[str]]:
    """Load canonical skill aliases dictionary dynamically from skill_aliases.json."""
    global _SKILL_ALIASES_CACHE
    if _SKILL_ALIASES_CACHE is not None and not force_reload:
        return _SKILL_ALIASES_CACHE

    filepath = _find_file("skill_aliases.json", _DATA_DIR_CANDIDATES)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        _SKILL_ALIASES_CACHE = data
        logger.info("Loaded skill aliases from %s (%d canonical skills)", filepath, len(data))
        return data
    except Exception as exc:
        logger.error("Failed to load skill_aliases.json from %s: %s", filepath, exc)
        raise RuntimeError(f"Could not load skill_aliases.json: {exc}") from exc


def load_scoring_config(force_reload: bool = False) -> Dict[str, Any]:
    """Load scoring configuration dynamically from scoring_config.json."""
    global _SCORING_CONFIG_CACHE
    if _SCORING_CONFIG_CACHE is not None and not force_reload:
        return _SCORING_CONFIG_CACHE

    filepath = _find_file("scoring_config.json", _DATA_DIR_CANDIDATES)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        _SCORING_CONFIG_CACHE = data
        logger.info("Loaded scoring config from %s", filepath)
        return data
    except Exception as exc:
        logger.error("Failed to load scoring_config.json from %s: %s", filepath, exc)
        raise RuntimeError(f"Could not load scoring_config.json: {exc}") from exc


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def list_roles() -> List[Dict[str, Any]]:
    """List all available roles loaded dynamically from technical_roles.json."""
    data = load_technical_roles()
    return data.get("roles", [])


def get_role_by_identifier(role_identifier: str) -> Optional[Dict[str, Any]]:
    """Find a role dynamically by role_id, role_name, or fuzzy alias matching."""
    if not role_identifier:
        return None

    roles = list_roles()
    target = _normalize_name(role_identifier)

    # 1. Exact match on role_id or role_name
    for role in roles:
        if _normalize_name(role.get("role_id", "")) == target:
            return role
        if _normalize_name(role.get("role_name", "")) == target:
            return role

    # 2. Match with replaced underscores/hyphens
    target_clean = role_identifier.strip().lower().replace("-", "_").replace(" ", "_")
    for role in roles:
        if role.get("role_id", "").lower() == target_clean:
            return role

    # 3. Substring / keyword match (e.g. 'ML' -> 'ML Engineer', 'Fullstack' -> 'Full Stack Developer')
    for role in roles:
        role_name_norm = _normalize_name(role.get("role_name", ""))
        role_id_norm = _normalize_name(role.get("role_id", ""))
        if target in role_name_norm or target in role_id_norm:
            return role
        if role_name_norm in target or role_id_norm in target:
            return role

    # 4. Fallback to default first role if nothing matches
    return None
