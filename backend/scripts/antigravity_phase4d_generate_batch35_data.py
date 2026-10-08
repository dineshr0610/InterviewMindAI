"""Batch 35 Part 1 question content (Java Developer). Targeted Gap Generation."""

ROLE = "Java Developer"

BUCKET_KEYS = {
    "JAVA_BACKEND_ENGINEERING": ("Java Backend Engineering", "APIs & I/O", "Java", ["Java Developer", "Backend Developer"]),
}

Q = [
# ---------------- JAVA_BACKEND_ENGINEERING ----------------
("JAVA_BACKEND_ENGINEERING", "scenario", "medium", "scenario", ["Spring AOP", "Transactions"],
 "In Spring Boot, method `A()` is `@Transactional`. It calls method `B()` within the *same* class, which is `@Transactional(propagation = Propagation.REQUIRES_NEW)`. If `B()` throws a RuntimeException, what happens to the transaction started by `A()`?",
 "The transaction in `A()` will roll back, and the `REQUIRES_NEW` in `B()` will be completely ignored. Spring's declarative transaction management uses AOP proxies. When a method calls another method within the same object (self-invocation), the call bypasses the proxy entirely, ignoring `B()`'s annotations. Fix: Move `B()` to an injected bean or use self-injection.",
 ["The transaction in `A()` rolls back; `B()`'s `REQUIRES_NEW` is completely ignored", "Spring transactions use AOP proxies. Internal method calls (self-invocation) bypass the proxy", "Fix: Move `B()` to a different Spring bean, or use self-injection to route through the proxy"],
 ["The database automatically creates a nested savepoint"]),

("JAVA_BACKEND_ENGINEERING", "debug", "hard", "debugging", ["Timeouts", "Networking"],
 "A Java service connects to an API using `HttpURLConnection`. Under load, the service hangs, CPU drops to 0%, and thread dumps show workers stuck in `SocketInputStream.socketRead0`. What is the failure and the architectural fix?",
 "You experienced network timeout exhaustion. By default, `HttpURLConnection` has an infinite (0) connect and read timeout. If the 3rd party API hangs without closing the TCP connection, Java threads block infinitely waiting for bytes, eventually exhausting the thread pool. You must explicitly configure `.setConnectTimeout()` and `.setReadTimeout()` on every connection.",
 ["Network timeout exhaustion (infinite blocking)", "`HttpURLConnection` has infinite (0) read/connect timeouts by default", "Fix: Explicitly enforce fail-fast behavior using `.setConnectTimeout()` and `.setReadTimeout()`"],
 ["The garbage collector paused the threads indefinitely"]),

("JAVA_BACKEND_ENGINEERING", "implement", "medium", "implementation", ["Testing", "Mockito"],
 "You need to mock a static method `UUID.randomUUID()` in a JUnit 5 test. Standard Mockito `when()` throws an error because the method is static. How do you implement this mock properly using modern Mockito (3.4+)?",
 "You use the `Mockito.mockStatic()` feature wrapped in a try-with-resources block: `try (MockedStatic<UUID> mocked = mockStatic(UUID.class)) { mocked.when(UUID::randomUUID).thenReturn(myUuid); /* test */ }`. This guarantees the static mock is safely de-registered after the test, preventing it from polluting other tests running in the same JVM.",
 ["Use `Mockito.mockStatic(UUID.class)`", "Wrap it in a `try-with-resources` block", "Guarantees the static mock is scoped and de-registered, preventing global JVM test pollution"],
 ["Use Reflection to change the memory address of the UUID class"]),

("JAVA_BACKEND_ENGINEERING", "tradeoff", "medium", "tradeoff", ["Optional", "NullPointerException"],
 "When architecting a Java backend, what is the tradeoff between returning `null` vs returning `java.util.Optional` from a repository method (e.g., `findById`)?",
 "Returning `Optional` explicitly forces the caller (via the type system) to handle the absence of a value, drastically reducing `NullPointerException`s and allowing clean functional chaining. Tradeoff: Slight memory/CPU overhead (an extra wrapper object on the heap), and `Optional` is not Serializable, making it inappropriate for Entity or DTO fields.",
 ["`Optional` forces callers to handle nulls via the type system, reducing NPEs", "`Optional` enables clean functional chaining (`.map`, `.orElseThrow`)", "Tradeoff: Slight heap allocation overhead, and it is NOT Serializable (bad for DTO/Entity fields)"],
 ["`Optional` automatically connects to the database to retry the query"]),

("JAVA_BACKEND_ENGINEERING", "explain", "easy", "concept", ["Exceptions", "Checked vs Unchecked"],
 "In Java Exception Handling, what is the architectural difference between a 'Checked' Exception and an 'Unchecked' Exception?",
 "Checked Exceptions (inheriting from `Exception`, like `IOException`) are verified by the compiler; the developer is explicitly forced to either `catch` them or declare them via `throws`. Unchecked Exceptions (inheriting from `RuntimeException`, like `NullPointerException`) are not enforced by the compiler, typically representing unrecoverable programming errors.",
 ["Checked Exceptions (inherit from `Exception`) are strictly verified by the compiler at compile-time", "Developers must explicitly `catch` Checked exceptions or declare them with `throws`", "Unchecked Exceptions (inherit from `RuntimeException`) bypass compiler checks, used for programming errors"],
 ["Checked exceptions have a checkmark next to them in the IDE"]),

("JAVA_BACKEND_ENGINEERING", "debug", "medium", "debugging", ["Jackson", "StackOverflowError"],
 "A Spring REST controller returns a `List<UserEntity>`. Testing it results in a `StackOverflowError` during JSON serialization. What architectural mistake usually causes this in ORM-driven applications?",
 "This is caused by bidirectional JPA entity relationships (e.g., User has Orders, Order references User). When Jackson serializes the User, it serializes the Orders, which serialize the User, creating an infinite loop that overflows the call stack. Fixes: map Entities to clean DTOs, use `@JsonIgnore`, or use `@JsonManagedReference`/`@JsonBackReference`.",
 ["Bidirectional JPA relationships (A references B, B references A)", "Causes an infinite recursive loop during Jackson JSON serialization, overflowing the stack", "Fix: Map entities to clean DTOs (best practice) or use `@JsonIgnore`/`@JsonManagedReference`"],
 ["The database returned too many rows and exceeded physical RAM"]),

("JAVA_BACKEND_ENGINEERING", "implement", "hard", "implementation", ["Dependency Injection", "Testing"],
 "A legacy class tightly couples dependencies: `class Service { Database db = new Database(); }`. You want to refactor this to use Dependency Injection. What specific pattern do you implement, and how does it make the class testable?",
 "Implement 'Constructor Injection'. Remove the `new Database()` call and define a constructor: `public Service(Database db) { this.db = db; }`. This completely decouples the class from the concrete creation of its dependencies. It makes the class testable because during a JUnit test, you can trivially pass a Mock or Stub Database via the constructor without needing a Spring context.",
 ["Implement 'Constructor Injection' (`public Service(Database db)`)", "Decouples the class from the concrete creation of its dependencies", "Allows trivial injection of Mock/Stub objects during JUnit unit testing without a DI container"],
 ["Use `Thread.sleep()` to wait for the database to be ready"]),

("JAVA_BACKEND_ENGINEERING", "scenario", "medium", "scenario", ["Logging", "Security"],
 "You log to a file via Logback. Security mandates no passwords ever appear in logs, but developers frequently log full DTOs: `log.info(\"Req: {}\", dto)`. How do you architect a robust solution to prevent password leakage?",
 "Relying on developers to manually redact fields is fragile. You must implement a custom Logback Layout/Converter (or use a library like Logbook). You configure the logging framework to automatically detect and mask sensitive JSON keys or regex patterns (e.g., `\"password\": \"***\"`) globally at the framework level before writing to the appender.",
 ["Manual redaction is fragile and error-prone", "Implement a custom Logback Layout/Converter (or interceptor library)", "Globally masks sensitive JSON keys/regex patterns at the framework level before writing to the appender"],
 ["Fire any developer who logs a password"]),

("JAVA_BACKEND_ENGINEERING", "tradeoff", "easy", "tradeoff", ["Dependency Injection", "Spring"],
 "In enterprise Java, what is the tradeoff of using standard Constructor Injection versus Field Injection (`@Autowired` on fields) in Spring components?",
 "Field injection requires less boilerplate, but it hides dependencies, tightly couples the class to the Spring container (cannot be instantiated without Spring), and allows circular dependencies. Constructor injection explicitly declares dependencies, allows fields to be `final` (immutable), and allows trivial instantiation in unit tests without Spring, making it universally recommended.",
 ["Field Injection: Less boilerplate, but tightly couples to Spring and hides dependencies", "Constructor Injection: Allows `final` immutable fields and prevents circular dependencies", "Constructor Injection allows trivial instantiation with mocks in unit tests without starting Spring"],
 ["Field injection causes the JVM to run out of memory faster"]),

("JAVA_BACKEND_ENGINEERING", "debug", "hard", "debugging", ["ThreadLocal", "Tomcat"],
 "You use `ThreadLocal<UserContext>` in a Tomcat web app to store the user ID during an HTTP request. However, users report seeing data belonging to other users. Why did the `ThreadLocal` leak state across requests?",
 "Tomcat uses a Thread Pool to handle HTTP requests. When a request finishes, the thread is NOT destroyed; it is returned to the pool and reused for future, unrelated user requests. If you fail to explicitly call `threadLocal.remove()` in a `finally` block or interceptor at the end of the request, the previous user's state leaks into the next user's session.",
 ["Tomcat reuses threads from a Thread Pool for subsequent HTTP requests", "If state is not cleared, the pooled thread carries the old `ThreadLocal` state into the new request", "Fix: Explicitly call `threadLocal.remove()` in a `finally` block or post-request interceptor"],
 ["The users accidentally guessed each other's passwords"]),

("JAVA_BACKEND_ENGINEERING", "explain", "medium", "concept", ["ORM", "N+1 Problem"],
 "What is the 'N+1 Select Problem' in Java ORM frameworks (like Hibernate/JPA), and how do you resolve it?",
 "The N+1 problem occurs when an ORM executes 1 query to fetch a list of entities (e.g., 100 Users), and then executes N additional separate queries to lazily fetch a related entity for each user (e.g., their Profiles), resulting in 101 total queries instead of 1. Resolve this by using explicitly defined `JOIN FETCH` queries, EntityGraphs, or batch fetching strategies.",
 ["Executes 1 query for a list, and N queries to lazily fetch relations for each item", "Massively degrades performance due to excessive database round-trips", "Fix: Use `JOIN FETCH` (JPQL), EntityGraphs, or batch fetching to retrieve all data in 1 optimized query"],
 ["It is an off-by-one error when counting arrays"]),

("JAVA_BACKEND_ENGINEERING", "implement", "medium", "implementation", ["I/O", "Streams"],
 "You must read a massive 10GB text file in Java. `Files.readAllLines()` throws an `OutOfMemoryError`. How do you implement this efficiently in modern Java without loading the whole file into RAM?",
 "Use `Files.lines(Path)` which returns a lazily evaluated `Stream<String>`. Wrap it in a try-with-resources block: `try (Stream<String> stream = Files.lines(path))`. Java will stream the file line-by-line from disk, process it, and instantly discard the line from memory, keeping the heap footprint near zero. Chain `.filter()` and `.count()` on the stream.",
 ["Use `Files.lines(path)` which returns a lazily evaluated `Stream<String>`", "Must be wrapped in a `try-with-resources` block to ensure the underlying file handle is closed", "Streams line-by-line, discarding processed lines to keep heap usage near zero"],
 ["Buy more RAM and increase the JVM heap size to 12GB"]),

("JAVA_BACKEND_ENGINEERING", "scenario", "hard", "scenario", ["Resilience", "Backpressure"],
 "A Java app makes async calls to a 3rd party API. The API slows down, causing the Java app to crash (OOM) because millions of pending requests queue up in memory. How do you prevent the JVM from crashing?",
 "You must implement Backpressure or a Circuit Breaker. To prevent the in-memory queue from unbounded growth, cap the queue size (e.g., `ArrayBlockingQueue`) and define a rejection policy (e.g., shedding/dropping requests). Alternatively, implement a Circuit Breaker (Resilience4j) that trips when latency spikes, instantly failing new requests and protecting the heap.",
 ["Implement a Circuit Breaker (e.g., Resilience4j) to fail-fast when the downstream degrades", "Implement Backpressure by bounding the async queue size (e.g., `ArrayBlockingQueue`)", "Define a rejection policy (shedding load) instead of allowing unbounded memory growth"],
 ["Send an angry email to the 3rd party API developers"]),

("JAVA_BACKEND_ENGINEERING", "tradeoff", "medium", "tradeoff", ["REST", "API Design"],
 "When designing a Java REST API, what is the tradeoff between returning a 404 (Not Found) versus returning an empty array `[]` when querying a collection endpoint (`GET /users?role=admin`) that yields no results?",
 "Returning an empty array `[]` (with a 200 OK) is preferred for collection queries because the endpoint itself legitimately exists; there just happen to be zero matches. This avoids forcing clients to write try/catch logic for a 404 exception during standard filtering. A 404 should be strictly reserved for when the requested resource path itself (`/users/999`) physically does not exist.",
 ["`[]` with a 200 OK is preferred because the collection endpoint legitimately exists", "Prevents forcing frontend clients to use try/catch exception handling for standard filtering", "404 should be reserved strictly for when the resource path/ID itself does not physically exist"],
 ["404 is faster because it saves bandwidth on empty brackets"]),

("JAVA_BACKEND_ENGINEERING", "debug", "medium", "debugging", ["JUnit", "Floating Point"],
 "A test uses `assertEquals(0.3, a + b)` where `a=0.1` and `b=0.2` (doubles). It fails with `expected: <0.3> but was: <0.30000000000000004>`. Why, and what is the proper fix?",
 "Floating-point arithmetic (IEEE 754) is imprecise and cannot perfectly represent base-10 fractions like 0.1, leading to microscopic rounding errors. The fix in JUnit is to use the overloaded `assertEquals` method that accepts a `delta` (tolerance) parameter: `assertEquals(0.3, a + b, 0.0001)`. This asserts the actual value is within an acceptable mathematical margin of error.",
 ["IEEE 754 floating-point arithmetic is inherently imprecise with base-10 fractions", "Results in microscopic rounding errors during math", "Fix: Use the `assertEquals(expected, actual, delta)` overload to provide an acceptable tolerance margin"],
 ["The CPU is overheating and miscalculating math"]),

("JAVA_BACKEND_ENGINEERING", "fundamentals", "easy", "concept", ["Serializable", "Marker Interfaces"],
 "In Java, what is the architectural purpose of the `Serializable` interface, and why is it considered a 'marker' interface?",
 "The `Serializable` interface indicates to the JVM that an object's state can be safely serialized into a byte stream (to be saved to disk or sent over a network). It is a 'marker' interface because it contains zero methods to implement; it merely tags the class with a metadata flag that the built-in Java serialization machinery dynamically recognizes.",
 ["Flags an object as capable of being serialized into a byte stream (disk/network)", "Considered a 'marker' interface because it contains exactly zero methods", "Merely tags the class metadata for the JVM's serialization machinery"],
 ["It serializes the code into an array of strings"]),

("JAVA_BACKEND_ENGINEERING", "scenario", "medium", "scenario", ["Security", "XXE"],
 "You parse incoming XML files from an untrusted 3rd party. An attacker sends an XML file with recursive entity expansions, causing the JVM to consume 100% CPU and crash (OOM). What is this attack, and how do you stop it?",
 "This is an 'XML External Entity' (XXE) or 'Billion Laughs' attack, designed to cause a Denial of Service via exponential memory expansion. To stop it, you must explicitly configure the `DocumentBuilderFactory` or `SAXParserFactory` to disable external entities by setting the feature `http://apache.org/xml/features/disallow-doctype-decl` to `true`.",
 ["'XML External Entity' (XXE) or 'Billion Laughs' Denial of Service attack", "Causes exponential memory expansion via recursive XML entity declarations", "Fix: Configure the XML Parser Factory to explicitly disallow DOCTYPE declarations/external entities"],
 ["The XML parser got trapped in a while(true) loop"])
]
