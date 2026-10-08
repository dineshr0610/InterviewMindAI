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
    # Java Networking & I/O
    ("B65_3_1", "diagnose", "hard", "debugging", ["Networking", "Netty"],
     "In a high-throughput Java Netty service, you notice that direct memory usage grows steadily until the JVM crashes with OutOfMemoryError: Direct buffer memory. JFR logs show millions of ByteBuf allocations without corresponding releases. What is Netty's ByteBuf reference counting mechanism, and how do you use ResourceLeakDetector to pinpoint the leaked buffer?",
     "Netty ByteBuf instances (specifically pooled and direct buffers) manage their lifecycle via explicit reference counting (ReferenceCounted). Every allocated buffer starts with a refCnt of 1. Calling retain() increments it, and release() decrements it; when refCnt reaches 0, the underlying direct memory is recycled to the pool or freed. If a channel handler creates or consumes a ByteBuf and fails to call release() (or fails to pass it down the pipeline via ctx.fireChannelRead()), the buffer leaks. Netty includes ResourceLeakDetector to catch this. In production, run with -Dio.netty.leakDetection.level=ADVANCED or PARANOID (which samples 100% of buffer allocations). Netty records allocation and access stack traces in a phantom reference queue; when a buffer is garbage collected with refCnt > 0, Netty logs an ERROR: LEAK: ByteBuf.release() was not called before it's garbage-collected along with the exact call site where the buffer was allocated.",
     ["Explains ReferenceCounted lifecycle: retain() increments and release() decrements", "Identifies handler forgetting to release or forward buffer as root cause", "Explains configuring ResourceLeakDetector level to ADVANCED or PARANOID to print allocation stack traces"],
     ["Claims Java garbage collector frees direct ByteBuf buffers immediately without release()"]),

    ("B65_3_2", "tradeoff", "medium", "tradeoff", ["Networking", "JVM Networking"],
     "What are the architectural tradeoffs of using HTTP/2 multiplexing via Java 11+ java.net.http.HttpClient versus HTTP/1.1 persistent connection pooling (e.g., Apache HttpClient) for inter-service communication?",
     "HTTP/1.1 connection pooling maintains multiple separate TCP connections to each target host. While established connections can be reused (Keep-Alive), each TCP connection can only handle one request-response cycle at a time (Head-of-Line blocking at HTTP level). This requires large connection pools (e.g., 50-200 sockets per route), leading to socket exhaustion and high memory overhead. In contrast, Java 11+ HttpClient supports HTTP/2, which enables request multiplexing over a single TCP connection using binary streams. Multiple concurrent requests travel interleaved over the single socket, eliminating HTTP Head-of-Line blocking and drastically reducing TCP handshake/TLS overhead and file descriptors. Tradeoffs: 1) Under packet loss on high-latency networks, TCP Head-of-Line blocking affects ALL multiplexed HTTP/2 streams on that socket; 2) Flow control window management (WINDOW_UPDATE) adds CPU complexity; 3) HTTP/2 multiplexing requires downstream services to handle concurrent streams without socket backpressure.",
     ["Explains HTTP/1.1 head-of-line blocking requiring multiple pooled TCP connections", "Explains HTTP/2 multiplexing streams over a single TCP connection reducing socket exhaustion", "Identifies TCP packet loss impact on multiplexed streams and flow control tradeoffs"],
     ["Claims HTTP/2 uses UDP sockets inside java.net.http.HttpClient"]),

    ("B65_3_3", "scenario", "hard", "scenario", ["Networking", "JVM Networking"],
     "During a cloud database failover, your Java backend continues attempting to connect to the old IP address for 10 minutes, failing health checks, even though DNS records updated in 5 seconds. Why does the JVM cache DNS resolutions, and how do you configure DNS TTL in Java services?",
     "By default, the OpenJDK JVM caches DNS lookups forever if a security manager is enabled, or caches for 30 seconds (networkaddress.cache.ttl=30) if no security manager is present (or indefinitely in older JDKs). Furthermore, negative DNS lookups (failed domain resolutions) are cached for 10 seconds (networkaddress.cache.negative.ttl=10). To prevent DNS caching from breaking cloud failovers: 1) Configure the JVM security property by adding -Dsun.net.inetaddr.ttl=10 or setting networkaddress.cache.ttl=10 in $JAVA_HOME/conf/security/java.security or programmatically via java.security.Security.setProperty('networkaddress.cache.ttl', '10') during startup; 2) Ensure HTTP connection pools (e.g., Apache HttpClient or WebClient) configure connection time-to-live (setConnectionTimeToLive(10, TimeUnit.SECONDS)) so pooled sockets close and re-resolve DNS rather than remaining open indefinitely.",
     ["Explains JVM default infinite or long DNS caching via networkaddress.cache.ttl", "Demonstrates configuring networkaddress.cache.ttl in java.security or via system properties", "Highlights need to bound HTTP/database connection pool TTL to trigger DNS re-resolution"],
     ["Recommends rebooting the Linux operating system to clear Java DNS cache"]),

    ("B65_3_4", "concept", "easy", "concept", ["Networking", "JVM Networking"],
     "What is the critical difference between 'Connection Timeout' (connectTimeout) and 'Read Timeout' (socketTimeout) in Java HTTP and database clients?",
     "Connection Timeout defines the maximum time the Java client will wait to establish the initial network socket connection to the target server (including TCP three-way handshake and TLS handshake). If the target server is down, unreachable, or dropped by a firewall, the client throws SocketTimeoutException or ConnectException when this timeout expires. Read Timeout (or Socket Timeout) begins AFTER the connection is successfully established and the request is sent; it defines the maximum time the client will wait for incoming data packets from the server between consecutive read operations. If the server accepts the connection but takes too long to process a database query or generate a response, the read timeout expires.",
     ["Distinguishes initial TCP/TLS handshake phase (connection timeout) from data arrival phase (read timeout)", "Explains socketTimeout measuring gap between incoming packets during request processing", "Identifies appropriate exception types thrown on timeout expiration"],
     ["Claims connection timeout and read timeout are identical parameters"]),

    ("B65_3_5", "diagnose", "medium", "debugging", ["Networking", "JVM Networking"],
     "A high-throughput Java service throws java.net.BindException: Address already in use: connect when opening outbound HTTP connections under peak load, despite only 500 concurrent users. What is ephemeral port exhaustion, and how do you resolve it?",
     "Every outbound TCP connection created by a Java client requires an ephemeral (source) port allocated by the operating system. When an HTTP connection is closed by the client, the TCP socket transitions to the TIME_WAIT state for 60-120 seconds (2 * MSL) to ensure stray packets are flushed from the network. If the Java application creates a new HTTP client or new socket for each request (e.g., new RestTemplate() or HttpURLConnection without connection pooling), thousands of short-lived connections quickly exhaust the entire OS ephemeral port range (~30,000 to 60,000 ports). Resolution: 1) Use a shared, singleton HTTP client with a persistent connection pool (e.g., Apache HttpClient PoolingHttpClientConnectionManager or Netty ConnectionProvider) that reuses existing TCP sockets; 2) Configure OS TCP socket recycling (tcp_tw_reuse = 1 on Linux); 3) Use HTTP/2 multiplexing.",
     ["Explains ephemeral source port allocation and TIME_WAIT socket lifecycle", "Identifies repeated instantiation of unpooled HTTP clients creating thousands of short-lived sockets", "Prescribes connection pooling with PoolingHttpClientConnectionManager or persistent Netty clients"],
     ["Attributes BindException to server listening port conflicts"]),

    ("B65_3_6", "tradeoff", "hard", "tradeoff", ["Networking", "Netty"],
     "In Netty's event-loop architecture, why is executing a blocking operation (like a JDBC query) directly inside a ChannelInboundHandler catastrophic, and what is the proper architectural offloading strategy?",
     "Netty relies on a small, fixed number of event-loop threads (typically 2 * CPU cores in NioEventLoopGroup), where each event loop manages hundreds or thousands of concurrent network channels. If a developer executes a blocking operation (e.g., synchronous JDBC query, Thread.sleep(), or blocking HTTP call) inside channelRead(), that event-loop thread halts. Consequently, all other channels assigned to that specific event-loop thread are completely frozen—they cannot read incoming packets, write responses, or process heartbeats. If a few blocking calls occur, all event loops starve and the entire server becomes unresponsive. The correct strategy is to offload blocking tasks to a dedicated worker thread pool: either by passing an EventExecutorGroup when adding the handler to the pipeline (pipeline.addLast(customExecutorGroup, myBlockingHandler)), or by dispatching the blocking task to a separate bounded ExecutorService or Schedulers.boundedElastic().",
     ["Explains that fixed event-loop threads multiplex thousands of concurrent channels", "Highlights that blocking one event loop freezes all channels assigned to that loop thread", "Prescribes using an EventExecutorGroup in the pipeline or dispatching to a dedicated bounded thread pool"],
     ["Suggests increasing the event loop thread count to 10,000"]),

    # Spring & Spring Boot Advanced Internals
    ("B65_3_7", "concept", "easy", "concept", ["Spring Framework", "Spring Boot"],
     "In Spring Boot, what is the 'Configuration Precedence' order between command-line arguments, OS environment variables, and application.properties?",
     "Spring Boot establishes a strict hierarchy of property sources (evaluated in order from highest to lowest precedence). Command-line arguments (--server.port=8081) have the highest priority, overriding all other property sources. OS environment variables (SERVER_PORT=8081) take precedence over internal configuration files. External profile-specific configuration files (config/application-{profile}.properties outside the jar) override packaged ones. Standard packaged application.properties inside the jar (classpath:/application.properties) has lower precedence, and @PropertySource annotations on @Configuration classes have the lowest precedence among user properties.",
     ["Identifies command-line arguments as highest precedence", "Places OS environment variables above application.properties files", "Orders packaged application.properties below external configuration files"],
     ["Claims application.properties inside jar overrides command-line arguments"]),

    ("B65_3_8", "diagnose", "hard", "debugging", ["Spring Framework", "Spring Internals"],
     "A method annotated with @Transactional inside a Spring @Service bean is called from another method within the same service bean (this.updateUser()). Why does the transaction fail to start, and what are the standard architectural fixes?",
     "Spring implements declarative transaction management using AOP dynamic proxies (CGLIB or JDK dynamic proxies). The transaction interceptor is wrapped around the outer proxy object, not the raw target bean. When an external caller invokes a service method, the invocation hits the proxy, which begins the transaction and delegates to the target bean. However, when a method inside the service bean calls another method on the same bean via this.updateUser(), it executes a local self-invocation. The invocation completely bypasses the Spring proxy; therefore, the @Transactional interceptor is never invoked, and no database transaction boundary is opened. Fix 1: Refactor the transactional method into a separate @Service or @Component bean so the call crosses a Spring-managed proxy boundary. Fix 2: Self-inject the bean using @Autowired or ObjectProvider<MyService> and call self.updateUser(). Fix 3: Use AspectJ compile-time or load-time weaving instead of Spring AOP proxies.",
     ["Explains Spring AOP proxy interception mechanism", "Identifies self-invocation via 'this' bypassing proxy boundaries", "Provides valid fixes: refactoring into separate bean, self-injection, or AspectJ weaving"],
     ["Claims @Transactional only works on interface declarations"]),

    ("B65_3_9", "scenario", "hard", "scenario", ["Spring Framework", "Transactions"],
     "A method with @Transactional(propagation = Propagation.REQUIRED) calls another service method annotated with @Transactional(propagation = Propagation.REQUIRES_NEW). Under load, the service exhausts its HikariCP connection pool and deadlocks. What is happening under the hood with database connections, and how do you prevent pool exhaustion deadlocks?",
     "When the outer method begins, it acquires a database connection from HikariCP and binds it to the current thread via TransactionSynchronizationManager. When execution enters the inner method with REQUIRES_NEW, Spring suspends the outer transaction and attempts to acquire a SECOND database connection from HikariCP for the new independent transaction. If the HikariCP pool has 10 connections and 10 concurrent requests execute the outer method simultaneously, all 10 connections are checked out by the outer transactions. When all 10 threads attempt to enter the inner REQUIRES_NEW method, they all request a second connection. Because the pool is empty, all 10 threads block waiting for a connection to free up. Since no thread can finish its outer transaction without obtaining an inner connection, the entire service enters an unrecoverable connection pool deadlock. Prevention: 1) Ensure pool size satisfies poolSize > maxThreads * (nestedTransactions + 1); 2) Avoid REQUIRES_NEW within synchronous web request worker threads; 3) Separate nested jobs into asynchronous messaging queues.",
     ["Explains outer transaction holding one connection while inner REQUIRES_NEW requests a second connection", "Identifies pool exhaustion deadlock when all concurrent threads exhaust the pool before acquiring inner connections", "Formulates sizing constraint: poolSize > maxThreads * 2, or refactors away from synchronous nested transactions"],
     ["Claims REQUIRES_NEW reuses the exact same database connection"]),

    ("B65_3_10", "implement", "medium", "implement", ["Spring Framework", "Spring Boot"],
     "How do you configure Spring Boot for 'Graceful Shutdown' (server.shutdown=graceful) in Kubernetes, and what happens to in-flight HTTP requests and background tasks during pod termination?",
     "Configure server.shutdown=graceful in application.properties, along with spring.lifecycle.timeout-per-shutdown-phase=30s. When Kubernetes sends a SIGTERM signal: 1) The embedded web server (Tomcat/Netty) immediately stops accepting new incoming HTTP connections; 2) In-flight HTTP requests that are currently executing are given a grace period (e.g., 30s) to complete normally; 3) If all in-flight requests complete before the timeout, Spring proceeds to shut down application contexts, closing HikariCP connection pools, stopping Kafka listeners, and destroying @PreDestroy beans; 4) If requests exceed the timeout, Spring forcefully closes remaining connections. A Kubernetes preStop hook sleep (e.g., sleep 10) is recommended to allow the ingress controller time to remove the pod from the routing table before the JVM graceful shutdown begins.",
     ["Enables server.shutdown=graceful and spring.lifecycle.timeout-per-shutdown-phase", "Describes rejecting new connections while permitting in-flight requests to complete within grace period", "Explains Kubernetes preStop hook sleep to coordinate ingress endpoint deregistration"],
     ["Claims graceful shutdown keeps the JVM running forever until all users log out"]),

    ("B65_3_11", "tradeoff", "medium", "tradeoff", ["Spring Framework", "Spring Internals"],
     "What is the difference between JDK Dynamic Proxies and CGLIB proxies in Spring AOP, and why did Spring Boot 2.x switch to CGLIB as the default proxy mechanism?",
     "JDK Dynamic Proxies require the target class to implement one or more Java interfaces. The proxy class is generated at runtime implementing those interfaces; if a caller attempts to inject the concrete class (@Autowired private MyServiceImpl service), Spring throws a BeanNotOfRequiredTypeException because the proxy is a sibling, not a subclass. CGLIB generates bytecode subclasses of the target concrete class at runtime by intercepting method calls. Spring Boot 2.x switched to CGLIB by default (spring.aop.proxy-target-class=true) because: 1) It allows injecting concrete classes directly without requiring artificial interfaces for every service; 2) It avoids confusing type-mismatch injection errors for developers; 3) Modern CGLIB / ByteBuddy bytecode generation has virtually identical performance to JDK dynamic proxies. CGLIB's tradeoff is that it cannot proxy final classes or final methods.",
     ["Contrasts interface-based JDK dynamic proxies with subclass-based CGLIB proxies", "Explains BeanNotOfRequiredTypeException when injecting concrete classes into JDK proxies", "Explains why Spring Boot defaulted to CGLIB (proxy-target-class=true) and notes final method limitations"],
     ["Claims JDK dynamic proxies modify class bytecode on disk"]),

    ("B65_3_12", "concept", "easy", "concept", ["Spring Framework", "Spring Internals"],
     "What is the purpose of @ConditionalOnMissingBean in Spring Boot auto-configuration, and how does bean definition order affect it?",
     "ConditionalOnMissingBean is a core condition annotation used in Spring Boot auto-configuration classes. It instructs Spring to register a default bean only if no bean of the specified type or name has already been registered in the ApplicationContext. This allows developers to easily override auto-configured beans simply by declaring their own @Bean method in user configuration. Order matters: user configurations (@Configuration scanned by @ComponentScan) are loaded first. Auto-configuration classes are evaluated second (controlled by @AutoConfigureAfter and @AutoConfiguration). If auto-configuration ran first, @ConditionalOnMissingBean would always evaluate to true, preventing user custom beans from taking precedence.",
     ["Explains purpose: allowing user-defined beans to override auto-configured defaults", "Explains ordering: user configurations evaluate before auto-configuration classes", "Mentions @AutoConfiguration or @AutoConfigureAfter controlling auto-config evaluation phase"],
     ["Claims ConditionalOnMissingBean throws an exception if a bean is missing"]),

    ("B65_3_13", "diagnose", "medium", "debugging", ["Spring Framework", "Transactions"],
     "In a Spring Boot service, an @Async method is called from inside an outer @Transactional method. The @Async method executes database writes. Why do the @Async writes fail to participate in the outer transaction?",
     "Spring's declarative transaction management relies on ThreadLocal storage via TransactionSynchronizationManager to bind the database Connection and transaction status to the currently executing thread. When a method is annotated with @Async, Spring's AsyncExecutionInterceptor dispatches the method execution to a separate worker thread managed by a TaskExecutor. Because ThreadLocal variables are not inherited by separate threads by default, the new worker thread has no knowledge of the outer thread's active transaction. The @Async method either executes in auto-commit mode (if no @Transactional is on it) or opens a completely separate database connection and independent transaction. Consequently, if the outer transaction rolls back, the @Async writes cannot be rolled back, violating ACID atomicity.",
     ["Identifies ThreadLocal storage in TransactionSynchronizationManager as transaction context holder", "Explains @Async switching execution to a separate thread pool thread", "Concludes that separate threads operate with separate connections and cannot share atomic commit/rollback boundaries"],
     ["Claims @Async methods cannot execute database queries"]),

    ("B65_3_14", "implement", "hard", "implement", ["Spring Framework", "Actuator"],
     "How do you implement a custom production Health Indicator in Spring Boot Actuator with reactive and liveness/readiness probe grouping support?",
     "Implement the HealthIndicator (or ReactiveHealthIndicator for WebFlux) interface and annotate it with @Component(\"customServiceHealth\"). Override health() to test the dependency (e.g., downstream TCP ping, cache ping). Return Health.up().withDetail(\"latencyMs\", latency).build() on success, or Health.down(exception).withDetail(\"error\", \"timeout\").build() on failure. To map this indicator into Kubernetes liveness or readiness probes, configure application.properties: management.endpoint.health.group.readiness.include=readinessState,customServiceHealth. This ensures /actuator/health/readiness fails (returning HTTP 503) if the custom service is down, prompting Kubernetes to stop routing traffic to the pod without triggering a destructive liveness pod restart.",
     ["Implements HealthIndicator or ReactiveHealthIndicator interface", "Returns Health.up() or Health.down() with diagnostic details", "Maps custom health check into Kubernetes readiness probe group via management.endpoint.health.group.readiness.include"],
     ["Recommends writing a custom HTTP servlet to handle health requests"]),

    ("B65_3_15", "tradeoff", "medium", "tradeoff", ["Spring Framework", "Spring Boot"],
     "What are the performance and startup tradeoffs of using @ComponentScan with deep package hierarchies versus explicit @Import or Spring Boot 3 AOT (Ahead-of-Time) compilation?",
     "ComponentScan performs classpath scanning at application startup, reading bytecode metadata for every class file across specified packages using ASM to detect annotations like @Component, @Service, and @Repository. In large enterprise applications with thousands of classes, classpath scanning and reflection add significant startup latency (several seconds) and high memory overhead during boot. Explicit @Import or functional bean registration registers beans directly, skipping scanning entirely. Spring Boot 3 AOT analyzes the application at build time, pre-computing bean definitions, proxy generation, and reflection metadata, producing optimized Java code that boots in fractions of a second with minimal memory footprint, but sacrifices dynamic runtime flexibility and requires strict reflection hints.",
     ["Explains ASM bytecode parsing and classpath scanning overhead during @ComponentScan startup", "Contrasts with explicit @Import or functional bean definition eliminating scanning", "Analyzes Spring Boot 3 AOT build-time pre-computation speeding startup while requiring reflection hints"],
     ["Claims @ComponentScan compiles Java code into machine binaries"]),

    ("B65_3_16", "concept", "easy", "concept", ["Spring Framework", "Spring Internals"],
     "What is the Bean Lifecycle in the Spring Framework, specifically the order of execution between @PostConstruct, InitializingBean.afterPropertiesSet(), and custom init-method?",
     "When Spring instantiates a bean: 1) The constructor is invoked; 2) Dependencies and property values are injected (populateBean); 3) Aware interfaces are called (BeanNameAware, BeanFactoryAware, ApplicationContextAware); 4) BeanPostProcessor.postProcessBeforeInitialization() runs; 5) Initialization methods execute in this exact order: first methods annotated with @PostConstruct (JSR-250), second InitializingBean.afterPropertiesSet(), and third any custom initMethod declared in @Bean(initMethod = '...'); 6) BeanPostProcessor.postProcessAfterInitialization() runs (where AOP proxies are created); 7) The bean is ready for use.",
     ["Lists initialization sequence: constructor -> dependency injection -> Aware interfaces", "Specifies precise order: @PostConstruct first, InitializingBean second, custom init-method third", "Identifies postProcessAfterInitialization as the point where AOP proxies wrap beans"],
     ["Claims @PostConstruct runs before the bean constructor is called"]),

    ("B65_3_17", "diagnose", "hard", "debugging", ["Spring Framework", "Spring Internals"],
     "A Spring Boot application fails to start with BeanCurrentlyInCreationException: Error creating bean with name 'A': Requested bean is currently in creation: Is there an unresolvable circular reference?. Why does constructor injection prevent circular reference resolution, whereas setter injection historically worked?",
     "Spring resolves circular dependencies for singleton beans by using a three-level cache (singletonObjects, earlySingletonObjects, singletonFactories). When bean A uses Setter injection, Spring can instantiate raw bean A via its default constructor, place an ObjectFactory into singletonFactories (Level 3 cache), and then begin injecting bean B. When bean B requests bean A, it retrieves the early, partially initialized reference of bean A from the cache, completing bean B's instantiation, and subsequently finishing bean A. However, with Constructor injection, bean A's constructor requires bean B to even instantiate bean A's raw memory object. Because bean A cannot be instantiated, it cannot publish an early reference to the cache. When bean B also requires bean A in its constructor, neither bean can even start construction, resulting in a fatal BeanCurrentlyInCreationException. The architectural fix is to break the cyclic dependency by introducing an event/mediator, refactoring shared responsibilities, or lazily loading with @Lazy.",
     ["Explains Spring three-level singleton cache and early reference exposure", "Identifies why constructor injection prevents early instantiation of the raw memory object", "Prescribes architectural fixes: refactoring cyclic responsibilities, events, or @Lazy"],
     ["Claims circular references are caused by database foreign key constraints"]),

    ("B65_3_18", "scenario", "medium", "scenario", ["Spring Framework", "Spring Boot"],
     "You want to ensure that a custom configuration bean is loaded ONLY after another third-party auto-configuration class has finished registering its beans. How do you enforce configuration ordering in Spring Boot?",
     "You annotate your custom auto-configuration class with @AutoConfiguration(after = ThirdPartyAutoConfiguration.class) or @AutoConfigureAfter(ThirdPartyAutoConfiguration.class) (and conversely @AutoConfigureBefore). Note that @AutoConfigureAfter and @Order ONLY apply to auto-configuration classes loaded via META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports (Spring Boot 3) or spring.factories (Spring Boot 2). They have NO effect on standard @Configuration classes discovered via @ComponentScan. For standard application classes, dependency ordering is enforced via bean method arguments or the @DependsOn annotation on @Bean definitions.",
     ["Uses @AutoConfiguration(after = ...) or @AutoConfigureAfter", "Explains that @AutoConfigureAfter only applies to auto-configuration imports, not @ComponentScan", "Explains using @DependsOn or direct bean parameters for standard user configuration beans"],
     ["Claims @Order annotation on standard classes guarantees bean creation order"]),

    ("B65_3_19", "tradeoff", "hard", "tradeoff", ["Spring Framework", "Transactions"],
     "What are the concurrency and consistency tradeoffs between Spring transaction isolation levels READ_COMMITTED and REPEATABLE_READ in a high-volume financial microservice?",
     "READ_COMMITTED prevents Dirty Reads (reading uncommitted changes from concurrent transactions) by reading only committed data. In MVCC databases (PostgreSQL/MySQL), it does this by taking a new snapshot at each query execution. Tradeoff: High concurrency and minimal lock contention, but subject to Non-Repeatable Reads (rereading the same row within a transaction can yield different values if another transaction committed) and Phantom Reads. REPEATABLE_READ takes a snapshot at the start of the transaction and uses it throughout, guaranteeing identical query results across the entire transaction. Tradeoff: Stronger consistency, but in databases that use locking or strict serialization checks, it causes higher lock contention, increased deadlocks, and transaction serialization rollbacks under concurrent row updates, requiring explicit application retry logic.",
     ["Explains MVCC snapshot behavior in READ_COMMITTED vs REPEATABLE_READ", "Analyzes Non-Repeatable Reads and Phantom Reads vulnerability in READ_COMMITTED", "Identifies increased lock contention, deadlocks, and serialization failure rollbacks in REPEATABLE_READ"],
     ["Claims REPEATABLE_READ prevents all database deadlocks"]),

    ("B65_3_20", "implement", "medium", "implement", ["Spring Framework", "Spring Boot"],
     "How do you implement a dynamic, custom Micrometer MeterBinder to expose custom JVM and thread pool metrics to Prometheus in a Spring Boot application?",
     "Create a class that implements io.micrometer.core.instrument.binder.MeterBinder and register it as a Spring @Component. In the bindTo(MeterRegistry registry) method, register custom gauges, counters, or timers. For example, to monitor a custom unbounded task queue: Gauge.builder('custom.queue.size', queue, Queue::size).description('Size of custom processing queue').tags('queue_name', 'orders').register(registry);. Micrometer will hold a weak reference to the queue and scrape its size dynamically when Prometheus hits the /actuator/prometheus endpoint, avoiding memory leaks and manual polling threads.",
     ["Implements io.micrometer.core.instrument.binder.MeterBinder interface", "Uses Gauge.builder() or Counter.builder() registered against MeterRegistry", "Explains weak reference dynamic sampling avoiding memory leaks during Prometheus scrapes"],
     ["Spawns an infinite while-loop thread to write metrics to a log file"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 3).")
    
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
    print("POST-BATCH AUDIT PART 3")
    print("========================================")
    print(f"Batch: 65 Part 3")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
