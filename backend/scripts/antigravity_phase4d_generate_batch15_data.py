"""Batch 15 question content (Java Developer). Antigravity-native, no Gemini API."""

ROLE = "Java Developer"

BUCKET_KEYS = {
    "JV_LA": ("Java Language", "Core Concepts", "Java", ["Backend Developer"]),
    "JV_CO": ("Collections", "Data Structures", "Java", ["Backend Developer"]),
    "JV_ST": ("Streams", "Functional Programming", "Java", ["Data Engineer"]),
    "JV_JM": ("JVM", "Internals", "Java", ["Performance Engineer"]),
    "JV_CN": ("Concurrency", "Multithreading", "Java", ["Performance Engineer", "Backend Developer"]),
    "JV_MD": ("Modern Java", "Language Features", "Java", ["Backend Developer"]),
    "JV_EX": ("Exception Handling", "Core Concepts", "Java", ["Backend Developer"]),
    "JV_PF": ("Performance", "Profiling & Tuning", "Java", ["Performance Engineer"]),
    "JV_TS": ("Testing", "JUnit & Mockito", "Java", ["Backend Developer"]),
    "JV_SP": ("Spring / Spring Boot", "Frameworks", "Spring", ["Backend Developer"]),
    "JV_BE": ("Java Backend Engineering", "APIs & I/O", "Java", ["Backend Developer"]),
    "JV_DS": ("Design", "Architecture", "Java", ["Architecture"]),
    "JV_DB": ("Debugging", "Troubleshooting", "Java", ["DevOps / Cloud Engineer"]),
}

