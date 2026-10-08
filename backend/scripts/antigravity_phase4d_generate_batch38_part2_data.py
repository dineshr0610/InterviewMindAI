import os

ROLE = "Backend Developer"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b3": ("Architecture", "Bottlenecks", "System Design", ["Backend Developer", "Full Stack Developer"]),
    "b4": ("API Evolution", "REST", "HTTP", ["Backend Developer", "Full Stack Developer"]),
    "b5": ("Traffic Management", "Load Balancing", "Architecture", ["Backend Developer", "DevOps / Cloud Engineer"]),
    "b6": ("Scalability", "Queues", "Architecture", ["Backend Developer"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    (
        "b3",
        "architecture",
        "medium",
        "architectural",
        ["Architecture", "Queues"],
        "You are designing a webhook delivery subsystem to dispatch real-time events to thousands of third-party external servers. How do you architect this system to handle unreliable subscriber endpoints without bottlenecking your core backend processing?",
        "A webhook delivery system must decouple outbound HTTP calls from core application workflows because third-party servers are inherently slow, unreliable, and prone to downtime. The architecture utilizes an asynchronous worker queue (e.g., RabbitMQ, SQS, or Celery). When an event occurs, the core backend publishes a webhook delivery job to the queue and immediately returns a success response to the user. A dedicated pool of background workers consumes these jobs and executes the outbound HTTP POST requests. To handle unreliability, the workers implement an Exponential Backoff retry strategy with jitter (e.g., retrying after 1s, 2s, 4s, 8s) to avoid overwhelming recovering subscriber servers. If the subscriber fails consistently after the maximum retry attempts, the worker routes the message to a Dead-Letter Queue (DLQ) for monitoring, alerting, or manual inspection. Additionally, outbound timeouts must be strictly enforced to prevent worker thread exhaustion.",
        [
            "Architects an asynchronous decoupling using queues and background workers.",
            "Specifies exponential backoff with jitter for retries and the use of Dead-Letter Queues (DLQs) for terminal failures."
        ],
        [
            "Suggests making blocking, synchronous HTTP calls to third-party webhooks directly during the core request lifecycle.",
            "Fails to mention retry strategies, timeouts, or failure isolation."
        ]
    ),
    (
        "b4",
        "optimize",
        "medium",
        "best_practices",
        ["API Evolution", "Performance"],
        "Your standard REST API payloads are consuming too much bandwidth for mobile clients on cellular networks. How do you optimize payload size dynamically without breaking the API schema for existing web clients?",
        "To optimize bandwidth without breaking the REST schema, you can implement 'Sparse Fieldsets' at the API layer. By allowing the client to specify exactly which fields it needs via query parameters (e.g., `GET /users/123?fields=id,name,email`), the backend dynamically prunes the JSON response, omitting massive nested objects or irrelevant arrays that the mobile client does not require. Alternatively, adopting GraphQL completely shifts this control to the client, allowing precise field selection by design. On the transport layer, ensure the API Gateway or reverse proxy is configured to negotiate and apply HTTP compression (gzip or Brotli) by respecting the `Accept-Encoding` header. Together, sparse fieldsets reduce the logical size of the payload, while Brotli/gzip compresses the physical size over the wire, optimizing mobile latency without impacting web clients that request the full payload.",
        [
            "Proposes Sparse Fieldsets (or GraphQL) to allow clients to request only required fields.",
            "Recommends transport-level HTTP compression (gzip/Brotli) to reduce physical payload size."
        ],
        [
            "Suggests creating an entirely separate `/mobile-api/` with hardcoded smaller responses.",
            "Advises removing fields permanently from the main API, violating backward compatibility."
        ]
    ),
    (
        "b4",
        "architecture",
        "medium",
        "architectural",
        ["API Evolution", "Architecture"],
        "When designing a backward-compatible evolution strategy for a public developer REST API, what are the architectural tradeoffs between URI path versioning, Query Parameter versioning, and Content Negotiation (Header) versioning?",
        "URI Path Versioning (e.g., `/v1/users` to `/v2/users`) is the most common and pragmatic approach; it explicitly routes traffic at the API Gateway level, is highly cacheable, and easily discoverable by developers in a browser, but it violates strict REST purism because the same resource entity has multiple different URIs. Query Parameter Versioning (e.g., `/users?version=2`) is simple to implement within application routing but can complicate CDN caching logic if query strings aren't properly configured. Content Negotiation (Header Versioning, e.g., `Accept: application/vnd.myapi.v2+json`) is the most strictly REST-compliant approach, preserving a single unique URI for the resource. However, it is significantly harder for developers to test manually via browser URLs, complicates API documentation, and requires more sophisticated reverse-proxy inspection to route traffic to different backend microservice versions.",
        [
            "Analyzes URI versioning as pragmatic and cache-friendly but less REST-pure.",
            "Analyzes Header versioning (Content Negotiation) as REST-pure but difficult for developer experience and testing."
        ],
        [
            "Claims that API versioning is unnecessary if you use JSON.",
            "Fails to identify how API Gateways route traffic differently based on path versus header inspection."
        ]
    ),
    (
        "b4",
        "diagnose",
        "medium",
        "problem_solving",
        ["API Evolution", "Testing"],
        "Your team deploys a 'non-breaking' update to a REST API. However, legacy mobile clients immediately start failing to parse the response and crash. You simply added a new, mandatory nested object to the JSON payload. Why did this break the clients, and how do you diagnose it?",
        "While adding a new field to a JSON response is generally considered a backward-compatible, non-breaking change according to API evolution rules (like OpenAPI specification guidelines), poorly implemented client parsers can break. If the legacy mobile client utilizes strict, rigid deserialization logic (e.g., failing on unknown properties in Jackson `FAIL_ON_UNKNOWN_PROPERTIES=true` or rigid struct mapping in Go/Swift without omitempty), the unexpected new field causes the parser to throw a fatal exception. To diagnose, you inspect mobile client crash logs or APM error traces looking for deserialization mapping errors. To prevent this, backend teams must test against Consumer-Driven Contracts (e.g., using Pact) to verify how actual clients parse payloads. In the short term, you must rollback the API deployment or emit the new field conditionally based on client API version headers.",
        [
            "Identifies strict client-side JSON deserialization (failing on unknown fields) as the root cause of the breakage.",
            "Recommends diagnostic logs on the client and long-term prevention using Consumer-Driven Contract testing (e.g., Pact)."
        ],
        [
            "Suggests that adding a field is always a breaking change and requires bumping to `/v2/`.",
            "Claims the failure is caused by a database migration rather than client parsing logic."
        ]
    ),
    (
        "b4",
        "compare",
        "easy",
        "conceptual",
        ["API Evolution", "Architecture"],
        "When architecting communication between internal microservices, what operational and performance differences lead you to choose gRPC over traditional REST JSON?",
        "Traditional REST JSON relies on text-based serialization over HTTP/1.1. It is highly readable, easy to debug with standard tools (cURL, Postman), and universally supported, but it suffers from bulky payload sizes, slow parsing overhead, and relies on untyped implicit contracts unless strict OpenAPI schemas are enforced. gRPC operates over HTTP/2, utilizing Protocol Buffers (Protobuf) for binary serialization. gRPC is significantly faster and uses less bandwidth due to dense binary packing. It enforces strict, strongly-typed contracts via `.proto` files, which auto-generate client and server stubs in multiple languages, eliminating boilerplate parsing code. Furthermore, gRPC natively supports bidirectional streaming and multiplexing. You choose gRPC for high-performance, low-latency, strictly-typed internal microservice-to-microservice communication, whereas REST JSON remains superior for external public-facing APIs or browser clients.",
        [
            "Highlights gRPC's binary Protobuf serialization and HTTP/2 multiplexing for performance and low latency.",
            "Emphasizes gRPC's strictly typed contract generation vs REST's text-based, loosely typed nature."
        ],
        [
            "Claims gRPC runs over HTTP/1.1 and uses JSON natively.",
            "Asserts that REST is strictly typed and faster for internal backend communication."
        ]
    ),
    (
        "b4",
        "architecture",
        "hard",
        "architectural",
        ["API Evolution", "Security"],
        "You are refactoring a monolithic backend into 50 microservices. How do you architect an API Gateway pattern to handle protocol translation, authentication offloading, and rate limiting without introducing a monolithic bottleneck?",
        "An API Gateway acts as the single entry point for all client requests, isolating external clients from internal microservice topologies. To handle protocol translation, the Gateway accepts external REST/JSON or GraphQL queries and internally routes them to microservices via gRPC or message queues. To offload authentication, the Gateway integrates with an Identity Provider (IdP); it validates incoming JWTs or OAuth tokens, terminates the external security context, and passes trusted, parsed identity headers (like `X-User-Id`) to downstream services, relieving them of cryptographic validation overhead. To avoid becoming a monolithic bottleneck or single point of failure, the Gateway must be stateless and horizontally scalable (e.g., Kong, Envoy, AWS API Gateway). Rate limiting is executed at the Gateway using distributed Redis counters. Finally, configuration should be decoupled using declarative routing rules managed by CI/CD (e.g., GitOps), preventing the Gateway repository from becoming an organizational bottleneck.",
        [
            "Details authentication offloading (validating JWTs and passing trusted internal headers to microservices).",
            "Explains the necessity of a stateless, horizontally scalable gateway to prevent a monolithic bottleneck."
        ],
        [
            "Recommends implementing complex business logic and database queries directly inside the API Gateway.",
            "Suggests that every microservice should handle its own external JWT validation and rate limiting."
        ]
    ),
    (
        "b5",
        "diagnose",
        "hard",
        "problem_solving",
        ["Traffic Management", "Networking"],
        "Your Layer 7 load balancer is distributing traffic across 10 identical backend pods. However, diagnostics reveal that 2 pods are sitting at 100% CPU while the other 8 are near 0%. The load balancer is configured for Round Robin. How do you diagnose and fix this uneven traffic distribution?",
        "This severe traffic imbalance, despite a Round Robin configuration, is typically caused by persistent HTTP Keep-Alive connections combined with a lack of request-level spreading. In HTTP/1.1 or HTTP/2, clients or intermediary proxies establish a persistent TCP connection to the load balancer, and the Layer 7 load balancer maintains a persistent connection to the backend pod. If a few very high-throughput clients connect, their traffic is pinned to the specific backend pod that accepted the initial connection. To diagnose, inspect the load balancer's active connection count versus the request rate per backend node. To fix this, configure the Layer 7 load balancer (e.g., HAProxy, Nginx, Envoy) to balance at the HTTP request level rather than the connection level by terminating Keep-Alives appropriately, enforcing a `max_requests_per_connection` limit on the backend servers to force clients to reconnect and rebalance, or switching the load balancing algorithm to 'Least Connections' rather than naive Round Robin.",
        [
            "Identifies HTTP Keep-Alive connection pinning as the root cause of the traffic imbalance.",
            "Recommends balancing algorithms like 'Least Connections' or enforcing maximum requests per connection to force rebalancing."
        ],
        [
            "Claims Round Robin is broken and suggests manually writing a custom load balancer.",
            "Blames the issue on CPU affinity without addressing the network transport layer."
        ]
    ),
    (
        "b5",
        "optimize",
        "medium",
        "best_practices",
        ["Traffic Management", "Architecture"],
        "During a massive Black Friday event, your backend is receiving 3x its maximum capacity. Scaling up takes 5 minutes, but the system is crashing now. How do you optimize backend degradation using load shedding and request prioritization?",
        "When a backend receives load exceeding its capacity, accepting all requests leads to resource exhaustion, elevated latency, and total cascading failure where zero requests succeed. To optimize degradation, the backend must implement Load Shedding. By monitoring critical internal signals (e.g., thread pool queue depth, CPU utilization, or event loop lag), the backend actively rejects excess incoming requests with HTTP 503 (Service Unavailable) or 429 (Too Many Requests) *before* processing them, preserving capacity to successfully serve a subset of traffic. To execute this intelligently, implement Request Prioritization: assign priority tiers to API routes or user tokens. During shedding, immediately drop low-priority traffic (e.g., background syncs, analytics payloads, free-tier users) while preserving capacity for high-priority traffic (e.g., checkout transactions, active user sessions). This ensures the most critical business functions survive the overload.",
        [
            "Defines Load Shedding as the deliberate rejection of excess requests to prevent total cascading failure.",
            "Explains Request Prioritization, dropping low-value background traffic to preserve capacity for critical transactional traffic."
        ],
        [
            "Suggests putting a massive buffer queue in front of the application, which only delays the inevitable timeout crash.",
            "Claims the only solution is to wait for the autoscaler to add more servers."
        ]
    ),
    (
        "b5",
        "compare",
        "easy",
        "conceptual",
        ["Traffic Management", "Networking"],
        "When designing a high-throughput video streaming backend, what are the architectural tradeoffs between using a Layer 4 (Transport) load balancer versus a Layer 7 (Application) load balancer?",
        "A Layer 4 load balancer operates at the TCP/UDP transport level. It routes traffic purely based on IP addresses and port numbers without inspecting the packet payload. Because it performs simple NAT (Network Address Translation) or packet forwarding, it offers ultra-high throughput, extremely low latency, and consumes minimal CPU, making it ideal for massive video streaming payloads or non-HTTP protocols. A Layer 7 load balancer operates at the application level (HTTP/HTTPS). It inspects headers, cookies, and URL paths, enabling advanced traffic management such as TLS termination, path-based routing (e.g., routing `/api` vs `/video`), session stickiness, and Web Application Firewall (WAF) inspection. The tradeoff is that Layer 7 requires significantly more compute power to terminate connections, decrypt TLS, inspect payloads, and re-encrypt, introducing higher latency and lower throughput limits compared to Layer 4.",
        [
            "Contrasts Layer 4 (IP/Port routing, high throughput, low latency) with Layer 7 (Header/Path inspection, TLS termination, higher overhead).",
            "Identifies Layer 4 as superior for raw massive throughput (like video streaming) and Layer 7 for intelligent HTTP routing."
        ],
        [
            "Claims Layer 4 load balancers can read HTTP cookies for session stickiness.",
            "Asserts that Layer 7 is always faster because it understands the application."
        ]
    ),
    (
        "b5",
        "architecture",
        "medium",
        "architectural",
        ["Traffic Management", "Distributed Systems"],
        "You are designing a distributed backend consisting of a deep call chain: Service A calls Service B, which calls Service C. How do you architect a circuit breaker topology to prevent cascading failures across this chain?",
        "If Service C experiences a severe database slowdown, Service B's threads will block waiting for a response, eventually exhausting its connection pools. Consequently, Service A will also block and exhaust its resources, leading to a cascading failure across the entire system. To prevent this, Circuit Breakers must be deployed at the outbound HTTP/gRPC client boundary of every calling service. Service B wraps its calls to C in a circuit breaker; if C times out repeatedly or returns 5xx errors exceeding a threshold, B's breaker trips 'Open' and immediately fails fast, rejecting subsequent calls to C without waiting. This preserves B's thread pools. Similarly, Service A wraps its calls to B. Furthermore, the architecture should implement graceful degradation (fallback logic) at each tier, so if B's breaker to C opens, B can return a cached response or a default value to A, stopping the error propagation entirely and preserving user experience.",
        [
            "Explains how thread pool exhaustion cascades up the call chain.",
            "Details deploying circuit breakers at the client boundaries of each service to fail fast and preserve resources.",
            "Suggests implementing fallback logic (graceful degradation) to prevent error propagation."
        ],
        [
            "Suggests increasing the timeout limits on all services to wait longer for Service C.",
            "Places the circuit breaker exclusively on the API Gateway, leaving internal microservices unprotected."
        ]
    ),
    (
        "b5",
        "diagnose",
        "medium",
        "debugging",
        ["Traffic Management", "CI/CD"],
        "During a rolling deployment of your backend application, the Nginx reverse proxy intermittently logs 502 Bad Gateway errors. The application starts up fine, and the errors disappear after the deployment finishes. How do you diagnose and resolve this issue?",
        "A 502 Bad Gateway error during a rolling deployment occurs when the reverse proxy attempts to route traffic to a backend instance that has already shut down its network socket, or when an active connection is abruptly severed by the terminating instance. When the deployment orchestrator (like Kubernetes) sends a `SIGTERM` to the old application process, the application immediately stops accepting new connections and may abruptly terminate active requests. Meanwhile, the reverse proxy is still unaware that the instance is shutting down and continues forwarding traffic. To diagnose, correlate proxy error logs with application shutdown timestamps. To resolve: 1) Implement graceful shutdown in the backend application, catching `SIGTERM` to stop accepting new requests but allowing active in-flight requests to complete before exiting; 2) Add a pre-stop sleep hook to delay the application shutdown slightly, allowing the orchestrator time to deregister the instance's IP from the reverse proxy's upstream pool.",
        [
            "Identifies the race condition between reverse proxy endpoint deregistration and abrupt application termination upon `SIGTERM`.",
            "Recommends implementing application-level graceful shutdown and pre-stop sleep hooks to coordinate network draining."
        ],
        [
            "Blames the 502 errors on syntax errors in the new application code.",
            "Suggests stopping the Nginx proxy completely during every deployment."
        ]
    ),
    (
        "b6",
        "architecture",
        "hard",
        "architectural",
        ["Scalability", "Queues"],
        "You must architect a distributed job processing system where premium customers' jobs are processed before free-tier customers' jobs. How do you design this priority queue topology to ensure strict priority without completely starving the free-tier jobs during peak load?",
        "A naive implementation using a single queue ordered by priority suffers from scaling limitations (distributed sorting is expensive) and strict starvation (free jobs never run if premium jobs continuously arrive). To architect this at scale, use multiple logical queues: one high-priority queue and one low-priority queue (e.g., using RabbitMQ, SQS, or Redis Lists). Dedicated consumer worker pools are assigned to process these queues. To prevent free-tier starvation, implement a weighted worker allocation or a token bucket consumption model. For example, assign 80% of workers exclusively to the premium queue, and 20% to the free queue. Alternatively, workers can poll the premium queue first; if empty, they poll the free queue, but a dedicated subset of workers is restricted to *only* poll the free queue to guarantee baseline throughput. Additionally, implement an aging mechanism (priority escalation) that periodically promotes free-tier jobs to the premium queue if they have waited beyond an acceptable SLA threshold.",
        [
            "Recommends physical/logical separation into multiple priority queues rather than a single sorted queue.",
            "Addresses starvation by assigning weighted worker pools or dedicated consumers.",
            "Suggests job aging/escalation mechanisms to guarantee SLA limits."
        ],
        [
            "Suggests using a massive SQL table with an `ORDER BY priority` query for every single job execution.",
            "Ignores the starvation problem entirely, leaving free-tier jobs permanently blocked."
        ]
    ),
    (
        "b6",
        "optimize",
        "medium",
        "problem_solving",
        ["Scalability", "Queues"],
        "Your backend consumes messages from an Apache Kafka topic. The business logic takes 50ms per message, but you are falling behind the ingestion rate. You have 10 consumer instances, but CPU utilization is low. How do you optimize consumer throughput?",
        "In Kafka, the maximum unit of parallel consumption within a consumer group is dictated by the number of partitions in the topic. If the topic only has 10 partitions, adding more than 10 consumer instances provides zero benefit, as the excess consumers will sit idle. To optimize throughput: 1) Increase the number of partitions in the Kafka topic to allow greater parallel horizontal scaling of consumers; 2) Instead of processing messages one-by-one synchronously, configure the consumer to fetch larger batches (`max.poll.records`) and process the batch asynchronously or using a localized worker thread pool within the application (taking care to manage manual offset commits only after the batch succeeds); 3) Ensure the consumer's `fetch.min.bytes` and `fetch.max.wait.ms` are tuned to reduce network round trips. If processing is I/O bound, wrapping the 50ms business logic in asynchronous futures/promises drastically increases single-node concurrency.",
        [
            "Identifies the fundamental Kafka limitation: parallel consumers cannot exceed partition count.",
            "Suggests increasing topic partitions for horizontal scaling.",
            "Suggests batch processing and asynchronous localized thread pools for vertical scaling."
        ],
        [
            "Suggests deploying 100 consumer instances without altering the partition count.",
            "Recommends migrating from Kafka to a SQL database for faster queueing."
        ]
    ),
    (
        "b6",
        "diagnose",
        "hard",
        "debugging",
        ["Scalability", "Queues"],
        "A backend worker cluster processing messages from an SQS queue (or RabbitMQ) suddenly halts progress. Monitoring shows the queue depth increasing endlessly. You observe that worker pods are frequently crashing and restarting. How do you diagnose and resolve this 'poison pill' message scenario?",
        "A 'poison pill' is a malformed or unexpected message on a queue that deterministicly causes the consumer application to throw an unhandled exception or crash (e.g., a missing required JSON field causing a NullPointerException). Because the worker crashes before acknowledging (ACKing) or deleting the message, the message returns to the queue after its visibility timeout expires. The next worker picks it up and crashes, creating an infinite loop that halts all queue processing. To diagnose, inspect application crash logs for repeating payload signatures or deserialization errors. To resolve: 1) Implement a Dead-Letter Queue (DLQ). Configure the message broker to automatically route messages to the DLQ after a maximum receive count (e.g., `maxReceiveCount = 3`); 2) Wrap the message parsing and business logic in strict `try/catch` blocks within the consumer; if an unrecoverable payload error occurs, the consumer should catch the exception, log it, explicitly ACK/delete the message to remove it, and optionally publish it to an application-level failure topic for investigation.",
        [
            "Accurately defines a poison pill message and the infinite crash/re-queue loop caused by unacknowledged messages.",
            "Provides infrastructure solutions (Dead-Letter Queues / DLQ based on max receive count).",
            "Provides application solutions (try/catch wrapping and explicit ACKing of malformed data)."
        ],
        [
            "Assumes the queue broker itself (SQS/RabbitMQ) has crashed.",
            "Suggests wiping the entire queue and deleting all messages to restore service."
        ]
    ),
    (
        "b6",
        "compare",
        "easy",
        "conceptual",
        ["Scalability", "Architecture"],
        "When designing a distributed event-driven backend, what is the practical difference between 'At-Least-Once' and 'Exactly-Once' delivery semantics, and how does each impact the application logic of the consumer?",
        "At-Least-Once delivery guarantees that a message will be delivered to the consumer, but in failure scenarios (e.g., network timeouts or consumer crashes before acknowledgment), the broker will re-deliver the message. This means the consumer application must be designed to be idempotent—capable of processing the identical message multiple times without corrupting state (e.g., using UPSERT operations or checking idempotency keys). Exactly-Once delivery ensures that a message is processed and impacts the final state exactly one time, regardless of network or broker failures. Achieving true exactly-once semantics end-to-end is notoriously difficult and computationally expensive; it requires transactional guarantees spanning both the message broker (like Kafka Transactions) and the destination database, usually involving two-phase commits. In practice, most scalable backends embrace At-Least-Once delivery combined with strict idempotent application logic rather than paying the massive performance overhead of distributed exactly-once transactions.",
        [
            "Contrasts the duplicate message possibility of At-Least-Once with the strict guarantee of Exactly-Once.",
            "Identifies the critical requirement for consumer idempotency in At-Least-Once architectures."
        ],
        [
            "Claims that all modern queues provide Exactly-Once delivery by default.",
            "Fails to mention idempotency or the performance overhead of exactly-once transactions."
        ]
    ),
    (
        "b6",
        "optimize",
        "medium",
        "best_practices",
        ["Scalability", "Databases"],
        "Your backend receives a massive stream of analytics events (thousands per second) over HTTP and must store them in a relational database. Executing a SQL `INSERT` for each request is causing database connection exhaustion and IOPS throttling. How do you optimize this ingestion path?",
        "Executing thousands of discrete, single-row `INSERT` statements per second incurs massive network overhead, transaction logging overhead, and index rebalancing contention on a relational database. To optimize ingestion, the backend must decouple the HTTP ingestion layer from the database write path using a buffering strategy. When an HTTP request arrives, the backend immediately pushes the event to an in-memory queue, a local file buffer, or a distributed message broker (like Kafka or Redis Streams) and returns a 200 OK. A dedicated asynchronous background worker polls this buffer, accumulating events over a short time window (e.g., 1 second) or batch size (e.g., 1000 records). The worker then executes a single bulk multi-row `INSERT` (e.g., `INSERT INTO analytics (...) VALUES (...), (...), (...)`) or utilizes database-specific fast-load APIs (like PostgreSQL `COPY`). This reduces database transaction overhead by orders of magnitude and maximizes write throughput.",
        [
            "Identifies the overhead of single-row inserts (transactions, network round trips).",
            "Proposes an asynchronous buffering architecture (in-memory or message broker).",
            "Recommends executing bulk/batch SQL inserts or fast-load utilities (e.g., `COPY`)."
        ],
        [
            "Suggests disabling database indexes permanently to speed up writes.",
            "Recommends increasing the connection pool size to 10,000, which will crash the database."
        ]
    ),
    (
        "b6",
        "architecture",
        "medium",
        "architectural",
        ["Architecture", "Databases"],
        "You are architecting a financial ledger backend where strict auditability and historical state reconstruction are mandatory. How does the Event Sourcing pattern fulfill these requirements compared to a traditional CRUD architecture?",
        "In a traditional CRUD (Create, Read, Update, Delete) architecture, the database stores the current state of an entity. When an update occurs, the previous state is overwritten and lost, making it difficult to reliably reconstruct history without fragile trigger-based audit tables. In an Event Sourcing architecture, the system does not store the current state; instead, it stores a strictly ordered, immutable append-only log of every state-changing event (e.g., `AccountCreated`, `FundsDeposited`, `FundsWithdrawn`). The current state is derived dynamically by replaying the sequence of events from inception. This guarantees perfect auditability because the event log is the absolute source of truth. It allows for point-in-time historical reconstruction, enables temporal queries ('what was the balance on Tuesday?'), and pairs naturally with CQRS (Command Query Responsibility Segregation) to project the event log into optimized, read-only materialized views. The tradeoff is increased complexity in handling eventual consistency and event schema evolution.",
        [
            "Contrasts the destructive updates of CRUD with the immutable append-only event log of Event Sourcing.",
            "Explains how state is derived by replaying events, ensuring perfect auditability and point-in-time reconstruction.",
            "Mentions tradeoffs or related patterns like CQRS and read projections."
        ],
        [
            "Confuses Event Sourcing with simply writing error logs to a file.",
            "Claims Event Sourcing is faster for simple read queries than a standard CRUD database."
        ]
    )
]
