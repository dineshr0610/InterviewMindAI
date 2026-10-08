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
        "B68_4_1",
        "implement",
        "hard",
        "implement",
        ["Data Consistency", "Database Architecture"],
        "PostgreSQL / MySQL",
        "Read-Your-Writes Session Consistency via Consistency Tokens",
        "In a master-replica database architecture with asynchronous replication lag of 200ms, a user updates their profile picture (`POST /profile`), and the client immediately re-fetches the profile page (`GET /profile`). The read request routes to a read replica that has not caught up yet, showing the user their old profile picture. How do you implement 'Read-Your-Writes Session Consistency' using Consistency Tokens (e.g., LSN or commit timestamps) without forcing 100% of read traffic to hit the master database?",
        "Forcing all reads to the master defeats the purpose of horizontal read scaling. To implement session consistency efficiently: 1) On State-Mutating Write: When the client executes `POST /profile`, the master database executes the write and captures its current Log Sequence Number (LSN in Postgres) or binary log position/commit timestamp: `lsn = pg_current_wal_lsn()`. 2) Token Propagation: The API returns this LSN to the client in an HTTP response header or cookie: `X-Consistency-Token: 0/16B3748`. 3) Read Request Routing: On the subsequent `GET /profile`, the client passes the token back (`X-Consistency-Token: 0/16B3748`). 4) Replica LSN Check: The application connection pool or query router queries candidate read replicas for their current applied replay position: `pg_last_wal_replay_lsn()`. 5) Dynamic Routing: If a read replica's replay LSN $\ge$ the client's token LSN, the replica is guaranteed to have applied the user's write; the read is safely executed on that replica. If the replica lags behind the token, the router can either wait up to 50ms for the replica to catch up or fall back to the primary master solely for that specific user's session. Reads without consistency tokens continue routing across all replicas freely.",
        [
            "Captures the master Log Sequence Number (LSN) or WAL commit position upon state mutation",
            "Returns the LSN as a consistency token to the client to send on subsequent reads",
            "Compares client token against replica pg_last_wal_replay_lsn to safely route reads to caught-up replicas"
        ],
        [
            "Suggests putting a Thread.sleep(500) in the frontend after every button click"
        ]
    ),
    (
        "B68_4_2",
        "diagnose",
        "hard",
        "debugging",
        ["Caching", "Concurrency"],
        "Redis / Cache-Aside",
        "The Stale Cache Overwrite Race Condition in Cache-Aside",
        "A backend service implements Cache-Aside: when updating data, it commits the update to PostgreSQL and then immediately executes `redis.del(key)` to invalidate the cache. However, under high concurrent read/write traffic, engineers discover that Redis occasionally holds stale, outdated data permanently until manual cache flushes. Explain the exact concurrent interleaving sequence that causes this Stale Cache Overwrite, and how Lease Tokens or versioned cache keys prevent it.",
        "The Interleaving Race Condition: 1) Time T0: Cache is empty (or missed). Client A (Reader) queries Redis, gets a cache miss. 2) Time T1: Client A queries PostgreSQL and reads the old value `status = 'PENDING'`. Client A's thread is then preempted by the OS scheduler or paused by GC. 3) Time T2: Client B (Writer) updates PostgreSQL: `UPDATE orders SET status = 'CONFIRMED'`. 4) Time T3: Client B invalidates Redis: `redis.del(key)` succeeds. 5) Time T4: Client A wakes up from its GC pause and executes its delayed cache populate: `redis.set(key, 'PENDING')`. 6) Consequence: The cache now permanently stores the old stale value `PENDING` indefinitely, while PostgreSQL has `CONFIRMED`. All future reads serve obsolete data. Mitigations: 1) Cache Versioning / Lease Tokens (Memcached/Redis Lease pattern): When a reader misses cache, the cache issues a unique numeric token/version. When writing back, the cache accepts the write ONLY if the token has not been invalidated by a concurrent write (`CAS` or Lua script). 2) Cache Invalidation via CDC: Instead of application-side `redis.del()`, stream database WAL commits (via Debezium/Kafka) to invalidate or update the cache asynchronously after transaction commit, ensuring strictly ordered cache updates.",
        [
            "Details the concurrent race: reader misses cache, reads old DB data, gets preempted while writer commits and deletes cache, then reader writes stale data to cache",
            "Identifies that the stale data remains in cache indefinitely until TTL expiration or manual eviction",
            "Resolves the race using Lease Tokens / Check-And-Set (CAS) logic or WAL-based CDC cache invalidation"
        ],
        [
            "Assumes Redis deleted the wrong key due to a spelling mistake"
        ]
    ),
    (
        "B68_4_3",
        "scenario",
        "medium",
        "scenario",
        ["Data Consistency", "Data Pipelines"],
        "PostgreSQL / Elasticsearch",
        "Dual-Write Asynchronous Reconciliation for Search Engines",
        "A product catalog writes product updates to PostgreSQL and asynchronously indexes them in Elasticsearch for full-text search. Over time, due to transient network drops, failed retries, and dropped messages, subtle 'data drift' accumulates: 0.1% of products in Elasticsearch have outdated prices or deleted items still appearing in search results. How do you architect an automated, continuous Asynchronous Reconciliation Pipeline to detect and heal data drift without taking the search cluster offline?",
        "To continuously heal data drift between primary database and secondary search indices: 1) Primary Monotonic Tracking: Ensure PostgreSQL records have an indexed `updated_at` timestamp and an `is_deleted` soft-delete marker, or maintain an append-only audit event log. 2) Asynchronous Shadow Reconciler: Implement a low-priority background reconciliation worker that sweeps through PostgreSQL records in chunks using keyset cursor pagination (`WHERE updated_at >= :checkpoint ORDER BY id LIMIT 500`). 3) Checksum / Fingerprint Comparison: Compute a lightweight deterministic cryptographic hash (e.g., MD5 or SHA-256 of canonical fields: `price + title + stock + status`) of the DB record. Compare it against the corresponding document version/hash in Elasticsearch. 4) Self-Healing Ingestion: If a document in Elasticsearch is missing, has an older version, or has a mismatched hash, the reconciler enqueues an asynchronous re-index job. If an active document in Elasticsearch is marked deleted in Postgres, it issues a delete command. 5) Throttled Execution: Throttle reconciler I/O dynamically based on DB CPU and ES cluster load to ensure zero impact on production search query latency.",
        [
            "Identifies that distributed dual-write pipelines inevitably suffer from subtle background drift",
            "Designs an asynchronous background sweeper comparing canonical checksums/hashes between Postgres and Elasticsearch",
            "Applies automated healing (re-indexing missing/outdated documents and deleting orphaned documents) with throttled I/O"
        ],
        [
            "Recommends completely deleting the Elasticsearch index and re-indexing all 100 million products every 10 minutes"
        ]
    ),
    (
        "B68_4_4",
        "explain",
        "medium",
        "explain",
        ["Data Consistency", "Distributed Databases"],
        "Database Replication",
        "Monotonic Read Consistency across Geographically Distributed Replicas",
        "What is 'Monotonic Read Consistency' in distributed database systems, and why does a user who repeatedly refreshes their web browser experience 'time-travel anomalies' (seeing new posts on refresh 1, and seeing older posts disappear on refresh 2) when load balancers use naive round-robin routing across read replicas with varying replication lag?",
        "Monotonic Read Consistency guarantees that if a client reads value $V_1$ at logical time $T_1$, any subsequent read by that same client will never observe a previous state $V_0$ ($T_0 < T_1$). In naive round-robin load balancing across distributed read replicas: 1) Replica A has 50ms of replication lag and has applied all updates up to 10:00:00 AM. 2) Replica B has 2000ms of replication lag and has only applied updates up to 09:59:58 AM. 3) On Refresh 1, the load balancer routes the user to Replica A. The user sees their latest comment posted at 09:59:59 AM. 4) On Refresh 2, the load balancer routes the user to Replica B. Because Replica B has not yet applied the 09:59:59 AM update, the comment completely disappears from the screen. 5) On Refresh 3, routed back to Replica A, the comment reappears. This jarring 'time-travel' experience destroys user trust and causes duplicate submission attempts. Resolution: Enforce session-pinned sticky routing (hashing the user ID or session token to a specific replica) or attach client-side monotonic replication sequence numbers so load balancers never route a user to a replica older than their last observed sequence.",
        [
            "Defines monotonic read consistency as guaranteeing that subsequent reads never observe older states than previously observed reads",
            "Explains that round-robin routing across replicas with uneven replication lag causes data to appear and disappear ('time travel')",
            "Resolves the issue via session-pinned replica routing or client-tracked monotonic replication timestamps"
        ],
        [
            "Claims the user's web browser cache is infected with malware"
        ]
    ),
    (
        "B68_4_5",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Database Architecture", "Performance Tuning"],
        "PostgreSQL / MySQL",
        "Dynamic Read/Write Routing Based on Replication Lag Metrics",
        "When designing a database access layer in a high-scale application, what are the architectural tradeoffs of implementing 'Dynamic Read/Write Routing' that automatically pulls read replicas out of the active read pool if their replication lag exceeds a strict threshold (e.g., > 1 second)?",
        "Dynamic Replication Lag Routing: 1) Mechanism: The application connection pool or proxy (e.g., ProxySQL, AWS Aurora RDS proxy) continuously samples replication lag metrics (e.g., PostgreSQL `pg_stat_replication.replay_lag` or MySQL `Seconds_Behind_Master`). If a replica exceeds a safe lag threshold (e.g., 1000ms), the router temporarily evicts it from the read pool and sheds read traffic to healthy replicas or the primary master. 2) Advantages: Strongly mitigates stale reads. Protects user-facing workflows from displaying severely outdated data during network partitions or heavy batch write jobs on the primary. 3) Tradeoffs and Risks: Cascading Primary Collapse. If heavy write load causes ALL read replicas to fall behind simultaneously, the router will evict all replicas at once, suddenly routing 100% of the entire company's read traffic to the primary master. The master, already strained by heavy writes, is instantly overwhelmed by millions of read queries, leading to complete database failure. 4) Mitigation: Implement a 'Minimum Replica Quota' and 'Circuit Breaker Floor' where the router refuses to evict more than a fixed percentage (e.g., 50%) of read replicas, accepting slightly stale reads over a total system crash.",
        [
            "Explains dynamic eviction of lagging replicas based on replication lag metrics to prevent stale reads",
            "Identifies the primary catastrophic failure mode: cascading traffic redirection that crashes the primary master",
            "Prescribes a minimum healthy replica floor or circuit breaker to prevent total master overload during global lag spikes"
        ],
        [
            "Claims replication lag can be completely eliminated by setting replica CPU to 100%"
        ]
    ),
    (
        "B68_4_6",
        "explain",
        "hard",
        "explain",
        ["Distributed Systems", "Data Consistency"],
        "Vector Clocks / Lamport Timestamps",
        "Causal Metadata and Vector Clocks in Collaborative Backend Systems",
        "In a distributed collaborative document editor (or multi-region distributed key-value store), physical wall-clock timestamps (like UTC NTP timestamps) cannot reliably determine whether Edit A happened before Edit B due to network latency and clock drift. How do 'Vector Clocks' capture causal relationships between concurrent distributed edits, and how do they detect true concurrent merge conflicts?",
        "Why Physical Wall Clocks Fail: NTP clock drift makes it impossible to know if Event A with timestamp 12:00:00.001 caused Event B with timestamp 12:00:00.000. Relying on physical time ('Last-Write-Wins') silently overwrites and deletes valid concurrent edits. Vector Clock Mechanics: 1) Structure: A vector clock is an array/map of logical counters across all participating nodes/actors: $V = [N_1: c_1, N_2: c_2, ..., N_k: c_k]$. 2) Local Tick: Before a node performs an edit, it increments its own counter: $V_i[N_i] += 1$. 3) Propagation: Every document update message includes the authoring node's vector clock. 4) Merging: When a node receives an update with vector $V_{remote}$, it updates its local vector: $V_{local}[k] = \\max(V_{local}[k], V_{remote}[k])$ for all nodes $k$. Causality Detection: 1) Causal Precedence ($A \rightarrow B$): Update A causally happened before B if every component in $V_A$ is $\le$ the corresponding component in $V_B$, and at least one component is $<$. The backend can safely apply B as a chronological progression. 2) Concurrent Conflict ($A \parallel B$): If neither $V_A \le V_B$ nor $V_B \le V_A$ (e.g., $V_A = [A:2, B:0]$ and $V_B = [A:1, B:1]$), neither edit knew about the other. The system mathematically detects a true concurrent conflict, requiring domain-specific conflict resolution (three-way merge, CRDTs, or user branching).",
        [
            "Explains why NTP clock drift causes silent data loss under Last-Write-Wins physical timestamping",
            "Defines vector clocks as arrays of logical counters incremented locally and merged via pairwise maximums",
            "Formulates the mathematical definition of causal precedence ($V_A \le V_B$) versus concurrent conflicts ($V_A \\parallel V_B$)"
        ],
        [
            "Claims vector clocks are used to measure the physical velocity of electricity across Ethernet cables"
        ]
    ),
    (
        "B68_4_7",
        "concept",
        "easy",
        "concept",
        ["Data Consistency", "Architecture"],
        "CQRS / Event-Driven Architecture",
        "Handling Asynchronous Materialized View Catch-Up Lag in CQRS",
        "In a CQRS (Command Query Responsibility Segregation) architecture, write commands execute against a write model, and read queries execute against an asynchronous materialized read view projected via Kafka. How do you design user interfaces and backend APIs to handle the 300ms 'catch-up lag' so users do not see stale data immediately after submitting a form?",
        "Because projections in CQRS are eventually consistent, immediately querying the read model after a command commits can return stale data. Architectural solutions: 1) Optimistic UI Updates: The client frontend assumes success upon receiving HTTP 200/202 from the command API and updates local UI state immediately, masking the 300ms propagation delay from the user. 2) Command Response Payload: Rather than returning an empty HTTP 200, the Command API returns the updated domain entity state directly in the response payload. The client uses this payload to render the immediate result, avoiding an immediate round-trip read query to the lagging read view. 3) Read-Your-Writes Version Header: The command API returns the new entity version (e.g., `version: 4`). When the client queries the read model, it includes `If-None-Match` or `min_version=4`. If the read model projection has not yet reached version 4, the read API can poll briefly or fall back to querying the write model directly for that single request.",
        [
            "Identifies that CQRS read models are eventually consistent and lag behind write commands",
            "Returns updated entity state directly in the Command response to eliminate immediate read queries",
            "Uses optimistic UI updates or version-aware read queries to handle the projection lag gracefully"
        ],
        [
            "Suggests converting the entire application into a single synchronous SQLite database file"
        ]
    ),
    (
        "B68_4_8",
        "concept",
        "easy",
        "concept",
        ["Caching", "Data Consistency"],
        "System Architecture",
        "Cache-Aside vs Write-Through vs Write-Behind Caching",
        "Compare 'Cache-Aside', 'Write-Through', and 'Write-Behind' (Write-Back) caching patterns regarding write latency, read latency, and data loss risk under sudden server crashes.",
        "1) Cache-Aside (Lazy Loading): The application code orchestrates reads and writes. On read: check cache; if miss, read DB and populate cache. On write: write to DB and invalidate/update cache. Tradeoffs: Resilient (cache crash does not stop DB writes; DB is authoritative). Read miss incurs extra round-trip. Zero risk of data loss. 2) Write-Through: The application writes to the caching layer; the cache synchronously writes to the database before acknowledging the application. Tradeoffs: Higher write latency (incurs cache + DB write time). Guarantees cache and DB are always strictly synchronized. Low risk of data loss. 3) Write-Behind (Write-Back): The application writes exclusively to the cache in RAM, which acknowledges success immediately. The cache asynchronously batches and writes accumulated updates to the database in the background. Tradeoffs: Blazing fast sub-millisecond write latency and massive write throughput. Extreme risk of data loss: if the cache node crashes, loses power, or reboots before flushing dirty in-memory data to the database, uncommitted writes are permanently lost.",
        [
            "Contrasts application-managed Cache-Aside with cache-orchestrated Write-Through and Write-Behind",
            "Identifies Write-Behind as offering fastest write latency via asynchronous in-memory flushes",
            "Highlights Write-Behind's catastrophic data loss risk if the cache crashes before flushing to the database"
        ],
        [
            "Claims Write-Behind caching writes data backwards into the database from bottom to top"
        ]
    ),
    (
        "B68_4_9",
        "implement",
        "medium",
        "implement",
        ["Caching", "Performance Tuning"],
        "Redis / Algorithms",
        "Probabilistic Early Expiration (XFetch Algorithm) vs Mutex Locking",
        "When an ultra-hot cache key (e.g., homepage configuration requested 50,000 times/sec) expires, a Cache Stampede occurs: thousands of threads miss cache simultaneously and hammer the database. While distributed mutex locks prevent stampedes, they introduce thread blocking and latency spikes. How does the 'XFetch Algorithm' (Probabilistic Early Expiration) prevent cache stampedes without locking?",
        "Mutex locking forces 49,999 threads to block or sleep while 1 thread queries the DB and repopulates the cache, causing latency spikes and thread contention. The XFetch Algorithm (optimal probabilistic cache rejuvenation) completely eliminates locking by refreshing the key *probabilistically in the background BEFORE it expires*: 1) Stored Metadata: When saving an item in Redis, store the data along with: $TTL$ (expiration time) and $\\Delta$ (the computation time it took to generate the value, e.g., 200ms). 2) Probabilistic Evaluation Formula: When a reader fetches the key at current time $now$, it calculates: $-\\beta \\times \\Delta \\times \\ln(random(0, 1)) > (TTL - now)$, where $\\beta > 0$ is an aggressiveness tuning multiplier. 3) Behavior: As time approaches expiration ($TTL - now$ approaches 0), the mathematical probability of this condition evaluating to true increases smoothly from 0% to 100%. 4) Single Async Refresh: Exactly one lucky reader's evaluation triggers true a few seconds *before* expiration. That single thread asynchronously fetches fresh data from the DB and updates Redis in the background. All other 49,999 readers continue receiving instantaneous cached hits from RAM with zero blocking, completely neutralizing cache stampedes.",
        [
            "Identifies that mutex locks introduce thread blocking and latency jitter under ultra-high concurrency",
            "Explains XFetch formula computing early expiration probability based on computation duration delta and time remaining",
            "Demonstrates that a single reader refreshes the cache probabilistically before expiration while other readers hit RAM uninterrupted"
        ],
        [
            "Claims XFetch is a tool used to download pirated movies"
        ]
    ),
    (
        "B68_4_10",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Data Consistency", "Architecture"],
        "Debezium / Apache Kafka / CDC",
        "Change Data Capture (CDC) vs Application-Level Dual-Writing",
        "Why is using Change Data Capture (CDC via Debezium reading PostgreSQL WAL) considered architecturally superior to Application-Level Dual-Writing (having backend code write to PostgreSQL and then immediately publish an event to Kafka)?",
        "Application-Level Dual-Writing Fallacy: In application code: `db.save(order); kafka.send(orderCreatedEvent);`. In distributed systems, this is fundamentally broken because there is no distributed transaction across the database and Kafka: 1) If the application commits to the DB, but crashes or loses network connectivity before `kafka.send()`, the event is permanently lost, causing silent downstream inconsistency. 2) If the application reverses the order (`kafka.send()` then `db.save()`), Kafka publishes the event, but the database transaction may fail (e.g., unique constraint violation), leaving ghost events in Kafka for rows that never existed. Change Data Capture (CDC) Architecture: 1) Mechanism: The application writes exclusively to PostgreSQL in a single local ACID transaction. 2) The database engine writes committed changes to its append-only Write-Ahead Log (WAL) on disk. 3) A CDC connector (e.g., Debezium) tails the WAL directly using logical replication decoding. 4) Advantages: 100% guarantee that every committed change—and ONLY committed changes—are captured and emitted to Kafka. It eliminates dual-write partial failures, survives application crashes, captures out-of-band updates, and decouples business code from messaging plumbing.",
        [
            "Identifies partial commit failures in application-level dual-writes (DB commits but Kafka drops, or vice versa)",
            "Explains CDC mechanism: reading committed transactions directly from the database Write-Ahead Log (WAL)",
            "Highlights that CDC guarantees exact alignment between committed DB state and emitted events without dual-write bugs"
        ],
        [
            "Claims dual-writing is superior because Debezium consumes 100% of the host machine's internet bandwidth"
        ]
    ),
    (
        "B68_4_11",
        "implement",
        "hard",
        "implement",
        ["Multi-Tenant Architecture", "Concurrency"],
        "Message Queues / Scheduling",
        "Fair Queuing and Noisy-Neighbor Starvation via Deficit Round Robin",
        "In a shared multi-tenant SaaS background processing cluster, Tenant A (a free-tier scraper) enqueues 200,000 tasks within 60 seconds, while Tenant B (a paying enterprise customer) enqueues 5 critical payment tasks. In a standard single-queue worker architecture, Tenant B's tasks sit behind Tenant A's 200,000 tasks for 3 hours. How do you implement a Fair Queuing algorithm like Deficit Round Robin (DRR) or virtual per-tenant queues to guarantee bounded latency for Tenant B?",
        "Standard FIFO queues suffer from head-of-line blocking by high-volume tenants. To implement fair multi-tenant scheduling: 1) Per-Tenant Virtual Queues: Instead of a single flat FIFO queue, the queue broker or Redis maintains separate virtual queues per tenant (`queue:tenant:A`, `queue:tenant:B`). 2) Deficit Round Robin (DRR) Worker Scheduling: Workers iterate across active tenant queues in round-robin fashion. Each tenant is allocated a quantum (credits/cost allowance per round). When inspecting Tenant A's queue: if Tenant A has credit, the worker pops tasks and decrements Tenant A's deficit counter until credits are exhausted, then immediately advances to Tenant B. 3) Work-Conserving Fairness: If Tenant B only has 5 tasks, workers execute all 5 tasks within milliseconds, exhausting Tenant B's backlog and immediately returning to process Tenant A's remaining work. 4) Concurrency Limits: Enforce a strict ceiling on concurrent worker threads executing tasks for any single tenant (e.g., max 10 threads out of 100 total for Tenant A). Tenant B's tasks are dispatched immediately without waiting behind Tenant A's 200,000 tasks.",
        [
            "Identifies head-of-line blocking in shared FIFO queues caused by high-volume tenants",
            "Implements per-tenant virtual queues and Deficit Round Robin (DRR) scheduling to rotate worker capacity",
            "Enforces per-tenant concurrency ceilings to guarantee low latency and immediate processing for low-volume tenants"
        ],
        [
            "Recommends deleting all tasks from Tenant A to allow Tenant B to run faster"
        ]
    ),
    (
        "B68_4_12",
        "scenario",
        "medium",
        "scenario",
        ["Multi-Tenant Architecture", "Caching"],
        "Redis / Caching",
        "Multi-Tenant Cache Namespacing and Eviction Isolation",
        "In a multi-tenant backend sharing a single Redis cluster, developers use generic cache keys: `user:{userId}` and `order:{orderId}`. Explain how this design creates severe security vulnerabilities (Tenant Cache Poisoning / Cross-Tenant Data Leakage) and how noisy-neighbor memory eviction can degrade performance across all tenants. How do you architect proper tenant cache isolation?",
        "Vulnerabilities of Generic Keys: 1) Cross-Tenant Data Leakage / Collisions: If Tenant 1 and Tenant 2 generate auto-incrementing integer IDs (`userId = 42`), Tenant 1's profile will overwrite or be read by Tenant 2, causing a catastrophic data breach. 2) Tenant Cache Poisoning: If an attacker in Tenant 1 can craft a key that collides with Tenant 2, they can inject malicious cached data. 3) Noisy-Neighbor Memory Eviction: Redis enforces global eviction policies (e.g., `allkeys-lru`). If Tenant 1 suddenly caches 500,000 large reports, Redis hits `maxmemory` and aggressively evicts frequently accessed hot keys belonging to Tenant 2 and Tenant 3, destroying cache hit rates across the entire platform. Architectural Solutions: 1) Strict Tenant Namespacing: Enforce key prefixes: `t:{tenant_id}:user:{user_id}` in all caching abstraction layers (preventing collision). 2) Tenant Eviction Isolation: For large enterprise tiers, provision dedicated Redis instances or separate Redis logical databases/ACLs. 3) Per-Tenant Cache Quotas / TTLs: Enforce aggressive TTLs and max-key limits per tenant in the application caching middleware to prevent a single tenant from exhausting shared cluster RAM.",
        [
            "Identifies cross-tenant data leakage and key collisions when using generic un-namespaced keys",
            "Explains noisy-neighbor eviction: one tenant filling RAM forces Redis allkeys-lru to evict other tenants' hot keys",
            "Enforces strict tenant-scoped key namespacing (t:{tenant_id}:...) and per-tenant memory quotas"
        ],
        [
            "Claims Redis automatically isolates tenants based on client IP addresses"
        ]
    ),
    (
        "B68_4_13",
        "scenario",
        "hard",
        "scenario",
        ["Multi-Tenant Architecture", "Cryptography"],
        "AWS KMS / Envelope Encryption",
        "Tenant-Specific Envelope Encryption (BYOK) and Instant Key Revocation",
        "An enterprise SaaS platform provides 'Bring Your Own Key' (BYOK) encryption for regulated enterprise customers. Each tenant's data stored in a shared PostgreSQL database must be encrypted using a dedicated Customer Master Key (CMK) hosted in the customer's own AWS KMS account. How do you implement Envelope Encryption in the backend application layer, and how do you ensure that if the customer revokes their KMS key, their data becomes instantaneously unreadable by anyone in your company?",
        "Envelope Encryption Implementation: 1) Mechanism: Encrypting every database row directly with AWS KMS is prohibitively slow and expensive (AWS KMS API limits and costs). Instead, use Envelope Encryption: A) For each tenant, the application requests a unique Data Encryption Key (DEK) from AWS KMS using the customer's CMK ARN: `kms.GenerateDataKey(KeyId=tenantCMK)`. B) KMS returns the Plaintext DEK and the Ciphertext DEK (encrypted by the customer's CMK). C) The application encrypts the sensitive data rows locally in RAM using AES-256-GCM with the Plaintext DEK. D) The application stores the encrypted data AND the Ciphertext DEK in the database row. The Plaintext DEK is discarded from memory immediately (or cached with a short 5-minute TTL). 2) Decryption Workflow: To read the data, the application sends the Ciphertext DEK back to the customer's AWS KMS: `kms.Decrypt(CiphertextKey)`. KMS decrypts the DEK using their CMK and returns the Plaintext DEK, allowing the app to decrypt the row. 3) Instant Key Revocation: If the enterprise customer suspects a breach or terminates their contract, they revoke access or delete their CMK in their own AWS account. The next time your backend attempts `kms.Decrypt()`, AWS KMS rejects the API call with `AccessDeniedException`. Because the backend cannot obtain the Plaintext DEK, the tenant's data becomes instantaneously cryptographically unreadable, achieving cryptographically guaranteed zero-knowledge data revocation.",
        [
            "Explains Envelope Encryption: local AES data encryption via Data Encryption Key (DEK) encrypted by customer's remote CMK",
            "Stores Ciphertext DEK alongside data while purging Plaintext DEK from RAM",
            "Demonstrates that revoking the customer's remote KMS CMK renders stored ciphertext permanently unreadable instantly"
        ],
        [
            "Recommends emailing the customer once a month asking them for their master AWS password"
        ]
    ),
    (
        "B68_4_14",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Multi-Tenant Architecture", "Database Architecture"],
        "Connection Pooling",
        "Shared Connection Pool vs Dynamic Per-Tenant Connection Pools",
        "When building a multi-tenant backend where each tenant has an isolated PostgreSQL database (Database-per-Tenant), what are the architectural tradeoffs between maintaining a 'Shared Global Connection Pool' versus 'Dynamic Per-Tenant Connection Pools' across 1,000 backend microservice instances?",
        "Database-per-Tenant requires connecting to thousands of distinct databases. 1) Dynamic Per-Tenant Connection Pools: Mechanics: Each backend application instance maintains an independent connection pool (e.g., HikariCP with 10 connections) for every tenant. Tradeoffs: Catastrophic Connection Explosion. If you have 500 tenants and 20 backend pods, $500 \times 20 \times 10 = 100,000$ open connections. Idle tenants consume database memory, and backend pods crash due to thread and file descriptor exhaustion. However, it provides absolute isolation: Tenant A's connection pool cannot starve Tenant B. 2) Shared Global Connection Pool with Dynamic Routing (or External Pooler like PgBouncer): Mechanics: The application maintains a shared connection pool, or routes all queries through a centralized connection multiplexer (PgBouncer in transaction pooling mode). Connections are dynamically bound to a specific tenant database for the duration of a single transaction, then immediately released back to the shared pool. Tradeoffs: Extremely memory efficient, scales to thousands of tenants, and keeps total physical database connections bounded. However, if Tenant A runs slow, unindexed queries that hold connections, it can exhaust the shared multiplexer pool, causing cross-tenant connection starvation unless strict per-tenant concurrency limits are enforced.",
        [
            "Calculates the massive connection multiplication of per-tenant pools ($tenants \\times pods \\times pool\\_size$)",
            "Highlights memory exhaustion and file descriptor limits when maintaining static per-tenant connection pools",
            "Analyzes shared connection multiplexing (e.g. PgBouncer transaction pooling) balancing resource efficiency vs noisy neighbor starvation"
        ],
        [
            "Claims PostgreSQL can comfortably handle 10 million concurrent direct connections without extra software"
        ]
    ),
    (
        "B68_4_15",
        "diagnose",
        "hard",
        "debugging",
        ["Multi-Tenant Architecture", "Concurrency"],
        "Thread Local / Context Propagation",
        "Tenant Context Leakage across Asynchronous Thread Pools",
        "In a multi-tenant Java/Spring Boot or Node.js backend, developers store the authenticated tenant ID in a `ThreadLocal` (or `AsyncLocalStorage`) during the initial HTTP request filter. In asynchronous background processing, code executes via a shared thread pool (`CompletableFuture.supplyAsync()` or worker threads). Intermittently, Tenant A's background worker writes confidential invoices into Tenant B's database schema. What causes this catastrophic tenant context leakage, and how do you guarantee immutable context propagation?",
        "Root Cause: Thread Pool Reuse and ThreadLocal Persistence. 1) In high-performance backend frameworks, worker threads in a thread pool (`ForkJoinPool`, `ThreadPoolExecutor`) are persistent and reused across millions of tasks to avoid OS thread creation overhead. 2) When Task 1 (for Tenant A) finishes, if the developer fails to explicitly clear the `ThreadLocal` (`tenantContext.remove()`), the tenant ID remains bound to that physical OS thread in memory. 3) When Task 2 (a background job for Tenant B, or a task without explicit context) is dispatched to that same worker thread, the thread still holds Tenant A's context. Task 2 executes queries using Tenant A's tenant ID, causing cross-tenant data contamination. Guarantees for Immutable Context Propagation: 1) Scoped Context Wrappers: Wrap tasks at submission time with an immutable context snapshot: `executor.submit(ContextAwareRunnable.wrap(task, currentContext))`. The wrapper captures the tenant ID when the task is scheduled, binds it when the worker thread begins, and *guarantees* cleanup in a mandatory `finally` block before yielding the thread. 2) Modern Language Primitives: In Java 21+, use `ScopedValue` rather than `ThreadLocal` to enforce strictly bounded lifetime; in Go, pass `context.Context` explicitly through all function signatures.",
        [
            "Diagnoses thread pool thread reuse preserving un-cleared ThreadLocal variables across independent tasks",
            "Explains that subsequent tasks inherit the previous tenant's context, causing severe cross-tenant data corruption",
            "Prescribes wrapping async tasks with context-propagating decorators enforcing cleanup in finally blocks or using ScopedValue"
        ],
        [
            "Claims thread leaks only happen on computers running Linux"
        ]
    ),
    (
        "B68_4_16",
        "explain",
        "medium",
        "explain",
        ["Multi-Tenant Architecture", "Data Governance"],
        "Compliance / GDPR",
        "Multi-Tenant Soft Deletion vs Hard Deletion and GDPR Erasure Guarantees",
        "When an enterprise tenant cancels their contract and invokes their GDPR 'Right to be Forgotten', why is simply setting `is_deleted = true` (soft deletion) legally and architecturally insufficient, and how do you execute a comprehensive Hard Deletion workflow across relational databases, S3 object storage, Elasticsearch, and immutable Kafka backups?",
        "Why Soft Deletion Fails GDPR: Article 17 of GDPR mandates the complete permanent erasure of personal data without undue delay. Setting `is_deleted = true` leaves customer PII permanently residing on disk, searchable by internal database admins and vulnerable to data breaches, which is an explicit compliance violation. Comprehensive Hard Deletion Architecture: 1) Relational DB Cascading Hard Purge: An asynchronous batch deletion job purges records from all relational tables in foreign-key dependency order (or uses cascading deletes with batch throttling to avoid table locks). 2) Object Storage Purging: Delete tenant-scoped buckets or invoke batch deletion APIs on S3 prefix: `s3://bucket/tenants/{tenant_id}/`. 3) Search Index Deletion: Issue `delete_by_query` in Elasticsearch: `{ query: { term: { tenant_id: '123' } } }` followed by index segment merging. 4) The Immutable Backup/Kafka Challenge: Kafka topics and database WAL backups are append-only and physically immutable; modifying historical backups is technically impossible. Solution: Cryptographic Erasure (Crypto-Shredding). If the tenant's data was encrypted with a unique per-tenant encryption key, deleting that tenant's key from the key management service instantaneously renders all historical data in Kafka logs, cold storage, and database snapshots permanently unrecoverable, satisfying GDPR compliance mathematically.",
        [
            "Explains why soft deletion fails GDPR Article 17 requirements for permanent personal data erasure",
            "Details asynchronous multi-system purging across databases, S3 prefixes, and Elasticsearch indices",
            "Solves the immutable log/backup challenge via Crypto-Shredding (deleting the tenant's unique encryption key)"
        ],
        [
            "Recommends formatting all hard drives in the datacenter whenever a user requests deletion"
        ]
    ),
    (
        "B68_4_17",
        "implement",
        "medium",
        "implement",
        ["Multi-Tenant Architecture", "Concurrency"],
        "Redis / Distributed Systems",
        "Per-Tenant Distributed Semaphores for Concurrency Throttling",
        "In a shared SaaS platform, users trigger heavy asynchronous PDF generation jobs. The background worker cluster has a maximum capacity of 50 concurrent PDF rendering processes. How do you implement a 'Per-Tenant Distributed Semaphore' in Redis to ensure that no single tenant can consume more than 5 concurrent rendering slots simultaneously, while leaving 45 slots available for other tenants?",
        "To enforce strict per-tenant concurrency limits across horizontally scaled workers: 1) Distributed Semaphore via Redis: For each tenant, maintain a Redis Sorted Set (ZSET) or Hash representing active leases: `semaphore:tenant:{tenant_id}`. 2) Atomic Acquisition via Lua Script: Before a worker begins rendering a tenant's PDF: A) Purge expired leases from the ZSET: `ZREMRANGEBYSCORE key -inf (now - lease_timeout)`. B) Check current active count: `ZCARD key`. C) If count $< 5$, insert a new lease entry: `ZADD key now worker_task_id`, set TTL on the key, and return 1 (Granted). D) If count $\ge 5$, return 0 (Denied / Capacity Exceeded). 3) Backpressure / Delayed Execution: If denied, the worker does NOT drop the job; it re-queues the job into the tenant's delayed queue or pauses that tenant's consumption channel for 2 seconds. 4) Explicit Release in Finally Block: When the PDF generation completes (or throws an exception), the worker immediately removes its task ID from the ZSET: `ZREM key worker_task_id`. 5) Crash Safety: If a worker pod crashes mid-render, the lease timeout automatically purges the orphaned slot on the next evaluation, guaranteeing slots are never permanently leaked.",
        [
            "Implements a distributed semaphore using Redis ZSET with atomic Lua script evaluation",
            "Checks current active count against the per-tenant threshold (max 5) before granting execution",
            "Uses timestamps and lease expiration to automatically reclaim slots if a worker crashes"
        ],
        [
            "Suggests using a Java AtomicInteger stored in a single server's local RAM"
        ]
    ),
    (
        "B68_4_18",
        "concept",
        "easy",
        "concept",
        ["Multi-Tenant Architecture", "Database Architecture"],
        "SaaS Architecture",
        "Multi-Tenant Database Isolation: Shared DB vs Schema vs DB-per-Tenant",
        "What are the three primary database multi-tenancy models (Shared Database / Shared Schema, Shared Database / Separate Schemas, and Database-per-Tenant), and what are their respective tradeoffs regarding cost, security isolation, and operational maintenance?",
        "1) Shared Database / Shared Schema (Row-Level Multi-Tenancy): All tenants share the exact same database and tables; every table includes a `tenant_id` column. Cost: Lowest possible infrastructure cost and highest resource density. Maintenance: Easiest schema migrations (run once). Tradeoffs: Weakest security isolation; vulnerable to application-level query bugs leaking cross-tenant data. 2) Shared Database / Separate Schemas: A single database instance, but each tenant has their own isolated PostgreSQL schema / namespace (`tenant_123.orders`). Cost: Low-to-moderate cost. Maintenance: Higher overhead; schema migrations must be run across hundreds of schemas. Isolation: Stronger; SQL queries cannot accidentally join across schemas without explicit permissions. 3) Database-per-Tenant: Each tenant is provisioned an entirely separate physical or logical database instance. Cost: Highest infrastructure cost (idle databases consume memory and CPU). Maintenance: Most complex; running schema migrations across 5,000 separate databases requires orchestration tools. Isolation: Absolute security and performance isolation; zero risk of cross-tenant data leakage or noisy-neighbor database lock contention; allows per-tenant backups and regional data residency.",
        [
            "Defines Shared Schema (lowest cost, highest density, highest risk of application data leakage)",
            "Defines Separate Schemas (moderate isolation and cost, complex multi-schema migrations)",
            "Defines Database-per-Tenant (maximum security and performance isolation, highest infrastructure and operational cost)"
        ],
        [
            "Claims Shared Schema means the database is publicly readable by anyone on the internet"
        ]
    ),
    (
        "B68_4_19",
        "diagnose",
        "medium",
        "debugging",
        ["Multi-Tenant Architecture", "Database Performance"],
        "PostgreSQL / MySQL",
        "Noisy Neighbor Database Disk I/O Starvation on Shared Schemas",
        "In a shared multi-tenant PostgreSQL database with 500 tenants, Tenant A initiates an unindexed analytics query: `SELECT * FROM events WHERE raw_payload LIKE '%error%'`. Within 5 seconds, API response times for all other 499 tenants spike from 10ms to 8,000ms, and CPU utilization reaches 100%. Explain how a single tenant's unindexed query starves database buffer pools and disk I/O, and what architectural safeguards must be enforced.",
        "Root Cause: Shared Buffer Pool Thrashing and Disk I/O Saturation. 1) An unindexed sequential table scan on a large table forces PostgreSQL to read gigabytes of data blocks from disk into the database's shared memory (`shared_buffers`). 2) This massive flood of cold pages flushes out the hot, frequently accessed cached indexes and pages belonging to the other 499 tenants (Buffer Pool Pollution). 3) When other tenants execute simple indexed lookups, their index blocks are no longer in RAM. Every single tenant query now incurs physical disk read I/O. 4) The disk controller and storage IOPS become completely saturated, causing query queues to back up and API latency to spike platform-wide. Safeguards: 1) Query Execution Timeouts: Enforce a strict `statement_timeout = '3s'` on all web API database connections to automatically terminate runaway queries. 2) Dedicated Read Replicas for Analytics: Route all customer reporting and search queries to an isolated read replica or analytical data warehouse (ClickHouse/Snowflake), strictly prohibiting analytical scans on the primary OLTP database. 3) Workload Management: Use PostgreSQL resource groups or connection-level memory limits (`work_mem`) to constrain individual query impact.",
        [
            "Diagnoses buffer pool thrashing: sequential scans evict hot cached pages of other tenants from RAM",
            "Explains disk I/O and IOPS saturation degrading all concurrent tenant queries",
            "Enforces aggressive statement_timeout and routes analytics queries to isolated read replicas or OLAP stores"
        ],
        [
            "Suggests telling developers never to write slow queries again"
        ]
    ),
    (
        "B68_4_20",
        "concept",
        "easy",
        "concept",
        ["Multi-Tenant Architecture", "Database Architecture"],
        "DevOps / CI/CD",
        "Progressive Schema Migrations across Multi-Tenant Fleets",
        "In a Database-per-Tenant architecture with 10,000 distinct tenant databases, running an `ALTER TABLE` schema migration sequentially would take 14 hours. How do engineering teams architect automated, progressive multi-tenant schema migration pipelines with failure blast-radius containment?",
        "Running migrations sequentially is too slow, while running on all 10,000 databases simultaneously risks exhausting DB connection limits or rolling out a broken migration platform-wide. Progressive Architecture: 1) Tenant Migration Ring Topology (Canary Rings): Divide tenant databases into deployment rings: Ring 0 (Internal dogfood tenants, 1%), Ring 1 (Low-risk beta tenants, 5%), Ring 2 (Standard tier tenants, 20%), Ring 3 (High-volume enterprise tenants, 74%). 2) Worker Pool Concurrency: A distributed migration runner uses a worker pool (e.g., 50 parallel workers) to execute migrations concurrently within a ring, strictly respecting database server connection and I/O limits. 3) Health Checks & Automated Rollback / Pause: Between rings, the pipeline pauses for 30 minutes to evaluate application error rates and database metrics. If error rates spike, the pipeline halts immediately, containing the blast radius to only the canary ring. 4) Schema Version Metadata: Each tenant database stores a `schema_migrations` ledger; applications use backward-compatible Expand/Contract coding patterns to ensure both old and new schema versions function concurrently during the rollout.",
        [
            "Divides tenant databases into progressive deployment rings (Canary, Beta, Enterprise) to contain blast radius",
            "Executes concurrent migrations using worker pools tuned to avoid database connection exhaustion",
            "Monitors application health metrics between rings to automatically halt rollout upon anomalies"
        ],
        [
            "Claims migrations should be run manually by an engineer logging into 10,000 database servers one by one"
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 4).")
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
    print("POST-BATCH AUDIT PART 4")
    print("========================================")
    print(f"Batch: 68 Part 4")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
