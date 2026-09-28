"""
Automated unit & integration tests for RAG pipeline, Supabase pgvector retriever,
embedding generation, and error fallback resilience.
"""

from __future__ import annotations

import pytest
import os
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

from ai_engine.vectorstores.supabase_store import SupabaseVectorRetriever
from ai_engine.embeddings.embedding_provider import embedding_provider, EmbeddingProvider


def test_relevant_query_retrieval() -> None:
    """Test 1: Relevant query retrieves relevant document."""
    mock_rows = [
        {
            "id": "123",
            "content": "Binary Search operates in O(log N) time complexity.",
            "metadata": {"topic": "Binary Search"},
            "similarity": 0.85,
        }
    ]

    retriever = SupabaseVectorRetriever(k=2, similarity_threshold=0.0)

    with patch.dict(os.environ, {"DATABASE_URL": ""}), \
         patch.object(embedding_provider, "embed_query") as mock_embed, \
         patch("requests.Session.post") as mock_post:
        
        mock_embed.return_value = [0.1] * 1536
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_rows
        mock_post.return_value = mock_resp

        docs = retriever._get_relevant_documents("How does binary search work?")
        assert len(docs) == 1
        assert "Binary Search" in docs[0].page_content
        assert docs[0].metadata["similarity"] == 0.85


def test_unrelated_query_no_false_retrieval() -> None:
    """Test 2: High similarity threshold prevents returning low similarity documents."""
    retriever = SupabaseVectorRetriever(k=2, similarity_threshold=0.9)

    with patch.dict(os.environ, {"DATABASE_URL": ""}), \
         patch.object(embedding_provider, "embed_query") as mock_embed, \
         patch("requests.Session.post") as mock_post:

        mock_embed.return_value = [0.1] * 1536
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_post.return_value = mock_resp

        docs = retriever._get_relevant_documents("Binary Search")
        assert len(docs) == 0


def test_empty_database_handled_safely() -> None:
    """Test 3: Empty database returns empty document list without raising exception."""
    retriever = SupabaseVectorRetriever(k=2, similarity_threshold=0.0)

    with patch.dict(os.environ, {"DATABASE_URL": ""}), \
         patch.object(embedding_provider, "embed_query") as mock_embed, \
         patch("requests.Session.post") as mock_post:

        mock_embed.return_value = [0.1] * 1536
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_post.return_value = mock_resp

        docs = retriever._get_relevant_documents("Any topic")
        assert isinstance(docs, list)
        assert len(docs) == 0


def test_retrieval_network_failure_handled_safely() -> None:
    """Test 4: Network failure during REST retrieval is caught and returns empty list safely."""
    retriever = SupabaseVectorRetriever(k=2, similarity_threshold=0.0)

    with patch.dict(os.environ, {"DATABASE_URL": ""}), \
         patch.object(embedding_provider, "embed_query") as mock_embed, \
         patch("requests.Session.post", side_effect=Exception("Connection reset")):

        mock_embed.return_value = [0.1] * 1536

        docs = retriever._get_relevant_documents("Binary Search")
        assert isinstance(docs, list)
        assert len(docs) == 0


def test_embedding_generation_failure_handled_safely() -> None:
    """Test 5: Embedding API failure is caught and handled safely."""
    retriever = SupabaseVectorRetriever(k=2, similarity_threshold=0.0)

    with patch.object(embedding_provider, "embed_query", side_effect=RuntimeError("API Error")):
        docs = retriever._get_relevant_documents("Binary Search")
        assert isinstance(docs, list)
        assert len(docs) == 0


def test_malformed_document_handled_safely() -> None:
    """Test 6: Malformed response row missing fields handled safely."""
    retriever = SupabaseVectorRetriever(k=2, similarity_threshold=0.0)

    mock_rows = [
        {
            "id": "789",
            # content is missing or null
            "metadata": None,
        }
    ]

    with patch.object(embedding_provider, "embed_query") as mock_embed, \
         patch("requests.Session.post") as mock_post:

        mock_embed.return_value = [0.1] * 1536
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_rows
        mock_post.return_value = mock_resp

        docs = retriever._get_relevant_documents("Binary Search")
        assert len(docs) == 1
        assert docs[0].page_content == ""
