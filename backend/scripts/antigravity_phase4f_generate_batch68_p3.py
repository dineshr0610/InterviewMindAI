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
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

# Tuple structure:
# (id_code, intent, difficulty, question_type, [primary_skill, secondary_skills...], technology, topic, question, expected_answer, strong_indicators, weak_indicators)
Q = [
    (
        "B68_3_1",
        "tradeoff",
        "hard",
        "tradeoff",
        ["API Gateway Architecture", "Network Protocols"],
        "Envoy / NGINX / API Gateway",
        "Request Buffering vs Streaming Proxying at the Edge",
        "What are the architectural tradeoffs between 'Request Buffering' and 'Streaming Proxying' when an API gateway proxies client HTTP requests with large payloads to downstream microservices, particularly regarding memory safety, latency, and automatic retries?",
        "Request Buffering: 1) Mechanism: The gateway reads the entire client HTTP request body into local RAM or temporary disk before establishing an upstream connection or forwarding the first byte. 2) Advantages: The gateway can inspect the entire payload for security threats (WAF, virus scanning, schema validation), compute accurate Content-Length headers, and safely execute transparent HTTP retries if the downstream service returns a 503 or drops the connection during the request. 3) Disadvantages: High memory consumption. If 1,000 concurrent clients upload 50MB files, the gateway requires 50GB of RAM, risking Out-Of-Memory (OOM) crashes. Increases Time-To-First-Byte (TTFB) because upstream processing cannot begin until the entire upload finishes. Streaming Proxying: 1) Mechanism: The gateway opens an upstream connection immediately and pipes chunks of the request body directly from the client socket to the upstream socket as they arrive over the wire. 2) Advantages: Minimal memory footprint (O(1) buffer size per stream) and lowest latency, enabling multi-gigabyte file uploads and real-time streaming. 3) Disadvantages: Once the first chunk is streamed upstream, the gateway CANNOT automatically retry the request if downstream fails mid-stream because the request body stream has already been consumed and cannot be replayed without buffering.",
        [
            "Explains that buffering enables full payload inspection and automatic retries but consumes high RAM and increases TTFB",
            "Explains that streaming proxying operates with constant low memory and minimal latency",
            "Identifies the inability to execute transparent retries mid-stream as the primary drawback of streaming proxying"
        ],
        [
            "Claims streaming proxying stores the entire file in an S3 bucket before forwarding"
        ]
    ),
    (
        "B68_3_2",
        "scenario",
        "medium",
        "scenario",
        ["API Gateway Architecture", "Resilience"],
        "Microservices Architecture",
        "Timeout Layering across Gateway and Upstream Services",
        "An API architecture has three layers: Client -> API Gateway -> Order Service -> Inventory Service. The client timeout is configured to 10 seconds, the API Gateway timeout to Order Service is set to 8 seconds, and the Order Service timeout to Inventory Service is set to 12 seconds. Explain how this misconfigured timeout layering causes orphaned background work and false HTTP 504 Gateway Timeouts under downstream latency spikes.",
        "The fundamental rule of Timeout Layering is that timeouts must decrease monotonically as requests travel deeper into the service graph: Client Timeout > Gateway Timeout > Downstream Timeout. In the misconfigured setup: 1) Downstream Latency Spike: Inventory Service experiences database lock contention and takes 10 seconds to respond. 2) Premature Gateway Termination: At second 8, the API Gateway's timeout triggers. The gateway tears down its connection to Order Service and returns an HTTP 504 Gateway Timeout to the client. 3) Orphaned Ghost Work: Meanwhile, Order Service is still waiting for Inventory Service because its downstream timeout is 12 seconds. At second 10, Inventory Service finally completes the database write and returns success. Order Service then proceeds to commit order creation, charge the customer, and deduct inventory. 4) Consequence: The client receives a 504 failure and assumes the order failed (potentially retrying and purchasing twice), while the backend completed the entire transaction in the background. Furthermore, backend compute, database connections, and memory were wasted executing work whose client already disconnected. Upstream timeouts must always be strictly shorter than the caller's timeout.",
        [
            "Identifies that timeouts must decrease as requests move deeper into the dependency graph",
            "Explains that the gateway times out and returns 504 to the client while downstream services continue executing",
            "Demonstrates the consequence: orphaned ghost transactions, duplicate purchases, and wasted server resources"
        ],
        [
            "Suggests setting all timeouts across all services to infinity to prevent 504 errors"
        ]
    ),
    (
        "B68_3_3",
        "diagnose",
        "hard",
        "debugging",
        ["Resilience Engineering", "API Reliability"],
        "Microservices Architecture",
        "The Gateway Retry Amplification Multiplier Effect",
        "A system experiences a 500ms network blip causing a downstream database to reject queries. The API Gateway is configured with 3 retries. Service A (which calls Service B) is configured with 3 retries. Service B (which queries the database) is configured with 3 retries. Why does this nested retry architecture cause an exponential traffic explosion (Retry Amplification) that permanently knocks down the database, and how do you stop it?",
        "Retry Amplification occurs when multiple layers in a microservice call tree independently retry failed requests. The total number of requests sent to the leaf dependency multiplies exponentially with call depth: $R_{total} = R_{gateway} \times R_{serviceA} \times R_{serviceB}$. In this setup: 1 original client request is retried 3 times by Service B. If Service A fails, it retries 3 times, causing Service B to retry 3 times each ($3 \times 3 = 9$ queries). If the Gateway also retries 3 times, the leaf database is bombarded with $3 \times 3 \times 3 = 27$ queries for a single user click. Under high incoming concurrency (e.g., 2,000 req/s), a transient 500ms blip generates a $27\times$ tsunami of 54,000 queries/s, completely crushing database connection pools and causing a permanent cascading outage long after the original blip resolved. Prevention: 1) Retry Budgeting: Allow retries only if recent retries comprise less than a strict percentage (e.g., 10%) of total traffic. 2) Single-Layer Retries: Enforce that retries only occur at ONE specific architectural boundary (typically at the immediate caller of the failing leaf dependency, or exclusively at the edge gateway). 3) Non-Retriable Error Propagation: Downstream services must return explicit non-retriable error codes (e.g., 429 Too Many Requests or custom headers `X-Do-Not-Retry`) so upstream gateways abort immediately without retrying.",
        [
            "Calculates exponential multiplication of retries across nested microservice layers",
            "Explains that retry amplification transforms a minor transient blip into a catastrophic permanent outage",
            "Prescribes retry budgets, restricting retries to a single architectural layer, and propagating non-retriable headers"
        ],
        [
            "Claims retries only increase traffic linearly by 3 requests regardless of architecture depth"
        ]
    ),
    (
        "B68_3_4",
        "implement",
        "medium",
        "implement",
        ["API Gateway Architecture", "Zero Downtime Deployments"],
        "Envoy / HTTP/2",
        "Connection Draining via HTTP/2 GOAWAY Frames",
        "During a zero-downtime rolling deployment of backend API pods, terminating an old pod abruptly severs long-lived HTTP/2 multiplexed connections, causing hundreds of in-flight client requests to abort with `ECONNRESET`. How do API gateways (like Envoy) use HTTP/2 `GOAWAY` frames to execute graceful connection draining without dropping active streams?",
        "HTTP/2 multiplexes hundreds of concurrent request streams over a single persistent TCP connection. Abruptly closing the TCP socket or sending a TCP RST terminates all in-flight streams simultaneously. To drain connections gracefully without dropping active requests: 1) When a pod receives a `SIGTERM` or is marked unhealthy, the gateway/proxy initiates connection draining. 2) Initial GOAWAY Frame: The server sends an HTTP/2 `GOAWAY` frame with `Last-Stream-ID: 2^31-1` (the maximum possible stream ID). This signals the client that connection teardown has begun, instructing the client to stop sending new requests on this connection while permitting current streams to proceed. 3) Final GOAWAY Frame: Shortly after, the server sends a second `GOAWAY` frame containing the *exact* highest Stream ID that the server has actually accepted and processed (e.g., `Last-Stream-ID: 154`). 4) In-Flight Completion: The server keeps the TCP socket open and processes all streams $\le 154$ to natural completion, returning HTTP responses. If the client sent streams $> 154$ in the race window, the client knows the server never processed them and safely retries those specific streams on a new connection. 5) Graceful Socket Close: Once all in-flight streams finish (or after a drain timeout), the server cleanly closes the TCP connection with zero aborted requests.",
        [
            "Explains that closing multiplexed HTTP/2 TCP sockets abruptly drops all active concurrent streams",
            "Describes sending HTTP/2 GOAWAY frames with Last-Stream-ID to stop new streams while finishing in-flight work",
            "Identifies that clients safely retry unaccepted streams on new connections while active streams complete cleanly"
        ],
        [
            "Recommends killing the backend process with SIGKILL immediately during rolling deployment"
        ]
    ),
    (
        "B68_3_5",
        "explain",
        "medium",
        "explain",
        ["API Gateway Architecture", "Microservices Architecture"],
        "gRPC / REST Gateway",
        "Protocol Translation: Edge HTTP/JSON to Internal gRPC",
        "Many microservice architectures expose RESTful HTTP/JSON to public clients while communicating exclusively via gRPC/Protobuf between internal backend services. How does an API Gateway perform protocol translation between HTTP/JSON and gRPC, and how are HTTP status codes mapped to gRPC status codes?",
        "An API Gateway performing REST-to-gRPC transcoding acts as a protocol bridge: 1) Schema Mapping: The gateway compiles the Protobuf service definitions and utilizes gRPC HTTP annotations (e.g., `google.api.http` options in `.proto` files) to generate a routing table mapping REST HTTP methods and URL paths (e.g., `POST /v1/users/{user_id}/orders`) to specific gRPC RPC methods (`OrderService.CreateOrder`). 2) Request Transcoding: The gateway extracts path parameters, query string parameters, and deserializes the JSON request body, transcoding the data into binary Protobuf wire format. 3) Multiplexed Upstream Dispatch: The gateway dispatches the binary Protobuf message over an existing persistent HTTP/2 connection pool to the upstream gRPC service. 4) Response Transcoding: The gateway receives the binary Protobuf response, serializes it to JSON, and streams it back to the client. 5) Status Code Mapping: The gateway translates gRPC status codes to standard HTTP codes: `OK` (0) -> `200 OK`, `INVALID_ARGUMENT` (3) -> `400 Bad Request`, `NOT_FOUND` (5) -> `404 Not Found`, `ALREADY_EXISTS` (6) -> `409 Conflict`, `PERMISSION_DENIED` (7) -> `403 Forbidden`, `UNAUTHENTICATED` (16) -> `401 Unauthorized`, `UNAVAILABLE` (14) -> `503 Service Unavailable`.",
        [
            "Describes using Protobuf HTTP annotations (google.api.http) to route REST paths to gRPC RPC methods",
            "Explains transcoding between JSON text and binary Protobuf over persistent HTTP/2 connections",
            "Details explicit mapping between gRPC canonical status codes and standard HTTP status codes"
        ],
        [
            "Claims gRPC and REST cannot interact without running a separate Python script in a Docker container"
        ]
    ),
    (
        "B68_3_6",
        "concept",
        "easy",
        "concept",
        ["API Gateway Architecture", "API Security"],
        "OAuth2 / JWT",
        "Edge Token Validation and Downstream Claims Header Propagation",
        "In a microservices architecture, why is it standard practice to validate client JWT tokens at the API Gateway and forward verified user claims as internal HTTP headers (`X-User-Id`, `X-Tenant-Id`, `X-Roles`) rather than requiring every internal microservice to independently parse and verify cryptographic JWT signatures?",
        "1) Performance and Resource Optimization: Cryptographic verification of asymmetric JWT signatures (RSA/ECDSA) requires non-trivial CPU cycles. Validating the JWT once at the edge gateway eliminates duplicate cryptographic verification across 10 downstream microservices per request, saving significant backend CPU. 2) Centralized Secret and Key Management: Public keys (JWKS endpoints) or asymmetric certificates only need to be configured, fetched, and cached in memory by the API Gateway. Internal microservices do not need complex JWT libraries, keystores, or outbound network access to identity providers. 3) Architectural Decoupling: Downstream microservices consume clean, structured, domain-specific headers (`X-User-Id`, `X-Tenant-Id`) directly, simplifying application code and testability. 4) Security Boundary: The API Gateway strips any incoming client-supplied `X-User-*` headers from the public internet before injecting verified claims, ensuring internal services trust headers only within the secure internal VPC.",
        [
            "Identifies CPU savings by eliminating redundant cryptographic signature verification across internal services",
            "Centralizes JWKS key management and identity provider integration at the edge gateway",
            "Stresses stripping public client headers and forwarding verified claims (e.g. X-User-Id) within the private network"
        ],
        [
            "Claims internal microservices cannot read HTTP headers so JWTs must be stripped"
        ]
    ),
    (
        "B68_3_7",
        "explain",
        "medium",
        "explain",
        ["API Gateway Architecture", "Performance Tuning"],
        "HTTP/1.1 / Chunked Encoding",
        "Response Buffering vs Chunked Streaming: TTFB and Buffer Bloat",
        "When an upstream microservice generates a large 100MB dynamic JSON export or CSV file using Chunked Transfer Encoding, why does enabling 'Response Buffering' on the edge reverse proxy degrade Time-To-First-Byte (TTFB) and risk proxy buffer bloat, and when is disabling buffering necessary?",
        "Response Buffering Mechanics: When response buffering is enabled (default in proxies like NGINX), the proxy reads chunks from the upstream microservice and buffers them in memory (or temp disk buffers) until the entire 100MB response is assembled before sending the first byte to the client. Degradation Effects: 1) Severe TTFB Penalty: The client receives zero response bytes for 30 seconds while the proxy waits for upstream completion, causing client UI freezes and browser request timeouts. 2) Buffer Bloat and Disk I/O: Under multiple concurrent 100MB downloads, proxy RAM buffers fill up, forcing the proxy to write temporary buffer files to disk (`proxy_temp_path`), causing heavy disk I/O bottlenecks and socket exhaustion. When to Disable Buffering: Response buffering must be disabled (`X-Accel-Buffering: no` or `proxy_buffering off`) for: large file downloads, dynamic CSV exports, Server-Sent Events (SSE), and gRPC streaming. Disabling buffering allows the proxy to immediately stream each chunk over the client socket as soon as it arrives from upstream, achieving immediate TTFB and constant low memory consumption.",
        [
            "Explains that response buffering holds chunks until completion, causing massive TTFB delays",
            "Identifies proxy memory exhaustion and disk spillover (proxy_temp) under concurrent large downloads",
            "Prescribes disabling buffering for large exports, SSE, and streaming to stream chunks immediately to the client"
        ],
        [
            "Claims chunked transfer encoding is only supported on dial-up internet connections"
        ]
    ),
    (
        "B68_3_8",
        "concept",
        "easy",
        "concept",
        ["API Gateway Architecture", "Cybersecurity"],
        "Reverse Proxies / WAF",
        "Request Body Size Limits and Slowloris Defenses",
        "Why must an edge reverse proxy enforce strict `client_max_body_size` and connection timeouts (`client_header_timeout`, `client_body_timeout`), and how do these safeguards protect backend application servers from Slowloris attacks?",
        "1) Preventing Out-Of-Memory and Resource Exhaustion: Without strict body limits (e.g., `client_max_body_size 10M`), malicious or buggy clients can send unbounded multi-gigabyte HTTP payloads (e.g., sending an infinite stream of zeros). This exhausts server RAM, fills temporary disk storage, and saturates network bandwidth. 2) Defending Against Slowloris Attacks: In a Slowloris attack, an attacker opens hundreds of HTTP connections and transmits headers or body chunks at an agonizingly slow pace (e.g., 1 byte every 15 seconds). Traditional backend application servers (like Tomcat, Puma, or Gunicorn) assign a dedicated worker thread or process to each active socket. By holding hundreds of sockets open slowly, the attacker exhausts the backend server's thread pool, denying service to all legitimate users without consuming significant bandwidth. 3) Edge Protection: An edge proxy (like NGINX or Envoy) uses non-blocking event-driven epoll loops that handle tens of thousands of connections on a few threads. By enforcing aggressive read timeouts, the proxy detects slow sockets, terminates them, and ensures that only fully formed, bounded requests reach backend application thread pools.",
        [
            "Explains that unbounded request bodies exhaust server RAM and disk capacity",
            "Describes Slowloris attacks: slowly sending bytes to tie up backend worker threads and exhaust thread pools",
            "Shows that event-driven edge proxies use strict timeouts to terminate slow connections before backend resources are consumed"
        ],
        [
            "Claims Slowloris attacks are physical hardware malfunctions caused by overheating CPUs"
        ]
    ),
    (
        "B68_3_9",
        "explain",
        "medium",
        "explain",
        ["Rate Limiting", "Algorithms"],
        "Distributed Caching",
        "Sliding-Window Counter Algorithm Mechanics",
        "How does the 'Sliding-Window Counter' algorithm approximate exact request rate limits with $O(1)$ memory and CPU, and how does its weighted time interpolation formula calculate whether an incoming request exceeds the limit?",
        "Fixed-window counters suffer from burst boundary vulnerabilities (allowing double the limit across window boundaries), while sliding-log counters require storing every timestamp in memory (consuming massive RAM at high scale). The Sliding-Window Counter solves this with $O(1)$ memory by tracking only two integers: the count of the previous window and the count of the current window. Mathematical Formula: When a request arrives at timestamp $T$ within the current window: 1) Calculate the percentage of time elapsed in the current window: $weight_{current} = \\frac{time\\_into\\_current\\_window}{window\\_duration}$. 2) The percentage of the previous window that overlaps the rolling 60-second window is: $weight_{previous} = 1 - weight_{current}$. 3) The estimated rolling request count is: $estimated\\_count = (count_{previous} \\times weight_{previous}) + count_{current}$. 4) If $estimated\\_count < limit$, the request is permitted and $count_{current}$ is incremented by 1. If $\\ge limit$, the request is rejected with HTTP 429. Tradeoffs: Extremely fast, requires storing only two integer counters per rate limit key, and smoothly prevents window boundary burst spikes with negligible statistical error.",
        [
            "Explains the weighted interpolation formula combining previous window count and current window count",
            "Contrasts O(1) memory footprint against high RAM consumption of sliding-log timestamp stores",
            "Highlights that sliding-window counters prevent double-rate burst spikes at fixed window boundaries"
        ],
        [
            "Claims sliding-window counters require storing every individual user HTTP request in an SQL database"
        ]
    ),
    (
        "B68_3_10",
        "implement",
        "hard",
        "implement",
        ["Rate Limiting", "Concurrency"],
        "Redis / Lua Scripting",
        "Distributed Token Bucket Implementation via Redis Lua",
        "When implementing a distributed Token Bucket rate limiter in Redis across 20 horizontally scaled API instances, why is executing separate `GET`, `SET`, and `EXPIRE` commands from application code vulnerable to race conditions, and how does executing the token bucket logic inside an atomic Redis Lua script resolve this?",
        "Race Condition Problem: If an API server reads the current token count (`GET`), computes token replenishment based on elapsed time, decrements the token, and writes back (`SET`), a classic 'Check-Then-Act' race condition occurs. Under high concurrency, 50 API nodes reading concurrently will all read the exact same token count (e.g., 5 tokens remaining), all think tokens are available, all decrement, and all allow 50 requests through, completely obliterating the rate limit. Atomic Lua Script Resolution: Redis executes Lua scripts as a single atomic unit on its main execution thread; no other command or script can run concurrently while the Lua script executes. Lua Script Logic: 1) Pass the key, rate (tokens/sec), burst capacity, and current timestamp as parameters. 2) The script fetches two stored fields (e.g., using Redis Hash): `last_updated_time` and `tokens`. 3) It calculates tokens generated since last update: $replenished = (now - last\\_updated) \\times rate$. 4) It caps tokens at $min(capacity, tokens + replenished)$. 5) If $tokens \\ge 1$, it decrements tokens by 1, saves the updated tokens and timestamp, and returns 1 (allow). If $tokens < 1$, it returns 0 (reject/429). 6) Everything executes atomically in memory with zero race conditions across distributed servers.",
        [
            "Identifies check-then-act race conditions when executing discrete GET and SET commands across concurrent nodes",
            "Explains that Redis Lua scripts execute atomically, blocking concurrent interleaved operations",
            "Details token replenishment math ($tokens + elapsed \\times rate$) capped at burst capacity inside the script"
        ],
        [
            "Suggests acquiring a global database lock on a PostgreSQL row before each HTTP request to check tokens"
        ]
    ),
    (
        "B68_3_11",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Rate Limiting", "Performance Tuning"],
        "Redis / Distributed Caching",
        "Local Token Bucket with Periodic Remote Sync vs Centralized Redis",
        "At a scale of 500,000 requests per second, making a synchronous network call to Redis for every single incoming HTTP request to check rate limits introduces significant latency (1-2ms RTT per request) and requires massive Redis clustering. What are the architectural tradeoffs of using 'Local In-Memory Token Buckets with Periodic Remote Batch Synchronization'?",
        "Synchronous Centralized Redis: 1) Advantages: Perfect, real-time consistency. Every node sees the exact same token count at every millisecond. No tenant can ever exceed their global quota by even a single request. 2) Tradeoffs: Massive network overhead, high tail latency (adding 1-2ms to every API request), and Redis becomes a high-throughput Single Point of Failure and cost center at 500k req/s. Local Token Buckets with Periodic Batch Sync: 1) Mechanism: Each API server maintains an in-memory token bucket. A background daemon periodically contacts the central cluster (e.g., every 100ms) to acquire a 'batch lease' of tokens (e.g., requesting 500 tokens for the next interval) or report consumed counts. Local requests consume local RAM tokens in sub-microsecond time with zero network I/O. 2) Advantages: Ultra-low latency, sub-microsecond local rate checks, and extreme resilience (if Redis crashes, API servers can continue operating with cached leases). 3) Tradeoffs: Eventual consistency and quota inaccuracy. If traffic is unevenly distributed across nodes, a node with high traffic may run out of tokens and reject requests even though other nodes hold unused tokens (under-utilization); or during rapid traffic bursts, tenants may temporarily exceed global limits by the batch allocation margin (burst over-allocation).",
        [
            "Contrasts absolute real-time accuracy of centralized Redis against network latency and cluster scaling costs",
            "Explains local token batch leasing: fetching token blocks periodically to enable sub-microsecond local RAM checks",
            "Analyzes the tradeoff: sub-microsecond latency and fault tolerance vs potential temporary over-allocation and uneven quota distribution"
        ],
        [
            "Claims local memory rate limiting is physically impossible across multiple server instances"
        ]
    ),
    (
        "B68_3_12",
        "scenario",
        "hard",
        "scenario",
        ["Rate Limiting", "Multi-Tenant Architecture"],
        "API Gateway",
        "Hierarchical Multi-Tiered Rate Limiting Quotas",
        "You are designing the rate limiting layer for a public enterprise API. The business mandates four simultaneous rate limiting rules: 1) Global System Limit (100,000 req/s across the entire infrastructure), 2) Organization Limit (Enterprise tier gets 5,000 req/s), 3) User Limit (Individual API key gets 500 req/s), 4) Endpoint Limit (Expensive `/v1/analytics/export` gets 10 req/s per user). How do you architect hierarchical quota evaluation to enforce all four rules efficiently without multiplying Redis latency by 4x?",
        "If an API server performs 4 sequential network calls to Redis (one for system, one for org, one for user, one for endpoint), every API request incurs 4 round-trips (8-10ms latency). Architectural Solution: 1) Hierarchical Evaluation in a Single Atomic Batch/Lua Call: Pass all four keys (`[global, org_id, user_id, user_endpoint]`) and their respective limits into a single Redis Lua script (or Redis MGET/pipeline). The script evaluates all four token buckets atomically. 2) Short-Circuit Logic: The Lua script checks the limits in order: if the user-endpoint bucket is exhausted, it rejects immediately without consuming tokens from the user, org, or global buckets. If all four buckets have available capacity, it atomically decrements all four and returns 200 OK. 3) Two-Tier Local/Remote Evaluation: Evaluate the highest-frequency rule (Endpoint or User) in local fast memory first. 4) HTTP 429 Header Precision: If any rule fails, the response must identify *which* tier was breached (`X-RateLimit-Scope: endpoint` vs `X-RateLimit-Scope: organization`) and include the appropriate `Retry-After` timestamp corresponding to the specific breached quota.",
        [
            "Rejects 4 sequential network round-trips to Redis in favor of a single atomic batched Lua script execution",
            "Implements short-circuit evaluation logic to preserve tokens if a lower-level quota is breached",
            "Emits explicit scope indicators in 429 responses identifying whether user, organization, or endpoint limits were hit"
        ],
        [
            "Recommends evaluating each of the 4 limits on different days of the week"
        ]
    ),
    (
        "B68_3_13",
        "diagnose",
        "medium",
        "debugging",
        ["Rate Limiting", "Distributed Systems"],
        "NTP / Clock Skew",
        "Clock Skew Vulnerability in Time-Windowed Rate Limiters",
        "A fleet of 50 backend nodes enforces a sliding-window rate limit using local system timestamps passed to Redis: `redis.zadd(key, System.currentTimeMillis(), req_id)`. Suddenly, customers routed to Node 12 report that their rate limits reset erratically, allowing massive traffic spikes, while customers on Node 45 report receiving instant HTTP 429 errors despite sending zero requests. Explain how NTP clock drift causes this and how to fix it.",
        "Root Cause: Distributed nodes rely on independent local hardware clocks synchronized via NTP. If Node 12 has clock drift backward by 30 seconds and Node 45 has clock drift forward by 30 seconds: 1) Node 45 writes timestamps 30 seconds in the future into the Redis ZSET. When subsequent requests arrive on other nodes, the sliding-log cleanup query (`ZREMRANGEBYSCORE key -inf (now - window)`) fails to purge Node 45's future timestamps because their scores appear newer than the current time. The sliding window appears permanently full, causing immediate 429 rejections for innocent users. 2) Node 12 writes timestamps 30 seconds in the past. When Node 12 records a request, other nodes' sliding window purges immediately clean it up as 'expired' data, allowing the user to bypass rate limits and send double the allowed traffic. Fix: 1) Never trust client or individual application node system clocks for distributed time-window math. 2) Use Redis Server Time: Fetch time directly from the central Redis node using `redis.call('TIME')` inside the atomic Lua script. Because all nodes rely on Redis's single authoritative monotonic clock, clock skew across application servers is completely eliminated.",
        [
            "Diagnoses NTP clock drift causing future or past timestamps in Redis sliding window data structures",
            "Explains that future timestamps prevent record expiration (causing false 429s) while past timestamps bypass limits",
            "Fixes the issue by relying on Redis server time via redis.call('TIME') inside the atomic Lua script"
        ],
        [
            "Suggests turning off NTP synchronization across all cloud servers"
        ]
    ),
    (
        "B68_3_14",
        "concept",
        "easy",
        "concept",
        ["Rate Limiting", "Traffic Shaping"],
        "Algorithms",
        "Token Bucket vs Leaky Bucket for Traffic Shaping",
        "What is the operational difference between the 'Token Bucket' algorithm and the 'Leaky Bucket' algorithm, and why is Leaky Bucket preferred when downstream dependencies cannot tolerate sudden traffic bursts?",
        "1) Token Bucket: Tokens are added to a bucket at a constant rate up to a maximum capacity. An incoming request consumes a token and proceeds immediately. If the bucket is full (e.g., 50 tokens accumulated during an idle period), a burst of 50 requests arriving simultaneously can ALL be processed instantly. Token Bucket permits burstiness up to bucket capacity while enforcing an average rate over time. 2) Leaky Bucket (as a queue / traffic shaper): Incoming requests enter a FIFO queue (the bucket) of fixed capacity. Requests leak out of the bottom of the bucket to downstream services at a strictly constant, unvarying rate (e.g., exactly 10 requests per second), regardless of how fast requests arrived. If incoming traffic surges and the bucket fills, excess requests overflow and are rejected. 3) Why Leaky Bucket is Preferred for Fragile Downstream Services: Fragile dependencies (such as legacy mainframes, relational databases, or third-party APIs with rigid concurrency limits) crash if hit with a sudden spike of 50 concurrent requests. Leaky Bucket smooths jagged traffic spikes into a predictable, constant-rate stream, completely eliminating burst pressure.",
        [
            "Defines Token Bucket as permitting sudden bursts up to bucket capacity while enforcing an average rate",
            "Defines Leaky Bucket as smoothing traffic into a strictly constant, unvarying egress rate",
            "Explains that Leaky Bucket protects fragile downstream dependencies that cannot tolerate concurrent burst spikes"
        ],
        [
            "Claims Leaky Bucket means the server has a physical water leak in the datacenter"
        ]
    ),
    (
        "B68_3_15",
        "scenario",
        "medium",
        "scenario",
        ["Rate Limiting", "Multi-Tenant Architecture"],
        "SaaS Architecture",
        "Noisy Neighbor Protection via Dynamic Tenant Rate Limiting",
        "Your SaaS platform offers Free and Enterprise tiers on a shared microservice backend. A free-tier developer writes a malfunctioning crawler script that submits 20,000 requests per second. Although the free-tier rate limit responds with HTTP 429, the sheer volume of 20,000 req/s hitting the edge gateways exhausts gateway worker threads and degrades latency for paying Enterprise customers. How do you implement multi-layered rate limiting to shield enterprise traffic from noisy free-tier storms?",
        "To protect paying tenants from rogue free-tier traffic storms: 1) Edge IP / Connection Throttling: Enforce connection-level rate limiting at the edge proxy (NGINX/Cloudflare/Envoy) before application request processing. If a single IP or API key exceeds 1,000 req/s, drop or reject connections at the edge proxy layer (or return lightweight HTTP 429) without routing traffic to internal API gateway clusters. 2) Tier-Isolated Thread / Connection Bulkheads: Physically partition edge gateway capacity. Allocate dedicated gateway instances or dedicated worker thread pools for Enterprise tenants (`enterprise.api.domain.com`) separate from Free-tier routing (`api.domain.com`). 3) Early API Key Rejection: Cache revoked or heavily throttled free-tier API keys in a high-speed edge in-memory bloom filter or CDN edge key-value store (Cloudflare Workers / Fastly). Drop their requests at the CDN edge before they reach the origin datacenter. 4) Backoff Penalty / Jail Time: Implement a graduated penalty box: if a free-tier client exceeds their quota by 10x, temporarily ban their API key for 15 minutes, instantly returning 429 from edge memory without evaluating rate limit buckets in Redis.",
        [
            "Implements edge-layer rate limiting (Cloudflare/proxy) to drop excessive traffic before touching backend gateways",
            "Applies bulkheading by isolating Enterprise endpoints/gateways from Free-tier ingress",
            "Introduces temporary bans / penalty boxes for clients that aggressively breach limits by orders of magnitude"
        ],
        [
            "Recommends deleting all Free-tier user databases immediately"
        ]
    ),
    (
        "B68_3_16",
        "implement",
        "medium",
        "implement",
        ["Rate Limiting", "API Design"],
        "GraphQL / Database APIs",
        "Cost-Based Rate Limiting for Complex Queries",
        "In a GraphQL API, simple queries (`{ user { id } }`) consume 0.1ms of database CPU, while deeply nested queries (`{ users { friends { posts { comments { author } } } } }`) consume 5 seconds of database CPU and 1GB of RAM. Explain why simple request-count rate limiting (e.g., 100 req/min) fails to protect the backend, and how you implement 'Cost-Based Rate Limiting'.",
        "Why Request-Count Rate Limiting Fails: A malicious or unoptimized client can stay well within the 100 requests/minute limit while sending 100 deeply nested, cyclic queries that join 10 database tables. 100 heavy queries will completely saturate database CPU and exhaust server memory, crashing the service despite technically complying with the rate limit. Implementation of Cost-Based Rate Limiting: 1) Query AST Static Analysis: Before executing the GraphQL query, parse the Abstract Syntax Tree (AST) to compute a 'Complexity Cost' based on field depth, multipliers on list fields (`posts(limit: 50)`), and expensive resolver attributes. 2) Token Cost Deduction: Instead of decrementing the token bucket by 1 per request, decrement by the calculated query cost: e.g., a simple query costs 1 point, while a deeply nested query costs 250 points. 3) Credit Ledger Evaluation: If the user's available bucket has fewer credits than the calculated complexity score, reject the query immediately with HTTP 429 *before* executing any database resolvers or allocating memory. 4) Client Visibility: Return query cost and remaining budget in HTTP response headers: `X-RateLimit-Query-Cost: 250`, `X-RateLimit-Remaining: 750`.",
        [
            "Explains that request counts fail because query execution costs vary by orders of magnitude",
            "Parses the GraphQL AST to calculate a complexity score based on field depth and list multipliers before execution",
            "Decrements rate limit token buckets by the query complexity score rather than by a flat 1 count"
        ],
        [
            "Suggests running the query first, timing how long it takes, and then charging the user's credit card"
        ]
    ),
    (
        "B68_3_17",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Rate Limiting", "Resilience"],
        "High Availability Architecture",
        "Distributed Rate Limiting: Fail-Open vs Fail-Closed",
        "During a catastrophic Redis cluster outage where the central rate-limiting store is completely unreachable, what is the architectural tradeoff between configuring your API Gateway to 'Fail-Open' versus 'Fail-Closed'?",
        "Fail-Open (Permissive Mode): 1) Behavior: If the rate limiter encounters a Redis timeout or connection error, it logs an alert and allows all incoming client requests to pass through to downstream backend services without throttling. 2) Tradeoff: Prioritizes Availability over Protection. Legitimate users experience zero downtime and business transactions proceed uninterrupted. However, the system loses its shield against DDoS attacks, runaway scraping bots, and abusive tenants; if the Redis outage coincided with a traffic surge, the unprotected downstream microservices and databases may be immediately overwhelmed and crash. Fail-Closed (Strict Mode): 1) Behavior: If Redis is unreachable, the rate limiter assumes the worst and rejects incoming requests with HTTP 429 or 503. 2) Tradeoff: Prioritizes Backend Protection over Availability. Guarantees that internal databases and core microservices are shielded from unmetered overload. However, this converts a localized Redis caching failure into a total outage for 100% of legitimate paying users. Production Best Practice: Hybrid Fail-Open with Local Fallback: Fall back to local in-memory heuristic rate limiting (e.g., local token bucket capping each node at a safe threshold) while Redis recovers.",
        [
            "Defines Fail-Open as allowing traffic through during rate store outages (prioritizing availability over protection)",
            "Defines Fail-Closed as rejecting traffic during rate store outages (prioritizing backend protection over availability)",
            "Advocates a hybrid approach: falling back to conservative local in-memory rate limits during central store outages"
        ],
        [
            "Claims rate limiters can never fail because Redis runs entirely in memory"
        ]
    ),
    (
        "B68_3_18",
        "scenario",
        "hard",
        "scenario",
        ["Rate Limiting", "Adaptive Systems"],
        "Resilience Engineering",
        "Adaptive Dynamic Rate Limiting via Downstream Backpressure Signals",
        "Static rate limits (e.g., 5,000 req/s) fail during downstream degradations: if a database loses two read replicas, 5,000 req/s crashes the database, whereas during low load, 5,000 req/s artificially throttles clients when the cluster has idle capacity. How do you design an 'Adaptive Dynamic Rate Limiting' system that automatically adjusts client quotas based on downstream latency, error rates, and queue depth?",
        "Adaptive Dynamic Rate Limiting replaces static numbers with a feedback loop modeled after TCP congestion control (AIMD or CoDel): 1) Continuous Metric Feedback: The rate limiting layer (or API Gateway) continuously samples key health metrics from downstream dependencies: p99 latency, database connection pool saturation, queue depth, and HTTP 5xx/429 error ratios. 2) Additive Increase / Multiplicative Decrease (AIMD): While downstream metrics remain below healthy thresholds (e.g., p99 latency < 50ms, DB connection utilization < 70%), the rate limiter gradually increases the global allowable capacity (Additive Increase: $+5\\%$ every 10 seconds). 3) Rapid Throttling under Strain: As soon as downstream metrics breach degradation thresholds (e.g., p99 latency spikes above 200ms or DB connection pool reaches 95%), the rate limiter immediately slashes allowable throughput (Multiplicative Decrease: cut total capacity by $30-50\\%$) to allow downstream resources to recover. 4) Priority Shedding: When throttling, shed traffic based on business priority: first throttle unauthenticated and free-tier traffic, then background batch jobs, while preserving capacity for core paying user workflows.",
        [
            "Identifies the limitation of static rate limits during infrastructure degradation",
            "Implements a feedback loop using Additive Increase / Multiplicative Decrease (AIMD) based on downstream latency and saturation",
            "Applies priority-based load shedding to throttle low-priority traffic while preserving critical user operations"
        ],
        [
            "Suggests manually editing YAML configuration files every time database latency spikes"
        ]
    ),
    (
        "B68_3_19",
        "concept",
        "easy",
        "concept",
        ["Rate Limiting", "API Design"],
        "HTTP Standards",
        "Standardized HTTP Rate Limiting Headers",
        "What are the standardized IETF rate limiting response headers (`RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`, and `Retry-After`), and how do client SDKs use them to implement automated, respectful backoff?",
        "Standardized Rate Limiting Headers: 1) `RateLimit-Limit`: The maximum number of requests allowed within the current quota window (e.g., `RateLimit-Limit: 1000`). 2) `RateLimit-Remaining`: The number of requests remaining in the current window (e.g., `RateLimit-Remaining: 42`). 3) `RateLimit-Reset`: The number of seconds (or Unix timestamp) until the current rate limit window resets and full quota is restored (e.g., `RateLimit-Reset: 15`). 4) `Retry-After`: Returned with an HTTP 429 Too Many Requests response, indicating the exact number of seconds the client must wait before making another request (e.g., `Retry-After: 30`). How Client SDKs Use Them: Instead of hardcoded retry loops, well-architected client SDKs inspect the headers: 1) Proactive Pacing: When `RateLimit-Remaining` approaches zero, SDKs can throttle outgoing request rates or queue non-urgent requests locally. 2) Automated Backoff: Upon receiving an HTTP 429, the SDK reads the `Retry-After` header, pauses execution for the exact specified duration (plus minor jitter), and retries the request safely without spamming the server.",
        [
            "Defines the roles of RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset, and Retry-After headers",
            "Explains that 429 responses utilize Retry-After to inform clients of the exact required wait duration",
            "Describes client SDK behavior: pacing requests when remaining quota is low and sleeping based on Retry-After"
        ],
        [
            "Claims HTTP 429 headers are used by web browsers to charge credit cards for extra bandwidth"
        ]
    ),
    (
        "B68_3_20",
        "diagnose",
        "medium",
        "debugging",
        ["Rate Limiting", "Performance Tuning"],
        "System Architecture",
        "Thundering Herd on Fixed-Window Rate Limit Resets",
        "An API implements a Fixed-Window rate limit of 6,000 requests per hour, resetting at the top of every hour (e.g., 01:00:00, 02:00:00). Every hour at exactly :00 seconds, the API server experiences a massive 50x CPU spike, thread pool exhaustion, and hundreds of database deadlocks for 15 seconds, after which traffic returns to normal. What causes this hourly surge, and how does randomized window jitter or sliding windows prevent it?",
        "Root Cause: The 'Thundering Herd on Window Reset' problem. Because all client rate limits reset at the exact same synchronized wall-clock minute (`:00:00`), hundreds of external client scrapers, automated sync scripts, and batch jobs that exhausted their hourly quota during the previous hour are programmed to sleep until the top of the hour. At exactly `:00:00`, thousands of paused clients wake up simultaneously and hammer the API with accumulated backlogs. This synchronized surge floods backend thread pools and database connections. Mitigations: 1) Sliding-Window Counter: Replace fixed windows with sliding-window counters. Quotas recover continuously second-by-second rather than in a single instantaneous midnight/hourly cliff, naturally distributing client retries across time. 2) Client-Specific Window Anchoring / Jitter: Instead of aligning windows to global wall-clock hours, anchor each client's 1-hour window to the timestamp of their *first request* (or randomize window reset times per user/API key using hash-based jitter). This staggers reset boundaries evenly across the 3,600 seconds of the hour, completely flattening the hourly spike.",
        [
            "Diagnoses synchronized client wakeups at fixed-window reset boundaries (:00:00) causing massive traffic spikes",
            "Replaces rigid fixed windows with rolling sliding windows to restore quota continuously",
            "Anchors rate limit windows to client start times or introduces randomized window jitter to stagger reset events"
        ],
        [
            "Recommends turning off server clocks at the top of every hour to avoid the reset"
        ]
    )
]

def run_batch():
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[7]) or LEAK.search(q[8]):
            print(f"PROMPT LEAK DETECTED in: {q[7]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[7] for q in Q]
    
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
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[7][:50]}...")
            rejected.append(q)
        else:
            print(f"ACCEPTED (Sim: {max_sim:.2f}): {q[7][:60]}...")
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 3).")
    if len(rejected) > 0:
        print("Stopping due to rejections.")
        sys.exit(1)
        
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "role": ROLE,
            "applicable_roles": ["Distributed Systems Engineer", "Software Engineer"],
            "primary_skill": q[4][0],
            "skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": q[5],
            "topic": q[6],
            "category": "Backend Engineering",
            "intent": q[1],
            "difficulty": q[2],
            "question_type": q[3],
            "question": q[7],
            "ideal_answer": q[8],
            "expected_answer": q[8],
            "evaluation_rubric": {
                "strong_indicators": q[9],
                "weak_indicators": q[10]
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
            
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r.get("primary_role") or r.get("role") for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT PART 3")
    print("========================================")
    print(f"Batch: 68 Part 3")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
