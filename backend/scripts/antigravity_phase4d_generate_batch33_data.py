"""Batch 33 Part 1 question content (Python Developer). Targeted Gap Generation."""

ROLE = "Python Developer"

BUCKET_KEYS = {
    "ADVANCED_OOP": ("Advanced OOP", "Metaclasses & Descriptors", "Python", ["Python Developer", "Backend Developer"]),
}

Q = [
# ---------------- ADVANCED_OOP ----------------
("ADVANCED_OOP", "explain", "medium", "concept", ["__init__", "__new__"],
 "What is the exact difference between `__init__` and `__new__` in Python, and when must you use `__new__`?",
 "`__new__` is a static class method that actually *creates* and returns the new uninitialized instance object in memory. `__init__` is an instance method that merely initializes the already-created object. You *must* use `__new__` when subclassing immutable built-in types (like `tuple` or `str`) because they cannot be modified after creation in `__init__`, or when implementing a Singleton pattern.",
 ["`__new__` creates the object instance; `__init__` initializes it", "Must use `__new__` when subclassing immutable types (tuples, strings)", "Must use `__new__` for structural allocation patterns like Singletons"],
 ["`__new__` is for Python 3 and `__init__` is for Python 2"]),

("ADVANCED_OOP", "implement", "hard", "implementation", ["Descriptors", "Validation"],
 "You need to implement a Python class attribute that strictly validates its value (e.g., must be a positive integer) across *all* instances, without writing repetitive `@property` decorators for every attribute. What advanced OOP feature do you use?",
 "You implement a Descriptor class. You define a separate class with `__get__`, `__set__`, and `__set_name__` methods. In `__set__`, you write the validation logic. Then, in your main class, you instantiate the descriptor as a class attribute. All attribute assignments will automatically route through the descriptor's `__set__` method, centralizing the validation.",
 ["Implement a Descriptor class (using `__get__` and `__set__`)", "The validation logic lives inside the descriptor's `__set__` method", "Instantiate the descriptor as a class-level attribute in the target class"],
 ["Use a global variable and an `if` statement in the `__init__`"]),

("ADVANCED_OOP", "debug", "hard", "debugging", ["Multiple Inheritance", "MRO"],
 "You have a hierarchy: `class D(B, C):`. Calling `super().__init__()` in `D` calls `B`'s init, but `C`'s init is completely skipped. Why did `super()` fail to call all parents, and how do you fix it?",
 "`super()` does not magically call all parent classes; it calls the *next* class in the Method Resolution Order (MRO). `C`'s init was skipped because `B`'s `__init__` failed to call `super().__init__()` inside itself to continue the chain. In multiple inheritance, every class in the hierarchy must call `super()` cooperatively to ensure the entire MRO is traversed.",
 ["`super()` calls the next class in the Method Resolution Order (MRO), not 'all parents'", "`B` failed to call `super().__init__()`, breaking the cooperative chain", "Fix: All classes in a multiple inheritance hierarchy must cooperatively call `super()`"],
 ["Python limits you to one parent class to prevent confusion"]),

("ADVANCED_OOP", "tradeoff", "medium", "tradeoff", ["__slots__", "Memory Management"],
 "What is the memory tradeoff of using `__slots__` in a Python class?",
 "By default, Python instances store attributes in a dynamic `__dict__` dictionary, which consumes significant memory overhead. Defining `__slots__ = ['attr1']` tells Python to use a static C-struct array instead, drastically reducing RAM usage for millions of instances. The tradeoff is the loss of dynamic assignment; you cannot add new attributes at runtime unless you explicitly add `'__dict__'` to the slots.",
 ["`__slots__` replaces the dynamic `__dict__` with a static C-struct array", "Drastically reduces memory overhead when instantiating millions of objects", "Tradeoff: Prevents dynamic attribute assignment at runtime"],
 ["`__slots__` makes the code run 100x slower for security reasons"]),

("ADVANCED_OOP", "explain", "hard", "concept", ["Metaclasses", "Class Decorators"],
 "How does a Python Metaclass differ from a Class Decorator, and when is a Metaclass required?",
 "A class decorator runs *after* the class object is fully created in memory, allowing you to mutate or wrap it. A metaclass (inheriting from `type`) hooks directly into the class *creation* process itself (via `__new__`). Metaclasses are required when you need to intercept and modify class-level attributes, methods, or inheritance *before* the class object actually exists.",
 ["Decorators run *after* the class is created; Metaclasses hook into the *creation* process itself", "Metaclasses inherit from `type` and override `__new__` / `__init__`", "Required when mutating class structure, inheritance, or attributes *before* memory allocation"],
 ["Metaclasses are just decorators written in C++"]),

("ADVANCED_OOP", "implement", "medium", "implementation", ["Singleton", "Metaclasses"],
 "How do you implement a robust Singleton pattern in Python that guarantees only one instance is ever created, even across multiple instantiations?",
 "The most robust way is to use a Metaclass that overrides `__call__`. The metaclass maintains a private `_instances` dictionary. When `MyClass()` is called, the metaclass checks if the class is in `_instances`; if not, it calls `super().__call__()`. This is superior to overriding `__new__` on the class itself, which still implicitly triggers `__init__` on every call.",
 ["Use a Metaclass overriding `__call__`", "Maintain a private dictionary of `_instances` inside the metaclass", "Prevents the `__init__` method from being re-executed on subsequent calls (unlike overriding `__new__`)"],
 ["Just create a global variable and hope nobody changes it"]),

("ADVANCED_OOP", "fundamentals", "easy", "concept", ["MRO", "C3 Linearization"],
 "What is 'Method Resolution Order' (MRO) in Python, and how can you view it?",
 "MRO is the strict, linearized sequence in which Python searches for base classes when resolving a method or attribute call in a multiple inheritance hierarchy. Python uses the C3 linearization algorithm to determine this order. You can view it by inspecting the `__mro__` dunder attribute on the class or calling the `.mro()` method.",
 ["The linearized sequence Python searches to resolve methods in multiple inheritance", "Uses the C3 Linearization algorithm", "Viewed via `ClassName.__mro__` or `ClassName.mro()`"],
 ["The order in which Python deletes variables during garbage collection"]),

("ADVANCED_OOP", "debug", "medium", "debugging", ["Mutable Defaults", "State Bleed"],
 "You define `def my_method(self, items=[]):`. Every time you append to `items` on a new object, the previous object's items are also modified. Why does state bleed across instances?",
 "This is the 'Mutable Default Argument' anti-pattern. Default arguments are evaluated exactly *once* when the `def` statement is executed (at module import time), not every time the method is called. All instances share the exact same underlying list object in memory. You must use `items=None` and initialize `self.items = items or []` inside the method.",
 ["Mutable Default Argument anti-pattern", "Default arguments are evaluated exactly once at module load time", "All instances share the exact same list in memory. Fix: Use `items=None`"],
 ["Python lists are globally connected by default"]),

("ADVANCED_OOP", "explain", "medium", "concept", ["@classmethod", "@staticmethod"],
 "What is the purpose of the `@classmethod` decorator compared to `@staticmethod`?",
 "`@classmethod` receives the class itself as the implicit first argument (`cls`), allowing the method to access class attributes, instantiate the class, or be inherited dynamically (heavily used for Alternative Constructors). `@staticmethod` receives neither the instance nor the class; it is just a regular function arbitrarily grouped inside the class namespace for organizational convenience.",
 ["`@classmethod` receives the class (`cls`) as the first argument; used for Alternative Constructors", "`@staticmethod` receives neither instance nor class; it is completely isolated from class state", "`@staticmethod` is just a regular function grouped in the class for organization"],
 ["`@classmethod` is for public methods, `@staticmethod` is for private methods"]),

("ADVANCED_OOP", "implement", "hard", "implementation", ["Dunder Methods", "Dictionary Subclass"],
 "You want to create a class that behaves like a dictionary (`obj['key'] = 'value'`), but natively supports dot-notation (`obj.key = 'value'`). How do you implement this?",
 "Create a class inheriting from `dict`. To support dot-notation, you must override the dunder methods `__getattr__` and `__setattr__`. `__getattr__` should `return self[key]` (handling `KeyError` by raising `AttributeError`), and `__setattr__` should execute `self[key] = value`.",
 ["Inherit from `dict`", "Override `__getattr__` to map dot-notation reads to `self[key]`", "Override `__setattr__` to map dot-notation assignments to `self[key] = value`"],
 ["Use `eval()` to convert the dot notation to a string key"]),

("ADVANCED_OOP", "tradeoff", "hard", "tradeoff", ["Abstract Base Classes", "Interfaces"],
 "You need an interface-like contract. What is the tradeoff of using the `abc` module (Abstract Base Classes) versus standard `NotImplementedError` exceptions?",
 "Using `abc.ABC` and `@abstractmethod` forces structural validation at *instantiation* time; Python will crash immediately if you try to instantiate a subclass missing a required method, failing fast. Standard `NotImplementedError` in a parent class only fails at *runtime* if that specific method is executed. ABCs are safer but add slight import overhead.",
 ["ABCs enforce contracts at *instantiation* time (fails fast)", "`NotImplementedError` only fails at *runtime* when the method is actually called", "ABCs natively support robust `issubclass()` and `isinstance()` checks"],
 ["ABCs require learning the alphabet first"]),

("ADVANCED_OOP", "scenario", "medium", "scenario", ["Context Managers", "Resource Cleanup"],
 "You are designing a database library. You want users to use your object in a `with` statement to guarantee connection cleanup. Which two dunder methods must you implement?",
 "You must implement the Context Manager protocol: `__enter__(self)` and `__exit__(self, exc_type, exc_val, exc_tb)`. `__enter__` sets up the resource and returns it. `__exit__` handles the teardown (closing connections). If an exception occurs inside the `with` block, `__exit__` receives the details and can optionally suppress it by returning `True`.",
 ["Must implement `__enter__` and `__exit__`", "`__enter__` allocates the resource; `__exit__` guarantees cleanup", "`__exit__` receives exception arguments and can suppress them by returning `True`"],
 ["`__start__` and `__stop__`"]),

("ADVANCED_OOP", "explain", "hard", "concept", ["Data Descriptors", "Lookup Priority"],
 "In Python, what is a 'Data Descriptor' vs a 'Non-Data Descriptor', and how does it affect attribute lookup priority?",
 "A Data Descriptor implements both `__get__` and `__set__`. A Non-Data Descriptor implements only `__get__` (like standard methods). Lookup priority is strict: Data Descriptors override instance variables in the `__dict__`. However, instance variables override Non-Data Descriptors. This is why you cannot overwrite a `@property` by assigning to `self.attr`, but you can overwrite a method.",
 ["Data Descriptor: implements `__get__` and `__set__`", "Non-Data Descriptor: implements only `__get__`", "Lookup priority: Data Descriptors > Instance variables > Non-Data Descriptors"],
 ["Data descriptors describe data, non-data descriptors describe emotions"]),

("ADVANCED_OOP", "implement", "medium", "implementation", ["__str__", "__repr__"],
 "You want `print(user)` to output 'User: John', but typing `user` in the REPL or logging it to output a strict debugging string `<User(id=5)>`. How do you implement this?",
 "Override both `__str__` and `__repr__`. `__str__` handles the human-readable `print()` output. `__repr__` handles the strict, unambiguous developer debugging output for the REPL/logs. If `__str__` is not defined, Python falls back to `__repr__`, making `__repr__` the most critical for debugging.",
 ["Implement `__str__` for human-readable output (e.g., `print()`)", "Implement `__repr__` for strict, unambiguous developer debugging (REPL/logging)", "If `__str__` is missing, Python safely falls back to `__repr__`"],
 ["Use an if statement checking if the user is a developer"]),

("ADVANCED_OOP", "debug", "hard", "debugging", ["Class Decorators", "Identity"],
 "You use a class decorator for a registry. The classes work, but `issubclass(SubClass, BaseClass)` starts returning `False` unexpectedly, and `__name__` is wrong. What did the decorator break?",
 "The class decorator likely returned a *wrapper function* or a dynamically created proxy class instead of returning the original class object. This destroys the original class identity, metadata, and inheritance chain. A proper class decorator (unless specifically designed as a transparent proxy) should perform its mutation and then `return cls` directly.",
 ["The decorator returned a wrapper or proxy instead of the original class object", "Destroyed the original class identity, inheritance chain, and metadata (`__name__`)", "Fix: A registry decorator should mutate state and `return cls` directly"],
 ["The decorator forgot to import the subclass module"]),

("ADVANCED_OOP", "fundamentals", "easy", "concept", ["Name Mangling", "Encapsulation"],
 "What is name mangling in Python, and how is it triggered?",
 "Name mangling is Python's rudimentary form of private variables, triggered by prefixing an attribute with double underscores (e.g., `__secret`). Python automatically renames this attribute internally to `_ClassName__secret`. It prevents naming collisions in deep inheritance hierarchies where subclasses might accidentally overwrite a parent's internal state.",
 ["Triggered by double underscore prefixes (`__attr`)", "Automatically renames the attribute internally to `_ClassName__attr`", "Intended to prevent naming collisions in inheritance hierarchies, not strict security"],
 ["Mangling destroys the variable so hackers can't read it"]),

("ADVANCED_OOP", "scenario", "medium", "scenario", ["Hashable", "Dictionaries"],
 "You want a custom object to be usable as a key in a Python dictionary. What two dunder methods must the object's class properly implement?",
 "The object must be Hashable. You must implement `__hash__` (returning a consistent integer based on immutable state) and `__eq__` (to handle hash collisions by comparing true logical equality). If the object is mutable, it should not implement `__hash__` (or set it to `None`), as mutating a key after insertion corrupts the dictionary's hash table.",
 ["Must implement `__hash__` and `__eq__`", "`__hash__` returns a consistent integer; `__eq__` resolves hash collisions", "The attributes used for the hash must be immutable to prevent corrupting the hash table"],
 ["`__dict__` and `__list__`"])
]
