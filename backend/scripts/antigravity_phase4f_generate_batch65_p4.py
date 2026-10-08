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

ROLE = "Java Developer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Spring Security Advanced
    ("B65_4_1", "diagnose", "hard", "debugging", ["Spring Security", "OAuth2"],
     "In a Spring Boot OAuth2 Resource Server validating JWTs from an external IdP (like Keycloak or Auth0), the IdP rotates its signing keys. Immediately, all API requests fail with 401 Unauthorized: Invalid signature. Why does NimbusJwtDecoder fail to pick up rotated keys, and how do you ensure zero-downtime key rotation?",
     "By default, Spring Security's NimbusJwtDecoder caches the JWK Set (retrieved from the jwks-uri endpoint) using an internal cache. If an incoming token arrives signed with a new kid (key ID) that is not in the cached JWK Set, Nimbus should refresh its cache. However, if the JWK Set endpoint was cached aggressively without TTL, or if Nimbus is configured with a static JWK source, or if downstream network rate limiting blocks JWK endpoint calls, the decoder throws a signature verification exception. To guarantee zero-downtime key rotation: 1) Configure NimbusJwtDecoder.withJwkSetUri(jwkSetUri).cache(cacheManager) with an appropriate cache TTL and refresh policy; 2) Ensure the IdP publishes the new public key to the JWKS endpoint well before issuing tokens signed with it (overlapping key lifecycle); 3) Ensure Spring Security allows JWK Set refetching on cache miss for unseen kid values.",
     ["Explains JWK Set caching behavior in NimbusJwtDecoder", "Identifies cache expiration, static sources, or rate limiting preventing new kid retrieval", "Prescribes overlapping key lifecycle in IdP and dynamic cache refetching on unseen kid"],
     ["Claims JWT secret keys must be hardcoded in application.properties"]),

    ("B65_4_2", "concept", "medium", "concept", ["Spring Security", "Security Context"],
     "Why does SecurityContextHolder.getContext().getAuthentication() return null inside a child thread spawned via CompletableFuture.supplyAsync() or a custom ExecutorService, and how do you propagate the security context?",
     "SecurityContextHolder uses a ThreadLocal strategy (MODE_THREADLOCAL) by default to store the SecurityContext. Because ThreadLocal variables are bound strictly to the thread that processed the incoming HTTP servlet request, any newly spawned worker thread has an empty context, returning null for getAuthentication(). To propagate the security context safely: 1) Wrap the ExecutorService using new DelegatingSecurityContextExecutorService(delegate); 2) Wrap specific tasks with DelegatingSecurityContextRunnable.create(task, SecurityContextHolder.getContext()); 3) In Spring configuration, configure SecurityContextHolder.setStrategyName(SecurityContextHolder.MODE_INHERITABLETHREADLOCAL) (though caution is required with thread pools where worker threads are reused, as InheritableThreadLocal can leak contexts across requests). The wrapping delegator pattern is the production standard.",
     ["Identifies ThreadLocal storage in SecurityContextHolder as boundary barrier", "Explains DelegatingSecurityContextExecutorService or DelegatingSecurityContextRunnable wrapping", "Analyzes risks of MODE_INHERITABLETHREADLOCAL in pooled thread executors"],
     ["Claims Spring Security automatically transfers context across all JVM threads"]),

    ("B65_4_3", "diagnose", "medium", "debugging", ["Spring Security", "Authorization"],
     "You add @PreAuthorize(\"hasRole('ADMIN')\") to a private or package-private helper method inside a Spring @Service class. Despite an unprivileged user calling the endpoint, the method executes without throwing AccessDeniedException. Why did method security fail to enforce authorization?",
     "Spring Security method-level authorization (@EnableMethodSecurity / @PreAuthorize) relies on Spring AOP proxies. Spring AOP proxies only intercept calls made to public methods invoked from external beans. Private methods cannot be intercepted by proxies because subclasses cannot override private methods, and package-private internal calls made within the same bean (this.helperMethod()) bypass the proxy completely. As a result, the AOP authorization advice is never executed. To enforce authorization: 1) Make the method public and call it across bean boundaries from another component; 2) Or use AspectJ compile-time / load-time weaving which can intercept private and intra-class calls; 3) Or place the @PreAuthorize annotation on the outer public entrypoint method.",
     ["Explains Spring AOP proxy interception limitation to public methods", "Identifies self-invocation bypassing AOP authorization advice", "Prescribes refactoring to public external methods or applying AspectJ weaving"],
     ["Claims @PreAuthorize requires a database connection to function"]),

    ("B65_4_4", "tradeoff", "hard", "tradeoff", ["Spring Security", "Architecture"],
     "What are the security and performance tradeoffs between Stateful Server-Side Sessions (Redis/HttpSession) and Stateless JWT tokens in enterprise Java microservice architectures?",
     "Stateless JWTs carry user claims and cryptographic signatures inside the token, eliminating server-side session lookup queries (zero database/cache I/O on authentication checks) and allowing easy horizontal scaling across microservices. Tradeoff: JWT revocation is notoriously difficult—if a user logs out, is banned, or permissions change, the token remains valid until it expires unless complex distributed token blacklists (which reintroduce state) are maintained. Furthermore, JWTs increase network bandwidth overhead on every HTTP request. Stateful sessions store a lightweight session ID cookie with data in a centralized store (e.g., Redis). Tradeoff: Instantaneous session revocation and permission updates, but introduces a single point of failure and database/cache network latency on every single request.",
     ["Highlights stateless scalability and zero-IO authorization of JWTs", "Analyzes severe revocation difficulty and token size overhead with JWTs", "Contrasts with immediate revocation and central state lookup latency in Redis sessions"],
     ["Claims JWT tokens are completely immune to security vulnerabilities"]),

    ("B65_4_5", "implement", "medium", "implement", ["Spring Security", "mTLS"],
     "How do you configure mutual TLS (mTLS) for inter-service communication in Spring Boot 3 using the new SSL Bundle abstraction?",
     "In Spring Boot 3.1+, configure SSL Bundles in application.properties: spring.ssl.bundle.jks.client-bundle.key.alias=client-cert, spring.ssl.bundle.jks.client-bundle.keystore.location=classpath:client.p12, spring.ssl.bundle.jks.client-bundle.keystore.password=secret, spring.ssl.bundle.jks.client-bundle.truststore.location=classpath:truststore.p12. On the server side, set server.ssl.bundle=client-bundle and server.ssl.client-auth=need to require client certificate authentication. For outbound clients (e.g., RestClient or WebClient), inject SslBundles sslBundles and apply the bundle: RestClient.builder().apply(sslBundles.getBundle('client-bundle').createClientHttpRequestFactoryBuilder()).build(). This standardizes keystore and truststore loading without manual SSLContext boilerplate.",
     ["Demonstrates Spring Boot 3 SSL Bundle configuration for keystore and truststore", "Configures server.ssl.client-auth=need for mutual authentication", "Applies SslBundles to RestClient or WebClient builders"],
     ["Recommends disabling SSL verification to simplify setup"]),

    ("B65_4_6", "concept", "easy", "concept", ["Spring Security", "Web Security"],
     "In a Spring Boot REST API consumed exclusively by mobile apps and SPA frontends using Bearer JWT tokens, why is it standard practice to disable CSRF protection (http.csrf(csrf -> csrf.disable()))?",
     "Cross-Site Request Forgery (CSRF) attacks occur when an attacker tricks a victim's browser into executing unwanted actions on a trusted site where the user is currently authenticated via ambient credentials (specifically, browser cookies automatically attached to cross-site requests). If an API uses stateless Bearer JWT authentication transmitted in the HTTP Authorization: Bearer <token> header, browsers do not automatically send Bearer tokens on cross-site requests. JavaScript running on an attacker's domain cannot access or attach the client's Bearer token. Therefore, CSRF attacks are technically impossible against header-based Bearer authentication, making CSRF protection unnecessary overhead.",
     ["Explains CSRF vulnerability relying on ambient browser cookie transmission", "Explains that Authorization Bearer headers are not automatically sent cross-origin", "Concludes CSRF protection is redundant for pure header-authenticated stateless REST APIs"],
     ["Claims CSRF protection encrypts user passwords"]),

    # Database & Java Interaction
    ("B65_4_7", "diagnose", "hard", "debugging", ["Database & Java", "HikariCP"],
     "A Java service logs frequent SQLTransientConnectionException: HikariPool-1 - Connection is not available, request timed out after 30000ms. Thread dumps show worker threads stuck waiting on HikariPool.getConnection(). How do you enable HikariCP leak detection, and how does it identify unclosed connections?",
     "Connection leaks occur when application code acquires a java.sql.Connection from HikariCP (via JDBC, JPA, or raw DataSource) and fails to close it (e.g., missing try-with-resources or transaction that never completes due to a hang). HikariCP provides a built-in leak detection mechanism configured via spring.datasource.hikari.leak-detection-threshold=2000 (time in milliseconds, min 2000ms). When a connection is borrowed, HikariCP schedules a tracking task. If the connection remains checked out longer than the threshold without being returned to the pool, HikariCP logs a warning: Apparent connection leak detected on connection ... accompanied by the exact thread stack trace where the connection was originally borrowed. This pinpoints the leaky method immediately.",
     ["Configures spring.datasource.hikari.leak-detection-threshold (e.g., 2000ms)", "Explains HikariCP capturing borrowing stack trace and logging apparent leak warnings", "Identifies unclosed connections or hung transactions as the underlying failure mode"],
     ["Claims HikariCP automatically increases the pool size to infinity when connections leak"]),

    ("B65_4_8", "tradeoff", "medium", "tradeoff", ["Database & Java", "HikariCP"],
     "Why does configuring HikariCP's maximumPoolSize to a very large number (e.g., 200) often degrade database throughput compared to a small pool size (e.g., 20-30)?",
     "The database server runs on hardware with a finite number of CPU cores and disk I/O channels. PostgreSQL, MySQL, and Oracle handle each connection with a dedicated process or thread. When 200 connections execute queries simultaneously on a 16-core server: 1) The OS scheduler spends more CPU time on thread context switching than executing query logic; 2) Database internal lock contention (latch contention, buffer pool contention) spikes dramatically; 3) Disk I/O queues become oversaturated. As described in the HikariCP pool sizing formula poolSize = Tn * (CPU_cores * 2) + effective_spindle_count, a smaller pool matches the database's true hardware parallelism. Keeping connections at 20-30 keeps the database CPU saturated with productive work rather than context-switch overhead, achieving higher transactions per second and lower overall latency.",
     ["Explains database hardware limits (CPU cores, disk channels, context switching)", "Analyzes latch contention, lock waiting, and OS scheduling thrash with 200 connections", "Cites pool sizing formula (cores * 2 + disk spindles) proving small pools maximize throughput"],
     ["Claims database throughput scales linearly with connection pool size"]),

    ("B65_4_9", "diagnose", "medium", "debugging", ["Database & Java", "Hibernate / JPA"],
     "What is the Hibernate N+1 query problem, how do you detect it in production application metrics, and how do you resolve it using @EntityGraph or JOIN FETCH?",
     "The N+1 problem occurs when an application loads an entity list of size N (1 query: SELECT * FROM authors), and then accesses a lazily loaded relationship on each entity (e.g., author.getBooks()). Because the relationship is lazy, Hibernate executes N additional independent SELECT queries (SELECT * FROM books WHERE author_id = ?) inside a loop—totaling 1 + N queries. In production, this shows up as sudden spikes in database query volume and high p99 response times. It can be detected using query counting interceptors in tests (datasource-proxy or HibernateQueryInterceptor). Resolution: 1) Use JPQL JOIN FETCH (SELECT a FROM Author a JOIN FETCH a.books) to load entities and relations in a single SQL JOIN; 2) Use @EntityGraph(attributePaths = {'books'}) on Spring Data repository methods to specify eager fetch plans dynamically.",
     ["Defines N+1 query pattern: 1 initial query followed by N secondary queries for lazy relations", "Detects issue via query counting tools or metric spikes in database query counts", "Resolves via JPQL JOIN FETCH or Spring Data JPA @EntityGraph"],
     ["Recommends making all JPA relationships FetchType.EAGER globally"]),

    ("B65_4_10", "concept", "easy", "concept", ["Database & Java", "Hibernate / JPA"],
     "In JPA / Hibernate, what is the 'First-Level Cache' (Persistence Context), and what is the difference between entityManager.persist() and entityManager.merge()?",
     "The First-Level Cache is bound to the active EntityManager session (typically per transaction). Any entity loaded or saved is cached by its primary key. Within the same transaction, repeated lookups of the same ID return the identical in-memory Java instance without executing additional SQL queries. persist() takes a new, transient entity instance, associates it with the persistence context, and marks it to be inserted into the database on flush. merge() is used for detached entities (instances not currently managed by the active session); it copies the state of the passed detached entity onto a newly fetched or existing managed entity in the persistence context and returns that managed instance (leaving the original passed instance detached).",
     ["Defines First-Level Cache bound to current EntityManager session / transaction", "Explains persist() making transient entity managed for INSERT", "Explains merge() copying detached state to a managed instance and returning it"],
     ["Claims First-Level Cache is shared across all JVM threads"]),

    ("B65_4_11", "scenario", "hard", "scenario", ["Database & Java", "Hibernate / JPA"],
     "A batch processing job inserts 500,000 records using Spring Data JPA repository.saveAll(). The application runs out of heap space (OutOfMemoryError: Java heap space) after 50,000 records. Why does JPA exhaust heap during large batch inserts, and how do you implement true JDBC batching?",
     "When inserting entities via JPA, Hibernate stores every managed entity in its First-Level Cache (persistence context) until the transaction commits. Inserting 500,000 entities means all 500,000 objects (and their dirty-checking snapshots) remain strongly referenced in memory, exhausting heap. Furthermore, if entity IDs are generated using GenerationType.IDENTITY, Hibernate cannot batch inserts because it must execute each INSERT immediately to retrieve the auto-generated ID from the database. Resolution: 1) Switch ID generation to GenerationType.SEQUENCE with an allocation size (e.g., 50); 2) Configure spring.jpa.properties.hibernate.jdbc.batch_size=50 and order_inserts=true; 3) Periodically call entityManager.flush() and entityManager.clear() every N entities (e.g., every 500 records) to flush SQL and evict objects from the first-level cache; 4) For massive volumes, bypass JPA entirely and use Spring JdbcTemplate.batchUpdate() with raw JDBC batching.",
     ["Identifies First-Level Cache and dirty-checking snapshot retention as root cause of OOM", "Explains why GenerationType.IDENTITY disables JDBC batching", "Prescribes entityManager.flush() and clear() eviction, or JdbcTemplate.batchUpdate()"],
     ["Recommends increasing JVM heap to 500GB without changing code"]),

    ("B65_4_12", "tradeoff", "medium", "tradeoff", ["Database & Java", "Hibernate / JPA"],
     "What is Hibernate 'Dirty Checking', how does it impact CPU and memory performance in long-running transactions, and how does @Transactional(readOnly = true) optimize it?",
     "When an entity is loaded into the Hibernate persistence context, Hibernate creates a deep copy snapshot of the entity's field values. Before transaction commit or query execution, Hibernate executes Dirty Checking: it iterates through all managed entities and compares their current field values against the stored snapshot. If changes are detected, it schedules an UPDATE query. In long-running transactions loading thousands of entities, dirty checking consumes significant CPU cycles and doubles the heap memory footprint. Adding @Transactional(readOnly = true) informs Hibernate to set the flush mode to FlushMode.MANUAL and disable dirty-checking snapshot creation. Hibernate does not track state changes, dramatically reducing heap allocation and accelerating query execution.",
     ["Explains initial snapshot copy and field comparison mechanism of Dirty Checking", "Identifies CPU overhead and memory footprint growth from snapshot retention", "Explains @Transactional(readOnly = true) disabling snapshots and setting FlushMode.MANUAL"],
     ["Claims dirty checking deletes corrupted records from the database"]),

    ("B65_4_13", "concept", "easy", "concept", ["Database & Java", "Concurrency"],
     "How does Optimistic Locking with @Version work in Spring Data JPA, and what exception is thrown when a concurrent update collision occurs?",
     "Optimistic Locking does not acquire database locks when reading data. Instead, the entity includes an integer or timestamp field annotated with @Version. When reading an entity, Hibernate reads the version (e.g., version = 1). When updating, Hibernate appends the version check to the SQL WHERE clause: UPDATE product SET stock = 5, version = 2 WHERE id = 10 AND version = 1. If another transaction updated the row in the meantime, the WHERE clause finds 0 rows, and Hibernate detects that the row was modified concurrently. Hibernate throws OptimisticLockException (wrapped by Spring Data as ObjectOptimisticLockingFailureException). The application can catch this exception and retry the business operation.",
     ["Explains @Version column included in UPDATE WHERE clause", "Describes detection when zero rows are updated", "Identifies OptimisticLockException / ObjectOptimisticLockingFailureException"],
     ["Claims @Version acquires exclusive database table locks"]),

    ("B65_4_14", "implement", "hard", "implement", ["Database & Java", "Architecture"],
     "How do you implement dynamic database Read/Write replica routing in a Spring Boot application using AbstractRoutingDataSource and @Transactional(readOnly = true)?",
     "Subclass org.springframework.jdbc.datasource.lookup.AbstractRoutingDataSource. Override determineCurrentLookupKey(). Define a ThreadLocal context holder (or inspect TransactionSynchronizationManager.isCurrentTransactionReadOnly()). Configure a master DataSource and one or more read replica DataSources, registering them in a target data sources map passed to setTargetDataSources(). Set the master as the default. In determineCurrentLookupKey(), if TransactionSynchronizationManager.isCurrentTransactionReadOnly() is true, return 'REPLICA', otherwise return 'PRIMARY'. Spring's AbstractRoutingDataSource dynamically selects the replica connection when executing @Transactional(readOnly = true) and the primary connection for write transactions. Note: To ensure Spring opens the connection after determining the transaction read-only flag, wrap the routing datasource in a LazyConnectionDataSourceProxy.",
     ["Subclasses AbstractRoutingDataSource and overrides determineCurrentLookupKey()", "Inspects TransactionSynchronizationManager.isCurrentTransactionReadOnly() to route to replica", "Emphasizes LazyConnectionDataSourceProxy to defer connection acquisition until query execution"],
     ["Creates separate application instances for reading and writing"]),

    ("B65_4_15", "diagnose", "medium", "debugging", ["Database & Java", "Hibernate / JPA"],
     "In a Spring Boot controller, accessing a lazy-loaded collection after the service method returns throws LazyInitializationException: could not initialize proxy - no Session. Why did this happen, and why is spring.jpa.open-in-view=true considered an anti-pattern to fix it?",
     "The JPA EntityManager session is bound to the transaction boundary defined by @Transactional at the service layer. When the service method completes, the transaction commits and the Hibernate session closes. When the web layer attempts to serialize the entity into JSON, Jackson calls the getter on the lazy proxy, but because there is no open session, Hibernate throws LazyInitializationException. Enabling open-in-view=true (OSIV) keeps the database connection and session open across the entire HTTP request rendering phase. This is an anti-pattern because: 1) It holds database connections from the HikariCP pool while transmitting slow network responses to clients, causing connection pool exhaustion; 2) It hides N+1 queries triggered during JSON serialization. The proper fix is to map entities to DTOs within the service transaction using JOIN FETCH or EntityGraphs.",
     ["Explains session closure at transaction boundary triggering LazyInitializationException during serialization", "Identifies Open Session In View (OSIV) anti-pattern holding connections during HTTP I/O", "Recommends DTO projections and JOIN FETCH within service layer"],
     ["Recommends converting all database columns to VARCHAR"]),

    ("B65_4_16", "tradeoff", "hard", "tradeoff", ["Database & Java", "Architecture"],
     "What are the architectural tradeoffs of handling optimistic locking collisions via Exponential Backoff Retries versus using Pessimistic Locking (SELECT FOR UPDATE) in high-contention inventory updates?",
     "Optimistic locking with exponential backoff retries assumes conflicts are rare. It avoids holding database row locks during business logic, maximizing read throughput and eliminating database deadlocks. However, under high contention (e.g., flash sale where 10,000 users buy the last 10 units), optimistic updates suffer from Retry Storms: hundreds of threads repeatedly fail, re-read, recalculate, and retry, burning massive CPU and database I/O while only one transaction succeeds per round. In high-contention scenarios, Pessimistic Locking (PESSIMISTIC_WRITE / SELECT ... FOR UPDATE) is far superior: the first transaction acquires an exclusive row lock; subsequent transactions wait their turn in the database queue, execute sequentially without retries, and exit cleanly. Tradeoff: Pessimistic locks risk deadlocks if lock acquisition order is not strictly deterministic, and hold open database connections longer.",
     ["Analyzes retry storms and CPU/IO thrashing under high-contention optimistic locking", "Explains serialized execution benefits of Pessimistic Locking (PESSIMISTIC_WRITE)", "Identifies deadlock risks and longer connection holding times with pessimistic locks"],
     ["Claims pessimistic locking allows unlimited concurrent updates"]),

    ("B65_4_17", "implement", "medium", "implement", ["Database & Java", "JDBC"],
     "How do you use Spring's JdbcTemplate.batchUpdate() with ParameterizedPreparedStatementSetter to execute high-throughput batch inserts with deterministic chunking?",
     "Inject JdbcTemplate. Use batchUpdate(String sql, Collection<T> batchArgs, int batchSize, ParameterizedPreparedStatementSetter<T> pss): jdbcTemplate.batchUpdate('INSERT INTO audit_log (id, message, created_at) VALUES (?, ?, ?)', logs, 1000, (ps, log) -> { ps.setString(1, log.getId()); ps.setString(2, log.getMessage()); ps.setTimestamp(3, Timestamp.from(log.getCreatedAt())); });. Spring executes the batch in chunks of 1000, calling ps.addBatch() and dispatching executeBatch() over the underlying JDBC connection. This minimizes network round-trips to the database and eliminates all ORM entity tracking overhead.",
     ["Uses JdbcTemplate.batchUpdate() with ParameterizedPreparedStatementSetter and chunk size", "Binds parameters in lambda (ps, item)", "Explains avoiding ORM persistence context overhead for massive ingest"],
     ["Executes single INSERT statements inside a standard for-loop"]),

    ("B65_4_18", "concept", "easy", "concept", ["Database & Java", "Hibernate / JPA"],
     "What is the difference between CascadeType.REMOVE and orphanRemoval = true in JPA entity relationships?",
     "CascadeType.REMOVE specifies that when the parent entity is explicitly deleted (e.g., entityManager.remove(parent)), the deletion cascades to all associated child entities. However, if you simply remove a child entity from the parent's collection (parent.getChildren().remove(child)), CascadeType.REMOVE does nothing—the child remains in the database with its foreign key set to null or orphaned. In contrast, orphanRemoval = true goes further: whenever a child entity is dereferenced or removed from the parent's collection, JPA automatically executes a SQL DELETE statement for that child entity. It also automatically cascades deletions when the parent is deleted.",
     ["Explains CascadeType.REMOVE only triggering on explicit parent deletion", "Explains orphanRemoval = true triggering SQL DELETE upon removing from Java collection", "Highlights orphanRemoval preventing orphaned rows in database"],
     ["Claims orphanRemoval = true drops the database table"]),

    ("B65_4_19", "diagnose", "hard", "debugging", ["Database & Java", "Transactions"],
     "In a Spring Boot application, two concurrent transactions update different rows in table A and table B, but the database terminates one with Deadlock found when trying to get lock; try restarting transaction. How do you identify application access patterns causing database deadlocks from application logs?",
     "Database deadlocks occur when Transaction 1 updates Table A then Table B, while concurrent Transaction 2 updates Table B then Table A. In application logs, this manifests as CannotAcquireLockException or DeadlockLoserDataAccessException. To diagnose: 1) Inspect database engine status (e.g., SHOW ENGINE INNODB STATUS in MySQL or PostgreSQL deadlock logs) to extract the two conflicting SQL statements, lock modes (X lock on index records), and transaction IDs; 2) Correlate the SQL statements with Spring service methods using distributed tracing (correlation IDs) or SQL query logging; 3) Identify that the two service endpoints update shared tables in inverse order. The permanent fix is enforcing Global Lock/Update Ordering across the application: ensure all business services update tables and rows in the exact same deterministic sequence.",
     ["Explains inverted table/row update sequences across concurrent transactions causing cycle", "Uses engine deadlock status reports (e.g., SHOW ENGINE INNODB STATUS) to correlate SQL statements", "Prescribes Global Update Ordering across application business logic"],
     ["Suggests disabling database transactions entirely to fix deadlocks"]),

    ("B65_4_20", "tradeoff", "medium", "tradeoff", ["Database & Java", "Architecture"],
     "What are the tradeoffs between using Spring Data JPA Specifications (Criteria API) versus Querydsl for dynamic multi-filter database queries?",
     "Spring Data JPA Specifications utilize the standard JPA Criteria API (org.springframework.data.jpa.domain.Specification). Advantage: No external code generation plugins or compilation steps required; it is built directly into Spring Data JPA. Tradeoff: The Criteria API is notoriously verbose, hard to read, and lacks compile-time safety on attribute string names unless JPA metamodel generation is configured. Querydsl generates type-safe query classes (e.g., QUser) at build time via an annotation processor. Advantage: Clean, fluent, highly readable syntax, and total compile-time type safety (renaming an entity field breaks compilation immediately rather than failing at runtime). Tradeoff: Requires configuring annotation processing in Maven/Gradle, and adds third-party library dependencies and build complexity.",
     ["Evaluates Criteria API built-in availability versus verbose syntax and string-based unsafe attributes", "Highlights Querydsl compile-time type safety via generated Q-classes and readable fluent DSL", "Notes Querydsl requirement for annotation processing plugins in build lifecycle"],
     ["Claims Querydsl bypasses the database completely"])
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
            "applicable_roles": ["Backend Developer", "Software Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Java",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "Software Engineering",
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
    print(f"Batch: 65 Part 4")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
