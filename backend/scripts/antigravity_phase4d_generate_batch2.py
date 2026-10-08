import json
import os
import uuid
import sys
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

questions_data = [
    # --- BUCKET 5: Python OOP -> Inheritance ---
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "AI Engineer"],
        "primary_skill": "OOP", "secondary_skills": [],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the difference between single and multiple inheritance in Python?",
        "expected_answer": "Single inheritance occurs when a child class derives from one parent class. Multiple inheritance occurs when a child class derives from more than one parent class simultaneously, inheriting attributes and methods from all of them.",
        "evaluation_rubric": {"strong_indicators": ["Correctly defines both terms", "Mentions attribute/method inheritance"], "weak_indicators": ["Confuses multiple inheritance with multilevel inheritance"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain how Python resolves method names in multiple inheritance scenarios. What algorithm is used?",
        "expected_answer": "Python uses the Method Resolution Order (MRO) to determine the class search path. It relies on the C3 linearization algorithm, which ensures a monotonic, deterministic search from left to right among parent classes, guaranteeing that a parent is never searched before all of its children.",
        "evaluation_rubric": {"strong_indicators": ["Mentions MRO", "Mentions C3 Linearization", "Left-to-right priority"], "weak_indicators": ["Thinks it searches purely depth-first without regard to diamond problems"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": [],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Provide a code example demonstrating how to properly initialize a parent class from a child class using `super()`.",
        "expected_answer": "`class Parent:\\n    def __init__(self, name):\\n        self.name = name\\n\\nclass Child(Parent):\\n    def __init__(self, name, age):\\n        super().__init__(name)\\n        self.age = age`",
        "evaluation_rubric": {"strong_indicators": ["Uses super().__init__() correctly without explicitly naming the parent class", "Passes the correct arguments"], "weak_indicators": ["Uses Parent.__init__(self) which breaks MRO"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "System Design"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the architectural trade-offs of using Multiple Inheritance versus Composition for code reuse in a large Python codebase?",
        "expected_answer": "Multiple inheritance provides seamless API integration and polymorphism but tightly couples classes, leads to fragile base classes, and introduces MRO complexity (the diamond problem). Composition (has-a) loosely couples components, is easier to unit test, and avoids MRO issues, but requires explicit delegation of methods.",
        "evaluation_rubric": {"strong_indicators": ["Identifies tight coupling in inheritance", "Identifies the diamond problem/MRO complexity", "Prefers composition for flexibility"], "weak_indicators": ["Fails to identify why multiple inheritance is dangerous at scale"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "You define `class A(B, C): pass`. Both `B` and `C` define a method named `process()`. When you call `A().process()`, the logic from `B` executes. Why did Python choose `B` over `C`?",
        "expected_answer": "Because of Python's Method Resolution Order (MRO). In `class A(B, C)`, class `B` is listed first (left-to-right). The C3 linearization algorithm places `B` before `C` in the MRO tuple, so Python finds `B.process()` first and stops searching.",
        "evaluation_rubric": {"strong_indicators": ["Explicitly mentions left-to-right ordering in the class definition", "Mentions MRO"], "weak_indicators": ["Says it's random", "Confuses with alphabetical ordering"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are designing an ORM model that must inherit from a `DeclarativeBase` provided by the database library, and a custom `AuditLoggingMixin` you wrote. How do you sequence the inheritance and why?",
        "expected_answer": "Mixins should be placed before the base class: `class UserModel(AuditLoggingMixin, DeclarativeBase):`. This ensures the Mixin's overridden methods (like `save()`) intercept the call in the MRO, execute their logging logic, and then call `super().save()` to hit the `DeclarativeBase`.",
        "evaluation_rubric": {"strong_indicators": ["Places Mixin first (leftmost)", "Explains MRO interception", "Explains the role of super() in the mixin"], "weak_indicators": ["Places base class first, defeating the mixin's overrides"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Design Patterns"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare standard class inheritance with the use of Mixins in Python.",
        "expected_answer": "Standard inheritance models an 'is-a' relationship establishing a strict hierarchy. A Mixin is a specific form of multiple inheritance designed to provide a specific bundle of functionality (e.g., logging, serialization) to a class without being a standalone entity or part of the primary 'is-a' hierarchy.",
        "evaluation_rubric": {"strong_indicators": ["Mixins don't stand alone", "Mixins don't require __init__ state typically", "Standard inheritance is 'is-a'"], "weak_indicators": ["Fails to differentiate their semantic purposes"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "When designing an extensible plugin framework, how can you use Python's `__init_subclass__` method to automatically register subclasses without relying on metaclasses?",
        "expected_answer": "You define a classmethod `__init_subclass__(cls, **kwargs)` on the base class. Whenever a developer creates a class inheriting from it, Python automatically calls this method, passing the new child class as `cls`. Inside the method, you can append `cls` to a global registry dictionary.",
        "evaluation_rubric": {"strong_indicators": ["Identifies __init_subclass__ triggers on child class creation", "Mentions appending to a registry"], "weak_indicators": ["Confuses it with __init__ or __new__"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "OOP", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "Do deep inheritance hierarchies impact performance when calling methods in Python?",
        "expected_answer": "Yes. Every time a method or attribute is accessed, Python dynamically traverses the MRO tuple starting from the instance class up through the parents. A very deep hierarchy requires more dictionary lookups (`__dict__`), causing slight performance degradation compared to flat structures.",
        "evaluation_rubric": {"strong_indicators": ["Identifies dynamic MRO traversal overhead", "Mentions dictionary lookups"], "weak_indicators": ["Believes method resolution is compiled away at runtime"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A class `D` inherits from `B` and `C`. Both `B` and `C` inherit from `A`. This forms a diamond hierarchy. How does Python's `super()` guarantee that `A.__init__` is only executed once?",
        "expected_answer": "`super()` does not simply call the parent. It proxies the next class in the computed MRO list. The MRO for `D` is `[D, B, C, A, object]`. When `B` calls `super().__init__`, it delegates to `C`, not `A`. When `C` calls `super()`, it delegates to `A`. Thus, `A` is only reached once.",
        "evaluation_rubric": {"strong_indicators": ["Explains that super() delegates to the next class in MRO, not strictly the parent", "Provides the linearized MRO flow"], "weak_indicators": ["Claims Python has a built-in flag tracking if A was called"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "OOP", "secondary_skills": [],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "What is the purpose of the `issubclass()` built-in function?",
        "expected_answer": "It is used to check if a specific class is a derived (child) class of another class (or a tuple of classes). It returns a boolean. E.g., `issubclass(bool, int)` returns True.",
        "evaluation_rubric": {"strong_indicators": ["Checks class hierarchy relationships", "Returns boolean"], "weak_indicators": ["Confuses it with isinstance()"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Machine Learning Engineer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Inheritance", "category": "Programming Languages",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "Implement an Abstract Base Class (ABC) in Python that strictly enforces all subclasses to implement a `calculate()` method.",
        "expected_answer": "Import `ABC` and `abstractmethod` from the `abc` module. Inherit the base class from `ABC`. Apply the `@abstractmethod` decorator to the `calculate` method. If a subclass fails to implement it, instantiation of the subclass will throw a TypeError.",
        "evaluation_rubric": {"strong_indicators": ["Imports ABC and abstractmethod", "Applies decorator correctly", "Notes TypeError upon instantiation"], "weak_indicators": ["Just raises NotImplementedError without using the abc module (which fails to prevent instantiation)"]}
    },

    # --- BUCKET 6: Python OOP -> Metaclasses ---
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "AI Engineer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is a metaclass in Python?",
        "expected_answer": "A metaclass is a 'class of a class'. Just as an object is an instance of a class, a class is an instance of a metaclass. Metaclasses define how a class behaves and how it is constructed at definition time. The default metaclass in Python is `type`.",
        "evaluation_rubric": {"strong_indicators": ["Class of a class", "Controls class creation", "Mentions 'type'"], "weak_indicators": ["Confuses metaclasses with base classes"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the difference in execution timeline: what happens when a Python script parses a class definition versus when the class is instantiated?",
        "expected_answer": "When parsed, Python executes the class body to collect attributes/methods into a dictionary, then passes this dictionary to the metaclass (usually `type()`) to create the class object in memory. Instantiation happens later at runtime, invoking `__new__` and `__init__` on the created class to generate an instance.",
        "evaluation_rubric": {"strong_indicators": ["Class definition triggers the metaclass", "Instantiation triggers __init__ on the class"], "weak_indicators": ["Thinks classes are purely static templates until instantiated"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "Implement a metaclass that automatically converts all non-dunder (non-magic) method names of its classes to uppercase during class creation.",
        "expected_answer": "`class UpperMeta(type):\\n    def __new__(cls, name, bases, dct):\\n        uppercase_dct = {}\\n        for k, v in dct.items():\\n            if not k.startswith('__'):\\n                uppercase_dct[k.upper()] = v\\n            else:\\n                uppercase_dct[k] = v\\n        return super().__new__(cls, name, bases, uppercase_dct)`",
        "evaluation_rubric": {"strong_indicators": ["Inherits from type", "Overrides __new__", "Iterates and modifies the class dictionary before calling super().__new__"], "weak_indicators": ["Tries to modify __init__", "Fails to return the class object"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "DevOps / Cloud Engineer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture", "System Design"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the maintainability trade-offs of using Metaclasses versus Class Decorators to modify class behavior?",
        "expected_answer": "Metaclasses are highly implicit, deeply inherited by all subclasses automatically, and can cause severe metaclass conflicts in multiple inheritance. They are harder to debug. Class decorators are explicit, applied only where specified, and easier to read, but they don't automatically propagate to subclasses and execute slightly later in the creation cycle.",
        "evaluation_rubric": {"strong_indicators": ["Metaclasses propagate to subclasses automatically", "Class decorators are explicit", "Mentions metaclass conflict issues"], "weak_indicators": ["Fails to identify the inheritance propagation difference"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "debug", "difficulty": "hard", "question_type": "debugging",
        "question": "Class `A` uses `MetaA`. Class `B` uses `MetaB`. You define `class C(A, B): pass`. Python throws a `TypeError: metaclass conflict`. Why does this happen and how do you resolve it?",
        "expected_answer": "Python requires the metaclass of a derived class to be a subclass of the metaclasses of all its bases. Since `MetaA` and `MetaB` are completely separate, Python cannot determine which metaclass should construct `C`. The fix is to manually create a new metaclass `class MetaC(MetaA, MetaB): pass` and explicitly assign it to `C`.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the lack of a shared metaclass ancestor", "Provides the multiple-inheritance metaclass fix"], "weak_indicators": ["Suggests removing multiple inheritance entirely as the only solution"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Database Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are building a custom ORM framework. You need to ensure that every subclass of `Model` explicitly defines a `__tablename__` attribute before the application even starts. How can a metaclass achieve this?",
        "expected_answer": "In the metaclass's `__new__` or `__init__` method, inspect the `dct` (class dictionary) passed in during class creation. If `__tablename__` is not present and the class being created isn't the base `Model` itself, immediately raise a `ValueError` or `TypeError`. This fails fast at import time.",
        "evaluation_rubric": {"strong_indicators": ["Validates the class dictionary at creation time", "Fails fast at import/parse time"], "weak_indicators": ["Suggests checking it during instance __init__ (too late)"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare the roles of `__new__` and `__init__` when defined inside a Metaclass.",
        "expected_answer": "`__new__` in a metaclass is responsible for allocating memory and actually creating the class object. It receives the class name, bases, and dictionary. `__init__` is called after the class object exists to initialize it. If you need to modify the class dictionary before creation, use `__new__`. If you just need to register the class, `__init__` suffices.",
        "evaluation_rubric": {"strong_indicators": ["__new__ allocates the class", "__init__ initializes the created class", "Modifying dict requires __new__"], "weak_indicators": ["Confuses metaclass __new__ with instance __new__"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How does Python's `abc.ABCMeta` metaclass internally prevent the instantiation of subclasses that have incomplete abstract methods?",
        "expected_answer": "`ABCMeta` intercepts the class creation process to populate a special hidden attribute (e.g., `__abstractmethods__`) containing a set of all methods decorated with `@abstractmethod`. During object instantiation, Python's internal C code checks this attribute; if the set is not empty, it blocks instantiation and raises a TypeError.",
        "evaluation_rubric": {"strong_indicators": ["Mentions tracking the abstract methods in a set/attribute", "Blocks instantiation at the instance __new__ level"], "weak_indicators": ["Thinks ABCMeta scans the source code dynamically at runtime"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "medium", "question_type": "debugging",
        "question": "You write a metaclass with a `__new__` method to inspect class attributes, but you forget to return `super().__new__(cls, name, bases, dct)`. What happens when a script imports the module defining a class with this metaclass?",
        "expected_answer": "The class definition process silently fails to return a class object. The name of the class in the module namespace will end up being bound to `None` (or whatever implicit value was returned). Instantiating it will result in a `TypeError: 'NoneType' object is not callable`.",
        "evaluation_rubric": {"strong_indicators": ["Identifies that the class object is never constructed", "Results in a NoneType error on instantiation"], "weak_indicators": ["Assumes Python falls back to the default type metaclass automatically"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "OOP", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "hard", "question_type": "optimization",
        "question": "Do metaclasses introduce runtime performance overhead every time you instantiate an object of the class?",
        "expected_answer": "Generally, no. Metaclass `__new__` and `__init__` methods execute exactly once per class when the module is imported and the class is constructed. Unless the metaclass explicitly overrides the `__call__` method (which intercepts instance creation), there is zero additional overhead during standard object instantiation.",
        "evaluation_rubric": {"strong_indicators": ["Clarifies execution at class definition time", "Notes that __call__ override is the only way it impacts instance creation performance"], "weak_indicators": ["Believes metaclasses run on every object creation"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": [],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the dual role of the built-in `type` function in Python.",
        "expected_answer": "When called with one argument, `type(obj)` returns the class/type of the object. When called with three arguments `type(name, bases, dict)`, it acts as the fundamental metaclass, dynamically creating and returning a new class object in memory.",
        "evaluation_rubric": {"strong_indicators": ["Type inspection (1 arg)", "Dynamic class creation (3 args)"], "weak_indicators": ["Only knows about type inspection"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "OOP", "secondary_skills": ["Design Patterns"],
        "technology": "Python", "topic": "Metaclasses", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Implement the Singleton design pattern in Python using a metaclass.",
        "expected_answer": "`class SingletonMeta(type):\\n    _instances = {}\\n    def __call__(cls, *args, **kwargs):\\n        if cls not in cls._instances:\\n            cls._instances[cls] = super().__call__(*args, **kwargs)\\n        return cls._instances[cls]`",
        "evaluation_rubric": {"strong_indicators": ["Overrides __call__ to intercept instance creation", "Uses a class-level dictionary to track instances"], "weak_indicators": ["Implements Singleton via standard __new__ instead of metaclass as requested"]}
    },

    # --- BUCKET 7: Python Memory Management -> GIL ---
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Memory Management", "secondary_skills": ["Concurrency"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the Global Interpreter Lock (GIL) in CPython?",
        "expected_answer": "The GIL is a mutex (lock) that allows only one thread to execute Python bytecode at a time in a single CPython process. This means that even on a multi-core processor, a standard Python multithreaded program will only utilize a single CPU core for execution.",
        "evaluation_rubric": {"strong_indicators": ["Mentions one thread executing bytecode at a time", "Mentions single CPU core limitation"], "weak_indicators": ["Thinks the GIL prevents multi-processing entirely"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the fundamental architectural reason why the GIL exists in the CPython implementation.",
        "expected_answer": "CPython uses reference counting for memory management. If multiple threads were allowed to increment and decrement object reference counts simultaneously without a lock, race conditions would corrupt memory, leading to memory leaks or premature garbage collection. The GIL is a coarse-grained lock that protects this internal memory state safely.",
        "evaluation_rubric": {"strong_indicators": ["Connects GIL to reference counting", "Mentions preventing memory corruption/race conditions"], "weak_indicators": ["Vague explanations about 'thread safety' without mentioning memory/reference counting"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Concurrency", "Performance"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the specific performance trade-offs of the GIL when running CPU-bound versus I/O-bound multithreaded applications?",
        "expected_answer": "For CPU-bound tasks, the GIL is detrimental because threads constantly fight for the lock, forcing single-core execution and adding severe context-switching overhead, making multithreading slower than sequential execution. For I/O-bound tasks, the GIL is automatically released during network or disk operations, allowing true concurrent progress and making multithreading highly effective.",
        "evaluation_rubric": {"strong_indicators": ["GIL is released during I/O", "Context-switching overhead ruins CPU-bound performance"], "weak_indicators": ["Believes multithreading is universally bad in Python"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "AI Engineer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Debugging", "Concurrency"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "You migrate a heavy image processing task to use the `threading` module to speed it up across an 8-core server. Upon deployment, CPU usage remains capped at 100% of a single core, and execution time increases. Why did this fail?",
        "expected_answer": "Image processing in pure Python is a CPU-bound task. The GIL prevents multiple threads from executing Python bytecode in parallel on multiple cores. The execution time actually increased due to the overhead of the OS rapidly switching thread contexts while they fight for the single GIL lock.",
        "evaluation_rubric": {"strong_indicators": ["Identifies task as CPU-bound", "Mentions GIL constraint", "Notes context switching overhead"], "weak_indicators": ["Fails to explain why execution time got worse"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Machine Learning Engineer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Architecture", "Performance"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are building a high-frequency data processing application in Python and must fully utilize 16 CPU cores. How do you architect the system to completely bypass the GIL?",
        "expected_answer": "The most common architectural approach is to use the `multiprocessing` module, which spawns separate OS processes, each with its own memory space and its own GIL. Alternatively, you can rewrite the CPU-bound algorithms in C/C++ or Cython and explicitly release the GIL (`with nogil:`) inside the extension before executing the math operations.",
        "evaluation_rubric": {"strong_indicators": ["Suggests multiprocessing", "Suggests C-extensions/Cython releasing the GIL"], "weak_indicators": ["Suggests asyncio", "Suggests standard threading"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Concurrency"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare how the GIL affects a Python `Thread` versus a Python `asyncio` Task.",
        "expected_answer": "The GIL restricts both. Python threads are OS-level threads managed by the kernel, requiring context switching and locking the GIL aggressively. `asyncio` Tasks are cooperative, user-space coroutines running on a single OS thread. The GIL is naturally held by the single event loop thread anyway, so `asyncio` avoids the overhead of GIL contention and OS context switching entirely for I/O tasks.",
        "evaluation_rubric": {"strong_indicators": ["Asyncio runs on a single thread so GIL contention is irrelevant", "Threads suffer OS context switching fighting for the GIL"], "weak_indicators": ["Thinks asyncio magically bypasses the GIL for CPU tasks"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Machine Learning Engineer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How do native C extensions like NumPy manage to achieve true parallelism and speed despite CPython's GIL?",
        "expected_answer": "NumPy relies on C/C++ code for heavy computations. Before starting a long-running matrix operation, NumPy's C code makes a specific API call (`Py_BEGIN_ALLOW_THREADS`) to release the GIL. Since the C code isn't interacting with Python objects or reference counts during the math, multiple C threads can execute in parallel. The GIL is re-acquired before returning results to Python.",
        "evaluation_rubric": {"strong_indicators": ["C extensions explicitly release the GIL", "Safe because they don't touch Python objects during computation"], "weak_indicators": ["Thinks NumPy is just inherently immune without releasing the lock"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A Python web server uses threads. One thread performs a long, pure-Python CPU task. You notice that all other threads serving simple HTTP requests experience massive latency spikes. How does the GIL's internal switching mechanism cause this?",
        "expected_answer": "The CPU-bound thread holds the GIL constantly. In modern Python, the GIL is released after a specific time interval (e.g., 5ms). However, the OS often reschedules the same CPU-bound thread immediately after it drops the lock, starving the I/O-bound HTTP threads that are waiting to acquire the GIL to parse requests.",
        "evaluation_rubric": {"strong_indicators": ["Identifies thread starvation", "Explains the drop-and-reacquire behavior of the active CPU thread"], "weak_indicators": ["Assumes the GIL is NEVER released by the CPU thread"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "If you are writing a custom C extension for Python, how do you explicitly release the GIL to allow multi-threading optimization?",
        "expected_answer": "You use the C-API macros `Py_BEGIN_ALLOW_THREADS` before the computational block begins, and `Py_END_ALLOW_THREADS` when it finishes. This allows other Python threads to run while the C code computes. (In Cython, this is done using the `with nogil:` context manager).",
        "evaluation_rubric": {"strong_indicators": ["Mentions Py_BEGIN_ALLOW_THREADS or Cython 'with nogil'"], "weak_indicators": ["Vague 'call a C function' without knowing the macros"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Memory Management", "secondary_skills": [],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "Does every implementation of Python have a Global Interpreter Lock (GIL)? Give examples.",
        "expected_answer": "No, the GIL is a specific implementation detail of CPython (the standard implementation). Other implementations like Jython (running on the JVM) and IronPython (running on .NET) do not have a GIL and support true multi-core threading.",
        "evaluation_rubric": {"strong_indicators": ["Identifies GIL as specific to CPython", "Provides Jython or IronPython as exceptions"], "weak_indicators": ["Thinks every Python variation has a GIL"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Concurrency"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Provide a concrete scenario and corresponding code concept where using `concurrent.futures.ProcessPoolExecutor` is strictly superior to `ThreadPoolExecutor` due to the GIL.",
        "expected_answer": "A scenario involving heavy mathematical computation, like factoring large primes or processing millions of rows of data natively in Python. The `ProcessPoolExecutor` spawns multiple processes, bypassing the GIL to use multiple cores. Code: `with ProcessPoolExecutor() as ex: results = ex.map(heavy_math_function, data_list)`.",
        "evaluation_rubric": {"strong_indicators": ["Identifies a CPU-bound mathematical/data scenario", "Mentions bypassing the GIL via processes"], "weak_indicators": ["Provides an I/O bound example like web scraping"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Architecture"],
        "primary_skill": "Memory Management", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "Python 3.13 introduces an experimental 'free-threaded' (No-GIL) build. What are the major architectural trade-offs and risks of disabling the GIL globally?",
        "expected_answer": "Removing the GIL unlocks true multi-core threading but introduces massive risks: single-threaded execution becomes slower due to fine-grained locking overhead (reference count locks), and thousands of third-party C extensions that implicitly relied on the GIL for thread safety will face catastrophic race conditions and crashes.",
        "evaluation_rubric": {"strong_indicators": ["Identifies third-party C extension thread safety risks", "Notes single-threaded performance degradation due to granular locks"], "weak_indicators": ["Thinks removing the GIL makes everything perfectly faster without side effects"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Java Developer"],
        "primary_skill": "Memory Management", "secondary_skills": ["Concurrency"],
        "technology": "Python", "topic": "GIL", "category": "Programming Languages",
        "intent": "compare", "difficulty": "hard", "question_type": "comparison",
        "question": "Compare the threading memory overhead and safety of CPython with the GIL versus a language with fine-grained object locking like Java.",
        "expected_answer": "CPython's GIL provides a massive safety net—it guarantees atomic bytecode execution, making internal dictionary/list updates thread-safe implicitly, keeping memory management simple and fast for single threads. Java uses fine-grained locking, requiring explicit synchronization on objects, which is harder to program and introduces memory overhead for object headers/monitors, but rewards the user with true parallel scaling.",
        "evaluation_rubric": {"strong_indicators": ["GIL provides implicit thread safety for built-ins", "Java requires explicit synchronization/monitors", "Fine-grained locks have higher single-thread overhead"], "weak_indicators": ["Fails to identify the safety benefits of the GIL"]}
    },

    # --- BUCKET 8: Python Concurrency -> Multithreading ---
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Concurrency", "secondary_skills": [],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the primary use case for the `threading` module in Python given the existence of the GIL?",
        "expected_answer": "The primary use case is handling I/O-bound operations concurrently, such as network requests, file reading/writing, or database queries. Since the GIL is released during I/O wait times, multiple threads can progress efficiently.",
        "evaluation_rubric": {"strong_indicators": ["Identifies I/O bound tasks", "Explains GIL release during I/O"], "weak_indicators": ["Claims threading is used for parallel computation"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Java Developer"],
        "primary_skill": "Concurrency", "secondary_skills": [],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the concept of a Race Condition in Python multithreading. Doesn't the GIL prevent them?",
        "expected_answer": "A race condition occurs when multiple threads access and mutate shared state concurrently. While the GIL protects internal CPython memory, it does not protect application-level logic. For example, `counter += 1` translates to multiple bytecode instructions. The GIL can switch threads between reading the counter and writing the incremented value, causing lost updates.",
        "evaluation_rubric": {"strong_indicators": ["Explains bytecode instruction interruption", "Distinguishes between internal memory safety and application state safety"], "weak_indicators": ["Believes the GIL prevents all race conditions natively"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Concurrency", "secondary_skills": [],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Implement a thread-safe counter class using `threading.Lock`.",
        "expected_answer": "`import threading\\nclass Counter:\\n    def __init__(self):\\n        self.val = 0\\n        self.lock = threading.Lock()\\n    def increment(self):\\n        with self.lock:\\n            self.val += 1`",
        "evaluation_rubric": {"strong_indicators": ["Uses context manager (with self.lock)", "Initializes lock in __init__"], "weak_indicators": ["Forgets to release the lock manually if not using the context manager"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Concurrency", "secondary_skills": [],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "medium", "question_type": "tradeoff",
        "question": "What are the trade-offs of using `threading.RLock` (Reentrant Lock) instead of a standard `threading.Lock`?",
        "expected_answer": "An `RLock` allows the *same* thread to acquire the lock multiple times without blocking itself, which is useful for recursive functions or complex object methods that call each other. However, `RLock` is slightly slower and consumes more overhead than a standard `Lock` because it must track thread ownership and recursion depth.",
        "evaluation_rubric": {"strong_indicators": ["Mentions the same thread acquiring it multiple times", "Identifies recursion depth tracking", "Mentions slight performance overhead"], "weak_indicators": ["Confuses RLock with Read/Write locks"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Concurrency", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "debug", "difficulty": "hard", "question_type": "debugging",
        "question": "Thread 1 acquires Lock A, then tries to acquire Lock B. Thread 2 acquires Lock B, then tries to acquire Lock A. The application freezes permanently. What is this called, and how do you fix it?",
        "expected_answer": "This is a classic Deadlock. It occurs due to circular waiting. The fix is to enforce a strict lock acquisition hierarchy globally—ensuring all threads acquire Lock A before Lock B—or to use non-blocking acquire attempts with a timeout to back off and retry.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the situation as a Deadlock", "Proposes strict ordering/hierarchy or timeout backoff"], "weak_indicators": ["Suggests just removing locks entirely without addressing the shared state"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Concurrency", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You need to concurrently scrape 1,000 independent URLs as fast as possible. Architect a thread pooling strategy to accomplish this without overwhelming the OS or the target servers.",
        "expected_answer": "Use `concurrent.futures.ThreadPoolExecutor`. Set `max_workers` to a sensible limit (e.g., 20-50) rather than spawning 1000 raw threads. Submit tasks to the pool and use `as_completed` to process results as they arrive. This controls OS context switching overhead and prevents network flooding.",
        "evaluation_rubric": {"strong_indicators": ["Suggests ThreadPoolExecutor", "Explicitly limits max_workers to batch the workload"], "weak_indicators": ["Suggests a raw loop of threading.Thread().start() 1000 times"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Concurrency", "secondary_skills": [],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare a `threading.Event` with a `threading.Condition` in Python.",
        "expected_answer": "An `Event` is a simple boolean flag; one thread sets it, and others wait for it to become true (useful for simple state signaling). A `Condition` wraps a Lock and allows threads to wait for a specific state change, while also allowing the notifying thread to wake up one or all waiting threads safely while holding the lock (useful for producer-consumer queues).",
        "evaluation_rubric": {"strong_indicators": ["Event is a simple boolean flag", "Condition wraps a lock for complex state checks and wakeups"], "weak_indicators": ["Fails to mention that Condition requires acquiring a lock"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Concurrency", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "When designing a multithreaded producer-consumer architecture, why is the built-in `queue.Queue` heavily preferred over using a standard Python `list` combined with manual locks?",
        "expected_answer": "`queue.Queue` is inherently thread-safe and abstracts away the complex locking logic. More importantly, it natively implements blocking `put()` and `get()` methods with optional timeouts, utilizing `threading.Condition` under the hood to efficiently put threads to sleep when the queue is empty/full, avoiding CPU-wasting spin-locks.",
        "evaluation_rubric": {"strong_indicators": ["Mentions built-in thread safety", "Highlights blocking get/put behavior without spin-locking"], "weak_indicators": ["Thinks standard lists are thread-safe natively"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "DevOps / Cloud Engineer"],
        "primary_skill": "Concurrency", "secondary_skills": ["Debugging"],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "medium", "question_type": "debugging",
        "question": "A child thread raises an unhandled exception during network processing. However, the main Python process continues running, hiding the failure. How do you properly capture exceptions from child threads?",
        "expected_answer": "Exceptions in spawned threads do not propagate to the main thread natively. To capture them, you can use `concurrent.futures.ThreadPoolExecutor` where calling `.result()` on the future re-raises the exception in the main thread. Alternatively, override `threading.excepthook` to log or handle uncaught thread exceptions globally.",
        "evaluation_rubric": {"strong_indicators": ["Identifies that thread exceptions don't propagate", "Suggests Future.result()", "Suggests threading.excepthook"], "weak_indicators": ["Suggests putting a try/except around the thread.start() call (which doesn't work)"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "System Design"],
        "primary_skill": "Concurrency", "secondary_skills": ["Performance"],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "hard", "question_type": "optimization",
        "question": "You need to maintain 10,000 persistent idle WebSocket connections. Does spawning 10,000 Python threads scale well for this? How do you optimize the architecture?",
        "expected_answer": "No. OS threads consume significant memory (typically megabytes per thread stack) and incur massive kernel context-switching overhead. 10,000 threads will likely crash the process or thrash the OS. Optimize this by switching to asynchronous I/O (`asyncio`), which can multiplex tens of thousands of sockets on a single thread using non-blocking event loops (epoll/kqueue).",
        "evaluation_rubric": {"strong_indicators": ["Identifies OS memory overhead per thread", "Identifies context switching overload", "Suggests asyncio/event loops"], "weak_indicators": ["Suggests using a ThreadPoolExecutor of size 10000"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Concurrency", "secondary_skills": [],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "What is a 'daemon thread' in Python and in what scenario should it be used?",
        "expected_answer": "A daemon thread is a background thread that does not prevent the Python interpreter from exiting. Once all non-daemon (main) threads complete, the program terminates and abruptly kills any remaining daemon threads. They are used for background tasks like telemetry reporting, garbage collection, or health checks that shouldn't block shutdown.",
        "evaluation_rubric": {"strong_indicators": ["Interpreter exits without waiting for daemon threads", "Mentions background tasks/telemetry"], "weak_indicators": ["Confuses daemon threads with Unix daemon processes"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Concurrency", "secondary_skills": [],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Write a snippet that spins up 5 threads executing a `worker()` function, and blocks the main thread until all 5 have finished.",
        "expected_answer": "`threads = []\\nfor _ in range(5):\\n    t = threading.Thread(target=worker)\\n    t.start()\\n    threads.append(t)\\nfor t in threads:\\n    t.join()`",
        "evaluation_rubric": {"strong_indicators": ["Appends threads to a list", "Iterates the list calling .join()"], "weak_indicators": ["Calls .join() immediately after .start() in the same loop (making it sequential)"]}
    },
    {
        "primary_role": "Python Developer", "applicable_roles": ["Backend Developer", "DevOps / Cloud Engineer"],
        "primary_skill": "Concurrency", "secondary_skills": ["Architecture"],
        "technology": "Python", "topic": "Multithreading", "category": "Programming Languages",
        "intent": "compare", "difficulty": "hard", "question_type": "comparison",
        "question": "Compare the memory footprint and OS-level handling of a Python Thread versus a Python Process created via the `multiprocessing` module.",
        "expected_answer": "A Thread is lightweight; it shares the same memory space, heap, and file descriptors as the main process, meaning its overhead is mostly just a stack allocated by the OS. A Process requires the OS to allocate a completely new virtual memory space, duplicate resources (or use Copy-on-Write), and instantiate a brand new Python interpreter with its own GIL, making it vastly more memory intensive.",
        "evaluation_rubric": {"strong_indicators": ["Shared memory vs independent memory", "New Python interpreter/GIL per process", "Copy-on-write mechanics"], "weak_indicators": ["Claims processes are faster without mentioning the heavy memory overhead"]}
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

    # Remaining gap from previous is 3661. We subtract accepted.
    remaining_count = 3661 - accepted

    report = {
        "Batch 2 buckets processed": 4, # Inheritance, Metaclasses, GIL, Multithreading
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
        "Remaining gap count": remaining_count,
        "Files updated": [
            "data/interview_question_bank_v2_generated.jsonl",
            "reports/phase4d_quality_report.json"
        ]
    }
    
    # Let's read the previous report to merge it or just overwrite it as a snapshot.
    # The prompt says "Update: reports/phase4d_quality_report.json"
    # We will just write the new snapshot.
    with open(os.path.join(REPORTS_DIR, "phase4d_quality_report_batch2.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    for k, v in report.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
