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
    ("B66_2_1", "concept", "hard", "concept", ["Transactions", "PostgreSQL Internals"],
     "Explain the 'Write Skew' anomaly in concurrent transactions, and why standard REPEATABLE READ isolation fails to prevent it. How does Serializable Snapshot Isolation (SSI) resolve this?",
     "Write Skew occurs when two concurrent transactions each read overlapping datasets, make a decision based on the reads, and then modify disjoint rows within that dataset in a way that violates a business constraint (e.g., two doctors both withdrawing from on-call duty simultaneously because they each saw the other was still on-call). Standard REPEATABLE READ isolation prevents phantom reads and non-repeatable reads by ensuring consistent snapshots, but it only checks for write-write conflicts on the *same exact row*. Since Write Skew involves writing to *different* rows based on the same read, REPEATABLE READ allows it. Serializable Snapshot Isolation (SSI) prevents Write Skew by tracking read/write dependencies (SIREAD locks) globally across transactions and aborting one of the transactions if a cycle (read-write dependency anomaly) is detected.",
     ["Defines Write Skew as transactions reading overlapping sets but writing to different rows, violating global constraints", "Explains REPEATABLE READ only blocks concurrent updates to the exact same physical row", "Explains SSI tracking global read-write dependencies to detect and abort cycles"],
     ["Confuses Write Skew with Dirty Reads or Phantom Reads"]),

    ("B66_2_2", "diagnose", "medium", "debugging", ["Database Operations", "Storage Engines"],
     "You observe a severe database latency spike every time an application runs a massive bulk INSERT. The IOPS on the primary database disk completely flatlines at maximum capacity. How do you redesign the INSERT operation to reduce disk I/O and write amplification?",
     "Massive row-by-row INSERT operations or un-batched INSERT statements cause extreme write amplification and locking overhead. Each insert requires WAL (Write-Ahead Log) writes, index tree traversal/splitting, and commit fsyncs. To optimize: 1) Batch the inserts using a single INSERT INTO table VALUES (...), (...), (...) or COPY command. 2) If the table has many indexes, drop the indexes before the bulk load, perform the massive insert, and then recreate the indexes (which sequentially scans and builds them in memory, avoiding random tree traversal). 3) If acceptable, use UNLOGGED tables (in PostgreSQL) to bypass WAL entirely during the staging phase. 4) Ensure transactions are properly sized—wrapping 10,000 inserts in a single transaction avoids 10,000 individual fsync calls to the disk.",
     ["Identifies row-by-row inserts causing excessive fsyncs, WAL writes, and random index I/O", "Recommends batched multi-row inserts or COPY commands", "Suggests dropping and recreating indexes for massive bulk loads to avoid B-tree fragmentation"],
     ["Recommends increasing disk swap space or adding more database CPU"]),

    ("B66_2_3", "scenario", "medium", "scenario", ["Concurrency", "Transactions"],
     "An e-commerce application implements an inventory system where multiple users can attempt to purchase the exact same item. When items are low in stock, users experience severe latency and deadlocks. The query is 'SELECT stock FROM inventory WHERE item_id = 5 FOR UPDATE;'. Why does this cause bottlenecks, and how do you fix it using SKIP LOCKED?",
     "SELECT ... FOR UPDATE acquires an exclusive row-level lock. When thousands of users try to purchase item_id = 5, the first transaction locks the row, and the remaining 9,999 transactions queue up in the database lock manager, consuming connections and waiting sequentially (Hot-Row Contention). If transactions update multiple items in different orders, Deadlocks frequently occur. By changing the query to SELECT stock FROM inventory WHERE item_id = 5 FOR UPDATE SKIP LOCKED;, the database will immediately skip any rows that are currently locked by other transactions, returning 0 rows to the blocked user instead of hanging their connection. The application can then instantly show the user an 'Out of Stock' or 'Processing' message, rather than exhausting database connection pools and waiting for lock timeouts.",
     ["Identifies FOR UPDATE causing massive lock queuing and connection pool exhaustion (Hot-Row Contention)", "Explains SKIP LOCKED instantly bypassing locked rows rather than blocking", "Connects database mechanics to improved application-level UX and fail-fast resilience"],
     ["Claims SKIP LOCKED ignores data integrity and allows double-spending"]),

    ("B66_2_4", "concept", "easy", "concept", ["Transactions", "Database Internals"],
     "What is a 'Phantom Read' anomaly, and in what transaction isolation level does it typically occur?",
     "A Phantom Read occurs when a transaction executes a query returning a set of rows that satisfy a search condition, and then, before the transaction completes, a second concurrent transaction INSERTs or DELETEs a row that matches the same condition. When the first transaction repeats the identical query, it suddenly sees a 'phantom' row that was not there previously, or a row has disappeared. This anomaly typically occurs in the READ COMMITTED isolation level (and READ UNCOMMITTED). It is prevented by REPEATABLE READ (in PostgreSQL via MVCC snapshotting) or SERIALIZABLE isolation levels.",
     ["Defines Phantom Read as new/deleted rows appearing in identical consecutive queries within a single transaction", "Identifies READ COMMITTED as vulnerable to this anomaly", "Identifies REPEATABLE READ or SERIALIZABLE as preventing this anomaly"],
     ["Confuses Phantom Reads with Dirty Reads (reading uncommitted data)"]),

    ("B66_2_5", "tradeoff", "hard", "tradeoff", ["Storage Engines", "Database Architecture"],
     "Modern SSDs provide massive IOPS, yet a high-throughput PostgreSQL database still struggles with latency during heavy UPDATE workloads. What is 'Write Amplification' at the hardware SSD level, and how does the database Buffer Pool interact with it?",
     "Write Amplification happens because SSDs cannot overwrite a single byte; they must erase and rewrite an entire NAND flash block (e.g., 256KB-4MB) even if only 8KB changed. When PostgreSQL updates a single byte, it writes an 8KB WAL page and an 8KB table page. The SSD controller then amplifies this to rewrite a massive NAND block. The database Buffer Pool (Shared Buffers) mitigates this by keeping 'dirty' 8KB pages in RAM, coalescing thousands of individual row updates into a single 8KB page write to disk during a checkpoint. However, if the Buffer Pool is too small (thrashing) or checkpoints are too frequent, the database continuously flushes pages, triggering massive SSD Write Amplification, rapidly wearing out the SSD and destroying write latency.",
     ["Explains hardware limitations: SSDs erase in large blocks, causing amplification of tiny database writes", "Explains the Buffer Pool coalescing multiple memory updates into a single disk flush", "Correlates small Buffer Pools or rapid checkpoints with SSD thrashing and degradation"],
     ["Claims SSDs are slower than HDDs for database writes due to mechanical seek times"]),

    ("B66_2_6", "implement", "medium", "implement", ["Concurrency", "Database Architecture"],
     "How do you implement Distributed Locks across an application cluster using PostgreSQL Advisory Locks, and why are they superior to table/row locks for this purpose?",
     "PostgreSQL Advisory Locks are application-defined locks that the database manages, but they have no connection to actual tables or rows. You implement them using functions like pg_try_advisory_lock(key_id). If an application node wants to run a singleton cron job or process a specific queue task, it requests the lock using a unique integer key. Why they are superior: 1) They don't block table reads/writes or cause row-level contention. 2) They bypass MVCC entirely, so they generate absolutely zero WAL or table bloat. 3) They are automatically released if the client connection drops or crashes, preventing distributed system deadlocks. 4) They can be scoped to the transaction or the session level.",
     ["Identifies pg_try_advisory_lock for application-level distributed locking", "Highlights the absence of MVCC bloat and WAL generation", "Mentions automatic release on session disconnect, preventing distributed deadlocks"],
     ["Recommends creating a 'locks' table with a boolean column instead"]),

    ("B66_2_7", "diagnose", "hard", "debugging", ["Concurrency", "Transactions"],
     "You observe a Deadlock graph in PostgreSQL where Transaction A is waiting on Transaction B, and Transaction B is waiting on Transaction A. Both transactions are running identical code: 'UPDATE accounts SET balance = balance - 100 WHERE id = 5; UPDATE accounts SET balance = balance + 100 WHERE id = 10;'. How does executing identical code result in a deadlock, and how do you guarantee prevention?",
     "Deadlocks occur when concurrent transactions acquire locks on multiple resources in different orders. Although the code is 'identical', the application is processing different data. If App Node 1 transfers $100 from Account 5 to Account 10, it locks 5, then tries to lock 10. If App Node 2 concurrently transfers $50 from Account 10 to Account 5, it locks 10, then tries to lock 5. A classic cyclic deadlock results. The database instantly aborts one of the transactions. To guarantee prevention, the application must enforce a deterministic, global locking order. Before executing the UPDATE statements, the code must dynamically sort the account IDs and ALWAYS update the lowest ID first, followed by the higher ID.",
     ["Explains that different variable inputs to the same code create cross-locking resource cycles", "Describes the cyclic dependency (A locks 5 wants 10; B locks 10 wants 5)", "Prescribes deterministic sorting of IDs before locking/updating to guarantee deadlocks never occur"],
     ["Suggests fixing deadlocks by using the NOLOCK hint to bypass concurrency controls"]),

    ("B66_2_8", "concept", "easy", "concept", ["Storage Engines", "Database Architecture"],
     "Explain the function of the Database Buffer Pool (or Shared Buffers). Why is it critical to allocate sufficient memory to it?",
     "The Buffer Pool is a dedicated block of RAM managed by the database engine used to cache frequently accessed data pages (blocks) and index pages from the disk. When a query requests data, the engine first checks the Buffer Pool. If the page is present (Cache Hit), the database reads it at RAM speed. If it's missing (Cache Miss), the database must perform a slow disk I/O fetch and load it into the pool. If sufficient memory is not allocated, the pool becomes too small to hold the working set of 'hot' data. This causes 'Buffer Thrashing', where the database constantly evicts pages to disk to make room for new ones, driving disk IOPS to 100% and completely destroying query performance.",
     ["Defines the Buffer Pool as an in-memory cache for disk pages/blocks", "Contrasts fast memory access (Cache Hit) with slow physical disk reads (Cache Miss)", "Explains Buffer Thrashing when the hot working set exceeds allocated RAM"],
     ["Confuses the Buffer Pool with connection pooling software like PgBouncer"]),

    ("B66_2_9", "scenario", "medium", "scenario", ["Transactions", "Failover & Consistency"],
     "A distributed microservices application uses the Two-Phase Commit (2PC) protocol via PREPARE TRANSACTION across three separate PostgreSQL databases. During phase 2, the coordinator node crashes before sending the COMMIT PREPARED command to one of the databases. What state is the database left in, and what operational problem does this cause?",
     "The database is left with an 'Orphaned Prepared Transaction'. When PREPARE TRANSACTION is executed, the database guarantees it has flushed all necessary data to disk and holds all necessary row locks to guarantee future commit success. However, because the coordinator crashed, the database never receives the final COMMIT or ROLLBACK. The severe operational problem is that the orphaned prepared transaction holds exclusive row locks indefinitely, blocking all other application queries trying to modify those rows. Furthermore, because it is an active transaction, it prevents autovacuum from cleaning up dead tuples across the entire database, eventually leading to massive bloat or transaction ID wraparound. A DBA must manually intervene and execute ROLLBACK PREPARED 'transaction_id'.",
     ["Identifies the orphaned prepared transaction retaining permanent row locks", "Highlights the system-wide danger of blocking autovacuum and causing bloat/wraparound", "Suggests manual DBA intervention with ROLLBACK PREPARED"],
     ["Claims the database automatically rolls back prepared transactions after 60 seconds"]),

    ("B66_2_10", "tradeoff", "medium", "tradeoff", ["Concurrency", "Indexing"],
     "What is the tradeoff of using a UUID (version 4) as a Primary Key compared to an auto-incrementing integer (SERIAL) or a sequential UUID (UUIDv7) in a B-tree indexed table?",
     "UUIDv4 generates completely random 128-bit strings. Tradeoff Advantages: It prevents ID collisions across distributed, disconnected systems, allows clients to generate IDs before insertion, and obscures business metrics (like total user count) from external observers. Tradeoff Disadvantages: Massive penalty on Database Storage and Insertion Performance. Because B-trees must maintain sorted order, random UUID inserts are scattered completely randomly across the index leaf pages. As the index grows larger than RAM, every random insert causes a Buffer Pool miss, resulting in a random disk read to fetch the index page, modifying it, and causing massive fragmentation and page splits. Auto-incrementing integers or time-sorted UUIDv7s append linearly to the right-most edge of the B-tree, keeping that specific page hot in memory and entirely eliminating random I/O during insertion.",
     ["Identifies advantages of UUIDv4: collision resistance in distributed generation and metric obscuration", "Explains catastrophic B-tree fragmentation and random I/O during insertion of random strings", "Recommends time-sorted identifiers (UUIDv7/ULID/SERIAL) to maintain right-edge linear appending"],
     ["Claims UUIDs use less disk space than 64-bit integers"]),

    ("B66_2_11", "implement", "medium", "implement", ["Transactions", "Database Internals"],
     "You are executing a massive batch migration script that processes 10,000 rows at a time in a single transaction. If one row fails a unique constraint, the entire transaction is aborted and rolled back. How do you implement Savepoints to safely handle individual row failures without losing the progress of the entire batch?",
     "Savepoints allow you to establish sub-transactions within a larger transaction block. To implement this: inside the BEGIN; block, before inserting/updating a row, the application executes SAVEPOINT row_save;. If the row operation succeeds, the script executes RELEASE SAVEPOINT row_save; (committing the sub-transaction to the main transaction). If the row operation throws a constraint violation or error, the database enters an aborted state, but the script can execute ROLLBACK TO SAVEPOINT row_save;. This rewinds the state back exactly to before that specific row operation, clearing the error state and allowing the massive transaction to cleanly continue processing the remaining 9,999 rows without losing all prior work.",
     ["Defines Savepoints as sub-transaction boundaries within a larger transaction block", "Explains the SAVEPOINT, RELEASE, and ROLLBACK TO SAVEPOINT syntax", "Demonstrates clearing the transaction abort state to preserve previous bulk progress"],
     ["Recommends disabling the unique constraint entirely during the batch migration"]),

    ("B66_2_12", "concept", "hard", "concept", ["Transactions", "PostgreSQL Internals"],
     "How does the PostgreSQL transaction engine implement atomicity and durability using the Write-Ahead Log (WAL) when a power failure occurs halfway through writing an 8KB data page to disk?",
     "Writing an 8KB data page to disk requires multiple physical sector writes by the OS/hardware. If power fails halfway through, the page on disk becomes 'torn' or corrupted, mixing old and new data. To prevent this, PostgreSQL uses Full-Page Writes in the WAL. The very first time a page is modified after a checkpoint, PostgreSQL writes the *entire, intact 8KB page* to the sequential WAL stream, followed by the specific row update record. The WAL is strictly appended and fsynced to disk *before* the actual data file page is ever written (Write-Ahead Logging). Upon restart after the crash, PostgreSQL reads the WAL. If it encounters a torn data page, it simply overwrites the corrupted page with the pristine 8KB Full-Page backup stored in the WAL, perfectly restoring atomicity and durability before reapplying subsequent transactions.",
     ["Identifies 'torn pages' resulting from partial hardware sector writes during a crash", "Explains Full-Page Writes into the WAL after checkpoints", "Describes the crash recovery process overwriting corrupt disk pages with the WAL backup before reapplying logs"],
     ["Claims the database reads the torn page and logically subtracts the incomplete SQL command"]),

    ("B66_2_13", "diagnose", "medium", "debugging", ["Concurrency", "Transactions"],
     "Two application threads execute 'UPDATE users SET points = points + 10 WHERE id = 1;' simultaneously under the READ COMMITTED isolation level. Why do both updates successfully apply (resulting in +20 points) instead of one overwriting the other, given that neither transaction explicitly locked the row beforehand?",
     "In PostgreSQL's READ COMMITTED isolation level, explicit locking (FOR UPDATE) is not strictly required for this specific update pattern. When Thread A executes the UPDATE, it implicitly acquires an exclusive row-level lock and computes points + 10 based on its current snapshot. When Thread B attempts the same UPDATE, it blocks waiting for Thread A's lock. Once Thread A commits, Thread B wakes up. Crucially, under READ COMMITTED, Thread B does NOT use its original snapshot. Instead, it 're-evaluates' the WHERE clause against the newly committed version of the row from Thread A. Seeing that the row still matches id = 1, Thread B uses the *new* committed points value as the base, adding its 10 points. Thus, the database safely serializes the updates, resulting in +20 points.",
     ["Identifies implicit exclusive row locks acquired automatically during UPDATE commands", "Explains that Thread B blocks and waits for Thread A to commit", "Critically explains that READ COMMITTED forces Thread B to re-evaluate its target row against Thread A's committed state, preventing lost updates"],
     ["Claims this works because the database parses the SQL and mathematically combines the addition statements"]),

    ("B66_2_14", "tradeoff", "medium", "tradeoff", ["Storage Engines", "Database Architecture"],
     "What is the architectural tradeoff of using a purely Log-Structured Merge-Tree (LSM-tree) storage engine (like RocksDB or Cassandra) versus a B+Tree storage engine (like PostgreSQL or MySQL InnoDB) for write-heavy vs read-heavy workloads?",
     "LSM-trees store incoming data in memory (MemTable) and periodically flush it to disk as immutable, sequentially written segments (SSTables). Tradeoff Advantages: Massive write throughput. LSM-trees eliminate random I/O and in-place updates, making them exceptionally fast for append-heavy or write-heavy workloads (e.g., time-series data). Tradeoff Disadvantages: Read amplification. Because data is scattered across multiple immutable segments on disk, reading a specific key requires searching memory, then checking multiple disk files (often using Bloom filters). Furthermore, background 'Compaction' processes consume heavy CPU and I/O to merge these segments. Conversely, B+Trees perform in-place updates, causing random I/O and page splits (slower writes), but guarantee that any read only requires navigating a single shallow tree structure, making them vastly superior for fast, consistent point-lookups and read-heavy relational workloads.",
     ["Defines LSM-trees as utilizing in-memory memtables and sequential immutable disk flushing", "Contrasts LSM-tree write superiority (no random I/O) against B+Tree read superiority (single tree traversal)", "Identifies LSM-tree compaction and read amplification penalties"],
     ["Claims B+Trees are designed for in-memory databases while LSM-trees are only for tape drives"]),

    ("B66_2_15", "concept", "easy", "concept", ["Transactions", "Database Operations"],
     "What does the 'D' in ACID stand for, and what specific hardware command does the database execute to guarantee it?",
     "The 'D' stands for Durability. It guarantees that once a transaction is successfully committed, the data changes will survive permanently, even in the event of an immediate catastrophic power loss, operating system crash, or database software panic. To guarantee this, the database engine must issue an fsync() (or fdatasync()) system call to the operating system. This command forces the OS to bypass its internal file system memory caches and physically flush the Write-Ahead Log (WAL) records directly onto the non-volatile storage hardware (SSD/HDD) before the database returns a 'Commit Successful' acknowledgment to the client application.",
     ["Defines Durability as data permanence following a successful commit despite systemic crashes", "Identifies the fsync() or fdatasync() system call", "Explains bypassing OS caches to guarantee physical hardware writes"],
     ["Claims Durability means the database schemas cannot be accidentally dropped"]),

    ("B66_2_16", "scenario", "medium", "scenario", ["Concurrency", "Database Architecture"],
     "You need to implement a job queue using a PostgreSQL table (jobs with status = 'PENDING'). Multiple worker nodes run 'SELECT id FROM jobs WHERE status = 'PENDING' LIMIT 1; UPDATE jobs SET status = 'PROCESSING' WHERE id = ?;'. What concurrency race condition occurs here, and how do you fix it?",
     "The race condition is a classic 'Select-then-Update' concurrency flaw. Multiple worker nodes will concurrently execute the SELECT statement and read the exact same job ID. They will then both execute the UPDATE statement. One will succeed first, and the other will redundantly update the already-processing job. As a result, multiple workers process the exact same job simultaneously, leading to duplicated work or corrupted application state. To fix this in a single atomic operation, use a Common Table Expression (CTE) with RETURNING and FOR UPDATE SKIP LOCKED: UPDATE jobs SET status = 'PROCESSING' WHERE id = (SELECT id FROM jobs WHERE status = 'PENDING' FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *;. This guarantees each worker safely locks and claims a unique job atomically.",
     ["Identifies 'Select-then-Update' gap allowing multiple workers to claim the identical row", "Proposes atomic combination of lock and update via CTEs or subqueries", "Crucially includes FOR UPDATE SKIP LOCKED to prevent workers from hanging on each other's locks"],
     ["Suggests fixing it by adding a random delay (jitter) to the worker nodes"]),

    ("B66_2_17", "implement", "hard", "implement", ["Transactions", "Database Operations"],
     "A legacy batch job deletes 50 million rows from a massive 500GB table using a single 'DELETE FROM logs WHERE created_at < '2020-01-01';' statement. This causes the database to lock up, run out of memory, and crash the primary disk with massive WAL generation. How do you implement a safe, chunked deletion strategy that respects database internals?",
     "A massive single DELETE generates millions of dead MVCC tuples simultaneously, creates a colossal single transaction that holds locks indefinitely, and generates gigabytes of Write-Ahead Log (WAL) that exhausts disk I/O and replica network bandwidth. To implement a safe strategy: 1) Chunking: Write a script to loop and delete a small batch at a time, e.g., DELETE FROM logs WHERE id IN (SELECT id FROM logs WHERE created_at < '2020-01-01' LIMIT 5000);. 2) Yielding: Add a pg_sleep(0.1) or application-level sleep between batches. This allows the database to flush WAL, allows concurrent queries to acquire locks, and most importantly, gives autovacuum time to run in the background and clean up the dead tuples incrementally, preventing table bloat and catastrophic I/O spikes.",
     ["Identifies massive WAL generation and infinite lock holding of single large DELETEs", "Recommends small, batched DELETEs using LIMIT clauses", "Crucially recommends pausing between batches to allow WAL flushing and background autovacuum to process dead tuples"],
     ["Suggests turning off the database server and deleting the rows manually from the storage drive"]),

    ("B66_2_18", "diagnose", "hard", "debugging", ["Concurrency", "Database Internals"],
     "In an application using Optimistic Concurrency Control (OCC) with a 'version' integer column, you notice that during high-contention bursts, 95% of update requests fail with 'Version mismatch' errors, forcing the application to retry heavily and crash the API servers. Why does OCC fail catastrophically under high contention, and what locking strategy should you switch to?",
     "Optimistic Concurrency Control (OCC) assumes conflicts are rare. It reads a row, performs application logic, and then executes UPDATE table SET val = new_val, version = version + 1 WHERE id = 1 AND version = old_version;. If 100 concurrent requests try to update the same row, 1 succeeds, and 99 fail the version = old_version check. The application must then re-fetch and retry 99 times, then 98 times, creating an exponentially amplifying retry storm that consumes all application CPU and database connections. OCC is an anti-pattern for high-contention hot-rows. You should switch to Pessimistic Concurrency Control using SELECT ... FOR UPDATE; (or implicitly via direct atomic updates like UPDATE table SET val = val + 1;). This forces the database's internal Lock Manager to serialize the requests cleanly into a queue, eliminating application-level retry storms entirely.",
     ["Explains OCC design assumption (rare conflicts) failing under high contention via retry storms", "Identifies API CPU and DB connection exhaustion due to amplifying retries", "Recommends Pessimistic locking (FOR UPDATE) to utilize the database's internal queuing mechanisms"],
     ["Suggests increasing the version column to a 64-bit integer to prevent overflow"]),

    ("B66_2_19", "concept", "easy", "concept", ["Concurrency", "Database Operations"],
     "What is the difference between a Shared Lock (Row Share) and an Exclusive Lock (Row Exclusive) on a database row?",
     "An Exclusive Lock (SELECT ... FOR UPDATE or an UPDATE/DELETE statement) declares absolute intent to modify the row. Only ONE transaction can hold an Exclusive Lock on a specific row at a time. If another transaction wants any type of lock on that row, it must wait. A Shared Lock (SELECT ... FOR SHARE) declares intent to read a row and ensure it is not modified or deleted by anyone else until the transaction completes. MULTIPLE transactions can simultaneously hold a Shared Lock on the exact same row. However, if any transaction attempts to acquire an Exclusive Lock to modify the row, it will be blocked until all current Shared Locks are released.",
     ["Defines Exclusive Lock as single-owner modification intent", "Defines Shared Lock as multi-owner read intent with modification prevention", "Explains that Exclusive locks wait for Shared locks to release, and vice versa"],
     ["Claims Shared Locks copy the row to a temporary table for viewing"]),

    ("B66_2_20", "tradeoff", "medium", "tradeoff", ["Storage Engines", "PostgreSQL Internals"],
     "What are the architectural tradeoffs of storing large binary files (images/PDFs) directly inside a relational database table (e.g., using BYTEA) versus storing them in object storage (e.g., S3) and keeping only the URL in the database?",
     "Storing binaries in the database (BYTEA/BLOB). Advantages: Strict ACID transactional consistency (if the row rolls back, the image rolls back), simplified backup/restore (one single dump file), and integrated access control. Disadvantages: Bloats the database size massively, heavily pollutes the database Buffer Pool (evicting hot relational data to serve static images), increases database CPU load for compression/decompression (TOAST), and creates massive, slow WAL replication traffic to read replicas. Storing in Object Storage (S3) + DB URL. Advantages: Offloads massive network bandwidth and disk I/O to a specialized CDN, keeping the relational database tiny, fast, and optimized for structured queries. Disadvantages: Breaks transactional integrity (an S3 upload might succeed while the DB insert fails, creating orphaned files) and requires complex two-phase cleanup logic.",
     ["Identifies database ACID compliance and simplified backups for inline binary storage", "Identifies Buffer Pool pollution and massive WAL replication overhead as database penalties", "Highlights S3 offloading network/IO but sacrificing transactional guarantees (orphaned files)"],
     ["Claims object storage automatically synchronizes with database foreign keys"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 2).")
    
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
    print("POST-BATCH AUDIT PART 2")
    print("========================================")
    print(f"Batch: 66 Part 2")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
