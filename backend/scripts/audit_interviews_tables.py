import asyncio
import os
import sys
import json
from collections import Counter
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sql_text
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

async def audit_interviews_tables():
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        int_res = await conn.execute(sql_text("SELECT id, role, topic, difficulty, status, phase FROM public.interviews"))
        int_rows = list(int_res.mappings())
        
        msg_res = await conn.execute(sql_text("SELECT id, interview_id, question, score, question_difficulty, question_type, topic, technical_concept FROM public.interview_messages"))
        msg_rows = list(msg_res.mappings())

    print(f"Total interviews: {len(int_rows)}")
    print(f"Total interview_messages: {len(msg_rows)}")
    
    int_roles = Counter(r["role"] for r in int_rows)
    int_topics = Counter(r["topic"] for r in int_rows)
    int_diffs = Counter(r["difficulty"] for r in int_rows)
    int_status = Counter(str(r["status"]) for r in int_rows)
    int_phase = Counter(r["phase"] for r in int_rows)
    
    print("\n--- INTERVIEW ROLES ---")
    print(int_roles.most_common(10))
    print("\n--- INTERVIEW TOPICS ---")
    print(int_topics.most_common(10))
    print("\n--- INTERVIEW DIFFICULTIES ---")
    print(dict(int_diffs))
    print("\n--- INTERVIEW STATUSES ---")
    print(dict(int_status))
    print("\n--- INTERVIEW PHASES ---")
    print(dict(int_phase))
    
    msg_types = Counter(r["question_type"] for r in msg_rows)
    msg_diffs = Counter(r["question_difficulty"] for r in msg_rows)
    msg_topics = Counter(r["topic"] for r in msg_rows)
    
    print("\n--- MESSAGE QUESTION TYPES ---")
    print(dict(msg_types))
    print("\n--- MESSAGE DIFFICULTIES ---")
    print(dict(msg_diffs))
    print("\n--- MESSAGE TOPICS (top 10) ---")
    print(msg_topics.most_common(10))
    
    # Check sample questions from interview_messages
    sample_msgs = [r["question"] for r in msg_rows if r["question"]][:5]
    print("\n--- SAMPLE INTERVIEW QUESTIONS (from live interview_messages) ---")
    for i, q in enumerate(sample_msgs, 1):
        print(f"{i}. {q}\n")

if __name__ == "__main__":
    asyncio.run(audit_interviews_tables())
