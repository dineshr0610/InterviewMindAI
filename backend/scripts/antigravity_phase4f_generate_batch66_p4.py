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
    ("B66_4_1", "scenario", "hard", "scenario", ["Caching", "Database Operations"],
     "A highly trafficked API relies on a Redis cache with a 5-minute TTL. The database suddenly experiences a catastrophic CPU spike at exactly 12:05, 12:10, and 12:15, crashing the cluster. What is a 'Cache Stampede' (Thundering Herd), and how do you resolve it using a Mutex or Probabilistic Early Expiration?",
     "A Cache Stampede occurs when a highly requested cache key expires. Instantly, thousands of concurrent application threads experience a cache miss simultaneously. They all simultaneously hit the database to recompute the expensive query, exhausting the database's connection pool and CPU. Resolutions: 1) Mutex (Locking): When a thread detects a cache miss, it must acquire a distributed lock (e.g., Redis SETNX) for that specific key. The one thread that gets the lock queries the database and updates the cache. The other 9,999 threads just wait a few milliseconds and poll the cache again. 2) Probabilistic Early Expiration (PERF): Threads randomly decide to proactively recompute and refresh the cache *before* it actually expires (based on a probability curve). This ensures one thread refreshes the data in the background while the others still read the slightly stale, unexpired data, preventing the herd entirely.",
     ["Identifies thousands of concurrent cache misses funneling to the database simultaneously", "Explains the Mutex lock strategy blocking duplicate database queries", "Explains the PERF / background-refresh strategy to renew cache before TTL expiry"],
     ["Claims a Cache Stampede is a DDoS attack and suggests a firewall blocking IPs"]),

    ("B66_4_2", "tradeoff", "medium", "tradeoff", ["Caching", "Database Architecture"],
     "What are the architectural tradeoffs of using a Write-Through caching strategy versus a Write-Behind (Write-Back) caching strategy when saving data to a relational database?",
     "Write-Through: The application writes data to the cache and the database synchronously in the same transaction, returning success only when both complete. Advantages: Perfect data consistency between cache and DB, and guaranteed persistence. Disadvantages: Slower write latency (waits for DB disk I/O). Write-Behind (Write-Back): The application writes data ONLY to the cache (e.g., Redis), which returns success immediately. A background process asynchronously flushes the cached data to the database in batches later. Advantages: Massive write throughput and near-zero latency, protecting the database from write spikes. Disadvantages: Severe risk of data loss. If the cache node crashes before the background flush occurs, the successfully acknowledged writes are permanently lost.",
     ["Defines Write-Through as synchronous dual-writes prioritizing consistency over latency", "Defines Write-Behind as asynchronous background flushing prioritizing latency over consistency", "Highlights catastrophic data loss risk in Write-Behind if the cache crashes"],
     ["Claims Write-Behind means writing to the database first and the cache second"]),

    ("B66_4_3", "concept", "easy", "concept", ["Caching", "Performance & Tuning"],
     "What is 'Negative Caching', and what specific denial-of-service vulnerability does it prevent?",
     "Negative Caching is the practice of caching the *absence* of data. If an application queries the database for user_id = 999 and the user does not exist, the application stores a key user:999 with a value of null (or empty) in the cache for a short TTL. This prevents a specific Denial-of-Service vulnerability: if a malicious actor or a broken bot repeatedly queries for non-existent IDs, the cache would normally miss every time, forcing the database to execute millions of useless queries that scan indexes to prove the data doesn't exist. Negative caching absorbs these malicious requests at the cache layer, protecting the database CPU.",
     ["Defines negative caching as storing 'null' or 'not found' results", "Explains the vulnerability: malicious brute-forcing of non-existent keys repeatedly missing the cache", "Explains that negative cache absorbs useless database index scans"],
     ["Claims negative caching means removing items from the cache"]),

    ("B66_4_4", "diagnose", "hard", "debugging", ["Schema Migrations", "Database Operations"],
     "You execute 'ALTER TABLE orders ADD COLUMN status VARCHAR(20) DEFAULT 'PENDING';' on a 500GB PostgreSQL 10 database. The database instantly completely locks up, and all application reads and writes to the orders table time out. Why does adding a column with a default value cause a catastrophic outage in older PostgreSQL versions, and how do you work around it safely?",
     "In older versions of PostgreSQL (prior to PG 11), adding a column with a DEFAULT value requires an AccessExclusiveLock on the entire table. The database must then physically rewrite every single row on disk (a full table rewrite) to inject the default value into the new column. For a 500GB table, this takes hours, during which all reads and writes are blocked, causing total application downtime. The safe workaround (and the internal mechanism adopted in PG 11+) is a 3-step process: 1) ALTER TABLE orders ADD COLUMN status VARCHAR(20); (Adds the column without a default, which is an instant metadata-only operation). 2) ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'PENDING'; (Applies the default for future inserts only, also instant). 3) Update the historical rows in small batches in the background: UPDATE orders SET status = 'PENDING' WHERE status IS NULL;.",
     ["Identifies the full table rewrite and AccessExclusiveLock triggered by a DEFAULT clause", "Explains the three-step workaround for zero downtime", "Identifies adding a column *without* a default as a fast metadata-only operation"],
     ["Suggests restarting the database server to clear the lock"]),

    ("B66_4_5", "scenario", "medium", "scenario", ["Schema Migrations", "Concurrency"],
     "A developer needs to change a column type from INTEGER to BIGINT on a massive transactions table. They run 'ALTER TABLE transactions ALTER COLUMN amount TYPE BIGINT;'. The command hangs, waiting for an AccessExclusiveLock. Meanwhile, all new incoming SELECT statements also hang. Why do the SELECT statements hang if they only require a Shared Lock, and the ALTER TABLE hasn't even acquired its lock yet?",
     "This is caused by Lock Queuing. The ALTER TABLE command requests an AccessExclusiveLock. It cannot acquire it immediately because there are active, long-running queries holding AccessShareLocks on the table. So, the ALTER TABLE enters the database's lock queue and waits. Crucially, lock queues are strictly First-In-First-Out (FIFO) and respect lock escalation. Any *new* incoming SELECT statements (requesting AccessShareLocks) must queue up *behind* the waiting ALTER TABLE command. Because AccessExclusiveLock conflicts with everything, the pending ALTER command effectively acts as a dam, blocking all subsequent reads and writes from executing, taking the table offline even before it starts its own work.",
     ["Identifies Lock Queuing and strictly FIFO behavior of the database lock manager", "Explains that pending exclusive lock requests act as a dam, blocking new shared locks", "Diagnoses the table effectively going offline before the ALTER command even executes"],
     ["Claims SELECT statements hang because changing an integer size corrupts the data types"]),

    ("B66_4_6", "concept", "easy", "concept", ["Schema Migrations", "Database Architecture"],
     "What is the 'Expand and Contract' pattern for database schema migrations, and why is it essential for zero-downtime deployments?",
     "Expand and Contract (also known as Parallel Change) is a pattern that breaks a breaking schema change (like renaming a column or splitting a table) into multiple backward-compatible phases to ensure zero downtime. 1) Expand: Add the new column/table alongside the old one. Update the application to dual-write to both, but continue reading from the old one. 2) Migrate: Run a background script to copy historical data from the old structure to the new structure. 3) Transition: Update the application to read exclusively from the new structure. 4) Contract: Drop the old column/table in a subsequent deployment. It is essential because standard deployments have a period where v1 and v2 of the application code are running simultaneously; if you modify the schema destructively in one step, either v1 or v2 will instantly crash.",
     ["Defines Expand phase (additive dual-writing) and Contract phase (destructive cleanup)", "Explains the necessity of handling multiple concurrent application versions (v1 and v2) during rolling deployments", "Identifies backfilling historical data between phases"],
     ["Claims it means increasing server RAM before running migrations to prevent crashes"]),

    ("B66_4_7", "diagnose", "medium", "debugging", ["Data Integrity", "Database Operations"],
     "You add a Foreign Key constraint 'ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);' on a massive table. The operation requires scanning the entire orders table to validate the constraint, taking 4 hours and blocking deployments. How can you add a Foreign Key to a massive table in PostgreSQL with zero downtime using the NOT VALID clause?",
     "To add a foreign key without a massive blocking validation scan, you use a two-step process. Step 1: ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID;. This command requires a very brief exclusive lock to update metadata. The NOT VALID flag tells PostgreSQL to enforce the constraint on all *new* inserts and updates, but to skip scanning the existing historical data. Step 2: ALTER TABLE orders VALIDATE CONSTRAINT fk_user;. This command runs in the background. It only requires a ShareUpdateExclusiveLock, meaning it scans the table to verify historical data without blocking concurrent reads or writes on the table. Once finished, the constraint is fully validated with zero downtime.",
     ["Identifies the NOT VALID clause enabling instant constraint enforcement for future rows only", "Explains VALIDATE CONSTRAINT running asynchronously without blocking table writes", "Highlights the two-step process achieving zero-downtime constraints"],
     ["Suggests turning off foreign key checks globally before running the ALTER TABLE command"]),

    ("B66_4_8", "tradeoff", "hard", "tradeoff", ["Data Integrity", "Concurrency"],
     "What is the severe concurrency tradeoff (Lock Contention) of heavily utilizing Foreign Key constraints in a high-throughput transaction processing system, particularly when updating or deleting rows in the parent table?",
     "While Foreign Keys guarantee referential integrity, they introduce hidden, severe lock contention across tables. When a transaction INSERTs or UPDATEs a row in the child table (e.g., orders), the database must implicitly acquire a Shared Lock on the parent row (e.g., users) to ensure the parent isn't deleted while the child is being inserted. Conversely, if you UPDATE the primary key of the parent, or DELETE the parent row, the database must implicitly lock and scan the entire child table (or use an index) to ensure no child records are orphaned, blocking all concurrent inserts to the child table. In massive, high-throughput systems (like distributed ledgers or social feeds), this cross-table locking serialization completely bottlenecks write throughput, leading architects to drop foreign keys entirely and enforce referential integrity within the application logic.",
     ["Explains implicit Shared Locks acquired on parent tables during child inserts", "Explains massive locking/scanning of child tables during parent DELETEs or PK updates", "Identifies cross-table serialization bottlenecking high-throughput horizontal scaling"],
     ["Claims Foreign Keys slow down SELECT statements because the database automatically performs a JOIN"]),

    ("B66_4_9", "scenario", "medium", "scenario", ["Data Integrity", "Transactions"],
     "An application inserts a complex hierarchical object: INSERT INTO users, followed by INSERT INTO profiles (user_id), followed by INSERT INTO settings (user_id). If the settings insert fails, the transaction rolls back. However, the application uses a message queue that retries the entire operation. The retry fails immediately because the users row already exists (Unique Violation). How do you redesign this ingestion process to be Idempotent?",
     "An idempotent operation produces the exact same result no matter how many times it is executed. To make the database ingestion idempotent, you must use 'Upsert' logic (e.g., ON CONFLICT DO UPDATE or ON CONFLICT DO NOTHING in PostgreSQL, or MERGE in SQL Server). Instead of a blind INSERT INTO users, the application executes INSERT INTO users (...) VALUES (...) ON CONFLICT (id) DO UPDATE SET last_login = EXCLUDED.last_login;. This ensures that if the message queue retries a partially or fully completed job, the database silently updates the existing rows instead of throwing fatal Unique Constraint violations, allowing the transaction to proceed and guarantee the child records (profiles, settings) are successfully processed.",
     ["Defines Idempotency as safe repetition of operations without adverse side effects", "Proposes ON CONFLICT DO UPDATE/NOTHING (Upsert) to handle retried inserts", "Connects idempotency to message queue resiliency and transaction continuation"],
     ["Recommends deleting all rows at the start of the transaction before re-inserting them"]),

    ("B66_4_10", "concept", "medium", "concept", ["Data Integrity", "Transactions"],
     "What are 'Deferred Constraints' in PostgreSQL, and in what specific scenario are they absolutely required to insert data successfully?",
     "By default, database constraints (like Foreign Keys or UNIQUE constraints) are checked immediately at the end of each individual SQL statement. A Deferred Constraint postpones this validation until the very end of the transaction, just before the COMMIT. They are absolutely required when inserting data with cyclic dependencies (Circular Foreign Keys). For example, if Table A has a foreign key to Table B, and Table B has a foreign key to Table A, it is impossible to insert the first row into either table because the referenced row in the other table doesn't exist yet. By defining the foreign keys as INITIALLY DEFERRED, you can open a transaction, insert the row into Table A (validation postponed), insert the row into Table B (validation postponed), and then COMMIT. The database then validates both constraints simultaneously, and the commit succeeds.",
     ["Defines deferred constraints as postponing validation until COMMIT", "Identifies Circular/Cyclic Foreign Keys as the required use case", "Explains the deadlock of inserting into mutually dependent tables without deferral"],
     ["Claims deferred constraints are used to run queries at midnight during low traffic periods"]),

    ("B66_4_11", "implement", "hard", "implement", ["Database Security", "Database Architecture"],
     "You are designing a multi-tenant SaaS application where 100 different companies share the exact same customers table. A bug in the application's WHERE tenant_id = ? clause could leak Company A's data to Company B. How do you implement PostgreSQL Row-Level Security (RLS) to enforce tenant isolation at the database engine level, making data leaks mathematically impossible regardless of application bugs?",
     "Row-Level Security (RLS) intercepts every query in the engine before execution. To implement: 1) Enable RLS: ALTER TABLE customers ENABLE ROW LEVEL SECURITY;. 2) Define a policy: CREATE POLICY tenant_isolation_policy ON customers USING (tenant_id = current_setting('app.current_tenant')::int);. 3) Application integration: When the application connects to the DB, it must execute SET LOCAL app.current_tenant = '5'; as the very first command in the transaction. Now, if the application executes SELECT * FROM customers; (forgetting the WHERE clause), the database engine automatically and transparently rewrites the query using the policy. It will strictly only return rows where tenant_id = 5. It provides absolute defense-in-depth, rendering SQL injection or ORM bugs harmless regarding cross-tenant data leakage.",
     ["Outlines enabling RLS and defining a CREATE POLICY mapped to a session variable", "Describes the application passing the tenant context via SET LOCAL", "Highlights defense-in-depth against ORM bugs or SQL injection by forcing database-level policy rewriting"],
     ["Recommends creating 100 separate databases instead of using RLS"]),

    ("B66_4_12", "diagnose", "medium", "debugging", ["Database Security", "PostgreSQL Internals"],
     "A database administrator creates a secure view: CREATE VIEW active_users AS SELECT * FROM users WHERE status = 'ACTIVE' AND is_deleted = false;. They grant SELECT on this view to a junior analyst role, but explicitly revoke SELECT on the underlying users table. However, the analyst runs SELECT * FROM active_users; and gets a 'Permission Denied' error. Why did this happen, and how does the concept of SECURITY INVOKER vs SECURITY DEFINER apply here?",
     "By default, Views and Functions in PostgreSQL execute with the privileges of the user calling them (SECURITY INVOKER). When the junior analyst queries the view, the database engine expands the view and attempts to read the underlying users table using the analyst's permissions. Since the analyst lacks permissions on the underlying table, the query is rejected. To fix this, you must change the view or function to execute with the privileges of the user who *created* it (SECURITY DEFINER). While standard views don't have a direct SECURITY DEFINER clause in older PG versions, you can wrap the logic in a SECURITY DEFINER function, or in modern PostgreSQL (15+), explicitly declare the view with WITH (security_invoker = false), allowing the analyst to read the subset of data without granting direct table access.",
     ["Identifies SECURITY INVOKER default behavior expanding the view using the caller's restricted permissions", "Recommends SECURITY DEFINER (or security_invoker=false) to execute using the creator's elevated permissions", "Connects this mechanism to safe data-subset exposure without underlying table grants"],
     ["Claims the analyst needs an SSH key added to the database server to view the data"]),

    ("B66_4_13", "concept", "easy", "concept", ["Database Security", "Database Operations"],
     "What is 'SQL Injection', and why do Prepared Statements (Parameterized Queries) completely neutralize the threat at the database protocol level?",
     "SQL Injection occurs when an application concatenates untrusted user input directly into a dynamic SQL string (e.g., query = \"SELECT * FROM users WHERE name = '\" + input + \"'\"). A malicious user can input ' OR '1'='1, altering the fundamental structure of the query to bypass authentication or extract data. Prepared Statements neutralize this because they split the operation into two distinct protocol steps. First, the application sends the query template (SELECT * FROM users WHERE name = $1) to the database, which parses, compiles, and locks the execution plan. Second, the application sends the parameter value separately. Because the query structure is already compiled, the database strictly treats the parameter as a literal data value, never as executable code, making injection mathematically impossible.",
     ["Defines SQL injection as malicious input altering the dynamic query structure", "Explains the two-step protocol: Pre-compiling the template, then sending raw values separately", "Highlights that the database engine physically cannot execute parameter values as SQL syntax after compilation"],
     ["Claims Prepared Statements work by using Regex to delete quotes from user input"]),

    ("B66_4_14", "tradeoff", "medium", "tradeoff", ["Database Security", "Database Architecture"],
     "What are the tradeoffs of handling Data Encryption at Rest via Transparent Data Encryption (TDE) at the database/disk level versus handling Application-Level Encryption before the data is sent to the database?",
     "Transparent Data Encryption (TDE) encrypts the physical disk files and WAL logs. Advantages: Completely transparent to the application, zero code changes required, preserves all database functionality (sorting, indexing, searching), and protects against someone physically stealing the hard drives. Disadvantages: Does not protect against compromised database credentials, SQL injection, or DBA snooping, as the data is decrypted in memory. Application-Level Encryption encrypts data (e.g., PII like SSNs) in the application memory before sending it to the database. Advantages: Ultimate security. Even the DBA or a SQL injection attacker only sees encrypted ciphertext. Disadvantages: Severe loss of database functionality. You cannot perform LIKE searches, range queries (>), or native sorting on the encrypted columns. Key management also becomes highly complex.",
     ["Identifies TDE advantages: preserves database search/index functionality and requires zero code changes", "Identifies TDE disadvantages: vulnerable to SQL injection and DBA snooping since memory is plaintext", "Identifies App-Level encryption tradeoff: ultimate security against DB compromise, but destroys searchability and native DB functions"],
     ["Claims Application-Level Encryption encrypts the network connection using TLS"]),

    ("B66_4_15", "scenario", "medium", "scenario", ["Database Architecture", "Performance & Tuning"],
     "An application has a 'leaderboard' feature that calculates the top 10 users by aggregating millions of points records. This query takes 5 seconds to run. The business wants the leaderboard updated in real-time, but querying the database on every page load crashes the DB. How do you implement a 'Materialized View' pattern to balance freshness and database CPU?",
     "A Materialized View physically computes and stores the result of the expensive aggregation query on disk as a snapshot. When users load the leaderboard, they query the Materialized View, which responds in 1 millisecond because it's just a simple table read. To keep it fresh without crashing the DB, you set up a background cron job or database trigger to execute REFRESH MATERIALIZED VIEW CONCURRENTLY leaderboard_view; every 1 minute. The CONCURRENTLY keyword is critical: it rebuilds the snapshot in the background and applies the delta without taking an exclusive lock, ensuring the leaderboard remains perfectly readable by the application while the 5-second aggregation computes.",
     ["Proposes Materialized Views to physically cache aggregation results on disk", "Proposes background refreshing (cron/triggers) to update the snapshot", "Critically identifies the CONCURRENTLY keyword to allow lock-free reads during the refresh"],
     ["Suggests rewriting the leaderboard query in Assembly language to make it faster"]),

    ("B66_4_16", "implement", "hard", "implement", ["Schema Migrations", "Performance & Tuning"],
     "You are managing a 1TB PostgreSQL table and need to reclaim massive amounts of disk space caused by dead tuple bloat. VACUUM FULL will lock the table for hours, which is unacceptable. How do you use the pg_repack or pg_squeeze extension to perform an online, lock-free table rewrite?",
     "VACUUM FULL requires an AccessExclusiveLock, preventing all reads and writes. To rewrite the table online, tools like pg_repack use a shadow-table strategy. Implementation mechanism: 1) It creates a log table to capture all new, ongoing changes to the original table. 2) It adds an INSERT/UPDATE/DELETE trigger to the original table to populate the log table. 3) It creates a brand new, empty shadow table and begins copying all valid rows from the original table to the shadow table (compacting them without bloat). 4) It builds all necessary indexes on the shadow table. 5) It plays back the changes from the log table to the shadow table to catch up. 6) It takes a brief, sub-second exclusive lock, swaps the filenames of the original and shadow tables in the system catalog, and drops the old bloated table.",
     ["Identifies shadow-table creation and background copying strategy", "Explains using triggers to log live mutations during the copy phase", "Explains playback catch-up and final sub-second atomic catalog swap"],
     ["Recommends using the Linux 'truncate' command to shrink the file sizes"]),

    ("B66_4_17", "diagnose", "medium", "debugging", ["Schema Migrations", "Database Operations"],
     "An application uses 'SELECT * FROM users;' and relies on the column order. A DBA drops a column and adds a new one. The application immediately crashes because the columns returned by SELECT * shifted. Why is SELECT * considered a severe anti-pattern in production code, and how does it relate to the database schema catalog?",
     "SELECT * dynamically requests every column present in the table's metadata catalog at the exact moment the query is compiled. If a DBA drops a column (e.g., middle_name) or adds a new one (e.g., is_admin), the physical layout and the sequence of columns returned to the application change instantly. If the application maps results by positional index (e.g., row[3]), or if an ORM rigidly expects a specific struct shape, the deserialization will fail, crashing the application. Furthermore, SELECT * forces the database to read and transmit massive amounts of unnecessary data (like large TEXT or BYTEA fields) over the network, wasting memory and bandwidth. Production code must always explicitly define the required columns (e.g., SELECT id, email FROM users;) to decouple application logic from underlying schema catalog shifts.",
     ["Explains SELECT * dynamically reading the catalog metadata at query time", "Highlights crash risk when applications map results positionally and columns shift", "Highlights network/memory waste transmitting unused large payload columns"],
     ["Claims SELECT * bypasses all database security policies"]),

    ("B66_4_18", "concept", "easy", "concept", ["Caching", "Database Operations"],
     "What is a 'Cache Hit Ratio', and why is a 99% hit ratio on a database caching layer not always an indicator of a healthy system?",
     "Cache Hit Ratio is the percentage of requests successfully served from the cache (Cache Hits) versus requests that had to fetch data from the primary database (Cache Misses). A 99% hit ratio means 99 out of 100 requests never hit the DB. However, it is not always a sign of health because of the 'Heavy Tail' problem. If an application receives 10,000 requests per second, a 99% hit ratio means 100 requests per second still fall through to the database. If those 100 queries are extremely complex, unoptimized analytical queries (the 'heavy tail'), they can still completely overwhelm the database CPU and cause an outage, despite the cache handling the vast majority of the traffic.",
     ["Defines Cache Hit Ratio mathematically", "Explains the 'Heavy Tail' problem where absolute volume of misses matters more than percentage", "Explains that a small percentage of highly complex misses can still crash the database"],
     ["Claims 99% means the cache is corrupted and needs to be flushed"]),

    ("B66_4_19", "tradeoff", "medium", "tradeoff", ["Database Security", "Database Architecture"],
     "What is the tradeoff of using highly granular Role-Based Access Control (RBAC) at the database layer (e.g., granting SELECT on specific columns to specific database users) versus managing all permissions at the Application Layer?",
     "Database-Layer RBAC Advantages: Defense-in-depth. If the application server is compromised or an engineer runs manual queries, the database engine strictly enforces permissions, preventing access to sensitive columns (e.g., SSN, passwords). It guarantees security regardless of the client. Disadvantages: Connection pooling becomes a nightmare. To utilize DB-level roles, every application user must have a dedicated DB connection/role, destroying the ability to use efficient connection poolers (like PgBouncer), severely limiting scalability. Application-Layer RBAC Advantages: Highly scalable. The application uses a single powerful DB user via a connection pool and handles authorization in code. Disadvantages: If there is an authorization bug in the code, or a SQL injection vulnerability, the single DB user has access to everything, leading to massive, unrestricted data breaches.",
     ["Identifies DB RBAC advantage: defense-in-depth and absolute client-agnostic enforcement", "Identifies DB RBAC disadvantage: destroys connection pooling scalability because roles cannot be easily multiplexed", "Identifies App RBAC tradeoff: infinitely scalable via poolers, but catastrophic blast radius if app code is breached"],
     ["Claims Database-Layer RBAC requires paying a separate licensing fee to Oracle"]),

    ("B66_4_20", "scenario", "hard", "scenario", ["Data Integrity", "Transactions"],
     "You are designing a financial ledger. You must subtract $100 from Account A and add $100 to Account B. However, the database does not support multi-row ACID transactions (e.g., you are using DynamoDB without TXs, or spanning two different microservice databases). How do you guarantee atomicity using the 'Saga Pattern' and Compensating Transactions?",
     "Without native ACID transactions, you must implement a Saga. A Saga breaks the operation into a sequence of local, atomic transactions, managed by an orchestrator or choreographed via events. Step 1: Execute UPDATE Account A SET balance = balance - 100. Step 2: Publish an event to execute UPDATE Account B SET balance = balance + 100. If Step 2 fails (e.g., Account B is closed or the network drops), the system is now in an inconsistent state (money vanished). To restore atomicity, the orchestrator MUST execute a Compensating Transaction: a logically reversed operation that undoes the previous steps. It executes UPDATE Account A SET balance = balance + 100 with a reason 'Reversal due to Step 2 failure'. The system is eventually consistent and guarantees no money is permanently lost, but it sacrifices true Isolation (other transactions might briefly see Account A missing the $100 before the compensation runs).",
     ["Explains the Saga Pattern orchestrating multiple independent local transactions", "Defines Compensating Transactions as logical reversals executed upon downstream failures", "Highlights the tradeoff: achieves Eventual Consistency but sacrifices strict Isolation (dirty reads during the saga)"],
     ["Suggests freezing both databases using a hardware lock before making the transfer"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 4).")
    
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
    print("POST-BATCH AUDIT PART 4")
    print("========================================")
    print(f"Batch: 66 Part 4")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
