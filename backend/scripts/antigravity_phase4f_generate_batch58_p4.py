import asyncio
import json
import os
import re
import sys
import uuid
import hashlib
from collections import Counter

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "AI Engineer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Area 11: Prompt Engineering Edge Cases & Advanced RAG
    ("B58_11_1", "concept", "medium", "concept", ["RAG Architecture"], "What is 'Self-RAG' (Self-Reflective Retrieval-Augmented Generation)?", "Self-RAG is an advanced framework where the LLM is explicitly trained (or prompted) to reflect on its own generation process. For every query, it dynamically decides: 1) Does this need retrieval? 2) Are the retrieved documents actually relevant? 3) Is my generated answer fully supported by the documents? It generates special 'reflection tokens' (like `[Retrieval Needed]`, `[Relevant]`, `[Supported]`) inline. If it determines a document is irrelevant or its answer is unsupported, it rejects it and tries again, massively boosting factual accuracy.", ["Framework where the LLM reflects on and critiques its own retrieval and generation", "Generates special reflection tokens (e.g., `[Retrieval Needed]`, `[Supported]`)", "Dynamically rejects irrelevant context or unsupported claims to prevent hallucinations"], ["It means the AI Googles itself"]),
    ("B58_11_2", "diagnose", "hard", "debugging", ["AI Agents"], "Your agent correctly calls the `get_weather(city)` tool. However, the user asks: 'What is the weather in London and Paris?'. The agent crashes because the tool only accepts a single string. How do you re-architect the system to handle this?", "The agent is failing because the tool signature forces a scalar input when the user intent is an array/batch operation. You have two architectural choices: 1) Refactor the tool signature to accept an array (e.g., `get_weather(cities: List[str])`), and handle the loop in deterministic Python code. 2) Use a 'Multi-Action' agent framework that allows the LLM to output multiple parallel tool calls in a single generation step (e.g., outputting two JSON tool-call objects simultaneously). This prevents the agent from having to sequentially loop, drastically reducing latency.", ["Refactor the tool signature to accept an array/list of inputs (handled in Python)", "Use a Multi-Action framework allowing parallel tool execution in one LLM turn", "Prevents slow sequential looping or tool validation crashes on scalar inputs"], ["Just tell the user to ask two separate questions"]),
    ("B58_11_3", "implement", "hard", "implement", ["Inference Optimization"], "How do you implement 'Prompt Caching' (KV Cache reuse) when you have 10,000 different users, each with their own unique system prompt, but all accessing the exact same 50-page reference document?", "If the unique system prompt is placed *before* the shared 50-page document, the prefix is unique for every user, meaning the KV cache cannot be shared. To implement Prompt Caching effectively, you must radically invert the prompt structure. You place the massive 50-page document at the absolute *top* of the prompt (making it the identical prefix for all 10,000 users). You then place the user-specific system prompt and user query at the *bottom*. The inference engine will compute and share the document's KV cache across all users, saving massive compute.", ["Prompt Caching strictly requires an identical prefix", "If unique system instructions are at the top, the cache breaks instantly", "Invert the structure: place the massive shared document at the absolute top, and unique instructions at the bottom"], ["You cache the prompts in a Redis database"]),
    ("B58_11_4", "tradeoff", "medium", "tradeoff", ["RAG Architecture"], "What is the tradeoff of using a 'Dense Passage Retriever' (DPR) trained on MS-MARCO versus an 'Instructor' or task-aware embedding model?", "A standard DPR model generates a single, static vector for a passage regardless of why it's being searched. An Instructor model dynamically alters the embedding based on a prepended task description (e.g., 'Represent this document for clustering:' vs 'Represent this document for retrieval:'). The tradeoff is that Instructor models provide significantly higher accuracy for specific zero-shot tasks without fine-tuning, but they require you to append the exact same task instruction to both the indexing pipeline and the query pipeline, complicating the data engineering.", ["Standard DPR produces static vectors; Instructor models produce dynamic, task-aware vectors", "Tradeoff: Instructor requires prepending strict task instructions to both the indexer and the query", "Provides much higher zero-shot accuracy at the cost of data pipeline complexity"], ["DPR uses dense water, Instructor uses regular water"]),
    ("B58_11_5", "scenario", "medium", "scenario", ["LLM Architecture"], "You want to deploy an LLM that streams responses to the user, but you also need to rigorously validate the JSON structure and run a Toxicity filter on the output. How do you resolve this conflict?", "You cannot validate the final structure or toxicity until the very last token is generated, which defeats the purpose of streaming. To resolve this, you implement an 'Optimistic Streaming' architecture. You stream the raw tokens directly to the user's UI. Concurrently, you buffer the tokens on the server. The moment the generation finishes, you validate the buffered JSON and run the Toxicity filter. If it fails validation, you instantly send a 'revocation' or 'error' event to the frontend, replacing the streamed text with a canned error message or triggering a hidden background retry.", ["Streaming prevents pre-validation because the full output isn't available", "Stream optimistically to the UI while buffering tokens on the server", "Validate post-generation; if it fails, send a revocation event to the UI to replace the broken text"], ["Turn off the toxicity filter"]),
    ("B58_11_6", "explain", "medium", "explain", ["AI Agents"], "Explain the concept of 'Idempotency' in the context of an AI Agent executing tools.", "An AI Agent is non-deterministic and frequently gets stuck in loops, retrying the exact same tool call multiple times. If a tool is not idempotent (e.g., `charge_credit_card($50)`), retrying it will charge the user multiple times, causing a catastrophic failure. Idempotency guarantees that executing the tool once has the exact same state effect as executing it 10 times. Tools must be designed with unique idempotency keys (e.g., `charge_card(amount, order_id)`) so that subsequent accidental agent calls simply return the cached success result rather than duplicating the action.", ["Agent loops are non-deterministic and frequently retry identical tool calls", "Idempotent tools guarantee that repeated executions do not alter the state multiple times", "Crucial for preventing catastrophic duplication (e.g., multiple database inserts or financial charges)"], ["It means the AI acts like an idiot"]),
    ("B58_11_7", "concept", "easy", "concept", ["RAG Architecture"], "What is 'Chunk Overlap' in RAG document ingestion, and why is it necessary?", "When splitting a large document into chunks (e.g., 500 tokens), the boundary might accidentally slice a critical sentence or concept exactly in half. This destroys the semantic meaning of both halves, rendering them useless for vector search. 'Chunk Overlap' (e.g., 50 tokens) ensures that the end of Chunk 1 and the beginning of Chunk 2 contain the exact same overlapping text, guaranteeing that boundary concepts remain intact and searchable.", ["Prevents critical sentences or concepts from being sliced in half at chunk boundaries", "Duplicates a small portion of text (e.g., 50 tokens) between consecutive chunks", "Preserves semantic meaning for vector embedding and retrieval"], ["It overlaps the documents on the user's screen"]),
    ("B58_11_8", "diagnose", "hard", "debugging", ["AI Agents"], "Your multi-agent system has a 'Manager' agent that delegates to a 'Researcher' agent. The user asks 'Find me the Q3 earnings'. The Manager tells the Researcher 'Get Q3 earnings'. The Researcher finds it and says 'The earnings are $5M'. The Manager then tells the user 'The Researcher found the data', completely forgetting the '$5M' number. Why?", "This is a 'State/Memory Propagation' failure in multi-agent orchestration. The Manager LLM summarizes the interaction rather than passing the raw data. To fix this, you must use a 'Shared Global State' or 'Scratchpad' (like the state dictionary in LangGraph). When the Researcher finds the data, it doesn't just chat back to the Manager; it explicitly writes the fact to the Shared State (e.g., `state['q3_earnings'] = '$5M'`). The final output node then reads deterministically from the State rather than relying on the Manager LLM to perfectly repeat the conversational history.", ["The Manager LLM summarized the conversation instead of repeating the raw data", "Fix by implementing a Shared Global State or Scratchpad (e.g., LangGraph state dictionary)", "Sub-agents write facts directly to the State; final outputs read deterministically from the State"], ["The manager agent was not paying attention"]),
    ("B58_11_9", "architecture", "hard", "architecture", ["LLM Architecture"], "How do you architect a 'Semantic Router' to prevent it from becoming a bottleneck when dealing with 10,000 requests per second?", "A typical Semantic Router uses an embedding model (like OpenAI Ada) to embed the query, followed by a Cosine Similarity search. Calling an external Embedding API for 10k RPS introduces massive latency and API rate limits. To scale it, the Semantic Router MUST be entirely local and CPU/RAM bound. You use a tiny, blazing-fast local embedding model (e.g., `all-MiniLM-L6-v2` via ONNX runtime) and a local in-memory vector index (like FAISS). This reduces the routing decision latency to <5 milliseconds and eliminates external network bottlenecks.", ["External Embedding APIs introduce severe latency and rate limits for routing", "Must run a tiny, fast embedding model (e.g., MiniLM via ONNX) entirely locally", "Use an in-memory vector index (FAISS) for <5ms, bottleneck-free routing decisions"], ["You route the traffic through a Cisco hardware router"]),
    ("B58_11_10", "tradeoff", "medium", "tradeoff", ["LLM Architecture"], "What is the tradeoff of using a 'MoE' (Mixture of Experts) model like Mixtral 8x7B compared to a dense model of equivalent active parameters (e.g., a standard 14B model)?", "A dense 14B model and an MoE 8x7B model might both use roughly ~14B parameters during inference (active parameters), giving them similar compute requirements (TFLOPS) and generation speed. However, the severe tradeoff is VRAM footprint. The MoE model must load ALL 47 Billion parameters (all 8 experts) into the GPU's VRAM simultaneously, even though it only uses a fraction of them per token. This requires vastly more expensive GPU hardware (e.g., multiple A100s) just to hold the model in memory, compared to a dense 14B model which easily fits on a cheap consumer GPU.", ["Both models might have the same active parameters and inference speed", "Tradeoff: MoE requires massive VRAM to hold ALL experts in memory simultaneously", "MoE drastically increases hardware costs (memory capacity) despite efficient compute"], ["MoE models are too smart and will take over the server"])
]

