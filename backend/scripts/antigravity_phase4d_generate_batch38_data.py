import os

ROLE = "Backend Developer"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b1": ("Caching", "Distributed Caching", "Redis", ["Backend Developer", "Full Stack Developer"]),
    "b2": ("Concurrency", "Thread Safety", "Architecture", ["Backend Developer", "Java Developer", "Python Developer"]),
    "b3": ("Architecture", "Bottlenecks", "System Design", ["Backend Developer", "Full Stack Developer"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    (
        "b1",
        "optimize",
        "medium",
        "problem_solving",
        ["Caching", "Performance"],
        "Your backend caches millions of small user preference objects in Redis. The memory usage is approaching the instance limit, but scaling up is cost-prohibitive. How can you optimize Redis memory usage for millions of small key-value pairs?",
        "Storing millions of independent string keys in Redis incurs significant memory overhead due to the Redis dictionary data structure and key metadata. To optimize memory footprint, group related small keys into Redis Hashes. Redis applies a memory optimization called 'ziplist' (or 'listpack' in newer versions) for small hashes when the number of fields and their sizes remain below configured limits (`hash-max-ziplist-entries` and `hash-max-ziplist-value`). By sharding the dataset—for example, grouping user preferences into hashes where the key is the user ID divided by 1000, and the field is the remainder—the data is stored in a highly compact, contiguous memory format. This structural change can reduce overall memory consumption by 5-10x compared to storing each user preference as a top-level string key, drastically reducing infrastructure costs.",
        [
            "Identifies that top-level string keys incur high metadata overhead in Redis.",
            "Explains the use of Redis Hashes and the underlying ziplist/listpack memory optimization.",
            "Describes a sharding strategy (e.g., bucketing IDs) to group small keys into hashes."
        ],
        [
            "Suggests compressing the data manually before storing it in string keys without mentioning structural optimizations.",
            "Recommends turning on Redis swap (virtual memory), which is obsolete and severely degrades performance."
        ]
    ),
    (
        "b1",
        "diagnose",
        "medium",
        "debugging",
        ["Caching", "Distributed Systems"],
        "During a product launch, a highly accessed cache key expires, and immediately your backend database CPU spikes to 100%, causing a service outage. What is this phenomenon, and how do you diagnose and resolve it at the application layer?",
        "This phenomenon is known as a 'cache stampede' or 'thundering herd'. It occurs when a heavily requested cached item expires or is evicted, causing hundreds of concurrent application threads to experience a cache miss simultaneously. They all bypass the cache and query the database at the exact same time to recompute the value, overwhelming the database CPU and exhausting connection pools. To diagnose, monitor cache hit/miss ratios and correlate cache misses on hot keys with sudden database CPU spikes. To resolve it at the application layer, implement 'Request Coalescing' (using a concurrency primitive like a mutex, singleflight, or Promise caching) so only the first thread queries the database while others wait for the result. Alternatively, implement 'Probabilistic Early Expiration' (XFetch) to recompute the cache asynchronously before the hard TTL expires, or use a background worker to continuously refresh hot keys.",
        [
            "Accurately defines a cache stampede / thundering herd resulting from concurrent cache misses.",
            "Details application-level solutions such as request coalescing (singleflight), mutex locks, or probabilistic early expiration."
        ],
        [
            "Suggests simply increasing the cache TTL without addressing the concurrent miss behavior when it eventually expires.",
            "Recommends blindly scaling up the database instance as the primary solution."
        ]
    ),
    (
        "b1",
        "architecture",
        "hard",
        "architectural",
        ["Architecture", "Distributed Systems"],
        "When designing a globally distributed caching strategy for a backend API serving users across three continents, what are the architectural tradeoffs between an Active-Passive cache replication model versus an Active-Active cache model?",
        "In an Active-Passive (Primary-Replica) caching architecture, all writes are directed to a single primary region and asynchronously replicated to read-only replicas in other regions. This guarantees strong write consistency and prevents cache conflicts, but introduces high write latency for users far from the primary region and risks stale reads during replication lag. In an Active-Active caching architecture (e.g., Redis Enterprise Active-Active with CRDTs, or multi-master Memcached setups), backend services read and write to their local regional cache. This drastically reduces write latency and improves regional fault tolerance. However, the tradeoffs include significant architectural complexity, the potential for cross-region write conflicts (requiring Conflict-Free Replicated Data Types or Last-Write-Wins resolution), higher infrastructure costs, and eventual consistency anomalies where a user might see different cached states depending on routing.",
        [
            "Contrasts write latency and consistency in Active-Passive with low latency and high availability in Active-Active.",
            "Identifies the complex conflict resolution mechanisms (e.g., CRDTs, LWW) required for Active-Active caching."
        ],
        [
            "Claims that caching data across continents has zero replication lag if using a fast fiber network.",
            "Fails to address write conflicts or consistency models in multi-region setups."
        ]
    ),
    (
        "b1",
        "compare",
        "easy",
        "conceptual",
        ["Caching", "Performance"],
        "When evaluating an in-memory caching tier for a backend service, what are the primary operational and data-structure differences that would lead you to choose Memcached over Redis, or vice versa?",
        "Memcached is a pure, high-performance, multithreaded distributed memory object caching system. It is extremely simple, scales easily by adding nodes, and is highly efficient for flat key-value strings (like rendered HTML fragments or serialized JSON). However, it lacks persistence, complex data types, and built-in replication. Redis is a single-threaded (for command execution) data structure server that supports complex types like Hashes, Lists, Sets, Sorted Sets, and Geospatial indexes. Redis allows atomic operations on these structures (e.g., incrementing a field in a hash or pushing to a list), supports pub/sub messaging, and provides persistence mechanisms (RDB snapshots and AOF logs) as well as native High Availability (Redis Sentinel) and clustering. You choose Memcached for absolute simplicity and multithreaded vertical scaling of flat strings, and Redis when you need advanced data structures, persistence, atomic operations, or pub/sub capabilities.",
        [
            "Highlights Memcached's multithreaded nature and simplicity for flat key-value storage.",
            "Details Redis's support for complex data structures, atomic operations, and persistence."
        ],
        [
            "Claims Memcached supports complex data structures like Lists and Hashes.",
            "Asserts that Redis is fully multithreaded for all command executions."
        ]
    ),
    (
        "b1",
        "optimize",
        "hard",
        "best_practices",
        ["Caching", "Architecture"],
        "In a high-throughput product catalog backend with a 99:1 read-to-write ratio, how do you evaluate and implement the tradeoffs between Write-Through, Write-Around, and Write-Back cache invalidation strategies?",
        "A Write-Through cache strategy writes data simultaneously to both the cache and the backing database. This ensures the cache is always consistent and read operations never experience a cache miss penalty, making it ideal for a 99:1 read-heavy catalog. However, it adds write latency. A Write-Around strategy writes data directly to the database, bypassing the cache; the cache is only populated on a subsequent cache miss. This reduces write latency and prevents the cache from being flooded with data that may not be read, but it imposes a latency penalty on the first read. A Write-Back (Write-Behind) strategy writes data only to the cache, acknowledging the write immediately, and asynchronously flushes it to the database later. This provides the highest write throughput and lowest latency but introduces a critical risk of permanent data loss if the cache node crashes before the flush. For a product catalog requiring high read performance and durability, Write-Through (or a proactive cache invalidation worker) is the optimal pattern.",
        [
            "Accurately defines Write-Through, Write-Around, and Write-Back strategies.",
            "Evaluates the tradeoffs of each in the context of a read-heavy system (latency vs. consistency vs. data loss risk)."
        ],
        [
            "Confuses Write-Back with Write-Through.",
            "Claims that Write-Back is perfectly safe and has no risk of data loss."
        ]
    ),
    (
        "b1",
        "diagnose",
        "medium",
        "problem_solving",
        ["Caching", "Scalability"],
        "Your backend utilizes a distributed Redis cluster with 10 shards. Monitoring alerts show that a single Redis node is pegged at 100% CPU while the other 9 nodes are mostly idle. How do you diagnose and mitigate this hot-key bottleneck?",
        "This uneven load distribution indicates a 'hot key' or 'hot hash tag' problem, where an overwhelmingly high percentage of read/write requests are routed to a single specific key (e.g., a trending product or global configuration flag) that resides on a single shard. To diagnose, you can use the `redis-cli --hotkeys` tool (if maxmemory-policy is LFU), monitor slowlogs, or capture network traffic (`tcpdump` or `MONITOR` command briefly) to identify the specific key. To mitigate the bottleneck at the application layer, implement a local in-memory cache (e.g., Guava Cache, Caffeine, or a simple dictionary) within the backend application instances to cache the hot key for a few seconds. This absorbs the massive read volume before it reaches Redis. Alternatively, for write-heavy hot keys, you can split the key into multiple sub-keys (e.g., `key_1`, `key_2`) spread across the cluster and aggregate them at the application level.",
        [
            "Identifies the root cause as a hot key concentrated on a single cluster shard.",
            "Proposes practical diagnostics (e.g., `redis-cli --hotkeys`) and mitigations like local in-memory caching or key splitting."
        ],
        [
            "Suggests adding more Redis shards to the cluster, which does not solve a single-key bottleneck.",
            "Recommends restarting the overloaded Redis node."
        ]
    ),
    (
        "b2",
        "diagnose",
        "hard",
        "debugging",
        ["Concurrency", "Databases"],
        "Users report being double-charged for purchases on your backend platform. The payment processing service is multi-threaded and runs across multiple application instances. How do you diagnose the root cause of this race condition, and what architectural lock mechanisms solve it?",
        "Double-charging typically occurs due to a 'check-then-act' race condition. When a user double-clicks the checkout button, two concurrent requests reach the backend. Both threads check the database (`SELECT status FROM orders WHERE id=X`), see the order is 'PENDING', and both proceed to call the payment gateway and update the status to 'PAID'. Because the application is distributed across multiple instances, local thread synchronization (like Java's `synchronized` block) fails. To diagnose, correlate application logs using trace IDs to identify identical requests processed simultaneously by different pods. To resolve this, implement distributed locking or database-level locking. You can use an Optimistic Lock by adding a version column (`UPDATE orders SET status='PAID', version=version+1 WHERE id=X AND version=1`). If the second thread attempts the update, the condition fails (version is now 2) and the application aborts. Alternatively, use a Pessimistic Lock (`SELECT ... FOR UPDATE`) to lock the database row, or a distributed Redis lock (Redlock) wrapping the payment gateway call.",
        [
            "Identifies the 'check-then-act' race condition occurring across distributed instances.",
            "Explains why local memory locks (e.g., `synchronized`) fail in distributed environments.",
            "Provides concrete solutions: Optimistic locking (versioning), Pessimistic locking (`FOR UPDATE`), or distributed Redis locks."
        ],
        [
            "Suggests relying solely on frontend UI disablement to prevent double-clicks.",
            "Recommends using local language-level threading locks without realizing the backend is multi-instance."
        ]
    ),
    (
        "b2",
        "optimize",
        "medium",
        "problem_solving",
        ["Concurrency", "Databases"],
        "In a highly concurrent inventory reservation system, multiple users frequently attempt to purchase the last remaining ticket simultaneously. How do you optimize the backend to handle this contention using pessimistic versus optimistic locking?",
        "Pessimistic locking (`SELECT * FROM inventory WHERE item_id=X FOR UPDATE`) acquires an exclusive lock on the database row at the start of the transaction. It prevents concurrent modifications but forces other threads to block and wait, which can cause connection pool exhaustion and deadlocks under massive contention (like a flash sale). Optimistic locking adds a `version` or `timestamp` column to the table. The application reads the row, performs business logic, and executes `UPDATE inventory SET stock=stock-1, version=version+1 WHERE item_id=X AND version=old_version`. If another thread updated the row first, the `UPDATE` affects 0 rows, and the application catches the `OptimisticLockException` to either retry or fail the request. For high-contention flash sales, optimistic locking avoids database blocking and scales better, but requires the backend application to implement robust retry loops. Another optimization is an atomic decrement: `UPDATE inventory SET stock = stock - 1 WHERE item_id = X AND stock > 0`.",
        [
            "Accurately contrasts the blocking nature of pessimistic locking with the non-blocking, version-based nature of optimistic locking.",
            "Evaluates tradeoffs under high contention and suggests atomic updates (`WHERE stock > 0`) as a highly optimal solution."
        ],
        [
            "Confuses optimistic and pessimistic locking concepts.",
            "Claims pessimistic locking is strictly faster because it requires fewer application retries."
        ]
    ),
    (
        "b2",
        "architecture",
        "hard",
        "architectural",
        ["Architecture", "Concurrency"],
        "You are architecting the backend for a real-time multiplayer gaming server with massive state concurrency. Managing shared mutable state with locks is causing severe CPU contention and deadlocks. How does adopting the Actor Model or a Message-Passing architecture eliminate these concurrency bottlenecks?",
        "Traditional shared-memory concurrency relies on locks, mutexes, and semaphores to protect mutable state (e.g., game room state or player scores) accessed by multiple threads simultaneously. Under high load, this causes thread contention, context switching overhead, and deadlocks. The Actor Model (implemented via frameworks like Akka, Erlang/OTP, or Orleans) eliminates shared mutable state entirely. An Actor is an isolated computational entity that encapsulates its own private state. Actors cannot access each other's memory; they communicate exclusively by passing asynchronous, immutable messages. Because each Actor processes its mailbox inbox sequentially on a single logical thread, there is no concurrent access to its internal state, completely removing the need for explicit locking. This architecture scales horizontally effortlessly, as Actors can be distributed seamlessly across network nodes, shifting the concurrency paradigm from 'sharing memory to communicate' to 'communicating to share memory'.",
        [
            "Contrasts shared mutable state and lock contention with the isolation of the Actor model.",
            "Explains that Actors encapsulate state, communicate via asynchronous message passing, and process messages sequentially, eliminating explicit locks."
        ],
        [
            "Describes the Actor Model as just another name for a thread pool.",
            "Fails to explain how state encapsulation and message mailboxes remove the need for mutexes."
        ]
    ),
    (
        "b2",
        "compare",
        "easy",
        "conceptual",
        ["Concurrency", "Performance"],
        "When building a backend service intended to handle tens of thousands of concurrent long-polling connections, how does the thread-per-request concurrency model compare to an asynchronous event-loop model?",
        "In the traditional thread-per-request model (used by standard Apache, Tomcat, or traditional Django), the server allocates a dedicated OS thread for every incoming connection. Since each OS thread consumes memory (typically 1-2MB for the stack) and context switching incurs CPU overhead, handling 10,000 concurrent connections requires gigabytes of RAM and causes severe CPU thrashing. When a connection waits for I/O (like long-polling), the thread sits idle and blocked. In an asynchronous event-loop model (used by Node.js, Nginx, Netty, or Python Asyncio), a single or small number of threads handle all connections using non-blocking I/O multiplexing (like `epoll` or `kqueue`). When a request waits for I/O, the thread registers a callback and immediately moves to process the next request. This allows the backend to handle tens of thousands of concurrent connections with minimal memory footprint and CPU overhead, making it vastly superior for long-polling, WebSockets, and I/O-bound workloads.",
        [
            "Highlights the heavy memory and context-switching overhead of the thread-per-request model.",
            "Explains how the asynchronous event-loop utilizes non-blocking I/O multiplexing to handle thousands of connections with a single/few threads."
        ],
        [
            "Claims that thread-per-request is faster for I/O bound workloads because it has more threads.",
            "Confuses the event-loop model with multi-core parallel processing of CPU-bound tasks."
        ]
    ),
    (
        "b2",
        "diagnose",
        "medium",
        "debugging",
        ["Concurrency", "Architecture"],
        "Your backend uses a reactive, asynchronous framework (like Node.js, Spring WebFlux, or Python Asyncio). Under moderate load, the entire application suddenly becomes unresponsive, though CPU and memory usage remain low. How do you diagnose and fix this thread pool starvation / event loop blocking?",
        "In a reactive or asynchronous framework, a small number of event loop threads handle all incoming requests. If a developer inadvertently introduces a blocking, synchronous operation—such as a synchronous database driver call, a `Thread.sleep()`, a heavy cryptographic hashing function (bcrypt), or a blocking HTTP client call—inside the event loop, the thread halts. Since there are very few event loop threads, blocking even a few of them quickly starves the system, preventing it from accepting or processing any new concurrent requests. This results in the application hanging while CPU usage remains near zero. To diagnose, capture a thread dump or use profiling tools (like Node's clinic.js or Java Flight Recorder) to identify threads stuck in blocking states. To fix the issue, replace all synchronous I/O calls with their non-blocking, asynchronous equivalents, and offload heavy CPU-bound computational tasks to a dedicated separate worker thread pool so the main event loop remains unblocked.",
        [
            "Identifies that synchronous/blocking calls within an async event loop cause total application starvation.",
            "Suggests diagnostics like thread dumps and prescribes offloading CPU-bound tasks to worker pools or using non-blocking I/O."
        ],
        [
            "Assumes the application ran out of RAM or CPU without addressing the event loop architecture.",
            "Suggests increasing the event loop thread count to 10,000 to solve the blocking."
        ]
    ),
    (
        "b2",
        "implement",
        "medium",
        "best_practices",
        ["Concurrency", "API Design"],
        "When implementing a backend API for processing financial payments, how do you use Idempotency Keys to ensure thread-safe and distributed-safe retry logic?",
        "Network requests can fail, timeout, or drop packets, forcing clients to retry. If a client retries a payment request that actually succeeded on the backend but failed to return a response, the backend could double-charge the user. To prevent this, the client generates a unique UUID (the Idempotency Key) and sends it in an HTTP header (e.g., `Idempotency-Key`). The backend uses this key to enforce exactly-once execution. Implementation involves: 1) The backend receives the request and attempts to acquire a distributed lock or insert a record into an 'idempotency_keys' database table using the key as a unique constraint. 2) If the insert fails due to a uniqueness constraint, the backend knows this is a retry. It looks up the saved payload from the original execution and immediately returns the cached HTTP response without reprocessing the payment. 3) If the insert succeeds, the backend processes the payment, saves the final response status against the idempotency key, and returns the result.",
        [
            "Explains the purpose of an Idempotency Key in preventing duplicate state mutations on retries.",
            "Details the backend implementation: storing the key with a unique constraint, checking for prior execution, and caching/returning the original response."
        ],
        [
            "Suggests that idempotency keys are used for encrypting payment payloads.",
            "Recommends relying solely on frontend logic to prevent retries instead of backend enforcement."
        ]
    ),
    (
        "b3",
        "architecture",
        "hard",
        "architectural",
        ["Architecture", "API Design"],
        "You are architecting a distributed rate-limiting service to protect your backend APIs. What are the architectural tradeoffs between implementing a Token Bucket algorithm versus a Fixed Window algorithm, and how would you implement this at scale using Redis?",
        "A Fixed Window algorithm increments a counter for a user within a discrete time block (e.g., 00:00 to 00:01). It is easy to implement using a Redis `INCR` and `EXPIRE` command, but suffers from the 'boundary effect': a user can exhaust their limit at the very end of one window and immediately exhaust the next limit at the start of the next, effectively bursting at 2x the allowed rate in a short span. The Token Bucket algorithm provides a smooth, continuous rate limit. Tokens are added to the bucket at a constant rate, and requests consume tokens. To implement Token Bucket at scale efficiently and atomically, you use a Redis Lua script. The script calculates the time elapsed since the last request, adds the appropriate regenerated tokens to the bucket, checks if the requested amount is available, deducts them, and updates the timestamp—all within a single atomic server-side execution. This prevents race conditions across distributed backend instances without requiring distributed locks.",
        [
            "Contrasts the boundary burst flaws of Fixed Window with the smooth rate enforcement of Token Bucket.",
            "Explains the necessity of using Redis Lua scripts to achieve atomic, lock-free evaluation of Token Bucket math in a distributed system."
        ],
        [
            "Claims Fixed Window is superior because it prevents all bursts.",
            "Suggests implementing the Token Bucket math in application memory, ignoring distributed race conditions across multiple instances."
        ]
    ),
    (
        "b3",
        "diagnose",
        "medium",
        "problem_solving",
        ["Architecture", "Databases"],
        "During a massive spike in upstream API traffic, your backend application suddenly begins throwing `ConnectionTimeoutException` when attempting to query the database. CPU on both the application and database is normal. How do you diagnose and resolve this connection pool exhaustion?",
        "This indicates that the backend's database connection pool (e.g., HikariCP, PgBouncer) has been exhausted. All available connections are actively in use or checked out, and new incoming application threads are blocked waiting for a connection until they hit the pool checkout timeout limit. To diagnose, inspect application logs for connection acquisition timeouts and check connection pool metrics (active vs. idle connections) via JMX, Prometheus, or APM tools. To resolve: 1) Identify and optimize long-running transactions (e.g., missing indexes, N+1 queries) that are holding connections open for too long; 2) Ensure transactions are closed and connections are reliably returned to the pool (e.g., in a `finally` block); 3) Avoid wrapping slow external network calls (like HTTP API requests) inside database transactions; 4) If the database can handle more concurrency, appropriately increase the connection pool size limits.",
        [
            "Identifies connection pool exhaustion as the root cause of checkout timeouts when resources are otherwise healthy.",
            "Provides practical resolutions: optimizing slow queries, avoiding network calls inside transactions, and ensuring connections are closed."
        ],
        [
            "Suggests increasing the database CPU instance size without checking pool configurations.",
            "Claims that connection timeouts are always caused by network firewall drops between the app and the database."
        ]
    ),
    (
        "b3",
        "optimize",
        "hard",
        "best_practices",
        ["Architecture", "Performance"],
        "Before transitioning a massive monolithic backend to a serverless or microservices architecture, you must optimize the monolith's excessive startup time and memory footprint. What architectural and JVM/Runtime techniques can drastically reduce these bottlenecks?",
        "Massive monoliths suffer from slow startup times (often minutes) and bloated memory footprints due to aggressive dynamic class loading, extensive reflection scanning (e.g., Spring classpath scanning), and JIT compiler warmup. To optimize startup time and memory without splitting the codebase: 1) Implement Lazy Initialization, where beans, singletons, or heavy components are only instantiated on first use rather than during application bootstrap; 2) Trim dependencies and remove unused modules to reduce classpath scanning overhead; 3) Utilize Ahead-of-Time (AOT) compilation and native image generation (e.g., using GraalVM or Spring Native). AOT compiles the application directly to a native executable, completely eliminating JVM startup overhead, JIT warmup, and class metadata memory overhead, resulting in sub-second startup times and a fraction of the RAM usage. 4) Use Application Class Data Sharing (AppCDS) in the JVM to dump and share pre-parsed class metadata across restarts.",
        [
            "Identifies reflection scanning and eager initialization as primary culprits of monolith bloat.",
            "Recommends advanced runtime optimizations like GraalVM AOT compilation, native images, AppCDS, and Lazy Initialization."
        ],
        [
            "Suggests simply increasing the RAM of the server to make the monolith start faster.",
            "Advises abandoning the monolith entirely as the only possible optimization."
        ]
    ),
    (
        "b3",
        "compare",
        "medium",
        "tradeoff",
        ["Architecture", "Distributed Systems"],
        "When managing distributed transactions across multiple microservices (e.g., Order, Payment, and Inventory services), what are the architectural tradeoffs between using an Event Choreography pattern versus a central Orchestration (Saga) pattern?",
        "In Event Choreography, microservices publish and subscribe to domain events (e.g., `OrderCreated`, `PaymentProcessed`) asynchronously through a message broker. It provides loose coupling, as no central coordinator exists, and avoids single points of failure. However, as the system grows, the flow of events becomes highly complex and difficult to monitor, making it hard to track the state of a transaction or implement compensating actions for rollbacks. In central Orchestration (a Saga pattern managed by tools like AWS Step Functions or Netflix Conductor), a central orchestrator service explicitly directs the transaction workflow, sending command messages to each service and waiting for replies. This centralizes the business logic, making the transaction state, error handling, and rollback execution trivial to monitor and visualize. The tradeoff is tighter coupling, as the orchestrator must know the domain APIs of all participating services, and it introduces a potential single point of failure and bottleneck.",
        [
            "Contrasts the decentralized, loosely coupled nature of Choreography with the centralized, explicitly managed nature of Orchestration.",
            "Highlights the difficulty of monitoring and rollbacks in Choreography versus the single-point-of-failure and tighter coupling risks of Orchestration."
        ],
        [
            "Claims that distributed transactions can simply use traditional ACID two-phase commit (2PC) across microservices without issue.",
            "Confuses orchestration with container orchestration (like Kubernetes) instead of transaction workflow."
        ]
    ),
    (
        "b3",
        "diagnose",
        "easy",
        "debugging",
        ["Performance", "Architecture"],
        "A long-running backend process experiences steadily increasing memory consumption over several days, eventually triggering aggressive garbage collection pauses and crashing with an OutOfMemoryError. How do you diagnose this memory leak?",
        "A memory leak in a managed language (Java, C#, Node.js) occurs when objects are no longer needed by the application logic but remain referenced by active objects (like static collections, caching maps without TTL, or unclosed event listeners), preventing the Garbage Collector (GC) from reclaiming them. To diagnose the leak: 1) Enable verbose GC logging or connect APM tools to observe the sawtooth memory graph where memory fails to return to the baseline after major GC cycles; 2) Configure the application runtime to automatically generate a heap dump upon crashing (e.g., `-XX:+HeapDumpOnOutOfMemoryError`); 3) Load the heap dump into a memory analyzer tool (like Eclipse MAT or VisualVM) to compute the 'Dominator Tree' and identify which objects or classes are consuming the most retained heap space; 4) Trace the GC root paths of those massive objects to find the exact line of code holding the erroneous references.",
        [
            "Explains how lingering object references prevent garbage collection in managed runtimes.",
            "Outlines the diagnostic workflow: observing GC logs, triggering a heap dump, and using a memory analyzer (like Eclipse MAT) to inspect the dominator tree."
        ],
        [
            "Claims memory leaks only happen in languages like C/C++ with manual memory management.",
            "Suggests writing a script to reboot the server daily as the primary diagnostic solution."
        ]
    )
]
