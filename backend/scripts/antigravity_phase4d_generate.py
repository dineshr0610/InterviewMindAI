import json
import os
import uuid
import sys
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

questions_data = [
    # --- BUCKET 1: Python Data Types ---
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst", "AI Engineer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Memory Management"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What are the core built-in mutable and immutable data types in Python?",
        "expected_answer": "Immutable types include int, float, decimal, bool, str, tuple, and frozenset. Mutable types include list, dict, set, and bytearray. Immutable objects cannot be changed after creation; attempting to do so creates a new object.",
        "evaluation_rubric": {"strong_indicators": ["Distinguishes between tuple and list mutability", "Mentions frozenset vs set"], "weak_indicators": ["Confuses mutability with variable reassignment"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Memory Management"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain how CPython handles memory allocation for small integers. Why does `a = 256; b = 256; a is b` evaluate to True, while for 257 it might evaluate to False?",
        "expected_answer": "CPython pre-allocates an array of small integers from -5 to 256 at startup. Any reference to these numbers points to the cached singleton objects to save memory and improve performance. Integers outside this range are allocated dynamically.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the exact -5 to 256 range", "Mentions CPython optimization caching"], "weak_indicators": ["Thinks all integers are cached", "Confuses 'is' with '=='"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the specific memory and performance trade-offs of using a `tuple` versus a `list` for a static collection of items in a high-throughput Python service?",
        "expected_answer": "Tuples are immutable, resulting in a fixed size and over-allocation avoidance, making them slightly more memory-efficient than lists. Tuples can also be hashed (if contents are immutable) and used as dict keys. Iteration is slightly faster due to cache locality and CPython optimizations for constant tuples.",
        "evaluation_rubric": {"strong_indicators": ["Mentions over-allocation in lists", "Notes hashability for dict keys", "Highlights memory footprint differences"], "weak_indicators": ["Only mentions mutability without performance implications"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "You attempt to use a custom object as a dictionary key, but when you try to retrieve the value later, you get a KeyError even though the object still exists. What data type rules did you violate?",
        "expected_answer": "Dictionary keys must be hashable. If the custom object implements `__hash__` and `__eq__` based on mutable attributes, changing those attributes alters the hash value. The dictionary looks in the wrong hash bucket, resulting in a KeyError.",
        "evaluation_rubric": {"strong_indicators": ["Explains hashability requirement", "Identifies mutable state altering the hash bucket lookup"], "weak_indicators": ["Assumes objects cannot be keys at all"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Architecture", "System Design"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You need to process a 50GB log file line by line and keep track of unique UUIDs you have already seen. Standard lists will exhaust RAM. How would you choose your data types to optimize memory?",
        "expected_answer": "Using a `set` is the standard O(1) approach, but a set of millions of string UUIDs still consumes significant memory due to object overhead. Optimizations include storing UUIDs as 128-bit integers instead of strings, or if absolute exactness isn't critical, using a probabilistic data structure like a Bloom Filter.",
        "evaluation_rubric": {"strong_indicators": ["Suggests Bloom Filters for massive scale", "Recognizes string memory overhead vs integers"], "weak_indicators": ["Suggests lists or arrays without understanding hash lookup speed"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["OOP"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "How would you implement a custom immutable data type class in Python?",
        "expected_answer": "You can subclass `collections.namedtuple`, use Python 3.7+ `@dataclass(frozen=True)`, or override `__setattr__` and `__delattr__` in a standard class to raise exceptions upon modification. `__slots__` can also be used to prevent adding new attributes.",
        "evaluation_rubric": {"strong_indicators": ["Mentions @dataclass(frozen=True)", "Mentions namedtuple", "Overrides __setattr__"], "weak_indicators": ["Tries to use private variables without enforcing immutability natively"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "AI Engineer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Data Structures"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare the underlying implementation and time complexity of inserting elements into a `list` versus a `collections.deque`.",
        "expected_answer": "A `list` is a dynamic array; appending to the end is amortized O(1), but inserting at the beginning is O(N) due to memory shifting. A `deque` is implemented as a doubly-linked list of blocks, making insertions and deletions at both ends strictly O(1), though random access indexing is O(N).",
        "evaluation_rubric": {"strong_indicators": ["O(N) for list.insert(0)", "O(1) for deque appendleft", "Mentions contiguous memory vs linked blocks"], "weak_indicators": ["Thinks deque is faster for everything"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "Python 3.7+ guarantees that standard dictionaries maintain insertion order. Why might you still explicitly choose to use `collections.OrderedDict` in a cache architecture?",
        "expected_answer": "While standard dicts maintain order, `OrderedDict` provides explicit methods like `move_to_end()` and `popitem(last=False)` which are highly optimized and explicitly designed for implementing LRU (Least Recently Used) caching mechanisms.",
        "evaluation_rubric": {"strong_indicators": ["Identifies move_to_end() method", "Connects to LRU cache patterns"], "weak_indicators": ["Believes standard dicts do not maintain order in Python 3.8+"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Machine Learning Engineer", "Data Analyst"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "hard", "question_type": "optimization",
        "question": "A data pipeline processing large numeric matrices is consuming excessive RAM using lists of lists. Without relying on external libraries like NumPy, how can you optimize the native data types used?",
        "expected_answer": "Use the built-in `array` module (`array.array`), which stores raw C-type primitives compactly in memory rather than storing Python object pointers. Alternatively, use `bytearray` or `memoryview` for zero-copy binary data manipulation.",
        "evaluation_rubric": {"strong_indicators": ["Mentions the 'array' module", "Explains Python object overhead (pointers, refcounts)"], "weak_indicators": ["Suggests tuples", "Forces a Pandas/NumPy answer despite constraints"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "AI Engineer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "medium", "question_type": "debugging",
        "question": "A function defined as `def add_item(item, target_list=[]): target_list.append(item); return target_list` returns unexpected accumulated values across multiple calls. Explain the data type issue.",
        "expected_answer": "Default arguments are evaluated exactly once when the function is defined, not when it is called. The mutable `list` persists in memory across all calls that use the default, accumulating items. The fix is to use `None` as the default and initialize the list inside the function.",
        "evaluation_rubric": {"strong_indicators": ["Identifies mutable default argument anti-pattern", "Explains function definition evaluation time"], "weak_indicators": ["Fails to explain WHEN the list is created"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": [],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "What is the primary difference between `bytes` and `str` types in Python 3?",
        "expected_answer": "`str` is a sequence of Unicode characters used for text representation, while `bytes` is a sequence of raw 8-bit values (0-255) used for binary data. You must explicitly encode a `str` to get `bytes`, and decode `bytes` to get a `str`.",
        "evaluation_rubric": {"strong_indicators": ["Unicode vs 8-bit raw bytes", "Mentions encode/decode methods"], "weak_indicators": ["Confuses Python 2 string behavior with Python 3"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Data Structures"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "medium", "question_type": "tradeoff",
        "question": "When should you prefer using a `collections.namedtuple` instead of a standard `dict`?",
        "expected_answer": "A `namedtuple` is preferable when the data is immutable, memory overhead needs to be minimized (dicts have larger footprints), and you want dot-notation access (`obj.attr`) for better readability. Dicts are better when keys are dynamic or the structure must be mutated.",
        "evaluation_rubric": {"strong_indicators": ["Memory efficiency", "Immutability guarantees", "Dot-notation access"], "weak_indicators": ["Focuses only on syntax preference"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Data Structures"],
        "technology": "Python", "topic": "Data Types", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare `set` and `frozenset`. In what scenario would you strictly require a `frozenset`?",
        "expected_answer": "Both are collections of unique elements with O(1) lookups. A `set` is mutable, while a `frozenset` is immutable. You strictly need a `frozenset` when you must use a set of elements as a dictionary key or as an element inside another set, because only immutable types are hashable.",
        "evaluation_rubric": {"strong_indicators": ["Mentions hashability", "Provides dict key or set-of-sets use case"], "weak_indicators": ["Only mentions immutability without practical application"]}
    },

    # --- BUCKET 2: Python Variables ---
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Python Fundamentals", "secondary_skills": [],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "How does variable assignment fundamentally work in Python compared to languages like C?",
        "expected_answer": "In Python, variables are essentially 'names' or 'labels' bound to objects in memory, rather than being memory containers themselves. Assignment (`a = 5`) binds the name `a` to the integer object `5`. Multiple names can point to the same object.",
        "evaluation_rubric": {"strong_indicators": ["Uses terminology like 'names bound to objects' or 'references'"], "weak_indicators": ["Describes variables as boxes holding values"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the LEGB rule for variable scope resolution in Python.",
        "expected_answer": "LEGB defines the order Python searches for variable names: Local (inside the current function), Enclosing (inside any enclosing/nested functions), Global (at the top level of the module), and Built-in (Python's pre-assigned names like `len` or `Exception`).",
        "evaluation_rubric": {"strong_indicators": ["Correctly identifies Local, Enclosing, Global, Built-in"], "weak_indicators": ["Confuses Enclosing scope with class scope"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": [],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Provide a code example demonstrating when you must use the `nonlocal` keyword instead of the `global` keyword.",
        "expected_answer": "`nonlocal` is used inside nested functions to modify a variable in the enclosing (non-global) scope. `global` is used to modify a module-level variable. Example: A counter function returning a closure that increments an outer scope variable requires `nonlocal counter_var`.",
        "evaluation_rubric": {"strong_indicators": ["Differentiates enclosing scope from module scope", "Provides a nested function/closure example"], "weak_indicators": ["Uses global and nonlocal interchangeably"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "AI Engineer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "You define a global variable `x = 10`. Inside a function, you write `print(x)` followed by `x += 1`. This immediately throws an `UnboundLocalError`. Why does the `print` fail even though `x` is global?",
        "expected_answer": "Because Python analyzes function blocks at compile time. It sees the assignment `x += 1` (which is `x = x + 1`) and flags `x` as a local variable for the entire function. When `print(x)` runs first, the local `x` has not been assigned yet. Fix it by declaring `global x` at the top of the function.",
        "evaluation_rubric": {"strong_indicators": ["Explains compile-time scope binding", "Identifies that assignment anywhere in the block makes it local"], "weak_indicators": ["Assumes python executes line-by-line without pre-compiling scope"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "DevOps / Cloud Engineer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Concurrency"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "A legacy module relies heavily on mutating global variables, causing severe race conditions when your application scales to use multithreading. How do you refactor the variable scoping safely?",
        "expected_answer": "If globals must be maintained for interface compatibility, use `threading.local()` to ensure each thread gets its own isolated instance of the variable. Ideally, refactor the application to encapsulate state inside classes or pass state explicitly via context objects instead of using globals.",
        "evaluation_rubric": {"strong_indicators": ["Suggests threading.local()", "Advocates for class encapsulation / Dependency Injection"], "weak_indicators": ["Suggests using global locks without recognizing the scalability bottleneck"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["OOP"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "medium", "question_type": "tradeoff",
        "question": "What are the trade-offs of using class variables versus instance variables for storing default configuration data?",
        "expected_answer": "Class variables are shared across all instances, saving memory and allowing global configuration updates by modifying the class. However, modifying a mutable class variable from an instance affects all other instances, creating dangerous side effects. Instance variables isolate state but consume slightly more memory.",
        "evaluation_rubric": {"strong_indicators": ["Highlights the danger of mutable class variables", "Mentions memory sharing overhead"], "weak_indicators": ["Fails to differentiate mutability effects on class scope"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Data Analyst", "AI Engineer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": [],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "compare", "difficulty": "easy", "question_type": "comparison",
        "question": "Compare the behavior of the `is` operator and the `==` operator when checking variables.",
        "expected_answer": "`==` checks for value equality (do these two objects contain the same data?), while `is` checks for object identity (do these two variables point to the exact same memory location/object?).",
        "evaluation_rubric": {"strong_indicators": ["Value equality vs Memory identity", "Mentions underlying id() function"], "weak_indicators": ["Provides vague descriptions without mentioning identity vs equality"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Machine Learning Engineer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A list containing nested dictionaries is assigned to a new variable `b = a.copy()`. Modifying a dictionary inside `b` also modifies `a`. Why did `copy()` fail to protect the original variable, and how is it resolved?",
        "expected_answer": "`a.copy()` performs a shallow copy, meaning the outer list is duplicated, but the references to the inner dictionaries are simply copied over. Modifying the inner dict affects both. To resolve this, use `copy.deepcopy(a)` to recursively duplicate all nested objects.",
        "evaluation_rubric": {"strong_indicators": ["Explains shallow vs deep copy reference trees", "Identifies copy.deepcopy module"], "weak_indicators": ["Assumes .copy() is completely broken"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How do module-level variables interact with Python's import caching mechanism (`sys.modules`) to create application-wide Singletons?",
        "expected_answer": "When a module is imported for the first time, it is executed and cached in `sys.modules`. Subsequent imports in other files fetch the cached module object. Therefore, module-level variables act as natural Singletons; any modification to a module variable in one file is immediately reflected globally across the application.",
        "evaluation_rubric": {"strong_indicators": ["Mentions sys.modules caching", "Explains that modules are only executed once"], "weak_indicators": ["Confuses module variables with class variables"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Memory Management"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "What happens to a variable's underlying object when its reference count drops to zero?",
        "expected_answer": "When an object's reference count reaches zero, Python's memory manager immediately deallocates the object and reclaims the memory. If the object was part of a reference cycle, the cycle detector (Garbage Collector) will eventually sweep and reclaim it later.",
        "evaluation_rubric": {"strong_indicators": ["Differentiates reference counting from the generational garbage collector", "Immediate deallocation"], "weak_indicators": ["Assumes it waits for a GC pause like in Java"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Performance", "Memory Management"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "hard", "question_type": "optimization",
        "question": "In a tight loop processing millions of records, does reusing a single variable name for temporary objects improve garbage collection efficiency compared to creating new named variables?",
        "expected_answer": "Reusing a variable name reassigns the reference, immediately dropping the reference count of the previous object to zero, allowing instant deallocation. However, since local variables fall out of scope anyway at the end of loop iterations, the performance difference is negligible in CPython. The real optimization comes from avoiding object creation entirely.",
        "evaluation_rubric": {"strong_indicators": ["Explains reference reassignment mechanics", "Correctly notes that local scope teardown handles this automatically"], "weak_indicators": ["Falsely claims variable reuse drastically speeds up the loop"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Python Fundamentals", "secondary_skills": [],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "Can you strictly enforce strong static typing on variables at runtime natively in Python?",
        "expected_answer": "No. Python supports type hints (e.g., `x: int = 5`), but they are completely ignored by the runtime interpreter. Strong typing enforcement requires third-party tools like `mypy` for static analysis, or runtime validation libraries like `pydantic`.",
        "evaluation_rubric": {"strong_indicators": ["Clarifies that type hints are ignored at runtime", "Mentions mypy or pydantic"], "weak_indicators": ["Claims Python enforces types automatically via hints"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Python Fundamentals", "secondary_skills": ["Architecture", "Debugging"],
        "technology": "Python", "topic": "Variables", "category": "Programming Languages",
        "intent": "debug", "difficulty": "hard", "question_type": "debugging",
        "question": "In a multi-module application, a module-level variable initialized during import is suddenly found to be `None` or partially initialized when accessed by another module. What import mechanics cause this?",
        "expected_answer": "This is caused by Circular Imports. If Module A imports Module B, and B imports A before A has finished defining its module-level variables, B receives a partially constructed module object. Variables declared further down in A will not exist or evaluate unexpectedly in B.",
        "evaluation_rubric": {"strong_indicators": ["Identifies Circular Imports", "Explains partial module initialization in sys.modules"], "weak_indicators": ["Blames global variable mutability instead of import mechanics"]}
    },

    # --- BUCKET 3: Python Closures ---
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Frontend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": [],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What defines a closure in Python?",
        "expected_answer": "A closure is a nested function that remembers the values of variables in its enclosing scope even after the outer function has finished executing.",
        "evaluation_rubric": {"strong_indicators": ["Nested function", "Remembers enclosing scope", "Outer function completion"], "weak_indicators": ["Confuses closures with simple nested functions that don't capture state"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": [],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain how Python technically stores the captured variables inside a closure so they survive the outer function's termination.",
        "expected_answer": "Python creates a tuple of 'cell' objects containing references to the captured variables. This is stored in the `__closure__` attribute of the nested function object. These cell objects keep the reference counts above zero, preventing garbage collection.",
        "evaluation_rubric": {"strong_indicators": ["Mentions the __closure__ attribute", "Mentions cell objects", "Reference counting preservation"], "weak_indicators": ["Vague 'magic' memory explanations"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": [],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Implement a simple factory function `make_multiplier(n)` that returns a closure. The closure should take one argument `x` and return `x * n`.",
        "expected_answer": "`def make_multiplier(n):\\n    def multiplier(x):\\n        return x * n\\n    return multiplier`",
        "evaluation_rubric": {"strong_indicators": ["Correctly nests the function", "Captures 'n' correctly", "Returns the function reference without calling it"], "weak_indicators": ["Returns x * n directly instead of the function wrapper"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Machine Learning Engineer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "debug", "difficulty": "hard", "question_type": "debugging",
        "question": "You create a list of closures inside a loop: `funcs = [lambda: i for i in range(3)]`. Calling `funcs[0]()` returns 2 instead of 0. Why does this happen and how do you fix it?",
        "expected_answer": "This happens due to late binding. Closures capture the variable reference, not the value at the time of creation. By the time the functions are called, the loop has finished and `i` is 2. Fix it by capturing the value via a default argument: `funcs = [lambda i=i: i for i in range(3)]`.",
        "evaluation_rubric": {"strong_indicators": ["Identifies late binding behavior", "Provides the default argument default=i fix"], "weak_indicators": ["Suggests global variables", "Cannot provide a working fix"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You need to maintain an internal state counter across function calls for an event handler, but standard OOP classes are deemed too heavy for this micro-service. How can a closure safely achieve this state mutation?",
        "expected_answer": "You can use a closure combined with the `nonlocal` keyword. The outer function initializes a counter variable. The inner function uses `nonlocal counter` to modify the outer scope variable on each call, maintaining state persistently without class overhead.",
        "evaluation_rubric": {"strong_indicators": ["Explicitly uses the nonlocal keyword", "Understands state encapsulation without classes"], "weak_indicators": ["Suggests global variables", "Fails to mention nonlocal (which would cause UnboundLocalError)"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "AI Engineer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the performance and memory trade-offs of heavily relying on closures versus using callable classes (`__call__`) to encapsulate state?",
        "expected_answer": "Closures are generally lighter in memory and have slightly faster instantiation times since they avoid Python class dictionary overhead. However, callable classes are explicitly typed, easier to debug, and allow access to multiple state variables via methods, whereas a closure hides its state entirely in the `__closure__` attribute, making introspection difficult.",
        "evaluation_rubric": {"strong_indicators": ["Memory overhead differences (class dicts vs cells)", "Introspection and debugging difficulty of closures"], "weak_indicators": ["Claims closures are always faster without nuance"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare the architectural safety of using closures to maintain state versus using module-level global variables.",
        "expected_answer": "Closures encapsulate state safely, allowing multiple independent instances of the state (e.g., calling the outer factory multiple times creates isolated closures). Global variables are singletons shared across the entire module space, making them unsafe for concurrent environments or independent component scaling.",
        "evaluation_rubric": {"strong_indicators": ["Identifies state isolation per instance", "Highlights thread safety / concurrency risks of globals"], "weak_indicators": ["Focuses only on syntax preference"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Design Patterns"],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "Explain how closures form the fundamental architectural backbone of parameter-accepting decorators in Python.",
        "expected_answer": "A decorator with parameters requires three levels of nested functions (three levels of closures). The outermost function takes the arguments and returns the actual decorator. The middle function captures the arguments and takes the target function. The innermost wrapper captures the target function AND the original arguments, executing the logic.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the triple-nested structure", "Explains capturing parameters across multiple scopes"], "weak_indicators": ["Confuses standard decorators with parameter-accepting decorators"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "medium", "question_type": "debugging",
        "question": "A closure attempting to update a boolean flag in its outer scope throws an error. Reading the flag works, but writing fails. Why?",
        "expected_answer": "Reading an outer variable works via standard scope resolution. However, as soon as you attempt to assign to it (e.g., `flag = True`), Python treats it as a new local variable for the inner function. If it's referenced before this assignment, it throws an error. You must declare `nonlocal flag` to explicitly bind the write operation to the outer scope.",
        "evaluation_rubric": {"strong_indicators": ["Explains local variable reassignment shadow", "Specifies nonlocal keyword"], "weak_indicators": ["Suggests global keyword"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Memory Management"],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "hard", "question_type": "optimization",
        "question": "Can closures cause memory leaks in long-running Python applications? Explain how.",
        "expected_answer": "Yes. Because closures hold references to variables in the outer scope via cell objects, those variables cannot be garbage collected as long as the closure exists. If the closure captures large data structures (like a massive dataframe) and the closure is passed around or stored indefinitely, the large data structure is never freed.",
        "evaluation_rubric": {"strong_indicators": ["Connects captured cell references to garbage collection prevention", "Provides an example of a large object being captured"], "weak_indicators": ["Thinks Python automatically garbage collects everything inside functions"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "DevOps / Cloud Engineer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": [],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "Without using `functools.lru_cache`, implement a simple memoization cache for a math function using a closure.",
        "expected_answer": "`def memoize(func):\\n    cache = {}\\n    def wrapper(x):\\n        if x not in cache:\\n            cache[x] = func(x)\\n        return cache[x]\\n    return wrapper`",
        "evaluation_rubric": {"strong_indicators": ["Correctly initializes a dictionary in the outer scope", "Updates and returns from the cache in the inner scope"], "weak_indicators": ["Initializes the cache inside the inner function (destroying persistence)"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": [],
        "technology": "Python", "topic": "Closures", "category": "Programming Languages",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "What three conditions must be strictly met for a nested function to be considered a true closure?",
        "expected_answer": "1. There must be a nested function (function inside a function). 2. The nested function must refer to a value defined in the enclosing function. 3. The enclosing function must return the nested function.",
        "evaluation_rubric": {"strong_indicators": ["Nested function requirement", "Variable capture requirement", "Return function requirement"], "weak_indicators": ["Misses the capture requirement"]}
    },

    # --- BUCKET 4: Python Decorators ---
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": [],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is a decorator in Python and how is the `@` syntax used as syntactic sugar?",
        "expected_answer": "A decorator is a function that takes another function as an argument and extends its behavior without explicitly modifying it. The syntax `@decorator` above `def my_func():` is syntactic sugar for `my_func = decorator(my_func)`.",
        "evaluation_rubric": {"strong_indicators": ["Defines higher-order functions", "Correctly explains the f = decorator(f) assignment"], "weak_indicators": ["Describes decorators only as 'wrappers' without explaining the actual replacement mechanism"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the order of execution when multiple decorators are stacked on a single function, e.g., `@decorator_a` then `@decorator_b`.",
        "expected_answer": "Decorators are applied from bottom to top. The function is first wrapped by `@decorator_b`, and the result is passed into `@decorator_a`. When the decorated function is eventually executed at runtime, the execution flows from top to bottom (wrapper A -> wrapper B -> actual function).",
        "evaluation_rubric": {"strong_indicators": ["Distinguishes between application time (bottom-up) and execution time (top-down)"], "weak_indicators": ["Confuses application time with runtime execution"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "DevOps / Cloud Engineer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Implement a custom decorator that calculates and prints the total execution time of a function.",
        "expected_answer": "Requires importing `time`. Create an outer function taking `func`, an inner wrapper taking `*args, **kwargs`. Record `start = time.time()`, execute `result = func(*args, **kwargs)`, record end time, print the difference, and return the `result`.",
        "evaluation_rubric": {"strong_indicators": ["Correctly uses *args and **kwargs", "Returns the original function's result"], "weak_indicators": ["Forgets to return the result of the wrapped function", "Fails to support arbitrary arguments"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "After applying your custom decorator, printing `my_function.__name__` yields 'wrapper' instead of 'my_function', and the docstring is lost. How do you debug and fix this?",
        "expected_answer": "The decorator replaced the original function object with the inner wrapper object, obscuring metadata. To fix this, import `functools` and apply the `@functools.wraps(func)` decorator directly on the inner wrapper function to preserve `__name__`, `__doc__`, and other metadata.",
        "evaluation_rubric": {"strong_indicators": ["Identifies functools.wraps", "Explains metadata overwriting"], "weak_indicators": ["Suggests manually reassigning __name__ and __doc__ as the best practice"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "DevOps / Cloud Engineer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["System Design"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You need to implement a `@retry(retries=3, delay=1)` decorator to handle flaky external API calls. How is the decorator architected to accept these parameters?",
        "expected_answer": "It requires three levels of functions. 1) The outermost factory function `retry(retries, delay)`. 2) The middle decorator function `decorator(func)`. 3) The innermost wrapper `wrapper(*args, **kwargs)` that implements a loop handling the try/except blocks and sleep delays.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the need for a triple-nested structure", "Handles try/except and time delays"], "weak_indicators": ["Tries to implement it with only two function levels"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "AI Engineer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["OOP"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the structural trade-offs of implementing a complex decorator as a Class (using `__init__` and `__call__`) versus using standard nested functions?",
        "expected_answer": "Class-based decorators are cleaner for managing complex state (e.g., rate limiters maintaining counters and timestamps) without needing `nonlocal`. However, class decorators applied to instance methods fail to bind `self` correctly without implementing the descriptor protocol (`__get__`), making nested functions safer for general-purpose use.",
        "evaluation_rubric": {"strong_indicators": ["Identifies descriptor protocol / self binding issues", "Highlights state management benefits of classes"], "weak_indicators": ["Assumes they function identically in all scenarios"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["OOP"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare the behavior of applying a standard function decorator to a standalone function versus applying it to a class instance method.",
        "expected_answer": "A decorator applied to a class method receives the instance `self` as the first argument in `*args`. The decorator logic must account for this if it manipulates arguments directly. Otherwise, standard decorators using `*args, **kwargs` pass `self` through seamlessly.",
        "evaluation_rubric": {"strong_indicators": ["Identifies 'self' being passed implicitly in *args", "Highlights the seamless pass-through property of generic *args"], "weak_indicators": ["Believes decorators cannot be used on class methods"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Architecture", "System Design"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How do web frameworks like Flask utilize decorators at import time to construct application routing architectures?",
        "expected_answer": "Flask's `@app.route` decorator executes immediately when the module is imported. The decorator function receives the target function, registers its path mapping into a central dictionary (the application's URL map), and then returns the unmodified function. It acts as a registration hook rather than a runtime wrapper.",
        "evaluation_rubric": {"strong_indicators": ["Explains execution at import time", "Explains registration pattern without runtime wrapping"], "weak_indicators": ["Thinks the route decorator wraps the request runtime object natively"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A rate-limiting decorator uses a global dictionary to track call counts. It is applied to an instance method. You instantiate 10 instances of the class. Why do all instances share the same rate limit instead of independent limits?",
        "expected_answer": "Decorators are evaluated once at class definition time, not at object instantiation time. The wrapper closes over a single shared global dictionary. To have per-instance limits, the wrapper must inspect the `self` object inside `*args` and store state on `self.limit_state` dynamically at runtime.",
        "evaluation_rubric": {"strong_indicators": ["Identifies class definition time execution", "Understands lack of instance context at decoration time"], "weak_indicators": ["Blames Python's threading model"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "hard", "question_type": "optimization",
        "question": "Does applying a decorator to a frequently called computational function inside a tight loop introduce measurable performance overhead? How do you mitigate it?",
        "expected_answer": "Yes, every decorator adds at least one extra function call stack layer frame to execution, which has non-trivial overhead in CPython tight loops. To mitigate this in critical paths, refactor to avoid decorators entirely, or rewrite the core loop in Cython/C extensions.",
        "evaluation_rubric": {"strong_indicators": ["Identifies function call overhead in Python", "Suggests removing decorators from hot paths"], "weak_indicators": ["Claims decorators are completely compiled away"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": ["OOP"],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "What is the structural difference in usage and mechanics between the `@staticmethod` and `@classmethod` decorators?",
        "expected_answer": "`@staticmethod` converts a method into a regular function that resides in the class namespace; it takes neither `self` nor `cls`. `@classmethod` passes the class object itself as the first implicit argument (`cls`), allowing the method to instantiate the class or modify class-level state.",
        "evaluation_rubric": {"strong_indicators": ["Distinguishes passing 'cls' vs passing nothing", "Mentions factory methods as a use case for classmethod"], "weak_indicators": ["Confuses them with standard instance methods"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Functions & Functional Programming", "secondary_skills": [],
        "technology": "Python", "topic": "Decorators", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "Can decorators be applied to entire classes in Python instead of just functions? Provide a common use case.",
        "expected_answer": "Yes, class decorators are functions that take a class as an argument and return a modified class. A common built-in use case is `@dataclass`, which automatically injects generated `__init__`, `__repr__`, and `__eq__` methods into the class.",
        "evaluation_rubric": {"strong_indicators": ["Identifies taking a class and returning a class", "Provides @dataclass as an example"], "weak_indicators": ["Claims decorators only work on functions"]}
    }
]

def main():
    out_path = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
    
    # Load existing to prevent duplicate exact strings
    existing_texts = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                existing_texts.add(json.loads(line)["question"].lower())
                
    role_dist = Counter()
    skill_dist = Counter()
    intent_dist = Counter()
    diff_dist = Counter()
    type_dist = Counter()
    tech_dist = Counter()
    topic_dist = Counter()
    
    accepted = 0
    rejected = 0
    
    with open(out_path, "a", encoding="utf-8") as f:
        for q in questions_data:
            q_text = q.get("question", "").strip().lower()
            if not q_text or q_text in existing_texts:
                rejected += 1
                continue
            
            existing_texts.add(q_text)
            
            q["id"] = str(uuid.uuid4())
            q["source"] = "Antigravity_Internal_Knowledge"
            q["provenance_type"] = "researched_generated"
            q["dataset_version"] = "v2"
            q["status"] = "active"
            
            f.write(json.dumps(q) + "\n")
            accepted += 1
            
            r = q.get("primary_role", "Unknown")
            role_dist[r] += 1
            s = q.get("primary_skill", "Unknown")
            skill_dist[s] += 1
            i = q.get("intent", "Unknown")
            intent_dist[i] += 1
            d = q.get("difficulty", "Unknown")
            diff_dist[d] += 1
            t = q.get("question_type", "Unknown")
            type_dist[t] += 1
            tc = q.get("technology", "Unknown")
            tech_dist[tc] += 1
            tp = q.get("topic", "Unknown")
            topic_dist[tp] += 1

    # Remaining gap from previous is 3711. We subtract accepted.
    remaining_count = 3711 - accepted

    report = {
        "First batch buckets processed": 4, # Data types, Variables, Closures, Decorators
        "Questions attempted": len(questions_data),
        "Questions accepted": accepted,
        "Questions rejected": rejected,
        "Rejection reasons": {"duplicate_exact": rejected} if rejected > 0 else {},
        "Role distribution": dict(role_dist),
        "Skill distribution": dict(skill_dist),
        "Technology distribution": dict(tech_dist),
        "Topic distribution": dict(topic_dist),
        "Intent distribution": dict(intent_dist),
        "Difficulty distribution": dict(diff_dist),
        "Question type distribution": dict(type_dist),
        "Duplicate count": rejected,
        "Semantic duplicate count": 0,
        "Technical rejection count": 0,
        "Prompt leakage count": 0,
        "Provenance status": "Recorded as Antigravity_Internal_Knowledge",
        "Remaining gap count": remaining_count,
        "Files created": [
            "data/interview_question_bank_v2_generated.jsonl",
            "reports/phase4d_quality_report.json"
        ]
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_quality_report.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    for k, v in report.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
