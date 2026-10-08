"""Batch 36 Part 2 question content (Database Developer). Targeted Gap Generation."""

ROLE = "Database Developer"

BUCKET_KEYS = {
    "QUERY_PERFORMANCE_AND_INDEXING": ("Query Performance & Indexing", "Performance & Tuning", "Database", ["Database Developer", "Backend Developer"]),
}

Q = [
# ---------------- QUERY_PERFORMANCE_AND_INDEXING ----------------
("QUERY_PERFORMANCE_AND_INDEXING", "debug", "hard", "debugging", ["Composite Indexes", "Left-Most Prefix"],
 "You create a composite index `(status, created_at)`. A query filtering by `status` AND `created_at` uses the index. A query filtering ONLY by `created_at` completely ignores the index and does a sequential scan. Why?",
 "This demonstrates the 'Left-Most Prefix Rule' of B-Tree composite indexes. The database can only use the index if the query filters on the columns in the exact order they were defined, starting from the left. `status` is the leading column. If a query omits `status` and only filters by `created_at`, the DB cannot traverse the B-Tree effectively, forcing a full table scan.",
 ["'Left-Most Prefix Rule' of B-Tree indexes", "The query omitted the leading column (`status`) of the composite index", "Without the leading column, the DB cannot traverse the sorted tree structure, forcing a full scan"],
 ["The database index was built backwards"]),

("QUERY_PERFORMANCE_AND_INDEXING", "implement", "medium", "implementation", ["Indexes", "Zero-Downtime"],
 "You need to add a new index to a massive 500GB table in production. Running `CREATE INDEX idx ON table(col)` causes the application to lock up and crash, as all `INSERT`/`UPDATE` operations freeze. How do you implement this without downtime?",
 "You must use the `CONCURRENTLY` keyword: `CREATE INDEX CONCURRENTLY idx ON table(col)`. A standard index creation acquires an exclusive lock on the table, blocking all writes. Creating it concurrently performs the build in the background without locking writes. Tradeoff: It takes significantly longer to build and consumes more CPU/IO.",
 ["Use `CREATE INDEX CONCURRENTLY`", "Standard index creation acquires an exclusive table lock, blocking all write operations", "Concurrently builds the index in the background without locking writes (though it takes longer)"],
 ["Copy the table to a USB drive, add the index, and copy it back"]),

("QUERY_PERFORMANCE_AND_INDEXING", "tradeoff", "hard", "tradeoff", ["Covering Indexes", "Architecture"],
 "When optimizing a highly read-heavy query, what is the architectural tradeoff of creating a 'Covering Index' (an index that includes every single column selected in the query)?",
 "A Covering Index provides maximum read performance via an 'Index-Only Scan'; the DB returns the result entirely from the B-Tree in RAM without incurring disk I/O to fetch actual table rows (the Heap). The massive tradeoff is write performance and storage: every `INSERT`/`UPDATE` requires maintaining a bloated, massive index, severely degrading latency and disk space.",
 ["Provides maximum read performance via 'Index-Only Scans' (no Heap/Disk lookups required)", "Tradeoff: Massive degradation in Write (`INSERT`/`UPDATE`) performance", "Tradeoff: Severe index bloat, consuming excessive disk space and RAM"],
 ["Covering indexes hide the data from unauthorized users"]),

("QUERY_PERFORMANCE_AND_INDEXING", "scenario", "medium", "scenario", ["Execution Plans", "Filtering"],
 "An `EXPLAIN ANALYZE` shows an `Index Scan` followed by a `Filter`, stating: `Rows Removed by Filter: 1,500,000`. What does this specific metric tell you about why the query is slow, and how do you fix it?",
 "The database used an index, but it was insufficiently selective. It had to fetch 1.5 million physical rows from the disk (heap), evaluate a secondary condition on those rows, and discard them, causing massive, unnecessary disk I/O. Fix: Create a more specific composite index including the filtered column to eliminate those rows at the index level before fetching from the heap.",
 ["The index was insufficiently selective", "The DB performed massive disk I/O fetching 1.5M rows only to immediately discard them", "Fix: Create a composite index including the filtered column to eliminate rows at the B-Tree level"],
 ["The database was cleaning up old deleted rows automatically"]),

("QUERY_PERFORMANCE_AND_INDEXING", "explain", "easy", "concept", ["Scans", "B-Trees"],
 "In database query execution, what is the fundamental difference between a `Sequential Scan` (Table Scan) and an `Index Seek`?",
 "A Sequential Scan reads every single row in the entire table from start to finish to see if it matches conditions (extremely slow for large tables, but fast for tiny ones). An Index Seek traverses a sorted B-Tree data structure to directly locate the exact memory address of the specific row(s) in O(log N) time, drastically reducing disk I/O.",
 ["Sequential Scan: Reads every single physical row in the table from start to finish", "Index Seek: Traverses a sorted B-Tree in O(log N) time", "Index Seeks drastically reduce disk I/O by finding the exact memory address of the row"],
 ["Sequential scan reads left to right, Index seek reads right to left"]),

("QUERY_PERFORMANCE_AND_INDEXING", "debug", "medium", "debugging", ["Indexes", "SARGability"],
 "A query `SELECT * FROM users WHERE LOWER(email) = 'test@example.com'` is running very slowly, despite having a standard B-Tree index on `email`. Why is the database ignoring the index, and how do you fix it?",
 "Applying a function (`LOWER()`) to an indexed column in the `WHERE` clause fundamentally alters the data, meaning it can no longer match the pre-sorted values in the index (a 'SARGability' violation). To fix it, either create an explicitly defined Functional Index (`CREATE INDEX idx ON users (LOWER(email))`) or enforce lowercase insertion at the application layer.",
 ["Applying a function (`LOWER`) to an indexed column violates SARGability", "The DB cannot match the altered data to the pre-sorted B-Tree index, forcing a full scan", "Fix: Create a Functional/Expression Index, or enforce lowercase at the application layer"],
 ["The database thinks 'test' is a reserved keyword"]),

("QUERY_PERFORMANCE_AND_INDEXING", "implement", "hard", "implementation", ["Spatial Indexes", "Geospatial"],
 "You design a geospatial database to find users within a 5-mile radius. A standard B-Tree index on `latitude`/`longitude` performs terribly for radius queries. What specific type of index must you implement, and what data structure does it use?",
 "You must implement a Spatial Index (e.g., GiST or SP-GiST with PostGIS). These indexes use data structures like R-Trees (Region Trees) or Geohashes, which divide 2D space into bounding boxes. This allows the DB to efficiently eliminate vast geographic areas from the search without scanning individual coordinates, enabling ultra-fast radius queries.",
 ["Must implement a Spatial Index (e.g., GiST in PostgreSQL/PostGIS)", "Uses advanced data structures like R-Trees (Region Trees) or Geohashes", "Divides 2D space into bounding boxes to eliminate vast geographic areas efficiently"],
 ["Use a B-Tree but sort it alphabetically by city name"]),

("QUERY_PERFORMANCE_AND_INDEXING", "tradeoff", "medium", "tradeoff", ["Partial Indexes", "Cardinality"],
 "A table has a boolean `is_active` column (95% `true`, 5% `false`). What is the tradeoff of creating a standard B-Tree index on `is_active`?",
 "Indexing a low-cardinality column is an anti-pattern. Querying `WHERE is_active = true` forces the planner to ignore the index entirely because sequentially scanning the table is vastly faster than reading the index and doing random heap lookups for 95% of the rows. The index degrades write performance while providing zero read benefit. You should create a 'Partial Index' (`WHERE is_active = false`).",
 ["The index is useless for `true` queries because sequential scans are faster than 95% random heap lookups", "Standard index degrades write performance while providing zero read benefit for the majority value", "Fix: Create a 'Partial Index' targeting only the rare 5% `false` values"],
 ["Booleans cannot be stored in B-Trees because they are not numbers"]),

("QUERY_PERFORMANCE_AND_INDEXING", "scenario", "hard", "scenario", ["MVCC", "Table Bloat"],
 "A PostgreSQL database suffers extreme I/O degradation. The DB size on disk is 500GB, but a full logical dump is only 50GB. The query planner makes terrible choices. What maintenance failure caused this, and what process fixes it?",
 "This is massive 'Table Bloat' and stale statistics. Because PostgreSQL uses MVCC, `UPDATE`/`DELETE` operations do not remove old data; they create new rows and mark old ones invisible. If Auto-vacuum is misconfigured or fails, these 'dead tuples' accumulate endlessly, bloating the table and corrupting statistics. Fix: Run `VACUUM FULL` (locks table) or use `pg_repack` (online).",
 ["Caused by massive 'Table Bloat' and accumulation of 'dead tuples'", "PostgreSQL MVCC does not delete old rows; it marks them invisible", "Auto-vacuum failed to clean up. Fix: Run `VACUUM FULL` or `pg_repack` to reclaim physical disk space"],
 ["The database was hacked and filled with malware"]),

("QUERY_PERFORMANCE_AND_INDEXING", "explain", "medium", "concept", ["Execution Plans", "Hash Joins"],
 "What is a 'Hash Join' in an execution plan, and when does the database optimizer choose it over a 'Nested Loop Join'?",
 "A Hash Join is an algorithm where the DB takes the smaller table, scans it, and builds an in-memory hash table using the join key. It then scans the larger table, probing the hash table for matches. The optimizer chooses Hash Joins for large, unsorted datasets where equality (`=`) is used. It avoids the catastrophic O(N*M) time complexity of a Nested Loop Join (which is only for tiny tables).",
 ["Builds an in-memory hash table from the smaller table, then probes it with the larger table", "Chosen for joining large, unsorted datasets using equality (`=`)", "Avoids the catastrophic O(N*M) time complexity of a Nested Loop Join"],
 ["It hashes the passwords before joining them for security"]),

("QUERY_PERFORMANCE_AND_INDEXING", "debug", "medium", "debugging", ["LIKE", "Indexes"],
 "You execute `SELECT * FROM logs WHERE created_at LIKE '%2023%'`. `created_at` (text) has a B-Tree index. The query takes 30s and performs a full sequential scan. Why did the `LIKE` operator defeat the index?",
 "A B-Tree index is sorted alphanumerically. It can only be used for prefix matching (`LIKE '2023%'`). Because your query uses a leading wildcard (`%2023`), the database cannot know where in the sorted B-Tree to start searching; the substring could be anywhere. Therefore, it is forced to scan every single row. You need a Trigram (`pg_trgm`) index or full-text search.",
 ["B-Tree indexes can only optimize prefix matches (`LIKE '2023%'`)", "A leading wildcard (`%2023`) destroys the ability to traverse the sorted tree", "Forces a full sequential scan. Fix: Use a Trigram index (`pg_trgm`)"],
 ["The percent sign is illegal in SQL queries"]),

("QUERY_PERFORMANCE_AND_INDEXING", "implement", "easy", "implementation", ["Pagination", "Cursor Pagination"],
 "A query `SELECT * FROM logs ORDER BY created_at DESC LIMIT 10 OFFSET 5000000;` takes 15 seconds. How do you implement a more performant pagination architecture?",
 "Replace `OFFSET/LIMIT` with 'Keyset Pagination' (or 'Cursor Pagination'). `OFFSET 5M` forces the DB to compute, sort, and discard the first 5 million rows. Keyset pagination uses the last seen value: `WHERE created_at < 'last_seen_date' ORDER BY created_at DESC LIMIT 10;`. This allows the DB to instantly jump to the exact location using the B-Tree index.",
 ["`OFFSET` is O(N) because the DB must physically fetch and discard all skipped rows", "Implement 'Keyset Pagination' (Cursor Pagination)", "Filter by the last seen value (`WHERE col < last_val`) to instantly jump via the index"],
 ["Ask the user to not click to page 500,000"]),

("QUERY_PERFORMANCE_AND_INDEXING", "tradeoff", "hard", "tradeoff", ["Memory Management", "Buffer Pool"],
 "When tuning a database, what is the architectural tradeoff of increasing the 'Shared Buffers' (or InnoDB Buffer Pool) to consume 90% of the server's physical RAM?",
 "While maximizing the buffer pool drastically reduces disk I/O for DB reads, setting it too high (90%) starves the underlying OS of memory. The OS needs RAM for its own filesystem cache, network buffers, and background processes. If the OS runs out of memory, it triggers aggressive disk swapping (thrashing) or the OOM Killer terminates the database instantly. (Best practice: 50-70%).",
 ["Maximizes cached DB pages in RAM, minimizing disk I/O", "Tradeoff: Starves the OS of memory needed for filesystem caching and networking", "Risk: Causes severe disk swapping (thrashing) or triggers the Linux OOM Killer to crash the DB"],
 ["It makes the RAM run too hot and melts the motherboard"]),

("QUERY_PERFORMANCE_AND_INDEXING", "scenario", "medium", "scenario", ["Mass Deletions", "Operations"],
 "An app executes `DELETE FROM logs WHERE age > 30` (50 million rows). It runs for 2 hours, bloats the WAL, blocks queries, and crashes. What is the standard engineering pattern to handle mass deletions?",
 "You must never perform mass deletions in a single transaction; it causes massive WAL bloat, locking, and rollback overhead. The pattern is to 'chunk' or 'batch' deletes: loop a query with a `LIMIT 5000` and commit frequently. Alternatively, if deleting the majority of a table, use Table Partitioning (by date) and simply `DROP PARTITION`, which is an instant metadata operation.",
 ["Never perform mass deletions in a single transaction (causes WAL bloat and locking)", "Fix 1: 'Chunk' or 'Batch' the deletions in small loops (`LIMIT 5000`) and commit frequently", "Fix 2: Use Table Partitioning by date and `DROP PARTITION` (instant metadata operation)"],
 ["Just pull the power plug on the server to stop it"]),

("QUERY_PERFORMANCE_AND_INDEXING", "explain", "hard", "concept", ["Execution Plans", "Bitmap Index Scan"],
 "What does it mean when an Execution Plan states it is doing an 'Index Scan' versus a 'Bitmap Index Scan'?",
 "An 'Index Scan' reads the index and immediately fetches the corresponding row from the heap, one by one. A 'Bitmap Index Scan' reads the index, builds an in-memory bitmap of the exact memory pages containing matches, sorts the bitmap, and *then* fetches the heap pages sequentially. This prevents random disk I/O and reading the same page twice, vastly improving large-result queries.",
 ["Index Scan: Fetches rows from the heap one-by-one as it reads the index", "Bitmap Index Scan: Builds an in-memory bitmap of matching memory pages first", "Sorts the bitmap to fetch heap pages sequentially, drastically reducing random disk I/O"],
 ["A Bitmap Scan creates a JPEG image of the query results"]),

("QUERY_PERFORMANCE_AND_INDEXING", "debug", "medium", "debugging", ["Sorting", "work_mem"],
 "A query `ORDER BY price DESC` fails with `Sort aborted: out of sort memory`. You already have an index on `price`. Why is it failing, and what configuration can you change?",
 "The database could not use the index for sorting (due to mismatched sort direction or filtering logic) and attempted an 'In-Memory Sort'. The sorted data exceeded the allocated `work_mem` (or `sort_buffer_size`), forcing the DB to spill to temporary disk files, which ran out of space. Fix: Increase the session-level `work_mem` or ensure an index perfectly matches the `ORDER BY`.",
 ["The DB could not use the index and attempted an 'In-Memory Sort'", "The dataset exceeded the configured `work_mem`, forcing a spill to temporary disk files", "Fix: Increase session-level `work_mem` or fix the index to perfectly match the sort direction"],
 ["The database forgot how to alphabetize numbers"]),

("QUERY_PERFORMANCE_AND_INDEXING", "implement", "hard", "implementation", ["Concurrency", "SKIP LOCKED"],
 "A queue query `SELECT * FROM q WHERE status='NEW' ORDER BY date LIMIT 10` causes severe lock contention as multiple workers select and lock the exact same 10 rows. How do you implement this cleanly in modern SQL?",
 "Implement the `SKIP LOCKED` clause: `... FOR UPDATE SKIP LOCKED`. This instructs the database to acquire row-level locks on the returned rows, but if it encounters a row *already* locked by another worker, it skips it and moves to the next oldest row. This completely eliminates lock contention and allows perfect parallel queue processing at the database layer.",
 ["Use the `FOR UPDATE SKIP LOCKED` clause", "If a row is already locked by another worker, the DB instantly skips it instead of blocking", "Eliminates lock contention and enables high-throughput parallel queue processing"],
 ["Use `FOR UPDATE IGNORE ERRORS`"])
]
