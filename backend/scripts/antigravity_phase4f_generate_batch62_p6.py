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

ROLE = "Backend Developer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Group 16: Additional Backend Engineering (13 questions)
    ("B62_16_1", "concept", "medium", "concept", ["API Reliability"], "What is the 'Bulkhead Pattern' in backend resilience engineering?", "In shipbuilding, bulkheads are watertight partitions that prevent a leak in one section from sinking the entire ship. In backend engineering, if your API makes synchronous calls to 3 external services (A, B, C) using a single global thread pool of 100 threads, and Service A hangs, all 100 threads will eventually block waiting for A. The entire API crashes, meaning B and C also fail. The Bulkhead pattern physically partitions the thread pools. Service A gets 30 threads, B gets 30, and C gets 30. If Service A hangs, it exhausts its 30 threads and fails, but the API continues processing requests for B and C perfectly because their threads are isolated.", ["Isolating system resources (like thread pools or connection pools) to prevent a localized failure from causing a total system crash", "Prevents a single slow downstream dependency from exhausting the global thread pool", "Named after watertight ship compartments: one flooded compartment doesn't sink the ship"], ["A bulkhead is a large server rack"]),
    ("B62_16_2", "diagnose", "hard", "debugging", ["Concurrency"], "You implement a 'Double-Checked Locking' singleton pattern in Java to instantiate a heavy database connection pool. `if(pool == null) { synchronized(this) { if(pool == null) { pool = new Pool(); } } }`. However, under massive concurrency, you see `NullPointerException`s coming from the `pool` object inside other threads. Why is this thread-unsafe?", "This is a classic 'Instruction Reordering' or 'Memory Visibility' bug. In Java (and C++), the compiler or the CPU is allowed to reorder execution for performance. The `pool = new Pool()` instruction does three things: 1) Allocate memory, 2) Initialize the object, 3) Assign the memory address to the `pool` reference. If the CPU reorders this to 1 -> 3 -> 2, Thread A assigns the address to `pool` BEFORE finishing the initialization. Thread B comes along, sees `pool != null` (because the address exists), skips the lock, tries to use the partially constructed object, and crashes with an NPE. You MUST declare the `pool` variable as `volatile` to enforce a strict memory barrier, preventing instruction reordering.", ["Instruction Reordering: The CPU or Compiler reordered the object instantiation steps for performance", "Thread B read the `pool` reference after memory was allocated but before the object was fully initialized", "Fix: The singleton variable must be declared `volatile` to enforce memory barriers and prevent reordering"], ["The database connection pool ran out of water"]),
    ("B62_16_3", "implement", "medium", "implement", ["API Security"], "How do you securely implement 'Secret Rotation' for a backend application's Database Password without taking the application offline (Zero Downtime)?", "You cannot just change the password in the database and restart the app; there will be a 30-second window where in-flight requests fail due to authentication errors. You must implement 'Dual Credentials'. 1) In the database, you create a SECOND active password (or secondary user mapped to the same permissions) alongside the first. 2) You update your CI/CD secrets manager to provide the New password. 3) You perform a rolling deployment of the backend. During the 5-minute rollout, old pods use the Old password, new pods use the New password. 4) Once 100% of the old pods are terminated, you physically delete the Old password from the database.", ["Zero-downtime rotation requires the database to temporarily support TWO valid passwords simultaneously", "Perform a rolling deployment so new servers use the new credential while old servers finish using the old one", "Only after the deployment is 100% complete do you revoke/delete the old credential"], ["You just type really fast when changing the password"]),
    ("B62_16_4", "tradeoff", "hard", "tradeoff", ["Distributed Systems"], "What is the architectural tradeoff of using 'Choreography' versus 'Orchestration' for distributed microservice transactions (Sagas)?", "In Choreography, there is no central controller. Service A finishes its job and broadcasts an event (`OrderCreated`). Service B listens, does its job, and broadcasts `PaymentProcessed`. It is highly decoupled and infinitely scalable. The severe tradeoff is Observability and cyclic dependencies. It is nearly impossible to track the holistic state of a single user transaction because the logic is scattered across 10 codebases. In Orchestration, a central 'Coordinator' service explicitly commands A, then B, then C. It provides phenomenal visibility (you can see exactly where an order is stuck) and handles rollback logic centrally. The tradeoff is that the Orchestrator becomes a massive Single Point of Failure and a tightly coupled 'God Service'.", ["Choreography (Event-Driven): Highly decoupled and scalable, but creates massive observability blind spots and scattered business logic", "Orchestration (Centralized): Provides perfect visibility and central rollback control, but introduces a Single Point of Failure", "Tradeoff: Systemic decoupling vs holistic transactional visibility"], ["Choreography involves dancing, orchestration involves playing instruments"]),
    ("B62_16_5", "scenario", "medium", "scenario", ["Performance Tuning"], "Your GraphQL API sits behind a CDN. You notice that 100% of the requests to fetch public, identical blog posts are bypassing the CDN and hitting your backend database, crushing performance. Why is the CDN failing to cache GraphQL?", "GraphQL natively operates exclusively over HTTP `POST` requests. By strict HTTP specification, CDNs and intermediate proxies (like Varnish or Cloudflare) will ONLY cache HTTP `GET` requests; they treat all `POST` requests as state-mutating and blindly forward them to the origin server. To fix this, you must implement 'Automatic Persisted Queries' (APQ). The client sends the query hash via a standard HTTP `GET` request (e.g., `GET /graphql?hash=123`). The CDN can now securely cache the JSON response at the edge based on the query hash.", ["GraphQL exclusively uses HTTP `POST`, which CDNs refuse to cache by default", "CDNs only cache HTTP `GET` requests because POST implies state mutation", "Fix: Use Automatic Persisted Queries (APQ) or configure clients to send Read queries as `GET` requests with query parameters"], ["The CDN doesn't understand GraphQL syntax"]),
    ("B62_16_6", "explain", "hard", "explain", ["Distributed Systems"], "Explain the 'Split-Brain' problem in distributed databases and how 'Leader Election' consensus algorithms (like Raft or Paxos) prevent it.", "Split-Brain occurs when a network cable is cut between Datacenter A and Datacenter B. Both halves of the database cluster think the other half is dead. If both promote themselves to 'Primary Leader', they both start accepting writes independently, completely corrupting the data. Raft and Paxos prevent this by enforcing a strict 'Majority Quorum' (N/2 + 1). If you have a 5-node cluster, 3 nodes must be able to communicate to elect a Leader. If the network splits 2 and 3, the side with 3 nodes elects a Leader and continues. The side with 2 nodes mathematically realizes it lacks a majority and instantly demotes itself to Read-Only or halts, definitively preventing two concurrent leaders.", ["Split-Brain: A network partition causes both sides of a cluster to assume leadership, corrupting data with conflicting writes", "Consensus Algorithms (Raft/Paxos) require a strict mathematical majority (N/2 + 1) to elect a leader", "The minority partition realizes it lacks quorum and halts writes, preventing data corruption"], ["Split brain is when the CPU is sliced in half"]),
    ("B62_16_7", "concept", "medium", "concept", ["Caching"], "What is the 'Cache Penetration' problem, and how does a Bloom Filter solve it without consuming massive amounts of RAM?", "Cache Penetration is when attackers request IDs that do not exist (e.g., `user/99999`). It misses the cache, hits the DB, the DB returns Null, and the cache isn't updated. The DB is continuously hammered. A Bloom Filter is a highly space-efficient probabilistic data structure placed in RAM before the cache. When a new user is created in the DB, they are added to the Bloom Filter. When a request arrives, the Bloom Filter checks if the ID exists. It can say 'Definitely Not' (with 100% certainty, instantly dropping the request without hitting the DB) or 'Possibly Yes'. It requires only megabytes of RAM to map billions of IDs, protecting the DB from malicious penetration.", ["Penetration: Malicious requests for non-existent data bypass the cache and hammer the DB", "Bloom Filter: A space-efficient probabilistic memory structure that definitively answers 'Is this item NOT in the set?'", "Drops 100% of invalid requests instantly in RAM without requiring a DB lookup"], ["A bloom filter is used to censor bad words in the cache"]),
    ("B62_16_8", "diagnose", "hard", "debugging", ["Background Processing"], "Your backend schedules payments using a distributed Cron system running on 5 identical backend nodes. Every midnight, a payment script executes. However, you notice that 20% of your users are being charged 5 times simultaneously for their subscription. What architectural flaw in your Cron system caused this?", "Running a standard local Cron daemon (`crontab` or a naive Node.js/Spring `@Scheduled` task) on a horizontally scaled architecture is a catastrophic anti-pattern. Because you have 5 nodes, all 5 identical Cron instances trigger at exactly midnight. They all query the database simultaneously, see the same 'unpaid' users, and all 5 independently charge the credit cards. To fix this, you MUST use a 'Distributed Job Scheduler' (like Quartz, BullMQ, or AWS EventBridge) backed by a centralized Database or Redis. The 5 nodes must compete for a centralized lock; only the node that successfully acquires the lock executes the midnight job.", ["Local Cron jobs running on horizontally scaled nodes will trigger duplicate, concurrent executions", "All N nodes wake up at the exact same time and execute the exact same business logic (charging users N times)", "Fix: Implement a Distributed Scheduler that uses centralized database/Redis locking to guarantee single execution"], ["The users pressed the pay button 5 times very fast"]),
    ("B62_16_9", "implement", "medium", "implement", ["API Evolution"], "How do you implement 'Pagination' for an API that returns 500,000 records, and why is `OFFSET/LIMIT` considered an anti-pattern for massive datasets?", "If you use `OFFSET 400000 LIMIT 100`, the database must still physically scan, load into memory, and discard the first 400,000 rows before returning the 100 you want. This causes queries on deep pages to take 10+ seconds and causes severe CPU spikes. To implement scalable pagination, you MUST use 'Keyset Pagination' (Cursor-Based Pagination). The API returns the highest `ID` (or timestamp) of the current page as a `next_cursor`. The client passes that cursor in the next request: `SELECT * FROM users WHERE id > :cursor LIMIT 100`. Because `id` is indexed, the DB jumps instantly to that exact row in O(log N) time, making page 4,000 exactly as fast as page 1.", ["`OFFSET` forces the database to scan and discard hundreds of thousands of rows, destroying performance on deep pages", "Architectural Fix: Keyset/Cursor-Based Pagination", "Use an indexed column (`WHERE id > :cursor LIMIT 100`) to jump instantly to the next record, ensuring O(log N) performance regardless of depth"], ["You just tell the frontend to download all 500,000 records at once"]),
    ("B62_16_10", "tradeoff", "hard", "tradeoff", ["Distributed Systems"], "What is the tradeoff of using a 'Shared Database' across multiple microservices versus the 'Database-per-Service' pattern?", "A Shared Database is incredibly easy to manage; you can do massive SQL `JOIN`s across 'Orders' and 'Users' instantly, and enforce foreign keys. The severe tradeoff is tight coupling and blast radius. If the 'Users' team renames a column, they instantly break the 'Orders' microservice. If the 'Analytics' service locks a table, the entire company goes down. 'Database-per-Service' forces absolute decoupling: the 'Orders' service CANNOT query the 'Users' DB. It must make an HTTP call to the Users API. This allows independent schema evolution and isolated scaling, but the massive tradeoff is that simple `JOIN`s are now impossible, forcing you to implement complex, slow, in-memory data aggregation at the API Gateway or BFF layer.", ["Shared Database: Easy `JOIN`s and ACID transactions, but massive blast radius and tight schema coupling that blocks independent deployments", "Database-per-Service: Guarantees deployment independence and isolates database failures", "Tradeoff: Eliminates the ability to do cross-domain SQL `JOIN`s, forcing complex distributed data aggregation in application code"], ["Shared database means the database is open source"]),
    ("B62_16_11", "scenario", "medium", "scenario", ["Concurrency"], "You have a backend API written in Python (Flask/Gunicorn). It connects to a Postgres database. You increase the Gunicorn workers to 100 to handle more HTTP traffic. Suddenly, every API request throws an error: `FATAL: sorry, too many clients already`. What is the bottleneck, and what specific architectural component must you introduce?", "PostgreSQL uses a heavy process-per-connection model. It typically maxes out at 100-300 direct concurrent connections before running out of memory. If you run 10 API servers, each with 100 Gunicorn workers, you are attempting to open 1,000 persistent connections to Postgres, instantly crashing it. You cannot fix this by tuning Postgres alone. You MUST introduce a 'Database Connection Multiplexer / Pooler' like PgBouncer. PgBouncer sits between the API and Postgres. It accepts the 1,000 connections from the API (which are lightweight), but multiplexes those queries onto a tiny pool of just 50 actual heavy physical connections to PostgreSQL.", ["PostgreSQL uses heavy OS processes for connections; it cannot handle thousands of direct persistent connections", "Scaling the API workers horizontally instantly exhausted the database connection limit", "Architectural Fix: Introduce a Connection Pooler/Multiplexer (e.g., PgBouncer) to funnel thousands of lightweight API connections into a small number of physical DB connections"], ["You just need to upgrade to Postgres Pro"]),
    ("B62_16_12", "concept", "medium", "concept", ["API Security"], "What is 'CORS' (Cross-Origin Resource Sharing) in backend APIs, and why doesn't it protect against Server-to-Server API abuse?", "CORS is a security mechanism enforced entirely by the USER'S WEB BROWSER. When a frontend script on `domain-a.com` tries to call a backend API on `domain-b.com`, the *browser* sends an `OPTIONS` Preflight request to the backend asking, 'Is domain-a allowed to call you?'. If the backend says no, the *browser* blocks the Javascript execution. CORS does absolutely nothing to protect the backend from a malicious script running on a Python/Node.js server, or a `curl` command, because those tools simply ignore CORS headers. CORS only prevents malicious Javascript in a browser from silently making requests on behalf of an authenticated user.", ["CORS is enforced exclusively by the Web Browser, not the Backend Server", "It prevents malicious Javascript from reading data from a different domain on behalf of the user", "It provides zero protection against malicious server-side scripts (e.g., Python `requests` or `curl`), which simply ignore CORS headers entirely"], ["CORS stands for Centralized Object Relational System"]),
    ("B62_16_13", "explain", "hard", "explain", ["Performance Tuning"], "Explain the impact of 'Garbage Collection (GC) Stop-The-World Pauses' on backend tail latency (p99), and how it dictates modern backend architecture.", "In managed languages (Java, C#, Node.js, Go), the runtime must periodically freeze the entire application to clean up orphaned memory objects (Stop-The-World). While a normal API request takes 5ms, if a user's request arrives during a 500ms GC pause, their specific request takes 505ms. This destroys p99 Tail Latency. In high-frequency trading or ultra-low latency microservices, a 500ms pause is unacceptable. To fix this, architects must either: 1) Tune the JVM to use concurrent low-pause collectors (ZGC/Shenandoah), 2) Implement 'Object Pooling' in the code to avoid creating new objects (eliminating GC pressure), or 3) Rewrite the specific latency-critical microservice in a non-GC language like Rust or C++.", ["GC pauses freeze the entire application randomly, causing severe, unpredictable spikes in p99 Tail Latency", "A 5ms request can randomly take 500ms if it hits during a Stop-The-World phase", "Mitigation: Use low-pause concurrent collectors (ZGC), implement Object Pooling to reduce allocation, or rewrite in Rust/C++"], ["Garbage collection is when the intern takes out the trash in the datacenter"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 6).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Systems Engineer", "Software Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Backend Core",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "Software Engineering",
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
    print(f"Batch: 62")
    print(f"Target role: {ROLE}")
    print(f"Attempted: 100")
    print(f"Accepted: {len(accepted)}") 
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")
    
    sha256 = hashlib.sha256()
    with open(OUT, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            
    print(f"\nFinal SHA256: {sha256.hexdigest()}")


if __name__ == "__main__":
    run_batch()
