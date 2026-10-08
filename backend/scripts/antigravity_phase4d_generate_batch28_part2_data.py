"""Batch 28 Part 2 question content (Backend Developer). Targeted Gap Generation."""

ROLE = "Backend Developer"

BUCKET_KEYS = {
    "BACKEND_SCALING": ("Horizontal Scaling", "Statelessness & Caching", "Backend", ["Backend Developer", "Architecture"]),
}

Q = [
# ---------------- BACKEND_SCALING ----------------
("BACKEND_SCALING", "scenario", "medium", "scenario", ["Statelessness", "Sessions"],
 "A monolithic backend stores user authentication sessions in local server memory. When the traffic spikes, you horizontally scale to 5 instances behind a load balancer. Suddenly, users report being randomly logged out on every other page click. Why did horizontal scaling break authentication, and how do you fix it?",
 "The load balancer is routing requests in a Round Robin fashion. A user authenticates on Server A, which stores the session in its local RAM. The user's next request is routed to Server B, which has no record of the session, treating the user as logged out. You fix this by extracting state to a centralized distributed session store (like Redis) or by using stateless JWTs.",
 ["The load balancer routes subsequent requests to servers that don't have the local session in RAM", "Violates the statelessness principle of horizontal scaling", "Fix: Extract session state to a centralized store (Redis) or use stateless JWTs"],
 ["The servers are competing to log the user out first"]),

("BACKEND_SCALING", "debug", "hard", "debugging", ["Connection Pools"],
 "You operate a fleet of 50 backend instances connecting to a central PostgreSQL database. You scale up to 100 instances during a traffic spike. Immediately, the database crashes with 'Too many clients already'. You check the instances, and none are heavily loaded. What scaling bottleneck occurred, and how is it resolved?",
 "You suffered a Connection Pool exhaustion. If each instance maintains a pool of 20 connections, 50 instances hold 1,000 connections. Scaling to 100 instances attempts to open 2,000 connections, exceeding the database's physical connection limit and crashing it. To scale horizontally, you must dynamically reduce the per-instance pool size, or introduce an infrastructure-level connection multiplexer like PgBouncer.",
 ["Connection Pool exhaustion", "Scaling instances linearly scales the number of open database connections, exceeding DB limits", "Fix: Reduce per-instance pool size or introduce a multiplexer like PgBouncer"],
 ["The database was intimidated by the number of servers"]),

("BACKEND_SCALING", "tradeoff", "medium", "tradeoff", ["Load Balancing", "Sessions"],
 "What are the tradeoffs of solving the horizontal scaling session problem by configuring 'Sticky Sessions' on the load balancer instead of using a centralized Redis session store?",
 "Sticky sessions are trivial to implement and require zero code changes or extra infrastructure, as the load balancer simply pins the user's IP/Cookie to a specific backend server. However, it completely destroys even load distribution (one server might get stuck with all the heavy power users). Worse, if that specific server crashes, all pinned users instantly lose their sessions.",
 ["Sticky sessions require zero code changes and no external infrastructure", "Tradeoff: Destroys even load distribution (hotspots)", "Tradeoff: If the pinned server crashes, all associated users instantly lose their sessions"],
 ["Sticky sessions physically glue the user to the server"]),

("BACKEND_SCALING", "explain", "easy", "concept", ["Architecture"],
 "Explain the concept of a 'Stateless' backend architecture.",
 "A stateless backend architecture dictates that a server does not retain any client context, session data, or local files between requests. Every single incoming HTTP request must contain all the information necessary to process it (e.g., via a JWT). This allows horizontal scaling to be trivial, because any server in the fleet can handle any request at any time without synchronization.",
 ["The server retains no client context or session data between requests", "Every HTTP request must contain all information necessary to process it", "Makes horizontal scaling trivial because any server can process any request"],
 ["It means the server has no nationality or geographic location"]),

("BACKEND_SCALING", "scenario", "hard", "scenario", ["Cache Stampede"],
 "A high-traffic API uses a Redis cache. The cached data expires exactly every 10 minutes. Exactly every 10 minutes, the backend instances experience a massive CPU spike, and the database grinds to a halt for 5 seconds before recovering. What is this phenomenon called, and how do you prevent it?",
 "This is a 'Thundering Herd' or 'Cache Stampede'. When the popular cache key expires, thousands of concurrent requests all hit the backend simultaneously, realize the cache is empty, and *all* query the database for the exact same data at the same millisecond. You prevent this by using a Distributed Lock (so only one request queries the DB while others wait), or by 'Cache Warming' (updating the cache in the background before it expires).",
 ["Known as a 'Thundering Herd' or 'Cache Stampede'", "When the cache expires, thousands of concurrent requests hammer the database simultaneously", "Fix: Use a Distributed Lock for cache misses, or use background Cache Warming"],
 ["The cache is physically migrating to a new server"]),

("BACKEND_SCALING", "fundamentals", "medium", "concept", ["Distributed Locks"],
 "In a horizontally scaled backend, what is the architectural purpose of a 'Distributed Lock' (e.g., Redis Redlock), and why should it generally be avoided for normal synchronous API endpoints?",
 "A distributed lock ensures that only one node in an entire cluster can execute a specific block of code or access a shared resource at a time (e.g., processing a critical payment). It should be avoided for normal API endpoints because it introduces massive latency, completely breaks horizontal concurrency (forcing the cluster to behave like a single thread), and is prone to deadlocks if a node crashes while holding the lock.",
 ["Ensures only one node in the cluster can execute a critical section of code at a time", "Avoid in APIs because it introduces massive latency and breaks horizontal concurrency", "Prone to distributed deadlocks if a node crashes while holding the lock"],
 ["A distributed lock secures the physical doors of the data center"]),

("BACKEND_SCALING", "tradeoff", "hard", "tradeoff", ["Rate Limiting"],
 "When architecting a rate limiter for a horizontally scaled API, what is the tradeoff between implementing a centralized Redis rate limiter versus a local in-memory rate limiter on each instance?",
 "A centralized Redis rate limiter provides perfect, global accuracy across the cluster, but adds a network hop and a Redis bottleneck to every single API request. A local in-memory rate limiter on each instance adds zero latency and scales infinitely, but sacrifices strict accuracy (if a user is allowed 100 req/min, and hits 5 instances, they might get 500 req/min) and requires dividing the rate limit heuristically across instances.",
 ["Centralized (Redis): Perfect global accuracy, but adds a network hop and bottleneck to every request", "Local (In-Memory): Zero latency and infinite scaling, but sacrifices strict accuracy", "Local tradeoff: Users can exceed limits if requests hit multiple different instances"],
 ["Centralized limiters limit the speed of the CPU physically"]),

("BACKEND_SCALING", "debug", "medium", "debugging", ["Statelessness", "File Storage"],
 "You scale your Node.js backend from 2 to 10 instances. However, file uploads suddenly become completely unreliable. Users upload an avatar, get a 200 OK, but when they refresh, the avatar is a broken image link 90% of the time. What architectural rule of horizontal scaling was violated?",
 "The backend violated the statelessness rule by saving uploaded files directly to the local disk/filesystem of the specific instance that received the POST request. When the user refreshed, the load balancer routed the GET request to one of the other 9 instances, which obviously didn't have the file. All file uploads in a scaled architecture must be streamed directly to centralized object storage like AWS S3.",
 ["Violated statelessness by saving files to the local instance disk", "Subsequent requests are routed to different instances that lack the file", "Fix: Stream all uploads to centralized object storage (e.g., AWS S3)"],
 ["The load balancer is deleting files to save bandwidth"]),

("BACKEND_SCALING", "scenario", "hard", "scenario", ["Load Shedding"],
 "You have a backend service calculating complex machine learning recommendations. It takes 2 seconds to compute. To protect the service from overload, you add an Auto Scaling Group. During a viral marketing event, traffic spikes 10x instantly. The autoscaler triggers, but the service completely crashes before the new instances boot up. What must be implemented at the application level to survive this?",
 "You must implement Graceful Degradation and Load Shedding. Autoscaling is a slow, reactive infrastructural response (taking minutes to boot VMs). The application must proactively survive the spike *before* the autoscaler finishes. It must detect its own CPU/Thread exhaustion and actively shed load (e.g., returning HTTP 503s or serving static, pre-computed generic recommendations) to stay alive until reinforcements arrive.",
 ["Must implement Graceful Degradation and Load Shedding", "Autoscaling is too slow (minutes) to handle instantaneous massive spikes", "The application must proactively detect exhaustion and shed load (HTTP 503) to stay alive"],
 ["Autoscaling requires a handwritten request to the cloud provider"]),

("BACKEND_SCALING", "implement", "medium", "implementation", ["WebSockets", "Pub/Sub"],
 "You have a fleet of backend instances processing real-time WebSocket connections for a chat application. If User A is connected to Instance 1, and User B is connected to Instance 2, how do you architect the backend so User A can send a message to User B?",
 "Because WebSockets are stateful, long-lived connections pinned to specific instances, Instance 1 cannot communicate directly with User B's socket. You must introduce a central Pub/Sub message broker (like Redis Pub/Sub). When User A sends a message, Instance 1 publishes it to a Redis channel. Instance 2 is subscribed to that channel, receives the message, and pushes it down the local WebSocket to User B.",
 ["WebSockets are stateful and pinned to specific instances", "Introduce a central Pub/Sub message broker (e.g., Redis Pub/Sub)", "Instances publish messages to the broker, and other instances subscribe to push to their local sockets"],
 ["Instance 1 sends an email to Instance 2 with the message payload"]),

("BACKEND_SCALING", "tradeoff", "medium", "tradeoff", ["Load Balancing"],
 "What are the tradeoffs of using a Layer 4 (Transport Layer) Load Balancer versus a Layer 7 (Application Layer) Load Balancer for a backend web service?",
 "A Layer 4 LB (TCP/UDP) is blazingly fast, consumes almost zero compute, and handles massive throughput because it simply forwards packets based on IP/Port without looking at the content. A Layer 7 LB (HTTP/HTTPS) is slower and consumes more compute because it fully parses the HTTP headers and payload, but provides immense value by allowing intelligent routing (e.g., path-based `/api/v1`), SSL termination, and cookie-based sticky sessions.",
 ["Layer 4 (TCP): Blazingly fast, low compute overhead, blind packet forwarding", "Layer 7 (HTTP): Slower, higher compute overhead due to parsing headers/payloads", "Layer 7 tradeoff/benefit: Allows intelligent path routing, SSL termination, and cookie inspection"],
 ["Layer 7 requires a 7-core processor"]),

("BACKEND_SCALING", "explain", "easy", "concept", ["Caching"],
 "What is 'Cache Invalidation', and why is it notoriously considered one of the hardest problems in backend architecture?",
 "Cache Invalidation is the process of safely removing or updating stale data in a cache when the underlying database data changes. It is incredibly difficult in distributed systems because if a backend instance updates the database but fails to invalidate the cache (due to a race condition, network blip, or crash), the entire system will serve incorrect, stale data indefinitely, destroying data integrity.",
 ["The process of removing/updating stale data in a cache when the source database changes", "Difficult due to distributed race conditions, network failures, and crash scenarios", "Failure to invalidate perfectly results in the system serving stale data indefinitely"],
 ["It is when a cache physically expires and grows mold"]),

("BACKEND_SCALING", "debug", "hard", "debugging", ["Consistent Hashing"],
 "Your backend uses a massive Memcached cluster. You notice that when you deploy a new backend version, there is a brief 30-second window where 50% of all cache lookups result in a 'Miss', severely stressing the database, even though the cache cluster wasn't restarted. Why did a code deployment cause a cache miss spike?",
 "The backend deployment likely altered the list of Memcached server IPs or their order in the client configuration, or added/removed a node. Because standard client-side sharding uses modulo hashing (`hash(key) % N`), changing `N` (the number of servers) instantly reshuffles the routing math for almost all keys, sending clients to the wrong cache nodes. You must use 'Consistent Hashing' in the client to prevent this.",
 ["Deployment changed the number or order of cache nodes in the client configuration", "Standard modulo hashing (`hash(key) % N`) reshuffles all keys if `N` changes", "Fix: Use Consistent Hashing to minimize key reshuffling when nodes change"],
 ["The deploy script accidentally ran a `FLUSHALL` command on the cache"]),

("BACKEND_SCALING", "scenario", "medium", "scenario", ["Read Replicas", "Consistency"],
 "An application generates heavy reporting dashboards. To scale reads, you configure the backend to send all `SELECT` queries to a database Read Replica, and all `INSERT/UPDATE` queries to the Primary database. Immediately, users complain that they submit a form, the page reloads, and their changes aren't there. What architectural problem did you introduce?",
 "You introduced 'Replication Lag', causing a lack of Read-After-Write consistency. The user wrote data to the Primary, the page reloaded, and the backend instantly queried the Read Replica *before* the asynchronous replication process had copied the new data over. The backend must be smart enough to route immediate post-write reads to the Primary, or use synchronous replication.",
 ["Caused by asynchronous 'Replication Lag'", "Violates Read-After-Write consistency (reading from replica before the write propagated)", "Fix: Route the first read immediately following a write to the Primary database"],
 ["The Read Replica is protesting the heavy workload"]),

("BACKEND_SCALING", "fundamentals", "easy", "concept", ["Architecture"],
 "In horizontal scaling, what is the 'Shared-Nothing' architecture?",
 "Shared-Nothing is an architecture where each backend node operates completely independently, possessing its own CPU, memory, and disk space, and shares absolutely no state or hardware with other nodes. Application state is pushed entirely to centralized external systems (Databases, Redis, S3). This makes horizontally scaling the compute tier infinitely easy because nodes are completely disposable and identical.",
 ["Nodes operate independently and share absolutely no state or hardware", "State is pushed entirely to centralized external systems (DBs, Redis)", "Makes scaling trivial because nodes are identical and disposable"],
 ["It means developers refuse to share code with each other"]),

("BACKEND_SCALING", "implement", "hard", "implementation", ["Local Caching", "Pub/Sub"],
 "You run a horizontally scaled backend API. You want to implement an in-memory cache on each instance to save Redis network hops, but you must guarantee that if Instance A updates a user's profile, Instance B's local in-memory cache is immediately invalidated. How do you implement this cross-instance coordination?",
 "You must implement a Cache Invalidation Broadcast via Pub/Sub. When Instance A updates the database, it publishes an invalidation message (e.g., 'Invalidate User:123') to a central Redis Pub/Sub topic. Every other instance (including B) subscribes to this topic. Upon receiving the message, Instance B instantly deletes 'User:123' from its local in-memory LRU cache, ensuring eventual consistency.",
 ["Implement a Cache Invalidation Broadcast via Pub/Sub (e.g., Redis Pub/Sub)", "The mutating instance publishes an invalidation message to a central topic", "All other instances subscribe and delete the stale key from their local memory"],
 ["Instance A SSHes into Instance B and deletes the memory physically"]),

("BACKEND_SCALING", "tradeoff", "medium", "tradeoff", ["Vertical Scaling"],
 "What is the tradeoff of scaling an application by increasing the per-instance memory and CPU (Vertical Scaling) instead of adding more instances (Horizontal Scaling)?",
 "Vertical Scaling is architecturally trivial—requiring zero code changes, no load balancers, and no complex distributed state management—and avoids network latency between nodes. However, it hits a hard physical ceiling (you can only buy a server so big), provides absolutely zero fault tolerance (if the single massive server crashes, the entire application dies), and requires downtime to upgrade the hardware.",
 ["Vertical Scaling: Architecturally trivial, requires no code changes or distributed state", "Tradeoff: Hits a hard physical maximum ceiling", "Tradeoff: Zero fault tolerance (single point of failure) and requires downtime to upgrade"],
 ["Vertical scaling makes the server physically taller and unstable in earthquakes"])
]
