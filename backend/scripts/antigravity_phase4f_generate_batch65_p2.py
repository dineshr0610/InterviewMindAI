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
    # Advanced Concurrency & Synchronization
    ("B65_2_1", "concept", "hard", "concept", ["Concurrency", "Java Concurrency"],
     "How does java.util.concurrent.locks.StampedLock work in optimistic reading mode (tryOptimisticRead() and validate()), and why must it NEVER be used with thread interruption without interruptible acquire methods?",
     "StampedLock provides an optimistic read mode that does not acquire an actual lock. Calling tryOptimisticRead() returns an integer stamp representing the lock's version state. The thread reads fields without any locking overhead or memory contention. Afterwards, the thread calls validate(stamp). If no write lock was acquired in the interim, validate() returns true and the reads are consistent. If false, the thread falls back to a pessimistic read lock (readLock()). StampedLock must never be used with thread interruption when waiting for a lock because its internal wait queue implementation does not properly handle interrupts on uninterruptible acquire methods—interrupting a thread waiting on readLock() or writeLock() can put the CPU into a 100% spinning loop or corrupt internal queue state. Always use readLockInterruptibly() or writeLockInterruptibly() if thread interruption is possible.",
     ["Explains optimistic read via tryOptimisticRead() returning a version stamp", "Describes validate(stamp) check and fallback to pessimistic read lock", "Identifies CPU 100% spinning / hang bug when interrupting uninterruptible StampedLock acquire methods"],
     ["Claims StampedLock is reentrant like ReentrantLock"]),

    ("B65_2_2", "diagnose", "medium", "debugging", ["Concurrency", "Java Concurrency"],
     "In a lock-free stack implementation using AtomicReference, explain how the 'ABA Problem' occurs during a compare-and-set (CAS) operation, and how AtomicStampedReference prevents it.",
     "The ABA problem occurs in multi-threaded lock-free data structures when a thread reads value A from an AtomicReference, prepares to CAS it to C, but is preempted. While preempted, another thread changes the reference from A to B, and then changes it back from B to A (e.g., recycling an allocated node back into a free pool). When the original thread resumes, it executes compareAndSet(A, C). The CAS succeeds because the memory reference matches A, but the structural integrity or underlying state of the data structure has changed, leading to silent memory corruption. AtomicStampedReference solves this by pairing the object reference with an integer stamp (version counter). The CAS updates both reference and stamp atomically: compareAndSet(expectedRef, newRef, expectedStamp, newStamp). Even if the reference returns to A, the stamp has incremented, causing the CAS to correctly fail.",
     ["Defines ABA problem where reference returns to A while state/structure changes", "Explains node recycling or ABA race condition in lock-free stacks", "Explains how AtomicStampedReference pairs object reference with version stamp to invalidate stale CAS"],
     ["Confuses ABA problem with simple deadlock"]),

    ("B65_2_3", "scenario", "hard", "scenario", ["Concurrency", "Java Concurrency"],
     "You chain several asynchronous tasks using CompletableFuture. Under high traffic, a downstream service intermittently throws an unhandled RuntimeException. The root future never completes, causing caller HTTP requests to hang until client timeout. How does exception propagation work across CompletableFuture stages, and how do you guarantee recovery or terminal failure?",
     "In CompletableFuture, if any stage in a pipeline throws an uncaught exception, that stage and all downstream stages chained with standard transformations (like thenApply() or thenAccept()) skip execution and become exceptionally completed. However, if the caller relies on get(timeout) or if downstream merging stages (like allOf() or nested thenCompose()) do not register explicit error handlers, failure propagation can drop errors silently or fail to signal calling frameworks. To ensure resilience: 1) Always attach an exception handler such as exceptionally(ex -> fallbackValue) or handle((res, ex) -> ...) which executes regardless of whether previous stages succeeded or threw; 2) In Java 9+, attach orTimeout(timeout, TimeUnit) or completeOnTimeout(fallback, timeout, TimeUnit) to ensure the future terminates deterministically even if asynchronous worker threads stall.",
     ["Explains exceptional completion skipping intermediate transformation stages", "Demonstrates using .exceptionally() or .handle() to intercept and recover from exceptions", "Uses .orTimeout() or .completeOnTimeout() to prevent unbounded thread hangs"],
     ["Claims CompletableFuture automatically retries failed asynchronous stages"]),

    ("B65_2_4", "tradeoff", "medium", "tradeoff", ["Concurrency", "Java Concurrency"],
     "What are the architectural tradeoffs of using ForkJoinPool.commonPool() for blocking I/O tasks versus maintaining dedicated bounded ThreadPoolExecutor instances?",
     "ForkJoinPool.commonPool() is designed strictly for compute-intensive, CPU-bound tasks utilizing work-stealing algorithms, with parallelism defaults tied to Runtime.getRuntime().availableProcessors() - 1. If blocking I/O calls (database queries, network requests) are dispatched to the common pool without using ForkJoinPool.ManagedBlocker, worker threads block on I/O. Because the common pool is a JVM-wide singleton shared by parallel Streams, CompletableFutures, and internal framework utilities, starving its worker threads degrades the throughput of the entire application. Dedicated bounded ThreadPoolExecutor instances isolate I/O workloads, allow configuring independent thread limits, queues, and saturation rejection policies (e.g., CallerRunsPolicy), preventing I/O stalls from cascading into unrelated CPU-bound tasks.",
     ["Highlights commonPool() design for CPU-bound tasks with core count parallelism", "Identifies risk of starving JVM-wide singleton shared by parallel streams and CompletableFuture", "Recommends dedicated bounded thread pools with custom rejection policies for blocking I/O"],
     ["Recommends using parallel streams for all database I/O"]),

    ("B65_2_5", "concept", "easy", "concept", ["Concurrency", "Java Concurrency"],
     "What is the difference between ThreadPoolExecutor.AbortPolicy and ThreadPoolExecutor.CallerRunsPolicy when a bounded thread pool's task queue is saturated?",
     "When a ThreadPoolExecutor reaches its maximum pool size and its bounded work queue is completely full, it delegates subsequent task submissions to its RejectedExecutionHandler. AbortPolicy (the default) immediately throws a RejectedExecutionException, failing the submitted task instantly and notifying the caller. In contrast, CallerRunsPolicy does not throw an exception; instead, it executes the submitted task directly on the thread that called submit() or execute(). This effectively throttles the incoming submission rate (providing natural backpressure) because the producing thread is forced to do work rather than enqueueing more tasks, but it can temporarily block upstream request dispatchers.",
     ["Explains AbortPolicy throws RejectedExecutionException failing fast", "Explains CallerRunsPolicy executes task synchronously on the calling thread", "Identifies backpressure effect of CallerRunsPolicy slowing the task producer"],
     ["Claims CallerRunsPolicy drops tasks silently without notification"]),

    ("B65_2_6", "diagnose", "hard", "debugging", ["Concurrency", "Java Concurrency"],
     "A multithreaded financial matching engine experiences intermittent complete application freezes under peak load. Thread dumps show two worker threads in BLOCKED state waiting on each other's intrinsic monitor locks (synchronized). How do you analyze the thread dump to identify the cyclic lock dependency, and what engineering pattern prevents monitor deadlocks?",
     "In a thread dump (jstack), JVM deadlocks on synchronized monitors are automatically detected and printed at the bottom under 'Found one Java-level deadlock:'. To analyze it manually: identify Thread 1, note 'waiting to lock <0xABC>' which is held by Thread 2 ('locked <0xABC>'), and observe Thread 2 'waiting to lock <0xXYZ>' held by Thread 1 ('locked <0xXYZ>'). The cycle Thread 1 -> Lock A -> Thread 2 -> Lock B -> Thread 1 proves the deadlock. The primary engineering pattern to prevent deadlocks is 'Global Lock Ordering': enforce that all threads acquire multiple shared resources in a strictly identical global sequence (e.g., sorting account IDs before acquiring locks: Account first = from.id < to.id ? from : to; synchronized(first) { synchronized(second) { ... } }). Alternatively, replace intrinsic monitors with ReentrantLock.tryLock(timeout) to back off and retry rather than blocking indefinitely.",
     ["Identifies cyclic lock dependency in thread dump waiting/holding blocks", "Prescribes Global Lock Ordering (e.g., acquiring resources in sorted ID order)", "Suggests ReentrantLock.tryLock() with timeout backoff as an alternative"],
     ["Suggests increasing JVM heap size to resolve lock deadlocks"]),

    ("B65_2_7", "implement", "medium", "implement", ["Concurrency", "Java Concurrency"],
     "How do you implement a bounded, non-blocking rate limiter using AtomicLong and compare-and-swap (CAS) loops without introducing lock contention?",
     "You implement a Token Bucket or Leaky Bucket algorithm. Store the available token count and the last refill timestamp in atomic state. When a request arrives (tryAcquire(long tokens)), run a CAS loop: 1) Read current timestamp and current token balance; 2) Calculate newly generated tokens since the last refill timestamp; 3) Compute newBalance = Math.min(maxCapacity, currentTokens + generatedTokens); 4) If newBalance < tokens, return false (rate limited); 5) Otherwise, compute targetBalance = newBalance - tokens and execute atomicRef.compareAndSet(currentState, new State(targetBalance, now)). If the CAS succeeds, permit the request; if it fails due to concurrent modification by another thread, loop and re-read. This eliminates lock contention while guaranteeing atomicity.",
     ["Implements token bucket calculation inside a CAS loop", "Atomically checks capacity and deducts tokens using compareAndSet", "Handles retry loop on CAS contention without thread blocking"],
     ["Uses synchronized methods to implement the rate limiter"]),

    # Java Memory & Off-Heap
    ("B65_2_8", "tradeoff", "hard", "tradeoff", ["Memory Management", "Off-Heap Memory"],
     "What are the architectural tradeoffs of allocating off-heap memory using ByteBuffer.allocateDirect() versus on-heap memory with byte arrays in high-throughput network applications?",
     "ByteBuffer.allocateDirect() allocates memory outside the JVM garbage collected heap directly via the operating system (using malloc / POSIX posix_memalign). The primary advantage is 'Zero-Copy' network and file I/O: OS native kernel socket and disk system calls (write(), read(), sendfile()) can pass the off-heap pointer directly to network interface DMA controllers without the JVM first having to copy the memory to an intermediate native buffer. Furthermore, off-heap buffers do not generate GC pressure or GC pauses. The major tradeoffs are: 1) Allocation and deallocation of direct ByteBuffers are significantly slower and more expensive than on-heap array allocation; 2) Direct memory is not bound by standard -Xmx heap limits and is hard to track without Native Memory Tracking (NMT); 3) Reclaiming direct memory relies on Cleaner / PhantomReferences or manual Unsafe deallocation, which can cause native memory leaks if GC is not triggered.",
     ["Highlights zero-copy I/O bypassing intermediate JVM-to-OS buffer copying", "Notes total avoidance of GC pressure for massive off-heap caches", "Identifies expensive allocation overhead and reliance on Cleaner/PhantomReferences for deallocation"],
     ["Claims direct ByteBuffers are stored on the JVM thread stack"]),

    ("B65_2_9", "diagnose", "hard", "debugging", ["Memory Management", "JVM Internals"],
     "A containerized Java application has its heap set to -Xmx4g inside a container with a 6GB memory limit. Over 48 hours, heap usage stays at 2GB, but the Linux kernel OOM-kills the pod because memory exceeds 6GB. How do you use Native Memory Tracking (NMT) and 'jcmd' to diagnose whether direct buffers, thread stacks, or Metaspace are consuming the off-heap memory?",
     "To diagnose native memory growth: 1) Launch the JVM with -XX:NativeMemoryTracking=detail (or summary); 2) Establish an early baseline using 'jcmd <pid> VM.native_memory baseline'; 3) When memory grows, run 'jcmd <pid> VM.native_memory detail.diff'. The diff report breaks down committed native memory across categories: 'Thread' (number of threads * -Xss stack size), 'Metaspace' (class metadata), 'GC' (GC data structures such as card tables and marking bitmaps), 'Internal' (direct ByteBuffers allocated via Unsafe.allocateMemory()), and 'Symbol' (string tables). If 'Internal' is expanding, direct ByteBuffers are leaking; if 'Thread' is expanding, unmanaged thread creation is leaking stack memory; if 'Arena' or JNI allocations grow, native C/C++ libraries are leaking memory.",
     ["Configures -XX:NativeMemoryTracking and establishes baseline via jcmd", "Analyzes VM.native_memory detail.diff categories (Thread, Metaspace, GC, Internal)", "Correlates category growth with underlying causes (direct buffers, thread stacks, JNI leaks)"],
     ["Claims heap dumps in Eclipse MAT display full native OS memory allocations"]),

    ("B65_2_10", "concept", "easy", "concept", ["Memory Management", "JVM Internals"],
     "How does the -XX:MaxDirectMemorySize JVM flag control off-heap direct buffer allocation, and what happens when an application attempts to allocate past this limit using ByteBuffer.allocateDirect()?",
     "The -XX:MaxDirectMemorySize flag sets the maximum total native memory that can be reserved for direct ByteBuffers allocated via ByteBuffer.allocateDirect(). If this flag is omitted, the JVM defaults its value to the maximum heap size (-Xmx). When an allocation request exceeds the remaining direct memory capacity, HotSpot executes Bits.reserveMemory(), which attempts to trigger a synchronous garbage collection (System.gc()) to prompt Cleaner reference objects to free unreachable direct buffers. If after the GC there is still insufficient direct memory available, the JVM throws java.lang.OutOfMemoryError: Direct buffer memory.",
     ["Explains default alignment with -Xmx if flag is not specified", "Describes Bits.reserveMemory() triggering System.gc() to invoke Cleaners", "Identifies OutOfMemoryError: Direct buffer memory when limits are exhausted"],
     ["Claims direct memory can grow indefinitely until the OS crashes"]),

    ("B65_2_11", "tradeoff", "medium", "tradeoff", ["Memory Management", "JVM Internals"],
     "Why is setting a JVM heap size to exactly 32GB or 33GB considered an anti-pattern due to Compressed Ordinary Object Pointers (Compressed OOPs)?",
     "On 64-bit JVMs, pointers are 64 bits (8 bytes) wide, increasing memory consumption by ~40%. HotSpot utilizes Compressed OOPs (-XX:+UseCompressedOops) to represent 64-bit object references using 32-bit integers by shifting addresses right by 3 bits (taking advantage of 8-byte object alignment). This allows 32-bit pointers to address up to 32GB of heap space. If you configure -Xmx to 32GB or slightly above (e.g., 33GB), the JVM crosses the 32GB addressable limit and MUST disable Compressed OOPs, reverting to full 64-bit pointers. Consequently, all object references double in size from 4 bytes to 8 bytes, causing the application to consume more memory at 33GB than it did at 31GB while degrading CPU cache efficiency (L1/L2/L3 cache misses). A 31GB heap effectively provides more usable object storage than a 33GB heap.",
     ["Explains Compressed OOPs shifting addresses by 3 bits to address 32GB using 32-bit pointers", "Identifies threshold crossing disabling Compressed OOPs and doubling reference sizes", "Explains why a 31GB heap has more usable capacity and better CPU cache locality than 33GB"],
     ["Claims Compressed OOPs are only used in 32-bit operating systems"]),

    ("B65_2_12", "implement", "medium", "implement", ["Memory Management", "Off-Heap Memory"],
     "How do you map a large 10GB file into off-heap virtual memory using FileChannel.map() (Memory-Mapped Files / MappedByteBuffer) in Java, and what are the precautions regarding unmapping the buffer?",
     "You open a FileChannel from a RandomAccessFile or FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE) and invoke channel.map(FileChannel.MapMode.READ_WRITE, 0, fileSize). This returns a MappedByteBuffer mapped directly to OS virtual memory pages without loading the entire file into heap RAM. The operating system page cache transparently pages blocks in and out of disk. Precaution: Java historically does not provide an explicit public unmap() method on MappedByteBuffer. The memory mapping remains locked by the OS until the MappedByteBuffer is garbage collected and its internal Cleaner runs. On Windows, this holds an open file lock preventing deletion. In Java 21+ via the Foreign Function & Memory API, you should use Arena.ofConfined() and FileChannel.map(..., arena) to guarantee deterministic, immediate unmapping upon closing the arena.",
     ["Demonstrates FileChannel.map() with MapMode and byte range", "Explains OS page cache virtual memory paging avoiding heap RAM exhaustion", "Highlights file lock issue on unmapping and modern resolution via Foreign Function & Memory Arena"],
     ["Claims MappedByteBuffer loads the entire 10GB file into the Java heap immediately"]),

    ("B65_2_13", "scenario", "hard", "scenario", ["Memory Management", "Containerized JVM"],
     "A Java 17 Spring Boot microservice running in a Docker container with a 2GB memory limit frequently gets terminated by Linux OOM killer with Exit Code 137, even though -XX:MaxRAMPercentage=75.0 is configured. Profiling shows heap never exceeds 1.5GB. What other JVM memory areas constitute the container footprint and how do you prevent the kill?",
     "Linux cgroups enforce memory limits on the entire operating system process (Resident Set Size). Setting MaxRAMPercentage=75.0 limits on-heap memory to 1.5GB, leaving only 512MB for ALL off-heap JVM components. The total container footprint consists of: Heap (1.5GB) + Metaspace (150-300MB) + Thread Stacks (e.g., 300 threads * 1MB -Xss = 300MB) + Direct ByteBuffers + GC data structures (card tables, marking queues: 50-150MB) + Code Cache (64-240MB) + JNI native memory. Total committed native memory easily exceeds 2.2GB, triggering cgroup OOM kill (exit 137). Prevention: 1) Reduce MaxRAMPercentage to 50-60% (1.0-1.2GB heap); 2) Limit thread stack size using -Xss512k and cap thread pool sizes; 3) Set -XX:MaxMetaspaceSize=256m and -XX:ReservedCodeCacheSize=128m; 4) Cap direct memory with -XX:MaxDirectMemorySize=256m.",
     ["Breaks down total RSS: Heap + Metaspace + Thread Stacks + Code Cache + GC structures + Direct Memory", "Identifies 75% heap leaving insufficient headroom for native JVM overhead in 2GB container", "Provides concrete tuning: lower MaxRAMPercentage, reduce -Xss, and bound Metaspace/CodeCache"],
     ["Recommends disabling the Linux OOM killer inside Docker containers"]),

    ("B65_2_14", "concept", "medium", "concept", ["Concurrency", "Java Concurrency"],
     "How does java.util.concurrent.ForkJoinPool implement the 'Work-Stealing' algorithm, and why are tasks stored in double-ended queues (deques)?",
     "In ForkJoinPool, each worker thread maintains its own private double-ended queue (deque) of tasks. When a worker thread generates subtasks (via fork()), it pushes them onto the HEAD of its own deque and pops tasks from the HEAD to execute them (LIFO order). This exploits CPU cache locality, as recent subtasks operate on warm data. When a worker thread runs out of tasks, it becomes a 'thief': it accesses the TAIL of another randomly selected worker thread's deque to steal a task (FIFO order). Accessing the tail minimizes synchronization contention with the queue owner operating at the head, and stealing the oldest tasks yields larger chunks of work (higher in the fork-join recursion tree), reducing subsequent stealing attempts.",
     ["Explains private deques per worker thread", "Describes LIFO push/pop at HEAD by the owner thread for cache locality", "Describes FIFO stealing at TAIL by idle worker threads to minimize contention"],
     ["Claims worker threads wait on a single shared synchronized queue"]),

    ("B65_2_15", "diagnose", "medium", "debugging", ["Concurrency", "Java Concurrency"],
     "You notice thread pool performance degrades under high concurrency when using java.util.concurrent.ArrayBlockingQueue, whereas switching to LinkedTransferQueue or ConcurrentLinkedQueue dramatically improves throughput. Why does ArrayBlockingQueue suffer from lock contention?",
     "ArrayBlockingQueue uses a single ReentrantLock for both enqueueing (put/offer) and dequeueing (take/poll) operations. Producers adding tasks and consumers taking tasks contend for the exact same lock monitor, creating a major concurrency bottleneck on multi-core systems. In contrast, LinkedBlockingQueue uses two separate locks (putLock and takeLock), allowing producers and consumers to operate concurrently. LinkedTransferQueue and ConcurrentLinkedQueue are lock-free algorithms based on non-blocking compare-and-swap (CAS) operations with dual queues, completely eliminating thread parking and lock serialization under high producer-consumer concurrency.",
     ["Explains single ReentrantLock bottleneck in ArrayBlockingQueue shared by producers and consumers", "Contrasts with two-lock design in LinkedBlockingQueue", "Explains lock-free CAS algorithm in LinkedTransferQueue eliminating thread parking"],
     ["Claims ArrayBlockingQueue is slow because it uses disk storage"]),

    ("B65_2_16", "scenario", "hard", "scenario", ["Concurrency", "Java Concurrency"],
     "A Java batch processing job splits millions of records across a custom ForkJoinPool. When some tasks perform synchronous HTTP calls to an external validation API, all worker threads become blocked, and unrelated compute tasks in the pool completely freeze. How does ForkJoinPool.ManagedBlocker prevent starvation during blocking operations?",
     "ForkJoinPool is designed with a fixed target parallelism level. When a worker thread blocks on synchronous I/O or a lock without notification, the pool's effective parallelism drops. If all workers block, the pool starves. ForkJoinPool.ManagedBlocker is an interface that informs the pool of potentially blocking operations. When a task wraps its blocking call inside ForkJoinPool.managedBlock(new ManagedBlocker() { ... }), the pool detects the block and proactively spawns a temporary spare worker thread to maintain the configured parallelism level while the current thread waits. Once the blocking operation completes and the thread resumes, the spare thread is eventually terminated or returned to the pool, guaranteeing that other compute tasks continue progressing.",
     ["Identifies drop in pool parallelism when worker threads block on external I/O", "Explains ForkJoinPool.ManagedBlocker interface signaling potential blockages", "Describes pool dynamically spawning spare compensation threads to maintain parallelism"],
     ["Suggests increasing the JVM priority of blocked threads"]),

    ("B65_2_17", "tradeoff", "easy", "tradeoff", ["Concurrency", "Java Concurrency"],
     "What is the tradeoff between java.util.concurrent.atomic.LongAdder and java.util.concurrent.atomic.AtomicLong when designing a high-throughput metrics counter?",
     "AtomicLong uses a single volatile variable updated via a compare-and-swap (CAS) loop. Under heavy multi-threaded write contention (dozens of threads incrementing simultaneously), all threads contend on the same cache line and memory address; CAS operations repeatedly fail and spin, causing high CPU burn and cache-coherence bus traffic. LongAdder maintains a dynamic array of cell variables (Cell[]), distributing updates across cells based on thread hash codes. Under contention, threads update independent cells without contention. The tradeoff is: 1) Higher memory footprint for LongAdder; 2) Reading the sum (sum()) requires aggregating across all cells and is not an atomic point-in-time snapshot, making it ideal for throughput metrics (e.g., request counters) but unsuitable where strict atomic read-and-update coordination is required.",
     ["Explains CAS contention and cache line bouncing in AtomicLong under high write load", "Explains striped Cell[] array distribution in LongAdder eliminating contention", "Notes trade-off: higher memory footprint and eventual consistency on sum() reads"],
     ["Claims AtomicLong is faster than LongAdder in multi-threaded benchmarks"]),

    ("B65_2_18", "implement", "hard", "implement", ["Memory Management", "Off-Heap Memory"],
     "How do you safely allocate, access, and free off-heap native memory using the Foreign Function & Memory API (Arena, MemorySegment, ValueLayout) introduced in Java 22 / Project Panama?",
     "The Foreign Function & Memory API replaces unsafe hacks (sun.misc.Unsafe) with safe, typed, off-heap abstractions. You use an Arena to govern memory lifecycle: try (Arena arena = Arena.ofConfined()) { MemorySegment segment = arena.allocate(1024, 8); segment.set(ValueLayout.JAVA_LONG, 0, 123456789L); long val = segment.get(ValueLayout.JAVA_LONG, 0); }. When the try-with-resources block exits, arena.close() deterministically deallocates the off-heap native memory immediately without waiting for GC. If any code attempts to access segment after closure, the JVM throws IllegalStateException, guaranteeing spatial safety (bounds checking) and temporal safety (prevention of use-after-free bugs).",
     ["Demonstrates Arena.ofConfined() with try-with-resources lifecycle management", "Uses MemorySegment and ValueLayout for typed off-heap reads and writes", "Highlights spatial safety (bounds checks) and temporal safety (preventing use-after-free)"],
     ["Uses sun.misc.Unsafe allocateMemory without bounds checking"]),

    ("B65_2_19", "concept", "easy", "concept", ["Concurrency", "Java Concurrency"],
     "What is 'Thread Starvation' in Java, and how does configuring fairness (new ReentrantLock(true)) mitigate starvation at the cost of throughput?",
     "Thread starvation occurs when a thread is perpetually denied CPU execution time or access to a shared resource because other higher-priority or greedy threads continuously acquire the resource first. In standard non-fair ReentrantLock (and synchronized monitors), lock acquisition is non-fair: when a lock is released, newly arriving threads can bargingly acquire the lock immediately without checking the wait queue, which maximizes throughput by avoiding thread parking/unparking context switches, but risks starving queued threads. Setting fairness to true (new ReentrantLock(true)) forces the lock to strictly honor arrival order via an internal FIFO queue (AQS). Any arriving thread must join the tail of the queue, preventing starvation but significantly reducing throughput due to frequent thread context switches.",
     ["Defines thread starvation as perpetual denial of lock/resource access", "Explains barging in non-fair locks boosting throughput but risking starvation", "Explains FIFO queuing in fair locks preventing starvation at the cost of thread context switch overhead"],
     ["Claims fair locks completely eliminate thread context switches"]),

    ("B65_2_20", "diagnose", "medium", "debugging", ["Concurrency", "Java Concurrency"],
     "You observe that calling Thread.interrupt() on a worker thread blocked on a socket read using standard java.io.InputStream fails to cancel the thread. Why does InputStream.read() ignore interrupts, and how do you achieve interruptible I/O in Java?",
     "Traditional java.io stream blocking operations (like InputStream.read() and OutputStream.write()) block directly on native OS system calls without checking the Java thread interruption status flag. Calling Thread.interrupt() sets the interrupt status flag, but the OS read call remains blocked indefinitely until data arrives or the socket closes. To achieve interruptible I/O: 1) Use Java NIO Channels (java.nio.channels.SocketChannel), which implement InterruptibleChannel. If a thread is blocked on a SocketChannel.read(), invoking Thread.interrupt() causes the channel to close and throws java.nio.channels.ClosedByInterruptException; 2) Alternatively, close the underlying socket asynchronously (socket.close()), which forces the blocked InputStream.read() to throw a SocketException.",
     ["Explains that traditional java.io blocks on native OS system calls without checking interrupt flags", "Recommends Java NIO SocketChannel implementing InterruptibleChannel", "Explains ClosedByInterruptException or asynchronous socket.close() unblocking the thread"],
     ["Claims Thread.interrupt() kills the operating system process immediately"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 2).")
    
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
    print("POST-BATCH AUDIT PART 2")
    print("========================================")
    print(f"Batch: 65 Part 2")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
