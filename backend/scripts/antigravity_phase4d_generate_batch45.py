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

ROLE = "Python Developer"
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
    # Bucket 1: C EXTENSIONS / NATIVE BOUNDARIES
    ("B1", "optimize", "hard", "optimize", ["C Extensions"], "A C extension performs a long-running, pure-mathematical array calculation, but you notice that other Python threads are completely starved of execution time while it runs. How do you fix this at the C level?", "The C extension is holding the Global Interpreter Lock (GIL) during the entire mathematical calculation, preventing any other Python thread from executing. Since the calculation does not interact with Python objects, you should wrap the long-running C code in `Py_BEGIN_ALLOW_THREADS` and `Py_END_ALLOW_THREADS` macros to release the GIL, allowing concurrent execution of Python threads.", ["Holding the GIL during native calculations", "Use Py_BEGIN_ALLOW_THREADS to release the GIL", "Other Python threads can run concurrently"], ["Use multiprocessing instead"]),
    ("B1", "diagnose", "hard", "debugging", ["C Extensions"], "A Python application using a custom C extension leaks memory rapidly. The C code creates a new Python dictionary using `PyDict_New()`, populates it, and returns it to Python. Why is it leaking, and how do you fix it?", "When `PyDict_New()` is called, it returns a new reference with a refcount of 1. If the C code returns this dictionary directly to Python, Python assumes ownership and will decrement the refcount when it goes out of scope. However, if the C code populates the dictionary using functions that return *new* references for the keys/values, those internal references might leak if `Py_DECREF` isn't called on them after insertion into the dict.", ["PyDict_New creates a new reference", "Values/keys inserted might also hold new references", "Must explicitly call Py_DECREF on keys/values after insertion"], ["The dictionary is too large"]),
    ("B1", "compare", "medium", "compare", ["C Extensions"], "When working with the CPython C API, what is the critical difference between a 'Borrowed Reference' and a 'New Reference' regarding object lifecycle management?", "A 'New Reference' means the C extension owns a reference to the object and is explicitly responsible for calling `Py_DECREF()` when finished to prevent a memory leak. A 'Borrowed Reference' (often returned by functions like `PyTuple_GetItem`) means the C code does not own the reference and should not call `Py_DECREF()`. If the original owner destroys the object, the borrowed reference becomes a dangling pointer.", ["New Reference requires explicit Py_DECREF to prevent leaks", "Borrowed Reference requires no cleanup", "Borrowed references can become dangling pointers if the owner frees them"], ["Borrowed references are stored on the disk"]),
    ("B1", "architecture", "medium", "architecture", ["CPython Internals"], "You need to pass a massive 1GB `bytes` object from Python to a C extension for processing, and you want to ensure zero-copy memory access to avoid doubling memory usage. How do you achieve this?", "You should use the CPython Buffer Protocol. In the Python layer, you can use `memoryview()` to expose the memory of the `bytes` object. In the C extension, you parse the argument using the `y*` or `w*` format string with `PyArg_ParseTuple`, which fills a `Py_buffer` struct. This gives the C code a direct pointer to the underlying raw memory bytes without copying the 1GB payload.", ["Use the CPython Buffer Protocol", "Parse arguments into a Py_buffer struct", "Provides direct pointer access without copying memory"], ["Pass it as a string and cast it to char*"]),
    ("B1", "tradeoff", "medium", "tradeoff", ["Cython"], "What is the performance difference between using `def`, `cdef`, and `cpdef` when defining functions in Cython?", "`def` creates a standard Python function with full Python overhead and dynamic typing. `cdef` creates a pure C function that is extremely fast and can bypass the GIL, but it cannot be called directly from Python code. `cpdef` creates both a C-level function for fast internal Cython calls and a Python wrapper so it can be called from standard Python scripts, offering a compromise between speed and interoperability.", ["def: Standard Python function overhead", "cdef: Pure C function, extremely fast, cannot be called from Python", "cpdef: Generates both C and Python interfaces for flexibility"], ["They all compile to the exact same assembly"]),
    ("B1", "diagnose", "hard", "debugging", ["C Extensions"], "A C extension throws a C-level exception internally (e.g., division by zero or a failed malloc). If it simply returns `NULL` to the Python interpreter, what happens to the Python application?", "If a C extension returns `NULL` but fails to set a Python exception explicitly (e.g., using `PyErr_SetString`), the CPython interpreter enters an inconsistent state. The next time the interpreter checks for an error or executes Python code, it will trigger a fatal `SystemError: error return without exception set` and crash the application.", ["Returning NULL signals an error to CPython", "Failing to set PyErr_SetString leaves interpreter inconsistent", "Causes a fatal SystemError crash"], ["It silently ignores the error"]),
    ("B1", "architecture", "hard", "architecture", ["C Extensions"], "You are building a custom C extension that utilizes multiple native OS threads internally. Before these native threads can safely interact with Python objects or call Python APIs, what strict requirement must they fulfill?", "Native OS threads created outside of CPython must explicitly acquire the Global Interpreter Lock (GIL) before interacting with any Python objects. They must first ensure they have a valid Python thread state by calling `PyGILState_Ensure()`. After completing their Python interaction, they must release it using `PyGILState_Release()`. Failing to acquire the GIL will cause immediate memory corruption or Segmentation Faults.", ["Must acquire the Global Interpreter Lock (GIL)", "Call PyGILState_Ensure() before interacting with Python APIs", "Call PyGILState_Release() when done"], ["They just need to use thread-safe data structures"]),
    ("B1", "compare", "medium", "compare", ["Python Performance"], "Compare the architectural tradeoffs of interacting with a native C library using `ctypes` versus writing a dedicated CPython C extension module.", "`ctypes` allows calling C libraries directly from pure Python without requiring a C compiler during installation, making distribution much easier. However, `ctypes` has a very high call overhead because it dynamically constructs C data types and handles FFI at runtime. A dedicated C extension requires a C compiler and build step (e.g., `setuptools`), but the execution and type-conversion overhead is dramatically lower, making it far superior for high-frequency calls.", ["ctypes requires no C compiler, easier distribution", "ctypes has high FFI call overhead", "C extensions are much faster for high-frequency calls but harder to build/distribute"], ["ctypes is faster because it bypasses the interpreter"]),
    ("B1", "scenario", "medium", "scenario", ["C Extensions"], "You are passing a Python `list` to a C extension, and the C code iterates through it using `PyList_GetItem`. If the C code stores one of the list items in a global C struct for later use, what memory bug have you introduced?", "`PyList_GetItem` returns a *borrowed reference*. The C extension does not own this object. If the Python application later removes that item from the list, Python's Garbage Collector will destroy the object. The C struct now holds a dangling pointer. To fix this, the C code must explicitly call `Py_INCREF()` on the borrowed item before storing it, and `Py_DECREF()` when it is eventually removed from the C struct.", ["PyList_GetItem returns a borrowed reference", "Storing it globally creates a dangling pointer if Python deletes the object", "Must explicitly Py_INCREF the object to claim ownership"], ["Lists in Python cannot be passed to C"]),
    ("B1", "diagnose", "hard", "debugging", ["CPython Internals"], "During a production incident, a Python process crashes abruptly with a Segmentation Fault (SIGSEGV). There is no Python traceback. Walk through the methodology to identify the exact line of code in the C extension causing the crash.", "A Segmentation Fault bypasses the Python interpreter's exception handling completely. You must capture a core dump of the crashed process. You then load the core dump into `gdb` (`gdb python core`). By running the `bt` (backtrace) command, you can view the C-level call stack. If the C extension was compiled with debug symbols (`-g`), `gdb` will show the exact C file and line number where the illegal memory access occurred.", ["Enable core dumps on the OS", "Load the core dump into gdb", "Run a C-level backtrace (bt) to find the offending C line"], ["Just read the Python logs"]),
    ("B1", "architecture", "medium", "architecture", ["C Extensions"], "What is the `Py_LIMITED_API` (Stable ABI) in CPython, and why would a library maintainer choose to compile their C extension using it?", "Normally, a C extension is tightly coupled to the exact minor version of CPython it was compiled against (e.g., Python 3.9). A new binary wheel must be built for Python 3.10, 3.11, etc. By defining `Py_LIMITED_API`, the extension restricts itself to a stable subset of the C API. This guarantees ABI (Application Binary Interface) compatibility across all future Python 3.x versions, meaning the maintainer only needs to build and distribute a single binary wheel.", ["Restricts extension to a stable subset of the C API", "Guarantees ABI compatibility across Python minor versions", "Allows distributing a single binary wheel for all future Python 3.x versions"], ["It makes the extension run faster"]),
    ("B1", "scenario", "hard", "scenario", ["C Extensions"], "A C extension defines a static global variable to cache some data. The module works perfectly in testing, but when deployed into a multi-tenant environment using sub-interpreters (like mod_wsgi or some modern testing frameworks), it starts returning corrupted data. Why?", "Static global variables in C are shared across the entire OS process. Python Sub-interpreters run within the same OS process but are completely isolated Python environments. If a C extension relies on global C state, that state bleeds across sub-interpreters, causing race conditions and corruption. To support sub-interpreters properly, C extensions must store their state dynamically on the module object itself (using PEP 3121 / PEP 489 module state APIs).", ["Static C variables are process-global", "Sub-interpreters share the same process but expect isolated state", "Global state bleeds across sub-interpreters causing corruption"], ["Sub-interpreters don't support C extensions"]),
    ("B1", "diagnose", "medium", "debugging", ["C Extensions"], "You use `sys.getrefcount(obj)` on a Python object before passing it to a C extension, and it returns 2. After returning from the C extension, it returns 3, even though you didn't assign the object to any new Python variables. What does this indicate?", "This strongly indicates a Reference Leak in the C extension. The C code likely called `Py_INCREF(obj)` (or used a function that returns a new reference) but forgot to call the corresponding `Py_DECREF(obj)` before returning execution back to Python. Because the reference count is artificially elevated, the Python Garbage Collector will never be able to destroy this object, resulting in a permanent memory leak.", ["Indicates a Reference Leak in the C extension", "C code called Py_INCREF but forgot Py_DECREF", "Object will never be Garbage Collected"], ["The object was cached by the OS"]),
    ("B1", "tradeoff", "easy", "tradeoff", ["C Extensions"], "When optimizing Python code, what is the primary tradeoff of rewriting a hot loop into a C extension versus using a JIT compiler like PyPy?", "Rewriting into a C extension allows for extreme, deterministic optimization and fine-grained memory/GIL control, but it requires maintaining C code, managing memory manually, and building OS-specific binary wheels. Using PyPy requires zero code changes and achieves massive speedups automatically via its JIT, but PyPy introduces significant memory overhead, has slower startup times, and historically struggles with compatibility for complex C-based libraries (like pandas/numpy).", ["C extensions require manual memory management and binary builds", "PyPy requires zero code changes but uses more memory", "PyPy can have compatibility issues with existing C extensions"], ["PyPy compiles code to JavaScript"]),
    ("B1", "explain", "medium", "concept", ["CPython Internals"], "What is the difference in memory lifecycle between using `PyMem_Malloc` versus standard C `malloc` within a CPython extension?", "Standard C `malloc` requests memory directly from the operating system's standard C library allocator. `PyMem_Malloc` integrates with CPython's internal memory management system (pymalloc). This ensures the memory is tracked by Python, benefits from Python's fast object pooling/arenas for small allocations, and guarantees that the memory allocation respects Python's memory limits and debugging hooks (like tracemalloc).", ["PyMem_Malloc integrates with CPython's internal allocator (pymalloc)", "Benefits from fast object pooling for small allocations", "Standard malloc bypasses Python's tracking and pooling"], ["PyMem_Malloc is garbage collected automatically"]),

    # Bucket 2: ASYNCIO INTERNALS
    ("B2", "diagnose", "hard", "debugging", ["Asyncio"], "An asyncio web server is handling 500 requests per second. One specific endpoint calculates the SHA-256 hash of a massive 1GB string synchronously. What happens to the other 499 concurrent requests while this hash is being calculated?", "They will completely freeze. Asyncio uses cooperative multitasking on a single thread. The synchronous SHA-256 calculation blocks the entire OS thread, causing 'Event Loop Starvation'. No other coroutines, callbacks, or network I/O can be processed until the blocking calculation finishes and yields control back to the event loop. The calculation must be offloaded to a process pool using `run_in_executor`.", ["Event Loop Starvation", "Synchronous calculation blocks the single asyncio thread", "Must offload CPU-bound work using run_in_executor"], ["Asyncio automatically spawns a new thread for the other requests"]),
    ("B2", "architecture", "medium", "architecture", ["Asyncio"], "In Python 3.11+, how does the `TaskGroup` architecture structurally improve upon the older `asyncio.gather()` method regarding error handling and cancellation?", "A `TaskGroup` enforces Structured Concurrency. If you launch multiple tasks inside an `async with TaskGroup() as tg:` block and one task raises an exception, the `TaskGroup` automatically and immediately cancels all other sibling tasks in that group. It then waits for them to exit before raising an `ExceptionGroup`. `asyncio.gather()` lacks this native sibling cancellation; if one task fails, the others continue running silently as orphans unless explicitly managed.", ["TaskGroup enforces Structured Concurrency", "Automatically cancels sibling tasks if one fails", "Raises an ExceptionGroup"], ["TaskGroup runs in multiple threads"]),
    ("B2", "scenario", "hard", "scenario", ["Asyncio"], "You have an asyncio Task downloading a file. The main routine calls `task.cancel()`. However, the task completely ignores the cancellation and continues running to completion. Why might an asyncio task fail to cancel?", "Cancellation in asyncio is cooperative. Calling `task.cancel()` simply injects an `asyncio.CancelledError` into the coroutine at its next `await` point. If the task is currently executing a blocking synchronous operation, or if it catches the `CancelledError` via a bare `except Exception:` block and fails to re-raise it, the cancellation is effectively swallowed, and the task will continue running.", ["Cancellation injects CancelledError at the next await point", "Swallowed by bare except blocks that don't re-raise", "Blocked by synchronous I/O preventing the await point"], ["Tasks cannot be canceled in Python"]),
    ("B2", "compare", "medium", "compare", ["Asyncio"], "What is the functional difference between `await coroutine()` and `asyncio.create_task(coroutine())`?", "`await coroutine()` executes the coroutine sequentially; the current function halts execution and waits for the coroutine to finish before moving to the next line. `asyncio.create_task(coroutine())` schedules the coroutine to run concurrently on the event loop in the background. It returns immediately, allowing the current function to continue executing other code while the task runs concurrently.", ["await executes sequentially and blocks the current function", "create_task schedules it concurrently in the background", "create_task returns immediately"], ["They do the exact same thing"]),
    ("B2", "architecture", "medium", "architecture", ["Asyncio"], "You want to implement a hard 5-second timeout on a critical database query in asyncio using `asyncio.wait_for(query(), timeout=5)`. If the timeout is reached, what exactly happens to the underlying `query()` coroutine?", "When the timeout expires, `asyncio.wait_for` explicitly calls `.cancel()` on the underlying `query()` task. This injects a `CancelledError` into the query. The database library will catch this error, gracefully clean up its network socket and resources, and then `wait_for` raises a `TimeoutError` to the caller. This ensures no resources are leaked in the background.", ["wait_for explicitly calls .cancel() on the underlying task", "Injects CancelledError to allow graceful cleanup", "Raises TimeoutError to the caller"], ["The query continues running invisibly in the background"]),
    ("B2", "diagnose", "medium", "debugging", ["Asyncio"], "You see a warning in your production logs: `Task was destroyed but it is pending!`. What architectural mistake causes this asyncio warning?", "This happens when you create an asyncio Task (e.g., via `create_task`) but you do not hold a strong reference to it, and you never `await` it. If the function exits, Python's Garbage Collector might destroy the Task object while the underlying coroutine is still queued or executing in the event loop. To fix it, you must store the Task in a global/class-level set to preserve a strong reference until it completes.", ["Task object is Garbage Collected while still pending", "Caused by failing to hold a strong reference to the Task", "Must store fire-and-forget tasks in a Set"], ["The event loop crashed"]),
    ("B2", "scenario", "medium", "scenario", ["Asyncio"], "You write an async generator to stream data from a database: `async for row in db_stream():`. If the consumer breaks out of the loop early (`break`), how does the async generator know to close the database connection?", "When the consumer `break`s out of the loop, the async generator object goes out of scope and is Garbage Collected. The Python runtime triggers the generator's `__del__` method, which injects a `GeneratorExit` exception into the generator. The async generator must use a `try...finally` block (or `async with` context manager) to catch the exit and gracefully close the database connection.", ["Garbage Collection triggers the generator's cleanup", "Injects a GeneratorExit exception into the generator", "Must use try...finally to ensure cleanup executes"], ["The database connection remains open permanently"]),
    ("B2", "tradeoff", "hard", "tradeoff", ["Asyncio"], "What is the tradeoff of using `asyncio.shield(task)` to protect a database write from being canceled during an HTTP request timeout?", "`asyncio.shield()` protects the inner task from receiving a cancellation signal if the outer caller is canceled (e.g., an HTTP timeout). The tradeoff is that the outer caller still receives a `CancelledError` immediately, while the shielded task silently continues in the background as an orphan. If the shielded task fails, its exception is often lost or unhandled, requiring careful logging and error handling within the shielded task itself.", ["Outer caller still cancels immediately, inner task continues as an orphan", "Exceptions in the shielded task are easily lost", "Requires robust internal error handling within the shielded task"], ["Shield makes the task run in a separate OS thread"]),
    ("B2", "architecture", "medium", "architecture", ["Asyncio"], "In modern Python, what is the purpose of an Async Context Manager (`async with`) compared to a standard Context Manager (`with`), and what dunder methods are required?", "Standard Context Managers (`__enter__`, `__exit__`) are strictly synchronous; they cannot perform non-blocking I/O during setup or teardown. An Async Context Manager implements `__aenter__` and `__aexit__`, allowing the use of `await` inside the setup/teardown phases. This is critical for asyncio applications to safely acquire and release network connections, database transaction locks, or HTTP sessions without blocking the event loop.", ["Implements __aenter__ and __aexit__", "Allows using await during setup and teardown", "Crucial for non-blocking resource cleanup (DB connections, sockets)"], ["Async context managers run in parallel"]),
    ("B2", "explain", "easy", "concept", ["Asyncio"], "What is the primary role of the asyncio 'Event Loop'?", "The Event Loop is the core orchestrator of an asyncio application. It runs in a single thread, maintaining a queue of pending tasks and callbacks. It constantly loops, executing tasks until they hit an `await` point (yielding control), handling I/O events from the OS (like incoming network data via `select` or `epoll`), and scheduling the resumption of coroutines when their awaited I/O is ready.", ["Single-threaded orchestrator of tasks and callbacks", "Executes tasks until they yield control (await)", "Monitors OS I/O events and resumes coroutines"], ["It spawns a new thread for every function call"]),
    ("B2", "diagnose", "medium", "debugging", ["Asyncio"], "Your asyncio application makes 10,000 concurrent HTTP requests using `asyncio.gather(*requests)`. The OS crashes with a 'Too many open files' error. How do you re-architect this to limit concurrency?", "You must implement an `asyncio.Semaphore`. By initializing `sem = asyncio.Semaphore(100)`, you can wrap the HTTP request logic inside an `async with sem:` block. This ensures that no matter how many tasks are scheduled via `gather`, only 100 concurrent network sockets are open at any given time, providing natural backpressure and preventing OS resource exhaustion.", ["Use asyncio.Semaphore", "Wrap the network call inside async with sem:", "Limits the number of concurrent active tasks/sockets"], ["Use time.sleep() between requests"]),
    ("B2", "compare", "medium", "compare", ["Asyncio"], "Compare the behavior of `asyncio.wait()` and `asyncio.as_completed()` when waiting on a list of 10 tasks.", "`asyncio.wait()` returns two sets (done and pending) and can be configured to return when ALL tasks finish, or when the FIRST task finishes/fails. It does not yield results continuously. `asyncio.as_completed()` returns an iterator that yields futures exactly in the order they complete, regardless of the order they were submitted. This allows you to process individual task results immediately as they arrive while the others are still running.", ["wait() returns bulk sets based on ALL or FIRST completion", "as_completed() yields an iterator of futures as they finish", "as_completed allows immediate processing of finished tasks"], ["They are identical functions with different names"]),
    ("B2", "scenario", "hard", "scenario", ["Asyncio"], "During a graceful shutdown of an asyncio application, you call `loop.stop()`. However, several background tasks writing to the database are abruptly killed without committing. How do you properly shutdown an asyncio event loop?", "Calling `loop.stop()` halts the loop immediately, abandoning all running tasks. For a graceful shutdown, you must first gather all pending tasks using `asyncio.all_tasks()`. You then explicitly cancel them (`task.cancel()`), and run the event loop briefly using `loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))` to allow the tasks to catch the `CancelledError` and execute their `finally` blocks to commit or rollback the database.", ["loop.stop() abruptly abandons tasks", "Must collect tasks via asyncio.all_tasks() and cancel them", "Run the loop until complete to allow finally blocks to execute"], ["Just use sys.exit(0)"]),
    ("B2", "tradeoff", "medium", "tradeoff", ["Asyncio"], "What is the tradeoff of using `asyncio.to_thread()` (or ThreadPoolExecutor) to run synchronous I/O within an asyncio application?", "Using `to_thread()` prevents a blocking synchronous call from starving the main asyncio event loop, maintaining application responsiveness. However, the tradeoff is the re-introduction of OS thread overhead (context switching and memory per thread). If you offload thousands of concurrent blocking calls, you will exhaust the thread pool or OS resources, defeating the highly scalable, single-threaded purpose of asyncio.", ["Prevents blocking the main event loop", "Re-introduces heavy OS thread context switching and memory overhead", "Can exhaust the thread pool under high concurrency"], ["to_thread converts synchronous code into asynchronous code magically"]),
    ("B2", "architecture", "hard", "architecture", ["Asyncio"], "How does backpressure work in Python's `asyncio.StreamWriter`, and why is it critical when sending massive files over a slow network socket?", "If you write data to a socket faster than the network can transmit it, the OS buffer fills up. In asyncio, `StreamWriter.write()` is not an `async` function; it returns instantly, buffering the data in Python's memory. If left unchecked, this causes massive memory bloat (OOM). Backpressure is enforced by explicitly calling `await writer.drain()`. This pauses the coroutine until the underlying buffer has fallen below the high-water mark, keeping memory usage strictly bounded.", ["write() buffers synchronously in Python memory", "await writer.drain() pauses execution until the buffer drains", "Prevents memory blowup (OOM) on slow networks"], ["It automatically compresses the data"]),
    ("B2", "explain", "medium", "concept", ["Asyncio"], "What is the difference between an `asyncio.Future` and an `asyncio.Task`?", "An `asyncio.Future` is a low-level, awaitable object representing the eventual result of an asynchronous operation (similar to a Promise in JS). It does not execute any code itself; someone must manually call `future.set_result()`. An `asyncio.Task` is a subclass of `Future` that specifically wraps a coroutine. It actively schedules and drives the execution of the coroutine on the event loop until it finishes.", ["Future is a low-level container for an eventual result", "Task is a subclass of Future that wraps and drives a coroutine", "Futures are resolved manually; Tasks execute code"], ["A Task runs in a thread, a Future runs in a process"]),

    # Bucket 3: MEMORY PROFILING & PRODUCTION DIAGNOSIS
    ("B3", "diagnose", "hard", "debugging", ["Memory Profiling"], "A Python service running in Kubernetes is repeatedly OOMKilled because its RSS (Resident Set Size) grows infinitely. However, standard Python heap profilers show total Python objects plateau at 100MB. What causes this discrepancy?", "The discrepancy means the leak is occurring outside of the standard Python object heap. This is typically caused by unreleased native memory in C extensions (like pandas, numpy, or crypto libraries), severe memory fragmentation where Python's `pymalloc` cannot return memory to the OS, or unbounded thread creation (each thread stack consumes native OS memory).", ["Leak is outside the standard Python object heap", "Caused by native C extensions leaking memory", "Or caused by severe fragmentation/thread stack limits"], ["Python hides memory from profilers"]),
    ("B3", "scenario", "medium", "scenario", ["Memory Profiling"], "You need to diagnose a slow memory leak in a production Python service without crashing it. How do you use the standard library `tracemalloc` to find the exact line of code allocating the leaked memory?", "You import `tracemalloc` and start it (`tracemalloc.start()`). You take a memory snapshot at time A (`tracemalloc.take_snapshot()`), allow the application to process traffic, and take a second snapshot at time B. You then use `snapshot_b.compare_to(snapshot_a, 'lineno')` to calculate the diff. This pinpoints the exact file and line number that allocated the most memory between the two snapshots.", ["Use tracemalloc.take_snapshot()", "Take snapshots at two different times", "Compare snapshots by 'lineno' to find the exact allocation source"], ["Just print sys.getsizeof() on every object"]),
    ("B3", "tradeoff", "medium", "tradeoff", ["Memory Management"], "What is the architectural tradeoff of using `multiprocessing.set_start_method('fork')` versus `'spawn'` regarding memory consumption on Linux?", "`fork` relies on OS Copy-On-Write (CoW). The child process instantly inherits the parent's entire memory space without copying it, leading to extremely fast startup and shared memory footprint. However, as the child modifies objects (or Python updates reference counts), CoW breaks, duplicating memory. `'spawn'` starts a completely fresh Python interpreter from scratch. It is slower and uses more memory initially, but provides perfect isolation and avoids complex deadlocks with native C libraries.", ["'fork' uses Copy-on-Write for fast startup and shared memory", "CoW breaks when refcounts update, causing delayed memory duplication", "'spawn' is slower and uses more memory but is completely safe/isolated"], ["fork runs on Windows, spawn runs on Linux"]),
    ("B3", "architecture", "hard", "architecture", ["Memory Management"], "How does CPython's internal `pymalloc` allocator manage memory for small objects (under 512 bytes), and why does this sometimes prevent the OS from recovering freed memory?", "`pymalloc` allocates large OS memory chunks called 'Arenas' (256KB), subdivided into Pools, then Blocks. When small Python objects are destroyed, `pymalloc` marks the Block as free but retains the Arena. An Arena can only be returned to the OS if *every single Block* within it is free. If even one small long-lived object remains in an Arena, the entire 256KB block is pinned in memory, leading to high RSS fragmentation even if the Python heap is mostly empty.", ["pymalloc manages memory in Arenas, Pools, and Blocks", "An Arena is only returned to the OS if 100% empty", "Single long-lived objects cause fragmentation and prevent OS memory release"], ["pymalloc uses Java's Garbage Collector"]),
    ("B3", "optimize", "medium", "optimize", ["Memory Management"], "You are building a caching system and notice memory is growing infinitely because cached objects reference each other in cycles. How can you use the `weakref` module to fix this?", "The `weakref` module allows you to hold a reference to an object without incrementing its reference count. You can use a `weakref.WeakValueDictionary` for the cache. If the rest of the application destroys all strong references to an object, the weak reference is automatically cleared, and the object is garbage collected, breaking the cycle and preventing the cache from leaking memory infinitely.", ["weakref does not increment the reference count", "Use WeakValueDictionary for caches", "Objects are garbage collected when strong references disappear"], ["Use the del keyword in a loop"]),
    ("B3", "diagnose", "medium", "debugging", ["Memory Profiling"], "A data processing script reads a 10GB CSV file and crashes with an OutOfMemory error. The code looks like this: `rows = [process(line) for line in open('data.csv')]`. How do you optimize this to use minimal memory?", "The list comprehension evaluates the entire loop immediately, materializing all 10GB of processed rows into a massive list in RAM simultaneously. To fix this, change the brackets `[]` to parentheses `()` to create a Generator Expression: `rows = (process(line) for line in open('data.csv'))`. This lazily evaluates and yields one row at a time, streaming the data with a near-zero memory footprint.", ["List comprehension materializes all data in RAM simultaneously", "Use a Generator Expression by replacing brackets with parentheses", "Lazily evaluates one row at a time, minimizing memory footprint"], ["Increase the server's RAM"]),
    ("B3", "explain", "easy", "concept", ["Memory Management"], "In CPython, how does the primary Reference Counting mechanism differ from the Generational Garbage Collector?", "Reference Counting is deterministic and immediate; every object tracks how many variables point to it, and when the count hits zero, the object is instantly destroyed. However, Reference Counting cannot detect cyclic references (A points to B, B points to A). The Generational Garbage Collector is a periodic background process specifically designed to scan the heap, detect these isolated cycles, and clean them up.", ["Reference Counting is immediate when count hits zero", "Reference Counting fails on cyclic references (A->B, B->A)", "Generational GC runs periodically specifically to clean up cyclic references"], ["They are two names for the exact same system"]),
    ("B3", "optimize", "medium", "optimize", ["Memory Management"], "You have a class `Point` representing 10 million 3D coordinates. Instantiating these objects consumes massive amounts of RAM due to Python's dynamic dictionary overhead. How do you optimize the class definition to drastically reduce memory usage?", "You define `__slots__ = ['x', 'y', 'z']` inside the class. By default, every Python object creates a dynamic `__dict__` to store arbitrary instance attributes, which carries significant memory overhead. Declaring `__slots__` disables the dynamic dictionary and statically allocates exactly enough memory for the declared attributes, saving massive amounts of RAM when instantiating millions of objects.", ["Define __slots__ inside the class", "Disables the dynamic __dict__ overhead per instance", "Statically allocates memory for exact attributes only"], ["Use a tuple instead of a class"]),
    ("B3", "scenario", "medium", "scenario", ["Memory Profiling"], "You apply the `@lru_cache` decorator to a function that fetches user profiles from a database. Over the next week, the application's memory usage steadily climbs until it crashes. What caused the leak?", "The `functools.lru_cache` decorator caches function results in an internal dictionary indefinitely if no `maxsize` is specified (or if set to `None`). Because every unique user profile request was cached forever in RAM, the cache grew unbounded. You must explicitly configure `@lru_cache(maxsize=1000)` to enforce an LRU eviction policy and bound memory usage.", ["@lru_cache caches results indefinitely if maxsize is missing/None", "Causes unbounded memory growth over time", "Must configure an explicit maxsize for LRU eviction"], ["The database connection leaked"]),
    ("B3", "compare", "medium", "compare", ["Memory Management"], "Compare the limitations of using `sys.getsizeof()` versus a dedicated memory profiler like `Pympler` when analyzing complex objects.", "`sys.getsizeof()` only returns the shallow memory size of the object itself. For a list or dictionary, it returns the size of the container, but completely ignores the size of the elements contained within it. `Pympler` (specifically `asizeof`) recursively traverses the object graph, summing the size of the container and all deeply nested child objects, providing an accurate representation of total memory retained.", ["sys.getsizeof is shallow (container only)", "sys.getsizeof ignores nested child elements", "Pympler recursively traverses and sums the entire object graph"], ["sys.getsizeof is just slower"]),
    ("B3", "diagnose", "hard", "debugging", ["Memory Profiling"], "You use `gc.get_objects()` to investigate a memory leak. You notice thousands of instances of a specific class. How do you determine exactly what is keeping these objects alive in memory?", "You can use the `gc.get_referrers(obj)` function, or a visual tool like `objgraph.show_backrefs()`. These tools introspect the Garbage Collector's tracking data and output the exact chain of variables, lists, or closures that hold strong references to your leaked object, allowing you to trace the leak back to the global variable or cache causing the issue.", ["Use gc.get_referrers(obj)", "Use objgraph.show_backrefs()", "Traces the chain of variables holding strong references to the object"], ["Just delete the class"]),
    ("B3", "architecture", "medium", "architecture", ["Memory Management"], "Why is string interning crucial for Python's memory and CPU performance, and how can you manually force it?", "String interning ensures that only one copy of a specific string exists in memory. This saves RAM. More importantly, it drastically speeds up dictionary lookups (which rely heavily on strings); the interpreter can compare memory addresses (pointer equality) using `is` instead of executing a character-by-character string comparison (`==`). You can manually force interning on dynamic strings using `sys.intern(string)`.", ["Saves RAM by keeping only one copy of a string", "Speeds up dictionary lookups by allowing pointer equality checks (is vs ==)", "Use sys.intern() to manually intern strings"], ["Interning compresses the string using gzip"]),
    ("B3", "tradeoff", "hard", "tradeoff", ["Memory Profiling"], "What is the severe tradeoff of calling `gc.disable()` in a latency-critical Python trading system?", "Disabling the Generational Garbage Collector prevents the random, Stop-The-World (STW) pauses that disrupt latency-critical trading algorithms. However, the tradeoff is that cyclic reference leaks (e.g., A -> B -> A) will never be cleaned up. The application will inevitably leak memory until it crashes with an OOM. This strategy requires the developer to ensure absolutely zero cyclic references exist in the hot path, or to manually call `gc.collect()` during known idle periods.", ["Prevents random Stop-The-World GC latency pauses", "Cyclic references will never be cleaned up, leading to OOM", "Requires manual collection during idle periods"], ["gc.disable() makes the application single-threaded"]),
    ("B3", "diagnose", "medium", "debugging", ["Memory Management"], "In older versions of Python (prior to 3.4), if two objects were stuck in a reference cycle and both defined a `__del__` method, the Garbage Collector would permanently leak them. Why?", "The Garbage Collector could not determine a safe order of destruction. If it destroyed Object A first, Object A's `__del__` method might attempt to interact with Object B, which is also being destroyed. To avoid executing unsafe code, the GC threw its hands up, placed the objects in the `gc.garbage` list, and refused to collect them. (PEP 442 in Python 3.4 fixed this by finalizing objects safely).", ["GC could not determine a safe order to call __del__", "Feared __del__ would access an already destroyed object", "Placed them in gc.garbage causing a permanent leak"], ["__del__ is not supported in Python"]),
    ("B3", "scenario", "medium", "scenario", ["Production Python"], "You have a Celery worker processing massive images. The Python memory allocator fragments over time, causing the worker process RSS to hit 2GB and trigger alerts, even when idle. How do you mitigate this without fixing the CPython allocator?", "You can configure Celery with `worker_max_tasks_per_child` (e.g., set to 100). This enforces a lifecycle limit. After a worker process completes 100 tasks, the master process gracefully terminates it and forks a brand new worker process. This completely destroys the fragmented memory space, returning the RSS footprint to baseline without dropping any jobs.", ["Configure worker_max_tasks_per_child", "Gracefully kills and respawns the worker after N tasks", "Destroys the fragmented OS memory space entirely"], ["You must rewrite the app in C++"])
]

