"""Batch 16 question content (Database Developer). Antigravity-native, no Gemini API."""

ROLE = "Database Developer"

BUCKET_KEYS = {
    "DB_AD": ("SQL Fundamentals", "Advanced SQL", "SQL", ["Data Analyst", "Data Engineer"]),
    "DB_IX": ("Indexing", "Performance", "SQL", ["Backend Developer"]),
    "DB_QO": ("Query Optimization", "Execution Plans", "SQL", ["Data Engineer", "Backend Developer"]),
    "DB_TR": ("Transactions", "Concurrency", "SQL", ["Backend Developer"]),
    "DB_SD": ("Schema Design", "Data Modeling", "SQL", ["Data Architect", "Backend Developer"]),
    "DB_PG": ("PostgreSQL", "Internals", "PostgreSQL", ["Backend Developer"]),
    "DB_NS": ("NoSQL", "Data Modeling", "MongoDB/Redis", ["Data Engineer"]),
    "DB_RP": ("Replication", "High Availability", "Distributed Systems", ["DevOps / Cloud Engineer"]),
    "DB_PF": ("Performance", "Partitioning", "SQL", ["Performance Engineer"]),
    "DB_OM": ("Operations", "Migrations & Security", "PostgreSQL", ["DevOps / Cloud Engineer"]),
}

