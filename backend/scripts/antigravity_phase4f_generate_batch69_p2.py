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
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

# Tuple structure:
# (id_code, intent, difficulty, question_type, [primary_skill, secondary_skills...], technology, topic, question, expected_answer, strong_indicators, weak_indicators)
Q = [
    (
        "B69_2_1",
        "explain",
        "hard",
        "explain",
        ["Async Concurrency", "Language Semantics"],
        "asyncio",
        "The asyncio.shield() Cancellation Semantics Trap",
        "In Python's `asyncio`, developers often use `await asyncio.shield(critical_task)` to prevent a critical operation from being canceled when the outer caller is cancelled. However, this pattern frequently leads to subtle bugs where the caller thinks the operation was aborted or fails to catch its exceptions. Explain the exact cancellation semantics of `asyncio.shield()`, and why cancelling the outer task does NOT stop the caller from immediately raising `CancelledError`.",
        "How asyncio.shield() Actually Operates: 1) Protection is Asymmetric: `asyncio.shield(inner_task)` creates a wrapper shield future. If a cancellation request is sent to the *outer* task awaiting the shield, the wrapper future raises `asyncio.CancelledError` *immediately to the awaiting caller*. However, the shield does NOT propagate the cancellation signal inward to `inner_task`. `inner_task` continues executing in the background uninterrupted. 2) The Critical Gotchas: A) Premature Caller Unblocking: The awaiting caller receives `CancelledError` instantly at the point of cancellation, *before* `inner_task` finishes! The caller assumes the work is done or abandoned and proceeds to run `finally` blocks, potentially releasing database locks or closing resources that `inner_task` is still actively using. B) Swallowed Exceptions & Unhandled Errors: If `inner_task` subsequently raises an unhandled exception or fails after the caller has already canceled, nobody is awaiting it anymore. The exception is either logged as an unhandled background task error or silently lost. 3) Correct Pattern: If the caller must ensure `inner_task` finishes before the caller exits, wrap the shield in an exception handler: `try: await asyncio.shield(t); except asyncio.CancelledError: await t; raise`.",
        [
            "Explains that outer cancellation immediately raises CancelledError to the awaiting caller while inner_task continues in background",
            "Identifies the race condition where caller's cleanup/finally blocks execute while inner_task is still actively running",
            "Describes unhandled exception leaks when inner_task fails after the caller has already abandoned awaiting"
        ],
        [
            "Claims asyncio.shield() physically prevents the operating system from terminating the Python process"
        ]
    ),
    (
        "B69_2_2",
        "implement",
        "medium",
        "implement",
        ["Async Concurrency", "Resource Management"],
        "asyncio",
        "Cancellation-Safe Async Resource Cleanup in Finally Blocks",
        "In an asynchronous worker, a developer acquires a distributed lock and writes cleanup in a `finally` block: `finally: await lock.release()`. Under high load, when the worker task is cancelled while executing inside the `finally` block, the lock is never released, causing a distributed deadlock. Why does cancellation interrupt asynchronous code inside `finally` blocks, and how do you implement cancellation-safe async cleanup?",
        "Why Cancellation Interrupts Finally Blocks: When a task is cancelled via `task.cancel()`, Python raises an `asyncio.CancelledError` at the current `await` point. The runtime enters the `finally` block to execute cleanup. However, if the cleanup code *itself* contains an `await` statement (`await lock.release()`), and the task still has a pending cancellation status (or receives a secondary cancellation signal from a parent task group), the `await lock.release()` point is *immediately cancelled*, raising another `CancelledError` before the network packet can be transmitted! The lock remains locked forever. How to Implement Cancellation-Safe Cleanup: 1) Using `asyncio.shield()` inside `finally`: Wrap the async cleanup call in `asyncio.shield()`: `finally: try: await asyncio.shield(lock.release()); except asyncio.CancelledError: pass`. This ensures that even though the outer task is cancelled, the coroutine releasing the lock runs to completion without being aborted. 2) Suppressing secondary cancellations: In Python 3.11+, use `try: ... except asyncio.CancelledError: ...` with explicit cleanup shielding or uncancel/timeout patterns, ensuring network sockets are closed cleanly before re-raising the cancellation error.",
        [
            "Explains that await statements inside finally blocks can be interrupted by pending CancelledError exceptions",
            "Identifies that interrupted cleanup abandons locks and connections, causing permanent distributed leaks",
            "Shields the async cleanup operation (e.g. via asyncio.shield) to guarantee execution to completion"
        ],
        [
            "Suggests never using finally blocks in asynchronous Python code"
        ]
    ),
    (
        "B69_2_3",
        "scenario",
        "medium",
        "scenario",
        ["Async Concurrency", "Resilience"],
        "asyncio",
        "Asyncio Semaphore Starvation and Unfair Queueing",
        "A high-throughput API gateway uses an `asyncio.Semaphore(10)` to rate-limit outbound requests to an authentication service. Under sudden burst traffic of 500 concurrent requests, you notice that some requests complete in 5ms while other identical requests wait in the semaphore queue for over 60 seconds and time out. What causes this semaphore latency disparity, and how does `asyncio.Semaphore`'s internal scheduling queue behavior cause unfair starvation?",
        "Root Cause: In CPython's standard `asyncio.Semaphore`, waiting coroutines are managed via an internal FIFO list of `Future` objects (`self._waiters`). However, starvation and latency disparities occur due to event loop scheduling races: 1) Future Scheduling Race: When a coroutine releases the semaphore (`sem.release()`), the semaphore pops the oldest waiter future and calls `loop.call_soon(waiter._set_result_unless_cancelled, None)`. 2) Cancellation Churn: If clients enforce client-side timeouts (e.g., 2 seconds), waiters in the middle of the `_waiters` queue cancel themselves. When waiters are cancelled, `asyncio.Semaphore` wakes up the next waiter. If multiple releases and cancellations interleave with new incoming coroutines calling `acquire()`, coroutines that happen to run right after a release can steal the permit if not strictly guarded, or heavy cancellation churn reshuffles task priorities. 3) Starvation Fix: Wrap semaphore acquisition with strict fairness queues or replace raw semaphores with a bounded `asyncio.Queue` acting as a worker pool. A worker pool assigns work to persistent worker coroutines in deterministic FIFO order, ensuring bounded maximum wait times ($O(N)$ bounded delay) without cancellation race churn.",
        [
            "Analyzes asyncio.Semaphore internal _waiters queue mechanics and loop.call_soon scheduling races",
            "Identifies that cancellations and bursty acquire/release interleaving create severe tail latency outliers",
            "Resolves starvation by structuring bounded worker pools via asyncio.Queue to enforce strict FIFO ordering"
        ],
        [
            "Claims semaphores in asyncio are hardware chips that overheat under 500 requests"
        ]
    ),
    (
        "B69_2_4",
        "implement",
        "medium",
        "implement",
        ["Async Concurrency", "Architecture"],
        "asyncio / Queue",
        "Bounded Async Producer-Consumer Pipeline with Graceful Drain",
        "You are designing an in-memory batching pipeline in Python using `asyncio.Queue(maxsize=100)`. Multiple async producers enqueue records, and 5 worker coroutines consume and batch them. When the application receives a shutdown signal (`SIGTERM`), how do you gracefully drain all remaining items in the queue, ensure workers finish their in-flight batches, and cleanly terminate without dropping records or leaving orphaned tasks?",
        "Graceful Queue Drain Implementation: 1) Stop Ingress (Producers): Set an application shutdown event (`shutdown_event = asyncio.Event()`). Producers check this event and immediately stop accepting new incoming requests, rejecting them with HTTP 503 or closing ingestion sockets. 2) Wait for Producers to Complete: Wait for all producer tasks to finish pushing their remaining data into the queue. 3) Sentinel Termination Pattern: Push 5 sentinel objects (e.g., `None` or a custom `object()` sentinel) into the queue—exactly one sentinel for each of the 5 worker coroutines: `for _ in range(5): await queue.put(SENTINEL)`. 4) Worker Sentinel Detection: Inside each worker's `while True:` loop: `item = await queue.get()`. If `item is SENTINEL`: `queue.task_done()`; `break`. The worker finishes any buffered batch and exits its loop naturally. 5) Await Queue Completion: The coordinator calls `await queue.join()`, which blocks until every item (and sentinel) has had `queue.task_done()` called on it. 6) Await Workers: Call `await asyncio.gather(*workers)` to ensure all 5 worker tasks have cleanly terminated before closing database connections and shutting down the event loop.",
        [
            "Stops producer ingestion first to prevent new data from entering the queue",
            "Injects sentinel objects (one per worker) into the queue to signal workers to break their processing loops",
            "Uses queue.join() and asyncio.gather(*workers) to ensure all enqueued records are processed before process exit"
        ],
        [
            "Suggests calling task.cancel() on all workers immediately, dropping all remaining queued items"
        ]
    ),
    (
        "B69_2_5",
        "concept",
        "easy",
        "concept",
        ["Async Concurrency", "Event Loop"],
        "asyncio",
        "Event Loop Starvation and Cooperative Yielding with asyncio.sleep(0)",
        "In an asyncio application, a coroutine performs a heavy in-memory computation: `for item in millions_of_items: compute(item)`. Even though there are no blocking I/O calls, the entire web server stops responding to HTTP health checks and other coroutines freeze. Why does this CPU loop starve the event loop, and how does `await asyncio.sleep(0)` restore cooperative multitasking?",
        "Why CPU Loops Starve the Event Loop: `asyncio` operates on a single thread using cooperative multitasking. The event loop can ONLY execute other coroutines, handle incoming network packets, and process timers when the currently executing coroutine explicitly yields control back to the loop via an `await` statement. If a coroutine executes a tight synchronous `for` loop with no `await` points, it monopolizes the operating system thread for seconds. The event loop cannot run its scheduler, causing health checks to time out and all concurrent connections to stall. How `await asyncio.sleep(0)` Fixes This: Calling `await asyncio.sleep(0)` creates a timer with zero delay, schedules the current coroutine to resume in the loop's ready queue (`call_soon`), and immediately yields execution back to the event loop. The event loop gets a turn to poll OS sockets (`epoll`), process pending network packets, execute other ready coroutines, and then resume the CPU loop on the next iteration. (For massive CPU tasks, offloading to `asyncio.to_thread` or `ProcessPoolExecutor` is preferred, but `sleep(0)` provides lightweight cooperative yielding in batch loops).",
        [
            "Explains that asyncio uses single-threaded cooperative multitasking requiring explicit await yield points",
            "Shows that synchronous CPU loops block the event loop from scheduling I/O polling and other tasks",
            "Demonstrates await asyncio.sleep(0) yielding control to the event loop scheduler to maintain system responsiveness"
        ],
        [
            "Claims asyncio.sleep(0) pauses the CPU hardware clock for zero nanoseconds"
        ]
    ),
    (
        "B69_2_6",
        "diagnose",
        "hard",
        "debugging",
        ["Async Concurrency", "Database Architecture"],
        "asyncpg / aiohttp",
        "Async Resource Pool Exhaustion under Uncaught Timeout Exceptions",
        "An asynchronous microservice uses an `asyncpg.Pool` with 20 maximum connections. Under load, API endpoints wrap database queries in timeouts: `async with asyncio.timeout(2.0): async with pool.acquire() as conn: await conn.execute(...)`. After 30 minutes, all subsequent queries hang forever, timing out on `pool.acquire()`. Inspecting PostgreSQL shows 20 idle connections in `idle in transaction` state. How did the timeout cancel the coroutine in a way that leaked the database connection, and how do you prevent async pool starvation?",
        "Mechanism of the Connection Leak: 1) The Timeout Cancellation Race: `asyncio.timeout(2.0)` cancels the running task when the timer expires by injecting `asyncio.CancelledError`. 2) Cancellation Interleaving during Acquisition: If the 2-second timeout expires *inside* the context manager `__aenter__` of `pool.acquire()`—specifically after the connection has been leased from the internal queue but *before* the Python context manager finishes binding the connection reference—the `CancelledError` causes the code to abort before entering the block. In poorly structured drivers, the connection is removed from the pool's idle list but `__aexit__` is never invoked, leaving the connection permanently checked out. 3) `idle in transaction` in PostgreSQL: If the timeout fires mid-query while a transaction was open, the connection socket was abandoned without sending an SQL `ROLLBACK`. Postgres keeps the transaction and locks open on the server. Mitigation: 1) Strict Driver Pooling: Use modern driver context managers that handle cancellation inside `acquire()` atomically (modern `asyncpg` versions shield internal acquisition state). 2) Always configure `timeout` *inside* the connection acquisition or set `statement_timeout` on the PostgreSQL server level so the database server automatically aborts hung transactions and resets connections. 3) Configure pool `command_timeout` and `max_inactive_connection_lifetime`.",
        [
            "Diagnoses task cancellation interrupting connection acquisition or checkout before cleanup bindings take effect",
            "Explains that abandoned sockets leave PostgreSQL connections stuck in 'idle in transaction' state",
            "Prescribes server-side statement_timeout and driver-level command timeouts to reclaim leaked connections"
        ],
        [
            "Suggests increasing the connection pool size from 20 to 500,000 connections"
        ]
    ),
    (
        "B69_2_7",
        "concept",
        "easy",
        "concept",
        ["Async Concurrency", "Language Semantics"],
        "asyncio / Python 3.11+",
        "asyncio.timeout() vs asyncio.wait_for() Performance and Safety",
        "In Python 3.11+, the `asyncio.timeout(delay)` context manager was introduced to replace `asyncio.wait_for(fut, timeout)`. Why is `asyncio.timeout()` considered safer, less prone to cancellation race conditions, and more performant than `wait_for()`?",
        "1) Elimination of Task Overhead: `asyncio.wait_for(coro, timeout)` works by implicitly wrapping the target coroutine into an entirely separate `asyncio.Task` object (`asyncio.ensure_future`). Creating a full Task incurs memory allocation and event loop registration overhead. `asyncio.timeout()` is a lightweight asynchronous context manager: it registers a simple timer handle with the event loop without creating an extra task, operating with near-zero allocation overhead. 2) Cleaner Cancellation Semantics: With `wait_for()`, when the timeout fires, it cancels the inner task and raises `asyncio.TimeoutError`. However, if the inner task catches or shields cancellation, subtle race conditions occur where the inner task continues running or raises unexpected `CancelledError` exceptions that mask the timeout. 3) Natural Scope Composition: `asyncio.timeout()` applies cleanly to a block of multiple sequential `await` statements: `async with asyncio.timeout(5.0): await step1(); await step2()`. The 5-second deadline applies across the *entire block*, whereas `wait_for` must be awkwardly nested around every single call.",
        [
            "Explains that wait_for() allocates an extra asyncio.Task whereas asyncio.timeout() uses lightweight timer handles",
            "Identifies that wait_for() suffers from cancellation race conditions and masking between CancelledError and TimeoutError",
            "Highlights that asyncio.timeout() context manager provides unified deadline scoping across multiple sequential awaits"
        ],
        [
            "Claims asyncio.wait_for() was deleted because it only worked on Python 2"
        ]
    ),
    (
        "B69_2_8",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Async Concurrency", "Performance Tuning"],
        "uvloop / libuv",
        "uvloop vs Default CPython Event Loop: Architecture and Caveats",
        "Many high-performance Python web frameworks (like Sanic or FastAPI with Uvicorn) recommend replacing CPython's default asyncio event loop with `uvloop`. How does `uvloop` achieve 2x to 4x higher throughput, and what are the operational caveats and limitations when deploying it in production?",
        "How uvloop Achieves High Performance: 1) libuv Engine: `uvloop` is a drop-in replacement for `asyncio.AbstractEventLoop` written in Cython on top of `libuv` (the C networking library powering Node.js). 2) Zero-Copy C Networking: The default CPython event loop is written in pure Python wrapping OS selectors (`selectors.epoll`). Every socket read, write, and callback scheduling traverses Python object layers, bytecode evaluation, and PyObject boxing. `uvloop` handles socket I/O, event dispatching, and callback queues entirely in optimized C code with minimal Python interpreter interaction, slashing CPU overhead and maximizing system call efficiency. Operational Caveats and Limitations: 1) Windows Incompatibility: `uvloop` is primarily built for Unix-like operating systems (Linux, macOS). It does not fully support Windows natively, making local development on Windows machines challenging without WSL. 2) C-Level Crash Vulnerability: Any memory corruption, Cython bug, or incompatible native extension interaction causes a hard C segmentation fault (`SIGSEGV`), bypassing Python exception handling. 3) Subprocess and Signal Complexities: Mixing custom signal handlers or complex multi-threaded subprocess piping can exhibit minor behavioral discrepancies compared to CPython's standard `_UnixSelectorEventLoop`.",
        [
            "Explains that uvloop is implemented in Cython on top of libuv, bypassing pure Python selector overhead",
            "Highlights throughput gains from C-level socket handling and minimal PyObject boxing",
            "Details operational caveats: lack of native Windows support, segfault risks, and signal/subprocess nuances"
        ],
        [
            "Claims uvloop runs Python code on GPU tensor cores instead of the CPU"
        ]
    ),
    (
        "B69_2_9",
        "diagnose",
        "medium",
        "debugging",
        ["Async Concurrency", "Error Handling"],
        "asyncio.gather",
        "Orphaned Sibling Tasks in asyncio.gather() under Partial Failures",
        "A developer executes three parallel API calls: `results = await asyncio.gather(fetch_a(), fetch_b(), fetch_c())`. `fetch_b()` fails with an `HTTPError` after 100ms. The caller's `try...except` catches the error immediately. However, 10 seconds later, server logs reveal that `fetch_a()` and `fetch_c()` were still executing and writing duplicate records to the database. Why didn't `gather()` cancel the sibling tasks when `fetch_b()` failed, and how does `asyncio.TaskGroup` (Python 3.11+) fix this?",
        "Why asyncio.gather() Leaves Orphaned Tasks: By default, `asyncio.gather(*tasks)` waits for all futures. If one task raises an unhandled exception, `gather()` *immediately re-raises that exception to the caller*. However, CPython's `gather()` does NOT automatically cancel the remaining sibling tasks! They are abandoned as detached, 'orphaned' tasks running concurrently in the background. Because the caller already exited the `try...except` block, the caller has lost all control or visibility over the running siblings, leading to ghost database writes, connection leaks, and resource corruption. How `asyncio.TaskGroup` Fixes This: In Python 3.11+, `asyncio.TaskGroup` implements structured concurrency: `async with asyncio.TaskGroup() as tg: t1 = tg.create_task(fetch_a()); t2 = tg.create_task(fetch_b()); t3 = tg.create_task(fetch_c())`. If any task raises an exception: 1) The TaskGroup automatically cancels all remaining active sibling tasks in the group. 2) It waits for all cancelled tasks to finish their `finally` cleanup. 3) It bundles all errors into an `ExceptionGroup` and raises it to the caller, guaranteeing zero orphaned ghost tasks.",
        [
            "Identifies that asyncio.gather() raises the first exception immediately without cancelling remaining sibling tasks",
            "Explains that orphaned siblings continue running unmanaged, executing duplicate database writes and leaking resources",
            "Prescribes asyncio.TaskGroup (structured concurrency) which automatically cancels siblings upon any failure"
        ],
        [
            "Claims asyncio.gather() automatically reboots the server when an exception is raised"
        ]
    ),
    (
        "B69_2_10",
        "explain",
        "medium",
        "explain",
        ["Async Concurrency", "Threading"],
        "asyncio / threading",
        "Bridging Threads and Event Loops with asyncio.run_coroutine_threadsafe()",
        "In a mixed architecture where a legacy background OS thread (e.g., an incoming MQTT message listener or Kafka thread) needs to invoke an asynchronous coroutine running inside the main `asyncio` event loop, why is calling `asyncio.create_task()` directly from the background thread unsafe, and how does `asyncio.run_coroutine_threadsafe()` guarantee thread safety?",
        "Why Calling create_task() from Another Thread Fails: `asyncio` event loops are fundamentally NOT thread-safe. Functions like `asyncio.create_task()`, `loop.call_soon()`, and coroutine frame manipulation mutate the event loop's internal scheduling data structures (`self._ready`, `self._scheduled`) without holding thread locks. Calling `create_task()` from an external OS thread causes race conditions, corrupted internal loop state, and missed wakeups because the event loop's OS selector thread is currently sleeping in an `epoll_wait()` syscall and has no idea that another thread added a task. How `run_coroutine_threadsafe()` Works: 1) Thread-Safe Scheduling: `concurrent_future = asyncio.run_coroutine_threadsafe(my_coro(), loop)`. It places the coroutine into the loop's thread-safe callback queue. 2) Selector Interruption via Self-Pipe: It writes a byte to the event loop's internal self-pipe (or eventfd socket). This immediately wakes up the event loop thread from its blocking `epoll_wait()` / `select()` syscall. 3) Future Bridge: It returns a standard `concurrent.futures.Future` (thread-safe future). The calling OS thread can safely block on `concurrent_future.result(timeout=5)` to wait for the coroutine's result or handle exceptions cleanly across thread boundaries.",
        [
            "Explains that asyncio event loop data structures are not thread-safe and cannot be mutated from external threads",
            "Details how run_coroutine_threadsafe uses self-pipe/eventfd to wake the event loop thread from epoll_wait",
            "Returns a thread-safe concurrent.futures.Future allowing the calling thread to await the result or exception"
        ],
        [
            "Claims Python automatically merges all OS threads into a single CPU core"
        ]
    ),
    (
        "B69_2_11",
        "scenario",
        "medium",
        "scenario",
        ["Web Architecture", "Resilience"],
        "ASGI / FastAPI / Uvicorn",
        "ASGI Lifespan Protocol Failures and Container Boot Loops",
        "You deploy a FastAPI microservice using the modern ASGI Lifespan protocol: `@asynccontextmanager async def lifespan(app): await db.connect(); yield; await db.disconnect()`. In production, the database cluster experiences a transient network delay during rollout. Pods crash repeatedly with `Application startup failed. Exiting.` and Kubernetes enters a `CrashLoopBackOff`. How does the ASGI Lifespan protocol handle startup failures, and how do you architect resilient startup probes to prevent container reboot loops?",
        "ASGI Lifespan Protocol Mechanics: 1) How Uvicorn Boots: When an ASGI server (Uvicorn/Hypercorn) boots, it sends a `{'type': 'lifespan.startup'}` message over the ASGI interface. The server blocks and refuses to bind its listening TCP socket until the application responds with `{'type': 'lifespan.startup.complete'}`. 2) Startup Crash Mechanism: If `await db.connect()` inside the `lifespan` context manager raises an uncaught exception (or times out), the ASGI application emits `{'type': 'lifespan.startup.failed'}`. The ASGI server immediately aborts process execution and exits with status 1. In Kubernetes, this causes an instant pod crash and `CrashLoopBackOff`. Resilient Architecture: 1) Bounded Startup Timeouts: Wrap external connections in explicit, short timeouts: `async with asyncio.timeout(3.0): await db.connect()`. 2) Resilient Degraded Startup: Do NOT crash during startup if an external dependency is unavailable. Catch connection errors, log a critical alert, set an internal flag `app.state.is_healthy = False`, and complete the lifespan startup cleanly. 3) Readiness vs Startup Probes: Expose `/readyz`. The Kubernetes Readiness Probe queries `/readyz`, sees `is_healthy == False`, and stops routing ingress traffic to the pod. The pod remains alive, attempting background reconnects every 5 seconds. As soon as the DB recovers, `is_healthy` becomes `True`, and Kubernetes begins routing traffic—preventing container restart storms.",
        [
            "Explains that unhandled exceptions during ASGI lifespan startup cause Uvicorn to exit immediately with status 1",
            "Identifies that Kubernetes converts startup exits into CrashLoopBackOff reboot storms",
            "Prescribes degraded startup: allowing the process to boot while failing Readiness probes until background reconnects succeed"
        ],
        [
            "Recommends deleting all database connection code from the application"
        ]
    ),
    (
        "B69_2_12",
        "diagnose",
        "hard",
        "debugging",
        ["Web Architecture", "Error Handling"],
        "FastAPI / Starlette",
        "Middleware Exception Bypass of FastAPI Exception Handlers",
        "In a FastAPI application, a developer defines custom exception handlers: `@app.exception_handler(CustomBusinessError)`. They also add a custom ASGI middleware inheriting from Starlette's `BaseHTTPMiddleware` to log request metadata. When an endpoint raises `CustomBusinessError`, instead of returning the expected custom JSON error response, the API returns a generic HTTP 500 Internal Server Error, and the custom exception handler is completely bypassed. Explain how ASGI middleware execution order causes this bypass, and how to fix it.",
        "Root Cause: Starlette Middleware Onion Architecture and Exception Boundaries: 1) The ASGI Call Stack: In Starlette/FastAPI, middleware components wrap the application like layers of an onion: `Uvicorn -> ExceptionMiddleware -> BaseHTTPMiddleware -> FastAPI Router -> Endpoint`. 2) Where Exception Handlers Live: FastAPI's `@app.exception_handler` decorators are registered inside Starlette's internal `ServerErrorMiddleware` and `ExceptionMiddleware`. 3) Why BaseHTTPMiddleware Bypasses Handlers: If a custom middleware uses `BaseHTTPMiddleware`, it wraps `call_next(request)` inside its own internal `dispatch()` method. If an exception is raised inside the endpoint, it bubbles up through the FastAPI router. If an exception occurs *inside the middleware dispatch method itself* (or if middleware intercepts the exception before `ExceptionMiddleware`), or if middleware re-raises an error, the exception escapes past Starlette's internal `ExceptionMiddleware` directly to Uvicorn's root handler. Uvicorn catches the unhandled Python exception and emits a raw HTTP 500 response. Solution: 1) Write Pure ASGI Middleware: Avoid `BaseHTTPMiddleware` (which adds task allocation overhead and exception catching quirks). Write standard ASGI middleware: `async def middleware(scope, receive, send)`. 2) Catch inside Endpoint or Router: Ensure business exceptions are handled within FastAPI router dependencies rather than bubbling raw into outer middleware layers. 3) Explicit Exception Catching: In custom middleware, wrap `call_next` with an explicit handler that catches expected domain exceptions and formats JSON responses directly.",
        [
            "Explains that FastAPI exception handlers reside inside Starlette's ExceptionMiddleware layer",
            "Identifies that BaseHTTPMiddleware wraps call_next and can bypass internal exception catching, bubbling to Uvicorn as raw 500s",
            "Prescribes writing pure ASGI middleware (scope, receive, send) or handling exceptions within router boundaries"
        ],
        [
            "Claims FastAPI does not support custom exception handlers"
        ]
    ),
    (
        "B69_2_13",
        "implement",
        "hard",
        "implement",
        ["Web Architecture", "Async Concurrency"],
        "ASGI / Starlette",
        "Detecting Client Disconnects during ASGI Streaming Responses",
        "In a FastAPI or Starlette application that streams a long-running 100MB data export using `StreamingResponse(generator())`, if a user closes their browser tab or cancels their download at 5%, the backend continues executing the generator and querying the database for the remaining 95MB of data. How do you poll the ASGI `receive` channel to detect `http.disconnect` events concurrently while streaming chunks to abort expensive backend processing?",
        "Why Streaming Responses Don't Abort Automatically: When an ASGI server streams data, `StreamingResponse` continuously calls `send({'type': 'http.response.body', 'body': chunk})`. In HTTP/1.1 and HTTP/2, if the client disconnects, socket write errors may not trigger until TCP socket write buffers fill up, which could take hundreds of chunks. Meanwhile, the generator continues executing heavy database queries. Implementation of Disconnect Detection: 1) The ASGI `receive` callable: The ASGI specification requires the server to send an event `{'type': 'http.disconnect'}` over the `receive` callable when the client closes the connection. 2) Concurrent Listening via `asyncio.create_task`: A streaming handler can run a background task concurrently that awaits `receive()`: `async def watch_disconnect(): message = await receive(); if message.get('type') == 'http.disconnect': disconnect_event.set()`. 3) Generator Interruption: In the streaming generator loop: before fetching each chunk from the database, check `if disconnect_event.is_set(): log.info('Client disconnected; aborting stream'); break`. 4) Clean Resource Teardown: Exiting the generator triggers its `finally` blocks, closing database cursors and releasing backend resources immediately rather than generating the remaining 95MB of unused data.",
        [
            "Explains that write sockets don't immediately fail upon client disconnect due to TCP socket buffering",
            "Listens on the ASGI receive callable for http.disconnect events concurrently using an asyncio task",
            "Aborts generator execution and triggers finally blocks to terminate upstream database cursors"
        ],
        [
            "Claims web servers automatically delete the client's computer when a browser tab closes"
        ]
    ),
    (
        "B69_2_14",
        "scenario",
        "medium",
        "scenario",
        ["Async Concurrency", "Performance Tuning"],
        "FastAPI / asyncio",
        "Sync-to-Async Thread Pool Exhaustion via asyncio.to_thread",
        "In a FastAPI application, a developer runs a legacy synchronous database library inside an async route: `@app.get('/data') async def get_data(): return await asyncio.to_thread(sync_db_query)`. Under load testing with 200 concurrent users, API response times jump from 50ms to 8,000ms, and the event loop appears starved, even though CPU usage is only 15%. What is the default thread pool concurrency ceiling of `asyncio.to_thread()`, and how do you architect dedicated thread pools for blocking I/O?",
        "Root Cause: Default ThreadPoolExecutor Saturation: 1) How `asyncio.to_thread()` Operates: `asyncio.to_thread()` offloads execution to the default thread pool executor of the event loop (`loop.run_in_executor(None, fn)`). 2) The Default 32-Thread Ceiling: In Python 3.8+, if no custom executor is configured, CPython creates a `ThreadPoolExecutor` sized to $\\min(32, \\text{os.cpu\_count()} + 4)$. On an 8-core server, the pool has a maximum of 32 worker threads. 3) Thread Starvation under 200 Users: When 200 concurrent requests arrive, 32 threads are instantly occupied by `sync_db_query` calls. The remaining 168 requests are queued in the executor's internal unbound task queue. Requests wait seconds in the thread queue before execution even begins. Concurrency drops to 32, degrading latency to 8 seconds. Architectural Solution: 1) Configure a Dedicated, Sized Executor: Do not use the global default thread pool for slow database I/O. Create a dedicated `ThreadPoolExecutor(max_workers=100, thread_name_prefix='db_worker')`. 2) Explicit Offloading: Offload explicitly to the dedicated pool: `await loop.run_in_executor(db_executor, sync_db_query)`. 3) Bounded Semaphore: Wrap calls in an `asyncio.Semaphore(100)` to fail fast or return HTTP 429 when concurrency exceeds thread pool capacity, protecting memory and database connection limits.",
        [
            "Identifies that asyncio.to_thread uses the default executor capped at min(32, cpu_count + 4) threads",
            "Explains that 200 concurrent requests queue behind the 32 threads, causing massive queue wait latency",
            "Prescribes creating dedicated ThreadPoolExecutor instances sized to the workload and guarded by semaphores"
        ],
        [
            "Recommends removing all threads and running synchronous database queries directly on the main event loop"
        ]
    ),
    (
        "B69_2_15",
        "explain",
        "medium",
        "explain",
        ["Language Semantics", "Observability"],
        "contextvars / PEP 567",
        "Request-Scoped Context Propagation with contextvars in Async Frameworks",
        "Why does using standard `threading.local()` fail completely for storing request-scoped metadata (like `request_id` or `tenant_id`) in asynchronous frameworks like FastAPI or Starlette, and how does `contextvars` (PEP 567) guarantee context isolation and context copying across concurrent coroutines?",
        "Why threading.local() Fails in Asyncio: 1) Many Coroutines, One Thread: `threading.local()` associates data with the physical operating system thread. In an asynchronous framework, thousands of concurrent HTTP requests execute cooperatively on the *exact same single OS thread*. If Request A stores its `request_id` in `threading.local()`, Request B running on the same thread will read and overwrite Request A's data, causing severe cross-request data leaks and corrupted audit logs. How `contextvars` Solves Context Isolation: 1) Coroutine Context Isolation: `contextvars.ContextVar('request_id')` associates data with the *logical execution context* of the current coroutine, not the thread. Each coroutine task has its own context. 2) Context Inheritance on Task Creation: When `asyncio.create_task(my_coro())` is invoked, CPython captures a shallow copy of the current `contextvars.Context` and binds it to the new task. Child coroutines inherit parent metadata without polluting the parent or sibling contexts. 3) Thread Bridging via `copy_context()`: If offloading work to an OS thread via `ThreadPoolExecutor`, context can be propagated explicitly: `ctx = contextvars.copy_context(); executor.submit(ctx.run, blocking_fn)`, ensuring logs inside worker threads retain the originating request ID.",
        [
            "Explains that threading.local() binds to the OS thread, leaking data across concurrent async coroutines on the same thread",
            "Defines contextvars as binding to the logical coroutine execution context with automatic child task inheritance",
            "Demonstrates propagating context to external threads using contextvars.copy_context() and ctx.run()"
        ],
        [
            "Claims contextvars are global variables stored in environment files"
        ]
    ),
    (
        "B69_2_16",
        "diagnose",
        "hard",
        "debugging",
        ["Memory Management", "Web Architecture"],
        "FastAPI / Closures",
        "Memory Retention via Circular Closures in Route Decorators",
        "A FastAPI service leaks memory at a rate of 50MB per hour. You use a memory profiler and discover that thousands of `Request` objects, database sessions, and large response payloads are permanently retained in heap memory. A code audit reveals that a custom endpoint decorator wraps routes: `def track_request(fn): def wrapper(*args, **kwargs): ... return wrapper`. How can decorators capturing request objects create circular closures that prevent garbage collection in long-lived web applications?",
        "Mechanism of the Closure Memory Leak: 1) Lexical Scope Retention: In Python, when an inner function (closure) is defined inside an outer function, the inner function holds a reference to the outer function's cell variables (`__closure__`). 2) Decorator Scope Pollution: If a developer mistakenly instantiates or references request-scoped state *at decorator evaluation time* or attaches the inner wrapper function to a long-lived registry (such as a global metric registry, Prometheus collector, or middleware router list), the wrapper's `__closure__` remains pinned in global memory for the lifetime of the process. 3) Bound Method Cycles: If the route handler is a method on a stateful class (`self.handler`), and the decorator captures `self`, while `self` stores a list of recent request objects or decorated handlers, a circular reference cycle forms: `Global Registry -> Wrapper -> __closure__ -> Frame/Locals -> Request -> Database Session -> Connection`. 4) Prevention: Never store request-scoped data in decorator-level variables. Use `functools.wraps` properly, keep decorators purely functional and stateless, pass request objects strictly as runtime arguments, and store per-request metrics using `contextvars` rather than closure caches.",
        [
            "Explains that closures capture outer variables in cell objects (__closure__), retaining referenced memory graphs",
            "Identifies attaching wrapper functions to global registries or stateful classes creating uncollected reference chains",
            "Prescribes keeping decorators strictly stateless and managing per-request state via runtime parameters or contextvars"
        ],
        [
            "Claims decorators in Python are automatically deleted after each HTTP request"
        ]
    ),
    (
        "B69_2_17",
        "explain",
        "medium",
        "explain",
        ["Web Architecture", "Networking"],
        "ASGI / TCP",
        "ASGI Connection State and Socket Backpressure",
        "When an ASGI server (like Uvicorn) streams data to a slow client (e.g., a mobile phone on a 2G network downloading a 50MB file), how does the ASGI specification implement socket backpressure through the `send` callable, and why does an un-buffered producer avoid filling application memory?",
        "Socket Backpressure in ASGI: 1) The Problem: If a backend producer generates 50MB of data in 100 milliseconds, but the slow mobile client can only consume 50KB per second, buffering all 50MB in application memory would exhaust server RAM if hundreds of slow clients download concurrently. 2) The ASGI Backpressure Mechanism: In the ASGI specification, the `send` callable is an *asynchronous coroutine*: `await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})`. 3) Flow Control via Kernel Buffers: When the server sends a chunk, Uvicorn writes it to the underlying OS socket buffer. When the OS TCP socket send buffer fills up (because the client's TCP ACK packets are delayed), the OS socket becomes unwritable. Uvicorn pauses the resolution of the `await send(...)` future. 4) Producer Throttling: Because `send` is awaited, the backend generator coroutine is suspended! It stops fetching the next row from the database and stops allocating new chunks in memory. As the slow client gradually receives packets and frees socket buffer space, the kernel marks the socket writable, Uvicorn resolves `send()`, and the generator resumes. Memory consumption remains strictly bounded at $O(1)$ chunk size regardless of client download speed.",
        [
            "Explains that ASGI send() is an asynchronous coroutine that pauses resolution when OS socket buffers fill",
            "Describes kernel TCP window and socket buffer exhaustion propagating backpressure to the application layer",
            "Shows that awaiting send() suspends the producer generator, bounding memory to O(1) buffer sizes"
        ],
        [
            "Claims Uvicorn sends data directly through satellite networks without TCP buffers"
        ]
    ),
    (
        "B69_2_18",
        "concept",
        "easy",
        "concept",
        ["Web Architecture", "Standards"],
        "WSGI vs ASGI",
        "WSGI vs ASGI: Interface Architecture and Protocol Contrasts",
        "Compare the interface architecture of WSGI (PEP 3333) with ASGI (Asynchronous Server Gateway Interface). What are the fundamental differences in how request scopes, input streams, and response streaming are handled between the two standards?",
        "1) WSGI (Web Server Gateway Interface - PEP 3333): Architecture: Synchronous, single-callable interface: `application(environ, start_response)`. Request Scope: The `environ` dictionary contains CGI-style headers and an input stream (`wsgi.input`). Input/Output: Synchronous blocking I/O: `environ['wsgi.input'].read()` blocks the OS thread. The application calls `start_response(status, headers)` and returns an iterable of byte chunks. Limitations: Fundamentally tied to synchronous 1-thread-per-request execution; incapable of natively handling WebSockets, long-polling, or HTTP/2 multiplexing. 2) ASGI (Asynchronous Server Gateway Interface): Architecture: Asynchronous 3-parameter callable: `async def application(scope, receive, send)`. Request Scope: The `scope` dictionary contains connection metadata (protocol type: `'http'` or `'websocket'`, path, headers). Input/Output: Event-driven push/pull channels. The application calls `await receive()` to receive incoming HTTP body chunks or WebSocket frames, and `await send()` to push response headers and body chunks. Capabilities: Supports asynchronous HTTP, WebSockets, Server-Sent Events (SSE), and bidirectional streaming over a single unified interface.",
        [
            "Contrasts WSGI synchronous callable (environ, start_response) with ASGI async 3-tuple (scope, receive, send)",
            "Highlights WSGI's blocking thread-per-request model vs ASGI's event-driven async channel streaming",
            "Identifies ASGI's native support for WebSockets, HTTP/2, and long-lived bidirectional streaming"
        ],
        [
            "Claims WSGI is written in Python while ASGI is written in Java"
        ]
    ),
    (
        "B69_2_19",
        "scenario",
        "hard",
        "scenario",
        ["Web Architecture", "Zero Downtime Deployments"],
        "Gunicorn / Uvicorn / Kubernetes",
        "Graceful Shutdown Coordination between Gunicorn, Uvicorn, and Kubernetes",
        "During a rolling update of a FastAPI microservice managed by Gunicorn with Uvicorn workers (`gunicorn -k uvicorn.workers.UvicornWorker`), clients experience intermittent `HTTP 502 Bad Gateway` errors. You discover that when Kubernetes terminates old pods, Gunicorn immediately terminates worker processes while in-flight requests are still running. How do you configure Gunicorn timeouts, Uvicorn workers, and Kubernetes `preStop` hooks to achieve zero-downtime rolling deploys?",
        "Why 502 Errors Occur during Rolling Deployments: 1) Race Condition on Pod Deletion: When Kubernetes deletes a pod, two actions happen concurrently: A) The kubelet sends `SIGTERM` to the container. B) The Kubernetes endpoint controller removes the pod IP from the Service endpoint list and updates iptables / kube-proxy on all cluster nodes. 2) If Gunicorn receives `SIGTERM` and begins terminating workers before kube-proxy has finished removing the pod IP from iptables, upstream load balancers (or NGINX ingress) continue routing new client traffic to the terminating pod, causing immediate connection refused / 502 Bad Gateway errors. Zero-Downtime Configuration: 1) Kubernetes `preStop` Hook: Add a preStop sleep hook to the container spec: `lifecycle: { preStop: { exec: { command: ['/bin/sh', '-c', 'sleep 10'] } } }`. When deletion begins, the pod sleeps for 10 seconds before sending `SIGTERM` to Gunicorn, giving Kubernetes ingress proxies ample time to remove the pod IP and cease routing new traffic. 2) Gunicorn Graceful Timeout: Configure Gunicorn with `--graceful-timeout 30` and `--timeout 60`. When `SIGTERM` finally arrives, Gunicorn stops accepting new connections and gives active Uvicorn workers 30 seconds to finish in-flight HTTP requests naturally before force-killing. 3) Kubernetes `terminationGracePeriodSeconds`: Ensure `terminationGracePeriodSeconds` (e.g., 45s) is greater than preStop sleep + Gunicorn graceful timeout.",
        [
            "Explains the race condition between SIGTERM pod termination and kube-proxy endpoint removal causing 502 errors",
            "Implements a Kubernetes preStop sleep hook (e.g. sleep 10) to allow ingress proxies to drain traffic first",
            "Configures Gunicorn --graceful-timeout to allow in-flight requests to complete before process shutdown"
        ],
        [
            "Recommends setting Gunicorn worker count to 1 to prevent concurrency"
        ]
    ),
    (
        "B69_2_20",
        "concept",
        "easy",
        "concept",
        ["Web Architecture", "Database Architecture"],
        "FastAPI / SQLAlchemy",
        "FastAPI Dependency Injection Lifecycle: yield Dependencies and Rollback",
        "In FastAPI, how does a `yield` dependency (such as `async def get_db(): db = Session(); try: yield db; finally: db.close()`) manage resource lifecycles across an HTTP request, and how do you ensure unhandled endpoint exceptions trigger an automatic database rollback?",
        "1) The Lifecycle of a `yield` Dependency: A `yield` dependency acts as an asynchronous context manager scoped to the HTTP request: A) Setup Phase: Before the route handler executes, FastAPI executes the code *before* the `yield` statement (e.g., creating the database session). B) Execution Phase: The yielded object (`db`) is injected as a parameter into the route handler. The endpoint executes business logic and returns a response. C) Teardown Phase: After the response is sent (or if an exception occurs), FastAPI resumes the dependency generator immediately *after* the `yield` statement, executing the `finally` block to close connections and release resources. 2) Ensuring Automatic Rollback on Exceptions: If an unhandled exception occurs inside the endpoint: A) The exception bubbles through the dependency. B) To guarantee transaction integrity, structure the dependency with explicit error handling: `try: yield db; await db.commit(); except Exception: await db.rollback(); raise; finally: await db.close()`. C) If the endpoint fails, the `except` block catches the error, rolls back uncommitted SQL mutations, re-raises the exception for FastAPI's exception handlers, and the `finally` block safely returns the connection to the pool.",
        [
            "Explains that code before yield executes before the endpoint, and code after yield executes during response teardown",
            "Structures try/except/finally blocks around yield to execute db.rollback() upon unhandled endpoint errors",
            "Ensures connections are cleanly closed or returned to the pool in the finally block"
        ],
        [
            "Claims FastAPI dependencies run once when the server boots and never run again"
        ]
    )
]

def run_batch():
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[7]) or LEAK.search(q[8]):
            print(f"PROMPT LEAK DETECTED in: {q[7]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[7] for q in Q]
    
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
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[7][:50]}...")
            rejected.append(q)
        else:
            print(f"ACCEPTED (Sim: {max_sim:.2f}): {q[7][:60]}...")
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 2).")
    if len(rejected) > 0:
        print("Stopping due to rejections.")
        sys.exit(1)
        
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "role": ROLE,
            "applicable_roles": ["Backend Developer", "Software Engineer"],
            "primary_skill": q[4][0],
            "skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": q[5],
            "topic": q[6],
            "category": "Software Engineering",
            "intent": q[1],
            "difficulty": q[2],
            "question_type": q[3],
            "question": q[7],
            "ideal_answer": q[8],
            "expected_answer": q[8],
            "evaluation_rubric": {
                "strong_indicators": q[9],
                "weak_indicators": q[10]
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
        
    role_counts = Counter(r.get("primary_role") or r.get("role") for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT PART 2")
    print("========================================")
    print(f"Batch: 69 Part 2")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
