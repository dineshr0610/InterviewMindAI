"""Batch 33 Part 2 question content (Python Developer). Targeted Gap Generation."""

ROLE = "Python Developer"

BUCKET_KEYS = {
    "PYTHON_CONCURRENCY": ("Python Concurrency", "Threading & Multiprocessing", "Python", ["Python Developer", "Backend Developer"]),
}

Q = [
# ---------------- PYTHON_CONCURRENCY ----------------
("PYTHON_CONCURRENCY", "tradeoff", "hard", "tradeoff", ["GIL", "Multiprocessing"],
 "In Python, what is the exact tradeoff between using `threading.Thread` versus `multiprocessing.Process` for a highly CPU-bound task like image processing?",
 "Because of the Global Interpreter Lock (GIL), multiple Python threads cannot execute bytecodes simultaneously on multiple cores. Using `threading` for CPU-bound tasks yields zero gain and degrades performance due to context-switching. `multiprocessing` spawns separate OS processes, bypassing the GIL for true multi-core parallelization, at the tradeoff of high memory overhead and complex Inter-Process Communication (IPC).",
 ["GIL prevents multiple threads from executing Python bytecodes concurrently on multiple cores", "`multiprocessing` spawns separate OS processes, bypassing the GIL for true parallelism", "Tradeoff: Processes consume vastly more memory and require complex IPC (serialization)"],
 ["Threading uses strings, Multiprocessing uses integers"]),

("PYTHON_CONCURRENCY", "debug", "medium", "debugging", ["Asyncio", "Event Loop"],
 "You write an `asyncio` script to scrape 100 websites concurrently. It takes exactly as long as a synchronous script. You check the code and see a loop doing `await fetch(url)`. Why is this asynchronous code completely sequential?",
 "You are `await`ing each coroutine inside a standard `for` loop. The `await` keyword pauses execution of the current function until the coroutine finishes, preventing the loop from advancing to the next URL. To run them concurrently, you must schedule them onto the event loop simultaneously using `asyncio.gather(*tasks)` or an `asyncio.TaskGroup`.",
 ["`await` inside a `for` loop blocks the loop until the current coroutine finishes", "It forces strictly sequential execution", "Fix: Must use `asyncio.gather()` or `TaskGroup` to schedule them concurrently on the event loop"],
 ["The websites noticed you were scraping them and slowed down intentionally"]),

("PYTHON_CONCURRENCY", "implement", "medium", "implementation", ["ThreadPoolExecutor", "I/O Bound"],
 "You need to execute 1,000 independent network requests concurrently. Using `multiprocessing` crashes out of memory, and managing manual threads is complex. What high-level standard library class provides the best solution?",
 "You should use `concurrent.futures.ThreadPoolExecutor`. Threads share memory, so 1000 threads use vastly less RAM than 1000 processes. Because network requests are I/O-bound, the GIL is released while waiting for the network, making multithreading highly efficient in Python. You submit tasks to the pool and retrieve results via `as_completed()`.",
 ["Use `concurrent.futures.ThreadPoolExecutor`", "Threads share memory, avoiding the massive overhead of multiprocessing", "The GIL is released during I/O (network calls), making threads highly efficient for this"],
 ["Use `os.fork()` 1000 times in a loop"]),

("PYTHON_CONCURRENCY", "scenario", "hard", "scenario", ["Asyncio", "Blocking Event Loop"],
 "You run an `asyncio` web server. A developer adds a route that calculates a massive prime number using a standard `while` loop. Whenever a user hits this route, *all* other users on the server experience timeouts. Why?",
 "The route introduced a synchronous, CPU-bound blocking call directly onto the `asyncio` event loop. The event loop is strictly single-threaded. While the `while` loop is crunching math, the event loop cannot physically yield to process any other incoming network requests or pending coroutines, freezing the server. Heavy CPU tasks must be offloaded via `run_in_executor()`.",
 ["The synchronous `while` loop blocked the single-threaded event loop", "The event loop cannot yield to process other network requests while blocked by CPU math", "Fix: Offload CPU-bound tasks to a `ProcessPoolExecutor` using `loop.run_in_executor()`"],
 ["The prime number was too large to fit through the ethernet cable"]),

("PYTHON_CONCURRENCY", "explain", "medium", "concept", ["GIL", "Memory Management"],
 "What exactly is the Global Interpreter Lock (GIL) in CPython, and why does it exist?",
 "The GIL is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecodes at once. It exists because CPython's memory management (reference counting) is not thread-safe. If two threads incremented a reference count simultaneously, it would cause memory leaks or segfaults. It simplifies CPython but limits CPU parallelization.",
 ["A mutex preventing multiple threads from executing Python bytecodes simultaneously", "Exists because CPython's reference counting memory management is not thread-safe", "Prevents true multi-core parallelization for CPU-bound tasks in a single process"],
 ["A physical lock on the server rack that prevents developers from stealing hard drives"]),

("PYTHON_CONCURRENCY", "debug", "hard", "debugging", ["Deadlocks", "Threading"],
 "Thread A acquires Lock 1, then attempts Lock 2. Thread B acquires Lock 2, then attempts Lock 1. Both threads freeze infinitely, and CPU usage drops to 0%. What happened, and how do you prevent it?",
 "This is a classic Deadlock. The threads are trapped in a circular wait condition; neither can proceed until the other releases its lock, which will never happen. You prevent deadlocks by enforcing a strict global ordering for lock acquisition (e.g., always acquire Lock 1 before Lock 2 across all threads), or by using lock timeouts (`lock.acquire(timeout=5)`).",
 ["Classic Deadlock due to a circular wait condition", "CPU drops to 0% because the threads are indefinitely suspended waiting for a lock", "Fix: Enforce a strict global lock ordering hierarchy, or use acquisition timeouts"],
 ["The threads fell asleep and forgot what they were doing"]),

("PYTHON_CONCURRENCY", "fundamentals", "easy", "concept", ["Coroutines", "Asyncio"],
 "What is a 'Coroutine' in Python's `asyncio` framework?",
 "A coroutine is a specialized generator function, defined with `async def`, that can suspend its execution (using `await`) and yield control back to the event loop, allowing other tasks to run concurrently. It does not run in a separate thread; it runs concurrently on a single thread through cooperative multitasking.",
 ["A specialized function defined with `async def`", "Can suspend execution via `await` to yield control back to the event loop", "Runs on a single thread via cooperative multitasking (not separate OS threads)"],
 ["A subroutine that specifically deals with corporate business logic"]),

("PYTHON_CONCURRENCY", "implement", "hard", "implementation", ["Multiprocessing", "Shared State"],
 "You are using `multiprocessing` to share a large, constantly updating dictionary between a Parent and Child process. Standard dictionaries don't sync because memory is isolated. How do you implement this shared state?",
 "You must use `multiprocessing.Manager()`. A Manager creates a centralized server process that holds the actual dictionary and provides proxy objects to the Parent and Child. When either process modifies its proxy, the Manager securely handles the IPC (Inter-Process Communication) under the hood to update the central state, ensuring process-safe synchronization.",
 ["Must use `multiprocessing.Manager()`", "Creates a centralized server process that holds the actual data structure", "Provides proxy objects to workers and handles the IPC synchronization under the hood"],
 ["Save it to a JSON file on disk and hope neither overwrites the other"]),

("PYTHON_CONCURRENCY", "scenario", "medium", "scenario", ["Asyncio", "Threading Integration"],
 "You need to run a legacy synchronous database function (`db.fetch_all()`) inside a modern `async def` API endpoint without blocking the entire event loop. How do you integrate it?",
 "You must offload the synchronous function to a separate background thread. In modern `asyncio`, you use `await asyncio.to_thread(db.fetch_all)`. This runs the blocking function in a separate thread, immediately yielding control back to the main event loop so it can continue serving other async requests while waiting for the database.",
 ["Offload the blocking synchronous call to a background thread pool", "Use `await asyncio.to_thread(func)` (or `run_in_executor`)", "Yields the event loop while the background thread waits for the DB"],
 ["Just add `await` in front of the synchronous function and hope it works"]),

("PYTHON_CONCURRENCY", "tradeoff", "medium", "tradeoff", ["Asyncio", "Threading"],
 "When designing an I/O-heavy application, what is the tradeoff between `asyncio` and standard `threading`?",
 "`asyncio` is vastly more lightweight (10k coroutines use MBs of RAM; 10k threads use GBs) and context switches are faster in userspace. Tradeoff: `asyncio` forces a viral 'async all the way down' architecture; a single accidental synchronous call blocks the entire system. Threading allows standard blocking libraries safely, but has higher memory/OS overhead.",
 ["`asyncio`: Vastly lower memory footprint and faster userspace context switching", "Tradeoff: Forces viral 'async all the way down' architecture (easy to accidentally block loop)", "Threading: Higher OS memory overhead, but safely supports legacy blocking libraries"],
 ["Asyncio is for Apple computers, threading is for Windows"]),

("PYTHON_CONCURRENCY", "explain", "easy", "concept", ["Yield", "Generators"],
 "What does the `yield` keyword do in a Python function, and what does it return?",
 "The `yield` keyword pauses the function's execution, saves its internal state, and produces a value to the caller. Unlike `return` (which destroys local state), `yield` allows the function to resume exactly where it left off on the next iteration. A function containing `yield` automatically becomes a Generator, returning an iterator object.",
 ["Pauses execution, saves state, and yields a value to the caller", "Allows the function to resume exactly where it left off", "Automatically converts the function into a Generator (returning an iterator)"],
 ["It physically yields CPU processing power to another computer on the network"]),

("PYTHON_CONCURRENCY", "debug", "hard", "debugging", ["GIL", "Atomic Operations"],
 "You spawn 5 threads that append to a single Python `list`. You didn't use a `Lock`. Surprisingly, the list is perfectly intact and no data is corrupted. Why is `list.append()` seemingly thread-safe in CPython even without locks?",
 "In CPython, `list.append()` is implemented as a single, atomic C operation. Because of the Global Interpreter Lock (GIL), the CPython interpreter will not trigger a thread context switch *during* a single atomic bytecode instruction. Therefore, atomic operations (like appending or dict fetching) are inherently thread-safe. (Unlike `x += 1`, which is multiple bytecodes).",
 ["`list.append()` is a single, atomic bytecode/C operation", "The GIL prevents context switching *during* a single atomic bytecode", "Because it cannot be interrupted mid-append, it is inherently thread-safe in CPython"],
 ["The threads politely waited their turn out of respect for the developer"]),

("PYTHON_CONCURRENCY", "implement", "medium", "implementation", ["Asyncio", "Fire and Forget"],
 "You use `asyncio`. You want to execute a task in the background (like sending telemetry) but you *do not* want to `await` it and block the current function. How do you fire-and-forget an async task?",
 "You use `asyncio.create_task(coroutine())`. This schedules the coroutine to run on the event loop concurrently in the background immediately, returning a `Task` object. You can safely let the current function proceed without `await`ing the task, effectively implementing a non-blocking fire-and-forget pattern.",
 ["Use `asyncio.create_task(coroutine())`", "Schedules the coroutine onto the event loop to run in the background", "Allows the current function to proceed immediately without blocking/`await`ing"],
 ["Use `threading.Thread(target=async_func).start()`"]),

("PYTHON_CONCURRENCY", "tradeoff", "hard", "tradeoff", ["Multiprocessing", "Serialization"],
 "You use `multiprocessing.Pool(4)`. You try to pass a complex custom database connection object to the worker processes, but the code crashes with a `PicklingError`. Why does this happen, and what is the structural tradeoff?",
 "`multiprocessing` creates entirely separate OS processes. To send data to the child, Python must serialize (pickle) the object via IPC. Complex objects with open network sockets, file descriptors, or locks (like DB connections) physically cannot be serialized. Tradeoff: You must initialize unpicklable resources *inside* the child worker's init phase, rather than passing them.",
 ["Data passed to multiprocessing workers must be serialized (Pickled) for IPC transport", "Network sockets, file descriptors, and DB connections physically cannot be Pickled", "Tradeoff: Must initialize complex state *inside* the worker process, not pass it from parent"],
 ["Pickles are sour and the database connection prefers sweet data"]),

("PYTHON_CONCURRENCY", "scenario", "medium", "scenario", ["Asyncio", "Silent Failures"],
 "An `asyncio` app crashes silently, but the console prints a warning: `Task was destroyed but it is pending!`. What architectural mistake causes this obscure failure?",
 "This occurs when an async `Task` raises an unhandled exception in the background, but the main program never actually `await`s the task to retrieve its result, nor attaches a `.add_done_callback()` error handler. The exception is swallowed silently until the Garbage Collector destroys the orphaned Task object, triggering the warning.",
 ["An unhandled exception occurred inside a background `Task`", "The main program never `await`ed the task to consume the error", "The Garbage collector destroyed the orphaned task, triggering the obscure warning"],
 ["A ninja infiltrated the server and assassinated the task"]),

("PYTHON_CONCURRENCY", "fundamentals", "easy", "concept", ["Daemon Threads"],
 "In the context of Python multithreading, what is a `Daemon Thread`?",
 "A Daemon Thread is a background thread tied to the lifecycle of the main Python program. When the main program finishes execution, it immediately shuts down and violently kills any running daemon threads without waiting for them to finish. Non-daemon threads will keep the Python program alive indefinitely until they finish.",
 ["A background thread tied to the lifecycle of the main program", "When the main thread finishes, daemon threads are violently killed immediately", "They do not block the program from exiting (unlike non-daemon threads)"],
 ["A thread summoned from the underworld to execute malicious code"]),

("PYTHON_CONCURRENCY", "implement", "hard", "implementation", ["Threading", "Queues"],
 "You have a multi-threaded app. Threads write to the same log file simultaneously, causing interleaved, corrupted text. How do you safely aggregate logs from multiple threads into a single file?",
 "You use a `queue.Queue`. The `queue` module is natively thread-safe (it implements all locking internally). You create a single dedicated 'Logging Thread'. Worker threads push log strings into the shared `Queue`. The Logging Thread continuously pops items off the queue and writes them to the file sequentially, completely eliminating file descriptor race conditions.",
 ["Use a `queue.Queue`, which is natively thread-safe and handles locking internally", "Worker threads push log strings onto the shared queue", "A single dedicated Logging Thread pops items and writes them to the file sequentially"],
 ["Tell the threads to talk quietly so they don't interrupt each other"])
]