Q = [
# ---------------- DB_AD ----------------
("DB_AD", "fundamentals", "easy", "concept", ["SQL"],
 "What is the primary difference between the `WHERE` clause and the `HAVING` clause in SQL?",
 "The `WHERE` clause filters rows *before* any groupings or aggregations are performed. The `HAVING` clause filters data *after* the `GROUP BY` clause and aggregation functions (like SUM, COUNT) have been applied.",
 ["WHERE filters before aggregation", "HAVING filters after aggregation (GROUP BY)", "HAVING is used with aggregate functions"],
 ["WHERE is for strings and HAVING is for numbers"]),

("DB_AD", "explain", "easy", "concept", ["SQL"],
 "Explain the purpose of a Common Table Expression (CTE) and how it differs from a subquery.",
 "A CTE (defined using the `WITH` clause) allows you to define a temporary, named result set that can be referenced multiple times within the main query. It improves readability and maintainability compared to nested subqueries. Unlike subqueries, CTEs can also be recursive.",
 ["Defined using WITH clause", "Improves readability over nested subqueries", "Can be referenced multiple times and can be recursive"],
 ["CTEs permanently save data to the database"]),

("DB_AD", "implement", "medium", "implementation", ["Window Functions"],
 "How would you write an analytical SQL query to find the top 3 highest-paid employees in each department, using window functions?",
 "I would use the `DENSE_RANK()` or `ROW_NUMBER()` window function, partitioning by the department and ordering by salary descending in a CTE or subquery. Then, I would query that CTE and filter for `WHERE rank <= 3`.",
 ["Use DENSE_RANK() or ROW_NUMBER() window function", "PARTITION BY department ORDER BY salary DESC", "Filter the rank <= 3 in the outer query"],
 ["Use GROUP BY and LIMIT 3"]),

("DB_AD", "scenario", "medium", "scenario", ["Window Functions"],
 "A query calculating a rolling 7-day average sales amount is extremely slow. How would you optimize the window function bounds to ensure it performs efficiently?",
 "I would ensure the window frame clause explicitly defines bounds, such as `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`. It is critical to ensure there is a covering index on the partitioning column (e.g., `store_id`) and the ordering column (e.g., `sale_date`) so the database doesn't have to sort the entire table in memory.",
 ["Use explicit ROWS BETWEEN bounds", "Ensure a covering index exists", "Index must include partition and order by columns"],
 ["Remove the window function and use a cursor"]),

("DB_AD", "tradeoff", "hard", "tradeoff", ["Data Modeling"],
 "What are the performance tradeoffs of using a recursive CTE to traverse a deeply nested hierarchical employee tree versus implementing the nested set model or materialized paths?",
 "Recursive CTEs are easy to write and maintain on standard adjacency list schemas (parent_id), but performance degrades exponentially with depth due to repeated joins. Materialized paths or nested sets allow extremely fast O(1) or O(log N) reads of entire subtrees, but make writes (like moving a node) highly complex and expensive.",
 ["Recursive CTEs: easy schema, slow deep reads", "Materialized paths/nested sets: extremely fast subtree reads", "Materialized paths/nested sets: complex and slow writes/updates"],
 ["Recursive CTEs are the fastest way to read graphs"]),

# ---------------- DB_IX ----------------
("DB_IX", "fundamentals", "easy", "concept", ["Indexing"],
 "What is a B-tree index, and why is it the default index type in most relational databases?",
 "A B-tree (Balanced Tree) index is a self-balancing tree data structure that keeps data sorted and allows searches, sequential access, insertions, and deletions in logarithmic time (O(log n)). It is the default because it efficiently handles both exact match (`=`) and range queries (`<`, `BETWEEN`).",
 ["Balanced tree structure (O(log n) time)", "Keeps data sorted", "Supports both exact matches and range queries efficiently"],
 ["B-tree stands for Binary tree"]),

("DB_IX", "explain", "medium", "concept", ["Indexing"],
 "Explain the concept of a 'covering index' and how it prevents table lookups.",
 "A covering index includes all the columns specified in both the `SELECT` clause and the `WHERE` clause of a query. Because all requested data is literally stored within the index structure itself, the database doesn't need to perform a costly 'heap fetch' (or table lookup) to retrieve the actual row data.",
 ["Includes all columns needed for SELECT and WHERE", "Satisfies the query entirely from the index", "Prevents costly heap fetches / table row lookups"],
 ["A covering index encrypts the table"]),

("DB_IX", "implement", "medium", "implementation", ["Indexing"],
 "You have a table of 100 million orders. You frequently query for orders placed today by a specific `user_id`. How would you design a composite index for this query, and does column order matter?",
 "Column order is critical. The index should be `(user_id, order_date)`. The leading column should be the one tested for exact equality (`user_id = ?`), followed by the column used for range conditions (`order_date = today`). If `order_date` were first, the index couldn't efficiently filter by `user_id` for that date.",
 ["Create a composite index (user_id, order_date)", "Order matters strictly", "Equality columns first, range columns second"],
 ["Order doesn't matter for composite indexes"]),

("DB_IX", "tradeoff", "hard", "tradeoff", ["Schema Design"],
 "What are the tradeoffs of using a UUID (Universally Unique Identifier) as a primary key clustered index instead of an auto-incrementing integer (SERIAL or BIGSERIAL)?",
 "UUIDs provide global uniqueness, excellent security (hard to guess), and allow clients to generate IDs safely before insertion. However, standard UUIDs are random, which causes massive fragmentation and page splits in a clustered B-tree index, destroying write performance and wasting memory. Sequential integers are highly optimized for fast, append-only B-tree inserts.",
 ["UUIDs: global uniqueness, safe client-side generation", "Random UUIDs cause B-tree fragmentation and page splits", "Integers: highly optimized for append-only clustered index writes"],
 ["UUIDs are faster for database indexing than integers"]),

("DB_IX", "debug", "hard", "debugging", ["Query Optimization"],
 "You notice that a query using an explicitly indexed column is still performing a full sequential table scan. What are the common reasons the query planner might ignore the index?",
 "The planner ignores the index if: 1. The query applies a function to the column (e.g., `LOWER(email) = ?`) without a functional index. 2. There is an implicit type conversion (e.g., string vs int). 3. The data distribution (cardinality) indicates the query will return a massive percentage of the table, making a sequential scan faster than random index reads. 4. Table statistics are outdated.",
 ["Functions on columns (e.g., LOWER) break index usage", "Implicit type conversions (string to int)", "High percentage of rows matched (cardinality limits)"],
 ["Indexes only work on primary keys"]),

# ---------------- DB_QO ----------------
("DB_QO", "explain", "easy", "concept", ["Optimization"],
 "What is the purpose of an EXPLAIN or EXPLAIN ANALYZE command in relational databases?",
 "The `EXPLAIN` command shows the execution plan generated by the database query optimizer, detailing how it will retrieve the data (e.g., index scans vs sequential scans). `EXPLAIN ANALYZE` actually executes the query and provides real-world timings, row counts, and memory usage alongside the planned estimates.",
 ["Shows the query optimizer's execution plan", "Details index scans vs sequential scans", "EXPLAIN ANALYZE actually runs the query for real timings"],
 ["It translates SQL into Python code"]),

("DB_QO", "scenario", "medium", "scenario", ["Execution Plans"],
 "A database query joining `users` and `orders` uses a Nested Loop Join and takes 5 minutes to execute. How do you analyze the execution plan to force or encourage a Hash Join or Merge Join?",
 "The Nested Loop is likely struggling because the inner table isn't properly indexed, or the cardinality estimates are drastically wrong (leading the planner to think the dataset is small). Analyze `EXPLAIN ANALYZE` to check if `estimated rows` match `actual rows`. Fix it by running `ANALYZE` to update statistics, or adding an index to the join condition columns.",
 ["Check if estimated rows match actual rows in EXPLAIN ANALYZE", "Update table statistics (e.g., run ANALYZE)", "Add indexes on the foreign key/join columns"],
 ["Rewrite the join into a subquery"]),

("DB_QO", "debug", "medium", "debugging", ["Optimization"],
 "An application occasionally experiences slow queries that run fast when tested manually in pgAdmin or DataGrip. What is parameter sniffing, and how does it cause this discrepancy?",
 "Parameter sniffing occurs when the database compiles and caches a query execution plan based on the first set of parameters provided. If the first parameter yielded a tiny dataset, the plan (e.g., Nested Loop) is cached. Later, if the application provides a parameter yielding a massive dataset, the cached plan is horribly inefficient. Manual tools often send raw SQL, bypassing the cached parameterized plan.",
 ["Database caches plan based on initial parameters", "Plan is inefficient for parameters with different cardinality", "Manual testing often uses raw SQL, bypassing the cache"],
 ["Parameter sniffing is a security vulnerability"]),

("DB_QO", "tradeoff", "medium", "tradeoff", ["SQL"],
 "What tradeoffs exist when using a `LEFT JOIN` compared to an `INNER JOIN` in terms of query execution planning and data volume?",
 "An `INNER JOIN` allows the query optimizer to reorder the join sequence freely to maximize performance, and filters out non-matching rows, reducing data volume early. A `LEFT JOIN` forces the optimizer to preserve all rows from the left table regardless of matches, generating larger intermediate datasets and strictly limiting how the optimizer can reorder the execution plan.",
 ["INNER JOIN allows the optimizer to freely reorder joins", "LEFT JOIN restricts optimizer reordering", "LEFT JOIN preserves rows, increasing intermediate data volume"],
 ["LEFT JOIN is always faster than INNER JOIN"]),

("DB_QO", "scenario", "hard", "scenario", ["Database Maintenance"],
 "A PostgreSQL database query planner suddenly starts making terrible choices (e.g., nested loop over 10M rows instead of hash join) right after a massive bulk insert. How do you diagnose and fix this immediately?",
 "The massive bulk insert invalidated the table's statistical distribution, but the auto-analyze daemon hasn't run yet. The query planner is making decisions based on stale, drastically undersized row estimates. Fix this immediately by manually running the `ANALYZE` (or `VACUUM ANALYZE`) command on the affected tables to update the planner's statistics.",
 ["Massive inserts make table statistics stale", "Planner uses incorrect cardinality estimates", "Fix immediately by manually running ANALYZE on the table"],
 ["Restart the PostgreSQL server"]),

# ---------------- DB_TR ----------------
("DB_TR", "fundamentals", "easy", "concept", ["Transactions"],
 "Explain the ACID properties of a database transaction.",
 "ACID stands for Atomicity (all operations succeed or all fail/rollback), Consistency (data moves from one valid state to another, respecting constraints), Isolation (concurrent transactions do not interfere with each other), and Durability (once committed, changes are permanently saved, even in a crash).",
 ["Atomicity: all or nothing", "Consistency: valid states and constraints", "Isolation: concurrent safety. Durability: permanent saves"],
 ["ACID stands for Asynchronous Concurrent Indexing Database"]),

("DB_TR", "explain", "medium", "concept", ["Isolation Levels"],
 "Explain the difference between a 'dirty read' and a 'non-repeatable read' in database transaction isolation.",
 "A dirty read occurs when a transaction reads data that has been modified by another concurrent, uncommitted transaction (risking reading rolled-back data). A non-repeatable read occurs when a transaction reads the same row twice, but another committed transaction modified that row in between the reads, yielding different results.",
 ["Dirty read: reading uncommitted changes", "Non-repeatable read: same query yields different results due to committed updates", "Both violate strict serialization"],
 ["They are exactly the same thing"]),

("DB_TR", "tradeoff", "hard", "tradeoff", ["Concurrency"],
 "What are the tradeoffs between optimistic concurrency control (using a `version` column) and pessimistic concurrency control (`SELECT FOR UPDATE`) in a high-contention relational database?",
 "Optimistic control doesn't use DB locks, maximizing read/write throughput, but requires the application to handle retry logic when `UPDATE WHERE version = ?` fails due to collisions. Pessimistic locking guarantees safety at the DB level, avoiding application retries, but forces concurrent transactions to queue, drastically reducing throughput and risking deadlocks.",
 ["Optimistic: maximizes throughput, requires app-level retries", "Pessimistic: guarantees DB safety, causes queuing and deadlocks", "Pessimistic drastically reduces throughput under contention"],
 ["Pessimistic locking is always faster"]),

("DB_TR", "scenario", "medium", "scenario", ["Architecture"],
 "A developer wraps an entire 10-second HTTP API request, including a third-party payment call, inside a single database transaction. What architectural problems does this cause at the database level?",
 "This is a massive anti-pattern. It holds the database connection and internal row locks open for the entire 10 seconds. Under concurrent load, this will rapidly exhaust the database connection pool, cause massive lock contention blocking other queries, and potentially trigger cascading timeouts across the entire system.",
 ["Holds database connection open during slow HTTP calls", "Causes severe lock contention on DB rows", "Exhausts connection pools and causes cascading failures"],
 ["Transactions speed up the third-party HTTP call"]),

("DB_TR", "debug", "hard", "debugging", ["Locking"],
 "A PostgreSQL-backed service begins experiencing lock contention and deadlocks during peak traffic. How would you diagnose the contention using system views?",
 "I would query the `pg_stat_activity` and `pg_locks` system views to see which queries are actively waiting for locks (`wait_event_type = 'Lock'`) and which PIDs are holding those locks. I would trace this to the specific application queries. To resolve deadlocks, I would ensure the application always acquires row locks in a consistent, alphabetical or sorted order.",
 ["Query pg_stat_activity and pg_locks", "Identify PIDs holding and waiting for locks", "Fix deadlocks by enforcing consistent lock acquisition order"],
 ["Ignore it, deadlocks resolve themselves automatically"]),

# ---------------- DB_SD ----------------
("DB_SD", "fundamentals", "easy", "concept", ["Schema Design"],
 "What is the primary goal of Third Normal Form (3NF) in relational database schema design?",
 "The primary goal of 3NF is to reduce data redundancy and ensure data integrity. It achieves this by ensuring that every non-key column is strictly dependent on the primary key, the whole primary key, and nothing but the primary key, eliminating transitive dependencies.",
 ["Reduce data redundancy", "Ensure data integrity", "Eliminate transitive dependencies (attributes depend only on the primary key)"],
 ["3NF makes queries run 3 times faster"]),

("DB_SD", "scenario", "medium", "scenario", ["Schema Design"],
 "An application requires tracking every change made to a sensitive `accounts` table over time. How would you design the schema to implement an immutable audit log?",
 "I would use an Event Sourcing approach or an Audit Table. I would create an `accounts_audit` table. Instead of having the application handle it, I would use database Triggers (`AFTER INSERT, UPDATE, DELETE` on `accounts`) to automatically insert a snapshot of the old and new row values, the timestamp, and the user performing the action into the immutable audit table.",
 ["Create a separate immutable audit table", "Use database Triggers for guaranteed capture", "Record old values, new values, timestamps, and actors"],
 ["Just add a 'last_modified' column to the accounts table"]),

("DB_SD", "tradeoff", "medium", "tradeoff", ["Data Integrity"],
 "What are the tradeoffs of using database-level constraints (like Foreign Keys and CHECK constraints) versus validating data exclusively in the application code?",
 "Database constraints provide an absolute guarantee of data integrity regardless of which application, script, or manual query modifies the database. However, they add overhead to write operations and can complicate schema migrations or sharding. Application-side validation is faster to scale and easier to test, but risks corruption if a bug occurs or a manual script bypasses the app.",
 ["DB constraints: absolute integrity guarantee, robust against manual queries", "DB constraints: adds write overhead, complicates sharding", "App validation: easier to scale, but risks data corruption"],
 ["Database constraints are completely useless if you use Java"]),

("DB_SD", "implement", "hard", "implementation", ["Data Modeling"],
 "How would you approach designing a schema for a highly polymorphic relationship, such as 'Comments' that can belong to either a 'Post', a 'Video', or an 'Image', avoiding anti-patterns?",
 "Avoid the 'Polymorphic Associations' anti-pattern (using `entity_type` and `entity_id`) because it prevents Foreign Key constraints. Instead, use 'Exclusive Arcs' (a `comments` table with nullable FKs `post_id`, `video_id`, `image_id` and a CHECK constraint ensuring exactly one is not null), or use 'Reverse Foreign Keys' (a central `commentable` interface table that Posts/Videos inherit from).",
 ["Avoid string 'entity_type' columns (breaks Foreign Keys)", "Use Exclusive Arcs (multiple nullable FKs with a CHECK constraint)", "Or use a central 'interface' table (commentable)"],
 ["Just use NoSQL, relational databases can't do this"]),

("DB_SD", "scenario", "hard", "scenario", ["Concurrency"],
 "A production database is suffering from extreme contention on a central `counters` table that tracks page views. How do you redesign the schema and application logic to allow massive concurrent increments without locking?",
 "Updating a single row concurrently causes massive locking bottlenecks. I would redesign it using 'Sharded Counters'. Instead of one row, create 100 rows for the same page view counter. When a view occurs, the application randomly picks one of the 100 rows to increment. To get the total, run `SUM(views) WHERE entity_id = ?`. Alternatively, use Redis for counting and flush to the DB periodically.",
 ["Implement Sharded Counters (multiple rows per entity)", "Randomly increment one of the shards to distribute locks", "Alternatively, aggregate in Redis and batch flush to DB"],
 ["Remove the primary key from the table"]),

# ---------------- DB_PG ----------------
("DB_PG", "explain", "easy", "concept", ["PostgreSQL"],
 "Explain the concept of Multi-Version Concurrency Control (MVCC) in PostgreSQL.",
 "MVCC is how PostgreSQL handles concurrency. Instead of locking a row when reading or writing, it creates a new version of the row for every update. Concurrent transactions see a snapshot of the database at a specific point in time, allowing readers to read without blocking writers, and writers to write without blocking readers.",
 ["Creates a new version of a row on update", "Transactions see a point-in-time snapshot", "Readers don't block writers; writers don't block readers"],
 ["MVCC locks the entire table during reads"]),

("DB_PG", "debug", "medium", "debugging", ["PostgreSQL"],
 "A PostgreSQL database's storage size on disk continues to grow indefinitely, even though millions of rows are regularly deleted. Why is this happening, and how do you resolve it?",
 "This is 'table bloat' caused by MVCC. `DELETE` and `UPDATE` operations don't actually remove data from disk; they just mark old row versions as invisible (dead tuples). If the `autovacuum` daemon is disabled, failing, or configured too conservatively, these dead tuples are never reclaimed. Fix by running `VACUUM FULL` (which locks the table) or tuning `autovacuum` settings.",
 ["Table bloat due to dead tuples (MVCC)", "Autovacuum daemon is failing to reclaim space", "Resolve by tuning autovacuum or running VACUUM FULL"],
 ["The hard drive is fragmented"]),

("DB_PG", "implement", "medium", "implementation", ["PostgreSQL"],
 "How would you index a large JSONB column in PostgreSQL to ensure fast lookups for a specific nested key-value pair?",
 "I would create a Generalized Inverted Index (GIN) on the JSONB column. A standard GIN index (e.g., `CREATE INDEX idx ON table USING GIN (json_col)`) allows extremely fast queries using the `@>` (contains) operator. If I only query a specific path, I would create a targeted B-tree expression index: `CREATE INDEX idx ON table ((json_col->>'status'))`.",
 ["Use a GIN (Generalized Inverted Index) for arbitrary JSON queries", "Use the @> (contains) operator", "Use a B-tree expression index for a specific known path"],
 ["PostgreSQL cannot index JSON data"]),

("DB_PG", "compare", "hard", "comparison", ["MySQL vs PostgreSQL"],
 "Compare the default transaction isolation level in MySQL (InnoDB) with PostgreSQL. How do they handle 'phantom reads' differently out of the box?",
 "PostgreSQL's default is `Read Committed`, which prevents dirty reads but allows phantom reads. MySQL (InnoDB)'s default is `Repeatable Read`, which prevents dirty and non-repeatable reads. Crucially, InnoDB goes beyond standard SQL by using Next-Key Locks to also prevent 'phantom reads' out of the box in its default `Repeatable Read` level, whereas PostgreSQL requires explicitly setting `Serializable` to prevent phantoms.",
 ["PostgreSQL default: Read Committed (allows phantoms)", "MySQL InnoDB default: Repeatable Read", "InnoDB prevents phantoms by default using Next-Key Locks"],
 ["MySQL and PostgreSQL are exactly identical in isolation"]),

("DB_PG", "scenario", "medium", "scenario", ["MySQL"],
 "A MySQL database using InnoDB is experiencing replication lag. You notice the primary is executing a massive, long-running `DELETE` statement. How do you redesign the `DELETE` operation to minimize replication lag?",
 "A massive `DELETE` generates enormous row-based replication logs (binlog), overwhelming the single-threaded replica applicator. Redesign it by batching the deletes: limit the delete to 1,000 rows at a time using `LIMIT 1000`, pause briefly, and loop. This keeps transactions small, locks minimal, and allows the replica to keep up.",
 ["Massive DELETEs create huge binlogs and overwhelm replicas", "Batch the operation (e.g., DELETE ... LIMIT 1000)", "Keep transactions small to allow replica application"],
 ["Turn off replication temporarily"]),

# ---------------- DB_NS ----------------
("DB_NS", "fundamentals", "easy", "concept", ["NoSQL"],
 "What is the difference between a document database (like MongoDB) and a key-value store (like Redis)?",
 "A key-value store uses opaque values accessed strictly by a primary key, prioritizing extreme speed in memory. A document database stores semi-structured data (like JSON/BSON), understands the internal structure of the document, and allows complex querying, filtering, and indexing on nested fields.",
 ["Key-Value: opaque data, accessed only by key, extremely fast", "Document: stores JSON/BSON, understands internal structure", "Document DBs allow complex querying on nested fields"],
 ["They are exactly the same thing"]),

("DB_NS", "tradeoff", "medium", "tradeoff", ["MongoDB"],
 "What are the tradeoffs of embedding documents (denormalization) versus referencing documents in MongoDB?",
 "Embedding documents optimizes for extremely fast read performance (single query retrieves all data) and provides atomic updates, but risks hitting the 16MB document size limit and causes data duplication. Referencing avoids duplication and infinite growth, but forces the application or database (`$lookup`) to perform multiple slower queries (joins) to retrieve related data.",
 ["Embedding: fast reads, atomic updates, hits 16MB limits", "Referencing: no duplication, requires slow $lookup (joins)", "Embedding duplicates data"],
 ["Embedding is always the wrong choice"]),

("DB_NS", "scenario", "medium", "scenario", ["Redis"],
 "A Redis instance used for caching is suddenly rejecting all new writes, throwing an OOM (Out of Memory) command error. What configuration policies would you check and adjust to fix this?",
 "Redis has reached its `maxmemory` limit. I would check the `maxmemory-policy` configuration. If it's set to `noeviction` (the default), it will refuse writes. I would change it to `allkeys-lru` or `volatile-lru` so Redis automatically evicts the least recently used keys to make room for new data.",
 ["Redis hit maxmemory limit", "Check maxmemory-policy configuration", "Change from noeviction to allkeys-lru or volatile-lru"],
 ["Restart Redis to clear memory completely"]),

("DB_NS", "implement", "hard", "implementation", ["Wide-Column"],
 "How would you model a many-to-many relationship (like Users and Groups) in a wide-column store like Cassandra, given that JOINs are not supported?",
 "In Cassandra, you design schema based strictly on the queries you will run. To support finding 'Groups for a User' and 'Users in a Group', you must maintain two separate, denormalized tables: `groups_by_user` (Partition key: user_id, Clustering key: group_id) and `users_by_group` (Partition key: group_id, Clustering key: user_id). The application must write to both tables simultaneously.",
 ["Design schema based strictly on query access patterns", "Create two denormalized tables (groups_by_user, users_by_group)", "Application must perform dual-writes to both tables"],
 ["Use a foreign key constraint between the tables"]),

("DB_NS", "compare", "medium", "comparison", ["Redis"],
 "Compare the persistence options in Redis: RDB snapshots versus AOF (Append-Only File). When would you use one over the other?",
 "RDB takes point-in-time snapshots of the dataset; it's highly compact and fast to restart, but risks losing minutes of data if it crashes between snapshots. AOF logs every write operation; it guarantees near-zero data loss (durability), but files become huge and restarts are slower. Use AOF for strict durability, and RDB for caching or faster backups.",
 ["RDB: compact snapshots, fast restart, risks data loss between snapshots", "AOF: logs every write, strict durability, large files/slow restart", "Can be used together for optimal durability"],
 ["Redis does not support persistence"]),

# ---------------- DB_RP ----------------
("DB_RP", "explain", "easy", "concept", ["Replication"],
 "Explain the difference between synchronous and asynchronous database replication.",
 "In synchronous replication, the primary database waits for the replica to confirm it has successfully written the data before acknowledging success to the client (guarantees zero data loss, but adds latency). In asynchronous replication, the primary responds to the client immediately and sends data to the replica in the background (fast, but risks data loss if primary crashes).",
 ["Synchronous: Primary waits for replica ack (zero data loss, slow)", "Asynchronous: Primary acks immediately, replica updates in background", "Asynchronous risks data loss on crash"],
 ["Synchronous means both databases are in the same building"]),

("DB_RP", "scenario", "medium", "scenario", ["Consistency"],
 "A backend API reads user profile data immediately after the user updates it, but occasionally the old data is returned. The database uses asynchronous read-replicas. How do you fix this consistency issue?",
 "This is replication lag. Fix it by implementing a 'read-your-own-writes' consistency strategy. The application should route read queries for that specific user's profile to the Primary (writer) database for a short window (e.g., 5 seconds) after an update, or cache the updated profile in Redis, while other users continue to read from the replicas.",
 ["Replication lag causing stale reads", "Implement 'read-your-own-writes' consistency", "Route reads to the Primary node temporarily after a write"],
 ["Force synchronous replication globally across the world"]),

("DB_RP", "tradeoff", "hard", "tradeoff", ["Architecture"],
 "What tradeoffs exist between implementing horizontal sharding at the application layer versus using a managed distributed SQL database (like CockroachDB or Spanner)?",
 "App-layer sharding uses standard, cheap databases (MySQL/Postgres), but forces the application to route queries, completely breaks cross-shard JOINs, and makes re-sharding an operational nightmare. Distributed SQL handles sharding, rebalancing, and distributed ACID transactions automatically under the hood, but introduces higher network latency per query, steep learning curves, and high infrastructure costs.",
 ["App sharding: cheap, but breaks JOINs and complicates app logic/re-sharding", "Distributed SQL: automatic sharding and ACID, but higher latency/cost", "Distributed SQL handles cross-node coordination seamlessly"],
 ["Application sharding is completely effortless to maintain"]),

("DB_RP", "debug", "hard", "debugging", ["PostgreSQL"],
 "You notice that a PostgreSQL read-replica is frequently cancelling queries initiated by data analysts, citing a 'recovery conflict'. What causes this, and how can you configure the replica to prevent it?",
 "A recovery conflict occurs when the Primary node modifies or deletes a row (via MVCC/vacuum) that the read-replica is currently using for a long-running analytical query. The replica prioritizes applying replication logs over running queries. Fix this by setting `max_standby_streaming_delay` to a much higher value, or enabling `hot_standby_feedback` so the replica tells the primary not to vacuum those rows.",
 ["Primary vacuumed a row the replica's long-running query was using", "Replica prioritizes log application over query execution", "Fix: enable hot_standby_feedback or increase max_standby_streaming_delay"],
 ["The data analysts typed the SQL query incorrectly"]),

("DB_RP", "implement", "medium", "implementation", ["High Availability"],
 "How would you approach implementing a zero-downtime database failover from a primary node to a replica in a high-availability production environment?",
 "I would use a connection pooler/proxy (like pgBouncer or ProxySQL) combined with a high-availability manager (like Patroni or Orchestrator). During failover, the manager pauses traffic at the proxy, promotes the synchronized replica to Primary, updates the proxy's routing configuration, and unpauses traffic. The application experiences a slight delay but no dropped connections.",
 ["Use a proxy/connection pooler (pgBouncer, ProxySQL)", "Use an HA manager (Patroni, Orchestrator) to promote the replica", "Pause traffic at the proxy during promotion to prevent dropped connections"],
 ["Change the IP address in the application source code and redeploy"]),

# ---------------- DB_PF ----------------
("DB_PF", "fundamentals", "easy", "concept", ["Partitioning"],
 "What is table partitioning, and how does it improve database performance?",
 "Partitioning divides a large logical table into smaller, separate physical tables based on a key (like a date range). It improves performance through 'partition pruning'—the query optimizer can completely ignore partitions that don't match the query filter, drastically reducing disk I/O and scan times for massive datasets.",
 ["Divides large table into smaller physical tables", "Improves performance via partition pruning", "Reduces disk I/O for targeted queries"],
 ["Partitioning deletes old data automatically"]),

("DB_PF", "scenario", "medium", "scenario", ["Partitioning"],
 "A massive `events` table with 5 billion rows is partitioned by month. However, a query filtering by date is still scanning all 60 partitions. What concept is failing, and how do you fix the query?",
 "Partition pruning is failing. This usually happens if the query uses a function on the partition key (e.g., `WHERE DATE(event_timestamp) = '2023-01-01'`) or casts the type incorrectly. Fix it by ensuring the `WHERE` clause filters directly on the raw partition column using a clear range: `WHERE event_timestamp >= '2023-01-01' AND event_timestamp < '2023-01-02'`.",
 ["Partition pruning is failing", "Caused by using functions on the partition column in the WHERE clause", "Fix by comparing the raw column to explicit ranges"],
 ["The database forgot how to prune"]),

("DB_PF", "implement", "hard", "implementation", ["Migrations"],
 "How would you approach migrating an unpartitioned 1TB PostgreSQL table to a time-based partitioning scheme with absolute zero downtime?",
 "Create a new partitioned table structure. Use logical replication (or database triggers) to capture all ongoing inserts/updates and mirror them to the new table. Use a background script to backfill historical data in chunks. Once synchronized, take a brief lock, rename the old table to '_old', rename the new table to the original name, and release the lock.",
 ["Create new partitioned table", "Use triggers/logical replication to mirror new writes", "Backfill historical data, then briefly lock and rename tables"],
 ["Drop the table and restore it from a backup into partitions"]),

("DB_PF", "tradeoff", "medium", "tradeoff", ["Architecture"],
 "What are the tradeoffs of maintaining a highly aggressive connection pool limit (e.g., max 100 connections) on the database server versus allowing applications to open unlimited connections?",
 "Unlimited connections cause severe context switching, memory exhaustion, and lock contention on the database, eventually causing latency to spike exponentially. A strict, small connection pool ensures the database engine stays within its optimal CPU concurrency limits (maximum throughput, low latency), but forces application-side threads to queue/wait if traffic exceeds the pool size.",
 ["Strict pool: maintains optimal DB throughput and prevents context switching", "Unlimited pool: exhausts DB memory and CPU, crashing the DB", "Strict pool forces application threads to queue"],
 ["Unlimited connections are always optimal for performance"]),

("DB_PF", "debug", "medium", "debugging", ["Performance"],
 "A database server's CPU is pegged at 100% during a load test, but memory and disk I/O are practically zero. What architectural or query issues typically cause this extreme CPU bottleneck?",
 "High CPU with low I/O almost always points to massive in-memory data processing. Causes include missing indexes resulting in massive sequential scans (even if data is cached in RAM), complex sorting (`ORDER BY`) or hashing (`GROUP BY`) on large datasets, or extreme lock contention/spinning on highly concurrent updates to a single row.",
 ["Massive in-memory sequential scans (missing indexes)", "Complex sorting or aggregations (ORDER BY / GROUP BY)", "Lock contention (spinlocks)"],
 ["The hard drive is failing"]),

# ---------------- DB_OM ----------------
("DB_OM", "explain", "easy", "concept", ["Disaster Recovery"],
 "What do the terms RPO (Recovery Point Objective) and RTO (Recovery Time Objective) mean in the context of database backups?",
 "RPO is the maximum acceptable amount of data loss measured in time (e.g., 'we can lose up to 15 minutes of data'). RTO is the maximum acceptable amount of downtime required to restore the system (e.g., 'the database must be back online within 1 hour').",
 ["RPO: Maximum acceptable data loss (time)", "RTO: Maximum acceptable downtime to restore", "Used to define disaster recovery architectures"],
 ["RPO is Recovery Password Object"]),

("DB_OM", "scenario", "medium", "scenario", ["Migrations"],
 "You need to add a new `NOT NULL` column with a default value to a 500GB production PostgreSQL table. How do you perform this schema migration without locking the table and causing downtime?",
 "In PostgreSQL 11+, `ALTER TABLE ADD COLUMN col DEFAULT val` is safe and instant (metadata only). However, for older versions, it rewrites the entire table, causing downtime. The zero-downtime strategy is: 1. Add column as nullable. 2. Set default for new rows. 3. Backfill old rows in small batches. 4. Add the `NOT NULL` constraint using an `INVALID` state, then validate it concurrently.",
 ["Modern PG (11+): instant metadata operation", "Older DBs: Add as nullable, set default, backfill in batches", "Apply NOT NULL constraint concurrently"],
 ["Just run the ALTER TABLE, it never locks"]),

("DB_OM", "implement", "hard", "implementation", ["Security"],
 "How would you design a database security model implementing Row-Level Security (RLS) in PostgreSQL so that tenants in a SaaS application can never read each other's data?",
 "I would enable RLS on the table (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`). I would create a policy (e.g., `CREATE POLICY tenant_isolation ON table USING (tenant_id = current_setting('app.current_tenant')::int)`). The backend application must securely set the `app.current_tenant` variable in the session context at the start of every connection or transaction based on the authenticated user.",
 ["Enable Row-Level Security (RLS) on the table", "Create a policy matching tenant_id to a session variable", "Backend app injects the session variable per request"],
 ["Create a completely separate database server for every user"]),

("DB_OM", "debug", "medium", "debugging", ["Memory Management"],
 "An application occasionally complains about dropping database connections. The database connection logs show intermittent 'OOM Killer' invocations by the Linux kernel. How do you diagnose and tune the database memory usage?",
 "The database requested more RAM than the OS physically had. In PostgreSQL, this usually means `shared_buffers`, combined with `work_mem` multiplied by `max_connections`, exceeded physical RAM. Tune it by drastically lowering `max_connections` (using a pooler like pgBouncer), lowering `work_mem` to prevent complex queries from eating RAM, and ensuring `shared_buffers` isn't set too high (typically 25%).",
 ["OS killed the DB due to memory exhaustion", "Reduce max_connections using a connection pooler", "Tune work_mem and shared_buffers safely"],
 ["Install antivirus software on the Linux kernel"]),

("DB_OM", "compare", "medium", "comparison", ["Disaster Recovery"],
 "Compare using logical backups (e.g., `pg_dump`) versus physical/binary backups (e.g., EBS snapshots or WAL archiving) for disaster recovery of a massive multi-terabyte database.",
 "Logical backups extract data as SQL text; they are highly portable across versions, allow restoring single tables, but take hours/days to create and restore on massive databases. Physical backups copy the actual disk blocks and transaction logs (WAL); they are extremely fast to backup and restore, and support Point-In-Time Recovery (PITR), but are tightly coupled to the DB binary version.",
 ["Logical: portable, table-level restore, very slow", "Physical: copies disk blocks/WAL, very fast, supports PITR", "Physical is required for multi-terabyte disaster recovery"],
 ["Logical backups are faster for massive databases"])
]
