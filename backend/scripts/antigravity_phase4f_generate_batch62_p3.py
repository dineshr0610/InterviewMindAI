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
    # Group 7: Security
    ("B62_7_1", "concept", "hard", "concept", ["API Security"], "What is the 'Confused Deputy' problem in microservice authorization, and how do you mitigate it?", "The Confused Deputy occurs when User A calls Service 1 (which they are authorized to use), and Service 1 calls Service 2 to fetch data on behalf of User A. If Service 1 uses its *own* highly privileged machine-to-machine token to call Service 2, Service 2 cannot tell that User A initiated the request. An attacker (User A) can trick Service 1 into fetching User B's private data from Service 2 (since Service 1 is highly privileged). To mitigate this, you must implement 'Token Exchange' (e.g., OAuth2 Token Exchange RFC 8693) or strictly propagate the original user's JWT through every microservice hop, so Service 2 evaluates both the service identity AND the original user's identity.", ["Occurs when a highly-privileged intermediary service is tricked into misusing its authority on behalf of a malicious user", "Service 2 blindly trusts Service 1's machine token, ignoring the original user context", "Mitigation: Forward the original user's JWT or use Token Exchange so downstream services evaluate the original user's permissions"], ["A confused deputy is an admin user who forgets their password"]),
    ("B62_7_2", "diagnose", "medium", "debugging", ["API Security"], "Your backend API has a feature allowing users to input an external Image URL, which the backend downloads and resizes. A security researcher inputs `http://169.254.169.254/latest/meta-data/` and successfully downloads your AWS IAM credentials. What vulnerability is this, and how do you fix it?", "This is a Server-Side Request Forgery (SSRF) vulnerability. The backend blindly accepted a user-provided URL and executed a GET request from the server's internal network. The IP `169.254.169.254` is the AWS EC2 metadata service, which is unauthenticated by default (IMDSv1) and returns temporary IAM credentials to any local process. To fix this: 1) Implement a strict Allowlist/Denylist in the backend code to reject internal IP ranges (10.x, 192.168.x, 169.254.x). 2) Upgrade AWS EC2 to IMDSv2, which requires a custom HTTP header (`X-aws-ec2-metadata-token`) to fetch metadata, defeating simple SSRF GET requests.", ["Server-Side Request Forgery (SSRF): The server was tricked into making an unauthorized internal HTTP request", "The attacker accessed the AWS Metadata endpoint to steal IAM credentials", "Fix: Block internal/loopback IPs in the application logic, and strictly enforce AWS IMDSv2"], ["The user hacked the database using SQL injection in the image url"]),
    ("B62_7_3", "implement", "hard", "implement", ["API Security"], "How do you securely architect Webhook Authentication for an external provider (like Stripe) sending POST requests to your API?", "You must NEVER rely solely on a static API key in the URL (`?api_key=123`) or a static header, as these are easily leaked or replayed. The secure architecture is 'HMAC Request Signing'. 1) You and Stripe share a cryptographic Secret. 2) Stripe takes the JSON body, timestamps it, and creates an HMAC-SHA256 signature, passing it in a custom header (e.g., `Stripe-Signature`). 3) Your backend takes the exact raw JSON body it received, timestamps it, and hashes it using your local copy of the Secret. 4) If the hashes match exactly, the payload is authentic and untampered. 5) You MUST also check the timestamp; if it is older than 5 minutes, reject it to prevent Replay Attacks.", ["Use HMAC-SHA256 cryptographic signatures, not static API keys", "Hash the raw JSON body with a shared secret to prove authenticity and data integrity", "Include and validate a Timestamp in the signature to prevent Replay Attacks"], ["Just check if the IP address belongs to Stripe"]),
    ("B62_7_4", "tradeoff", "medium", "tradeoff", ["API Security"], "What is the architectural tradeoff of storing user Authorization Roles (e.g., 'Admin', 'Editor') directly inside a JWT versus looking them up in the database on every request?", "Storing roles in the JWT creates a 'Stateless' architecture. The backend can instantly verify permissions purely using CPU cryptography without ever hitting the database, providing phenomenal scalability and zero-latency authorization. The severe tradeoff is 'Stale Permissions'. If you fire an employee and remove their 'Admin' role in the database, their existing JWT remains cryptographically valid as an 'Admin' until it hits its expiration time (TTL). To mitigate this, you must either use extremely short TTLs (e.g., 5 minutes) or maintain a centralized Redis Denylist, which ironically ruins the statelessness of the JWT.", ["JWT (Stateless): Phenomenal scalability because authorization requires zero DB queries", "Tradeoff: Permissions are 'baked in' and cannot be revoked instantly without a Redis Denylist", "If an Admin is demoted, they retain Admin access until the token's TTL expires"], ["JWT means the database doesn't need to exist anymore"]),
    ("B62_7_5", "scenario", "hard", "scenario", ["API Security"], "You operate a B2B SaaS platform. Tenant A's Admin generates an API Key. Tenant A's Admin makes a request to `GET /api/v1/invoices?tenant_id=B`. The API returns all of Tenant B's financial data. How did this happen, and what is the exact architectural pattern to prevent Insecure Direct Object Reference (IDOR) in multi-tenant APIs?", "This is a catastrophic IDOR (or Cross-Tenant Data Leak). The backend code merely checked `if user.isValid()`, but failed to verify if the user's `tenant_id` matched the requested resource's `tenant_id`. In a multi-tenant backend, you must NEVER trust the `tenant_id` provided in the URL or JSON body. The architectural fix is 'Context-Aware Data Access'. 1) Extract the `tenant_id` securely from the authenticated JWT/API Key session context. 2) Inject this trusted `tenant_id` directly into the SQL query context at the ORM/Data Access layer (e.g., `SELECT * FROM invoices WHERE tenant_id = ? AND id = ?`). This mathematically forces every single database query to be scoped to the authenticated tenant, making cross-tenant IDOR physically impossible.", ["IDOR (Cross-Tenant Leak): The API blindly trusted user-provided IDs without validating ownership", "Never trust IDs passed in the URL/Body for authorization boundaries", "Fix: Extract the `tenant_id` from the secure Session/JWT and enforce it globally at the Data Access (SQL) layer"], ["You just encrypt the database so Tenant A can't read it"]),
    ("B62_7_6", "explain", "medium", "explain", ["API Security"], "Explain the 'OAuth2 Client Credentials Flow' and when a backend developer should use it.", "The standard OAuth2 Authorization Code flow is for *Human* users (it involves a browser redirect to a login screen). The 'Client Credentials Flow' is strictly for Machine-to-Machine (M2M) communication where there is no human involved (e.g., a Cron Job backend service needing to call a Billing backend service). Service A is given a Client ID and Client Secret. It makes a direct POST request to the OAuth Authorization Server, authenticates itself, and receives a short-lived Access Token (JWT). It then uses that token to call Service B. It provides secure, rotating, standard-based authentication for background tasks.", ["Used strictly for Machine-to-Machine (M2M) communication with no human user/browser involved", "The client service uses a Client ID and Secret to directly request an Access Token from the Auth Server", "Ideal for backend cron jobs, background workers, or inter-service microservice calls"], ["It is a flow where the user types their credentials into the client"]),

    # Group 8: Observability & Debugging
    ("B62_8_1", "concept", "medium", "concept", ["Observability"], "What is 'Distributed Tracing Context Propagation' (e.g., W3C Trace Context) and why is it mandatory for debugging microservices?", "If a user request hits the API Gateway, passes to Service A, then Service B, and finally the Database, reading individual log files is useless because you cannot correlate which log lines belong to the same user request. Context Propagation solves this. The Gateway generates a unique `Trace ID` (e.g., `traceparent` header). Service A MUST read this HTTP header and explicitly inject it into its own outgoing HTTP request to Service B. Every service includes this exact Trace ID in its JSON logs. When the logs are aggregated in Datadog/ELK, a developer can search that single Trace ID and instantly see the entire sequential lifecycle of the request across the distributed system.", ["Microservices generate isolated, disconnected logs that are impossible to correlate without a shared ID", "W3C Trace Context defines standard HTTP headers (`traceparent`) to pass a unique Trace ID between services", "Guarantees that every log line and performance span across the architecture can be tied to a single user request"], ["Context propagation is when you tell your coworkers what you are working on"]),
    ("B62_8_2", "diagnose", "hard", "debugging", ["Observability"], "You implement OpenTelemetry Distributed Tracing across 50 microservices. The visualization perfectly shows the network time between Service A and Service B. However, within Service B itself, a specific request takes 4 seconds, but the trace just shows one massive 4-second block named `HTTP GET /process`. You cannot see what the code is actually doing. Why?", "Network-level tracing (often auto-instrumented by Service Meshes or API Gateways) only captures the entry and exit points (Ingress/Egress) of a microservice. It is entirely blind to internal application execution. To fix this, developers must implement 'Manual Code-Level Spans' within Service B. You must wrap the heavy internal functions (e.g., `processImage()`, `calculateTax()`, `queryDatabase()`) with OpenTelemetry SDK calls to create Child Spans. These child spans will break down the 4-second block into granular waterfall steps, revealing exactly which internal function caused the latency.", ["Auto-instrumentation at the network layer only traces Entry/Exit (Ingress/Egress) points", "The tracing system has zero visibility into internal thread execution or function calls", "Fix: Developers must manually instrument the application code using the SDK to create granular Child Spans for heavy functions"], ["The tracer ran out of ink inside Service B"]),
    ("B62_8_3", "implement", "medium", "implement", ["Observability"], "How do you implement 'Structured Logging' in a backend application, and why is standard string logging (`console.log('User ' + id + ' logged in')`) an anti-pattern?", "Standard string logging is unstructured text. If an engineer wants to search ELK/Splunk for all logins by User 123, they have to write fragile Regex parsers (`grep \"User 123\"`) which break the moment a developer changes the string format. Structured Logging requires the application to emit logs strictly as JSON objects: `{\"event\": \"login\", \"user_id\": 123, \"timestamp\": \"2023-10-01\"}`. Log aggregators natively index JSON keys. This allows engineers to perform instant, mathematically precise queries (e.g., `user_id = 123 AND event = login`) without Regex, enabling automated alerting and dashboards.", ["String logs require fragile Regex parsing in logging tools, breaking easily", "Structured logging emits logs strictly as JSON objects (Key-Value pairs)", "Allows log aggregators (ELK/Splunk) to index fields natively for instant, reliable, Regex-free querying"], ["Structured logging means writing the logs in a nice font"]),
    ("B62_8_4", "tradeoff", "medium", "tradeoff", ["Observability"], "What is the tradeoff of using 'Head-Based Sampling' versus 'Tail-Based Sampling' in Distributed Tracing?", "In massive architectures, tracing 100% of requests costs millions of dollars in Datadog bills. 'Head-Based Sampling' makes the keep/drop decision at the very beginning (the API Gateway decides to trace 1% of traffic randomly). It is extremely cheap and requires zero buffering, but you will almost certainly miss capturing the rare 500 Errors or extreme latency spikes, because they likely fell into the 99% dropped bucket. 'Tail-Based Sampling' records 100% of requests into a temporary memory buffer. It waits until the request *finishes*, and if it detects an Error or High Latency, it keeps the trace; otherwise, it drops it. It guarantees you capture every single anomaly, but requires massive, expensive memory infrastructure to buffer all in-flight traces.", ["Head-Based: Decides to trace randomly at the start. Cheap, but misses rare errors/anomalies", "Tail-Based: Buffers all traces and only keeps them if they fail or are slow at the end", "Tradeoff: Tail-based guarantees capturing anomalies but requires massive, expensive memory infrastructure to buffer in-flight data"], ["Head based sampling samples the headers, tail based samples the footers"]),
    ("B62_8_5", "scenario", "hard", "scenario", ["Observability"], "A critical payment background job runs every hour. It usually takes 2 minutes. Today, you get an alert that the CPU is pegged at 100% for 45 minutes, but there are ZERO errors in the logs. You SSH into the server, and the process is still running. How do you diagnose exactly which line of code is stuck without killing the process?", "You cannot rely on logs if the application is deadlocked or in an infinite loop without print statements. You must use a Continuous Profiler or take a 'Thread Dump' / 'CPU Profile' of the live process. In Java, you run `jstack <pid>`. In Go, you use `pprof`. In Python, you use `py-spy`. This instantly outputs the exact Call Stack (line of code) that every single thread is currently executing. You will likely see the threads stuck on an infinite `while(true)` loop, a Regex catastrophic backtracking evaluation, or a deadlocked database socket waiting for a response without a timeout.", ["Logs are useless for silent deadlocks or infinite loops that don't throw exceptions", "You must take a live Thread Dump or use a CPU Profiler (`jstack`, `pprof`, `py-spy`)", "This reveals the exact line of code and call stack the thread is currently frozen on without killing the process"], ["You just read the source code really carefully"]),

    # Group 9: Performance Engineering
    ("B62_9_1", "concept", "medium", "concept", ["Performance Tuning"], "What is the 'N+1 Query Problem' in ORMs (Object-Relational Mappers), and how does it devastate backend latency?", "The N+1 problem occurs when you fetch a list of entities, and then lazily iterate over them to fetch their relations. If you query `SELECT * FROM users` (1 query, returns 100 users), and then your code loops `for user in users: getPosts(user.id)`, the ORM executes 100 individual `SELECT * FROM posts WHERE user_id = X` queries. The backend is now making 101 separate network round-trips to the database instead of 1. If network latency is 2ms, you just added 200ms of pure idle network waiting. To fix it, you must use 'Eager Loading' (e.g., `JOIN` or `WHERE IN (1, 2, 3...)`) to fetch all related data in exactly 2 queries.", ["Occurs when an ORM executes 1 query to get a list, and N individual queries to get related data inside a loop", "Causes massive latency due to hundreds of unnecessary sequential network round-trips to the DB", "Fix: Use Eager Loading (`JOIN` or `WHERE IN`) to fetch all data in 1 or 2 batch queries"], ["N+1 means the database is one version newer than the backend"]),
    ("B62_9_2", "diagnose", "hard", "debugging", ["Performance Tuning"], "Your Node.js backend handles 10,000 concurrent WebSocket connections perfectly. A developer adds a new feature that uses a complex regular expression to parse incoming messages. Suddenly, the entire Node.js server freezes. No WebSocket messages are processed, HTTP endpoints time out, and CPU hits 100%. Why did a Regex take down an asynchronous server?", "This is 'Event Loop Blocking' caused by 'Catastrophic Backtracking' in the Regex. Node.js is single-threaded (uses an Event Loop). It handles 10,000 connections by quickly switching between them during I/O waits. However, CPU-bound operations (like a complex, poorly written Regex evaluating a malicious 5MB string) cannot be paused. The Regex monopolizes the single CPU thread for 15 seconds. Because the single thread is blocked, the Event Loop physically cannot process incoming HTTP requests, WebSocket pings, or database callbacks. To fix this, use safe Regex, or offload heavy CPU tasks to 'Worker Threads' so the main Event Loop remains unblocked.", ["Node.js is single-threaded; it relies on the Event Loop returning quickly after async I/O", "Heavy synchronous CPU tasks (like complex Regex) completely block the single thread", "When the thread is blocked, the Event Loop halts, and zero concurrent connections can be processed (total server freeze)"], ["The regex was too long and didn't fit in the RAM"]),
    ("B62_9_3", "implement", "medium", "implement", ["Performance Tuning"], "How do you implement 'Batching' (Micro-batching) to optimize a backend that receives 5,000 individual IoT sensor telemetry events per second and writes them to a database?", "If you execute 5,000 individual `INSERT` statements per second, the database will crash due to network overhead, transaction commit overhead, and IOPS saturation. You must implement Micro-batching in the application layer. 1) The backend receives an event and pushes it into an in-memory queue/array. 2) You configure a background timer (e.g., every 500ms) or a size threshold (e.g., array length == 1000). 3) When the threshold triggers, the backend flushes the array to the Database using a single Bulk Insert (`INSERT INTO table VALUES (1), (2), (3)...`). This reduces 5,000 transactions/sec to just 5 bulk transactions/sec, massively increasing throughput.", ["Executing thousands of individual `INSERT` transactions overwhelms DB IOPS and connection overhead", "Buffer incoming requests into an in-memory array", "Flush the buffer every N milliseconds or N items using a single Bulk Insert statement"], ["You just ask the IoT sensors to send data slower"]),
    ("B62_9_4", "tradeoff", "hard", "tradeoff", ["Performance Tuning"], "What is the architectural tradeoff of optimizing for 'Average Latency' versus optimizing for 'Tail Latency' (p99) in a distributed backend?", "Optimizing for Average Latency often involves caching common requests or relying on Garbage Collected languages (Java/C#). The average request takes 10ms, looking great on a dashboard. The tradeoff is ignoring the 'Tail' (the worst 1% of requests). If the p99 latency is 4,000ms due to massive GC pauses or cold-start database queries, the system is fundamentally broken for heavy users. In a microservice chain (A -> B -> C -> D), if each service has a 1% chance of hitting a 4,000ms tail latency, the overall user request has a massive probability of being slow. Optimizing for Tail Latency requires expensive, deterministic engineering (e.g., rewriting in Rust/C++, pre-allocating memory pools, manual memory management) which increases development time immensely just to fix the 1% edge cases.", ["Average Latency ignores the worst 1% of requests, which often suffer massive spikes due to GC pauses or cache misses", "In deep microservice chains, tail latencies compound, guaranteeing a bad experience for a large percentage of users", "Tradeoff: Fixing Tail Latency requires extreme, expensive engineering (Rust, memory pooling) compared to just throwing caches at Average Latency"], ["Tail latency is how fast the mouse moves on the screen"]),
    ("B62_9_5", "scenario", "medium", "scenario", ["Performance Tuning"], "Your API endpoint downloads a 500MB generated report from S3 and returns it to the user. As traffic increases, the backend servers constantly crash with `OutOfMemory` (OOM) errors. You notice the memory spikes exactly when users download the reports. How do you re-architect the code to prevent memory exhaustion?", "The developer is likely loading the entire 500MB file into a variable in RAM (Memory buffering) before sending it to the client. If 10 users download it simultaneously, the server needs 5GB of RAM and crashes. You must re-architect the code to use 'Streaming'. The backend should open a Read Stream from S3 and pipe it directly to the HTTP Response Write Stream. This keeps the memory footprint at a constant, tiny buffer (e.g., 64KB) regardless of the file size, as data flows directly through the server without accumulating in RAM. (Even better: use S3 Pre-Signed URLs to bypass the backend entirely).", ["Loading massive files entirely into RAM variables causes instant OutOfMemory crashes under concurrency", "Architectural Fix: Use I/O Streams to pipe the data directly from the source to the HTTP response", "Streaming maintains a tiny, constant memory footprint (e.g., 64KB) regardless of the file size"], ["You just buy a 1TB RAM server"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 3).")
    
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
