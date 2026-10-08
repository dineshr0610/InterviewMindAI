"""Batch 26 Part 3 question content (Database Developer). Targeted Gap Generation."""

ROLE = "Database Developer"

BUCKET_KEYS = {
    "DB_OPERATIONS": ("Database Operations", "Migrations & Recovery", "Databases", ["Backend Developer", "Site Reliability Engineer", "Data Engineer"]),
}

Q = [
# ---------------- DB_OPERATIONS ----------------
("DB_OPERATIONS", "scenario", "medium", "scenario", ["Zero-Downtime Migrations"],
 "You need to perform an online schema migration to add a column with a default value to a 500GB PostgreSQL table. If you simply run `ALTER TABLE ADD COLUMN default 'X'`, the entire application goes down for an hour. Why, and how do you do this with zero downtime?",
 "In older PostgreSQL versions, adding a column with a default value forces a full table rewrite, acquiring an `AccessExclusiveLock` that completely blocks all reads and writes. To achieve zero downtime, you must add the column *without* a default (an instant metadata-only operation), update the application code to write the default on new inserts, and then run a concurrent background script to backfill the existing rows in small batches.",
 ["Adding a default value forces a full table rewrite and acquires an exclusive lock, blocking all traffic", "Fix: Add the column WITHOUT a default (instant metadata operation)", "Update the app to write the default, then backfill existing rows in small background batches"],
 ["You must unplug the router before running the ALTER command"]),

("DB_OPERATIONS", "explain", "hard", "concept", ["Blue-Green Deployments"],
 "Explain the 'Blue-Green' deployment pattern specifically for databases. Why is it exponentially harder than Blue-Green deployments for stateless application servers?",
 "Database Blue-Green involves standing up a clone of the DB (Green), applying schema changes, and swapping traffic from Blue to Green. It is exponentially harder because databases are inherently stateful. While traffic is routed to Green, any new data written to Blue during the transition window must be bi-directionally synchronized back to Green, otherwise massive data loss occurs. Resolving synchronization conflicts during this swap is incredibly complex.",
 ["Database Blue-Green requires bi-directional synchronization of state", "Databases are stateful; stateless apps can just be destroyed and recreated", "Extremely complex to guarantee zero data loss and resolve conflicts during the traffic swap"],
 ["Blue-Green databases use energy-efficient green hard drives"]),

("DB_OPERATIONS", "tradeoff", "medium", "tradeoff", ["Connection Pooling"],
 "What is the tradeoff of relying on Connection Pooling at the application level (e.g., HikariCP) versus at the database infrastructure level (e.g., PgBouncer)?",
 "Application-level pooling is simple but scales poorly across microservices; if 100 app pods each have a pool of 20, you instantly exhaust a database limit of 1000 connections. Infrastructure-level pooling (PgBouncer) multiplexes thousands of incoming application connections onto a tiny number of actual backend database connections, saving DB RAM and CPU, but it introduces a central point of failure and adds network hop latency.",
 ["App-level: Simple, but scales poorly and exhausts DB connections with many pods", "Infrastructure-level (PgBouncer): Multiplexes thousands of connections to save DB resources", "Infrastructure tradeoff: Introduces a central point of failure and extra network latency"],
 ["PgBouncer literally bounces the data packets off a satellite"]),

("DB_OPERATIONS", "debug", "hard", "debugging", ["Transactions"],
 "During a major e-commerce sale, the database CPU spikes to 100%, but query volume is normal. You investigate and find massive numbers of `Idle in Transaction` connections. What application-level bug causes this, and why does it destroy database performance?",
 "The application is opening a transaction (`BEGIN`), executing a query, and then performing a slow external API call (or crashing) without ever calling `COMMIT` or `ROLLBACK` before returning the connection to the pool. This destroys performance because it forces the database to hold open Row Locks indefinitely and completely halts MVCC garbage collection (Vacuuming), causing massive table bloat and CPU thrashing.",
 ["The application opens a transaction but fails to COMMIT/ROLLBACK (e.g., blocked on an external API)", "Holds Row Locks indefinitely, blocking other queries", "Halts MVCC Vacuuming (Garbage Collection), causing massive table bloat and CPU thrashing"],
 ["The database is taking a mandated lunch break"]),

("DB_OPERATIONS", "fundamentals", "easy", "concept", ["Vacuuming"],
 "What is Database Vacuuming (or Garbage Collection in MVCC databases), and why is it operationally critical?",
 "In Multi-Version Concurrency Control (MVCC) databases (like PostgreSQL), an `UPDATE` or `DELETE` does not physically remove the old data; it merely marks the row as invisible. Vacuuming is the background operational process that physically scans for and reclaims that dead disk space. If it fails to run, the database suffers severe 'bloat', slowing down all sequential scans and eventually completely filling the disk.",
 ["`UPDATE`/`DELETE` in MVCC does not delete data, only marks it invisible", "Vacuuming is the background process that physically reclaims the dead disk space", "Critical to prevent severe table 'bloat' and degraded scan performance"],
 ["Vacuuming sucks the dust out of the physical server chassis"]),

("DB_OPERATIONS", "scenario", "medium", "scenario", ["Migrations"],
 "You need to migrate a massive, live database from an on-premise data center to AWS RDS with absolutely zero downtime. How do you architect this migration?",
 "You must use continuous logical replication or a tool like AWS Database Migration Service (DMS). First, you take a snapshot of the on-prem DB and restore it to RDS. Then, you configure DMS to tail the on-prem Write-Ahead Log (WAL) and continuously stream all subsequent changes to RDS. Once replication lag hits zero, you briefly pause application traffic, cut the DNS over to RDS, and resume traffic.",
 ["Use continuous logical replication (e.g., AWS DMS)", "Restore a snapshot, then continuously tail and stream the WAL to catch up", "Wait for zero replication lag, pause traffic, flip DNS, and resume"],
 ["Burn the data to Blu-Ray discs and mail them to Amazon"]),

("DB_OPERATIONS", "implement", "medium", "implementation", ["Disaster Recovery"],
 "You are designing an automated backup strategy. You currently take a full backup every Sunday at 2 AM. If a catastrophic failure occurs on Thursday at 3 PM, you will lose 4.5 days of data. How do you modify the architecture to achieve a Recovery Point Objective (RPO) of 5 minutes?",
 "You must implement continuous WAL / Transaction Log archiving. You configure the database to push every completed WAL segment (or stream them continuously) to secure object storage (like S3) every 5 minutes. During a catastrophic recovery, you restore Sunday's full backup and then sequentially replay all the archived WAL files up to the exact point of failure.",
 ["Implement continuous WAL / Transaction Log archiving to external storage (S3)", "Archive logs continuously or every 5 minutes to meet the RPO", "Restore the full backup, then replay the archived WALs up to the point of failure"],
 ["Take a full 10TB backup every 5 minutes"]),

("DB_OPERATIONS", "tradeoff", "hard", "tradeoff", ["Storage Architecture"],
 "What are the tradeoffs of using a 'Shared-Nothing' database architecture versus a 'Shared-Disk' architecture (like AWS Aurora)?",
 "Shared-Nothing (standard PostgreSQL clusters) scales horizontally but requires heavy network bandwidth because every replica must independently execute the WAL to update its own local disks. Shared-Disk (Aurora) centralizes the storage layer across the network; compute nodes only scale memory/CPU, and read replicas don't execute WAL because they read from the same physical network volume. The tradeoff is extreme vendor lock-in and potential storage-layer I/O bottlenecks.",
 ["Shared-Nothing: Independent disks, requires replicas to execute WAL (heavy network/CPU cost)", "Shared-Disk (Aurora): Centralized storage, replicas don't execute WAL (reads from shared volume)", "Shared-Disk tradeoff: Extreme vendor lock-in and centralized storage-layer I/O bottlenecks"],
 ["Shared-Disk means sharing floppy disks with the DevOps team"]),

("DB_OPERATIONS", "debug", "medium", "debugging", ["PITR Failures"],
 "A developer accidentally drops a critical table in production at 2:00 PM. You initiate a Point-In-Time Recovery (PITR) to restore the database to 1:59 PM. However, the recovery fails with an error stating 'WAL file sequence broken/missing'. What operational mistake caused this?",
 "The automated process responsible for archiving the Write-Ahead Logs to external storage (e.g., S3) silently failed days ago, or an aggressive cleanup script deleted the logs prematurely. PITR strictly requires an absolutely unbroken, contiguous chain of WAL files from the base backup up to the target timestamp. Missing even a single file in the sequence makes further recovery mathematically impossible.",
 ["The WAL archiving process silently failed, or logs were deleted prematurely", "PITR strictly requires an unbroken, contiguous chain of WAL files", "Missing a single WAL file breaks the chain and halts the recovery process"],
 ["The database refused to go back in time due to the grandfather paradox"]),

("DB_OPERATIONS", "explain", "medium", "concept", ["Connection Thrashing"],
 "Explain the concept of 'Connection Thrashing' (or Connection Storms) in database operations, and how it differs from simple high query traffic.",
 "Connection thrashing occurs when an application rapidly opens and closes database connections at a massive rate, rather than reusing them from a pool. Because establishing a TCP connection and authenticating at the database layer is highly CPU-intensive, a connection storm can max out the database CPU purely on network handshake overhead, completely starving actual query execution. High query traffic executes queries; thrashing wastes CPU on handshakes.",
 ["Occurs when applications rapidly open and close connections instead of pooling", "TCP handshake and authentication overhead is highly CPU-intensive", "Maxes out database CPU entirely on connection overhead, starving actual query execution"],
 ["It is when the database administrator violently shakes the server cables"]),

("DB_OPERATIONS", "scenario", "hard", "scenario", ["Network Partitions"],
 "You have a globally distributed database. Due to a severe routing misconfiguration, the network is partitioned: Region A can communicate with Region B, Region B can communicate with Region C, but Region A cannot communicate directly with Region C. How does this 'Asymmetric Network Partition' affect cluster consensus protocols like Raft?",
 "An asymmetric partition severely destabilizes the cluster. Region A and C might both think they are isolated and trigger leader elections. Because Region B can see both, it receives conflicting election requests. Depending on the exact Raft implementation, this can lead to an endless election loop (dueling candidates) where no leader is ever successfully elected, bringing the entire database cluster down.",
 ["Region A and C both think they are isolated and trigger leader elections", "Region B receives conflicting requests from both sides", "Can cause an endless election loop (dueling candidates), preventing the cluster from functioning"],
 ["The database automatically creates a VPN tunnel to fix it"]),

("DB_OPERATIONS", "fundamentals", "easy", "concept", ["Indexing"],
 "What is the operational purpose of an 'Index Build' running concurrently (e.g., `CREATE INDEX CONCURRENTLY` in Postgres) versus a standard index build?",
 "A standard index build acquires an exclusive table lock, completely blocking all `INSERT`, `UPDATE`, and `DELETE` operations on that table until the index is finished, causing massive application downtime. A concurrent index build acquires a much weaker lock, allowing normal application write traffic to continue uninterrupted. The tradeoff is that the concurrent build takes significantly longer and consumes more CPU/Disk I/O.",
 ["Standard builds acquire exclusive locks, completely blocking all application writes", "Concurrent builds acquire weak locks, allowing normal writes to continue without downtime", "Concurrent tradeoff: Takes significantly longer and consumes more resources to build"],
 ["Concurrent indexes are built by two administrators typing at the same time"]),

("DB_OPERATIONS", "tradeoff", "medium", "tradeoff", ["Triggers"],
 "What is the operational tradeoff of using Database Triggers for business logic (e.g., automatically updating an 'updated_at' timestamp or auditing changes)?",
 "Triggers perfectly guarantee data integrity at the lowest level regardless of which application connects to the database. The major operational tradeoff is hidden complexity: business logic is buried in the database, making it extremely difficult to version control, test, debug, and scale. Furthermore, heavy triggers severely degrade write throughput because they execute synchronously within the transaction.",
 ["Guarantees data integrity regardless of the connecting application", "Tradeoff: Buries business logic in the DB, making it hard to version control and debug", "Tradeoff: Executes synchronously, severely degrading write throughput"],
 ["Triggers are physical buttons on the server motherboard"]),

("DB_OPERATIONS", "implement", "hard", "implementation", ["Capacity Planning"],
 "You are operating a database cluster that is nearing its maximum IOPS (Input/Output Operations Per Second) capacity. Query optimization is already perfect. Without changing the database engine or sharding, what three infrastructure-level operational changes can immediately reduce disk IOPS?",
 "1. Increase the database RAM to allow the engine to cache more of the working set in memory (Buffer Pool), drastically reducing disk reads. 2. Batch application writes together to reduce the frequency of WAL syncs to disk. 3. Delay or disable non-critical background operational tasks during peak hours, such as heavy Vacuuming or backup snapshotting.",
 ["Increase RAM to cache more working set in memory (reduces read IOPS)", "Batch application writes together (reduces WAL sync frequency/write IOPS)", "Delay background tasks like Vacuuming or snapshotting to off-peak hours"],
 ["Turn the server off and on again rapidly"]),

("DB_OPERATIONS", "debug", "medium", "debugging", ["Query Planner"],
 "A new application version is deployed that introduces a highly optimized `SELECT` query utilizing a perfectly designed composite index. However, in production, the database completely ignores the index and performs a full table scan, causing a severe outage. The query works perfectly on the staging database. What operational maintenance step was missed?",
 "The database statistics are outdated. The query planner relies on statistical histograms of the data distribution to estimate whether an index scan is cheaper than a full table scan. Because the production data was significantly updated but the statistics were not refreshed (e.g., via the `ANALYZE` command), the planner incorrectly assumed a full table scan would be cheaper. Running `ANALYZE` forces the planner to use the index.",
 ["Database statistics/histograms are outdated", "The query planner uses statistics to estimate query cost", "If statistics are stale, it may incorrectly choose a full table scan over an index. Fix: Run `ANALYZE`"],
 ["The index was written in the wrong font"])
]
