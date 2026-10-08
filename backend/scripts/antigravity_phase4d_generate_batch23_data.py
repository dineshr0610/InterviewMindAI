"""Batch 23 question content (Python Developer). Targeted Gap Generation."""

ROLE = "Python Developer"

BUCKET_KEYS = {
    "PY_ASYNC": ("Python Concurrency", "Asyncio & Event Loops", "Python", ["Backend Developer", "Software Engineer"]),
    "PY_CONCUR": ("Python Concurrency", "Threading & Multiprocessing", "Python", ["Backend Developer", "Data Engineer"]),
    "PY_MEM": ("Memory Management", "Garbage Collection & Profiling", "Python", ["Software Engineer"]),
    "PY_OOP_ADV": ("Advanced OOP", "Metaclasses & Descriptors", "Python", ["Software Engineer"]),
    "PY_DEBUG": ("Production Debugging", "Profiling & Diagnostics", "Python", ["Site Reliability Engineer", "Backend Developer"]),
}

Q = [
# ---------------- PY_ASYNC ----------------
("PY_ASYNC", "scenario", "medium", "scenario", ["Asyncio"],
 "An asyncio service is designed to make hundreds of concurrent HTTP requests. However, you notice the application is entirely blocking and only processing one request at a time. You investigate and find the code uses `requests.get()` inside an `async def` function. Why does this ruin asyncio throughput, and how do you fix it?",
 "The `requests` library is synchronous and blocking. When it executes a network call, it physically blocks the underlying OS thread, completely freezing the asyncio Event Loop and preventing any other coroutines from running. To fix it, you must either replace `requests` with a native async library like `aiohttp`/`httpx`, or offload the synchronous `requests.get()` call to a background thread using `loop.run_in_executor()`.",
 ["`requests` is a synchronous, blocking library", "It blocks the OS thread, freezing the entire asyncio Event Loop", "Fix by using an async library (aiohttp/httpx) or offloading to a thread via `run_in_executor`"],
 ["The server doesn't have enough RAM"]),

("PY_ASYNC", "debug", "hard", "debugging", ["Event Loop"],
 "You have a long-running `asyncio` task that performs heavy CPU-bound matrix math inside a tight `while` loop. During this calculation, all other async tasks completely freeze. How do you yield control back to the event loop during this intensive calculation without offloading to another thread?",
 "Because `asyncio` uses cooperative multitasking, a coroutine must explicitly yield control. A tight CPU-bound loop never hits an `await` expression, starving the event loop. You can yield control back to the loop periodically by inserting `await asyncio.sleep(0)` inside the `while` loop. This suspends the coroutine for 0 seconds, signaling the event loop to instantly run other pending tasks before resuming the calculation.",
 ["CPU-bound loops never yield control, starving the event loop", "Insert `await asyncio.sleep(0)` inside the calculation loop", "Forces a context switch, allowing the event loop to process other pending tasks"],
 ["Just run the math faster"]),

("PY_ASYNC", "tradeoff", "medium", "tradeoff", ["Task Scheduling"],
 "What are the tradeoffs between using `asyncio.gather()` versus `asyncio.as_completed()` when waiting for multiple asynchronous tasks to finish?",
 "`asyncio.gather()` waits for all tasks and returns a single list of results in the exact order the tasks were passed in. However, you must wait for the slowest task to finish before processing any results. `asyncio.as_completed()` returns an iterator that yields results the exact moment each task finishes, allowing immediate processing, but the results arrive out of order.",
 ["`gather()`: Returns results in original order, but blocks until the slowest task finishes", "`as_completed()`: Yields results immediately as they finish (lower latency), but out of order", "Use `gather` for strict ordering, `as_completed` for immediate pipeline processing"],
 ["`gather` uses more CPU, `as_completed` uses more RAM"]),

("PY_ASYNC", "implement", "hard", "implementation", ["Graceful Shutdown"],
 "How do you gracefully shut down an asyncio event loop, ensuring all currently pending background tasks (like database writes) complete before the application exits?",
 "You must intercept the shutdown signal (like SIGINT/SIGTERM). Inside the handler, fetch all running tasks using `asyncio.all_tasks()`. Call `.cancel()` on all of them, which injects `CancelledError`. Then, use `loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))` to await them. The tasks must contain `try/except asyncio.CancelledError` blocks to perform their final cleanup (closing connections) before cleanly exiting.",
 ["Fetch all running tasks via `asyncio.all_tasks()`", "Call `.cancel()` on the tasks and await them using `gather(return_exceptions=True)`", "Coroutines must catch `CancelledError` to perform cleanup logic (closing DB connections)"],
 ["Just unplug the server to shut it down gracefully"]),

("PY_ASYNC", "scenario", "medium", "scenario", ["Task Lifecycle"],
 "You schedule a background task using `asyncio.create_task(my_coro())` but do not assign the result to a variable. A few minutes later, the task mysteriously stops executing before completion, even though no exception was raised. What garbage collection mechanism caused this?",
 "The asyncio event loop only holds a 'weak reference' to scheduled tasks. If you fire-and-forget a task without assigning it to a variable (or adding it to a global tracking set), Python's Garbage Collector sees no strong references to the Task object and destroys it mid-flight. You must always maintain a strong reference to background tasks (e.g., `background_tasks.add(task)`).",
 ["The event loop only holds a weak reference to tasks", "If unreferenced, Python's Garbage Collector destroys the Task mid-flight", "Must maintain a strong reference (assign to variable or append to a collection)"],
 ["The event loop got tired and went to sleep"]),

("PY_ASYNC", "explain", "medium", "concept", ["Cancellation"],
 "Explain the concept of Task Cancellation in `asyncio`. When you call `.cancel()` on a Task, what exactly happens at the code level inside the coroutine?",
 "Task Cancellation is a mechanism to abort a running coroutine. When `.cancel()` is called, the event loop schedules an `asyncio.CancelledError` exception to be thrown directly into the coroutine at the exact point of its current `await` expression. The coroutine can catch this exception to perform cleanup, but it should generally allow the exception to bubble up to acknowledge the cancellation.",
 ["Schedules an `asyncio.CancelledError` to be thrown into the coroutine", "Exception is injected at the coroutine's current `await` point", "Allows the coroutine to catch it for cleanup before aborting"],
 ["The code deletes the file from the hard drive"]),

("PY_ASYNC", "fundamentals", "easy", "concept", ["Event Loop"],
 "What is the purpose of `asyncio.run()`?",
 "`asyncio.run()` is the primary entry point for modern asyncio applications. It automatically creates a new event loop, schedules and runs the passed top-level coroutine until it completes, and then safely and synchronously closes the event loop and finalizes asynchronous generators.",
 ["Primary entry point for modern asyncio apps", "Creates a new event loop and runs the main coroutine", "Safely tears down and closes the loop upon completion"],
 ["It makes standard Python code run 10x faster automatically"]),

("PY_ASYNC", "debug", "medium", "debugging", ["Event Loop"],
 "An asyncio application occasionally throws the error `RuntimeError: This event loop is already running`. Under what architectural mistake does this typically occur?",
 "This typically occurs when a developer attempts to call `asyncio.run()` or uses synchronous event loop blocking methods (like `loop.run_until_complete()`) from *inside* a coroutine or callback that is already currently executing on that exact same event loop. You cannot recursively block a loop that is already running.",
 ["Attempting to call `asyncio.run()` or `run_until_complete()` from inside an active coroutine", "You cannot recursively block an event loop that is already actively running", "Usually indicates mixing sync/async architectural patterns incorrectly"],
 ["The loop is spinning too fast and overheating"]),

("PY_ASYNC", "implement", "medium", "implementation", ["Integration"],
 "You have a legacy synchronous database driver that you absolutely must use within a modern FastAPI (asyncio) application. How do you execute this synchronous driver without blocking the main event loop?",
 "You must offload the synchronous driver call to a separate worker thread so it doesn't block the async event loop. You do this using `await loop.run_in_executor(None, legacy_db_call, args)`. This schedules the blocking function on the default `ThreadPoolExecutor` and yields an awaitable future back to the event loop.",
 ["Offload the synchronous blocking call to a background thread", "Use `loop.run_in_executor(executor, func, *args)`", "Allows the main event loop to remain unblocked while the thread waits on the legacy driver"],
 ["Wrap the database in a try/catch block"]),

("PY_ASYNC", "scenario", "hard", "scenario", ["Synchronization"],
 "You are using `asyncio.Semaphore` to limit concurrent API requests to 10. However, if a coroutine holding the semaphore throws an unhandled exception, the semaphore counter never decrements, eventually deadlocking the entire application. How must you implement the semaphore to guarantee release?",
 "You must acquire and release the semaphore using the `async with` context manager block (e.g., `async with semaphore:`). The context manager guarantees that the semaphore's `.release()` method is called during the teardown phase, regardless of whether the block succeeds or raises an unhandled exception, preventing the deadlock.",
 ["Must use the `async with` context manager block", "Guarantees `.release()` is called even if an unhandled exception occurs", "Prevents resource leaks and deadlocks in synchronization primitives"],
 ["Just restart the application every 5 minutes"]),

# ---------------- PY_CONCUR ----------------
("PY_CONCUR", "tradeoff", "medium", "tradeoff", ["Concurrency Models"],
 "When designing a Python web scraper, what are the tradeoffs of using a `ThreadPoolExecutor` versus a `ProcessPoolExecutor`?",
 "Threads share memory and have extremely low startup overhead. They bypass the GIL for I/O operations (like network requests), making them perfect for web scraping. Processes create entirely separate Python interpreters, bypassing the GIL completely for CPU-bound tasks, but they consume massive amounts of memory, have high startup latency, and require all shared data to be serialized (Pickled) over IPC.",
 ["Threads: Shared memory, low overhead, bypass GIL for I/O (perfect for scraping)", "Processes: Separate memory, massive overhead, bypass GIL for CPU-bound work", "Processes require data serialization (Pickling) across IPC"],
 ["Threads are for Mac, Processes are for Windows"]),

("PY_CONCUR", "scenario", "hard", "scenario", ["Race Conditions"],
 "A multi-threaded Python worker fetches jobs from a shared list. Despite using `threading.Lock()` around the `pop()` operation, workers occasionally crash with an `IndexError: pop from empty list`. What synchronization mistake causes this?",
 "The lock protects the exact moment of popping, but the check for list emptiness (`if len(jobs) > 0:`) was done *outside* the lock. This creates a classic 'Time-Of-Check to Time-Of-Use' race condition. Thread A checks the list (len=1). Thread B checks the list (len=1). Thread A acquires the lock and pops. Thread B acquires the lock, tries to pop, and crashes. Both the check and the pop must be inside the single lock block.",
 ["Time-Of-Check to Time-Of-Use race condition", "The emptiness check (`len > 0`) occurred outside the lock boundary", "Thread A pops the last item after Thread B checked, causing Thread B to crash. Both must be inside the lock."],
 ["The list was deleted by the garbage collector"]),

("PY_CONCUR", "fundamentals", "easy", "concept", ["Multiprocessing"],
 "In Python's `multiprocessing` module, why must all data passed between processes (e.g., via a Queue) be Picklable?",
 "Because completely separate processes do not share a memory space. To pass an object from Process A to Process B, Python must serialize the object into a byte stream (Pickling), send those bytes over an Inter-Process Communication (IPC) pipe, and deserialize them in the target process. If an object cannot be Pickled (like a network socket or file handle), it cannot be sent.",
 ["Processes do not share memory space", "Objects must be serialized (Pickled) to a byte stream to traverse IPC pipes", "Unpicklable objects (sockets, locks) cannot be passed between processes"],
 ["Pickles are a delicious snack for the CPU"]),

("PY_CONCUR", "debug", "medium", "debugging", ["Windows Multiprocessing"],
 "A Python script uses `multiprocessing.Pool` to process 10,000 images. The code runs fine on Linux, but when deployed to Windows, it immediately crashes in an infinite recursive loop of creating new processes. What Python-specific guard block is missing?",
 "The script is missing the `if __name__ == '__main__':` guard block. Linux uses `fork()` to clone processes (inheriting memory). Windows does not have `fork()`; it uses `spawn()`, which imports the main module from scratch in every new child process. Without the `__main__` guard, the child process executes the top-level `multiprocessing.Pool` call again, spawning children recursively until the OS crashes.",
 ["Missing the `if __name__ == '__main__':` guard block", "Windows uses `spawn()` (re-importing the module), not `fork()`", "Without the guard, child processes recursively execute the Pool creation code"],
 ["Windows requires a paid license for multiprocessing"]),

("PY_CONCUR", "explain", "hard", "concept", ["Deadlocks"],
 "Explain how a Deadlock occurs in a multithreaded Python application. Give a conceptual example involving two threads and two Locks.",
 "A deadlock occurs when two or more threads are permanently blocked, each waiting for a resource held by the other. For example: Thread A acquires Lock 1. Thread B acquires Lock 2. Thread A then tries to acquire Lock 2 (blocked by B), while Thread B tries to acquire Lock 1 (blocked by A). Both threads will wait infinitely, deadlocking the system. It is avoided by ensuring all threads acquire locks in a strict global order.",
 ["Threads are permanently blocked waiting for resources held by each other", "Thread A holds Lock 1 and waits for Lock 2; Thread B holds Lock 2 and waits for Lock 1", "Prevented by enforcing a strict global ordering for lock acquisition"],
 ["A deadlock is when the server battery dies"]),

("PY_CONCUR", "implement", "medium", "implementation", ["Shared Memory"],
 "You need to share a massive 5GB read-only dictionary across 8 worker processes. Passing it via a `multiprocessing.Queue` causes out-of-memory errors and massive serialization overhead. How do you share it efficiently?",
 "If on Linux/Unix, you can simply initialize the 5GB dictionary globally *before* calling the multiprocessing pool. Because Unix uses `fork()`, the children inherit the memory mapping via Copy-On-Write, consuming zero extra RAM as long as it remains read-only. Alternatively, you can use `multiprocessing.shared_memory` (introduced in Python 3.8) to map raw memory blocks accessible by all processes.",
 ["Linux/Unix: Initialize before fork to utilize Copy-On-Write (zero extra RAM if read-only)", "Cross-platform: Use `multiprocessing.shared_memory`", "Avoids the massive Pickling and IPC overhead of passing 5GB via Queues"],
 ["Zip the dictionary into a file and email it to the processes"]),

("PY_CONCUR", "scenario", "medium", "scenario", ["GIL Limits"],
 "Two Python threads attempt to increment a shared global counter `x += 1` 1,000,000 times. Even with the GIL, the final result is significantly less than 2,000,000. Why does the GIL not protect this operation?",
 "The GIL ensures only one thread executes Python bytecodes at a time, but `x += 1` is NOT a single atomic bytecode. It involves three steps: LOAD the value, ADD 1, and STORE the value. The GIL can pause a thread in the middle of these steps and switch to the other thread, causing a classic race condition where increments are overwritten. You still must use `threading.Lock()`.",
 ["`x += 1` is not an atomic bytecode operation (LOAD, ADD, STORE)", "The GIL can context-switch threads between the load and the store", "Creates a race condition; the GIL does not replace the need for Locks"],
 ["The GIL deletes random numbers to save space"]),

("PY_CONCUR", "fundamentals", "easy", "concept", ["Threading"],
 "What is a `Daemon Thread` in Python, and how does its lifecycle differ from a normal thread?",
 "A normal Python thread prevents the main program from exiting until the thread completes its work. A Daemon Thread runs in the background and is abruptly terminated the exact moment the main program (and all non-daemon threads) finish. Daemon threads are useful for background tasks like heartbeats or metric logging that shouldn't block shutdown.",
 ["Normal threads block the program from exiting", "Daemon threads are abruptly killed when the main program finishes", "Useful for infinite background loops (e.g., heartbeats, monitoring)"],
 ["Daemon threads only run at midnight"]),

("PY_CONCUR", "tradeoff", "medium", "tradeoff", ["Thread Synchronization"],
 "What are the tradeoffs between using `queue.Queue` (Thread-safe) versus a standard Python `collections.deque` when sharing data between threads?",
 "`queue.Queue` provides advanced synchronization semantics, allowing threads to block, wait, or timeout when getting/putting items, making it perfect for producer-consumer architectures, but it introduces locking overhead. `collections.deque` provides inherently thread-safe, atomic append/pop operations that are incredibly fast, but it lacks any built-in blocking/waiting mechanisms if the deque is empty.",
 ["`Queue`: Fully synchronized, supports blocking/timeouts, perfect for Producer-Consumer", "`Queue`: Slower due to explicit locking overhead", "`deque`: Atomic, extremely fast appends/pops, but no blocking/timeout capabilities"],
 ["Deque is for French developers, Queue is for English developers"]),

("PY_CONCUR", "debug", "hard", "debugging", ["Process Pool"],
 "You use `concurrent.futures.ProcessPoolExecutor` to map a function over a large list. The program hangs indefinitely without throwing any error. You discover the worker function is raising a `MemoryError`. Why does the main program hang instead of crashing?",
 "When a child process crashes catastrophically (like a C-level segfault, OS kill, or out-of-memory) without properly returning a Python Exception object over IPC, the `Future` object tracking that job in the main process never receives a terminal state. The main process waits indefinitely for a response that will never arrive. You must implement timeouts on your Future `.result(timeout=X)` to prevent hanging.",
 ["Child process crashed catastrophically without returning an exception over IPC", "The `Future` in the main process gets stuck in a pending state forever", "Must use `.result(timeout=X)` to prevent infinite hanging"],
 ["The worker function went on vacation"]),

# ---------------- PY_MEM ----------------
("PY_MEM", "explain", "easy", "concept", ["Garbage Collection"],
 "How does Python's primary memory management system (Reference Counting) work?",
 "Every object in Python maintains a count of how many variables, lists, or attributes are currently pointing to it. When you assign a variable to an object, the count goes up. When a variable goes out of scope or is deleted, the count goes down. The exact moment the reference count hits zero, Python immediately destroys the object and reclaims the memory.",
 ["Every object tracks the number of references pointing to it", "When a reference is deleted or goes out of scope, count decreases", "When count reaches zero, the object is immediately destroyed"],
 ["It counts how many times the user looks at the screen"]),

("PY_MEM", "scenario", "hard", "scenario", ["Memory Leaks"],
 "You have a long-running Python worker processing streaming data. Memory usage climbs linearly over 24 hours until OOM. You take a heap dump and find millions of custom `Node` objects. `Node A` points to `Node B`, and `Node B` points to `Node A`. Both are deleted from the active dictionary. Why didn't Reference Counting destroy them?",
 "They formed a Circular Reference (Reference Cycle). Even though the active application no longer points to them, `Node A` and `Node B` still point to each other. Therefore, their reference counts never drop to zero, and the primary Reference Counting system ignores them. They will remain in memory until the secondary Generational Garbage Collector runs and detects the isolated cycle.",
 ["Circular References (Reference Cycles)", "Objects point to each other, so their ref counts never reach zero", "Reference Counting fails; must rely on the background Generational GC to sweep them"],
 ["The nodes were marked as VIP objects"]),

("PY_MEM", "fundamentals", "medium", "concept", ["Garbage Collection"],
 "If Reference Counting fails to clean up circular references, how does Python eventually reclaim that memory?",
 "Python includes a secondary, background Generational Garbage Collector (the `gc` module). It specifically scans container objects (lists, dicts, custom classes) to detect isolated circular reference graphs that are no longer reachable from the main program. Once an unreachable cycle is detected, the GC breaks the cycle and reclaims the memory. It organizes objects into 3 generations to optimize scanning.",
 ["Secondary background Generational Garbage Collector scans for cycles", "Detects isolated, unreachable reference graphs and breaks the cycle", "Organizes objects into 3 generations (young, middle, old) to optimize scan performance"],
 ["It sends the memory to the recycling plant"]),

("PY_MEM", "implement", "medium", "implementation", ["GC Controls"],
 "How do you explicitly instruct Python's Garbage Collector to run a full sweep, and when might you legitimately need to do this in production?",
 "You call `import gc; gc.collect()`. While generally discouraged because it causes a blocking CPU pause, it is legitimately useful in memory-constrained environments (like Kubernetes pods with strict limits) immediately after deleting a massive, complex, cyclic data structure to force the OS to reclaim the RAM instantly, preventing a proactive OOM kill.",
 ["Call `import gc` and `gc.collect()`", "Forces a synchronous, full blocking sweep of all generations", "Useful after deleting massive cyclic data in memory-constrained environments to prevent OOM kills"],
 ["Press Alt-F4 on the server keyboard"]),

("PY_MEM", "debug", "hard", "debugging", ["Weak References"],
 "You are caching database objects in a global dictionary to avoid repeated queries. Over time, this dictionary consumes 10GB of RAM because objects are never removed, causing a memory leak. How do you re-architect this cache using `weakref` so objects are cached only as long as they are being used elsewhere in the application?",
 "You replace the standard dictionary with a `weakref.WeakValueDictionary`. A standard dict holds a 'strong reference' to the object, preventing it from ever being garbage collected. A weak reference allows the cache to track the object without incrementing its reference count. When the rest of the application is done with the object, it is destroyed, and the `WeakValueDictionary` automatically removes the cache entry.",
 ["Use `weakref.WeakValueDictionary`", "Weak references do not increment the object's reference count", "When the app drops the object, it is garbage collected, and automatically disappears from the cache"],
 ["Just reboot the server every 10 minutes to clear the cache"]),

("PY_MEM", "tradeoff", "medium", "tradeoff", ["Memory Optimization"],
 "What is the tradeoff of defining `__slots__` on a Python class?",
 "By default, every Python instance uses a dynamic `__dict__` to store attributes, which consumes significant memory overhead. Defining `__slots__ = ['x', 'y']` replaces the dictionary with a static array, drastically reducing memory usage per instance and speeding up attribute access. The tradeoff is strict rigidity: you can no longer dynamically add arbitrary new attributes to instances at runtime.",
 ["Drastically reduces memory overhead per instance by eliminating the underlying `__dict__`", "Speeds up attribute access times", "Strict rigidity: cannot dynamically add new attributes at runtime"],
 ["Slots turn the class into a casino game"]),

("PY_MEM", "explain", "medium", "concept", ["Memory Fragmentation"],
 "What is 'Memory Fragmentation' in a long-running CPython process, and why might the OS report high RAM usage even if you `del` a large number of objects?",
 "CPython uses a custom memory allocator (`pymalloc`) optimized for tiny objects (<512 bytes), allocating memory in large blocks (Arenas). When you `del` objects, CPython marks that memory as 'free' internally for future Python objects, but it rarely releases the physical memory block back to the Operating System unless the entire 256KB Arena is completely empty. This causes high apparent OS RAM usage despite a low internal object count.",
 ["CPython uses a custom allocator (`pymalloc`) that pools memory into Arenas", "Deleted objects are marked free internally, but not immediately returned to the OS", "OS RAM stays high until the entire Arena is completely empty (Fragmentation)"],
 ["Memory fragmentation means the RAM stick physically snapped in half"]),

("PY_MEM", "implement", "easy", "implementation", ["Profiling"],
 "What built-in module would you use to trace memory allocations and find exactly which line of Python code is consuming the most RAM?",
 "You would use the built-in `tracemalloc` module. It allows you to take snapshots of memory allocation at different times and compare them, pinpointing the exact file and line number responsible for massive allocations or memory leaks.",
 ["The built-in `tracemalloc` module", "Takes snapshots of memory allocation", "Pinpoints exact line numbers causing allocations or leaks"],
 ["Microsoft Excel"]),

("PY_MEM", "scenario", "medium", "scenario", ["Memory Limits"],
 "You read a massive 10GB CSV file in Python using `data = file.read().splitlines()`. The server crashes with a MemoryError. How do you rewrite this code to process the file using near-zero memory?",
 "The `read().splitlines()` method loads the entire 10GB file into RAM simultaneously as a massive list of strings. To fix this, you must process the file lazily as a generator. You rewrite the code to iterate directly over the file object (e.g., `for line in file:`), which reads, yields, and discards exactly one line at a time, consuming mere kilobytes of RAM.",
 ["`read().splitlines()` loads the entire 10GB file into RAM at once", "Rewrite to iterate directly over the file: `for line in file:`", "Lazily yields one line at a time, keeping RAM footprint near zero"],
 ["Buy a 128GB RAM upgrade for the server"]),

("PY_MEM", "debug", "hard", "debugging", ["Object Lifecycle"],
 "You define a class with a finalizer `__del__(self)`. When instances of this class are involved in a circular reference, earlier versions of Python refused to garbage collect them, causing an unresolvable leak. Why does `__del__` complicate cyclic garbage collection?",
 "When two objects point to each other and both have `__del__` finalizers, the Garbage Collector cannot determine a safe order to destroy them. If it calls A's finalizer first, A might try to access B, but B might already be in an unstable state. Prior to Python 3.4, the GC just gave up and placed them in `gc.garbage`. Python 3.4+ (PEP 442) fixed this by running finalizers before tearing down the cycle.",
 ["The GC cannot determine a safe destruction order when both objects have finalizers", "Object A's finalizer might try to access Object B during teardown", "Python 3.4+ fixed this (PEP 442) by executing finalizers prior to breaking the reference links"],
 ["`__del__` deletes the Python interpreter from the hard drive"]),

# ---------------- PY_OOP_ADV ----------------
("PY_OOP_ADV", "fundamentals", "medium", "concept", ["Metaclasses"],
 "What is a Python Metaclass, and what is its primary use case?",
 "A metaclass is essentially the 'class of a class'. Just as a class defines the behavior of its instances, a metaclass defines the behavior of the class itself. It intercepts class creation at import time. Metaclasses are primarily used in frameworks (like Django ORM) to automatically register classes, enforce API contracts, or dynamically inject methods into subclasses before instantiation.",
 ["A metaclass is the class of a class; it defines how a class is constructed", "Intercepts class creation at import time", "Used by frameworks for auto-registration, API enforcement, or dynamic method injection"],
 ["It is a class that exists only in the Metaverse"]),

("PY_OOP_ADV", "implement", "medium", "implementation", ["Context Managers"],
 "You want to execute setup code before a block runs, and teardown code (like closing a network socket) unconditionally after the block finishes, even if an exception occurs. What OOP construct do you implement?",
 "You implement a Context Manager. You do this by defining a class with `__enter__(self)` (for the setup code) and `__exit__(self, exc_type, exc_val, traceback)` (for the guaranteed teardown code). The object is then invoked using the `with` statement, guaranteeing the cleanup executes regardless of exceptions.",
 ["Implement a Context Manager", "Define `__enter__` for setup and `__exit__` for guaranteed teardown", "Invoked using the `with` statement"],
 ["Write a global try/except block around the entire application"]),

("PY_OOP_ADV", "explain", "hard", "concept", ["Descriptors"],
 "Explain the Python Descriptor protocol. What specific dunder methods must a class implement to become a descriptor, and what is a real-world example of this in the standard library?",
 "The Descriptor protocol allows a class to control how its attributes are accessed, set, or deleted. A class becomes a descriptor by implementing `__get__`, `__set__`, or `__delete__`. When assigned as a class attribute, Python routes access to these methods. Real-world examples include the `@property` decorator, `@classmethod`, and `@staticmethod`, which are all implemented using descriptors under the hood.",
 ["Allows a class to control the access, mutation, or deletion of attributes", "Must implement `__get__`, `__set__`, or `__delete__`", "Underpins standard features like `@property`, `@classmethod`, and `@staticmethod`"],
 ["A descriptor is a string that describes what a class does"]),

("PY_OOP_ADV", "tradeoff", "medium", "tradeoff", ["Design Patterns"],
 "What are the tradeoffs between using standard Class Inheritance (subclassing) versus Composition when designing complex Python objects?",
 "Inheritance provides immediate, automatic method reuse, but creates rigid, fragile hierarchies (tight coupling) and complex Method Resolution Order (MRO) issues. Composition provides massive flexibility by injecting behavior dependencies at runtime (loose coupling) and avoiding deep hierarchies, but requires explicitly writing delegation methods to pass calls to the composed objects.",
 ["Inheritance: Automatic reuse, but causes rigid hierarchies, tight coupling, and MRO complexity", "Composition: Massive flexibility, loose coupling, dependency injection", "Composition: Requires boilerplate to explicitly delegate method calls"],
 ["Inheritance costs money, Composition is free"]),

("PY_OOP_ADV", "debug", "medium", "debugging", ["Class Attributes"],
 "You define a Python class with a class attribute `config = {}`. You create two instances, `a` and `b`. You execute `a.config['timeout'] = 10`. You then inspect `b.config['timeout']` and it is also 10. Why did modifying `a` affect `b`, and how do you fix it?",
 "Because `config` was defined at the class level, it is a shared mutable object belonging to the class itself, not the instances. Modifying the dictionary via instance `a` mutates the single shared object, affecting all instances. To fix it, you must define `self.config = {}` inside the `__init__` method, creating a unique instance-level dictionary for every object.",
 ["Class attributes are shared across all instances of the class", "Dictionaries are mutable; mutating it via `a` changes the shared object seen by `b`", "Fix by defining `self.config = {}` inside `__init__` for instance-level isolation"],
 ["Python's quantum entanglement linked the two variables"]),

("PY_OOP_ADV", "scenario", "hard", "scenario", ["Multiple Inheritance"],
 "You use Multiple Inheritance: `class D(B, C): pass`. Both `B` and `C` define a method named `process()`. When you call `d.process()`, which method executes, and what internal Python algorithm decides this?",
 "`B.process()` will execute. Python resolves method calls in multiple inheritance using the Method Resolution Order (MRO). The MRO is calculated using the C3 Linearization algorithm, which searches from bottom to top, left to right. Since `B` is listed first in the inheritance tuple `(B, C)`, the MRO places `B` before `C`, and its method is executed.",
 ["`B.process()` executes", "Determined by the Method Resolution Order (MRO)", "MRO uses C3 Linearization to search bottom-to-top, left-to-right (respecting inheritance tuple order)"],
 ["It runs both methods simultaneously in parallel threads"]),

("PY_OOP_ADV", "implement", "easy", "implementation", ["Properties"],
 "How do you implement a strictly Read-Only attribute on a Python class that calculates its value dynamically when accessed?",
 "You define a method that calculates the value and decorate it with the built-in `@property` decorator. As long as you do not define a corresponding `@attribute.setter` method, any attempt to overwrite the value directly will raise an `AttributeError`, making it strictly read-only.",
 ["Define a method and decorate it with `@property`", "Do not define a corresponding `@name.setter` method", "Attempts to mutate it will throw an AttributeError"],
 ["Use `readonly = True` in the constructor"]),

("PY_OOP_ADV", "explain", "medium", "concept", ["Super"],
 "What is the `super()` function actually doing in Python, and why is it essential in Multiple Inheritance?",
 "`super()` dynamically delegates method calls to the next class in the object's Method Resolution Order (MRO). It does not simply call the 'parent'. In complex multiple inheritance topologies (diamond patterns), `super()` guarantees that all sibling and parent classes in the MRO are initialized exactly once, in the correct deterministic order, preventing duplicate calls.",
 ["Dynamically delegates method calls to the next class in the MRO", "Does not strictly mean 'parent' in multiple inheritance", "Guarantees all classes in a diamond pattern are initialized exactly once in order"],
 ["It makes the class a 'Super Class' with extra CPU privileges"]),

("PY_OOP_ADV", "scenario", "medium", "scenario", ["Abstract Classes"],
 "You want to restrict users from directly instantiating a base class `AbstractWorker`. You want it to strictly enforce that all subclasses implement a `run()` method. How do you enforce this at the language level?",
 "You inherit the class from `abc.ABC` (Abstract Base Class) and decorate the required `run` method with `@abc.abstractmethod`. If a user tries to instantiate `AbstractWorker` directly, or instantiates a subclass that failed to override `run()`, Python will immediately throw a `TypeError` at instantiation time.",
 ["Inherit the base class from `abc.ABC`", "Decorate the required method with `@abc.abstractmethod`", "Throws a `TypeError` on instantiation if the method is not implemented"],
 ["Send an angry email to developers who don't follow the rules"]),

("PY_OOP_ADV", "tradeoff", "hard", "tradeoff", ["Dataclasses"],
 "What are the tradeoffs of using Python's `@dataclass` versus manually defining `__init__`, `__repr__`, and `__eq__` methods?",
 "Dataclasses eliminate immense amounts of boilerplate code, natively enforce type hinting, and auto-generate efficient dunder methods. However, they add a slight performance overhead at class creation (import time), they heavily obscure the initialization signature (making IDE introspection sometimes struggle), and their strict automatic behavior can complicate complex multiple-inheritance hierarchies compared to explicit manual methods.",
 ["Eliminates boilerplate and auto-generates efficient dunder methods (`__init__`, `__repr__`)", "Adds slight performance overhead at class creation (import time)", "Can obscure the signature and complicate complex multiple inheritance"],
 ["Dataclasses automatically store their data in an SQL database"]),

# ---------------- PY_DEBUG ----------------
("PY_DEBUG", "fundamentals", "easy", "concept", ["Profiling"],
 "What is the difference between `cProfile` and `timeit` when profiling Python code?",
 "`cProfile` provides deterministic profiling of an entire application, showing exactly how many times every function was called and total time spent in each. `timeit` is a micro-benchmarking tool used to repeatedly execute a tiny snippet of code (thousands of times) to find its exact execution average, ignoring application context.",
 ["`cProfile`: Deterministic profiler for entire applications (tracks call counts and total time)", "`timeit`: Micro-benchmarking tool for timing tiny snippets repeatedly", "cProfile provides macro context, timeit provides micro precision"],
 ["cProfile is for C code, timeit is for Python code"]),

("PY_DEBUG", "scenario", "medium", "scenario", ["Performance Monitoring"],
 "Your production Python web server sporadically hangs for 5 seconds every hour. You suspect a specific function is running slowly, but you cannot reproduce it locally. How can you safely inject a timing mechanism in production to log the duration of specific function calls?",
 "You can implement a custom Python decorator. The decorator records `start = time.perf_counter()` before executing the function, and `duration = time.perf_counter() - start` after it returns. If the duration exceeds a threshold (e.g., 1 second), it writes the duration and function name to the application's central logging system for diagnosis.",
 ["Implement a custom timing decorator", "Use `time.perf_counter()` before and after the function execution", "Log the delta to the central logging system if it exceeds a threshold"],
 ["Stand next to the server with a stopwatch"]),

("PY_DEBUG", "debug", "hard", "debugging", ["Recursion Limits"],
 "A Python application crashes with a `RecursionError: maximum recursion depth exceeded`. You increase `sys.setrecursionlimit()` to 100,000 to fix it. The application now abruptly crashes with a segmentation fault (C-level crash) instead of a Python traceback. Why did this happen?",
 "Python's recursion limit exists to protect the underlying C stack of the host operating system. By artificially increasing it to a massive number, the Python interpreter bypassed its safety check, allowing deep recursion to physically overflow the underlying C thread stack. This causes a catastrophic OS-level memory violation (Segmentation Fault), instantly killing the process without a Python traceback.",
 ["Python's recursion limit protects the underlying C-level thread stack", "Wildly increasing the limit bypasses this safety mechanism", "Deep recursion overflows the C stack, causing a hard OS-level Segmentation Fault"],
 ["The CPU couldn't count to 100,000 fast enough"]),

("PY_DEBUG", "tradeoff", "medium", "tradeoff", ["Profiling Tools"],
 "What are the tradeoffs of using a statistical profiler (like `py-spy` or `Austin`) versus a deterministic profiler (like `cProfile`) in a production Python environment?",
 "Deterministic profilers (`cProfile`) inject hooks into every single function call. This provides 100% exact call counts but introduces massive execution overhead (up to 50% slowdown), ruining production performance. Statistical profilers (`py-spy`) do not modify execution; they sample the call stack from the outside at a fixed rate (e.g., 100Hz). This provides near-zero overhead suitable for live production, but sacrifices exact call counts.",
 ["Deterministic (`cProfile`): 100% exact metrics, but massive overhead (unsuitable for production)", "Statistical (`py-spy`): Samples the stack externally, providing near-zero overhead", "Statistical sacrifices exact function call counts for production safety"],
 ["Statistical profilers guess the code, Deterministic profilers read the code"]),

("PY_DEBUG", "implement", "medium", "implementation", ["Live Diagnostics"],
 "You have a long-running script that occasionally freezes indefinitely. You want to inspect exactly what line of code it is stuck on without killing the process. What tool or signal handler can you attach to the process?",
 "You can use an external tool like `py-spy dump --pid <PID>` to instantly print the live Python call stack without modifying the code. Alternatively, you can proactively implement a signal handler (`signal.signal(signal.SIGUSR1, dump_stack)`) that uses the built-in `traceback` module to print the current execution frame whenever you send a USR1 kill signal to the process.",
 ["Use an external sampling tool like `py-spy dump` to read the stack", "Proactively implement a signal handler (e.g., `SIGUSR1`)", "Use the `traceback` module in the handler to print the live execution frame"],
 ["Shake the server rack to unfreeze the process"]),

("PY_DEBUG", "explain", "medium", "concept", ["Time Metrics"],
 "What is the difference between CPU Time and Wall Clock Time when profiling a Python application?",
 "Wall Clock Time is the actual physical time that elapsed in the real world from start to finish, including all time spent sleeping, waiting for network I/O, or blocked by locks. CPU Time strictly measures the exact amount of time the processor spent actively executing computational instructions for that specific process, entirely ignoring I/O wait times.",
 ["Wall Clock Time: Actual physical elapsed time (includes I/O, sleep, and locks)", "CPU Time: Exact processor time spent actively executing computational instructions", "A network request might have 5s Wall Clock time but only 0.01s CPU time"],
 ["Wall Clock time is measured by a clock on the wall, CPU time is measured by a watch"]),

("PY_DEBUG", "scenario", "hard", "scenario", ["Memory Profiling"],
 "A memory leak in your Django application only occurs when a specific rare API endpoint is hit. You use `tracemalloc`, but the logs are too noisy to find the leak. How do you specifically isolate the memory delta of just that one endpoint request?",
 "You must bracket the specific endpoint logic. You take a `tracemalloc.take_snapshot()` exactly at the start of the Django view/request, and another snapshot exactly at the end. You then use `snapshot_end.compare_to(snapshot_start, 'lineno')`. This isolates and displays exactly which lines of code allocated new memory strictly during that specific time window, ignoring global background noise.",
 ["Bracket the specific endpoint logic with `tracemalloc.take_snapshot()`", "Take one snapshot at the start of the request, and one at the end", "Use `compare_to('lineno')` to isolate the exact allocations that occurred in that window"],
 ["Take a photo of the RAM stick before and after the request"]),

("PY_DEBUG", "fundamentals", "easy", "concept", ["Interactive Debugging"],
 "What built-in Python module provides a read-eval-print loop (REPL) that allows you to interactively step through your code line-by-line, inspect variables, and evaluate expressions during runtime debugging?",
 "The built-in `pdb` (Python Debugger) module provides this. You invoke it by inserting `import pdb; pdb.set_trace()` (or simply `breakpoint()` in Python 3.7+) into your code, which halts execution and drops you into the interactive debugging REPL.",
 ["The built-in `pdb` (Python Debugger) module", "Invoked via `breakpoint()` or `pdb.set_trace()`", "Halts execution and opens an interactive stepping REPL"],
 ["The matrix module"]),

("PY_DEBUG", "implement", "medium", "implementation", ["Secrets Management"],
 "You need to securely store and access an API key in a Python application. You must ensure it is not hardcoded in the source code. How do you accomplish this in a standard production environment?",
 "You store the API key as an Environment Variable in the host operating system, Docker container, or CI/CD secrets manager. Inside the Python application, you access it securely using `os.getenv('API_KEY')` or `os.environ['API_KEY']`, ensuring the secret never enters version control.",
 ["Store the key as an Environment Variable in the OS / Docker container", "Access it in Python using `os.getenv('API_KEY')`", "Prevents secrets from being hardcoded or committed to version control"],
 ["Write it on a post-it note and stick it to the monitor"]),

("PY_DEBUG", "tradeoff", "hard", "tradeoff", ["Debugging Approaches"],
 "When debugging an elusive concurrency bug, what are the tradeoffs of inserting `print()` statements (or logging) versus attaching a step-through debugger like `pdb`?",
 "A step-through debugger (`pdb`) pauses the entire process, allowing perfect variable introspection. However, pausing instantly alters thread timing, completely masking or artificially resolving race conditions (the 'Heisenbug' effect). Print statements and logging do not pause the program, preserving real-world concurrent timing and exposing race conditions, but they introduce slight I/O overhead and cannot inspect state interactively.",
 ["Debugger (`pdb`): Pauses process, allowing perfect introspection, but alters timing", "Debugger masks race conditions (Heisenbug effect) by pausing threads", "Print/Logging: Preserves real-world concurrent timing to expose race conditions, but lacks interactive state inspection"],
 ["Print statements run on the GPU, pdb runs on the CPU"])
]