BUCKET_KEYS = {
    "B1": ("C Extensions", "CPython Internals", "CPython", ["Python Developer"]),
    "B2": ("Asyncio", "Async Concurrency", "asyncio", ["Python Developer", "Backend Developer"]),
    "B3": ("Memory Profiling", "Memory Management", "tracemalloc", ["Python Developer", "Backend Developer"]),
}

def main():
    with open(OUT, encoding="utf-8") as f:
        prior = [json.loads(l) for l in f if l.strip()]
    
    staged_q = [p["question"] for p in prior]
    staged_a = [p["expected_answer"] for p in prior]
    
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

    # I generated 46 distinct candidates in the code above (15 + 16 + 15). 
    # I need EXACTLY 50 for the batch. Let me add 4 more to B1/B2/B3.
    cands.extend([
        {
            "primary_role": ROLE,
            "applicable_roles": ["Python Developer"],
            "primary_skill": "CPython Internals",
            "secondary_skills": ["C Extensions"],
            "technology": "C API",
            "topic": "Reference Ownership",
            "category": "Software Engineering",
            "intent": "diagnose",
            "difficulty": "hard",
            "question_type": "debugging",
            "question": "A C extension uses `PyList_Append(list, item)`. Does this function steal the reference to `item`, or do you still need to call `Py_DECREF(item)` later?",
            "expected_answer": "`PyList_Append` does NOT steal the reference (unlike `PyTuple_SetItem` or `PyList_SetItem`). It increments the reference count of the item when adding it to the list. Therefore, if the C extension created `item` as a new reference (e.g. `PyLong_FromLong`), the C extension still owns the original reference and must explicitly call `Py_DECREF(item)` afterward to avoid a memory leak.",
            "evaluation_rubric": {"strong_indicators": ["PyList_Append does not steal the reference", "It increments the refcount internally", "Must call Py_DECREF if you own the original reference"], "weak_indicators": ["It steals the reference"]}
        },
        {
            "primary_role": ROLE,
            "applicable_roles": ["Python Developer"],
            "primary_skill": "Asyncio",
            "secondary_skills": ["Async Concurrency"],
            "technology": "asyncio",
            "topic": "Event Loop Internals",
            "category": "Software Engineering",
            "intent": "tradeoff",
            "difficulty": "medium",
            "question_type": "tradeoff",
            "question": "What is the architectural tradeoff of using `uvloop` instead of the standard library asyncio event loop?",
            "expected_answer": "`uvloop` is a drop-in replacement written in Cython on top of libuv (the same C library powering Node.js). The tradeoff is a massive increase in performance (2x-4x faster I/O) making Python almost as fast as Go for networking. However, `uvloop` introduces a native C dependency, does not support Windows natively, and can have edge-case incompatibilities with deeply obscure asyncio features.",
            "evaluation_rubric": {"strong_indicators": ["Written in Cython using libuv", "Massive performance increase", "Native dependency, no native Windows support"], "weak_indicators": ["uvloop is slower"]}
        },
        {
            "primary_role": ROLE,
            "applicable_roles": ["Python Developer"],
            "primary_skill": "Memory Profiling",
            "secondary_skills": ["Memory Management"],
            "technology": "tracemalloc",
            "topic": "Production Profiling",
            "category": "Software Engineering",
            "intent": "compare",
            "difficulty": "medium",
            "question_type": "compare",
            "question": "Compare the use cases for `tracemalloc` versus `cProfile` in a production Python application.",
            "expected_answer": "`cProfile` is a deterministic CPU profiler; it tracks function call counts and execution time to find CPU bottlenecks. It does not track memory. `tracemalloc` is a memory profiler built into CPython; it traces exactly where memory blocks are allocated to find memory leaks. They solve completely different problems: `cProfile` for speed/latency, `tracemalloc` for RAM growth.",
            "evaluation_rubric": {"strong_indicators": ["cProfile tracks CPU execution time/function calls", "tracemalloc tracks memory allocations", "Speed vs RAM"], "weak_indicators": ["They are the same thing"]}
        },
        {
            "primary_role": ROLE,
            "applicable_roles": ["Python Developer"],
            "primary_skill": "Memory Management",
            "secondary_skills": ["Runtime Diagnostics"],
            "technology": "Python",
            "topic": "Object Lifecycle",
            "category": "Software Engineering",
            "intent": "explain",
            "difficulty": "medium",
            "question_type": "concept",
            "question": "Explain why catching and holding onto an Exception object (or the `sys.exc_info()` traceback) in a long-lived global variable is a dangerous memory anti-pattern in Python.",
            "expected_answer": "A traceback object in Python holds a strong reference to the entire stack frame where the exception occurred. This stack frame holds references to every local variable that existed in that scope. If you persist the traceback globally, you inadvertently prevent Garbage Collection for all those local variables, causing a massive, cascading memory leak.",
            "evaluation_rubric": {"strong_indicators": ["Traceback holds references to the stack frame", "Stack frame holds references to all local variables", "Prevents garbage collection of local variables causing a leak"], "weak_indicators": ["Exceptions are just strings"]}
        }
    ])
    
    # 50 total candidates

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
        c["generation_batch"] = "batch_45_python_developer"

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
        "batch": "batch_45_python_developer",
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
    
    with open(os.path.join(REPORTS_DIR, "phase4d_batch45_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_batch45_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Phase 4D - Batch 45 (Python Developer)\n\n")
        f.write(f"- **Attempted**: {len(cands)}\n")
        f.write(f"- **Accepted**: {len(accepted)}\n")
        f.write(f"- **Rejected**: {sum(rej.values())}\n")
        f.write(f"- **Rejections**: {dict(rej)}\n\n")
        f.write("### Staging Totals\n")
        f.write(f"- **Previous Staging Total**: {len(prior)}\n")
        f.write(f"- **Final Staging Total**: {final_staging_total}\n")
        f.write(f"- **Python Developer Role Total**: {role_counts[ROLE]}\n")
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

    print(f"Successfully generated 50 Python Developer questions.")

if __name__ == "__main__":
    main()
