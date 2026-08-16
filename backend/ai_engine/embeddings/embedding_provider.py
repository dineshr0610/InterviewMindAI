from __future__ import annotations

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class EmbeddingProvider:
    MODEL = "gemini-embedding-2"
    DIMENSIONS = 1536

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=api_key)

    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=self.DIMENSIONS,
                task_type="RETRIEVAL_QUERY",
            ),
        )

        return list(response.embeddings[0].values)

    def embed_document(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=self.DIMENSIONS,
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )

        return list(response.embeddings[0].values)


embedding_provider = EmbeddingProvider()