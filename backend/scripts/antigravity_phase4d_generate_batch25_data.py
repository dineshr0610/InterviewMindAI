"""Batch 25 question content (Java Developer). Targeted Gap Generation."""

ROLE = "Java Developer"

BUCKET_KEYS = {
    "JAVA_JVM_MEM": ("JVM & Memory Management", "Garbage Collection & JIT", "Java", ["Backend Developer", "Performance Engineer"]),
    "JAVA_CONCUR": ("Java Concurrency", "Multithreading & Thread Pools", "Java", ["Backend Developer", "Software Engineer"]),
    "JAVA_ARCH": ("Enterprise Architecture", "Distributed Systems & Resilience", "Java", ["Backend Developer", "Architecture"]),
}

Q = [
# ---------------- JAVA_JVM_MEM ----------------
("JAVA_JVM_MEM", "debug", "hard", "debugging", ["Heap Analysis"],
 "You notice your Java application periodically completely freezes for several seconds at a time. The application logs show nothing, but GC logs show massive 'Stop-The-World' pauses during Full GC collections. What JVM metric would you investigate to determine if this is caused by a memory leak or simply bad GC tuning, and how?",
 "You must investigate the heap utilization exactly *after* a Full GC completes. If the heap usage drops back to a normal baseline after every Full GC, the application is simply suffering from bad tuning or an excessively high allocation rate (thrashing). However, if the baseline heap usage steadily creeps upward over time after consecutive Full GCs, it confirms a genuine memory leak where objects are permanently retained.",
 ["Investigate heap utilization *after* a Full GC completes", "If usage drops to baseline, it's an allocation rate/tuning issue", "If baseline usage steadily creeps upward over time, it's a memory leak"],
 ["Check if the CPU temperature is too high"]),

("JAVA_JVM_MEM", "scenario", "hard", "scenario", ["Metaspace"],
 "A high-throughput Java service throws an `OutOfMemoryError: Metaspace`. You are not creating massive object graphs, and heap usage is perfectly fine. What specific runtime mechanism typically causes a Metaspace leak in long-running Java applications?",
 "The Metaspace strictly stores class metadata, not object instances. A Metaspace OOM almost always indicates a ClassLoader leak. This occurs when dynamic proxy generation frameworks (like CGLIB, Hibernate, or Spring) continuously generate new runtime classes, but the old classes are never unloaded because their parent ClassLoaders are being inadvertently retained in memory.",
 ["Metaspace stores class metadata, not object instances", "Indicates a ClassLoader leak, not a standard heap memory leak", "Caused by frameworks continuously generating dynamic classes without unloading old ClassLoaders"],
 ["The garbage collector forgot to clean the database"]),

("JAVA_JVM_MEM", "explain", "medium", "concept", ["Garbage Collection"],
 "Explain the primary architectural difference between the G1 Garbage Collector and the older Parallel GC.",
 "Parallel GC strictly partitions the heap into large, contiguous Young and Old generations, inherently causing long 'Stop-The-World' global pauses when sweeping the massive Old generation. The G1 (Garbage First) GC divides the heap into thousands of small, equal-sized dynamic regions. It evaluates which regions contain the most garbage and prioritizes collecting them first, allowing it to meet strict, predictable pause-time goals.",
 ["Parallel GC uses large, contiguous generations, causing long global pauses", "G1 GC divides the heap into thousands of small, equal-sized regions", "G1 prioritizes regions with the most garbage to meet predictable pause-time targets"],
 ["G1 stands for Generation 1, Parallel stands for Generation 2"]),

("JAVA_JVM_MEM", "tradeoff", "medium", "tradeoff", ["GC Tuning"],
 "When tuning a Java application, what is the tradeoff of significantly increasing the maximum heap size (`-Xmx`)?",
 "A larger heap massively improves peak throughput because the application can sustain high allocation rates and cache more data for much longer without triggering Garbage Collection. The severe tradeoff is that when the heap finally fills up and a Full GC is triggered, the 'Stop-The-World' pause time will be drastically longer because the GC thread has a significantly larger memory space to traverse and sweep.",
 ["Increases peak throughput and delays GC cycles", "Allows caching more data and sustaining high allocation rates", "Tradeoff: When a Full GC occurs, the 'Stop-The-World' pause time is drastically longer"],
 ["Increasing the heap size makes the code compile slower"]),

("JAVA_JVM_MEM", "implement", "easy", "implementation", ["Diagnostics"],
 "How do you capture a Heap Dump from a live, running Java application that is experiencing a memory leak, without crashing the process?",
 "You can natively use the `jmap` CLI tool included in the JDK (e.g., `jmap -dump:live,format=b,file=heap.bin <PID>`). Alternatively, you can use the more modern `jcmd <PID> GC.heap_dump heap.bin`, or connect via JMX using a visual diagnostic tool like VisualVM or JDK Mission Control.",
 ["Use the `jmap` CLI tool (e.g., `jmap -dump:live...`)", "Use the modern `jcmd` tool", "Connect via JMX using VisualVM or JDK Mission Control"],
 ["Take a screenshot of the server terminal"]),

("JAVA_JVM_MEM", "fundamentals", "medium", "concept", ["JIT Compiler"],
 "What exactly does the JVM's JIT (Just-In-Time) compiler do at runtime that makes a long-running Java application faster than when it first starts?",
 "The JIT compiler continuously profiles the running application to identify 'hot spots' (frequently executed methods or loops). Instead of slowly interpreting the bytecode, the JIT dynamically compiles those specific hot spots down to highly optimized, native machine code for the host OS. Because it observes actual runtime behavior, it performs aggressive optimizations like method inlining, loop unrolling, and dead-code elimination.",
 ["Profiles the running application to identify 'hot spots'", "Dynamically compiles hot bytecode into highly optimized native machine code", "Performs runtime optimizations (e.g., method inlining) based on actual execution profiles"],
 ["It downloads RAM from the internet"]),

("JAVA_JVM_MEM", "scenario", "hard", "scenario", ["JIT Optimization"],
 "You have a perfectly optimized mathematical loop in Java. You run it once and it takes 100ms. You run it 10,000 times, and the execution time suddenly drops to 5ms per loop. Then, you pass a slightly different subclass object into the loop, and the execution time spikes back up to 80ms. What JVM mechanism caused this sudden degradation?",
 "The JIT compiler heavily optimized the loop via 'Monomorphic Inline Caching'. Because it initially saw only one class type, it stripped away dynamic dispatch overhead and hardcoded the method execution. When you introduced a new subclass, the call site became Megamorphic. The JIT's assumptions were violated, forcing it to immediately 'deoptimize' (throw away the native code) and revert to slower interpreted polymorphic dispatch.",
 ["JIT initially applied 'Monomorphic Inline Caching' (hardcoding the method for one class type)", "Introducing a new subclass made the call site Megamorphic", "Forced the JIT to 'deoptimize', discarding the native code and reverting to slow interpreted execution"],
 ["The subclass was too heavy for the CPU to lift"]),

("JAVA_JVM_MEM", "debug", "medium", "debugging", ["OOM Exceptions"],
 "An application crashes with `java.lang.OutOfMemoryError: GC overhead limit exceeded`. What exact state triggers this specific exception?",
 "This specific exception is triggered as a fail-fast mechanism when the JVM is spending more than 98% of its total CPU time exclusively performing Garbage Collection, but is successfully recovering less than 2% of the total heap space. It indicates that the application is critically out of memory and completely thrashing (essentially frozen), preventing it from doing any actual application work.",
 ["JVM spends >98% of CPU time doing Garbage Collection", "Recovers <2% of heap space", "Indicates the JVM is critically out of memory, completely thrashing, and frozen"],
 ["The garbage collector is on strike"]),

("JAVA_JVM_MEM", "tradeoff", "hard", "tradeoff", ["Garbage Collection"],
 "What are the tradeoffs between the modern ZGC (Z Garbage Collector) and the G1 GC?",
 "ZGC is designed for ultra-low latency, offering sub-millisecond pause times regardless of heap size (even on terabyte heaps) by performing almost all GC operations concurrently with application threads. The tradeoff is that ZGC generally requires more overall CPU overhead and may reduce peak application throughput compared to G1. G1 offers higher peak throughput but larger, less predictable Stop-The-World pause times.",
 ["ZGC: Ultra-low, sub-millisecond pause times regardless of heap size (highly concurrent)", "ZGC Tradeoff: Requires more CPU overhead, reducing peak application throughput", "G1: Higher peak throughput but less predictable, longer pause times"],
 ["ZGC deletes zero-value integers, G1 deletes one-value integers"]),

("JAVA_JVM_MEM", "explain", "medium", "concept", ["Escape Analysis"],
 "What is 'Escape Analysis' in the context of the Java JVM, and how does it optimize memory allocation?",
 "Escape Analysis is an advanced JIT compiler optimization. The JIT analyzes the scope of an object created inside a method to determine if a reference to that object ever 'escapes' the method (e.g., returned, or assigned to a global field). If the object strictly does not escape, the JIT optimizes allocation by placing the object entirely on the thread's Stack (or in CPU registers) instead of the Heap, completely bypassing Garbage Collection.",
 ["JIT optimization determining if an object reference 'escapes' its creating method's scope", "If it does not escape, the object is allocated on the Thread Stack instead of the Heap", "Eliminates GC overhead for temporary local objects"],
 ["It analyzes how hackers can escape the application sandbox"]),

("JAVA_JVM_MEM", "implement", "medium", "implementation", ["Thread Analysis"],
 "You suspect a multithreaded Java application is experiencing thread starvation or deadlocks. You only have shell access to the Linux server. How do you natively capture a snapshot of exactly what every thread is doing at that exact moment?",
 "You natively capture a Thread Dump using the JDK's `jstack` utility. You run `jstack <PID>` (or `jcmd <PID> Thread.print`). This immediately prints a full thread dump to the console, revealing the exact stack trace, current state (RUNNABLE, BLOCKED, WAITING), and specific lock acquisition status of every active thread in the JVM.",
 ["Use the `jstack <PID>` or `jcmd <PID> Thread.print` CLI tools", "Prints a full thread dump showing exact stack traces", "Reveals thread states (BLOCKED/WAITING) and lock acquisition status"],
 ["Take a photo of the CPU threads with a microscope"]),

("JAVA_JVM_MEM", "scenario", "hard", "scenario", ["ThreadLocal"],
 "A Java application uses `ThreadLocal` variables to cache user context. The application runs inside a Tomcat web server utilizing a thread pool. Users are occasionally seeing data belonging to completely different users. Why did this happen?",
 "`ThreadLocal` variables are strictly bound to the specific OS thread executing them. Because Tomcat (and most web servers) reuse threads from a pool to handle sequential HTTP requests, a `ThreadLocal` value set during User A's request remains bound to that physical thread. When the thread is reused for User B's request, User B sees User A's data. You must explicitly call `threadLocal.remove()` in a `finally` block at the end of every request.",
 ["`ThreadLocal` variables are bound to the specific physical OS thread", "Web servers (Tomcat) reuse threads from a pool across different HTTP requests", "Values bleed across requests if `threadLocal.remove()` is not called in a `finally` block"],
 ["The database mixed up the user IDs"]),

("JAVA_JVM_MEM", "fundamentals", "easy", "concept", ["Heap Layout"],
 "What is the purpose of the 'Survivor Spaces' (S0 and S1) inside the JVM's Young Generation memory model?",
 "Survivor spaces act as an age buffer. Objects that survive a Minor GC in the initial Eden space are moved to a Survivor space. During subsequent Minor GCs, surviving objects are swapped back and forth between S0 and S1, incrementing their age. This provides a grace period, allowing short-lived objects to die off before they are prematurely and permanently promoted to the expensive Old Generation.",
 ["Act as an age buffer between the Eden space and the Old Generation", "Objects swap between S0 and S1 during Minor GCs, incrementing their age", "Allows short-lived objects to die before being promoted to the expensive Old Generation"],
 ["They are VIP rooms for important objects"]),

("JAVA_JVM_MEM", "debug", "medium", "debugging", ["ClassLoading"],
 "You deploy a new `.jar` file to an enterprise Java application. At runtime, the application crashes with a `java.lang.NoSuchMethodError`. You are 100% certain the method exists in the dependency you compiled against. What runtime classpath issue causes this?",
 "This is caused by 'Jar Hell' (Shadowing). Multiple different versions of the exact same library (or class) exist on the runtime classpath. At runtime, the JVM's ClassLoader scans the classpath and happened to find and load the older version of the class (which lacks the new method) before it found the newer version you compiled against.",
 ["'Jar Hell' or Class Shadowing", "Multiple different versions of the same library exist on the runtime classpath", "The ClassLoader loaded the older version (missing the method) first"],
 ["The method was deleted by a hacker"]),

("JAVA_JVM_MEM", "explain", "hard", "concept", ["Safepoints"],
 "Explain the JVM 'Safepoint' mechanism. Why must the JVM bring all threads to a safepoint before performing a Stop-The-World garbage collection?",
 "A Safepoint is a state where a thread's execution is suspended at a known, mathematically safe boundary (e.g., method entries, loop backedges). The JVM must bring all application threads to a safepoint before a Stop-The-World GC because the GC must safely traverse thread stacks to find GC roots, and crucially, physically move objects to new memory addresses. If threads were actively executing, they would instantly crash when following pointers to moved objects.",
 ["A state where a thread is suspended at a known, safe execution boundary", "Required to safely traverse thread stacks for GC roots", "Required because the GC physically moves objects; active threads would access invalid memory addresses"],
 ["Safepoints are backup saves in case the JVM crashes"])
]
