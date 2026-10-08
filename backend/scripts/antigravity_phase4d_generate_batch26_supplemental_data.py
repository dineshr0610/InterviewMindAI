"""Batch 26 Supplemental question content (Database Developer). Targeted Gap Generation."""

ROLE = "Database Developer"

BUCKET_KEYS = {
    "DB_OPERATIONS": ("Database Operations", "Migrations & Recovery", "Databases", ["Backend Developer", "Site Reliability Engineer", "Data Engineer"]),
}

Q = [
# ---------------- DB_OPERATIONS ----------------
("DB_OPERATIONS", "debug", "medium", "debugging", ["Performance Tuning"],
 "You run a heavily trafficked PostgreSQL database. The application team frequently queries a massive table using `ORDER BY created_at DESC LIMIT 10`, but they have not indexed the `created_at` column. The database CPU suddenly spikes to 100% and stays there, even though disk I/O remains extremely low. Why does a missing index on a sort operation cause a CPU spike rather than a disk I/O spike?",
 "Without an index providing pre-sorted data, the database engine must perform a complete 'In-Memory Sort' on every single query. If the data already resides in the cached Buffer Pool, the database reads the rows directly from RAM (causing near-zero disk I/O) and then uses the CPU to aggressively execute sorting algorithms (like QuickSort) on the entire massive dataset just to return the top 10 rows. This heavy computational sorting purely exhausts the CPU.",
 ["The database must perform a complete In-Memory Sort on every query", "Data is read from the cached RAM Buffer Pool, explaining the lack of disk I/O", "Sorting millions of rows in memory to return 10 purely exhausts the CPU"],
 ["The CPU is busy encrypting the data before sorting it"])
]
