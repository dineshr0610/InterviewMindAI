"""Batch 18 question content (Backend Developer). Antigravity-native, no Gemini API."""

ROLE = "Backend Developer"

BUCKET_KEYS = {
    "BE_API": ("API Design", "REST & Webhooks", "HTTP", ["Frontend Developer", "Architecture"]),
    "BE_SEC": ("Security", "Auth & Rate Limiting", "Security", ["Security Engineer", "Architecture"]),
    "BE_DS": ("Distributed Systems", "Microservices", "Architecture", ["Architecture"]),
    "BE_MS": ("Messaging", "Queues & Events", "Architecture", ["Data Engineer"]),
    "BE_CA": ("Performance", "Caching", "Redis", ["Performance Engineer"]),
    "BE_DB": ("Databases", "Transactions & ORMs", "SQL", ["Database Developer"]),
    "BE_RE": ("Reliability", "Fault Tolerance", "Architecture", ["DevOps / Cloud Engineer"]),
    "BE_SC": ("Scaling", "Load Balancing", "Architecture", ["DevOps / Cloud Engineer"]),
    "BE_OB": ("Observability", "Debugging", "Monitoring", ["DevOps / Cloud Engineer", "Performance Engineer"]),
}

Q = [
# ---------------- BE_API ----------------
("BE_API", "fundamentals", "easy", "concept", ["API Design"],
 "What is the semantic difference between a `PUT` request and a `PATCH` request in RESTful API design?",
 "`PUT` is used to completely replace an entire resource with a new representation; if the resource doesn't exist, it can create it. `PATCH` is used to apply partial modifications to an existing resource, updating only the specific fields provided in the payload.",
 ["PUT completely replaces the resource", "PATCH applies partial updates to specific fields", "Both modify existing resources"],
 ["PUT is for databases, PATCH is for files"]),

("BE_API", "tradeoff", "medium", "tradeoff", ["API Design"],
 "What tradeoffs exist between embedding related resource data directly into an API response versus returning a URL (hypermedia link) for the client to fetch it separately?",
 "Embedding data reduces network round-trips and latency for clients that definitely need the data, but bloats the payload size, increases backend database load, and wastes bandwidth if the client ignores it. Returning URLs (HATEOAS) keeps payloads small and highly cacheable, but forces the client to make multiple sequential HTTP requests (the N+1 problem) to gather all data.",
 ["Embedding: reduces network round trips, but bloats payloads and wastes bandwidth if unused", "Linking: keeps payloads small/cacheable, but forces N+1 network requests", "Embedding increases database joins/load"],
 ["Embedding data is illegal in REST APIs"]),

("BE_API", "scenario", "medium", "scenario", ["Webhooks"],
 "An external partner consumes your webhooks. Their servers occasionally go down, causing your webhook delivery service to experience massive timeouts and queue backlogs. How do you redesign your webhook architecture to protect your systems?",
 "I would decouple the webhook dispatching system using an asynchronous message queue (e.g., SQS or RabbitMQ). I would implement strict timeouts on the HTTP outbound calls, and configure the queue with an exponential backoff retry policy and a Dead Letter Queue (DLQ) so that failing partner endpoints do not block the delivery of webhooks to healthy partners.",
 ["Decouple using an asynchronous message queue", "Implement strict HTTP timeouts on outbound calls", "Use exponential backoff retries and Dead Letter Queues (DLQs)"],
 ["Just turn off the webhooks permanently"]),

("BE_API", "explain", "easy", "concept", ["HTTP Caching"],
 "Explain the purpose of the `ETag` and `If-None-Match` HTTP headers in caching API responses.",
 "An `ETag` is a unique identifier (like a hash) assigned by the server to a specific version of a resource. When a client re-requests the resource, it sends the `ETag` in the `If-None-Match` header. The server compares it; if the resource hasn't changed, the server returns a lightweight `304 Not Modified` empty response, saving massive bandwidth and client rendering time.",
 ["ETag is a unique identifier/hash for a resource version", "Client sends ETag back using If-None-Match", "Server returns 304 Not Modified if unchanged, saving bandwidth"],
 ["ETags are used to track user search history"]),

("BE_API", "implement", "hard", "implementation", ["Pagination"],
 "How would you approach designing a pagination strategy for a high-traffic REST API endpoint returning millions of records, given that `OFFSET` and `LIMIT` queries become extremely slow at deep pages?",
 "I would implement Keyset Pagination (also known as Cursor-based Pagination). Instead of using `OFFSET`, the client passes a cursor (e.g., the last `id` or `timestamp` they received). The backend queries `WHERE id > ? LIMIT 50`. This utilizes the database B-tree index efficiently, providing constant O(1) time complexity regardless of how deep the page is.",
 ["Avoid OFFSET/LIMIT which requires scanning and discarding rows (O(N))", "Implement Keyset or Cursor-based Pagination", "Use WHERE id > cursor LIMIT X to leverage B-tree indexes (O(1))"],
 ["Just return all 1 million records in one giant JSON array"]),

("BE_API", "debug", "medium", "debugging", ["Networking"],
 "A client application receives an HTTP 429 Too Many Requests response from your API. However, your backend rate limiter logs show the client hasn't exceeded its quota. What upstream infrastructure component usually causes this false positive?",
 "This is usually caused by an upstream API Gateway, Web Application Firewall (WAF), or Reverse Proxy (like Cloudflare or NGINX) enforcing its own infrastructure-level rate limits or DDoS protection rules, completely intercepting the request before it even reaches the backend application code.",
 ["Upstream infrastructure is intercepting the request", "API Gateway, WAF, or Reverse Proxy (Cloudflare/NGINX)", "Infrastructure-level DDoS protection or rate limiting triggers first"],
 ["The database is out of hard drive space"]),

# ---------------- BE_SEC ----------------
("BE_SEC", "fundamentals", "easy", "concept", ["Security"],
 "What is the primary difference between Authentication and Authorization?",
 "Authentication is the process of verifying WHO a user or system is (e.g., logging in with a password or validating a token signature). Authorization is the process of determining WHAT that authenticated user is allowed to do (e.g., checking if they have 'admin' roles to delete a resource).",
 ["Authentication: Verifying identity (Who you are)", "Authorization: Verifying permissions (What you can do)", "Authentication always precedes Authorization"],
 ["They are identical terms in cybersecurity"]),

("BE_SEC", "scenario", "medium", "scenario", ["Authentication"],
 "A security audit reveals that your JWT access tokens are valid for 24 hours. A user logs out, but their token remains completely usable until it expires. How do you conceptually fix this while minimizing database lookups?",
 "JWTs are stateless, meaning they cannot be invalidated on the server by default. To fix this, reduce the JWT lifespan to 15 minutes and issue a stateful Refresh Token. When a user logs out, revoke the Refresh Token in the database. The short-lived JWT will naturally expire quickly. Alternatively, maintain a Redis 'blacklist' of revoked token IDs (jti) until they expire.",
 ["Reduce JWT lifespan drastically (e.g., 15 minutes)", "Use a stateful Refresh Token that can be revoked in the database", "Alternatively, use a Redis blacklist for explicitly revoked token IDs (jti)"],
 ["Delete the user's account entirely on logout"]),

("BE_SEC", "explain", "medium", "concept", ["OAuth2"],
 "Explain the concept of the OAuth2 Authorization Code Grant flow. Why is it more secure than the Implicit flow for web applications?",
 "In the Authorization Code flow, the client redirects the user to the Auth server, which returns a temporary 'code' via the browser. The backend server then exchanges this code for an Access Token directly with the Auth server via a secure back-channel. This is highly secure because the Access Token is never exposed to the user's browser, unlike the Implicit flow which leaks tokens in the URL hash.",
 ["Returns a temporary code to the browser", "Backend exchanges the code for a token via a secure back-channel", "Prevents the Access Token from ever being exposed to the browser/frontend"],
 ["It uses AES-256 encryption on the password field"]),

("BE_SEC", "tradeoff", "hard", "tradeoff", ["Microservices Security"],
 "What are the architectural tradeoffs of validating a JWT statelessly on every microservice versus using an API Gateway to perform a stateful token inspection (introspection) against an Identity Provider?",
 "Stateless JWT validation at the microservice level is extremely fast, highly scalable, and requires zero network calls, but strictly prevents immediate token revocation (tokens remain valid until expiry). Stateful introspection at the Gateway guarantees absolute real-time revocation and centralized security, but introduces network latency on every request and creates a massive single point of failure at the Identity Provider.",
 ["Stateless JWT: zero network latency, highly scalable, but impossible to revoke instantly", "Stateful Introspection: instant real-time revocation, centralized security", "Stateful Introspection: adds network latency and bottlenecks the Identity Provider"],
 ["Stateless validation requires sharing the database password with everyone"]),

("BE_SEC", "implement", "medium", "implementation", ["Rate Limiting"],
 "How would you implement rate limiting for a public API that allows 100 requests per minute per IP address, specifically using Redis? Which data structure or algorithm would you use?",
 "I would use a Sliding Window Log or a Token Bucket algorithm. In Redis, for a simple Sliding Window Log, I would use a Sorted Set (`ZSET`) where the key is the IP, the score is the timestamp, and the value is a UUID. I count the elements within the last 60 seconds; if > 100, reject. I'd then remove elements older than 60 seconds to free memory.",
 ["Use a Sliding Window Log or Token Bucket algorithm", "Use Redis Sorted Sets (ZSET) for Sliding Window", "Score is timestamp; filter and count requests in the last 60 seconds"],
 ["Store every request in a SQL database table indefinitely"]),

("BE_SEC", "debug", "hard", "debugging", ["Concurrency"],
 "You implemented a standard Redis-based sliding window rate limiter. Under extreme concurrent load, a single user is able to bypass the limit and send 150 requests. Why did this race condition occur, and how do you fix it?",
 "The race condition occurs because reading the current count and incrementing the count are two separate network operations. Multiple threads read '99' simultaneously, and all are allowed through before the count updates. Fix this by ensuring atomicity: wrap the Redis commands in a Lua script (which Redis executes atomically) or use a Redis `MULTI/EXEC` transaction block.",
 ["Reading the count and incrementing are non-atomic (Race Condition)", "Multiple threads read a low count simultaneously", "Fix by executing operations atomically using a Redis Lua Script or MULTI/EXEC"],
 ["Redis is just inherently slow and drops data"]),

# ---------------- BE_DS ----------------
("BE_DS", "fundamentals", "easy", "concept", ["Architecture"],
 "What is a Microservices architecture, and what primary organizational problem does it aim to solve compared to a Monolith?",
 "Microservices architecture structures an application as a collection of loosely coupled, independently deployable services organized around business capabilities. It primarily solves organizational scaling problems by allowing multiple independent teams to develop, deploy, and scale their specific domain services autonomously without blocking each other on a massive monolithic codebase.",
 ["Loosely coupled, independently deployable services", "Organized around business capabilities/domains", "Allows independent teams to scale and deploy autonomously without bottlenecks"],
 ["Microservices mean writing the code in smaller font sizes"]),

("BE_DS", "explain", "medium", "concept", ["Distributed Transactions"],
 "Explain the Saga pattern in distributed systems. Why is it used instead of traditional ACID transactions across microservices?",
 "The Saga pattern manages distributed transactions by breaking them into a sequence of local ACID transactions. If a step fails, the Saga executes compensating transactions (undos) for the completed steps. It is used because traditional distributed ACID transactions (Two-Phase Commit / 2PC) lock database rows across multiple services over the network, causing catastrophic latency and bottlenecks.",
 ["Breaks distributed transactions into a sequence of local transactions", "Uses compensating transactions to 'undo' steps upon failure", "Avoids the severe locking latency and bottlenecks of Two-Phase Commit (2PC)"],
 ["Sagas are used to write epic fantasy novels inside the codebase"]),

("BE_DS", "scenario", "medium", "scenario", ["Resilience"],
 "Microservice A calls Microservice B synchronously via HTTP. Microservice B relies on a slow legacy database. Service A begins exhausting its thread pool. How do you prevent Service B's latency from crashing Service A?",
 "I would implement the Circuit Breaker pattern (and strict timeouts) on Service A. When Service A detects elevated latency or failures from Service B, the circuit 'opens' and immediately rejects new requests (fast-fail), preventing thread exhaustion in Service A. The circuit periodically allows a test request to see if Service B has recovered.",
 ["Implement the Circuit Breaker pattern", "Implement strict network timeouts", "Fails fast to prevent thread pool exhaustion and cascading failures"],
 ["Just restart Service A every 5 minutes"]),

("BE_DS", "tradeoff", "hard", "tradeoff", ["Architecture"],
 "What tradeoffs exist between orchestrating a distributed business process (using a central orchestrator service) versus choreographing it (where services react autonomously to events)?",
 "Orchestration provides a clear, centralized view of the business workflow and simplifies monitoring, but creates a massive central point of coupling and potential bottleneck (the 'god service'). Choreography (event-driven) creates highly decoupled, autonomous services that scale perfectly, but makes the overall business flow extremely difficult to track, debug, and understand (the 'distributed monolith' risk).",
 ["Orchestration: centralized logic, easy to monitor, but tightly coupled 'god service'", "Choreography: highly decoupled/scalable, no central bottleneck", "Choreography: extremely difficult to track overall flow and debug"],
 ["Orchestration uses musical instruments, choreography uses dancing"]),

("BE_DS", "implement", "medium", "implementation", ["Service Security"],
 "How would you design a service-to-service authentication mechanism to ensure Microservice A is cryptographically authorized to invoke Microservice B without relying solely on network perimeter security?",
 "I would implement Mutual TLS (mTLS) where both services authenticate each other's cryptographic certificates during the TLS handshake (often managed by a Service Mesh like Istio). Alternatively, Service A can request an internal JWT (JSON Web Token) from an identity server, sign it, and pass it in the Authorization header for Service B to validate.",
 ["Use Mutual TLS (mTLS) for cryptographic certificate verification", "Use a Service Mesh to manage the certificates automatically", "Alternatively, use signed internal JWTs passed in headers"],
 ["Use a hardcoded password string like 'admin123'"]),

("BE_DS", "debug", "hard", "debugging", ["Microservices"],
 "A distributed trace shows a request bouncing back and forth between Service X and Service Y in an infinite loop until the HTTP request times out. How do you prevent this architectural flaw?",
 "This is a distributed cyclic dependency. Architecturally, it should be prevented by enforcing strict domain boundaries and layered architecture (e.g., A calls B, but B cannot call A). Technically, it can be mitigated by passing a 'Hop Count' or 'TTL' header in the HTTP request (similar to network TTL); if the count exceeds a threshold, the service instantly drops the request to break the loop.",
 ["Enforce strict domain boundaries (prevent bidirectional calling)", "Pass a 'Hop Count' or 'TTL' header via context propagation", "Drop the request if the Hop Count exceeds a safe threshold"],
 ["Increase the HTTP timeout to infinity"]),

# ---------------- BE_MS ----------------
("BE_MS", "fundamentals", "easy", "concept", ["Messaging"],
 "What is the difference between a Message Queue (like RabbitMQ) and an Event Stream (like Apache Kafka)?",
 "A Message Queue routes specific commands/tasks to a worker; once the message is successfully processed, it is deleted from the queue (point-to-point). An Event Stream acts as a persistent, append-only log of historical facts; consumers read the stream at their own pace, and messages remain in the log for other consumers to read independently (pub/sub).",
 ["Message Queue: task-oriented, message is deleted after processing (point-to-point)", "Event Stream: append-only log of facts, persistent", "Event Stream: allows multiple independent consumers to replay history"],
 ["Kafka is for Java, RabbitMQ is for Python"]),

("BE_MS", "tradeoff", "medium", "tradeoff", ["Concurrency"],
 "What are the tradeoffs of processing background jobs sequentially using a single worker versus processing them concurrently across 50 workers?",
 "A single worker is extremely easy to debug, guarantees strict chronological processing order, and prevents database locking issues, but yields terrible throughput and cannot scale. 50 workers provide massive throughput and horizontal scalability, but completely destroy message ordering, cause massive database row contention/deadlocks, and require strict idempotency handling for race conditions.",
 ["Single worker: guarantees strict order, easy to debug, no DB contention, but terrible throughput", "50 workers: massive throughput and scalability", "50 workers: destroys ordering, causes DB deadlocks, requires strict idempotency"],
 ["50 workers will always process 50 times slower due to the internet"]),

("BE_MS", "scenario", "hard", "scenario", ["Error Handling"],
 "A background worker processing video uploads from an SQS queue crashes randomly due to Out-Of-Memory errors mid-processing. When the worker restarts, the video processes again and crashes again (a poison pill). How do you handle this automatically?",
 "Configure a Dead Letter Queue (DLQ) with a `maxReceiveCount` (e.g., 3). When the worker crashes, the message's visibility timeout expires, and it returns to the queue. After failing 3 times, the queue automatically moves the 'poison pill' message to the DLQ. This unblocks the queue, allowing healthy videos to process, while engineers investigate the DLQ.",
 ["Configure a Dead Letter Queue (DLQ)", "Set a maxReceiveCount threshold (e.g., 3 retries)", "Unblocks the main queue by isolating the 'poison pill' message"],
 ["Write a try-catch block that ignores OutOfMemory errors"]),

("BE_MS", "implement", "medium", "implementation", ["Distributed Architecture"],
 "How would you design an event-driven architecture to guarantee that a 'UserCreated' event is published to Kafka strictly *if and only if* the database transaction committing the user succeeds?",
 "I would use the Transactional Outbox Pattern. During the database transaction, I insert the user record AND insert a serialized 'UserCreated' event into a separate `outbox` table in the exact same transaction. A separate background process (like Debezium / Change Data Capture) continuously polls or tails the `outbox` table and safely publishes the events to Kafka.",
 ["Use the Transactional Outbox Pattern", "Save the event to an `outbox` table in the same ACID transaction as the business data", "Use a separate background worker or CDC to publish the outbox table to Kafka"],
 ["Publish to Kafka first, then cross your fingers the database works"]),

("BE_MS", "explain", "medium", "concept", ["Kafka"],
 "Explain the concept of 'Consumer Groups' in Apache Kafka and how they enable horizontal scalability.",
 "A Consumer Group is a logical grouping of consumers reading from the same Kafka Topic. Kafka achieves horizontal scalability by assigning distinct 'Partitions' of the topic to different instances within the same Consumer Group. If a topic has 10 partitions, you can run 10 consumer instances in the group, and Kafka will load balance the work perfectly among them.",
 ["Logical grouping of consumers reading a topic", "Kafka assigns topic Partitions exclusively to instances within the group", "Enables perfect horizontal load balancing across multiple worker instances"],
 ["Consumer Groups are people who buy products from an e-commerce site"]),

("BE_MS", "debug", "hard", "debugging", ["Messaging"],
 "An application publishes messages to an SNS topic, which fans out to multiple SQS queues. You notice that messages are arriving completely out of order at the consumer. Why is this expected, and how do you enforce strict global ordering if it's genuinely required?",
 "Standard SNS and SQS operate on highly distributed, multi-AZ architectures, guaranteeing 'at-least-once' delivery but explicitly NOT guaranteeing order. To enforce strict global ordering, you must switch to SNS FIFO topics and SQS FIFO queues, and ensure the publisher provides a consistent `MessageGroupId`. Note that FIFO drastically limits throughput/TPS compared to standard queues.",
 ["Standard SQS/SNS explicitly do NOT guarantee message ordering", "Switch to SQS FIFO queues and SNS FIFO topics", "Provide a consistent MessageGroupId, acknowledging the tradeoff in throughput"],
 ["Reboot the SQS server to fix the ordering bug"]),

# ---------------- BE_CA ----------------
("BE_CA", "fundamentals", "easy", "concept", ["Caching"],
 "What is a Cache Stampede (or Cache Miss Storm) in backend systems?",
 "A cache stampede occurs when a highly requested, computationally expensive cache key suddenly expires. Instantly, thousands of concurrent requests check the cache, see a 'miss', and all simultaneously hit the underlying database or slow service to regenerate the same data, completely overwhelming and crashing the database.",
 ["Highly requested cache key expires", "Thousands of concurrent requests experience a cache miss simultaneously", "All requests hit the database at once to regenerate the data, causing a crash"],
 ["A stampede of actual servers falling over"]),

("BE_CA", "explain", "medium", "concept", ["Caching Strategies"],
 "Explain the difference between a Write-Through cache and a Cache-Aside (Lazy Loading) caching strategy.",
 "In Cache-Aside (Lazy), the application checks the cache; if it misses, the app fetches from the DB and writes to the cache. In Write-Through, the application writes data directly to the cache, and the cache synchronously writes it to the database before returning success. Write-Through ensures perfect consistency but adds write latency, while Cache-Aside is fast but risks stale data.",
 ["Cache-Aside: App handles misses by reading DB and populating cache (lazy)", "Write-Through: App writes to cache, which synchronously updates the DB", "Write-Through guarantees consistency but adds write latency"],
 ["Write-Through writes directly to the user's hard drive"]),

("BE_CA", "scenario", "medium", "scenario", ["Performance Engineering"],
 "A backend API aggregates data from three slow external services. You cache the response in Redis for 5 minutes. During the cache expiration moment, 1,000 concurrent requests hit the API, overwhelming the external services. How do you mitigate this?",
 "To prevent this Cache Stampede, I would implement Mutex Locking (e.g., using Redis `SETNX`). The first request acquires a lock, queries the external services, and updates the cache. The other 999 requests wait for the lock to release or return a slightly stale cached version. Alternatively, implement asynchronous background cache refreshing before expiration.",
 ["Implement Mutex Locking (e.g., Redis SETNX)", "Only one thread fetches the data, others wait or read stale data", "Alternatively, use asynchronous background refreshing before expiration"],
 ["Tell the users to stop refreshing the page"]),

("BE_CA", "tradeoff", "hard", "tradeoff", ["Caching"],
 "What are the tradeoffs of caching data locally in the application's memory (e.g., Guava cache/Caffeine) versus caching it in a distributed system like Redis?",
 "Local in-memory caching is blisteringly fast (zero network hops) and immune to network partitions, but causes extreme memory bloat across instances, causes cache incoherence (stale data) across a fleet of load-balanced servers, and loses data on restarts. Distributed caching (Redis) guarantees consistency across the fleet and saves app memory, but introduces network latency, serialization overhead, and a central point of failure.",
 ["Local: zero network latency, but causes memory bloat and cache incoherence across servers", "Distributed (Redis): guarantees global consistency, saves app memory", "Distributed introduces network latency, serialization, and point of failure"],
 ["Local caching requires purchasing physical RAM sticks"]),

("BE_CA", "implement", "medium", "implementation", ["Caching Strategies"],
 "How would you design a caching strategy for an e-commerce product catalog where prices change dynamically every few minutes, but product descriptions rarely change?",
 "I would use Cache Segmentation. I would cache the static 'Product Details' (descriptions, images) with a long TTL (e.g., 24 hours) or invalidate them via events. I would cache the highly volatile 'Pricing and Inventory' data separately with a very short TTL (e.g., 30 seconds), or entirely bypass the cache for price lookups to ensure transaction accuracy.",
 ["Use Cache Segmentation (split volatile and static data)", "Cache static details (descriptions) with long TTLs", "Cache volatile data (prices) with extremely short TTLs or query DB directly"],
 ["Cache everything together for 10 years to save money"]),

# ---------------- BE_DB ----------------
("BE_DB", "explain", "easy", "concept", ["Databases"],
 "What is a Database Connection Pool, and why is it necessary for backend web applications?",
 "Opening a new TCP connection and authenticating with a database is computationally expensive and slow. A connection pool maintains a set of warm, pre-established, reusable database connections. The backend application borrows a connection, runs its query, and returns it to the pool, drastically reducing latency and preventing the database from crashing due to connection overload.",
 ["Maintains pre-established, reusable DB connections", "Opening new DB connections per request is incredibly slow and expensive", "Reduces query latency and protects the DB from connection exhaustion"],
 ["A pool of water used to cool down database servers"]),

("BE_DB", "scenario", "medium", "scenario", ["Concurrency"],
 "Two users simultaneously attempt to purchase the absolute last item in stock. Both read the stock as '1' and both successfully checkout, leaving the stock at '-1'. How do you resolve this race condition using the database?",
 "I would use Optimistic Locking by adding a `version` column. `UPDATE stock SET qty=0, version=2 WHERE item=X AND version=1`. The second user's update will affect 0 rows, triggering a failure. Alternatively, I would use Pessimistic Locking with `SELECT ... FOR UPDATE`, locking the row exclusively during the first user's transaction so the second user's read is blocked until completion.",
 ["Optimistic Locking: use a version column and check for affected rows", "Pessimistic Locking: use SELECT ... FOR UPDATE to explicitly lock the row", "Either prevents the race condition at the database level"],
 ["Delete the item from the database so no one can buy it"]),

("BE_DB", "tradeoff", "medium", "tradeoff", ["ORMs"],
 "What tradeoffs exist when using an Object-Relational Mapper (ORM) versus writing raw SQL queries for a backend application?",
 "ORMs provide massive developer productivity, type safety, prevent SQL injection automatically, and abstract away database dialects. However, ORMs often generate horribly inefficient queries (e.g., N+1 problems), hide complex performance bottlenecks, and make complex analytical queries (aggregations, window functions) very difficult to write compared to raw, optimized SQL.",
 ["ORM: high developer velocity, type safety, prevents SQL injection", "ORM: generates inefficient queries (N+1), hides performance issues", "Raw SQL: absolute performance control, essential for complex analytics"],
 ["ORMs are always faster than raw SQL"]),

("BE_DB", "implement", "hard", "implementation", ["Security & Migrations"],
 "How would you design a reliable mechanism to safely migrate millions of user passwords from a legacy hashing algorithm (like MD5) to a modern algorithm (like Argon2) without forcing all users to instantly reset their passwords?",
 "Because hashes are one-way, you cannot simply decrypt them. Add a new `argon_hash` column. When a user successfully logs in, the backend verifies their plaintext password against the old MD5 hash. Upon success, the backend immediately hashes that plaintext password with Argon2 in memory, saves it to the new column, and sets a flag. Over time, active users seamlessly migrate themselves.",
 ["You cannot reverse hashes; migration must happen seamlessly at login", "Verify old MD5 hash, then immediately generate Argon2 hash with the plaintext password", "Save the new hash to the DB and update authentication logic"],
 ["Use a highly advanced quantum computer to reverse the MD5 hashes"]),

("BE_DB", "debug", "medium", "debugging", ["Connection Pooling"],
 "A backend service starts logging `Connection acquisition timed out` errors from its connection pool. The database server itself reports virtually zero CPU usage and plenty of available memory. What application-level issue usually causes this?",
 "This indicates a Connection Leak in the backend code. The application is successfully borrowing connections from the pool but failing to return/close them (often because an exception was thrown and the `close()` method was not in a `finally` block). The pool empties, and new threads timeout waiting for a connection, while the database sits completely idle.",
 ["Application is suffering from a Connection Leak", "Connections are borrowed but never closed/returned to the pool", "Causes pool exhaustion while the database server remains idle"],
 ["The database CPU is too fast for the application"]),

("BE_DB", "fundamentals", "easy", "concept", ["ORMs"],
 "What is the 'N+1 Query Problem' in backend development, and how does it typically manifest?",
 "The N+1 problem occurs when an ORM executes 1 query to fetch a list of N parent records (e.g., 50 Authors), and then executes N additional individual queries to fetch the related child records (e.g., 1 query for each Author's Books). This results in 51 database queries instead of 1 optimized `JOIN`, severely degrading backend performance.",
 ["Fetching N parent records, then executing N individual queries for their children", "Caused by lazy loading in ORMs", "Results in catastrophic latency; fixed by using Eager Loading or explicit JOINs"],
 ["It means writing N plus 1 lines of code"]),

("BE_DB", "scenario", "hard", "scenario", ["Batch Processing"],
 "A backend job performs a massive data migration using a single database transaction that takes 45 minutes. Halfway through, the database runs out of transaction log space and rolls back. How do you redesign this batch process to be safe and resumable?",
 "Never use massive, long-running transactions. Redesign the job to process in small, bounded chunks (e.g., 1,000 rows per transaction) ordered by a primary key or timestamp cursor. Maintain state (the last processed ID) in a separate tracking table. If the job crashes, it simply resumes from the last successfully committed chunk ID, completely avoiding massive locks and log exhaustion.",
 ["Never use massive long-running transactions (exhausts locks/logs)", "Process in small chunks (e.g., 1000 rows per ACID transaction)", "Save cursor state (last processed ID) to allow safe resumption on failure"],
 ["Buy a larger hard drive for the transaction logs"]),

# ---------------- BE_RE ----------------
("BE_RE", "explain", "easy", "concept", ["API Design"],
 "Explain the concept of Idempotency in the context of REST API design. Which HTTP methods are strictly defined as idempotent?",
 "Idempotency means that making the exact same API request multiple times yields the same system state as making it exactly once. It allows clients to safely retry requests after network timeouts. By standard, `GET`, `PUT`, `DELETE`, and `HEAD` are strictly defined as idempotent, whereas `POST` is explicitly not.",
 ["Multiple identical requests yield the same state as a single request", "Allows safe automated retries on network failure", "GET, PUT, DELETE are idempotent (POST is not)"],
 ["It means the API returns an error if you call it twice"]),

("BE_RE", "tradeoff", "medium", "tradeoff", ["Resilience"],
 "What are the tradeoffs of implementing automated retries for failing API calls versus immediately failing the request and returning an error to the user?",
 "Automated retries silently mask transient network blips and improve user experience without requiring manual intervention. However, aggressive retries exponentially increase network load during an outage, causing 'Retry Storms' that essentially DDoS struggling downstream services. Fast failing protects system resources and alerts the user immediately, but requires the user to manually retry the action.",
 ["Retries: mask transient errors, improve UX, but risk DDoS'ing struggling downstream services", "Fast Fail: protects system resources, gives instant feedback, degrades UX", "Retries require complex tuning (exponential backoff/jitter) to be safe"],
 ["Retries cost money per HTTP request"]),

("BE_RE", "scenario", "medium", "scenario", ["Payment Processing"],
 "A payment gateway API responds with a `504 Gateway Timeout` after you submit a charge request. You do not know if the charge succeeded. How do you safely handle this without double-charging the customer?",
 "You must design the API to use an Idempotency Key (e.g., a unique UUID generated by the client). Send the Idempotency Key in an HTTP header with the `POST` request. If a timeout occurs, the client safely retries the exact same request with the exact same key. The payment gateway checks the key; if already processed, it simply returns the cached success response without charging again.",
 ["Use an Idempotency Key (unique UUID generated by the client)", "Send the key in an HTTP header with the POST request", "Gateway caches the result by key and prevents duplicate processing"],
 ["Refund all transactions automatically to be safe"]),

("BE_RE", "implement", "hard", "implementation", ["Circuit Breakers"],
 "How would you design a Circuit Breaker pattern from scratch? What states must it track, and what conditions trigger the transitions between those states?",
 "The Circuit Breaker tracks three states. `CLOSED`: Traffic flows normally. If the failure rate (e.g., 500s or timeouts) exceeds a configured threshold in a time window, it transitions to `OPEN`. `OPEN`: All requests are instantly rejected (fast-fail) to give the downstream service time to recover. After a timeout, it transitions to `HALF-OPEN`. `HALF-OPEN`: A limited number of test requests are allowed through. If they succeed, transition to `CLOSED`; if they fail, revert to `OPEN`.",
 ["Track three states: CLOSED, OPEN, HALF-OPEN", "Transition CLOSED -> OPEN on failure rate threshold breach (fast fail)", "Transition OPEN -> HALF-OPEN after a timeout to test recovery"],
 ["The states are ON, OFF, and STANDBY"]),

("BE_RE", "debug", "medium", "debugging", ["Retry Algorithms"],
 "Your backend service implements retries with exponential backoff for a failing downstream dependency. However, when the dependency recovers, it is instantly crushed by traffic and crashes again. What critical mathematical technique is missing from your backoff algorithm?",
 "The algorithm is missing 'Jitter' (randomization). With pure exponential backoff, thousands of concurrent failing clients will all wait exactly 2 seconds, then 4 seconds, then 8 seconds, creating massive synchronized traffic spikes (the Thundering Herd problem) that repeatedly crash the recovering service. Adding random jitter (e.g., 4 seconds +/- random milliseconds) smooths out the retry distribution.",
 ["Missing 'Jitter' (randomized delay addition)", "Pure backoff causes synchronized 'Thundering Herd' spikes", "Jitter spreads out the retries smoothly over time"],
 ["The algorithm needs to be written in C++"]),

("BE_RE", "explain", "easy", "concept", ["Architecture"],
 "What is Graceful Degradation in backend architecture?",
 "Graceful degradation is a design philosophy where a system is architected to continue functioning, albeit with reduced features or performance, when a component fails. Instead of returning a fatal 500 error, an e-commerce site might disable the personalized recommendation engine and fall back to generic top-sellers, allowing users to continue checking out.",
 ["System continues to function with reduced features during failures", "Prevents fatal global errors (500s) from non-critical component failures", "Example: showing generic products when the recommendation engine fails"],
 ["It means writing apology letters to users when the site crashes"]),

("BE_RE", "scenario", "hard", "scenario", ["High Availability"],
 "A critical microservice heavily depends on Redis for caching user session state. Redis goes down completely for 30 minutes. How do you architect the service to gracefully degrade rather than returning 500 errors to all users?",
 "To achieve graceful degradation without the state store, I would configure the application to intercept the Redis failure and automatically switch to stateless session management by issuing JWTs (JSON Web Tokens) encoded with the critical session claims directly to the client. Alternatively, I would fall back to a slower, persistent database strictly for core session validation, discarding non-critical cached data.",
 ["Catch connection errors and prevent them from throwing 500s", "Fallback to stateless tokens (JWTs) for core authentication", "Fallback to a persistent database (Postgres) temporarily with reduced features"],
 ["Tell the users to wait 30 minutes"]),

# ---------------- BE_SC ----------------
("BE_SC", "fundamentals", "easy", "concept", ["Scaling"],
 "What is the difference between Vertical Scaling (Scaling Up) and Horizontal Scaling (Scaling Out)?",
 "Vertical scaling means adding more CPU, RAM, or disk to a single existing machine; it requires downtime and eventually hits a physical hardware limit. Horizontal scaling means adding more concurrent machines (instances) to a load-balanced pool; it provides infinite scale and high availability, but requires the application architecture to be stateless.",
 ["Vertical (Up): Adding more CPU/RAM to a single machine (hits physical limits)", "Horizontal (Out): Adding more machines to a load-balanced pool", "Horizontal requires stateless application architecture"],
 ["Vertical scaling means moving servers to a higher floor in the building"]),

("BE_SC", "tradeoff", "medium", "tradeoff", ["Load Balancing"],
 "What tradeoffs exist between relying on 'Sticky Sessions' (Session Affinity) at the load balancer versus maintaining stateless backend application servers?",
 "Sticky sessions allow you to store user state (like a shopping cart) purely in the memory of one specific backend server, making development incredibly easy, but creating massive headaches: if that server crashes, the user loses their state, and traffic cannot be balanced evenly across the cluster. Stateless backends allow perfect load balancing and seamless failure recovery, but require externalizing state to a distributed cache (like Redis), increasing architectural complexity.",
 ["Sticky Sessions: easy to develop, but creates uneven load balancing and data loss on crashes", "Stateless: perfect load balancing and resilience", "Stateless: requires complex external state stores (Redis/Memcached)"],
 ["Sticky sessions literally glue the server to the rack"]),

("BE_SC", "scenario", "medium", "scenario", ["Queuing"],
 "A sudden viral social media post drives 100x normal traffic to your backend registration API, overwhelming your database. You cannot scale the database fast enough. How do you use asynchronous queuing to absorb this traffic spike?",
 "I would implement Load Leveling (or Queue-Based Load Leveling). The registration API would instantly validate the payload, place the 'Registration Request' into a high-throughput message queue (like SQS or Kafka), and return a `202 Accepted` to the user immediately. Background workers then consume from the queue at a controlled rate that the database can safely handle, smoothing out the massive spike.",
 ["Implement Load Leveling using a Message Queue", "API places the request in the queue and returns 202 Accepted instantly", "Background workers process the queue at a safe, controlled rate for the database"],
 ["I would turn off the website until traffic dies down"]),

("BE_SC", "implement", "hard", "implementation", ["WebSockets"],
 "How would you approach designing a horizontal scaling strategy for a stateful WebSocket backend (like a chat application) where clients must maintain persistent connections to specific servers?",
 "Because WebSockets are persistent TCP connections, standard round-robin scaling doesn't work for message routing. I would use a Pub/Sub message broker (like Redis Pub/Sub or Kafka) as a central backplane. When User A (on Server 1) sends a message to User B (on Server 2), Server 1 publishes the message to the Redis channel. Server 2 is subscribed, receives it, and pushes it down the persistent WebSocket connection to User B.",
 ["WebSockets are persistent and stateful; standard load balancing doesn't route cross-server messages", "Implement a central Pub/Sub backplane (Redis Pub/Sub or Kafka)", "Servers publish messages to the backplane, and subscribe to route them to connected clients"],
 ["WebSockets can be scaled easily using a standard HTTP load balancer without modifications"]),

# ---------------- BE_OB ----------------
("BE_OB", "explain", "easy", "concept", ["Observability"],
 "What is Distributed Tracing, and why is it essential in a microservices architecture?",
 "Distributed Tracing tracks a single user request as it traverses across dozens of independent microservices. It passes a unique `trace_id` via HTTP headers. It is essential because when an API takes 5 seconds, standard logs cannot easily identify which specific downstream service or database query caused the bottleneck. Tracing visualizes the latency of every hop in a waterfall graph.",
 ["Tracks a single request across multiple microservices using a trace_id", "Passes context via HTTP headers", "Visualizes latency per hop to instantly identify distributed bottlenecks"],
 ["Tracing is drawing diagrams of the server racks"]),

("BE_OB", "scenario", "medium", "scenario", ["Production Debugging"],
 "A backend service occasionally spikes to 100% CPU usage for exactly 2 minutes every hour at the top of the hour. There is no corresponding spike in HTTP traffic. How do you approach debugging this?",
 "This deterministic, time-based pattern (top of the hour) heavily indicates a scheduled background task. I would look for internal Cron jobs, aggressive Garbage Collection cycles, log rotation scripts, or batched database aggregations running on the host. I would verify this by checking the application scheduler logs or generating a CPU flame graph during the spike.",
 ["Deterministic time-based spikes indicate scheduled background tasks", "Investigate Cron jobs, log rotations, or batch processing", "Use CPU profiling (flame graphs) during the spike to identify the specific thread"],
 ["It is a hacker trying to breach the system every hour"]),

("BE_OB", "tradeoff", "medium", "tradeoff", ["Logging"],
 "What tradeoffs exist between aggressively logging every backend function call (DEBUG level) for maximum visibility versus only logging warnings and errors in a high-throughput production environment?",
 "Aggressive logging provides massive visibility for debugging complex logic, but in high-throughput systems, string formatting and synchronous disk/network I/O for logging can utterly consume the CPU and crash the application. It also results in exorbitant storage costs (e.g., Datadog/Splunk bills) and risks leaking PII. Error-only logging is cheap and performant, but leaves you blind when trying to trace the steps leading up to an error.",
 ["DEBUG: maximum visibility, but massive CPU/IO overhead and exorbitant vendor costs", "Error-only: highly performant and cheap, but provides no context leading up to a crash", "DEBUG logging risks leaking sensitive PII"],
 ["Logs take up absolutely zero disk space in modern clouds"])
]
