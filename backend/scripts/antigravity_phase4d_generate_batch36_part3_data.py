"""Batch 36 Part 3 question content (Database Developer). Targeted Gap Generation."""

ROLE = "Database Developer"

BUCKET_KEYS = {
    "TRANSACTIONS_AND_OPERATIONS": ("Transactions & Operations", "Database Internals", "Database", ["Database Developer", "Backend Developer"]),
}

Q = [
# ---------------- TRANSACTIONS_AND_OPERATIONS ----------------
("TRANSACTIONS_AND_OPERATIONS", "debug", "hard", "debugging", ["Locking", "Batch Processing"],
 "You run a batch job updating 50M rows. During the job, unrelated read queries randomly time out. DB CPU/memory are normal. What fundamental transaction configuration caused the long job to block other queries, and how do you fix it?",
 "The batch job is running inside a single massive transaction. It is consuming all available row-level locks, forcing the database engine to escalate to a full table or database lock (Lock Escalation), freezing other queries. Fix: Disable auto-commit and explicitly break the batch job into thousands of smaller, discrete transactions (`LIMIT 5000`), releasing locks frequently.",
 ["Running a massive update inside a single transaction exhausts available row locks", "Forces the DB engine to trigger 'Lock Escalation', acquiring a full table lock", "Fix: Break the batch job into thousands of smaller, discrete transactions to release locks frequently"],
 ["The database was encrypting the rows and forgot the password"]),

("TRANSACTIONS_AND_OPERATIONS", "tradeoff", "medium", "tradeoff", ["Normalization", "Schema Design"],
 "When designing a database schema, what is the specific performance tradeoff of adhering strictly to Third Normal Form (3NF) versus intentionally denormalizing the data?",
 "Third Normal Form (3NF) minimizes data redundancy and guarantees absolute data integrity (preventing update anomalies). The massive tradeoff is read performance: constructing a complete view of an entity requires multiple expensive, CPU-intensive `JOIN` operations. Denormalization intentionally duplicates data (e.g., storing customer name directly in the order table) to eliminate `JOIN`s and massively accelerate read throughput at the cost of complex, slower writes.",
 ["3NF minimizes redundancy and guarantees integrity, but requires expensive `JOIN`s for reads", "Denormalization intentionally duplicates data to eliminate `JOIN`s, massively accelerating read performance", "Tradeoff: Read speed (Denormalized) vs Write speed / Data Integrity (3NF)"],
 ["3NF stands for 3 Normal Friends who share a database"]),

("TRANSACTIONS_AND_OPERATIONS", "tradeoff", "hard", "tradeoff", ["Isolation Levels", "SERIALIZABLE"],
 "In relational databases, what is the exact tradeoff of setting Transaction Isolation Level to `SERIALIZABLE` versus `READ COMMITTED`?",
 "`SERIALIZABLE` provides the strictest consistency, mathematically guaranteeing concurrent transactions execute exactly as if run sequentially, eliminating dirty/non-repeatable/phantom reads. Tradeoff: Massive performance hit. It acquires heavy read/write locks (or uses optimistic control causing frequent aborts/rollbacks), leading to severe lock contention, deadlocks, and forcing app-level retries.",
 ["`SERIALIZABLE`: Strictest consistency, eliminating dirty, non-repeatable, and phantom reads", "Tradeoff: Severe performance degradation due to heavy read/write locking", "Tradeoff: Massive increase in lock contention, deadlocks, and forced transaction rollbacks/retries"],
 ["Serializable makes the database output in JSON format"]),

("TRANSACTIONS_AND_OPERATIONS", "scenario", "medium", "scenario", ["Deadlocks", "Concurrency"],
 "Transaction A locks Account 1 and tries to lock Account 2. Transaction B locks Account 2 and tries to lock Account 1. Both freeze infinitely. What database phenomenon is this, and how does the engine resolve it?",
 "This is a classic 'Deadlock'. The database engine runs a background Deadlock Detector process (using a wait-for graph). When it detects a cycle of dependencies where neither transaction can proceed, it arbitrarily selects one transaction as the 'victim', violently kills/rolls it back, and throws a Deadlock Exception, allowing the survivor to proceed.",
 ["This is a classic 'Deadlock' (a cyclical dependency of locks)", "The database engine's background Deadlock Detector identifies the cycle", "It arbitrarily selects one transaction as a 'victim', kills it, and rolls it back"],
 ["The database merges both transactions into one super-transaction"]),

("TRANSACTIONS_AND_OPERATIONS", "explain", "easy", "concept", ["ACID", "Isolation"],
 "In database engineering, what does 'ACID' stand for, and what specifically does the 'I' guarantee?",
 "ACID stands for Atomicity, Consistency, Isolation, Durability. The 'I' stands for Isolation. Isolation guarantees that concurrent transactions executing simultaneously do not interfere with each other; intermediate, uncommitted states of one transaction must remain completely invisible to other transactions until the commit is finalized.",
 ["Atomicity, Consistency, Isolation, Durability", "Isolation guarantees concurrent transactions do not interfere with each other", "Uncommitted, intermediate states of one transaction are invisible to others"],
 ["It stands for Acidic, meaning the database destroys old data quickly"]),

("TRANSACTIONS_AND_OPERATIONS", "debug", "medium", "debugging", ["Connection Pooling", "Architecture"],
 "You deploy a new microservice. Traffic is low, but the DB connection limit (`max_connections=100`) is instantly exhausted, crashing the DB. You see `new Connection()` called for every HTTP request. What architectural component is missing?",
 "You are missing a 'Connection Pool' (e.g., HikariCP, PgBouncer). Establishing a physical TCP connection to a database is extremely slow and memory-intensive. Creating a new connection per request quickly exhausts hard limits. A connection pool maintains a small, fixed number of permanent, multiplexed connections that are continuously reused by fast, short-lived HTTP requests.",
 ["Missing a 'Connection Pool' (e.g., PgBouncer, HikariCP)", "Establishing physical TCP database connections per request is extremely slow and exhausts limits", "Pools maintain a small set of permanent, multiplexed connections to be reused continuously"],
 ["The database needs a faster internet connection"]),

("TRANSACTIONS_AND_OPERATIONS", "implement", "hard", "implementation", ["Window Functions", "Analytics"],
 "You must calculate a running total (cumulative sum) of the `amount` column ordered by `transaction_date` for each individual `user_id`. How do you implement this in modern SQL without correlated subqueries or self-joins?",
 "Implement this using 'Window Functions'. The query uses `SUM(amount) OVER (PARTITION BY user_id ORDER BY transaction_date)`. This instructs the database engine to logically group rows by user, order them by date, and apply the aggregate sum cumulatively down the partition in a single, highly optimized pass.",
 ["Use 'Window Functions' (Analytic Functions)", "`SUM(amount) OVER (PARTITION BY user_id ORDER BY transaction_date)`", "Calculates cumulative aggregates across partitions in a single optimized pass without JOINs"],
 ["Download the data to Excel, calculate it there, and upload it back"]),

("TRANSACTIONS_AND_OPERATIONS", "tradeoff", "medium", "tradeoff", ["Locking", "Optimistic vs Pessimistic"],
 "When designing a concurrent booking system, what is the tradeoff of using 'Pessimistic Locking' (`SELECT FOR UPDATE`) versus 'Optimistic Locking' (using a `version` column)?",
 "Pessimistic locking acquires an exclusive physical lock on the row, preventing concurrent edits but severely bottlenecking throughput and causing deadlocks. Optimistic locking acquires no locks; it checks `WHERE version = old_version` during the `UPDATE`. If another transaction updated the row first, the update fails (0 rows affected), and the app must retry. Optimistic is vastly better for read-heavy workloads.",
 ["Pessimistic (`FOR UPDATE`): Exclusive physical locks. Prevents conflicts but bottlenecks throughput", "Optimistic (Version column): No locks. Relies on `WHERE version = X` during UPDATE", "Optimistic Tradeoff: Requires the application layer to explicitly handle retries if the update fails"],
 ["Pessimistic locking makes the database sad, Optimistic makes it happy"]),

("TRANSACTIONS_AND_OPERATIONS", "scenario", "hard", "scenario", ["MVCC", "Undo Logs"],
 "You manage an InnoDB database. An engineer opens a transaction, runs a `SELECT`, and goes to lunch, leaving the transaction idle for 2 hours. What internal database mechanism will eventually cause the DB to crash or run out of disk space?",
 "This causes 'Undo Log' (or MVCC) exhaustion. Because MySQL uses Multi-Version Concurrency Control to provide consistent reads, it must retain older versions of all rows modified by *other* transactions just in case the 2-hour-old transaction decides to read them. This prevents the DB from purging dead tuples, causing the undo tablespace to bloat massively until the disk fills.",
 ["Causes 'Undo Log' (MVCC) exhaustion and massive disk bloat", "The DB must retain old versions of all modified rows globally to provide a consistent read view for the idle transaction", "Prevents garbage collection (vacuuming) of dead tuples, filling the disk"],
 ["The database gets bored and decides to reboot itself"]),

("TRANSACTIONS_AND_OPERATIONS", "explain", "medium", "concept", ["Isolation Levels", "Phantom Reads"],
 "What is the 'Phantom Read' anomaly in database transaction isolation, and which isolation level is required to strictly prevent it?",
 "A Phantom Read occurs when Transaction A reads a set of rows (e.g., `WHERE status = 'active'`). Transaction B then `INSERT`s a new row matching that condition and commits. If Transaction A executes the exact same query again, a new 'phantom' row magically appears in the results. To strictly prevent this, use `SERIALIZABLE` isolation (which employs range/predicate locks).",
 ["Transaction A reads a range of rows. Transaction B `INSERT`s a new row into that range", "When Transaction A reads again, a new 'phantom' row magically appears", "Strictly prevented ONLY by the `SERIALIZABLE` isolation level (via range/predicate locks)"],
 ["It is when a database row is deleted but its ghost remains in the UI"]),

("TRANSACTIONS_AND_OPERATIONS", "debug", "medium", "debugging", ["DDL Locks", "TRUNCATE"],
 "A developer runs `TRUNCATE TABLE users;`. The command hangs indefinitely. They see someone else running a long `SELECT count(*) FROM users;`. Why does a simple read query block a `TRUNCATE` command?",
 "`TRUNCATE` is a DDL (Data Definition Language) command, not a DML command (like `DELETE`). It requires acquiring an exclusive 'Access Exclusive Lock' on the entire physical table structure. Because the `SELECT` query is actively holding a shared read lock on the table, the database prevents the `TRUNCATE` from acquiring the exclusive lock until the read finishes.",
 ["`TRUNCATE` is a DDL command that requires an 'Access Exclusive Lock' on the physical table", "The active `SELECT` query holds a shared read lock", "The DDL command is blocked indefinitely until all shared read locks are released"],
 ["The `TRUNCATE` command is waiting for the `SELECT` to tell it how many rows to delete"]),

("TRANSACTIONS_AND_OPERATIONS", "implement", "easy", "implementation", ["Upserts", "ON CONFLICT"],
 "You insert a new user. If a user with the same `email` (UNIQUE constraint) already exists, you want to simply update their `last_login` instead of failing with a constraint error. How do you implement this in modern SQL?",
 "Implement an 'Upsert' (Insert on Conflict). In PostgreSQL: `INSERT INTO users (email, last_login) VALUES (...) ON CONFLICT (email) DO UPDATE SET last_login = EXCLUDED.last_login;`. In MySQL: `INSERT ... ON DUPLICATE KEY UPDATE last_login = VALUES(last_login);`. This executes atomically at the engine level.",
 ["Implement an 'Upsert' natively in SQL", "PostgreSQL: `ON CONFLICT (col) DO UPDATE SET ...`", "MySQL: `ON DUPLICATE KEY UPDATE ...`"],
 ["First try to insert, and if it throws an error in Java, catch it and run an update query"]),

("TRANSACTIONS_AND_OPERATIONS", "tradeoff", "hard", "tradeoff", ["Primary Keys", "UUIDs vs Integers"],
 "What is the architectural tradeoff of using UUIDs (v4 random) versus Auto-Incrementing Integers as primary keys in a clustered relational database (like MySQL/InnoDB)?",
 "UUIDs are fantastic for distributed systems (generated independently by clients, trivial sharding). The massive tradeoff is DB performance: standard v4 UUIDs are completely random. Inserting them into a clustered B-Tree index causes massive 'page splits' and fragmentation, degrading `INSERT` performance severely compared to appending sequential Integers. (Fix: use sequential UUIDv7).",
 ["UUID Advantage: Independently generated by distributed clients, trivial sharding/merging", "Tradeoff: V4 UUIDs are completely random, not sequential", "Tradeoff: Causes massive B-Tree 'page splits' and fragmentation, severely degrading `INSERT` performance"],
 ["UUIDs are too long to fit on a standard computer monitor screen"]),

("TRANSACTIONS_AND_OPERATIONS", "scenario", "medium", "scenario", ["Indexes", "Bulk Updates"],
 "You run `UPDATE users SET status = 'migrated';` on 10 million rows. It takes hours. You notice the table has 15 different indexes. Why is the `UPDATE` so slow, and how do you optimize the migration?",
 "The `UPDATE` is slow because for every single row changed, the DB must synchronously update and rebalance all 15 B-Tree indexes. The standard optimization for massive bulk updates/inserts is to explicitly `DROP` (or disable) all non-essential indexes, perform the bulk `UPDATE` at maximum disk speed, and then `CREATE INDEX` to rebuild them all at once.",
 ["Every updated row forces the DB to synchronously update and rebalance 15 separate B-Trees", "Massively degrades write throughput", "Fix: `DROP` non-essential indexes, execute the bulk update, then `CREATE INDEX` to rebuild them efficiently"],
 ["The database is trying to email all 10 million users about the update"]),

("TRANSACTIONS_AND_OPERATIONS", "explain", "hard", "concept", ["PostgreSQL", "FDW"],
 "In PostgreSQL, what is a 'Foreign Data Wrapper' (FDW), and what specific architectural capability does it provide?",
 "A Foreign Data Wrapper (FDW) is an extension allowing PostgreSQL to seamlessly query data residing in external, separate systems (another PostgreSQL DB, MySQL, MongoDB, CSV files) as if they were local tables. It provides 'Federated Queries', allowing you to execute distributed `JOIN`s across disparate data sources natively within a single SQL statement.",
 ["An extension to seamlessly query external, disparate database systems as if they were local tables", "Provides the capability of 'Federated Queries'", "Allows native SQL `JOIN`s across completely different data sources (e.g., joining Postgres with MongoDB)"],
 ["It is a plastic wrapper used to protect foreign databases from viruses"]),

("TRANSACTIONS_AND_OPERATIONS", "debug", "medium", "debugging", ["Query Planner", "Statistics"],
 "A complex query uses a slow 'Nested Loop Join' (20 mins) instead of a faster 'Hash Join'. None of the tables have foreign keys or updated statistics. Why did the optimizer make a bad choice, and how do you fix it?",
 "The Query Planner relies heavily on internal statistical samples (row counts, histograms) to calculate the cheapest execution path. If statistics are stale/missing, the planner assumes the tables are tiny and incorrectly chooses a Nested Loop Join. Fix: Explicitly run `ANALYZE` (or `UPDATE STATISTICS`), forcing the DB to recount data and generate a faster Hash Join plan.",
 ["The Query Planner relies on statistical sampling (row counts, histograms) to build execution plans", "Missing/stale statistics cause the planner to assume tables are tiny, incorrectly choosing Nested Loops", "Fix: Execute `ANALYZE` (or `UPDATE STATISTICS`) to refresh metadata and trigger a Hash Join"],
 ["The optimizer was tired and chose the first join it could think of"])
]
