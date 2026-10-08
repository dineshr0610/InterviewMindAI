import asyncio
import json
import os
import re
import sys
import uuid
from collections import Counter

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from phase4d_diversity_audit import fetch_all_supabase, normalize_text

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "Java Developer"
VALID_INTENTS = {"fundamentals", "explain", "implement", "tradeoff", "debug", "scenario", "compare",
                 "architecture", "optimize", "diagnose"}
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|prompt instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

def existing_supabase():
    out = []
    for r in asyncio.run(fetch_all_supabase()):
        meta = r.get("metadata", {})
        if meta.get("status") == "inactive":
            continue
        c = r.get("content", "")
        if "### Instruction:" in c and "### Output:" in c:
            q = c.split("### Instruction:")[1].split("### Output:")[0].strip()
            if "write a program" in q.lower() or "implement a function" in q.lower():
                continue
            a = c.split("### Output:")[1].strip()
        elif "**Answer:**" in c:
            q = c.split("**Answer:**")[0].replace("### Technical Interview Question", "").replace("**Question:**", "").strip()
            a = c.split("**Answer:**")[1].strip()
        else:
            q = meta.get("question", c[:200])
            a = meta.get("expected_answer", "")
        if len(set(re.findall(r"[a-z0-9]+", q.lower()))) < 3:
            continue
        out.append((q, a))
    return out

def opening(q, n=3):
    return " ".join(normalize_text(q).split()[:n])