Q = [
# ---------------- JV_LA ----------------
("JV_LA", "fundamentals", "easy", "concept", ["Memory Management"],
 "What is the difference between a primitive type and a reference type in Java, specifically regarding memory allocation?",
 "Primitive types (like int, double, boolean) store the actual value directly in memory (usually on the Stack). Reference types (like String, Objects, Arrays) store a memory address (reference) on the Stack that points to the actual object data allocated dynamically on the Heap.",
 ["Primitives store the actual value directly (Stack)", "Reference types store a memory address/pointer (Stack)", "Reference data lives on the Heap"],
 ["Primitives are stored in the database"]),

("JV_LA", "explain", "easy", "concept", ["Generics"],
 "Explain the concept of type erasure in Java Generics.",
 "Type erasure is a process where the Java compiler removes all generic type information during compilation to ensure backward compatibility with older Java versions. At runtime, a `List<String>` and a `List<Integer>` are both just a `List`, and the compiler inserts necessary type casts automatically.",
 ["Removes generic type information at compile time", "Ensures backward compatibility", "Generics are not retained at runtime"],
 ["Type erasure deletes variables from memory"]),

("JV_LA", "scenario", "medium", "scenario", ["Enums"],
 "A Java application uses an `enum` to represent order states. You need to attach specific behavior (methods) to each state without using a giant switch statement. How would you design this?",
 "I would define an abstract method inside the `enum` definition, and have each individual enum constant override and implement that method. This uses polymorphism to attach state-specific behavior directly to the enum constant, eliminating the need for complex switch statements.",
 ["Define an abstract method in the enum", "Override the method in each enum constant", "Utilizes polymorphism instead of switch statements"],
 ["Use a switch statement anyway because enums can't have methods"]),

("JV_LA", "tradeoff", "medium", "tradeoff", ["OOP Design"],
 "What are the tradeoffs of using composition over inheritance when designing a robust Java class hierarchy?",
 "Inheritance creates a rigid, tightly coupled 'is-a' relationship, breaking encapsulation (the fragile base class problem) and Java only supports single inheritance. Composition ('has-a') is highly flexible, allows injecting behavior dynamically at runtime, and prevents deep, unmaintainable hierarchies, but requires slightly more boilerplate to forward method calls.",
 ["Inheritance is tightly coupled and rigid (fragile base class)", "Composition is flexible and prevents deep hierarchies", "Composition requires more boilerplate/delegation"],
 ["Inheritance is always better because it saves typing"]),

# ---------------- JV_CO ----------------
("JV_CO", "fundamentals", "easy", "concept", ["Data Structures"],
 "What is the primary difference in internal data structure between an `ArrayList` and a `LinkedList` in Java?",
 "An `ArrayList` uses a dynamic array internally, offering contiguous memory and O(1) random access by index, but slow insertions/deletions in the middle. A `LinkedList` uses a doubly-linked list of node objects, offering O(1) insertions/deletions during traversal but slow O(n) random access.",
 ["ArrayList uses a dynamic contiguous array", "LinkedList uses a doubly-linked list of nodes", "ArrayList has fast random access; LinkedList has fast insertions/deletions"],
 ["ArrayList is a tree and LinkedList is an array"]),

("JV_CO", "compare", "medium", "comparison", ["Data Structures"],
 "Compare `HashMap` and `TreeMap`. When would you choose to use a `TreeMap` over a `HashMap`?",
 "A `HashMap` uses a hash table providing O(1) average time complexity for operations, but it does not maintain any order. A `TreeMap` is backed by a Red-Black Tree, providing O(log n) time complexity, but it inherently keeps its keys sorted. Use `TreeMap` only when you explicitly need sorted keys or range queries.",
 ["HashMap offers O(1) average time, unordered", "TreeMap offers O(log n) time, backed by Red-Black Tree", "Use TreeMap when sorted keys or range queries are required"],
 ["TreeMap is faster than HashMap for all operations"]),

("JV_CO", "scenario", "hard", "scenario", ["Concurrency"],
 "A multi-threaded Java application iterates over a `HashMap` while other threads actively add new keys. You notice intermittent `ConcurrentModificationException`s. How do you resolve this while maintaining high read throughput?",
 "Replace the standard `HashMap` with a `ConcurrentHashMap`. It uses lock striping (or CAS operations in newer Java versions) to allow highly concurrent reads without locking the entire map, and safely supports iteration while modifications are occurring without throwing `ConcurrentModificationException`.",
 ["Replace HashMap with ConcurrentHashMap", "ConcurrentHashMap allows concurrent reads/writes without throwing the exception", "Uses lock striping / CAS for high throughput"],
 ["Wrap the entire HashMap in a global synchronized block"]),

("JV_CO", "tradeoff", "medium", "tradeoff", ["Immutability"],
 "What tradeoffs are involved in using `Collections.unmodifiableList()` versus creating a defensive copy of a list before returning it from a getter method?",
 "`Collections.unmodifiableList()` provides a read-only view in O(1) time (very fast), but if the underlying list changes, those changes are visible to the caller (not truly immutable). A defensive copy (`new ArrayList<>(list)`) guarantees true isolation and immutability, but incurs O(n) time and memory overhead for copying.",
 ["unmodifiableList is a fast O(1) view but underlying changes are visible", "Defensive copy guarantees isolation but costs O(n) memory/CPU", "unmodifiableList is not truly immutable if the source changes"],
 ["unmodifiableList deletes the original list"]),

# ---------------- JV_ST ----------------
("JV_ST", "explain", "easy", "concept", ["Functional Programming"],
 "Explain the difference between intermediate and terminal operations in the Java Stream API.",
 "Intermediate operations (like `map`, `filter`) return a new Stream, are lazy, and do not execute until a terminal operation is invoked. Terminal operations (like `collect`, `forEach`, `count`) produce a final non-Stream result or a side effect, and trigger the actual execution of the entire stream pipeline.",
 ["Intermediate operations are lazy and return a Stream", "Terminal operations trigger execution and return a result", "Intermediate ops don't run without a terminal op"],
 ["Intermediate operations delete data from the stream"]),

("JV_ST", "implement", "medium", "implementation", ["Collectors"],
 "How would you approach processing a massive `List<User>` to group them by their `departmentId` and then count the number of users in each department using the Stream API?",
 "I would stream the list and use a terminal collector. Specifically, `users.stream().collect(Collectors.groupingBy(User::getDepartmentId, Collectors.counting()))`. This produces a `Map<String, Long>` mapping each department to its total count in a concise, declarative way.",
 ["Use the Stream API", "Use Collectors.groupingBy() for the department ID", "Use Collectors.counting() as the downstream collector"],
 ["Use a nested for-loop with three different HashMaps"]),

("JV_ST", "debug", "medium", "debugging", ["Streams"],
 "A developer attempts to reuse a Java `Stream` instance after already calling a terminal operation on it, resulting in an `IllegalStateException`. Why does this happen, and how should it be fixed?",
 "In Java, a Stream is consumed and closed once a terminal operation is executed on it; it cannot be reused or re-traversed. To fix this, you must obtain a new Stream instance from the original data source (e.g., `list.stream()`) for every distinct terminal operation, or store the intermediate results in a collection.",
 ["Streams are consumed upon terminal operation execution", "Cannot be reused or re-traversed", "Must generate a new stream from the source"],
 ["Catch the exception and force the stream to reopen"]),

("JV_ST", "tradeoff", "hard", "tradeoff", ["Performance"],
 "What are the performance tradeoffs of using `.parallelStream()` versus `.stream()` on a collection of 10,000 items? When might parallel streams actually decrease performance?",
 "Parallel streams divide the work across the common ForkJoinPool, speeding up CPU-intensive operations on massive datasets. However, for small datasets or fast operations, the overhead of splitting the data, managing threads, and merging results is far greater than the work itself, actively degrading performance.",
 ["Parallel streams leverage the ForkJoinPool for concurrency", "Overhead of thread management/splitting can exceed the work", "Decreases performance on small datasets or fast operations"],
 ["Parallel streams are always faster on any dataset"]),

# ---------------- JV_JM ----------------
("JV_JM", "fundamentals", "easy", "concept", ["Memory Architecture"],
 "What is the difference between the Java Heap and the Java Stack?",
 "The Heap is a globally shared memory area where all Java objects and instance variables are allocated. The Stack is thread-local memory where method executions, local primitive variables, and object references (pointers) are stored; it automatically cleans up when a method returns.",
 ["Heap: globally shared, stores all Objects", "Stack: thread-local, stores method frames, primitives, and object references", "Stack cleans up automatically upon method return"],
 ["Heap is for integers, Stack is for strings"]),

("JV_JM", "explain", "medium", "concept", ["Garbage Collection"],
 "Explain the role of the Garbage Collector in Java, specifically the concept of 'Stop-The-World' pauses.",
 "The Garbage Collector (GC) automatically reclaims memory by deleting objects that are no longer reachable by the application. A 'Stop-The-World' pause occurs when the GC completely halts all application threads to safely analyze memory references or move objects around, causing application latency spikes.",
 ["Automatically reclaims unreachable memory", "Stop-The-World halts all application threads", "Causes temporary application latency/pauses"],
 ["GC deletes all active variables randomly"]),

("JV_JM", "scenario", "hard", "scenario", ["Memory Leaks"],
 "A Java backend service experiences an `OutOfMemoryError: Metaspace` after running for a few days, particularly after numerous hot-deployments. What is the likely cause?",
 "The Metaspace stores class metadata, not object instances. This error is caused by a Classloader memory leak. During hot-deployments (like in Tomcat), old classloaders and their loaded classes are not properly garbage collected because the application holds strong references to them (e.g., via ThreadLocals or static fields).",
 ["Metaspace stores class metadata", "Caused by Classloader memory leaks", "Common in hot-deployments holding references to old classes"],
 ["The server ran out of hard drive space"]),

("JV_JM", "compare", "medium", "comparison", ["Garbage Collection"],
 "Compare the G1 Garbage Collector with the Z Garbage Collector (ZGC). What specific problem does ZGC aim to solve?",
 "G1GC is a generational, region-based collector aiming for predictable pause times, but pauses scale with heap size and can exceed hundreds of milliseconds. ZGC is a highly concurrent collector designed for massive heaps (terabytes) where it performs almost all work concurrently, keeping 'Stop-The-World' pauses under 1-10ms regardless of heap size.",
 ["G1GC pauses can scale with heap size", "ZGC performs almost all work concurrently", "ZGC keeps pauses under 1-10ms regardless of heap size"],
 ["ZGC uses zero RAM compared to G1GC"]),

# ---------------- JV_CN ----------------
("JV_CN", "fundamentals", "easy", "concept", ["Concurrency"],
 "What is the purpose of the `volatile` keyword in Java?",
 "The `volatile` keyword guarantees visibility of changes to variables across threads. It forces the JVM to read and write the variable directly from main memory, bypassing local CPU caches, ensuring that when one thread modifies it, other threads instantly see the updated value.",
 ["Guarantees cross-thread visibility", "Bypasses local CPU caches", "Reads/writes directly to main memory"],
 ["It makes a variable immutable"]),

("JV_CN", "scenario", "hard", "scenario", ["Executors"],
 "A Java service using `CompletableFuture` begins exhausting its executor under burst traffic, leading to massive memory usage. How would you diagnose the problem and redesign the asynchronous execution strategy?",
 "The default `ForkJoinPool.commonPool()` is likely saturated. If developers used `Executors.newFixedThreadPool()` with an unbounded queue, the queue will grow infinitely under load, causing OOM. I would diagnose by checking thread dumps and heap usage. I would redesign it using a custom `ThreadPoolExecutor` with a bounded queue (e.g., ArrayBlockingQueue) and a strict `RejectedExecutionHandler` to apply backpressure.",
 ["Diagnose unbounded queues in the executor", "Replace with ThreadPoolExecutor using a bounded queue", "Implement a RejectedExecutionHandler for backpressure"],
 ["CompletableFuture doesn't use memory"]),

("JV_CN", "implement", "medium", "implementation", ["Atomics"],
 "How would you safely update a shared integer counter from 100 concurrent threads without using synchronized blocks?",
 "I would use `AtomicInteger` from the `java.util.concurrent.atomic` package. Calling methods like `incrementAndGet()` utilizes low-level CPU Compare-And-Swap (CAS) instructions to update the value atomically and lock-free, providing thread safety with much higher performance than synchronization.",
 ["Use AtomicInteger", "Use incrementAndGet()", "Utilizes lock-free Compare-And-Swap (CAS) operations"],
 ["Just use a normal int, Java handles it automatically"]),

("JV_CN", "debug", "hard", "debugging", ["Deadlocks"],
 "You notice a production Java application is completely unresponsive. A thread dump reveals a classic deadlock. How do you conceptually avoid deadlocks when acquiring multiple nested locks?",
 "A deadlock occurs when threads acquire multiple locks in different orders (circular wait). The primary way to prevent deadlocks conceptually is to enforce a strict, globally consistent lock acquisition order across all threads. Alternatively, use `ReentrantLock.tryLock()` with a timeout to back off if a lock cannot be immediately acquired.",
 ["Enforce a strict global lock acquisition order", "Prevent circular wait conditions", "Alternatively, use tryLock() with timeouts"],
 ["Add Thread.sleep() randomly in the code"]),

# ---------------- JV_MD ----------------
("JV_MD", "explain", "easy", "concept", ["Language Features"],
 "Explain the purpose and benefits of Java `record`s introduced in modern Java versions.",
 "Java `record`s are a concise way to create immutable data carriers. The compiler automatically generates the constructor, getters, `equals()`, `hashCode()`, and `toString()` methods, drastically reducing boilerplate code compared to traditional POJOs.",
 ["Concise way to create immutable data carriers", "Compiler auto-generates constructor, getters, equals, hashCode", "Reduces boilerplate POJO code"],
 ["Records are used to record database transactions"]),

("JV_MD", "tradeoff", "medium", "tradeoff", ["Optional"],
 "What are the tradeoffs of heavily using `Optional<T>` as method parameters versus using them strictly as return types?",
 "Using `Optional` as a return type elegantly forces the caller to handle nullability. However, using `Optional` as a method parameter adds unnecessary boilerplate, forces callers to wrap values, and incurs a slight performance penalty (creating wrapper objects). It is generally considered an anti-pattern to use `Optional` in method parameters or class fields.",
 ["Return types: elegantly forces null checking", "Parameters: adds boilerplate and wrapper object overhead", "Parameters/Fields are generally considered anti-patterns for Optional"],
 ["Optional should be used for every single variable in Java"]),

("JV_MD", "scenario", "medium", "scenario", ["Language Features"],
 "You have a domain model with a fixed, closed hierarchy (e.g., `Result` can only be `Success` or `Failure`). How would you model this in modern Java to ensure exhaustive compile-time checking?",
 "I would use Sealed Classes. Declare `public sealed interface Result permits Success, Failure`. This restricts which classes can implement the interface. When combined with modern pattern-matching `switch` expressions, the compiler guarantees exhaustiveness, ensuring all possible subclasses are handled without needing a `default` case.",
 ["Use Sealed Classes/Interfaces (`sealed` and `permits`)", "Restricts which classes can extend/implement", "Enables exhaustive compile-time checking in switch expressions"],
 ["Use standard inheritance and cast everything"]),

("JV_MD", "implement", "medium", "implementation", ["Language Features"],
 "How would you refactor a legacy `switch` statement containing multiple `instanceof` checks and casts into modern Java code using Pattern Matching?",
 "Using modern Java Pattern Matching for `switch`, I would replace the `instanceof` and manual casting with type patterns directly in the switch cases: `switch(obj) { case String s -> s.toUpperCase(); case Integer i -> i * 2; default -> null; }`. This extracts and casts the variable safely in one step.",
 ["Use Pattern Matching for switch", "Combine type check and cast in the case label (e.g., case String s)", "Results in cleaner, safer, more concise code"],
 ["Replace it with a giant if-else chain"]),

# ---------------- JV_EX ----------------
("JV_EX", "fundamentals", "easy", "concept", ["Exception Handling"],
 "What is the difference between a Checked Exception and an Unchecked (Runtime) Exception in Java?",
 "Checked exceptions (inheriting from `Exception`) represent recoverable conditions and the compiler forces you to either catch them or declare them in the method signature (e.g., `IOException`). Unchecked exceptions (inheriting from `RuntimeException`) represent programming bugs (e.g., `NullPointerException`) and the compiler does not enforce catching them.",
 ["Checked: compiler forces catch or declare (recoverable)", "Unchecked: no compiler enforcement (programming bugs)", "Unchecked inherit from RuntimeException"],
 ["Checked exceptions check the database connection"]),

("JV_EX", "tradeoff", "medium", "tradeoff", ["Exception Handling"],
 "What are the architectural tradeoffs of throwing custom Checked Exceptions versus wrapping them in standard RuntimeExceptions at the service layer boundary?",
 "Checked exceptions force callers to explicitly handle errors, providing self-documenting code, but heavily clutter method signatures up the entire call stack and don't play well with Streams/Lambdas. Wrapping them in RuntimeExceptions cleans up signatures and integrates with modern frameworks (like Spring's global handlers), but risks callers forgetting to handle critical business errors.",
 ["Checked: forces handling, clutters signatures, bad for Lambdas", "Runtime: clean signatures, integrates with Spring/global handlers", "Runtime risks callers ignoring critical business errors"],
 ["Checked exceptions are faster than Runtime exceptions"]),

("JV_EX", "scenario", "medium", "scenario", ["Resource Management"],
 "A Java method opens a database connection, performs a query, and opens a file output stream. How do you ensure both resources are always safely closed, even if an exception occurs during the query?",
 "Use the `try-with-resources` statement. Any object that implements `AutoCloseable` can be instantiated within the `try` parentheses. The JVM guarantees that the `close()` method will be called on both the connection and the stream automatically, in reverse order of creation, regardless of whether an exception is thrown.",
 ["Use try-with-resources", "Resources must implement AutoCloseable", "JVM guarantees automatic closure even on exceptions"],
 ["Write a finally block and use System.gc()"]),

("JV_EX", "debug", "hard", "debugging", ["Exception Handling"],
 "A developer catches `Exception` globally in a REST controller advice, but notices that critical JVM errors like `OutOfMemoryError` are bypassing the handler and crashing the app. Why is this happening, and what should be caught instead?",
 "`OutOfMemoryError` inherits from `Error`, not `Exception`. Both inherit from `Throwable`. By catching `Exception`, you miss severe JVM errors. While you generally shouldn't try to gracefully handle `Error`s (as the JVM is compromised), if you must log them globally, you must catch `Throwable`.",
 ["OutOfMemoryError inherits from Error, not Exception", "Both inherit from Throwable", "Catch Throwable to capture both Exceptions and Errors"],
 ["OutOfMemoryError cannot be caught by Java code"]),

# ---------------- JV_PF ----------------
("JV_PF", "scenario", "medium", "scenario", ["Profiling"],
 "A Java web application experiences high CPU utilization. Using `top`, you identify the Java process is the culprit. How would you pinpoint which specific Java method is burning the CPU?",
 "I would capture a thread dump using `jstack` and map the native OS thread ID (converted to Hex) from `top -H` to the internal Java `nid` (native ID) in the thread dump. Alternatively, and more effectively, I would use a profiler like async-profiler or JDK Flight Recorder (JFR) to generate a CPU flame graph to visually identify the hot methods.",
 ["Map OS thread ID to Java nid using jstack", "Use profilers like async-profiler or JDK Flight Recorder", "Generate CPU flame graphs"],
 ["Restart the server to clear the CPU"]),

("JV_PF", "debug", "hard", "debugging", ["Memory Leaks"],
 "You suspect a memory leak in a long-running Java application. You trigger a heap dump, but it's 8GB. What tools and specific techniques would you use to find the object holding the strong references?",
 "I would load the heap dump into a tool like Eclipse MAT (Memory Analyzer Tool) or VisualVM. I would calculate the 'Retained Size' of objects (memory that would be freed if the object was removed). I would then run a 'Dominator Tree' analysis or 'Find Leak Suspects' report to trace the GC Roots holding strong references to the massive objects.",
 ["Use Eclipse MAT or VisualVM", "Analyze Retained Size (not just shallow size)", "Use Dominator Tree / trace back to GC Roots"],
 ["Open the 8GB file in a text editor and search for 'leak'"]),

("JV_PF", "tradeoff", "medium", "tradeoff", ["Garbage Collection"],
 "What tradeoffs exist between aggressively tuning the JVM heap size to be as large as possible versus keeping it smaller and horizontally scaling the application instances?",
 "A massive heap reduces the frequency of garbage collection cycles, allowing higher throughput, but causes catastrophic, multi-second 'Stop-The-World' pauses when a major GC finally occurs (unless using ZGC). Smaller heaps trigger frequent, brief GC pauses (predictable latency) and are easier to horizontally scale in containerized environments (Kubernetes).",
 ["Large heap: higher throughput, but massive GC pause times", "Small heap: predictable low latency, better for Kubernetes/containers", "Small heap triggers GC more frequently"],
 ["Massive heaps make the CPU run faster"]),

("JV_PF", "implement", "hard", "implementation", ["Concurrency"],
 "How would you approach identifying and resolving thread contention (lock starvation) in a highly concurrent Java application using profiling tools like JDK Mission Control (JMC)?",
 "I would start a JDK Flight Recorder (JFR) recording and open it in JMC. I would analyze the 'Lock Instances' and 'Thread Blocked' events to find exactly which object monitor is experiencing high contention. To resolve it, I would reduce the lock scope, switch from `synchronized` to `ReentrantReadWriteLock`, or use lock-free data structures (`ConcurrentHashMap`, `AtomicInteger`).",
 ["Use JFR/JMC to analyze 'Thread Blocked' events", "Identify the specific highly contended lock/monitor", "Resolve by reducing lock scope or using lock-free structures"],
 ["Just remove all synchronized blocks completely"]),

# ---------------- JV_TS ----------------
("JV_TS", "explain", "easy", "concept", ["Testing"],
 "Explain the purpose of the `@Mock` and `@InjectMocks` annotations in the Mockito framework.",
 "`@Mock` creates a fake, simulated instance of a dependency. `@InjectMocks` is placed on the class being tested; Mockito will instantiate this class and automatically inject the created `@Mock` fields into it (via constructor or field injection), perfectly isolating the class for unit testing.",
 ["@Mock creates a fake dependency", "@InjectMocks creates the test subject and injects the mocks", "Isolates the class for unit testing"],
 ["@Mock creates a real database connection"]),

("JV_TS", "implement", "medium", "implementation", ["JUnit"],
 "How would you design a parameterized JUnit 5 test to validate an email validation utility method across dozens of valid and invalid input strings?",
 "I would use the `@ParameterizedTest` annotation combined with `@CsvSource` or `@MethodSource`. This allows me to pass a dataset of inputs (e.g., 'test@example.com', 'invalid-email') and their expected boolean outcomes into a single test method, executing the test independently for each data row without duplicating test code.",
 ["Use @ParameterizedTest", "Use @CsvSource or @MethodSource for data input", "Executes the same test method multiple times with different data"],
 ["Write 50 separate @Test methods manually"]),

("JV_TS", "scenario", "hard", "scenario", ["Spring Testing"],
 "A Spring Boot integration test suite annotated with `@SpringBootTest` takes 15 minutes to run locally because it restarts the Spring Application Context for every test class. How do you optimize this to share the context?",
 "Spring automatically caches and reuses the ApplicationContext across tests IF the context configuration is identical. The restarts are likely caused by test classes altering the context via `@MockBean`, `@SpyBean`, `@DirtiesContext`, or varying `@ActiveProfiles`. Optimize by minimizing `@MockBean`, consolidating profiles, and grouping tests that require identical context configurations.",
 ["Spring caches contexts if configurations are exactly identical", "Restarts are caused by @MockBean, @DirtiesContext, or varying profiles", "Optimize by minimizing @MockBean and aligning configurations"],
 ["Turn off the database to make it run faster"]),

("JV_TS", "tradeoff", "medium", "tradeoff", ["Testing"],
 "What are the tradeoffs of using an in-memory H2 database for integration tests versus using a real PostgreSQL instance via Testcontainers?",
 "H2 is extremely fast to spin up and requires no Docker environment, but its SQL dialect, constraints, and JSON support differ from PostgreSQL, causing false positives/negatives in tests. Testcontainers spins up a real PostgreSQL Docker container, guaranteeing exact production compatibility, but adds execution time overhead and requires a running Docker daemon.",
 ["H2: fast, no Docker needed, but lacks Postgres compatibility (false positives)", "Testcontainers: real Postgres, guarantees compatibility", "Testcontainers adds time overhead and requires Docker"],
 ["H2 is a NoSQL database, PostgreSQL is SQL"]),

# ---------------- JV_SP ----------------
("JV_SP", "fundamentals", "easy", "concept", ["Spring Core"],
 "What is the primary difference between constructor injection and field injection (using `@Autowired`) in Spring Boot?",
 "Field injection uses reflection to set private fields, which makes the class impossible to instantiate in unit tests without Spring or reflection, and hides required dependencies. Constructor injection explicitly declares dependencies in the constructor signature, ensuring the class cannot be instantiated in an invalid state and making unit testing trivial without Spring.",
 ["Field injection uses reflection, hard to unit test", "Constructor injection explicitly requires dependencies", "Constructor injection makes unit testing easy without Spring"],
 ["Field injection is much faster at runtime"]),

("JV_SP", "explain", "medium", "concept", ["Spring Core"],
 "Explain the concept of the Spring ApplicationContext and the lifecycle of a typical Singleton bean.",
 "The `ApplicationContext` is the IoC container that instantiates, configures, and manages beans. For a Singleton bean, the context instantiates it once at startup, injects dependencies, calls initialization methods (`@PostConstruct`), caches it, serves the exact same instance to all requesters, and finally calls destruction methods (`@PreDestroy`) when the application shuts down.",
 ["ApplicationContext is the IoC container", "Singleton is instantiated once at startup and cached", "Manages lifecycle methods (@PostConstruct, @PreDestroy)"],
 ["Singleton beans are recreated for every HTTP request"]),

("JV_SP", "scenario", "hard", "scenario", ["Spring Transactions"],
 "A Spring service method annotated with `@Transactional` catches a checked `IOException` and swallows it, but the database transaction still successfully commits, even though the business logic failed. Why did this happen, and how do you fix it?",
 "By default, Spring's `@Transactional` only rolls back for Unchecked exceptions (`RuntimeException` and `Error`). Because `IOException` is a Checked exception, Spring commits the transaction. To fix it, you must explicitly declare `@Transactional(rollbackFor = Exception.class)` to force rollback on all exceptions.",
 ["@Transactional only rolls back on RuntimeExceptions by default", "Checked exceptions (like IOException) will commit", "Fix by adding rollbackFor = Exception.class"],
 ["Spring doesn't support database rollbacks"]),

("JV_SP", "implement", "medium", "implementation", ["Spring Web"],
 "How would you approach designing a global, centralized exception handling strategy for a Spring Boot REST API to return consistent JSON error responses?",
 "I would create a global class annotated with `@RestControllerAdvice`. Inside, I would define methods annotated with `@ExceptionHandler` to intercept specific exceptions (e.g., `EntityNotFoundException`, `MethodArgumentNotValidException`). These methods would map the exception details into a standard custom JSON error object and return the appropriate HTTP status code via `ResponseEntity`.",
 ["Use @RestControllerAdvice for global handling", "Use @ExceptionHandler for specific exceptions", "Return a standardized JSON error object and HTTP status"],
 ["Put a try-catch block inside every single controller method"]),

("JV_SP", "debug", "medium", "debugging", ["Spring Core"],
 "A developer injects a prototype-scoped bean into a singleton-scoped Spring component, but notices the prototype bean behaves like a singleton (the same instance is reused). How do you resolve this 'scoped proxy' problem?",
 "The singleton bean is only instantiated once, so its dependencies are only injected once. To get a fresh prototype instance every time the singleton uses it, you can annotate the singleton with `@Lookup` on a getter method, use `ObjectProvider<PrototypeBean>`, or change the prototype's scope to explicitly use a `ScopedProxyMode.TARGET_CLASS`.",
 ["Singleton dependencies are only injected once at startup", "Use @Lookup method injection", "Or use ObjectProvider to fetch a new instance dynamically"],
 ["Change the singleton bean to prototype"]),

# ---------------- JV_BE ----------------
("JV_BE", "scenario", "medium", "scenario", ["Serialization"],
 "A Java REST API uses Jackson for JSON serialization. A large entity graph contains bidirectional relationships (e.g., Parent has List<Child>, Child has Parent), causing an infinite recursion `StackOverflowError` during serialization. How do you fix this?",
 "Use Jackson annotations to break the cycle. Annotate the child's reference to the parent with `@JsonIgnore` to omit it from serialization, or use `@JsonManagedReference` on the parent and `@JsonBackReference` on the child. Alternatively, serialize DTOs (Data Transfer Objects) instead of raw Hibernate entities.",
 ["Use @JsonIgnore on the back-reference", "Use @JsonManagedReference and @JsonBackReference", "Map entities to DTOs before serialization"],
 ["Increase the JVM stack size to infinity"]),

("JV_BE", "implement", "hard", "implementation", ["Databases"],
 "How would you configure and tune a HikariCP database connection pool in a high-throughput Java backend service to prevent connection exhaustion and latency spikes?",
 "I would set `maximumPoolSize` strictly based on the database capacity (often lower than expected, e.g., 10-20 to prevent DB thrashing). I would set `connectionTimeout` (e.g., 5-10s) to fail fast if the pool is exhausted. I would also ensure `minimumIdle` is equal to `maximumPoolSize` to prevent latency spikes caused by dynamically opening connections under load.",
 ["Set maximumPoolSize based on DB capacity (keep it small)", "Set connectionTimeout to fail fast during exhaustion", "Keep minimumIdle equal to max to avoid dynamic connection overhead"],
 ["Set maximumPoolSize to 10,000 to handle more users"]),

("JV_BE", "compare", "medium", "comparison", ["I/O Architecture"],
 "Compare traditional blocking Java I/O (e.g., Spring MVC / Tomcat) with non-blocking, reactive I/O (e.g., Spring WebFlux / Netty).",
 "Blocking I/O assigns one OS thread per HTTP request. If the request waits on a DB, the thread is blocked, leading to thread exhaustion under high concurrency. Reactive I/O uses an event loop with a small number of threads. I/O operations are non-blocking, allowing a single thread to handle thousands of concurrent requests by switching contexts via callbacks/publishers.",
 ["Blocking (MVC/Tomcat): Thread-per-request, risks thread exhaustion", "Reactive (WebFlux/Netty): Event loop, non-blocking I/O", "Reactive scales better under massive concurrent connections"],
 ["Blocking I/O is faster because it uses callbacks"]),

# ---------------- JV_DS ----------------
("JV_DS", "explain", "easy", "concept", ["Architecture"],
 "Explain the Dependency Inversion Principle (the 'D' in SOLID) in the context of Java application design.",
 "The Dependency Inversion Principle states that high-level modules should not depend on low-level modules; both should depend on abstractions (interfaces). Practically in Java, a Controller should depend on a `PaymentService` interface, not a concrete `StripePaymentServiceImpl`. This decouples code, making it easy to swap implementations and mock dependencies for testing.",
 ["High-level modules should depend on abstractions (interfaces)", "Decouples implementations", "Makes code highly testable via mocking"],
 ["It means avoiding the use of databases entirely"]),

("JV_DS", "tradeoff", "medium", "tradeoff", ["Domain Driven Design"],
 "What tradeoffs exist between placing business logic directly inside a JPA `@Entity` class (Rich Domain Model) versus keeping the entity anemic and placing logic in a `@Service` class?",
 "A Rich Domain Model (OOP standard) encapsulates state and behavior together, making the domain highly cohesive and self-validating, but struggles when business logic requires external services or complex DB queries. An Anemic Domain Model (entities as dumb structs) separates data from logic, making it easy to inject external services, but scatters business logic across service classes, violating OOP encapsulation.",
 ["Rich Domain: cohesive, OOP encapsulation, hard to inject services", "Anemic Domain: separates logic/data, easy to inject, violates OOP", "Anemic scatters logic into Service classes"],
 ["Rich domain models delete the database automatically"]),

("JV_DS", "scenario", "hard", "scenario", ["Refactoring"],
 "A core Java utility class has 50 static methods, creating tight coupling across the entire codebase and making unit testing impossible. How do you gradually refactor this monolithic utility class into a maintainable, testable design?",
 "I would convert the static utility methods into instance methods within highly cohesive, domain-specific component classes (e.g., extracting date methods to `DateService`). I would register these new components as injectable beans (in Spring) and use dependency injection to provide them to callers, enabling interfaces and mocking for unit tests.",
 ["Extract static methods into cohesive instance classes", "Use Dependency Injection (DI) instead of static calls", "Enables mocking and unit testing"],
 ["Delete the class and rewrite the whole app"]),

# ---------------- JV_DB ----------------
("JV_DB", "debug", "medium", "debugging", ["Classloading"],
 "A Java application in production periodically logs `java.lang.NoClassDefFoundError`. The class exists in the deployment artifact. What classloading issues typically cause this at runtime?",
 "Unlike `ClassNotFoundException` (missing at compile/load time), `NoClassDefFoundError` happens when the JVM successfully loaded the class previously, but static initialization of that class failed (e.g., an exception in a `static {}` block or static field assignment). Subsequent attempts to use the class yield this error.",
 ["Static initialization block/field assignment threw an exception", "Class was found, but failed to initialize correctly", "JVM marks it as unusable for subsequent calls"],
 ["The Java version is too old to run the class"]),

("JV_DB", "scenario", "medium", "scenario", ["Networking"],
 "A legacy Java service occasionally hangs indefinitely when making an external HTTP call using `HttpURLConnection`. How do you diagnose and fix this?",
 "The legacy code is likely missing strict network timeouts. If the external server accepts the connection but silently drops packets or never sends a response, the Java thread will block forever on the socket read. Fix it by explicitly calling `setConnectTimeout()` and `setReadTimeout()` on the connection.",
 ["Missing explicit network timeouts", "Thread blocks indefinitely on socket read", "Fix by setting connect and read timeouts"],
 ["The external server is written in Python"]),

("JV_DB", "compare", "hard", "comparison", ["Observability"],
 "Compare diagnosing a performance bottleneck using standard logs/metrics versus attaching a Java Agent (like Datadog or New Relic) at runtime. What specific insights does the Java Agent provide that logs miss?",
 "Logs and metrics provide high-level boundaries (e.g., 'API took 2s'), but require manual instrumentation. A Java Agent uses JVM instrumentation (bytecode manipulation) to automatically trace execution deep into third-party libraries, ORMs, and JDBC drivers. It can identify the exact SQL query or internal library method causing the latency without altering the application code.",
 ["Logs require manual instrumentation and provide boundary timings", "Java Agents use bytecode manipulation for automatic deep tracing", "Agents reveal exact SQL queries or library methods causing latency"],
 ["Java Agents delete log files to save disk space"])
]
