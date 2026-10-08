"""Batch 25 Part 2 question content (Java Developer). Targeted Gap Generation."""

ROLE = "Java Developer"

BUCKET_KEYS = {
    "JAVA_CONCUR": ("Java Concurrency", "Multithreading & Thread Pools", "Java", ["Backend Developer", "Software Engineer"]),
}

Q = [
# ---------------- JAVA_CONCUR ----------------
("JAVA_CONCUR", "scenario", "hard", "scenario", ["Wait/Notify"],
 "You have a classic 'Producer-Consumer' pattern using a `java.util.LinkedList` protected by a `synchronized` block. Sometimes, a consumer thread wakes up from a `wait()` call but immediately crashes with a `NoSuchElementException` when popping the list. What crucial loop structure did the developer miss when calling `wait()`?",
 "The developer used an `if (list.isEmpty()) wait();` conditional block instead of a `while (list.isEmpty()) wait();` loop. Threads can suffer from arbitrary OS-level 'spurious wakeups', or another consumer thread might have preempted the awakened thread and emptied the list between the wakeup and the lock re-acquisition. `wait()` must always be wrapped in a `while` loop that re-checks the condition.",
 ["Used an `if` block instead of a `while` loop to check the condition", "Threads can suffer from arbitrary 'spurious wakeups'", "Another thread might empty the list between the wakeup and lock re-acquisition"],
 ["The list was deleted by the garbage collector"]),

("JAVA_CONCUR", "tradeoff", "medium", "tradeoff", ["Locks"],
 "What are the tradeoffs between using a `ReentrantLock` versus a standard `synchronized` block in Java?",
 "`synchronized` is syntactically simple, highly optimized by the JVM via Lock Elision/Coarsening, and automatically releases the lock upon exiting or exceptions. `ReentrantLock` requires explicit `try/finally` unlocking (which is error-prone), but provides powerful advanced concurrency features like fairness policies, interruptible lock acquisition (`lockInterruptibly()`), and timeout-based non-blocking acquisition (`tryLock()`).",
 ["`synchronized`: Syntactically simple, auto-releases on exceptions, JIT optimized", "`ReentrantLock`: Requires explicit `try/finally` unlocking", "Tradeoff: `ReentrantLock` provides advanced features (fairness, interruptible locks, timeout acquisition)"],
 ["`ReentrantLock` allows locking multiple doors at once"]),

("JAVA_CONCUR", "debug", "medium", "debugging", ["Volatile"],
 "Two threads increment a shared integer: `public volatile int counter = 0; ... counter++;`. Even though the variable is `volatile`, the final count is inaccurate under high load. Why doesn't `volatile` prevent this race condition?",
 "The `volatile` keyword only guarantees memory visibility (ensuring threads always read the most recently written value from main memory, bypassing CPU caches). It does NOT make compound operations atomic. The `counter++` operation is actually three distinct steps: read, modify, write. The threads can still preempt and interleave between the read and the write, causing lost updates. You must use `AtomicInteger` or synchronization.",
 ["`volatile` only guarantees memory visibility (reads see latest writes), not atomicity", "`counter++` is a read-modify-write operation (3 distinct steps)", "Threads can interleave between the read and write steps, losing updates"],
 ["`volatile` evaporates quickly under heavy load"]),

("JAVA_CONCUR", "implement", "hard", "implementation", ["CompletableFuture"],
 "You need to execute 10 independent database queries asynchronously and wait for ALL of them to complete. If any single query fails, you want the entire operation to immediately fail fast. How do you implement this cleanly using Java `CompletableFuture`?",
 "You collect the 10 asynchronous futures into an array and pass them to `CompletableFuture.allOf(futures...).join()`. The `allOf` method returns a single future that completes when all provided futures complete. If any underlying future completes exceptionally, the `join()` call will immediately throw a `CompletionException`, achieving clean, fail-fast behavior.",
 ["Collect futures into an array", "Use `CompletableFuture.allOf(futures...).join()`", "If any future fails, `join()` immediately throws a `CompletionException`"],
 ["Wrap all 10 calls in a massive `try-catch` block"]),

("JAVA_CONCUR", "fundamentals", "easy", "concept", ["Executors"],
 "What is the primary difference between `ExecutorService.submit()` and `ExecutorService.execute()` when submitting tasks to a Java thread pool?",
 "`execute()` takes a `Runnable`, returns `void`, and if an unhandled exception occurs inside the task, it instantly prints a stack trace and permanently kills the worker thread. `submit()` takes a `Callable` or `Runnable`, returns a `Future` object, and silently captures any unhandled exceptions. The exception is only re-thrown when you explicitly call `future.get()`.",
 ["`execute()` returns void; unhandled exceptions instantly kill the worker thread", "`submit()` returns a `Future` object", "`submit()` captures exceptions, which are only thrown when `future.get()` is called"],
 ["`submit()` requires a physical button press"]),

("JAVA_CONCUR", "explain", "medium", "concept", ["Thread Pools"],
 "Explain the concept of 'Thread Starvation' in Java. How can an improperly configured `ThreadPoolExecutor` cause starvation when executing recursive or dependent tasks?",
 "Starvation occurs when threads are perpetually denied access to CPU execution time. If a thread pool of size 5 executes 5 'parent' tasks, and those parent tasks submit 5 'child' tasks to the *same* pool and block waiting for them (e.g., via `future.get()`), the pool instantly deadlocks. The children can never execute because the parents are consuming all 5 available threads while indefinitely waiting for the children to finish.",
 ["Starvation occurs when threads are perpetually denied execution resources", "If parent tasks submit child tasks to the same pool and block waiting for them, the pool deadlocks", "Parents consume all threads waiting for children that have no threads to execute on"],
 ["Threads literally run out of RAM and starve to death"]),

("JAVA_CONCUR", "scenario", "hard", "scenario", ["Concurrent Collections"],
 "A developer uses `ConcurrentHashMap` for high-performance concurrent counting: `map.put(key, map.getOrDefault(key, 0) + 1);`. Under heavy concurrency, counts are lost. Why does this fail, and what is the correct `ConcurrentHashMap` method to use?",
 "While the individual `get()` and `put()` calls are completely thread-safe, combining them creates a classic 'Check-Then-Act' race condition. A thread can read a value, get preempted by the OS, and another thread updates it before the first thread executes its `put()`. To fix this, you must use atomic methods like `map.compute(key, (k, v) -> (v == null) ? 1 : v + 1)` or `map.merge()`.",
 ["Individual `get()` and `put()` are thread-safe, but combining them is not atomic", "Creates a classic 'Check-Then-Act' race condition between the read and the write", "Must use atomic methods like `map.compute()` or `map.merge()`"],
 ["The map was too small and dropped the numbers"]),

("JAVA_CONCUR", "tradeoff", "hard", "tradeoff", ["Virtual Threads"],
 "What are the tradeoffs of using Java 21 Virtual Threads (Project Loom) versus traditional OS-level Platform Threads for a high-concurrency web server?",
 "Virtual threads are incredibly lightweight (managed by the JVM, not the OS), allowing you to spawn millions of them, drastically simplifying asynchronous code by using synchronous blocking I/O styles without exhausting OS resources. However, they provide zero performance benefit for purely CPU-bound tasks. Furthermore, Virtual Threads can suffer from 'Pinning'—if they execute `synchronized` blocks or call native JNI code, they block the underlying OS carrier thread, negating their benefits.",
 ["Virtual Threads: Extremely lightweight, allows millions of concurrent blocking I/O tasks", "Tradeoff: Zero performance benefit for purely CPU-bound tasks", "Tradeoff: Susceptible to 'Pinning' when using `synchronized` blocks or JNI, blocking the underlying OS carrier thread"],
 ["Virtual Threads require a VR headset to debug"]),

("JAVA_CONCUR", "debug", "medium", "debugging", ["Executors"],
 "You have a `ThreadPoolExecutor` configured with `corePoolSize=10`, `maxPoolSize=50`, and a `LinkedBlockingQueue(100)`. When 20 concurrent requests arrive, you notice only 10 threads are running, and 10 tasks are queued. Why doesn't the pool spin up the remaining 40 threads to `maxPoolSize`?",
 "By design, a standard `ThreadPoolExecutor` only creates new threads beyond the `corePoolSize` *after* the blocking queue is completely full. Because the queue (capacity 100) easily holds the 10 overflow tasks, the pool has no architectural reason to create new threads yet. It will only scale to `maxPoolSize` when 111 concurrent tasks arrive.",
 ["Pools only create threads beyond `corePoolSize` AFTER the blocking queue is completely full", "Because the queue (capacity 100) holds the extra 10 tasks, no new threads are created", "Will only scale to `maxPoolSize` when the queue reaches 100% capacity"],
 ["The OS limits all Java programs to exactly 10 threads"]),

("JAVA_CONCUR", "implement", "easy", "implementation", ["Safe Publication"],
 "How do you safely publish a fully initialized, complex configuration object to multiple reader threads without using explicit `synchronized` locks?",
 "You can declare the reference variable pointing to the object as `volatile` (e.g., `private volatile Config config;`). Alternatively, if the configuration is immutable, you declare all internal fields of the Config object as `final`. The Java Memory Model explicitly guarantees that `final` fields are safely published and visible to all threads once the constructor finishes, without requiring locks.",
 ["Declare the reference variable as `volatile`", "Alternatively, declare all internal fields of the object as `final`", "The Java Memory Model guarantees safe publication for `final` fields without locks"],
 ["Print the configuration to the console for threads to read"]),

("JAVA_CONCUR", "fundamentals", "medium", "concept", ["Synchronization Aids"],
 "What does the `java.util.concurrent.CountDownLatch` do, and how does it differ from a `CyclicBarrier`?",
 "A `CountDownLatch` allows one or more threads to wait until a specific number of operations performed by other threads completes (the latch counts down to zero). Crucially, a CountDownLatch cannot be reused once it hits zero. A `CyclicBarrier` forces a set number of threads to wait for *each other* to reach a common barrier execution point before they can all continue, and it can be reset and reused for subsequent iterations.",
 ["`CountDownLatch`: Threads wait until a counter reaches zero. Cannot be reused.", "`CyclicBarrier`: Threads wait for *each other* to reach a common barrier point.", "`CyclicBarrier` can be reset and reused for cyclic operations"],
 ["`CountDownLatch` locks the physical server rack"]),

("JAVA_CONCUR", "scenario", "hard", "scenario", ["ReadWriteLocks"],
 "You use a `ReentrantReadWriteLock` to protect a cache. Multiple reader threads hold the read lock. A writer thread attempts to acquire the write lock and is blocked. While the writer is waiting, more reader threads request the read lock. In a perfectly 'fair' locking scenario, what happens to the new reader threads?",
 "In a fair `ReentrantReadWriteLock`, the new reader threads will be blocked and queued *behind* the waiting writer thread. If the lock were 'unfair', new readers could continually acquire the lock as long as any other reader held it, causing perpetual 'Writer Starvation'. Fair mode strictly guarantees the writer eventually gets the lock by blocking subsequent readers.",
 ["New reader threads are blocked and queued *behind* the waiting writer thread", "Prevents 'Writer Starvation'", "Ensures the writer eventually gets the lock in a strictly FIFO queue"],
 ["The new readers fight the writer in memory"]),

("JAVA_CONCUR", "explain", "medium", "concept", ["Atomics"],
 "What is the 'ABA Problem' in concurrent lock-free programming, and how does Java's `AtomicStampedReference` solve it?",
 "The ABA problem occurs in Compare-And-Swap (CAS) operations. Thread 1 reads value 'A'. Thread 2 changes it to 'B', and then back to 'A'. Thread 1's CAS succeeds because the value is still 'A', completely missing the interim state changes (which can corrupt linked structures). `AtomicStampedReference` solves this by attaching an integer stamp (version number) to the reference. CAS checks both the value and the stamp, failing if the stamp changed.",
 ["Occurs when a value changes from A to B and back to A, tricking a CAS operation into succeeding", "`AtomicStampedReference` attaches a version stamp to the reference", "CAS checks both the value and the stamp, failing if interim changes incremented the stamp"],
 ["ABA stands for Always Be Allocating"]),

("JAVA_CONCUR", "tradeoff", "medium", "tradeoff", ["Concurrent Collections"],
 "What is the tradeoff of using `CopyOnWriteArrayList` compared to `Collections.synchronizedList()`?",
 "`CopyOnWriteArrayList` provides blazing fast, entirely lock-free thread-safe iteration because every write/modification creates a brand new physical copy of the underlying array. The severe tradeoff is horrific performance and massive memory overhead for write operations. It is architecturally only suitable for lists where traversals/reads vastly outnumber mutations (e.g., event listener lists).",
 ["Provides blazing fast, lock-free iteration", "Tradeoff: Every write operation creates a full physical copy of the underlying array", "Tradeoff: Horrific write performance/memory overhead; only suitable for read-heavy workloads"],
 ["It physically copies the list to a USB drive"]),

("JAVA_CONCUR", "debug", "hard", "debugging", ["CompletableFuture"],
 "You execute `CompletableFuture.supplyAsync(() -> doHeavyWork()).thenAccept(result -> process(result));`. You notice that sometimes `process(result)` is executed by a `ForkJoinPool` worker thread, but other times it executes directly on the main calling thread. Why is the execution thread unpredictable?",
 "Because `thenAccept` (without the 'Async' suffix) executes the continuation synchronously on whatever thread happens to complete the previous stage. If the `supplyAsync` heavy work finishes *before* the main thread even reaches the `thenAccept` line, the main thread instantly executes the continuation itself. If `supplyAsync` is still running, the background worker thread will execute the continuation upon completion.",
 ["`thenAccept` executes synchronously on whatever thread completes the previous stage", "If `supplyAsync` finishes quickly, the main caller thread executes it", "If `supplyAsync` takes time, the background worker thread executes it"],
 ["The JVM flips a coin to decide thread assignment"]),

("JAVA_CONCUR", "implement", "medium", "implementation", ["Synchronization Aids"],
 "You need to implement a strict rate limiter that allows exactly 5 concurrent threads to access a third-party API simultaneously. Additional threads must block until a slot opens. What specific Java concurrency primitive is designed for this?",
 "You use a `java.util.concurrent.Semaphore` initialized with 5 permits (`new Semaphore(5)`). Threads call `.acquire()` before making the API call, which blocks if all 5 permits are taken. They must call `.release()` inside a `finally` block after the API call finishes to return the permit.",
 ["Use a `java.util.concurrent.Semaphore` initialized with 5 permits", "Threads call `.acquire()` before the operation", "Threads call `.release()` inside a `finally` block to return the permit"],
 ["Use 5 separate keyboards"]),

("JAVA_CONCUR", "fundamentals", "easy", "concept", ["Thread States"],
 "What does the `Thread.yield()` method do?",
 "It acts as a hint to the underlying OS thread scheduler that the current thread is willing to temporarily pause its execution and yield its current CPU time slice, allowing other threads of the same or higher priority to execute. Crucially, the OS is entirely free to ignore this hint, and it does not release any synchronized locks held by the thread.",
 ["A hint to the OS scheduler to temporarily pause the thread and yield its CPU time slice", "Allows other threads of the same/higher priority to execute", "The OS can ignore it, and it does not release held locks"],
 ["It causes the thread to permanently surrender to the JVM"]),

("JAVA_CONCUR", "scenario", "medium", "scenario", ["Architecture"],
 "A Java web server handles incoming requests by spinning up a `new Thread(task).start()` for every single request. Under extreme load, the server crashes with `OutOfMemoryError: unable to create new native thread`. Why is this architecture fundamentally flawed, and what is the fix?",
 "Creating native OS threads is incredibly expensive in terms of CPU overhead, and each thread strictly allocates a massive chunk of OS memory (typically 1MB for the thread stack). Unbounded thread creation rapidly exhausts OS RAM and kernel thread limits. The correct architecture is to use a bounded `ThreadPoolExecutor` (to reuse a fixed number of threads) or adopt Java 21 Virtual Threads.",
 ["Creating OS threads is expensive and allocates massive stack memory (1MB each)", "Unbounded creation exhausts OS RAM and kernel limits", "Fix: Use a bounded `ThreadPoolExecutor` to reuse threads, or use Virtual Threads"],
 ["Threads are downloaded from the internet, saturating bandwidth"]),

("JAVA_CONCUR", "explain", "hard", "concept", ["JIT Compiler"],
 "Explain 'Lock Coarsening' and 'Lock Elision' optimizations performed by the JVM JIT compiler.",
 "Lock Coarsening: If the JIT detects multiple sequential synchronized blocks on the exact same object, it merges them into a single larger lock to avoid the CPU overhead of repeatedly acquiring/releasing. Lock Elision: Using Escape Analysis, if the JIT proves that a synchronized object (like a local `StringBuffer`) never escapes the executing thread, it completely removes the synchronization instructions because a lock is mathematically unnecessary.",
 ["Lock Coarsening: Merges multiple sequential locks on the same object into one larger lock", "Lock Elision: Removes locks entirely if Escape Analysis proves the object never escapes the thread", "Both heavily optimize naive synchronization overhead at runtime"],
 ["They are physical filters applied to the CPU fan"]),

("JAVA_CONCUR", "tradeoff", "hard", "tradeoff", ["ThreadLocal"],
 "What are the tradeoffs between using standard Thread-Local variables (`ThreadLocal<T>`) versus the newer Scoped Values (`ScopedValue<T>`) introduced in recent Java versions?",
 "`ThreadLocal` allows arbitrary, mutable state associated with a thread, but it can easily cause severe memory leaks and data pollution in thread pools if not explicitly removed. `ScopedValue` is strictly immutable, bound to a specific lexical scope (e.g., a lambda block), automatically cleans up when the scope exits (preventing leaks entirely), and scales significantly better regarding memory across millions of Virtual Threads.",
 ["`ThreadLocal`: Mutable, but prone to severe memory leaks in thread pools if not explicitly cleared", "`ScopedValue`: Immutable and strictly bound to a lexical scope", "`ScopedValue` tradeoff: Automatically cleans up and scales better for Virtual Threads, but prevents arbitrary mutation"],
 ["`ScopedValue` requires a microscope to read"])
]