Q = [
    # Bucket 1: JVM GARBAGE COLLECTION
    ("B1", "diagnose", "hard", "debugging", ["G1GC"], "A production JVM using G1GC begins logging frequent 'Evacuation Failure' or 'To-space Exhausted' events, followed immediately by massive latency spikes. What causes this, and how do you tune G1 to prevent it?", "An Evacuation Failure occurs when G1 runs out of empty regions in the heap while trying to copy surviving objects from the Young/Eden regions during a collection. This forces a fallback to a brutal single-threaded Full GC (the latency spike). You prevent it by increasing the heap size, increasing `G1ReservePercent`, or decreasing `InitiatingHeapOccupancyPercent` (IHOP) to trigger concurrent marking cycles earlier.", ["Evacuation Failure / To-space Exhausted", "Fallback to single-threaded Full GC", "Tune IHOP or G1ReservePercent"], ["It means the disk is full"]),
    ("B1", "compare", "medium", "compare", ["ZGC", "Shenandoah"], "Compare the technical mechanisms that allow modern low-latency garbage collectors like ZGC and Shenandoah to perform concurrent object relocation without stopping application threads.", "ZGC uses 'Colored Pointers' (storing metadata bits inside the 64-bit reference address itself) combined with load barriers to detect and heal stale references as the application reads them. Shenandoah traditionally used 'Brooks Pointers' (an extra forwarding pointer embedded in the object header) and load/store barriers to redirect reads/writes to the newly relocated object copy.", ["ZGC uses Colored Pointers", "Shenandoah uses Brooks Pointers / forwarding pointers", "Both use read/load barriers to heal references concurrently"], ["They just use more CPU threads"]),
    ("B1", "diagnose", "medium", "debugging", ["Generational GC"], "During a load test, you notice 'Premature Promotion' occurring frequently in the JVM. What does this mean for Garbage Collection performance, and what JVM flags help diagnose/tune it?", "Premature Promotion happens when short-lived objects survive long enough in the Young Generation to hit the `MaxTenuringThreshold` (or the survivor spaces are too small, forcing overflow) and are promoted to the Old Generation. This degrades performance because the Old Gen fills up rapidly with garbage, triggering expensive Major/Full GCs. It is diagnosed using `-XX:+PrintTenuringDistribution` and fixed by tuning `-XX:SurvivorRatio` or increasing the Young Gen size.", ["Short-lived objects promoted to Old Gen", "Survivor spaces too small or threshold too low", "-XX:+PrintTenuringDistribution"], ["It means the objects are too large"]),
    ("B1", "scenario", "medium", "scenario", ["G1GC"], "Your application allocates large `byte[]` arrays frequently. In G1GC, how are these 'humongous objects' treated differently from standard allocations, and why might they cause performance degradation?", "In G1GC, an object larger than 50% of a region size is classified as a 'humongous object'. They bypass the Young Generation entirely and are allocated directly into contiguous regions in the Old Generation. Frequent humongous allocations fragment the Old Gen rapidly and can trigger continuous, expensive Concurrent Marking cycles. Tuning `-XX:G1HeapRegionSize` to be larger can prevent objects from being classified as humongous.", ["Allocated directly in Old Generation", "Can cause rapid fragmentation and continuous concurrent cycles", "Tune -XX:G1HeapRegionSize"], ["They are stored on disk"]),
    ("B1", "optimize", "medium", "optimize", ["Memory Tuning"], "A Java backend caching millions of user profiles suffers from high heap usage. Profiling reveals that 30% of the heap consists of identical `String` objects (e.g., repeating city names). How can you optimize this without changing application code?", "You can enable G1GC String Deduplication using `-XX:+UseStringDeduplication`. During garbage collection, G1 will identify Strings that have identical underlying `char[]` or `byte[]` arrays and rewrite their references to point to a single shared array, significantly reducing memory footprint with a very small CPU overhead during GC.", ["-XX:+UseStringDeduplication", "Shares identical underlying byte arrays", "Zero code changes required"], ["Use String.intern() everywhere"]),
    ("B1", "explain", "hard", "concept", ["GC Pauses"], "When analyzing a G1GC log, you observe a long 'Concurrent Mark' phase that took 500ms, but the application SLA monitor shows no latency spikes. However, a 'Remark' phase of 50ms caused SLA alerts. Why?", "The 'Concurrent Mark' phase runs entirely in the background concurrently with application threads, so it does not block application execution (no STW pause). The 'Remark' phase, however, is a Stop-The-World (STW) pause required to finalize the marking process. Therefore, even though Remark is much shorter, it pauses all application threads, causing the SLA latency alerts.", ["Concurrent Mark runs alongside application threads (no STW)", "Remark is a Stop-The-World (STW) pause", "STW pauses block application execution causing latency"], ["Concurrent mark is faster"]),
    ("B1", "diagnose", "hard", "debugging", ["Allocation Buffers"], "A highly concurrent Java application exhibits severe thread lock contention during object allocation, but only on heavily loaded 64-core servers. How do Thread-Local Allocation Buffers (TLABs) relate to this, and how might you tune them?", "TLABs allow threads to allocate objects in their own dedicated chunk of Eden space without locking. On a 64-core server with massive allocation rates, threads may exhaust their TLABs too quickly. When a TLAB is exhausted, the thread must acquire a lock on the shared Eden space to get a new TLAB, causing contention. You can tune this by increasing the TLAB size or using `-XX:+ResizeTLAB` to allow the JVM to automatically adapt TLAB sizes.", ["TLABs prevent locking during allocation", "Frequent exhaustion forces threads to lock the shared Eden space", "Increase TLAB size"], ["The JVM uses synchronized blocks for all memory"]),
    ("B1", "tradeoff", "medium", "tradeoff", ["References"], "You are implementing a memory-sensitive cache in Java. What is the explicit tradeoff between using `SoftReference` versus `WeakReference` for the cached entries regarding Garbage Collection behavior?", "A `WeakReference` is aggressively collected by the GC on the very next cycle if there are no strong references to it, making it unsuitable for a persistent cache. A `SoftReference` is specifically designed for caching; the JVM will keep it alive through multiple GC cycles and will only aggressively clear it if the JVM is under severe memory pressure and approaching an OutOfMemoryError.", ["WeakReferences are cleared on the next GC cycle", "SoftReferences survive until the JVM faces memory pressure", "SoftReferences are better for caching"], ["Soft references are faster"]),
    ("B1", "diagnose", "easy", "debugging", ["Memory Tuning"], "A Java application crashes with `java.lang.OutOfMemoryError: Metaspace`. What typically causes a Metaspace leak as opposed to a standard Java Heap leak?", "The Metaspace stores class metadata, static fields, and method definitions, not instance objects. A Metaspace OOM is almost always caused by a ClassLoader leak. This occurs when an application dynamically generates classes at runtime (e.g., using CGLib, proxies, or reflection) or when hot-reloading applications in an application server (like Tomcat) fails to garbage collect the old ClassLoaders.", ["Metaspace stores class metadata", "Caused by dynamic class generation or ClassLoader leaks", "Not caused by standard object creation"], ["You created too many HashMaps"]),
    ("B1", "tradeoff", "medium", "tradeoff", ["JVM Flags"], "A legacy library calls `System.gc()` frequently, causing massive Stop-The-World pauses. You apply the `-XX:+DisableExplicitGC` flag to fix it. What is the primary hidden risk of disabling explicit GCs, particularly involving direct memory?", "The hidden risk involves Direct ByteBuffers (NIO memory allocated outside the Java heap). Direct buffers rely on the garbage collection of their small Java 'wrapper' objects to trigger the freeing of the native memory. If you disable explicit GCs, RMI or NIO libraries that rely on `System.gc()` to clean up direct memory might fail to run, leading to a native OutOfMemoryError.", ["Direct ByteBuffers rely on GC to free native memory", "Disabling explicit GC can cause native OutOfMemoryErrors"], ["It makes the heap grow infinitely"]),

    # Bucket 2: JVM PERFORMANCE / TUNING
    ("B2", "explain", "medium", "concept", ["JIT Compiler"], "In the HotSpot JVM, what is the architectural purpose of Tiered Compilation (utilizing both the C1 and C2 compilers)?", "Tiered Compilation balances fast startup times with peak long-term performance. The C1 compiler acts quickly, compiling methods with minimal optimization to get the application running fast. As the application runs, the JVM profiles the code. Heavily used ('hot') methods are then passed to the C2 compiler, which takes longer to compile but applies aggressive, deep optimizations (like inlining and loop unrolling) for peak throughput.", ["C1 compiles quickly for fast startup", "C2 compiles slowly with deep optimizations for peak performance", "Profiles code at runtime to identify hot methods"], ["C1 is for frontend, C2 is for backend"]),
    ("B2", "diagnose", "hard", "debugging", ["JIT Compiler"], "A low-latency Java trading system runs flawlessly for 3 hours. Suddenly, throughput plummets for 5 seconds, CPU spikes, and a 'Deoptimization' log is generated before performance returns to normal. What just happened inside the JIT compiler?", "The C2 JIT compiler aggressively optimizes code based on optimistic assumptions (e.g., 'this interface only ever has one implementation'). If a new class is dynamically loaded that breaks that assumption (e.g., a second implementation of the interface), the JIT's optimized machine code is no longer valid. The JVM throws it away (Deoptimization), falls back to the slow interpreter, and must re-profile and re-compile the code.", ["JIT made optimistic assumptions that were invalidated", "JVM throws away optimized code and falls back to interpreter", "Re-compiles code, causing the temporary CPU/latency spike"], ["The JVM ran out of memory"]),
    ("B2", "diagnose", "hard", "debugging", ["Safepoints"], "You observe intermittent 500ms latency spikes in your application. GC logs show the actual pause times are 10ms, but the 'Time To Safepoint' (TTSP) is 490ms. What code pattern causes high Time To Safepoint?", "A high Time To Safepoint means the JVM requested a global pause (STW), but one or more threads refused to yield. This is typically caused by threads executing large, tight 'counted loops' (e.g., iterating a massive array) where the JIT compiler optimized away the safepoint polling checks. The JVM must wait for the loop to finish before the GC can begin. Using `-XX:+UseCountedLoopSafepoints` can mitigate this.", ["JVM requested STW but threads refused to yield", "Caused by tight counted loops missing safepoint polls", "JVM waits for the loop to finish before pausing"], ["The database is slow"]),
    ("B2", "architecture", "medium", "architecture", ["Memory Tuning"], "When building high-performance concurrency frameworks (like Disruptor), developers historically used 'cache line padding' to prevent False Sharing. How does modern Java solve this more cleanly?", "Modern Java provides the `@Contended` annotation. False sharing occurs when two independent volatile variables happen to reside on the same 64-byte CPU cache line; when one thread updates variable A, it invalidates the cache line for a thread reading variable B, causing a memory stall. `@Contended` instructs the JVM to automatically insert memory padding around the variable, isolating it on its own cache line.", ["@Contended annotation", "Prevents independent variables from sharing a CPU cache line", "Avoids cache invalidation stalls across threads"], ["Use the volatile keyword everywhere"]),
    ("B2", "tradeoff", "medium", "tradeoff", ["Profiling"], "When profiling a Java application in production, why is `async-profiler` vastly superior to traditional JMX-based profilers (like VisualVM or JConsole) regarding thread sampling?", "Traditional profilers rely on JVMTI and require threads to reach a JVM Safepoint to capture a stack trace. This causes the 'Safepoint Bias' problem, where tight loops or native code execution are completely missed, and the profiling itself causes massive STW overhead. `async-profiler` uses OS-level APIs (like `perf_events` on Linux) to interrupt and sample threads asynchronously at the CPU level, providing highly accurate profiles with near-zero overhead.", ["Traditional profilers require Safepoints (Safepoint Bias)", "async-profiler uses OS APIs (perf_events) asynchronously", "Near-zero overhead and captures native/tight loop execution"], ["async-profiler is written in Python"]),
    ("B2", "explain", "medium", "concept", ["JIT Compiler"], "What is 'Escape Analysis' in the HotSpot JVM, and what specific optimization does it unlock that dramatically reduces Garbage Collection pressure?", "Escape Analysis is a JIT compiler technique that determines if an object's reference 'escapes' the local scope of a method or thread. If the JIT proves an object never escapes, it unlocks 'Scalar Replacement'. Instead of allocating the object on the Heap, the JIT breaks the object down into its primitive fields and stores them directly in CPU registers or on the thread's Stack. This prevents heap allocation entirely, removing work for the GC.", ["JIT checks if an object reference leaves the method scope", "Unlocks Scalar Replacement", "Allocates object fields on the Stack/Registers instead of Heap"], ["It prevents memory leaks"]),
    ("B2", "diagnose", "hard", "debugging", ["JIT Compiler"], "Your application iterates over a `List<Animal>` calling `animal.speak()`. For the first hour, the list only contains `Dog` objects, and it executes in 10ms. Later, you add `Cat` and `Bird` objects to the list. The loop execution time jumps to 50ms, even though there are the same number of items. Why did the JIT performance degrade?", "The method call transitioned from Monomorphic to Megamorphic. When only `Dog` was present, the JIT used 'Inline Caching' and potentially inlined the method entirely because there was only one receiver type. Once multiple implementations appeared (`Cat`, `Bird`), the call became Megamorphic. The JIT can no longer inline it and must perform a costly virtual method table (vtable) lookup on every iteration.", ["Monomorphic to Megamorphic transition", "JIT loses ability to inline the method", "Must perform virtual method table lookups"], ["Cats and Birds are larger objects"]),
    ("B2", "compare", "medium", "compare", ["GraalVM"], "Compare the warmup characteristics of a standard HotSpot JVM application versus an Ahead-Of-Time (AOT) compiled GraalVM Native Image.", "A HotSpot JVM starts slowly and executes code using the interpreter. It requires 'warmup' time to profile the application and allow the JIT compiler to generate highly optimized machine code, eventually reaching high peak throughput. A GraalVM Native Image is compiled to machine code at build time. It starts almost instantly (zero warmup), making it ideal for Serverless functions, but its peak throughput is often slightly lower than HotSpot because it lacks dynamic runtime profiling data.", ["HotSpot starts slow but reaches high peak throughput via JIT", "GraalVM starts instantly via AOT compilation", "GraalVM may have lower peak throughput due to lack of runtime profiling"], ["GraalVM uses Python instead of Java"]),
    ("B2", "diagnose", "medium", "debugging", ["JVM Internals"], "A massive Java monolith is deployed. After a few days, a warning appears: 'CodeCache is full. Compiler has been disabled.' What is the immediate impact on the application, and how do you fix it?", "The Code Cache is the memory area where the JVM stores compiled JIT machine code. When it fills up, the JIT compiler stops working. The immediate impact is a catastrophic degradation in performance because any newly loaded or uncompiled methods will be forced to execute in the slow interpreter forever. You fix it by increasing `-XX:ReservedCodeCacheSize`.", ["JIT compiler stops working", "Methods forced to run in the slow interpreter", "Increase -XX:ReservedCodeCacheSize"], ["The JVM throws an OutOfMemoryError and crashes"]),
    ("B2", "optimize", "medium", "architecture", ["Memory Tuning"], "How does enabling Large Pages (HugePages) via `-XX:+UseLargePages` improve JVM performance on heavily loaded systems with massive heaps?", "Modern CPUs use a Translation Lookaside Buffer (TLB) to cache mappings from virtual memory to physical RAM. With standard 4KB pages, a massive JVM heap causes frequent TLB misses, forcing the CPU to perform slow page table walks. Large Pages (e.g., 2MB or 1GB) drastically reduce the number of memory pages required. This increases the TLB hit rate, directly improving CPU memory access speeds and reducing GC pause times.", ["Reduces TLB (Translation Lookaside Buffer) misses", "CPU spends less time doing page table walks", "Improves memory access speed and GC pauses"], ["It makes the hard drive faster"]),

    # Bucket 3: REACTIVE STREAMS (Reactor)
    ("B3", "scenario", "medium", "scenario", ["Reactive Streams"], "In a Project Reactor pipeline, your fast Kafka consumer produces events significantly faster than your slow downstream Postgres database can save them. How does Reactive Streams prevent an `OutOfMemoryError`?", "Reactive Streams prevents OOMs using Backpressure. The slow subscriber (Postgres writer) sends a 'demand' signal (`request(n)`) up the pipeline to the fast publisher (Kafka). The publisher is contractually obligated to only push `n` items. If the database cannot keep up, it stops requesting items, forcing the Kafka consumer to pause polling, thus naturally buffering at the source rather than crashing the JVM memory.", ["Backpressure via demand signaling (request(n))", "Subscriber dictates the pace of data flow", "Prevents unbounded buffering in JVM memory"], ["It uses a try/catch block"]),
    ("B3", "compare", "hard", "compare", ["Reactive Streams"], "In Project Reactor, compare the behavioral difference between placing `subscribeOn()` versus `publishOn()` in a `Flux` pipeline.", "`subscribeOn()` dictates which thread scheduler executes the entire subscription process from the very beginning (the source emission), and it affects the upstream publisher regardless of where it is placed in the chain. `publishOn()` affects the thread context for downstream operators. It intercepts signals and passes them to a different scheduler, changing the thread execution only for operators chained *after* it.", ["subscribeOn affects the upstream source emission thread", "publishOn affects downstream operators sequentially after it", "subscribeOn placement doesn't matter, publishOn placement does"], ["They do the exact same thing"]),
    ("B3", "diagnose", "medium", "debugging", ["Reactive Streams"], "Your reactive Spring WebFlux application occasionally freezes entirely. You suspect a developer accidentally used a blocking JDBC call inside a reactive pipeline, tying up the limited Netty event loop threads. How can you definitively detect this in testing?", "You should integrate `BlockHound` into your test suite. BlockHound instruments the JVM at a low level to detect if any thread marked as 'non-blocking' (like a Reactor Netty thread) attempts to execute a blocking system call (like `Thread.sleep()`, socket reads, or JDBC calls). It will immediately throw an exception, pointing directly to the offending line of code.", ["Integrate BlockHound", "Detects blocking I/O calls on non-blocking threads", "Throws an exception pointing to the blocking code"], ["Just read the code manually"]),
    ("B3", "explain", "medium", "concept", ["Reactive Streams"], "Explain the difference between a 'Hot' and 'Cold' Publisher in Project Reactor.", "A Cold Publisher generates data anew for every single subscriber; nothing happens until `subscribe()` is called (e.g., executing a database query per subscriber). A Hot Publisher emits data continuously regardless of whether anyone is listening, and multiple subscribers share the same stream of data (e.g., listening to a live mouse click stream or a Kafka topic).", ["Cold publishers generate data anew for each subscriber (lazy)", "Hot publishers emit data continuously (multicast/shared)", "Nothing happens in Cold until subscribe() is called"], ["Hot publishers are faster"]),
    ("B3", "tradeoff", "hard", "tradeoff", ["Reactive Streams"], "When processing a `Flux` of IDs and calling a remote API for each, what is the exact tradeoff between using `flatMap()` versus `concatMap()`?", "`flatMap()` executes the inner publishers concurrently, interleaving the results. It provides maximum throughput and speed, but the output order is completely non-deterministic. `concatMap()` executes the inner publishers strictly sequentially, waiting for one to complete before subscribing to the next. It guarantees ordering but sacrifices all concurrency, acting as a performance bottleneck.", ["flatMap executes concurrently but loses ordering", "concatMap executes sequentially preserving order", "Tradeoff between throughput and determinism"], ["concatMap is just a newer version of flatMap"]),
    ("B3", "scenario", "medium", "scenario", ["Reactive Streams"], "In a Reactor pipeline, an API call fails and throws an exception. If you use `onErrorResume()`, what happens to the original `Flux` pipeline after the fallback value is emitted?", "In the Reactive Streams specification, an error is a terminal signal. When `onErrorResume()` catches the exception and emits the fallback sequence, the original `Flux` sequence is permanently terminated. It will not process any remaining elements that were queued in the original source. If you want to continue processing subsequent elements, you must handle the error within a flatMap inner publisher.", ["Errors are terminal signals", "The original Flux is permanently terminated", "It will not process remaining elements"], ["It just skips the error and continues normally"]),
    ("B3", "compare", "medium", "compare", ["Reactive Streams"], "Why can't you safely use `ThreadLocal` variables (like Spring Security context or MDC logging contexts) in a reactive `Flux` pipeline, and what is the Reactor alternative?", "Reactive pipelines execute asynchronously, meaning a single request's processing will hop across multiple different threads in an Event Loop pool during its lifecycle. A `ThreadLocal` is bound to one specific thread, so the context will be lost or leaked when the pipeline hops threads. The Reactor alternative is the `ContextView` (or Context API), which binds immutable data to the specific `Subscription` flow rather than a thread.", ["Execution hops across multiple threads", "ThreadLocal data is lost during thread hops", "Use the Reactor Context API instead"], ["ThreadLocal is deprecated in Java 17"]),
    ("B3", "compare", "medium", "compare", ["Java Concurrency"], "Compare `CompletableFuture` and Project Reactor's `Mono` regarding eager versus lazy execution.", "A `CompletableFuture` is eager; the moment it is instantiated or returned from a method, the asynchronous computation has already started. A `Mono` is entirely lazy; creating a `Mono` simply defines an execution plan. Absolutely no work, network calls, or side effects occur until a downstream consumer explicitly calls `subscribe()` on it.", ["CompletableFuture is eager (starts immediately)", "Mono is lazy (waits for subscribe())", "Mono defines a blueprint for execution"], ["Mono is just a wrapper for CompletableFuture"]),
    ("B3", "explain", "easy", "concept", ["Reactive Streams"], "When combining two Reactive streams using `zip()`, how does it determine when to emit an element?", "`zip()` strictly waits for one element from *every* participating source publisher. Once it has a matching pair (or tuple) of elements, it combines them using a combinator function and emits the result. If one publisher emits faster than the other, `zip` internally buffers the fast publisher's elements until the slow publisher produces a matching element.", ["Waits for one element from every source", "Combines them into a pair/tuple", "Buffers fast publishers until slow publishers emit"], ["It emits whenever any source emits"]),
    ("B3", "architecture", "medium", "architecture", ["Reactive Streams"], "You are building a Spring WebFlux application, but you must call a legacy blocking SOAP API that takes 2 seconds to respond. How do you architect this to avoid crashing the WebFlux event loop?", "You must isolate the blocking call using `subscribeOn()` or `publishOn()` backed by a dedicated bounded scheduler, typically `Schedulers.boundedElastic()`. This offloads the blocking SOAP call to a separate, dynamically sizing thread pool designed for blocking I/O, ensuring the primary Netty event loop threads remain completely free to handle other non-blocking web requests.", ["Isolate the blocking call using subscribeOn/publishOn", "Use Schedulers.boundedElastic()", "Offloads to a dedicated thread pool so Netty threads don't block"], ["You can't do this in WebFlux"]),

    # Bucket 4: ADVANCED CONCURRENCY
    ("B4", "explain", "medium", "concept", ["Java Memory Model"], "In the Java Memory Model, explain the 'happens-before' guarantee provided by the `volatile` keyword.", "The `volatile` keyword ensures that any write to a volatile variable establishes a 'happens-before' relationship with any subsequent read of that same variable. This guarantees visibility across threads: when Thread A writes to a volatile variable, the CPU flushes its local cache to main memory. When Thread B reads it, it invalidates its local cache and reads directly from main memory, ensuring it sees the latest value.", ["Ensures visibility across threads", "Flushes local CPU cache to main memory on write", "Invalidates local cache on read"], ["It makes the variable thread-safe for increments"]),
    ("B4", "architecture", "hard", "architecture", ["Java Concurrency"], "How does `ConcurrentHashMap` achieve high concurrency without locking the entire map during writes, and how did this implementation change from Java 7 to Java 8?", "In Java 7, it used 'Segmenting' (an array of segments, each with its own ReentrantLock). In Java 8, it abandoned segments and achieves concurrency at the individual bucket (node) level. It uses Compare-And-Swap (CAS) operations to insert new nodes into empty buckets lock-free, and only uses `synchronized` on the specific head node of a bucket if a collision occurs, drastically reducing lock contention.", ["Java 8 locks at the individual bucket/node level", "Uses Compare-And-Swap (CAS) for empty buckets", "Java 7 used Segment locking"], ["Java 8 just uses a giant synchronized block"]),
    ("B4", "diagnose", "hard", "debugging", ["Virtual Threads"], "You migrate a Spring Boot application to Java 21 Virtual Threads. Performance improves overall, but suddenly a specific endpoint using JDBC suffers from severe thread starvation and latency spikes. What is 'Carrier Thread Pinning', and how does it explain this?", "Virtual threads execute on top of a small pool of OS 'carrier threads'. If a virtual thread enters a `synchronized` block or executes a native method (which older JDBC drivers often did), it 'pins' the carrier thread to the CPU. If the virtual thread then performs a blocking I/O operation while pinned, the OS carrier thread is blocked entirely. If enough virtual threads do this, all carrier threads are exhausted, stalling the entire application.", ["Virtual threads execute on OS carrier threads", "Synchronized blocks 'pin' the carrier thread", "Blocking while pinned exhausts the carrier thread pool"], ["Virtual threads are just slower than real threads"]),
    ("B4", "compare", "medium", "compare", ["Java Concurrency"], "Compare a `ReentrantReadWriteLock` with the newer `StampedLock`. In what specific read-heavy scenario does `StampedLock` provide superior performance?", "`ReentrantReadWriteLock` forces all readers to acquire a lock, which still causes cache-line contention among readers updating the lock's state. `StampedLock` provides an 'Optimistic Read' mode. It returns a stamp (long) without acquiring any locks or updating state. After reading the variables, the thread validates the stamp. If no write occurred, the read is completely lock-free and extremely fast. If a write did occur, it falls back to a pessimistic read lock.", ["StampedLock provides an Optimistic Read mode", "Reads require zero lock acquisition or state updates", "Validates a stamp after reading to ensure consistency"], ["StampedLock is for distributed systems"]),
    ("B4", "explain", "medium", "concept", ["Java Concurrency"], "What is the primary advantage of using `VarHandle` (introduced in Java 9) over the legacy `Unsafe` class or `AtomicReferenceFieldUpdater`?", "`VarHandle` provides a safe, standard API for performing atomic operations, Compare-And-Swap (CAS), and fine-grained memory fencing on variables (including arrays) without the overhead of instantiating `Atomic` wrapper objects. It replaces the internal, unsupported, and dangerous `sun.misc.Unsafe` class, while providing better performance and type-safety than the reflection-based `AtomicReferenceFieldUpdater`.", ["Safe, standard replacement for sun.misc.Unsafe", "Performs atomic/CAS operations without Atomic wrapper overhead", "Better performance and type-safety than FieldUpdaters"], ["VarHandle is used for writing variables to disk"]),
    ("B4", "diagnose", "easy", "debugging", ["Java Concurrency"], "When analyzing a Java thread dump, how do you differentiate between a Deadlock and a Livelock based on the thread states?", "In a Deadlock, the thread dump will explicitly show threads in a `BLOCKED` state, waiting to acquire a monitor lock held by another thread, and the JVM often automatically detects and prints the deadlock chain. In a Livelock, the threads are actively executing and yielding to each other, so the thread dump will show them in a `RUNNABLE` state, consuming high CPU but making no actual progress.", ["Deadlock threads are in BLOCKED state", "Livelock threads are in RUNNABLE state consuming CPU", "JVM can automatically detect BLOCKED deadlocks"], ["Deadlocks only happen with databases"]),
    ("B4", "compare", "medium", "compare", ["Java Concurrency"], "Compare `CountDownLatch` and `CyclicBarrier`. Which one is reusable, and which one allows threads to wait for each other rather than just waiting for a countdown?", "A `CountDownLatch` cannot be reset; once the count reaches zero, it remains open forever. It is used when one thread waits for N operations to complete. A `CyclicBarrier` is reusable (cyclic). It is used when N threads must all wait for *each other* to reach a common barrier point before any of them are allowed to proceed.", ["CyclicBarrier is reusable, CountDownLatch is not", "CyclicBarrier makes threads wait for each other", "CountDownLatch makes a thread wait for N events"], ["They are identical"]),
    ("B4", "architecture", "hard", "architecture", ["Java Concurrency"], "Explain the 'Work-Stealing' algorithm used internally by the `ForkJoinPool` (which powers parallel streams and `CompletableFuture`).", "In a `ForkJoinPool`, every worker thread maintains its own double-ended queue (deque) of tasks. When a thread spawns new sub-tasks, it pushes them onto the head of its own deque and processes them LIFO (Last-In-First-Out) for better cache locality. If a thread runs out of tasks, it acts as a 'thief' and steals tasks from the *tail* (FIFO) of another busy thread's deque, naturally balancing the load while minimizing lock contention.", ["Threads have their own double-ended queues (deque)", "Threads steal from the tail of other threads' queues when idle", "Minimizes lock contention and balances load naturally"], ["It sends tasks over the network to other servers"]),
    ("B4", "scenario", "medium", "scenario", ["Java Concurrency"], "You have a fixed-size `ThreadPoolExecutor` of 10 threads. You submit 10 parent tasks. Each parent task submits a child task to the *same* executor and calls `.get()` to wait for the child result. What happens, and what is this anti-pattern called?", "The application will instantly freeze in a Thread Starvation Deadlock. All 10 threads in the pool are occupied by the parent tasks. Every parent task is blocked waiting for its child task to finish. However, the child tasks are sitting in the executor's queue waiting for a thread to become available. Since no threads will ever become available, the system deadlocks.", ["Thread Starvation Deadlock", "Parent tasks consume all threads and block", "Child tasks stuck in queue waiting for threads"], ["The executor automatically creates more threads"]),
    ("B4", "diagnose", "medium", "debugging", ["Java Concurrency"], "A Java backend application using a massive `ThreadLocal` cache is deployed to Tomcat. After a few hot redeployments, the server crashes with `OutOfMemoryError: Metaspace`. Why did the `ThreadLocal` cause this?", "Tomcat uses a persistent thread pool. When the application is redeployed, the application ClassLoader is discarded, but the Tomcat worker threads remain alive. If the application does not explicitly clear its `ThreadLocal` variables during shutdown, the persistent Tomcat threads hold references to objects created by the old ClassLoader. This prevents the entire ClassLoader (and all its classes in Metaspace) from being garbage collected, causing a massive leak.", ["Tomcat worker threads survive redeployments", "ThreadLocal references keep the old ClassLoader alive", "Prevents Metaspace garbage collection"], ["ThreadLocal is too large for the heap"]),

    # Bucket 5: PRODUCTION JVM DIAGNOSIS
    ("B5", "diagnose", "hard", "debugging", ["JVM Diagnostics"], "A production Linux server running Java is experiencing 100% CPU usage. Walk through the exact command-line steps to identify the specific line of Java code causing the spike.", "First, run `top -H -p <pid>` to view individual threads for the JVM process and identify the OS Thread ID (PID) consuming the CPU. Second, convert that decimal OS Thread ID to Hexadecimal. Third, run `jstack <pid>` to capture a JVM thread dump. Finally, search the thread dump for `nid=0x<hex_id>`. The stack trace under that Native ID (nid) reveals the exact Java code causing the spike.", ["Use top -H to find the OS thread ID consuming CPU", "Convert thread ID to Hexadecimal", "Use jstack and search for the nid matching the hex value"], ["Just restart the server"]),
    ("B5", "diagnose", "medium", "debugging", ["JVM Diagnostics"], "You capture a Java Heap Dump to analyze a memory leak using the Eclipse Memory Analyzer Tool (MAT). What is the conceptual difference between the 'Shallow Heap' and the 'Retained Heap' of an object?", "The 'Shallow Heap' is simply the memory consumed by the object itself (its headers and primitive fields), which is usually very small. The 'Retained Heap' is the crucial metric for leaks: it represents the total memory that would be freed by the Garbage Collector if that specific object were destroyed, including all child objects that are kept alive exclusively by this parent object.", ["Shallow Heap is just the object itself", "Retained Heap is the memory freed if the object is garbage collected", "Retained Heap includes exclusively referenced child objects"], ["Shallow heap is on disk, Retained is in RAM"]),
    ("B5", "diagnose", "medium", "debugging", ["JVM Diagnostics"], "Your JVM occasionally crashes with `java.lang.OutOfMemoryError: unable to create new native thread`. The heap has plenty of free space. What are the two most common OS-level causes for this?", "This error means the JVM asked the OS for a new thread and the OS refused. The two main causes are: 1) The OS has reached a user-level process/thread limit (e.g., `ulimit -u` in Linux is set too low). 2) The machine is genuinely out of physical RAM and Swap space, so the OS cannot allocate the required native memory for the new thread's execution stack.", ["OS user-level thread limits reached (ulimit -u)", "Machine is completely out of physical RAM for thread stacks", "Not related to Java Heap space"], ["The Java Heap is full"]),
    ("B5", "tradeoff", "medium", "tradeoff", ["Profiling"], "You are investigating a latency regression in production. What is the fundamental performance tradeoff between generating a JVM Thread Dump (`jstack`) versus recording a profile with Java Flight Recorder (JFR)?", "A Thread Dump (`jstack`) requires a global Stop-The-World (STW) safepoint to snapshot all threads. Taking frequent thread dumps causes severe application pausing (the observer effect). JFR is deeply integrated into the JVM C++ runtime and records events lock-free into thread-local buffers asynchronously. JFR can run continuously in production with less than 1% overhead, capturing historical data without pausing the application.", ["Thread dumps require expensive STW safepoints", "JFR writes asynchronously to thread-local buffers with <1% overhead", "JFR can run continuously in production safely"], ["Thread dumps require restarting the JVM"]),
    ("B5", "architecture", "easy", "architecture", ["JVM Diagnostics"], "A monitoring tool needs to trigger a diagnostic command inside a running Java process (like forcing a GC or printing GC class stats). Historically JMX was used. What modern command-line tool provides this capability locally without needing JMX ports open?", "The `jcmd` utility. It allows you to send diagnostic command requests to a running JVM on the local machine (e.g., `jcmd <pid> GC.run` or `jcmd <pid> Thread.print`). It is faster, more secure, and less resource-intensive than configuring and connecting via JMX.", ["jcmd utility", "Sends diagnostic commands locally without JMX", "Faster and more secure"], ["Use the kill command"]),
    ("B5", "diagnose", "hard", "debugging", ["Memory Tuning"], "A Java microservice processing network streams throws `OutOfMemoryError: Direct buffer memory`. The `-Xmx` (Heap) is large and mostly empty. What causes this, and how do you diagnose/fix it?", "Direct buffer memory is allocated outside the Java Heap by NIO libraries (like Netty) using `ByteBuffer.allocateDirect()`. The limit is controlled independently by `-XX:MaxDirectMemorySize`. If the application leaks direct buffers or the limit is too low, this OOM occurs. You fix it by increasing the flag, or using tools like JFR or Netty's `ResourceLeakDetector` to track down unreleased native buffers.", ["Allocated outside Java Heap via NIO", "Controlled by -XX:MaxDirectMemorySize", "Diagnosed using Netty leak detector or JFR"], ["It means the hard drive is full"]),
    ("B5", "scenario", "medium", "scenario", ["JVM Diagnostics"], "A production Java service is heavily CPU bound. You notice the CPU usage is extremely high, but when you profile the application code, the business logic methods consume very little time. However, JVM internal methods related to `Integer.valueOf()` and garbage collection dominate the profile. What is the root cause?", "The root cause is excessive Autoboxing in a tight loop. The application is converting primitive `int` values to `Integer` objects repeatedly. Since values outside the cache range (-128 to 127) require allocating a new `Integer` object on the heap, this creates massive allocation pressure, saturating the CPU with continuous minor Garbage Collection cycles rather than business logic.", ["Excessive Autoboxing in tight loops", "Creates massive allocation pressure on the heap", "CPU is consumed by Garbage Collection, not business logic"], ["The Integer class is deprecated"]),
    ("B5", "diagnose", "medium", "debugging", ["JVM Performance"], "Your Spring Boot application handles 1000 requests per second. Suddenly, latency spikes to 10 seconds for all users. The CPU is at 5%, Memory is stable, and there are no GC pauses. A thread dump reveals 200 Tomcat worker threads in a `WAITING` state on a `HikariCP` connection pool. What is the diagnosis?", "The application has exhausted the database connection pool (Connection Pool Starvation). The backend is waiting for the database to respond, or a slow query/deadlock in the database is preventing connections from being returned to the pool. Because all threads are stuck waiting for a database connection, no new HTTP requests can be processed, despite the JVM being healthy and idle.", ["Connection Pool Starvation", "Threads are stuck waiting for a database connection", "Caused by slow DB queries or unreturned connections"], ["The JVM Garbage Collector is broken"]),
    ("B5", "explain", "medium", "concept", ["JVM Internals"], "When capturing a Java Heap Dump in production, it is common to add the `:live` option (e.g., `jmap -dump:live,format=b,file=heap.bin <pid>`). What hidden performance danger does the `:live` flag introduce?", "The `:live` flag forces the JVM to execute a full Stop-The-World (STW) Garbage Collection *before* generating the heap dump. This ensures only reachable, live objects are dumped, making the file smaller and easier to analyze. However, forcing a Full GC on a massive heap in production will cause a severe, multi-second latency pause that can trigger load balancer timeouts.", ["Forces a Stop-The-World Full GC before dumping", "Causes severe latency pauses in production", "Only dumps reachable, live objects"], ["It encrypts the heap dump causing CPU spikes"]),
    ("B5", "architecture", "hard", "architecture", ["JVM Performance"], "You are tuning a latency-critical trading engine. You notice the JVM occasionally pauses for 50ms due to 'RevokeBias' safepoint operations. What is Biased Locking, and how do you resolve this pause?", "Biased Locking is a JVM optimization where a lock is 'biased' toward the thread that first acquires it, making subsequent acquisitions by that same thread lock-free. However, if a different thread attempts to acquire that lock, the JVM must revoke the bias, which requires a global Safepoint (STW pause). In modern, highly concurrent applications (or Java 15+ where it's disabled by default), the overhead of revocation outweighs the benefits. You resolve it by passing `-XX:-UseBiasedLocking`.", ["Biased locking optimizes locks for single-thread access", "Revoking bias for a different thread requires a STW Safepoint", "Disable it using -XX:-UseBiasedLocking"], ["Biased locking prevents deadlocks"])
]

