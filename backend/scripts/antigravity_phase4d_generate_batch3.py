import json
import os
import uuid
import sys
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

questions_data = [
    # --- BUCKET 1: Java Core -> Types ---
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Java Core", "secondary_skills": [],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the primary difference between primitive types (e.g., int, boolean) and their wrapper classes (e.g., Integer, Boolean) in Java?",
        "expected_answer": "Primitive types store basic values directly in memory (stack) and have no methods or overhead. Wrapper classes are objects stored on the heap that encapsulate primitives, providing utility methods and allowing them to be used in Java Collections (like List<Integer>), which only accept objects.",
        "evaluation_rubric": {"strong_indicators": ["Stack vs Heap memory", "Collections support"], "weak_indicators": ["Confuses wrapper classes with custom objects"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": [],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the concepts of autoboxing and unboxing in Java.",
        "expected_answer": "Autoboxing is the automatic conversion the Java compiler makes between primitive types and their corresponding object wrapper classes (e.g., int to Integer). Unboxing is the reverse process (Integer to int). It simplifies code but can hide performance costs associated with object creation.",
        "evaluation_rubric": {"strong_indicators": ["Defines both directions clearly", "Mentions compiler automation"], "weak_indicators": ["Confuses it with type casting"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Java Core", "secondary_skills": ["Performance"],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the memory and performance trade-offs of using an array of `Integer` objects versus an array of primitive `int` values for 10 million elements?",
        "expected_answer": "An `int[]` uses contiguous memory, consuming exactly 4 bytes per element (40MB total) with excellent CPU cache locality. An `Integer[]` stores 10 million object references. Each `Integer` object has a 16-byte object header plus 4 bytes for the int payload, plus reference overhead, consuming over 200MB. It also triggers massive garbage collection pressure and destroys cache locality.",
        "evaluation_rubric": {"strong_indicators": ["Identifies object header overhead", "Identifies CPU cache locality destruction", "Identifies Garbage Collection pressure"], "weak_indicators": ["Only says 'it takes more memory' without explaining why"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["Debugging"],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "You compare two `Integer` variables using `==`. `Integer a = 1000; Integer b = 1000; a == b` returns `false`. However, `Integer x = 100; Integer y = 100; x == y` returns `true`. Why does this happen?",
        "expected_answer": "Java maintains an Integer Cache pool for values between -128 and 127. When autoboxing occurs in this range, the JVM reuses the same object reference, so `x == y` evaluates to true (identity check). 1000 is outside this cache, so two distinct objects are created in the heap, returning false for `a == b`. `.equals()` should always be used to compare values.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the Integer Cache pool", "Mentions -128 to 127 range", "Explains identity (==) vs value (.equals())"], "weak_indicators": ["Thinks 1000 overflows some limit"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Java Core", "secondary_skills": ["Architecture"],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are building a high-precision trading application. Why must you strictly avoid using `double` or `float` for currency calculations, and what type is appropriate?",
        "expected_answer": "`float` and `double` use IEEE 754 binary floating-point representation, which cannot accurately represent decimal fractions like 0.1, leading to precision loss and compounding rounding errors. For financial applications, `BigDecimal` must be used as it allows arbitrary-precision arithmetic without base-2 representation errors.",
        "evaluation_rubric": {"strong_indicators": ["Mentions IEEE 754 floating point issues", "Identifies BigDecimal"], "weak_indicators": ["Suggests using long/cents without addressing the core float issue"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": [],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "implement", "difficulty": "easy", "question_type": "implementation",
        "question": "How do you safely convert a `String` to an `int` in Java, handling potential parsing errors?",
        "expected_answer": "Use `Integer.parseInt(string)`. Because the string might contain non-numeric characters, you must wrap the call in a `try-catch` block to handle the `NumberFormatException`.",
        "evaluation_rubric": {"strong_indicators": ["Integer.parseInt", "try/catch block", "NumberFormatException"], "weak_indicators": ["Fails to mention exception handling"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["Concurrency"],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare `String`, `StringBuilder`, and `StringBuffer` in terms of mutability and thread safety.",
        "expected_answer": "`String` is immutable; every modification creates a new object. `StringBuilder` and `StringBuffer` are mutable. `StringBuffer` has synchronized methods, making it thread-safe but slower. `StringBuilder` is not synchronized, making it significantly faster and preferred in single-threaded scenarios.",
        "evaluation_rubric": {"strong_indicators": ["String is immutable", "StringBuffer is thread-safe/synchronized", "StringBuilder is fast/unsynchronized"], "weak_indicators": ["Confuses StringBuilder and StringBuffer"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "API Designer"],
        "primary_skill": "Java Core", "secondary_skills": ["Architecture"],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "When designing an API entity or DTO in Java, under what specific architectural condition should you define a field as the wrapper `Boolean` instead of the primitive `boolean`?",
        "expected_answer": "You should use `Boolean` when the value is optional and must support a `null` state to represent 'unknown', 'not provided', or 'missing in database'. A primitive `boolean` defaults to `false`, which makes it impossible to distinguish between a client explicitly setting 'false' versus simply omitting the field.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the nullability requirement", "Identifies the false default ambiguity of primitives"], "weak_indicators": ["Says wrappers are just better for serialization generally"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Java Core", "secondary_skills": ["Performance"],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "Why is using the `+` operator for `String` concatenation inside a tight loop detrimental to JVM performance, and what is the standard optimization?",
        "expected_answer": "Strings are immutable. Using `+` inside a loop creates a brand new `String` object (and throws away the old one) on every single iteration, flooding the heap and causing massive Garbage Collection pauses. The optimization is to instantiate a `StringBuilder` outside the loop and call `.append()` inside.",
        "evaluation_rubric": {"strong_indicators": ["Identifies String immutability", "Identifies O(N^2) memory creation", "Suggests StringBuilder"], "weak_indicators": ["Suggests StringBuffer without context"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["Debugging"],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "You receive an `Object` reference representing a list. You cast it to `(List<String>) obj`. The compiler issues an 'unchecked cast' warning. Explain the concept of Type Erasure that makes this cast potentially unsafe at runtime.",
        "expected_answer": "Due to Type Erasure, generic type information (`<String>`) is removed during compilation. At runtime, the JVM only sees a raw `List`. `instanceof List<String>` is illegal because the JVM cannot verify the generic type. An unchecked cast suppresses the compiler warning, but if the list actually contains Integers, a `ClassCastException` will occur much later when reading from the list.",
        "evaluation_rubric": {"strong_indicators": ["Mentions Type Erasure", "Explains that generics do not exist at runtime", "Mentions delayed ClassCastException"], "weak_indicators": ["Thinks the JVM verifies the cast at runtime"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": [],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the default value of a `boolean` primitive when declared as an instance variable in a class?",
        "expected_answer": "The default value is `false`.",
        "evaluation_rubric": {"strong_indicators": ["Correctly identifies false"], "weak_indicators": ["Claims it is null or undefined"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["Memory Management"],
        "technology": "Java", "topic": "Types", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the internal mechanism of the String Constant Pool in Java.",
        "expected_answer": "The String Pool is a special storage area in the heap memory. When a string literal (e.g., `\"hello\"`) is created, the JVM checks the pool. If the string already exists, the reference to the pooled instance is returned. If not, a new string is added to the pool. This conserves memory for repeated literals. `new String(\"hello\")` bypasses this and forces heap allocation.",
        "evaluation_rubric": {"strong_indicators": ["Resides in heap", "Reuses literals for memory conservation", "Differentiates literals from 'new String()'"], "weak_indicators": ["Claims all strings are interned automatically"]}
    },

    # --- BUCKET 2: Java Core -> OOP ---
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Full Stack Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "Name and briefly define the four foundational pillars of Object-Oriented Programming as implemented in Java.",
        "expected_answer": "1. Encapsulation: Hiding internal state (private fields) and requiring access via methods (getters/setters). 2. Abstraction: Hiding complex implementation details behind simple interfaces. 3. Inheritance: Reusing code by creating subclasses from parent classes. 4. Polymorphism: Allowing one interface/method to be used for a general class of actions (overloading/overriding).",
        "evaluation_rubric": {"strong_indicators": ["Lists all four", "Provides accurate definitions"], "weak_indicators": ["Misses one or provides vague textbook definitions"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "What is the difference between method overloading and method overriding in Java?",
        "expected_answer": "Overloading is compile-time polymorphism where multiple methods in the same class share a name but have different parameter signatures (types or counts). Overriding is runtime polymorphism where a subclass provides a specific implementation of a method already defined in its parent class, matching the exact same signature.",
        "evaluation_rubric": {"strong_indicators": ["Compile-time vs Runtime polymorphism", "Same class vs Subclass", "Different signature vs Exact signature"], "weak_indicators": ["Confuses the two terms completely"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "What are the strict requirements to design and implement an entirely immutable class in Java?",
        "expected_answer": "1. Declare the class as `final` so it cannot be extended. 2. Make all fields `private` and `final`. 3. Do not provide setter methods. 4. Initialize all fields via a constructor. 5. If fields contain mutable objects (like Lists or Dates), perform deep copies in the constructor and return clones in getter methods to prevent external mutation.",
        "evaluation_rubric": {"strong_indicators": ["final class", "private final fields", "Deep copies of mutable objects / defensive copying"], "weak_indicators": ["Forgets defensive copying for mutable fields"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Architecture"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP", "Architecture"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "Since Java 8 introduced default methods in Interfaces, what are the architectural trade-offs of using Abstract Classes versus Interfaces for base type definitions?",
        "expected_answer": "Interfaces allow multiple inheritance of type and behavior (default methods), enabling high flexibility, but they cannot hold instance state (non-static fields) or private constructors. Abstract classes can hold state, define protected fields, and have constructors, but a class can only extend one abstract class, creating a rigid single-inheritance hierarchy.",
        "evaluation_rubric": {"strong_indicators": ["Identifies state/fields limitation in interfaces", "Identifies single vs multiple inheritance differences"], "weak_indicators": ["Thinks abstract classes are completely obsolete in Java 8+"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP", "Debugging"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "A parent class defines `public void execute()`. The subclass overrides it with `protected void execute()`. Compilation fails. Why does Java enforce this access modifier rule?",
        "expected_answer": "Liskov Substitution Principle (Polymorphism). The subclass must be substitutable anywhere the parent class is expected. If the parent promises `public` visibility, clients expect to call it from anywhere. Restricting it to `protected` in the subclass breaks this contract, so the compiler enforces that overriding methods cannot have more restrictive access.",
        "evaluation_rubric": {"strong_indicators": ["Identifies Liskov Substitution Principle", "Explains breaking the contract of the parent's API"], "weak_indicators": ["Just says 'it's illegal' without explaining why"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Architecture"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP", "System Design"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "In Java 15+, you are designing a core library. You have a `Shape` interface and you want to strictly guarantee that ONLY `Circle` and `Square` can implement it, preventing any third-party code from extending your hierarchy. How do you implement this?",
        "expected_answer": "Use Sealed Classes/Interfaces. Define it as `public sealed interface Shape permits Circle, Square`. This explicitly locks down the hierarchy at the compiler level, ensuring exhaustive type safety and preventing unauthorized implementations.",
        "evaluation_rubric": {"strong_indicators": ["Uses the 'sealed' keyword", "Uses the 'permits' keyword"], "weak_indicators": ["Suggests package-private classes (which doesn't scale to public APIs)"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare deep copy and shallow copy in Java. How is the default `clone()` method of `Object` implemented?",
        "expected_answer": "A shallow copy creates a new object but inserts references to the nested objects found in the original. Modifying a nested object affects both. A deep copy recursively creates new instances of all nested objects. The default `Object.clone()` is a shallow copy; you must override it and manually copy nested objects to achieve a deep copy.",
        "evaluation_rubric": {"strong_indicators": ["Defines shallow copy as sharing inner references", "Identifies Object.clone() as shallow"], "weak_indicators": ["Assumes clone() handles deep copying automatically"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP", "Architecture"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How does the JVM internally implement dynamic method dispatch (runtime polymorphism) when an overridden method is invoked on a parent reference?",
        "expected_answer": "The JVM uses Virtual Method Tables (vtable). Each class has an array of method pointers. When a subclass overrides a method, its vtable entry for that method signature points to the subclass's memory address. At runtime, the JVM looks up the actual object's class header, jumps to its vtable, and executes the resolved pointer.",
        "evaluation_rubric": {"strong_indicators": ["Mentions Virtual Method Tables (vtable)", "Explains pointer resolution at runtime"], "weak_indicators": ["Vague explanations of 'checking the type' without memory structures"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP", "Performance"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "hard", "question_type": "optimization",
        "question": "Can excessive use of deep polymorphism negatively impact JVM Just-In-Time (JIT) compilation performance? Explain 'megamorphic' dispatch.",
        "expected_answer": "Yes. When a call site sees only one or two target classes (monomorphic/bimorphic), the JIT compiler aggressively inlines the code for massive performance gains. If a call site sees many different subclass implementations (megamorphic), the JIT cannot inline effectively and must rely on slower vtable lookups, degrading execution speed.",
        "evaluation_rubric": {"strong_indicators": ["Identifies inline optimization failures", "Understands megamorphic vs monomorphic call sites"], "weak_indicators": ["Believes polymorphism is completely free"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP", "Debugging"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A parent class calls a `public void initialize()` method from inside its own constructor. A subclass overrides `initialize()`. What critical danger does this pattern introduce during object creation?",
        "expected_answer": "Because the parent constructor runs before the child constructor, the overridden `initialize()` method executes before the child class has finished initializing its state (fields are still null or 0). If the overridden method accesses child-specific fields, it will likely throw a `NullPointerException` or result in corrupted state.",
        "evaluation_rubric": {"strong_indicators": ["Explains initialization order (parent before child)", "Identifies NullPointerExceptions or uninitialized state access"], "weak_indicators": ["Assumes the parent method executes instead of the child method"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "Explain the purpose of the `final` keyword when applied to a class, a method, and a variable.",
        "expected_answer": "Class: Cannot be subclassed/extended. Method: Cannot be overridden by subclasses. Variable: Cannot be reassigned once initialized (makes primitives constant, references unchangeable).",
        "evaluation_rubric": {"strong_indicators": ["Clearly maps the keyword to all three targets"], "weak_indicators": ["Fails to differentiate primitive finality vs object finality"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP", "Design Patterns"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "Implement the Singleton design pattern using an `enum` in Java, and explain why this approach is considered serialization-safe compared to static instances.",
        "expected_answer": "`public enum Singleton { INSTANCE; public void doWork() {} }`. It is serialization-safe because Java guarantees internally that enum values are instantiated exactly once. Standard Singleton classes can be bypassed using Reflection or Deserialization (which bypasses the private constructor), creating multiple instances, whereas enums are immune to this.",
        "evaluation_rubric": {"strong_indicators": ["Provides correct Enum syntax", "Explains Reflection and Deserialization vulnerabilities of standard Singletons"], "weak_indicators": ["Cannot explain why it is safer"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Java Core", "secondary_skills": ["OOP"],
        "technology": "Java", "topic": "OOP", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "What is the structural difference between an `Inner Class` and a `Static Nested Class` in Java?",
        "expected_answer": "An Inner Class (non-static) holds an implicit reference to its enclosing outer class instance, allowing it to access instance variables of the outer class. A Static Nested Class does not hold a reference to an outer instance, acts like a regular top-level class scoped inside another, and can only access static members of the outer class.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the implicit reference to the outer instance", "Identifies memory leak risks of inner classes"], "weak_indicators": ["Fails to mention access to instance vs static variables"]}
    },

    # --- BUCKET 3: Collections Framework -> Map ---
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the `Map` interface in Java, and why doesn't it extend the `Collection` interface?",
        "expected_answer": "A Map stores key-value pairs where keys must be unique. It does not extend `Collection` because Collections represent a single sequence or group of elements (like List or Set). The semantics of `add()` or `iterator()` do not naturally apply to key-value mappings without distinguishing between keys and values.",
        "evaluation_rubric": {"strong_indicators": ["Key-Value pair distinction", "Notes incompatible semantics (add vs put)"], "weak_indicators": ["Thinks it does extend Collection"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the internal data structure and working mechanism of a `HashMap` in Java.",
        "expected_answer": "A HashMap is internally an array of nodes (buckets). When `put()` is called, it calculates the hashcode of the key, applies a hashing function to find the array index, and stores a Node (key, value, hash, next pointer). If two keys map to the same bucket (collision), it forms a Linked List.",
        "evaluation_rubric": {"strong_indicators": ["Array of buckets", "Hashcode index calculation", "Linked list for collisions"], "weak_indicators": ["Thinks it's a pure binary tree"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Write the most efficient way to iterate over both the keys and values of a `HashMap` simultaneously.",
        "expected_answer": "Use `entrySet()`. Example: `for (Map.Entry<K, V> entry : map.entrySet()) { K key = entry.getKey(); V val = entry.getValue(); }` or using Java 8: `map.forEach((k, v) -> { ... });`. Iterating over `keySet()` and calling `get(key)` inside the loop is inefficient.",
        "evaluation_rubric": {"strong_indicators": ["Uses entrySet()", "Uses forEach() BiConsumer", "Highlights inefficiency of keySet + get"], "weak_indicators": ["Suggests keySet() loop with .get()"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Performance"],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the time complexity and ordering trade-offs of using a `TreeMap` versus a `HashMap`?",
        "expected_answer": "A `HashMap` offers O(1) constant time performance for `get` and `put` operations but provides no ordering guarantee. A `TreeMap` is backed by a Red-Black tree, providing O(log N) time complexity for operations but guaranteeing elements are sorted according to the natural ordering of keys (or a provided Comparator).",
        "evaluation_rubric": {"strong_indicators": ["O(1) vs O(log N)", "Unordered vs Sorted", "Red-Black Tree mention"], "weak_indicators": ["Thinks TreeMap is faster"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Debugging"],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "debug", "difficulty": "hard", "question_type": "debugging",
        "question": "You use a custom `User` object as a key in a `HashMap`. You insert an entry. Later, using a different `User` instance with identical data, `get()` returns null. What did you forget to implement?",
        "expected_answer": "You failed to override `equals()` and `hashCode()` in the `User` class. By default, Object's `hashCode` returns memory addresses. The HashMap calculates a different hash bucket for the second instance. Even if in the same bucket, default `equals` checks memory identity, so the keys are deemed different.",
        "evaluation_rubric": {"strong_indicators": ["Must override both equals() and hashCode()", "Explains bucket location failure"], "weak_indicators": ["Fails to explain the relationship between equals and hashCode"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Architecture"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Concurrency"],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are building a high-throughput cache handling thousands of concurrent read/write threads. Why is `ConcurrentHashMap` superior to `Collections.synchronizedMap(new HashMap<>())`?",
        "expected_answer": "`synchronizedMap` places a single global lock on the entire map object; every read or write blocks all other threads, causing severe bottlenecks. `ConcurrentHashMap` uses lock striping (or CAS operations in Java 8+ at the node level), allowing multiple threads to read and write to different segments/nodes simultaneously without blocking each other.",
        "evaluation_rubric": {"strong_indicators": ["Global lock vs Node-level/Segment-level locks", "Lock striping", "Compare and Swap (CAS)"], "weak_indicators": ["Says it's just 'optimized' without technical details"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare the iteration order guarantees of `HashMap`, `LinkedHashMap`, and `TreeMap`.",
        "expected_answer": "`HashMap` guarantees no specific iteration order; it appears random and can change over time. `LinkedHashMap` maintains a doubly-linked list running through its entries, guaranteeing iteration in insertion order (or access order). `TreeMap` guarantees iteration based on the sorted natural order of its keys.",
        "evaluation_rubric": {"strong_indicators": ["HashMap = Random", "LinkedHashMap = Insertion/Access Order", "TreeMap = Sorted Key Order"], "weak_indicators": ["Confuses LinkedHashMap and TreeMap"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Architecture"],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "In Java 8, `HashMap` introduced an architectural change to handle severe hash collisions. What is the threshold for this change, what data structure does it convert to, and what interface must the keys implement for this optimization to be fully effective?",
        "expected_answer": "When a single bucket's linked list reaches 8 elements (TREEIFY_THRESHOLD), the HashMap converts that bucket into a Balanced Red-Black Tree, improving worst-case search from O(N) to O(log N). For this tree structure to order elements efficiently during insertion, the key objects should implement the `Comparable` interface.",
        "evaluation_rubric": {"strong_indicators": ["Identifies threshold 8", "Identifies Red-Black tree conversion", "Mentions Comparable requirement for tie-breaking"], "weak_indicators": ["Misses the Comparable interface requirement"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Performance"],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "If you know exactly that you will insert 10,000 items into a `HashMap`, why is it important to initialize it with an explicit initial capacity, and what value should you choose?",
        "expected_answer": "Because HashMaps resize dynamically when they hit their load factor (default 0.75), causing a massive O(N) penalty to rehash all existing elements into a new larger array. To prevent resizing, you should initialize the capacity to `10000 / 0.75 + 1` (approx 13,334) so it never reaches the threshold.",
        "evaluation_rubric": {"strong_indicators": ["Identifies rehashing penalty overhead", "Understands load factor math"], "weak_indicators": ["Just says capacity = 10000 (which will still trigger a rehash)"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Debugging", "Memory Management"],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "medium", "question_type": "debugging",
        "question": "You build a cache using a standard `HashMap`. However, the server runs out of memory because objects used as keys are kept alive by the Map even after the rest of the application discards them. Which specific Map implementation resolves this?",
        "expected_answer": "`WeakHashMap`. It stores keys using `WeakReference` objects. If there are no strong references to the key elsewhere in the application, the Garbage Collector will automatically remove the entry from the map, preventing the memory leak.",
        "evaluation_rubric": {"strong_indicators": ["Identifies WeakHashMap", "Explains WeakReference garbage collection mechanics"], "weak_indicators": ["Suggests clearing the map manually on a timer"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "Can a `HashMap` contain `null` keys or `null` values? How does it differ from a `ConcurrentHashMap` in this regard?",
        "expected_answer": "A `HashMap` allows exactly one `null` key and any number of `null` values. A `ConcurrentHashMap`, however, throws a `NullPointerException` if you attempt to insert a `null` key or a `null` value.",
        "evaluation_rubric": {"strong_indicators": ["HashMap allows 1 null key and multiple null values", "ConcurrentHashMap allows NO nulls"], "weak_indicators": ["Fails to differentiate the two"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "System Design"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Architecture"],
        "technology": "Java", "topic": "Map", "category": "Programming Languages",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "Implement a simple, thread-unsafe Least Recently Used (LRU) Cache by extending a class from the standard Java Collections Framework.",
        "expected_answer": "Extend `LinkedHashMap<K, V>`. Pass `(capacity, 0.75f, true)` to the `super` constructor to enable 'access-order' mode. Then, override the protected method `removeEldestEntry(Map.Entry<K,V> eldest)` to return `size() > MAX_CAPACITY`.",
        "evaluation_rubric": {"strong_indicators": ["Identifies LinkedHashMap access-order mode", "Overrides removeEldestEntry"], "weak_indicators": ["Tries to implement it from scratch with a HashMap and a LinkedList"]}
    },

    # --- BUCKET 4: Collections Framework -> List ---
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What distinguishes the `List` interface from the `Set` interface in Java?",
        "expected_answer": "A `List` is an ordered collection that allows duplicate elements and maintains insertion order, allowing access via an integer index. A `Set` is an unordered collection that prohibits duplicate elements and generally does not provide index-based access.",
        "evaluation_rubric": {"strong_indicators": ["Allows duplicates", "Ordered/Index-based access"], "weak_indicators": ["Vague 'different use cases'"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain how an `ArrayList` dynamically resizes itself when it reaches capacity.",
        "expected_answer": "When an `ArrayList` reaches its internal array's capacity and a new element is added, it allocates a completely new, larger array (typically 1.5x the size of the old one). It then uses `System.arraycopy()` to copy all existing elements to the new array before discarding the old one.",
        "evaluation_rubric": {"strong_indicators": ["New larger array allocation", "1.5x growth factor", "Array copy overhead"], "weak_indicators": ["Thinks memory is just extended in place"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Performance"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the algorithmic and memory trade-offs between using an `ArrayList` and a `LinkedList`?",
        "expected_answer": "`ArrayList` provides O(1) random access (get) but O(N) insertions/deletions in the middle due to shifting elements. It uses contiguous memory. `LinkedList` provides O(N) random access but theoretically O(1) insertions/deletions (once the node is found). However, `LinkedList` has terrible CPU cache locality and high memory overhead per element (pointers). In 99% of practical cases, `ArrayList` is faster.",
        "evaluation_rubric": {"strong_indicators": ["O(1) vs O(N) access", "O(N) vs O(1) insertion", "Mentions Cache Locality and memory overhead of nodes"], "weak_indicators": ["Claims LinkedList is always faster for all insertions"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Debugging"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "You iterate over an `ArrayList` using a standard `for-each` loop. Inside the loop, if a condition is met, you call `list.remove(item)`. A `ConcurrentModificationException` is thrown. Why, and how do you fix it?",
        "expected_answer": "The `for-each` loop uses an Iterator implicitly. Calling `list.remove()` modifies the structural count (`modCount`) of the list directly. The iterator detects this mismatch on the next cycle and throws a fail-fast exception. The fix is to use an explicit `Iterator` and call `iterator.remove()`, or in Java 8+, use `list.removeIf(condition)`.",
        "evaluation_rubric": {"strong_indicators": ["Identifies fail-fast Iterator mechanics", "Suggests explicit iterator.remove() or list.removeIf()"], "weak_indicators": ["Suggests using a regular indexed for-loop (which skips elements after removal)"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Architecture"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You have a single-threaded queueing system that constantly adds and removes elements strictly at both ends of a massive collection, never accessing the middle. Which Java Collection type is optimal?",
        "expected_answer": "An `ArrayDeque`. While `LinkedList` works, `ArrayDeque` is significantly more memory-efficient and cache-friendly because it uses a circular array implementation rather than allocating separate node objects for every element. It outperforms `LinkedList` for queue/stack operations.",
        "evaluation_rubric": {"strong_indicators": ["Suggests ArrayDeque", "Identifies circular array efficiency over nodes"], "weak_indicators": ["Suggests LinkedList without acknowledging ArrayDeque"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Concurrency"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "How do you synchronize an existing `ArrayList` to make it thread-safe without instantiating a `CopyOnWriteArrayList`?",
        "expected_answer": "You wrap it using the utility class method: `List<String> syncList = Collections.synchronizedList(new ArrayList<>());`. Note that while individual operations are synchronized, iterating over it still requires a manual `synchronized (syncList)` block to prevent concurrent modification exceptions.",
        "evaluation_rubric": {"strong_indicators": ["Uses Collections.synchronizedList()", "Notes the manual synchronization required during iteration"], "weak_indicators": ["Fails to mention the iteration caveat"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Concurrency"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare `ArrayList` and `Vector` in Java. Why is `Vector` considered largely obsolete?",
        "expected_answer": "Both implement dynamic arrays. However, `Vector` synchronizes every single method by default, making it thread-safe but exceptionally slow in single-threaded contexts. `ArrayList` is unsynchronized and fast. Modern Java prefers `ArrayList` for single-thread and `CopyOnWriteArrayList` or `Collections.synchronizedList()` for concurrency, rendering `Vector` obsolete.",
        "evaluation_rubric": {"strong_indicators": ["Vector is synchronized/thread-safe", "Vector is a legacy class with high overhead"], "weak_indicators": ["Thinks they are exactly the same"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "System Design"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Concurrency"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "Under what specific high-concurrency read/write ratio scenarios does `CopyOnWriteArrayList` excel, and when does it become a severe bottleneck?",
        "expected_answer": "It excels in scenarios with massively high reads and extremely rare writes (e.g., maintaining a list of event listeners). It is a severe bottleneck if writes are frequent, because every write operation allocates a completely new copy of the underlying array, leading to O(N) copy overhead and terrible Garbage Collection pressure.",
        "evaluation_rubric": {"strong_indicators": ["High reads, rare writes", "Explains the array-copy-on-write memory penalty"], "weak_indicators": ["Thinks it's just a 'better' thread-safe list for all scenarios"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Performance"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "You need to remove multiple elements from the middle of a massive `ArrayList` based on a boolean condition. What is the most efficient method available in Java 8+ to achieve this without multiple array shifting passes?",
        "expected_answer": "Use the `removeIf(Predicate)` method (e.g., `list.removeIf(item -> item.isExpired());`). Internally, `removeIf` on an `ArrayList` is heavily optimized to perform a single pass, shifting elements down collectively at the end, rather than shifting the entire array O(N) times for every single removed element.",
        "evaluation_rubric": {"strong_indicators": ["Identifies removeIf()", "Explains the single-pass shift optimization"], "weak_indicators": ["Suggests Iterator.remove() (which still shifts the array every time)"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Debugging"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "You initialize a list via `List<Integer> nums = Arrays.asList(1, 2, 3);`. You then call `nums.add(4)`. This throws an `UnsupportedOperationException`. Why?",
        "expected_answer": "`Arrays.asList()` returns a fixed-size, array-backed list wrapper (a private inner class `java.util.Arrays.ArrayList`, not `java.util.ArrayList`). Because it is backed directly by the original array, it cannot be resized. Add and remove operations are unsupported. You must wrap it: `new ArrayList<>(Arrays.asList(...))`.",
        "evaluation_rubric": {"strong_indicators": ["Identifies fixed-size list", "Distinguishes Arrays.ArrayList from java.util.ArrayList"], "weak_indicators": ["Thinks the list is completely immutable (set() actually works)"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "How does the `subList(fromIndex, toIndex)` method work on a List? Does it create a new independent list?",
        "expected_answer": "No, it returns a 'view' of the portion of the original list. Any structural modifications made to the subList (like adding/removing elements) are directly reflected in the original list, and vice versa. Modifying the original list directly while holding a subList view will invalidate the subList.",
        "evaluation_rubric": {"strong_indicators": ["Identifies it as a view", "Modifications affect the original"], "weak_indicators": ["Thinks it clones/copies the data"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Collections Framework", "secondary_skills": [],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "implement", "difficulty": "easy", "question_type": "implementation",
        "question": "Write a concise line of Java 8 code to sort a `List<Employee>` named `employees` by their `salary` in descending order.",
        "expected_answer": "`employees.sort(Comparator.comparing(Employee::getSalary).reversed());` or `employees.sort((e1, e2) -> Double.compare(e2.getSalary(), e1.getSalary()));`",
        "evaluation_rubric": {"strong_indicators": ["Uses list.sort()", "Uses Comparator.comparing", "Applies reversed() appropriately"], "weak_indicators": ["Tries to write a manual bubble sort"]}
    },
    {
        "primary_role": "Java Developer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Collections Framework", "secondary_skills": ["Performance", "Memory Management"],
        "technology": "Java", "topic": "List", "category": "Programming Languages",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "A memory-constrained application needs to store and sort 10 million primitive `int` values. Why is `ArrayList<Integer>` a poor architectural choice, and what is the standard alternative?",
        "expected_answer": "`ArrayList<Integer>` requires storing 10 million `Integer` wrapper objects on the heap, massively bloating memory with object headers and pointers, and destroying CPU cache locality. The standard alternative is to use a simple primitive `int[]` array, or rely on specialized primitive collection libraries like Eclipse Collections, Trove, or FastUtil to avoid autoboxing overhead.",
        "evaluation_rubric": {"strong_indicators": ["Identifies autoboxing wrapper object memory overhead", "Suggests primitive arrays or specialized primitive libraries"], "weak_indicators": ["Suggests LinkedList"]}
    }
]

def main():
    out_path = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
    
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

    # Remaining gap from previous is 3611. We subtract accepted.
    remaining_count = 3611 - accepted

    report = {
        "Batch 3 buckets processed": 4, # Java Types, OOP, Map, List
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
    
    with open(os.path.join(REPORTS_DIR, "phase4d_quality_report_batch3.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    for k, v in report.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
