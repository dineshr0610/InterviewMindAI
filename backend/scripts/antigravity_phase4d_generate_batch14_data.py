"""Batch 14 question content (Backend Developer). Antigravity-native, no Gemini API."""

ROLE = "Backend Developer"

BUCKET_KEYS = {
    "AP_EV": ("API Evolution", "Versioning", "HTTP", ["Full Stack Developer"]),
    "DS_SY": ("Distributed Systems", "Consistency", "Architecture", ["Architecture", "DevOps / Cloud Engineer"]),
    "RE_EN": ("Reliability", "Retries & Backoff", "System Design", ["DevOps / Cloud Engineer"]),
    "MS_SY": ("Messaging", "Delivery Semantics", "Kafka/RabbitMQ", ["Data Engineer"]),
    "AU_AR": ("Security", "Authorization", "RBAC/ABAC", ["Security Engineer", "Full Stack Developer"]),
    "RL_RT": ("Traffic Management", "Rate Limiting", "System Design", ["DevOps / Cloud Engineer", "Security Engineer"]),
    "OB_TR": ("Observability", "Tracing & Metrics", "Monitoring", ["DevOps / Cloud Engineer"]),
    "BE_TS": ("Testing", "Integration Testing", "System Design", ["Full Stack Developer"]),
    "BG_JB": ("Background Processing", "Job Queues", "Architecture", ["Data Engineer"]),
    "SC_AL": ("Scalability", "Load Distribution", "Architecture", ["Architecture", "Performance Engineer"]),
}

