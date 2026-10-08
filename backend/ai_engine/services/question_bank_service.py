"""Local Question Bank Service for InterviewMind AI.

Provides safe, in-memory, role-aware question retrieval from the canonical
frozen 3,146-question dataset (data/question_bank_v3/canonical_questions.jsonl).
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("interviewmind.ai_engine.question_bank")

# Canonical Role Names
ROLE_BACKEND = "Backend Developer"
ROLE_FRONTEND = "Frontend Developer"
ROLE_FULLSTACK = "Full Stack Developer"
ROLE_PYTHON = "Python Developer"
ROLE_JAVA = "Java Developer"
ROLE_DEVOPS = "DevOps / Cloud Engineer"
ROLE_DATABASE = "Database Developer"
ROLE_DATA_ANALYST = "Data Analyst"
ROLE_AI = "AI Engineer"
ROLE_ML = "ML Engineer"

CANONICAL_ROLES: List[str] = [
    ROLE_BACKEND,
    ROLE_FRONTEND,
    ROLE_FULLSTACK,
    ROLE_PYTHON,
    ROLE_JAVA,
    ROLE_DEVOPS,
    ROLE_DATABASE,
    ROLE_DATA_ANALYST,
    ROLE_AI,
    ROLE_ML,
]


def normalize_role(role_name: Optional[str]) -> str:
    """
    Normalizes any role string variation into one of the 10 canonical role names.
    Handles 'backend_developer', 'Backend Developer', 'backend', etc.
    """
    if not role_name or not isinstance(role_name, str):
        return ROLE_BACKEND

    r = role_name.strip().lower().replace("-", " ").replace("_", " ")

    if "full stack" in r or "fullstack" in r:
        return ROLE_FULLSTACK
    if "frontend" in r or "front end" in r or "react" in r:
        return ROLE_FRONTEND
    if "backend" in r or "back end" in r:
        return ROLE_BACKEND
    if "python" in r:
        return ROLE_PYTHON
    if "java" in r and "javascript" not in r:
        return ROLE_JAVA
    if "devops" in r or "cloud" in r or "sre" in r or "infrastructure" in r:
        return ROLE_DEVOPS
    if "database" in r or "dba" in r or "sql" in r:
        return ROLE_DATABASE
    if "data analyst" in r or "analytics" in r or "bi" in r:
        return ROLE_DATA_ANALYST
    if "ai" in r or "artificial intelligence" in r or "genai" in r or "llm" in r:
        return ROLE_AI
    if "ml" in r or "machine learning" in r or "deep learning" in r:
        return ROLE_ML

    return ROLE_BACKEND


class QuestionBankService:
    """
    Thread-safe, singleton-backed local Question Bank service.
    Loads and caches questions in memory from the frozen canonical dataset.
    """

    _instance: Optional["QuestionBankService"] = None
    _init_lock = threading.Lock()

    def __init__(self, data_path: Optional[str] = None, jsonl_path: Optional[str] = None) -> None:
        self.lock = threading.Lock()
        self._loaded = False
        self._data_path = self._resolve_data_path(data_path or jsonl_path)
        self._all_records: List[Dict[str, Any]] = []
        self._by_role: Dict[str, List[Dict[str, Any]]] = {r: [] for r in CANONICAL_ROLES}
        if data_path or jsonl_path:
            self.load()

    def count(self) -> int:
        return self.total_records

    @classmethod
    def get_instance(cls, data_path: Optional[str] = None) -> "QuestionBankService":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    instance = cls(data_path=data_path)
                    instance.load()
                    cls._instance = instance
        return cls._instance

    def _resolve_data_path(self, custom_path: Optional[str] = None) -> Path:
        if custom_path:
            p = Path(custom_path)
            if p.exists():
                return p

        # Look in known backend locations
        base_dir = Path(__file__).resolve().parent.parent.parent
        candidates = [
            base_dir / "data" / "question_bank_v3" / "canonical_questions.jsonl",
            base_dir / "data" / "interview_question_bank_v2_generated.jsonl",
            Path("data/question_bank_v3/canonical_questions.jsonl").resolve(),
            Path("data/interview_question_bank_v2_generated.jsonl").resolve(),
        ]

        for cand in candidates:
            if cand.exists():
                return cand

        # Fallback to default expected path even if not yet checked
        return base_dir / "data" / "question_bank_v3" / "canonical_questions.jsonl"

    def load(self, force_reload: bool = False) -> int:
        """
        Safely loads records from the frozen JSONL dataset into memory.
        Validates records, skips malformed rows, and groups by canonical role.
        """
        with self.lock:
            if self._loaded and not force_reload:
                return len(self._all_records)

            if not self._data_path.exists():
                logger.warning(
                    "Question bank file not found at %s. Empty bank loaded.",
                    self._data_path,
                )
                self._all_records = []
                self._by_role = {r: [] for r in CANONICAL_ROLES}
                self._loaded = True
                return 0

            records: List[Dict[str, Any]] = []
            by_role: Dict[str, List[Dict[str, Any]]] = {r: [] for r in CANONICAL_ROLES}
            malformed_count = 0

            try:
                with open(self._data_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line_str = line.strip()
                        if not line_str:
                            continue
                        try:
                            obj = json.loads(line_str)
                            if not isinstance(obj, dict):
                                malformed_count += 1
                                continue

                            q_text = obj.get("question") or obj.get("text")
                            if not q_text or not isinstance(q_text, str) or len(q_text.strip()) < 10:
                                malformed_count += 1
                                continue

                            # Normalize role for rapid indexing
                            raw_role = obj.get("role") or obj.get("primary_role") or ""
                            canonical_role = normalize_role(raw_role)
                            obj["_canonical_role"] = canonical_role

                            records.append(obj)
                            by_role[canonical_role].append(obj)

                        except json.JSONDecodeError:
                            malformed_count += 1
                            continue
                        except Exception as parse_exc:
                            logger.debug("Line %d skipped due to parsing error: %s", line_num, parse_exc)
                            malformed_count += 1
                            continue

                self._all_records = records
                self._by_role = by_role
                self._loaded = True

                logger.info(
                    "QuestionBankService loaded %d questions (%d roles) from %s (skipped %d malformed).",
                    len(records),
                    len([r for r, qs in by_role.items() if qs]),
                    self._data_path.name,
                    malformed_count,
                )
                return len(records)

            except Exception as exc:
                logger.error("Failed to load question bank from %s: %s", self._data_path, exc)
                self._all_records = []
                self._by_role = {r: [] for r in CANONICAL_ROLES}
                self._loaded = True
                return 0

    @property
    def total_records(self) -> int:
        if not self._loaded:
            self.load()
        return len(self._all_records)

    def get_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Returns all questions matching the given role (normalized)."""
        if not self._loaded:
            self.load()
        canonical = normalize_role(role)
        return list(self._by_role.get(canonical, []))

    def search(
        self,
        query: str,
        role: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Keyword search within questions and topics for a given role."""
        if not self._loaded:
            self.load()

        canonical_role = normalize_role(role) if role else None
        pool = self._by_role.get(canonical_role, self._all_records) if canonical_role else self._all_records

        tokens = set(re.findall(r"\w+", query.lower()))
        if not tokens:
            return pool[:limit]

        scored = []
        for r in pool:
            q_text = (r.get("question") or "").lower()
            topic = (r.get("topic") or "").lower()
            tech = (r.get("technology") or "").lower()
            search_corpus = f"{q_text} {topic} {tech}"

            match_count = sum(1 for t in tokens if t in search_corpus)
            if match_count > 0:
                scored.append((match_count, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def retrieve_candidates(
        self,
        role: str,
        *,
        technology: Optional[str] = None,
        skill: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        intent: Optional[str] = None,
        search_query: Optional[str] = None,
        excluded_questions: Optional[List[str]] = None,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Role-aware deterministic local retrieval following strict priority:
          1. Exact role match (mandatory filter; never returns unrelated role)
          2. Role + Technology match (+40)
          3. Role + Skill match (+30)
          4. Role + Topic match (+20)
          5. Difficulty compatibility (+15 exact, +5 adjacent)
          6. Intent compatibility (+10)
          7. Keyword/token overlap (+1 per token)

        Progressively broadens within the role if exact technology/skill is absent.
        Never returns questions from an unrelated role.
        """
        if not self._loaded:
            self.load()

        canonical_role = normalize_role(role)
        pool = self._by_role.get(canonical_role, [])
        if not pool:
            logger.warning("[QuestionBank] No questions found for canonical role '%s'", canonical_role)
            return []

        # Build exclusion set for fast deduplication
        excluded_set: Set[str] = set()
        if excluded_questions:
            for eq in excluded_questions:
                if eq and isinstance(eq, str):
                    clean_eq = re.sub(r"\s+", " ", eq.strip().lower())
                    excluded_set.add(clean_eq)

        # Normalize filter parameters
        tech_str = technology.strip().lower() if technology else None
        skill_str = skill.strip().lower() if skill else None
        topic_str = topic.strip().lower() if topic else None
        diff_str = difficulty.strip().lower() if difficulty else None
        intent_str = intent.strip().lower() if intent else None

        query_tokens = set(re.findall(r"\w+", search_query.lower())) if search_query else set()

        scored_candidates: List[tuple[float, Dict[str, Any]]] = []

        for record in pool:
            q_text = str(record.get("question") or "").strip()
            clean_q = re.sub(r"\s+", " ", q_text.lower())

            # Skip questions already asked
            if clean_q in excluded_set or any(clean_q.startswith(ex[:40]) for ex in excluded_set if len(ex) >= 40):
                continue

            score = 10.0  # Base role match score

            rec_tech = str(record.get("technology") or "").lower()
            rec_skill = str(record.get("skill") or record.get("primary_skill") or "").lower()
            rec_topic = str(record.get("topic") or record.get("category") or "").lower()
            rec_diff = str(record.get("difficulty") or "").lower()
            rec_intent = str(record.get("intent") or "").lower()
            rec_sec_skills = str(record.get("secondary_skills") or "").lower()

            # Priority 2: Technology Match
            if tech_str:
                if tech_str in rec_tech:
                    score += 40.0
                elif tech_str in clean_q:
                    score += 25.0
                elif tech_str in rec_sec_skills:
                    score += 20.0

            # Priority 3: Skill Match
            if skill_str:
                if skill_str in rec_skill:
                    score += 30.0
                elif skill_str in clean_q:
                    score += 15.0

            # Priority 4: Topic Match
            if topic_str:
                if topic_str in rec_topic:
                    score += 20.0
                elif topic_str in clean_q:
                    score += 10.0

            # Priority 5: Difficulty Compatibility
            if diff_str:
                if rec_diff == diff_str:
                    score += 15.0
                elif (diff_str == "easy" and rec_diff == "medium") or (diff_str == "hard" and rec_diff == "medium"):
                    score += 5.0

            # Priority 6: Intent Compatibility
            if intent_str:
                if intent_str in rec_intent:
                    score += 10.0
                elif intent_str in clean_q:
                    score += 5.0

            # Priority 7: Keyword Overlap
            if query_tokens:
                corpus = f"{clean_q} {rec_tech} {rec_skill} {rec_topic}"
                overlap = sum(1 for t in query_tokens if t in corpus)
                score += min(overlap, 10) * 1.0

            scored_candidates.append((score, record))

        # Sort descending by calculated score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        results: List[Dict[str, Any]] = []
        for rank_idx, (cand_score, rec) in enumerate(scored_candidates[:limit]):
            formatted = {
                "question": rec.get("question"),
                "ideal_answer": rec.get("ideal_answer") or rec.get("expected_answer") or "",
                "role": rec.get("role") or canonical_role,
                "technology": rec.get("technology"),
                "skill": rec.get("skill") or rec.get("primary_skill"),
                "topic": rec.get("topic"),
                "category": rec.get("category"),
                "difficulty": rec.get("difficulty") or difficulty or "Medium",
                "intent": rec.get("intent") or "explain",
                "id": str(rec.get("id") or f"local_{rank_idx}"),
                "source": "local_question_bank",
                "retrieval_method": "deterministic_rank",
                "similarity": round(cand_score / 100.0, 4),
                "rank": rank_idx + 1,
                "metadata": {
                    "id": str(rec.get("id") or f"local_{rank_idx}"),
                    "role": rec.get("role") or canonical_role,
                    "technology": rec.get("technology"),
                    "skill": rec.get("skill") or rec.get("primary_skill"),
                    "topic": rec.get("topic"),
                    "category": rec.get("category"),
                    "difficulty": rec.get("difficulty"),
                    "intent": rec.get("intent"),
                    "source": "local_question_bank",
                    "retrieval_method": "deterministic_rank",
                    "retrieval_score": cand_score,
                },
            }
            results.append(formatted)

        return results


# Module-level convenience functions
def get_question_bank_service() -> QuestionBankService:
    return QuestionBankService.get_instance()
