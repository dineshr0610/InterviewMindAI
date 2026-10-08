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

ROLE = "Python Developer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Python Threading & Concurrency
    ("B63_4_1", "concept", "medium", "concept", ["Concurrency"], "Does the Global Interpreter Lock (GIL) protect your Python application from all Race Conditions when using threads?", "No. The GIL only guarantees that CPython's *internal* structures (like the reference count integer of a list) are thread-safe, preventing interpreter crashes. It does NOT protect your application's business logic. If Thread A and Thread B both execute `account.balance += 10`, this is not an atomic operation in Python bytecode (it compiles to LOAD, ADD, STORE). The GIL can context-switch exactly between the ADD and the STORE, causing a Lost Update race condition. You must still use explicit `threading.Lock()` to protect shared mutable state in your application code.", ["The GIL protects CPython's internal memory allocator, not user-level business logic", "Complex operations (like `+=`) compile to multiple bytecode instructions", "The GIL can context switch between those instructions, causing standard Race Conditions (Lost Updates)"], ["The GIL is a myth created to sell more CPUs"]),
    ("B63_4_2", "diagnose", "hard", "debugging", ["Concurrency"], "Your multi-threaded Python app uses a standard `threading.Lock()` to protect a shared resource. You write a recursive function that requires this lock. The thread acquires the lock, calls itself, and the entire application instantly freezes. Why?", "A standard `threading.Lock()` is not reentrant. When the thread acquires it on the first pass, the lock is marked as Held. When the function recurses and the EXACT SAME thread tries to acquire the lock again, the lock blindly blocks, waiting for the lock to be released. However, the thread holding the lock is the one that is blocked, creating an instant single-thread Deadlock. To fix this, you must use a `threading.RLock()` (Reentrant Lock), which tracks the *owning thread's ID* and a recursion counter, allowing the same thread to acquire it multiple times without blocking.", ["Standard Locks block any attempt to acquire them, even if the requesting thread already owns it", "Calling a locked recursive function causes an instant Deadlock", "Fix: Use `threading.RLock()` which allows the owning thread to re-acquire the lock safely"], ["The function forgot what it was doing"]),
    ("B63_4_3", "implement", "medium", "implement", ["Concurrency"], "How do you implement a 'Condition Variable' (`threading.Condition`) to optimize a Producer-Consumer thread architecture instead of using a `while True` sleep loop?", "If a Consumer thread uses `while len(queue) == 0: time.sleep(0.1)`, it wastes massive amounts of CPU polling and introduces a 100ms latency penalty. A Condition Variable fixes this. The Consumer acquires the condition lock and calls `condition.wait()`. This atomically releases the lock and physically puts the OS thread to sleep (0% CPU usage). When the Producer adds an item, it calls `condition.notify()`. The OS instantly wakes up the exact sleeping Consumer thread, re-acquires the lock, and allows it to process the item with zero polling latency.", ["Polling loops (`while True: sleep`) waste CPU and introduce artificial latency", "`condition.wait()` puts the thread to sleep efficiently at the OS level", "`condition.notify()` wakes the sleeping thread instantly when data is ready"], ["Condition variables check if the weather is good before running the code"]),
    ("B63_4_4", "tradeoff", "hard", "tradeoff", ["Concurrency"], "What is the tradeoff of using a `threading.Barrier` to synchronize 10 worker threads versus letting them execute completely independently?", "A Barrier forces all 10 threads to stop at a specific point in the code (`barrier.wait()`) until ALL 10 threads have reached that exact line, at which point they are all released simultaneously. The benefit is coordinated execution (e.g., ensuring all threads have downloaded their chunk of a file before any thread begins compiling it). The severe tradeoff is the 'Straggler Problem'. If 9 threads finish in 1 second, but 1 thread hits a slow network socket and takes 45 seconds, the other 9 threads sit completely idle, wasting CPU resources and destroying overall system throughput.", ["Barriers guarantee synchronized progression across multiple concurrent threads", "Tradeoff: The Straggler Problem. The entire group is bottlenecked by the absolute slowest thread", "Wastes resources because fast threads sit blocked instead of moving on to the next task"], ["A barrier is an IF statement that stops the code"]),
    ("B63_4_5", "scenario", "medium", "scenario", ["Concurrency"], "You use a `ThreadPoolExecutor(max_workers=5)` to handle web scraping. You submit 10,000 URLs to the executor. Within seconds, the Python process crashes with `MemoryError`. Why did a limited pool of 5 workers cause memory exhaustion?", "While there are only 5 active worker threads executing tasks, the `ThreadPoolExecutor.submit()` method is non-blocking and instantly queues the pending tasks. If you loop 10,000 times, you instantly create 10,000 `Future` objects and 10,000 task closures in RAM, overwhelming the memory before the 5 workers even finish the first batch. To fix this, you must introduce Backpressure. Either use `executor.map(urls, chunksize=X)` as an iterator, or use an explicit `queue.Queue(maxsize=50)` to block the producer loop when the backlog gets too large.", ["`max_workers` limits concurrent execution, but does NOT limit the internal pending task queue", "Submitting thousands of tasks instantly allocates massive memory for Futures and closures", "Fix: Implement Backpressure using a bounded `queue.Queue` or generator-based `map`"], ["The 5 workers drank all the RAM juice"]),

    # Advanced Asyncio
    ("B63_4_6", "concept", "medium", "concept", ["Asyncio"], "What is 'Event Loop Starvation' in `asyncio`, and how does a single CPU-bound function cause it?", "The `asyncio` Event Loop runs on a single OS thread. It multiplexes I/O by rapidly switching between coroutines when they `await`. If a developer writes an `async def` function but calls a synchronous, CPU-bound library inside it (e.g., `bcrypt.hashpw` or `json.loads` on a 50MB string), that function does not `await`. It physically hijacks the single OS thread for 500ms. During that half-second, the Event Loop is 'Starved'—it is mathematically impossible for it to accept new incoming network connections, process WebSocket pings, or resume other sleeping coroutines, causing a total application freeze.", ["The Event Loop relies on cooperative multitasking (coroutines explicitly yielding via `await`)", "CPU-bound or blocking synchronous code hijacks the single thread", "The Event Loop is starved, preventing it from processing any other concurrent I/O events"], ["Starvation means the event loop didn't get enough electricity"]),
    ("B63_4_7", "diagnose", "hard", "debugging", ["Asyncio"], "Your `asyncio` application gracefully shuts down when it receives a `SIGTERM`. You cancel all pending tasks and close the loop. However, database connections are left hanging, and `finally` blocks inside your coroutines are not executing. Why?", "When you call `task.cancel()`, `asyncio` injects a `CancelledError` exception into the coroutine at the exact `await` line it is currently paused on. The coroutine then executes its `except` and `finally` blocks. However, if your shutdown script immediately calls `loop.close()` after issuing the cancellations, the coroutines are instantly destroyed BEFORE they have a chance to execute their teardown logic. You must explicitly `await asyncio.gather(*tasks, return_exceptions=True)` AFTER cancelling them, giving the Event Loop time to actually run the `finally` blocks and close the DB connections before terminating the loop.", ["`task.cancel()` does not instantly stop a task; it schedules an exception to be thrown inside it", "Calling `loop.close()` immediately after cancellation destroys the loop before cleanup code (`finally`) can run", "Fix: You must `await` the cancelled tasks to allow them to execute their teardown logic on the loop"], ["The finally blocks were written in a different language"]),
    ("B63_4_8", "implement", "medium", "implement", ["Asyncio"], "How do you implement a 'Semaphore' in `asyncio` to prevent 10,000 concurrent web scraper tasks from DDoS-ing a target server?", "If you use `asyncio.gather(*10000_tasks)`, Python will instantly open 10,000 concurrent HTTP sockets, getting your IP banned instantly or crashing your own router. You must limit concurrency using an `asyncio.Semaphore(10)`. You pass this semaphore to the scraper coroutine. Inside the coroutine, you wrap the HTTP call in `async with semaphore:`. The semaphore maintains an internal counter. The first 10 coroutines acquire it instantly. The 11th coroutine suspends (`awaits`) until one of the first 10 finishes and releases the semaphore. This guarantees exactly 10 concurrent requests at any given microsecond.", ["Unbounded `asyncio.gather` will instantly exhaust sockets or trigger rate-limits", "Instantiate a single `asyncio.Semaphore(max_concurrency)` and pass it to all tasks", "Wrap the critical network call in an `async with` block so excess tasks suspend until a slot opens"], ["You just send an email to the server asking for permission"]),
    ("B63_4_9", "tradeoff", "hard", "tradeoff", ["Asyncio"], "What is the architectural tradeoff of using an `AsyncGenerator` (an `async def` function that `yields`) versus returning an entire `list` of awaited results?", "Returning a `list` requires the server to wait for all asynchronous operations to finish, materializing the entire dataset in RAM before sending it to the client. This consumes massive memory and causes high 'Time to First Byte' (TTFB) latency. An `AsyncGenerator` yields items one by one *as they complete* over the network. This provides phenomenal TTFB and a tiny memory footprint (Streaming). The severe tradeoff is Error Handling and Connection Lifecycles. If the client disconnects halfway through the stream, the `AsyncGenerator` is violently interrupted with a `GeneratorExit` exception, complicating resource cleanup (like DB cursors), and making it impossible to return standard HTTP error codes once the stream has started.", ["Returning a List: High memory usage and slow TTFB, but simple, atomic error handling", "AsyncGenerator: Phenomenal memory efficiency and TTFB via streaming", "Tradeoff: Complex cleanup on premature client disconnects and inability to change HTTP status codes mid-stream"], ["Async generators run on diesel fuel"]),
    ("B63_4_10", "scenario", "medium", "scenario", ["Asyncio"], "You use `asyncio.create_task(background_worker())` inside an HTTP endpoint to process a webhook without delaying the HTTP response. A week later, you realize half the background tasks never actually executed. Why did `asyncio` silently drop your tasks?", "This is the infamous 'Dangling Task Garbage Collection' trap in Python 3.7+. When you call `asyncio.create_task()`, it schedules the task on the loop and returns a `Task` object. If you do not store a strong reference to that `Task` object (e.g., you just throw it away), Python's standard Garbage Collector sees that the `Task` object has a reference count of 0. The GC will instantly delete the task object from memory *mid-execution*, silently aborting the background work. You must ALWAYS append background tasks to a persistent global `set()` to maintain a strong reference until they complete.", ["`create_task()` returns an object. If you don't save a reference to it, the GC will delete it", "Deleting the `Task` object instantly and silently aborts its execution on the Event Loop", "Fix: Maintain a strong reference (like storing it in a global `set()`) until the task finishes"], ["The background worker went on strike"]),

    # Performance Engineering
    ("B63_4_11", "concept", "medium", "concept", ["Performance Tuning"], "What is 'Vectorization' in Python (using NumPy/Pandas), and why is it 100x faster than a standard Python `for` loop?", "In a standard Python `for` loop over a million integers, Python must dynamically check the type of the variable, invoke the `__add__` dunder method, and allocate a brand new Integer object in RAM for EVERY single iteration. This CPU overhead is catastrophic. 'Vectorization' leverages NumPy, which stores data in contiguous, strictly-typed C-arrays in RAM. When you type `array_a + array_b`, NumPy completely bypasses the Python interpreter. It pushes the mathematical operation down to highly optimized, pre-compiled C or Fortran code that utilizes CPU SIMD (Single Instruction, Multiple Data) instructions, performing the math on entire chunks of memory simultaneously.", ["Python `for` loops suffer massive overhead from dynamic typing, object allocation, and bytecode evaluation", "Vectorization uses strictly typed, contiguous C-arrays (NumPy)", "It bypasses the Python interpreter entirely, executing SIMD instructions directly on the CPU via compiled C code"], ["Vectorization is drawing the numbers using SVG lines"]),
    ("B63_4_12", "diagnose", "hard", "debugging", ["Performance Tuning"], "Your Python data pipeline parses a 10GB CSV file using Pandas. The server has 16GB of RAM. `pandas.read_csv('data.csv')` consistently crashes with an `MemoryError` (OOM). Why does a 10GB file crash a 16GB server, and how do you fix it?", "Pandas heavily inflates memory. A 10GB raw text CSV often expands to 20-30GB of RAM when parsed into Python object overhead, 64-bit float representations, and Pandas DataFrame internal structures. To fix this, you must NOT load the entire file at once. You must use 'Chunking' (`pd.read_csv('data.csv', chunksize=10000)`), which returns an iterator. You process 10,000 rows at a time, aggregate the results, and let the GC free the chunk before loading the next one. Alternatively, use out-of-core libraries like `Dask` or `Polars` which natively support streaming massive datasets.", ["Parsing raw text into rich Python objects/DataFrames inherently multiplies the memory footprint (Object Overhead)", "Loading a 10GB CSV will easily demand 20-30GB of RAM, triggering an OOM kill", "Fix: Use `chunksize` to iterate through the file in batches, or use out-of-core tools like Dask"], ["Pandas are heavy animals and break the server"]),
    ("B63_4_13", "implement", "medium", "implement", ["Performance Tuning"], "How do you optimize the performance of Python string concatenation inside a massive loop (`for string in list: result += string`)?", "Using the `+=` operator inside a loop is catastrophic in Python. Because strings are Immutable, Python mathematically cannot modify the string in place. Every time `+=` is called, Python must allocate a brand NEW block of memory, copy the old string into it, and append the new string. In a loop of 100,000 strings, this causes O(N^2) quadratic memory allocation overhead. The strictly correct implementation is to append all substrings into a Python list (`result_list.append(string)`), and then call `''.join(result_list)` ONCE at the very end. The `join()` method calculates the total memory needed in a single pass and allocates it in C, achieving O(N) linear time.", ["Strings in Python are Immutable; `+=` forces a brand new memory allocation and copy every iteration", "This results in O(N^2) quadratic performance degradation and massive GC overhead", "Fix: Append to a list and use `''.join()`, which pre-allocates memory and runs in O(N) time"], ["You just type faster on the keyboard"]),
    ("B63_4_14", "tradeoff", "hard", "tradeoff", ["Performance Tuning"], "What is the tradeoff of replacing standard Python classes with C-Extensions (like Cython or pybind11) to optimize algorithmic bottlenecks?", "Writing a bottleneck algorithm in C/Rust (via Cython/pybind11) provides a massive 50x-100x performance boost, bypasses the GIL, and allows true multithreading. The severe tradeoff is complexity and portability. You lose the ability to deploy raw `.py` files; you must now compile platform-specific binary Wheels (`.whl`) for Windows, Mac, and Linux. It vastly complicates the CI/CD pipeline, introduces the risk of C-level memory leaks (Segfaults) that bypass Python's safe garbage collector, and makes the codebase unmaintainable for junior Python developers.", ["C-Extensions provide 100x speedups, true multithreading, and GIL circumvention", "Tradeoff: Destroys cross-platform deployment simplicity (requires compiling binaries per OS)", "Tradeoff: Introduces manual memory management risks (Segfaults) and requires polyglot developer expertise"], ["C extensions make the code look like an ancient language"]),
    ("B63_4_15", "scenario", "medium", "scenario", ["Performance Tuning"], "Your Python API fetches data from Redis and returns it to the user. The Redis query takes 2ms, but the API latency is 400ms. You run a profiler and find that `json.dumps()` is consuming 398ms. The payload is a massive list of dictionaries. How do you optimize this JSON serialization bottleneck?", "The standard library `json` module is written in C, but it still suffers overhead when traversing deep, complex Python objects recursively. If the bottleneck is purely serialization, you should swap the standard library for an ultra-fast third-party JSON encoder written purely in Rust or C, such as `orjson` or `ujson`. `orjson.dumps()` is typically 5x to 10x faster than the standard library. Furthermore, if the data is already stored in Redis as a JSON string, you should NOT deserialize it into Python dictionaries just to serialize it again; simply fetch the raw string and return it directly via `Response(content=redis_str, media_type=\"application/json\")`.", ["The standard `json` module is slow at traversing massively nested Python objects", "Fix 1: Swap to a high-performance C/Rust serialization library like `orjson` or `ujson`", "Fix 2 (Architectural): If the data is already a JSON string in Redis, stream the raw string directly to the client to bypass parsing entirely"], ["You just ask the users to read binary instead"]),
    ("B63_4_16", "explain", "medium", "explain", ["Performance Tuning"], "Explain why accessing a Global Variable in a tight Python loop is significantly slower than accessing a Local Variable.", "This is a CPython bytecode optimization quirk. When you access a local variable inside a function, Python's compiler optimizes it using the `LOAD_FAST` instruction, which retrieves the variable instantly from a fixed-size C array based on an index. When you access a Global variable, Python is forced to use the `LOAD_GLOBAL` instruction, which requires performing an expensive hash-table lookup in the global `__dict__` every single time. In a loop of 10 million iterations, this dictionary lookup overhead is massive. To fix it, you simply assign the global variable to a local variable *before* the loop starts (`local_var = GLOBAL_VAR`).", ["Local variables use `LOAD_FAST` (instant array index access)", "Global variables use `LOAD_GLOBAL` (expensive dictionary hash-table lookups)", "In tight loops, assigning a global to a local variable first provides a massive, free speedup"], ["Global variables are heavier because they have to travel across the globe"])
]

def run_batch():
    # Load all existing records to do deduplication
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 4).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Systems Engineer", "Software Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Python",
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
            
    # Final audit reporting
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r["primary_role"] for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT")
    print("========================================")
    print(f"Batch: 63")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
