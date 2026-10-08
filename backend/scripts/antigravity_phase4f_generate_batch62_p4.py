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
    # Group 10: Multi-Tenancy
    ("B62_10_1", "concept", "medium", "concept", ["Multi-Tenancy"], "In a B2B SaaS backend, what is the difference between 'Row-Level Multi-Tenancy' (Shared Schema) and 'Database-per-Tenant' (Siloed), and why would you choose the latter?", "Row-Level Multi-Tenancy stores all customers in the exact same tables, differentiated only by a `tenant_id` column. It is extremely cheap and easy to manage (one DB migration updates everyone). However, it risks catastrophic cross-tenant data leaks (a missing `WHERE` clause exposes another company's data) and 'Noisy Neighbor' problems (Tenant A runs a massive report and slows down the DB for Tenant B). Database-per-Tenant gives every customer their own physical or logical database. It is much more expensive and makes schema migrations difficult, but mathematically guarantees data isolation (perfect for healthcare/finance compliance) and ensures dedicated performance per tenant.", ["Row-Level (Shared): Cheap and easy to maintain, but high risk of data leaks and Noisy Neighbor performance degradation", "Database-per-Tenant (Siloed): Complex schema migrations and high cost, but mathematically guarantees isolation and dedicated performance", "Choose Database-per-Tenant for strict regulatory compliance (HIPAA/SOC2) or enterprise SLAs"], ["Row-level means the tenants live in a row of houses"]),
    ("B62_10_2", "diagnose", "hard", "debugging", ["Multi-Tenancy"], "Your SaaS backend uses Row-Level Multi-Tenancy (all tenants in one PostgreSQL table). You implement a new 'Search Users by Email' API endpoint. During a pen-test, an attacker from Tenant A successfully discovers the email addresses of the CEO of Tenant B. You check the code, and the SQL query correctly includes `WHERE tenant_id = 'A'`. How is cross-tenant data leaking?", "This is a Timing Attack or Error-Based Data Leak caused by Unique Constraints. The attacker attempts to register or search for `ceo@tenantB.com`. Even though the `WHERE tenant_id = 'A'` clause is present, the database evaluates the global `UNIQUE(email)` constraint across the entire table *before* returning. If the email exists in Tenant B, the DB throws a 'Unique Constraint Violation' error, or the query takes slightly longer to fail. The backend catches the error and returns `Email already in use`. The attacker now mathematically knows the CEO is a customer. To fix this, Unique Indexes in multi-tenant shared schemas MUST be composite: `UNIQUE(tenant_id, email)`. Otherwise, the global index leaks existence across tenant boundaries.", ["Global Unique Indexes in a shared schema leak the existence of data across tenant boundaries", "Attackers use error messages ('Email taken') or timing attacks to map out competitors' users", "Fix: Unique constraints MUST be composite, pairing the field with the `tenant_id` (e.g., `UNIQUE(tenant_id, email)`)"], ["The CEO accidentally emailed the attacker"]),
    ("B62_10_3", "implement", "medium", "implement", ["Multi-Tenancy"], "How do you implement 'Noisy Neighbor Protection' in a multi-tenant backend API to prevent one enterprise customer from crashing the system for all small customers?", "A global rate limit (e.g., 10,000 req/sec total) does not work; the enterprise customer will simply consume all 10,000 requests, starving everyone else. You must implement 'Per-Tenant Quotas' and 'Fair Queuing'. When a request arrives, the API Gateway or Backend extracts the `tenant_id` from the JWT. It checks a Redis token-bucket explicitly keyed to that tenant (e.g., `rate_limit:tenant_A`). If Tenant A exceeds their specific tier's quota (e.g., 100 req/sec), they receive a `429 Too Many Requests`, while Tenant B's API calls pass through completely unaffected.", ["Global rate limits fail because a single massive tenant will consume the entire global pool", "Extract the `tenant_id` at the API Gateway or Middleware layer", "Enforce strict Per-Tenant Quotas using a centralized store like Redis, returning 429s only to the violating tenant"], ["You just ask the noisy neighbor to keep it down"]),
    ("B62_10_4", "tradeoff", "hard", "tradeoff", ["Multi-Tenancy"], "What is the tradeoff of implementing 'Tenant-Level Encryption' (Customer Managed Keys - CMK) versus 'Platform-Level Encryption' in a B2B backend?", "Platform-Level Encryption (where the SaaS provider holds one master key for the entire DB) is transparent, cheap, and zero-maintenance. However, enterprise customers often refuse to buy the software because a rogue DBA at the SaaS company could read their data. Tenant-Level Encryption allows each customer to bring their own AWS KMS key. The backend dynamically fetches Tenant A's key to encrypt/decrypt their specific rows. If Tenant A leaves, they delete their key in AWS, instantly cryptographically shredding their data in your DB. The severe tradeoff is Performance and Searchability. You can no longer run simple `LIKE` searches or `ORDER BY` on encrypted columns in the DB, and every read/write requires a CPU-heavy cryptographic operation and a KMS API call.", ["Platform-Level: Cheap, transparent, supports native SQL sorting/searching, but offers no isolation against rogue insiders", "Tenant-Level: Allows customers to 'Bring Your Own Key' (BYOK) for cryptographic shredding and absolute privacy", "Tradeoff: Destroys the ability to do native DB searches (`LIKE`), degrades performance, and massively increases architectural complexity"], ["Tenant level encryption means the tenant has to encrypt the data themselves with a pen and paper"]),
    ("B62_10_5", "scenario", "medium", "scenario", ["Multi-Tenancy"], "You are migrating a massive legacy customer (Tenant Z) from the Shared DB to their own Dedicated DB to improve performance. The migration script takes 4 hours to copy the data. How do you ensure zero data loss and minimal downtime for Tenant Z during this backend migration?", "You must use the 'Dual-Write' or 'Change Data Capture (CDC)' pattern. You cannot afford 4 hours of downtime, but if you leave Tenant Z active in the Shared DB during the 4-hour copy, any new writes they make will be missing from the new Dedicated DB. 1) Configure the backend to Dual-Write (write to both the Shared DB and a Kafka queue/CDC log). 2) Run the massive 4-hour historical copy. 3) Once the copy finishes, apply the backlog of CDC events to the new Dedicated DB to catch it up to real-time. 4) Briefly pause Tenant Z's traffic for 5 seconds, switch their connection string to the new DB, and resume traffic. Zero data loss, near-zero downtime.", ["Leaving the system active during a long migration results in lost 'delta' writes", "Use Dual-Writes or Change Data Capture (CDC) to stream live changes while the historical copy runs", "Replay the CDC delta backlog to catch up the new DB, requiring only seconds of cutover downtime"], ["You just tell the customer to stop using the app for 4 hours"]),
    ("B62_10_6", "explain", "medium", "explain", ["Multi-Tenancy"], "Explain how PostgreSQL 'Row Level Security' (RLS) simplifies multi-tenant backend code.", "Without RLS, every single SQL query in the backend code MUST manually include `WHERE tenant_id = ?`. If a junior developer forgets this clause on a `DELETE` or `SELECT` statement, it causes a catastrophic cross-tenant data breach. PostgreSQL RLS pushes this security down to the database kernel. You define a policy on the table (`CREATE POLICY... USING (tenant_id = current_setting('app.current_tenant'))`). In the backend, when you open a DB connection, you execute one command to set the session variable to the user's `tenant_id`. From that point on, even if the backend executes a raw `SELECT * FROM users`, the PostgreSQL kernel automatically intercepts it and mathematically restricts the results to that specific tenant, providing bulletproof, invisible isolation.", ["Without RLS, developers must manually append `WHERE tenant_id = ?` to every query, risking catastrophic human error", "RLS enforces the isolation at the PostgreSQL kernel level via Policies", "The backend sets a session variable once per request; the database automatically scopes all subsequent queries, guaranteeing security even on `SELECT *`"], ["RLS means the rows are protected by a security guard"]),

    # Group 11: Real-Time Backend Systems
    ("B62_11_1", "concept", "medium", "concept", ["Real-Time Systems"], "What is the difference between Server-Sent Events (SSE) and WebSockets, and when would a backend developer choose SSE?", "WebSockets provide full-duplex, bidirectional communication over a single persistent TCP connection; the client can send data to the server, and the server can push data to the client. It requires complex load balancing and custom framing. Server-Sent Events (SSE) provide unidirectional, server-to-client communication over standard HTTP. The client opens a standard HTTP GET request, and the server holds it open, continuously writing data chunks (`text/event-stream`). SSE is drastically simpler to implement, works perfectly with standard HTTP load balancers and firewalls, and has built-in automatic reconnection. You choose SSE for unidirectional feeds (Live stock tickers, News feeds, Progress bars) where the client doesn't need to stream data back.", ["WebSockets: Bidirectional, full-duplex, complex load balancing, custom protocol", "SSE: Unidirectional (Server-to-Client), standard HTTP, built-in reconnection logic", "Choose SSE for real-time dashboards or feeds where the client only listens, avoiding WebSocket complexity"], ["SSE is for sending emails, WebSockets are for sockets"]),
    ("B62_11_2", "diagnose", "hard", "debugging", ["Real-Time Systems"], "Your backend has a fleet of 5 Node.js WebSocket servers behind an AWS ALB. User A connects to Server 1. User B connects to Server 2. User A sends a chat message intended for User B. User B never receives it. The database shows the message was saved. Why did the real-time delivery fail, and how do you fix it?", "This is the classic 'Distributed Pub/Sub' failure in stateful WebSocket architectures. User A's connection is physically held in the RAM of Server 1. User B's connection is physically held in the RAM of Server 2. When Server 1 processes User A's message, it searches its local RAM for User B's socket, fails to find it, and drops the real-time push. To fix this, you must implement a 'Backplane' (usually Redis Pub/Sub). When Server 1 receives the message, it publishes it to Redis. Server 2 is subscribed to Redis, receives the event, finds User B in its local RAM, and pushes the message over the socket.", ["WebSocket connections are stateful and pinned to the specific server's physical RAM", "Server 1 has no way to push data to a socket connected to Server 2", "Architectural Fix: Implement a Redis Pub/Sub Backplane. All servers publish and subscribe to Redis to route messages across the fleet"], ["The load balancer ate the message"]),
    ("B62_11_3", "implement", "medium", "implement", ["Real-Time Systems"], "How do you implement 'Connection Affinity' (Sticky Sessions) for long-polling or WebSocket connections, and what is its major architectural drawback?", "To implement Sticky Sessions, you configure the Load Balancer (ALB, NGINX) to inject a routing Cookie into the client's first response, or to hash the client's IP address. On all subsequent requests, the Load Balancer reads the cookie/hash and guarantees the client is routed to the exact same backend server. This is crucial for long-polling state. The massive drawback is 'Uneven Load Distribution' and 'Fragility'. If Server 1 crashes, all its pinned clients instantly disconnect and flood Server 2, potentially crashing it. Furthermore, a single server might randomly get pinned with 100 power-users, maxing out its CPU, while other servers sit idle, defeating the purpose of load balancing.", ["Configure the Load Balancer to use Cookie injection or IP Hashing to route clients to the same physical backend server", "Required for maintaining in-memory state across multiple HTTP requests (like long-polling)", "Drawback: Causes uneven CPU load distribution and catastrophic 'thundering herds' if a server crashes and shifts its pinned traffic"], ["You implement it by putting superglue on the server rack"]),
    ("B62_11_4", "tradeoff", "hard", "tradeoff", ["Real-Time Systems"], "What is the tradeoff of handling 'Offline Client Syncing' via an Event Sourcing log replay versus a Last-Modified-Timestamp pull?", "In a Timestamp Pull, when a mobile client comes back offline after 3 days, it simply calls `GET /data?since=1630000000`. The backend queries the DB for any rows modified since that timestamp. It is incredibly simple to implement and uses standard CRUD DB indexes. The tradeoff is it cannot easily handle 'Deletions' (if a row is deleted, its timestamp is gone, so the client never learns it was deleted without complex Tombstone rows) and it loses granular state transitions. Event Sourcing Log Replay forces the client to download the exact stream of domain events (`ItemAdded`, `ItemUpdated`, `ItemDeleted`) that occurred while offline. It guarantees perfect, deterministic state synchronization (including deletes), but requires a highly complex, append-only Kafka/EventStore architecture and forces the client to process heavy business logic locally.", ["Timestamp Pull: Simple CRUD query using `updated_at`. Tradeoff: Cannot natively sync Deletions (requires Tombstones) and misses intermediate state changes", "Event Log Replay: Client downloads an immutable stream of exact domain events. Tradeoff: Highly complex architecture and forces heavy client-side processing", "Event sourcing guarantees perfect offline sync (including deletes) at the cost of massive system complexity"], ["Timestamp pull involves literally pulling a clock out of the server"]),
    ("B62_11_5", "scenario", "medium", "scenario", ["Real-Time Systems"], "Your backend broadcasts live sports scores via WebSockets to 500,000 concurrent mobile users. During a major goal, the backend attempts to write 500,000 JSON payloads to the open sockets. The backend instantly runs out of memory (OOMKilled). How do you re-architect the 'Fan-Out' to prevent memory exhaustion?", "This is a Fan-Out memory explosion. The backend is likely iterating over an array of 500,000 connection objects, serializing a string to JSON 500,000 times, and placing 500,000 copies of the payload into the OS network send buffers simultaneously, instantly exhausting RAM. To fix this: 1) Serialize the JSON exactly ONCE. 2) Use 'Backpressure'. Do not blindly push to all sockets in a synchronous loop. Chunk the broadcasts (e.g., send to 10,000 users, yield to the Event Loop, send to the next 10,000). 3) Offload the Fan-Out entirely to a managed edge service like AWS API Gateway WebSockets, Pusher, or Ably, so your backend only sends ONE payload to the edge, and the edge handles the 500,000 socket buffers.", ["Serializing and buffering 500,000 payloads in a single synchronous loop will instantly exhaust Node/JVM memory", "Serialize the JSON exactly once before the loop", "Implement Backpressure/Chunking to yield memory, or completely offload the Fan-Out to a managed Edge/PubSub provider (AWS IoT/Pusher)"], ["You just send the score via SMS instead"]),

    # Group 12: Background Job Systems
    ("B62_12_1", "concept", "medium", "concept", ["Background Processing"], "What is a 'Visibility Timeout' in a background job queue (like AWS SQS), and why is it critical for fault tolerance?", "In distributed queues, a message is not instantly deleted when a worker reads it; otherwise, if the worker crashes mid-processing, the message is permanently lost. Instead, when Worker A reads the message, the queue 'hides' it from all other workers for a specific duration (the Visibility Timeout, e.g., 5 minutes). If Worker A successfully processes the job, it makes an explicit API call to delete the message. If Worker A crashes (or takes longer than 5 minutes due to a deadlock), the Visibility Timeout expires, and the queue automatically makes the message visible again so Worker B can pick it up and process it. It guarantees at-least-once processing despite worker failure.", ["Workers do not delete messages upon reading; the queue hides them temporarily", "If the worker succeeds, it explicitly deletes the message", "If the worker crashes, the timeout expires, the message reappears, and another worker retries it, guaranteeing fault tolerance"], ["It means the message wears camouflage so hackers can't see it"]),
    ("B62_12_2", "diagnose", "hard", "debugging", ["Background Processing"], "A background worker processes video uploads. It pulls a job from SQS (Visibility Timeout: 10 mins). The video processing takes 15 minutes. The worker successfully finishes and deletes the message from SQS. However, the database shows the exact same video was processed twice. Why did this duplicate processing occur?", "The job processing time (15 mins) exceeded the SQS Visibility Timeout (10 mins). When the timer hit 10 minutes, SQS assumed the first worker had crashed, and made the message visible again. A second worker immediately pulled the message and started processing the exact same video. Five minutes later, the first worker finished and deleted the message, but the second worker was already halfway through the duplicate job. To fix this, you must either increase the global Visibility Timeout to > 15 mins, or have the worker dynamically call `ChangeMessageVisibility` to 'heartbeat' and extend the timeout while it is actively working on long jobs.", ["The job execution time exceeded the queue's Visibility Timeout", "The queue assumed the worker died and handed the job to a second worker, causing concurrent duplicate processing", "Fix: Increase the timeout, or implement a background 'heartbeat' thread in the worker to dynamically extend the visibility timeout"], ["The video was so good the server wanted to watch it twice"]),
    ("B62_12_3", "implement", "medium", "implement", ["Background Processing"], "How do you implement 'Job Deduplication' in a distributed background worker system to prevent the same email from being sent to a user 5 times if the event queue has a retry storm?", "Background queues (SQS, RabbitMQ, Kafka) only guarantee 'At-Least-Once' delivery; duplicates are inevitable due to network blips. You must implement Idempotency in the worker logic. 1) The job payload must include a unique `Job-ID` or `Idempotency-Key` (e.g., `email_user123_welcome`). 2) Before sending the email, the worker attempts to write this ID to a centralized datastore (Redis or PostgreSQL) with a Unique Constraint. If the DB returns a Unique Constraint Violation (or Redis `SETNX` returns false), it means another worker already processed this exact job. The current worker instantly aborts, marks the job as success, and moves on, guaranteeing exactly-once side effects.", ["Queues inherently deliver duplicates; exactly-once delivery is a myth at the network layer", "The job payload must contain a deterministic Unique ID", "The worker must use a centralized DB/Redis atomic check (Unique Constraint or `SETNX`) to verify if the ID was already processed before executing side-effects"], ["You just ask the user to ignore duplicate emails"]),
    ("B62_12_4", "tradeoff", "hard", "tradeoff", ["Background Processing"], "What is the architectural tradeoff of using an In-Memory queue (e.g., Node.js `bull`, Java `ArrayBlockingQueue`) versus a persistent external broker (e.g., RabbitMQ, Kafka) for background tasks?", "In-Memory queues are incredibly fast (nanosecond latency), require zero external infrastructure, and are trivial to deploy. The severe tradeoff is Data Volatility and Scalability. If the API server crashes, restarts, or scales down, every pending job in the in-memory queue is permanently wiped out. Furthermore, you cannot distribute jobs across multiple servers; if Server A has 10,000 jobs in RAM and Server B has 0, Server B cannot help process them. External brokers (Kafka/RabbitMQ) write jobs to persistent disk, surviving crashes and allowing 50 workers to independently pull from a centralized backlog, but require complex infrastructure management and introduce network latency.", ["In-Memory: Nanosecond speed, zero infrastructure cost, but highly volatile", "External Broker: Persistent disk storage, survives server crashes, enables distributed worker scaling", "Tradeoff: In-Memory risks catastrophic data loss on crash and prevents load-balancing background tasks across multiple nodes"], ["In-memory queues require you to memorize the jobs yourself"]),
    ("B62_12_5", "scenario", "medium", "scenario", ["Background Processing"], "Your backend generates massive end-of-month financial PDF reports. The API receives a request, generates the PDF synchronously (takes 45 seconds), and returns it. During month-end, the server crashes due to 100% CPU. You are tasked with offloading this to a background worker. How does the frontend client retrieve the PDF after it's generated?", "The synchronous HTTP request must be refactored into an Asynchronous 'Polling' or 'Webhook' pattern. 1) Frontend requests the report. 2) Backend pushes a job to SQS and instantly returns an HTTP 202 Accepted with a `job_id`. 3) The frontend displays a loading spinner and polls an endpoint `GET /reports/status/{job_id}` every 3 seconds. 4) The background worker generates the PDF, uploads it to AWS S3, and updates the database row for `job_id` to 'COMPLETED' with the S3 URL. 5) The next time the frontend polls, the backend returns HTTP 200 with the S3 download URL, and the frontend redirects the user to download the file.", ["The synchronous API must be converted to an Asynchronous Request-Reply pattern", "The API instantly returns a tracking `job_id` (HTTP 202 Accepted)", "The worker processes the heavy task, uploads the result to S3, and updates the DB state so the polling frontend can finally retrieve the URL"], ["The server just prints the PDF and mails it to the user"])
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
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