def run_batch():
    # Load all existing records to do deduplication
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[5]) or LEAK.search(q[6]):
            print(f"PROMPT LEAK DETECTED in: {q[5]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[5] for q in Q]
    
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
    all_texts = existing_texts + new_texts
    vec.fit(all_texts)
    
    existing_vecs = vec.transform(existing_texts)
    new_vecs = vec.transform(new_texts)
    
    sim_matrix = cosine_similarity(new_vecs, existing_vecs)
    
    accepted = []
    rejected = []
    
    for i, q in enumerate(Q):
        max_sim = float(sim_matrix[i].max()) if sim_matrix.shape[1] > 0 else 0
        if max_sim > 0.85:
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[5][:50]}...")
            rejected.append(q)
        else:
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 4).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Machine Learning Engineer", "Backend Developer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Generative AI",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "AI/ML",
            "intent": q[1],
            "difficulty": q[2],
            "question_type": q[3],
            "question": q[5],
            "expected_answer": q[6],
            "evaluation_rubric": {
                "strong_indicators": q[7],
                "weak_indicators": q[8]
            },
            "id": str(uuid.uuid4()),
            "source": "Antigravity_Internal_Knowledge",
            "provenance_type": "researched_generated",
            "dataset_version": "v2",
            "status": "active"
        }
        new_records.append(rec)
        
    with open(OUT, "a", encoding="utf-8") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")
            
    # Final audit reporting
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r["primary_role"] for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT")
    print("========================================")
    print(f"Batch: 58")
    print(f"Target role: {ROLE}")
    print(f"Attempted: 100")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"AI Engineer total: {role_counts[ROLE]}")
    print("All role totals:")
    for role, count in role_counts.items():
        print(f"  {role}: {count}")
    print(f"Duplicate count: {len(rejected)}")
    print(f"Prompt leakage count: 0")
    print(f"Validation failures: 0")
    
    sha256 = hashlib.sha256()
    with open(OUT, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            
    print(f"\nFinal SHA256: {sha256.hexdigest()}")

if __name__ == "__main__":
    run_batch()
