"""Batch 33 Part 3 question content (Python Developer). Targeted Gap Generation."""

ROLE = "Python Developer"

BUCKET_KEYS = {
    "PRODUCTION_DEBUGGING": ("Production Debugging", "Garbage Collection & Profiling", "Python", ["Python Developer", "Backend Developer"]),
}

Q = [
# ---------------- PRODUCTION_DEBUGGING ----------------
("PRODUCTION_DEBUGGING", "debug", "medium", "debugging", ["Memory Leaks", "Garbage Collection"],
 "Your long-running Python pipeline slowly consumes memory over 24 hours until crashing (OOM). You are not storing objects in global lists. What Python-specific memory leak is likely occurring?",
 "This is likely a 'Reference Cycle' causing uncollectable garbage. If Object A references Object B, and Object B references A, their reference counts never reach zero. If the Garbage Collector (`gc`) is disabled, or if the cyclic objects implemented custom `__del__` methods (in older Python), the GC cannot safely destroy them, causing a silent leak.",
 ["'Reference Cycle' causing uncollectable garbage (A points to B, B points to A)", "Reference counts never reach zero", "Garbage Collector fails to destroy them (e.g., GC disabled or custom `__del__` conflicts)"],
 ["Python strings absorb memory from the network over time"]),

("PRODUCTION_DEBUGGING", "implement", "hard", "implementation", ["tracemalloc", "Memory Profiling"],
 "You need to diagnose a silent memory leak in a production Python web server. You cannot restart the server. How do you find exactly which line of Python code is allocating the leaked memory?",
 "You use the built-in `tracemalloc` module. Ensure `tracemalloc.start()` is running. Take a memory snapshot at Time 1, wait for the leak to grow, and take snapshot at Time 2. Use `snapshot2.compare_to(snapshot1, 'lineno')` to print a strict diff. This outputs the exact filename and line of code that allocated the most new, unreleased memory blocks.",
 ["Use the built-in `tracemalloc` module", "Take two snapshots over time as the leak grows", "Use `snapshot2.compare_to(snapshot1, 'lineno')` to find the exact line of code allocating unreleased memory"],
 ["Download more RAM from the cloud provider"]),

("PRODUCTION_DEBUGGING", "scenario", "medium", "scenario", ["Circular Imports", "Architecture"],
 "You run a script and get `ImportError: cannot import name 'X' from partially initialized module 'Y'`. How do you architecturally resolve a circular import without merging the files?",
 "A circular import occurs when Module A imports B, which immediately imports A before A finishes initializing. Resolve this by moving the import statement *inside* the specific function that needs it (local import) so it evaluates at runtime, or refactor the shared dependency (e.g., Type Hints) into a third, separate module that both A and B can import.",
 ["Circular import: A imports B, B imports A before A is fully initialized", "Fix 1: Move the import inside the function/method (Local Import, evaluated at runtime)", "Fix 2: Refactor the shared dependency into a third, independent module"],
 ["Tell Python to import it backwards"]),

("PRODUCTION_DEBUGGING", "tradeoff", "medium", "tradeoff", ["Caching", "Weakref"],
 "When building a cache in Python, what is the memory management tradeoff of using a standard dictionary versus the `weakref` module (e.g., `WeakValueDictionary`)?",
 "A standard dictionary creates 'strong' references; even if the application no longer needs an object, the dict keeps it alive forever, causing a massive memory leak. A `WeakValueDictionary` creates 'weak' references. If the rest of the application deletes the object, the garbage collector automatically destroys it and seamlessly removes the dictionary entry.",
 ["Standard Dict: Strong references keep objects alive forever, causing massive cache memory leaks", "WeakValueDictionary: Weak references allow the Garbage Collector to destroy unused objects", "GC automatically removes the destroyed object from the weak dictionary, preventing leaks"],
 ["Weak dictionaries only hold weak passwords"]),

("PRODUCTION_DEBUGGING", "explain", "easy", "concept", ["Exceptions", "Tracebacks"],
 "In Python exception handling, what is the difference between `raise e` and a bare `raise`?",
 "Using `raise e` re-raises the exception, but truncates or alters the original traceback to point to the line where `raise e` was executed, obscuring the root cause. Using a bare `raise` keyword inside an `except` block perfectly preserves the original, pristine stack trace from where the error actually originated, making it superior for debugging.",
 ["`raise e` alters/truncates the traceback to the current line, obscuring the root cause", "Bare `raise` perfectly preserves the original, pristine stack trace", "Bare `raise` is vastly superior for production logging and debugging"],
 ["`raise e` raises the letter e into the alphabet"]),

("PRODUCTION_DEBUGGING", "debug", "hard", "debugging", ["Exception Chaining", "__cause__"],
 "Inside an `except` block for a DB error, you attempt to log it, but the logging throws a `KeyError`. The console shows a massive double stack trace. How do you intentionally chain exceptions to make this readable?",
 "This is an accidental implicit exception chain. To explicitly chain exceptions, use the `from` keyword (`raise new_exc from original_exc`). To completely suppress/hide the original exception (e.g., to hide DB credentials), you raise `new_exc from None`. This explicitly manipulates the `__cause__` and `__context__` attributes of the traceback.",
 ["Accidental implicit exception chain creates massive, confusing tracebacks", "Use `raise new_exc from original_exc` to explicitly chain logical consequences", "Use `raise new_exc from None` to completely suppress the original exception (hiding sensitive info)"],
 ["Put physical chains around the server rack"]),

("PRODUCTION_DEBUGGING", "implement", "medium", "implementation", ["Profiling", "cProfile"],
 "You are profiling a slow Python script to find the bottleneck. You want to see exactly how many times each function was called and the cumulative time spent inside it. What built-in tool do you use?",
 "You use the built-in `cProfile` module (`python -m cProfile -s cumtime script.py`). It provides deterministic profiling of Python programs, outputting a highly detailed table showing `ncalls` (number of calls), `tottime` (time spent strictly in the function), and `cumtime` (time spent in the function *and* all sub-functions).",
 ["Use the built-in `cProfile` module", "Provides deterministic profiling (time and call counts)", "Outputs `ncalls`, `tottime` (local time), and `cumtime` (total time including sub-functions)"],
 ["Use a stopwatch and stare at the screen very closely"]),

("PRODUCTION_DEBUGGING", "scenario", "hard", "scenario", ["Gunicorn", "Network Timeouts"],
 "You deploy a web service using Gunicorn with 4 synchronous workers. CPU/Memory are 5%, but the service stops responding. `py-spy` shows all 4 workers stuck on `socket.recv()`. What production failure occurred?",
 "This is a network timeout exhaustion failure. All 4 synchronous workers made an outbound HTTP request (via `requests`) to a 3rd-party service that hung, and the developer failed to provide an explicit `timeout=` argument. The workers are infinitely blocked waiting for data. With all workers blocked, the server cannot accept new connections.",
 ["Network timeout exhaustion failure", "Workers made outbound HTTP requests (e.g., `requests`) without an explicit `timeout=` argument", "The synchronous workers are infinitely blocked waiting for data, incapable of accepting new connections"],
 ["The workers went on strike for better working conditions"]),

("PRODUCTION_DEBUGGING", "tradeoff", "medium", "tradeoff", ["Logging", "pprint"],
 "When debugging a massive Python data structure in production, what is the tradeoff of using standard `print(obj)` versus the `pprint` module?",
 "`print()` dumps the entire nested structure onto a single unreadable, infinitely wrapping terminal line. `pprint` (Pretty Print) intelligently formats the object with proper indentation and depth limiting. The tradeoff is that `pprint` is significantly slower and consumes more CPU/memory to calculate the layout, so it shouldn't be used in high-volume hot paths.",
 ["`print()` outputs a single, unreadable wrapping line", "`pprint` formats with proper indentation, line breaks, and depth limiting", "Tradeoff: `pprint` is significantly slower and consumes more CPU/RAM (bad for high-volume logs)"],
 ["`pprint` uses expensive colored ink in the terminal"]),

("PRODUCTION_DEBUGGING", "explain", "easy", "concept", ["assert", "Optimization Flags"],
 "What does the `assert` statement do in Python, and why is it dangerous to use it for validating user input in production?",
 "`assert condition` evaluates the condition; if False, it raises an `AssertionError`. It is dangerous for production validation because Python can be executed with the `-O` (Optimize) flag (`python -O`). This globally disables and entirely ignores *all* `assert` statements. If used for security, running `-O` completely removes the security checks.",
 ["Evaluates a condition and raises `AssertionError` if False", "Running Python with the `-O` (Optimize) flag globally disables all `assert` statements", "Dangerous for security/validation because the checks can be silently removed at runtime"],
 ["`assert` makes the server physically yell at the user"]),

("PRODUCTION_DEBUGGING", "debug", "medium", "debugging", ["List Mutation", "Iteration"],
 "You iterate over a list: `for item in my_list: if item == 'bad': my_list.remove(item)`. The script silently skips elements and fails to remove all 'bad' items. Why?",
 "You are mutating a list while iterating over it. When you remove an item, all subsequent elements shift left by one index. However, the internal loop iterator still advances its index by one. This causes the loop to completely skip the element immediately following the removed item. You must iterate over a copy (`my_list.copy()`) or use a comprehension.",
 ["Mutating a list while iterating over it causes index shifting", "Subsequent elements shift left, but the iterator still advances right, skipping elements", "Fix: Iterate over a copy (`for item in my_list.copy():`) or use a list comprehension"],
 ["Python lists are naturally evasive and dodge the removal attempt"]),

("PRODUCTION_DEBUGGING", "implement", "hard", "implementation", ["REPL", "breakpoint()"],
 "You are debugging a complex algorithm. You want to drop into an interactive REPL *exactly* at line 50 to inspect local variables, without stopping the whole production server. How do you do this?",
 "In modern Python (3.7+), insert the `breakpoint()` built-in function at line 50. When execution hits that line, it pauses the thread and drops you into the `pdb` (Python Debugger) interactive console to inspect variables. You can easily disable this globally in production by setting the `PYTHONBREAKPOINT=0` environment variable.",
 ["Insert the `breakpoint()` built-in function at the exact line", "Drops execution into the interactive `pdb` (Python Debugger) console", "Can be globally disabled in production via the `PYTHONBREAKPOINT=0` environment variable"],
 ["Physically cut the ethernet cable exactly when line 50 runs"]),

("PRODUCTION_DEBUGGING", "scenario", "medium", "scenario", ["Generators", "Memory Out of Bounds"],
 "You process a 50GB CSV file using a generator: `def read_file(): for line in open('file'): yield line`. It crashes with `MemoryError`. Why did it crash if generators are memory efficient?",
 "While the generator itself yields one line at a time, the processing logic *consuming* the generator likely accumulated the results in memory. Calling `list(read_file())` or appending every processed line to a global list entirely defeats the generator, forcing the 50GB dataset into RAM. You must process and stream the output to disk incrementally.",
 ["The processing logic *consuming* the generator accumulated the results in memory", "Example: Calling `list(generator)` forces the entire dataset into RAM", "Fix: Process and stream the output to disk incrementally, never accumulating a master list"],
 ["Generators naturally explode when exposed to large files"]),

("PRODUCTION_DEBUGGING", "explain", "hard", "concept", ["Garbage Collection", "Reference Counting"],
 "In Python's Garbage Collection system, what is the difference between 'Reference Counting' and the 'Generational Garbage Collector'?",
 "Reference Counting is the primary, real-time memory system; every object tracks how many variables point to it. When count hits zero, it's instantly destroyed. However, it cannot detect circular references. The Generational GC is a secondary, periodic background process that scans objects specifically to detect and destroy isolated circular reference loops.",
 ["Reference Counting: Primary, real-time system. Destroys objects instantly when count hits zero.", "Flaw: Reference counting cannot detect circular references (A points to B, B to A)", "Generational GC: Secondary background process that specifically finds and destroys circular loops"],
 ["The generational GC only deletes variables created by older programmers"]),

("PRODUCTION_DEBUGGING", "debug", "medium", "debugging", ["Global State", "Imports"],
 "Module `config.py` defines `MAX_RETRIES = 3`. In `worker.py`, you do `from config import MAX_RETRIES`, then do `MAX_RETRIES = 5`. However, other modules still see it as 3. Why did the state fail to update globally?",
 "When you do `from config import MAX_RETRIES`, Python creates a completely separate, local binding of the integer in the `worker.py` namespace. Mutating the local integer does not affect the original module. To mutate global state, you must `import config` and explicitly mutate the module attribute: `config.MAX_RETRIES = 5`.",
 ["`from module import var` creates a separate, local namespace binding of the variable", "Mutating the local integer does not affect the original module's global state", "Fix: `import config` and mutate the attribute directly (`config.MAX_RETRIES = 5`)"],
 ["Python automatically resets variables to 3 for safety reasons"]),

("PRODUCTION_DEBUGGING", "fundamentals", "easy", "concept", ["__pycache__", "Bytecode"],
 "What is the purpose of the `__pycache__` directory and `.pyc` files in Python?",
 "When Python imports a module, it compiles the human-readable `.py` source code into intermediate bytecode and saves it as a `.pyc` file inside `__pycache__`. On subsequent runs, Python skips the compilation step and loads the bytecode directly, significantly speeding up application startup time (though it doesn't make runtime execution faster).",
 ["Caches the compiled intermediate bytecode (`.pyc` files)", "Skips the compilation step on subsequent runs", "Significantly speeds up application startup/import time (but not runtime execution speed)"],
 ["It is where Python hides bugs from the developer"])
]
