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
        "B68_2_1",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Message Processing", "Distributed Systems"],
        "Apache Kafka",
        "Cooperative Sticky Rebalance vs Eager Rebalancing",
        "In Apache Kafka consumer groups, what is the architectural difference between the legacy 'Eager Rebalance Protocol' and the 'Cooperative Sticky Rebalance Protocol', and how does cooperative rebalancing eliminate consumer group stop-the-world processing freezes during rolling deploys?",
        "Eager Rebalancing Protocol: 1) Mechanism: Whenever a consumer joins or leaves a group (e.g., during a rolling deployment of consumer pods), the group coordinator forces ALL consumers in the group to immediately revoke ownership of ALL their assigned partitions, stop consuming entirely, and send a JoinGroup request. 2) Impact: This causes a cluster-wide 'stop-the-world' pause where message consumption halts completely across all partitions while the coordinator recomputes and reassigns partitions from scratch. Under large consumer groups, this causes severe latency spikes and consumer lag accumulation. Cooperative Sticky Rebalancing Protocol: 1) Mechanism: Rebalancing occurs in two non-blocking phases (incremental rebalancing). In Phase 1, consumers report their current partition assignments without revoking them. The leader identifies only the minimal subset of partitions that must move to new consumers. 2) Consumers continue actively processing messages on all unaffected partitions throughout the rebalance. 3) In Phase 2, only consumers holding partitions that must be migrated revoke those specific partitions, allowing them to be reassigned to the new consumer. 4) Result: 90%+ of partitions continue streaming uninterrupted, completely eliminating group-wide stop-the-world halts during rolling restarts.",
        [
            "Explains that eager rebalancing forces all consumers to revoke all partitions, halting consumption cluster-wide",
            "Explains that cooperative sticky rebalancing performs incremental two-phase rebalancing where unaffected partitions continue processing",
            "Identifies the elimination of stop-the-world latency spikes during rolling deployments as the primary benefit"
        ],
        [
            "Claims cooperative rebalancing means consumers negotiate partitions via peer-to-peer WebSockets without a broker coordinator"
        ]
    ),
    (
        "B68_2_2",
        "diagnose",
        "hard",
        "debugging",
        ["Message Processing", "Observability"],
        "Apache Kafka",
        "Consumer Lag Decomposition: LEO vs Committed Offset",
        "A consumer group processing financial transactions from a 16-partition Kafka topic shows a rapidly growing consumer lag of 500,000 messages. You inspect the metrics and discover that 15 partitions have a lag of 0, while Partition 7 alone has 500,000 lag. You check the consumer pod handling Partition 7; its CPU is at 5% and memory is stable. Explain how you diagnose whether the root cause is partition key skew, a slow downstream poison message, or a thread deadlock, and how you resolve it.",
        "To systematically diagnose Partition 7's localized lag: 1) Metric Analysis (LEO vs Committed Offset): Compare the Log End Offset (LEO) and Current Offset of Partition 7. If LEO is increasing rapidly while Committed Offset is also advancing at a normal rate, the root cause is 'Key Skew'—a specific high-volume merchant or tenant key is hashing exclusively to Partition 7, overwhelming a single consumer core with disproportionate throughput. 2) If Committed Offset is completely frozen (not advancing at all) while LEO increases, the consumer thread is stuck. 3) Inspect Consumer Thread State: Take a thread dump or check logs for Partition 7's worker. If the thread is blocked on an un-timed external HTTP/database call or in a synchronization deadlock, the consumer cannot complete processing to commit offsets. If the consumer is repeatedly fetching the same malformed message, throwing an unhandled exception, and failing before commit, it is stuck in an infinite retry poison-pill loop. Resolution: If Key Skew: Salting the message key or redesigning the partition hashing key to distribute the high-volume entity across multiple partitions. If Poison Pill/Stuck Thread: Implement strict socket timeouts on downstream calls, route the failing message to a dead-letter topic, and commit the offset to unblock Partition 7.",
        [
            "Differentiates key skew (offset advancing but LEO growing faster due to high-volume key) from frozen consumer (offset not advancing)",
            "Diagnoses thread blockage on downstream dependencies or poison-pill exception loops",
            "Prescribes partition key salting or DLQ routing and offset commit to unblock consumption"
        ],
        [
            "Recommends adding 50 more consumer pods to the consumer group without checking partition counts"
        ]
    ),
    (
        "B68_2_3",
        "explain",
        "medium",
        "explain",
        ["API Evolution", "Data Serialization"],
        "Schema Registry / Avro / Protobuf",
        "Schema Compatibility Modes in Event-Driven Architecture",
        "When evolving event schemas in an event-driven architecture using Confluent Schema Registry or Protobuf, what is the architectural difference between 'BACKWARD Compatibility' and 'FORWARD Compatibility', and which mode is required when consumers must be updated before producers versus producers before consumers?",
        "1) BACKWARD Compatibility: Means that a new schema version can be used to deserialize data written with the previous schema version. Required deployment order: Consumers MUST be upgraded before Producers. If consumers are running the new schema first, they can successfully read old events still being emitted by old producers. Once all consumers are upgraded, producers can safely begin emitting events with the new schema. Rule: New schema can add optional fields (with defaults) or delete optional fields. 2) FORWARD Compatibility: Means that data written with a new schema version can be read by consumers running the old schema version. Required deployment order: Producers MUST be upgraded before Consumers. Producers begin emitting the new schema version, and legacy consumers simply ignore newly added unknown fields without crashing. Rule: New schema can delete optional fields, but cannot add required fields. 3) FULL Compatibility: Both backward and forward compatible. Consumers and producers can be deployed in any arbitrary order without breaking event processing.",
        [
            "Defines BACKWARD compatibility as new consumers reading old producer events (deploy consumers first)",
            "Defines FORWARD compatibility as old consumers reading new producer events (deploy producers first)",
            "Identifies FULL compatibility as permitting arbitrary deployment order"
        ],
        [
            "Claims backward compatibility means producers can read events written by consumers"
        ]
    ),
    (
        "B68_2_4",
        "scenario",
        "medium",
        "scenario",
        ["Message Processing", "Fault Tolerance"],
        "Distributed Message Queues",
        "Dead-Letter Processing Ladders vs In-Process Sleep",
        "A backend worker consumes messages from an SQS queue. If a downstream external payment gateway returns an HTTP 503 Service Unavailable, a developer writes `Thread.sleep(60000)` inside the consumer loop to wait 60 seconds before retrying the message. Explain why in-process sleeping inside message consumers is an operational disaster, and how to architect a 'Retry Backoff Topic Ladder'.",
        "Why In-Process Sleeping is an Operational Disaster: 1) Blocking the consumer thread with `Thread.sleep(60s)` wastes thread pool resources and stops the consumer from processing hundreds of healthy messages waiting in the queue for other merchants. 2) If the queue's visibility timeout (e.g., 30s) is shorter than the sleep duration, the message becomes visible to other workers while the first worker is still sleeping, causing duplicate concurrent executions and worker stampedes. 3) If the worker process restarts or scales down during sleep, the in-flight state is lost. Retry Backoff Topic Ladder Architecture: 1) Instead of sleeping in-process, when a transient error occurs, the consumer immediately commits the offset on the main queue and republishes the message to a delayed retry topic (e.g., `orders-retry-1m`). 2) The delayed topic uses native broker delay mechanisms (e.g., SQS DelaySeconds, RabbitMQ dead-letter TTL with exchange routing, or Kafka scheduled buckets). 3) Messages progress through a ladder: `retry-1m` -> `retry-5m` -> `retry-15m`. 4) If retries exceed a maximum attempt threshold (e.g., 5 attempts), the message is routed to the final Dead-Letter Queue (DLQ) for alerting and manual inspection. The main worker thread never blocks and continues processing healthy traffic at full line speed.",
        [
            "Identifies that in-process sleep blocks consumer throughput and risks visibility timeout expiration races",
            "Designs an asynchronous retry topic ladder (e.g., retry-1m, retry-5m) using broker delay mechanisms",
            "Ensures the main consumer acknowledges or commits the original message immediately to maintain unblocked throughput"
        ],
        [
            "Recommends increasing the Thread.sleep duration to 10 minutes to give the gateway more time to recover"
        ]
    ),
    (
        "B68_2_5",
        "implement",
        "hard",
        "implement",
        ["Message Processing", "Concurrency"],
        "Apache Kafka",
        "Consumer Backpressure and Partition Pausing",
        "In a high-throughput Kafka consumer written in Java or Go, worker threads process heavy CPU-intensive tasks using an internal thread pool of 20 workers. The Kafka polling thread polls batches of 500 records. When the internal thread pool's task queue fills up, if the polling thread blocks or sleeps waiting for free workers, Kafka's group coordinator considers the consumer dead and kicks it out of the group (`max.poll.interval.ms` exceeded). How do you implement non-blocking consumer backpressure using `consumer.pause()` and `consumer.resume()`?",
        "To prevent coordinator kick-outs while managing internal worker backpressure: 1) Root Cause: Kafka requires the main consumer polling thread to continuously invoke `consumer.poll()` within `max.poll.interval.ms`. If the polling thread blocks waiting for internal worker pool capacity, the heartbeat thread may keep the socket alive, but the coordinator declares the consumer unresponsive and triggers a disruptive group rebalance. 2) Implementation: When the internal worker thread pool's queue depth exceeds a high-water mark (e.g., 80% capacity), the polling thread calls `consumer.pause(assignedPartitions)`. 3) While paused, the consumer loop continues calling `consumer.poll(timeout)` regularly. In paused mode, `poll()` returns 0 records immediately, satisfying the `max.poll.interval.ms` heartbeat contract with the broker without fetching any new data into memory. 4) As worker threads complete tasks and the internal queue drops below a low-water mark (e.g., 20% capacity), the polling thread calls `consumer.resume(assignedPartitions)`. 5) On the subsequent `poll()` call, the consumer resumes fetching records from the broker, achieving smooth, native backpressure without risking rebalance storms.",
        [
            "Explains that blocking the polling thread causes max.poll.interval.ms expiration and group rebalance evictions",
            "Uses consumer.pause() to halt message fetching while continuing to invoke poll() to maintain coordinator liveness",
            "Uses consumer.resume() once internal worker queue drops below the low-water mark threshold"
        ],
        [
            "Recommends setting max.poll.interval.ms to Integer.MAX_VALUE to disable rebalancing"
        ]
    ),
    (
        "B68_2_6",
        "explain",
        "medium",
        "explain",
        ["Message Processing", "Distributed Systems"],
        "RabbitMQ / SQS / Redis",
        "Delayed Message Processing Architectures",
        "Your backend needs to schedule 10 million reminders to be delivered at specific future times (varying from 5 minutes to 30 days in the future). Why is polling a relational database table with `SELECT * FROM tasks WHERE trigger_at <= NOW()` an anti-pattern at scale, and how do you architect delayed message processing using a message broker or sorted set?",
        "Why Database Polling Fails: 1) Polling a table with millions of rows every second causes severe database CPU spikes, constant index scans, lock contention, and high I/O. 2) As concurrency scales across multiple backend pollers, workers compete for rows, requiring `SELECT FOR UPDATE SKIP LOCKED`, which strains the DB buffer pool and degrades write performance. Modern Architectural Alternatives: 1) Redis Sorted Set (ZSET): Insert tasks with `ZADD reminders <timestamp_unix> <task_id>`. A lightweight poller uses `ZRANGEBYSCORE reminders -inf <current_unix> LIMIT 100` to fetch due tasks with $O(\log N + M)$ efficiency, then atomically removes them using `ZREM` or Lua scripts, offloading the relational database. 2) RabbitMQ Delayed Message Exchange (x-delayed-message): Uses an Erlang-based timer wheel plugin. Messages are published with an `x-delay` header; RabbitMQ holds the message until the delay expires before routing it to the destination queue. 3) SQS Delay Queues / EventBridge Scheduled Rules: For AWS architectures, utilizing native broker-managed delay features or Step Functions execution eliminates custom polling infrastructure entirely.",
        [
            "Identifies database CPU spikes, lock contention, and index churn caused by continuous polling",
            "Designs a Redis ZSET architecture using Unix timestamps as scores for O(log N) due-task extraction",
            "Mentions native broker delay mechanisms (RabbitMQ delayed exchange, SQS delay queues, EventBridge)"
        ],
        [
            "Suggests creating a new database table for every minute of the day"
        ]
    ),
    (
        "B68_2_7",
        "concept",
        "easy",
        "concept",
        ["Message Processing", "Architecture"],
        "Message Brokers",
        "Strict Priority Queues vs Weighted Fair Queuing",
        "What is the operational risk of using a 'Strict Priority Queue' (e.g., Priority 1 processed before Priority 2) for background jobs, and how does 'Weighted Fair Queuing' (WFQ) prevent starvation of low-priority tasks?",
        "1) Operational Risk of Strict Priority Queuing: Under strict priority, workers always process higher-priority messages before touching lower-priority messages. If traffic surges and high-priority messages arrive continuously at or above the worker pool's processing capacity, lower-priority messages (e.g., weekly digest emails, analytics syncs) will NEVER be processed. They suffer from 'Starvation', sitting in the queue for days until timeouts or TTL expirations occur. 2) Weighted Fair Queuing (WFQ): Instead of absolute preemption, WFQ assigns bandwidth/worker capacity ratios to different priority classes. For example, a 70/20/10 weight allocation ensures that for every 10 jobs processed, workers consume 7 High-priority, 2 Medium-priority, and 1 Low-priority job. Even during massive high-priority surges, low-priority queues are guaranteed forward progress and bounded latency.",
        [
            "Explains that strict priority queues cause indefinite starvation of lower-priority jobs during high-priority surges",
            "Defines Weighted Fair Queuing as allocating proportional processing capacity across priority levels",
            "Highlights that WFQ guarantees forward progress for low-priority queues even under heavy load"
        ],
        [
            "Claims strict priority queues automatically delete low-priority jobs to speed up the server"
        ]
    ),
    (
        "B68_2_8",
        "scenario",
        "medium",
        "scenario",
        ["Message Processing", "Data Consistency"],
        "Apache Kafka / Stream Processing",
        "Message Replay and Offset Rewind Post-Bugfix",
        "A stream processing service computes real-time merchant account balances from Kafka payment events. A critical bug deployed 48 hours ago caused all currency conversions from EUR to USD to use an inverted exchange rate, corrupting merchant balances. You deploy a bugfix. How do you execute a message replay / offset rewind in production to recalculate correct balances without creating duplicate balance adjustments or double-charging merchants?",
        "To safely execute a message replay: 1) Isolate Output Sinks: The corrected stream processor must not blindly write into the production balance ledger, as doing so would cause duplicate entries or conflicting balances with real-time operations that occurred during the 48-hour window. 2) New Consumer Group / Shadow State: Deploy the corrected application using a NEW consumer group ID (e.g., `balance-recalculator-v2`). Set the starting offset for this group back to the specific timestamp from 48 hours ago (`offsetsForTimes(48h_timestamp)`). 3) Replay to Isolated Store: Stream through the 48 hours of messages into an isolated shadow database or temporary reconciliation table, recalculating accurate running balances. 4) Delta Reconciliation: Run a reconciliation script that compares the shadow recalculation against the live production balances. For each merchant with a discrepancy, generate an explicit, auditable 'Correction Adjustment' ledger entry (`CORRECTION_ADJUSTMENT`, delta_amount) rather than overwriting historical records. 5) Cutover: Decommission the old buggy consumer group, switch real-time processing to the new pipeline, and record the reconciliation audit log.",
        [
            "Prescribes creating a new consumer group and rewinding offsets using timestamp lookup (offsetsForTimes)",
            "Processes replayed events into an isolated shadow state to prevent corrupting live production tables",
            "Generates explicit delta correction adjustment transactions rather than destructively overwriting history"
        ],
        [
            "Suggests deleting all records in the production database and rewinding the main consumer group offset"
        ]
    ),
    (
        "B68_2_9",
        "concept",
        "medium",
        "concept",
        ["Event-Driven Architecture", "Domain-Driven Design"],
        "Event Sourcing",
        "The Upcasting Pattern for Immutable Event History Migration",
        "In an event-sourced backend where events stored in an append-only event store are strictly immutable, you cannot run an SQL `UPDATE` or `ALTER TABLE` to modify historical events when business requirements change (e.g., splitting a `CustomerRegistered` event's `fullName` field into `firstName` and `lastName`). How does the 'Upcaster' (or Event Adapter) pattern solve event schema migration without modifying past events?",
        "Because historical events in an event store are immutable facts that must remain unmodified for audit and cryptographic integrity, database migration scripts are prohibited. The Upcaster (Event Adapter) pattern resolves this at the application deserialization boundary: 1) Historical events remain permanently untouched in the storage engine in their original version 1 schema. 2) An Upcaster is an in-memory transformation pipeline that intercepts raw events as they are read from the event store before they are handed to domain aggregates or projectors. 3) The Upcaster detects the version tag (e.g., `version: 1`). It executes deterministic transformation logic: extracting `fullName`, splitting it on the first whitespace into `firstName` and `lastName`, and transforming the payload into the `version: 2` domain event structure. 4) The domain model and projections only ever interact with current, up-to-date event models. 5) Upcasters can be chained sequentially ($V1 \rightarrow V2 \rightarrow V3$), ensuring seamless backward compatibility across multiple years of schema evolution without touching raw historical records.",
        [
            "Affirms that historical events in an event store must remain physically immutable on disk",
            "Explains that Upcasters transform older event versions in-memory during deserialization before domain processing",
            "Describes chaining upcasters (V1 -> V2 -> V3) to present a uniform, modern event schema to the domain model"
        ],
        [
            "Recommends writing a script to decrypt the event store and rewrite raw past event JSON payloads"
        ]
    ),
    (
        "B68_2_10",
        "explain",
        "hard",
        "explain",
        ["Message Processing", "Distributed Transactions"],
        "Apache Kafka",
        "Exactly-Once Processing (EOP) in Kafka Read-Process-Write Loops",
        "How does Apache Kafka's Transactional API achieve 'Exactly-Once Processing' (EOP) across a read-process-write loop (reading from Topic A, updating state, and writing to Topic B), and how does the Transaction Coordinator coordinate with the `__transaction_state` topic and markers?",
        "Kafka EOP across read-process-write loops guarantees that output messages are produced to Topic B and consumed offsets are committed to Topic A atomically—either both succeed or neither takes effect. Mechanics: 1) Transactional ID & Epoch: The producer initializes with a unique `transactional.id`. The Transaction Coordinator assigns an epoch, fencing off any zombie producer instances. 2) Adding Partitions: When the producer begins a transaction (`beginTransaction`), it registers output partitions (Topic B) and consumer group offset partitions with the Transaction Coordinator, which logs them to the internal `__transaction_state` topic. 3) Atomic Offset Commit: Instead of committing offsets directly to `__consumer_offsets`, the consumer sends offsets to the producer, which writes them to the Transaction Coordinator via `sendOffsetsToTransaction`. 4) Two-Phase Commit with Control Markers: When `commitTransaction` is called: Phase 1: The coordinator writes a `PREPARE_COMMIT` record to `__transaction_state`. Phase 2: The coordinator writes a special 'Commit Marker' (control message) to all user topic partitions (Topic B and `__consumer_offsets`). 5) Downstream Read Isolation: Downstream consumers configured with `isolation.level=read_committed` buffer messages and only expose them to the application once the Commit Marker is observed, filtering out aborted transactions and uncommitted data completely.",
        [
            "Explains atomic coordination of output topic writes and consumed offset commits via a Transaction Coordinator",
            "Describes the use of Commit Markers written to topic partitions to signal transaction completion",
            "Identifies consumer isolation.level=read_committed filtering uncommitted or aborted messages until commit markers appear"
        ],
        [
            "Claims Kafka guarantees exactly-once by relying on TCP sequence numbers across client networks"
        ]
    ),
    (
        "B68_2_11",
        "implement",
        "hard",
        "implement",
        ["API Security", "Webhook Architecture"],
        "Webhooks / Cryptography",
        "Webhook Replay Attack Prevention: HMAC and Timestamp Windows",
        "You are designing a public Webhook dispatch service for a fintech platform. You already sign webhook payloads using HMAC SHA-256 (`X-Signature-SHA256: hmac_sha256(secret, payload)`). However, a security auditor proves that an attacker intercepting HTTPS traffic (or an untrusted proxy) can capture a valid webhook and replay it 12 hours later, triggering duplicate bank deposits. How do you redesign the webhook signature scheme and subscriber verification protocol to prevent replay attacks?",
        "To eliminate replay attacks, the webhook payload must be cryptographically bound to a short time window and a unique identifier: 1) Dispatcher Implementation: The dispatcher includes a current Unix epoch timestamp header (`X-Webhook-Timestamp: 1712574000`) and a unique delivery ID (`X-Webhook-ID: uuid`). 2) Signature Canonicalization: The HMAC signature must NOT be computed over the raw payload alone. Instead, sign the concatenated string of timestamp and payload: `signature = HMAC_SHA256(secret, timestamp + '.' + raw_body)`. Include this signature in `X-Webhook-Signature`. 3) Subscriber Verification Protocol: Step A (Tolerance Check): The subscriber reads `X-Webhook-Timestamp` and compares it to its current system time (`Math.abs(currentTime - webhookTime)`). If the difference exceeds a strict tolerance window (e.g., 5 minutes), the request is rejected immediately. This renders 12-hour-old replayed packets invalid. Step B (Cryptographic Check): The subscriber recomputes the HMAC over `webhookTime + '.' + raw_body` and performs a constant-time comparison (`crypto.timingSafeEqual`) against `X-Webhook-Signature`. Step C (Nonce/ID Deduplication): Within the 5-minute validity window, the subscriber records `X-Webhook-ID` in a Redis cache with a 5-minute TTL. If an attacker replays a valid packet within the 5-minute window, the duplicate ID check blocks it.",
        [
            "Signs the concatenated timestamp and raw body to prevent payload tampering and timestamp forging",
            "Enforces a strict subscriber-side timestamp tolerance window (e.g., 5 minutes) to invalidate stale replays",
            "Combines timestamp validation with Redis nonce/ID deduplication to prevent replays within the tolerance window"
        ],
        [
            "Claims HTTPS encryption makes replay attacks impossible so timestamps are unnecessary"
        ]
    ),
    (
        "B68_2_12",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Webhook Architecture", "Reliability"],
        "Retry Strategies",
        "Exponential Backoff with Full Jitter for Webhook Retries",
        "Your webhook dispatch infrastructure retries failed subscriber webhooks using standard exponential backoff (`delay = initial_delay * 2^attempt`). During a major outage at a popular SaaS webhook receiver (e.g., an integration platform hosting 10,000 subscriber endpoints), the receiver recovers. Suddenly, your webhook dispatcher crashes the receiver again within 3 seconds of recovery. Why does standard exponential backoff cause this synchronized thundering herd, and how does 'Full Jitter' resolve it?",
        "Standard Exponential Backoff Problem: When the receiver platform goes down, thousands of independent webhook deliveries fail at roughly the same time. Because pure exponential backoff uses a deterministic mathematical formula ($2^1, 2^2, 2^3$), all 10,000 retries calculate the exact same delay intervals. Their retry attempts become synchronized into periodic, massive traffic spikes. When the receiver recovers, all 10,000 retries hit the receiver simultaneously in a synchronized thundering herd, immediately overwhelming its connection pool and crashing it again. Full Jitter Resolution: Full Jitter introduces a uniform random variable between 0 and the exponential backoff ceiling: `sleep = random_between(0, min(max_backoff, base * 2^attempt))`. By randomizing each individual worker's retry delay across the entire time interval, the concentrated spikes of traffic are flattened into a continuous, smooth distribution of requests. When the receiver comes back online, retries trickle in gradually, allowing the receiver to warm its caches, scale worker pools, and process the backlog without crashing.",
        [
            "Explains that deterministic exponential backoff synchronizes retry spikes into destructive thundering herds",
            "Defines Full Jitter as randomizing sleep time uniformly between 0 and the exponential ceiling",
            "Demonstrates that jitter smooths traffic into a uniform distribution, allowing recovered services to absorb backlog"
        ],
        [
            "Claims Full Jitter means retrying failed webhooks immediately with zero delay"
        ]
    ),
    (
        "B68_2_13",
        "scenario",
        "hard",
        "scenario",
        ["Webhook Architecture", "Concurrency"],
        "Distributed Scheduling",
        "Multi-Tenant Webhook Fairness and Slow Subscriber Isolation",
        "A platform dispatches millions of webhooks across 5,000 business tenants using a shared worker pool of 100 concurrent HTTP workers. Tenant A configures their webhook URL to an endpoint running on a severely overloaded server that takes 30 seconds to respond or time out. Within 10 minutes, webhook delivery latency for all other 4,999 tenants jumps from 50ms to 45 minutes, creating a massive platform-wide backlog. How do you architect tenant-isolated fair dispatching to eliminate this noisy-neighbor vulnerability?",
        "Root Cause: When Tenant A's endpoint hangs for 30 seconds, shared worker threads picking up Tenant A's jobs become blocked waiting on slow network sockets. Because Tenant A is generating thousands of events, Tenant A's slow requests saturate all 100 worker threads in the global pool, starving the other 4,999 tenants whose endpoints respond in 50ms. Architectural Solution: 1) Decouple Ingestion from Execution with Per-Tenant Queues / Deficit Round Robin: Instead of a single shared FIFO queue, partition webhook jobs into virtual per-tenant queues or partitioned Kafka topics keyed by `tenant_id`. 2) Concurrency Limits Per Tenant: Enforce a strict max concurrent dispatch limit per tenant (e.g., maximum 5 concurrent outbound HTTP requests per tenant). 3) Tenant Bulkheads: If Tenant A has 5 requests in-flight, any further webhooks for Tenant A remain queued in Tenant A's backlog. The remaining 95 worker threads remain freely available to process fast webhooks from other tenants. 4) Strict Outbound HTTP Timeouts: Configure aggressive connect timeouts (e.g., 2s) and read timeouts (e.g., 5s) on the HTTP client so broken endpoints are terminated quickly rather than holding threads for 30 seconds.",
        [
            "Identifies worker thread starvation caused by slow subscriber endpoints blocking shared worker pools",
            "Implements per-tenant concurrency limits or virtual per-tenant queues to isolate noisy neighbors",
            "Enforces aggressive outbound HTTP timeouts to release worker threads rapidly"
        ],
        [
            "Recommends deleting Tenant A's account from the database immediately"
        ]
    ),
    (
        "B68_2_14",
        "scenario",
        "medium",
        "scenario",
        ["Webhook Architecture", "Resilience"],
        "Circuit Breakers / Systems Design",
        "Automatic Webhook Endpoint Deactivation Policies",
        "Your webhook system sends events to subscriber URLs. A subscriber company goes out of business and abandons their domain. The domain is purchased by a domain squatter, and their webhook endpoint now returns HTTP 404 or connection refused on every request. Your system is spending compute and network bandwidth attempting millions of retries indefinitely. How do you design an automated endpoint deactivation policy with circuit breakers and safe reactivation workflows?",
        "To eliminate unbounded waste while protecting legitimate tenants: 1) Circuit Breaker State Machine: Model each webhook subscription with states: `HEALTHY`, `DEGRADED`, `SUSPENDED`. 2) Failure Thresholding: Track consecutive delivery failures and error types. Differentiate transient errors (HTTP 500, 502, timeouts) from permanent terminal errors (HTTP 404 Not Found, 410 Gone, SSL certificate invalidation). 3) Transition to Suspended: If an endpoint records 50 consecutive failures over a 24-hour period, or returns an explicit HTTP 410 Gone, transition the subscription to `SUSPENDED`. Immediately halt all automated retry loops for that endpoint. 4) Notification Escalation: Emit a high-priority email notification to the tenant admin alerting them that webhooks have been deactivated due to persistent delivery failures, including timestamps and HTTP response codes. 5) Safe Reactivation Workflow: Provide a 'Send Test Ping' button in the tenant portal. The system sends an isolated test event. Only when the subscriber endpoint returns an HTTP 200 OK does the subscription transition back to `HEALTHY`, resuming queued or future webhook dispatch.",
        [
            "Defines explicit subscription states (Healthy, Degraded, Suspended) based on consecutive failure thresholds",
            "Differentiates terminal HTTP status codes (404, 410) from transient errors to trigger faster suspension",
            "Provides automated admin alerts and a test-ping verification mechanism before restoring active status"
        ],
        [
            "Recommends silently deleting the customer's webhook configuration without sending an email"
        ]
    ),
    (
        "B68_2_15",
        "concept",
        "easy",
        "concept",
        ["Webhook Architecture", "Idempotency"],
        "HTTP APIs",
        "Webhook Idempotency Keys and Subscriber Deduplication",
        "Why must public webhook architectures guarantee 'At-Least-Once Delivery' rather than 'Exactly-Once Delivery', and what standard HTTP headers must the dispatcher send to enable subscribers to safely deduplicate webhook events?",
        "1) Why At-Least-Once Delivery is Mandatory: In distributed networks, true 'Exactly-Once Delivery' across independent HTTP endpoints is physically impossible due to the Two Generals problem. If the dispatcher POSTs a webhook, the subscriber processes it successfully, but the network drops the HTTP 200 OK response packet, the dispatcher must assume delivery failed and retry the request. Therefore, duplicate deliveries are an inevitable reality of reliable distributed messaging. 2) Headers Required for Deduplication: The dispatcher must include a unique, persistent event identifier in the request headers: `X-Webhook-ID: evt_abc123` (or `Idempotency-Key: evt_abc123`). The subscriber maintains an idempotency ledger (e.g., in Redis or an SQL unique table). When a webhook arrives, the subscriber checks if `evt_abc123` has already been processed. If yes, it immediately returns HTTP 200 OK without re-executing business logic, ensuring exactly-once processing semantics at the application layer.",
        [
            "Explains that network packet loss on response packets forces retries, making at-least-once delivery inevitable",
            "Identifies passing a unique event identifier (e.g. X-Webhook-ID or Idempotency-Key) in HTTP headers",
            "Describes subscriber-side deduplication caching to achieve exactly-once processing semantics"
        ],
        [
            "Claims HTTP 3.0 provides built-in exactly-once delivery guarantees that eliminate duplicate webhooks"
        ]
    ),
    (
        "B68_2_16",
        "diagnose",
        "medium",
        "debugging",
        ["Webhook Architecture", "Data Consistency"],
        "Event-Driven Architecture",
        "Out-of-Order Webhook Delivery and Sequence Counters",
        "A warehouse fulfillment subscriber receives webhooks from an e-commerce platform for order lifecycle events: `OrderCreated`, `OrderPaid`, `OrderCancelled`. Because of network retries, the `OrderCancelled` webhook is delayed and arrives AFTER `OrderCreated`, but BEFORE `OrderPaid`. The subscriber processes `OrderCancelled` (canceling the order), and then processes `OrderPaid`, accidentally reopening and fulfilling the canceled order! How do you redesign the webhook payload and subscriber ingestion logic to prevent out-of-order state corruption?",
        "Root Cause: The subscriber blindly applies state transitions based on arrival order rather than logical event causality. When network retries reorder events, late-arriving earlier events overwrite newer states. Solution: 1) Monotonic Sequence Numbers / Logical Clocks: The dispatcher must include an entity-scoped monotonic sequence number in the webhook payload (e.g., `\"sequence\": 3`, or an RFC 3339 event occurrence timestamp `\"occurred_at\": \"2026-10-08T10:00:00Z\"`). 2) Subscriber-Side State Machine & Version Checks: The subscriber stores the `last_processed_version` (or timestamp) on the local `Order` record. When an incoming webhook arrives: If `event.version <= order.last_processed_version`, the subscriber detects an obsolete event and discards it (returning HTTP 200). 3) Terminal State Protection: Define explicit, irreversible terminal states in the state machine. Once an order enters `CANCELLED`, transitions to `PAID` are mathematically rejected by domain validation, preventing resurrecting canceled entities.",
        [
            "Diagnoses out-of-order webhook delivery causing stale state overwrites on the subscriber",
            "Prescribes including monotonic sequence numbers or entity-scoped logical timestamps in payloads",
            "Implements subscriber-side version checking and terminal state validation in domain state machines"
        ],
        [
            "Suggests putting a Thread.sleep(5000) on all incoming webhook requests to let earlier events catch up"
        ]
    ),
    (
        "B68_2_17",
        "concept",
        "easy",
        "concept",
        ["API Evolution", "Webhook Architecture"],
        "API Design",
        "Webhook Payload Versioning Strategies",
        "When an API provider needs to introduce breaking changes to its webhook event payloads, what are the architectural tradeoffs between 'URL-Based Versioning' (e.g., `/webhooks/v2`) and 'Header/Subscription-Level Versioning' (pinning the webhook schema to the subscriber's configured API version)?",
        "1) URL-Based Versioning (Path-based): The subscriber registers an explicit endpoint containing the version in the URL path (e.g., `https://client.com/webhooks/v2`). Tradeoffs: Very simple to route on the subscriber's reverse proxy or controller router. However, migrating requires the subscriber to create a new endpoint, update their subscription configuration in the provider dashboard, and run both v1 and v2 endpoints simultaneously during cutover. 2) Header / Subscription-Level Versioning (Stripe-style API version pinning): The webhook subscription configuration in the provider's database stores a pinned API version (e.g., `2026-08-01`). The dispatcher sends the payload transformed according to the pinned version, indicating the version in an HTTP header (`X-Webhook-Version: 2026-08-01`). Tradeoffs: Allows the subscriber to upgrade their webhook payload schema independently of their HTTP endpoint URL, and allows testing new versions in sandbox environments before switching production versions. However, the provider backend must maintain and maintain upcaster/transformer pipelines for every legacy schema version supported.",
        [
            "Contrasts explicit URL path routing with subscription-pinned schema versioning",
            "Analyzes subscriber migration burden: spinning up new URLs vs upgrading pinned version in dashboard",
            "Highlights provider backend complexity: maintaining versioned transformers/upcasters for pinned schemas"
        ],
        [
            "Claims webhook payloads can never be changed once deployed to production"
        ]
    ),
    (
        "B68_2_18",
        "explain",
        "medium",
        "explain",
        ["Webhook Architecture", "Observability"],
        "SaaS Architecture",
        "Webhook Delivery Observability and Self-Service Audit Logs",
        "Why is self-service webhook delivery observability (e.g., exposing an audit log of past deliveries, HTTP status codes, request headers, response bodies, and latency) considered an essential backend architectural component of developer-facing SaaS platforms?",
        "Webhooks operate across organizational boundaries: the SaaS provider's backend executes HTTP calls against an external, third-party server managed by the customer. When webhooks fail, customers instinctively blame the SaaS provider ('Your webhooks aren't firing!'). Without granular delivery observability: 1) Support engineering spends hundreds of hours grepping internal logs to prove whether the webhook was sent, what URL was called, and what HTTP error the customer's server returned. 2) Customer developers have zero visibility into why their integrations broke (e.g., SSL certificate expiration, firewall IP blocking, or HTTP 500 stack traces). Architectural Solution: Persist a structured `webhook_deliveries` audit table recording: `id`, `subscription_id`, `event_type`, `attempt_number`, `dispatched_at`, `duration_ms`, `http_status_code`, sanitized request headers, and the first 1KB of the customer's HTTP response body. Exposing this via a customer dashboard and REST API empowers customer developers to debug their own endpoints in real-time without contacting support.",
        [
            "Identifies that webhooks cross organizational boundaries, making proof of delivery and external debugging critical",
            "Highlights support overhead reduction by shifting troubleshooting to self-service customer audit logs",
            "Specifies storing delivery attempt metadata: HTTP status codes, latency, timestamps, and response snippets"
        ],
        [
            "Claims storing webhook logs is illegal under web security standards"
        ]
    ),
    (
        "B68_2_19",
        "tradeoff",
        "medium",
        "tradeoff",
        ["API Security", "Network Architecture"],
        "Mutual TLS (mTLS)",
        "Mutual TLS vs HMAC Signatures for Webhook Security",
        "What are the security and operational tradeoffs between using 'Mutual TLS (mTLS)' versus 'HMAC-SHA256 Signatures' for securing webhook transmissions between enterprise financial institutions?",
        "HMAC-SHA256 Signatures: 1) Mechanism: Application-layer cryptographic signature sent in an HTTP header over standard one-way TLS. 2) Advantages: Extremely simple to implement, zero infrastructure or network-layer overhead. Works effortlessly with serverless functions (AWS Lambda), API gateways, and cloud load balancers. 3) Disadvantages: Security is entirely dependent on application code correctly parsing the raw body and verifying the hash. Vulnerable to misconfigurations if developers fail to verify signatures. Mutual TLS (mTLS): 1) Mechanism: Transport-layer mutual authentication. Both client (webhook dispatcher) and server (subscriber) present and verify X.509 certificates during the TLS handshake before any HTTP data is exchanged. 2) Advantages: Unmatched cryptographic security. Hardware-level client authentication enforced at the network/proxy layer (NGINX, Envoy). The subscriber's web server drops unauthorized connections before application code or CPU resources are touched. 3) Disadvantages: High operational complexity. Requires managing, distributing, and rotating X.509 certificates across enterprise boundaries before expiration. Difficult to route through many standard cloud CDNs or serverless edge platforms without dedicated reverse proxies.",
        [
            "Contrasts application-layer HMAC verification with transport-layer X.509 certificate exchange (mTLS)",
            "Highlights mTLS security advantage: network-level rejection of unauthorized connections before application code executes",
            "Analyzes mTLS operational drawback: enterprise certificate distribution, lifecycle rotation, and CDN/proxy complexity"
        ],
        [
            "Claims mTLS requires replacing fiber optic cables between the two companies"
        ]
    ),
    (
        "B68_2_20",
        "concept",
        "easy",
        "concept",
        ["Webhook Architecture", "Performance Tuning"],
        "Asynchronous Processing",
        "Asynchronous Webhook Ingestion on the Subscriber Side",
        "When an engineer builds an endpoint to receive incoming webhooks from external providers (like Stripe or GitHub), why is doing heavy business logic (e.g., database updates, third-party API calls, PDF generation) synchronously inside the HTTP handler considered a dangerous anti-pattern, and how should it be structured?",
        "Dangerous Anti-Pattern: Most webhook dispatchers enforce strict HTTP response timeouts (typically 5 to 10 seconds). If the subscriber's HTTP handler synchronously performs PDF generation, complex SQL transactions, and email dispatches, any transient latency spike will cause the handler to exceed the provider's timeout. The provider marks the delivery as failed and triggers an exponential retry storm, repeatedly re-executing the heavy workload and crashing the subscriber's server. Recommended Asynchronous Structure: 1) Step 1 (Edge Ingestion): The HTTP handler strictly performs HMAC signature verification and payload schema validation. 2) Step 2 (Buffer to Queue): The handler immediately enqueues the verified raw payload into an internal message queue (e.g., Redis Streams, RabbitMQ, SQS). 3) Step 3 (Immediate 200 OK): The handler immediately returns an HTTP 200 OK (or 202 Accepted) response to the dispatcher within 50 milliseconds. 4) Step 4 (Asynchronous Workers): Decoupled background workers consume events from the internal queue, executing heavy business logic, PDF generation, and database updates with independent retry policies without risking webhook timeout failures.",
        [
            "Explains that dispatcher timeouts (5-10s) trigger retry storms if the subscriber executes slow synchronous work",
            "Designs an architecture that validates signatures, buffers payloads to an internal queue, and immediately returns HTTP 200 OK",
            "Delegates heavy processing (PDFs, external APIs, complex DB transactions) to decoupled background workers"
        ],
        [
            "Recommends returning HTTP 500 so the dispatcher knows the server is busy working"
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 2).")
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
    print("POST-BATCH AUDIT PART 2")
    print("========================================")
    print(f"Batch: 68 Part 2")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
