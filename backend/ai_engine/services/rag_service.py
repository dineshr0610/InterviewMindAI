"""RAG Service for InterviewMind AI.

Coordinates retrieval across Supabase pgvector and the local QuestionBankService fallback.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_engine.services.question_bank_service import (
    get_question_bank_service,
    normalize_role,
)

logger = logging.getLogger("interviewmind.ai_engine.rag_service")

SOURCE_SUPABASE_VECTOR = "supabase_bank"
SOURCE_LOCAL_BANK = "local_question_bank"


class RAGService:
    """
    Unified RAG retrieval service.
    First tries Supabase pgvector retrieval.
    If Supabase returns 0 documents, is missing embeddings, or errors,
    it automatically falls back to local QuestionBankService.
    """

    def ask(
        self,
        search_query: str,
        filters: Optional[dict] = None,
        *,
        role: Optional[str] = None,
        technology: Optional[str] = None,
        skill: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        intent: Optional[str] = None,
        excluded_questions: Optional[List[str]] = None,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        filters = dict(filters or {})

        # Extract parameters from filters if not explicitly provided
        target_role = role or filters.get("role")
        target_tech = technology or filters.get("technology")
        target_skill = skill or filters.get("skill")
        target_topic = topic or filters.get("topic")
        target_diff = difficulty or filters.get("difficulty")
        target_intent = intent or filters.get("intent")
        target_excluded = excluded_questions or filters.get("excluded_questions")

        canonical_role = normalize_role(target_role)

        # -------------------------------------------------------------
        # 1. Try Supabase pgvector retrieval first
        # -------------------------------------------------------------
        supabase_results: List[Dict[str, Any]] = []
        try:
            from ai_engine.vectorstores.supabase_store import retriever

            # Supabase metadata filter accepts role and difficulty
            sb_filter = {}
            if target_role:
                sb_filter["role"] = target_role
            if target_diff:
                sb_filter["difficulty"] = target_diff

            docs = retriever.get_filtered_documents(search_query, metadata_filter=sb_filter if sb_filter else None)
            if docs:
                for i, doc in enumerate(docs):
                    supabase_results.append({
                        "question": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": doc.metadata.get("similarity", 0.0),
                        "rank": i + 1,
                        "source": SOURCE_SUPABASE_VECTOR,
                        "retrieval_method": "vector",
                    })

                logger.info("[RAG] source=SUPABASE_VECTOR candidates=%d", len(supabase_results))
                return supabase_results
            else:
                logger.info("[RAG] Supabase vector retrieval returned 0 documents for query '%s'", search_query)
        except Exception as exc:
            logger.warning("[RAG] Supabase vector retrieval failed (%s), proceeding to local fallback", exc)

        # -------------------------------------------------------------
        # 2. Local QuestionBankService Fallback (5,000 canonical dataset)
        # -------------------------------------------------------------
        try:
            bank_service = get_question_bank_service()
            local_results = bank_service.retrieve_candidates(
                role=canonical_role,
                technology=target_tech,
                skill=target_skill,
                topic=target_topic,
                difficulty=target_diff,
                intent=target_intent,
                search_query=search_query,
                excluded_questions=target_excluded,
                limit=limit,
            )

            if local_results:
                logger.info("[RAG] source=LOCAL_QUESTION_BANK candidates=%d", len(local_results))
                return local_results
            else:
                logger.info("[RAG] source=RESUME_ONLY candidates=0")
                return []
        except Exception as local_exc:
            logger.error("[RAG] Local question bank fallback error: %s", local_exc)
            logger.info("[RAG] source=RESUME_ONLY candidates=0")
            return []