BUCKET_KEYS = {
    "B1": ("Garbage Collection", "GC Tuning", "JVM", ["Java Developer"]),
    "B2": ("JVM Performance", "JIT Compiler", "JVM", ["Java Developer"]),
    "B3": ("Reactive Programming", "Reactor", "Project Reactor", ["Java Developer"]),
    "B4": ("Java Concurrency", "Advanced Concurrency", "Java", ["Java Developer"]),
    "B5": ("JVM Diagnostics", "Production Profiling", "JVM", ["Java Developer"]),
}

def main():
    with open(OUT, encoding="utf-8") as f:
        prior = [json.loads(l) for l in f if l.strip()]
    
    staged_q = [p["question"] for p in prior]
    staged_a = [p["expected_answer"] for p in prior]
    
    # Adding legacy supabase text for overlap detection
    sup = existing_supabase()
    staged_q.extend([q for q, _ in sup])
    staged_a.extend([a for _, a in sup])

    cands = []
    for b, intent, diff, qt, sec, q, a, strong, weak in Q:
        skill, topic, tech, roles = BUCKET_KEYS[b]
        cands.append({
            "primary_role": ROLE,
            "applicable_roles": roles,
            "primary_skill": skill,
            "secondary_skills": sec,
            "technology": tech,
            "topic": topic,
            "category": "Software Engineering",
            "intent": intent,
            "difficulty": diff,
            "question_type": qt,
            "question": q,
            "expected_answer": a,
            "evaluation_rubric": {"strong_indicators": strong, "weak_indicators": weak}
        })

    corpus = staged_q + staged_a + [c["question"] for c in cands] + [c["expected_answer"] for c in cands]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit(corpus)
    SQ, SA = vec.transform(staged_q), vec.transform(staged_a)
    SC = vec.transform([x + " " + y for x, y in zip(staged_q, staged_a)])
    seen_norm = {normalize_text(q) for q in staged_q}

    rej = Counter()
    accepted = []
    details = []
    ans_flags = []
    
    for idx, c in enumerate(cands):
        nq = normalize_text(c["question"])
        reason = None
        if nq in seen_norm:
            reason = "exact_duplicate"
        else:
            qs = cosine_similarity(vec.transform([c["question"]]), SQ)[0]
            as_ = cosine_similarity(vec.transform([c["expected_answer"]]), SA)[0]
            comp = cosine_similarity(vec.transform([c["question"] + " " + c["expected_answer"]]), SC)[0]
            
            details.append((float(qs.max()), float(as_.max()), float(comp.max())))
            if as_.max() >= 0.5:
                ans_flags.append((c["question"][:70], round(float(as_.max()), 3)))
                
            if qs.max() >= 0.80:
                reason = "near_duplicate"
            elif comp.max() >= 0.60:
                reason = "semantic_competency_duplicate"
            elif as_.max() >= 0.70:
                reason = "expected_answer_overlap"
                
        if not reason and LEAK.search(c["question"] + " " + c["expected_answer"]):
            reason = "prompt_leakage"
        
        if reason:
            rej[reason] += 1
            print(f"Rejected Q{idx+1}: {reason}")
            continue
            
        seen_norm.add(nq)
        accepted.append(c)

    print(f"Attempted: {len(cands)}, Accepted: {len(accepted)}, Rejected: {sum(rej.values())}")
    
    if len(accepted) != 50:
        print(f"ERROR: Did not accept exactly 50 (got {len(accepted)}). Aborting write.")
        sys.exit(1)

    for c in accepted:
        c["id"] = "gen_" + str(uuid.uuid4())
        c["generation_batch"] = "batch_43_java_developer"

    with open(OUT, "a", encoding="utf-8") as f:
        for c in accepted:
            f.write(json.dumps(c) + "\n")
            
    final_staging_total = len(prior) + len(accepted)
    role_counts = Counter(p.get("primary_role") for p in prior)
    role_counts[ROLE] += len(accepted)
    
    diff_counts = Counter(c["difficulty"] for c in accepted)
    intent_counts = Counter(c["intent"] for c in accepted)
    skill_counts = Counter(c["primary_skill"] for c in accepted)
    tech_counts = Counter(c["technology"] for c in accepted)
    topic_counts = Counter(c["topic"] for c in accepted)
    openings = Counter(opening(c["question"], 3) for c in accepted)
    
    bq = [c["question"] for c in accepted]
    M = cosine_similarity(vec.transform(bq)) if bq else [[0]]
    intra = [(i, j, round(float(M[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if M[i][j] >= 0.6]
    intra_qa = cosine_similarity(vec.transform([c["expected_answer"] for c in accepted])) if bq else [[0]]
    intra_ans = [(i, j, round(float(intra_qa[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if intra_qa[i][j] >= 0.5]
    
    report = {
        "batch": "batch_43_java_developer",
        "records_attempted": len(cands),
        "records_accepted": len(accepted),
        "records_rejected": sum(rej.values()),
        "rejection_reasons": dict(rej),
        "max_similarity_scores": {
            "question": round(max((d[0] for d in details), default=0), 3),
            "answer": round(max((d[1] for d in details), default=0), 3),
            "combined": round(max((d[2] for d in details), default=0), 3)
        },
        "intra_batch_overlaps": len(intra),
        "intra_batch_answer_overlaps": len(intra_ans),
        "answer_flags_gt_50": len(ans_flags),
        "staging_metrics": {
            "previous_staging_total": len(prior),
            "final_staging_total": final_staging_total,
            "role_total": role_counts[ROLE],
            "remaining_to_500": max(0, 500 - role_counts[ROLE])
        },
        "distributions": {
            "difficulty": dict(diff_counts),
            "intent": dict(intent_counts),
            "primary_skill": dict(skill_counts),
            "technology": dict(tech_counts),
            "topic": dict(topic_counts),
            "opening_diversity": dict(openings.most_common(10))
        }
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_batch43_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_batch43_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Phase 4D - Batch 43 (Java Developer)\n\n")
        f.write(f"- **Attempted**: {len(cands)}\n")
        f.write(f"- **Accepted**: {len(accepted)}\n")
        f.write(f"- **Rejected**: {sum(rej.values())}\n")
        f.write(f"- **Rejections**: {dict(rej)}\n\n")
        f.write("### Staging Totals\n")
        f.write(f"- **Previous Staging Total**: {len(prior)}\n")
        f.write(f"- **Final Staging Total**: {final_staging_total}\n")
        f.write(f"- **Java Developer Role Total**: {role_counts[ROLE]}\n")
        f.write(f"- **Remaining to 500 Target**: {report['staging_metrics']['remaining_to_500']}\n\n")
        f.write("### Similarity\n")
        f.write(f"- **Max Question Sim**: {report['max_similarity_scores']['question']}\n")
        f.write(f"- **Max Answer Sim**: {report['max_similarity_scores']['answer']}\n")
        f.write(f"- **Max Combined Sim**: {report['max_similarity_scores']['combined']}\n")
        f.write(f"- **Intra-batch Overlaps**: {len(intra)}\n")
        f.write(f"- **Answer Overlaps (>0.5)**: {len(ans_flags)}\n\n")
        f.write("### Distributions\n")
        f.write(f"- **Difficulty**: {dict(diff_counts)}\n")
        f.write(f"- **Intent**: {dict(intent_counts)}\n")
        f.write(f"- **Primary Skill**: {dict(skill_counts)}\n")
        f.write(f"- **Technology**: {dict(tech_counts)}\n")
        f.write(f"- **Topic**: {dict(topic_counts)}\n\n")
        f.write("### Top Openings\n")
        for op, count in openings.most_common(8):
            f.write(f"- `{op}`: {count}\n")

    print(f"Successfully generated 50 Java Developer questions.")

if __name__ == "__main__":
    main()
