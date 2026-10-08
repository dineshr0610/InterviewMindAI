"""Batch 13 question content (Backend Developer). Antigravity-native, no Gemini API."""

ROLE = "Backend Developer"

BUCKET_KEYS = {
    "AP_DS": ("API Design", "REST", "HTTP", ["Full Stack Developer"]),
    "AU_AT": ("Security", "Authentication", "JWT", ["Full Stack Developer", "Security Engineer"]),
    "DB_RL": ("Databases", "Relational", "SQL", ["Database Developer"]),
    "CC_CA": ("Caching", "Distributed Caching", "Redis", ["DevOps / Cloud Engineer"]),
    "MS_AY": ("Messaging", "Queues", "RabbitMQ", ["Data Engineer"]),
    "MC_SV": ("Architecture", "Microservices", "System Design", ["DevOps / Cloud Engineer", "Architecture"]),
    "CN_CN": ("Concurrency", "Thread Safety", "Java/Go/Python", ["Performance Engineer"]),
    "RL_FT": ("Reliability", "Fault Tolerance", "System Design", ["Architecture", "DevOps / Cloud Engineer"]),
    "PR_PF": ("Performance", "Bottlenecks", "System Design", ["Performance Engineer"]),
    "OB_LG": ("Observability", "Logging & Metrics", "Monitoring", ["DevOps / Cloud Engineer"]),
}

