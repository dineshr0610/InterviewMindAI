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


def normalize_role_name(role_identifier: str) -> str:
    """Canonical role normalization as per Phase 6 requirements."""
    if not role_identifier:
        return ""
        
    r = role_identifier.lower().strip()
    
    if "python" in r:
        return "Python Developer"
    if "java" in r and "javascript" not in r:
        return "Java Developer"
    if "frontend" in r or "front-end" in r or "front end" in r or "react" in r or "ui" in r:
        return "Frontend Developer"
    if "backend" in r or "back-end" in r or "back end" in r or "api" in r or "server" in r:
        return "Backend Developer"
    if "full stack" in r or "full-stack" in r or "fullstack" in r:
        return "Full Stack Developer"
    if "devops" in r or "cloud" in r or "sre" in r or "infrastructure" in r:
        return "DevOps / Cloud Engineer"
    if "database" in r or "sql" in r or "dba" in r or "data engineer" in r:
        return "Database Developer"
    if "data analyst" in r or "data analysis" in r or "analytics" in r:
        return "Data Analyst"
    if "ai engineer" in r or "artificial intelligence" in r or "genai" in r or "llm" in r:
        return "AI Engineer"
    if "ml engineer" in r or "machine learning" in r or "ml" in r.split():
        return "ML Engineer"
        
    return role_identifier.strip().title()

def get_role_by_identifier(role_identifier: str) -> Optional[Dict[str, Any]]:
    """Find a role dynamically by canonical role mapping. Do not use fallbacks."""
    if not role_identifier:
        return None

    canonical = normalize_role_name(role_identifier)
    roles = list_roles()

    # 1. Exact match on canonical role_name
    for role in roles:
        if role.get("role_name") == canonical:
            return role

    # 2. Try matching by clean role_id
    target_clean = canonical.lower().replace(" ", "_").replace("/", "").replace("__", "_")
    for role in roles:
        if role.get("role_id") == target_clean:
            return role
            
    # 3. Substring / keyword match
    target_norm = _normalize_name(canonical)
    for role in roles:
        role_name_norm = _normalize_name(role.get("role_name", ""))
        role_id_norm = _normalize_name(role.get("role_id", ""))
        if target_norm in role_name_norm or target_norm in role_id_norm:
            return role
        if role_name_norm in target_norm or role_id_norm in target_norm:
            return role

    # No fallback to Full Stack Developer or roles[0]. Return None to trigger ValueError.
    return None

