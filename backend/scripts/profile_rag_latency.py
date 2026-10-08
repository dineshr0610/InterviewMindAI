import sys
import os
import time
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from ai_engine.embeddings.embedding_provider import embedding_provider
import asyncpg
import asyncio

async def profile_rag():
    print("=== RAG LATENCY PROFILER ===")
    
    query = "How does Node.js handle concurrency?"
    role = "Backend Developer"
    
    print(f"Query: {query}")
    
    # 1. Profile Embedding Generation
    t0 = time.time()
    query_embedding = embedding_provider.embed_query(query)
    t1 = time.time()
    emb_latency = t1 - t0
    print(f"[1] Embedding Generation: {emb_latency:.3f}s")
    
    # 2. Profile Supabase REST RPC
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")
    
    if supabase_url and supabase_key:
        rpc_url = supabase_url.rstrip("/") + "/rest/v1/rpc/match_document_embeddings_filtered"
        headers = {
            "apikey": supabase_key,
            "Authorization": "Bearer " + supabase_key,
            "Content-Type": "application/json",
        }
        payload = {
            "query_embedding": query_embedding,
            "match_threshold": 0.3,
            "match_count": 3,
            "metadata_filter": {"role": role}
        }
        
        t0 = time.time()
        try:
            response = requests.post(rpc_url, headers=headers, json=payload, timeout=5)
            t1 = time.time()
            if response.status_code == 200:
                print(f"[2] REST RPC Success: {t1-t0:.3f}s")
            else:
                print(f"[2] REST RPC Failed ({response.status_code}): {t1-t0:.3f}s")
        except Exception as e:
            t1 = time.time()
            print(f"[2] REST RPC Exception ({type(e).__name__}): {t1-t0:.3f}s - {e}")
            
    # 3. Profile asyncpg direct DB fallback
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        t0 = time.time()
        try:
            conn = await asyncpg.connect(db_url)
            t1 = time.time()
            conn_latency = t1 - t0
            print(f"[3a] Asyncpg Connection: {conn_latency:.3f}s")
            
            t0 = time.time()
            # Perform pgvector search with JSONB filtering
            emb_str = "[" + ",".join(str(f) for f in query_embedding) + "]"
            filter_json = '{"role": "Backend Developer"}'
            
            sql = '''
                SELECT id, content, metadata, 1 - (embedding <=> $1::vector) as similarity
                FROM document_embeddings
                WHERE 1 - (embedding <=> $1::vector) > $2
                AND metadata @> $3::jsonb
                ORDER BY embedding <=> $1::vector
                LIMIT $4
            '''
            rows = await conn.fetch(sql, emb_str, 0.3, filter_json, 3)
            t1 = time.time()
            query_latency = t1 - t0
            print(f"[3b] Asyncpg Query Execution: {query_latency:.3f}s")
            print(f"     -> Retrieved {len(rows)} rows.")
            
            await conn.close()
        except Exception as e:
            print(f"[3] Asyncpg Error: {e}")

if __name__ == "__main__":
    asyncio.run(profile_rag())
