"""Batch 26 Part 2 question content (Database Developer). Targeted Gap Generation."""

ROLE = "Database Developer"

BUCKET_KEYS = {
    "DB_DISTRIBUTED": ("Distributed Databases", "Sharding & Consistency", "Databases", ["Backend Developer", "Data Architect"]),
}

Q = [
# ---------------- DB_DISTRIBUTED ----------------
("DB_DISTRIBUTED", "scenario", "medium", "scenario", ["Sharding"],
 "You are designing a sharded database. You choose `customer_id` as the Shard Key. After launch, you notice that 90% of the database CPU and Disk I/O is concentrated on a single shard, while the other 9 shards sit idle. What is this architectural failure called, and how do you prevent it?",
 "This is called a 'Hot Partition' or 'Hot Spot'. It occurs because the chosen Shard Key has an uneven access distribution (e.g., one massive enterprise customer generates 90% of the traffic). To prevent this, you must choose a Shard Key with a highly uniform access distribution, or implement compound sharding keys (e.g., `customer_id + entity_id`) to evenly scatter the high-volume data across the cluster.",
 ["Known as a 'Hot Partition' or 'Hot Spot'", "Caused by an uneven data or access distribution on a specific Shard Key", "Prevented by choosing a Shard Key with high cardinality and uniform access distribution"],
 ["The database server is physically overheating"]),

("DB_DISTRIBUTED", "explain", "hard", "concept", ["Distributed Transactions"],
 "Explain the 'Two-Phase Commit' (2PC) protocol used for Distributed Transactions. What is its primary operational vulnerability?",
 "2PC coordinates a transaction across multiple independent databases. Phase 1 (Prepare): The coordinator asks all nodes if they *can* commit; nodes write to their logs and exclusively lock resources. Phase 2 (Commit/Rollback): If all vote yes, the coordinator tells all to commit. Its massive operational vulnerability is that it is a 'blocking' protocol. If the Coordinator node crashes after Phase 1, the participant databases are trapped holding exclusive locks indefinitely, freezing the system.",
 ["Phase 1 (Prepare): Coordinator asks nodes to lock resources and prepare to commit", "Phase 2 (Commit/Rollback): Coordinator executes the final decision based on votes", "Vulnerability: It is a blocking protocol. If the coordinator crashes, participants hold locks indefinitely"],
 ["It requires users to type their password twice"]),

("DB_DISTRIBUTED", "tradeoff", "medium", "tradeoff", ["Sharding Strategies"],
 "What are the tradeoffs of using a Hash-based Sharding strategy versus a Range-based Sharding strategy?",
 "Hash sharding guarantees an extremely even distribution of data across all shards, effectively preventing hot spots. However, it completely destroys data locality, making range queries (e.g., `BETWEEN date A and date B`) impossibly slow because they must scatter-gather across every shard. Range sharding keeps related data together for blazing fast range queries, but is highly susceptible to hot partitions if recent data is accessed disproportionately.",
 ["Hash Sharding: Extremely even data distribution, but terrible for Range Queries (requires scatter-gather)", "Range Sharding: Blazing fast range queries (data locality)", "Range Tradeoff: Highly susceptible to Hot Partitions if traffic targets recent data"],
 ["Hash sharding encrypts the data, Range sharding does not"]),

("DB_DISTRIBUTED", "debug", "hard", "debugging", ["Eventual Consistency"],
 "You use a distributed NoSQL database like DynamoDB or Cassandra. A developer complains that they update a user's status to 'Active', but when they immediately query the database 10 milliseconds later, the status sometimes still reads 'Pending'. Why does this happen, and what consistency setting must be adjusted?",
 "The distributed database is architecturally configured for Eventual Consistency. The write successfully committed to Node A, but the subsequent rapid read hit Node B before the background replication process finished. To fix this, you must adjust the read request to use 'Strong Consistency' (e.g., `ReadConsistency=Strong` or Quorum reads), which forces the read operation to wait and coordinate with the cluster for the absolute latest agreed value.",
 ["The database is configured for Eventual Consistency", "The read hit a replica that hadn't received the background replication update yet", "Fix: Adjust the read request to use Strong Consistency / Quorum Reads"],
 ["The developer has a slow internet connection"]),

("DB_DISTRIBUTED", "fundamentals", "easy", "concept", ["CAP Theorem"],
 "In the context of database architecture, what does the CAP Theorem state?",
 "The CAP Theorem states that a distributed data store can simultaneously provide at most two out of three guarantees: Consistency (every read receives the most recent write), Availability (every request receives a non-error response), and Partition Tolerance (the system continues operating despite network drops between nodes). Because network partitions are inevitable in distributed systems, databases must fundamentally choose to prioritize either Consistency (CP) or Availability (AP).",
 ["Guarantees max 2 of 3: Consistency, Availability, Partition Tolerance", "Because network partitions are inevitable, systems must choose between Consistency or Availability", "Consistency: All nodes see the same data; Availability: All nodes respond to queries"],
 ["CAP stands for Create, Append, Purge"]),

("DB_DISTRIBUTED", "scenario", "medium", "scenario", ["Strong Consistency"],
 "A multi-region globally distributed database advertises 'Strong Consistency'. A user in Tokyo writes data, and a user in New York reads it 50 milliseconds later. The speed of light in fiber prevents data from traveling that fast. How does a strongly consistent global database handle the New York read request?",
 "The New York read request must be intentionally blocked by the database engine. The local New York node will not respond to the client until it has synchronously coordinated with the Tokyo node (or a majority cluster quorum) over the network to guarantee it has the absolute latest committed value. This results in significantly high latency for the reader in exchange for strict correctness.",
 ["The New York read request is intentionally blocked", "The local node must synchronously coordinate with Tokyo/Quorum over the WAN", "Results in high read latency in exchange for strict data correctness"],
 ["The database uses quantum entanglement to bypass the speed of light"]),

("DB_DISTRIBUTED", "implement", "medium", "implementation", ["Scaling"],
 "You have a massive 10TB PostgreSQL table that can no longer fit on a single machine. You must split the table across multiple physical PostgreSQL servers. What architectural technique do you implement, and how does the application know where to query?",
 "You must implement Database Sharding (Horizontal Partitioning). You partition the data across servers based on a designated Shard Key. To route queries, the application must introduce a routing layer (often handled by a smart ORM, a library like Citus, or a middleware proxy like ProxySQL) that mathematically hashes the Shard Key provided in the SQL query and routes the TCP connection to the correct physical database node.",
 ["Implement Database Sharding (Horizontal Partitioning) based on a Shard Key", "Introduce a routing layer (middleware proxy, Citus, or smart ORM)", "The routing layer hashes the Shard Key to determine the correct physical node"],
 ["Buy a 20TB flash drive and plug it into the server"]),

("DB_DISTRIBUTED", "tradeoff", "hard", "tradeoff", ["Distributed SQL"],
 "What is the tradeoff of using a fully ACID-compliant distributed SQL database (like CockroachDB or Spanner) compared to a traditional single-node RDBMS with asynchronous read replicas?",
 "Distributed SQL databases provide transparent global scalability, extreme fault tolerance, and guaranteed strong consistency across regions without manual sharding. The massive tradeoff is significantly higher write latency and lower raw peak throughput. Every single write must undergo complex distributed consensus (like Raft/Paxos) across multiple network nodes before committing, whereas a single-node RDBMS writes instantly to local disk.",
 ["Distributed SQL: Transparent global scale, extreme fault tolerance, strong consistency", "Tradeoff: Significantly higher write latency", "Writes require complex distributed consensus (Raft/Paxos) across network nodes before committing"],
 ["CockroachDB only survives nuclear attacks, not software bugs"]),

("DB_DISTRIBUTED", "explain", "medium", "concept", ["Consistent Hashing"],
 "Explain the concept of 'Consistent Hashing' in distributed databases like Cassandra. What specific operational problem does it solve when scaling out?",
 "In naive sharding (`hash(key) % N`), adding a single new database node changes `N`, forcing almost all existing data to be reshuffled across the network. Consistent Hashing maps physical nodes and data keys to a fixed conceptual ring. When a new node is added or removed, only the specific data mapped to its immediate adjacent neighbors on the ring is moved. This drastically minimizes network data reshuffling during scale-out operations.",
 ["Maps nodes and data keys to a fixed conceptual ring", "Solves the massive data reshuffling problem of naive modulo sharding", "When a node is added/removed, only adjacent neighbor data is moved, saving network bandwidth"],
 ["It ensures the hash is exactly the same length every time"]),

("DB_DISTRIBUTED", "debug", "medium", "debugging", ["ID Generation"],
 "A developer implements an incrementing primary key (`id SERIAL`) in a newly sharded database environment. Very quickly, insert queries begin failing with `DuplicateKeyException`. Why did the primary key generation fail?",
 "Standard auto-incrementing sequences are strictly local to a single physical database node. When sharded across multiple independent databases, Node A and Node B will both independently generate `id=1, 2, 3`. When the application queries the data globally, massive collisions occur. The architecture must switch to a decentralized distributed ID generation strategy, such as UUIDv4 or Twitter Snowflake IDs.",
 ["Auto-incrementing sequences are local to a single physical node", "Independent shards will generate identical IDs, causing massive collisions", "Must switch to decentralized generation like UUIDv4 or Snowflake IDs"],
 ["The database ran out of numbers"]),

("DB_DISTRIBUTED", "scenario", "hard", "scenario", ["CRDTs"],
 "You are designing a globally distributed collaborative text editor. Two users in different countries edit the exact same sentence while completely offline, and then both reconnect simultaneously. Which specific distributed database datatype or algorithm is required to automatically merge these edits without locking the entire document?",
 "You must architect the system using CRDTs (Conflict-free Replicated Data Types) or Operational Transformation (OT). These mathematical structures guarantee that concurrent, decentralized modifications can be merged in absolutely any order across the network and will always eventually result in the exact same final state on all nodes, entirely avoiding complex, slow locking mechanisms.",
 ["Must use CRDTs (Conflict-free Replicated Data Types) or Operational Transformation (OT)", "Mathematically guarantees that decentralized edits merge to the exact same final state", "Avoids distributed locking mechanisms entirely"],
 ["Use a global database lock to freeze the screen of the second user"]),

("DB_DISTRIBUTED", "fundamentals", "easy", "concept", ["Scaling"],
 "What is the difference between Vertical Scaling and Horizontal Scaling (Sharding) in database engineering?",
 "Vertical Scaling (Scaling Up) involves adding more CPU, RAM, and Disk to a single physical database machine; it requires no architectural changes but eventually hits a hard, expensive physical limit. Horizontal Scaling (Scaling Out / Sharding) involves splitting the data across multiple cheaper, smaller database machines; it provides infinite capacity but introduces massive architectural complexity for routing queries and managing distributed transactions.",
 ["Vertical (Up): Adding more CPU/RAM to a single machine (hits physical limits)", "Horizontal (Out): Splitting data across multiple machines (infinite capacity)", "Horizontal tradeoff: Introduces massive architectural complexity for queries and transactions"],
 ["Vertical scaling turns the server on its side"]),

("DB_DISTRIBUTED", "tradeoff", "medium", "tradeoff", ["Data Modeling"],
 "When querying a distributed NoSQL database, what is the operational tradeoff between using Secondary Indexes versus Denormalizing the data into multiple tables?",
 "Secondary indexes are easier to maintain, but they heavily degrade read performance at scale because a query must perform a 'Scatter-Gather' operation, hitting every physical shard in the cluster to find matching records. Denormalizing (duplicating the data into a new table specifically optimized for that query path) provides blazing fast reads on a single shard, but requires the application to maintain complex dual-write consistency on every update.",
 ["Secondary Indexes: Easy to maintain, but slow reads due to 'Scatter-Gather' across all shards", "Denormalization: Blazing fast, single-shard reads", "Denormalization tradeoff: Requires the application to manage complex dual-write consistency"],
 ["Denormalization is illegal in relational databases"]),

("DB_DISTRIBUTED", "implement", "hard", "implementation", ["Colocation"],
 "You are migrating a monolithic database to a sharded architecture. You have a `Users` table and an `Orders` table. The application frequently runs `SELECT * FROM Orders JOIN Users ON ...`. How must you configure your Shard Keys to ensure this JOIN remains performant and doesn't require pulling massive data into application memory?",
 "You must use 'Data Colocation' (or Co-partitioning). You configure `user_id` as the Shard Key for BOTH the `Users` table and the `Orders` table. This mathematically guarantees that a specific user and all of their associated orders are permanently stored on the exact same physical database shard, allowing the database engine to perform the JOIN locally and efficiently.",
 ["Use 'Data Colocation' (Co-partitioning)", "Use the same Shard Key (`user_id`) for both the Users and Orders tables", "Guarantees related data is on the exact same physical shard, allowing fast local JOINs"],
 ["You must download both tables to the frontend and join them in JavaScript"]),

("DB_DISTRIBUTED", "explain", "medium", "concept", ["Failure Detection"],
 "What is the 'Gossip Protocol' used in distributed databases like Cassandra, and what operational purpose does it serve?",
 "The Gossip Protocol is a decentralized, peer-to-peer communication mechanism. Instead of relying on a fragile, centralized master node to track cluster health, every node periodically exchanges state information (who is alive, who is dead, schema versions) with a few random peers. This information rapidly propagates through the cluster like a rumor, creating a highly resilient, masterless topology for failure detection.",
 ["A decentralized, peer-to-peer communication mechanism", "Nodes periodically exchange cluster state with random peers", "Creates a highly resilient, masterless topology for failure detection without a central bottleneck"],
 ["It is when databases leak user passwords to other databases"])
]
