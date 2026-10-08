import asyncio
import json
import os
import re
import sys
import uuid
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

ROLE = "Database Developer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    ("B66_3_1", "tradeoff", "hard", "tradeoff", ["Replication", "Failover & Consistency"],
     "Explain the architectural differences between PostgreSQL Physical Streaming Replication and Logical Replication. In what scenarios would you strictly choose Logical over Physical?",
     "Physical Streaming Replication works at the disk-block level. It streams exact byte-for-byte WAL records from the primary to the replica, creating an identical binary clone. It is highly efficient but restricted: the replica must be read-only, must run the exact same major PostgreSQL version, and must replicate the entire cluster. Logical Replication decodes WAL into a logical format (e.g., 'INSERT row X into table Y'). Scenarios to strictly choose Logical: 1) Zero-downtime major version upgrades (replicating from PG 12 to PG 15); 2) Active-Active or Bi-directional replication setups; 3) Replicating only a subset of tables to a data warehouse; 4) Replicating between different OS architectures; 5) When the replica needs to be writable or needs additional indexes not present on the primary.",
     ["Defines Physical replication as block-level binary cloning with strict version requirements", "Defines Logical replication as decoding WAL into SQL-like mutations", "Identifies zero-downtime upgrades, partial replication, or writable replicas as key Logical use cases"],
     ["Claims physical replication uses slower network protocols than logical replication"]),

    ("B66_3_2", "scenario", "medium", "scenario", ["Replication", "Failover & Consistency"],
     "An application writes a new user profile to the Primary database and immediately redirects the user to their profile page, which reads from a Read Replica. The user occasionally sees a 'Profile Not Found' error, which disappears upon refreshing. What causes this 'Read-After-Write' inconsistency, and how do you resolve it?",
     "This is caused by Asynchronous Replication Lag. The primary commits the write and acknowledges the application, but the WAL stream takes several milliseconds (or seconds under load) to reach and replay on the Read Replica. When the application immediately queries the replica, the data hasn't arrived yet. Resolutions: 1) Synchronous Replication (forces primary to wait for replica, massive latency hit); 2) Session Consistency Routing: The application sets a flag/cookie upon writing, and the DB router sends all reads for that specific user's session to the Primary for the next 5 seconds; 3) Wait-for-GTID/LSN: The primary returns the Log Sequence Number of the commit, and the application queries the replica with a blocking request to wait until the replica has replayed past that specific LSN before executing the read.",
     ["Identifies asynchronous replication lag causing data to not yet exist on the read replica", "Proposes Session Consistency Routing (pinning writer to primary temporarily)", "Proposes LSN/GTID tracking or fully synchronous replication tradeoffs"],
     ["Claims the database cache needs to be flushed manually to fix the bug"]),

    ("B66_3_3", "concept", "medium", "concept", ["Sharding", "Distributed Databases"],
     "In a sharded database architecture, what is a 'Scattered Join' (or Cross-Shard Join), why is it a severe anti-pattern, and how do you avoid it?",
     "A Scattered Join occurs when a query needs to join data that lives on different physical database shards. Because the shards don't share memory or disk, the database router (or application) must pull massive amounts of unjoined data over the network from multiple shards into a single coordinator node to perform the join in memory. This destroys performance, consumes massive network bandwidth, and defeats the purpose of sharding. To avoid it: 1) Co-location: Carefully choose a Shard Key (e.g., tenant_id) so that all related data (users, orders, invoices for a tenant) lives on the exact same physical shard, allowing standard local joins; 2) Data Duplication: For small, frequently joined lookup tables (e.g., countries), replicate the table entirely to every single shard (Reference Tables).",
     ["Defines Scattered Join as joining data across disparate physical nodes over the network", "Explains the massive network and memory penalty of coordinator-node joining", "Recommends data co-location via strategic Shard Keys or Reference Table replication"],
     ["Claims Scattered Joins are optimized by creating cross-server foreign keys"]),

    ("B66_3_4", "diagnose", "hard", "debugging", ["Sharding", "Distributed Databases"],
     "A global social media platform shards its messages database by timestamp (time-based sharding). During a major viral event, the database cluster crashes despite having 50 shards available. What is the fundamental flaw in time-based sharding, and what sharding strategy fixes it?",
     "The fundamental flaw in time-based sharding (or monotonically increasing keys) is 'Hotspotting'. Because all new messages share the current timestamp, 100% of the write traffic is routed to a single physical shard (the 'current' time shard), completely overwhelming its CPU and I/O. The other 49 historical shards sit idle, processing only reads. The cluster crashes because write capacity cannot scale horizontally. To fix this, you must use Hash-based Sharding on a high-cardinality key (e.g., hash(user_id) or hash(message_id)). This evenly distributes the write workload across all 50 shards simultaneously. If time-range queries are required, a composite shard key (e.g., hash(user_id) + timestamp) can be used to balance writes while localizing user history.",
     ["Identifies 'Hotspotting' where monotonically increasing keys funnel 100% of writes to a single shard", "Explains that horizontal write scaling is entirely defeated by time-based keys", "Recommends Hash-based sharding or Composite keys to distribute write load"],
     ["Suggests fixing the crash by increasing the RAM on the historical shards"]),

    ("B66_3_5", "concept", "easy", "concept", ["Sharding", "Database Architecture"],
     "Explain the concept of 'Consistent Hashing' and why it is critical when adding or removing shards in a distributed database system.",
     "In standard modulo hashing (hash(key) % N_shards), if you add a new shard (changing N from 4 to 5), the mathematical result for almost every single key changes. This requires rebalancing and moving nearly 100% of the data across the network, taking the system offline. Consistent Hashing places shards and data keys on a virtual circular ring. When a data key is hashed, it walks clockwise around the ring until it finds the first shard. When a new shard is added to the ring, it only takes over a small slice of the circle from its immediate neighbor. Thus, only 1/N of the data needs to be moved to the new shard, leaving the vast majority of the data safely untouched, allowing elastic scaling with minimal disruption.",
     ["Contrasts Consistent Hashing with standard modulo hashing", "Explains the virtual ring topology allowing shards to claim adjacent subsets", "Highlights the critical benefit: moving only 1/N of the data instead of 100% during resharding"],
     ["Confuses consistent hashing with cryptographic password hashing (bcrypt)"]),

    ("B66_3_6", "tradeoff", "medium", "tradeoff", ["NoSQL", "Distributed Consensus"],
     "In an AP NoSQL database like Cassandra or DynamoDB, what is the tradeoff of using a Read Quorum (R) + Write Quorum (W) > N (Replication Factor) configuration?",
     "The formula R + W > N guarantees Strong Consistency (preventing stale reads) in an eventually consistent distributed system. For example, with a Replication Factor of 3, setting Write Quorum = 2 and Read Quorum = 2 ensures that the read and write operations will always overlap on at least one node, guaranteeing the reader sees the latest written value. Tradeoff Advantages: Strong data consistency without requiring a single master node. Tradeoff Disadvantages: Increased latency (writes must wait for network ACKs from multiple nodes over the WAN) and reduced availability. If 2 out of 3 nodes go down, the database completely rejects all reads and writes because it cannot mathematically satisfy the quorum, defeating the primary 'High Availability' purpose of the AP system.",
     ["Explains the mathematical guarantee of R + W > N enforcing read/write overlap", "Identifies advantage: Strong consistency in masterless systems", "Identifies disadvantage: Higher latency and loss of true high availability during node failures"],
     ["Claims quorum formulas are used to calculate the database's monthly cloud billing"]),

    ("B66_3_7", "diagnose", "medium", "debugging", ["NoSQL", "Database Operations"],
     "In Apache Cassandra, a developer frequently uses DELETE to remove millions of old records. Suddenly, simple SELECT queries for the remaining active data start timing out, and disk usage actually increases. What are 'Tombstones', and why do massive deletes destroy Cassandra read performance?",
     "Cassandra is an LSM-tree based append-only database. It cannot physically delete a record in-place. Instead, a DELETE command inserts a new, special marker called a 'Tombstone'. Tombstones act as anti-data, suppressing older versions of the row during read operations. If millions of rows are deleted, millions of Tombstones are created (increasing disk size). When a SELECT query runs, Cassandra must scan the disk, fetch the data, and then process millions of Tombstone markers in CPU/memory to determine what data to hide from the client. This massive read amplification causes the timeouts. Resolution: Avoid massive deletes. Use Time-To-Live (TTL) expiration upon insertion, or drop entire partitions/tables, which avoids Tombstone creation entirely.",
     ["Defines Tombstones as append-only markers suppressing old data", "Explains that disk size increases and reads time out because Cassandra must scan and process the markers", "Recommends TTL or dropping partitions instead of row-by-row DELETEs"],
     ["Claims Tombstones are an index fragmentation issue fixed by defragmenting the disk"]),

    ("B66_3_8", "concept", "easy", "concept", ["Replication", "High Availability"],
     "What is 'Replication Lag', and what are the primary hardware and network bottlenecks that cause it?",
     "Replication Lag is the time difference (latency) between when a transaction is committed on the Primary database and when that identical transaction is replayed and visible on the Read Replica. Primary causes: 1) Network Bandwidth/Latency: If the replica is in a different geographic region, network constraints delay WAL transmission. 2) Disk I/O Bottlenecks: The primary writes transactions using multiple concurrent threads, but the replica often replays the WAL stream using a single thread. If the replica's disk cannot keep up with the primary's write throughput, lag spikes. 3) Lock Contention: If the replica is serving long-running read queries, those queries hold shared locks that can block the replication thread from applying conflicting updates (e.g., dropping a table or altering a schema).",
     ["Defines replication lag as the time delta for transaction visibility on replicas", "Identifies single-threaded WAL replay vs multi-threaded primary writes", "Identifies network latency and lock contention from long-running replica reads"],
     ["Claims replication lag is caused by the database caching data in the browser"]),

    ("B66_3_9", "implement", "hard", "implement", ["NoSQL", "Database Internals"],
     "In a Dynamo-style distributed database (like Riak or Cassandra), what is 'Hinted Handoff', and how does it prevent data loss during temporary node failures without requiring an immediate full-cluster rebalance?",
     "Hinted Handoff is a resiliency mechanism for temporary node outages. If Node A is supposed to receive a write, but is temporarily offline due to a network blip, the coordinator node will not fail the write. Instead, it writes the data locally to a neighboring Node B, along with a 'Hint' (a metadata tag) stating 'This data belongs to Node A'. Node B stores this in a separate, isolated queue. Once Node A comes back online, Node B immediately detects the heartbeat and 'hands off' (streams) the queued data to Node A. This provides High Availability for writes and self-heals temporary outages instantly, avoiding the massive network I/O penalty of triggering a full anti-entropy repair or cluster rebalancing for a 5-second network flap.",
     ["Explains neighboring nodes storing 'hints' for temporarily offline nodes", "Describes the automatic playback/streaming mechanism when the offline node recovers", "Highlights the avoidance of expensive cluster-wide repairs for transient network blips"],
     ["Confuses hinted handoff with DNS failover routing"]),

    ("B66_3_10", "tradeoff", "medium", "tradeoff", ["Replication", "Failover & Consistency"],
     "When configuring High Availability (HA) for a relational database, what are the architectural tradeoffs of using a Shared-Disk failover cluster (e.g., AWS Aurora or SAN) versus a Shared-Nothing replication cluster (e.g., standard PostgreSQL Streaming Replication)?",
     "Shared-Disk Architecture uses multiple compute nodes connecting to a single, highly available storage layer. Advantages: Failover is near-instantaneous (the standby just attaches to the disk), there is zero replication lag (all nodes see the exact same disk blocks), and it requires no WAL streaming over the network. Disadvantages: The storage layer is a single point of failure (if the SAN corrupts the file system, all nodes die simultaneously), and write-scaling is impossible since there is only one disk. Shared-Nothing Architecture uses completely independent servers with their own CPU, RAM, and internal SSDs, syncing via WAL over the network. Advantages: Perfect isolation. Hardware failure or disk corruption on the primary does not impact the replica. Disadvantages: Slower failover, potential data loss (if async), and vulnerability to network partitions (Split-Brain scenarios).",
     ["Contrasts Shared-Disk (single storage layer) with Shared-Nothing (independent physical disks)", "Identifies Shared-Disk advantages: instantaneous failover and zero replication lag", "Identifies Shared-Nothing advantages: physical isolation and protection against SAN file system corruption"],
     ["Claims Shared-Disk architectures require manual USB drive transfers between servers"]),

    ("B66_3_11", "scenario", "medium", "scenario", ["Distributed Databases", "Failover & Consistency"],
     "In a globally distributed database, a network cable is severed, isolating the European data center from the US data center (a Network Partition). According to the CAP Theorem, the system must now choose between Consistency or Availability. Describe how the database behaves in this exact moment if it is configured for CP versus AP.",
     "According to the CAP theorem, when a Partition (P) occurs, you must sacrifice C or A. If the system is CP (Consistency/Partition Tolerance), the European data center detects it cannot communicate with the US master to verify the global state. To prevent split-brain and ensure consistency, it immediately stops accepting all writes (and potentially reads), sacrificing Availability until the network heals. If the system is AP (Availability/Partition Tolerance), both the European and US data centers continue accepting writes independently, remaining fully Available. However, this sacrifices Consistency: European users and US users will see entirely different data, and the system will experience a massive data conflict (divergent states) that must be merged via vector clocks or last-write-wins when the network is eventually restored.",
     ["Correctly applies CAP theorem to a physical network partition scenario", "Explains CP behavior: halting writes to guarantee absolute data correctness globally", "Explains AP behavior: accepting concurrent isolated writes, requiring eventual conflict resolution"],
     ["Claims CAP theorem states a database can never run in two countries simultaneously"]),

    ("B66_3_12", "concept", "easy", "concept", ["NoSQL", "Distributed Databases"],
     "What are 'Vector Clocks', and how do they resolve data divergence in AP (Available/Partition Tolerant) distributed databases?",
     "A Vector Clock is an array of counters attached to a piece of data, tracking which node updated it and when (e.g., [NodeA:2, NodeB:1]). In an AP system, network partitions allow two different nodes to update the exact same record concurrently, creating conflicting versions. When the network heals, the database compares the Vector Clocks. If one clock is strictly greater than the other (e.g., [NodeA:3, NodeB:1] vs [NodeA:2, NodeB:1]), the database safely drops the older version. If the clocks are divergent (e.g., [NodeA:3, NodeB:1] vs [NodeA:2, NodeB:2]), the database detects a concurrent conflict. It cannot resolve it automatically, so it returns both conflicting versions to the client application, forcing the application's business logic to merge them (e.g., merging two shopping cart arrays).",
     ["Defines Vector Clocks as arrays of node-specific version counters", "Explains the comparison logic to determine chronological dominance", "Explains returning divergent versions to the client application for manual merging"],
     ["Claims Vector Clocks are hardware atomic clocks synchronized via GPS"]),

    ("B66_3_13", "diagnose", "hard", "debugging", ["Sharding", "Database Operations"],
     "You manage a manually sharded PostgreSQL cluster using an application-level routing layer. You need to perform a 'Resharding' operation (moving a tenant from Shard A to Shard B) with absolutely zero downtime. How do you execute this migration without losing writes or locking the application?",
     "Zero-downtime resharding requires a dual-write state machine migration. 1) Preparation: Create the tenant's schema/tables on Shard B. 2) Dual-Write: Update the app router to write all new INSERTS/UPDATES to BOTH Shard A and Shard B synchronously, while continuing to read only from Shard A. 3) Backfill: Write a background script to slowly copy historical data from Shard A to Shard B, ignoring collisions (since dual-write handles the newest data). 4) Verification: Run a checksum script to verify Shard A and Shard B data perfectly match for that tenant. 5) Cutover: Update the app router to read and write exclusively to Shard B. 6) Cleanup: Delete the tenant's data from Shard A. This guarantees zero downtime and prevents data loss.",
     ["Outlines a phased dual-write migration strategy", "Identifies routing new writes to both shards simultaneously before backfilling old data", "Identifies checksum verification and instantaneous router cutover"],
     ["Recommends taking the database offline for 5 minutes during the lowest traffic window"]),

    ("B66_3_14", "implement", "medium", "implement", ["NoSQL", "Database Operations"],
     "In MongoDB, you have a collection of session tokens and you create a TTL (Time-To-Live) index to automatically delete them after 30 days: db.sessions.createIndex({ 'createdAt': 1 }, { expireAfterSeconds: 2592000 }). However, you notice that tokens from 32 days ago are still occasionally present in the collection. What causes this delay, and how does the TTL thread operate?",
     "MongoDB TTL indexes do not guarantee that a document is deleted the exact millisecond it expires. The TTL mechanism is driven by a background thread in the mongod process that wakes up only once every 60 seconds. When it wakes up, it queries the index for expired documents and issues standard DELETE operations. If the database is under severe load, or if millions of documents expire at the exact same time, the TTL thread must yield to foreground application traffic and cannot delete them instantly. Therefore, documents can remain visible in queries for minutes or even hours after their expiration time. To fix this at the application level, any find() query on the sessions collection MUST include an explicit filter: createdAt: { $gt: thirty_days_ago } to logically hide expired documents before the background thread physically deletes them.",
     ["Explains the MongoDB TTL background thread running periodically (60s intervals)", "Explains the thread yielding to heavy foreground write traffic, causing deletion backlogs", "Recommends application-level filtering to logically enforce the TTL while physical deletion lags"],
     ["Claims the TTL index was created with the wrong time zone format"]),

    ("B66_3_15", "concept", "hard", "concept", ["Distributed Databases", "Database Internals"],
     "Explain the 'Read Repair' mechanism in Cassandra. How does it maintain data consistency in a cluster where the Read Quorum is satisfied, but some nodes return stale data?",
     "In Cassandra, a client requests data with a Read Quorum (e.g., 2 out of 3 nodes). The coordinator node sends data requests to the fastest node, and hash-digest requests (checksums) to the other nodes. If the fastest node returns Value=X and the second node returns a digest indicating it holds Value=Y, the coordinator detects a consistency mismatch. It then pulls the full data from all nodes, compares their internal timestamps, and returns the newest version to the client. Crucially, before closing the request, the coordinator initiates a 'Read Repair': it asynchronously sends the newest data version back to the node(s) holding the stale data, forcing them to overwrite it. This mechanism self-heals data drift 'on-the-fly' during normal read operations without requiring massive cluster-wide repair jobs.",
     ["Describes coordinator requesting digests from secondary nodes to compare against primary data", "Explains timestamp resolution to determine the authoritative latest value", "Describes the asynchronous background push of corrected data to stale nodes"],
     ["Confuses Read Repair with the disk defragmentation 'nodetool repair' command"]),

    ("B66_3_16", "tradeoff", "medium", "tradeoff", ["Replication", "Database Operations"],
     "What is the tradeoff of using Statement-Based Replication (SBR) versus Row-Based Replication (RBR) in MySQL?",
     "Statement-Based Replication streams the exact SQL query (e.g., UPDATE users SET status = 'active' WHERE id < 100) to the replica. Advantages: Tiny network bandwidth footprint and low WAL (Binlog) size. Disadvantages: Severe consistency risks. Non-deterministic queries (e.g., using RAND(), NOW(), or implicitly relying on unordered LIMIT) will execute differently on the replica, permanently corrupting data consistency. Row-Based Replication streams the actual physical changes to the rows (e.g., 'Change Row 5 from X to Y'). Advantages: Absolute deterministic data consistency, immune to non-deterministic functions. Disadvantages: Massive network and disk overhead. A single UPDATE users SET points = 0 query could modify 10 million rows, generating gigabytes of RBR binlogs for a single SQL statement.",
     ["Contrasts replicating SQL syntax (SBR) vs physical row mutations (RBR)", "Highlights SBR vulnerability to non-deterministic functions (NOW, RAND) corrupting replicas", "Highlights RBR tradeoff of massive binlog bloat for bulk update statements"],
     ["Claims Statement-Based Replication encrypts the SQL queries for security"]),

    ("B66_3_17", "scenario", "medium", "scenario", ["Distributed Databases", "Concurrency"],
     "In a globally distributed database using asynchronous active-active (multi-master) replication, two users in different regions update the exact same row simultaneously. Region A sets status = 'APPROVED', and Region B sets status = 'REJECTED'. How do systems like Spanner or Cassandra resolve this inherent conflict when the replication streams finally merge?",
     "Asynchronous active-active databases must use a deterministic conflict resolution algorithm because neither write blocked the other. The most common default algorithm is 'Last-Write-Wins' (LWW). The database attaches a timestamp to every write. When the streams merge, the engine compares the timestamps, keeps the mutation with the highest timestamp, and silently discards the other. Systems like Google Spanner use TrueTime (atomic clocks) to guarantee strict chronological ordering of these timestamps globally. Systems like Cassandra rely on the application server's local NTP clock. If NTP is out of sync (Clock Skew), LWW can result in a write from 5 seconds ago silently overwriting a write from 1 second ago, leading to inexplicable data loss. Alternative resolutions include Custom Conflict Handlers (CRDTs) where the application code defines the merge logic.",
     ["Identifies Last-Write-Wins (LWW) timestamp comparison as the default resolution", "Highlights the danger of clock skew (NTP) in Cassandra causing silent data loss", "Mentions TrueTime (Spanner) or CRDTs as advanced conflict resolution mechanisms"],
     ["Claims the database automatically asks the user via email which version to keep"]),

    ("B66_3_18", "diagnose", "medium", "debugging", ["Replication", "Performance & Tuning"],
     "You monitor a PostgreSQL Read Replica and notice that during heavy reporting queries, the replication lag spikes significantly. Checking the logs, you see 'canceling statement due to conflict with recovery'. What causes this conflict, and how do you resolve it?",
     "This is a classic MVCC replication conflict. The Primary database executes a DELETE or UPDATE, and autovacuum cleans up the dead tuple. This cleanup is written to the WAL and streamed to the Replica. However, the Replica is currently running a long 30-minute reporting query that *needs* to read that specific old tuple to maintain its snapshot consistency. If the Replica replays the WAL, it destroys the old tuple and ruins the reporting query. By default, PostgreSQL waits a short time (max_standby_streaming_delay, default 30s) and then violently kills the reporting query to keep replication moving. Resolution: 1) Increase max_standby_streaming_delay (allows the replica to intentionally lag behind the primary until the report finishes); 2) Enable hot_standby_feedback = on, which makes the replica inform the primary about its oldest active snapshot, preventing the primary's autovacuum from deleting the tuple in the first place (tradeoff: can cause massive bloat on the primary).",
     ["Identifies primary autovacuum cleanup conflicting with long-running replica query snapshots", "Explains that PostgreSQL kills the replica query to prevent WAL replay stagnation", "Suggests tuning max_standby_streaming_delay or enabling hot_standby_feedback (with bloat tradeoff warning)"],
     ["Suggests the error means the replica hard drive is physically corrupted"]),

    ("B66_3_19", "implement", "hard", "implement", ["Sharding", "Database Internals"],
     "How do you implement a 'Global Secondary Index' (GSI) in a horizontally sharded database environment, and why are reads against a GSI inherently eventually consistent?",
     "In a sharded database, the primary data is distributed by the Shard Key (e.g., user_id). If you need to query by email efficiently without scattered joins, you must build a Global Secondary Index. A GSI is essentially a completely separate, asynchronously replicated sharded table where the Shard Key is email, and the payload is the user_id. Implementation: When a write occurs on the Primary table, an asynchronous event (e.g., via Change Data Capture or Kafka) is fired to update the GSI table. Why it's eventually consistent: The primary data write and the GSI index write occur on completely different physical shards. Enforcing a synchronous distributed 2PC transaction across shards for every single index update would destroy write availability. Therefore, the GSI is updated asynchronously, meaning a user might update their email, but querying the GSI milliseconds later might still return the old email or no result.",
     ["Defines GSI as a secondary table sharded by the alternate query key", "Explains asynchronous propagation (CDC/events) to populate the GSI", "Explains that synchronous 2PC cross-shard index updates are avoided to preserve write availability, causing eventual consistency"],
     ["Claims a Global Secondary Index is an index stored on the global DNS server"]),

    ("B66_3_20", "tradeoff", "medium", "tradeoff", ["Replication", "Failover & Consistency"],
     "What is the tradeoff between configuring PostgreSQL replication as async vs sync, and how does sync impact the primary database when the network connection to the replica drops?",
     "Asynchronous replication writes to the primary disk and returns success to the client immediately, streaming WAL to the replica in the background. Tradeoff: Maximum write throughput, but risks data loss if the primary crashes before the WAL reaches the replica. Synchronous replication (synchronous_commit = on and synchronous_standby_names configured) forces the primary to wait until the replica receives and writes the WAL to its disk before returning success to the client. Tradeoff: Guarantees zero data loss (RPO = 0), but adds network round-trip time to every transaction, severely reducing write throughput. Critical impact: If the network drops or the replica crashes, the Primary database will hang indefinitely on all COMMIT statements, bringing the entire application to a halt until the replica comes back online or the DBA manually disables synchronous replication.",
     ["Contrasts throughput speed (async) with zero-data-loss guarantee (sync)", "Identifies the penalty of adding network round-trip latency to every sync commit", "Explains the catastrophic failure mode: sync replication halts all primary writes if the replica disconnects"],
     ["Claims synchronous replication uses a cron job every 5 minutes"])
]

def run_batch():
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[5]) or LEAK.search(q[6]):
            print(f"PROMPT LEAK DETECTED in: {q[5]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[5] for q in Q]
    
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
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[5][:50]}...")
            rejected.append(q)
        else:
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 3).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Backend Developer", "Data Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "PostgreSQL",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "Database Engineering",
            "intent": q[1],
            "difficulty": q[2],
            "question_type": q[3],
            "question": q[5],
            "expected_answer": q[6],
            "evaluation_rubric": {
                "strong_indicators": q[7],
                "weak_indicators": q[8]
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
        
    role_counts = Counter(r["primary_role"] for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT PART 3")
    print("========================================")
    print(f"Batch: 66 Part 3")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
