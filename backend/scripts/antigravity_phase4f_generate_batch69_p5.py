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
        "B69_5_1",
        "implement",
        "hard",
        "implement",
        ["Testing", "Async Concurrency"],
        "pytest-asyncio / Synchronization",
        "Deterministic Race Condition Testing without time.sleep()",
        "When testing asynchronous race conditions in Python (e.g., verifying that a balance deduction function prevents double-spending when two concurrent requests arrive simultaneously), developers often use arbitrary sleeps: `await asyncio.sleep(0.1)`. Explain why `sleep()` makes tests flaky and non-deterministic, and how do you use `asyncio.Event` synchronization barriers to interleave coroutines deterministically at exact execution points?",
        "Why Sleeps Cause Flaky Tests: Arbitrary sleeps (`await asyncio.sleep(0.1)`) introduce timing-dependent race conditions into the test suite. On a busy CI runner with high CPU load or under virtualization, a 0.1-second sleep may resume before or after the target task, causing random test failures. Increasing the sleep to 1 second slows down the test suite without providing mathematical synchronization guarantees. Deterministic Synchronization with `asyncio.Event` Barriers: 1) Double-Event Handshake Pattern: Create two coordination events: `step1_reached = asyncio.Event()` and `resume_step1 = asyncio.Event()`. 2) Hooking Execution Points: Mock or intercept the shared resource (e.g., the database check in `withdraw()`): `async def intercepted_check(): step1_reached.set(); await resume_step1.wait(); return original_check()`. 3) Orchestrating the Interleaving: In the test function: A) Launch Request 1 as a background task (`t1 = asyncio.create_task(withdraw(100))`). B) Wait deterministically for Request 1 to execute up to the balance verification point: `await step1_reached.wait()`. At this exact microsecond, Request 1 has verified the balance but has not deducted funds. C) Launch Request 2 (`t2 = asyncio.create_task(withdraw(100))`). Request 2 executes its check concurrently. D) Unblock Request 1: `resume_step1.set()`. E) Await both tasks. The race condition is tested with 100% mathematical determinism, zero flakiness, and zero wasted sleep delay.",
        [
            "Explains that sleep() makes tests timing-dependent and flaky under varying CI/runner CPU load",
            "Implements two-phase coordination using asyncio.Event barriers to pause execution at exact points",
            "Forces deterministic interleaving between concurrent tasks without arbitrary time delays"
        ],
        [
            "Suggests setting time.sleep() to 30 seconds to guarantee the race condition is caught"
        ]
    ),
    (
        "B69_5_2",
        "diagnose",
        "medium",
        "debugging",
        ["Testing", "Time Manipulation"],
        "pytest / freezegun / time-machine",
        "Flaky Tests with freezegun and time.monotonic() in Timeout Loops",
        "In a test suite, a developer uses the popular library `freezegun` (`@freeze_time('2026-01-01')`) to mock time for testing an asynchronous polling function with a 5-second timeout: `deadline = time.monotonic() + 5; while time.monotonic() < deadline: ...`. When running pytest, the test hangs in an infinite loop forever. Why does `freezegun` fail to advance `time.monotonic()`, and how does `time-machine` provide reliable monotonic time mocking?",
        "Root Cause: Wall-Clock Time vs Monotonic Time in freezegun: 1) What freezegun Does: `freezegun` works by monkey-patching Python's wall-clock time functions (`datetime.datetime.now()`, `datetime.date.today()`, and `time.time()`). 2) The Monotonic Disconnect: Standard timeout loops and asynchronous schedulers rely on `time.monotonic()` or `time.perf_counter()`, which are steady, monotonic clocks guaranteed not to be affected by system clock adjustments. By default, `freezegun` does NOT freeze or advance `time.monotonic()`; or if frozen, `time.monotonic()` remains at a static fixed number. 3) The Infinite Loop: If `time.monotonic()` is frozen at 100.0, the loop condition `while time.monotonic() < deadline` calculates `deadline = 105.0`. Because time is frozen, `time.monotonic()` continuously returns 100.0 on every iteration. The loop condition is always true, hanging pytest forever. Why `time-machine` is Superior: `time-machine` is a C-extension that hooks into CPython's internal C-level clock functions. It mocks both wall-clock time (`time.time()`) AND monotonic time (`time.monotonic()`) simultaneously, and allows programmatic clock shifting (`time_machine.shift(delta)`), ensuring timeout loops advance cleanly and deterministically.",
        [
            "Explains that freezegun mocks wall-clock datetime.now() but fails to advance time.monotonic() used in timeout loops",
            "Identifies static monotonic clock values causing while loops to evaluate as indefinitely true, hanging tests",
            "Prescribes using time-machine which mocks both wall-clock and monotonic clocks at the C-extension level"
        ],
        [
            "Claims time.monotonic() is a hardware sensor that can never be mocked in software"
        ]
    ),
    (
        "B69_5_3",
        "implement",
        "hard",
        "implement",
        ["Testing", "Property-Based Testing"],
        "Hypothesis / RuleBasedStateMachine",
        "Stateful Property-Based Testing with Hypothesis RuleBasedStateMachine",
        "Standard unit tests for a bank account or shopping cart only test linear, predictable scenarios (deposit -> withdraw). How do you implement stateful property-based testing using Hypothesis's `RuleBasedStateMachine` to generate thousands of random sequences of concurrent deposits, withdrawals, and transfers to discover edge-case invariant violations and race conditions?",
        "Implementation of RuleBasedStateMachine: 1) Concept: Standard Hypothesis tests generate random inputs for a single function. A `RuleBasedStateMachine` generates random, multi-step stateful workflows: it models an abstract state machine where Hypothesis randomly picks operations (rules) in arbitrary sequences and lengths (e.g., withdraw -> transfer -> deposit -> transfer). 2) Modeling the State Machine: Subclass `hypothesis.stateful.RuleBasedStateMachine`: Maintain a reference tracking model (e.g., `self.expected_balance = 0`) and the real system under test (`self.account = BankAccount()`). 3) Defining Rules with Strategies: Use `@rule()`: `@rule(amount=st.integers(min_value=1, max_value=1000))` `def deposit(self, amount): self.account.deposit(amount); self.expected_balance += amount`. `@rule(amount=st.integers(min_value=1, max_value=1000))` `def withdraw(self, amount): if self.expected_balance >= amount: self.account.withdraw(amount); self.expected_balance -= amount`. 4) Invariant Assertions: Use `@invariant()`: `@invariant() def check_invariants(self): assert self.account.balance == self.expected_balance; assert self.account.balance >= 0`. 5) Shrinking and Edge Discovery: Hypothesis executes thousands of random permutations. When an invariant fails, it 'shrinks' the complex failure down to the minimal reproducible sequence of operations (e.g., 2 specific steps), exposing obscure state corruption bugs that human testers would never conceive.",
        [
            "Subclasses Hypothesis RuleBasedStateMachine to model stateful operations and expected reference models",
            "Defines @rule methods with typed strategies to execute random sequences of business actions",
            "Defines @invariant assertions that run after every step to verify business guarantees and leverages shrinking"
        ],
        [
            "Claims property-based testing is only used for verifying CSS button colors"
        ]
    ),
    (
        "B69_5_4",
        "scenario",
        "medium",
        "scenario",
        ["Testing", "Concurrency"],
        "pytest-xdist / Test Isolation",
        "Test Isolation and Port/Database Collisions in pytest-xdist",
        "To speed up a slow 20-minute test suite, a team enables `pytest -n auto` using `pytest-xdist` across 8 parallel CPU cores. Immediately, 40% of the tests fail with database unique constraint errors (`duplicate key value violates unique constraint`) and network binding errors (`OSError: [Errno 98] Address already in use: 8080`). How do you architect test fixture isolation in `pytest-xdist` using the `worker_id` fixture?",
        "Why Tests Collide in pytest-xdist: `pytest-xdist` executes tests by spawning 8 completely independent worker processes. If tests share a single PostgreSQL database or bind to a hardcoded local port (e.g., `localhost:8080`), multiple workers attempt to insert records with the same IDs simultaneously, and multiple test servers attempt to bind the exact same TCP port, causing race conditions and port conflicts. Architectural Fix with `worker_id`: 1) Isolated Worker Databases: In `conftest.py`, inspect the built-in `worker_id` fixture (which returns `'gw0'`, `'gw1'`, ..., or `'master'`): `def db_url(worker_id): return f'postgresql://localhost/test_db_{worker_id}'`. Before the test run, run a session-scoped setup hook to create 8 separate databases (`test_db_gw0` through `test_db_gw7`). Each worker process operates exclusively inside its own isolated database with zero collision. 2) Dynamic Port Allocation: Instead of hardcoding port 8080, bind test HTTP servers to port 0: `sock.bind(('127.0.0.1', 0))`. The OS kernel dynamically assigns an unused ephemeral port. Extract the allocated port via `sock.getsockname()[1]` and pass it to the test client.",
        [
            "Identifies that pytest-xdist runs multiple worker processes that collide on shared databases and hardcoded ports",
            "Uses the worker_id fixture to provision isolated per-worker databases (e.g. test_db_gw0, test_db_gw1)",
            "Allocates dynamic ephemeral ports (port 0) for test servers to eliminate address already in use errors"
        ],
        [
            "Suggests running tests sequentially one at a time on an old laptop"
        ]
    ),
    (
        "B69_5_5",
        "concept",
        "easy",
        "concept",
        ["Testing", "Code Quality"],
        "Mutation Testing / Mutmut",
        "Mutation Testing with Mutmut: Evaluating Test Suite Rigor beyond Code Coverage",
        "A development team achieves 100% line coverage in pytest. A senior engineer warns that line coverage is a vanity metric and runs a mutation test using `mutmut`. Why can a test suite achieve 100% code coverage while failing to catch critical bugs, and how does Mutation Testing expose assertion gaps?",
        "1) The Fallacy of Line Coverage: Line coverage only measures whether a line of code was *executed* during a test run; it does NOT measure whether the test actually verified the correctness of that execution! A developer can write a test that invokes a function with zero assertions (`test_function()`), executing 100% of the lines while asserting nothing. Or, assertions may be superficial, checking only that the return value is not `None`. 2) How Mutation Testing Works (`mutmut`): Mutation testing systematically tests the *tests themselves*: A) Code Mutation: Mutmut parses the project's Abstract Syntax Tree (AST) and generates hundreds of subtle code mutations (mutants): changing `>` to `>=`, changing `+` to `-`, replacing `True` with `False`, or deleting an `if` statement block. B) Running the Test Suite: For each mutant, Mutmut runs the test suite. C) Killed vs Survived Mutants: If the test suite fails (catches the bug), the mutant is 'Killed' (good). If the test suite passes with 100% success on the broken code, the mutant has 'Survived' (bad). A surviving mutant exposes a blind spot where critical business logic is completely unasserted.",
        [
            "Explains that line coverage only tracks execution, not whether assertions verify business correctness",
            "Describes mutation testing generating AST mutations (e.g. changing operators, booleans, logic)",
            "Defines killed mutants (tests caught the bug) vs surviving mutants (tests passed on broken code, exposing blind spots)"
        ],
        [
            "Claims mutation testing genetically modifies the developer's DNA"
        ]
    ),
    (
        "B69_5_6",
        "explain",
        "hard",
        "explain",
        ["Security", "Operating Systems"],
        "Filesystem TOCTOU / Atomic Operations",
        "Filesystem TOCTOU Race Conditions and Atomic File Creation",
        "A developer secures a file creation endpoint: `if not os.path.exists(path): with open(path, 'w') as f: f.write(data)`. A security auditor flags this as a critical Time-Of-Check to Time-Of-Use (TOCTOU) vulnerability susceptible to symlink attacks. Explain how an attacker exploits this race window, and how to implement atomic file creation in Python using `os.open()` with POSIX flags.",
        "The TOCTOU Race Condition Mechanism: 1) The Time Window: The check `os.path.exists(path)` and the creation `open(path, 'w')` are two separate, non-atomic system calls. There is a microsecond gap between the check and the write. 2) The Symlink Exploit: An attacker runs a concurrent process that monitors the filesystem. The moment `os.path.exists(path)` returns `False`, the attacker creates a symbolic link at `path` pointing to a sensitive system file (e.g., `/etc/passwd` or `/etc/shadow`). When the Python script proceeds to `open(path, 'w')`, it follows the symlink and overwrites the sensitive system file with user data, leading to privilege escalation or system destruction. Atomic Implementation in Python: To eliminate the TOCTOU window, file creation and verification must occur in a *single atomic operating system kernel call*: `flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY; fd = os.open(path, flags, 0o600); with os.fdopen(fd, 'w') as f: f.write(data)`. The `O_CREAT | O_EXCL` flags instruct the OS kernel to create the file atomically. If the file (or a symlink) already exists at that exact millisecond, the kernel fails the call immediately with `FileExistsError`, completely closing the race window.",
        [
            "Explains the TOCTOU race: non-atomic gap between os.path.exists() and open() allowing symlink substitution",
            "Demonstrates symlink attacks redirecting writes to sensitive system files (e.g. /etc/passwd)",
            "Implements atomic file creation using os.open() with os.O_CREAT | os.O_EXCL | os.O_WRONLY flags"
        ],
        [
            "Claims TOCTOU vulnerabilities can be resolved by deleting all files on the hard drive"
        ]
    ),
    (
        "B69_5_7",
        "diagnose",
        "medium",
        "debugging",
        ["Security", "Filesystem"],
        "Path Traversal / pathlib",
        "Path Traversal and Symlink Escapes: pathlib.Path.resolve() vs os.path.abspath()",
        "A Python file download endpoint attempts to prevent directory traversal attacks: `safe_dir = '/var/data'; full_path = os.path.abspath(os.path.join(safe_dir, user_filename)); if not full_path.startswith(safe_dir): raise PermissionError()`. An attacker bypasses this check and downloads `/etc/shadow`. How did an attacker use symbolic links to bypass `os.path.abspath()`, and how does `pathlib.Path.resolve(strict=True)` guarantee containment?",
        "Why os.path.abspath() Fails against Symlinks: 1) What abspath Does: `os.path.abspath()` is a purely logical string manipulation function. It resolves `..` relative segments and normalizes slashes, but it does NOT inspect the filesystem or resolve symbolic links! 2) The Symlink Attack: If an attacker uploads or creates a symbolic link inside `/var/data` (e.g., `/var/data/link -> /etc/`), and requests `user_filename = 'link/shadow'`: `os.path.abspath('/var/data/link/shadow')` evaluates to `'/var/data/link/shadow'`. 3) Bypass: The string check `'/var/data/link/shadow'.startswith('/var/data')` evaluates to `True`! When `open()` executes, the OS kernel resolves the symlink, opening `/etc/shadow`. Secure Resolution with `pathlib.Path`: 1) Real Path Resolution: Use `pathlib.Path.resolve(strict=True)`: `base_dir = Path('/var/data').resolve(); target_path = (base_dir / user_filename).resolve()`. 2) Physical Link Traversal: `.resolve()` physically traverses the filesystem and resolves ALL symbolic links to their real target path (turning `link/shadow` into `/etc/shadow`). 3) Containment Check: Use `target_path.is_relative_to(base_dir)` (Python 3.9+). If `/etc/shadow` is checked, `is_relative_to(base_dir)` returns `False`, completely neutralizing symlink escapes.",
        [
            "Explains that os.path.abspath() normalizes string paths but does not resolve filesystem symbolic links",
            "Demonstrates symlinks bypassing string startswith() checks while pointing outside the safe directory",
            "Prescribes pathlib.Path.resolve(strict=True) combined with target.is_relative_to(base) to enforce physical containment"
        ],
        [
            "Claims path traversal attacks are physically impossible in Python 3"
        ]
    ),
    (
        "B69_5_8",
        "concept",
        "easy",
        "concept",
        ["Security", "Operating Systems"],
        "tempfile module",
        "Secure Temporary File Creation: tempfile.NamedTemporaryFile vs mktemp",
        "Why is `tempfile.mktemp()` deprecated and prohibited in secure Python applications, and how do `tempfile.NamedTemporaryFile()` and `tempfile.TemporaryDirectory()` guarantee secure file creation?",
        "1) The `tempfile.mktemp()` Vulnerability: `mktemp()` merely generates a random string representing a temporary file path; it does NOT create the file. A developer typically writes: `path = tempfile.mktemp(); open(path, 'w')`. This introduces a classic TOCTOU race: an attacker monitoring `/tmp` can create a symlink at that generated path in the microsecond before `open()` runs, redirecting writes to overwrite system files or reading the created file before permissions are restricted. 2) Secure Creation via `NamedTemporaryFile()`: `tempfile.NamedTemporaryFile()` creates the file atomically at the OS kernel level using `O_CREAT | O_EXCL` flags. 3) Restrictive Permissions: It automatically assigns strict file permissions (`0600` on Unix), ensuring that ONLY the current process user can read or write to the file; other users on the shared machine cannot access it. 4) Automatic Cleanup: When closed (or when context exits), the file is automatically unlinked and deleted from disk.",
        [
            "Explains that mktemp() generates a path without creating the file, introducing TOCTOU symlink races",
            "Details NamedTemporaryFile() creating files atomically with O_CREAT | O_EXCL kernel flags",
            "Highlights strict 0600 file permissions and automated deletion on close"
        ],
        [
            "Claims temporary files are automatically deleted by the CPU hardware every 60 seconds"
        ]
    ),
    (
        "B69_5_9",
        "implement",
        "medium",
        "implement",
        ["Security", "Logging"],
        "traceback / sys.excepthook",
        "Preventing Sensitive Credential Leakage in Exception Tracebacks",
        "In a Python backend application, an unhandled database exception prints a traceback containing local variables (`f_locals`), inadvertently exposing database passwords, API keys, and customer credit cards in centralized logging systems (Datadog/Sentry). How do you implement automated traceback sanitization using custom `sys.excepthook` or `__traceback_hide__` to strip sensitive credentials from logs?",
        "Traceback Credential Sanitization: 1) The Danger of Frame Introspection: When exceptions occur, error reporting tools inspect the traceback frames (`tb.tb_frame.f_locals`). If variables like `password`, `auth_token`, or `api_key` exist in local scope, their plaintext values are serialized into log files. 2) Using `__traceback_hide__`: In libraries and frameworks (FastAPI, pytest), setting `__traceback_hide__ = True` inside a function instructs reporting tools to omit that entire frame from the traceback. 3) Global Exception Sanitization via `sys.excepthook`: Override `sys.excepthook` to sanitize frames before printing: `def secure_excepthook(exc_type, exc_value, tb): sanitize_traceback(tb); sys.__excepthook__(exc_type, exc_value, tb)`. 4) Sanitization Logic: Traverse frames (`while tb:`), inspect `tb.tb_frame.f_locals`. For any key matching sensitive patterns (`*password*`, `*secret*`, `*token*`, `*key*`), scrub or mask the value (`'***REDACTED***'`). 5) Clearing Frame References: Call `traceback.clear_frames(tb)` to break circular references and free local variables from memory once logged.",
        [
            "Identifies that unhandled exception tracebacks serialize frame locals (f_locals), exposing secrets in logs",
            "Implements custom sys.excepthook to intercept uncaught exceptions and sanitize sensitive variable names",
            "Uses traceback.clear_frames() to purge frame local variables from memory after logging"
        ],
        [
            "Suggests never catching exceptions and letting servers crash silently"
        ]
    ),
    (
        "B69_5_10",
        "explain",
        "hard",
        "explain",
        ["Security", "Networking"],
        "urllib.parse / SSRF",
        "Unsafe URL Parsing in urllib.parse and Parser Ambiguities",
        "A developer validates outbound URLs to prevent SSRF: `parsed = urllib.parse.urlsplit(url); if parsed.hostname not in ALLOWED_HOSTS: raise ValueError()`. Security researchers demonstrate that attackers can bypass this check using URL parser discrepancies (such as backslashes, whitespace, and port confusion). How do discrepancies between Python's `urlsplit()` and underlying HTTP clients (like `curl` or `requests`) enable parser differential attacks?",
        "Parser Differential Vulnerabilities in urllib.parse: 1) The Parser Differential Problem: Security validation occurs in Python using `urllib.parse.urlsplit()`, but the actual network request is executed by an underlying HTTP client or library (`requests`, `urllib3`, or `curl`). If Python and the HTTP client parse RFC 3986 URL specifications differently, the validator and requester see two different destinations! 2) Backslash Handling: In older Python versions, `urlsplit('https://allowed.com\\@evil.com')` extracted `allowed.com` as the hostname. However, web browsers and cURL treat backslashes as forward slashes (`/`), resolving the hostname as `evil.com`. The validator approved `allowed.com`, but the HTTP client requested `evil.com`. 3) Embedded Control Characters and Whitespace: Leading/trailing tabs or newline characters (`\\r`, `\\n`) in URL strings can be stripped or normalized differently across libraries. 4) IDNA Domain Spoofing: Unicode domain normalization can cause homograph confusion where visually identical characters resolve to different IP addresses. Remediation: 1) Always use updated Python releases with CVE-patched URL parsers. 2) Reconstruct Canonical URLs: Do not forward raw client URL strings; validate individual components and reconstruct the canonical URL string (`urlunsplit()`). 3) Socket-level IP validation.",
        [
            "Defines parser differential attacks: validator (urlsplit) and requester (HTTP client) disagreeing on parsed hostname",
            "Identifies backslash and control character normalization vulnerabilities routing to malicious hosts",
            "Prescribes reconstructing canonical URLs from validated components and validating resolved socket IPs"
        ],
        [
            "Claims urllib.parse is an insecure library that was banned by the United Nations"
        ]
    ),
    (
        "B69_5_11",
        "diagnose",
        "hard",
        "debugging",
        ["Memory Management", "CPython Internals"],
        "functools.lru_cache / Memory Leaks",
        "The functools.lru_cache Memory Leak on Class Instance Methods",
        "In a web application, a developer decorates an instance method with `@functools.lru_cache(maxsize=128)`: `class User: @lru_cache(maxsize=128) def get_permissions(self): ...`. Over time, server memory grows continuously, and `User` instances are NEVER garbage collected, even after users log out and sessions end. Why does decorating an instance method with `lru_cache` cause permanent memory leaks, and how do you resolve it?",
        "Root Cause: Bound Methods and Circular Reference Pinning: 1) Method vs Function Scope: When `@lru_cache` decorates a function, the cache dictionary belongs to the function object. When decorating an *instance method* on a class, the cache is shared or created on the method definition. 2) Implicit `self` Argument: An instance method's first parameter is `self`. The cache dictionary keys are tuples of function arguments: `(self, args...)`. 3) The Strong Reference Trap: The `lru_cache` internal dictionary holds a *strong reference* to all cache keys and values! Because `self` is part of the cache key, `lru_cache` holds a strong reference to the `User` instance. 4) Result: Even if the application drops all external references to `user`, the global class method's `lru_cache` keeps the `User` object alive in memory. If 100,000 users visit the site, all 100,000 `User` instances remain pinned in RAM permanently. Solutions: 1) Never decorate instance methods directly with `@lru_cache`. 2) Cache on IDs: Decorate a static method or module-level function taking primitive IDs: `@lru_cache def get_permissions(user_id): ...`. 3) Instance-Level Cache: Initialize the cache inside `__init__` or use a custom descriptor that binds cache lifecycles to individual instance lifecycles.",
        [
            "Explains that lru_cache stores arguments as cache keys, holding strong references to self (the instance)",
            "Identifies that class-level caches prevent User instances from ever reaching zero reference count, causing permanent leaks",
            "Prescribes caching by primitive ID (user_id) or attaching caches strictly to instance lifecycles"
        ],
        [
            "Claims lru_cache can only store numbers between 1 and 10"
        ]
    ),
    (
        "B69_5_12",
        "diagnose",
        "medium",
        "debugging",
        ["Performance Tuning", "Concurrency"],
        "CPU Contention / Busy-Waiting",
        "Diagnosing 100% CPU Utilization during Zero-Traffic Idle Periods",
        "A background worker service deployed on Kubernetes shows 100% CPU utilization across all cores, even in staging environments with zero incoming tasks or traffic. You attach a profiler and find that no actual business logic is executing. What common Python programming mistakes cause busy-wait spinning, and how do you diagnose this using `strace` and `py-spy`?",
        "Root Causes of Busy-Wait Spinning: 1) Non-Blocking Polling Loops: Writing a `while True:` loop without blocking syscalls: `while True: msg = queue.get_nowait(); if msg: process(msg)`. When the queue is empty, `get_nowait()` throws `Empty` immediately, causing the `while` loop to spin millions of times per second on the CPU core. 2) Tight Loop on `select` with Zero Timeout: Calling `select.select(sockets, [], [], 0)` in a loop with a 0-second timeout polls without blocking, burning 100% CPU. 3) Misconfigured SQS/Redis Polling: Calling short-polling Redis `RPOP` in a loop without sleeping instead of blocking `BRPOP`. Diagnosis Procedure: 1) `py-spy`: Run `py-spy dump --pid <PID>`. The stack trace immediately reveals the exact line of Python code executing repeatedly inside the busy-wait loop. 2) `strace`: Run `strace -p <PID> -c`. If `strace` reports hundreds of thousands of non-blocking `epoll_wait` or `read` syscalls per second returning immediately with `EAGAIN` or empty responses, the process is busy-spinning. Remediation: Replace busy-wait loops with true blocking calls (`queue.get()` with timeout, blocking `BRPOP`, or `asyncio.Event.wait()`).",
        [
            "Identifies non-blocking polling loops (e.g. get_nowait() or zero-timeout select) spinning continuously",
            "Uses py-spy stack traces to locate the spinning line of Python code",
            "Uses strace to detect thousands of non-blocking syscalls per second and remediates with blocking primitives"
        ],
        [
            "Suggests turning off the CPU cooling fan to slow down the processor"
        ]
    ),
    (
        "B69_5_13",
        "diagnose",
        "medium",
        "debugging",
        ["Async Concurrency", "Performance Tuning"],
        "asyncio / Blocking I/O",
        "Diagnosing Latency Spikes from Synchronous Calls in Asyncio Loops",
        "A FastAPI microservice designed for high concurrency exhibits sudden latency spikes from 15ms to 6,000ms under moderate load. You inspect APM metrics and notice that whenever the spike occurs, all concurrent HTTP requests across all endpoints freeze simultaneously. What causes synchronous blocking I/O (like `requests.get()` or `time.sleep()`) to freeze an entire asyncio service, and how do you detect blocking calls using `asyncio` debug mode?",
        "Mechanism of the Freeze: `asyncio` runs on a single operating system thread. When code executes an asynchronous call (`await httpx_client.get()`), it yields execution to the event loop. However, if a developer mistakenly writes a synchronous blocking call: `requests.get('http://thirdparty.com')`, `time.sleep(5)`, or a synchronous file write, the single Python thread *blocks at the OS kernel socket level*. The event loop is completely frozen! It cannot poll network descriptors, cannot process incoming HTTP connections, and cannot advance any other coroutines. All concurrent users experience a latency spike equal to the duration of the synchronous call. How to Detect Blocking Calls: 1) Enable Asyncio Debug Mode: Set environment variable `PYTHONASYNCIODEBUG=1` or configure `loop.set_debug(True)`. 2) Slow Callback Threshold: Configure `loop.slow_callback_duration = 0.05` (50ms). When any coroutine or callback executes synchronously without yielding for more than 50ms, asyncio logs a critical warning with the exact file and line number: `Executing <Handle ...> took 1.250 seconds!`. 3) Profiling with py-spy: Capture non-blocking thread traces to pinpoint the synchronous blocking call and replace it with `asyncio.to_thread()` or async native libraries.",
        [
            "Explains that synchronous blocking calls block the single event loop thread, freezing all concurrent requests",
            "Enables asyncio debug mode (PYTHONASYNCIODEBUG=1) and tunes slow_callback_duration to catch blocking callbacks",
            "Prescribes replacing blocking synchronous calls with async native clients or offloading to asyncio.to_thread"
        ],
        [
            "Claims asyncio applications can never make HTTP requests"
        ]
    ),
    (
        "B69_5_14",
        "scenario",
        "medium",
        "scenario",
        ["Multiprocessing", "CPython Internals"],
        "Import Lock / fork Deadlock",
        "Multi-Threaded Fork Deadlocks on CPython Module Imports",
        "A Python backend initializes background threads (e.g., telemetry reporting) at startup. Later, when a heavy task arrives, it spawns child worker processes using `multiprocessing.Process(target=worker)`. Intermittently, child processes hang permanently immediately upon starting, before executing any business logic. Attaching `gdb` shows the child process is blocked on CPython's internal `import lock`. How does importing modules post-fork cause this deadlock, and how do you resolve it?",
        "Root Cause: The CPython Global Import Lock across Fork Boundaries: 1) The Import Lock Mechanism: In CPython, module importing is thread-safe: whenever a thread executes an `import` statement, CPython acquires an internal per-module lock (or global import lock) to ensure two threads do not import the same module concurrently. 2) The Multi-Threaded Fork Race: Thread A (telemetry worker) begins importing a module (e.g., `import requests`). Thread A acquires the internal import lock. 3) The Interruption: At that exact microsecond, Thread B (the main thread) calls `os.fork()`. 4) Deadlock in Child: As dictated by POSIX fork rules, Thread A does NOT exist in the child process! However, the import lock's C memory state is copied to the child in the *locked* state. When the child process boots up and executes its first line: `import my_module`, the child attempts to acquire the import lock. Because the lock is held by a dead thread that will never release it, the child process deadlocks forever before executing a single line of application code. Solutions: 1) Pre-import all modules in the main thread before starting background threads or spawning children. 2) Switch startup method from `fork` to `spawn` or `forkserver` (`multiprocessing.set_start_method('spawn')`), ensuring child processes start with clean lock states.",
        [
            "Explains that CPython module imports acquire an internal import lock for thread safety",
            "Identifies that forking while a secondary thread holds the import lock leaves the lock permanently held in the child",
            "Resolves deadlock by pre-importing all modules before thread creation or switching start method to spawn/forkserver"
        ],
        [
            "Claims Python import statements should only be written at the bottom of files"
        ]
    ),
    (
        "B69_5_15",
        "explain",
        "medium",
        "explain",
        ["Memory Management", "Error Handling"],
        "Exceptions / Reference Cycles",
        "Exception Scope Reference Cycles: The 'as exc' Variable Leak",
        "In Python, writing `except Exception as exc:` creates an implicit exception variable. Prior to Python 3, this frequently caused permanent memory leaks. How does an exception object hold a reference cycle to its own execution frame, and why does Python 3's compiler automatically generate a `del exc` in the `finally` block of every `except` clause?",
        "The Exception-Frame Reference Cycle: 1) Anatomy of an Exception Object: When an exception occurs, Python attaches a traceback object to it: `exc.__traceback__`. 2) The Frame Pointer: The traceback object holds a reference to the execution frame where the exception occurred (`tb_frame`). 3) The Local Variable Pointer: The frame object holds a dictionary/array of all local variables in that function (`f_locals`). 4) The Circular Trap: When you write `except Exception as exc:`, `exc` becomes a local variable in `f_locals`! A direct circular reference forms: `exc -> __traceback__ -> tb_frame -> f_locals -> exc`. 5) Consequence: The exception, the traceback, and ALL local variables in that function remain pinned in memory. The entire stack frame cannot be freed by reference counting; it must wait for cyclic GC collection. The Python 3 Compiler Solution: To prevent this memory trap, the Python 3 compiler translates `except Exception as exc:` into an implicit `try...finally` block: `try: ... except Exception as exc: try: ... finally: del exc`. By automatically deleting the local variable `exc` upon exiting the `except` block, Python breaks the circular reference, allowing execution frames and local variables to be deallocated immediately.",
        [
            "Details the cycle: exc -> __traceback__ -> tb_frame -> f_locals -> exc",
            "Explains that the cycle keeps execution frames and all local variables pinned in memory",
            "Shows that Python 3's compiler automatically generates a hidden finally: del exc to break the circular reference"
        ],
        [
            "Claims Python deletes exception variables to make error messages unreadable"
        ]
    ),
    (
        "B69_5_16",
        "explain",
        "medium",
        "explain",
        ["Performance Tuning", "Profiling"],
        "py-spy / Flame Graphs",
        "Zero-Overhead Production Profiling with py-spy and Flame Graph Analysis",
        "Why is using standard Python profilers like `cProfile` dangerous in high-throughput production environments, and how does `py-spy` profile running CPython processes with near-zero overhead by reading process virtual memory directly?",
        "Why cProfile is Dangerous in Production: 1) Deterministic Tracing Overhead: `cProfile` is a deterministic instrumentation profiler that hooks into CPython's internal `sys.setprofile()` C-API. It intercepts every single function call, return, and exception. In high-throughput microservices, this introduces a 20% to 100% latency penalty, alters timing characteristics, and can crash production services under heavy load. How `py-spy` Works with Zero Overhead: 1) Out-of-Process Memory Sampling: `py-spy` is written in Rust and runs as an external, out-of-process sampling profiler. It does NOT modify or inject code into the running Python process. 2) Reading OS Virtual Memory: It uses OS debugging syscalls (`process_vm_readv` on Linux, `vm_read` on macOS) to read the target process's virtual memory address space directly. 3) CPython Struct Traversal: `py-spy` parses CPython's internal C structures (`PyInterpreterState`, `PyThreadState`, and active `PyFrameObject` linked lists) from outside the process. It samples call stacks 100 times per second with less than 1% CPU overhead. 4) Flame Graphs: It generates interactive SVG Flame Graphs visualizing CPU hotspots, distinguishing pure Python bytecode evaluation time from native C-extension execution and GIL wait time.",
        [
            "Explains that cProfile hooks sys.setprofile, introducing 20-100% overhead that alters production timing",
            "Describes py-spy reading process virtual memory out-of-process via process_vm_readv without code injection",
            "Generates Flame Graphs with < 1% overhead, distinguishing Python execution from native C and GIL wait times"
        ],
        [
            "Claims py-spy is a government surveillance spyware tool"
        ]
    ),
    (
        "B69_5_17",
        "concept",
        "easy",
        "concept",
        ["Performance Tuning", "CPython Internals"],
        "Bytecode Optimization",
        "Function Call Overhead in Python and Local Variable Caching",
        "Why do function calls in Python incur non-trivial CPU overhead compared to languages like C or Go, and why does caching global built-in functions as local variables (`_len = len`) accelerate tight execution loops?",
        "1) The Cost of Python Function Calls: Unlike compiled languages where function calls compile to a single CPU `CALL` instruction, a Python function call is heavy: A) CPython must allocate a new `PyFrameObject` on the heap (or reuse from a frame free list). B) It must bind positional and keyword arguments, create tuple/dict objects for `*args` and `**kwargs`, set up default argument pointers, and initialize the fast-locals array. In tight loops running millions of iterations, function call overhead easily dominates execution time. 2) Local Variable Caching (`_len = len`): Opcodes for global lookups (`LOAD_GLOBAL`) must search the module globals dictionary and the builtins dictionary. In contrast, local variable access uses `LOAD_FAST`, which indexes directly into the internal C array `f_localsplus` via an integer index in a single CPU instruction. Caching `_len = len` before a tight loop converts thousands of dictionary lookups into instant array lookups, speeding up CPU-bound loops by 15-25%.",
        [
            "Breaks down Python function call overhead: PyFrameObject allocation, argument tuple/dict creation, and setup",
            "Contrasts LOAD_GLOBAL dictionary lookups with LOAD_FAST contiguous C array indexing",
            "Demonstrates local variable caching (_len = len) accelerating tight loops by avoiding global dictionary lookups"
        ],
        [
            "Claims local variables run faster because they are stored on the monitor screen"
        ]
    ),
    (
        "B69_5_18",
        "scenario",
        "medium",
        "scenario",
        ["Web Architecture", "Performance Tuning"],
        "Imports / Tail Latency",
        "Tail Latency Spikes from Lazy Module Imports in Route Handlers",
        "To optimize application startup time, a developer moves heavy imports inside endpoint handlers: `@app.get('/analyze') def analyze(): import scipy.stats; ...`. After deployment, average API latency is 10ms, but the 99th percentile (p99) latency spikes to 1,500ms on newly scaled worker pods. Why do lazy imports inside request handlers cause severe tail latency, and how should module loading be architected?",
        "Mechanism of the Tail Latency Spike: 1) Heavy Disk and Bytecode Overhead: When `import scipy.stats` executes for the first time, CPython must locate dozens of `.py` and native `.so` files on disk, compile or read bytecode, allocate hundreds of module dictionaries, and execute C initialization routines. This takes 500ms to 2,000ms. 2) The Cold-Start Penalty: The *first* unfortunate user whose request hits a newly autoscaled worker pod suffers the entire 1,500ms import penalty (causing a massive p99/p99.9 tail latency spike). 3) Import Lock Contention: If multiple concurrent requests hit the uninitialized endpoint simultaneously, they contend on CPython's internal module import lock, serializing execution and blocking worker threads. Architectural Fix: 1) Eager Module Loading: Move all standard and heavy imports to module top-level scope. 2) Container Startup Probes: Let the import overhead occur during container startup. The Kubernetes Startup/Readiness probe will keep the pod out of the load balancer rotation until all modules are fully loaded in memory. Once the pod receives user traffic, all requests execute in 10ms with consistent, flat p99 latency.",
        [
            "Identifies that lazy imports defer disk I/O, compilation, and C initialization to runtime request threads",
            "Explains that initial requests on newly scaled pods suffer 1,500ms import penalties, destroying p99 tail latency",
            "Prescribes eager top-level imports combined with Kubernetes readiness probes to warm pods before serving traffic"
        ],
        [
            "Claims scipy.stats can only be imported when connected to the internet"
        ]
    ),
    (
        "B69_5_19",
        "explain",
        "medium",
        "explain",
        ["Performance Tuning", "Data Science"],
        "NumPy / Vectorization",
        "Vectorization vs Python List Comprehensions: Memory Locality and SIMD",
        "A Python list comprehension processing 10 million floats (`[x * 2.5 for x in numbers]`) takes 1.2 seconds, while the equivalent NumPy vectorized operation (`numbers * 2.5`) takes 0.008 seconds (150x faster). Explain the hardware and memory architecture reasons (CPU cache locality, pointer dereferencing, and SIMD vectorization) that make NumPy operations orders of magnitude faster.",
        "Architectural Differences between Python Lists and NumPy Arrays: 1) Memory Layout and Pointer Chasing: A Python list is a contiguous array of *pointers* (8 bytes each). Each pointer points to an independent, heap-allocated `PyFloatObject` scattered randomly across RAM. Accessing elements requires 'pointer chasing', causing constant CPU cache misses. In contrast, a NumPy array stores raw 64-bit IEEE 754 floating-point numbers *contiguously in a single contiguous block of physical RAM*. 2) CPU Cache Locality: Because NumPy data is contiguous, modern CPU hardware pre-fetchers load entire cache lines (64 bytes / 8 floats) into L1/L2 CPU caches ahead of time, achieving near-zero memory latency. 3) Elimination of Dynamic Type Boxing: In a Python list comprehension, every iteration checks types, unpacks the float, multiplies, and boxes the result into a new heap `PyFloatObject`. NumPy executes in compiled C code with fixed types, bypassing Python interpreter evaluation entirely. 4) Hardware SIMD (Vectorization): The C compiler compiles NumPy array operations into CPU SIMD (AVX-512 / AVX2) vector instructions. A single CPU instruction multiplies 4 or 8 floats simultaneously in parallel hardware registers, achieving 150x speedups.",
        [
            "Contrasts Python list pointer chasing (cache misses) with NumPy's contiguous raw memory blocks (cache line hits)",
            "Explains elimination of dynamic type checking and PyFloatObject boxing overhead in compiled C loops",
            "Details hardware SIMD vectorization (AVX2/AVX-512) processing multiple numbers in parallel per CPU cycle"
        ],
        [
            "Claims NumPy is faster because it deletes half of the numbers to save time"
        ]
    ),
    (
        "B69_5_20",
        "explain",
        "hard",
        "explain",
        ["Concurrency", "CPython Internals"],
        "GIL / Threading Contention",
        "GIL Contention in Mixed CPU and I/O Multi-Threaded Workloads",
        "In Python, running two threads—Thread 1 (performing heavy CPU number crunching) and Thread 2 (handling lightweight network I/O)—often causes Thread 2's network latency to jump by 50x compared to running Thread 2 alone. Explain how the CPython Global Interpreter Lock (GIL) switching mechanism (`sys.getswitchinterval()`) and lock contention cause the CPU-bound thread to starve the I/O thread.",
        "How the GIL Causes I/O Thread Starvation: 1) The Switch Interval: In Python 3.2+, the GIL uses a time-based switching mechanism (`sys.setswitchinterval(0.005)`, default 5 milliseconds). When a CPU thread runs, it holds the GIL. When 5ms elapse, the operating system signals that the GIL should be released. 2) The Convoy and Starvation Race: When Thread 2 (I/O thread) receives a network packet, the OS wakes it up. Thread 2 must acquire the GIL before it can execute a single Python bytecode. It signals Thread 1 to release the GIL and waits on a condition variable. 3) The Lock Contention Race: Thread 1 sees the signal, releases the GIL, and immediately attempts to re-acquire it. On multi-core CPUs, Thread 1 (which is already hot and running on an active CPU core) frequently re-acquires the GIL *before* the operating system can context-switch Thread 2 into execution! 4) The 'Battle of the Threads': Thread 2 is forced to wait through multiple 5ms switch intervals just to process a single network packet, turning a 0.5ms network response into a 50ms latency spike. Solution: Never mix CPU-heavy loops with latency-sensitive async or I/O threads in the same Python process. Offload CPU workloads to `multiprocessing`, C-extensions releasing the GIL (`Py_BEGIN_ALLOW_THREADS`), or independent worker processes.",
        [
            "Explains the GIL switch interval (sys.getswitchinterval, default 5ms) governing thread preemption",
            "Describes CPU-bound threads re-acquiring the GIL before the OS can schedule the waking I/O thread",
            "Identifies severe I/O latency degradation caused by GIL contention and prescribes isolating CPU work to separate processes"
        ],
        [
            "Claims the GIL is an error message displayed when a computer runs out of disk space"
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 5).")
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
    print("POST-BATCH AUDIT PART 5")
    print("========================================")
    print(f"Batch: 69 Part 5")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
