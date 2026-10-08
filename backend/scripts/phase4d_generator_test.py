import json
import os
import sys
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
DATA_DIR = os.path.join(BACKEND_DIR, "data")

test_questions = [
    # PYTHON
    {"role": "Python Developer", "skill": "Functions & Functional Programming", "technology": "Python", "topic": "Closures", "intent": "explain", "difficulty": "medium", "question_type": "concept", 
     "question": "Walk through what happens when a nested Python function references a variable from its enclosing scope after the outer function has already returned. Where is that variable stored?", 
     "expected_answer": "It is stored in the function's __closure__ attribute as a cell object. This allows the nested function to retain access to the variable's state even after the outer scope's execution frame is destroyed."},
    
    {"role": "Python Developer", "skill": "Functions & Functional Programming", "technology": "Python", "topic": "Decorators", "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff", 
     "question": "A team proposes replacing a complex inheritance hierarchy with a series of stacked class decorators. What concerns would you raise regarding debugging and code readability?", 
     "expected_answer": "Stacked decorators can obscure the class signature and type hinting, making static analysis tools fail. Debugging becomes harder because the traceback is deeply nested in wrapper functions. Inheritance, while rigid, provides explicit MRO and clear type boundaries."},
    
    {"role": "Python Developer", "skill": "Iterators & Generators", "technology": "Python", "topic": "yield", "intent": "implement", "difficulty": "medium", "question_type": "implementation", 
     "question": "Sketch an approach for processing a 50GB log file in Python using generators. What would the implementation need to handle to prevent memory exhaustion?", 
     "expected_answer": "You would use a generator function with the `yield` keyword to read the file line-by-line (e.g., iterating directly over the file object). This prevents loading the entire 50GB into RAM, keeping memory usage constant regardless of file size."},
    
    {"role": "Python Developer", "skill": "Functions & Functional Programming", "technology": "Python", "topic": "Decorators", "intent": "debug", "difficulty": "hard", "question_type": "debugging", 
     "question": "A production application exhibits unexpected behavior because multiple decorators are altering the signature of the underlying function, breaking downstream kwargs. What would you inspect before changing the implementation, and how would you fix the signature loss?", 
     "expected_answer": "I would inspect the wrapper functions inside the decorators. To fix the signature loss, I would ensure every wrapper is decorated with `functools.wraps`, which explicitly copies the original function's `__name__`, `__doc__`, and signature metadata to the wrapper."},
    
    {"role": "Python Developer", "skill": "Functions & Functional Programming", "technology": "Python", "topic": "Closures", "intent": "architecture", "difficulty": "hard", "question_type": "architecture", 
     "question": "Where would you place the state boundary if you needed to maintain a private counter in a Python module without using classes or global variables? Design a solution utilizing closures.", 
     "expected_answer": "I would define an outer factory function that initializes a counter variable, and an inner function that uses the `nonlocal` keyword to modify the outer variable. The outer function returns the inner function, entirely encapsulating the state within the closure."},

    # JAVA
    {"role": "Java Developer", "skill": "Memory Management", "technology": "Java", "topic": "GC", "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff", 
     "question": "Under what workload would the G1 Garbage Collector become the weaker choice compared to the Z Garbage Collector (ZGC) in a Java 17 environment, and what would you sacrifice by switching?", 
     "expected_answer": "G1 becomes weaker for massive heaps (e.g., >100GB) requiring strict sub-millisecond pause times, as its pause times scale with heap size. ZGC guarantees ultra-low pauses regardless of heap size. However, switching to ZGC sacrifices overall application throughput due to higher concurrent CPU overhead."},
    
    {"role": "Java Developer", "skill": "Memory Management", "technology": "Java", "topic": "JVM", "intent": "diagnose", "difficulty": "hard", "question_type": "debugging", 
     "question": "A production team reports a massive spike in Metaspace usage leading to an OutOfMemoryError, even though heap usage is normal. What evidence would distinguish between a classloader leak and excessive reflection generation?", 
     "expected_answer": "I would capture a heap dump and inspect the classloader instances. A classloader leak shows multiple dead application classloaders kept alive by lingering references. Excessive reflection shows tens of thousands of auto-generated `sun.reflect.GeneratedMethodAccessor` classes created by the JVM to optimize reflection calls."},
    
    {"role": "Java Developer", "skill": "Concurrency", "technology": "Java", "topic": "Threads", "intent": "compare", "difficulty": "medium", "question_type": "comparison", 
     "question": "Which characteristics distinguish virtual threads (Project Loom) from traditional OS-bound platform threads, and under what circumstances would their behavior diverge under heavy I/O load?", 
     "expected_answer": "Virtual threads are lightweight, managed by the JVM, and do not map 1:1 to OS threads. Under heavy blocking I/O, platform threads block the underlying OS thread, causing resource exhaustion. Virtual threads simply unmount from the carrier OS thread when blocked, allowing the carrier to execute other virtual threads, massively increasing concurrency."},
    
    {"role": "Java Developer", "skill": "Memory Management", "technology": "Java", "topic": "GC", "intent": "scenario", "difficulty": "hard", "question_type": "scenario", 
     "question": "You inherit a system where the application experiences unpredictable 5-second 'stop-the-world' pauses during peak traffic. Which hypotheses would you test first regarding object promotion and survivor space sizing?", 
     "expected_answer": "I would hypothesize that the survivor spaces are too small, causing premature promotion of short-lived objects directly into the Old Generation. This leads to rapid Old Gen exhaustion and forces an expensive Full GC. I would test this by analyzing GC logs for 'promotion failure' or adjusting `-XX:SurvivorRatio`."},
    
    {"role": "Java Developer", "skill": "Memory Management", "technology": "Java", "topic": "JVM", "intent": "fundamentals", "difficulty": "easy", "question_type": "concept", 
     "question": "What invariant or principle explains why the JVM uses a dual-pass Just-In-Time (JIT) compilation strategy (C1 and C2 compilers) instead of purely interpreting bytecode or fully compiling it ahead of time?", 
     "expected_answer": "The principle is 'Tiered Compilation'. Pure interpretation is too slow. Full AOT compilation lacks runtime profiling data. The JVM interprets first for fast startup, uses C1 for quick, lightweight compilation, and uses runtime profiling data to heavily optimize hot paths with the slower, more aggressive C2 compiler."},

    # DEVOPS
    {"role": "DevOps / Cloud Engineer", "skill": "Docker", "technology": "Docker", "topic": "Images", "intent": "optimize", "difficulty": "medium", "question_type": "optimization", 
     "question": "A workload has degraded because CI/CD pipelines are pulling a 2GB Docker image on every deployment. Which optimization would you test first to drastically reduce the image footprint without breaking native dependencies?", 
     "expected_answer": "I would implement a multi-stage build. This allows the first stage to contain massive compile-time dependencies (like GCC or JDK) to build the binary, while the final stage only copies the compiled binary into a minimal base image like Alpine or distroless, dropping the 2GB overhead entirely."},
    
    {"role": "DevOps / Cloud Engineer", "skill": "Bash Scripting", "technology": "Linux", "topic": "Scripts", "intent": "implement", "difficulty": "hard", "question_type": "implementation", 
     "question": "What would the implementation need to handle if you were writing a Bash script to gracefully terminate background child processes when the main script receives a SIGTERM from Kubernetes?", 
     "expected_answer": "The script must implement an explicit `trap` for the SIGTERM signal. Inside the trap function, it must send SIGTERM to all its child process PIDs (often tracked via `$!`), optionally `wait` for them to exit gracefully, and then `exit` the main script. Otherwise, bash simply exits and leaves orphan processes."},
    
    {"role": "DevOps / Cloud Engineer", "skill": "Kubernetes Core", "technology": "Kubernetes", "topic": "Pods", "intent": "architecture", "difficulty": "hard", "question_type": "architecture", 
     "question": "A production system must support an application container that requires secure, localized fetching of secrets from HashiCorp Vault before startup. How would you structure a multi-container Pod to achieve this without leaking the vault token?", 
     "expected_answer": "I would structure the Pod using an Init Container. The Init Container authenticates with Vault, fetches the secrets, and writes them to an in-memory `emptyDir` volume (backed by tmpfs). The Init Container terminates, and the main application container mounts that `emptyDir` to read the secrets, ensuring the main app never possesses the Vault authentication token."},
    
    {"role": "DevOps / Cloud Engineer", "skill": "Kubernetes Core", "technology": "Kubernetes", "topic": "Pods", "intent": "debug", "difficulty": "medium", "question_type": "debugging", 
     "question": "A deployment introduces a new Pod configuration, but the Pod is permanently stuck in the 'Pending' state. What evidence would you collect first from the cluster scheduler, and which constraints might prevent node assignment?", 
     "expected_answer": "I would run `kubectl describe pod` and look at the 'Events' section. Common constraints preventing the scheduler from finding a node include insufficient CPU/Memory resources requested by the pod, unmatched node selectors or node affinities, or untolerated node taints."},
    
    {"role": "DevOps / Cloud Engineer", "skill": "Docker", "technology": "Docker", "topic": "Images", "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff", 
     "question": "When would building a single 'fat' monolithic Docker image be preferable to maintaining five highly optimized microservice images, and what would you sacrifice in terms of security scanning?", 
     "expected_answer": "A 'fat' image is preferable in resource-constrained edge/IoT deployments or simplified on-premise distributions where orchestrating multiple containers is too complex. However, you sacrifice security scanning precision; a vulnerability in one component flags the entire monolithic image, and the expanded attack surface increases the overall risk."},

    # AI ENGINEER
    {"role": "AI Engineer", "skill": "RAG Advanced", "technology": "Vector DBs", "topic": "Re-ranking", "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff", 
     "question": "Which constraints would make you choose to bypass a Cross-Encoder reranking step in your RAG pipeline, and what exactly would you give up regarding retrieval precision?", 
     "expected_answer": "Severe latency constraints or strict cost limits would force bypassing the Cross-Encoder, as reranking requires passing every retrieved chunk and the query through an expensive transformer model simultaneously. You sacrifice deep semantic interaction; without it, you rely purely on the bi-encoder's compressed semantic similarity, risking high-ranking but contextually irrelevant chunks."},
    
    {"role": "AI Engineer", "skill": "RAG Advanced", "technology": "Vector DBs", "topic": "Chunking Strategies", "intent": "implement", "difficulty": "hard", "question_type": "implementation", 
     "question": "Describe the implementation strategy for embedding a massive financial report containing complex, multi-page data tables. What would you change in the standard sliding-window chunking logic to prevent semantic destruction of the tables?", 
     "expected_answer": "Standard token-based sliding windows will slice tables arbitrarily, destroying structural meaning. I would implement semantic parsing (e.g., using Unstructured.io) to extract tables entirely. I would then generate a textual summary of the table for embedding, but retain the raw Markdown/HTML table in metadata to pass to the LLM during generation, ensuring structural integrity."},
    
    {"role": "AI Engineer", "skill": "AI Agents", "technology": "Tool Use", "topic": "Reasoning Loops", "intent": "architecture", "difficulty": "hard", "question_type": "architecture", 
     "question": "What would the major boundaries be when designing a ReAct (Reasoning and Acting) agent loop that must guarantee termination within 3 iterations regardless of the LLM's internal confidence?", 
     "expected_answer": "The core boundary is a deterministic host-side controller wrapper. The while-loop must strictly track the iteration count. On iteration 3, if the LLM attempts another tool call, the host intercepts it, prevents the API call, and forcibly injects a system prompt commanding the model to produce a final answer using only the current context, overriding the agent's autonomy."},
    
    {"role": "AI Engineer", "skill": "AI Agents", "technology": "Tool Use", "topic": "Reasoning Loops", "intent": "scenario", "difficulty": "hard", "question_type": "scenario", 
     "question": "Suppose traffic suddenly spikes on an agentic customer support system, leading to massive OpenAI API bills because the agent gets trapped in recursive tool-calling loops. How would you approach redesigning the system prompt and loop constraints to force decisive action?", 
     "expected_answer": "I would enforce strict 'circuit breakers' in the host code (e.g., max 5 tool calls per session). In the system prompt, I would penalize indecision by explicitly instructing the agent to return a standard 'handoff to human' response if it cannot resolve the issue in 2 steps, and providing few-shot examples showing when to stop gathering data and make a decision."},
    
    {"role": "AI Engineer", "skill": "RAG Advanced", "technology": "Vector DBs", "topic": "Re-ranking", "intent": "diagnose", "difficulty": "hard", "question_type": "debugging", 
     "question": "What would you check first, and why, if a RAG system successfully retrieves the correct document in the top 10 results from the vector database, but the final generative response completely ignores it after the reranking phase?", 
     "expected_answer": "I would check the exact scores output by the Cross-Encoder. The reranker is likely assigning a very low score to the correct document because of a vocabulary mismatch or lack of explicit keyword overlap with the query. If the reranker mistakenly pushes the correct document out of the Top-K cutoff sent to the LLM, the LLM physically cannot see it to answer the question."}
]

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def main():
    # Load the 1,980 existing staging questions
    all_qs = []
    
    # We will simulate loading the 1,980 by reading the jsonl and ignoring supabase for speed in this quick test,
    # BUT the prompt asks to run the diversity check against the 1980 dataset.
    # So we'll read both the local file and Supabase like the previous script.
    
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text as sql_text
    
    async def fetch_all_supabase():
        db_url = os.getenv("DATABASE_URL")
        clean_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://") if not db_url.startswith("postgresql+asyncpg") else db_url
        engine = create_async_engine(clean_db_url)
        out_rows = []
        async with engine.connect() as conn:
            res = await conn.execute(sql_text("SELECT id, content, metadata FROM public.document_embeddings;"))
            for r in res.fetchall():
                out_rows.append({"id": str(r[0]), "content": r[1], "metadata": r[2] if isinstance(r[2], dict) else json.loads(r[2] or "{}")})
        await engine.dispose()
        return out_rows
        
    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_running_loop()
        records = loop.run_until_complete(fetch_all_supabase())
    except Exception:
        records = asyncio.run(fetch_all_supabase())
        
    for r in records:
        meta = r.get("metadata", {})
        if meta.get("status") == "inactive": continue
        c = r.get("content", "")
        if "### Instruction:" in c and "### Output:" in c:
            q_text = c.split("### Instruction:")[1].split("### Output:")[0].strip()
            if "write a program" in q_text.lower() or "implement a function" in q_text.lower(): continue
        elif "### Technical Interview Question" in c:
            try:
                if "**Answer:**" in c:
                    q_text = c.split("**Answer:**")[0].replace("### Technical Interview Question", "").replace("**Question:**", "").strip()
                else:
                    q_text = meta.get("question", c[:200])
            except Exception:
                q_text = meta.get("question", c[:200])
        else:
            q_text = meta.get("question", c[:200])
            
        words = set(re.findall(r"\b[a-z0-9]+\b", q_text.lower()))
        if len(words) < 3: continue
        all_qs.append(q_text)
        
    gen_file = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
    if os.path.exists(gen_file):
        with open(gen_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                q = json.loads(line)
                all_qs.append(q.get("question", ""))
                
    print(f"Total reference questions loaded: {len(all_qs)}")
    
    ref_norm = [normalize_text(q) for q in all_qs]
    test_norm = [normalize_text(q["question"]) for q in test_questions]
    
    vectorizer = TfidfVectorizer(stop_words='english')
    # Fit on all to have a shared vocab
    vectorizer.fit(ref_norm + test_norm)
    
    ref_tfidf = vectorizer.transform(ref_norm)
    test_tfidf = vectorizer.transform(test_norm)
    
    sims = cosine_similarity(test_tfidf, ref_tfidf)
    
    exact_dupes = 0
    near_dupes = 0
    semantic_dupes = 0 # Using heuristic here
    
    for i in range(len(test_questions)):
        max_sim = sims[i].max() if len(sims[i]) > 0 else 0
        if max_sim > 0.98: exact_dupes += 1
        elif max_sim > 0.85: near_dupes += 1
        elif max_sim > 0.75: semantic_dupes += 1
        
    # Analyze Framing Diversity of Test Batch
    openings = []
    for q in test_questions:
        norm_q = normalize_text(q["question"])
        words = norm_q.split()
        if len(words) >= 3:
            openings.append(" ".join(words[:3]))
            
    top_openings = Counter(openings).most_common(5)
    
    intent_dist = Counter([q["intent"] for q in test_questions])
    diff_dist = Counter([q["difficulty"] for q in test_questions])
    
    print("\n--- TEST GENERATOR VALIDATION REPORT ---")
    print(f"Total Test Questions: {len(test_questions)}")
    print(f"Exact Duplicates against 1980: {exact_dupes}")
    print(f"Near Duplicates against 1980: {near_dupes}")
    print(f"Semantic/Competency Duplicates: {semantic_dupes}")
    print("\nTop 5 Opening Phrases (Framing Diversity):")
    for phrase, count in top_openings:
        print(f"  '{phrase}': {count} ({count/len(test_questions)*100:.1f}%)")
        
    print("\nIntent Distribution:")
    for i, c in intent_dist.items(): print(f"  {i}: {c}")
    print("\nDifficulty Distribution:")
    for d, c in diff_dist.items(): print(f"  {d}: {c}")

if __name__ == "__main__":
    main()
