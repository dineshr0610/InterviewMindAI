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

ROLE = "Backend Developer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

# Tuple structure:
# (id_code, intent, difficulty, question_type, [primary_skill, secondary_skills...], technology, topic, question, expected_answer, strong_indicators, weak_indicators)
Q = [
    (
        "B68_1_1",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Distributed Transactions", "Saga Pattern"],
        "Microservices Architecture",
        "Pivot and Compensable Transactions in Sagas",
        "In a distributed Saga pattern orchestrating an order fulfillment workflow across payment, inventory, shipping, and email services, what is the architectural distinction between 'Compensable Transactions', the 'Pivot Transaction', and 'Retriable Transactions', and how does identifying the pivot transaction define the point of no return for rollback?",
        "In a Saga workflow: 1) Compensable Transactions are steps that occur before the pivot transaction and can be semantically undone if a subsequent step fails (e.g., reserving inventory can be undone by releasing inventory; placing a temporary hold on a credit card can be undone by canceling the hold). 2) The Pivot Transaction is the single irreversible or critical turning point of the workflow. Once the pivot transaction commits successfully, the Saga guarantees that the overall business process will not be rolled back; instead, it must proceed forward to completion. For example, capturing the user's payment or submitting the order to physical fulfillment is the pivot transaction. If the pivot transaction fails, all previously completed compensable steps must execute their compensation logic in reverse order. 3) Retriable Transactions are steps that occur *after* the pivot transaction and are guaranteed to eventually succeed via retries (e.g., sending an order confirmation email or notifying analytics). Because they cannot fail permanently without violating business consistency, they must be idempotent and retried until completion. Identifying the pivot transaction is essential because once it commits, compensation is no longer possible, and the backend must transition exclusively from backward recovery (compensation) to forward recovery (retries and escalation).",
        [
            "Defines compensable transactions as reversible operations preceding the pivot transaction",
            "Defines the pivot transaction as the definitive turning point after which rollback is impossible",
            "Defines retriable transactions as idempotent operations following the pivot that must succeed via forward recovery"
        ],
        [
            "Claims that every single step in a saga must be compensable even after payment is captured"
        ]
    ),
    (
        "B68_1_2",
        "scenario",
        "hard",
        "scenario",
        ["Distributed Transactions", "Fault Tolerance"],
        "Workflow Orchestrator",
        "Compensation Failure Handling in Saga Orchestration",
        "You are designing a centralized Saga orchestrator for a banking platform. During a multi-step fund transfer, Step 3 (debit destination account) fails, triggering compensations. However, when the orchestrator sends a compensation command to Step 2 (refund source account), the source account service repeatedly responds with an HTTP 500 Internal Server Error due to a database deadlock. How must the orchestrator handle compensation failures to prevent financial inconsistency, and why is an infinite synchronous retry loop hazardous?",
        "When a compensation step fails in a Saga, the orchestrator cannot simply abort the rollback or ignore the failure; doing so leaves the system in a corrupt, partially compensated state where money is permanently lost or duplicated. To handle this safely: 1) The orchestrator must persist the compensation intent in a durable transaction log with an explicit status like 'COMPENSATION_PENDING' or 'COMPENSATION_FAILED'. 2) The orchestrator must not rely on an unbounded synchronous retry loop in the request thread because holding resources (threads, open connections) under persistent failures causes thread pool starvation and cascading failure. 3) Retries must be scheduled asynchronously using exponential backoff with jitter and a maximum retry threshold. 4) If automated retries are exhausted or return unrecoverable errors, the orchestrator must transition the saga to an 'OPERATOR_INTERVENTION_REQUIRED' state, route the saga context to a dedicated Dead-Letter/Escalation queue, and trigger high-priority alerts for automated reconcile workers or manual finance engineering reconciliation. 5) The participant microservice must expose an idempotent compensation endpoint so that when retries succeed, duplicate refunds are strictly avoided.",
        [
            "Identifies that compensation failures cannot be dropped and must be durably recorded in state",
            "Rejects unbounded synchronous retries to avoid thread and resource exhaustion",
            "Prescribes asynchronous exponential backoff and escalation to a manual intervention / dead-letter queue when retries fail"
        ],
        [
            "Suggests ignoring the compensation failure and assuming the user will report missing funds"
        ]
    ),
    (
        "B68_1_3",
        "diagnose",
        "medium",
        "debugging",
        ["Distributed Transactions", "Timeout Handling"],
        "gRPC/HTTP Microservices",
        "Orchestrator Timeout Ambiguity and State Queries",
        "An API orchestrator invokes a downstream billing service via gRPC to capture a $500 payment. The orchestrator's client-side deadline expires after 5 seconds, throwing a `DEADLINE_EXCEEDED` error. The developer immediately triggers compensation logic to release reserved inventory. However, 10 minutes later, the customer complains that their credit card was charged AND their order was canceled. What distributed systems flaw caused this bug, and what must the orchestrator do before initiating compensation upon a timeout?",
        "The flaw is treating a network or deadline timeout as a confirmed failure. In distributed systems, a `DEADLINE_EXCEEDED` error indicates an *unknown state* (the two-generals problem): the request packet may have been lost before reaching the server, the server may still be actively executing the charge, or the server may have completed the charge successfully while the response packet was lost in transit. By immediately triggering compensation without confirming the downstream state, the orchestrator assumed the payment failed when it actually succeeded, causing double cancellation and wrongful billing. To fix this: 1) The orchestrator must never assume a timed-out call failed. 2) Before initiating compensation or declaring the workflow terminated, the orchestrator must query the billing service's idempotent status API using the original unique `Idempotency-Key` or `Transaction-ID`. 3) If the billing service reports the charge succeeded, the orchestrator can either proceed forward with the workflow or issue an explicit idempotent refund. 4) If the billing service reports no transaction exists, it marks the idempotency key as aborted so any delayed in-flight charge attempt will be rejected.",
        [
            "Identifies that a client-side timeout represents an unknown state, not a confirmed failure",
            "Explains that the downstream billing service may have processed the payment despite the timeout",
            "Mandates querying the downstream service state via an idempotency key before deciding to compensate or advance"
        ],
        [
            "Assumes a DEADLINE_EXCEEDED error guarantees that downstream database changes were automatically rolled back"
        ]
    ),
    (
        "B68_1_4",
        "implement",
        "medium",
        "implement",
        ["Distributed Transactions", "Idempotency"],
        "Event-Driven Architecture",
        "Idempotent Compensation Handlers via State Fencing",
        "In an event-driven choreography saga, compensation events (`RollbackInventory`, `CancelReservation`) can arrive out of order, repeatedly, or even before the original forward event (`ReserveInventory`) due to message broker retries and network race conditions. How do you design an idempotent compensation consumer that prevents applying refunds to non-existent reservations or applying compensations multiple times?",
        "To handle out-of-order and duplicate compensations reliably: 1) Use a State-Fencing Machine with persistent state tracking per entity (e.g., `Reservation` table with states: `PENDING`, `CONFIRMED`, `COMPENSATING`, `COMPENSATED`). 2) Maintain an Idempotency/Transaction Ledger recording processed event IDs and their resulting states within the same local database transaction. 3) If a compensation event arrives for an already `COMPENSATED` entity, the consumer detects the completed state and immediately acknowledges the message without reapplying the compensation. 4) If a compensation event arrives *before* the forward creation event (due to network reordering): the consumer inserts a placeholder record with state `COMPENSATED` or `CANCELED_BEFORE_CREATION`. When the delayed forward event finally arrives, it checks the entity state, sees it is already marked `COMPENSATED`, and immediately aborts execution without allocating resources. 5) All state transitions must occur within atomic database transactions with conditional updates (`WHERE status IN ('PENDING', 'CONFIRMED')`).",
        [
            "Utilizes an explicit state machine and entity status checks to reject duplicate compensation",
            "Addresses the out-of-order scenario where compensation arrives before the forward action by creating a canceled placeholder state",
            "Enforces atomic local database transactions with conditional updates"
        ],
        [
            "Suggests dropping compensation messages if the reservation record is not found in the database"
        ]
    ),
    (
        "B68_1_5",
        "concept",
        "easy",
        "concept",
        ["Distributed Systems", "Fault Tolerance"],
        "Distributed Computing",
        "Forward Recovery vs Backward Recovery in Distributed Workflows",
        "What is the difference between 'Forward Recovery' and 'Backward Recovery' in long-running distributed backend workflows, and what physical or real-world constraints force an engineering team to choose forward recovery?",
        "Backward Recovery (Rollback / Compensation): The system restores itself to its initial state prior to the transaction by executing compensating actions in reverse order (e.g., releasing held inventory, crediting a wallet). It is suitable when all actions are reversible and the business prefers abandoning the operation over waiting. Forward Recovery (Roll-forward / Retry): The system accepts that the transaction has progressed past the point of return and guarantees that the workflow will eventually reach a successful completed state by retrying failed components, utilizing backup workers, or applying state machine transitions until complete. Constraints forcing forward recovery: 1) Physical actions that cannot be electronically undone (e.g., an automated warehouse robot has already placed a package on a courier truck, or an SMS OTP has already been transmitted). 2) External irreversible third-party APIs that do not support cancellation. 3) Operations where legal or financial regulations mandate that once initiated, the transaction must settle (e.g., certain inter-bank clearing protocols).",
        [
            "Defines backward recovery as rolling back to the initial state via compensation",
            "Defines forward recovery as retrying and progressing forward to reach terminal completion",
            "Cites irreversible physical actions, external non-cancellable APIs, or regulatory settlement rules as reasons for forward recovery"
        ],
        [
            "States that forward recovery means restarting the entire workflow from step 1 with a new ID"
        ]
    ),
    (
        "B68_1_6",
        "scenario",
        "medium",
        "scenario",
        ["Database Architecture", "Performance Tuning"],
        "Relational Databases",
        "Transaction Boundary Anti-Pattern with External RPCs",
        "A backend developer writes an order checkout endpoint: `@Transactional public void processOrder(...) { db.deductCredits(userId); httpPostToPaymentGateway(); db.createOrder(orderId); }`. Under peak load of 500 requests per second, the database CPU sits at 15%, but the application server connection pool is completely exhausted, and all database queries time out across the entire platform. Explain the exact mechanism of this failure and how to refactor the transaction boundary.",
        "The root cause is holding an open Relational Database Transaction and its underlying database connection across a high-latency external HTTP RPC call. When `@Transactional` starts, the thread acquires a physical connection from the database connection pool and opens a database transaction. The thread then calls `httpPostToPaymentGateway()`. External HTTP calls routinely take 200ms to 2000ms (or longer under network jitter). While the thread waits for the payment gateway's HTTP response, the database connection remains locked and idle. At 500 requests/sec, if each request holds a connection for 500ms, the system requires 250 concurrent database connections exclusively to wait on network I/O. The connection pool (typically 20-50 connections) is exhausted in milliseconds. Refactoring: 1) Strictly decouple database transactions from external network calls. 2) Step 1: Open a short-lived local DB transaction to record the order in a `PENDING` state and commit immediately, releasing the DB connection. 3) Step 2: Execute the external HTTP call outside of any DB transaction. 4) Step 3: Open a second short-lived local DB transaction to record the payment result, deduct credits, and transition the order state to `CONFIRMED`.",
        [
            "Diagnoses holding an active database connection and transaction across an external HTTP call",
            "Explains that external network latency keeps DB connections idle, causing rapid pool exhaustion",
            "Refactors into separate short-lived local transactions executed before and after the external HTTP call"
        ],
        [
            "Recommends simply increasing the database connection pool size to 5,000 connections"
        ]
    ),
    (
        "B68_1_7",
        "explain",
        "medium",
        "explain",
        ["Distributed Systems", "Observability"],
        "Distributed Tracing",
        "Observability and Correlation in Asynchronous Sagas",
        "In a distributed saga spanning 6 microservices communicating asynchronously via Kafka topics, how do you architect end-to-end observability so that engineers can trace a specific customer's saga execution across asynchronous boundaries and pinpoint which specific participant halted or failed?",
        "To achieve end-to-end observability across asynchronous message boundaries: 1) Correlation ID & Saga ID Propagation: The initiating service generates a unique `Saga-ID` (business lifecycle identifier) and a `Trace-ID` (distributed trace context). These identifiers must be injected into the message metadata/headers (e.g., Kafka record headers `x-correlation-id`, `traceparent` conforming to W3C Trace Context). 2) Context Extraction: Every consuming microservice extracts the trace context from the incoming message headers and binds it to its local execution context (e.g., OpenTelemetry span context, MDC logging context) before invoking business logic. 3) Structured Lifecycle Logging: Every saga participant must emit structured JSON logs containing `saga_id`, `step_name`, `entity_id`, and `step_status` (`STARTED`, `COMPLETED`, `COMPENSATING`, `FAILED`). 4) Orchestrator/Audit Store: In an orchestrated saga, the coordinator persists state transitions in a centralized saga state repository. In choreography, an asynchronous audit consumer listens to all saga domain events and materializes a timeline view in a central document store or Elasticsearch, allowing engineers to query the exact timeline and state of any `saga_id`.",
        [
            "Requires propagating Saga-ID and W3C trace context via message headers across broker boundaries",
            "Instructs consumers to extract context into local tracing spans and structured logging contexts",
            "Recommends centralized timeline visualization via an orchestrator state log or an audit event consumer"
        ],
        [
            "Suggests searching application log files on individual servers by timestamp to correlate events"
        ]
    ),
    (
        "B68_1_8",
        "explain",
        "hard",
        "explain",
        ["Workflow Orchestration", "Durable Execution"],
        "Temporal / Cadence",
        "Determinism Requirement and Event History Replay",
        "In durable workflow orchestration platforms like Temporal or Cadence, workflow definitions must be strictly 'deterministic'. Why does executing non-deterministic code (such as generating random UUIDs, calling `System.currentTimeMillis()`, reading system environment variables, or executing raw HTTP requests directly inside a workflow function) corrupt workflow state during event history replay?",
        "Temporal-style orchestrators implement durable execution by maintaining an append-only Event History of state transitions in a centralized database, rather than continuously serializing entire operating system thread memory. When a workflow pauses (e.g., awaiting an external timer or human approval) or when a worker pod crashes, a replacement worker reconstructs the exact in-memory state of the workflow by 'replaying' the workflow function against the recorded Event History from step 1. If the workflow code is deterministic, re-executing it produces the exact same sequence of commands (e.g., 'ScheduleActivity A', 'StartTimer 1hr') that match the historical events. However, if the workflow function contains non-deterministic operations: 1) Calling `UUID.randomUUID()` or `System.currentTimeMillis()` will generate different values during replay than when the step was originally recorded. 2) Calling a raw HTTP request directly may return different data or fail. When the replayed code generates a command that does not match the recorded Event History, the orchestrator detects a 'Non-Deterministic Execution Error' (History Mismatch) and halts the workflow completely to prevent silent state corruption. All side effects and non-deterministic operations must be delegated to Activities or executed using workflow-provided deterministic APIs (`workflow.now()`, `workflow.sideEffect()`).",
        [
            "Explains that durable orchestrators reconstruct in-memory state by replaying workflow code against recorded event history",
            "Shows that non-deterministic functions (UUIDs, clocks, network I/O) generate differing commands during replay",
            "Identifies history mismatch errors and explains delegating side effects to activities or deterministic runtime wrappers"
        ],
        [
            "Claims that Temporal saves a complete RAM memory snapshot to disk after every line of code"
        ]
    ),
    (
        "B68_1_9",
        "concept",
        "hard",
        "concept",
        ["Workflow Orchestration", "Durable Execution"],
        "Temporal / Cadence",
        "Event History Replay Mechanics vs Checkpointing",
        "Contrast the 'Event History Replay' execution model used by Temporal with the traditional 'Database State Checkpointing' model used by traditional task engines (like Celery or Airflow). What are the tradeoffs in developer experience, storage scaling, and memory efficiency?",
        "Traditional Database State Checkpointing (Celery/Airflow): 1) Mechanics: The engine stores a row in a relational database for each task and updates a `status` column (`PENDING`, `RUNNING`, `SUCCESS`) as steps finish. 2) Developer Experience: Developers must manually manage state persistence, write explicit state-machine transitions, and glue together discrete tasks via DAG definitions or callback queues. If a task fails mid-execution, intermediate local variables are lost unless explicitly saved to external storage. 3) Tradeoffs: Simple to inspect via SQL, but complex workflows with nested loops, conditional branches, and timers require cumbersome state machines. Temporal Event History Replay: 1) Mechanics: Developers write standard sequential code with loops, local variables, and conditionals. The platform intercepts blocking calls and records their outcomes in an append-only event log. On recovery, the code is replayed from the beginning, reconstructing local variables up to the point of failure. 2) Developer Experience: Clean, idiomatic code where durable timers and retries feel like standard language primitives without manual database plumbing. 3) Tradeoffs: Workflows with thousands of loop iterations accumulate massive event histories, requiring periodic `Continue-As-New` calls to truncate history; and developers must adhere to strict determinism constraints.",
        [
            "Contrasts discrete DB status updates with replay of procedural code against append-only event history",
            "Highlights Temporal's superior developer experience (idiomatic code, preserved local variables) vs manual DAG/callback plumbing",
            "Identifies event history growth and determinism constraints as the primary tradeoffs of replay-based orchestration"
        ],
        [
            "Claims Celery replays code from event history while Temporal uses MySQL table rows for each step"
        ]
    ),
    (
        "B68_1_10",
        "implement",
        "medium",
        "implement",
        ["Workflow Orchestration", "Fault Tolerance"],
        "Temporal / Cadence",
        "Activity Heartbeats and Worker Death Detection",
        "In a durable workflow system, an activity executes a long-running video transcoding task that takes 4 hours. If the worker machine running the activity suddenly loses power, how do Activity Heartbeats allow the orchestrator to detect the failure within 30 seconds rather than waiting for the entire 4-hour execution timeout to elapse?",
        "If an activity only defines an `ExecutionTimeout` of 4 hours without heartbeats, the orchestrator cannot distinguish between an activity that is working normally and one whose worker machine died; it must wait the entire 4 hours before marking the activity failed and rescheduling it. To resolve this: 1) Define a short `HeartbeatTimeout` (e.g., 30 seconds) on the activity options alongside the 4-hour `ScheduleToCloseTimeout`. 2) Inside the activity implementation, periodically invoke the runtime's heartbeat API (e.g., `activity.RecordHeartbeat(progressPercentage)`) every 10 seconds during the transcoding loop. 3) The orchestrator resets its internal countdown timer upon receiving each heartbeat. 4) If the worker machine loses power or crashes, heartbeats stop. Once 30 seconds elapse without a heartbeat, the orchestrator detects worker failure, cancels the dead activity instance, and immediately reschedules the activity on a healthy worker. 5) Furthermore, the new worker can retrieve the last reported heartbeat details (e.g., last processed video frame) to resume processing rather than restarting from frame 0.",
        [
            "Explains configuring a short HeartbeatTimeout (e.g., 30s) alongside a long execution timeout",
            "Requires periodically calling RecordHeartbeat inside the running activity loop",
            "Highlights immediate failure detection upon missed heartbeats and the ability to resume from checkpointed heartbeat details"
        ],
        [
            "Suggests opening an SSH session from the orchestrator to ping the worker process every second"
        ]
    ),
    (
        "B68_1_11",
        "scenario",
        "hard",
        "scenario",
        ["Workflow Orchestration", "API Evolution"],
        "Temporal / Cadence",
        "Workflow Versioning and In-Flight History Incompatibility",
        "You have 50,000 long-running workflows currently in progress, each executing an insurance claim workflow that takes 30 days to complete. You deploy an update to the workflow code that reorders two activity calls and adds a new notification step. Immediately after deployment, hundreds of existing workflows throw `HistoryMismatchError` and crash. How does workflow versioning (e.g., `workflow.GetVersion`) prevent this breakage during rolling deployments?",
        "The crash occurs because in-flight workflows that reached step 2 were created under the old code. When a worker wakes up to continue an in-flight workflow, it replays the workflow code against the existing event history. Because the updated code now invokes a new notification activity where the history expected a different activity, the deterministic replay engine detects an irreconcilable conflict and aborts execution. To prevent this, you must use Workflow Versioning APIs (such as `workflow.GetVersion(changeID, minVersion, maxVersion)`): 1) Wrap the code change in a version check: `version = workflow.GetVersion('ClaimNotificationUpdate', DefaultVersion, Version1)`. 2) If `version == Version1`, execute the new code path (new activity order and notification). If `version == DefaultVersion`, execute the legacy code path. 3) During replay of an existing workflow, the orchestrator remembers that this workflow was previously tagged with `DefaultVersion` (or records the marker), so it takes the legacy branch, matching history perfectly. 4) Newly initiated workflows evaluate the version call as `Version1` and execute the new logic. 5) Only after all 50,000 legacy workflows finish (e.g., after 30 days) can the old branch and version check be safely cleaned up.",
        [
            "Explains that altering in-flight workflow code causes replay history mismatch with existing recorded events",
            "Prescribes using workflow versioning primitives (e.g., GetVersion) to branch between legacy and updated logic",
            "Clarifies that legacy branches must remain in the codebase until all older in-flight workflow executions terminate"
        ],
        [
            "Recommends terminating and deleting all 50,000 in-flight workflows and asking customers to reapply"
        ]
    ),
    (
        "B68_1_12",
        "concept",
        "easy",
        "concept",
        ["Workflow Orchestration", "API Design"],
        "Temporal / Cadence",
        "Signals vs Queries in Durable Workflows",
        "What is the difference between a 'Signal' and a 'Query' when interacting with a running durable workflow, and how do they differ regarding workflow state mutation and history recording?",
        "1) Signal: An asynchronous, write-only operation sent to a running workflow to deliver external events or state mutations (e.g., a user clicking 'Approve Order', an external payment webhook arriving, or a cancellation request). When a signal is sent, it is appended to the workflow's Event History as a durable event (`WorkflowExecutionSignaled`). The workflow logic can react to signals by unblocking a channel, updating internal state variables, or transitioning to another phase. Because signals modify state, they participate in event history replay. 2) Query: A synchronous, read-only operation sent to inspect the current in-memory state of a running workflow without modifying it (e.g., 'What is the current status of order #123?'). Queries do NOT write events to the workflow's Event History. The orchestrator executes the query handler against the workflow's current in-memory state (replaying history up to the current point if necessary) and immediately returns the result to the caller. Queries are completely side-effect-free.",
        [
            "Defines Signal as an asynchronous state-mutating operation recorded in the workflow event history",
            "Defines Query as a synchronous, read-only inspection that does not write to event history",
            "Contrasts the durable event generation of signals with the side-effect-free nature of queries"
        ],
        [
            "Claims that Queries are used to send payments and Signals are used to read database tables"
        ]
    ),
    (
        "B68_1_13",
        "explain",
        "medium",
        "explain",
        ["Workflow Orchestration", "Operating Systems"],
        "Temporal / Cadence",
        "Durable Timers vs In-Memory Sleep",
        "How do durable workflow orchestrators implement workflow sleep statements (e.g., `workflow.sleep(30 * 24 * time.Hour)`) without holding open OS threads, memory allocations, or database connections for 30 days?",
        "In a standard backend service, calling `Thread.sleep(30 days)` or `time.Sleep()` consumes an operating system thread or keeps a memory-allocated goroutine/coroutine suspended in RAM, which fails if the process restarts or the server reboots. In a durable workflow engine: 1) When `workflow.sleep(30 days)` is executed, the workflow runtime intercepts the call and emits a `StartTimer` command to the central orchestration cluster. 2) The cluster records a durable `TimerStarted` event with an absolute expiration timestamp in its persistent database (e.g., Cassandra, PostgreSQL). 3) The worker process then completely unloads the workflow from memory and releases its OS thread back to the thread pool. The workflow consumes zero RAM, zero CPU, and zero network connections during the 30-day wait. 4) The orchestration cluster maintains time-indexed queues (or durable timer partitions). When the 30-day deadline arrives, the cluster fires a `TimerFired` event and places a task on the workflow task queue. 5) An available worker pulls the task, replays the event history, unblocks the sleep statement, and continues executing subsequent workflow code.",
        [
            "Explains that workflow sleep emits a StartTimer command persisted with a future timestamp in the cluster DB",
            "Highlights that workers unload the workflow entirely, consuming zero RAM, CPU, or OS threads during the timer period",
            "Describes time-indexed cluster queues waking the workflow via task queues upon deadline expiration"
        ],
        [
            "Assumes the worker machine keeps a background thread looping with Thread.sleep for the entire 30 days"
        ]
    ),
    (
        "B68_1_14",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Workflow Orchestration", "Architecture"],
        "Temporal / Cadence",
        "Child Workflows vs Activities",
        "When designing a distributed business process in a workflow engine, what are the architectural tradeoffs of modeling a sub-process as a 'Child Workflow' versus modeling it as a series of 'Activities'?",
        "Activities: 1) Nature: A single, non-durable unit of work executed by a worker (e.g., sending an email, querying a DB, making a single HTTP call). Activities cannot contain workflows or manage their own event histories. 2) Tradeoffs: Very lightweight, low overhead, and fast execution. However, they lack workflow orchestration features—an activity cannot pause for external signals, cannot execute durable multi-day timers, and must fit within standard timeout limits. Child Workflows: 1) Nature: An independent, durable workflow spawned and supervised by a parent workflow. 2) Advantages: Owns its own independent Event History, meaning high-frequency sub-processes do not bloat the parent's history limit. Can contain complex multi-step branching, handle its own signals/queries, manage separate retries, and run across different task queues or worker pools. 3) Disadvantages: Higher scheduling overhead and latency (requires multiple cluster state transitions). Parent-child lifecycle management adds complexity (e.g., deciding whether child workflows should abort or continue running if the parent workflow is canceled).",
        [
            "Defines activities as lightweight, single-action units of work without independent event histories",
            "Defines child workflows as independent durable entities capable of complex branching, timers, and separate event histories",
            "Analyzes the tradeoff: performance/simplicity of activities vs isolation, independent lifecycle, and history sizing of child workflows"
        ],
        [
            "Claims child workflows are executed on client browsers while activities execute in backend servers"
        ]
    ),
    (
        "B68_1_15",
        "diagnose",
        "hard",
        "debugging",
        ["Workflow Orchestration", "Performance Tuning"],
        "Temporal / Cadence",
        "Unbounded Event History Bloat and Continue-As-New",
        "A fleet of IoT device manager workflows running in Temporal monitor incoming sensor telemetry in an infinite loop: `while(true) { event = receiveSignal(); process(event); }`. After 3 months in production, the orchestrator begins experiencing severe performance degradation, high database I/O, worker out-of-memory errors, and warnings that event history has exceeded 50,000 events. What is the root cause, and how does the `Continue-As-New` pattern resolve it?",
        "The root cause is Unbounded Event History Growth. Durable workflow engines append every state transition, signal, and activity completion to the workflow's Event History. In an infinite loop, receiving signals and executing steps continuously appends tens of thousands of events. As history grows: 1) Every time a worker evaluates a task, the cluster must load and transmit megabytes of JSON event history across the network. 2) The worker must replay all 50,000+ historical events from scratch in memory, causing CPU spikes, high memory allocation, and GC pauses. 3) Eventually, the history exceeds platform safety limits (typically 50,000 events or 50MB), leading to forced termination. Resolution: Implement the `Continue-As-New` pattern. The workflow tracks its iteration count or event size. Once it reaches a safe threshold (e.g., every 1,000 iterations or every 24 hours), the workflow calls `workflow.ContinueAsNew(currentAccumulatedState)`. This atomically terminates the current workflow execution and starts a completely fresh execution with an empty event history, carrying over only the essential state arguments, preventing history bloat while preserving infinite operational continuity.",
        [
            "Identifies unbounded append-only event history accumulation in infinite loops as the root cause of performance degradation",
            "Explains that massive event histories cause network serialization bottlenecks and slow worker replay times",
            "Prescribes the Continue-As-New pattern to atomically restart execution with clean event history while carrying over state"
        ],
        [
            "Recommends manually running an SQL DELETE query on the Temporal event history database table"
        ]
    ),
    (
        "B68_1_16",
        "concept",
        "medium",
        "concept",
        ["Distributed Systems", "Consensus"],
        "Raft / Paxos",
        "Idempotent Application of Replicated State Machine Logs",
        "In consensus algorithms like Raft or Paxos, log entries are replicated across nodes before being committed. However, during network partitions and leader failovers, a newly elected leader may replay previously committed log entries to catch up lagging followers. Why must the state machine applying these log entries be strictly idempotent, and what metadata is required to guarantee exactly-once state transitions?",
        "Consensus algorithms guarantee total ordering and replication of log entries, but they do NOT inherently prevent client retries or duplicate command proposals from reaching the log. If a client submits a command `Transfer $10`, the leader proposes it, but the client experiences a timeout and resubmits the same command, both commands could be replicated. Furthermore, during node recovery or log compaction replay, the state machine applies entries sequentially. If applying a log entry modifies balance (`balance += 10`), re-applying the log entry or applying duplicate proposals would corrupt business state. To guarantee exactly-once application at the state machine level: 1) Every client request must carry a unique `ClientId` and a monotonically increasing `SequenceNumber` (or unique request UUID). 2) The state machine maintains a session/deduplication table tracking the latest sequence number and response for each client. 3) When an entry is about to be applied, the state machine verifies whether `entry.SequenceNumber <= clientSession.LastAppliedSequence`. If it was already applied, the state machine skips state mutation and returns the cached response, ensuring deterministic, idempotent state execution.",
        [
            "Explains that consensus logs ensure message ordering but do not prevent duplicate client command submissions",
            "Highlights that non-idempotent state mutations (e.g. balance increments) cause data corruption upon duplicate application",
            "Specifies tracking ClientId and monotonic SequenceNumbers in a state machine session table to filter duplicates"
        ],
        [
            "Claims Raft automatically deduplicates bank transactions without requiring application-level logic"
        ]
    ),
    (
        "B68_1_17",
        "explain",
        "medium",
        "explain",
        ["Database Architecture", "Storage Engines"],
        "Write-Ahead Logging (WAL)",
        "Write-Ahead Logging in Application-Level Durable Queues",
        "When building a high-throughput, embedded message queue or background job worker in Java or Go, why is writing incoming jobs to a sequential Write-Ahead Log (WAL) with `fsync` significantly faster than writing directly to a traditional relational database or indexed B-Tree, and how does it guarantee durability?",
        "Writing to a traditional relational database or indexed B-Tree involves random disk I/O: the engine must find data pages, update internal node pointers, rebalance B-Tree branches, and update secondary index structures scattered across disk blocks. Random I/O is physically slow and incurs significant write amplification. In contrast, a Write-Ahead Log (WAL): 1) Uses pure Sequential Append-Only I/O. New incoming messages are serialized and appended directly to the end of an open log file. Operating systems and modern NVMe/SSD controllers optimize sequential writes with massive write throughput. 2) Durability is guaranteed by issuing an `fsync()` (or synchronous flush) call immediately after appending the record, ensuring data transitions from OS page cache directly onto non-volatile hardware storage before acknowledging the producer. 3) If the application crashes, the in-memory state (e.g., job queue pointers) is lost, but during reboot, the queue engine sequentially scans the WAL from the last checkpoint to instantly reconstruct the exact queue state without data loss.",
        [
            "Contrasts sequential append-only disk I/O with random I/O and index updates of B-Trees",
            "Explains the role of fsync() in flushing OS page cache to physical disk for durability guarantees",
            "Describes crash recovery via sequential WAL replay from the last committed checkpoint"
        ],
        [
            "Claims WAL is faster because it stores records entirely in RAM without ever touching physical disk"
        ]
    ),
    (
        "B68_1_18",
        "concept",
        "easy",
        "concept",
        ["Distributed Systems", "Concurrency"],
        "Distributed Coordination",
        "Leases vs Distributed Locks with Mutual Exclusion",
        "What is the difference between a traditional 'Distributed Lock' and a 'Lease' in distributed coordination systems (like etcd, Consul, or ZooKeeper), and why do leases prevent catastrophic resource lockup when a worker node crashes?",
        "A traditional Distributed Lock without expiration grants exclusive ownership of a resource until the holder explicitly sends a 'release' or 'unlock' command. The severe failure mode: if the worker process holding the lock suddenly crashes, suffers an unhandled exception, loses network connectivity, or experiences a kernel panic before releasing the lock, the lock remains held indefinitely. No other node can ever acquire the resource, causing a permanent system deadlock. A Lease is a time-bounded distributed lock with a Time-To-Live (TTL). When a worker acquires a lease (e.g., for 10 seconds), it is granted exclusive access, but it must continuously send background 'keep-alive' heartbeats to the coordination cluster to renew the lease. If the worker crashes or loses network connectivity, heartbeats cease. Once the 10-second TTL expires, the coordination cluster automatically revokes the lease and frees the resource, allowing standby workers to safely take over without human intervention.",
        [
            "Defines traditional locks as indefinite until explicitly unlocked, risking permanent deadlocks upon worker crash",
            "Defines leases as time-bounded locks with TTLs requiring continuous heartbeats",
            "Explains automatic resource recovery upon expiration when a crashed worker stops renewing heartbeats"
        ],
        [
            "Claims leases are financial agreements signed between cloud hosting providers"
        ]
    ),
    (
        "B68_1_19",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Distributed Systems", "Distributed Transactions"],
        "Two-Phase Commit (2PC)",
        "The Blocking Coordinator Problem in Two-Phase Commit",
        "Two-Phase Commit (2PC) guarantees strict ACID atomicity across distributed databases. However, it is rarely used in high-throughput cloud microservices due to the 'Blocking Coordinator Problem'. Explain what happens when a coordinator crashes after participants vote 'PREPARE', and why participants cannot unilaterally decide to abort or commit.",
        "In 2PC, Phase 1 requires all participants to vote `VOTE_COMMIT` or `VOTE_ABORT`. Once a participant votes `VOTE_COMMIT`, it locks all local database rows and enters an uncertain ('in-doubt') state, yielding control to the coordinator. The Blocking Coordinator Problem occurs if the coordinator node crashes immediately after collecting the votes but *before* broadcasting the final `GLOBAL_COMMIT` or `GLOBAL_ABORT` decision: 1) The participants cannot unilaterally abort because the coordinator might have sent `GLOBAL_COMMIT` to another participant before crashing, which would cause split-brain inconsistency. 2) The participants cannot unilaterally commit because another participant might have voted `VOTE_ABORT`, which would also cause inconsistency. 3) Consequently, all participants remain completely blocked, holding database locks and holding open transactions indefinitely until the coordinator recovers and reads its write-ahead log. In cloud environments where latency and transient node failures are frequent, this causes cascading connection pool exhaustion and system-wide freezes, making 2PC impractical compared to eventual consistency or Sagas.",
        [
            "Explains the 'in-doubt' state where participants have voted commit and locked resources",
            "Identifies that a coordinator crash leaves participants unable to unilaterally commit or abort without risking inconsistency",
            "Highlights the consequence: indefinitely held database locks, connection pool exhaustion, and system-wide blocking"
        ],
        [
            "Claims participants can safely vote amongst themselves using HTTP GET requests to finish the commit"
        ]
    ),
    (
        "B68_1_20",
        "scenario",
        "medium",
        "scenario",
        ["Distributed Systems", "Data Consistency"],
        "Distributed Databases",
        "Partial Commit Recovery across Multi-Partition Writes",
        "Your backend handles user registration by writing to two independent database shards: Shard A (storing the user authentication record) and Shard B (storing the user profile and initial billing ledger). Your application executes both writes asynchronously. Shard A commits successfully, but Shard B throws a network timeout. How do you architect partial commit recovery to prevent orphaned authentication records without using distributed locks?",
        "When writing across independent uncoordinated database shards without 2PC, partial failures are inevitable. To handle this without distributed locks: 1) Two-Phase State Pattern: Make the write to Shard A conditional and provisional. Insert the authentication record with a status of `PENDING_ACTIVATION` rather than `ACTIVE`. 2) Asynchronous Outbox / Compensation: If the write to Shard B fails, the application asynchronously marks Shard A for deletion/cleanup or publishes a `RegistrationAborted` event to a retry queue to remove the provisional record. 3) Background Reconciliation Sweeper: Implement a scheduled reconciliation worker that queries Shard A for records in `PENDING_ACTIVATION` older than a threshold (e.g., 5 minutes). The sweeper checks Shard B: if the corresponding profile exists, it promotes Shard A to `ACTIVE`; if Shard B has no record, it cleans up the orphaned record on Shard A. 4) Idempotent User Retry: If the user retries registration with the same email, the registration endpoint detects the `PENDING_ACTIVATION` state on Shard A, attempts to complete the missing write to Shard B, and activates the account upon success.",
        [
            "Uses a provisional status (e.g., PENDING_ACTIVATION) on the first shard rather than an immediate active state",
            "Implements an asynchronous reconciliation sweeper to detect and resolve orphaned records based on timeouts",
            "Ensures client retries can idempotently complete missing secondary shard writes"
        ],
        [
            "Suggests wrapping both database shards in a single Python thread lock"
        ]
    )
]

def run_batch():
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        # q[7] is question text, q[8] is expected answer
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
            "applicable_roles": ["Distributed Systems Engineer", "Software Engineer"],
            "primary_skill": q[4][0],
            "skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": q[5],
            "topic": q[6],
            "category": "Backend Engineering",
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
    print(f"Batch: 68 Part 1")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
