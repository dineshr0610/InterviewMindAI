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
        "B68_5_1",
        "diagnose",
        "hard",
        "debugging",
        ["Resource Management", "Linux / OS"],
        "Operating Systems / Go / Java",
        "File Descriptor Leaks and EMFILE Exhaustion",
        "A backend microservice runs reliably for 4 days, then suddenly begins rejecting all incoming HTTP requests and database connections with `java.io.IOException: Too many open files` (or `EMFILE: accept tcp [::]:8080: accept4: too many open files`). Heap memory and CPU are at 10%. How do you diagnose which resources are leaking using Linux tools (`lsof`, `/proc`), and what common application code mistakes cause file descriptor leaks?",
        "Diagnosis: 1) Check Limits: Inspect process file descriptor limits via `cat /proc/<PID>/limits | grep 'open files'` to view soft and hard `nofile` limits. 2) Identify Leaking Descriptors: Run `lsof -p <PID> | wc -l` to count open descriptors, and `ls -l /proc/<PID>/fd` to inspect the descriptor symlinks. Group descriptors by type: `lsof -p <PID> | awk '{print $5}' | sort | uniq -c | sort -nr`. If thousands of descriptors are `FIFO` or `sock`, network sockets are leaking; if `REG`, disk files are leaking. 3) Inspect Remote Socket Endpoints: Run `lsof -i -a -p <PID>` to see target IPs and ports of leaked sockets. Common Application Code Mistakes: A) Unclosed Outbound HTTP Response Bodies: In Go (`resp.Body.Close()`), Java (`InputStream.close()`), or Python, failing to read and close the HTTP response body prevents the underlying TCP socket from returning to the connection pool, leaking the file descriptor on every outbound API call. B) Unclosed Database Connections or ResultSets: Failing to release connections in a `finally` block or try-with-resources. C) Unclosed File Streams: Opening files for logging or reading without closing them. Fix: Always use deterministic resource management (`try-with-resources` in Java, `defer resp.Body.Close()` in Go) and configure connection pool maximums.",
        [
            "Inspects process file descriptor limits and active descriptors via /proc/<PID>/fd and lsof",
            "Identifies unclosed HTTP response bodies (e.g. Go resp.Body.Close) leaking underlying TCP sockets",
            "Prescribes deterministic resource cleanup via try-with-resources / defer statements"
        ],
        [
            "Suggests restarting the server every hour with a cron job as the permanent fix"
        ]
    ),
    (
        "B68_5_2",
        "implement",
        "medium",
        "implement",
        ["Resource Management", "Concurrency"],
        "Go / Java / Node.js",
        "Request Cancellation Propagation to Downstream Dependencies",
        "When an end-user navigates away or cancels a web search that triggers a heavy 5-second SQL query and 3 downstream microservice RPCs, what is 'Ghost Processing', and how do you implement Request Cancellation Propagation (e.g., Go `context.Context` cancellation or Java `CompletableFuture.cancel`) to abort downstream execution immediately upon client disconnect?",
        "Ghost Processing occurs when an upstream client disconnects (closes their browser tab, terminates the HTTP connection, or experiences a client-side timeout), but the backend server blindly continues executing the 5-second SQL query and downstream microservice calls to completion. This wastes massive amounts of database CPU, memory, thread pool slots, and network bandwidth on results that will be immediately discarded upon attempting to write back to the closed socket. Implementation of Request Cancellation Propagation: 1) Socket Disconnect Listener: The HTTP server detects socket closure via TCP FIN/RST packets. 2) Cancellation Signal: In Go, the server binds this to `r.Context()`. When the client disconnects, `ctx.Done()` is closed. In Java, register an asynchronous callback on the servlet/reactive request context to trigger cancellation tokens. 3) Context Propagation Downstream: Pass the cancellable context into: A) The Database Driver (`db.QueryContext(ctx, query)`): When context cancels, the database driver sends an explicit query cancellation packet (e.g., PostgreSQL `pg_cancel_backend`) to immediately kill the running SQL query on the database engine. B) Outbound HTTP/gRPC Clients: The gRPC client immediately sends an `RST_STREAM` frame to upstream microservices, propagating the cancellation recursively through the entire service tree and releasing resources instantly.",
        [
            "Defines Ghost Processing as executing work whose requesting client has already disconnected",
            "Binds client TCP socket closure to language cancellation primitives (Go context.Context, Java cancellation tokens)",
            "Propagates cancellation to database drivers (terminating running queries) and gRPC/HTTP clients (sending cancel frames)"
        ],
        [
            "Claims web servers cannot know when a client closes their browser tab"
        ]
    ),
    (
        "B68_5_3",
        "diagnose",
        "hard",
        "debugging",
        ["Resource Management", "Memory Management"],
        "Netty / JVM Off-Heap",
        "Off-Heap Direct Memory Leaks and Netty ByteBuf Reference Counting",
        "A high-throughput API gateway built on Netty (or Spring WebFlux) crashes every 24 hours with `java.lang.OutOfMemoryError: Direct buffer memory`. You analyze a JVM heap dump and discover that the JVM heap is nearly empty (only 500MB used out of 8GB allocated). What is 'Off-Heap Direct Memory', why don't JVM Garbage Collectors automatically free it, and how does Netty's `ByteBuf` reference counting cause this leak when developers miss `ReferenceCountUtil.release()`?",
        "Why Heap Dumps Show Empty Memory: Java allocates standard objects on the JVM Heap, managed by Garbage Collection. However, high-performance networking frameworks like Netty use 'Direct ByteBuffers' allocated outside the JVM heap in native C OS memory (Off-Heap) to enable zero-copy network I/O directly from OS kernel sockets to network buffers. Because off-heap memory resides outside the JVM heap, standard JVM Garbage Collection algorithms do NOT regularly scan or reclaim it, and JVM heap dump analysis tools cannot inspect native off-heap memory. Root Cause: Netty implements manual reference counting for `ByteBuf` instances (`retain()` and `release()`) for pooling and performance. Whenever an inbound network packet is decoded, Netty increments the `ByteBuf` reference count. If an application developer writes custom pipeline handlers and reads a `ByteBuf` without either forwarding it down the Netty channel pipeline or explicitly calling `ReferenceCountUtil.release(msg)`, the native off-heap buffer is never freed. Over millions of requests, native memory steadily accumulates until the OS/JVM direct memory limit (`-XX:MaxDirectMemorySize`) is breached, crashing the JVM. Diagnosis and Fix: Enable Netty leak detection in staging (`-Dio.netty.leakDetection.level=PARANOID`), inspect leak stack traces, and ensure every consumed buffer is released in a mandatory `try-finally` block.",
        [
            "Explains that Netty direct memory resides off-heap in native OS memory for zero-copy I/O and is not freed by standard GC",
            "Identifies unreleased ByteBuf reference counts (missing ReferenceCountUtil.release) as the cause of native leaks",
            "Prescribes enabling Netty leak detection (-Dio.netty.leakDetection.level=PARANOID) and releasing buffers in try-finally blocks"
        ],
        [
            "Suggests increasing JVM heap size to 128GB to fix direct buffer memory errors"
        ]
    ),
    (
        "B68_5_4",
        "explain",
        "medium",
        "explain",
        ["Resource Management", "Networking"],
        "TCP / Sockets",
        "Ephemeral Port Exhaustion and Sockets in TIME_WAIT State",
        "A microservice makes 2,000 outbound HTTP calls per second to an external payment API. Every few hours, outbound requests abruptly fail with `java.net.NoRouteToHostException: Cannot assign requested address` (or `connect: cannot assign requested address`). Running `netstat -an | grep TIME_WAIT` shows 60,000 sockets stuck in `TIME_WAIT`. What causes this ephemeral port exhaustion, and how does HTTP connection pooling resolve it?",
        "Mechanism of Failure: 1) TCP Connection Lifecycle: When an application makes an HTTP request and closes the connection, the TCP protocol mandates that the side initiating the active close must keep the socket in the `TIME_WAIT` state for $2 \times MSL$ (Maximum Segment Lifetime, typically 60 to 120 seconds). This ensures any delayed duplicate packets in the network are safely discarded and do not corrupt future connections. 2) Ephemeral Port Exhaustion: Linux allocates a range of ephemeral local ports for outbound connections (typically ~28,000 to 60,000 ports via `/proc/sys/net/ipv4/ip_local_port_range`). 3) If an application creates a new HTTP client or TCP connection for every single request instead of reusing connections, at 2,000 requests/sec over 60 seconds, it consumes 120,000 ephemeral ports. Because `TIME_WAIT` locks ports for 60 seconds, the kernel runs completely out of available source ports, throwing `Cannot assign requested address`. Resolution: Implement Persistent HTTP Connection Pooling (HTTP Keep-Alive). Configure the HTTP client to maintain a pooled set of persistent TCP connections (e.g., 50-100 connections) and reuse them across requests. By keeping sockets open and multiplexing requests over existing connections, outbound connection creation drops to near zero, completely eliminating ephemeral port exhaustion and `TIME_WAIT` buildup.",
        [
            "Explains that active TCP close keeps sockets in TIME_WAIT state for 2*MSL (60-120 seconds)",
            "Shows that creating new connections per request exhausts the Linux ephemeral port range (~30k-60k ports)",
            "Resolves the issue via persistent HTTP connection pooling and Keep-Alive to reuse sockets"
        ],
        [
            "Claims TIME_WAIT means the server's clock is set to the wrong timezone"
        ]
    ),
    (
        "B68_5_5",
        "explain",
        "medium",
        "explain",
        ["Capacity Planning", "Performance Tuning"],
        "Queuing Theory / Little's Law",
        "Applying Little's Law to Backend Capacity Planning",
        "How do backend architects use Little's Law ($L = \\lambda W$) to calculate the required concurrency (thread pool size or connection pool size) for an API service, and how does a 3x increase in downstream latency trigger catastrophic queue backlog explosions under constant traffic?",
        "Little's Law Formula: In a stable system, the average number of concurrent requests in the system ($L$) equals the arrival rate of requests ($\\lambda$) multiplied by the average time a request spends in the system ($W$): $L = \\lambda \\times W$. Capacity Planning Application: If an API receives an arrival rate of $\\lambda = 1,000$ requests/sec and downstream processing takes an average of $W = 50ms$ (0.05s), the required concurrent execution capacity is $L = 1,000 \\times 0.05 = 50$ concurrent threads/connections. The architect provisions a thread pool and DB connection pool of 60 to comfortably handle normal load. Catastrophic Latency Multiplication: Suppose arrival rate $\\lambda$ remains constant at 1,000 req/s, but a downstream database dependency slows down due to lock contention, increasing average latency $W$ from 50ms to 150ms ($3\\times$). By Little's Law: $L_{new} = 1,000 \\times 0.15 = 150$ concurrent requests. Because the server only has 50 worker threads, the remaining 100 requests per second are forced into the in-memory task queue. Within 10 seconds, 1,000 requests accumulate in the queue. Memory usage explodes, request queue wait times skyrocket to 10+ seconds, client timeouts trigger retries, and the service suffers total collapse despite traffic volume never changing.",
        [
            "Applies Little's Law ($L = \\lambda W$) to compute required thread/connection pool concurrency",
            "Demonstrates that a 3x latency increase triples the required concurrency under constant request arrival rates",
            "Explains queue backlog accumulation, memory saturation, and eventual collapse when latency exceeds pool capacity"
        ],
        [
            "Claims Little's Law is a rule stating that junior developers write smaller code than seniors"
        ]
    ),
    (
        "B68_5_6",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Performance Tuning", "Distributed Systems"],
        "Tail Latency / Distributed Architecture",
        "Fan-Out Tail Latency Amplification and Hedged Requests",
        "In a microservices architecture, a user request fans out in parallel to 20 downstream microservices (`CompletableFuture.allOf()`). If each individual microservice has a 99th percentile (p99) latency of 100ms, why is the user's overall p99 latency drastically worse than 100ms, and how do 'Hedged Requests' (speculative retries) mitigate tail latency without doubling cluster load?",
        "Tail Latency Amplification Math: When a service fans out to $N$ independent parallel dependencies, the overall request latency is dictated by the *slowest* dependency ($Latency_{total} = \\max(L_1, L_2, ..., L_{20})$). The probability that ALL 20 services respond within their individual 99th percentile (1% chance of being slow) is: $(0.99)^{20} \\approx 0.818$ (81.8%). This means that roughly 18.2% of all user requests will experience a tail latency spike! Even though each individual service has a 99% success rate, the aggregated service delivers a dreadful p82 tail latency. At 100 parallel calls, 63% of requests hit tail latency. Hedged Requests (Speculative Retries) Mitigation: Instead of sending two identical requests simultaneously (which doubles backend load), a Hedged Request sends the initial request and starts a timer at the expected 95th percentile latency (e.g., 50ms). If the primary request has not responded after 50ms, the client dispatches a second 'hedged' copy of the request to an alternate server replica. Whichever copy returns first is accepted, and the other is immediately canceled. Because only 5% of requests trigger a hedged call, backend load increases by only ~5%, but severe p99/p99.9 tail latency outliers (caused by GC pauses, disk hiccups, or thread contention on a single node) are virtually eliminated.",
        [
            "Calculates the tail latency probability degradation across parallel fan-outs ($P = (0.99)^N$)",
            "Explains that the aggregate request latency is bounded by the slowest single service in the fan-out",
            "Implements Hedged Requests: dispatching a speculative secondary request after a p95 delay threshold to cancel tail outliers with minimal extra load"
        ],
        [
            "Claims parallel fan-out latency is always equal to the average of all 20 services"
        ]
    ),
    (
        "B68_5_7",
        "scenario",
        "medium",
        "scenario",
        ["Resource Management", "Concurrency"],
        "Thread Pools",
        "Thread Pool Starvation via Blocking I/O in Shared Pools",
        "A backend service uses a shared thread pool of 50 threads for both fast CPU operations (calculating discounts) and external HTTP API calls. A developer adds a call to a third-party CRM that intermittently takes 10 seconds to respond. Suddenly, simple in-memory discount calculations that normally take 0.5ms take 10 seconds, and the API throughput drops by 98%. Explain how blocking I/O causes Thread Pool Starvation, and how to structure thread pool bulkheads.",
        "Root Cause: Thread Pool Starvation. In a shared thread pool, every worker thread is fungible. When the CRM API experiences high latency (10 seconds), worker threads picking up CRM tasks become blocked waiting on network socket I/O. Because CRM requests arrive continuously, all 50 threads in the global pool become occupied waiting for CRM network sockets. Simple, fast CPU discount calculations waiting in the task queue cannot acquire a thread; they sit queued for 10 seconds behind blocked network calls. A 0.5ms operation now exhibits 10,000ms latency due to queue wait time. Architectural Solution: Thread Pool Bulkheading: 1) Dedicated Pool for Fast Work: Create a dedicated, non-blocking CPU thread pool sized to the number of CPU cores for in-memory computations. 2) Dedicated Bounded Pool for External I/O: Isolate external CRM calls into a separate, dedicated thread pool with strict bounds (e.g., max 15 threads, queue capacity 20). 3) Fast-Failing Queue / Circuit Breaker: If the CRM pool fills up, immediately reject further CRM calls with HTTP 503 or trip a circuit breaker rather than allowing backlog accumulation. The CPU discount calculations continue executing at full sub-millisecond line speed with zero interference.",
        [
            "Diagnoses fast in-memory tasks being starved in the work queue because slow blocking I/O occupies all shared worker threads",
            "Applies the Bulkhead pattern: segregating CPU-bound tasks from external blocking network I/O into separate thread pools",
            "Enforces bounded task queues and circuit breakers on the external I/O pool to fail fast without degrading core services"
        ],
        [
            "Suggests setting the thread pool size to 50,000 threads"
        ]
    ),
    (
        "B68_5_8",
        "concept",
        "easy",
        "concept",
        ["Resource Management", "Reliability"],
        "Process Lifecycle / Kubernetes",
        "Graceful Shutdown Lifecycle in Backend Applications",
        "When a cloud orchestrator (like Kubernetes) deploys a new version of a microservice, it terminates old pods by sending a `SIGTERM` followed by a `SIGKILL` 30 seconds later. What sequence of operations must a backend application execute during graceful shutdown to avoid dropping in-flight client requests or corrupting database transactions?",
        "Proper Graceful Shutdown Sequence: 1) Trap SIGTERM: The application registers an OS signal handler for `SIGTERM`. 2) Stop Accepting Ingress Traffic: Immediately stop accepting *new* incoming HTTP/TCP connections (close the listening server socket or fail readiness probes). Load balancers detect this and stop routing new client traffic to this pod. 3) In-Flight Request Draining: Keep existing worker threads alive and allow currently active in-flight HTTP requests and database transactions to finish processing naturally (up to a graceful drain timeout, e.g., 20 seconds). 4) Consumer / Background Worker Shutdown: Pause message queue consumers (e.g., Kafka `consumer.wakeup()` or RabbitMQ channel pause) so no new messages are pulled from the broker; finish processing current message batches and commit offsets. 5) Resource Cleanup: Close database connection pools, flush log buffers to disk, and release Redis/network connections. 6) Clean Exit: Call `System.exit(0)` before Kubernetes sends `SIGKILL` (which would abruptly terminate processes and corrupt uncommitted state).",
        [
            "Traps SIGTERM and stops accepting new connections / fails readiness probes",
            "Drains in-flight HTTP requests and database transactions to completion within a graceful timeout window",
            "Pauses background consumers, commits offsets, and flushes connection pools before exit"
        ],
        [
            "Claims SIGKILL should be called immediately on the first line of code"
        ]
    ),
    (
        "B68_5_9",
        "explain",
        "hard",
        "explain",
        ["API Security", "Network Protocols"],
        "HTTP Request Smuggling",
        "HTTP Request Smuggling: TE.CL and CL.TE Desynchronization",
        "In a backend architecture where an edge reverse proxy forwards HTTP/1.1 requests over persistent keep-alive connections to backend application servers, how does conflicting interpretation of `Content-Length` (CL) and `Transfer-Encoding` (TE) headers cause HTTP Request Smuggling, and how can an attacker hijack subsequent users' requests?",
        "HTTP Request Smuggling occurs when the front-end reverse proxy and the back-end application server disagree on where an HTTP request message boundary ends on a persistent TCP stream. RFC 2616 specifies that if both headers are present, `Transfer-Encoding` takes precedence over `Content-Length`. However, discrepancies occur: 1) CL.TE Desynchronization: The front-end uses `Content-Length`, but the back-end uses `Transfer-Encoding`. An attacker crafts a request with `Content-Length: 13` and `Transfer-Encoding: chunked`. The front-end proxy reads 13 bytes and forwards the entire packet. The backend server reads the chunked encoding, hits a chunk of length 0 (terminating request 1), and treats the remaining trailing bytes as the START of request 2! 2) TE.CL Desynchronization: The front-end uses `Transfer-Encoding`, but the back-end uses `Content-Length`. The front-end processes chunked data and forwards it; the back-end reads only the byte count specified in Content-Length, leaving the remaining payload lingering in the backend TCP socket buffer. 3) Attack Impact: The leftover 'smuggled' data sits in the shared TCP buffer. When an innocent user sends their next request (e.g., `GET /account`), the backend prepends the smuggled prefix to the innocent user's request, allowing the attacker to hijack credentials, poison web caches, or bypass authentication. Fix: Disable HTTP/1.1 pipelining, enforce HTTP/2 end-to-end, or configure edge proxies to strictly normalize and strip conflicting headers.",
        [
            "Explains that request smuggling arises from front-end and back-end proxies disagreeing on request boundaries on persistent TCP streams",
            "Contrasts CL.TE and TE.CL desynchronization mechanisms with chunked encoding and Content-Length mismatches",
            "Demonstrates that orphaned smuggled bytes in socket buffers prepend to subsequent users' requests, hijacking sessions"
        ],
        [
            "Claims request smuggling means sneaking a flash drive into the physical server room"
        ]
    ),
    (
        "B68_5_10",
        "diagnose",
        "hard",
        "debugging",
        ["API Security", "Networking"],
        "SSRF / DNS Rebinding",
        "SSRF via DNS Rebinding Attacks and Socket-Level Validation",
        "A developer secures an endpoint that fetches user-provided URLs (`POST /fetch-url { \"url\": \"http://example.com/data\" }`) by checking the hostname before requesting: `ip = dns.resolve(host); if(isPrivateIP(ip)) throw Error(); http.get(url);`. An attacker bypasses this check and successfully extracts AWS EC2 instance metadata (`http://169.254.169.254/latest/meta-data/`). Explain how DNS Rebinding bypassed the developer's check, and how to implement secure socket-level IP validation.",
        "Why the Check Failed (DNS Rebinding): The developer commits a classic Time-of-Check to Time-of-Use (TOCTOU) vulnerability: 1) The attacker sets up a malicious DNS nameserver for domain `attacker.com` with a DNS TTL of 0 seconds. 2) Check Phase: The application executes `dns.resolve('attacker.com')`. The attacker's DNS server returns a legitimate public IP (`93.184.216.34`). The `isPrivateIP()` check passes. 3) Execution Phase: When `http.get('http://attacker.com/data')` executes a millisecond later, the HTTP client performs a *second* DNS resolution because the TTL was 0 seconds. This time, the attacker's DNS server responds with `169.254.169.254` (the AWS link-local metadata IP). The HTTP client connects directly to the internal metadata service and returns private AWS credentials to the attacker. Secure Socket-Level IP Validation: 1) Eliminate Hostname-Based HTTP Requests: Do not resolve DNS once for validation and let the HTTP client resolve it again. 2) Custom Socket Dialer: Intercept the socket connection at the transport layer (e.g., custom `net.Dialer` in Go or custom `SocketFactory` in Java). 3) In the socket dialer, resolve the IP, immediately validate that the resolved IP does NOT match private/loopback/link-local ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`), and connect directly to that *exact validated IP address*. 4) Pass the original hostname only in the HTTP `Host` header, completely eliminating the DNS rebinding window.",
        [
            "Explains TOCTOU race: first DNS lookup validates a public IP, but second lookup via TTL=0 returns the private metadata IP",
            "Identifies AWS link-local metadata IP (169.254.169.254) as the extraction target",
            "Prescribes a custom socket dialer validating IP ranges at connection time and connecting directly to the validated IP"
        ],
        [
            "Claims DNS Rebinding can be fixed by installing an antivirus program on the developer's laptop"
        ]
    ),
    (
        "B68_5_11",
        "implement",
        "medium",
        "implement",
        ["API Security", "OAuth2"],
        "RFC 8693 / Token Exchange",
        "Token Exchange (RFC 8693) for Internal Microservices",
        "In a microservices architecture, why is passing the end-user's raw OAuth2 Bearer JWT across 10 internal microservices a violation of the Principle of Least Privilege, and how does OAuth 2.0 Token Exchange (RFC 8693) generate scoped, downscoped service tokens for downstream calls?",
        "Why Passing Raw Bearer Tokens Violates Least Privilege: 1) Excessive Scope: The user's initial bearer token often has broad permissions (e.g., `scope: [read_profile, edit_payment, delete_account]`). If the Frontend calls the Order Service, and Order Service forwards this exact raw token to an unprivileged Analytics or Shipping service, a vulnerability or compromised container in Analytics can use the user's broad token to delete the user's account or modify payments (Confused Deputy problem). 2) Audience Confusion: The token's `aud` (audience) claim points to the initial API; forwarding it internally breaks cryptographic audience boundaries. RFC 8693 Token Exchange Implementation: 1) When Order Service needs to call Shipping Service on behalf of the user, it calls the internal Authorization Server / Identity Provider (`POST /oauth/v2/token`) specifying `grant_type=urn:ietf:params:oauth:grant-type:token-exchange`. 2) Parameters: It passes the user's incoming token as `subject_token`, its own client credentials, and the desired audience `audience=https://shipping.internal` with downscoped permissions `scope=read_shipping_labels`. 3) Result: The IdP validates that Order Service is authorized to impersonate or act on behalf of the user, and issues a new, short-lived JWT scoped strictly to Shipping Service. If Shipping Service is compromised, the attacker cannot reuse the token against Payment or Account services.",
        [
            "Identifies the Confused Deputy vulnerability and excessive privilege when forwarding raw user tokens internally",
            "Implements RFC 8693 Token Exchange to trade user tokens for tightly scoped, audience-restricted downstream tokens",
            "Demonstrates least privilege containment: downstream compromised services receive tokens valid only for their domain"
        ],
        [
            "Claims all microservices should share a single plaintext password stored in Git"
        ]
    ),
    (
        "B68_5_12",
        "scenario",
        "medium",
        "scenario",
        ["API Security", "Key Management"],
        "HashiCorp Vault",
        "Dynamic Ephemeral Database Credentials via Secret Engines",
        "Instead of storing static PostgreSQL credentials (`db_user` and `db_password`) in Kubernetes ConfigMaps or environment variables that never change, how do you architect backend application integration with HashiCorp Vault's Database Secret Engine to generate dynamic, short-lived ephemeral credentials that automatically expire in 1 hour?",
        "Architecture with Dynamic Vault Secrets: 1) Application Identity & Authentication: When a backend pod starts, it authenticates with Vault using its Kubernetes Service Account token via the Vault Kubernetes Auth Method. Vault verifies the token against the Kubernetes API and returns a scoped Vault client token. 2) Dynamic Credential Generation: Instead of reading static secrets, the application requests dynamic DB credentials from Vault's database secrets engine: `GET /v1/database/creds/order-service-role`. 3) Vault-Postgres Creation: Vault connects to PostgreSQL as an admin and dynamically creates a brand new, unique SQL user on the fly: `CREATE ROLE v_kub_order_17125... WITH PASSWORD 'xyz' VALID UNTIL '<1 hour>'; GRANT SELECT, INSERT ON orders TO ...;`. 4) Short-Lived Lease: Vault returns the dynamic username, password, and a Lease ID with a 1-hour TTL to the application. 5) Lease Renewal Daemon: A background thread in the application periodically renews the lease (`PUT /v1/sys/leases/renew`). If the pod crashes or is terminated, the lease is abandoned. 6) Automated Expiration: Once the lease expires without renewal, Vault automatically issues `DROP ROLE` in Postgres. If an attacker dumps application memory or logs, the leaked credentials become completely useless within minutes.",
        [
            "Authenticates pod identity with Vault via Kubernetes Service Account tokens",
            "Generates unique, short-lived database users dynamically via Vault's database secret engine",
            "Renews leases periodically and relies on automated user drops upon lease expiration"
        ],
        [
            "Recommends hardcoding root database credentials into Dockerfile environment variables"
        ]
    ),
    (
        "B68_5_13",
        "tradeoff",
        "medium",
        "tradeoff",
        ["API Security", "Caching"],
        "Redis / JWT Revocation",
        "Authorization Cache Invalidation under Immediate Privilege Revocation",
        "To optimize performance, an API gateway caches user authorization permissions (e.g., `user:123 -> [ROLE_ADMIN]`) in Redis for 15 minutes. An administrator immediately revokes the admin privileges of an employee whose account was compromised. What are the architectural tradeoffs between 'Instant Cache Invalidation via Invalidation Pub/Sub' versus 'Short-Lived Ephemeral Tokens with Bloom Filter Denylists'?",
        "1) Instant Cache Invalidation via Invalidation Events (Pub/Sub): Mechanism: When the admin revokes privileges, the identity service deletes the Redis cache key and broadcasts an invalidation event across Redis Pub/Sub to all API Gateway memory caches. Advantages: Instantaneous enforcement; the rogue user is blocked on their very next HTTP request within 5 milliseconds. Tradeoffs: Architectural coupling and reliability gaps. If an API Gateway node experiences a network hiccup or misses the Pub/Sub broadcast, it will continue serving cached admin permissions for the remainder of the 15-minute TTL. Requires every gateway instance to maintain active pub/sub listener sockets. 2) Short-Lived Ephemeral Tokens (e.g., 2-Minute Tokens) with Distributed Denylists: Mechanism: The system issues short-lived JWTs that expire in 120 seconds. For immediate emergency revocation, the ID of the revoked user or token is placed in an in-memory Bloom filter / distributed set denylist in Redis. Advantages: Highly resilient. Denylists only store actively revoked IDs (tiny memory footprint). If the denylist is lost, exposure is bounded strictly to the 120-second token lifetime. Tradeoffs: Slightly higher token refresh frequency on clients and small latency check against the revocation denylist on sensitive administrative routes.",
        [
            "Analyzes instant invalidation via Pub/Sub (sub-millisecond revocation vs risk of missed event broadcasts)",
            "Analyzes short-lived tokens with denylists (bounded 120s exposure window vs client refresh overhead)",
            "Evaluates tradeoffs between instantaneous security enforcement and distributed cache complexity"
        ],
        [
            "Claims authorization permissions cannot be revoked until the user voluntarily logs out"
        ]
    ),
    (
        "B68_5_14",
        "concept",
        "easy",
        "concept",
        ["API Security", "Zero Trust"],
        "SPIFFE / SPIRE / mTLS",
        "Service Identity via SPIFFE/SPIRE vs Static API Keys",
        "Why is using static API keys (e.g., `Authorization: Bearer static-secret-123`) for service-to-service communication considered an anti-pattern in modern cloud-native architectures, and how does SPIFFE/SPIRE provide cryptographic service identity?",
        "Anti-Patterns of Static API Keys: 1) Vulnerable to Leakage: Static keys are frequently committed to source control, leaked in debug logs, exposed in error traces, or captured in network packet dumps. 2) Never Rotated: Because rotating static keys requires synchronized configuration updates and restarts across dozens of microservices, teams rarely rotate them, leaving keys valid for years. 3) Lack of Provenance: An API key proves knowledge of a secret, not the physical identity of the calling software. Anyone who steals the key can impersonate the service from anywhere. How SPIFFE/SPIRE Solves Service Identity: 1) SPIFFE (Secure Production Identity Framework for Everyone): Defines a standardized URI format for service identity (e.g., `spiffe://example.com/ns/production/sa/payment-service`). 2) SPIRE (The SPIFFE Runtime Environment): Runs as a node daemon that attests the workload based on kernel and container metadata (verifying container image, namespace, cgroup, Linux UID). 3) Cryptographic SVIDs: SPIRE automatically issues and injects short-lived X.509 certificates (SVIDs) directly into the service process. Services authenticate mutually via mTLS. 4) Zero Management: Certificates expire every hour and are rotated automatically in memory without service restarts or static credentials.",
        [
            "Identifies static API keys as prone to leaks, difficult to rotate, and lacking verifiable workload provenance",
            "Defines SPIFFE/SPIRE as workload attestation based on kernel/container attributes issuing short-lived X.509 SVIDs",
            "Highlights automated in-memory certificate rotation over mTLS without static secret management"
        ],
        [
            "Claims SPIFFE is an encryption algorithm designed specifically for video game consoles"
        ]
    ),
    (
        "B68_5_15",
        "implement",
        "medium",
        "implement",
        ["Observability", "Distributed Tracing"],
        "OpenTelemetry / W3C Trace Context",
        "Asynchronous Trace Context Propagation across Message Brokers",
        "When an HTTP request triggers an asynchronous background job published to Kafka or RabbitMQ, downstream consumer spans often appear disconnected as root traces in Jaeger/Zipkin rather than child spans of the original HTTP request. How do you implement distributed trace context injection and extraction across asynchronous message boundaries using OpenTelemetry and W3C `traceparent` headers?",
        "Why Traces Break: OpenTelemetry trace context is stored in thread-local or coroutine context. When an HTTP handler publishes a message to a broker, the network message payload does not automatically inherit the memory context. When a consumer worker thread pulls the message minutes later, it has an empty trace context and naively starts a new root trace, breaking end-to-end trace visualization. Implementation of Asynchronous Context Propagation: 1) Producer Injection: Before publishing, use the OpenTelemetry propagator to inject the active span context into the message's metadata headers (e.g., Kafka Record Headers): `OpenTelemetry.getPropagators().getTextMapPropagator().inject(Context.current(), kafkaRecord.headers(), headerSetter)`. This injects the W3C standard `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01` header into the message. 2) Consumer Extraction: Inside the consumer worker loop, extract the context from the message headers before creating a span: `Context extractedContext = propagator.extract(Context.current(), kafkaRecord.headers(), headerGetter)`. 3) Span Link / Child Span: Create the consumer span with the extracted context as its parent: `tracer.spanBuilder('process_order').setParent(extractedContext).startSpan()`. For batch consumers, attach extracted contexts as Span Links (`addLink()`). Distributed tracing platforms can now visualize the complete causal chain from the initial web click through the message queue to final background database execution.",
        [
            "Identifies that thread-local trace contexts do not cross asynchronous network message boundaries automatically",
            "Injects W3C traceparent headers into message metadata on the producer side via OpenTelemetry propagators",
            "Extracts trace context from message headers on the consumer side and sets it as the parent span or span link"
        ],
        [
            "Suggests converting the entire application into a synchronous HTTP API to avoid message queues"
        ]
    ),
    (
        "B68_5_16",
        "explain",
        "medium",
        "explain",
        ["Observability", "Performance Tuning"],
        "Distributed Tracing / OpenTelemetry",
        "Decomposing Queue Wait Latency vs Processing Latency",
        "In a distributed background processing architecture, an end-to-end trace shows an asynchronous image processing task took 10 minutes to finish. However, the image processing algorithm itself takes only 200 milliseconds of CPU execution time. How do you structure OpenTelemetry spans to clearly decompose 'Queue Wait Latency' (time waiting in backlog) from 'Execution Processing Latency' in distributed tracing dashboards?",
        "If an engineer only records a single span around the consumer worker execution (`tracer.spanBuilder('process_image')`), the trace span duration will show 200ms. The 9 minutes and 59.8 seconds spent sitting in the queue backlog is completely invisible on the trace waterfall, leading engineers to mistakenly believe the system is fast when user experience is severely degraded. Proper Span Decomposition: 1) Publish Span: The producer creates a span `image_job.enqueue` recording the timestamp when the message was sent to the queue, injecting the trace context into message headers. 2) Enqueue Timestamp Attribute: The producer explicitly attaches an attribute: `messaging.message.enqueued_timestamp = now()`. 3) Consumer Extraction & Queue Span: When the worker picks up the job: A) Span 1 (`image_job.receive` / `queue_wait`): The worker creates a synthetic span starting from `enqueued_timestamp` to the current `now()`, labeled `messaging.operation = 'receive'`. This explicitly visualizes the 9m 59s queue backlog delay in the trace timeline. B) Span 2 (`image_job.process`): The worker creates a child span wrapping the actual 200ms image transcoding function, labeled `messaging.operation = 'process'`. 4) Observability Benefit: Dashboards immediately reveal that 99.9% of latency was queuing delay (indicating under-provisioned worker pools or consumer lag) rather than inefficient application transcoding code.",
        [
            "Explains that measuring only worker execution duration hides queue wait backlog delays",
            "Records enqueued_timestamp in message headers and creates explicit spans representing queue wait time",
            "Separates messaging.operation='receive' (queue backlog) from messaging.operation='process' (actual CPU work)"
        ],
        [
            "Claims distributed tracing cannot measure time spent in message queues"
        ]
    ),
    (
        "B68_5_17",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Observability", "Distributed Tracing"],
        "OpenTelemetry / Sampling",
        "Tail-Based Sampling vs Head-Based Sampling in Distributed Tracing",
        "At a scale of 100,000 requests per second, collecting 100% of distributed tracing spans generates terabytes of telemetry per hour, resulting in massive storage costs and network overhead. What are the architectural tradeoffs between 'Head-Based Sampling' (sampling at the edge gateway) versus 'Tail-Based Sampling' (sampling at an OpenTelemetry Collector)?",
        "Head-Based Sampling: 1) Mechanism: The decision to sample or drop a trace is made at the very beginning of the request (e.g., at the API Gateway or ingress proxy) before the request executes. A random percentage (e.g., 1% or 5%) is sampled; downstream services respect this decision via trace flags (`traceparent` sampled bit). 2) Advantages: Extremely lightweight, zero memory overhead, and requires no centralized telemetry buffering infrastructure. Downstream services immediately discard unsampled spans, saving CPU and network bandwidth. 3) Disadvantages: High Blind Spot Risk. Sampling decisions are made *before* the request fails. If an error, database deadlock, or p99 10-second latency spike occurs on an unsampled request, that critical failure trace is permanently lost. Tail-Based Sampling: 1) Mechanism: Downstream services collect 100% of spans and stream them to an OpenTelemetry Collector cluster. The Collector buffers all spans belonging to a trace in memory until the entire trace completes. It then evaluates the completed trace: 'Did this trace contain an HTTP 5xx error? Did duration exceed 2 seconds?' If yes, sample 100% of it; if normal 200 OK fast trace, sample only 0.1%. 2) Advantages: Perfect signal-to-noise ratio. Guarantees 100% capture of all production errors and tail latency outliers while discarding boring success traces. 3) Disadvantages: High infrastructure complexity and RAM cost. Collectors must maintain gigabytes of in-memory routing tables and trace buffers, and trace routing proxies must ensure all spans for the same `trace_id` reach the exact same Collector instance.",
        [
            "Defines Head-Based Sampling (decision made at ingress before execution, low overhead, drops critical errors)",
            "Defines Tail-Based Sampling (decision made after execution completes based on errors and latency thresholds)",
            "Analyzes Tail-Based tradeoffs: perfect capture of errors and tail latency vs collector memory buffering and routing complexity"
        ],
        [
            "Claims sampling means rounding all database numbers to the nearest integer"
        ]
    ),
    (
        "B68_5_18",
        "concept",
        "easy",
        "concept",
        ["Observability", "Metrics"],
        "Prometheus / High Cardinality",
        "High Cardinality Dimensions and Metric Storage Explosions",
        "Why is including high-cardinality values (such as `user_id`, `email`, or `order_id`) as label dimensions in Prometheus metrics (e.g., `http_requests_total{user_id=\"12345\"}`) considered an architectural anti-pattern, and what catastrophic failure mode does it cause in the monitoring infrastructure?",
        "Anti-Pattern Mechanism: In time-series databases like Prometheus, every unique combination of key-value label pairs creates an entirely new, distinct Time Series in memory and on disk. Cardinality Explosion: If an API serves 50 million unique users, adding `{user_id=\"...\"}` creates 50 million separate time series for that single metric. Failure Mode: 1) Memory Exhaustion (OOM): Prometheus maintains active time series chunks in RAM. 50 million time series consume tens of gigabytes of RAM within minutes, crashing the Prometheus server with Out-Of-Memory errors. 2) Inverted Index Churn: The time series database's head block and inverted index suffer severe write amplification, causing CPU thrashing and corrupting TSDB blocks. 3) Query Timeouts: PromQL queries (`sum(rate(http_requests_total[5m]))`) must scan and aggregate 50 million series, causing scrape timeouts and rendering alerting dashboards completely dead. Correct Architectural Practice: Reserve metrics labels strictly for low-cardinality, bounded enum values (e.g., `http_status_code`, `method`, `handler`, `region`). High-cardinality identifiers (`user_id`, `order_id`) belong exclusively in structured logs and distributed tracing spans.",
        [
            "Explains that unique label combinations create separate time series, causing cardinality explosions",
            "Identifies Prometheus memory exhaustion (OOM), index churn, and query timeouts as consequences",
            "Restricts metric labels to low-cardinality enums and routes high-cardinality identifiers (user_id) to logs and traces"
        ],
        [
            "Claims Prometheus can store infinite dimensions without using any computer memory"
        ]
    ),
    (
        "B68_5_19",
        "diagnose",
        "medium",
        "debugging",
        ["Observability", "Resilience"],
        "Distributed Systems / Microservices",
        "Detecting Cyclical Microservice Dependency Deadlocks",
        "During a deployment, a severe cascading outage occurs: Service A calls Service B, Service B calls Service C, and Service C calls Service A over synchronous HTTP RPCs. Under high traffic, all three services freeze simultaneously with 100% thread pool exhaustion. How do distributed tracing tools and dependency graphs detect this architectural cycle, and how do you break cyclical dependencies?",
        "Root Cause: Synchronous Dependency Cycles and Distributed Thread Deadlocks. When Service A calls B, Thread A1 blocks waiting for B. Service B calls C, blocking Thread B1. Service C calls back to Service A, requiring a new Thread A2. Under high concurrent traffic, all available worker threads in Service A's thread pool become occupied waiting for B (Thread A1 slots). When Service C attempts to call Service A to complete its work, Service A has zero free worker threads to accept the inbound call. Service C blocks forever, which keeps Service B blocked forever, which keeps Service A blocked forever. The entire cycle enters a distributed deadlock, freezing all three services. Detection: Distributed tracing tools (Jaeger, OpenTelemetry) generate Service Dependency Graphs from span parent-child relationships. Graph cycle detection algorithms (Tarjan's strongly connected components) immediately highlight the circular loop ($A \rightarrow B \rightarrow C \rightarrow A$). How to Break the Cycle: 1) Asynchronous Event Decoupling: Break the synchronous loop by converting the return call from Service C to Service A into an asynchronous message broker event (e.g., publishing `COperationCompleted` to Kafka), allowing Service C to finish and return immediately. 2) Re-architect Domain Boundaries: Extract the shared logic that Service C needs from Service A into an independent, lower-level shared Service D, preserving a strict Directed Acyclic Graph (DAG) of dependencies.",
        [
            "Diagnoses distributed thread deadlock: circular synchronous calls exhaust thread pools, causing mutual blocking",
            "Uses distributed tracing dependency graphs to identify circular dependency loops across services",
            "Breaks cycles by converting return calls to asynchronous messaging or extracting shared dependencies into a DAG"
        ],
        [
            "Suggests connecting the three servers with a circular Ethernet loop cable"
        ]
    ),
    (
        "B68_5_20",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Observability", "Resilience"],
        "Kubernetes / Health Probes",
        "Deep Health Checks vs Shallow Liveness/Readiness Probes",
        "Why is implementing 'Deep Health Checks' (where an application's `/healthz` endpoint executes live queries against downstream databases, Redis caches, and third-party APIs) considered a dangerous operational anti-pattern for Kubernetes Liveness probes, and what is the proper separation between Liveness and Readiness probes?",
        "The Deep Health Check Catastrophe: A Kubernetes 'Liveness Probe' asks a simple question: 'Is this process dead, stuck in an infinite loop, or deadlocked such that restarting the container will fix it?' If the liveness probe fails, Kubernetes immediately kills the container with `SIGKILL` and restarts it. If `/healthz` checks downstream database connectivity: 1) Cascading Cluster Collapse: When the shared PostgreSQL database experiences a transient 10-second latency spike or network hiccup, the liveness probes for all 200 microservice pods fail simultaneously. 2) Restart Storm: Kubernetes kills and restarts all 200 pods at the exact same moment. 3) Thundering Herd: As all 200 pods reboot simultaneously, they execute startup initialization, establish thousands of fresh database connections, and warm caches, completely crushing the already struggling database and turning a 10-second blip into a total company-wide outage. Proper Architectural Separation: 1) Liveness Probe (Shallow Only): Must be strictly internal and shallow (`/livez`). Verifies only that the local application process is running, its event loop is not deadlocked, and local memory is responsive. It must NEVER make external network calls. 2) Readiness Probe (Traffic Routing): Verifies if the pod is currently capable of handling traffic (`/readyz`). Can check local warm-up status. If downstream dependencies are unavailable, failing the readiness probe simply stops the load balancer from routing traffic to this pod without restarting the process.",
        [
            "Identifies that deep liveness probes trigger cluster-wide pod restart storms during transient dependency hiccups",
            "Explains that rebooting pods simultaneously amplifies database overload with thousands of reconnect attempts",
            "Enforces shallow, local-only liveness probes (/livez) while reserving readiness probes (/readyz) for traffic routing decisions"
        ],
        [
            "Claims health checks should be disabled completely in all production environments"
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 5).")
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
    print("POST-BATCH AUDIT PART 5")
    print("========================================")
    print(f"Batch: 68 Part 5")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
