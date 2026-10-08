"""Batch 35 Part 2 question content (Java Developer). Targeted Gap Generation."""

ROLE = "Java Developer"

BUCKET_KEYS = {
    "JVM_AND_CONCURRENCY": ("JVM & Concurrency", "Multithreading & Tuning", "Java", ["Java Developer", "Backend Developer"]),
}

Q = [
# ---------------- JVM_AND_CONCURRENCY ----------------
("JVM_AND_CONCURRENCY", "tradeoff", "hard", "tradeoff", ["Garbage Collection", "ZGC"],
 "When tuning the JVM GC for a high-frequency trading platform, what is the exact tradeoff between using the Parallel GC versus the Z Garbage Collector (ZGC)?",
 "The Parallel GC maximizes absolute throughput (total transactions/sec) by pausing the application entirely to run parallel cleanup; this causes unpredictable, long 'Stop-The-World' pauses, violating latency requirements. ZGC sacrifices a small percentage of overall throughput to guarantee ultra-low latency, ensuring Stop-The-World pauses never exceed a few milliseconds, making ZGC vastly superior for HFT.",
 ["Parallel GC maximizes throughput but introduces long, unpredictable Stop-The-World pauses", "ZGC sacrifices slight throughput for guaranteed ultra-low latency (sub-millisecond pauses)", "ZGC is vastly superior for strict real-time/HFT systems where latency consistency is critical"],
 ["Parallel GC is for Windows, ZGC is for Linux"]),

("JVM_AND_CONCURRENCY", "debug", "medium", "debugging", ["Metaspace", "Memory Leaks"],
 "You encounter `OutOfMemoryError: Metaspace`. You increase `-Xmx` (Heap Space), but the app crashes with the exact same error. Why didn't increasing the heap fix the issue?",
 "The Metaspace is a completely separate memory region from the Java Heap. It stores class metadata, static variables, and the constant pool. Increasing `-Xmx` only increases the space for instantiated objects, doing absolutely nothing for the Metaspace. To fix it, you must increase `-XX:MaxMetaspaceSize` or investigate a classloader memory leak (dynamically generating too many classes).",
 ["Metaspace is physically separate from the standard Java Heap", "Increasing `-Xmx` only increases Heap space for objects, not class metadata", "Fix: Increase `-XX:MaxMetaspaceSize` or fix the dynamic classloader leak"],
 ["You didn't download enough RAM from the cloud"]),

("JVM_AND_CONCURRENCY", "implement", "hard", "implementation", ["Locking", "ReadWriteLock"],
 "Multiple threads frequently read a cached config object, but rarely write to it. Using a `synchronized` block on the read methods causes massive lock contention. How do you implement a more efficient locking architecture?",
 "Replace the `synchronized` blocks with a `ReadWriteLock` (specifically `ReentrantReadWriteLock` or modern `StampedLock`). This allows an infinite number of threads to acquire the read lock simultaneously, drastically increasing read throughput. The write lock remains mutually exclusive, completely blocking all reads and writes only during the rare configuration updates.",
 ["Use `ReentrantReadWriteLock` or `StampedLock`", "Allows concurrent, simultaneous read access by multiple threads (eliminating read contention)", "Write lock remains mutually exclusive, safely blocking all access during updates"],
 ["Ask the threads nicely to take turns"]),

("JVM_AND_CONCURRENCY", "scenario", "medium", "scenario", ["Garbage Collection", "GC Roots"],
 "You debug a massive memory leak. A heap dump shows an `ArrayList` identified as a 'GC Root' holding 4GB of data. What does it mean for an object to be a 'GC Root', and why does it prevent memory cleanup?",
 "A 'GC Root' is an object that is intrinsically accessible and kept alive by the JVM itself (e.g., a static variable, an active local variable in a running thread's stack, or JNI references). The GC traces all references starting from these roots. Because the `ArrayList` is a GC Root (likely `static`), the GC considers it perpetually 'in use', preventing destruction.",
 ["GC Roots are objects inherently kept alive by the JVM (e.g., static fields, active thread stacks)", "The GC traces all reachable objects starting from these roots", "Because it is a root, the GC assumes it is actively 'in use' and cannot free the memory"],
 ["It has roots that physically dug into the motherboard RAM slots"]),

("JVM_AND_CONCURRENCY", "explain", "easy", "concept", ["volatile", "Java Memory Model"],
 "In the Java Memory Model, what specific guarantee does the `volatile` keyword provide for a variable?",
 "The `volatile` keyword guarantees 'visibility'. It forces the JVM to read the variable directly from main memory (RAM) and write changes directly back to main memory, bypassing local CPU cache optimization. This guarantees that if Thread A modifies a variable, Thread B will instantly see the update. However, `volatile` does *not* guarantee atomicity (e.g., `count++` is not thread-safe).",
 ["Guarantees cross-thread 'visibility' of the variable's value", "Forces reads/writes directly to main RAM, bypassing CPU L1/L2 caches", "Tradeoff: Does NOT guarantee atomicity (compound operations like `++` will still race)"],
 ["It makes the variable highly explosive and likely to crash the server"]),

("JVM_AND_CONCURRENCY", "debug", "hard", "debugging", ["CompletableFuture", "ForkJoinPool"],
 "A developer uses `CompletableFuture.supplyAsync(() -> slowDBQuery())`. During a traffic spike, the entire Java app becomes unresponsive, including unrelated endpoints. Why did `supplyAsync` cause a global bottleneck?",
 "By default, if you do not explicitly pass a custom `Executor`, `supplyAsync()` executes on the shared global `ForkJoinPool.commonPool()`. If you flood the common pool with slow, blocking I/O tasks, you exhaust all its threads. Any other part of the app (e.g., parallel streams) attempting to use the common pool freezes. You must explicitly pass a dedicated `ThreadPoolExecutor` for blocking I/O.",
 ["`supplyAsync()` defaults to the global `ForkJoinPool.commonPool()`", "Flooding it with blocking I/O exhausts the shared threads, freezing the entire JVM", "Fix: Explicitly pass a dedicated, bounded `ThreadPoolExecutor` for I/O tasks"],
 ["The database was scared of the traffic spike and hid"]),

("JVM_AND_CONCURRENCY", "implement", "medium", "implementation", ["Atomic Classes", "CAS"],
 "You need a thread-safe counter. Using a `synchronized` method for `increment()` works but creates a bottleneck. What built-in Java class provides a lock-free, highly performant alternative?",
 "Use `java.util.concurrent.atomic.AtomicInteger` (or `AtomicLong`). These classes use hardware-level Compare-And-Swap (CAS) instructions to safely increment the value without ever acquiring a software lock or suspending threads. For even higher contention scenarios (multiple threads heavily updating, rarely reading), `LongAdder` is even more performant.",
 ["Use `AtomicInteger` or `AtomicLong`", "Uses hardware-level Compare-And-Swap (CAS) instructions to avoid software locks", "For extremely high contention, use `LongAdder`"],
 ["Use a `String` and append \"1\" to it every time"]),

("JVM_AND_CONCURRENCY", "tradeoff", "hard", "tradeoff", ["Virtual Threads", "Project Loom"],
 "Java 21 introduced Virtual Threads. What is the architectural tradeoff of replacing OS threads with Virtual Threads for a strictly CPU-bound mathematical application (like video encoding)?",
 "Virtual Threads are lightweight and multiplexed onto a small pool of carrier OS threads. They excel at I/O-bound tasks because they yield the carrier thread when blocking. However, for a purely CPU-bound task that never blocks, a Virtual Thread monopolizes the carrier OS thread. There is zero performance gain (and slight scheduling overhead) for CPU tasks; you are fundamentally limited by physical CPU cores.",
 ["Virtual Threads excel at I/O-bound tasks by yielding the OS carrier thread when blocking", "For strictly CPU-bound tasks, they monopolize the carrier OS thread entirely", "Tradeoff: Zero performance gain for CPU-bound math; standard OS threads or parallel streams are better"],
 ["Virtual threads only exist in the Metaverse"]),

("JVM_AND_CONCURRENCY", "scenario", "medium", "scenario", ["wait/notify", "Spurious Wakeups"],
 "A Java thread is stuck in `WAITING`. It used `object.wait()` inside a `synchronized` block, and another thread explicitly called `object.notify()`. Why is the waiting thread still not waking up?",
 "The `notify()` method wakes up exactly one *random* thread waiting on that monitor. If multiple threads were waiting, the JVM might have woken the wrong thread. Alternatively, a 'missed signal' occurred if `notify()` was called *before* the target reached `wait()`. Fix: Always use `notifyAll()`, and wrap `wait()` in a `while (condition)` loop to handle spurious wakeups/missed signals.",
 ["`notify()` wakes up a random thread; it may have woken the wrong one", "Missed signal: `notify()` occurred before the thread actually called `wait()`", "Fix: Use `notifyAll()` and wrap `wait()` inside a `while(condition)` loop"],
 ["The thread was wearing noise-canceling headphones"]),

("JVM_AND_CONCURRENCY", "explain", "easy", "concept", ["Thread Dumps", "Diagnostics"],
 "What is a 'Thread Dump' in Java, and what specific problem is it primarily used to diagnose?",
 "A Thread Dump is a snapshot of the exact state and call stack of every single thread running inside the JVM at a specific millisecond. It is the primary diagnostic tool used to identify Deadlocks (threads trapped waiting on each other's locks), infinite loops, or to see exactly which method is blocking a hung thread pool.",
 ["A snapshot of the exact state and call stack of every JVM thread", "Primarily used to diagnose Deadlocks and infinite loops", "Shows exactly which line of code is blocking a thread"],
 ["It dumps all the threads out of the CPU to cool it down"]),

("JVM_AND_CONCURRENCY", "debug", "medium", "debugging", ["ConcurrentHashMap", "Race Conditions"],
 "Thread A calls `map.put(\"key\", 1)`. Thread B concurrently calls `map.put(\"key\", 2)`. Why does `ConcurrentHashMap` guarantee internal thread safety, but still potentially result in logical race conditions for your app?",
 "`ConcurrentHashMap` guarantees its internal hash buckets will not be corrupted during concurrent writes. However, if you perform a compound action ('Check-then-Act': `if (!map.containsKey(k)) map.put(k, v)`), the thread can be preempted between the check and the put, causing a logical race. You must use atomic methods like `map.putIfAbsent(key, val)` or `map.compute()`.",
 ["Guarantees internal data structure integrity (no corrupted hash buckets)", "Does NOT protect compound 'Check-then-Act' logic (e.g., `if (!contains) put()`)", "Fix: Must use atomic compound methods like `putIfAbsent()` or `compute()`"],
 ["The map throws a `RaceConditionException` automatically"]),

("JVM_AND_CONCURRENCY", "implement", "hard", "implementation", ["JFR", "Profiling"],
 "You are profiling a Java app in production to find CPU bottlenecks. You cannot install APM agents or restart the JVM. What built-in, low-overhead diagnostic tool can you dynamically attach to record profiles?",
 "Use Java Flight Recorder (JFR) combined with `jcmd`. JFR is deeply integrated into the JVM and has roughly ~1% overhead, making it safe for production. You use `jcmd <pid> JFR.start` to begin recording a profile (CPU sampling, memory allocation, GC pauses), and later dump the recording to analyze offline in Java Mission Control (JMC).",
 ["Use Java Flight Recorder (JFR) via the `jcmd` CLI tool", "JFR has ~1% overhead, making it perfectly safe for live production profiling", "Analyze the resulting dump offline using Java Mission Control (JMC)"],
 ["Attach a webcam to the server to watch the CPU spin"]),

("JVM_AND_CONCURRENCY", "tradeoff", "medium", "tradeoff", ["ThreadLocal", "Architecture"],
 "When designing a multithreaded architecture, what is the tradeoff of using `ThreadLocal` variables versus explicitly passing a 'Context' object as a parameter through every method signature?",
 "`ThreadLocal` magically provides global access to state (like User Session) anywhere in the call stack without cluttering method signatures. Tradeoff: It creates hidden dependencies (harder to test), and introduces severe memory leak risks in thread-pool environments (like Tomcat) if the variable is not explicitly cleaned up (`.remove()`) at the end of the request.",
 ["`ThreadLocal` prevents method signature clutter by magically passing state globally", "Tradeoff: Creates hidden dependencies, making unit testing harder", "Tradeoff: Causes severe memory leaks in Thread Pools if `.remove()` is not explicitly called"],
 ["`ThreadLocal` only works within a 5-mile radius of the server"]),

("JVM_AND_CONCURRENCY", "scenario", "hard", "scenario", ["Safepoints", "GC Pauses"],
 "During a massive GC pause, JVM logs show a long 'Safepoint Sync Time'. What is a Safepoint, and why did it delay the Garbage Collector from starting?",
 "Before a Stop-The-World GC begins, every running Java thread must pause at a designated 'Safepoint' so the JVM has a consistent view of memory. 'Safepoint Sync Time' is the time the JVM waits for the *last* lagging thread to finally reach a safepoint. This happens if a thread is stuck in a massive loop (e.g., array copying) lacking safepoint polling, delaying the entire GC.",
 ["A Safepoint is a designated pause location for threads so the JVM can safely analyze memory", "The JVM must wait for *every* thread to reach a safepoint before starting Stop-The-World GC", "Lagging threads (e.g., in massive unpolled loops) delay the synchronization, stalling the GC"],
 ["A Safepoint is a backup server where the JVM saves its data"]),

("JVM_AND_CONCURRENCY", "explain", "hard", "concept", ["Escape Analysis", "JIT Compiler"],
 "What is 'Escape Analysis' in the JVM JIT compiler, and how does it improve performance?",
 "Escape Analysis is a JIT optimization technique. The compiler analyzes a newly instantiated object to determine if it 'escapes' the current method (e.g., returned to a caller, or assigned to a global field). If it *never* escapes, the JIT completely skips heap allocation, instead allocating the object's fields directly onto the CPU registers or Thread Stack, eliminating GC overhead.",
 ["JIT optimization determining if an object's reference 'escapes' the local method scope", "If it does not escape, the JVM skips standard Heap allocation", "Allocates the object directly on the Thread Stack/CPU registers, eliminating Garbage Collection overhead"],
 ["It analyzes the building blueprints to find the fastest fire exit"]),

("JVM_AND_CONCURRENCY", "debug", "medium", "debugging", ["Thread Pools", "OutOfMemoryError"],
 "A developer creates a `new Thread(new RunnableTask()).start()` inside a web controller for every incoming HTTP request. Under heavy load, the server crashes with `OutOfMemoryError: unable to create new native thread`. Why?",
 "Spawning a raw OS thread is incredibly expensive; each thread consumes ~1MB of memory outside the heap for its stack. Creating a new thread per request unbounded quickly exhausts OS memory limits or hits the OS thread cap (`ulimit`). You must *never* spawn raw threads per request; strictly bound concurrency using a `ThreadPoolExecutor` or Virtual Threads.",
 ["Raw OS threads are extremely expensive (~1MB stack memory each outside the heap)", "Unbounded thread creation quickly exhausts physical OS memory or hits the `ulimit` thread cap", "Fix: Strictly bound concurrency using a `ThreadPoolExecutor` (or Virtual Threads)"],
 ["The threads got tangled together and short-circuited"]),

("JVM_AND_CONCURRENCY", "implement", "easy", "implementation", ["Daemon Threads", "Lifecycle"],
 "You have a background thread. You want to ensure that if the main application shuts down, this background thread does not keep the JVM alive indefinitely. What specific configuration must you apply?",
 "You must set the thread as a Daemon thread by calling `thread.setDaemon(true)` *before* calling `thread.start()`. The JVM will automatically exit and violently terminate all running threads as soon as all non-daemon (user) threads have finished execution.",
 ["Call `thread.setDaemon(true)` before starting it", "Daemon threads do not prevent the JVM from shutting down", "The JVM violently terminates daemon threads when all user threads finish"],
 ["Ask the thread politely to commit seppuku"])
]
