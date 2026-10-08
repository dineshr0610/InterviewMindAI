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
    # Reactive Java (Project Reactor & WebFlux)
    ("B65_5_1", "diagnose", "hard", "debugging", ["Reactive Programming", "Project Reactor"],
     "In a Spring WebFlux application running on Netty, response latency suddenly degrades from 10ms to several seconds for all endpoints under load. A thread dump reveals that several reactor-http-nio-* threads are stuck in BLOCKED or WAITING state on a third-party caching library call. Why does blocking a single Netty thread degrade the entire WebFlux application, and how does Schedulers.boundedElastic() isolate blocking calls?",
     "Spring WebFlux on Netty runs on a non-blocking event-loop architecture with a very small thread pool (typically equal to the number of CPU cores). All incoming HTTP requests and reactive pipelines share these few reactor-http-nio-* event-loop threads. If a developer invokes a blocking operation (e.g., synchronous cache lookup, legacy SDK call, or file I/O) directly within the reactive pipeline, that event-loop thread cannot process any other requests or I/O events assigned to it. If all event-loop threads block, the entire server halts. To safely integrate blocking legacy code into WebFlux, offload the blocking call to a dedicated scheduler using publishOn(Schedulers.boundedElastic()) or Mono.fromCallable(blockingCall).subscribeOn(Schedulers.boundedElastic()). boundedElastic uses a dynamically sized, bounded thread pool specifically engineered for blocking I/O, shielding the Netty event loops.",
     ["Explains event-loop thread pool model sized to CPU core count", "Identifies blocking calls starving event loops and freezing unrelated channels", "Prescribes offloading blocking operations via Schedulers.boundedElastic()"],
     ["Recommends adding Thread.sleep() to wait for locks to clear"]),

    ("B65_5_2", "tradeoff", "medium", "tradeoff", ["Reactive Programming", "Project Reactor"],
     "What are the architectural tradeoffs of using Reactive Streams backpressure strategies (onBackpressureBuffer, onBackpressureDrop, onBackpressureLatest) when a fast producer overwhelms a slow consumer in Project Reactor?",
     "Backpressure coordinates data flow between producers and consumers. When a fast upstream producer emits items faster than a downstream subscriber can process: 1) onBackpressureBuffer() stores excess elements in a memory buffer. Tradeoff: Zero data loss, but unbounded buffers risk OutOfMemoryError under sustained load; bounded buffers require overflow drop strategies; 2) onBackpressureDrop() immediately discards excess items that downstream cannot handle. Tradeoff: Fixed, deterministic memory usage and zero consumer starvation, but causes data loss; suitable for real-time telemetry or sensor streams where outdated samples can be discarded; 3) onBackpressureLatest() drops older unconsumed items but always keeps the most recently emitted element. Tradeoff: Prevents unbounded memory growth while guaranteeing the consumer receives the latest state (ideal for UI dashboards or price tickers), but intermediate states are lost.",
     ["Analyzes onBackpressureBuffer() zero data loss vs OutOfMemoryError risk", "Analyzes onBackpressureDrop() bounded memory vs discarded items", "Analyzes onBackpressureLatest() maintaining latest state while skipping intermediate samples"],
     ["Claims backpressure automatically expands physical host RAM"]),

    ("B65_5_3", "concept", "medium", "concept", ["Reactive Programming", "Project Reactor"],
     "Why does Java's traditional ThreadLocal fail to propagate contextual data (like distributed trace IDs or tenant context) in Project Reactor, and how does Reactor's Context (ContextView) solve this?",
     "In imperative Java frameworks, a single thread handles an HTTP request from beginning to end, making ThreadLocal a reliable way to store request context. In Project Reactor, asynchronous pipelines switch execution across multiple different threads (e.g., from Netty event loop to boundedElastic worker pool, to I/O selector threads) at operator boundaries (publishOn, subscribeOn). As a result, ThreadLocal values are lost as soon as the thread switches. Reactor solves this via its immutable Context API. The Context is attached to the downstream Subscriber and flows upstream during the subscription phase. Any operator in the pipeline can read the context via Mono.deferContextual(ctx -> ...) or contextWrite(), allowing metadata (trace IDs, security tokens) to follow the reactive stream transparently across thread boundaries without relying on ThreadLocal.",
     ["Explains thread hopping across asynchronous operators breaking ThreadLocal guarantees", "Explains Reactor Context attached to Subscriber flowing upstream during subscription", "Uses Mono.deferContextual() and contextWrite() to propagate context safely"],
     ["Claims ThreadLocal works identically in reactive streams as in servlet threads"]),

    # Distributed Java Applications (Kafka & Tracing)
    ("B65_5_4", "diagnose", "hard", "debugging", ["Distributed Systems", "Apache Kafka"],
     "In a Spring Kafka consumer application, consumer pods repeatedly drop out of the consumer group, triggering continuous rebalance storms and duplicate message processing under heavy load. The Kafka broker logs show CommitFailedException and consumer group heartbeat timeouts. What is causing this, and how do max.poll.interval.ms and max.poll.records resolve it?",
     "Kafka consumers maintain group membership via background heartbeat threads. However, Kafka also enforces a maximum time between consecutive poll() invocations configured by max.poll.interval.ms (default 5 minutes). If a consumer fetches a batch of messages and processing takes longer than max.poll.interval.ms (due to slow database queries or downstream API timeouts), the Kafka coordinator presumes the consumer has died. The coordinator kicks the consumer out of the group and triggers a rebalance. When the consumer finally finishes and attempts to commit offsets, it throws CommitFailedException. The reassigned consumer then reprocesses the exact same batch, causing duplicate processing and triggering another timeout rebalance storm. Resolution: 1) Decrease max.poll.records (e.g., from 500 to 50) so each batch is smaller and finishes quickly; 2) Increase max.poll.interval.ms to give long tasks sufficient processing time; 3) Offload heavy processing to worker thread pools and commit offsets asynchronously.",
     ["Explains max.poll.interval.ms exceeded when batch processing takes too long", "Describes broker coordinator kicking slow consumer and triggering rebalance storms", "Tunes max.poll.records lower or increases max.poll.interval.ms to resolve issue"],
     ["Claims Kafka consumers rebalance due to GC heap memory corruption"]),

    ("B65_5_5", "concept", "medium", "concept", ["Distributed Systems", "Apache Kafka"],
     "How does an 'Idempotent Producer' in Apache Kafka (enable.idempotence=true) prevent duplicate messages in Java services, and why are sequence numbers assigned by the Java producer client?",
     "In distributed messaging, network transient failures can cause a producer to resend a message if it does not receive an ACK, leading to duplicates if the broker actually stored the original message. When enable.idempotence=true is enabled in the Java producer: 1) The broker assigns the producer a unique Producer ID (PID); 2) For each partition, the Java client assigns a strictly monotonically increasing Sequence Number to every record; 3) When the broker receives a record, it checks the incoming Sequence Number against the last committed sequence number for that PID and partition. If incomingSeq == lastSeq + 1, the broker accepts and commits it; if incomingSeq <= lastSeq, the broker acknowledges receipt but discards the duplicate write. This guarantees exactly-once delivery per partition from a single producer session without requiring distributed transactions.",
     ["Identifies Producer ID (PID) and sequence numbers assigned per partition", "Explains broker discarding duplicate writes where incomingSeq <= lastSeq", "Highlights prevention of retry duplication without requiring heavy two-phase commit transactions"],
     ["Claims idempotent producers delete duplicate consumer records from the database"]),

    ("B65_5_6", "tradeoff", "medium", "tradeoff", ["Distributed Systems", "Apache Kafka"],
     "What are the architectural tradeoffs of implementing Dead Letter Topics (DLT) with non-blocking retries using Spring Kafka's @RetryableTopic versus synchronous consumer retries?",
     "Synchronous consumer retries pause the Kafka consumer thread and re-attempt processing of the failed record in-place with backoff before advancing the partition offset. Tradeoff: Preserves strict in-order message processing within the partition, but Head-of-Line blocks the entire partition. If one poison message repeatedly fails, all subsequent messages in that partition are delayed, degrading consumer throughput. Spring Kafka's @RetryableTopic implements Non-Blocking Retries: failed messages are published to separate retry topics with increasing backoff delays (topic-retry-1000, topic-retry-5000) and ultimately to a DLT (topic-dlt), allowing the consumer to immediately commit the offset and continue processing subsequent records in the main topic. Tradeoff: Maintains high consumer throughput and isolates poison pills, but sacrifices strict message ordering across the partition.",
     ["Explains Head-of-Line blocking in synchronous consumer retries", "Explains non-blocking retry topics forwarding failed messages to delay/DLT topics", "Identifies tradeoff between strict message ordering and continuous consumer throughput"],
     ["Claims @RetryableTopic automatically fixes buggy message payloads"]),

    ("B65_5_7", "implement", "medium", "implement", ["Distributed Systems", "Observability"],
     "How do you configure distributed tracing in Spring Boot 3 using Micrometer Tracing and OpenTelemetry to propagate the traceparent (W3C Trace Context) header across outbound HTTP calls?",
     "In Spring Boot 3, add dependencies micrometer-tracing-bridge-otel and an exporter (like opentelemetry-exporter-otlp). Spring Boot automatically configures an ObservationRegistry and W3C TraceContextPropagator. When using Spring's RestClient, WebClient, or RestTemplate, you must create the client instance using their respective auto-configured builders (RestClient.Builder, WebClient.Builder, or RestTemplateBuilder). These builders automatically register Micrometer's Observation interceptors (ClientRequestObservationConvention). When an outbound HTTP request is executed, the interceptor injects the W3C traceparent: 00-{traceId}-{spanId}-{flags} and tracestate headers into the HTTP request headers, ensuring the downstream service correlates logs and spans into the same distributed trace.",
     ["Adds micrometer-tracing-bridge-otel and OTLP exporter dependencies", "Uses auto-configured client builders (RestClient.Builder, RestTemplateBuilder) to inherit Observation interceptors", "Explains injection of W3C traceparent and tracestate headers across network calls"],
     ["Manually concatenates random UUID strings in HTTP request headers"]),

    # Microservice Resilience (Resilience4j)
    ("B65_5_8", "concept", "easy", "concept", ["Resilience", "Resilience4j"],
     "What are the three primary states of a Resilience4j Circuit Breaker, and what triggers transitions between them?",
     "The three primary states are: 1) CLOSED: Normal operation. All requests pass through to the protected service. Resilience4j tracks call outcomes in a sliding window (count-based or time-based). If the failure rate or slow call rate exceeds the configured threshold (e.g., 50%), the circuit transitions to OPEN; 2) OPEN: Trip state. Requests fail fast immediately without calling the protected service, throwing CallNotPermittedException (or invoking fallbacks). The circuit remains OPEN for a configured waitDurationInOpenState (e.g., 10 seconds), after which it transitions to HALF_OPEN; 3) HALF_OPEN: Trial state. A limited number of test calls (permittedNumberOfCallsInHalfOpenState) are permitted. If success rate meets criteria, it transitions back to CLOSED; if failures persist, it transitions back to OPEN.",
     ["Defines CLOSED (normal), OPEN (fail fast), and HALF_OPEN (probing trial) states", "Identifies failure rate threshold triggering CLOSED -> OPEN transition", "Explains waitDurationInOpenState transitioning to HALF_OPEN and evaluation criteria"],
     ["Claims circuit breakers shut down the JVM operating system process"]),

    ("B65_5_9", "tradeoff", "medium", "tradeoff", ["Resilience", "Resilience4j"],
     "In Resilience4j, what is the architectural difference between a 'ThreadPoolBulkhead' and a 'SemaphoreBulkhead', and when should each be used?",
     "Bulkheads isolate system resources to prevent failures in one dependency from consuming all application resources. SemaphoreBulkhead controls the maximum number of concurrent executions using a lightweight semaphore counter on the calling thread. Tradeoff: Near-zero CPU and memory overhead with no thread context switching, but it does not provide execution timeouts or queueing, and the caller thread is still blocked by the underlying operation. ThreadPoolBulkhead executes tasks asynchronously on a dedicated, isolated thread pool with a bounded queue. Tradeoff: True resource isolation (caller thread is never blocked, and tasks can be cancelled or timed out independently), but introduces thread allocation overhead, thread pool management, and CPU context switching. Use Semaphore for fast in-process operations; use ThreadPool for slow, third-party remote I/O.",
     ["Contrasts SemaphoreBulkhead (calling thread, zero context switch, no timeout) with ThreadPoolBulkhead (isolated threads, queueing, timeout capability)", "Analyzes CPU overhead and memory tradeoffs between semaphores and thread pools", "Recommends appropriate use cases for each bulkhead type"],
     ["Claims bulkheads are used to compress database records on disk"]),

    ("B65_5_10", "diagnose", "medium", "debugging", ["Resilience", "Distributed Systems"],
     "An upstream microservice calls a downstream payment API with automatic retries (3 retries). During a minor database hiccup, downstream latency increases slightly. Suddenly, the entire payment service crashes under 4x normal request volume. What is 'Retry Amplification' (Retry Storm), and how does Exponential Backoff with Jitter prevent it?",
     "Retry Amplification occurs when multiple callers independently retry failed or timed-out requests simultaneously. If a downstream service slows down, 1,000 incoming requests trigger 3,000 retry attempts, multiplying traffic by 4x. This avalanche of retries overwhelms the already struggling service, pushing it into total collapse. If callers retry at fixed intervals, requests synchronize into periodic traffic surges. Exponential Backoff with Jitter prevents this: 1) Exponential backoff increases wait times exponentially after each failure (2^attempt * baseDelay), giving the downstream service breathing room to recover; 2) Jitter introduces random noise into the backoff delay (e.g., delay = random(0, baseDelay * 2^attempt)), desynchronizing client retry attempts and smoothing the traffic curve.",
     ["Explains retry amplification multiplying request load on degraded services", "Explains exponential backoff widening retry intervals", "Explains jitter adding random dispersion to break synchronization waves"],
     ["Claims retry storms are caused by hardware fan failures in data centers"]),

    # Testing & Debugging
    ("B65_5_11", "implement", "medium", "implement", ["Testing & Debugging", "Concurrency"],
     "Why are standard JUnit unit tests unreliable for catching concurrency bugs and race conditions in Java, and how does the Java Concurrency Stress test framework (jcstress) reliably detect memory model anomalies?",
     "Standard JUnit tests run single-threaded or execute ad-hoc multi-threaded threads in loops. Because JIT compiler optimizations, CPU cache coherence, and hardware memory reordering happen nondeterministically and are affected by OS thread scheduling, race conditions and JMM visibility bugs (like stale reads or torn writes) may only manifest once in a billion executions, passing JUnit suites consistently. jcstress (OpenJDK tool) is designed specifically to test hardware and JVM concurrency semantics. It annotates test classes with @JCStressTest and @Outcome, running state mutations across dedicated threads millions of times under varying CPU affinities, compiler tiers, and cache invalidation loops. It collects all observed result permutations and mathematically proves whether forbidden outcomes (violating JMM happens-before) occur.",
     ["Explains nondeterministic nature of JMM memory reordering and cache effects hiding bugs in JUnit", "Describes jcstress using @JCStressTest and @Outcome annotations", "Explains aggressive permutation testing across compiler tiers and CPU affinities to detect race outcomes"],
     ["Claims JUnit automatically catches all multi-threaded deadlocks"]),

    ("B65_5_12", "concept", "easy", "concept", ["Testing & Debugging", "Testcontainers"],
     "What is Testcontainers in Java, and how does the Ryuk container ensure cleanup of Docker containers created during integration test execution?",
     "Testcontainers is a Java library that provides lightweight, throwaway instances of real databases, message brokers, or web servers running inside Docker containers for integration tests. Instead of using mocks or in-memory databases (like H2), tests run against production-identical engines (PostgreSQL, Kafka). When a Java test process starts Testcontainers, Testcontainers launches a tiny sidecar container named 'Ryuk' (testcontainers/ryuk). Ryuk connects to the Docker daemon via a Unix socket. If the Java test suite finishes normally, or if the test process crashes, is killed, or JVM aborts abruptly, Ryuk monitors the connection; once the Java process disconnects, Ryuk automatically terminates and removes all Docker containers, networks, and volumes created during the test run, preventing orphaned containers from leaking host resources.",
     ["Defines Testcontainers providing throwaway containerized dependencies for integration testing", "Explains Ryuk sidecar container monitoring the JVM connection socket", "Describes Ryuk terminating orphaned containers and networks upon test crash or completion"],
     ["Claims Ryuk is a malicious virus that deletes Java code"]),

    ("B65_5_13", "diagnose", "hard", "debugging", ["Testing & Debugging", "Memory Management"],
     "You capture a heap dump (.hprof) from an application that crashed with OutOfMemoryError. In Eclipse Memory Analyzer (MAT), what is the difference between 'Shallow Heap' and 'Retained Heap', and how do you use the Dominator Tree to locate the leak suspect?",
     "Shallow Heap is the memory consumed by an object itself (its header, primitive fields, and reference pointers), typically 24 to 64 bytes. Retained Heap is the total amount of memory that would be freed by the garbage collector if that specific object were collected—it includes the object's shallow size plus the shallow sizes of all objects transitively reachable exclusively through it. An object with a tiny shallow heap (e.g., a HashMap node of 32 bytes) can have a gigabyte-scale retained heap. The Dominator Tree in MAT organizes objects into a tree where node X dominates node Y if every path from the GC roots to Y must pass through X. Opening the Dominator Tree immediately brings the objects with the largest Retained Heap to the top of the tree, exposing the single root object (e.g., an unbounded static cache) holding millions of child objects.",
     ["Distinguishes Shallow Heap (object's own size) from Retained Heap (total memory freed if collected)", "Explains Dominator Tree concept: node dominating all exclusively reachable descendants", "Identifies objects with highest retained heap at tree root as primary leak suspects"],
     ["Claims Shallow Heap and Retained Heap are always equal in size"]),

    # Build, Dependency & JVM Security
    ("B65_5_14", "tradeoff", "medium", "tradeoff", ["Build & Dependency", "Maven / Gradle"],
     "What is the fundamental difference in dependency conflict resolution between Apache Maven and Gradle, and how does Maven's 'Nearest Definition Wins' strategy cause unexpected NoSuchMethodError?",
     "Maven resolves dependency version conflicts using 'Nearest Definition Wins' based on the depth in the dependency tree (not version number). If dependency A brings library X:1.0 (depth 2) and dependency B brings X:2.0 (depth 3), Maven chooses X:1.0 simply because it is closer to the root pom, even though X:2.0 is newer. If dependency B compiled against a new method introduced in X:2.0, the JVM throws java.lang.NoSuchMethodError at runtime when B calls that method. In contrast, Gradle defaults to 'Newest Wins' (highest version), selecting X:2.0. To prevent runtime linkage errors in Maven: 1) Run mvn dependency:tree -Dverbose to detect conflicts; 2) Enforce consistent versions using dependencyManagement or the Maven Enforcer Plugin with the dependencyConvergence rule.",
     ["Contrasts Maven's 'Nearest Definition Wins' with Gradle's 'Newest Wins' strategy", "Explains older version selection causing runtime NoSuchMethodError in downstream callers", "Prescribes dependencyManagement or Maven Enforcer dependencyConvergence rule"],
     ["Claims Maven automatically compiles all conflicting dependency versions simultaneously"]),

    ("B65_5_15", "scenario", "medium", "scenario", ["Security", "Java Security"],
     "What makes Java Native Deserialization (ObjectInputStream.readObject()) inherently dangerous, what is a 'Gadget Chain', and how does JEP 290 Serialization Filtering mitigate remote code execution?",
     "Java native deserialization reconstructs objects by reading binary bytecode streams without invoking constructors. During deserialization, readObject() invokes internal callback methods on the deserialized classes. A Gadget Chain is a sequence of existing classes present on the application's classpath (e.g., Apache Commons Collections) whose methods chain together in unexpected ways (e.g., transforming a Map lookup into an arbitrary reflection or runtime command invocation: Runtime.getRuntime().exec()). If an attacker passes a crafted serialized binary payload, deserializing it executes arbitrary OS code. JEP 290 (Serialization Filtering) mitigates this by allowing developers and JVM administrators to define fine-grained pattern-based filters (jdk.serialFilter) specifying allowed class names, maximum object graph depth, array lengths, and total reference counts before classes are instantiated.",
     ["Explains readObject() invoking magic methods during deserialization without constructor checks", "Defines gadget chains linking existing classpath classes to achieve arbitrary command execution", "Explains JEP 290 serialization filters (jdk.serialFilter) validating class whitelists and graph bounds"],
     ["Claims deserialization is safe if data is transferred over HTTPS"]),

    ("B65_5_16", "concept", "medium", "concept", ["Security", "Spring Security"],
     "How can user input passed into Spring Expression Language (SpEL) parsers lead to Remote Code Execution (RCE), and how do you secure SpelExpressionParser?",
     "SpEL is a powerful expression language that supports method invocation, type referencing (T(java.lang.Runtime)), and constructor calls. If an application parses user-supplied strings directly using SpelExpressionParser.parseExpression(userInput).getValue(context), an attacker can inject malicious expressions like T(java.lang.Runtime).getRuntime().exec('id'), resulting in instant RCE. To secure SpEL: 1) Never evaluate untrusted, raw user input with SpEL; 2) If user expressions must be evaluated, replace StandardEvaluationContext with SimpleEvaluationContext (SimpleEvaluationContext.forReadOnlyDataBinding().build()). SimpleEvaluationContext explicitly restricts SpEL features: it disables Java type references (T(...)), disables constructor calls, and permits only basic property navigation and data binding, eliminating code execution vectors.",
     ["Identifies T(...) Java type referencing and method invocation in SpEL as RCE vectors", "Explains StandardEvaluationContext permitting arbitrary reflection and command execution", "Prescribes SimpleEvaluationContext for restricted data-binding evaluation"],
     ["Claims SpEL expressions only execute client-side in the web browser"]),

    # Containerized JVM Operations
    ("B65_5_17", "diagnose", "medium", "debugging", ["Containerized JVM", "JVM Performance"],
     "A Java 17 service running in a Kubernetes container with CPU limits set to cpu: 2.0 on a 64-core host machine exhibits unexpectedly poor performance and high GC pauses. You discover that the JVM initialized with 45 GC threads and 63 ForkJoinPool workers. Why did JVM ergonomics miscalculate CPU cores, and how does -XX:ActiveProcessorCount fix it?",
     "Older JVMs or misconfigured container runtimes (pre-container-aware JDKs or older cgroup v1 setups) inspect /proc/cpuinfo instead of cgroup quota limits, seeing all 64 host cores. The JVM ergonomics calculate GC parallel threads (ParallelGCThreads = cores * 5/8) and JIT/ForkJoinPool threads based on the 64 host cores rather than the 2 allocated cores. Spawning 45 GC threads and 63 ForkJoin threads on a container capped at 2 CPU cores causes catastrophic thread contention and CPU throttling: the OS CFS (Completely Fair Scheduler) quota is exhausted instantly by dozens of active threads, throttling the container for hundreds of milliseconds. Modern container-aware JVMs detect cgroup quotas automatically, but if overridden or in edge cases, you can explicitly set -XX:ActiveProcessorCount=2 to force JVM ergonomics to configure thread pools correctly.",
     ["Explains JVM reading host core count (/proc/cpuinfo) instead of cgroup quota", "Analyzes thread explosion causing severe OS CFS CPU quota throttling", "Sets -XX:ActiveProcessorCount to align JVM thread ergonomics with container limits"],
     ["Recommends disabling CPU limits in Kubernetes without investigation"]),

    ("B65_5_18", "tradeoff", "medium", "tradeoff", ["Containerized JVM", "Performance Tuning"],
     "What are the tradeoffs of using Class Data Sharing (CDS / AppCDS) versus standard JAR classloading for accelerating Java microservice startup times in Kubernetes?",
     "Application Class Data Sharing (AppCDS) dumps class metadata into an optimized, memory-mapped shared archive (.jsa file) during a training run. At runtime, the JVM maps the archive directly into memory, bypassing class file reading, parsing, and bytecode verification. Advantage: Reduces application startup time by 30-50% and reduces memory footprint across multiple JVM pods sharing the same host node. Tradeoff: Increases CI/CD container build pipeline complexity, as a preliminary training run must be executed during Docker image build to generate the .jsa file; any change in application JARs, classpath order, or dependencies invalidates the archive, requiring a full regeneration.",
     ["Explains memory-mapping shared archive (.jsa) bypassing class parsing and bytecode verification", "Quantifies startup time and memory footprint reduction", "Identifies CI/CD build complexity and invalidation upon classpath modifications as tradeoffs"],
     ["Claims AppCDS converts Java bytecode directly into C++ source files"]),

    ("B65_5_19", "scenario", "medium", "scenario", ["Distributed Systems", "Apache Kafka"],
     "In a Spring Kafka listener with manual ACK (ContainerProperties.AckMode.MANUAL_IMMEDIATE), a message processing fails due to a temporary network timeout. If the consumer does not call acknowledgment.acknowledge(), what happens to message delivery on subsequent polls and pod restarts?",
     "In Kafka, message offsets are maintained on the broker per partition. Calling acknowledgment.acknowledge() tells Spring Kafka to commit the consumer offset to the Kafka broker. If an error occurs and the application simply returns without calling acknowledge(), the offset is not committed. However, during the current running consumer session, subsequent calls to consumer.poll() will continue advancing and fetching new messages from the partition—Kafka does not automatically redeliver the unacknowledged message during the same session. The uncommitted message will only be redelivered if the consumer restarts (pod crash/deployment) or a consumer group rebalance occurs, at which point the consumer reads from the last committed offset, replaying all messages from the failure onward. To handle immediate retry within the session, the listener must throw an exception or delegate to a retry template.",
     ["Explains that uncommitted offsets remain uncommitted on the broker", "Clarifies that current consumer session continues polling subsequent messages without in-session redelivery", "Explains that redelivery occurs upon consumer restart or group rebalance from last committed offset"],
     ["Claims Kafka immediately pauses all partitions whenever acknowledge() is omitted"]),

    ("B65_5_20", "concept", "easy", "concept", ["JVM Internals", "Classloading"],
     "What is a ClassLoader leak in Java web applications, and how does storing objects in ThreadLocal without calling remove() cause the entire ClassLoader to remain uncollected?",
     "A ClassLoader can only be garbage collected when there are zero live references to the ClassLoader itself, and zero live references to any of the classes it loaded or their instances. When a web request thread stores a custom application object in a ThreadLocal variable and fails to call threadLocal.remove() in a finally block: 1) The thread belongs to the container's thread pool (e.g., Tomcat worker thread) and lives forever; 2) The thread's threadLocals map holds a strong reference to the application object; 3) The object references its Class; 4) The Class references its ClassLoader. When the web application is redeployed or undeployed, the container creates a new ClassLoader, but the old ClassLoader cannot be collected because the worker thread still holds the reference chain, leaking all class metadata in Metaspace and leading to OutOfMemoryError: Metaspace.",
     ["Traces reference chain: worker thread -> ThreadLocal map -> application object -> Class -> ClassLoader", "Explains why pooled container threads surviving application redeployment cause leaks", "Prescribes mandatory threadLocal.remove() in finally blocks to allow ClassLoader garbage collection"],
     ["Claims ThreadLocal variables are automatically erased on every HTTP response"])
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
    print("POST-BATCH AUDIT PART 5")
    print("========================================")
    print(f"Batch: 65 Part 5")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
