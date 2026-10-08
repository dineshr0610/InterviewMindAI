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
    # JVM Garbage Collection & Internals
    ("B65_1_1", "diagnose", "hard", "debugging", ["Garbage Collection", "JVM Internals"],
     "In a high-throughput Java application running on G1 GC, you observe periodic multi-second stop-the-world pauses marked as 'to-space exhausted' or 'evacuation failure' in GC logs. What is the root cause of evacuation failure in G1, and how do you tune the JVM to mitigate it?",
     "Evacuation failure occurs when G1 GC attempts to evacuate alive objects from young or survivor regions into new survivor or old regions during a collection cycle, but there are no free regions left in the heap to receive them. This forces G1 to fall back to an expensive single-threaded or unoptimized Full GC. Root causes include sudden allocation spikes, undersized old generation, or delayed initiation of the concurrent marking cycle. Remediation includes decreasing -XX:InitiatingHeapOccupancyPercent (IHOP) to trigger concurrent marking earlier, increasing -XX:G1ReservePercent (default 10%) to maintain a larger reserve buffer for evacuations, increasing total heap size (-Xmx), and reducing allocation rate of short-lived objects.",
     ["Identifies lack of free regions during object evacuation as root cause", "Explains fallback to expensive Full GC", "Recommends tuning -XX:InitiatingHeapOccupancyPercent and -XX:G1ReservePercent"],
     ["Claims G1 does not support stop-the-world pauses"]),

    ("B65_1_2", "concept", "medium", "concept", ["Garbage Collection", "JVM Internals"],
     "What are 'Humongous Allocations' in the G1 Garbage Collector, why do they bypass standard Eden allocation, and what performance degradation do they cause?",
     "In G1 GC, any object whose size exceeds 50% of the G1 region size (-XX:G1RegionSize, typically 1MB to 32MB) is classified as a Humongous Object. Instead of being allocated in Eden and progressing through Survivor spaces, humongous objects are allocated directly into contiguous sequences of Old Generation regions. Because they require contiguous physical blocks of regions, frequent humongous allocations cause severe heap fragmentation, premature triggering of concurrent marking cycles, high pause times, and rapid exhaustion of old generation space even when total free heap appears plentiful. Solutions include increasing the G1 region size using -XX:G1RegionSize=16m or 32m so objects fit into normal regions, or refactoring the code to stream or chunk large arrays and byte buffers.",
     ["Defines humongous objects as exceeding 50% of G1 region size", "Explains direct allocation into contiguous Old Generation regions", "Notes heap fragmentation and premature concurrent marking cycles", "Suggests tuning -XX:G1RegionSize or streaming payloads"],
     ["Confuses humongous allocations with standard memory leaks"]),

    ("B65_1_3", "tradeoff", "hard", "tradeoff", ["Garbage Collection", "JVM Internals"],
     "What are the fundamental architectural differences and tradeoffs between the Z Garbage Collector (ZGC) and the G1 Garbage Collector regarding pause times, CPU throughput, and memory overhead?",
     "ZGC is a concurrent, low-latency garbage collector where almost all GC phases—marking, relocation (evacuation), and reference processing—occur concurrently with application threads, keeping STW pauses sub-millisecond (<1ms) regardless of heap size (from MBs to TBs). ZGC achieves this using load barriers and colored pointers (or reference metadata in generational ZGC). The tradeoff is lower maximum CPU throughput (typically 5-15% throughput penalty compared to G1) because load barriers introduce instructions on every object reference read, and concurrent GC threads compete with application threads for CPU cores. In contrast, G1 optimizes for balanced throughput and bounded pause times (default target 200ms) with higher overall compute efficiency, but exhibits higher tail latency and occasional stop-the-world spikes under severe allocation pressure.",
     ["Distinguishes concurrent evacuation via load barriers and colored pointers in ZGC", "Highlights sub-millisecond pause times in ZGC across multi-terabyte heaps", "Analyzes throughput penalty from load barriers and concurrent thread competition", "Contrasts with G1 throughput efficiency and bounded pause target"],
     ["Claims ZGC requires pausing all application threads during compaction"]),

    ("B65_1_4", "diagnose", "medium", "debugging", ["JVM Internals", "Memory Management"],
     "A Java service crashes with 'java.lang.OutOfMemoryError: Metaspace'. What is Metaspace, what typically causes Metaspace exhaustion in modern Java applications, and how do you diagnose it?",
     "Metaspace is an off-heap native memory area introduced in Java 8 (replacing PermGen) that stores class metadata, runtime constant pools, method bytecode, and annotations. Metaspace exhaustion is almost never caused by standard application code classes; rather, it is caused by dynamic class generation without proper classloader unloading. Common culprits include reflection inflation, CGLIB/ByteBuddy proxies generated repeatedly in libraries (e.g., poorly configured Spring, Hibernate, or scripting engines like Groovy), or ClassLoader leaks in dynamic plugin/web application reloads where references to custom ClassLoaders prevent class metadata from being garbage collected. Diagnosis involves capturing a heap dump and using tools like Eclipse MAT or 'jcmd <pid> VM.classloader_stats' and 'VM.metaspace' to identify which ClassLoader is holding millions of generated classes.",
     ["Explains Metaspace as native memory for class metadata and constant pools", "Identifies dynamic proxy generation, reflection inflation, or ClassLoader leaks as culprits", "Specifies diagnostics using jcmd VM.classloader_stats or heap dump analysis in MAT"],
     ["Assumes Metaspace is located inside the standard JVM young generation heap"]),

    ("B65_1_5", "implement", "medium", "implement", ["JVM Diagnostics", "Garbage Collection"],
     "How do you configure modern unified JVM GC logging (-Xlog:gc*) to diagnose pause-time spikes in production without incurring noticeable I/O performance overhead?",
     "In Java 9+, GC logging is configured via unified JVM logging. For production diagnostics with minimal overhead, configure: -Xlog:gc*,gc+phases=debug,gc+safepoint=info:file=/var/log/jvm/gc.log:time,uptime,pid:filecount=10,filesize=100m. Key aspects: 1) Using file rotation (filecount=10,filesize=100m) prevents unbounded disk usage; 2) Including decorators time,uptime,pid correlates GC pauses with application metrics and system APM traces; 3) Logging to a fast local filesystem (avoiding NFS or synchronous remote volumes) ensures file write operations do not block the JVM during GC safepoints; 4) Capturing gc+phases=debug reveals sub-millisecond breakdowns of GC sub-tasks such as root scanning, evacuation, and string deduplication.",
     ["Provides valid unified logging syntax with rotation (-Xlog:gc*:file=...:time,uptime,pid:filecount=...,filesize=...)", "Explains avoiding remote/NFS disk to prevent I/O blocking during safepoint writes", "Mentions capturing gc+phases or safepoint details for latency correlation"],
     ["Recommends deprecated Java 8 flags like -XX:+PrintGCDetails"]),

    ("B65_1_6", "scenario", "hard", "scenario", ["Garbage Collection", "Performance Tuning"],
     "In a high-throughput Java microservice, you observe that Young Generation GC pauses are lasting 350ms instead of the configured target of 50ms, yet total heap utilization is only 40%. Profiling reveals that the vast majority of pause time is spent in 'Object Copy' and 'Root Scanning'. What is occurring and how do you resolve it?",
     "Long Young GC pause times dominated by 'Object Copy' indicate that a large volume of objects created in Eden are surviving Young GC cycles rather than dying quickly (violating the Weak Generational Hypothesis). These surviving objects must be copied between Survivor regions or promoted to Old Gen, which is a memory-bandwidth-heavy, CPU-intensive stop-the-world task. Root Scanning pauses increase when there are massive thread stacks, huge JNI global references, or deep string table references. To resolve this: 1) Profile object lifetimes using JFR or async-profiler (-e alloc) to identify mid-lived objects (e.g., bloated in-memory caches, oversized request buffers) and refactor them to be either truly short-lived or permanently cached; 2) Tune survivor space sizing and MaxTenuringThreshold (-XX:MaxTenuringThreshold) or increase young generation size if objects are dying just after surviving one collection; 3) Reduce thread stack depths or thread counts to reduce root scanning overhead.",
     ["Identifies violation of Weak Generational Hypothesis where objects survive Eden", "Explains that copying surviving objects consumes high CPU and memory bandwidth during pauses", "Analyzes root scanning overhead from thread stacks or native references", "Proposes profiling mid-lived allocations and tuning tenuring thresholds or Eden capacity"],
     ["Suggests increasing GC threads without analyzing object survival rates"]),

    ("B65_1_7", "concept", "easy", "concept", ["Garbage Collection", "JVM Internals"],
     "What is the purpose of the 'Survivor Spaces' (S0 and S1) in the JVM Generational Garbage Collection model, and how does the tenuring threshold determine object promotion?",
     "Generational garbage collectors divide the Young Generation into Eden and two Survivor spaces (FromSpace/S0 and ToSpace/S1). When Eden fills, active objects that survive minor GC are copied to the empty survivor space, rather than immediately promoted to Old Generation. Each time an object survives a young collection cycle within a survivor space, its age counter is incremented by 1. Once an object's age exceeds the 'tenuring threshold' (configured via -XX:MaxTenuringThreshold, or determined dynamically via adaptive sizing to keep survivor spaces below -XX:TargetSurvivorRatio), it is promoted to the Old Generation. This buffering mechanism prevents transient, medium-lived objects from polluting the Old Generation, keeping Old Gen collections rare.",
     ["Explains alternating FromSpace/ToSpace roles between S0 and S1", "Explains age incrementing on each surviving collection cycle", "Describes promotion to Old Gen when surpassing tenuring threshold or survivor ratio"],
     ["Claims both S0 and S1 are written to simultaneously during application execution"]),

    # JVM Performance & Profiling
    ("B65_1_8", "diagnose", "hard", "debugging", ["JVM Performance", "Profiling"],
     "What is 'Safepoint Bias' in JVM profiling tools, why do sampling profilers that rely on GetCallTrace or standard thread dumps yield inaccurate CPU hotspots, and how does 'async-profiler' overcome this limitation?",
     "The JVM can only capture thread stack traces at 'safepoints'—points in execution where code is in a known, consistent state (e.g., method entries, loop branches in non-counted loops, allocation points). Profilers relying on JVM safepoints (like standard JMX sampling or jstack) suffer from 'Safepoint Bias': threads running intensive JIT-compiled counted loops or primitive operations do not yield to safepoints immediately, causing the profiler to attribute disproportionate CPU samples to whatever instruction eventually reaches a safepoint. async-profiler avoids this bias entirely by leveraging Linux OS perf events (hardware performance counters) or timer signals (SIGPROF) and reading JVM stacks asynchronously via the HotSpot AsyncGetCallTrace API. It interrupts threads at true timer intervals anywhere in execution, producing accurate, unbiased CPU flame graphs.",
     ["Explains safepoints as synchronization points required for thread inspection", "Defines safepoint bias where non-safepoint-yielding code is omitted or misattributed", "Explains how async-profiler uses OS signals (SIGPROF) and AsyncGetCallTrace to sample without safepoints"],
     ["Claims thread dumps provide mathematically exact CPU execution percentages"]),

    ("B65_1_9", "concept", "medium", "concept", ["JVM Internals", "JIT Compiler"],
     "Explain the mechanism of 'Tiered Compilation' in the HotSpot JVM. What are the roles of the C1 (Client) compiler and C2 (Server) compiler during application warmup?",
     "Tiered Compilation (-XX:+TieredCompilation, enabled by default since Java 8) balances fast JVM startup time with peak runtime optimization throughput across 5 execution tiers (Tier 0 to Tier 4). Tier 0 is the Interpreter, which starts executing bytecode immediately while collecting profiling statistics (Method Data Objects / MDOs). When invocation and backedge counters hit thresholds, code transitions to Tier 1-3: the C1 compiler compiles methods with various levels of profiling instrumentation quickly with minimal compilation delay. As methods become heavily used ('hot'), Tier 3 profile data informs Tier 4: the C2 (Server) compiler performs aggressive, global optimizations (aggressive inlining, loop unrolling, escape analysis, vectorization). This tiered approach eliminates the historic tradeoff between slow server warmup and poor client performance.",
     ["Describes execution tiers from Interpreter (Tier 0) through C1 (Tiers 1-3) to C2 (Tier 4)", "Explains profiling instrumentation and Method Data Objects (MDOs)", "Explains how C2 performs deep speculative optimizations for hot methods"],
     ["Asserts that C1 and C2 compile the exact same bytecode identically"]),

    ("B65_1_10", "implement", "hard", "implement", ["JVM Diagnostics", "Profiling"],
     "How do you configure and trigger a Java Flight Recorder (JFR) continuous low-overhead recording in a production Kubernetes pod, and extract it via 'jcmd' when an anomalous latency spike is detected?",
     "To maintain continuous low-overhead production profiling, launch the JVM with default continuous JFR recording enabled: -XX:StartFlightRecording=disk=true,dumponexit=true,maxsize=500m,maxage=1h,settings=profile.jfc,name=continuous-rec. This writes JFR events into an in-memory/disk circular buffer with <1-2% CPU overhead. When an APM or health check detects an anomalous latency spike or thread spike, an operator or automated sidecar triggers an on-demand dump of the buffered recording using jcmd: 'jcmd <PID> JFR.dump name=continuous-rec filename=/tmp/incident_dump.jfr path-to-gc-roots=true'. The resulting .jfr file contains execution samples, memory allocations, thread locks, GC phases, and OS metrics for the preceding hour up to the exact moment of the incident.",
     ["Configures continuous circular buffer recording with maxsize and maxage flags", "Emphasizes negligible production overhead (<1-2%) using profile.jfc or default.jfc", "Demonstrates extracting the recording via 'jcmd <PID> JFR.dump' upon incident detection"],
     ["Claims JFR requires stopping the JVM to extract event logs"]),

    ("B65_1_11", "tradeoff", "medium", "tradeoff", ["JVM Internals", "JIT Compiler"],
     "What is 'Escape Analysis' in HotSpot JIT compilation, what is 'Scalar Replacement', and what architectural code patterns can inadvertently break escape analysis?",
     "Escape Analysis is a C2 compiler optimization that determines whether the scope of an allocated object escapes the executing method or thread. If an object does not escape, the JIT compiler can perform 'Scalar Replacement'—breaking the object down into its constituent primitive fields and keeping them directly in CPU registers or on the stack frame, completely eliminating heap allocation and GC pressure. It can also eliminate synchronization (Lock Elision). Escape analysis breaks when: 1) The object is stored into a field of an instance or static variable; 2) The object is passed as an argument to a method that cannot be inlined (due to excessive bytecode size, deep call depth, or megamorphic call sites); 3) The object is returned from the method.",
     ["Defines escape analysis as determining object reachability beyond method/thread scope", "Defines scalar replacement as mapping object fields to registers/stack, bypassing heap allocation", "Identifies breaking patterns: storing in fields, escaping returns, and non-inlined method calls"],
     ["Claims scalar replacement moves objects to the old generation heap"]),

    ("B65_1_12", "scenario", "hard", "scenario", ["JVM Performance", "Profiling"],
     "An e-commerce service experiences severe 2-second response latency pauses every 10 minutes. Thread dumps and GC logs show NO major garbage collection pauses. However, JFR reveals massive durations under 'jdk.SafepointBegin' and 'jdk.SafepointWaitBlocked'. What is causing these safepoint delays, and how do you diagnose the offending thread?",
     "When the JVM initiates a safepoint (for biased lock revocation, class redefinition, or GC phase initiation), it signals all application threads to halt at their nearest safepoint. The safepoint cannot execute until EVERY single thread has reached a safepoint. If one thread is executing an uncounted loop (or in older JVMs, a long-running counted loop with integer variables where safepoint polling was eliminated by JIT loop optimizations), or is executing slow JNI code, that thread blocks the entire JVM from reaching the safepoint (SafepointWaitBlocked). To diagnose: enable -Xlog:safepoint=info,safepoint+stats=debug. In JFR, inspect the ExecutionSample events during the SafepointBegin window to identify which thread ID failed to park, and add -XX:+UseCountedLoopSafepoints to ensure JIT inserts safepoint checks into loops.",
     ["Explains that all threads must reach a safepoint before safepoint operations can proceed", "Identifies long-running uncounted/optimized loops or JNI calls delaying safepoint arrival", "Prescribes enabling unified safepoint logging (-Xlog:safepoint=info) and -XX:+UseCountedLoopSafepoints"],
     ["Attributes safepoint delays to network database socket timeouts"]),

    ("B65_1_13", "concept", "easy", "concept", ["JVM Internals", "JIT Compiler"],
     "What is JIT 'Deoptimization' (or Uncommon Trap) in Java, and why does it occur when an application's workload characteristics change?",
     "HotSpot JIT C2 makes speculative optimizations based on runtime profiling data (e.g., assuming a class hierarchy is monomorphic, assuming an if-condition is always true, or assuming an interface has only one implementing class). An 'Uncommon Trap' is a fallback mechanism inserted into the compiled native code. If the application's runtime behavior changes (e.g., a new class is loaded introducing a second implementation of an interface, or a null value is passed for the first time), the speculative assumption is invalidated. The JVM triggers 'Deoptimization': it pauses execution, converts the compiled native CPU frame back into interpreted bytecode stack frames, discards the invalidated compiled code, and resumes execution in the Interpreter while gathering new profile data.",
     ["Explains speculative optimization based on monomorphic calls or branch profiling", "Defines uncommon traps as guard checks validating speculative assumptions", "Explains deoptimization process: unwinding native frames to interpreted frames"],
     ["Claims deoptimization crashes the JVM with a fatal error"]),

    ("B65_1_14", "diagnose", "medium", "debugging", ["JVM Performance", "Profiling"],
     "How do you use 'async-profiler' in allocation mode (-e alloc) to diagnose memory allocation pressure, and why is allocation profiling often superior to analyzing heap dumps for GC tuning?",
     "Heap dumps show a static snapshot of what objects are currently alive in memory, which is useful for memory leaks. However, high GC pause frequency and CPU burn are often caused by 'allocation churn'—terabytes of short-lived objects created and discarded per minute that never survive long enough to appear in a heap dump. Running 'async-profiler -e alloc -d 30 -f alloc_flamegraph.html <PID>' intercepts TLAB (Thread-Local Allocation Buffer) allocations and direct outside-TLAB allocations. The resulting flame graph shows the exact call stacks and method lines responsible for the highest rates of object allocation per second, allowing engineers to pinpoint unnecessary object instantiation (e.g., redundant String concatenation, boxing, or stream pipelines) directly at the allocation source.",
     ["Distinguishes allocation churn (rate of creation) from retained heap (static memory leak)", "Explains sampling TLAB allocations and outside-TLAB allocations", "Highlights using allocation flame graphs to identify hotspot allocation call stacks"],
     ["Asserts that heap dumps and allocation profilers provide identical information"]),

    ("B65_1_15", "tradeoff", "hard", "tradeoff", ["Garbage Collection", "JVM Internals"],
     "In low-latency systems, what are the architectural tradeoffs of choosing the Shenandoah Garbage Collector versus Generational ZGC in OpenJDK 21?",
     "Shenandoah and ZGC both aim for sub-millisecond stop-the-world pauses by performing concurrent evacuation. Shenandoah historically used Brooks pointers and now uses load-reference barriers on object access. Generational ZGC (introduced in Java 21) separates young and old generations concurrently using colored pointers with load barriers. Generational ZGC handles high allocation rates significantly better than single-generation collectors like original Shenandoah or non-generational ZGC because it collects short-lived young objects frequently with minimal work, drastically reducing allocation stalls. However, Generational ZGC requires newer kernels (supports virtual memory remapping) and can have slightly higher RSS native memory consumption. Shenandoah provides a battle-tested low-latency alternative especially on diverse Linux distributions, but can suffer from allocation pacing/stalls if the young allocation rate outpaces its concurrent collection cycle.",
     ["Compares concurrent evacuation techniques (load-reference barriers vs colored pointers)", "Explains generational advantage in Generational ZGC for handling high allocation churn without stalls", "Evaluates operational requirements (kernel virtual memory support and RSS overhead)"],
     ["Claims Shenandoah does not support concurrent compaction"]),

    ("B65_1_16", "scenario", "medium", "scenario", ["JVM Performance", "Profiling"],
     "After deploying a new release of a Java service to production, CPU utilization spikes to 100% for the first 3 minutes of traffic, causing initial health check timeouts, before stabilizing at 15% CPU. What is causing this warmup penalty and how can it be mitigated?",
     "This is caused by JVM warmup effects: cold class loading, interpreter execution, and simultaneous heavy JIT compilation (both C1 and C2 compilation queues are saturated with thousands of hot methods). While methods are interpreted and JIT compilers consume multiple CPU cores, request latency increases dramatically. Mitigation strategies include: 1) Implementing Kubernetes readiness probes with initial delay and slow warmup traffic ramping (e.g., Envoy or Istio traffic warming); 2) Using Class Data Sharing (CDS / AppCDS) to eliminate class loading and verification overhead; 3) Using OpenJDK CRaC (Coordinated Restore at Checkpoint) or GraalVM Native Image to bypass JIT compilation entirely; 4) Warmup scripts executing simulated production queries during pod startup before signaling readiness.",
     ["Attributes CPU spike to simultaneous bytecode interpretation, profiling, and C1/C2 JIT compilation queues", "Suggests traffic ramp-up / slow start via ingress controllers", "Proposes CDS (Class Data Sharing), CRaC, or AOT compilation to accelerate warmup"],
     ["Recommends disabling JIT compilation permanently in production"]),

    ("B65_1_17", "concept", "easy", "concept", ["JVM Diagnostics", "JVM Internals"],
     "What is a Thread-Local Allocation Buffer (TLAB) in the JVM, and why is it essential for multi-threaded allocation throughput?",
     "In a multi-threaded JVM, if all threads allocated objects directly onto a shared global heap, they would have to synchronize (using locks or CAS operations on the heap pointer) for every single object creation, creating a severe bottleneck. A TLAB is a dedicated chunk of the Eden space assigned exclusively to an individual thread. The thread can allocate objects inside its private TLAB simply by bumping a local pointer (bump-the-pointer allocation) without any synchronization or lock contention. Only when a thread's TLAB fills up does it acquire a synchronized lock to request a new TLAB from the young generation.",
     ["Defines TLAB as dedicated thread-specific chunk of Eden space", "Explains bump-the-pointer allocation avoiding global synchronization locks", "Notes synchronization only occurs when replenishing a full TLAB"],
     ["Claims TLABs are stored on the operating system stack"]),

    ("B65_1_18", "diagnose", "medium", "debugging", ["JVM Performance", "Profiling"],
     "You analyze a Java thread dump taken during a period of high request queuing and notice dozens of threads in state 'WAITING (parking)' on 'java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionNode'. How do you identify which thread is holding the corresponding lock?",
     "In a standard thread dump (jstack -l <pid>), threads blocked on java.util.concurrent locks (such as ReentrantLock or thread pools) display parking status with the lock object ID: '- parking to wait for <0x00000007...>'. To find the lock holder: 1) Run jstack with the -l (long) flag to print 'Locked ownable synchronizers'; 2) Search the thread dump text for the memory address '0x00000007...' under other thread entries; 3) Find the thread that has '- locked <0x00000007...>' in its stack trace or lists that address under its 'Locked ownable synchronizers' section. That thread is the current owner preventing all waiting threads from proceeding.",
     ["Identifies lock memory address in thread dump parking string", "Uses jstack -l to inspect 'Locked ownable synchronizers'", "Locates the owning thread holding the exact memory address reference"],
     ["Claims AQS locks do not appear in thread dumps"]),

    ("B65_1_19", "implement", "hard", "implement", ["JVM Diagnostics", "Profiling"],
     "How do you create and register a custom Java Flight Recorder (JFR) Event in a high-performance Java service to measure transaction latency without degrading runtime performance?",
     "Subclass 'jdk.jfr.Event', annotate it with @Name, @Label, @Category, and optionally @StackTrace(false) to minimize overhead if call stacks are not needed. Define event payload fields (e.g., String customerId, long amountMicros). In code, instantiate the event, call event.begin(), execute the transaction in a try-finally block, and in finally call event.end() and event.commit(). If the JFR recording is not currently running or the event is disabled by the current JFR profile, JFR's intrinsic methods make event.shouldCommit() return false with near-zero overhead (a simple memory read), ensuring virtually zero performance penalty during normal execution.",
     ["Subclasses jdk.jfr.Event with appropriate annotations (@Name, @Label, @Category)", "Uses event.begin(), event.end(), and event.commit() lifecycle", "Explains low-overhead intrinsics and shouldCommit() check when inactive"],
     ["Creates a custom background thread to poll JFR metrics"]),

    ("B65_1_20", "tradeoff", "medium", "tradeoff", ["Garbage Collection", "Performance Tuning"],
     "What is the operational tradeoff between setting static heap boundaries (-Xms equal to -Xmx) versus allowing dynamic heap expansion in containerized Java services?",
     "Setting -Xms equal to -Xmx pre-allocates the entire heap memory upfront during JVM startup. Tradeoff: It guarantees that the container has enough host memory immediately (failing fast at boot if memory is constrained) and completely eliminates the runtime latency pauses caused by the JVM requesting additional memory pages from the operating system and zeroing them during runtime traffic spikes. The downside is reduced container density: the pod consumes its maximum memory footprint from second one, preventing cluster bin-packing and dynamic memory sharing across co-located workloads. Dynamic heap sizing allows lower idle memory usage, but risks runtime page allocation latency and unexpected OOMKills if the host exhausts physical RAM during a traffic surge.",
     ["Explains pre-allocation and fail-fast behavior of -Xms equal to -Xmx", "Highlights elimination of runtime heap expansion latency pauses", "Contrasts with container density, memory footprint, and cluster bin-packing efficiency"],
     ["Claims -Xms and -Xmx control off-heap direct memory buffers"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 1).")
    
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
    print("POST-BATCH AUDIT PART 1")
    print("========================================")
    print(f"Batch: 65 Part 1")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
