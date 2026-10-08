"""Batch 35 Part 3 question content (Java Developer). Targeted Gap Generation."""

ROLE = "Java Developer"

BUCKET_KEYS = {
    "MODERN_JAVA_AND_LANGUAGE": ("Java Language", "Language Features", "Java", ["Java Developer", "Backend Developer"]),
}

Q = [
# ---------------- MODERN_JAVA_AND_LANGUAGE ----------------
("MODERN_JAVA_AND_LANGUAGE", "debug", "medium", "debugging", ["Collections", "Arrays.asList"],
 "A developer creates `List<String> list = Arrays.asList(\"A\", \"B\");` and calls `list.add(\"C\");`. The app crashes with `UnsupportedOperationException`. Why does adding to this list crash, and what is the fix?",
 "`Arrays.asList()` (and `List.of()`) return specialized, fixed-size or immutable list implementations, not standard `java.util.ArrayList` objects. You cannot add or remove elements from them. To fix it and create a fully mutable list, wrap it in a new ArrayList constructor: `new ArrayList<>(Arrays.asList(\"A\", \"B\"))`.",
 ["`Arrays.asList()` returns a fixed-size list wrapper, not a standard `java.util.ArrayList`", "Attempting to modify the size (add/remove) throws `UnsupportedOperationException`", "Fix: Wrap it to instantiate a new mutable list (`new ArrayList<>(Arrays.asList(...))`)"],
 ["The alphabet only has 26 letters and \"C\" was already used"]),

("MODERN_JAVA_AND_LANGUAGE", "tradeoff", "easy", "tradeoff", ["Records", "Immutability"],
 "In modern Java (14+), what is the architectural tradeoff of declaring a DTO as a `record` instead of a standard `class`?",
 "A `record` drastically reduces boilerplate; the compiler automatically generates immutable fields, a canonical constructor, getters, `equals()`, `hashCode()`, and `toString()`. Tradeoff: Strict immutability and lack of inheritance. All fields are fundamentally `final`, you cannot add instance fields outside the header, and a `record` cannot extend any other class.",
 ["Drastically reduces boilerplate (auto-generates constructor, getters, `equals`, `hashCode`, `toString`)", "Tradeoff: Strict immutability (all fields are `final`)", "Tradeoff: Cannot extend any other class (no inheritance)"],
 ["Records require a vinyl turntable to execute properly"]),

("MODERN_JAVA_AND_LANGUAGE", "implement", "medium", "implementation", ["Streams", "Collectors"],
 "You have a `List<Employee>`. You want to group these employees by their department (`String`) into a `Map<String, List<Employee>>`. Provide the single line of Java Streams code to achieve this.",
 "`employees.stream().collect(Collectors.groupingBy(Employee::getDepartment));`. This utilizes the built-in `groupingBy` collector to automatically bucket the stream elements into a Map based on the provided classifier function (the department getter).",
 ["Use the Streams API: `employees.stream()`", "Use the terminal operation: `.collect(...)`", "Use the specific collector: `Collectors.groupingBy(Employee::getDepartment)`"],
 ["Use a `for` loop and a `switch` statement for every possible department"]),

("MODERN_JAVA_AND_LANGUAGE", "scenario", "hard", "scenario", ["Recursion", "StackOverflowError"],
 "A deeply nested recursive method occasionally crashes with `StackOverflowError`. Increasing the JVM `-Xss` (thread stack size) only delays the crash. How do you permanently eliminate the error without modifying the core logic?",
 "Refactor the algorithm from recursion to iteration using an explicit Heap-based data structure (like `java.util.Stack` or `ArrayDeque`). Recursion consumes a new frame on the Thread Stack for every call, which is highly bounded (~1MB). An explicit `Deque` in a `while` loop moves memory tracking to the massive Java Heap, allowing unbounded depth.",
 ["Refactor the algorithm from recursion to iteration", "Use an explicit Heap-based data structure (e.g., `ArrayDeque` or `Stack`)", "Moves the call hierarchy memory from the tiny Thread Stack to the massive Java Heap"],
 ["Recursion is illegal in modern Java versions"]),

("MODERN_JAVA_AND_LANGUAGE", "explain", "medium", "concept", ["Sealed Classes", "Domain Modeling"],
 "What is a 'Sealed Class' in Java (15+), and what specific architectural problem does it solve?",
 "A Sealed Class (`public sealed class Shape permits Circle, Square`) strictly restricts which specific other classes are allowed to extend it. It solves the architectural problem of exhaustive domain modeling; it allows the API creator to define a closed taxonomy. This enables the compiler to enforce exhaustiveness checks in modern `switch` pattern matching.",
 ["Strictly restricts exactly which classes are permitted to extend it", "Solves exhaustive domain modeling (defining a closed, finite taxonomy of types)", "Enables the compiler to enforce exhaustive `switch` pattern matching (no `default` case needed)"],
 ["It seals the class so hackers cannot open it with a decompiler"]),

("MODERN_JAVA_AND_LANGUAGE", "debug", "hard", "debugging", ["Parallel Streams", "Blocking I/O"],
 "You use `list.parallelStream().map(obj -> slowHttpCall(obj)).collect(...)`. The stream performs terribly and freezes other parts of the app. Why is `parallelStream` the wrong tool here?",
 "`parallelStream()` executes tasks on the shared global `ForkJoinPool.commonPool()`. This pool is sized exactly to the number of physical CPU cores (e.g., 8 threads). If you block those 8 threads with slow HTTP I/O, the entire stream halts, and the common pool becomes completely exhausted, freezing all other parallel streams. Use a custom thread pool for I/O.",
 ["`parallelStream` uses the shared global `ForkJoinPool.commonPool()`", "Blocking I/O completely exhausts the limited threads in the common pool", "Freezes all other parallel streams in the JVM. Fix: Parallel streams are strictly for CPU-bound tasks"],
 ["The HTTP call got dizzy from being parallelized"]),

("MODERN_JAVA_AND_LANGUAGE", "tradeoff", "medium", "tradeoff", ["Arrays", "Lists"],
 "When designing an API, what is the tradeoff of accepting an array (`String[]`) versus a `List<String>` as a method parameter?",
 "Arrays are covariant but inherently mutable and strictly fixed in size. Lists are invariant, dynamically resizable, and can easily be made fully immutable (`List.of()`). Lists provide a vastly richer API (Streams, Collections) and better type safety via Generics, making `List` universally preferred in modern Java APIs, reserving arrays for low-level performance.",
 ["Arrays are strictly fixed in size and inherently mutable", "Lists are dynamically resizable, support Generics, and can be made fully immutable", "Lists provide a richer API (Streams) and are universally preferred for domain modeling"],
 ["Arrays are for numbers, Lists are for text"]),

("MODERN_JAVA_AND_LANGUAGE", "implement", "easy", "implementation", ["Map", "Iteration"],
 "You need to iterate over a `Map<String, Integer>` and print the key and value. What is the cleanest, most performant way to do this in modern Java without looking up the key twice?",
 "Use `map.forEach((key, value) -> System.out.println(key + \": \" + value));`. Alternatively, iterate over `map.entrySet()` in a for-each loop: `for (Map.Entry<String, Integer> entry : map.entrySet())`. Never iterate over `map.keySet()` and call `map.get(key)` inside the loop, as it performs a redundant, expensive hash lookup.",
 ["Use `map.forEach((key, value) -> ...)`", "Alternatively, use a for-each loop over `map.entrySet()`", "Prevents redundant and expensive `.get(key)` hash lookups"],
 ["Print the memory address of the Map instead"]),

("MODERN_JAVA_AND_LANGUAGE", "scenario", "medium", "scenario", ["equals", "hashCode"],
 "You override `equals()` on a custom class. `obj1.equals(obj2)` returns `true`. However, you add `obj1` to a `HashSet`, and `set.contains(obj2)` incorrectly returns `false`. What contract did you violate?",
 "You violated the `equals()` and `hashCode()` contract. If two objects are logically equal (via `equals`), they *must* return the exact same integer from `hashCode()`. `HashSet` uses the hash code to determine which internal bucket to look in. Because you didn't override `hashCode()`, `obj1` and `obj2` landed in different buckets, so the Set couldn't find it.",
 ["Violated the `equals()` and `hashCode()` contract", "If two objects are logically equal, they MUST return the exact same `hashCode()`", "Without overriding `hashCode()`, the `HashSet` looks in the wrong internal bucket"],
 ["The HashSet secretly deletes items to save memory"]),

("MODERN_JAVA_AND_LANGUAGE", "explain", "hard", "concept", ["Generics", "Type Erasure"],
 "In Java Generics, what is 'Type Erasure', and why does it prevent you from writing `if (obj instanceof List<String>)`?",
 "Type Erasure is a backwards-compatibility mechanism. The Java compiler entirely removes (erases) all Generic type parameters (`<String>`) during compilation, replacing them with raw types (e.g., `Object`). At runtime, the JVM has absolutely no knowledge of the Generic types. Therefore, an `instanceof` check against `<String>` is physically impossible at runtime.",
 ["Type Erasure removes Generic type parameters during compilation for backwards compatibility", "At runtime, the JVM only sees raw types (e.g., `Object` or `List`), stripping the Generic metadata", "Prevents runtime type checking (`instanceof`) against specific Generic implementations"],
 ["Type Erasure is when you use a pencil eraser on the monitor"]),

("MODERN_JAVA_AND_LANGUAGE", "debug", "medium", "debugging", ["Strings", "Immutability"],
 "A developer writes: `String s = \"\"; for (int i=0; i<10000; i++) { s += \"A\"; }`. The code takes seconds to run and consumes massive memory. Why is String concatenation inside a loop a critical performance flaw?",
 "Strings in Java are strictly immutable. Using the `+=` operator inside a loop forces the JVM to allocate a brand new `String` object on the heap and copy the entire contents of the previous string on *every single iteration*. This results in O(N^2) time complexity and massive GC overhead. Fix: Use a mutable `StringBuilder` and `.append()`.",
 ["Strings are strictly immutable in Java", "`+=` inside a loop forces the JVM to allocate a brand new String object on every iteration", "Results in O(N^2) time complexity and massive GC overhead. Fix: Use `StringBuilder.append()`"],
 ["The letter 'A' is mathematically heavier than other letters"]),

("MODERN_JAVA_AND_LANGUAGE", "implement", "hard", "implementation", ["Generics", "Wildcards"],
 "You need a method that accepts a list of *any* type of Number (`Integer`, `Double`, etc.) and sums them up. How do you define the signature using Generic wildcards to safely accept a `List` of any Number subclass?",
 "You must use an Upper Bounded Wildcard: `public double sum(List<? extends Number> numbers)`. This tells the compiler that the list can safely contain any subclass of `Number`. If you just used `List<Number>`, it would strictly reject `List<Integer>` because Generics are invariant.",
 ["Use an Upper Bounded Wildcard: `List<? extends Number>`", "Allows the method to safely accept a List parameterized with any subclass of Number", "Standard `List<Number>` fails because Java Generics are strictly invariant"],
 ["Just use `List<Object>` and cast it repeatedly"]),

("MODERN_JAVA_AND_LANGUAGE", "tradeoff", "medium", "tradeoff", ["Reflection", "Metaprogramming"],
 "What is the tradeoff of using Java Reflection to dynamically access private fields of an object at runtime?",
 "Reflection enables powerful metaprogramming, dependency injection (Spring), and testing by bypassing standard visibility rules (`field.setAccessible(true)`). The massive tradeoff is performance (reflection disables JIT optimizations, making it vastly slower) and type safety (compile-time errors become catastrophic runtime `RuntimeExceptions`).",
 ["Enables powerful metaprogramming and bypasses standard visibility (`setAccessible(true)`)", "Tradeoff 1: Massive performance penalty (disables JIT optimizations)", "Tradeoff 2: Destroys compile-time type safety (errors become production RuntimeExceptions)"],
 ["Reflection creates a mirror universe inside the JVM"]),

("MODERN_JAVA_AND_LANGUAGE", "scenario", "easy", "scenario", ["final", "Initialization"],
 "You declare `final int x;` inside a class without assigning it a value on the declaration line. What is the one and only place you are legally allowed to initialize this variable?",
 "You must initialize it in the class Constructor (or an instance initializer block). A `final` instance variable must be definitively assigned exactly once before the object is fully constructed. If the class has multiple constructors, *every* constructor must guarantee the variable is assigned.",
 ["Must be initialized inside the class Constructor (or instance initializer block)", "Must be definitively assigned exactly once before object construction completes", "Every single constructor path must guarantee assignment"],
 ["You must email James Gosling for permission to change it"]),

("MODERN_JAVA_AND_LANGUAGE", "explain", "medium", "concept", ["Functional Interfaces", "Lambdas"],
 "What is a 'Functional Interface' in Java, and why is the `@FunctionalInterface` annotation useful?",
 "A Functional Interface contains exactly one abstract method (SAM - Single Abstract Method), like `Runnable`. They are the foundation of Lambda expressions; a lambda is simply an anonymous implementation of that single method. The `@FunctionalInterface` annotation instructs the compiler to throw an error if a second abstract method is accidentally added, protecting the contract.",
 ["An interface with exactly one abstract method (Single Abstract Method - SAM)", "They are the foundation for Lambda expressions in Java", "`@FunctionalInterface` forces a compiler error if someone accidentally adds a second abstract method"],
 ["It is an interface that works, as opposed to a dysfunctional interface"]),

("MODERN_JAVA_AND_LANGUAGE", "debug", "hard", "debugging", ["GC Thrashing", "Performance"],
 "You create a memory-intensive cache. When the JVM approaches the max heap (`-Xmx`), instead of throwing an `OutOfMemoryError`, the app freezes, consuming 100% CPU forever. What JVM death spiral did you enter?",
 "You entered 'GC Thrashing' (GC Overhead Limit Exceeded). When the heap is nearly full, the Garbage Collector runs continuously trying to free memory, but only reclaims a tiny fraction. Because it immediately runs out of memory again, the JVM spends 99% of its CPU time locked in Stop-The-World GC pauses, completely freezing application logic without officially crashing.",
 ["'GC Thrashing' or 'GC Overhead Limit Exceeded'", "The JVM spends nearly 100% of its CPU time running the Garbage Collector", "Because almost no memory is reclaimed, the application logic is permanently frozen by GC pauses"],
 ["The CPU got addicted to collecting garbage and forgot to run the code"])
]
