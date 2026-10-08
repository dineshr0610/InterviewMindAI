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
    # Group 4: API Reliability & Failure domains
    ("B62_4_1", "concept", "medium", "concept", ["API Reliability"], "What is a 'Retry Storm' (Retry amplification) and how do you prevent it in a microservice architecture?", "A Retry Storm occurs when a core downstream service (like a database) slows down. Service C times out and retries. Service B times out waiting for C, and retries. Service A times out waiting for B, and retries. A single slow DB query multiplies into 1,000 cascading retries, completely DDoS-ing your own infrastructure and guaranteeing the database crashes. To prevent this, you must implement 'Exponential Backoff with Jitter' (randomized delay between retries to prevent synchronized thundering herds) and 'Circuit Breakers' (if 50% of requests fail, trip the circuit and instantly fail new requests locally without actually making the network call).", ["A cascading failure where upstream services blindly retry timeouts, multiplying traffic and DDoS-ing the degraded downstream service", "Implement Exponential Backoff with Jitter (randomization) to spread out retry load", "Implement Circuit Breakers to fail-fast locally and shed load from the struggling dependency"], ["A retry storm is when it rains really hard on the servers"]),
    ("B62_4_2", "diagnose", "hard", "debugging", ["API Reliability"], "Your checkout API calls an external fraud-detection service synchronously. The fraud service starts experiencing a 10-second latency degradation. Within minutes, your checkout API completely crashes, throwing HTTP 503s for all requests, even those that don't use the fraud service. Why did a localized 3rd-party latency spike crash your entire API?", "This is Thread Pool / Connection Pool Exhaustion caused by a lack of strict 'Timeouts' and 'Bulkheads'. The checkout API handles requests using a finite thread pool (e.g., 200 Tomcat threads). Because the fraud service takes 10 seconds, the threads sit blocked, doing nothing. Within seconds, all 200 threads are blocked waiting for fraud. When a completely unrelated API request arrives (e.g., fetching a user profile), there are zero threads available to serve it, taking down the entire application. You must implement strict network timeouts (e.g., 500ms) and 'Bulkheads' (isolate thread pools so the fraud service only gets a maximum of 50 threads, leaving 150 for the rest of the API).", ["Missing strict timeouts caused threads to hang infinitely on external network I/O", "The single slow dependency exhausted the entire application's global thread/connection pool", "Fix: Enforce strict timeouts and 'Bulkheads' (thread pool isolation) so one failing dependency cannot consume all server resources"], ["The fraud service reported your API to the police"]),
    ("B62_4_3", "implement", "medium", "implement", ["API Reliability"], "How do you implement 'Idempotency' for a `POST /charge-credit-card` endpoint to prevent users from being double-charged if their mobile app loses network connection and retries the request?", "A standard POST is not idempotent; calling it twice creates two charges. You must require the client to generate a unique `Idempotency-Key` (a UUID) and include it in the HTTP headers. When the backend receives the request, it checks a fast, centralized store (like Redis or the primary Database). If the key does not exist, it saves the key with a 'PENDING' status, calls the payment gateway, and then updates the key to 'SUCCESS' with the JSON response payload. If the client retries the exact same key, the backend sees 'SUCCESS', completely skips the payment gateway, and instantly returns the cached JSON response.", ["Require the client to send a unique `Idempotency-Key` (UUID) in the HTTP Header", "Store the key centrally (Redis/DB) and lock it during the first processing attempt", "On subsequent retries with the same key, bypass the business logic and return the cached success response"], ["You just write 'DO NOT DOUBLE CHARGE' in the code comments"]),
    ("B62_4_4", "tradeoff", "hard", "tradeoff", ["API Reliability"], "What is the architectural tradeoff of using 'Load Shedding' versus unbounded request queuing during an massive, unexpected traffic spike?", "Unbounded queuing accepts all requests and puts them in a massive backlog. The tradeoff is that latency skyrockets; a user's API call might take 45 seconds to process. In modern systems, the user's browser or upstream microservice has already timed out at 5 seconds and closed the connection. The backend wastes massive CPU processing a request that the client no longer cares about, leading to total collapse. 'Load Shedding' actively rejects excess traffic with HTTP 429 or 503 the moment the system exceeds its safe capacity. This guarantees the system remains fast and stable for the users it *does* admit, but the severe tradeoff is that rejected users experience a hard failure.", ["Unbounded Queuing: Accepts all traffic, but latency skyrockets, leading to wasted CPU processing requests that clients have already timed out on", "Load Shedding: Actively rejects excess traffic (HTTP 503/429) to protect system stability and guarantee fast responses for admitted users", "Tradeoff: Protecting core system stability and preventing cascading failure versus actively dropping user requests"], ["Load shedding means the server is losing its fur"]),
    ("B62_4_5", "scenario", "medium", "scenario", ["API Reliability"], "You have a microservice that generates PDF reports. It takes 15 seconds to generate a report. The frontend makes a synchronous HTTP call to this API. Users complain of constant timeouts and broken connections. How do you re-architect this interaction?", "Synchronous HTTP is the wrong protocol for long-running, CPU-heavy tasks. Browsers, load balancers, and API gateways (like AWS API Gateway) have strict idle timeouts (often 30 seconds or less) and will aggressively sever the connection. You must re-architect this using the 'Asynchronous Request-Reply' pattern. 1) The frontend calls `POST /reports`. 2) The backend instantly drops a message in an SQS/RabbitMQ queue and returns a `HTTP 202 Accepted` with a `Location: /reports/status/123` header. 3) A background worker processes the queue and saves the PDF to S3. 4) The frontend polls the status endpoint (or uses WebSockets) until it returns `HTTP 303 See Other` with the S3 download link.", ["Synchronous HTTP connections are severed by Load Balancer/Browser idle timeouts for long-running tasks", "Architectural Fix: Use Asynchronous Request-Reply (HTTP 202 Accepted + Polling/WebSockets)", "Offload the heavy processing to a background worker queue (SQS/RabbitMQ) to free up the API threads"], ["Just increase the timeout to 5 hours"]),
    ("B62_4_6", "explain", "medium", "explain", ["API Reliability"], "Explain how 'Deadline Propagation' (Distributed Timeouts) works across a microservice chain (A -> B -> C).", "If a user request to Service A has a total timeout budget of 2 seconds, Service A must not just use its own static timeouts. If A takes 1.5 seconds to do some work, and then calls Service B, it must pass the *remaining* budget (500ms) to Service B via a gRPC deadline or HTTP Header (e.g., `grpc-timeout: 500m`). If Service B takes 400ms and calls Service C, it passes a deadline of 100ms. If Service C knows its DB query alone takes 200ms, it checks the deadline, realizes it's mathematically impossible to finish in time, and instantly aborts the query to save CPU, returning a timeout error immediately. This prevents downstream services from wasting resources on doomed requests.", ["Passes the remaining, absolute time budget downstream via HTTP headers or gRPC context", "Prevents downstream services from wasting CPU/DB resources on requests that the upstream client has already abandoned", "Services check the remaining deadline before starting heavy work and abort early if impossible"], ["Deadline propagation means missing your deadline and blaming your coworkers"]),

    # Group 5: High-scale Caching
    ("B62_5_1", "concept", "medium", "concept", ["Caching"], "What is a 'Cache Stampede' (Thundering Herd), and how do you prevent it using the 'Stale-While-Revalidate' pattern?", "A Cache Stampede occurs when a highly requested, computationally expensive item (e.g., the homepage feed) expires from Redis. In the exact millisecond it expires, 10,000 concurrent user requests hit the API. They all check Redis, get a Cache Miss, and all 10,000 threads simultaneously hit the Database to compute the feed, instantly crashing the Database. 'Stale-While-Revalidate' prevents this. When a key is near expiration, the cache serves the slightly stale data to 9,999 users, but elects exactly *one* background thread to asynchronously fetch the fresh data from the DB and update the cache. The users experience zero latency, and the DB only receives 1 query.", ["Cache Stampede: Simultaneous cache misses cause thousands of concurrent requests to instantly crush the primary database", "Stale-While-Revalidate: Serves slightly stale data to users while asynchronously fetching fresh data in the background", "Ensures only a single background thread hits the database, completely protecting it from the thundering herd"], ["A cache stampede is when the servers run out of the datacenter"]),
    ("B62_5_2", "diagnose", "hard", "debugging", ["Caching"], "Your backend API is under a massive DDoS attack requesting randomized, non-existent user IDs (e.g., `/users/999999991`, `/users/999999992`). You have a Redis cache in front of your Database. However, the Database CPU hits 100% and crashes. Why didn't Redis protect the Database, and how do you fix it?", "This is a 'Cache Penetration' attack. The attacker is intentionally requesting IDs that do not exist. The backend checks Redis (Cache Miss), queries the Database (Returns Null), and returns a 404 to the user. Because the data is Null, the backend developer foolishly did not cache the result. Therefore, every single malicious request perfectly bypasses Redis and strikes the Database directly. To fix this, you must implement 'Negative Caching' (cache the Null/404 response in Redis for a short TTL, e.g., 60 seconds). A more advanced fix is to put a Bloom Filter in memory before Redis to instantly mathematically reject IDs that do not exist.", ["Cache Penetration: Attackers request non-existent keys, causing a Cache Miss that strikes the Database directly every time", "The backend failed to cache the empty/Null results", "Fix: Implement 'Negative Caching' (cache the 404s) or use an in-memory Bloom Filter to instantly reject invalid IDs"], ["Redis got scared of the hackers and stopped working"]),
    ("B62_5_3", "implement", "medium", "implement", ["Caching"], "How do you implement 'Distributed Cache Invalidation' when a user updates their profile, ensuring that all 50 stateless API servers serve the fresh data immediately?", "Cache invalidation is notoriously difficult. If the data is cached in a centralized Redis, you simply `DEL` or overwrite the key in Redis when the DB is updated. However, if the 50 API servers use an *In-Memory Local Cache* (like Guava/Caffeine) to avoid network hops, updating the DB on Server A leaves Servers B-Z serving stale local data. You must implement a Pub/Sub mechanism (e.g., Redis Pub/Sub or Kafka). When Server A updates the DB, it broadcasts a `ProfileUpdatedEvent`. All 50 servers subscribe to this channel, receive the event in milliseconds, and explicitly evict that specific user's ID from their local memory cache.", ["Centralized Cache (Redis): Simple, just overwrite or delete the key", "Local In-Memory Cache: Highly complex, requires a Pub/Sub broadcast mechanism", "When Server A mutates data, it broadcasts an eviction event; all other servers listen and purge their local stale copies"], ["You just wait for the cache to realize it's wrong"]),
    ("B62_5_4", "tradeoff", "hard", "tradeoff", ["Caching"], "What is the tradeoff of using 'Write-Through' caching versus 'Write-Behind' (Write-Back) caching in a high-throughput backend?", "In a Write-Through cache, the application synchronously writes data to the Cache, and then synchronously writes to the Database, only returning HTTP 200 when both succeed. This guarantees perfect data consistency, but the tradeoff is write latency (you pay the network penalty of two remote calls). In a Write-Behind cache, the application writes ONLY to the Cache (e.g., Redis) and instantly returns HTTP 200. A background process asynchronously flushes the data from the cache to the Database later. This provides phenomenal, sub-millisecond write speed and can batch writes to save DB IOPS. The severe tradeoff is Data Loss: if the Redis node crashes before the background flush occurs, the acknowledged data is permanently lost.", ["Write-Through: Synchronous writes to both Cache and DB. Guarantees consistency but increases write latency", "Write-Behind: Synchronous write to Cache only, asynchronous flush to DB. Phenomenal speed and batching", "Tradeoff: Write-Behind risks catastrophic data loss if the cache node crashes before flushing to persistent storage"], ["Write-behind means writing the code behind your back"]),
    ("B62_5_5", "scenario", "medium", "scenario", ["Caching"], "During a massive flash sale, a specific product ID goes viral. You are using Memcached. The Memcached cluster has 20 nodes. The database is fine, but exactly ONE Memcached node hits 100% CPU and crashes, taking down the product page. Why did only one node crash, and how do you architect around it?", "This is a 'Hot Key' problem. Memcached distributes keys across nodes using consistent hashing based on the key name. Because millions of users are requesting the exact same Product ID, the hashing algorithm routes 100% of that traffic to a single specific Memcached node, completely overwhelming its CPU and NIC. Adding more Memcached nodes does nothing, because the hash will still route that specific key to one node. To fix this, you must implement 'Local In-Memory Caching' (L1 Cache) on the API servers themselves for 5-10 seconds, or 'Salt' the cache key (e.g., `product:123:node1`, `product:123:node2`) to force the load balancer to distribute the single key across multiple cache nodes.", ["Hot Key: Consistent hashing routes millions of requests for a single viral ID to exactly one Cache node", "Adding more cache nodes does not solve the problem (the hash remains the same)", "Fix: Implement a short-lived Local L1 Cache on the API servers to absorb the traffic before it hits Memcached, or Salt the keys to distribute them"], ["The cache node got jealous of the other nodes"]),
    ("B62_5_6", "explain", "medium", "explain", ["Caching"], "Explain the difference between a 'Cache Avalanche' and a 'Cache Stampede'.", "A Cache Stampede is localized to a SINGLE highly-concurrent key expiring, causing a thundering herd on the database for that one specific query. A Cache Avalanche is systemic. It occurs when a massive percentage of your ENTIRE cache expires at the exact same second (usually because a developer flushed the cache, a Redis node crashed, or all keys were written with the exact same 60-minute TTL during a batch job). Thousands of different queries simultaneously miss the cache and hit the database, instantly bringing down the entire infrastructure. To prevent an avalanche, you must 'Jitter' your TTLs (e.g., instead of 60 minutes, set TTLs to a random value between 55 and 65 minutes) so expirations are smoothed out over time.", ["Stampede: A single viral key expires, causing a localized thundering herd for one query", "Avalanche: A massive percentage of all keys expire simultaneously (due to restart or identical TTLs), causing total systemic DB collapse", "Prevention: Add randomized 'Jitter' to your Cache TTLs to smooth out expirations over time"], ["An avalanche is made of snow, a stampede is made of cows"]),

    # Group 6: Microservice Communication & Architecture
    ("B62_6_1", "concept", "medium", "concept", ["Microservices"], "What is the 'BFF' (Backend-For-Frontend) pattern, and what problem does it solve in microservice architectures?", "In a raw microservice architecture, a mobile app might have to make 10 different HTTP calls to 10 different microservices (Users, Orders, Inventory, Reviews) just to render a single profile page. This causes massive latency over mobile networks (paying the TCP/TLS handshake penalty 10 times) and forces the mobile app to handle complex data aggregation. A BFF is a dedicated, lightweight backend API tailored specifically for a client (e.g., a Mobile BFF, a Web BFF). The mobile app makes 1 single call to the BFF. The BFF, sitting inside the high-speed datacenter, makes the 10 microservice calls concurrently, aggregates the JSON, strips out unnecessary data, and returns exactly what the UI needs in a single payload.", ["Mobile clients making dozens of HTTP calls to separate microservices suffer massive latency and over-fetching", "BFF (Backend-For-Frontend): A dedicated aggregation layer specifically tailored to one client type (Mobile, Web)", "The BFF orchestrates concurrent microservice calls inside the datacenter and returns a single, optimized JSON payload to the client"], ["BFF stands for Best Friends Forever, meaning the servers are friends"]),
    ("B62_6_2", "diagnose", "hard", "debugging", ["Microservices"], "Your microservice uses a standard Round-Robin load balancer to communicate with 5 instances of a downstream service. Instance 3 starts experiencing a severe CPU degradation, taking 10 seconds to respond, while the others take 50ms. Overall system latency skyrockets, and error rates spike. Why is the load balancer making the problem worse, and how do you fix it?", "Round-Robin is entirely blind to the health and latency of the downstream targets. It stubbornly sends 20% of your traffic to Instance 3, causing those requests to hang and timeout, exhausting your upstream connection pools. To fix this, you must switch from Server-Side Round-Robin to Client-Side Load Balancing (or a Service Mesh) using advanced algorithms like 'Least Connections' or 'Peak Exponentially Weighted Moving Average (EWMA)'. EWMA mathematically tracks the latency of each node in real-time. It detects that Instance 3 is slow and automatically stops routing traffic to it, routing entirely to the healthy nodes until Instance 3 recovers.", ["Round-Robin is 'blind' and will stubbornly route traffic to a degraded, slow node, causing cascading connection exhaustion", "Server-side load balancers often lack the context to detect subtle latency degradation (only checking binary Health Checks)", "Fix: Use latency-aware algorithms like 'Least Connections' or 'EWMA' (via Service Mesh/Client-side routing) to dynamically avoid slow nodes"], ["The load balancer is dizzy from spinning in a circle"]),
    ("B62_6_3", "implement", "medium", "implement", ["Microservices"], "How do you implement secure 'Service-to-Service Authorization' to ensure that the Billing Microservice can only be called by the Checkout Microservice, and not by the User Profile Microservice?", "You cannot rely on Network Firewalls (IP blocking) inside a dynamic Kubernetes cluster because Pod IPs constantly change. You must implement identity-based security using Mutual TLS (mTLS) via a Service Mesh (like Istio/Linkerd), OR use JWT-based service tokens. With mTLS, every microservice is issued a cryptographic X.509 certificate representing its identity (e.g., `spiffe://checkout`). When Checkout calls Billing, the TLS handshake mathematically proves its identity. You then write a strict Authorization Policy in the Service Mesh: `Allow traffic to Billing ONLY IF source.principal == checkout`. Any other service is rejected at the proxy layer with a 403 Forbidden.", ["IP-based firewalls fail in dynamic orchestrators like Kubernetes due to ephemeral IPs", "Implement Mutual TLS (mTLS) via a Service Mesh (Istio/Linkerd) to cryptographically prove service identity", "Enforce strict Layer 7 Authorization Policies (`Allow Billing ONLY IF source == Checkout`)"], ["You make the servers use a secret handshake"]),
    ("B62_6_4", "tradeoff", "hard", "tradeoff", ["Microservices"], "What is the architectural tradeoff of migrating inter-service communication from REST/JSON over HTTP/1.1 to gRPC/Protobuf over HTTP/2?", "gRPC provides phenomenal performance. It uses Protobuf (a binary serialization format), cutting payload sizes by 50% compared to JSON. It uses HTTP/2, allowing multiplexing (sending 100 concurrent requests over a single TCP connection), eliminating the latency of opening new connections. It also generates strongly typed client/server code, eliminating runtime parsing errors. The severe tradeoff is Observability and Debugging. You can no longer just `curl` the endpoint or read the payload in Wireshark because it's a compiled binary stream. It breaks standard AWS ALBs (which historically struggled with HTTP/2 routing) and forces you to use specialized gRPC tooling (like `grpcurl`) and Service Meshes for load balancing.", ["gRPC/Protobuf: Binary serialization and HTTP/2 multiplexing provide phenomenal performance, low latency, and strongly-typed contracts", "Tradeoff: Massive loss of human readability. You cannot easily `curl` or packet-sniff the binary payloads", "Tradeoff: Complex load balancing; traditional HTTP/1.1 proxies/ALBs struggle to balance long-lived multiplexed HTTP/2 connections properly"], ["gRPC is just REST but written in Greek"]),
    ("B62_6_5", "scenario", "medium", "scenario", ["Microservices"], "Service A uses a Synchronous REST call to Service B to create a user account. Service B takes 5 seconds to process. During peak load, Service A completely crashes because it runs out of RAM. How do you re-architect this interaction to prevent memory exhaustion?", "Synchronous REST calls force Service A's threads to block and wait for 5 seconds. Each blocked thread holds memory (stack context) and holds open network sockets. During a spike, thousands of threads block, exhausting RAM and crashing Service A. You must re-architect using 'Asynchronous Event-Driven Messaging'. Service A should validate the request, instantly publish a `CreateUserCommand` to a Kafka/RabbitMQ queue, and return a `202 Accepted` to the client in 10 milliseconds. Service B pulls from the queue at its own pace. Service A's threads are freed instantly, completely eliminating the memory and connection exhaustion.", ["Synchronous blocking calls cause upstream services to exhaust memory/threads while waiting for slow downstream services", "Architectural Fix: Decouple the services using an Asynchronous Message Queue (Kafka/RabbitMQ)", "Service A publishes the event and instantly returns (Fire and Forget), freeing its threads and protecting its RAM"], ["You tell Service A to buy more RAM on Amazon"]),
    ("B62_6_6", "explain", "medium", "explain", ["Microservices"], "Explain the 'Strangler Fig' pattern for migrating a monolithic application to microservices.", "The Strangler Fig pattern is a safe, incremental migration strategy. Instead of rewriting the entire monolith in a massive 2-year 'Big Bang' project (which usually fails), you put an API Gateway / Reverse Proxy in front of the legacy monolith. All traffic routes to the monolith initially. You then extract ONE specific bounded context (e.g., 'Billing') into a brand new microservice. You update the API Gateway to route ONLY `/billing` traffic to the new microservice, while all other traffic still goes to the monolith. You repeat this process, slowly 'strangling' the legacy system, until the monolith handles zero traffic and can be safely deleted.", ["A strategy for incrementally migrating a Monolith to Microservices without a risky 'Big Bang' rewrite", "Place an API Gateway in front, and route specific endpoints to new microservices one-by-one", "Slowly 'strangles' the legacy monolith as functionality is iteratively extracted, ensuring continuous delivery and safe rollbacks"], ["You strangle the developer who wrote the monolith"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 2).")
    
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
