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

ROLE = "Database Developer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Query Planner / Optimizer & PostgreSQL Internals
    ("B66_1_1", "diagnose", "hard", "debugging", ["Query Optimization", "PostgreSQL Internals"],
     "A complex PostgreSQL reporting query suddenly takes 40 seconds instead of 1 second after a minor application release. EXPLAIN ANALYZE reveals that the query planner selected a Nested Loop Join over a Hash Join, but the actual rows returned by the outer scan were 5 million instead of the estimated 10 rows. What causes this catastrophic cardinality misestimation, and how do you resolve it?",
     "Cardinality misestimation often occurs when the planner relies on stale statistics, or when the query filters on multiple correlated columns (e.g., WHERE city = 'San Francisco' AND state = 'CA'). By default, the planner assumes column probabilities are independent and multiplies their selectivity, resulting in a massive underestimation of the actual row count. Because the planner expects only 10 rows, it chooses a Nested Loop Join (which is O(N*M) and disastrous for 5 million rows) rather than a Hash Join. Resolution: 1) Run ANALYZE on the table to update stale histograms; 2) For correlated columns, create extended statistics using CREATE STATISTICS stat_name (dependencies) ON city, state FROM table_name; allowing the planner to understand the correlation and choose the correct Hash Join plan.",
     ["Identifies stale statistics or correlated column filters as root cause", "Explains that underestimated rows cause the optimizer to favor Nested Loops over Hash Joins", "Prescribes running ANALYZE or creating extended statistics (CREATE STATISTICS)"],
     ["Suggests rewriting the query using subqueries to force execution order"]),

    ("B66_1_2", "concept", "medium", "concept", ["Query Optimization", "Database Architecture"],
     "Explain the architectural differences and optimal use cases for Nested Loop, Hash, and Merge join algorithms in a relational database engine.",
     "1) Nested Loop Join iterates through each row of the outer table and performs an index lookup on the inner table. It has minimal startup cost and is extremely fast when the outer result set is small (few rows) and the inner table is indexed. 2) Hash Join scans the smaller table to build an in-memory hash table, then scans the larger table, probing the hash table for matches. It requires high startup time and memory allocation (work_mem) but is exceptionally efficient for large, unindexed equijoins. 3) Merge Join requires both inputs to be sorted on the join key (either via an existing B-tree index scan or an explicit sort phase). It then streams both sorted sets simultaneously. It is optimal when inputs are already sorted or when dealing with massive datasets that exceed memory limits, as it spills gracefully to disk.",
     ["Defines Nested Loop as outer iteration with inner index lookup (optimal for small sets)", "Defines Hash Join as building in-memory hash tables (optimal for large unindexed equijoins)", "Defines Merge Join as simultaneous streaming of pre-sorted data (optimal for large memory-bound sets)"],
     ["Claims Hash Joins only work if the database uses a NoSQL storage engine"]),

    ("B66_1_3", "scenario", "hard", "scenario", ["Query Optimization", "Database Operations"],
     "In SQL Server or PostgreSQL, a stored procedure or prepared statement executes in 50ms for 99% of requests. However, when a specific customer ID is passed, the query times out after 30 seconds. If that customer's query is run dynamically (not as a prepared statement), it completes in 50ms. What is 'Parameter Sniffing' (or Parameter-Sensitive Plans), and how do you mitigate it?",
     "Parameter Sniffing occurs when the database optimizer compiles a query execution plan on the very first execution of a prepared statement and caches it. If the first execution uses a parameter with extremely high selectivity (e.g., a customer with 5 orders), the optimizer might cache a Nested Loop / Index Scan plan. When a subsequent execution passes a parameter with terrible selectivity (e.g., a massive enterprise customer with 5 million orders), the database reuses the cached Nested Loop plan, which causes catastrophic performance. Mitigation: 1) Recompile the query per execution (e.g., OPTION (RECOMPILE) in SQL Server); 2) Optimize for unknown parameters to force a generic, balanced plan (e.g., Hash Join); 3) Manually partition the application logic so massive customers use a different query signature than small customers, yielding two separate cached plans.",
     ["Defines Parameter Sniffing as caching an execution plan optimized for the first parameter value provided", "Explains catastrophic failure when a cached high-selectivity plan is used for low-selectivity data", "Recommends recompilation flags or application-level query partitioning"],
     ["Claims Parameter Sniffing is a network packet inspection security vulnerability"]),

    ("B66_1_4", "tradeoff", "medium", "tradeoff", ["Indexing", "Query Optimization"],
     "When designing a composite B-tree index on (tenant_id, created_at, status), what is the architectural tradeoff of column ordering, and how does it impact Range Scans versus Equality predicates?",
     "B-tree composite indexes sort data hierarchically left-to-right. The rule of thumb is to place equality predicates (=, IN) before range predicates (>, <, BETWEEN). If the index is (tenant_id, created_at, status), a query WHERE tenant_id = 5 AND created_at > '2023-01-01' AND status = 'ACTIVE' will traverse the B-tree to find the specific tenant, then scan all leaf nodes matching the date range. However, because the range column (created_at) appears before the equality column (status), the index cannot jump directly to 'ACTIVE' statuses; it must scan every index tuple within the date range and filter out non-active statuses (Index Condition Pushdown). Swapping the index to (tenant_id, status, created_at) allows the engine to jump directly to the exact subset of active records for the tenant, drastically reducing the number of index pages read.",
     ["Explains left-to-right hierarchical sorting of B-tree composite indexes", "Articulates the rule of placing equality predicates before range predicates", "Demonstrates how range columns block subsequent columns from participating in tree traversal jumping"],
     ["Claims column order does not matter in modern databases because the optimizer rearranges them"]),

    ("B66_1_5", "concept", "easy", "concept", ["Indexing", "Query Optimization"],
     "What is a 'Covering Index' (or Index-Only Scan), and how does it eliminate the need for table heap lookups?",
     "A query requires a table heap lookup when it selects or filters columns that are not stored in the index structure. An index 'covers' a query when every single column referenced in the SELECT, WHERE, JOIN, and ORDER BY clauses is present in the index. When this happens, the database optimizer can perform an 'Index-Only Scan'. It reads the data directly from the index leaf nodes and completely skips fetching the actual table row from disk. In PostgreSQL, this is facilitated by the INCLUDE clause (CREATE INDEX idx ON table (col1) INCLUDE (col2, col3)), which stores non-key payload data in the leaf nodes, avoiding heap fetches and massively reducing disk I/O for read-heavy queries.",
     ["Defines a covering index as containing all columns required by the query", "Explains Index-Only Scan bypassing the actual table heap retrieval", "Mentions the INCLUDE clause storing payload data without expanding the B-tree search keys"],
     ["Claims covering indexes encrypt data to prevent unauthorized access"]),

    ("B66_1_6", "implement", "medium", "implement", ["Indexing", "PostgreSQL Internals"],
     "You have a users table with 10 million rows, but only 50,000 users are currently active (status = 'ACTIVE'). Queries frequently filter by active users. How do you use a Partial Index to optimize disk space and query performance?",
     "You create a Partial Index by adding a WHERE clause to the index definition: CREATE INDEX idx_active_users ON users(email) WHERE status = 'ACTIVE';. This instructs the database to only add index entries for rows where the status is active. The tradeoffs and benefits are massive: 1) The index size is a tiny fraction of a full index, saving disk space and memory in the buffer pool; 2) Index maintenance overhead (inserts/updates on inactive users) is completely eliminated; 3) The query planner will automatically use this tiny, highly cached index for any query that includes WHERE status = 'ACTIVE' AND email = ?.",
     ["Implements partial index using WHERE clause in CREATE INDEX", "Highlights dramatic reduction in disk footprint and buffer pool usage", "Highlights elimination of maintenance overhead on inactive row mutations"],
     ["Creates a partitioned table instead of a partial index"]),

    ("B66_1_7", "diagnose", "medium", "debugging", ["PostgreSQL Internals", "Database Operations"],
     "In PostgreSQL, updating a row physically creates a brand new row version (tuple) due to MVCC. This typically requires updating all indexes to point to the new tuple. How does the HOT (Heap-Only Tuple) update optimization prevent index write amplification, and why might it fail to trigger?",
     "HOT (Heap-Only Tuple) optimization occurs when an UPDATE does not modify any columns that are part of an index, and there is sufficient free space on the exact same database page (block) to store the new row version. When HOT triggers, PostgreSQL links the old tuple to the new tuple on the same page. Because the physical location of the logical row on the page hasn't changed from the index's perspective, PostgreSQL completely skips updating all the table's indexes, drastically reducing write amplification and WAL generation. HOT fails to trigger if: 1) An indexed column is modified; or 2) The page's fillfactor is 100% and there is no free space left on the block, forcing the new tuple onto a different page and requiring full index updates.",
     ["Defines HOT update skipping index pointer updates when row remains on the same page", "Identifies requirement 1: No indexed columns are modified", "Identifies requirement 2: Free space on the page (fillfactor tuning)"],
     ["Claims HOT updates happen in system memory before committing to disk"]),

    ("B66_1_8", "concept", "hard", "concept", ["PostgreSQL Internals", "Transactions"],
     "What is 'Transaction ID (XID) Wraparound' in PostgreSQL, what catastrophic failure does it cause, and how does the FREEZE process prevent it?",
     "PostgreSQL uses 32-bit transaction IDs to implement MVCC visibility. Because 32 bits limit the database to 4 billion transactions, XIDs must wrap around. PostgreSQL handles this by treating the XID space as a circular buffer: any XID in the past 2 billion is visible, and any in the future 2 billion is invisible. If a database processes 2 billion transactions without maintenance, old rows suddenly appear to be in the 'future' and vanish from all queries, destroying data visibility. To prevent this, autovacuum runs a FREEZE operation: it scans old tuples and replaces their XID with a special FrozenTransactionId (or sets a freeze bit). Frozen tuples are considered unconditionally visible to all future transactions, safely allowing the global XID counter to wrap around without causing data loss.",
     ["Explains 32-bit transaction ID limits and circular buffer logic", "Describes catastrophic failure where past data becomes 'invisible' future data", "Explains autovacuum FREEZE mechanism making tuples unconditionally visible"],
     ["Claims XID wraparound corrupts the primary key sequences on tables"]),

    ("B66_1_9", "scenario", "hard", "scenario", ["PostgreSQL Internals", "Database Operations"],
     "A high-throughput PostgreSQL database experiences sudden, severe I/O spikes every 15 minutes, causing query latency to jump from 5ms to 500ms. You notice the spikes correlate exactly with database Checkpoints. What are 'Full-Page Writes' during a checkpoint, and how do you tune checkpoint parameters to smooth the I/O spikes?",
     "Checkpoints flush dirty buffers from memory to disk. To prevent page corruption in the event of a crash during a write, PostgreSQL writes the entire 8KB page to the Write-Ahead Log (WAL) the very first time that page is modified after a checkpoint (Full-Page Writes). This causes massive I/O bursts immediately following a checkpoint. If checkpoints occur too frequently (every 15 mins), the database spends most of its time doing full-page writes. To smooth out I/O: 1) Increase max_wal_size to allow more WAL generation between checkpoints; 2) Increase checkpoint_timeout (e.g., to 30 or 60 minutes) to reduce checkpoint frequency; 3) Increase checkpoint_completion_target (e.g., to 0.9) to instruct the checkpointer process to spread out the dirty buffer flushing slowly over the duration of the checkpoint interval, rather than flushing them all in a massive panic spike.",
     ["Identifies Full-Page Writes into WAL as the source of post-checkpoint I/O spikes", "Suggests increasing max_wal_size and checkpoint_timeout to reduce frequency", "Suggests increasing checkpoint_completion_target to smooth dirty buffer flushing"],
     ["Recommends disabling the WAL entirely to improve write speed"]),

    ("B66_1_10", "tradeoff", "medium", "tradeoff", ["PostgreSQL Internals", "Storage Engines"],
     "What are the architectural tradeoffs of PostgreSQL's TOAST (The Oversized-Attribute Storage Technique) mechanism when storing large JSONB documents or text blobs in a relational table?",
     "PostgreSQL pages are strictly 8KB. When a row exceeds this limit (usually around 2KB threshold), PostgreSQL transparently compresses and moves large variable-length fields (like JSONB or TEXT) into a separate, hidden TOAST table, storing only a small pointer in the main table row. Tradeoff Advantages: The main table remains physically dense, allowing sequential scans and index operations to fit significantly more rows per 8KB page in the buffer cache, improving performance for queries that do not select the TOASTed column. Tradeoff Disadvantages: If a query SELECTs the TOASTed JSONB column, PostgreSQL must perform random I/O to fetch the chunked data from the TOAST table and decompress it on the CPU, causing severe read amplification and CPU spikes.",
     ["Explains out-of-line storage for rows exceeding 8KB page limits", "Identifies advantage: dense primary table maximizing buffer cache efficiency for index/sequential scans", "Identifies disadvantage: random I/O and CPU decompression penalty when selecting the TOASTed column"],
     ["Claims TOAST replicates data to secondary disks for disaster recovery"]),

    ("B66_1_11", "diagnose", "medium", "debugging", ["PostgreSQL Internals", "Replication"],
     "The primary PostgreSQL database suddenly runs out of disk space. Investigation shows the pg_wal (Write-Ahead Log) directory has accumulated hundreds of gigabytes of WAL files. You discover an abandoned logical replication slot. Why do replication slots prevent WAL recycling, and how do you fix it safely?",
     "A replication slot guarantees that the primary database will not delete WAL files until the connected replica has explicitly consumed and acknowledged them. If a replica crashes, disconnects permanently, or falls hopelessly behind, the replication slot remains active. To fulfill the slot's guarantee, the primary hoards WAL files indefinitely, eventually filling the entire disk and crashing the primary database. To fix it: identify the abandoned slot via SELECT slot_name, active FROM pg_replication_slots;. If active is false and it is abandoned, drop it using SELECT pg_drop_replication_slot('slot_name');. The primary will immediately recycle the accumulated WAL files. To prevent recurrence, configure max_slot_wal_keep_size (PostgreSQL 13+) to enforce a hard limit on how much WAL a slot can retain before it is automatically invalidated.",
     ["Explains replication slot guarantees hoarding WAL files for disconnected replicas", "Prescribes querying pg_replication_slots and executing pg_drop_replication_slot", "Suggests max_slot_wal_keep_size constraint to prevent future unbounded disk consumption"],
     ["Recommends deleting files directly from the pg_wal directory using the Linux rm command"]),

    ("B66_1_12", "concept", "easy", "concept", ["PostgreSQL Internals", "Database Operations"],
     "In PostgreSQL MVCC, what is 'Table Bloat', and why does a standard DELETE query not instantly reclaim disk space?",
     "PostgreSQL uses Multi-Version Concurrency Control (MVCC). When a row is DELETEd (or UPDATEd), the database does not physically erase the row from the disk. Instead, it marks the row as 'dead' (setting the xmax transaction ID) so concurrent transactions can still read the old version if their snapshot requires it. Over time, these dead tuples accumulate, causing 'Table Bloat'. Disk space is not returned to the operating system. Instead, the autovacuum daemon periodically scans the table in the background, marks the dead tuples as available free space, and records them in the Free Space Map (FSM) so future INSERTs can overwrite those slots. To actually return space to the OS, a blocking VACUUM FULL (which rewrites the entire table) is required.",
     ["Explains MVCC creating dead tuples on UPDATE/DELETE instead of physical erasure", "Describes autovacuum reclaiming space for future inserts via the Free Space Map", "Differentiates standard VACUUM from VACUUM FULL returning space to the OS"],
     ["Claims DELETE writes zeros to the disk immediately but leaves the file size unchanged"]),

    ("B66_1_13", "scenario", "medium", "scenario", ["PostgreSQL Internals", "Database Operations"],
     "You notice that autovacuum is running on a heavily updated table, but dead tuples are not being removed, and table bloat continues to grow. You check pg_stat_activity and find a developer left an idle psql session open with a query 'BEGIN; SELECT * FROM users;' from 3 days ago. Why does this block autovacuum?",
     "Autovacuum can only remove dead tuples if it is mathematically certain that NO active transaction in the entire database could possibly need to read them. A transaction snapshot is established when the SELECT query runs. Because the developer's transaction has been open for 3 days (an Idle in Transaction state), its snapshot is 3 days old. PostgreSQL must retain every single row version (dead tuple) deleted or updated system-wide over the last 3 days just in case that idle transaction decides to query them. This entirely paralyzes autovacuum's ability to clean up bloat. Resolution: kill the idle transaction using pg_terminate_backend(pid), and prevent recurrence by setting the idle_in_transaction_session_timeout parameter to automatically kill abandoned sessions.",
     ["Identifies Idle in Transaction holding an ancient MVCC snapshot horizon", "Explains that autovacuum cannot purge tuples newer than the oldest active snapshot", "Recommends pg_terminate_backend and configuring idle_in_transaction_session_timeout"],
     ["Claims autovacuum paused because the table exceeded the maximum size limit"]),

    ("B66_1_14", "implement", "hard", "implement", ["Query Optimization", "Indexing"],
     "How do you use an Expression Index (Function-Based Index) in PostgreSQL to optimize case-insensitive searches and prevent the query planner from bypassing the index?",
     "Standard B-tree indexes are sensitive to exact byte-for-byte equality. If you have an index on email, a query using WHERE lower(email) = 'user@example.com' will perform a full sequential table scan because the function lower() alters the value, rendering the standard index unusable (Non-Sargable query). To optimize this, you implement an Expression Index: CREATE INDEX idx_lower_email ON users (lower(email));. The database evaluates the function during INSERT/UPDATE and stores the resulting lowercase string directly in the B-tree. The query planner will now perfectly match the lower(email) predicate to the expression index, resulting in a lightning-fast Index Scan.",
     ["Identifies functions breaking standard B-tree index usage (Non-Sargable)", "Provides exact syntax: CREATE INDEX idx ON table (func(col))", "Explains pre-computing the function output and storing it directly in the B-tree leaf nodes"],
     ["Recommends adding a trigger to convert all text to lowercase before inserting"]),

    ("B66_1_15", "concept", "easy", "concept", ["PostgreSQL Internals", "Database Architecture"],
     "What is the 'Visibility Map' in PostgreSQL, and how does it optimize Index-Only Scans?",
     "The Visibility Map is a small, highly cached bitmap data structure that tracks which data blocks (pages) in a table contain ONLY rows that are unconditionally visible to all active transactions (i.e., pages with no dead tuples or uncommitted rows). In MVCC, index leaf nodes do not store transaction visibility information. When the database performs an Index-Only Scan, it usually still has to fetch the table heap page to check if the row is visible to the current transaction. However, if the Visibility Map indicates that the target page is 100% visible, PostgreSQL completely skips the heap fetch, delivering the true performance benefit of an Index-Only Scan.",
     ["Defines Visibility Map as a bitmap tracking pages with 100% visible tuples", "Explains that indexes do not store MVCC visibility data", "Explains that the Visibility Map allows Index-Only Scans to bypass the heap page fetch entirely"],
     ["Claims the Visibility Map hides tables from unauthorized users"]),

    ("B66_1_16", "diagnose", "medium", "debugging", ["Query Optimization", "Performance & Tuning"],
     "An analytics query performs a GROUP BY and ORDER BY on a dataset of 2 million rows. Execution time degrades severely, and the EXPLAIN plan shows 'External merge Disk: 500MB'. What configuration parameter is undersized, and how do you tune it safely?",
     "The query requires sorting and hashing 2 million rows. The database allocates a fixed amount of memory per query operation (e.g., a sort or hash node), controlled in PostgreSQL by work_mem (default is often a tiny 4MB). When the data volume exceeds work_mem, the database engine spills the sort operation to disk, creating temporary files and using an 'External merge' sort algorithm. Disk I/O is orders of magnitude slower than RAM. To fix this, you increase work_mem for the specific session or user executing the analytics query (e.g., SET work_mem = '1GB';). It should not be set globally to a massive value, because work_mem can be allocated multiple times per query (e.g., for multiple hash joins) and per concurrent connection, which could easily cause an Out-Of-Memory (OOM) crash on the database server.",
     ["Identifies work_mem exhaustion causing disk-spill sorting (External merge Disk)", "Explains the extreme latency penalty of disk-based sorting vs in-memory Quicksort", "Warns against massive global work_mem sizing to avoid OOM due to per-node multiplier limits"],
     ["Recommends increasing shared_buffers to fix query sorting performance"]),

    ("B66_1_17", "tradeoff", "medium", "tradeoff", ["PostgreSQL Internals", "Storage Engines"],
     "What is the tradeoff between configuring PostgreSQL synchronous_commit to 'on' versus 'off' for write-heavy workloads?",
     "When synchronous_commit = on (default), the database guarantees that the transaction's Write-Ahead Log (WAL) records are safely flushed to physical disk (fsync) before returning a success acknowledgment to the client application. Tradeoff: Provides strict ACID Durability and guarantees zero data loss on a crash, but incurs severe I/O latency, limiting throughput to the IOPS capacity of the disk. Setting synchronous_commit = off allows the database to return success immediately after writing WAL to memory buffers, deferring the physical disk flush to a background writer thread. Tradeoff: Massive increase in write throughput and reduced latency, but sacrifices strict Durability. If the OS crashes or loses power within the flush window (typically 3 * wal_writer_delay, roughly 600ms), successfully acknowledged transactions will be lost.",
     ["Contrasts synchronous disk fsyncing with deferred memory buffer flushing", "Identifies zero data loss guarantee vs disk I/O latency throughput bottleneck", "Identifies data loss window (e.g., 600ms) on OS crash when synchronous_commit is off"],
     ["Claims synchronous_commit forces replicas to acknowledge writes before committing"]),

    ("B66_1_18", "scenario", "medium", "scenario", ["Query Optimization", "Execution Plans"],
     "A developer complains that adding a LIMIT 1 to a fast query makes it take 10 seconds. The query joins a large orders table with a users table, ordered by orders.created_at. Why does the query planner choose a disastrous plan when a LIMIT is introduced?",
     "Without the LIMIT, the planner might choose to use a Hash Join to process the entire dataset quickly, and then sort the final result. When LIMIT 1 is introduced, the planner attempts a 'Fast-Start' optimization. It switches to a Nested Loop scan using an index on orders.created_at. It assumes it can scan the index in order, look up the user, and immediately abort after finding the first match. However, if the WHERE clause has a highly restrictive filter on users (e.g., users.status = 'BANNED'), the database might have to scan millions of recent orders sequentially, performing millions of index lookups, before it finally finds a banned user. The assumption that it would find a match quickly fails catastrophically.",
     ["Identifies 'Fast-Start' planner optimization bias caused by LIMIT clauses", "Explains switch from Hash Join to ordered Index Scan / Nested Loops", "Explains catastrophic failure when the sequential scan encounters highly restrictive filters before finding a match"],
     ["Claims LIMIT 1 causes the database to lock the entire table"]),

    ("B66_1_19", "implement", "hard", "implement", ["Query Optimization", "Indexing"],
     "How do you implement and utilize a Block Range Index (BRIN) in PostgreSQL, and in what specific architectural scenario does it outperform a standard B-tree index?",
     "A BRIN index is created via CREATE INDEX idx_brin ON events USING brin (created_at);. BRIN indexes do not store every row. Instead, they store the minimum and maximum values of a column for contiguous ranges of physical data blocks (e.g., every 128 pages). During a query, the planner checks the BRIN index; if the queried value falls outside the min/max range of a block group, it skips those blocks entirely. BRIN outperforms B-trees on massive, append-only time-series tables (like IoT telemetry or audit logs) where the indexed column (e.g., created_at) is naturally perfectly correlated with its physical insertion order on disk. The tradeoff is that BRIN is a lossy index—it narrows the search down to a few blocks, which must then be sequentially scanned—but its memory footprint is less than 1% of a B-tree, and its insertion overhead is virtually zero.",
     ["Explains BRIN tracking min/max boundaries across physical block ranges", "Identifies massive append-only time-series data with natural physical correlation as the optimal use case", "Highlights tiny memory footprint and insertion speed vs lossy block-scanning tradeoff"],
     ["Claims BRIN indexes are used to enforce primary key uniqueness across shards"]),

    ("B66_1_20", "diagnose", "medium", "debugging", ["Query Optimization", "Database Operations"],
     "You deploy an online DDL migration CREATE INDEX CONCURRENTLY idx_status ON orders(status); in PostgreSQL. The command hangs for hours and blocks subsequent table migrations. What lock conflicts occur during concurrent index creation, and how do you diagnose the blocking transaction?",
     "Unlike standard CREATE INDEX, which acquires an exclusive lock and blocks all writes, CREATE INDEX CONCURRENTLY (CIC) avoids blocking writes by running in multiple phases and acquiring a ShareUpdateExclusiveLock. However, CIC must wait for all existing transactions that could potentially modify or read the table to finish before it can scan the table and validate the index. If there is a long-running transaction (even a SELECT in another session) that started before the CIC command, the CIC process will hang in a Lock:relation wait event. Furthermore, because CIC holds a ShareUpdateExclusiveLock, it will queue up and block any subsequent DDL or vacuum operations on the table. To diagnose, query pg_stat_activity and pg_locks to find sessions holding locks on the target relation that have an older backend_start or xact_start timestamp than the CIC process.",
     ["Explains ShareUpdateExclusiveLock allowing concurrent writes but waiting for active transactions", "Identifies older long-running transactions (even SELECTs) as the blocking root cause", "Recommends querying pg_stat_activity and pg_locks to identify older transaction PIDs"],
     ["Suggests that concurrent indexes block because the disk is full"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 1).")
    
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
    print("POST-BATCH AUDIT PART 1")
    print("========================================")
    print(f"Batch: 66 Part 1")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
