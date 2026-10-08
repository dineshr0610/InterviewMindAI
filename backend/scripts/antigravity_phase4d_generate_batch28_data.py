"""Batch 28 question content (Backend Developer). Targeted Gap Generation."""

ROLE = "Backend Developer"

BUCKET_KEYS = {
    "BACKEND_PROCESSING": ("Background Processing", "Queues & Workers", "Backend", ["Backend Developer", "Software Engineer"]),
}

Q = [
# ---------------- BACKEND_PROCESSING ----------------
("BACKEND_PROCESSING", "scenario", "medium", "scenario", ["Queues"],
 "A background worker pulls jobs from an SQS queue. The worker takes 5 minutes to process a video rendering job, but the SQS queue's 'Visibility Timeout' is configured to only 2 minutes. What specific failure occurs in the system?",
 "Because the visibility timeout is significantly shorter than the processing time, the queue assumes the worker crashed after 2 minutes and places the exact same job back into the visible queue. A second worker picks it up and begins processing it concurrently. This results in duplicate, parallel processing of the exact same job, wasting compute resources and potentially causing data corruption.",
 ["Visibility timeout is shorter than processing time", "The queue assumes the worker crashed and re-queues the message", "Results in duplicate, parallel processing of the exact same job"],
 ["The video renders twice as fast"]),

("BACKEND_PROCESSING", "debug", "hard", "debugging", ["Dead Letter Queues"],
 "You notice that a specific background job parsing a malicious XML file always crashes the worker process with an OutOfMemory error. The worker restarts, picks up the exact same job, and crashes again. This continues infinitely, blocking the entire queue. What is this phenomenon called, and how must you architecturally resolve it?",
 "This is known as a 'Poison Message' or 'Poison Pill'. It permanently crashes consumers. You must resolve it by configuring a Dead Letter Queue (DLQ) and setting a `max_receive_count` (e.g., 3). If the job crashes the worker and is retried 3 times, the broker automatically routes it to the DLQ, permanently removing it from the main queue and allowing healthy jobs to proceed.",
 ["Known as a 'Poison Message' or 'Poison Pill'", "Configure a Dead Letter Queue (DLQ) on the message broker", "Set a maximum retry count; exceeding it automatically moves the message to the DLQ"],
 ["The queue needs to be restarted manually every time this happens"]),

("BACKEND_PROCESSING", "tradeoff", "medium", "tradeoff", ["Delivery Semantics"],
 "What are the tradeoffs between 'At-Least-Once' and 'Exactly-Once' message processing semantics in distributed background jobs?",
 "'At-Least-Once' guarantees the message is processed but might deliver it multiple times (requiring strict idempotency from the application), but it is highly performant and easy to scale. 'Exactly-Once' guarantees single execution but is incredibly complex to implement across a distributed system, heavily degrading raw performance and throughput because it requires distributed locks, two-phase commits, or strict state tracking to prevent duplicates.",
 ["At-Least-Once: Highly performant and scalable, but requires application idempotency to handle duplicates", "Exactly-Once: Guarantees single execution, preventing duplicates natively", "Exactly-Once tradeoff: Incredibly complex, heavily degrades throughput due to locking/state coordination"],
 ["Exactly-Once processes the message in exactly one second"]),

("BACKEND_PROCESSING", "implement", "hard", "implementation", ["Idempotency"],
 "How do you architect an idempotent background worker for processing e-commerce payments so that if the worker crashes exactly midway through charging the credit card, a retry does not charge the user twice?",
 "You must generate a unique `Idempotency Key` (e.g., a UUID) when the job is initially created and pass it to the third-party payment gateway. If the worker crashes and retries the exact same job, it sends the exact same Idempotency Key. The payment gateway detects the duplicate key and simply returns the previous successful response without charging the card again.",
 ["Generate a unique `Idempotency Key` when the job is created", "Pass the key to the external payment gateway", "The gateway uses the key to detect duplicates and prevent double-charging on retries"],
 ["Cancel the user's credit card and issue a new one"]),

("BACKEND_PROCESSING", "explain", "easy", "concept", ["Retries"],
 "Explain the concept of 'Exponential Backoff with Jitter' when implementing retry logic for failed background jobs.",
 "Exponential backoff means increasing the wait time exponentially between retries (e.g., 1s, 2s, 4s, 8s) to avoid hammering a struggling downstream service. 'Jitter' adds a random time variance to the backoff (e.g., 4s + random(0-1s)) so that hundreds of concurrently failing workers don't all retry at the exact same millisecond, which would cause synchronized retry storms and instantly overload the service again.",
 ["Exponential Backoff: Increasing wait time exponentially between retries", "Prevents hammering a struggling downstream service", "Jitter: Adding random variance to prevent synchronized 'retry storms' from concurrent workers"],
 ["Jitter means the worker vibrates the server rack"]),

("BACKEND_PROCESSING", "fundamentals", "medium", "concept", ["Queues"],
 "In message queue architecture, what is the exact difference between a Push-based consumer and a Pull-based (Polling) consumer?",
 "Push-based architectures (like Webhooks or SNS) aggressively send messages directly to consumers as they arrive; it provides extreme low latency but can easily overwhelm and crash consumers if the arrival rate exceeds processing capacity. Pull-based architectures (like SQS or Kafka) require the consumer to actively request/poll messages when they are ready; this naturally creates backpressure and protects the consumer from overload, but adds slight polling latency.",
 ["Push: Broker aggressively sends messages to consumers (low latency, high risk of overload)", "Pull: Consumer actively requests messages when ready (adds polling latency)", "Pull naturally creates backpressure, protecting the consumer from traffic spikes"],
 ["Push consumers push data to the database; Pull consumers pull it out"]),

("BACKEND_PROCESSING", "scenario", "hard", "scenario", ["Concurrency"],
 "A Node.js backend uses a Redis-backed job queue to schedule 10,000 delayed emails for 8:00 AM. At exactly 8:00 AM, the Node.js server completely locks up and stops serving all incoming HTTP API requests for 30 seconds. Why did the background job schedule destroy the API server?",
 "The architecture failed to isolate workloads. The Node.js Event Loop is strictly single-threaded. Because 10,000 background jobs fired simultaneously in the exact same Node.js process serving the HTTP API, the heavy synchronous CPU processing for the jobs entirely blocked the event loop. Background workers must be deployed as entirely separate, isolated processes/containers from the user-facing API servers.",
 ["The Node.js Event Loop is single-threaded", "Processing 10,000 jobs simultaneously in the same process completely blocked the event loop", "Background workers must be deployed as entirely separate, isolated processes from the API"],
 ["Node.js is notoriously bad at sending emails"]),

("BACKEND_PROCESSING", "debug", "medium", "debugging", ["Concurrency Starvation"],
 "A Python Celery worker is configured with a concurrency of 10. The queue contains 1,000 fast jobs (10ms each) and 10 extremely slow jobs (1 hour each). Very quickly, the fast jobs stop being processed completely, even though there are thousands waiting. What happened to the worker?",
 "The worker suffered from 'Concurrency Starvation'. Because it only has 10 concurrent execution slots (threads/processes), all 10 slots became permanently occupied by the 10 slow, 1-hour jobs. The worker is now completely blocked for an hour and cannot pull any fast jobs from the queue. Architecturally, drastically slow jobs must be routed to a dedicated, separate queue with its own isolated worker pool.",
 ["Suffered from 'Concurrency Starvation'", "All 10 execution slots became occupied by the 10 slow jobs, blocking the entire worker", "Fix: Route slow jobs to a dedicated queue with a separate, isolated worker pool"],
 ["The worker went to sleep because it was bored of the fast jobs"]),

("BACKEND_PROCESSING", "tradeoff", "medium", "tradeoff", ["Queues"],
 "What is the tradeoff of using an in-memory queue (like a Go channel or Java BlockingQueue) versus an external message broker (like RabbitMQ or Redis) for background processing?",
 "In-memory queues provide blazing fast, sub-millisecond latency and require zero external infrastructure, but if the application process crashes or restarts, all queued jobs are permanently lost (no durability). External brokers provide strict durability, crash recovery, and horizontal scaling across multiple worker nodes, but they introduce network latency, serialization overhead, and an entirely new infrastructure component to monitor and manage.",
 ["In-memory: Blazing fast, no infrastructure, but loses all jobs on process crash (no durability)", "External Broker: Strict durability, crash recovery, horizontal scaling across nodes", "External Tradeoff: Introduces network latency, serialization, and complex infrastructure management"],
 ["In-memory queues only hold data while you are actively looking at them"]),

("BACKEND_PROCESSING", "explain", "hard", "concept", ["Outbox Pattern"],
 "Explain the 'Outbox Pattern' in the context of backend microservices. What specific background processing problem does it solve?",
 "When a service needs to update its local database AND publish a message to a background queue, a crash between the two steps causes severe inconsistency (the dual-write problem). The Outbox Pattern solves this by writing the database update and inserting the message payload into a local 'outbox' table within the *same* ACID database transaction. A separate, reliable background process then safely polls the outbox and publishes the messages to the queue.",
 ["Solves the 'dual-write' inconsistency problem between a database and a message broker", "Writes business data AND the event payload to an outbox table in the SAME database transaction", "A background process polls the outbox and reliably publishes to the queue (guaranteed at-least-once)"],
 ["It is an email client built into the backend service"]),

("BACKEND_PROCESSING", "scenario", "medium", "scenario", ["Job Deduplication"],
 "You implement a background job to generate massive PDF reports. Users click 'Generate' multiple times out of impatience. The queue receives 5 identical requests for the same report. How do you implement 'Job Deduplication' to prevent wasting compute power on the extra 4 jobs?",
 "Before enqueuing the job, you hash the core job parameters (e.g., `hash(report_id, date)`). You use a fast centralized cache (like Redis) to atomically check if this exact hash is already currently processing or queued (e.g., using `SETNX`). If the hash exists, you drop the duplicate request and immediately return the ID of the already-running job to the user.",
 ["Hash the core job parameters to create a unique signature", "Atomically check a cache (Redis `SETNX`) to see if the signature is already processing", "Drop duplicates and return the ID of the existing job to the user"],
 ["Tell the users to be patient via a pop-up window"]),

("BACKEND_PROCESSING", "implement", "hard", "implementation", ["Batch Processing"],
 "A backend worker pulls a batch of 10 records from a queue. It processes 9 successfully, but the 10th throws a fatal exception. If the worker simply crashes and leaves the message unacknowledged, the entire batch of 10 is retried later. How do you architect the worker to handle partial batch failures efficiently?",
 "You must capture all asynchronous results or process sequentially. For the 9 successes, you immediately commit their state. Crucially, you do NOT reject the entire queue message. Instead, you explicitly acknowledge the original batch message to the queue to delete it, and then dynamically enqueue a *new*, smaller message containing *only* the 1 failed record to be retried independently.",
 ["Commit the state of the successful records", "Acknowledge the original batch message to completely remove it from the queue", "Dynamically enqueue a NEW message containing only the failed records for independent retry"],
 ["Throw an exception and hope the database figures it out"]),

("BACKEND_PROCESSING", "debug", "medium", "debugging", ["Scheduling"],
 "An application uses a background Cron job running every 5 minutes to sweep the database for expired subscriptions. You deploy a second instance of the application for horizontal scaling. Suddenly, customers are receiving duplicate 'Subscription Expired' emails. Why?",
 "Cron jobs running natively within the application code are stateless and unaware of other instances. When you scaled to 2 instances, both servers executed the exact same cron job at exactly the same time, processing the same database rows concurrently. You must extract the cron job to a centralized scheduler (like Kubernetes CronJob) or implement a distributed lock (e.g., Redis Redlock) so only one instance executes the sweep.",
 ["In-app cron jobs are unaware of other instances; both instances ran the sweep concurrently", "Both processed the same database rows at the same time", "Fix: Use a centralized scheduler (K8s CronJob) or a distributed lock (Redis Redlock)"],
 ["The customers subscribed twice by accident"]),

("BACKEND_PROCESSING", "fundamentals", "easy", "concept", ["Backpressure"],
 "What is 'Backpressure' in the context of backend queue and worker architectures?",
 "Backpressure is a reliability feedback mechanism where a downstream system (like a worker or database) explicitly signals to an upstream system (like an API or message queue) that it is currently overloaded and cannot accept more work. The upstream system then slows down, queues requests, or actively rejects new traffic (e.g., returning HTTP 429 Too Many Requests) to prevent the downstream system from crashing.",
 ["A feedback mechanism where a downstream system signals it is overloaded", "Forces the upstream system to slow down, queue, or reject new traffic (HTTP 429)", "Prevents the downstream system from completely crashing under extreme load"],
 ["Backpressure is the physical air pressure inside the server chassis"]),

("BACKEND_PROCESSING", "scenario", "medium", "scenario", ["TTL"],
 "A massive backlog of 5 million jobs builds up in RabbitMQ during an outage. When the backend workers come back online, you realize that 90% of the jobs are 'Send Password Reset Email' requests that are now 12 hours old and useless. Processing them will take 3 hours. How do you architect the queue to prevent processing useless, stale jobs?",
 "You configure a Message TTL (Time-To-Live) on the queue or the specific message type. For time-sensitive jobs like password resets, you set a strict TTL of 15 minutes. If the message sits in the queue longer than 15 minutes without being consumed, the broker automatically drops it (or routes it to a DLQ), instantly clearing the backlog of stale work without wasting worker compute.",
 ["Configure a Message TTL (Time-To-Live) on the queue or message", "If the message sits in the queue longer than the TTL, the broker automatically drops it", "Instantly clears stale backlogs without wasting worker compute time"],
 ["Manually delete the queue and recreate it from scratch"]),

("BACKEND_PROCESSING", "tradeoff", "hard", "tradeoff", ["Architecture"],
 "When architecting a distributed task scheduler, what is the tradeoff between a 'Choreography' (Event-Driven) architecture and an 'Orchestration' (Central Coordinator) architecture for complex background workflows?",
 "Choreography relies on services reacting to events independently, providing extreme loose coupling and massive scalability, but makes the overall workflow invisible, impossible to trace, and a nightmare to debug. Orchestration relies on a central controller (like Temporal or Airflow) explicitly commanding services, providing strict observability, trivial error recovery, and clear workflow state, but creates a massive single point of failure and tight domain coupling.",
 ["Choreography: Extreme loose coupling/scaling, but workflows are invisible and nearly impossible to trace", "Orchestration: Strict observability, clear state, trivial error recovery", "Orchestration tradeoff: Creates a single point of failure and tight domain coupling"],
 ["Choreography requires services to dance; Orchestration requires them to play instruments"]),

("BACKEND_PROCESSING", "implement", "medium", "implementation", ["Graceful Shutdown"],
 "You deploy a background worker processing high-CPU video encoding jobs. When deploying a new version, Kubernetes sends a `SIGTERM` signal to stop the old container. However, half-finished videos are immediately corrupted. How do you implement 'Graceful Shutdown' for this worker?",
 "The worker application must actively intercept the OS `SIGTERM` signal. Upon receiving it, the worker immediately stops pulling *new* jobs from the queue. It then waits for all currently executing jobs to finish processing (or explicitly saves their state), and only then safely calls `exit(0)`. You must also ensure the Kubernetes `terminationGracePeriodSeconds` is set longer than the maximum possible video encoding time.",
 ["Actively intercept the OS `SIGTERM` signal in the application code", "Stop pulling new jobs, but wait for currently executing jobs to finish completely", "Ensure Kubernetes `terminationGracePeriodSeconds` exceeds the maximum job duration"],
 ["Unplug the server so the videos don't have time to corrupt"])
]
