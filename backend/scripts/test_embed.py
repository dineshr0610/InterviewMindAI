import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.embeddings.embedding_provider import embedding_provider
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

def test_embed():
    print("Testing embed_documents...")
    try:
        res = embedding_provider.embed_documents(["What is Java?"])
        print(f"Success! Dimension: {len(res[0])}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_embed()
