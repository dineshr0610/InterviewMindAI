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
        "B69_3_1",
        "explain",
        "hard",
        "explain",
        ["Multiprocessing", "Operating Systems"],
        "multiprocessing",
        "Process Startup Methods: fork vs spawn vs forkserver Deadlocks",
        "In Python's `multiprocessing`, what is the architectural difference between `fork`, `spawn`, and `forkserver` process startup methods? Why is using `fork` in multi-threaded Python applications a recipe for immediate deadlocks, and why did Python change the default start method on macOS (and planned for Linux) away from `fork`?",
        "Process Startup Methods in CPython: 1) `fork` (POSIX): The OS kernel clones the parent process via the `fork()` syscall. Memory pages are shared via Copy-on-Write (CoW). It is extremely fast because it avoids re-initializing the Python runtime. 2) The Multi-Threaded Fork Deadlock Hazard: The POSIX specification states that when a multi-threaded process calls `fork()`, *only the calling thread* is duplicated into the child process; all other threads instantly vanish without running destructors. If Thread 2 in the parent held an internal mutex (such as the CPython memory allocator lock, an import lock, a logging lock, or a database driver lock) at the exact microsecond Thread 1 called `fork()`, that lock remains permanently in the 'locked' state in the child process. However, the thread that owned the lock does not exist in the child! The child process attempts to acquire the lock (e.g., calling `logging.info()` or allocating memory) and immediately deadlocks forever. 3) `spawn`: Starts a completely fresh Python interpreter process via `execve()`. Only explicitly passed arguments are pickled and transmitted. It is 100% immune to thread lock deadlocks, but has higher startup latency and requires all target functions and arguments to be picklable. 4) `forkserver`: Spawns a dedicated single-threaded server process at startup. When new workers are needed, the forkserver forks itself. Because the forkserver is guaranteed single-threaded, it provides fast CoW startup with zero multi-threaded lock deadlocks.",
        [
            "Explains that fork() only duplicates the calling thread, leaving locks held by other threads permanently deadlocked in the child",
            "Identifies spawn as starting a clean Python interpreter via execve, eliminating lock inheritance at the cost of higher startup latency",
            "Defines forkserver as maintaining a pristine single-threaded process to fork safely without multi-threaded deadlocks"
        ],
        [
            "Claims fork startup is dangerous because child processes copy the parent's monitor resolution"
        ]
    ),
    (
        "B69_3_2",
        "implement",
        "hard",
        "implement",
        ["Multiprocessing", "Linux / OS"],
        "multiprocessing / ctypes / prctl",
        "Orphan Process Prevention via PR_SET_PDEATHSIG in Linux Workers",
        "In a microservice architecture, a Python parent process spawns multiple worker subprocesses using `multiprocessing.Process`. If the parent process is killed abruptly by the Linux OOM Killer (`SIGKILL -9`), the child processes continue running in the background as orphaned processes re-parented to `init` (PID 1), consuming 100% of CPU and preventing new parent deployments from binding ports. How do you use Linux `prctl(PR_SET_PDEATHSIG, SIGTERM)` via `ctypes` in child process initializers to guarantee automatic child termination upon parent death?",
        "Orphan Process Mechanics and Solution: 1) Why Standard Cleanup Fails on SIGKILL: When a parent process receives `SIGKILL`, it is terminated immediately by the OS kernel without running Python signal handlers, `atexit` callbacks, or `finally` blocks. The child processes are re-parented to PID 1 (systemd/init) and keep executing indefinitely. 2) The Linux `PR_SET_PDEATHSIG` Mechanism: Linux provides a specific kernel-level process control flag: `PR_SET_PDEATHSIG`. When set on a child process, the Linux kernel automatically delivers a specified signal (e.g., `SIGTERM`) to the child process the exact microsecond its parent process terminates, even if the parent died from `SIGKILL`, crash, or power loss. 3) Implementation via ctypes in Worker Initializer: Inside the worker target function or process initializer: `import ctypes; libc = ctypes.CDLL('libc.so.6'); PR_SET_PDEATHSIG = 1; SIGTERM = 15; libc.prctl(PR_SET_PDEATHSIG, SIGTERM)`. 4) Guarding Against Race on Startup: If the parent died *between* the `fork()` syscall and the execution of `prctl()`, the child may already be orphaned to PID 1. Guard against this by checking `if os.getppid() != original_parent_pid: os._exit(1)` immediately after calling `prctl()`.",
        [
            "Explains that SIGKILL aborts parents without executing atexit or finally blocks, re-parenting children to PID 1",
            "Implements libc.prctl(PR_SET_PDEATHSIG, SIGTERM) via ctypes to instruct the Linux kernel to kill children upon parent exit",
            "Validates os.getppid() immediately after prctl to prevent race conditions where parent died before flag assignment"
        ],
        [
            "Suggests having child processes ping the parent over an HTTP REST API every second"
        ]
    ),
    (
        "B69_3_3",
        "diagnose",
        "medium",
        "debugging",
        ["Multiprocessing", "Signal Handling"],
        "multiprocessing.Pool",
        "Signal Propagation Deadlocks in multiprocessing.Pool under SIGINT",
        "A developer writes a data pipeline using `multiprocessing.Pool(4)`. When running the script in a terminal, pressing `Ctrl+C` (`SIGINT`) causes the terminal to freeze completely. The developer is forced to open another terminal and run `killall -9 python`. You inspect the code and see that each worker process sets a custom signal handler: `signal.signal(signal.SIGINT, custom_handler)`. Why does custom signal handling in child pool workers deadlock `multiprocessing.Pool`, and what is the proper pattern for graceful keyboard interruption?",
        "Root Cause: When the user presses `Ctrl+C`, the operating system terminal driver broadcasts `SIGINT` to the *entire foreground process group*, delivering the signal simultaneously to both the parent process AND all 4 child worker processes. 1) Internal Pool Architecture: A `multiprocessing.Pool` relies on multiple internal threads in the parent (Task Handler, Result Handler, Worker Handler) communicating with child processes over IPC pipes/queues. 2) The Deadlock Mechanism: If child processes intercept `SIGINT` with a custom handler that catches or ignores the signal, or attempts to execute cleanup while waiting on an IPC pipe, the child refuses to terminate. Meanwhile, the parent's default `SIGINT` handler catches `KeyboardInterrupt` and attempts to terminate the pool by calling `pool.terminate()` and `pool.join()`. If the child is caught in an un-timed IPC read/write or blocked on a pipe, `pool.join()` blocks forever waiting for the children to exit. Proper Pattern: 1) Ignore Signals in Children: In the pool initializer, set child processes to ignore `SIGINT`: `def init_worker(): signal.signal(signal.SIGINT, signal.SIG_IGN)`. 2) Let Parent Handle Shutdown: When `SIGINT` arrives, children ignore it and keep working; only the parent catches `KeyboardInterrupt`. The parent calls `pool.terminate()` followed by `pool.join()`, cleanly sending termination signals to the child workers without deadlocks.",
        [
            "Identifies that Ctrl+C sends SIGINT to the entire process group, causing parent and children to race on signal handling",
            "Explains that custom child handlers prevent children from exiting while parent pool.join() waits indefinitely",
            "Prescribes ignoring SIGINT in child workers via pool initializer (signal.SIG_IGN) and letting the parent coordinate pool.terminate()"
        ],
        [
            "Claims Ctrl+C is disabled by Python when running on multi-core computers"
        ]
    ),
    (
        "B69_3_4",
        "diagnose",
        "hard",
        "debugging",
        ["Multiprocessing", "Concurrency"],
        "multiprocessing.Queue",
        "The multiprocessing.Queue Feeder Thread Deadlock on Process Join",
        "A developer writes a multi-process script: `q = multiprocessing.Queue(); p = multiprocessing.Process(target=worker, args=(q,)); p.start(); q.put(large_data); p.join()`. The script hangs indefinitely at `p.join()`. Taking a stack trace reveals that `worker` exited normally, yet `p.join()` refuses to return. Why does putting data into a `multiprocessing.Queue` before joining a child cause this deadlock, and how does the queue's background 'feeder thread' behave?",
        "Root Cause: The Hidden Feeder Thread and Pipe Buffers: 1) Architecture of `multiprocessing.Queue`: A `multiprocessing.Queue` is NOT a simple OS pipe. It is composed of a Python pipe, an in-memory deque buffer, and an internal background thread called the 'Feeder Thread'. 2) How `put()` Operates: When `q.put(large_data)` is called, the data is placed into the in-memory deque buffer immediately. The background Feeder Thread is responsible for serializing the object and flushing bytes into the underlying OS pipe. 3) The Deadlock Sequence: A) If `large_data` exceeds the OS pipe buffer capacity (typically 64KB on Linux), the Feeder Thread blocks waiting for the other end of the pipe to read bytes. B) The child process finishes its task without reading all data (or exits). C) The main process calls `p.join()`. D) By default, Python processes that use a `multiprocessing.Queue` register an `atexit` handler that automatically calls `q.join_thread()`. `join_thread()` blocks until the Feeder Thread flushes all buffered items into the pipe. E) Because the child process has terminated, nobody will ever read from the pipe! The Feeder Thread blocks forever trying to flush data, and `p.join()` blocks forever waiting for the Feeder Thread. Resolution: 1) Consume all queue data before calling `p.join()`. 2) Or call `q.cancel_join_thread()` before `p.join()` to explicitly tell the feeder thread to discard buffered data upon exit.",
        [
            "Explains that multiprocessing.Queue uses an internal background Feeder Thread to flush buffer deque items to OS pipes",
            "Identifies that large data exceeding pipe buffer capacity blocks the Feeder Thread until the pipe is read",
            "Resolves deadlock by consuming queue data before p.join() or calling q.cancel_join_thread() to discard unread buffers"
        ],
        [
            "Claims multiprocessing.Queue can only store up to 5 bytes of data"
        ]
    ),
    (
        "B69_3_5",
        "scenario",
        "medium",
        "scenario",
        ["Multiprocessing", "Memory Management"],
        "multiprocessing.shared_memory",
        "Shared Memory Lifecycle and Orphaned /dev/shm Segment Leaks",
        "A machine learning service uses Python 3.8+'s `multiprocessing.shared_memory.SharedMemory` to pass 2GB NumPy arrays between parent and child processes with zero copy. Over a weekend, child processes crash occasionally due to uncaught data validation exceptions. On Monday morning, the server crashes with `OSError: [Errno 28] No space left on device`, but `df -h` shows disk drives are 90% empty. You check `/dev/shm` and discover hundreds of orphaned shared memory files. Why did shared memory leak, and how do you ensure bulletproof cleanup?",
        "Root Cause: Distinction between `close()` and `unlink()`: 1) POSIX Shared Memory Semantics: When `SharedMemory(create=True, size=...)` is called on Linux, the kernel creates a POSIX shared memory file descriptor under `/dev/shm` (a tmpfs RAM-backed filesystem). 2) Two-Step Cleanup Requirement: A) `shm.close()`: Detaches the shared memory mapping from the current process's virtual memory space. It does NOT delete the shared memory segment! B) `shm.unlink()`: Instructs the operating system kernel to destroy and free the shared memory segment from `/dev/shm`. Exactly ONE process must call `unlink()` when all processes are done with it. 3) Why Crashes Leak Memory: If a child or parent process terminates abruptly (uncaught exception, segfault, or SIGKILL) before calling `shm.unlink()`, the 2GB shared memory segment remains allocated in `/dev/shm` indefinitely. Because `/dev/shm` uses system RAM, accumulating hundreds of 2GB segments fills `/dev/shm` completely, throwing `No space left on device`. Bulletproof Cleanup Strategy: 1) Use `SharedMemoryManager`: Instead of manual instantiation, use `multiprocessing.managers.SharedMemoryManager()`, which runs a dedicated supervisor process to manage and guarantee unlinking. 2) Crash Cleanup Hook: Register `atexit` handlers and `try...finally` blocks. 3) Startup Orphan Sweeper: On application boot, inspect `/dev/shm/psm_*` and unlink stale segments from prior crashed runs.",
        [
            "Differentiates shm.close() (detaches virtual mapping) from shm.unlink() (destroys the OS shared memory segment)",
            "Explains that unhandled crashes leave orphaned /dev/shm POSIX segments consuming system RAM",
            "Prescribes using SharedMemoryManager or startup sweeper routines to guarantee segment unlinking"
        ],
        [
            "Claims /dev/shm is a physical USB drive plugged into the motherboard"
        ]
    ),
    (
        "B69_3_6",
        "explain",
        "hard",
        "explain",
        ["Multiprocessing", "Resilience"],
        "concurrent.futures / ProcessPoolExecutor",
        "ProcessPoolExecutor Crash Recovery and BrokenProcessPool Failures",
        "When using `concurrent.futures.ProcessPoolExecutor`, if a worker process crashes due to a C-level segmentation fault or is killed by the OS kernel (`kill -9`), all future tasks submitted to the executor immediately raise `concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly while the future was running`. Why does a single worker death break the entire pool permanently, and how do you architect resilient process supervision?",
        "Why ProcessPoolExecutor Breaks Permanently: 1) Internal State Invalidation: `ProcessPoolExecutor` uses shared internal pipes to coordinate task queues and result queues across worker processes. When a worker process dies abruptly via `SIGKILL` or segfault, it may have been in the middle of reading a task from the pipe or writing a pickled result. 2) Undetectable State Corruption: The executor's internal management thread detects that a worker process terminated unexpectedly. Because Python cannot verify whether the task completed, whether data on the IPC pipe was corrupted, or whether IPC locks were left in a deadlocked state, the executor assumes the entire IPC communication channel is unrecoverable. 3) Terminal Broken State: To prevent silent data corruption, the executor marks itself as 'broken'. All currently pending futures and any subsequent calls to `submit()` immediately raise `BrokenProcessPool`. The pool refuses to accept further work and cannot heal itself. Resilient Architecture: 1) Dynamic Pool Re-instantiation: Wrap executor calls in an abstraction layer: if `BrokenProcessPool` is caught, immediately shut down the dead executor (`executor.shutdown(wait=False, cancel_futures=True)`), instantiate a fresh `ProcessPoolExecutor`, and retry the affected jobs. 2) Isolated Execution via Subprocesses: For dangerous tasks that risk native segfaults (e.g., untrusted C libraries), execute them via isolated one-shot subprocesses (`subprocess.run()`) rather than persistent pooled workers.",
        [
            "Explains that unexpected worker death risks pipe buffer corruption and deadlocked IPC synchronization state",
            "Identifies that ProcessPoolExecutor intentionally enters a terminal BrokenProcessPool state to prevent corrupt executions",
            "Prescribes recreating the executor dynamically upon BrokenProcessPool or isolating risky tasks in one-shot subprocesses"
        ],
        [
            "Claims BrokenProcessPool means the CPU broke a physical transistor"
        ]
    ),
    (
        "B69_3_7",
        "concept",
        "easy",
        "concept",
        ["Multiprocessing", "Serialization"],
        "pickle / multiprocessing",
        "Pickling Limitations in Multiprocessing and Alternative Serializers",
        "When submitting tasks to Python's `multiprocessing.Pool` or `ProcessPoolExecutor`, submitting a lambda function, a nested function, or an instance method frequently fails with `_pickle.PicklingError: Can't pickle <function <lambda>>: attribute lookup failed`. Why does standard Python `pickle` fail on these callables, and how do libraries like `dill` or `pathos` overcome this?",
        "Why Standard Pickle Fails: 1) Pickling by Name, Not Bytecode: CPython's standard `pickle` module does not serialize the actual bytecode or execution state of function objects. Instead, it pickles functions *by name and module path* (`module.__name__` + `.` + `function.__qualname__`). 2) The Importability Requirement: During deserialization, the unpickler simply imports the module and looks up the function name in the module dictionary. Lambdas (which have name `<lambda>`) and nested functions defined inside another function are NOT top-level attributes in the module namespace; they cannot be looked up by name, causing `PicklingError`. How `dill` / `pathos.multiprocessing` Solve This: `dill` extends Python's pickle protocol to serialize the actual underlying CPython `CodeType` object, bytecode (`co_code`), constants (`co_consts`), defaults, and closure cell variables (`__closure__`). It serializes the entire functional definition and recreates the function dynamically in the child process without requiring it to exist as a named top-level module attribute.",
        [
            "Explains that standard pickle serializes functions by qualified module name, not by code or bytecode",
            "Identifies that lambdas and nested functions lack top-level module attributes, causing lookup failures",
            "Explains that dill/pathos serialize the actual CodeType, bytecode, and closure cells directly"
        ],
        [
            "Claims pickle fails on lambdas because Python prohibits using anonymous functions on multi-core computers"
        ]
    ),
    (
        "B69_3_8",
        "explain",
        "medium",
        "explain",
        ["Multiprocessing", "Networking"],
        "POSIX / fork",
        "File Descriptor and Socket Inheritance Hazards across Forked Children",
        "In a Python service that establishes database connections and Redis clients at the module level, spawning worker processes via `multiprocessing.Process(target=worker)` using the default `fork` method causes intermittent SSL decryption errors (`SSL_ERROR_SSL`), database transaction corruption, and unexpected timeouts. Why does forking inherit open sockets and file descriptors, and how must client connections be initialized across process boundaries?",
        "The Socket Inheritance Hazard: 1) POSIX Fork Behavior: When a process forks, child processes inherit identical copies of all open file descriptors from the parent. This includes open TCP sockets, database connection handles (psycopg2, SQLAlchemy), and Redis socket connections. 2) Shared Socket Stream Corruption: The parent and all child processes now hold file descriptors pointing to the *exact same underlying OS socket endpoint*! 3) Interleaved Traffic Collision: When Child A sends a SQL query and Child B sends another SQL query over the inherited connection, their TCP packets interleave on the wire. When the database server responds, both children read from the socket concurrently: Child A might read the first half of the TLS packet, and Child B reads the second half. Both processes fail with corrupted TLS frames, broken protocols, or unexpected query responses. Solution: 1) Rule of Process Boundaries: Connections MUST NEVER be opened before forking and shared across children. 2) Post-Fork Initialization: Close parent connections before forking, or initialize database pools and HTTP clients *strictly inside the child worker's target function* (`run()` or pool initializer). 3) SQLAlchemy Engine Disconnect: In SQLAlchemy, call `engine.dispose(close=False)` in the parent before forking so that child processes are forced to establish fresh, independent TCP connections.",
        [
            "Explains that fork() copies open file descriptors, leaving parent and children connected to the same TCP socket",
            "Demonstrates interleaved reads/writes corrupting TLS frames and database protocol state",
            "Prescribes initializing connections strictly post-fork or disposing SQLAlchemy connection pools prior to forking"
        ],
        [
            "Claims child processes cannot use the internet if the parent process is running"
        ]
    ),
    (
        "B69_3_9",
        "concept",
        "easy",
        "concept",
        ["Multiprocessing", "Performance Tuning"],
        "multiprocessing.Array vs SharedMemory",
        "multiprocessing.Array vs multiprocessing.shared_memory.SharedMemory",
        "Compare the legacy `multiprocessing.Array` (ctypes-based) with Python 3.8+'s `multiprocessing.shared_memory.SharedMemory`. What are the performance and architectural differences when sharing large multidimensional numerical data across processes?",
        "1) `multiprocessing.Array`: Architecture: Wraps a flat C array allocated via shared memory using `ctypes` primitives (e.g., `Array('i', 1000)`). Synchronization: Comes bundled with a default `multiprocessing.RLock` to serialize access across processes. Limitations: Accessing elements from Python incurs ctypes unboxing overhead. Slicing creates copies. Reshaping into multidimensional structures requires awkward wrapping, making it slow and cumbersome for complex data structures like NumPy arrays or image frames. 2) `multiprocessing.shared_memory.SharedMemory` (Python 3.8+): Architecture: Allocates raw POSIX shared memory segments accessible via a `memoryview` buffer. Zero-Copy Integration: Can be wrapped directly by `numpy.ndarray(shape, dtype, buffer=shm.buf)` with zero copying and zero conversion overhead. Multiple child processes can read and write multidimensional arrays at native C speeds. Synchronization: Does NOT include an implicit lock; synchronization must be managed explicitly by the developer using `multiprocessing.Lock` or semaphores, providing maximum raw performance for high-throughput data pipelines.",
        [
            "Contrasts ctypes-wrapped Array with raw POSIX SharedMemory accessible via memoryview",
            "Highlights SharedMemory's native zero-copy integration with NumPy ndarrays",
            "Notes that Array includes default RLock synchronization while SharedMemory offers lockless raw performance"
        ],
        [
            "Claims multiprocessing.Array is stored in cloud databases while SharedMemory is stored on disk"
        ]
    ),
    (
        "B69_3_10",
        "concept",
        "easy",
        "concept",
        ["Multiprocessing", "Resource Management"],
        "multiprocessing.Pool / maxtasksperchild",
        "Worker Recycling via maxtasksperchild for Memory Leak Containment",
        "In a batch processing service using `multiprocessing.Pool`, why is configuring `maxtasksperchild` (e.g., `Pool(processes=4, maxtasksperchild=100)`) an essential operational safeguard against gradual memory leaks in third-party C libraries?",
        "The Memory Leak Dilemma in Long-Lived Workers: Many Python applications rely on native C/C++ extensions (OpenCV, GDAL, lxml, TensorFlow) or complex object graphs that suffer from minor, slow memory fragmentation or native memory leaks. Over 24 hours of continuous task execution, worker processes steadily accumulate resident memory (RSS), eventually exhausting server RAM and crashing the machine. How `maxtasksperchild` Solves This: 1) Automatic Recycling: `maxtasksperchild=100` instructs the `multiprocessing.Pool` coordinator to automatically terminate a worker process after it has executed exactly 100 tasks, and immediately spawn a fresh, clean replacement worker process. 2) Complete OS Memory Reclamation: When the operating system terminates the worker process, the kernel automatically reclaims 100% of the process's address space, heap allocations, C-extension memory leaks, and fragmented PyMalloc arenas. 3) Zero Downtime: The recycling happens seamlessly in the background between tasks without dropping queued jobs or interrupting the overall batch pipeline.",
        [
            "Identifies native C-extension memory leaks and PyMalloc fragmentation accumulating in long-lived worker processes",
            "Explains that maxtasksperchild terminates workers after N tasks and spawns clean replacements",
            "Highlights that OS process termination guarantees 100% reclamation of all leaked memory and fragmentation"
        ],
        [
            "Claims maxtasksperchild limits the total number of users who can visit a website"
        ]
    ),
    (
        "B69_3_11",
        "diagnose",
        "hard",
        "debugging",
        ["Distributed Workers", "Task Queues"],
        "Celery / RabbitMQ / Redis",
        "Celery Prefetch Multiplier and Head-of-Line Task Starvation",
        "A company processes two types of tasks in Celery: Fast tasks (taking 100ms) and Heavy tasks (taking 10 minutes). They have 4 Celery worker pods with 4 concurrency slots each (16 total slots). Suddenly, 10,000 fast tasks sit in the queue waiting for hours, while 3 worker pods are completely idle with 0% CPU. You inspect the busy worker pod: it has pre-fetched 64 heavy tasks and queued them in its local memory. Why does Celery's default `worker_prefetch_multiplier = 4` cause this head-of-line blocking, and how do you resolve it?",
        "Root Cause: Celery Prefetch Multiplier Mechanics: 1) How Prefetching Works: By default, Celery configures `worker_prefetch_multiplier = 4`. When a worker connects to the broker, it pre-fetches $concurrency \times multiplier$ tasks into its local process memory buffer to minimize network round-trip latency. For a 4-concurrency worker, it pulls $4 \times 4 = 16$ tasks (or with multiple workers, up to 64 tasks). 2) Head-of-Line Starvation: When a burst of heavy 10-minute tasks arrives, Worker 1 pulls 16 heavy tasks into its local buffer. The other workers may be busy with initial tasks. Worker 1 executes 4 tasks concurrently, while the remaining 12 heavy tasks sit buffered in Worker 1's local RAM. Even when Workers 2, 3, and 4 finish their work and become completely idle, they CANNOT steal the buffered tasks from Worker 1! The tasks are locked in Worker 1's memory, starving the cluster. Resolution: 1) Set `worker_prefetch_multiplier = 1`: This restricts workers to fetching only 1 reserve task per concurrency slot. 2) Enable `task_acks_late = True`: Tasks are acknowledged only AFTER execution completes, ensuring unacknowledged tasks remain in the broker or can be re-routed. 3) Queue Routing Segregation: The ultimate architectural fix is separating workloads into dedicated queues: route fast tasks to a `fast_queue` with high concurrency, and heavy tasks to a `heavy_queue` with dedicated workers.",
        [
            "Explains that prefetch_multiplier calculates local task buffer size ($concurrency \\times multiplier$)",
            "Identifies head-of-line blocking where one worker hoards long-running tasks in local RAM while other workers sit idle",
            "Prescribes setting worker_prefetch_multiplier = 1, task_acks_late = True, and isolating tasks into dedicated queues"
        ],
        [
            "Suggests increasing worker_prefetch_multiplier to 1,000 to speed up the tasks"
        ]
    ),
    (
        "B69_3_12",
        "scenario",
        "medium",
        "scenario",
        ["Distributed Workers", "Task Queues"],
        "Celery / SQS / Redis",
        "Visibility Timeout vs Long-Running Tasks: Duplicate Concurrent Execution",
        "A Celery task generates massive monthly PDF reports, taking an average of 45 minutes to execute. The task broker is configured with a default Visibility Timeout of 30 minutes. Exactly 30 minutes into report generation, a second Celery worker picks up the exact same report task and begins generating it again. At minute 45, both workers attempt to save the report, corrupting file storage. Explain how Visibility Timeout expiration causes duplicate task execution, and how to configure Celery correctly.",
        "Mechanism of Duplicate Execution: 1) What Visibility Timeout Is: In message brokers like Amazon SQS or Redis (when used as a Celery broker), when a worker pulls a task, the broker does not delete the message; it hides it from other workers for a configured duration known as the 'Visibility Timeout' (e.g., 30 minutes). 2) Expiration Race: If a worker executes a task that takes 45 minutes, at minute 30 the Visibility Timeout expires while Worker 1 is still actively working! The broker assumes Worker 1 crashed, lost power, or died. 3) Re-delivery: The broker makes the message visible again on the queue. Worker 2 immediately pulls the message and begins executing the exact same task in parallel with Worker 1. At minute 45, both workers attempt conflicting writes. Solution: 1) Increase Visibility Timeout: Configure `broker_transport_options = {'visibility_timeout': 3600 * 2}` (e.g., 2 hours), ensuring the timeout strictly exceeds the maximum possible task execution duration (`time_limit`). 2) Celery Task Hard/Soft Time Limits: Configure `@task(time_limit=1800, soft_time_limit=1700)` to force tasks to abort cleanly *before* the visibility timeout can ever expire. 3) Distributed Locks: Use an entity-level Redis lock (`idempotency_key`) to prevent concurrent executions of the same report.",
        [
            "Explains that Visibility Timeout expiration causes the broker to assume the worker died, re-delivering the active task",
            "Demonstrates parallel concurrent execution by multiple workers causing duplicate processing and storage corruption",
            "Prescribes configuring visibility_timeout to exceed task execution time, combined with strict Celery task time_limits"
        ],
        [
            "Claims Visibility Timeout means the user cannot see the progress bar on the website"
        ]
    ),
    (
        "B69_3_13",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Distributed Workers", "Reliability"],
        "Celery / acks_late",
        "Celery Early Acknowledgment vs Late Acknowledgment (acks_late)",
        "In Celery, what is the architectural difference between default 'Early Acknowledgment' and 'Late Acknowledgment' (`task_acks_late = True`), and why does enabling `acks_late` mandate that all task functions be strictly idempotent?",
        "1) Early Acknowledgment (Default: `task_acks_late = False`): Mechanism: The worker acknowledges the message (sends `basic_ack` to RabbitMQ or deletes from Redis) *immediately when the worker pops the task from the queue, BEFORE beginning execution*. Tradeoff: At-Most-Once Execution. If the worker machine loses power, suffers an unhandled C-extension segmentation fault, or is killed by the Kubernetes OOM Killer while executing, the task is permanently lost! The broker already marked it completed. Suitable only for non-critical, ephemeral tasks (like analytics pings). 2) Late Acknowledgment (`task_acks_late = True`): Mechanism: The worker acknowledges the message *strictly AFTER the task function has successfully completed and returned*. Tradeoff: At-Least-Once Execution. If the worker crashes mid-task, the message is not lost; the broker re-queues it for another worker. 3) Why Idempotency is Mandatory: Because the task was interrupted mid-execution, a retry worker will re-execute the function from line 1. If the function charged a credit card or deducted inventory before crashing, running it again would double-charge the user! Therefore, `task_acks_late = True` strictly mandates that tasks use idempotency keys, atomic database updates, or state machines to guarantee exactly-once business semantics.",
        [
            "Contrasts early acknowledgment (at-most-once, task loss upon crash) with late acknowledgment (at-least-once, zero loss)",
            "Explains that early ack confirms receipt before execution starts, leaving crashes unrecovered",
            "Demonstrates why late ack mandates strict task idempotency to prevent duplicate side effects upon re-delivery"
        ],
        [
            "Claims acks_late makes tasks run 5 days later than scheduled"
        ]
    ),
    (
        "B69_3_14",
        "implement",
        "medium",
        "implement",
        ["Distributed Workers", "Memory Management"],
        "Celery / Worker Supervision",
        "Worker Memory Management: max_tasks_per_child and max_memory_per_child",
        "A Celery worker fleet processing heavy image and PDF manipulations slowly consumes all host RAM over 24 hours. How do you configure `max_tasks_per_child` and `max_memory_per_child` in Celery to automate child process recycling, and how do they differ in execution timing?",
        "Celery Worker Recycling Configuration: 1) `max_tasks_per_child`: Configuration: `worker_max_tasks_per_child = 50`. Mechanics: A worker child process executes up to 50 tasks. Upon completing the 50th task, the child process cleanly exits, and the main Celery supervisor process spawns a fresh replacement child process. Use Case: Bounded execution lifespan that steadily recycles memory without monitoring actual RAM usage. 2) `max_memory_per_child`: Configuration: `worker_max_memory_per_child = 300000` (in kilobytes, e.g., 300MB). Mechanics: After every task completes, the worker checks its current Resident Set Size (RSS) memory consumption via OS syscalls. If memory exceeds 300MB, the child process gracefully exits after completing the current task, and the supervisor replaces it. 3) Key Difference in Timing: Neither setting ever aborts or kills an *active in-flight task*. Both settings perform recycling *cooperatively between tasks*, ensuring zero dropped jobs while permanently capping worker memory bloat.",
        [
            "Configures worker_max_tasks_per_child to recycle workers after a fixed number of completed tasks",
            "Configures worker_max_memory_per_child to recycle workers when RSS memory exceeds a specific threshold",
            "Highlights that recycling occurs cooperatively between tasks, ensuring active tasks are never aborted"
        ],
        [
            "Suggests rebooting the entire AWS cloud account every 20 minutes"
        ]
    ),
    (
        "B69_3_15",
        "scenario",
        "hard",
        "scenario",
        ["Distributed Workers", "Fault Tolerance"],
        "Celery / Serialization",
        "Poison-Pill Tasks and Deserialization Crash Loops in Celery",
        "A malicious user or buggy client enqueues a malformed task payload into Celery. Whenever a Celery worker picks up this message, it raises an uncatchable C-level segfault or unpickling exception inside the Celery daemon loop before task execution begins. The message is re-queued, picked up by Worker 2, crashes Worker 2, and rapidly knocks down all 20 worker processes across the cluster in an infinite crash loop. How do you isolate poison-pill tasks and architect dead-letter quarantine?",
        "The Poison-Pill Crash Loop Mechanism: If a message has a malformed serialization payload (or arguments triggering a crash during unpickling or header parsing), Celery crashes *inside the consumer daemon loop*. If the broker is configured to re-queue unacknowledged messages upon worker disconnection, the poison pill is immediately redelivered to the next available worker, cascading across the entire cluster until all workers are dead. Resolution Architecture: 1) Safe Deserialization: Disallow `pickle` serializer; enforce strict JSON serializer (`task_serializer = 'json'`, `accept_content = ['json']`). JSON deserialization errors raise standard Python exceptions rather than C segfaults. 2) Custom Reject-on-Failure Middleware: Configure `task_reject_on_worker_lost = True` combined with Dead-Letter Exchanges (DLX) in RabbitMQ. When a worker dies unexpectedly, the broker routes the failed message to a DLQ rather than re-queueing to the main queue. 3) Delivery Count Thresholding (RabbitMQ Quorum Queues / SQS MaxReceiveCount): Enforce a maximum delivery attempt limit (e.g., `x-delivery-limit: 3`). Once a message fails 3 times, the broker automatically quarantines it into a dead-letter queue, shielding healthy worker processes from infinite crash loops.",
        [
            "Explains that unhandled deserialization crashes or segfaults trigger re-queues, creating a cluster-wide cascading crash loop",
            "Replaces unsafe pickle serialization with strict JSON serialization to prevent native crash vectors",
            "Configures Dead-Letter Exchanges (DLX) and maximum delivery count thresholds (x-delivery-limit) to quarantine poison messages"
        ],
        [
            "Recommends deleting all queues and starting the business over from scratch"
        ]
    ),
    (
        "B69_3_16",
        "explain",
        "medium",
        "explain",
        ["Distributed Workers", "Scheduling"],
        "Celery Beat / Distributed Locking",
        "Celery Beat Distributed Scheduling and Duplicate Job Prevention",
        "In a Kubernetes deployment, running 3 replicas of a Celery Beat deployment (`celery -A proj beat`) causes scheduled cron tasks (like sending daily customer billing invoices) to trigger 3 times simultaneously. Why is standard Celery Beat incapable of running in a multi-replica high-availability configuration, and how do distributed schedulers like RedBeat or database-backed schedulers solve this?",
        "Why Standard Celery Beat Fails in Multi-Replica Deployments: Standard Celery Beat is a simple single-process scheduler. It maintains an internal schedule in local memory (or a local shelve file `celerybeat-schedule`). It has ZERO distributed coordination, zero consensus protocol, and zero knowledge of other Beat instances. If you scale the Kubernetes deployment to 3 pods, all 3 pods wake up at midnight, all 3 read their schedules, and all 3 publish identical `send_billing_invoice` tasks to the message broker. Solution via Distributed Schedulers: 1) Distributed Lock on Scheduling (RedBeat): RedBeat uses Redis to store the schedule and coordinates execution using distributed Redis locks (`redbeat:lock`). Multiple RedBeat instances can run for high availability, but only the single instance currently holding the distributed lease acquires the authority to publish cron tasks. If the active Beat pod crashes, another standby pod acquires the lease. 2) Database-Backed Schedulers (django-celery-beat): Stores schedules in a relational database with row-level locking or leader election, ensuring exactly one scheduler emits tasks at any scheduled timestamp.",
        [
            "Explains that standard Celery Beat is a single-process local scheduler with zero distributed coordination",
            "Highlights that multiple Beat replicas independently emit duplicate tasks for every cron entry",
            "Prescribes distributed schedulers (RedBeat with Redis locks, or django-celery-beat with database locking) for HA leader election"
        ],
        [
            "Claims Celery Beat coordinates using satellite atomic clocks"
        ]
    ),
    (
        "B69_3_17",
        "explain",
        "medium",
        "explain",
        ["Distributed Workers", "Architecture"],
        "Celery / Redis / RabbitMQ",
        "Priority Queues in Celery: RabbitMQ x-max-priority vs Redis Priority Steps",
        "How do priority queues in Celery differ architecturally when using RabbitMQ as the broker versus using Redis, and what are the operational limitations of Redis's priority emulation?",
        "1) RabbitMQ Native Priority Queues: Mechanism: RabbitMQ implements true server-side message prioritization conforming to AMQP standards using the `x-max-priority` argument on queues (e.g., priority 0 to 10). Internal Behavior: RabbitMQ's Erlang queue engine maintains an internal priority tree. When consumers poll, RabbitMQ delivers the highest-priority message currently in the queue, even if 100,000 lower-priority messages were enqueued earlier. Performance is high, and memory overhead is minimal. 2) Redis Priority Emulation in Celery: Mechanism: Redis does NOT have native message queue prioritization. To emulate priority, Celery creates multiple separate Redis list keys for each priority level using `priority_steps` (e.g., `queue`, `queue\x06\x163`, `queue\x06\x166`, `queue\x06\x169`). Internal Behavior: When a worker polls, it executes a blocking `BRPOP` across all priority list keys in order: `BRPOP queue_9 queue_6 queue_3 queue_0 timeout`. Limitations: Higher CPU and connection overhead in Redis. Priority is inverted if too many steps are defined. Strict priority can cause complete starvation of lower-priority lists during high-priority bursts.",
        [
            "Explains that RabbitMQ uses native server-side priority trees via x-max-priority queue arguments",
            "Explains that Redis emulates priority by generating multiple physical list keys (priority_steps) polled via BRPOP",
            "Identifies Redis limitations: multiple key polling overhead and potential lower-priority starvation"
        ],
        [
            "Claims Redis priority queues sort messages alphabetically by task name"
        ]
    ),
    (
        "B69_3_18",
        "implement",
        "medium",
        "implement",
        ["Distributed Workers", "Workflow Orchestration"],
        "Celery Canvas",
        "Celery Canvas Primitives: Implementing Chords with Distributed Barriers",
        "In a distributed data processing workflow, you need to fan-out and process 100 data partitions in parallel, and then execute a single aggregation task only after ALL 100 parallel tasks have finished successfully. How do you implement this using Celery Canvas's `chord` primitive (`chord(header)(callback)`), and how does the Celery result backend track task completion barriers?",
        "Implementation with Celery Chord: 1) The Chord Structure: In Celery Canvas: `header = [process_partition.s(i) for i in range(100)]; callback = aggregate_results.s(); chord(header)(callback)`. 2) Execution Mechanics: A) The Celery client publishes all 100 `process_partition` tasks to the broker. B) The 100 tasks execute concurrently across all available distributed workers. C) When each task completes, it writes its return value to the Celery Result Backend (e.g., Redis or database). 3) Distributed Barrier Synchronization: In Redis, Celery uses an atomic counter and a set: A) A chord barrier key is created with count 100: `chord:uuid:count = 100`. B) As each of the 100 tasks finishes, the worker executes an atomic decrement in Redis (`DECR chord:uuid:count`). C) The worker that decrements the counter to exactly 0 realizes it is the final task. D) That final worker fetches the accumulated results of all 100 tasks from the backend and immediately enqueues the `aggregate_results` callback task with the collected list of return values.",
        [
            "Implements chord(header)(callback) where header represents parallel tasks and callback is the aggregator",
            "Explains distributed barrier coordination via atomic decrements (DECR) in the result backend",
            "Identifies the final task reaching zero count triggering the execution of the callback task"
        ],
        [
            "Claims chords can only play musical notes on the server's sound card"
        ]
    ),
    (
        "B69_3_19",
        "concept",
        "easy",
        "concept",
        ["Distributed Workers", "Data Consistency"],
        "Celery / Message Ordering",
        "Enforcing Strict FIFO Task Ordering in Distributed Celery Fleets",
        "Why can't a distributed Celery worker cluster running across 10 worker pods guarantee that tasks for a specific customer are processed in strict FIFO order, and how do you architect sequential execution for specific entity IDs?",
        "Why Standard Celery Breaks FIFO Ordering: 1) Concurrent Multi-Worker Consumption: Even if the message broker (like RabbitMQ) stores tasks in FIFO order, multiple worker pods poll the queue concurrently. If Task 1 (Order Created) is picked up by Worker A and Task 2 (Order Cancelled) is picked up by Worker B, network latency, GC pauses, or CPU contention can cause Worker B to finish Task 2 *before* Worker A finishes Task 1, corrupting customer state. 2) Worker Prefetching: Prefetched batches reorder execution across worker nodes. How to Enforce Entity-Level Sequential Execution: 1) Entity-Key Partitioned Queues: Route all tasks for Customer 123 to a dedicated queue with a single dedicated worker concurrency slot (`concurrency = 1`). 2) Distributed Entity Locks: Use Redis distributed locks keyed by entity ID (`lock:customer:123`). When a task runs, it acquires the lock; subsequent tasks for that customer see the lock and delay themselves (`countdown=5`) or re-queue until the prior task releases the lock. 3) State-Machine Version Checks: Attach monotonic sequence numbers (`sequence_id`) to tasks; workers verify that `task.sequence_id == entity.last_processed_sequence + 1` before executing.",
        [
            "Explains that concurrent multi-worker consumption and prefetching cause out-of-order execution across distributed nodes",
            "Designs entity-partitioned single-concurrency queues to guarantee strict FIFO per entity",
            "Utilizes entity-scoped distributed locks or monotonic sequence verification in task handlers"
        ],
        [
            "Claims FIFO ordering can be guaranteed by setting task priority to 0"
        ]
    ),
    (
        "B69_3_20",
        "explain",
        "medium",
        "explain",
        ["Distributed Workers", "Rate Limiting"],
        "Celery / Token Bucket",
        "Task Rate Limiting in Celery: Token Buckets vs Broker Backpressure",
        "When defining a rate limit on a Celery task (`@app.task(rate_limit='100/m')`), how does Celery enforce this limit across workers using the Token Bucket algorithm, and why is task-level rate limiting ineffective at preventing message broker queue backlog growth?",
        "How Celery Enforces Task-Level Rate Limits: 1) Kombu Token Bucket Implementation: When `rate_limit='100/m'` is specified, Celery creates a token bucket managed by the worker's internal consumer timer. Tokens are added to the bucket at a rate of 100 per minute. 2) Local Throttling Delay: When a worker pulls a task from the broker, it checks its local token bucket. If tokens are available, it executes immediately. If tokens are exhausted, the worker calculates the time until the next token is replenished and schedules the task to sleep using the worker's internal timer event loop (`eta` delay), refusing to execute it until the token arrives. Why It Fails to Prevent Broker Queue Backlog: 1) Client Ingestion is Unthrottled: Celery's `rate_limit` only throttles *worker execution speed*; it does NOTHING to stop upstream web APIs from calling `my_task.delay()` 10,000 times per minute! 2) Massive Queue Accumulation: The broker queue will accumulate 9,900 unconsumed tasks every minute. Queue memory expands, latency skyrockets, and broker storage is exhausted. To control backlog growth, rate limiting and backpressure must be enforced at the *API producer ingestion boundary* (e.g., API gateway token buckets), not merely at the worker consumer boundary.",
        [
            "Explains that Celery enforces rate limits via internal worker token buckets delaying task execution timers",
            "Identifies that worker rate limiting does not throttle producer task publishing (.delay())",
            "Demonstrates that unconstrained publishing causes massive broker queue backlog accumulation, requiring edge rate limiting"
        ],
        [
            "Claims rate_limit='100/m' charges the developer $100 per minute on their credit card"
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 3).")
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
    print("POST-BATCH AUDIT PART 3")
    print("========================================")
    print(f"Batch: 69 Part 3")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
