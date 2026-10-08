from __future__ import annotations

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from ai_engine.key_pool import gemini_key_pool

load_dotenv()

class EmbeddingProvider:
    MODEL = "gemini-embedding-2"
    DIMENSIONS = 1536

    def __init__(self):
        # Using centralized key pool, no need to init static client
        pass

    def embed_query(self, text: str) -> list[float]:
        def do_embed(key: str):
            client = genai.Client(api_key=key)
            response = client.models.embed_content(
                model=self.MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.DIMENSIONS,
                    task_type="RETRIEVAL_QUERY",
                ),
            )
            return list(response.embeddings[0].values)
        
        return gemini_key_pool.execute_with_fallback(do_embed)

    def embed_document(self, text: str) -> list[float]:
        def do_embed(key: str):
            client = genai.Client(api_key=key)
            response = client.models.embed_content(
                model=self.MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.DIMENSIONS,
                    task_type="RETRIEVAL_DOCUMENT",
                ),
            )
            return list(response.embeddings[0].values)
            
        return gemini_key_pool.execute_with_fallback(do_embed)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import requests
        def do_embed_batch(key: str):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:batchEmbedContents?key={key}"
            requests_payload = []
            for t in texts:
                requests_payload.append({
                    "model": f"models/{self.MODEL}",
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": self.DIMENSIONS
                })
            
            response = requests.post(url, json={"requests": requests_payload}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                embeddings = data.get("embeddings", [])
                if len(embeddings) != len(texts):
                    raise RuntimeError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")
                
                results = []
                for emb in embeddings:
                    # Google REST API returns values in 'values' key
                    vals = emb.get("values", [])
                    # Adjust dimensionality locally if needed, but the REST API defaults to 768 for old models.
                    # Wait, we need outputDimensionality! Let's pass it in the request.
                    results.append(vals)
                return results
            else:
                raise RuntimeError(response.text)
                
        return gemini_key_pool.execute_with_fallback(do_embed_batch)

embedding_provider = EmbeddingProvider()