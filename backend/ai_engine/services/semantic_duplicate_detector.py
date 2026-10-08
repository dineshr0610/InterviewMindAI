import logging
import numpy as np
from ai_engine.embeddings.embedding_provider import embedding_provider

logger = logging.getLogger(__name__)

# Temporary, uncalibrated threshold
SEMANTIC_DUPLICATE_THRESHOLD = 0.85

class SemanticDuplicateDetector:
    """
    Implements semantic duplicate detection for candidate questions 
    by comparing them against previously asked questions using embeddings.
    """
    def __init__(self, previous_questions: list[str]):
        self.previous_questions = [pq.strip() for pq in previous_questions if pq.strip()]
        self.previous_embeddings = []
        
        if self.previous_questions:
            try:
                # Fetch embeddings for all previous questions in one batch to cache them
                self.previous_embeddings = embedding_provider.embed_documents(self.previous_questions)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for previous questions: {e}")
                self.previous_embeddings = []
                
        self.candidate_embeddings_cache = {}
                
    def prefetch_candidate_embeddings(self, candidate_texts: list[str]):
        """
        Batches embedding generation for all candidate questions.
        """
        if not self.previous_embeddings or not candidate_texts:
            return
            
        try:
            unique_texts = list(set(t.strip() for t in candidate_texts if t.strip()))
            if unique_texts:
                embeddings = embedding_provider.embed_documents(unique_texts)
                self.candidate_embeddings_cache = {text: emb for text, emb in zip(unique_texts, embeddings)}
        except Exception as e:
            logger.error(f"Failed to batch embed candidates: {e}")
            self.candidate_embeddings_cache = {}
                
    def check_duplicate(self, candidate_text: str) -> dict:
        """
        Checks if the candidate text is semantically similar to any previous question.
        Returns a dictionary with diagnostic data.
        """
        if not self.previous_embeddings:
            return {
                "semantic_duplicate": False,
                "candidate_similarity": None,
                "matched_previous_question_index": None,
                "threshold": SEMANTIC_DUPLICATE_THRESHOLD,
                "error": "Embeddings unavailable or no previous questions"
            }
            
        try:
            candidate_text = candidate_text.strip()
            cand_embedding = self.candidate_embeddings_cache.get(candidate_text)
            
            if cand_embedding is None:
                # Fallback to no duplicate if we didn't prefetch or prefetch failed
                # Avoid triggering individual API calls when batching failed
                return {
                    "semantic_duplicate": False,
                    "candidate_similarity": None,
                    "matched_previous_question_index": None,
                    "threshold": SEMANTIC_DUPLICATE_THRESHOLD,
                    "error": "Candidate embedding not found in cache"
                }
            
            # compute cosine similarity
            max_sim = -1.0
            max_idx = None
            
            cand_vec = np.array(cand_embedding)
            cand_norm = np.linalg.norm(cand_vec)
            
            if cand_norm > 0:
                for idx, p_emb in enumerate(self.previous_embeddings):
                    p_vec = np.array(p_emb)
                    p_norm = np.linalg.norm(p_vec)
                    if p_norm > 0:
                        sim = np.dot(cand_vec, p_vec) / (cand_norm * p_norm)
                        if sim > max_sim:
                            max_sim = float(sim)
                            max_idx = idx
                            
            is_dup = max_sim >= SEMANTIC_DUPLICATE_THRESHOLD
            
            return {
                "semantic_duplicate": is_dup,
                "candidate_similarity": max_sim if max_idx is not None else None,
                "matched_previous_question_index": max_idx,
                "threshold": SEMANTIC_DUPLICATE_THRESHOLD
            }
        except Exception as e:
            logger.error(f"Failed to check semantic duplicate for candidate: {e}")
            return {
                "semantic_duplicate": False,
                "candidate_similarity": None,
                "matched_previous_question_index": None,
                "threshold": SEMANTIC_DUPLICATE_THRESHOLD,
                "error": str(e)
            }
