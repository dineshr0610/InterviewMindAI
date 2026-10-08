"""Batch 36 Part 1 question content (Database Developer). Targeted Gap Generation."""

ROLE = "Database Developer"

BUCKET_KEYS = {
    "DB_ARCHITECTURE_AND_HA": ("Database Architecture", "Replication & HA", "Database", ["Database Developer", "Backend Developer", "DevOps / Cloud Engineer"]),
}

Q = [
# ---------------- DB_ARCHITECTURE_AND_HA ----------------
("DB_ARCHITECTURE_AND_HA", "tradeoff", "hard", "tradeoff", ["Replication", "Consistency"],
 "When architecting a high-availability database cluster, what is the exact tradeoff of configuring synchronous replication versus asynchronous replication?",
 "Synchronous replication guarantees zero data loss (RPO=0) because the primary waits for the replica to acknowledge the write before committing. Tradeoff: Heavily increased write latency and potential DB lockup if the replica goes offline. Asynchronous replication maximizes write performance (primary commits instantly), but trades off consistency, risking permanent data loss if the primary crashes before the WAL is shipped.",
 ["Synchronous: Guarantees zero data loss (RPO=0), but drastically increases write latency and risks freezing writes if replicas drop", "Asynchronous: Maximizes write throughput and availability, but risks permanent data loss on primary crash", "Tradeoff is fundamentally Performance/Availability vs Strict Consistency"],
 ["Synchronous runs on a clock, asynchronous runs randomly"]),

("DB_ARCHITECTURE_AND_HA", "scenario", "medium", "scenario", ["Failover", "Replication Lag"],
 "You manage an async primary-replica cluster. The primary suffers catastrophic hardware failure. You promote the replica. After failover, users report recent transactions they saw just before the crash are now missing. What architectural concept explains this?",
 "This is 'Replication Lag'. In asynchronous replication, transactions are acknowledged to the client by the primary *before* the Write-Ahead Log (WAL) changes are successfully transmitted and applied to the replica. When you promoted the replica, those in-flight transactions were permanently lost, resulting in an RPO (Recovery Point Objective) > 0.",
 ["Replication Lag in asynchronous replication", "The primary acknowledged the client's write before shipping the WAL to the replica", "When the primary died, those unshipped transactions were permanently lost (RPO > 0)"],
 ["The database decided to rollback the transactions for safety"]),

("DB_ARCHITECTURE_AND_HA", "debug", "hard", "debugging", ["Sharding", "Data Skew"],
 "In a sharded database, Shard 1 consumes 99% CPU and bottlenecks, while Shards 2, 3, 4 are idle. The sharding key is `customer_id` hashed using modulo (`id % 4`). What is this specific architectural failure, and how do you fix it?",
 "This is a 'Hot Shard' or 'Hot Partition' caused by extreme data skew. Even though the hash distributes the raw ID evenly, one specific customer (e.g., a massive enterprise account) generates 90% of the traffic, overwhelming their designated shard. You must fix this by using a more granular or composite Shard Key (e.g., `customer_id + timestamp` or `device_id`) to evenly distribute that customer's traffic.",
 ["A 'Hot Shard' / 'Hot Partition' caused by extreme traffic/data skew from a single massive tenant", "Standard modulo hashing fails if a single key generates vastly disproportionate load", "Fix: Redesign the Shard Key to be more granular (e.g., appending a timestamp) to spray the load across shards"],
 ["The shard needs a bigger CPU cooling fan"]),

("DB_ARCHITECTURE_AND_HA", "explain", "easy", "concept", ["Disaster Recovery", "WAL"],
 "In a relational database, what is the architectural purpose of a Write-Ahead Log (WAL), and how does it prevent data loss during a sudden power failure?",
 "The WAL is an append-only file where all database modifications are sequentially written to disk *before* they are applied to the actual data files (the heap). Writing sequentially is vastly faster than random I/O. If a power failure occurs, the database recovers on startup by simply reading the WAL and re-applying (replaying) the logged changes to the data files, ensuring strict Durability.",
 ["Append-only file where modifications are logged sequentially before updating actual data files", "Sequential disk writes are vastly faster than random I/O (updating the B-Tree directly)", "During crash recovery, the database replays the WAL to restore any uncommitted/unflushed data (Durability)"],
 ["The WAL is a firewall that blocks unauthorized writes"]),

("DB_ARCHITECTURE_AND_HA", "implement", "medium", "implementation", ["Distributed Transactions", "Two-Phase Commit"],
 "A microservices architecture requires an order DB and a billing DB to update atomically. If one fails, both rollback. What distributed database protocol implements this guarantee, and what is its primary weakness?",
 "You implement the 'Two-Phase Commit' (2PC) protocol. A transaction coordinator prepares both databases, and if both agree, it issues the commit. Its primary weakness is that it is a blocking, synchronous protocol; if the coordinator crashes during the commit phase, the databases are left holding exclusive locks indefinitely, freezing the system.",
 ["Implements the 'Two-Phase Commit' (2PC) protocol", "Phase 1: Prepare (lock resources). Phase 2: Commit (execute)", "Primary weakness: It is blocking. If the coordinator crashes mid-commit, databases hold locks indefinitely"],
 ["Use a try-catch block around both network calls"]),

("DB_ARCHITECTURE_AND_HA", "tradeoff", "medium", "tradeoff", ["PostgreSQL", "Replication"],
 "When replicating PostgreSQL databases, what is the architectural tradeoff of using Logical Replication versus Physical (Streaming) Replication?",
 "Physical replication copies exact binary disk blocks (WAL), ensuring a perfectly identical byte-for-byte clone. It is fast, but the replica must run the exact same DB version, and it is strictly read-only. Logical replication decodes the WAL into row-level SQL statements. Tradeoff: Logical uses vastly more CPU, but allows cross-version replication, partial table replication, and allows the replica to accept writes.",
 ["Physical Replication: Byte-for-byte exact clone. Fast, but strictly read-only and requires identical DB versions", "Logical Replication: Decodes WAL into SQL statements", "Logical Tradeoff: Higher CPU overhead, but allows partial replication, cross-version upgrades, and writable replicas"],
 ["Physical replication uses USB drives, logical uses Wi-Fi"]),

("DB_ARCHITECTURE_AND_HA", "scenario", "hard", "scenario", ["CAP Theorem", "Network Partitions"],
 "A network partition severs communication between Data Center A and Data Center B. According to the CAP theorem, if the database is configured to prioritize Consistency (a CP system), what exactly will the database do to clients?",
 "To guarantee Consistency (CP) during a network partition, the database will deliberately refuse to accept writes (and potentially reads) from the minority partition. It will effectively declare downtime (sacrificing Availability) to ensure that no split-brain scenario occurs and that clients do not read stale or conflicting data.",
 ["The database will sacrifice Availability to guarantee Consistency", "It will deliberately reject writes (and potentially reads) from nodes that lose quorum", "Ensures no split-brain or divergent data corruption occurs"],
 ["It will slow down the network to fix the consistency"]),

("DB_ARCHITECTURE_AND_HA", "debug", "medium", "debugging", ["Quorum", "Consistency"],
 "A 5-node NoSQL cluster uses Quorum replication. Read quorum (R) is 2, Write quorum (W) is 3. A client writes a record, but a read immediately after returns stale data. Why did this configuration fail to provide Strong Consistency?",
 "To guarantee strong consistency (reading the latest write), a quorum system must obey the rule: `R + W > N`. Here, `2 + 3 = 5`, which is NOT strictly greater than `N` (5). Because `R + W` equals `N`, a read request might hit 2 nodes that were *not* part of the 3 nodes that received the write, resulting in stale data. You must increase R to 3 or W to 4.",
 ["Quorum strict consistency requires `R + W > N`", "`2 + 3 = 5`, which does not overlap on a 5-node cluster", "The 2 read nodes could be the exact 2 nodes that did NOT receive the write", "Fix: Increase R to 3 or W to 4 to guarantee node overlap"],
 ["The nodes were too far apart geographically"]),

("DB_ARCHITECTURE_AND_HA", "explain", "medium", "concept", ["Split-Brain", "High Availability"],
 "What is a 'Split-Brain' scenario in a high-availability database cluster, and how do modern systems prevent it?",
 "Split-Brain occurs when a network failure causes two database nodes to lose contact with each other, and both incorrectly assume the other is dead. Both promote themselves to 'Primary' and accept writes, resulting in massive, irreconcilable data corruption. Systems prevent this using 'Fencing' (cutting power/network to the old primary) or by using consensus protocols (Raft/Paxos) requiring a strict majority vote.",
 ["A network partition causes multiple nodes to incorrectly assume the primary is dead", "Multiple nodes promote themselves to Primary, accepting conflicting writes (data corruption)", "Prevented via Fencing (STONITH) or distributed consensus protocols (Raft) requiring a majority quorum vote"],
 ["It is when the DBA team can't agree on a schema design"]),

("DB_ARCHITECTURE_AND_HA", "implement", "easy", "implementation", ["PITR", "Backups"],
 "You need to perform a Point-in-Time Recovery (PITR) to precisely 2:05 PM yesterday. What two components are fundamentally required to execute this recovery?",
 "You require 1) A full Base Backup (snapshot) taken prior to the target time, and 2) The continuous archive of the Write-Ahead Logs (WAL) spanning from the exact time of the base backup up to the 2:05 PM target. The database restores the snapshot and then replays the WAL sequentially to arrive at that exact millisecond.",
 ["A full Base Backup (snapshot) taken before the target recovery time", "The continuous Write-Ahead Log (WAL) archives from the backup up to the target time", "The database replays the WAL on top of the snapshot to reach the exact state"],
 ["A time machine and a lot of luck"]),

("DB_ARCHITECTURE_AND_HA", "tradeoff", "hard", "tradeoff", ["Consistent Hashing", "Sharding"],
 "What is the architectural tradeoff of using 'Consistent Hashing' instead of standard modulo hashing (`hash(key) % N`) when distributing data across a database cluster?",
 "Standard modulo hashing causes a catastrophic data reshuffle if a node is added/removed because the denominator `N` changes, altering the location of almost every key. Consistent Hashing places nodes and keys on a logical ring. Advantage: Adding/removing a node only requires moving data from its immediate neighbors. Tradeoff: Increased complexity and potential data imbalance on the ring (requiring 'virtual nodes' to fix).",
 ["Modulo hashing causes massive data reshuffling when nodes are added/removed (denominator changes)", "Consistent Hashing on a logical ring minimizes data movement (only neighbors are affected)", "Tradeoff: Potential data/load imbalance across nodes, requiring complex 'virtual node' configurations"],
 ["Consistent hashing is much slower at generating hashes"]),

("DB_ARCHITECTURE_AND_HA", "scenario", "medium", "scenario", ["Replication", "Read-Your-Own-Writes"],
 "You manage a primary DB with a read replica. Users complain that when they update their profile and immediately redirect, they sometimes see old data. What is the standard architectural pattern to solve this 'Read-Your-Own-Writes' problem?",
 "You implement 'Read-Your-Own-Writes' consistency routing at the application layer. The app tracks if the user has mutated data recently (e.g., setting a flag in the session with a timestamp). If they wrote data within the replication lag window (e.g., the last 5 seconds), the app forcibly routes their read queries directly to the Primary database instead of the Replica.",
 ["Implement 'Read-Your-Own-Writes' consistency routing in the application layer", "Track recent mutations via a session flag or timestamp", "Route reads directly to the Primary database for a brief window after a write, bypassing the replica"],
 ["Tell the users to clear their browser cache"]),

("DB_ARCHITECTURE_AND_HA", "explain", "hard", "concept", ["Replication", "SBR vs RBR"],
 "In database replication, what is 'Row-Based Replication' (RBR) versus 'Statement-Based Replication' (SBR), and why is SBR considered dangerous for certain queries?",
 "SBR replicates the exact SQL string (e.g., `UPDATE users SET last_login = NOW()`). RBR replicates the actual binary changed data for specific rows. SBR is dangerous for non-deterministic functions (like `NOW()`, `RAND()`, or `UUID()`); if the replica executes the SQL string slightly later, it will generate a different timestamp/UUID, silently corrupting and permanently diverging the replica's data.",
 ["Statement-Based (SBR): Replicates the exact SQL query string", "Row-Based (RBR): Replicates the actual binary data changes for the rows", "SBR is dangerous for non-deterministic functions (`NOW()`, `RAND()`); it will generate divergent data on the replica"],
 ["SBR replicates the database schema, RBR replicates the rows"]),

("DB_ARCHITECTURE_AND_HA", "debug", "medium", "debugging", ["Redis", "Eviction Policies"],
 "A Redis cache with a 2GB limit is constantly evicting recently added, important keys. Cache misses are skyrocketing. The eviction policy is `allkeys-random`. What policy should you configure to optimize hit rates?",
 "Change the policy to `allkeys-lru` (Least Recently Used) or `allkeys-lfu` (Least Frequently Used). `allkeys-random` blindly deletes keys regardless of how often they are accessed, destroying the hit rate. LRU ensures that only the oldest, 'coldest' data is purged when memory is full, preserving the frequently accessed 'hot' data.",
 ["`allkeys-random` blindly deletes keys, destroying cache hit rates for hot data", "Fix: Configure `allkeys-lru` (Least Recently Used) or `allkeys-lfu`", "Ensures only cold, unused data is evicted to make room for new keys"],
 ["Increase the 2GB limit to 200GB"]),

("DB_ARCHITECTURE_AND_HA", "implement", "hard", "implementation", ["Multi-Master", "Conflict Resolution"],
 "In a globally distributed multi-master database (like DynamoDB/Cassandra), two users in different continents update the exact same record simultaneously. How do these databases resolve conflicting writes without distributed locks?",
 "They typically use 'Last Write Wins' (LWW) resolution based on timestamps, or vector clocks/CRDTs (Conflict-Free Replicated Data Types). With LWW, the database compares the timestamp attached to each mutation by the client or coordinator node; the write with the highest timestamp simply overwrites the older one across all nodes, guaranteeing eventual consistency without synchronous locking.",
 ["Cannot use synchronous distributed locks over WAN due to massive latency", "Uses 'Last Write Wins' (LWW) based on timestamps attached to the mutations", "Alternatively uses Vector Clocks or CRDTs for deterministic, lock-free conflict resolution"],
 ["The database crashes and asks the admin to resolve it manually"]),

("DB_ARCHITECTURE_AND_HA", "scenario", "easy", "scenario", ["Backups", "Operations"],
 "Your automated `pg_dump` runs nightly, reporting 0 errors. The DB crashes, and you discover the backups are completely useless and cannot be restored. What critical database operations procedure did you neglect?",
 "You failed to perform routine 'Restore Testing' (Backup Validation). Taking a backup is only half the process; you must systematically and routinely execute test restores onto an isolated staging server to guarantee the backup files are not corrupt, encryption keys are available, and the RTO can actually be met in an emergency.",
 ["Failed to perform routine Restore Testing (Backup Validation)", "Backups are useless if they cannot be successfully restored", "Must routinely execute test restores to a staging server to verify integrity and RTO"],
 ["You forgot to compress the backup file"]),

("DB_ARCHITECTURE_AND_HA", "tradeoff", "medium", "tradeoff", ["NoSQL", "Data Modeling"],
 "When designing a NoSQL schema for a one-to-many relationship (Blog Post and Comments), what is the tradeoff of embedding comments directly inside the Post document versus referencing them in a separate collection?",
 "Embedding comments allows the application to retrieve all data in a single, extremely fast read operation (no JOINs). Tradeoff: The 'Unbounded Array' problem. If a post gets millions of comments, the single document will hit the database's physical size limit (e.g., MongoDB's 16MB limit) and severely degrade write performance. Referencing avoids size limits but requires multiple queries.",
 ["Embedding: Extremely fast single-read operations (no JOINs)", "Embedding Tradeoff: The Unbounded Array problem. Massive arrays hit document size limits (e.g., 16MB) and degrade writes", "Referencing Tradeoff: Safely avoids size limits but requires multiple queries/application-level joins"],
 ["Embedding makes the database look messy on the screen"])
]
