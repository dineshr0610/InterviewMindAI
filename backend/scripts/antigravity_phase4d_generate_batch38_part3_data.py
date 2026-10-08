import os

ROLE = "Backend Developer"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b7": ("Performance", "Relational", "SQL", ["Backend Developer", "Database Developer"]),
    "b8": ("Performance", "Debugging", "Monitoring", ["Backend Developer"]),
    "b9": ("API Design", "Authentication", "Security", ["Backend Developer", "Full Stack Developer"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    (
        "b7",
        "diagnose",
        "hard",
        "problem_solving",
        ["Databases", "Performance"],
        "Your backend API endpoint for retrieving a list of authors and their respective books is experiencing severe latency. Database CPU is fine, but the APM shows the endpoint makes 101 separate database queries to serve a single request. How do you diagnose and resolve this N+1 query problem hidden behind your modern ORM?",
        "This is the classic N+1 query problem, common with lazy-loading ORMs (like Hibernate, SQLAlchemy, Entity Framework, or Prisma). The ORM executes 1 query to fetch a list of N authors, and then as the application iterates through the authors in a loop to access their books, the ORM dynamically executes N additional individual queries to fetch the books for each author. This results in massive network latency round-trips. To diagnose, examine SQL query logs or APM trace spans to identify repeating identical queries varying only by foreign key ID. To resolve it at the application layer, instruct the ORM to use 'Eager Loading' (e.g., using `JOIN FETCH` in JPA, `.joinedload()` in SQLAlchemy, or `.include()` in Prisma). This forces the ORM to execute a single, optimized SQL `JOIN` (or two batch queries using a `WHERE IN` clause) to retrieve the authors and all related books in one trip, drastically reducing latency.",
        [
            "Identifies the mechanics of the N+1 problem: 1 query for parents, N queries for lazy-loaded children inside a loop.",
            "Diagnoses via SQL logs or APM traces showing repeating identical queries.",
            "Resolves using Eager Loading (JOIN fetching) or batch/subselect loading at the ORM layer."
        ],
        [
            "Suggests adding more database indexes, which does not fix the 100 network round-trips.",
            "Recommends writing a raw SQL stored procedure as the only way to join tables."
        ]
    ),
    (
        "b7",
        "optimize",
        "medium",
        "problem_solving",
        ["Databases", "Performance"],
        "A paginated backend API endpoint for a multi-million row table uses standard `OFFSET` and `LIMIT` parameters. As users navigate to deeper pages (e.g., page 10,000), the queries become extremely slow and time out. How do you optimize this pagination performance?",
        "Standard `OFFSET M LIMIT N` pagination forces the relational database engine to compute, fetch, and discard M rows before returning the N rows required for the page. For deep pages (high OFFSET), this incurs massive disk I/O and CPU overhead. To optimize deep pagination, switch to Keyset Pagination (also known as Cursor-based Pagination or the Seek Method). Instead of an offset, the client provides a cursor based on the last seen row (e.g., `last_id = 1500`). The backend executes a query using a `WHERE` clause on an indexed column: `SELECT * FROM table WHERE id > 1500 ORDER BY id ASC LIMIT 10`. Because the database uses the B-Tree index to instantly jump to the cursor value, the query execution time remains constant (O(1) relative to depth) regardless of how deep the user paginates. This approach is highly efficient but requires a deterministic, indexed sort column.",
        [
            "Identifies the flaw in OFFSET/LIMIT requiring the database to scan and discard rows.",
            "Proposes Keyset/Cursor pagination utilizing a `WHERE` clause on an indexed column.",
            "Explains that cursor pagination provides O(1) performance for deep pages."
        ],
        [
            "Suggests caching every single page in Redis.",
            "Claims adding an index to OFFSET fixes the performance issue."
        ]
    ),
    (
        "b7",
        "compare",
        "easy",
        "conceptual",
        ["Databases", "Concurrency"],
        "When configuring the database connection for a backend service handling financial transactions, how does the Read-Committed isolation level differ from the Serializable isolation level, and what are the tradeoffs?",
        "Read-Committed is the default isolation level in many databases (like PostgreSQL). It guarantees that a transaction only sees data that has been committed by other transactions, preventing 'Dirty Reads'. However, it is susceptible to 'Non-Repeatable Reads' (data changing if read twice in the same transaction) and 'Phantom Reads' (new rows appearing). It offers high concurrency and performance with minimal locking. Serializable is the strictest isolation level. It guarantees that the outcome of executing concurrent transactions is identical to if they were executed sequentially, one after the other. It completely prevents dirty reads, non-repeatable reads, and phantom reads. The tradeoff is severe performance degradation; Serializable enforces aggressive locking (or high rollback rates in MVCC systems) which drastically reduces concurrency and forces the backend application to handle frequent serialization failure retries. For most applications, Read-Committed with explicit application-level locking (optimistic/pessimistic) is preferred over strict Serializable.",
        [
            "Accurately defines Read-Committed (prevents dirty reads, allows phantom reads) and Serializable (highest strictness, sequential execution).",
            "Highlights the tradeoff: Serializable prevents all anomalies but severely limits concurrency and performance."
        ],
        [
            "Claims Serializable is the fastest isolation level because it doesn't need to check locks.",
            "Confuses isolation levels with disk persistence (syncing to disk)."
        ]
    ),
    (
        "b7",
        "diagnose",
        "medium",
        "debugging",
        ["Databases", "Concurrency"],
        "Your backend processes bulk updates. You are seeing intermittent `Deadlock found when trying to get lock` errors from the relational database. Both concurrent transactions are updating the exact same set of rows. How do you diagnose and fix this?",
        "Database deadlocks occur when two concurrent transactions acquire exclusive locks on rows in a different order. For example, Transaction A locks Row 1 and waits for Row 2, while Transaction B locks Row 2 and waits for Row 1. The database detects the circular dependency and forcefully aborts one transaction to break the deadlock. To diagnose, inspect the database engine's deadlock logs (e.g., `SHOW ENGINE INNODB STATUS` in MySQL) to identify the conflicting queries and the order of locks acquired. To fix this at the application layer, enforce a consistent ordering rule for all bulk operations. Before executing the `UPDATE` statements, the backend application must sort the target records by a unique identifier (like the Primary Key ID). If all concurrent transactions consistently update rows in ascending ID order, Transaction B will block waiting for Row 1 rather than locking Row 2, completely eliminating the possibility of a circular deadlock.",
        [
            "Identifies the root cause: concurrent transactions locking rows in different, conflicting orders.",
            "Proposes the solution: sorting the target rows by a deterministic key (e.g., Primary Key) in application logic before executing bulk updates."
        ],
        [
            "Suggests disabling database locking entirely.",
            "Recommends wrapping the updates in an infinite retry loop without addressing the underlying order."
        ]
    ),
    (
        "b7",
        "architecture",
        "medium",
        "architectural",
        ["Databases", "Scalability"],
        "You are scaling a backend API by deploying a Primary database for writes and multiple asynchronous Read-Replicas for queries. However, users are complaining that immediately after they update their profile, the page reloads and shows the old data. How do you architect a routing strategy to solve this staleness?",
        "This issue is caused by replication lag; the backend writes to the Primary, but the subsequent read is routed to a Replica that hasn't received the asynchronous update yet. To solve this, implement a 'Read-Your-Writes' consistency strategy at the application layer. 1) Pinning/Sticky Routing: When a user performs a write operation, the backend sets a cookie or cache flag marking the user as 'recently modified'. For a short window (e.g., 2-5 seconds, comfortably exceeding maximum replication lag), the backend explicitly routes all read queries from that specific user directly to the Primary database. All other users read from the Replicas. 2) Versioning/Token verification: The write operation returns a sequence number or timestamp. Subsequent read requests pass this token. If the routed replica's state is older than the token, the backend falls back to reading from the Primary. This balances read scalability while guaranteeing monotonic consistency for the mutating user.",
        [
            "Identifies asynchronous replication lag as the cause of the stale reads.",
            "Architects a 'Read-Your-Writes' strategy (e.g., pinning the user to the Primary for a short time after a write, or verifying sequence tokens)."
        ],
        [
            "Suggests switching the database to synchronous replication, ignoring the massive write latency penalty.",
            "Advises putting a `sleep(5000)` in the frontend before reloading."
        ]
    ),
    (
        "b8",
        "diagnose",
        "hard",
        "problem_solving",
        ["Performance", "Architecture"],
        "A data ingestion backend processing large JSON payloads (50MB+) experiences severe CPU spikes and extreme garbage collection overhead, bottlenecking the entire server. Profiling shows network I/O is minimal. How do you diagnose and resolve this serialization bottleneck?",
        "When handling massive JSON payloads, standard tree-based deserialization libraries (like default Jackson `ObjectMapper` or `JSON.parse`) parse the entire document into memory at once. This creates an enormous memory footprint (often 3-5x the physical payload size) and generates millions of short-lived objects, triggering continuous, aggressive garbage collection (GC thrashing) and monopolizing the CPU. To diagnose, use a CPU/Memory profiler to identify the exact serialization library classes dominating the CPU cycles and heap allocations. To resolve this, switch from tree-model (DOM-style) parsing to streaming (event-driven) parsing. Libraries like Jackson's `JsonParser` (Streaming API) or Gson's `JsonReader` process the JSON stream token by token (or chunk by chunk) incrementally. This approach operates with a minimal, constant memory footprint and avoids large object tree allocations, completely eliminating the GC thrashing and CPU spikes.",
        [
            "Identifies that tree-model JSON parsing loads the entire payload into memory, causing massive object allocations and GC thrashing.",
            "Recommends diagnosing via CPU/Memory profilers focusing on deserialization classes.",
            "Resolves the issue by implementing streaming/event-driven JSON parsing (incremental tokenization)."
        ],
        [
            "Suggests adding more database indexes to speed up the ingestion.",
            "Recommends zipping the JSON before parsing it in memory."
        ]
    ),
    (
        "b8",
        "optimize",
        "hard",
        "best_practices",
        ["Performance", "Architecture"],
        "Your Java backend handles real-time trading with a strict 20ms SLA. However, the application occasionally freezes for 500ms due to 'Stop-The-World' Garbage Collection pauses. How do you optimize JVM GC to eliminate these latency spikes?",
        "Traditional generational garbage collectors (like Parallel GC or standard CMS) pause all application threads ('Stop-The-World') during major collections to compact the heap and move objects safely. For a latency-sensitive application with strict SLAs, these pauses are unacceptable. To optimize, switch to a modern, low-latency concurrent Garbage Collector like ZGC (Z Garbage Collector) or Shenandoah, or optimize G1GC. ZGC and Shenandoah perform all expensive work (marking, relocation, compaction) concurrently with application threads, guaranteeing sub-millisecond pause times regardless of the heap size. If restricted to G1GC, tune the target pause time (`-XX:MaxGCPauseMillis=20`), which forces the GC to work in smaller, more frequent increments. Furthermore, at the application code level, reduce object allocation rates (e.g., utilize object pooling for high-frequency buffers, or use primitive arrays instead of wrapped objects) to minimize the pressure on the young generation.",
        [
            "Identifies 'Stop-The-World' pauses as the root cause of the latency spikes.",
            "Recommends migrating to modern low-latency GCs like ZGC or Shenandoah.",
            "Suggests tuning G1GC targets or reducing application-level object allocations to relieve heap pressure."
        ],
        [
            "Suggests increasing the heap size to 100GB to 'delay' the garbage collection, which actually results in significantly longer pauses when they inevitably occur.",
            "Claims Garbage Collection cannot be tuned."
        ]
    ),
    (
        "b8",
        "diagnose",
        "medium",
        "debugging",
        ["Performance", "API Design"],
        "Your backend integrates with a third-party payment API. Suddenly, your API Gateway reports a massive spike in 504 Gateway Timeouts for your service, and monitoring shows all your application threads are stuck. The third-party API is experiencing an unannounced partial outage. How do you diagnose the thread starvation, and how should you have prevented it?",
        "The third-party API is failing silently; instead of returning a 5xx error or connection refusal, it is accepting TCP connections but indefinitely hanging, sending no data. Because the backend's HTTP client was misconfigured without strict socket read timeouts, the application threads initiate the request and block indefinitely waiting for a response. As more requests arrive, all available application threads or connection pool slots become permanently blocked, resulting in total thread starvation. The reverse proxy/Gateway eventually gives up waiting for your backend and returns 504. To diagnose, capture a thread dump (e.g., `jstack` or `/debug/pprof/goroutine`) which will clearly show hundreds of threads in a `WAITING` state on network socket reads associated with the third-party client. To prevent this, every outbound network call must have strictly enforced connection timeouts and read timeouts. Furthermore, the call should be wrapped in a Circuit Breaker to quickly fail fast during degraded third-party states.",
        [
            "Identifies the root cause as missing read timeouts on the HTTP client causing indefinite thread blocking.",
            "Recommends taking a thread dump to observe threads stuck in socket read states.",
            "Prescribes enforcing strict connection/read timeouts and implementing a Circuit Breaker."
        ],
        [
            "Assumes the backend's database is slow.",
            "Suggests the solution is to increase the API Gateway's timeout limit."
        ]
    ),
    (
        "b8",
        "optimize",
        "medium",
        "problem_solving",
        ["Performance", "Distributed Systems"],
        "In a distributed microservices environment, the 99th percentile (p99) tail latency for a critical read operation is unacceptably high (e.g., 2 seconds), even though the median latency is fast (50ms). How can you optimize the backend using Hedged Requests (speculative retries) to crush this tail latency?",
        "Tail latency often arises from intermittent network congestion, degraded hardware, or GC pauses on a specific distributed node. Instead of waiting the full timeout to retry, 'Hedged Requests' (or speculative retries) proactively mask this variance. When the backend application initiates a critical read request to a distributed service, it waits for a short threshold (e.g., the 95th percentile latency, like 100ms). If the first request hasn't responded by then, the backend fires a second identical request to a *different* replica or node in the cluster, without canceling the first. The application accepts whichever response arrives first and cancels the pending request. Because the probability of two independent nodes both experiencing p99 latency simultaneously is exponentially small, hedging drastically reduces the p99 latency observed by the client. This technique is strictly limited to idempotent, safe read operations to avoid mutating state twice, and should be carefully throttled to prevent capacity amplification during major outages.",
        [
            "Explains the mechanics of Hedged Requests: firing a second request to a different node if the first doesn't respond within a fast threshold.",
            "Explains how taking the first successful response mathematically reduces tail (p99) latency.",
            "Crucially identifies that this is only safe for idempotent/read operations."
        ],
        [
            "Confuses hedged requests with standard exponential backoff retries upon failure.",
            "Recommends executing hedged requests for credit card transactions (mutating state)."
        ]
    ),
    (
        "b8",
        "compare",
        "medium",
        "conceptual",
        ["Performance", "Observability"],
        "When investigating poor performance in a modern, distributed backend, what is the conceptual difference between Application-level Profiling (e.g., CPU/Memory sampling) and Distributed Tracing (e.g., OpenTelemetry), and when should you use each?",
        "Distributed Tracing (using OpenTelemetry, Jaeger, or Datadog) provides macro-level observability across the entire system. It injects context headers (Trace IDs) into incoming requests and propagates them across network boundaries. It visually charts the lifecycle of a request as a waterfall of spans, allowing you to instantly identify *which* microservice, database, or external API call is causing the latency bottleneck in a distributed chain. Application-level Profiling (using tools like JFR, pprof, or async-profiler) provides micro-level observability within a single process. It samples thread stacks, CPU instruction execution, and memory allocations at a high frequency to show you exactly which lines of code, algorithms, or garbage collection events are consuming resources. You use Distributed Tracing first to isolate the bottleneck to a specific service or network hop, and then use Profiling to dive deep into that specific service's codebase to fix algorithmic inefficiencies.",
        [
            "Contrasts Tracing (macro-level, cross-network, span waterfalls) with Profiling (micro-level, intra-process, CPU/Memory code execution).",
            "Identifies the correct workflow: Trace to find the slow service, Profile to fix the slow code within that service."
        ],
        [
            "Claims that tracing and profiling are synonymous.",
            "Suggests using a CPU profiler to find network latency issues in external microservices."
        ]
    ),
    (
        "b8",
        "diagnose",
        "hard",
        "problem_solving",
        ["Debugging", "Networking"],
        "Your backend service running on Linux crashes randomly with the error `java.net.SocketException: Too many open files` (or equivalent `EMFILE` in Node/Python). CPU and memory are stable. How do you diagnose the root cause, and what application code pattern typically causes this descriptor leak?",
        "The 'Too many open files' error occurs when the backend process exhausts the operating system's file descriptor limit (defined by `ulimit -n`). In Linux, every network connection (socket), file, and pipe consumes a file descriptor. To diagnose, find the process ID (PID) and run `lsof -p <PID>` to inspect the active descriptors. If the list is dominated by network sockets in `ESTABLISHED` or `CLOSE_WAIT` states connected to a specific downstream service, you have a socket leak. At the application code level, this is almost always caused by failing to properly close HTTP client connections or response bodies. When developers make an outbound HTTP request but fail to explicitly close the response stream in a `finally` block (or fail to utilize language constructs like `try-with-resources` or `defer`), the underlying TCP socket is never released back to the OS or connection pool. Fixing the leak requires ensuring all network streams are deterministically closed.",
        [
            "Explains that network sockets consume file descriptors, leading to `EMFILE`.",
            "Suggests using `lsof` or `/proc/<PID>/fd` to diagnose the nature of the leaked descriptors.",
            "Identifies unclosed HTTP response streams / missing `finally` blocks as the primary code-level root cause."
        ],
        [
            "Assumes the application is writing too many log files to disk without checking sockets.",
            "Suggests infinitely increasing the OS `ulimit` as the permanent solution without fixing the code leak."
        ]
    ),
    (
        "b9",
        "architecture",
        "hard",
        "architectural",
        ["API Design", "Security"],
        "You are architecting a stateless session management system using JSON Web Tokens (JWT) for a fleet of backend microservices. Since JWTs are stateless, how do you address token revocation (e.g., immediate logout or compromised accounts) and protect against Cross-Site Request Forgery (CSRF)?",
        "Because JWTs are self-contained and verified locally via cryptography, they cannot be 'deleted' from the server like stateful session IDs. To handle revocation, architect a hybrid approach: keep the JWT expiry (TTL) very short (e.g., 15 minutes) and issue a long-lived, opaque Refresh Token stored securely in a central database. When a user logs out, revoke the Refresh Token in the database. For critical, immediate revocation of the short-lived JWT, implement a highly performant Redis-based Denylist (blacklist) at the API Gateway, storing the compromised JWT's `jti` (JWT ID) until its natural expiry time. To protect against CSRF (if tokens are stored in cookies), configure the HTTP response with `Set-Cookie: HttpOnly; Secure; SameSite=Strict`. The `SameSite` attribute instructs the browser not to attach the cookie to cross-origin requests. Alternatively, use the Double Submit Cookie pattern or store the JWT in memory (though this exposes it to XSS).",
        [
            "Addresses revocation by combining short-lived JWTs, long-lived refresh tokens, and a Redis-based Denylist/Blacklist for immediate invalidation.",
            "Addresses CSRF protection by specifying `SameSite=Strict` for cookies or utilizing Anti-CSRF tokens."
        ],
        [
            "Claims JWTs can simply be deleted from the database.",
            "Ignores CSRF entirely, assuming JWTs magically prevent it."
        ]
    ),
    (
        "b9",
        "optimize",
        "medium",
        "best_practices",
        ["API Design", "Security"],
        "In a microservices architecture, multiple backend services must validate incoming authentication tokens. Querying a central Identity Provider (IdP) for every request creates a massive bottleneck. How do you optimize token validation using asymmetric JWT signing?",
        "To eliminate the central bottleneck, the backend must transition to decentralized, stateless token validation. The Identity Provider signs the JWT using an asymmetric cryptographic algorithm like RSA (e.g., RS256). The IdP holds the Private Key, which is exclusively used to sign the tokens. The corresponding Public Key is made available to all microservices, typically via a standard JWKS (JSON Web Key Set) endpoint hosted by the IdP. When a request hits a microservice, the service downloads the Public Key (and caches it in memory). It then uses this Public Key to cryptographically verify the signature of the incoming JWT. Because asymmetric verification requires no network round-trip to the IdP, the microservice can validate the token's authenticity, integrity, and claims entirely locally in microseconds, massively optimizing authentication throughput.",
        [
            "Identifies asymmetric cryptography (e.g., RS256) using private/public key pairs.",
            "Explains that the IdP signs with the private key, while microservices verify locally using cached public keys (JWKS).",
            "Highlights that local verification eliminates network round-trips to the IdP."
        ],
        [
            "Suggests sharing a symmetric secret key (HS256) across all microservices, which is a massive security risk.",
            "Suggests putting a Redis cache in front of the IdP but still validating over the network."
        ]
    ),
    (
        "b9",
        "diagnose",
        "medium",
        "debugging",
        ["API Design", "Security"],
        "Your backend authorization server issues a JWT. Immediately after receiving it, the client sends it to a backend resource server, which sporadically rejects it with a 401 Unauthorized error indicating the token is 'not yet valid'. A minute later, the exact same token succeeds. What is the root cause and how do you fix it?",
        "This is a classic manifestation of Clock Skew across distributed servers. When the Authorization Server issues the JWT, it includes standard time-based claims: `iat` (Issued At), `exp` (Expiration Time), and `nbf` (Not Before). If the clock on the Resource Server is slightly behind the clock on the Authorization Server, the Resource Server evaluates the `nbf` or `iat` claim, sees a timestamp that is technically in the 'future' according to its local time, and correctly rejects the token as not yet valid. A minute later, when local time catches up, the token is accepted. To fix this at the application layer, configure the JWT validation library on the resource servers to allow a small 'leeway' or 'clock skew' window (typically 30-60 seconds) when evaluating time claims. Operationally, ensure all backend instances synchronize their system clocks using NTP (Network Time Protocol).",
        [
            "Identifies Clock Skew between the issuing server and the validating server as the root cause.",
            "Explains how the `nbf` (Not Before) or `iat` claims fail validation if evaluated against a slower clock.",
            "Recommends configuring a leeway/tolerance window in the JWT library and syncing clocks via NTP."
        ],
        [
            "Assumes the network latency is causing the token to expire.",
            "Recommends deleting the expiration claims entirely, destroying token security."
        ]
    ),
    (
        "b9",
        "compare",
        "easy",
        "conceptual",
        ["API Design", "Security"],
        "When integrating backend security, what is the primary difference in use case between the OAuth 2.0 Authorization Code flow and the Client Credentials flow?",
        "The OAuth 2.0 flows serve fundamentally different identity paradigms. The Authorization Code flow (often with PKCE) is used for delegated user authorization. It involves a human user interacting with a browser to authenticate with an Identity Provider, grant consent, and authorize a client application to access resources on their behalf. The identity represented by the token is the human user. The Client Credentials flow is strictly for machine-to-machine (backend-to-backend) communication where there is no human user involved. A backend service securely authenticates itself to the Identity Provider using its own credentials (a Client ID and Client Secret) to obtain an access token. The identity represented by the token is the backend service itself. You use Authorization Code for frontend-to-backend user sessions, and Client Credentials for internal microservice or cron job integrations.",
        [
            "Contrasts Authorization Code as user-centric, requiring human interaction and consent.",
            "Contrasts Client Credentials as machine-to-machine, using secrets without human involvement."
        ],
        [
            "Claims Client Credentials is for storing user passwords safely.",
            "Confuses the flows, suggesting users should type in a Client ID and Secret to log in."
        ]
    ),
    (
        "b9",
        "architecture",
        "medium",
        "architectural",
        ["API Design", "Security"],
        "You are designing the authorization layer for a complex B2B backend platform. Customers require policies like 'Employees can only edit documents created in their specific department during business hours'. Why would a traditional Role-Based Access Control (RBAC) system fail here, and how does Attribute-Based Access Control (ABAC) solve this?",
        "Role-Based Access Control (RBAC) grants permissions based strictly on static roles assigned to a user (e.g., 'Admin', 'Editor'). Implementing complex, dynamic conditions (like department matching or time-of-day restrictions) in RBAC requires an exponential explosion of hyper-specific roles (e.g., 'Editor_Sales_Daytime', 'Editor_Engineering_Night'), which becomes impossible to manage and scales poorly. Attribute-Based Access Control (ABAC) solves this by evaluating dynamic policies against attributes of the User (e.g., department=Sales), the Resource (e.g., document_department=Sales), the Action (e.g., edit), and the Environment (e.g., time=14:00, IP_address). The backend authorization engine (such as OPA - Open Policy Agent) evaluates these attributes at runtime against logical rules (e.g., `Allow IF user.department == resource.department AND env.time < 17:00`). This completely decouples authorization logic from static roles, providing infinite, fine-grained flexibility for complex B2B environments.",
        [
            "Explains that RBAC fails due to 'role explosion' when attempting to handle dynamic or contextual conditions.",
            "Describes how ABAC evaluates policies at runtime using attributes of the User, Resource, and Environment, easily accommodating dynamic rules."
        ],
        [
            "Claims RBAC is superior because ABAC requires too much database storage.",
            "Fails to articulate what the 'Attributes' in ABAC actually are."
        ]
    )
]
