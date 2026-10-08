"""Batch 25 Part 3 question content (Java Developer). Targeted Gap Generation."""

ROLE = "Java Developer"

BUCKET_KEYS = {
    "JAVA_ARCH": ("Enterprise Architecture", "Distributed Systems & Resilience", "Java", ["Backend Developer", "Architecture"]),
}

Q = [
# ---------------- JAVA_ARCH ----------------
("JAVA_ARCH", "scenario", "medium", "scenario", ["Resilience"],
 "An enterprise Java application makes synchronous HTTP REST calls sequentially to User Service, Billing Service, and Notification Service to complete a checkout. If the Billing Service becomes extremely slow, the entire application eventually crashes. What architectural pattern must be implemented to prevent this cascading failure?",
 "You must implement the Circuit Breaker pattern (e.g., using Resilience4j). If the Billing service times out repeatedly, the circuit 'opens', instantly failing fast on subsequent calls. This immediately prevents the exhaustion of the calling service's thread pool, stopping the cascading failure and allowing the rest of the system to degrade gracefully.",
 ["Implement the Circuit Breaker pattern (e.g., Resilience4j)", "If a downstream service fails repeatedly, the circuit opens and fails fast", "Prevents thread pool exhaustion and cascading failures"],
 ["Tell the Billing team to buy faster servers"]),

("JAVA_ARCH", "implement", "medium", "implementation", ["Modularity"],
 "You are designing a modular Java 9+ application. You have a `core-service` module that uses an internal utility class `com.core.internal.SecretUtil`. How do you configure the `module-info.java` to explicitly prevent any other module from importing or reflecting on this internal class?",
 "You simply do NOT `export` the `com.core.internal` package in the module's `module-info.java` file. Java 9 modules strictly encapsulate unexported packages by default. Any other module attempting to compile against or use reflection on those internal classes will result in immediate compile-time or runtime access exceptions.",
 ["Do NOT `export` the package in `module-info.java`", "Java 9 modules strictly encapsulate unexported packages by default", "Prevents compilation and runtime reflection access from other modules"],
 ["Rename the class to `SecretUtil_DoNotUse`"]),

("JAVA_ARCH", "explain", "hard", "concept", ["Distributed Systems"],
 "In a distributed Java microservices architecture, explain the 'Outbox Pattern' and what specific data consistency problem it solves.",
 "When a service needs to save data to a database AND publish an event to Kafka, a crash between the two operations causes severe data inconsistency (no dual-commit). The Outbox Pattern solves this by saving the business data AND the event data to an 'outbox' table in the *same* database transaction. A separate, reliable background process then polls the outbox and publishes the events to Kafka, guaranteeing eventual consistency.",
 ["Solves the dual-commit problem between a database and a message broker", "Saves business data and event data to an outbox table in the SAME database transaction", "A background process polls the outbox and reliably publishes to the broker"],
 ["It is an email server configured in Java"]),

("JAVA_ARCH", "tradeoff", "medium", "tradeoff", ["Communication"],
 "What are the tradeoffs of using synchronous REST (HTTP/JSON) communication between internal Java microservices versus asynchronous event-driven messaging (e.g., Kafka/RabbitMQ)?",
 "REST is simple, highly traceable, and provides immediate success/failure feedback, but it creates tight temporal coupling and causes cascading failures if downstream services are slow. Event-driven messaging provides extreme loose coupling, robust asynchronous scaling, and temporal independence (services can be down temporarily), but it drastically complicates system observability, error handling, and forces the architecture to reason about eventual consistency.",
 ["REST: Simple, highly traceable, immediate feedback, but causes tight temporal coupling and cascading failures", "Messaging: Extreme loose coupling, temporal independence, robust scaling", "Messaging tradeoff: Complicates observability, error handling, and forces eventual consistency"],
 ["REST requires sleeping, Messaging does not"]),

("JAVA_ARCH", "debug", "hard", "debugging", ["JPA/Hibernate"],
 "You are using Spring Data JPA (Hibernate) in a Java service. You query a list of 100 `Author` entities. Then, a loop iterates through the authors, calling `author.getBooks().size()`. The database monitoring shows 101 separate SQL queries executed. What is this architectural anti-pattern called, and how do you fix it?",
 "This is the classic 'N+1 Query Problem'. 1 query loads the authors, and N (100) subsequent queries lazy-load the books for each author. Architecturally, you fix this by instructing Hibernate to eagerly fetch the association in a single query. You can do this by using a `JOIN FETCH` clause in custom JPQL, or by defining a JPA `@EntityGraph` on the repository method.",
 ["The 'N+1 Query Problem'", "1 query loads the parent entities, N queries lazy-load the children", "Fix: Use `JOIN FETCH` in JPQL or an `@EntityGraph` to eagerly load data in a single SQL query"],
 ["The database is charging you per query"]),

("JAVA_ARCH", "fundamentals", "easy", "concept", ["API Design"],
 "What is the primary purpose of the 'BFF' (Backend For Frontend) architectural pattern in enterprise Java ecosystems?",
 "The BFF pattern introduces a dedicated backend service tailored strictly for a specific frontend interface (e.g., a Mobile BFF vs a Web Dashboard BFF). It acts as an orchestrator, aggregating calls to multiple underlying domain microservices, shaping the complex JSON payloads specifically for that UI's needs, and hiding complex domain boundaries from the client.",
 ["A dedicated backend service tailored for a specific frontend UI (e.g., mobile vs web)", "Aggregates calls to multiple underlying microservices", "Shapes JSON payloads for the UI and hides complex domain boundaries"],
 ["BFF stands for Best Friends Forever"]),

("JAVA_ARCH", "scenario", "medium", "scenario", ["Scheduling"],
 "You deploy multiple instances of a Java scheduling service. Suddenly, background cron jobs (like sending daily emails) are being executed three times simultaneously. How do you architecturally solve this distributed scheduling problem in a stateless Java ecosystem?",
 "Stateless instances are blind to each other. You must implement a distributed lock or use a dedicated distributed scheduling framework (like Quartz with JDBC JobStore, or ShedLock). Before executing the cron job, the node attempts to acquire a centralized lock (in a Database or Redis); if it acquires the lock, it executes. If it fails, it skips the execution, guaranteeing only one node processes the job.",
 ["Stateless nodes execute cron jobs independently, causing duplicates", "Implement a distributed lock (Database/Redis) or use a framework like ShedLock/Quartz", "Nodes attempt to acquire the lock before execution; only the winner executes the job"],
 ["Tell the nodes to whisper to each other before executing"]),

("JAVA_ARCH", "tradeoff", "hard", "tradeoff", ["Event Sourcing"],
 "When architecting an Event Sourcing system in Java, what is the tradeoff between storing pure Domain Events (Event Sourcing) versus storing the final mutated State (CRUD)?",
 "Event Sourcing provides an absolute, immutable audit log, perfectly enables temporal queries (time travel), and avoids complex relational impedance mismatch on writes. The severe tradeoff is massive complexity in reading data: you must rebuild the current state by replaying all historical events. This requires building complex 'CQRS' read models (projections) and 'Snapshotting' mechanisms to maintain read performance.",
 ["Event Sourcing: Immutable audit log, time travel, fast append-only writes", "Tradeoff: Massive read complexity; must replay events to rebuild state", "Tradeoff: Requires CQRS read projections and snapshots to maintain query performance"],
 ["CRUD is an offensive word in Java"]),

("JAVA_ARCH", "explain", "medium", "concept", ["Observability"],
 "Explain 'Distributed Tracing' (e.g., OpenTelemetry, Zipkin) in a Java microservices environment. How does a trace correctly link a request traversing 5 different independent JVMs?",
 "A Distributed Trace tracks a transaction across process boundaries. It works by generating a unique `Trace ID` at the ingress gateway. Every Java service must extract this ID from incoming HTTP headers or Kafka records, log its local execution time as 'Spans', and crucially, propagate the exact same `Trace ID` forward into the headers of any outgoing downstream requests, linking all logs centrally.",
 ["Tracks a single transaction across multiple independent JVM boundaries", "Generates a unique `Trace ID` at the ingress gateway", "Services must extract the ID, log local 'Spans', and propagate the ID in downstream request headers"],
 ["It uses GPS trackers attached to the data packets"]),

("JAVA_ARCH", "implement", "easy", "implementation", ["Kubernetes"],
 "How do you implement a simple Health Check endpoint in a containerized Java application to inform Kubernetes when the application is actually ready to receive traffic, rather than just when the JVM process started?",
 "You expose a specific HTTP endpoint (e.g., `/health/ready`) that strictly verifies live connections to critical dependencies (like the Database or Redis). Kubernetes configures this endpoint as the `readinessProbe`. The JVM might be up and running, but Kubernetes won't route traffic to the pod until the database is reachable and the probe returns an HTTP 200.",
 ["Expose an HTTP endpoint (e.g., `/health/ready`)", "The endpoint must verify connections to critical dependencies (DB, Redis)", "Kubernetes uses this as a `readinessProbe` to control traffic routing"],
 ["Send an email to the Kubernetes administrator"]),

("JAVA_ARCH", "debug", "medium", "debugging", ["Sagas"],
 "A distributed transaction spanning a Java Inventory Service and a Java Payment Service fails. The Payment succeeds, but the Inventory fails. You realize you cannot use a standard database `ROLLBACK` because they are entirely separate databases. What architectural pattern must you implement to revert the Payment?",
 "You must implement the 'Saga Pattern', specifically Compensating Transactions. Because a technical SQL rollback is impossible across independent service databases, the Inventory service failure must trigger an asynchronous event back to the Payment Service, instructing it to execute specific, semantic business reversal logic (e.g., issue a financial refund to the user).",
 ["Implement the 'Saga Pattern' (Compensating Transactions)", "Technical SQL rollbacks are impossible across independent databases", "Execute semantic business reversal logic (e.g., issue a refund) upon failure"],
 ["Call the bank and apologize manually"]),

("JAVA_ARCH", "tradeoff", "medium", "tradeoff", ["Deployment"],
 "What are the tradeoffs of packaging an enterprise Java application as a massive 'Uber-JAR' (Fat JAR) versus a traditional WAR file deployed to an external application server (like WildFly/Tomcat)?",
 "Fat JARs embed the server (like Tomcat/Jetty) directly inside the jar, providing absolute environment parity, trivial Docker containerization, and easy execution (`java -jar`), but they create massive artifacts. Traditional WARs require managing, patching, and configuring heavy, external application servers separately, but they allow multiple distinct applications to share the exact same server memory footprint and connection pools.",
 ["Fat JARs: Embed the server, provide environment parity, trivial to containerize", "WARs: Require managing external application servers", "WAR tradeoff: Allows multiple apps to share the same server memory footprint and resources"],
 ["Fat JARs are illegal on airplanes"]),

("JAVA_ARCH", "scenario", "hard", "scenario", ["Kafka"],
 "You architect a Java microservice that consumes a high-volume Kafka topic. You configure the consumer to Auto-Commit offsets. The service fetches 100 records, processes 50, and then crashes due to an OutOfMemoryError. When the service restarts, it skips the remaining 50 records. Why, and how do you architecturally guarantee 'At-Least-Once' processing?",
 "Auto-commit acknowledges the Kafka offset in a background thread on a timer, completely independent of your actual processing logic. If it commits the offset *before* the processing finishes and then crashes, Kafka assumes all 100 records were processed successfully. To guarantee At-Least-Once processing, you must disable auto-commit and explicitly manually commit the offset only *after* the database transaction processing the records successfully commits.",
 ["Auto-commit acknowledges offsets on a background timer, independent of processing success", "If a crash occurs after the timer ticks, unprocessed records are skipped", "Fix: Disable auto-commit and manually commit offsets *after* successful business processing"],
 ["Kafka deleted the records to save disk space"]),

("JAVA_ARCH", "explain", "easy", "concept", ["REST"],
 "What is 'Idempotency' in the context of RESTful Java APIs, and which standard HTTP verbs are architecturally required to be idempotent?",
 "Idempotency means that executing the exact same request multiple times produces the exact same outcome on the server state as executing it only once, without unexpected duplicate side effects. According to REST standards, `GET`, `PUT`, and `DELETE` must be architecturally idempotent. `POST` is non-idempotent (e.g., executing it twice creates two resources).",
 ["Executing the same request multiple times produces the exact same server state as executing it once", "Prevents unexpected duplicate side effects", "`GET`, `PUT`, and `DELETE` must be idempotent; `POST` is non-idempotent"],
 ["It means the API only accepts integers"]),

("JAVA_ARCH", "fundamentals", "medium", "concept", ["CAP Theorem"],
 "In the context of the CAP Theorem, if a network partition occurs between your two distributed Java database nodes, you must choose between Consistency and Availability. Give a real-world example of an architecture choosing Availability over Consistency (AP).",
 "A classic AP architecture is an e-commerce Shopping Cart. If the master database node is unreachable, the system allows the user to continue adding items to a local or cached replica (remaining highly Available), accepting that the data might be temporarily out of sync across the cluster (sacrificing strict Consistency). It relies on 'eventual consistency' to merge the cart states once the network recovers.",
 ["Shopping Cart systems often choose Availability over strict Consistency (AP)", "Allows users to add items to a local replica during a network partition", "Relies on eventual consistency to merge states later, prioritizing uptime and revenue"],
 ["A banking transfer system (which actually requires strict Consistency)"])
]
