"""Batch 26 question content (Database Developer). Targeted Gap Generation."""

ROLE = "Database Developer"

BUCKET_KEYS = {
    "DB_REPLICATION": ("Database Replication", "Failover & Consistency", "Databases", ["Backend Developer", "Site Reliability Engineer", "Data Engineer"]),
}

Q = [
# ---------------- DB_REPLICATION ----------------
("DB_REPLICATION", "scenario", "medium", "scenario", ["Consistency"],
 "An application writes a new user record to the primary database and instantly redirects the user to their profile page, which reads from a read replica. The user occasionally sees a 'Profile Not Found' error. What is the fundamental cause of this, and how can the architecture guarantee 'Read-After-Write' consistency?",
 "This is caused by asynchronous replication lag; the read replica has not yet received and applied the write from the primary database before the read request arrives. To guarantee Read-After-Write consistency, the application can route the very first read immediately following a write directly to the primary node, or the database can be configured to use synchronous replication (which severely degrades write performance).",
 ["Caused by asynchronous replication lag", "Route the first read after a write to the primary node", "Alternatively, use synchronous replication to guarantee the replica is up-to-date"],
 ["The database deleted the user because they didn't have a profile picture"]),

("DB_REPLICATION", "tradeoff", "hard", "tradeoff", ["Replication Types"],
 "What is the operational tradeoff between fully synchronous replication and asynchronous replication in a primary-replica database architecture?",
 "Synchronous replication guarantees zero data loss (RPO=0) because a commit must be acknowledged by the replica before succeeding, but it severely degrades write latency and availability (if the replica goes offline, all writes to the primary block). Asynchronous replication provides fast, highly available writes because the primary commits immediately, but it risks data loss if the primary crashes before the Write-Ahead Log (WAL) is shipped to the replica.",
 ["Synchronous: Zero data loss, but degrades latency and blocks writes if the replica is down", "Asynchronous: Fast, highly available writes", "Asynchronous Tradeoff: Risks data loss if the primary crashes before logs are shipped"],
 ["Synchronous uses TCP, Asynchronous uses UDP"]),

("DB_REPLICATION", "debug", "hard", "debugging", ["WAL & Storage"],
 "A PostgreSQL database has a replication slot configured for a read replica. The replica goes completely offline and stays down for 3 days over a long weekend. On Monday, the primary database crashes due to `No space left on device`. Why did the offline replica cause the primary to run out of disk space?",
 "A logical or physical replication slot forces the primary database to indefinitely retain all Write-Ahead Logs (WAL files) until the replica explicitly acknowledges it has consumed them. Because the replica was offline for 3 days, the primary was unable to rotate or delete any WAL files, accumulating 3 days of transaction logs until it entirely exhausted the primary server's physical disk space.",
 ["Replication slots force the primary to retain all WAL files until the replica consumes them", "Because the replica was offline, the primary could not delete old WAL files", "Accumulated WAL files exhausted the physical disk space"],
 ["The replica uploaded a massive virus to the primary"]),

("DB_REPLICATION", "explain", "medium", "concept", ["High Availability"],
 "Explain the concept of 'Split-Brain' in a high-availability database cluster. Why is it dangerous?",
 "Split-Brain occurs when a severe network partition causes a cluster to split into two isolated halves. Both halves mistakenly assume the other side is dead and independently elect a primary node. It is incredibly dangerous because both primaries will independently accept and commit conflicting writes from applications. This permanently corrupts the data state, making reconciliation nearly impossible without manual intervention and massive data loss.",
 ["Occurs during a network partition where two isolated halves both elect a primary", "Both primaries independently accept conflicting writes", "Causes permanent data corruption and requires manual, lossy reconciliation"],
 ["It happens when the database becomes too intelligent"]),

("DB_REPLICATION", "scenario", "hard", "scenario", ["Failover"],
 "An automated failover orchestrator detects that the primary database is down and successfully promotes a replica to the new primary role. However, two minutes later, data corruption occurs because the old primary comes back online and some application servers are still sending writes to it. What crucial failover step was missed?",
 "The orchestrator failed to perform 'Fencing' (e.g., STONITH - Shoot The Other Node In The Head). Before promoting any new primary, the old primary must be aggressively isolated, physically powered off, or blocked at the network level to absolutely guarantee it can never accept another write, preventing a Split-Brain scenario when it inevitably recovers.",
 ["Failed to perform 'Fencing' (STONITH)", "The old primary must be aggressively isolated, powered off, or network-blocked", "Guarantees the old primary can never accept writes when it recovers"],
 ["The orchestrator forgot to send an email to the DBA"]),

("DB_REPLICATION", "fundamentals", "easy", "concept", ["Database Internals"],
 "What is a Database Write-Ahead Log (WAL), and what dual purpose does it serve for crash recovery and replication?",
 "The WAL is an append-only transaction log where all database modifications are recorded sequentially *before* they are flushed to the actual data files on disk. For crash recovery, it allows the database to replay uncommitted operations upon restarting after a power failure. For replication, the WAL serves as the exact binary stream shipped to read replicas to keep their state perfectly synchronized with the primary.",
 ["An append-only log where modifications are recorded *before* being written to data files", "Crash recovery: Allows the DB to replay uncommitted operations after a crash", "Replication: Shipped to read replicas to synchronize state"],
 ["WAL stands for Wide Area Locator"]),

("DB_REPLICATION", "implement", "medium", "implementation", ["Consistency"],
 "You are designing a multi-region database architecture. You want read replicas in Europe to serve European users, but the primary is in the US. The business requires that any European user reading data must NEVER see data go backwards in time (Monotonic Reads). How do you guarantee this despite replication lag?",
 "You guarantee Monotonic Reads by pinning the user's session and tracking a 'High Watermark' or Log Sequence Number (LSN) of their last read/write. When the user makes a subsequent read request to the European replica, the replica checks if its current applied LSN is greater than or equal to the user's watermark. If not, the replica must intentionally block and wait until it catches up before serving the read.",
 ["Track a 'High Watermark' or Log Sequence Number (LSN) in the user's session", "When reading, compare the replica's current LSN to the user's watermark", "If the replica is behind, block the read until the replica catches up to the LSN"],
 ["Send a chronometer in the HTTP header"]),

("DB_REPLICATION", "debug", "medium", "debugging", ["Replication Bottlenecks"],
 "During a massive traffic spike, your read replicas fall 5 minutes behind the primary. CPU and Memory on the replicas look completely fine. What specific characteristic of relational database replication makes it bottlenecked on a single CPU core, causing this lag?",
 "Traditional physical replication application is inherently single-threaded. Because the Write-Ahead Log is a strict, sequential serialization of transactions, the replica must replay them in the exact same serial order to guarantee ACID consistency and prevent locking anomalies. This prevents the replica from utilizing multiple CPU cores to catch up, bottlenecking replication on single-thread performance.",
 ["Traditional physical replication replay is inherently single-threaded", "WAL transactions must be replayed in strict serial order to guarantee consistency", "Prevents the replica from utilizing multiple CPU cores, causing a bottleneck during high write throughput"],
 ["The CPU is saving power because it thinks it's a replica"]),

("DB_REPLICATION", "scenario", "hard", "scenario", ["Logical Replication"],
 "You are using PostgreSQL Logical Replication to stream changes from a transactional database to a data warehouse. You drop a column on the primary database, but the replication immediately breaks and stops streaming. Why did logical replication break, and how does it differ from physical replication in this scenario?",
 "Logical replication decodes the WAL into row-level DML statements (INSERT/UPDATE) based on the exact schema structure. If the schema mismatches (e.g., dropping a column), the DML statement fails on the subscriber. Physical replication copies raw binary disk blocks completely identically; it does not care about schemas, meaning DDL changes like dropping a column are seamlessly replicated block-by-block without breaking.",
 ["Logical replication decodes WAL into schema-dependent DML (INSERT/UPDATE)", "A schema mismatch (dropped column) instantly breaks the DML application on the subscriber", "Physical replication copies raw binary disk blocks and is immune to schema mismatches"],
 ["Logical replication is offended by dropped columns"]),

("DB_REPLICATION", "tradeoff", "medium", "tradeoff", ["Active-Active"],
 "What are the tradeoffs of using a 'Multi-Primary' (Active-Active) database replication architecture across two geographically distant data centers?",
 "Active-Active allows writes in both regions, providing incredibly fast local write latency and seamless disaster recovery. The severe tradeoff is massive complexity in conflict resolution. If two users update the exact same row simultaneously in different data centers, the system must employ complex logic (like CRDTs, Last-Write-Wins timestamps, or manual application intervention) to resolve the replication collision.",
 ["Active-Active provides fast local write latency and seamless disaster recovery", "Tradeoff: Massive complexity in resolving write conflicts", "Requires complex logic (CRDTs, Last-Write-Wins) to handle simultaneous edits to the same row"],
 ["Active-Active requires both data centers to be in the same timezone"]),

("DB_REPLICATION", "explain", "easy", "concept", ["Disaster Recovery"],
 "In the context of database disaster recovery, what is the difference between RTO (Recovery Time Objective) and RPO (Recovery Point Objective)?",
 "RPO (Recovery Point Objective) is the maximum acceptable amount of data loss, measured in time (e.g., 'we can afford to lose the last 15 minutes of writes'). RTO (Recovery Time Objective) is the maximum acceptable amount of downtime before the database is brought back online and is fully functional.",
 ["RPO: Maximum acceptable amount of data loss (measured in time)", "RTO: Maximum acceptable amount of downtime before the system is restored", "RPO dictates backup frequency; RTO dictates recovery automation"],
 ["RTO stands for Return To Office"]),

("DB_REPLICATION", "scenario", "medium", "scenario", ["Replication Lag"],
 "Your monitoring system alerts you that a MySQL Read Replica has a 'Replication Lag' of 600 seconds. However, there has been very little write traffic on the primary today. You investigate and find an analyst running a massive `SELECT COUNT(*)` query on the replica that takes 15 minutes. Why does a heavy read query on the replica cause replication lag?",
 "In many database engines (like MySQL), long-running read queries acquire shared metadata locks or prevent garbage collection (MVCC snapshot isolation). To prevent modifying data or schema structures that the long query is currently reading, the single-threaded replication SQL thread on the replica is blocked from applying new WAL changes until the read query finishes.",
 ["Long-running read queries acquire shared locks or hold open MVCC snapshots", "The replication thread is blocked from applying conflicting WAL changes to prevent corrupting the read", "Replication is stalled until the massive read query completes"],
 ["The replica is too tired from counting to apply updates"]),

("DB_REPLICATION", "debug", "hard", "debugging", ["Connection Management"],
 "An application relies on PgBouncer for connection pooling to a PostgreSQL primary database. During a managed failover, the primary IP is remapped to the new replica via DNS. However, the application completely halts, throwing thousands of `ReadOnlySqlException` errors, despite the DNS updating instantly. Why?",
 "PgBouncer and the application maintain long-lived, persistent TCP connections to the original IP address. DNS TTL changes only affect *newly established* connections. The existing connection pool remains physically connected to the old primary (which has now been demoted to a read-only replica). The connection pool must be explicitly flushed, restarted, or sent a reload signal during the failover orchestration.",
 ["Connection pools maintain long-lived, persistent TCP connections", "DNS updates only route *new* connections; existing connections stay bound to the old primary", "The pool must be explicitly flushed/recycled to force reconnections to the new primary"],
 ["DNS is inherently incompatible with PostgreSQL"]),

("DB_REPLICATION", "implement", "hard", "implementation", ["Failover Routing"],
 "How do you architect a database failover mechanism to be completely transparent to the application layers, so that application instances do not need to be restarted or reconfigured when a new primary is elected?",
 "You introduce a highly available, topology-aware proxy layer (like HAProxy, ProxySQL, or PgBouncer with a VIP) between the application and the database cluster. The application strictly connects to a static VIP on the proxy. The proxy dynamically polls the database cluster state, identifies the current elected primary, and seamlessly routes all write traffic to the new node at the network layer during a failover.",
 ["Introduce a topology-aware database proxy layer (HAProxy, ProxySQL)", "The application connects to a static Virtual IP (VIP) on the proxy", "The proxy dynamically monitors cluster state and seamlessly reroutes traffic to the new primary"],
 ["Send an SMS to all applications telling them the new IP address"]),

("DB_REPLICATION", "fundamentals", "medium", "concept", ["Consensus"],
 "Explain the concept of 'Quorum' in a distributed database cluster (e.g., a 5-node Cassandra or CockroachDB cluster). Why is a quorum size of 3 preferred over 2?",
 "A Quorum is the strict minimum number of nodes that must acknowledge a read or write operation for it to be considered successful (usually calculated as `N/2 + 1`). In a 5-node cluster, a quorum of 3 is preferred because it mathematically guarantees strict overlap between reads and writes, and crucially prevents Split-Brain. If the network splits, you can never have two competing partitions that both achieve 3 votes. A quorum of 2 would allow a 2-2 tie.",
 ["The minimum number of nodes that must acknowledge an operation (usually `N/2 + 1`)", "Guarantees overlap between read and write operations for consistency", "In a 5-node cluster, a quorum of 3 mathematically prevents a Split-Brain tie"],
 ["Quorum is a type of SQL join"]),

("DB_REPLICATION", "tradeoff", "medium", "tradeoff", ["Backup Strategy"],
 "When designing a disaster recovery strategy, what is the operational tradeoff of relying exclusively on asynchronous cross-region Read Replicas versus relying on daily EBS Volume Snapshots?",
 "Cross-region replicas provide near-zero RPO and RTO because the data is instantly available in the other region. However, if a malicious user executes `DROP TABLE`, that destructive command is instantly replicated, completely destroying the 'backup'. Snapshots are much slower to restore (high RTO) and lose up to 24 hours of data (high RPO), but they perfectly protect against accidental or malicious logical data corruption.",
 ["Replicas: Near-zero RPO/RTO, but instantly replicate destructive commands (`DROP TABLE`)", "Snapshots: High RTO/RPO (slow to restore, data loss), but protect against logical data destruction", "Replicas provide availability; Snapshots provide true data preservation"],
 ["Snapshots take physical polaroids of the hard drive"]),

("DB_REPLICATION", "scenario", "hard", "scenario", ["Synchronous Replication"],
 "You use a database that supports 'Synchronous Replication' to a single replica to guarantee zero data loss. The network link between the primary and the replica briefly drops for 10 seconds. What exactly happens to the application trying to write to the primary during those 10 seconds?",
 "The application writes will completely hang, block, or timeout. In strict synchronous replication, the primary database *must* wait for the replica to acknowledge the receipt of the WAL before it is allowed to return a successful commit to the client. Because the replica is unreachable, the primary refuses to acknowledge commits, actively sacrificing Availability to maintain strict Consistency.",
 ["Application writes will completely hang, block, or timeout", "The primary *must* wait for the replica's acknowledgment before committing", "Sacrifices Availability to maintain strict Consistency during network failures"],
 ["The database automatically converts to a NoSQL database"]),

("DB_REPLICATION", "debug", "medium", "debugging", ["Consensus Failures"],
 "A database cluster uses a Leader Election protocol (like Raft or Paxos). The cluster has exactly 2 nodes (Node A and Node B) in different availability zones. Node B goes offline. Node A is perfectly healthy but completely refuses to accept any writes, paralyzing the application. Why?",
 "Consensus protocols require a strict majority quorum (`N/2 + 1`) to elect a leader and accept writes. With exactly 2 nodes, a majority is 2. When Node B dies, Node A only has 1 vote, failing to achieve the necessary quorum. Distributed consensus clusters must always be deployed with an odd number of nodes (minimum 3) so that the surviving majority can continue operating if one node fails.",
 ["Consensus protocols require a strict majority quorum (`N/2 + 1`)", "With 2 nodes, the majority is 2. If one fails, the survivor has 1 vote and loses quorum", "Clusters must be deployed with an odd number of nodes (minimum 3) to survive single-node failures"],
 ["Node A is mourning the loss of Node B"]),

("DB_REPLICATION", "explain", "easy", "concept", ["Eventual Consistency"],
 "What does it mean when a distributed database is described as 'Eventually Consistent'?",
 "It means that if no new updates are made to a specific piece of data, eventually all reads to that data on any replica in the cluster will return the exact same, latest value. However, there is a known window of time immediately after a write where reading from different replicas might return older, stale versions of the data.",
 ["If no new updates occur, all replicas will eventually hold the same latest value", "There is a window of time where reads from different replicas may return stale data", "Prioritizes high availability and low latency over strict immediate consistency"],
 ["It means the database will eventually delete all your data"]),

("DB_REPLICATION", "implement", "medium", "implementation", ["PITR"],
 "You need to perform a Point-In-Time Recovery (PITR) to restore a production database to exactly 10:45 AM today because a developer accidentally deleted a critical table at 10:46 AM. What two core operational components do you need to execute this recovery?",
 "You need the most recent Full Database Backup (e.g., taken at 2:00 AM) AND an unbroken, sequential archive of all Write-Ahead Logs (WAL files) generated between 2:00 AM and 10:45 AM. You restore the physical backup, then apply the WAL archive, instructing the database recovery process to halt replay at precisely 10:45:00.",
 ["The most recent Full Database Backup", "An unbroken archive of all Write-Ahead Logs (WAL) generated since the backup", "Restore the backup, then replay the WAL files, halting exactly at the target timestamp"],
 ["You need a time machine and a screwdriver"])
]
