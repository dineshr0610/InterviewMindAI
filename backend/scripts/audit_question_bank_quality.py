import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import asyncpg

async def audit_quality():
    conn_str = os.getenv("DATABASE_URL")
    if not conn_str:
        print("DATABASE_URL not found.")
        return

    conn = await asyncpg.connect(conn_str)
    
    print("=== QUESTION BANK QUALITY AUDIT ===")
    
    rows = await conn.fetch("SELECT id, content, metadata FROM document_embeddings")
    
    total = len(rows)
    empty = 0
    short = 0
    long_article = 0
    markdown_blob = 0
    malformed = 0
    missing_role = 0
    missing_difficulty = 0
    missing_category = 0
    missing_tech = 0
    inactive = 0
    
    # Predefined sets for validation
    valid_difficulties = {"Easy", "Medium", "Hard"}
    
    for r in rows:
        content = r['content'] or ""
        meta = r['metadata'] or {}
        
        # Text Quality Metrics
        length = len(content)
        if length == 0:
            empty += 1
        elif length < 20:
            short += 1
        elif length > 1500:
            long_article += 1
            
        if "```" in content and length > 500:
            markdown_blob += 1
            
        if "?" not in content and not content.lower().startswith(("explain", "describe", "write", "what", "how", "why")):
            malformed += 1
            
        # Metadata Quality Metrics
        if not meta.get("role"):
            missing_role += 1
            
        diff = meta.get("difficulty")
        if not diff or diff not in valid_difficulties:
            missing_difficulty += 1
            
        if not meta.get("category"):
            missing_category += 1
            
        if not meta.get("topic") and not meta.get("languages"):
            missing_tech += 1
            
        if meta.get("status") == "inactive":
            inactive += 1
            
    print(f"Total Rows Evaluated: {total}")
    print("\n-- Text Quality --")
    print(f"Empty Content: {empty}")
    print(f"Extremely Short (<20 chars): {short}")
    print(f"Long Articles (>1500 chars): {long_article}")
    print(f"Large Markdown Blobs: {markdown_blob}")
    print(f"Potentially Malformed (Not a question/prompt): {malformed}")
    
    print("\n-- Metadata Quality --")
    print(f"Missing/Invalid Role: {missing_role}")
    print(f"Missing/Invalid Difficulty: {missing_difficulty}")
    print(f"Missing Category: {missing_category}")
    print(f"Missing Technology/Topic: {missing_tech}")
    print(f"Explicitly Inactive: {inactive}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(audit_quality())
