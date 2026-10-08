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
    ("B66_5_1", "diagnose", "hard", "debugging", ["Connection Management", "PostgreSQL Internals"],
     "An application uses PgBouncer in 'Transaction pooling' mode to handle 10,000 concurrent client connections over 100 actual database connections. Suddenly, queries relying on PREPARE statements start throwing errors: 'prepared statement does not exist'. Why does Transaction pooling break prepared statements, and how do you fix it?",
     "In Transaction pooling mode, PgBouncer assigns a physical database connection to a client only for the duration of a single transaction. Once the COMMIT happens, the connection goes back to the pool and is handed to a completely different client. Prepared statements are strictly session-bound at the database protocol level. If Client A prepares a statement on Connection #1, commits, and then tries to execute it, PgBouncer might route the EXECUTE command over Connection #2, where the statement literally does not exist. To fix this, you must either: 1) Switch PgBouncer to 'Session pooling' mode (which destroys the massive concurrency benefits); or 2) In newer PgBouncer versions, enable the max_prepared_statements feature at the proxy level; or 3) Disable prepared statements entirely in the application's ORM database driver.",
     ["Identifies Prepared Statements as strictly session-bound to a physical connection", "Explains Transaction pooling disconnecting the client from the physical connection after COMMIT", "Recommends disabling prepared statements in the ORM or using newer PgBouncer statement caching"],
     ["Claims the database dropped the prepared statement due to low memory constraints"]),

    ("B66_5_2", "tradeoff", "hard", "tradeoff", ["Analytics & OLAP", "Storage Engines"],
     "Compare the physical disk layout of a Row-Oriented database (PostgreSQL) versus a Column-Oriented database (ClickHouse/Redshift) when executing an aggregation query like 'SELECT SUM(revenue) FROM sales WHERE year = 2023;'. Why is the columnar engine mathematically faster for this specific query, yet terrible for OLTP inserts?",
     "In a Row-Oriented layout, a single physical disk block contains complete records (id, user, date, revenue, status). To calculate SUM(revenue), the database must pull entire blocks from disk into memory, discarding 90% of the payload data to isolate the revenue column. This causes massive, unnecessary I/O read amplification. In a Column-Oriented layout, each column is stored in its own separate, highly compressed physical file. The database sequentially streams only the year file and the revenue file from disk, minimizing I/O, utilizing CPU vectorization (SIMD), and scanning billions of rows in milliseconds. Tradeoff: OLTP Inserts are terrible in columnar databases because inserting a single new row requires performing random disk writes across 20 different column files, destroying write throughput compared to appending a single row block.",
     ["Contrasts physical disk blocking: row-based storing all attributes together vs column-based segregating attributes into files", "Identifies massive read-I/O reduction and SIMD vectorization for columnar aggregation", "Highlights the random I/O write amplification penalty when inserting single rows into columnar stores"],
     ["Claims Columnar databases run entirely in RAM while Row databases use HDD"]),

    ("B66_5_3", "concept", "easy", "concept", ["Analytics & OLAP", "Performance & Tuning"],
     "What is a 'HyperLogLog' (HLL) data structure, and why is it essential for massive analytical workloads involving COUNT(DISTINCT user_id)?",
     "COUNT(DISTINCT) is exceptionally expensive on large datasets because the database must keep every single unique ID it has seen in a massive in-memory hash set to check for duplicates, often exceeding work_mem and spilling to disk. HyperLogLog is a probabilistic data structure that estimates the cardinality (number of unique elements) of a dataset. Instead of storing actual IDs, it hashes the IDs and looks at the pattern of leading zeros. It uses a fixed, tiny amount of memory (e.g., 12KB) to count billions of distinct items. The tradeoff is that it returns an approximation (usually within 1-2% error), but it runs thousands of times faster than exact counting and consumes virtually zero RAM.",
     ["Defines HyperLogLog as a probabilistic cardinality estimator", "Explains the severe memory/disk spill penalty of exact COUNT(DISTINCT)", "Highlights the tradeoff: 1-2% accuracy error in exchange for massive speed and tiny memory footprint"],
     ["Claims HyperLogLog is an audit logging mechanism for database security changes"]),

    ("B66_5_4", "diagnose", "medium", "debugging", ["Observability & Diagnosis", "Database Operations"],
     "A production PostgreSQL database's CPU spikes to 100%. The pg_stat_activity view shows 500 connections executing 'SELECT * FROM users WHERE status = 'PENDING''. You look at the wait_event column and see 'LWLock: buffer_mapping'. What does this specific wait event indicate, and why doesn't adding more CPU cores fix it?",
     "LWLock (Lightweight Lock) is an internal spinlock used by the database engine to protect shared memory structures. Specifically, buffer_mapping indicates that hundreds of processes are simultaneously trying to allocate or evict pages within the database's Buffer Pool (Shared Buffers), creating massive internal lock contention. The CPU is completely consumed by spinlock spinning (kernel context switching), not actual query execution. This typically happens when the Buffer Pool is too small for the working dataset, causing rapid buffer thrashing. Adding more CPU cores actually makes the problem *worse* because it allows more concurrent threads to spin and fight over the exact same internal memory lock. The fix is to increase shared_buffers or optimize the query to use an index and read fewer pages.",
     ["Identifies LWLock: buffer_mapping as extreme contention in the Shared Buffers pool", "Explains that CPU is wasted on spinlock context switching, not query execution", "Critically notes that adding CPU cores increases lock contention, worsening the outage"],
     ["Recommends adding more CPU cores to process the queries faster"]),

    ("B66_5_5", "scenario", "medium", "scenario", ["Observability & Diagnosis", "Performance & Tuning"],
     "You run EXPLAIN ANALYZE on a slow query and see this node: 'Index Scan using idx_users_status on users (cost=0.42..1500.50 rows=1000 width=8) (actual time=0.01..550.00 rows=15 loops=1)'. Compare the 'estimated' rows versus the 'actual' rows. What does this massive discrepancy indicate about the database's internal state?",
     "The planner estimated it would find 1,000 rows (rows=1000), but during execution, it actually found only 15 rows (rows=15). This massive discrepancy (nearly 100x overestimation) indicates that the table's internal statistics histograms are severely outdated or missing entirely. Because the planner believed there were 1,000 matches, it might have chosen a sub-optimal execution plan for subsequent JOIN operations higher up the tree (e.g., choosing a Hash Join instead of a Nested Loop). This indicates that the autovacuum or ANALYZE daemon is either failing, misconfigured, or has not run recently on the users table.",
     ["Identifies the delta between estimated 'rows=1000' and 'actual rows=15'", "Connects the overestimation to stale or missing database table statistics", "Diagnoses a failure in the autovacuum/ANALYZE background processes"],
     ["Claims the discrepancy means the index is corrupted and needs to be rebuilt"]),

    ("B66_5_6", "concept", "easy", "concept", ["Connection Management", "Database Architecture"],
     "Explain why 'Connection Exhaustion' happens so easily in PostgreSQL compared to asynchronous web servers (like Node.js), and why connection poolers (PgBouncer) are mandatory at scale.",
     "PostgreSQL uses a 'Process-per-Connection' architecture. Every single time a client connects, the master database process forks an entirely new, heavyweight operating system process (postgres: connection). Each process consumes a fixed chunk of RAM (often 2-10MB) just to idle. If an application opens 5,000 concurrent connections, it consumes 50GB of RAM just for connection overhead, triggering Out-Of-Memory (OOM) crashes and kernel context-switching exhaustion. Asynchronous web servers use single-threaded event loops (epoll/kqueue) that handle thousands of sockets with kilobytes of RAM. PgBouncer is mandatory because it sits in front of the database, accepts 10,000 lightweight client TCP connections, and multiplexes their queries over a small, highly controlled pool of 100 actual heavyweight PostgreSQL processes.",
     ["Identifies PostgreSQL's 'Process-per-Connection' heavyweight OS architecture", "Explains the massive RAM and context-switching penalty of thousands of idle connections", "Defines PgBouncer as a multiplexing proxy decoupling lightweight client TCP connections from heavyweight DB processes"],
     ["Claims PostgreSQL connections are limited by the database license key"]),

    ("B66_5_7", "implement", "hard", "implement", ["Observability & Diagnosis", "Database Internals"],
     "You want to monitor query performance in a production PostgreSQL database. How do you configure and utilize the pg_stat_statements extension to definitively identify the query consuming the most aggregate disk I/O over the last 24 hours?",
     "pg_stat_statements tracks execution statistics of all SQL statements executed by the server. 1) Configuration: Add pg_stat_statements to shared_preload_libraries in postgresql.conf and restart the DB, then run CREATE EXTENSION pg_stat_statements;. Ensure track_io_timing = on is set so block read times are recorded. 2) Identification Query: You execute a query sorting by the aggregate number of physical disk blocks read: SELECT query, calls, total_exec_time, shared_blks_read, shared_blks_hit FROM pg_stat_statements ORDER BY shared_blks_read DESC LIMIT 5;. 3) Timeframe: Because the statistics accumulate indefinitely, you must run SELECT pg_stat_statements_reset(); at the beginning of the 24-hour period, or capture a snapshot of the table at T1 and T2, subtracting the metrics to find the delta for the exact 24-hour window.",
     ["Identifies shared_preload_libraries configuration and CREATE EXTENSION requirement", "Provides the SQL logic: querying pg_stat_statements ordering by shared_blks_read DESC", "Crucially identifies the need to call pg_stat_statements_reset() or snapshot deltas to measure a specific time window"],
     ["Suggests reading the standard postgres.log file and using grep to count lines"]),

    ("B66_5_8", "tradeoff", "medium", "tradeoff", ["Analytics & OLAP", "Performance & Tuning"],
     "When designing an OLAP data warehouse, what is the tradeoff between a Star Schema and a Snowflake Schema?",
     "Star Schema denormalizes dimension tables (e.g., merging Cities, States, and Countries into a single flat Geography table directly attached to the Sales fact table). Advantages: Incredibly fast query performance and simpler SQL, because querying facts requires only a single, shallow JOIN to the dimension. Disadvantages: Data redundancy and higher storage costs. Snowflake Schema fully normalizes dimension tables (e.g., Sales joins Cities, which joins States, which joins Countries). Advantages: Eliminates data redundancy, saves storage space, and ensures absolute data integrity via cascading foreign keys. Disadvantages: Severe performance penalty due to the complex, multi-level chain of JOINs required to answer simple analytical questions. Modern OLAP heavily favors Star Schemas (or flat wide tables) because storage is cheap but CPU/join execution is expensive.",
     ["Defines Star Schema as denormalized dimensions (fast shallow JOINs, high storage cost)", "Defines Snowflake Schema as normalized dimension hierarchies (slow chained JOINs, low storage cost)", "Identifies the modern OLAP bias towards Star Schemas prioritizing CPU/speed over cheap storage"],
     ["Claims Star Schema is for NoSQL databases and Snowflake Schema is for Relational databases"]),

    ("B66_5_9", "diagnose", "hard", "debugging", ["Connection Management", "Concurrency"],
     "A Java/Spring Boot application uses HikariCP for connection pooling. During a database failover event (primary switches to a new IP), the application goes completely offline. The database is up, but the app logs show SocketTimeoutException or hanging connections indefinitely. Why didn't HikariCP recover, and what TCP/OS-level configuration is missing?",
     "When the primary database crashes or network routing changes suddenly, the established TCP sockets between HikariCP and the old database IP are left 'half-open'. The OS kernel on the application server does not realize the other side is dead, so HikariCP continues to wait indefinitely for TCP acknowledgments that will never arrive (TCP retransmission timeout can default to 15+ minutes). HikariCP believes the pool is full of healthy connections and hands them to application threads, which then hang forever. To fix this, you must configure TCP Keepalives at the OS/JDBC level. By setting tcpKeepAlive=true and tuning the OS kernel parameters (tcp_keepalive_time, tcp_keepalive_intvl), the OS actively probes idle sockets. If the probe fails, the OS forcefully terminates the dead socket, HikariCP detects the closure, drops the dead connections, and rapidly spins up new connections to the new IP.",
     ["Diagnoses 'half-open' TCP sockets hanging the connection pool during ungraceful IP swaps", "Explains that HikariCP hands out dead connections because the OS has not dropped the socket", "Prescribes enabling and tuning OS-level TCP Keepalives to forcefully probe and terminate dead sockets"],
     ["Recommends rebooting the Java application server whenever the database fails over"]),

    ("B66_5_10", "concept", "easy", "concept", ["Observability & Diagnosis", "Database Operations"],
     "In the context of database slow query logs, what is the difference between Wall-Clock time and CPU time?",
     "Wall-Clock time (Total Duration) is the exact physical time elapsed from the millisecond the database received the query to the millisecond it finished sending the result back to the client (what the user experiences). CPU Time is the actual amount of time the database processor spent actively executing calculations for that query. If a query has a Wall-Clock time of 5 seconds, but a CPU time of 0.01 seconds, it means the query was extremely fast to compute, but it spent 4.99 seconds waiting. It was likely blocked in a Lock Queue waiting for another transaction, waiting for a slow physical disk I/O read, or blocked waiting for network bandwidth to transmit a massive result set to the client.",
     ["Defines Wall-Clock time as total elapsed end-to-end duration", "Defines CPU Time as actual processing cycles utilized", "Explains that a large delta between the two indicates external waiting (locks, disk I/O, network)"],
     ["Claims Wall-Clock time includes the time spent rendering the HTML in the user's browser"]),

    ("B66_5_11", "scenario", "medium", "scenario", ["Observability & Diagnosis", "Execution Plans"],
     "An EXPLAIN ANALYZE output shows a 'Seq Scan on massive_table (cost=0.00..50000.00) (actual time=0.05..300.00) Filter: (status = 'ARCHIVED') Rows Removed by Filter: 5000000'. The developer immediately creates an index on status. The next day, EXPLAIN ANALYZE shows the exact same Seq Scan plan, and the query is still slow. Why did the optimizer ignore the new index?",
     "The optimizer ignored the index because of Low Selectivity. If massive_table contains 6 million rows, and the filter status = 'ARCHIVED' removes 5 million rows, it means the query returns 1 million rows (roughly 16% of the entire table). When a query returns a significant percentage of a table, an Index Scan is drastically slower than a Sequential Scan. An Index Scan must perform a random disk read for the index leaf, followed by a random disk read for the table heap, doing this 1 million times. A Sequential Scan ignores the index entirely, reads the table heap linearly from disk using highly optimized OS read-ahead buffers, and filters the rows in memory. The optimizer correctly calculated that doing massive random I/O (via the index) is mathematically more expensive than doing massive sequential I/O.",
     ["Identifies Low Selectivity (fetching a large percentage of the table) as the reason indexes are ignored", "Explains the extreme penalty of Random Disk I/O performed during Index Heap lookups", "Explains the extreme efficiency of Sequential OS Read-Ahead buffering for full table scans"],
     ["Suggests the database forgot to restart after the index was created"]),

    ("B66_5_12", "implement", "medium", "implement", ["Analytics & OLAP", "Database Operations"],
     "How do you partition a massive 10-year sales table in PostgreSQL by date, and what is the specific performance benefit of 'Partition Pruning' during analytical queries?",
     "To partition the table, you use Declarative Partitioning: CREATE TABLE sales (id int, created_at date) PARTITION BY RANGE (created_at);, followed by creating specific child tables: CREATE TABLE sales_2023 PARTITION OF sales FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');. The primary performance benefit is Partition Pruning. When an analytical query runs: SELECT SUM(amount) FROM sales WHERE created_at = '2023-05-05';, the query planner inspects the WHERE clause before execution. It knows mathematically that the requested date can only exist in the sales_2023 physical table. It completely drops (prunes) the other 9 years of partition tables from the execution plan. Instead of sequentially scanning a massive 10-year heap, the database scans a tiny 1-year file, massively accelerating performance and reducing I/O.",
     ["Provides exact declarative partitioning syntax: PARTITION BY RANGE and PARTITION OF", "Defines Partition Pruning as the optimizer mathematically eliminating child tables from the execution plan", "Highlights the massive I/O reduction by skipping irrelevant historical partitions entirely"],
     ["Claims partitioning compresses the old data using gzip to save space"]),

    ("B66_5_13", "tradeoff", "medium", "tradeoff", ["Connection Management", "Performance & Tuning"],
     "What is the tradeoff of using PgBouncer's 'Statement pooling' versus 'Transaction pooling' mode?",
     "Transaction Pooling mode assigns a database connection to a client for the duration of a BEGIN...COMMIT block. Advantages: Highly efficient, excellent concurrency multiplexing, and supports multi-statement ACID transactions safely. Disadvantages: Cannot use session-level features like Prepared Statements or SET LOCAL variables across the transaction. Statement Pooling mode is the most extreme form of multiplexing. It assigns a physical DB connection to a client only for the exact duration of a *single SQL statement*. Advantages: Maximum possible connection multiplexing; thousands of clients can share a tiny pool of 10 connections. Disadvantages: Absolutely destroys transactional integrity. You cannot use BEGIN...COMMIT blocks, because the BEGIN might execute on connection #1, and the UPDATE might execute on connection #2, completely breaking the ACID boundary. It is strictly limited to auto-commit queries (like simple web API reads).",
     ["Defines Transaction pooling multiplexing at the BEGIN/COMMIT boundary (safe for multi-step transactions)", "Defines Statement pooling multiplexing per-query (destroys transaction boundaries)", "Highlights the absolute restriction: Statement pooling breaks BEGIN/COMMIT ACID compliance"],
     ["Claims Statement pooling caches the SQL text while Transaction pooling caches the data"]),

    ("B66_5_14", "diagnose", "hard", "debugging", ["Observability & Diagnosis", "Database Internals"],
     "You are diagnosing latency in PostgreSQL using pg_stat_activity. A crucial backend process is hung in the wait_event_type = 'Client' and wait_event = 'ClientRead' state for 20 minutes, holding an AccessShareLock on a massive table and blocking DROP TABLE deployments. What is causing this, and how do you fix the application behavior?",
     "ClientRead means the database engine has finished executing the query or chunk of data and is completely idle, waiting for the client application over the TCP network to read the TCP buffer or send the next command in the transaction. This occurs when an application opens a transaction, executes a massive SELECT, and then begins iterating through the result set ResultSet.next() very slowly, doing heavy application-layer API calls or processing *while the transaction and network socket remain open*. The database is held hostage by the slow client. To fix this: the application must fetch the data, buffer it into application memory, immediately close the ResultSet and database transaction, and *then* perform the slow business logic processing offline, entirely decoupling the database lock duration from the application processing speed.",
     ["Identifies ClientRead as the database sitting idle waiting for a slow application over TCP", "Diagnoses the application anti-pattern: processing data synchronously while keeping the ResultSet/Transaction open", "Prescribes buffering data in RAM, closing the DB transaction immediately, then processing offline"],
     ["Claims ClientRead means the database is waiting for the hard drive to spin up"]),

    ("B66_5_15", "scenario", "medium", "scenario", ["Observability & Diagnosis", "Execution Plans"],
     "In an execution plan, you see a 'Hash Join (cost=100.00..50000.00)'. What do the two numbers inside the cost parentheses (e.g., 100.00 and 50000.00) specifically represent in PostgreSQL?",
     "The two numbers represent the 'Startup Cost' and the 'Total Cost'. The first number (100.00) is the Startup Cost: it represents the estimated amount of work/time required *before* the node can return its very first row. For a Hash Join, the startup cost is high because it must first sequentially scan the entire inner table and build the complete hash table in memory before it can begin matching and yielding results. The second number (50000.00) is the Total Cost: the estimated work/time required to process the node to completion and return every single row. Costs are not measured in milliseconds; they are arbitrary units relative to a single sequential page fetch from disk (seq_page_cost = 1.0).",
     ["Defines the first number as Startup Cost (cost to return the first row)", "Defines the second number as Total Cost (cost to process all rows)", "Explains the high startup cost of Hash Joins requiring full in-memory hash table construction before yielding"],
     ["Claims the numbers represent milliseconds and megabytes of RAM used"]),

    ("B66_5_16", "concept", "easy", "concept", ["Analytics & OLAP", "Database Operations"],
     "What is a 'Data Lake', and how does it differ fundamentally from a traditional 'Data Warehouse' in terms of schema validation (Schema-on-Write vs Schema-on-Read)?",
     "A Data Warehouse requires 'Schema-on-Write'. Before you can load data into it (via ETL), you must pre-define rigid, structured tables. If the incoming data format changes, the load pipeline crashes. Data Warehouses are highly optimized for structured SQL querying. A Data Lake (e.g., AWS S3 + Athena) is a massive storage repository that holds vast amounts of raw data in its native format (JSON, CSV, Parquet, images, logs). It uses 'Schema-on-Read'. You dump the data in without any prior structuring or validation. When you want to query it later, you apply a schema dynamically at the exact moment of the read operation. This provides immense flexibility for data scientists to explore raw unstructured data, but generally performs slower than a pre-optimized warehouse.",
     ["Defines Data Warehouse using 'Schema-on-Write' requiring strict upfront ETL formatting", "Defines Data Lake as a repository for raw, unstructured native data formats", "Defines 'Schema-on-Read' dynamically parsing the raw data structure at query time"],
     ["Claims a Data Lake is just a backup snapshot of a Data Warehouse"]),

    ("B66_5_17", "implement", "medium", "implement", ["Observability & Diagnosis", "Performance & Tuning"],
     "How do you configure PostgreSQL to automatically log queries that exceed a specific execution time threshold without requiring manual EXPLAIN profiling?",
     "You configure the log_min_duration_statement parameter in postgresql.conf. For example, setting log_min_duration_statement = '1000ms' instructs the database engine to automatically write any SQL statement that takes longer than 1 second to complete directly to the database error logs, along with its exact execution duration. This is critical for passive observability, as it continuously captures the slow 'heavy tail' queries impacting production without the massive performance penalty of setting log_statement = 'all' (which would log every single micro-query and exhaust disk space).",
     ["Identifies the exact configuration parameter: log_min_duration_statement", "Explains the mechanism of automatically writing long-running queries to the server logs", "Highlights the performance safety compared to blindly logging all statements"],
     ["Suggests writing a Bash script to parse the application logs for timeouts"]),

    ("B66_5_18", "diagnose", "hard", "debugging", ["Observability & Diagnosis", "Database Internals"],
     "Your monitoring system alerts that the PostgreSQL pg_xact (transaction status) directory is growing rapidly and disk space is nearly full. You check pg_stat_activity and find no long-running active queries. What hidden component (often related to Two-Phase Commit) causes pg_xact to balloon, and how do you diagnose it?",
     "The pg_xact (formerly pg_clog) directory stores the commit status (committed/aborted) of every transaction ID. It grows out of control when the global transaction ID horizon is held back, preventing the truncation of old logs. If there are no long-running active queries, the hidden culprit is almost always an orphaned 'Prepared Transaction' (from Two-Phase Commit, 2PC) or an abandoned 'Replication Slot'. Even if the client connection has disconnected, a transaction that executed PREPARE TRANSACTION remains indefinitely preserved in the database engine, holding its XID horizon and locking resources until a COMMIT PREPARED or ROLLBACK PREPARED is received. You diagnose it by querying SELECT * FROM pg_prepared_xacts; and manually issuing ROLLBACK PREPARED to clear the stalled transaction and allow pg_xact truncation.",
     ["Identifies orphaned 'Prepared Transactions' (2PC) or Replication Slots holding back the XID horizon", "Explains that disconnected clients do not automatically clear prepared transactions", "Recommends querying pg_prepared_xacts and issuing ROLLBACK PREPARED to release the log truncation hold"],
     ["Claims the pg_xact directory fills up because indexing is turned off"]),

    ("B66_5_19", "tradeoff", "medium", "tradeoff", ["Observability & Diagnosis", "Performance & Tuning"],
     "What is the performance tradeoff of executing EXPLAIN ANALYZE versus just EXPLAIN when diagnosing a slow query in a production environment?",
     "EXPLAIN simply asks the query planner to output its theoretical execution strategy (the mathematical estimation of costs, rows, and plan choices). It does NOT execute the query, takes milliseconds, and is perfectly safe to run in production. EXPLAIN ANALYZE actually *executes* the query physically in the database engine, gathers precise real-world timing and row counts at every node, and then rolls back (if it's a mutation) or returns the metrics. Tradeoff: While EXPLAIN ANALYZE provides the definitive, ground-truth performance data needed for diagnosis, running it on an unoptimized query in production might perform a massive 5-minute table scan, severely degrading overall database performance and burning CPU, making it a highly dangerous command for active production environments.",
     ["Defines EXPLAIN as returning mathematical estimations without executing (100% safe)", "Defines EXPLAIN ANALYZE as physically executing the query to gather actual timing metrics", "Warns of the massive production danger of running ANALYZE on a 5-minute unoptimized query"],
     ["Claims EXPLAIN ANALYZE is faster because it bypasses the database caches"]),

    ("B66_5_20", "scenario", "medium", "scenario", ["Connection Management", "Performance & Tuning"],
     "A microservices architecture features 50 identical pods. Each pod configures its local connection pool (e.g., HikariCP) with minimumIdle = 10 and maximumPoolSize = 50. The database limit max_connections is set to 1000. Why does this application continuously crash the database with 'too many clients already' errors during moderate traffic spikes, and how do you calculate correct pool sizes?",
     "The crash is caused by local pool multiplication. 50 pods * 50 max connections = 2,500 potential connections attempting to hit the database. During a traffic spike, the pods independently scale their local pools up to their max size, completely shattering the database's 1000 max_connections hard limit. To calculate correct pool sizes, you must look at the global architecture, not the local pod. The formula for the *maximum* possible connections must be (Pod Count * maxPoolSize) < Database Limit. If you have 50 pods and a 1000 DB limit, the absolute maximum maximumPoolSize per pod must be 20. Alternatively, introduce a centralized multiplexing proxy like PgBouncer in front of the DB, allowing the 50 pods to safely open 2,500 lightweight connections that are funneled into 100 actual database connections.",
     ["Diagnoses local connection pool multiplication exceeding global database limits (50 pods * 50 = 2500)", "Identifies the correct math: globally distributing the max_connections limit across the pod count", "Recommends a centralized proxy (PgBouncer) to safely absorb the massive distributed connection spike"],
     ["Suggests increasing the server RAM so it can handle infinite connections"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 5).")
    
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
    print("POST-BATCH AUDIT PART 5")
    print("========================================")
    print(f"Batch: 66 Part 5")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