Q = [
# ---------------- AP_DS ----------------
("AP_DS", "fundamentals", "easy", "concept", ["HTTP"],
 "When designing a REST API, what is the difference between a PUT and a PATCH request?",
 "PUT is used to completely replace an existing resource with the provided payload. PATCH is used to apply partial modifications to a resource, updating only the specific fields provided in the payload while leaving others intact.",
 ["PUT replaces the entire resource", "PATCH applies partial updates", "Both modify existing resources"],
 ["Says PUT is for creation and PATCH is for deletion"]),

("AP_DS", "implement", "medium", "implementation", ["Pagination"],
 "How would you approach designing an API endpoint that supports robust cursor-based pagination for a high-velocity feed?",
 "I would design the API to accept a `cursor` query parameter (e.g., an encoded string representing a timestamp and unique ID) and a `limit`. The response would include the data items and a `next_cursor` field. This approach prevents data drift (duplicates or skips) that occurs with offset-based pagination when new items are rapidly inserted.",
 ["Accept cursor and limit parameters", "Return next_cursor in response", "Prevents data drift from rapid inserts"],
 ["Use standard page and offset query parameters"]),

("AP_DS", "debug", "hard", "debugging", ["Idempotency"],
 "You notice that an idempotent API endpoint for creating orders occasionally results in duplicate rows in the database during high-traffic spikes. How do you resolve this?",
 "The client is likely retrying the request before the first one finishes due to timeouts. Implement an Idempotency-Key header. The backend should atomically check if the key exists in a cache/database constraint before processing. If it's already processing, return a 409 Conflict or a 202 Accepted; if completed, return the cached successful response.",
 ["Use an Idempotency-Key header", "Atomically check/lock the key before processing", "Return cached response for duplicates"],
 ["Just delete the duplicates in a cron job later"]),

("AP_DS", "tradeoff", "medium", "tradeoff", ["Data Modeling"],
 "What tradeoffs exist between embedding related resources directly in an API response versus returning a list of IDs to be fetched separately?",
 "Embedding resources reduces the number of HTTP requests (avoiding under-fetching), which is great for high-latency mobile clients, but it increases payload size and backend complexity (over-fetching). Returning IDs keeps the payload small and cacheable but forces the client to make multiple round-trips (N+1 problem).",
 ["Embedding reduces round trips but increases payload", "IDs keep payload small but increase requests", "Caching implications"],
 ["Embedding is always the wrong choice"]),

("AP_DS", "scenario", "medium", "scenario", ["Error Handling"],
 "A service begins returning 429 Too Many Requests errors to a critical client. How would you design a retry mechanism in the client, and what headers should the API provide to help?",
 "The client should implement exponential backoff with jitter to retry the request without overwhelming the server. The backend API should provide a `Retry-After` header indicating exactly how many seconds the client must wait before making another request.",
 ["Exponential backoff with jitter on the client", "Provide a Retry-After header from the API", "Respect the API's rate limits"],
 ["Retry infinitely in a tight while loop"]),

# ---------------- AU_AT ----------------
("AU_AT", "explain", "easy", "concept", ["OAuth"],
 "Explain the purpose of a Refresh Token in a standard OAuth2 / JWT authentication flow.",
 "A Refresh Token is a long-lived credential used to obtain a new short-lived Access Token (JWT) when the original one expires. This enhances security because if a short-lived Access Token is stolen, it is only valid for a brief period, while the Refresh Token is stored securely and can be revoked.",
 ["Obtain new short-lived Access Tokens", "Enhances security by limiting Access Token lifespan", "Can be revoked centrally"],
 ["It is used to refresh the browser UI"]),

("AU_AT", "tradeoff", "medium", "tradeoff", ["Sessions"],
 "What are the tradeoffs of storing session state in a centralized Redis cluster versus issuing stateless JWTs to clients?",
 "Redis sessions offer absolute control, immediate revocation, and smaller client payloads, but require a database lookup on every request, adding latency and infrastructure cost. Stateless JWTs eliminate the database lookup (scaling infinitely), but cannot be instantly revoked before expiration and increase the HTTP header payload size.",
 ["Redis: strict control/revocation, but adds DB latency", "JWT: stateless/scalable, but hard to revoke", "JWT increases payload size"],
 ["JWTs are stored in Redis"]),

("AU_AT", "scenario", "hard", "scenario", ["Revocation"],
 "A compromised stateless JWT is actively being used by an attacker, and it has 2 hours left before expiration. How would you architect a system to revoke it immediately?",
 "Since the JWT is stateless, you cannot simply delete a session. You must implement a token blocklist (denylist) in a fast, in-memory store like Redis. The backend API gateway must check this Redis blocklist on every request. Alternatively, you can rotate the signing key, though this invalidates all current tokens for all users.",
 ["Implement a token blocklist in Redis", "Check blocklist on every authenticated request", "Rotate signing keys as a nuclear option"],
 ["Delete the token from the user's browser"]),

("AU_AT", "debug", "medium", "debugging", ["JWT"],
 "An application experiences sudden logout issues because the JWT signature validation is failing on one specific API server instance. What is the most likely cause?",
 "That specific server instance likely has an incorrect, rotated, or missing JWT secret/public key in its environment variables, causing it to reject perfectly valid tokens signed by the other instances. It could also be an issue with clock skew on that particular server causing premature expiration.",
 ["Mismatched JWT secret/key on that instance", "Environment variable misconfiguration", "Server clock skew"],
 ["The database is down"]),

("AU_AT", "implement", "hard", "implementation", ["RBAC"],
 "How would you design a secure, fine-grained Role-Based Access Control (RBAC) system for a multi-tenant B2B SaaS application?",
 "I would model roles and permissions independently. A tenant has users, and a user is assigned a Role within that specific Tenant. The JWT would encode the `tenant_id` and the `role`. The backend authorization middleware would read the JWT, look up the Role's specific permissions, and verify that the user has the required permission for the specific `tenant_id` resource being accessed.",
 ["Separate Roles and Permissions", "Map Users to Roles per Tenant", "Enforce tenant_id isolation in middleware"],
 ["Just put 'is_admin=true' in the token"]),

# ---------------- DB_RL ----------------
("DB_RL", "fundamentals", "easy", "concept", ["Architecture"],
 "What is a database connection pool, and why is it necessary for a backend application?",
 "A connection pool is a cache of pre-established database connections maintained by the backend. It is necessary because establishing a new TCP connection and authenticating with a database for every single request is extremely slow and resource-intensive. Reusing connections dramatically improves latency and throughput.",
 ["Cache of pre-established database connections", "Creating new connections is slow/expensive", "Reusing connections improves performance"],
 ["It pools data rows in memory to avoid queries"]),

("DB_RL", "scenario", "medium", "scenario", ["Performance"],
 "A production API experiences high latency because a backend service is opening a new database connection for every single HTTP request. How do you re-architect this?",
 "Implement a database connection pooler (like HikariCP for Java, pgBouncer for PostgreSQL, or a built-in ORM pool). Configure the application to borrow a connection from the pool at the start of a request and return it immediately after the query finishes, capping the maximum number of connections to protect the database.",
 ["Implement a connection pooler (e.g., pgBouncer, HikariCP)", "Borrow and return connections per request", "Cap maximum concurrent connections"],
 ["Increase the database RAM"]),

("DB_RL", "debug", "hard", "debugging", ["ORM"],
 "You notice that an endpoint suffers from the N+1 query problem, but it's hidden behind a complex ORM abstraction. How do you diagnose and fix the performance bottleneck?",
 "Diagnose by enabling SQL query logging in the ORM or using an APM tool to observe a single request emitting hundreds of queries. Fix it by explicitly instructing the ORM to eagerly load the related entities using features like `JOIN FETCH`, `.include()`, or `.select_related()`, executing a single JOIN query instead of N individual queries.",
 ["Enable SQL query logging / APM to diagnose", "Identified by one query followed by N identical queries", "Fix by eager loading (JOIN) in the ORM"],
 ["Cache the N+1 queries in Redis"]),

("DB_RL", "explain", "medium", "concept", ["Transactions"],
 "Explain how database transaction isolation levels affect backend concurrency, specifically focusing on the difference between Read Committed and Serializable.",
 "Isolation levels determine how concurrent transactions interact. 'Read Committed' prevents dirty reads by only seeing committed data, but allows non-repeatable reads (data changing during the transaction). 'Serializable' is the strictest level, locking rows or tables to guarantee transactions execute as if they were strictly sequential, preventing all anomalies but severely reducing concurrency and throughput.",
 ["Read Committed allows non-repeatable reads", "Serializable enforces strict sequential execution", "Serializable heavily reduces concurrency/throughput"],
 ["Read Committed is faster because it skips indexes"]),

("DB_RL", "tradeoff", "hard", "tradeoff", ["Concurrency"],
 "What tradeoffs are involved in using optimistic concurrency control versus pessimistic locking in a highly concurrent inventory checkout system?",
 "Optimistic locking (using a version/timestamp column) doesn't block the database, maximizing read throughput, but fails the transaction if a collision occurs, requiring application-level retries. Pessimistic locking (`SELECT FOR UPDATE`) blocks other transactions at the database level, preventing collision failures but heavily reducing throughput and risking deadlocks.",
 ["Optimistic: non-blocking, requires app retries on failure", "Pessimistic: blocks DB rows, risks deadlocks", "Pessimistic reduces throughput but guarantees state"],
 ["Optimistic locking uses Redis"]),

# ---------------- CC_CA ----------------
("CC_CA", "compare", "easy", "comparison", ["Architecture"],
 "Compare the cache-aside pattern with the write-through cache pattern.",
 "In cache-aside, the application code checks the cache first, and if missing, queries the DB and updates the cache. In write-through, the application writes data directly to the cache, and the cache synchronously writes it to the database, ensuring the cache is always completely consistent with the DB.",
 ["Cache-aside: App manages cache and DB independently", "Write-through: App writes to cache, cache writes to DB", "Write-through guarantees consistency"],
 ["They are exactly the same thing"]),

("CC_CA", "scenario", "medium", "scenario", ["Performance"],
 "A service begins experiencing severe database overload exactly when a popular cached item expires. How would you diagnose and prevent this 'cache stampede'?",
 "This is a cache stampede (thundering herd), diagnosed by a massive spike in DB queries for the exact same key. Prevent it by implementing distributed locking (mutex) so only one thread queries the DB to rebuild the cache while others wait, or by preemptively refreshing the cache in the background before the TTL expires.",
 ["Cache stampede / Thundering herd", "Implement distributed locking (mutex) for the DB query", "Preemptively refresh cache before TTL expiration"],
 ["Just increase the TTL to 10 years"]),

("CC_CA", "implement", "hard", "implementation", ["Invalidation"],
 "How would you design a cache invalidation strategy for a distributed e-commerce backend where product prices change frequently and must be reflected immediately?",
 "Time-to-Live (TTL) alone is insufficient. I would implement an event-driven write-through or cache-aside strategy. When a price is updated in the database, the service publishes an event (e.g., via Kafka) or immediately issues a `DEL` command to Redis for that specific product key, ensuring subsequent reads fetch the fresh price.",
 ["Event-driven invalidation or direct cache eviction on write", "Publish update event to message broker", "Avoid relying solely on TTL"],
 ["Just use a 1-second TTL on everything"]),

("CC_CA", "tradeoff", "medium", "tradeoff", ["Data Modeling"],
 "What are the tradeoffs of caching raw database query results versus caching fully serialized JSON API responses?",
 "Caching raw DB queries allows the data to be reused across different API endpoints and formats, but requires the backend to spend CPU cycles serializing it on every request. Caching serialized JSON responses uses zero CPU on a cache hit (extremely fast), but duplicates data if multiple endpoints need different views of the same resource.",
 ["Raw queries: reusable, requires CPU serialization", "Serialized JSON: zero CPU overhead, extremely fast", "Serialized JSON causes cache duplication"],
 ["Caching raw queries is faster than caching JSON"]),

("CC_CA", "debug", "medium", "debugging", ["HTTP Caching"],
 "An endpoint intermittently returns stale data to users even though the backend explicitly cleared the Redis cache. Where else might the response be cached, and how do you verify it?",
 "The response might be cached downstream by a CDN (Cloudflare), a reverse proxy (NGINX), or the user's browser. Verify this by inspecting the HTTP response headers (e.g., `Cache-Control`, `X-Cache: HIT`, `Age`). Fix it by sending proper `Cache-Control: no-cache` or `max-age=0` headers for dynamic endpoints.",
 ["Check CDN, reverse proxy, or browser caching", "Inspect HTTP response headers (Cache-Control, X-Cache)", "Ensure backend sends correct Cache-Control headers"],
 ["Redis is just slow to update"]),

# ---------------- MS_AY ----------------
("MS_AY", "fundamentals", "easy", "concept", ["Architecture"],
 "What is a Dead Letter Queue (DLQ) and what is its primary purpose in an asynchronous messaging architecture?",
 "A Dead Letter Queue is a secondary queue used to store messages that cannot be processed successfully after a certain number of retries. Its purpose is to prevent poison-pill messages from infinitely blocking the main queue and to allow engineers to manually inspect and debug the failed messages.",
 ["Stores messages that repeatedly fail processing", "Prevents blocking the main queue", "Allows manual inspection/debugging"],
 ["It deletes messages permanently to save space"]),

("MS_AY", "scenario", "medium", "scenario", ["Reliability"],
 "An application uses a message queue to process email notifications, but a bug in the worker causes it to crash halfway through processing a message. How do you ensure the message isn't lost?",
 "Ensure the worker does not auto-acknowledge (auto-ack) the message upon receipt. It must explicitly acknowledge the message only *after* successful processing. If the worker crashes, the broker detects the broken TCP connection and requeues the unacknowledged message for another worker to process.",
 ["Disable auto-acknowledge", "Explicitly acknowledge only after success", "Broker requeues unacknowledged messages on crash"],
 ["Catch the error and delete the message"]),

("MS_AY", "debug", "hard", "debugging", ["Poison Pills"],
 "You notice that a message broker is completely backed up because a poison-pill message is repeatedly failing and being retried infinitely. How do you resolve this at the infrastructure and application levels?",
 "At the infrastructure level, configure a maximum delivery attempt count on the queue, after which the broker automatically routes the message to a Dead Letter Queue (DLQ). At the application level, ensure the worker gracefully catches validation errors (non-retriable errors) and actively rejects the message without requeuing it.",
 ["Configure max delivery attempts on the broker", "Route to a Dead Letter Queue (DLQ)", "Application should catch non-retriable errors and reject"],
 ["Restart the message broker"]),

("MS_AY", "architecture", "hard", "architecture", ["Distributed Systems"],
 "How would you design an event-driven system to guarantee exactly-once processing when the underlying message queue only provides at-least-once delivery?",
 "Exactly-once delivery is impossible, so you must implement exactly-once *processing* via idempotency. The worker must extract a unique ID from the message payload and atomically check a database constraint (or Redis) to ensure this ID hasn't been processed yet. If it has, the worker safely acknowledges and ignores the duplicate.",
 ["Exactly-once delivery is impossible; use at-least-once", "Implement idempotency in the consumer", "Atomically check unique message ID before processing"],
 ["Switch to a queue that promises exactly-once delivery"]),

("MS_AY", "tradeoff", "medium", "tradeoff", ["Architecture"],
 "What tradeoffs exist between using a pull-based message queue (like RabbitMQ/SQS) versus a push-based pub/sub system (like SNS or Webhooks) for backend service communication?",
 "Pull-based queues allow consumers to dictate their own pace, providing built-in backpressure and load balancing, but require active polling. Push-based systems deliver messages instantly (lower latency) and easily support multiple distinct subscribers, but can overwhelm downstream services if they lack their own rate limiting.",
 ["Pull-based provides built-in backpressure/pacing", "Push-based offers lower latency and multiple subscribers", "Push-based can overwhelm slow consumers"],
 ["Pull-based is for frontends, push-based is for backends"]),

# ---------------- MC_SV ----------------
("MC_SV", "explain", "easy", "concept", ["Architecture"],
 "Explain the API Gateway pattern in a microservices architecture.",
 "An API Gateway is a single entry point for all client requests. It sits in front of the microservices and handles cross-cutting concerns like routing, authentication, SSL termination, rate limiting, and request aggregation, shielding clients from the internal complexity of the microservice architecture.",
 ["Single entry point for clients", "Handles routing, auth, rate limiting", "Shields clients from internal architecture"],
 ["It is a database that all microservices share"]),

("MC_SV", "compare", "medium", "comparison", ["Communication"],
 "Compare synchronous HTTP communication (REST/gRPC) with asynchronous event-driven communication between microservices.",
 "Synchronous communication is easy to reason about and provides immediate responses, but creates tight temporal coupling—if the downstream service is down, the request fails. Asynchronous communication (via message brokers) provides loose coupling and fault tolerance, but adds complexity regarding eventual consistency and debugging.",
 ["Sync provides immediate response but tight coupling", "Async provides fault tolerance but eventual consistency", "Sync fails if downstream is down"],
 ["Sync is always faster than Async"]),

("MC_SV", "architecture", "hard", "architecture", ["Distributed Transactions"],
 "Suppose a user registers, requiring profile creation in Service A, billing in Service B, and an email via Service C. How do you handle a failure in Service B to maintain data consistency?",
 "Since distributed transactions (2PC) are anti-patterns in microservices, use the Saga pattern. If Service B fails, the orchestrator or choreographing event bus must trigger a compensating transaction in Service A to undo the profile creation, rolling back the system to a consistent state.",
 ["Use the Saga pattern", "Trigger compensating transactions", "Rollback Service A if Service B fails"],
 ["Use a massive SQL database with 2-Phase Commit (2PC)"]),

("MC_SV", "scenario", "medium", "scenario", ["Resilience"],
 "A service begins failing intermittently because a downstream microservice it depends on is taking 30 seconds to respond. How do you protect the calling service from cascading failure?",
 "Implement a Circuit Breaker pattern and strict timeouts on the HTTP client. If the downstream service exceeds the timeout or error threshold, the circuit trips, and the calling service immediately returns an error or fallback response without waiting 30 seconds, preventing thread pool exhaustion.",
 ["Implement strict HTTP timeouts", "Use a Circuit Breaker pattern", "Prevents thread pool exhaustion / cascading failure"],
 ["Increase the timeout to 60 seconds"]),

("MC_SV", "tradeoff", "hard", "tradeoff", ["Data Modeling"],
 "What are the tradeoffs of using a shared database between two microservices versus forcing them to communicate strictly through APIs?",
 "A shared database violates microservice isolation; a schema change by one service breaks the other, and it creates a single point of scaling failure. However, it makes joins and transactions trivial. API-driven communication guarantees isolation and independent scaling, but forces the system to deal with eventual consistency and network latency.",
 ["Shared DB violates isolation but makes joins easy", "API guarantees isolation and independent scaling", "API introduces eventual consistency and network latency"],
 ["Shared databases are required in microservices"]),

# ---------------- CN_CN ----------------
("CN_CN", "fundamentals", "easy", "concept", ["Concurrency"],
 "What is a race condition in a backend application, and how does it typically manifest?",
 "A race condition occurs when two or more threads or processes access shared data simultaneously and try to modify it without proper synchronization. It manifests as unpredictable, intermittent bugs where data is corrupted or counts are incorrect depending on the exact timing of execution.",
 ["Multiple threads modifying shared data simultaneously", "Lack of proper synchronization/locking", "Results in unpredictable data corruption"],
 ["It is when a database query takes too long"]),

("CN_CN", "implement", "medium", "implementation", ["Data Structures"],
 "How would you approach thread-safe access to a shared in-memory dictionary in a multi-threaded backend application?",
 "You must protect the dictionary using synchronization primitives. Depending on the language, use a Read-Write Lock (allowing concurrent reads but exclusive writes), or use a natively concurrent data structure provided by the language standard library (e.g., `ConcurrentHashMap` in Java, `sync.Map` in Go).",
 ["Use a Read-Write Lock (Mutex)", "Use native concurrent data structures (ConcurrentHashMap)", "Prevent simultaneous write access"],
 ["Just use a normal dictionary, it's fine"]),

("CN_CN", "debug", "hard", "debugging", ["Deadlocks"],
 "You notice that a multi-threaded backend application is experiencing a deadlock in production. What conditions cause a deadlock, and how would you diagnose it using application dumps?",
 "Deadlocks occur when two threads hold locks the other needs, creating a circular wait. Diagnose it by taking a thread dump (e.g., `jstack` in Java or pprof in Go). Analyze the dump to find blocked threads waiting on monitors/mutexes held by each other. Fix by enforcing a strict lock acquisition order.",
 ["Circular wait condition between threads holding locks", "Diagnose using thread dumps (jstack/pprof)", "Fix by enforcing strict lock ordering"],
 ["Restart the server to fix the code automatically"]),

("CN_CN", "scenario", "medium", "scenario", ["Transactions"],
 "An endpoint allows users to claim a limited promo code. Under heavy concurrent load, 110 users claim a code that was only supposed to have 100 uses. How do you fix this backend logic?",
 "The backend is performing a read-modify-write without locking. Fix it by delegating the atomicity to the database. Use an atomic `UPDATE promo SET count = count - 1 WHERE id = 1 AND count > 0` query. Check the number of affected rows; if 0, the promo is sold out.",
 ["Avoid non-atomic read-modify-write in the application", "Delegate atomicity to the database", "Use UPDATE with a WHERE count > 0 constraint"],
 ["Add a sleep() to the endpoint"]),

("CN_CN", "compare", "hard", "comparison", ["Architecture"],
 "Compare the performance and scaling characteristics of a thread-per-request concurrency model versus an asynchronous event-loop model.",
 "Thread-per-request (Tomcat) isolates requests but consumes significant memory (stack per thread) and CPU overhead for context switching, struggling under high concurrent connections (C10k problem). Event-loop (Node.js) uses a single thread with non-blocking I/O, scaling massively to thousands of connections with low memory, but blocks entirely if a heavy CPU task is executed.",
 ["Thread-per-request: high memory, heavy context switching", "Event-loop: low memory, highly scalable I/O", "Event-loop suffers under heavy CPU bound tasks"],
 ["Event loops spawn millions of threads under the hood"]),

# ---------------- RL_FT ----------------
("RL_FT", "explain", "easy", "concept", ["Architecture"],
 "Explain what a Circuit Breaker is in the context of backend reliability.",
 "A Circuit Breaker is a design pattern that wraps a remote service call. If the remote service repeatedly fails or times out, the circuit 'trips' (opens), and subsequent calls fail fast immediately without attempting the network request. This prevents cascading failures and gives the failing service time to recover.",
 ["Wraps remote service calls", "Trips on repeated failures to fail fast", "Prevents cascading failures and resource exhaustion"],
 ["It shuts down the server to save electricity"]),

("RL_FT", "scenario", "medium", "scenario", ["UX"],
 "A downstream dependency goes completely offline. How would you design a graceful degradation strategy for an e-commerce product page relying on that dependency for personalized recommendations?",
 "Instead of failing the entire product page request, catch the downstream timeout or error and return a fallback response. The fallback could be a static list of 'top-selling products', a cached version of older recommendations, or simply an empty list so the page renders without recommendations.",
 ["Catch the downstream failure", "Return a static fallback or cached data", "Ensure the main page still renders successfully"],
 ["Return a 500 error to the user"]),

("RL_FT", "tradeoff", "medium", "tradeoff", ["Retries"],
 "What tradeoffs exist between implementing aggressive exponential backoff retries versus failing fast when a downstream API returns a 503 error?",
 "Aggressive retries hide temporary network blips from the user, improving UX, but tie up the calling service's threads and can exacerbate the downstream outage (thundering herd). Failing fast frees up local resources immediately and protects the downstream service, but forces the user to manually retry.",
 ["Retries improve UX but tie up resources/threads", "Failing fast protects resources and downstream systems", "Aggressive retries risk thundering herd issues"],
 ["Retrying always fixes the error instantly"]),

("RL_FT", "architecture", "hard", "architecture", ["Rate Limiting"],
 "How would you design a rate-limiting system for a distributed API that must enforce a strict global quota of 100 requests per second per tenant across 50 load-balanced servers?",
 "An in-memory counter won't work across 50 servers. Use a centralized fast data store like Redis. Implement a sliding window log or token bucket algorithm using Redis atomic scripts (Lua) to increment and check limits. This guarantees atomicity and global consistency across all 50 servers without race conditions.",
 ["Centralized data store (Redis)", "Implement Token Bucket or Sliding Window", "Use atomic Lua scripts to prevent race conditions"],
 ["Use a global variable in the load balancer code"]),

("RL_FT", "debug", "medium", "debugging", ["Resource Exhaustion"],
 "An application experiences sudden OOM crashes due to a massive influx of large HTTP requests. How do you implement backpressure to prevent the server from accepting more work than it can handle?",
 "Implement strict limits on the maximum concurrent HTTP connections (e.g., MaxClients in the web server). Limit the maximum payload size (e.g., 2MB). Finally, if the internal queues or worker threads are full, the API should actively shed load by returning a 429 Too Many Requests or 503 Service Unavailable immediately.",
 ["Limit concurrent connections", "Limit maximum request payload size", "Shed load (return 429/503) when internal queues are full"],
 ["Install more RAM on the server automatically"]),

# ---------------- PR_PF ----------------
("PR_PF", "fundamentals", "easy", "concept", ["Metrics"],
 "What is the difference between latency and throughput in backend system performance?",
 "Latency is the time it takes to process a single request and return a response (measured in milliseconds). Throughput is the volume of requests the system can handle concurrently over a given time period (measured in Requests Per Second).",
 ["Latency is response time for a single request", "Throughput is volume of requests over time", "Measured in ms vs RPS"],
 ["Latency is speed, throughput is database size"]),

("PR_PF", "debug", "medium", "debugging", ["Bottlenecks"],
 "A production API endpoint suddenly degrades from 50ms to 5000ms response times. CPU and memory are normal, but database connection pool utilization is at 100%. What is the likely cause?",
 "The application threads are likely starved, waiting for available database connections. This indicates either a sudden spike in traffic, a slow database query holding the connection open too long (e.g., a missing index), or a connection leak in the code where connections are not being released back to the pool.",
 ["Thread starvation waiting for DB connections", "Slow query locking connections", "Connection leak in application code"],
 ["The CPU needs to be upgraded"]),

("PR_PF", "implement", "hard", "implementation", ["Profiling"],
 "How would you approach profiling a backend application that experiences random latency spikes only under high concurrent load?",
 "Use an Application Performance Monitoring (APM) tool with distributed tracing to sample requests. Under load, take CPU and memory profiles (flame graphs) to identify lock contention, excessive garbage collection pauses, or thread pool exhaustion. Perform load testing in staging mirroring the concurrent traffic to reproduce and isolate the bottleneck.",
 ["Use APM and distributed tracing", "Analyze CPU flame graphs and GC logs", "Simulate concurrent load in staging"],
 ["Add console.log to every line of code"]),

("PR_PF", "scenario", "medium", "scenario", ["Optimization"],
 "An endpoint fetching a user's dashboard makes 15 sequential HTTP requests to internal microservices. How do you optimize this to reduce overall response latency?",
 "Instead of awaiting each request sequentially, parallelize them. Execute the independent HTTP requests concurrently using features like `Promise.all` in Node, `CompletableFuture` in Java, or `async.gather` in Python, reducing the total latency to the duration of the single slowest request.",
 ["Parallelize independent requests", "Use concurrency constructs (Promise.all, async/await)", "Total latency drops to the slowest request"],
 ["Combine all microservices into one immediately"]),

("PR_PF", "compare", "hard", "comparison", ["Protocols"],
 "Compare the performance implications of using a JSON-based REST API versus a binary protocol like gRPC (Protocol Buffers) for internal service-to-service communication.",
 "JSON is human-readable but text-heavy, requiring significant CPU overhead to parse and serialize, and generates larger network payloads. gRPC uses Protocol Buffers, which is a highly compressed binary format. It is much faster to serialize/deserialize and uses less bandwidth, making it vastly superior for high-throughput microservice communication.",
 ["JSON has heavy parsing/serialization CPU overhead", "gRPC is binary, compressed, and faster", "gRPC uses HTTP/2 multiplexing"],
 ["JSON is faster because the browser supports it natively"]),

# ---------------- OB_LG ----------------
("OB_LG", "explain", "easy", "concept", ["Tracing"],
 "Explain the concept of a Correlation ID and why it is essential in distributed systems.",
 "A Correlation ID is a unique identifier generated at the entry point of a system (like an API Gateway) and passed along in the headers of all downstream microservice requests. It allows developers to aggregate and trace the entire lifecycle of a single user action across multiple distributed logs.",
 ["Unique identifier passed through downstream requests", "Aggregates logs across multiple microservices", "Essential for tracing distributed workflows"],
 ["It is the user's database ID"]),

("OB_LG", "scenario", "medium", "scenario", ["Logging"],
 "A production bug occurs silently without throwing an explicit exception. How would you design a structured logging strategy to ensure you have enough context to trace the logical flow of the request?",
 "Use structured JSON logging instead of plain text. Include contextual metadata in every log entry (e.g., `user_id`, `correlation_id`, `endpoint`, `state`). Log at key boundary points (request received, DB query started, external API called) so the exact logical path can be reconstructed in a log aggregator like ELK or Datadog.",
 ["Use structured JSON logs", "Inject contextual metadata (correlation_id)", "Log at key application boundaries"],
 ["Write extremely long paragraphs in plain text logs"]),

("OB_LG", "debug", "hard", "debugging", ["Logging Configuration"],
 "You notice that the application logs are completely flooded with verbose debug messages, causing the logging infrastructure to crash. How do you dynamically adjust log levels in a distributed environment without restarting the services?",
 "Implement a centralized configuration management system (like Consul, etcd, or Spring Cloud Config). The application should watch this configuration store or expose an authenticated admin endpoint to change the logging level in memory at runtime (e.g., from DEBUG to WARN), applying the change instantly without restarts.",
 ["Centralized dynamic configuration (Consul/etcd)", "Expose admin endpoint to alter log level", "Change log level in memory without restarting"],
 ["SSH into the server and delete the log files"]),

("OB_LG", "tradeoff", "medium", "tradeoff", ["Observability"],
 "What tradeoffs are involved in logging the full HTTP request and response payloads for every API call in a high-throughput production environment?",
 "It provides incredible debugging context, but massively inflates log storage costs and I/O overhead (potentially slowing down the application). Furthermore, it creates severe security and compliance risks (GDPR, PCI) by inadvertently logging PII, passwords, or credit card numbers.",
 ["Massive storage costs and I/O performance hit", "Severe security/PII compliance risks", "Provides excellent debugging context"],
 ["Logging is free and has no downsides"]),

("OB_LG", "implement", "medium", "implementation", ["Metrics"],
 "How would you approach instrumenting a backend service to expose Prometheus metrics for tracking the 99th percentile latency of a specific API endpoint?",
 "I would instrument the endpoint middleware using a Prometheus client library to record the execution duration in a `Histogram` or `Summary` metric vector, labeled by the endpoint route. Prometheus then scrapes this endpoint, and tools like Grafana use the `histogram_quantile(0.99, ...)` function to calculate the 99th percentile.",
 ["Use a Histogram or Summary metric type", "Instrument endpoint middleware to record duration", "Calculate quantiles in Prometheus/Grafana"],
 ["Just log Date.now() and manually calculate it in Excel"])
]
