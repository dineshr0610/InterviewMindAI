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
        "B69_1_1",
        "explain",
        "hard",
        "explain",
        ["CPython Internals", "Compiler Design"],
        "CPython",
        "Bytecode Specialization and Adaptive Interpreter Behavior",
        "In Python 3.11+, PEP 659 introduced the Specializing and Adaptive Interpreter. How does CPython detect hot execution loops at runtime, how does it specialize generic bytecodes (like `BINARY_OP` or `LOAD_GLOBAL`) into specialized instructions (such as `BINARY_OP_ADD_INT` or `LOAD_GLOBAL_MODULE`), and what causes a specialized bytecode to de-specialize back to its generic opcode?",
        "CPython's Adaptive Interpreter in Python 3.11+ optimizes execution dynamically without a JIT compiler: 1) Warmup Counters: Every bytecode instruction that can be specialized is paired with an inline cache entry containing an adaptive counter. When an opcode executes, the counter decrements. Once the counter reaches zero (typically after a loop executes the instruction ~8 times), the interpreter flags the bytecode as 'hot' and attempts specialization. 2) Specialization & Inline Caching: CPython inspects the concrete runtime types of the operands. If `BINARY_OP` repeatedly adds two small integers, CPython replaces the generic opcode with a specialized instruction: `BINARY_OP_ADD_INT`. It writes cache metadata (such as type checks and function pointers) directly into inline cache entries (`CACHE` opcodes) following the instruction in the code object. Future executions skip generic type dispatching and execute the fast C path directly. 3) De-specialization: If the instruction encounters an unexpected operand type (e.g., adding a string to an integer, or accessing a global variable whose dictionary version changed), the specialized opcode's guard check fails. CPython de-specializes the instruction back to an adaptive opcode, resets the warmup counter, and eventually reverts to the generic opcode if type polymorphism continues.",
        [
            "Explains adaptive warmup counters identifying hot instructions after repeated executions",
            "Describes replacing generic bytecodes with specialized opcodes (e.g., BINARY_OP_ADD_INT) backed by inline caches",
            "Identifies guard check failures on polymorphic types causing de-specialization back to generic opcodes"
        ],
        [
            "Claims Python 3.11 compiles all Python code to native x86 machine assembly using LLVM"
        ]
    ),
    (
        "B69_1_2",
        "explain",
        "medium",
        "explain",
        ["CPython Internals", "Debugging"],
        "CPython / dis",
        "Disassembly Analysis and Bytecode Cache Entries in Python 3.11+",
        "When disassembling a function using Python's `dis` module in Python 3.11+ (`dis.dis(fn)`), you observe multiple `CACHE` instructions appearing between standard bytecodes, and instruction offsets increment by 2 or more bytes per entry. What is the architectural purpose of these `CACHE` bytecode entries, and why does modifying a function's code object without accounting for inline cache sizes cause interpreter crashes?",
        "In Python 3.11+, CPython redesigned its bytecode representation to support inline caching for the specializing interpreter (PEP 659): 1) Purpose of CACHE entries: A `CACHE` entry is an internal pseudo-instruction that reserves fixed memory space (typically 2, 4, or 8 bytes) immediately following an adaptive opcode within the compiled bytecode sequence. These bytes store runtime cache data: type pointers, dictionary keys, object shape identifiers, and version counters used by specialized instructions (like `LOAD_ATTR_INSTANCE_VALUE`). 2) Instruction Offsets: In Python 3.11, all instructions use 2-byte code units (1 byte opcode, 1 byte argument). An opcode that requires an inline cache is followed by one or more `CACHE` code units, which explains why bytecode offset increments jump by 4, 8, or 10 bytes instead of 2. 3) Risk of Direct Code Object Manipulation: If a developer attempts low-level bytecode manipulation by modifying `fn.__code__.co_code` without strictly preserving the expected number of `CACHE` entries required by each specific opcode, the interpreter's program counter misaligns. CPython will attempt to execute inline cache metadata as executable opcodes, resulting in immediate segmentation faults or interpreter crashes.",
        [
            "Identifies CACHE entries as reserved memory space for inline cache data used by specialized opcodes",
            "Explains that bytecode offsets jump because instructions are followed by 2-byte CACHE code units",
            "Warns that altering co_code without accounting for opcode CACHE allocations causes memory misalignment and crashes"
        ],
        [
            "Claims CACHE entries are temporary files written to the Linux /tmp directory"
        ]
    ),
    (
        "B69_1_3",
        "explain",
        "hard",
        "explain",
        ["CPython Internals", "Language Semantics"],
        "CPython / Frames",
        "Frame Object Internals: f_locals Dictionaries vs Fast Locals Array",
        "Inside a Python function, if a developer writes `locals()['x'] = 100`, the value of local variable `x` remains unchanged in subsequent statements, whereas doing the same at the module level modifies the variable. Explain the CPython implementation difference between module-level dictionaries and function frame objects (`f_locals` vs `fast locals` / `f_localsplus`), and why modifying `f_locals` inside a function has no effect.",
        "Module Scope vs Function Scope Mechanics: 1) Module Scope: At the module (global) level, variables reside in a standard Python dictionary (`__dict__`). When you call `locals()` or `globals()`, it returns a direct reference to that module dictionary. Mutating `locals()['x']` directly updates the dictionary. 2) Function Scope (Fast Locals): Inside a function, CPython optimizes local variable access for speed using the `LOAD_FAST` and `STORE_FAST` opcodes. Fast locals are NOT stored in a dictionary; they are stored in a contiguous C array (`f_localsplus`) indexed directly by integer offsets determined at compile time. Array indexing provides $O(1)$ CPU register/cache-level access without hash lookups. 3) What locals() Does Inside a Function: When `locals()` is called inside a function, CPython dynamically allocates a *brand new dictionary* (or updates a proxy copy) and copies the values from the internal C array `f_localsplus` into this temporary dictionary. 4) Why Mutation Fails: Mutating `locals()['x'] = 100` merely modifies the temporary dictionary copy. The CPython bytecode evaluator continues reading from the internal C array `f_localsplus`, completely ignoring the dictionary. (Note: In Python 3.13, PEP 667 formalizes `locals()` behavior with a write-through proxy in specific contexts, but historically and fundamentally, fast locals are array-backed).",
        [
            "Explains that function local variables are stored in a contiguous C array (f_localsplus / fast locals), not a dictionary",
            "Describes locals() inside functions creating or synchronizing a temporary dictionary snapshot from the C array",
            "Clarifies that mutating the dictionary does not alter the underlying array read by LOAD_FAST opcodes"
        ],
        [
            "Claims Python local variables are stored in an encrypted database in memory"
        ]
    ),
    (
        "B69_1_4",
        "concept",
        "medium",
        "concept",
        ["CPython Internals", "Async Concurrency"],
        "CPython / Coroutines",
        "Generator and Coroutine Frame Suspension Mechanics",
        "When a Python generator executes a `yield` statement or an asynchronous coroutine executes an `await` statement, how does CPython suspend and resume execution without blocking or suspending an operating system thread, and how does the frame object track its execution state?",
        "Unlike operating system threads that require OS kernel context switches and private call stacks, Python generators and coroutines are cooperative, language-level state machines: 1) Frame Retention in Heap Memory: Standard function frames are allocated and deallocated when the function returns. For a generator or coroutine, CPython wraps the frame in a heap-allocated generator object (`PyGenObject`) or coroutine object (`PyCoroObject`). This prevents the frame (`gi_frame` or `cr_frame`) from being destroyed when execution yields. 2) Execution State Tracking (`f_lasti`): The frame object maintains an instruction pointer attribute `f_lasti` (last instruction index) and an internal evaluation stack. When `yield` or `await` executes, CPython saves the evaluation stack pointers, records the current bytecode offset into `f_lasti`, sets the generator state to `GEN_SUSPENDED`, and returns the yielded value directly to the caller. 3) Resumption (`send()`): When `gen.send(value)` or the asyncio event loop resumes the coroutine, CPython re-enters the evaluation loop (`_PyEval_EvalFrameDefault`), restores the stack, pushes the incoming value onto the top of the evaluation stack, and continues executing bytecodes starting from `f_lasti + 2`. 4) Cleanup: If a generator is abandoned before completion, garbage collection invokes its finalizer, which injects a `GeneratorExit` exception into the frame to trigger `finally` blocks.",
        [
            "Explains that generator/coroutine frames reside on the Python heap within PyGenObject / PyCoroObject",
            "Describes tracking suspension via the instruction pointer f_lasti and evaluation stack preservation",
            "Details resumption via send() jumping to f_lasti and cleanup via GeneratorExit exceptions"
        ],
        [
            "Claims Python yields by pausing the OS thread using Windows or Linux kernel thread sleep APIs"
        ]
    ),
    (
        "B69_1_5",
        "diagnose",
        "medium",
        "debugging",
        ["Language Semantics", "Architecture"],
        "CPython / Imports",
        "Circular Import Failures: Partially Initialized Modules",
        "In a Python project, `module_a.py` has `from module_b import func_b`, and `module_b.py` has `from module_a import func_a`. Running `python module_a.py` crashes with `ImportError: cannot import name 'func_b' from partially initialized module 'module_b' (most likely due to a circular import)`. However, changing both imports to `import module_b` and `import module_a` resolves the crash. Why does the `from ... import ...` syntax fail on circular imports while the module import succeeds?",
        "Root Cause: CPython's Module Execution Sequence and `sys.modules`: 1) When `module_a.py` starts, CPython creates an empty module object and registers it in `sys.modules['module_a']`. It then begins executing the top-level statements of `module_a.py`. 2) Line 1: `from module_b import func_b`. CPython sees `module_b` is not in `sys.modules`, so it creates an empty module object `sys.modules['module_b']` and pauses `module_a` to execute `module_b.py`. 3) Line 1 of `module_b.py`: `from module_a import func_a`. CPython checks `sys.modules`, sees `module_a` already exists (preventing an infinite import loop), and attempts to extract attribute `func_a` from `module_a`. 4) Failure: Because `module_a` was paused on its very first line, it has NOT executed the definition `def func_a(): ...` yet! Attribute `func_a` does not exist on the partially initialized module, raising an `ImportError`. Why `import module_a` Succeeds: If `module_b` uses `import module_a`, CPython merely assigns the existing module object reference `module_a` to a local variable. It does NOT look up `func_a` at import time. As long as `func_a` is not called until runtime (after both files finish top-level initialization), the circular reference succeeds cleanly.",
        [
            "Explains sys.modules caching empty module objects during initialization to prevent infinite recursion",
            "Identifies that 'from ... import attribute' requires immediate attribute resolution on partially initialized modules",
            "Shows that 'import module' succeeds because attribute resolution is deferred until function execution time"
        ],
        [
            "Claims circular imports can only be resolved by merging all Python files into a single 10,000-line script"
        ]
    ),
    (
        "B69_1_6",
        "implement",
        "hard",
        "implement",
        ["CPython Internals", "Security Architecture"],
        "importlib / PEP 451",
        "Custom Import Hooks via sys.meta_path and Module Loaders",
        "You are tasked with building a secure Python runtime plugin loader that intercepts `import` statements for plugins (e.g., `import plugin_alpha`) to load and decrypt encrypted bytecode files (`.enc`) from an encrypted memory store rather than reading plaintext files from disk. How do you implement a custom `MetaPathFinder` and `Loader` conforming to PEP 451 and register it with `sys.meta_path`?",
        "To build a PEP 451-compliant import hook: 1) Implement a custom MetaPathFinder: Create a class with `find_spec(self, fullname, path, target=None)`. If `fullname` matches the plugin namespace (e.g., starts with `plugin_`): A) Query the in-memory encrypted repository for the module. B) Return an `importlib.machinery.ModuleSpec(fullname, loader=EncryptedLoader(), origin='encrypted_store')`. If not a plugin, return `None` to allow standard filesystem finders in `sys.meta_path` to handle it. 2) Implement a custom Loader: Create a class implementing `create_module(self, spec)` (returning `None` to use standard module creation) and `exec_module(self, module)`: A) In `exec_module`, retrieve the encrypted bytes from memory. B) Decrypt the bytecode using AES/ChaCha20 into plaintext Python bytecode or code object. C) Call `exec(code_object, module.__dict__)` to populate the module namespace. D) Set module metadata (`__spec__`, `__loader__`, `__file__`). 3) Registration: Prepend an instance of the finder to the global import hook list: `sys.meta_path.insert(0, EncryptedPluginFinder())`. Any subsequent `import plugin_alpha` is routed through the custom finder without touching disk.",
        [
            "Implements a PEP 451 MetaPathFinder returning a ModuleSpec with a custom Loader",
            "Implements exec_module in the Loader to decrypt bytecode and execute it within module.__dict__",
            "Registers the custom finder by prepending it to sys.meta_path"
        ],
        [
            "Suggests overwriting the built-in __import__ function with a recursive lambda"
        ]
    ),
    (
        "B69_1_7",
        "concept",
        "easy",
        "concept",
        ["Language Semantics", "Debugging"],
        "importlib",
        "The Limitations and Pitfalls of importlib.reload()",
        "In a long-running Python application, a developer uses `importlib.reload(my_module)` to apply code updates without restarting the process. Why doesn't `reload()` update existing object instances, functions imported via `from my_module import func`, or Enum singletons?",
        "Pitfalls and Limitations of `importlib.reload()`: 1) In-Place Module Mutation, Not Object Replacement: `reload()` re-executes the module's top-level code inside the *existing* module dictionary. It updates module-level attributes, but does NOT seek out or update existing objects already instantiated by earlier code. 2) Existing Class Instances Retain Old Methods: Objects instantiated prior to reload retain references to the old class definition in their `__class__` pointer. Calling `instance.method()` invokes the old bytecode, not the reloaded class bytecode. 3) `from ... import ...` References Remain Unchanged: If another module imported a function via `from my_module import calculate`, that importing module holds a direct reference to the old function object in its local namespace. Reloading `my_module` updates `my_module.calculate`, but the other module continues pointing to the old function. 4) Identity Breaks (Enums / Singletons): Reloading creates new class objects. Checks like `isinstance(obj, ReloadedClass)` or `enum_val is ReloadedEnum.A` evaluate to `False` because the old and new classes are distinct objects at different memory addresses.",
        [
            "Explains that reload() mutates the module dictionary but leaves existing instantiated objects pointing to old classes",
            "Identifies that other modules holding references via 'from my_module import func' remain bound to old objects",
            "Highlights that identity checks (isinstance, is, Enums) fail between pre-reload and post-reload types"
        ],
        [
            "Claims importlib.reload() restarts the operating system kernel"
        ]
    ),
    (
        "B69_1_8",
        "explain",
        "hard",
        "explain",
        ["CPython Internals", "Memory Management"],
        "CPython / PyMalloc",
        "PyMalloc Allocator Architecture and Memory Fragmentation",
        "A long-running Python ETL worker processes 10 million small dictionary objects (each < 100 bytes). After processing, the script calls `del records` and `gc.collect()`. Running `sys.getallocatedblocks()` shows that millions of objects were freed, but inspecting the OS Resident Set Size (RSS) via `top` reveals that memory usage did NOT drop, remaining at 4GB. Explain how CPython's PyMalloc allocator (Arenas, Pools, and Size Classes) causes this high-water mark memory retention.",
        "Architecture of PyMalloc (Python's Small Object Allocator): 1) Hierarchy: For small allocations ($\le 512$ bytes), CPython uses PyMalloc rather than the system `malloc()`: A) Arenas: 256KB chunks allocated from the OS via `malloc()`. B) Pools: Arenas are subdivided into 4KB pools. C) Blocks: Pools are partitioned into fixed-size blocks aligned to size classes (multiples of 8 bytes: 8, 16, 24, ..., 512 bytes). 2) Deallocation Mechanics & Fragmentation: When an individual object is deleted, its block is returned to the pool's free list. When all blocks in a 4KB pool are freed, the pool is returned to the arena. However, PyMalloc can ONLY return memory back to the operating system (via `free()`) when an ENTIRE 256KB Arena is completely 100% empty! 3) The High-Water Mark Problem: In an ETL batch processing millions of objects, small long-lived objects (like strings, cached variables, or internal frame objects) become scattered across nearly every arena. If a 256KB arena contains 1 single surviving object, that entire 256KB arena CANNOT be released back to the OS. 4) Consequence: The memory remains allocated to PyMalloc. It can be reused for future Python small object allocations, but OS RSS remains permanently elevated at the historical high-water mark.",
        [
            "Details PyMalloc hierarchy: 256KB Arenas, 4KB Pools, and size classes for allocations <= 512 bytes",
            "Explains that memory can only be freed back to the OS if an entire 256KB arena is 100% empty",
            "Identifies memory fragmentation (a single surviving object pinning an entire arena) as the cause of high OS RSS"
        ],
        [
            "Claims Linux operating systems never permit freeing memory until the computer reboots"
        ]
    ),
    (
        "B69_1_9",
        "diagnose",
        "hard",
        "debugging",
        ["Memory Management", "Async Concurrency"],
        "CPython / asyncio / gc",
        "Reference Cycles involving Async Tasks and Coroutine Frames",
        "A backend service running an asyncio event loop leaks memory slowly over several days. You inspect memory using `tracemalloc` and discover thousands of leaked coroutine objects, task instances, and bound methods. A developer argues: 'Python has automatic Garbage Collection, so reference cycles are always cleaned up!' What specific reference cycle structure involving asyncio tasks, exception tracebacks, and bound methods prevents or delays garbage collection, causing heap bloat?",
        "Why Cyclical Async Tasks Accumulate: 1) The Reference Cycle Structure: When an asynchronous task runs, a background coroutine often captures a bound method (`self.handler`). The bound method holds a strong reference to `self` (the service/controller). If the coroutine creates a task and stores it on `self` (`self.active_tasks.append(task)`), or if an exception occurs inside the coroutine, a cycle forms: `Task -> Coroutine -> Frame -> Locals -> self -> active_tasks -> Task`. 2) Exception Traceback Pinning: If a coroutine fails with an unhandled exception, the exception object (`exc`) holds a reference to its traceback (`__traceback__`), which holds the execution frame (`tb_frame`), which holds all local variables (`f_locals`), which holds `self`. Unless `exc.__traceback__ = None` is called or the task is cleared, the entire memory graph of the task remains pinned. 3) Garbage Collector Limitations: Python's reference counting cannot collect cycles; it relies on the cyclic garbage collector. In asyncio, generation 0 and 1 collections occur frequently, but long-lived tasks survive into Generation 2. Generation 2 GC runs rarely (after many allocations). Furthermore, if tasks are continuously enqueued, the rate of cycle generation outpaces Generation 2 collection. If any object in the cycle implements a legacy `__del__` (prior to PEP 442) or is held by an active event loop callback list, it is permanently uncollectable.",
        [
            "Details the cycle: Task -> coroutine -> frame -> local variables -> self -> active_tasks list -> Task",
            "Explains that unhandled exceptions pin execution frames and local variables via __traceback__ references",
            "Identifies that cyclic GC generation 2 collection intervals allow rapid memory bloat under continuous task generation"
        ],
        [
            "Claims asyncio tasks run in separate OS virtual machines that cannot be garbage collected"
        ]
    ),
    (
        "B69_1_10",
        "scenario",
        "medium",
        "scenario",
        ["Memory Management", "Debugging"],
        "CPython / C Extensions",
        "Diagnosing Invisible Native Memory Leaks Bypassing tracemalloc",
        "A Python machine learning microservice processes images using OpenCV (`cv2`) and NumPy. Over 12 hours, the Linux process RSS grows from 500MB to 16GB, eventually triggering the Linux OOM Killer. A developer runs Python's built-in `tracemalloc` module, but `tracemalloc` reports that Python heap memory is completely flat at only 400MB. Why is `tracemalloc` blind to this 15.6GB memory leak, and how do you diagnose native C-extension memory leaks using tools like `pympler` and `/proc/[pid]/smaps`?",
        "Why tracemalloc is Blind: Python's built-in `tracemalloc` module hooks into CPython's internal memory allocators (`PyMem_Malloc`, `PyMem_RawMalloc`, and PyMalloc). It tracks memory allocated *by the Python interpreter itself*. However, native C/C++ extensions (such as OpenCV, PyTorch, or NumPy routines compiled with C/CUDA) frequently call the system C allocator directly (`malloc()`, `calloc()`, or C++ `new`) without notifying the Python runtime. These direct system allocations bypass CPython entirely, making them 100% invisible to `tracemalloc`. Diagnosis Procedure: 1) System-Level Inspection (`/proc/<pid>/smaps`): Inspect memory mapping details. Check the Private_Dirty and PSS (Proportional Set Size) lines in `/proc/<pid>/smaps`. If non-heap anonymous mappings (`[anon]`) are growing while Python heap remains static, native extension allocations are leaking. 2) Native Profilers: Run the process under Valgrind (Massif tool: `valgrind --tool=massif python script.py`) or compile with AddressSanitizer (ASan / LSan) to track C-level `malloc()` calls and identify the exact C++ OpenCV function failing to call `free()` or `cv::Mat::release()`. 3) Pympler / gc: Use `pympler.asizeof` to confirm whether Python wrappers are leaking native pointers.",
        [
            "Explains that tracemalloc hooks CPython allocators and is blind to native C malloc() / C++ new calls",
            "Inspects /proc/<pid>/smaps to detect growing anonymous memory mappings (Private_Dirty / PSS)",
            "Prescribes using native tooling (Valgrind Massif or LeakSanitizer/ASan) to trace native C-extension leaks"
        ],
        [
            "Suggests running gc.collect() every millisecond inside the OpenCV image processing loop"
        ]
    ),
    (
        "B69_1_11",
        "implement",
        "medium",
        "implement",
        ["Operating Systems", "Performance Tuning"],
        "mmap / CPython",
        "Memory-Mapped Files (mmap) for Zero-Copy I/O and SIGBUS Handling",
        "You need to search for regex patterns across a massive 50GB log file in Python on a machine with only 8GB of RAM. Reading the file line-by-line via `file.readline()` causes excessive GC allocation overhead and takes 15 minutes. How do you implement zero-copy scanning using Python's `mmap` module, and how must your code guard against `SIGBUS` errors if another process truncates the file during reading?",
        "Implementation with mmap: 1) Mechanism: The `mmap` module maps the file's disk blocks directly into the process's virtual address space via the OS `mmap()` syscall. The OS kernel reads data into RAM page cache lazily as the memory is accessed, without copying bytes into Python heap memory or allocating intermediate Python string objects. 2) Zero-Copy Pattern: Open the file in binary mode (`open(path, 'r+b')`), map it (`mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)`), and pass the `mmap` object directly into `re.finditer(pattern, mm)`. The regex engine operates directly on the kernel page cache bytes with zero copy. 3) Handling SIGBUS on Truncation: In Unix-like OSes, if another process truncates or shrinks the file while an application accesses an address beyond the new end-of-file, the CPU hardware generates a page fault that the kernel cannot satisfy, terminating the Python process with an uncatchable `SIGBUS` (Bus Error). 4) Guarding against SIGBUS: In production, install a POSIX signal handler for `signal.SIGBUS` (or use POSIX advisory file locking via `fcntl.flock(f, fcntl.LOCK_SH)` before mapping) to prevent concurrent truncation while the mapping is active.",
        [
            "Uses mmap.mmap with ACCESS_READ to map files into virtual memory, avoiding Python heap copies",
            "Executes regex operations directly on the memory-mapped buffer using kernel page cache",
            "Identifies SIGBUS errors caused by concurrent file truncation and mitigates via file locking (fcntl.flock)"
        ],
        [
            "Recommends increasing RAM on the machine to 128GB so the entire file fits in memory"
        ]
    ),
    (
        "B69_1_12",
        "diagnose",
        "medium",
        "debugging",
        ["Memory Management", "Debugging"],
        "objgraph / CPython",
        "Pinpointing Object Leaks in Long-Lived Workers with objgraph",
        "A Celery worker running for 48 hours shows slow, steady memory growth. You suspect that an in-memory cache or event listener list is retaining stale objects. How do you use the `objgraph` library to identify which Python object types are growing between worker tasks, and how do you trace the backreference graph to find the root object preventing garbage collection?",
        "Using objgraph for Memory Leak Diagnosis: 1) Tracking Object Growth: At the beginning and end of a repeating Celery task, run `objgraph.show_growth(limit=10)`. `show_growth()` compares the current count of all heap objects with the count from the previous invocation. If classes like `UserSession`, `HttpRequest`, or `dict` show positive growth (+500 every task), you have identified the leaking object type. 2) Identifying the Leaking Instances: Call `leaked_objs = objgraph.by_type('UserSession')` to retrieve active instances from memory. 3) Tracing Backreferences (Who holds the reference?): Call `objgraph.show_backrefs(leaked_objs[-1], max_depth=5, filename='leak_chain.png')`. This traverses the CPython garbage collector's reference graph backwards, generating a visual Graphviz diagram showing the exact chain of references keeping the object alive: e.g., `UserSession` is referenced by a `list`, which is referenced by a closure variable in an event listener, which is held by a global singleton `EventManager`. 4) Remediation: Remove the object from the global listener upon task completion or replace strong references with `weakref.WeakSet`.",
        [
            "Uses objgraph.show_growth() across task boundaries to identify object types with positive growth rates",
            "Uses objgraph.by_type() and objgraph.show_backrefs() to trace the retention chain to the root holder",
            "Identifies global containers, event listeners, or closures holding strong references as the cause of retention"
        ],
        [
            "Claims objgraph is a tool used for creating 3D video game animations"
        ]
    ),
    (
        "B69_1_13",
        "tradeoff",
        "medium",
        "tradeoff",
        ["CPython Internals", "Performance Tuning"],
        "gc module",
        "Tuning Generational GC Thresholds vs Disabling GC in High-Throughput ETL",
        "In a high-throughput Python batch processing pipeline that constructs and destroys 50 million short-lived objects per minute, what are the performance tradeoffs of tuning generational GC thresholds via `gc.set_threshold()` versus temporarily disabling GC entirely (`gc.disable()`) during batch loops?",
        "Python's cyclic garbage collector inspects objects across three generations (0, 1, 2). Generation 0 runs when allocations exceed `threshold0` (default 700). 1) Tuning GC Thresholds (`gc.set_threshold(70000, 10, 10)`): Tradeoffs: Drastically reduces the frequency of GC collection sweeps (by 100x), allowing short-lived objects to be freed immediately by reference counting ($refcount = 0$) without triggering expensive cyclical GC pointer scans. Keeps cyclic GC active in the background, preventing catastrophic memory leaks from actual reference cycles. Moderate memory overhead between sweeps. 2) Disabling GC Entirely (`gc.disable()`): Tradeoffs: Maximum possible throughput. Eliminates 100% of cyclic GC overhead and stop-the-world pointer traversals during CPU-intensive loops. Pure reference counting continues to free non-cyclical objects instantly. Severe Risk: Any reference cycle created during the batch will NEVER be collected, causing linear, unbounded memory growth. If memory usage spikes, the OS may kill the process. Production Best Practice: Call `gc.disable()` strictly within tightly bounded sub-batches where code is proven to be cycle-free, and call `gc.collect()` explicitly at the end of each batch before re-enabling.",
        [
            "Explains that increasing GC thresholds reduces sweep frequency, allowing reference counting to free objects",
            "Highlights that gc.disable() eliminates cycle-traversal CPU overhead while reference counting remains active",
            "Warns that disabling GC causes unbounded memory bloat if any circular references exist in batch data"
        ],
        [
            "Claims gc.disable() disables reference counting, causing Python to become C++"
        ]
    ),
    (
        "B69_1_14",
        "concept",
        "easy",
        "concept",
        ["CPython Internals", "Memory Management"],
        "CPython / sys",
        "String Interning with sys.intern() for Memory and Performance",
        "When parsing gigabytes of XML or JSON data containing millions of repeating dictionary keys (such as `\"status\"`, `\"user_id\"`, `\"type\"`), how does `sys.intern()` reduce memory consumption and accelerate dictionary lookups?",
        "1) Memory Reduction via String Deduplication: By default, strings read from files or network sockets are allocated as independent `PyASCIIObject` or `PyCompactUnicodeObject` instances in heap memory, each consuming ~50 bytes. If the string `\"PENDING\"` appears 10 million times, it consumes 500MB of RAM. When `sys.intern(s)` is called, CPython checks an internal global interned string dictionary. If the string already exists, it returns a pointer to the existing canonical string object and discards the duplicate. 10 million occurrences now point to the exact same 50-byte object in RAM, slashing memory from 500MB to 50 bytes. 2) Accelerated Dictionary Lookups (Pointer Comparison): Python dictionaries optimize string key lookups: if the hash matches, CPython first checks pointer identity (`key1 == key2`). For interned strings, pointer comparison succeeds immediately ($O(1)$ single CPU instruction) without executing byte-by-byte string comparisons (`memcmp`), boosting dictionary search throughput significantly.",
        [
            "Explains that sys.intern() deduplicates identical strings to point to a single canonical heap instance",
            "Quantifies memory savings when parsing millions of repeating keys/values",
            "Explains faster dictionary lookups due to fast pointer equality (identity checks) bypassing byte comparisons"
        ],
        [
            "Claims sys.intern() sends strings over the internet to a global cloud server"
        ]
    ),
    (
        "B69_1_15",
        "concept",
        "easy",
        "concept",
        ["Memory Management", "Design Patterns"],
        "weakref module",
        "Weak References and WeakValueDictionary for In-Memory Caches",
        "Why does building an in-memory object cache using a standard Python dictionary (`cache[id] = heavy_obj`) cause unbounded memory leaks, and how does `weakref.WeakValueDictionary` solve this without manual cache eviction logic?",
        "1) The Strong Reference Problem: A standard Python dictionary holds a *strong reference* to its values. As long as `heavy_obj` is in `cache`, its reference count can never drop to zero. Even if the rest of the application finishes using the object and drops all other references, the dictionary keeps the object alive indefinitely in RAM. Without manual TTL eviction, LRU pruning, or cache clearing, the cache grows continuously until memory exhaustion. 2) Solution via `weakref.WeakValueDictionary`: A `WeakValueDictionary` stores *weak references* to its values. A weak reference allows referencing an object without incrementing its reference count. As long as active application code holds a strong reference to `heavy_obj`, cache lookups (`cache[id]`) return the object. The moment the last active caller drops its strong reference, `heavy_obj`'s reference count drops to 0. CPython immediately garbage collects the object, and `WeakValueDictionary` automatically and atomically purges the dead key from the cache, providing zero-maintenance, memory-safe caching.",
        [
            "Explains that standard dictionary strong references prevent reference counts from reaching zero",
            "Defines weak references as referencing objects without incrementing their reference count",
            "Demonstrates WeakValueDictionary automatically purging keys the moment the object has no external strong references"
        ],
        [
            "Claims weak references delete objects every 5 seconds regardless of usage"
        ]
    ),
    (
        "B69_1_16",
        "implement",
        "medium",
        "implement",
        ["CPython Internals", "Testing"],
        "types / CodeType",
        "Code Object Immutability and types.CodeType.replace()",
        "In Python, function code objects (`fn.__code__`) are strictly immutable: you cannot directly assign `fn.__code__.co_consts = new_consts`. How does Python 3.8+'s `code.replace()` method allow developers to construct modified code objects safely, and when is this technique used in advanced mocking or instrumentation libraries?",
        "1) Code Object Immutability: In CPython, `CodeType` instances are immutable C structures. Once compiled, attributes like `co_code` (bytecodes), `co_consts` (constants), and `co_varnames` cannot be modified in-place to prevent thread-safety races and interpreter corruption. 2) Safe Modification with `code.replace()`: In Python 3.8+, `code.replace(**kwargs)` returns a *new* code object derived from the original with specific fields substituted. For example, to redirect a hardcoded URL constant in a function without modifying source files: `new_code = fn.__code__.replace(co_consts=tuple('http://mock.test' if c == 'http://prod.api' else c for c in fn.__code__.co_consts))`, then bind it back to the function: `fn.__code__ = new_code`. 3) Use Cases in Instrumentation: Used by: A) Security sandboxes (rewriting bytecode instructions to block forbidden opcodes). B) Coverage and profiling tools (injecting trace opcodes or line-number markers). C) Advanced test mocking frameworks (hot-patching constants or local variable names in frozen third-party libraries).",
        [
            "Explains that code objects are immutable C structures to guarantee interpreter execution integrity",
            "Uses code.replace() to construct a new code object with modified constants or bytecodes",
            "Identifies use cases in bytecode instrumentation, security sandboxing, and non-invasive test mocking"
        ],
        [
            "Suggests opening the .pyc file in a text editor and typing new words into the binary"
        ]
    ),
    (
        "B69_1_17",
        "explain",
        "medium",
        "explain",
        ["Language Semantics", "Performance Tuning"],
        "dict / __missing__",
        "The __missing__ Method on dict Subclasses vs defaultdict",
        "When building a custom caching or counting dictionary in Python, how does defining the special `__missing__(self, key)` method on a `dict` subclass differ from using `collections.defaultdict`, and why is `__missing__` more memory-efficient when the default value depends on the requested key?",
        "Differences and Mechanics: 1) How `__missing__` Works: In CPython's `dict` implementation, when key lookup `d[key]` fails to find the key in the hash table, `dict.__getitem__` checks if the subclass defines a `__missing__` method. If present, CPython calls `__missing__(key)` passing the missing key as an argument. Whatever `__missing__` returns is returned as the lookup result. (Note: `__missing__` is ONLY triggered by `d[key]`, not by `d.get(key)`). 2) Advantage over `collections.defaultdict`: `defaultdict` takes a zero-argument factory callable (`default_factory()`). It CANNOT pass the missing key to the factory. If you want a cache where missing key lookups fetch from a database based on the key (`fetch_user(user_id)`), `defaultdict` cannot do this natively without awkward closures. With a `dict` subclass implementing `__missing__(self, key)`: you can compute `val = fetch_user(key); self[key] = val; return val`. 3) Memory Efficiency: It avoids storing dummy default values in memory for keys that were merely queried and not meant to be retained.",
        [
            "Explains that __missing__ is invoked by dict.__getitem__ specifically when a key is absent",
            "Highlights that __missing__ receives the missing key as an argument, unlike defaultdict's zero-arg factory",
            "Demonstrates self-populating caches that compute and store values dynamically based on the requested key"
        ],
        [
            "Claims __missing__ is called when a programmer forgets to write a function"
        ]
    ),
    (
        "B69_1_18",
        "tradeoff",
        "medium",
        "tradeoff",
        ["CPython Internals", "Memory Management"],
        "Data Structures / array module",
        "Memory Overhead of Python Built-ins vs array.array",
        "In CPython, an integer like `x = 42` consumes 28 bytes of memory, and storing 10 million integers in a Python list consumes over 300MB of RAM. What internal CPython structures cause this memory overhead, and what are the tradeoffs of using `array.array('i')` or NumPy arrays instead of Python lists?",
        "Why Python Integers and Lists Consume High Memory: 1) `PyObject_HEAD` Overhead: Every Python object is a boxed C structure. In CPython 64-bit, every object begins with `PyObject_HEAD`: 8 bytes for reference count (`ob_refcnt`) and 8 bytes for type pointer (`ob_type`). 2) Arbitrary Precision Integers: Python integers are variable-length structs (`PyLongObject`) containing size fields and digit arrays, totaling 28 bytes for a single small int. 3) List Overhead: A Python `list` is an array of *pointers* (8 bytes per pointer), not raw values. A list of 10 million integers stores 10 million 8-byte pointers (80MB) pointing to 10 million separate 28-byte integer objects (280MB), plus list over-allocation, exceeding 360MB. Tradeoffs of `array.array('i')` and NumPy: 1) Memory Reduction: An `array.array('i')` stores contiguous raw 32-bit (4-byte) C integers in a single memory block. 10 million integers consume exactly 40MB of RAM—a 90% memory reduction with zero pointer dereferencing. 2) Tradeoffs: Strict homogeneity (can only store a single primitive C type). Accessing an element unboxes it into a temporary Python integer object, incurring minor boxing overhead during Python-level iteration.",
        [
            "Breaks down PyObject_HEAD overhead (reference count, type pointer, arbitrary-precision long fields)",
            "Explains that Python lists store pointers to heap-boxed objects, causing massive memory multiplication",
            "Quantifies memory savings of contiguous raw C arrays (array.array) vs boxing overhead on access"
        ],
        [
            "Claims Python integers take 28 bytes because they store 28 decimal digits"
        ]
    ),
    (
        "B69_1_19",
        "scenario",
        "hard",
        "scenario",
        ["CPython Internals", "Debugging"],
        "C Extensions / AddressSanitizer",
        "Debugging C-Extension Memory Corruption with AddressSanitizer and python3-dbg",
        "A Python microservice importing a custom C/Cython extension crashes randomly with `Fatal Python error: Segmentation fault` or `corrupted double-linked list`. Standard Python tracebacks are empty because the crash happens in native C code. How do you compile CPython and your extension with AddressSanitizer (ASan) and use a Python debug build (`python3-dbg`) to pinpoint heap buffer overflows and use-after-free bugs?",
        "Debugging Native Memory Corruption: 1) Why Standard Tools Fail: Segfaults inside C extensions abort the process at the OS kernel level before CPython's exception handler or traceback machinery can execute. Standard gdb backtraces on release builds often show mangled inlined frames. 2) Using Python Debug Builds (`python3-dbg`): Install `python3-dbg`. Debug builds compile CPython with `-g3 -O0`, define `Py_DEBUG`, and include extra reference count checks, memory allocation canaries, and assertions. It provides detailed PyObject inspection macros in gdb (`py-bt`, `py-list`). 3) Compiling with AddressSanitizer (ASan): Recompile the extension and/or CPython using Clang/GCC with `-fsanitize=address -fno-omit-frame-pointer -g`. Set environment variables: `export ASAN_OPTIONS=detect_leaks=1:halt_on_error=1`. 4) Execution & Root Cause Pinpointing: Run the test under ASan. When memory corruption occurs, ASan intercepts the invalid read/write immediately at the exact C instruction, printing a comprehensive report: the exact memory address, whether it is a Heap-Buffer-Overflow or Heap-Use-After-Free, the allocation stack trace, the deallocation stack trace, and the crashing thread stack trace.",
        [
            "Explains that native segfaults crash before Python traceback machinery can capture the error",
            "Utilizes python3-dbg with Py_DEBUG and gdb macros (py-bt) for internal CPython state inspection",
            "Compiles C/Cython extensions with AddressSanitizer (-fsanitize=address) to capture use-after-free and buffer overflows"
        ],
        [
            "Suggests putting a try...except Exception block around the C library import"
        ]
    ),
    (
        "B69_1_20",
        "explain",
        "medium",
        "explain",
        ["CPython Internals", "Memory Management"],
        "PEP 442 / __del__",
        "Object Finalization Semantics: PEP 442 and Cyclic Garbage Collection",
        "In Python 3.3 and earlier, if two objects with custom `__del__` methods formed a circular reference, CPython's cyclic garbage collector could NOT collect them, dumping them into `gc.garbage` as uncollectable memory leaks. How did PEP 442 (Safe Object Finalization) modernize CPython's garbage collector in Python 3.4+ to safely break and collect reference cycles containing `__del__` finalizers?",
        "Historical Problem (Pre-PEP 442): Prior to Python 3.4, if Object A and Object B referenced each other and both defined `__del__()`, CPython's cyclic garbage collector could not determine which object's `__del__()` should be executed first. If A's finalizer ran first, it might try to access B, which might expect A to be alive. To avoid executing finalizers on half-destroyed objects, CPython gave up, refused to collect the cycle, and moved both objects to `gc.garbage`. The memory was leaked permanently. PEP 442 Solution: 1) Two-Phase Finalization: PEP 442 introduced safe finalization: when a reference cycle is identified as unreachable, CPython first executes all `__del__()` methods on objects in the cycle *while the entire reference cycle is still completely intact in memory*. 2) Weakref Callbacks: Weak reference callbacks are executed after `__del__()` methods. 3) Cycle Resurrect Check: CPython checks if any finalizer resurrected objects in the cycle (e.g., assigning `self` to a global variable). 4) Cycle Breaking: If no objects were resurrected, CPython proceeds to Phase 2: it breaks the cycle by clearing all object attributes and freeing the memory blocks safely, completely eliminating the historical `gc.garbage` uncollectable cycle leak.",
        [
            "Explains pre-PEP 442 flaw: undefined finalization ordering caused cycles with __del__ to be abandoned in gc.garbage",
            "Details PEP 442 two-phase finalization: executing __del__ methods while the cycle remains fully intact",
            "Describes resurrection checks and subsequent cycle breaking to safely free memory"
        ],
        [
            "Claims PEP 442 removed the __del__ method from Python entirely"
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 1).")
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
    print("POST-BATCH AUDIT PART 1")
    print("========================================")
    print(f"Batch: 69 Part 1")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