Q = [
# ---------------- AP_EV ----------------
("AP_EV", "fundamentals", "easy", "concept", ["HTTP"],
 "When designing a REST API, what is the difference between URI versioning (e.g., /v1/users) and Header versioning (e.g., Accept: application/vnd.api+json;version=1)?",
 "URI versioning places the version directly in the URL path, making it highly visible, easy to cache, and simple to test in a browser, but it arguably violates strict REST semantics. Header versioning (content negotiation) keeps the URL clean and adheres strictly to REST, but is harder to cache and test manually.",
 ["URI versioning modifies the URL path", "Header versioning uses Accept or custom headers", "URI is easier to cache/test, Header is strictly RESTful"],
 ["Says URI versioning is more secure"]),

("AP_EV", "scenario", "medium", "scenario", ["JSON", "Schema Design"],
 "A production API needs to deprecate a widely used field in a JSON response. How would you approach this schema evolution without breaking existing mobile clients?",
 "I would mark the field as deprecated in the API documentation and OpenAPI spec. I would then add the new, improved field alongside the old one in the response. Both fields must be maintained until telemetry shows the old field is no longer accessed by any active client versions, after which it can be safely removed in a new API version.",
 ["Do not remove the field immediately", "Add the new field alongside the old one", "Use telemetry/metrics to determine when it is safe to remove"],
 ["Just delete the field and send an email to clients"]),

("AP_EV", "implement", "medium", "implementation", ["Webhooks"],
 "How would you design a webhook payload to ensure backward compatibility when adding new event types that old consumers don't understand?",
 "I would include a clear `event_type` field and a `version` field in the payload wrapper. I would explicitly document that consumers must ignore unknown fields and unknown `event_type`s gracefully. This ensures that adding new event types won't crash older consumers that strictly validate payloads.",
 ["Include event_type and version", "Consumers must ignore unknown fields/types", "Graceful fallback for unknown events"],
 ["Change the webhook URL for every new event"]),

("AP_EV", "tradeoff", "hard", "tradeoff", ["Architecture"],
 "What tradeoffs are involved in maintaining multiple major API versions simultaneously versus forcing clients to migrate to the newest version via a strict sunset policy?",
 "Maintaining multiple versions places a massive technical debt burden on backend developers, requiring complex routing and database backward-compatibility adapters, but provides excellent UX for clients. A strict sunset policy keeps the codebase clean and agile, but risks alienating users and requires aggressive communication and rigid deprecation windows.",
 ["Multiple versions: technical debt/complexity vs good client UX", "Sunset policy: clean codebase vs alienated users", "Database adapter complexity"],
 ["Maintaining 10 versions is easy and free"]),

("AP_EV", "debug", "medium", "debugging", ["GraphQL"],
 "An endpoint utilizing GraphQL suddenly starts returning null for a newly added field for some clients but not others. What is a common cause of this partial failure in schema evolution?",
 "In GraphQL, a resolver might be throwing an error for that specific new field. GraphQL is designed to return partial data; it returns `null` for the failed field and populates the `errors` array in the response. The issue is likely a backend bug in the specific resolver function for the new field, perhaps missing a database column.",
 ["Resolver for the new field is throwing an error", "GraphQL returns partial data (null for failed fields)", "Check the 'errors' array in the response"],
 ["GraphQL doesn't support adding new fields"]),

# ---------------- DS_SY ----------------
("DS_SY", "explain", "easy", "concept", ["Architecture"],
 "Explain the difference between strong consistency and eventual consistency in a distributed system.",
 "Strong consistency guarantees that once a write is acknowledged, all subsequent reads from any node will reflect that updated value. Eventual consistency means that if no new updates are made, all nodes will eventually converge to the same value, but reads immediately following a write might return stale data.",
 ["Strong: immediate visibility across all nodes", "Eventual: nodes converge over time", "Eventual risks reading stale data temporarily"],
 ["Eventual consistency means data is eventually deleted"]),

("DS_SY", "tradeoff", "hard", "tradeoff", ["Microservices"],
 "What tradeoffs exist between using the Saga pattern with choreography versus orchestration for a distributed transaction involving four separate microservices?",
 "Choreography uses decentralized events (pub/sub); it has no single point of failure and is highly decoupled, but the business logic becomes hard to track and debug across multiple codebases. Orchestration uses a central controller to command the microservices; it is easier to monitor and reason about the workflow, but the orchestrator becomes a tightly coupled single point of failure.",
 ["Choreography: decentralized, decoupled, hard to track", "Orchestration: centralized, easy to monitor, single point of failure", "Both handle compensating transactions"],
 ["Sagas guarantee strong ACID consistency across microservices"]),

("DS_SY", "scenario", "medium", "scenario", ["Resilience"],
 "A service updates a user's balance in a relational database and then publishes a 'BalanceUpdated' event to a message broker. If the broker is down, the event is lost. How do you guarantee both occur atomically?",
 "Implement the Transactional Outbox pattern. Inside the same database transaction that updates the user's balance, insert a record representing the event into an 'outbox' table. A separate background process (or CDC tool like Debezium) constantly reads the outbox table and reliably forwards the events to the broker.",
 ["Transactional Outbox pattern", "Write event to an outbox table in the same DB transaction", "Separate process forwards to the broker"],
 ["Wrap the DB and message broker in a 2-Phase Commit"]),

("DS_SY", "compare", "hard", "comparison", ["Concurrency"],
 "Compare a distributed lock backed by Redis (e.g., Redlock) with a lock backed by a consensus system like Zookeeper or etcd in terms of safety during network partitions.",
 "Redis-backed locks are generally AP (Available/Partition tolerant) and rely heavily on wall-clock time and TTLs, meaning a prolonged GC pause or network partition can cause two clients to hold the lock simultaneously (unsafe). Zookeeper/etcd are CP (Consistent/Partition tolerant) consensus systems that use monotonically increasing session epochs/fencing tokens, guaranteeing strict lock safety even during severe partitions.",
 ["Redis relies on wall-clock time/TTLs (unsafe under GC/partitions)", "Zookeeper/etcd use consensus and fencing tokens (strictly safe)", "Redis is AP, Zookeeper is CP"],
 ["Redis is perfectly safe for strict financial locking"]),

("DS_SY", "debug", "medium", "debugging", ["Replication"],
 "An application occasionally shows users stale profile data immediately after they update it, but refreshing the page a second later fixes it. How would you diagnose this replication lag issue?",
 "The backend is likely routing writes to the primary database and reads to an asynchronous read-replica. Diagnosing involves checking the replication lag metrics. To fix the UX, implement 'read-your-own-writes' consistency by routing reads to the primary database for a few seconds immediately following a write by that specific user.",
 ["Writes go to primary, reads go to async replica", "Diagnose by checking replica lag metrics", "Implement read-your-own-writes (route to primary temporarily)"],
 ["The browser is caching the database natively"]),

# ---------------- RE_EN ----------------
("RE_EN", "fundamentals", "easy", "concept", ["Networking"],
 "Why is it important to add 'jitter' (randomness) to an exponential backoff retry strategy?",
 "Without jitter, if a downstream service recovers from an outage, hundreds of clients executing exponential backoff might all retry at the exact same synchronized intervals. This creates a 'thundering herd' that instantly takes the service down again. Jitter spreads the retries out over time.",
 ["Prevents the 'thundering herd' problem", "Desynchronizes client retries", "Spreads the load on the recovering server"],
 ["Jitter makes the network packets travel faster"]),

("RE_EN", "scenario", "medium", "scenario", ["Architecture"],
 "A downstream billing service begins throwing 500 Internal Server Error for 50% of requests. How would you design a Bulkhead pattern to prevent this from exhausting the calling service's thread pool?",
 "Use the Bulkhead pattern to isolate resources. Allocate a strictly limited, dedicated thread pool or semaphore specifically for calls to the billing service. Once that small pool is exhausted by slow or failing billing requests, subsequent calls immediately fail fast, preserving the rest of the application's threads for healthy downstream services.",
 ["Isolate resources using a dedicated thread pool or semaphore", "Limit the blast radius of the failure", "Fail fast when the dedicated pool is full"],
 ["The bulkhead pattern means retrying infinitely"]),

("RE_EN", "implement", "medium", "implementation", ["Timeouts"],
 "How would you approach setting appropriate network and read timeouts for an HTTP client calling a third-party payment gateway that typically responds in 200ms but can take up to 5 seconds?",
 "Set a very short connection timeout (e.g., 500ms) because establishing a TCP connection should always be fast. Set a read timeout slightly above their maximum SLA (e.g., 6 seconds). Crucially, ensure the client does NOT automatically retry POST/payment requests on a read timeout, as the transaction may have actually succeeded on the gateway.",
 ["Short connection timeout", "Read timeout slightly above maximum SLA (5-6s)", "Do not auto-retry non-idempotent operations (POSTs)"],
 ["Set both timeouts to infinity"]),

("RE_EN", "debug", "hard", "debugging", ["Microservices"],
 "You notice a 'retry storm' bringing down your internal services. Service A calls B, which calls C. C is slow, causing B to retry, causing A to retry. How do you architect a solution to prevent compounding retries?",
 "Prevent compounding retries by implementing a 'retry budget' or simply enforcing a rule that only the edge-most service (or the client) initiates retries. Intermediate services (like B) should fail fast and pass the error back up. Additionally, use Circuit Breakers at each layer to quickly trip and halt the cascade.",
 ["Only retry at the edge / restrict intermediate retries", "Use Circuit Breakers to halt the cascade", "Implement retry budgets (e.g., max 10% of requests can retry)"],
 ["Add more retries to Service C"]),

("RE_EN", "explain", "medium", "concept", ["Traffic Control"],
 "Explain the concept of backpressure. How does returning a 429 Too Many Requests status code help a backend service survive a traffic spike?",
 "Backpressure is a mechanism where a struggling system signals upstream producers to slow down. Returning a 429 status code actively rejects excess work quickly with minimal CPU/memory overhead, preventing the server's internal queues from filling up and causing catastrophic OOM crashes or massive latency degradation.",
 ["Signals upstream systems to slow down", "Actively rejects work to protect internal resources", "Prevents OOM crashes and extreme latency"],
 ["Backpressure means upgrading the server CPU"]),

# ---------------- MS_SY ----------------
("MS_SY", "fundamentals", "easy", "concept", ["Architecture"],
 "What is the difference between at-most-once and at-least-once delivery semantics in a messaging system?",
 "At-most-once (fire and forget) guarantees the message will never be duplicated, but it might be lost if a failure occurs. At-least-once guarantees the message will be delivered and processed, but in the event of a failure and retry, the consumer might receive the exact same message multiple times.",
 ["At-most-once: no duplicates, might lose messages", "At-least-once: no lost messages, might have duplicates", "At-least-once requires idempotent consumers"],
 ["At-least-once guarantees no duplicates"]),

("MS_SY", "scenario", "hard", "scenario", ["Idempotency"],
 "A background worker processing payment events crashes immediately after charging the credit card but before acknowledging the message to the queue. How do you ensure the retry doesn't double-charge the user?",
 "The worker must be idempotent. Before charging the card, the worker extracts a unique 'transaction_id' from the event and checks the database (or sends it as an idempotency key to the payment gateway). If the ID is already marked as processed or exists at the gateway, the worker safely skips the charge and acknowledges the message.",
 ["Implement idempotency using a unique event ID", "Check DB or pass Idempotency-Key to the gateway", "Skip the charge on retry and acknowledge"],
 ["Catch the crash in a try-catch block to prevent it"]),

("MS_SY", "compare", "medium", "comparison", ["Brokers"],
 "Compare using a standard message queue (like RabbitMQ) with a partitioned commit log (like Apache Kafka) for event-driven backend communication.",
 "RabbitMQ is a smart-broker/dumb-consumer model optimized for task routing, where messages are deleted upon acknowledgment. Kafka is a dumb-broker/smart-consumer append-only log, where messages are retained for days. Kafka excels at massive throughput, event sourcing, and allowing multiple consumers to replay history; RabbitMQ excels at complex routing and competitive consumer task queues.",
 ["RabbitMQ: deletes messages on ack, complex routing", "Kafka: append-only log, retains messages, high throughput", "Kafka allows replayability"],
 ["Kafka is just a faster version of RabbitMQ"]),

("MS_SY", "implement", "medium", "implementation", ["Error Handling"],
 "How would you design a Dead Letter Queue (DLQ) workflow to handle 'poison pill' messages that crash the JSON parser of a consumer service?",
 "The consumer must wrap the parsing logic in a try-catch block. If a permanent error occurs (like malformed JSON), it should immediately reject the message without requeuing it. The broker should be configured to route rejected messages to the DLQ. Engineers can then monitor the DLQ, inspect the bad payload, fix the producer, and discard the poison pill.",
 ["Catch parsing errors and reject without requeuing", "Broker routes rejected messages to DLQ", "Allows monitoring and manual inspection"],
 ["Infinitely retry parsing the bad JSON"]),

("MS_SY", "tradeoff", "hard", "tradeoff", ["Concurrency"],
 "What tradeoffs are involved in attempting to guarantee strict message ordering in a distributed queueing system with multiple concurrent consumer workers?",
 "Strict global ordering generally forces you to use a single consumer (a bottleneck), destroying concurrency and horizontal scalability. In systems like Kafka, you can achieve partial ordering by partitioning data by a key (e.g., user_id), ensuring events for a specific user are ordered and processed by a single consumer thread, while still allowing overall system concurrency across different keys.",
 ["Global ordering destroys concurrency (single consumer bottleneck)", "Partitioning by key allows localized ordering with concurrency", "Strict ordering is very hard to scale"],
 ["Message queues guarantee global ordering automatically"]),

# ---------------- AU_AR ----------------
("AU_AR", "explain", "easy", "concept", ["Security"],
 "Explain the difference between Authentication (AuthN) and Authorization (AuthZ) in a backend system.",
 "Authentication (AuthN) verifies the identity of the user (e.g., checking a username and password to prove 'who you are'). Authorization (AuthZ) verifies whether the authenticated user has the necessary permissions to perform a specific action (e.g., checking if the user is an admin to prove 'what you are allowed to do').",
 ["AuthN: verifies identity (Who you are)", "AuthZ: verifies permissions (What you can do)", "AuthN happens before AuthZ"],
 ["They are exactly the same concept"]),

("AU_AR", "scenario", "medium", "scenario", ["Architecture"],
 "A multi-tenant application uses Role-Based Access Control (RBAC). A user belongs to Tenant A but attempts to access a resource belonging to Tenant B. How do you enforce tenant isolation at the API layer?",
 "Every API endpoint must extract the `tenant_id` from the requested resource (e.g., the URL or database row). The authorization middleware must compare this resource `tenant_id` against the `tenant_id` explicitly bound to the user in their authenticated session or JWT. If they don't match, return a 403 Forbidden.",
 ["Extract tenant_id from the requested resource", "Compare against the tenant_id in the user's JWT/session", "Return 403 Forbidden if mismatched"],
 ["Hide the Tenant B URL so they can't click it"]),

("AU_AR", "implement", "hard", "implementation", ["ABAC"],
 "How would you approach designing an Attribute-Based Access Control (ABAC) system where a user can only edit a document if they are the owner OR if the document is in a 'draft' state and the user is an 'editor'?",
 "Unlike RBAC, ABAC requires evaluating dynamic attributes at runtime. The authorization service must fetch the document metadata (owner_id, status) from the database before granting access. The logic evaluates the user's attributes (id, role) against the resource attributes (owner_id, status) using a policy engine (like OPA or custom code) before proceeding.",
 ["Fetch resource attributes (metadata) dynamically at runtime", "Evaluate user attributes against resource attributes", "Use a policy engine or custom logic layer"],
 ["Encode the document state inside the user's JWT"]),

("AU_AR", "debug", "medium", "debugging", ["Vulnerabilities"],
 "You notice an API endpoint allows any authenticated user to delete any other user's account by modifying the `user_id` in the URL. What is this vulnerability called, and how do you fix it?",
 "This is an Insecure Direct Object Reference (IDOR) or Broken Object Level Authorization (BOLA). Fix it by implementing resource-level authorization checks: before deleting the record, the backend must verify that the authenticated user's ID matches the `user_id` in the URL, or that the user possesses a global 'admin' role.",
 ["Insecure Direct Object Reference (IDOR) / BOLA", "Enforce resource-level authorization checks", "Verify authenticated ID matches requested ID"],
 ["Hash the user_id in the URL to hide it"]),

("AU_AR", "tradeoff", "medium", "tradeoff", ["Microservices"],
 "What are the tradeoffs of handling authorization checks centrally in an API Gateway versus pushing the authorization logic down into the individual microservices?",
 "Centralized AuthZ in the Gateway simplifies microservices and ensures a unified security posture, but struggles with fine-grained, resource-level checks (which require DB lookups). Decentralized AuthZ in the microservices allows complex, data-dependent rules but duplicates policy logic across services and risks inconsistent security enforcement.",
 ["Gateway: unified posture, simpler services, hard to do resource-level checks", "Microservices: enables fine-grained data checks, risks inconsistency", "Gateway lacks context of individual database rows"],
 ["The Gateway can easily query every microservice's database"]),

# ---------------- RL_RT ----------------
("RL_RT", "fundamentals", "easy", "concept", ["Traffic Control"],
 "What is the purpose of rate limiting a public-facing backend API?",
 "Rate limiting protects the backend infrastructure from being overwhelmed by traffic spikes, prevents Denial of Service (DoS) attacks, stops brute-force credential stuffing, and enforces fair usage quotas or billing tiers among API consumers.",
 ["Protects infrastructure from overload/DoS", "Prevents brute-force attacks", "Enforces usage quotas and billing tiers"],
 ["It speeds up database queries"]),

("RL_RT", "explain", "medium", "concept", ["Algorithms"],
 "Explain how the 'token bucket' rate-limiting algorithm works, including the concepts of bucket capacity and refill rate.",
 "In the token bucket algorithm, a 'bucket' holds a maximum capacity of tokens. Tokens are added to the bucket at a constant refill rate (e.g., 10 tokens per second). When a request arrives, it must consume a token. If the bucket is empty, the request is rejected. This allows for brief bursts of traffic up to the bucket's capacity, while enforcing a steady long-term rate.",
 ["Bucket holds a maximum number of tokens (capacity)", "Refills at a constant rate", "Allows traffic bursts up to the capacity"],
 ["It groups requests into a bucket and processes them in batches"]),

("RL_RT", "implement", "hard", "implementation", ["Distributed Systems"],
 "How would you approach designing a distributed rate limiter for a global API using Redis, ensuring that a user's quota is enforced accurately across multiple data centers?",
 "I would use a centralized Redis cluster (or Redis Enterprise with Active-Active replication). To prevent race conditions, I would implement the rate limiting logic (like token bucket or sliding window) entirely inside a Lua script. The backend executes the Lua script atomically on Redis, passing the user's IP or API key as the identifier.",
 ["Centralized Redis for global state", "Use Lua scripts for atomic operations", "Use API key or IP as the identifier"],
 ["Store the limits in a local variable in Node.js"]),

("RL_RT", "scenario", "medium", "scenario", ["Security"],
 "A malicious botnet is bypassing your IP-based rate limiter by rotating thousands of IP addresses. How do you adjust your rate limiting strategy to block the abuse?",
 "IP-based limits are ineffective against distributed botnets. Shift the rate limiting identifier to a more robust dimension: require authentication and limit by User ID or API Token. For unauthenticated endpoints, limit by device fingerprint, session cookie, or utilize a Web Application Firewall (WAF) to detect bot-like behavioral patterns.",
 ["Limit by User ID or API Token instead of IP", "Use device fingerprinting or session cookies", "Deploy a WAF for behavioral analysis"],
 ["Just block all IP addresses entirely"]),

("RL_RT", "compare", "medium", "comparison", ["Algorithms"],
 "Compare the 'fixed window' rate-limiting algorithm with the 'sliding window' algorithm. What specific problem does the sliding window solve?",
 "The fixed window resets the counter at the start of a defined minute/hour, creating a vulnerability where a user can send a massive burst of traffic exactly at the boundary (e.g., 200 requests at 1:59:59 and 200 at 2:00:01). The sliding window rolls the time frame continuously, smoothing out the allowance and preventing boundary burst attacks.",
 ["Fixed window resets at strict boundaries", "Boundary attacks can double the allowed burst", "Sliding window rolls continuously to prevent boundary bursts"],
 ["Fixed window is faster than sliding window"]),

# ---------------- OB_TR ----------------
("OB_TR", "fundamentals", "easy", "concept", ["Tracing"],
 "What is a Correlation ID, and how is it typically passed between microservices?",
 "A Correlation ID is a unique string generated at the entry point of a distributed request (like an API gateway). It is passed to downstream microservices via HTTP headers (e.g., `X-Correlation-ID` or W3C `traceparent`) and included in every log statement, allowing developers to trace the entire lifecycle of a single transaction.",
 ["Unique string generated at entry point", "Passed via HTTP headers", "Included in all log statements for tracing"],
 ["It is a foreign key in the database"]),

("OB_TR", "scenario", "medium", "scenario", ["Logging"],
 "A critical background job fails silently at 3 AM. The logs show the job started but have no error output. How would you improve the structured logging and metrics to diagnose this in the future?",
 "Ensure the job uses structured JSON logging. Add explicit log statements wrapping the execution (e.g., 'started', 'completed_successfully', 'failed'). Crucially, wrap the entire job execution in a global try/catch block that logs any unhandled exceptions with full stack traces. Add a metric counter for job failures to trigger alerting.",
 ["Use structured JSON logging", "Wrap execution in a global try/catch to log unhandled exceptions", "Add metric counters and alerting for failures"],
 ["Just check the logs manually every morning"]),

("OB_TR", "implement", "hard", "implementation", ["OpenTelemetry"],
 "How would you design a distributed tracing strategy (using OpenTelemetry/Jaeger) across a system involving an API Gateway, an async message broker, and a database?",
 "Instrument the API Gateway to generate a Trace ID and root Span. Inject the tracing context into HTTP headers. When a service publishes to the broker, inject the trace context into the message headers/metadata. The consumer extracts the context to continue the trace. Use auto-instrumentation libraries for the DB driver to automatically create child spans for SQL queries.",
 ["Generate Trace ID and inject into HTTP headers", "Inject trace context into message broker headers/metadata", "Use auto-instrumentation for database query spans"],
 ["Send logs to a text file and grep them later"]),

("OB_TR", "debug", "medium", "debugging", ["Performance"],
 "You notice that the 99th percentile (p99) latency of an endpoint is 5 seconds, while the median (p50) is 50ms. What kind of backend bottlenecks typically cause this massive long-tail latency?",
 "A massive gap between p50 and p99 usually indicates intermittent resource exhaustion. Common causes include long Stop-The-World Garbage Collection (GC) pauses, thread pool exhaustion, database connection pool exhaustion, or sudden spikes in noisy neighbor traffic stealing CPU time.",
 ["Stop-The-World Garbage Collection pauses", "Thread/Database connection pool exhaustion", "Intermittent resource contention / noisy neighbors"],
 ["The database is consistently slow for every query"]),

("OB_TR", "tradeoff", "medium", "tradeoff", ["Architecture"],
 "What tradeoffs exist when choosing between logging application errors to stdout/stderr versus having the application directly send logs over the network to an aggregator like Datadog?",
 "Logging to stdout (the 12-factor app pattern) decouples the application from the logging infrastructure; it's highly performant, resilient to network drops, and offloads routing to a daemon (like Fluentbit). Sending directly over the network simplifies infrastructure setup but adds network I/O overhead to the app and risks losing logs if the aggregator endpoint goes down.",
 ["stdout decouples app and is highly performant (12-factor)", "Network logging adds I/O overhead and risks log loss on outage", "Network logging simplifies infrastructure"],
 ["stdout uses too much CPU compared to network logging"]),

# ---------------- BE_TS ----------------
("BE_TS", "fundamentals", "easy", "concept", ["Testing"],
 "Explain the difference between a unit test and an integration test in a backend API context.",
 "A unit test isolates a specific function or class, mocking all external dependencies (like the DB or network) to ensure the logic works in a vacuum. An integration test verifies that multiple components (e.g., the API route, the ORM, and the actual database) work together correctly, usually requiring a real or in-memory database.",
 ["Unit test: isolated, mocks dependencies", "Integration test: tests multiple components together", "Integration usually requires a real database"],
 ["Unit tests take longer to run than integration tests"]),

("BE_TS", "tradeoff", "medium", "tradeoff", ["Mocking"],
 "What are the tradeoffs of heavily mocking the database layer in unit tests versus running tests against a real database instance (e.g., using Testcontainers)?",
 "Mocking the DB makes tests incredibly fast and deterministic, but risks false positives because mocks don't validate SQL syntax, constraints, or unique indexing behavior. Using a real database (Testcontainers) provides absolute confidence that the queries and constraints work, but makes the test suite significantly slower and more complex to orchestrate.",
 ["Mocks: fast, deterministic, but miss SQL/constraint bugs", "Real DB: high confidence, validates SQL", "Real DB: slower execution, complex orchestration"],
 ["Mocks validate SQL syntax automatically"]),

("BE_TS", "scenario", "hard", "scenario", ["Third-Party APIs"],
 "A microservice calls an external third-party API that charges per request. How do you design an integration test suite that proves the code works without incurring costs or failing when the third-party is down?",
 "Do not hit the real API in CI. Instead, use an HTTP mocking tool like WireMock, Nock, or VCR to intercept the outbound HTTP requests and return pre-recorded, deterministic JSON responses. This ensures the integration tests validate the HTTP client parsing and error handling logic locally without touching the internet.",
 ["Use HTTP mocking tools (WireMock, Nock, VCR)", "Return deterministic, pre-recorded responses", "Tests client parsing and error handling without network calls"],
 ["Skip the tests entirely in CI"]),

("BE_TS", "implement", "medium", "implementation", ["Contract Testing"],
 "How would you approach writing a contract test (e.g., using Pact) between a backend provider and a frontend consumer to ensure schema changes don't break the frontend?",
 "The frontend (consumer) defines its expectations (the 'contract') of what the API request and response should look like. This contract is uploaded to a broker. The backend (provider) pulls the contract during its CI pipeline and runs a test against its actual API to ensure the response strictly matches the frontend's expectations.",
 ["Consumer defines the expected request/response contract", "Provider pulls the contract during its CI", "Provider validates its actual API matches the contract"],
 ["Contract tests are just end-to-end Selenium tests"]),

("BE_TS", "debug", "medium", "debugging", ["Flaky Tests"],
 "You notice that backend integration tests are failing intermittently (flaky tests) on the CI server. What are common causes of test flakiness involving the database, and how do you fix them?",
 "Common causes include tests sharing state (not clearing the DB between runs), relying on non-deterministic data (like hardcoded timestamps), or race conditions when running tests in parallel. Fix by wrapping tests in DB transactions and rolling back after each test, avoiding hardcoded dates, and ensuring unique test data.",
 ["Shared database state between tests", "Race conditions from parallel execution", "Fix by rolling back transactions after each test"],
 ["Increase the CI server RAM to stop flakiness"]),

# ---------------- BG_JB ----------------
("BG_JB", "fundamentals", "easy", "concept", ["Architecture"],
 "Why would you choose to offload a task (like generating a PDF report) to a background worker rather than processing it synchronously in the HTTP request?",
 "Generating a PDF is a slow, CPU-intensive task. Doing it synchronously blocks the HTTP request thread, creating a poor user experience (long loading screen) and risking a gateway timeout. Offloading it frees the web server to handle more traffic and allows the PDF to be generated asynchronously and retried on failure.",
 ["Prevents blocking the HTTP request thread", "Improves user experience and avoids timeouts", "Allows asynchronous processing and retries"],
 ["Background workers generate PDFs faster than web servers"]),

("BG_JB", "implement", "medium", "implementation", ["Memory Management"],
 "How would you design a robust background job system that can safely pause and resume processing a massive list of 10 million database rows without running out of memory?",
 "I would not load 10 million rows into memory at once. I would use a cursor-based approach or chunking (fetching 1,000 rows at a time). To support pausing and resuming, the job should record its progress (the last processed ID) to a database or Redis checkpoint after every chunk. On restart, it resumes from the last checkpoint.",
 ["Use chunking or cursors to limit memory usage", "Save the last processed ID (checkpoint) to DB/Redis", "Resume processing from the checkpoint"],
 ["Load all 10 million rows into a global array"]),

("BG_JB", "scenario", "hard", "scenario", ["Concurrency"],
 "A background worker is designed to run once a day to charge subscriptions. Due to a deployment error, two instances of the worker spin up simultaneously. How do you prevent users from being charged twice?",
 "Implement a distributed lock (e.g., using Redis) around the entire cron job to ensure only one instance executes. More importantly, implement idempotency at the database row level: the worker should execute an atomic `UPDATE subscriptions SET status='charged' WHERE id=1 AND status='pending'` to ensure concurrent workers cannot charge the same row.",
 ["Distributed lock on the overall cron job execution", "Database-level atomic updates (optimistic locking)", "Update WHERE status='pending'"],
 ["Just tell DevOps to shut one instance down manually"]),

("BG_JB", "debug", "medium", "debugging", ["Queues"],
 "An application uses a Redis-backed job queue. Jobs are enqueued successfully, but the queue size keeps growing indefinitely and workers seem idle. What would you check to diagnose this?",
 "I would check if the worker processes are actually running and connected to the correct Redis host/queue name. If connected, I would check if all worker threads are deadlocked, waiting indefinitely on a hung network request without a timeout, or if a poison-pill job is crashing the worker loop silently.",
 ["Check if workers are running/connected to correct queue", "Check for thread deadlocks or hung network requests without timeouts", "Check for silent crashes in the worker loop"],
 ["Increase the Redis memory limit"]),

("BG_JB", "compare", "medium", "comparison", ["Architecture"],
 "Compare using a CRON job (scheduled task) with using an event-driven background worker triggered by a message queue for processing user uploads.",
 "A CRON job polls the database on a schedule (e.g., every 5 minutes) looking for new uploads, introducing latency and wasting DB queries when idle. An event-driven worker listens to a queue and processes uploads instantly the moment the user finishes the upload, providing real-time processing and better scalability.",
 ["CRON introduces latency and polls the DB", "Event-driven processes instantly via queues", "Event-driven is more scalable and real-time"],
 ["CRON is always faster because it is built into Linux"]),

# ---------------- SC_AL ----------------
("SC_AL", "explain", "easy", "concept", ["Databases"],
 "Explain the difference between horizontal scaling (scaling out) and vertical scaling (scaling up) a backend database.",
 "Vertical scaling means adding more power (CPU, RAM, faster disks) to a single existing database server. Horizontal scaling means adding more physical servers to the system, distributing the data and read/write load across a cluster of multiple nodes.",
 ["Vertical: adding CPU/RAM to a single server", "Horizontal: adding more servers/nodes to a cluster", "Horizontal distributes the load"],
 ["Horizontal means changing the database schema"]),

("SC_AL", "tradeoff", "medium", "tradeoff", ["Sessions"],
 "What tradeoffs exist between storing user session data in sticky sessions (load balancer level) versus a centralized stateless store like Redis?",
 "Sticky sessions keep routing a user to the same server, meaning sessions live in local memory (fast), but it breaks load distribution, complicates deployments (taking down a server destroys active sessions), and hinders auto-scaling. A centralized Redis store keeps the backend entirely stateless, allowing perfect load balancing and safe scaling, but adds network latency to every request.",
 ["Sticky sessions: fast local memory, but breaks scaling/deployments", "Redis: stateless backends, perfect load balancing", "Redis adds network latency"],
 ["Sticky sessions are highly scalable in the cloud"]),

("SC_AL", "scenario", "hard", "scenario", ["Incident Response"],
 "A stateless backend service is suddenly saturated with traffic, maximizing CPU usage on all instances. The database is completely idle. Auto-scaling takes 5 minutes to add more instances. How do you mitigate the impact in the immediate term?",
 "Since the bottleneck is the application CPU (not the database), you must shed load immediately. Implement rate limiting or feature flagging to disable non-critical CPU-heavy features (like PDF generation or complex search). At the load balancer level, return 429 or 503 errors quickly for excess traffic to prevent the existing nodes from completely crashing until auto-scaling catches up.",
 ["Shed load (return 429/503) at the load balancer", "Disable CPU-heavy non-critical features via feature flags", "Protect existing nodes from catastrophic failure"],
 ["Wait 5 minutes for auto-scaling to fix it"]),

("SC_AL", "implement", "medium", "implementation", ["Sharding"],
 "How would you approach designing a database sharding strategy for a multi-tenant B2B application experiencing massive data growth?",
 "I would shard the database using the `tenant_id` (customer ID) as the shard key, because B2B queries are almost exclusively scoped to a single tenant. This ensures all data for a specific customer lives on the same shard, allowing fast, localized JOIN operations without requiring complex cross-shard aggregations.",
 ["Use tenant_id / customer ID as the shard key", "Keeps all tenant data on a single physical node", "Allows fast, localized JOINs"],
 ["Shard alphabetically by the user's first name"]),

("SC_AL", "debug", "hard", "debugging", ["Architecture"],
 "You notice that an application scales perfectly to 10 instances, but adding instances 11 through 20 actually decreases overall throughput and increases latency. What architectural bottlenecks typically cause negative scaling?",
 "Negative scaling usually points to extreme contention on a shared centralized resource. The new instances are likely exhausting the database connection limit, causing all instances to queue, or they are creating massive lock contention on a single hot row in the database. It could also be network bandwidth saturation at the shared load balancer or database NIC.",
 ["Contention on a shared centralized resource", "Database connection limit exhaustion", "Lock contention on a hot database row"],
 ["The programming language inherently doesn't support more than 10 instances"])
]
