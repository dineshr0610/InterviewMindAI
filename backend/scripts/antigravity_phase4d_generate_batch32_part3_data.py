"""Batch 32 Part 3 question content (Full Stack). Targeted Gap Generation."""

ROLE = "Full Stack Developer"

BUCKET_KEYS = {
    "FULL_STACK_OBSERVABILITY": ("Observability", "Telemetry & Monitoring", "Architecture", ["Full Stack Developer", "Backend Developer", "Site Reliability Engineer"]),
}

Q = [
# ---------------- FULL_STACK_OBSERVABILITY ----------------
("FULL_STACK_OBSERVABILITY", "debug", "hard", "debugging", ["Distributed Tracing", "Correlation IDs"],
 "A user reports clicking 'Checkout' failed. You check backend logs and see thousands of 500 errors, making it impossible to find their specific click. How do you architect observability to instantly find the exact backend log for a specific frontend click?",
 "Implement Distributed Tracing with Correlation IDs (Trace IDs). The frontend generates a unique UUID (`X-Correlation-ID`) on click and attaches it to HTTP headers. Every microservice, backend API, and database injects this ID into their structured logs. When a user reports an error, you search the logging platform for that specific Trace ID to see the complete lifecycle.",
 ["Implement Distributed Tracing using Correlation IDs (Trace IDs)", "The frontend generates a unique UUID on click and attaches it to HTTP headers", "Every downstream service injects this ID into their logs, enabling full lifecycle search"],
 ["Ask the user what time they clicked the button and guess"]),

("FULL_STACK_OBSERVABILITY", "implement", "medium", "implementation", ["Frontend Telemetry", "Source Maps"],
 "You log frontend errors to Sentry, but the stack traces are completely unreadable (e.g., `a.b is not a function at app.min.js:1:405`). How do you configure the deployment pipeline to fix these obfuscated frontend stack traces?",
 "You must upload 'Source Maps' to your error tracking provider during the CI/CD build process. Source maps securely map the obfuscated, minified production JavaScript back to your original, human-readable source code (like TypeScript/JSX). Source maps should only be uploaded to the private tracking server, never deployed to the public CDN.",
 ["Upload 'Source Maps' to the error tracking provider during the CI/CD build step", "Securely maps the obfuscated, minified production JS back to original source code", "Never deploy source maps to the public CDN to protect source code"],
 ["Hire a cryptographer to decode the minified Javascript by hand"]),

("FULL_STACK_OBSERVABILITY", "tradeoff", "hard", "tradeoff", ["Tracing", "Sampling"],
 "When implementing Distributed Tracing (10,000 requests/sec), what is the tradeoff between 'Head-Based Sampling' and 'Tail-Based Sampling'?",
 "Head-Based Sampling randomly decides to keep a trace at the very beginning (frontend/API). It is cheap/scalable, but misses 99% of rare errors because they are randomly dropped before failing. Tail-Based Sampling records everything into a memory buffer, waits for the request to finish, and *then* decides to keep it (keeping 100% of errors). It is vastly superior for debugging but requires expensive memory buffers.",
 ["Head-Based: Decides at the start. Cheap/scalable, but misses 99% of rare errors.", "Tail-Based: Waits for request finish, then decides. Keeps 100% of errors.", "Tradeoff: Tail-based is vastly superior for debugging but requires massive, expensive memory infrastructure."],
 ["Head sampling measures the user's brainwaves, Tail sampling measures the mouse"]),

("FULL_STACK_OBSERVABILITY", "explain", "easy", "concept", ["RUM", "Synthetic Monitoring"],
 "In full-stack observability, what is the difference between 'Synthetic Monitoring' and 'Real User Monitoring' (RUM)?",
 "Synthetic Monitoring uses automated bots/scripts to continuously ping your application globally (e.g., executing a fake checkout flow every minute) to proactively detect downtime before users notice. Real User Monitoring (RUM) embeds a telemetry script directly in the live frontend to measure the actual, organic performance experienced by real human users on their specific devices.",
 ["Synthetic: Automated bots continuously testing flows to proactively detect downtime", "Real User Monitoring (RUM): Embedded frontend scripts measuring actual organic user experience", "Synthetic is proactive/simulated; RUM is reactive/real-world"],
 ["Synthetic monitoring monitors artificial intelligence, RUM monitors alcohol sales"]),

("FULL_STACK_OBSERVABILITY", "scenario", "medium", "scenario", ["Alerting", "SLIs"],
 "You configure an alert to trigger if CPU usage exceeds 90% on the backend. It triggers constantly, waking up on-call engineers, but the app is functioning perfectly fine for users. What observability anti-pattern is this, and how do you fix it?",
 "You committed the 'Alerting on Causes instead of Symptoms' anti-pattern. High CPU is a system cause, not a user-facing symptom (orchestrators intentionally run CPUs hot for efficiency). You must re-architect alerts based on Service Level Indicators (SLIs) that directly impact the user experience, such as 'API Error Rate > 1%' or 'P99 Latency > 2s'.",
 ["'Alerting on Causes instead of Symptoms' anti-pattern", "High CPU is a system cause, not a direct measurement of user pain", "Fix: Alert based on user-facing SLIs (Error Rates, P99 Latency, Availability)"],
 ["The server is just excited and needs to burn off energy"]),

("FULL_STACK_OBSERVABILITY", "implement", "hard", "implementation", ["Prometheus", "High Cardinality"],
 "You log HTTP metrics (Method, Path, Status) to Prometheus. A junior developer adds a new label: `user_id`. Within 2 hours, the Prometheus server crashes from memory exhaustion. Why did adding `user_id` crash the metrics server?",
 "This is a 'High Cardinality' failure. Time-series databases create a brand new time-series array in RAM for every unique combination of labels. By adding `user_id`, the DB attempted to create millions of independent memory streams. Labels must strictly be low-cardinality (Status 200, Method GET). High-cardinality data must be stored in structured logs or traces, never metrics.",
 ["'High Cardinality' failure in a time-series database", "Creates a new memory stream for every unique combination of labels (millions for `user_id`)", "Fix: Store high-cardinality data in structured logs/traces, strictly limiting metrics to low-cardinality labels"],
 ["Prometheus physically cannot read that many usernames at once"]),

("FULL_STACK_OBSERVABILITY", "debug", "medium", "debugging", ["Tracing", "Bottlenecks"],
 "A distributed trace shows a latency spike: Frontend (3000ms) -> API Gateway (2900ms) -> Backend Service (2800ms). However, the Backend Service span shows 2800ms of 'blank space' with no DB queries or sub-spans. Where is the bottleneck?",
 "The bottleneck is occurring entirely within the Backend Service compute layer, *before* it talks to the database. The 'blank space' indicates blocking CPU execution, un-instrumented synchronous code (like parsing massive JSON or heavy regex), or thread-pool exhaustion waiting for an I/O lock. You must add granular custom trace spans inside the backend code to reveal the CPU operations.",
 ["Bottleneck is entirely within the Backend Service compute layer (CPU/App code)", "Indicates un-instrumented synchronous execution (parsing, regex) or thread-pool exhaustion", "Fix: Add custom, granular trace spans inside the application code"],
 ["The backend took a 2800ms nap before executing the query"]),

("FULL_STACK_OBSERVABILITY", "tradeoff", "medium", "tradeoff", ["Structured Logging"],
 "When building full-stack logs, what is the tradeoff between standard text logging (`console.log('User 123 logged in')`) and Structured Logging (`logger.info('Login', {userId: 123})`)?",
 "Text logging is trivially easy for a human to read raw, but impossible to reliably query, aggregate, or alert on programmatically because it requires fragile regex. Structured Logging outputs JSON. While harder to read raw, it allows centralized logging platforms (ELK/Datadog) to instantly index every field, enabling powerful exact-match queries (`userId:123 AND event:Login`).",
 ["Text Logging: Easy to read raw, impossible to reliably query programmatically (fragile regex)", "Structured Logging (JSON): Harder to read raw, enables powerful indexed querying", "Allows centralized platforms to index fields for exact-match searches (`userId:123`)"],
 ["Structured logging builds a physical structure around the server logs"]),

("FULL_STACK_OBSERVABILITY", "scenario", "hard", "scenario", ["Context Propagation", "Node.js"],
 "You implement W3C Trace Context. The frontend sends a Trace ID to the Node.js backend. The backend receives it, but subsequent DB queries generate entirely new, disjointed Trace IDs. Why did the trace context break inside Node.js?",
 "The trace context was lost due to the asynchronous nature of the Node.js event loop. When the request handler yielded to an async operation (`await db.query()`), the standard execution context was lost; the global tracer forgot which incoming request triggered the callback. You must use `AsyncLocalStorage` to maintain and propagate trace context across asynchronous boundaries.",
 ["Context lost due to the asynchronous nature of the Node.js event loop", "Yielding to async callbacks drops standard execution context variables", "Fix: Use `AsyncLocalStorage` to propagate trace context across asynchronous execution boundaries"],
 ["Node.js intentionally deletes tracing headers for security reasons"]),

("FULL_STACK_OBSERVABILITY", "explain", "easy", "concept", ["SLI", "SRE"],
 "What is a 'Service Level Indicator' (SLI) in the context of Site Reliability Engineering?",
 "An SLI is a carefully defined, quantitative measurement of a specific aspect of a service's performance from the perspective of the user. Common SLIs include Request Latency, Error Rate (percentage of 500s), or Availability. SLIs form the mathematical foundation for setting Service Level Objectives (SLOs) and triggering actionable alerts.",
 ["A quantitative measurement of service performance from the user's perspective", "Examples: Request Latency, Error Rate, Availability", "Forms the mathematical foundation for setting SLOs and actionable alerting"],
 ["A physical indicator light on the server rack that turns red on failure"]),

("FULL_STACK_OBSERVABILITY", "implement", "medium", "implementation", ["Database Observability", "Sqlcommenter"],
 "You want to monitor PostgreSQL queries in a full-stack app. How do you architect the backend ORM/query builder to inject observability context directly into the database server logs?",
 "You inject context as SQL comments using a technique like 'Sqlcommenter'. Before the backend executes the query, it automatically appends a structured comment string to the end of the raw SQL (e.g., `SELECT * FROM users /* trace_id='abc', route='/login' */`). This allows DBAs to look at slow query logs and instantly correlate DB load back to the specific frontend user/route.",
 ["Inject context directly as SQL comments ('Sqlcommenter' pattern)", "Append structured comments to raw SQL (`/* trace_id='abc', route='/login' */`)", "Allows DBAs to instantly correlate slow DB queries back to specific frontend routes/users"],
 ["Email the DBA every time a query is executed"]),

("FULL_STACK_OBSERVABILITY", "debug", "hard", "debugging", ["Async Tracing", "Kafka"],
 "A user clicks 'Generate' (Frontend) -> API (Backend) -> publishes to Kafka -> Background Worker emails report. The trace links Frontend and Backend, but the Worker appears disconnected. How do you fix this broken asynchronous trace?",
 "Standard HTTP trace propagation uses HTTP headers. When pushed to Kafka, the HTTP context stops. To propagate across async message brokers, you must explicitly extract the Trace ID from the HTTP request context and inject it into the Kafka message *Headers* (or payload metadata). The Background Worker must explicitly extract the Trace ID from the Kafka header to resume the span.",
 ["HTTP trace context stops at the message broker boundary", "Fix: Extract the Trace ID and inject it into the Kafka message Headers/Metadata", "The Background Worker must explicitly extract the Trace ID from Kafka to resume the span"],
 ["Kafka naturally destroys all metadata to run faster"]),

("FULL_STACK_OBSERVABILITY", "scenario", "medium", "scenario", ["RUM", "Blind Spots"],
 "Your backend API monitoring shows a 99.9% success rate. However, the frontend RUM (Real User Monitoring) shows 20% of users experiencing critical login failures. What boundary failure explains this discrepancy?",
 "The failure occurs between the user and your backend infrastructure, completely outside the backend's visibility. This could be a broken CDN config, a massive ISP routing failure dropping packets, or a catastrophic JavaScript exception on the frontend (e.g., a React render crash) preventing the HTTP request from ever sending. The backend shows 99.9% because it's blind to requests that never arrive.",
 ["Failure is occurring outside the visibility of the backend infrastructure", "Examples: Broken CDN, ISP packet drops, or fatal frontend JavaScript crashes", "The backend only measures requests that actually reach it, creating a massive blind spot"],
 ["The users are lying to make the backend engineers look bad"]),

("FULL_STACK_OBSERVABILITY", "tradeoff", "hard", "tradeoff", ["Web Vitals", "LCP"],
 "When monitoring frontend performance, what is the tradeoff between measuring the `load` event (`window.onload`) versus 'Core Web Vitals' (like Largest Contentful Paint - LCP)?",
 "The `load` event measures when all network assets (images, iframes) finish downloading; it is a legacy metric that often triggers long after the user is interacting with the page. Core Web Vitals (LCP) measure the exact moment the most visually significant content renders on screen. LCP is vastly superior for measuring true perceived user experience, but requires modern browser APIs to instrument.",
 ["`load` event: Legacy metric triggering when all assets finish downloading, ignoring perceived experience", "LCP: Measures exactly when the most visually significant content renders on screen", "Tradeoff: LCP is superior for perceived UX but harder to instrument/requires modern APIs"],
 ["`window.onload` actually measures how heavy the monitor physically is"]),

("FULL_STACK_OBSERVABILITY", "implement", "medium", "implementation", ["Metrics Aggregation", "Percentiles"],
 "You are building a dashboard for a distributed microservice architecture. How do you calculate 'P99 Latency' mathematically correctly when aggregating data across 10 different backend servers?",
 "You cannot calculate local P99 latency on each server and average those 10 values together; percentiles are mathematically un-averageable. You must configure the servers to emit latency data using a summary data structure (like HDR Histogram or T-Digest) to the central metrics server. The central server merges these raw distributions, calculating the true global P99 percentile.",
 ["Percentiles are mathematically un-averageable across distributed nodes", "Must emit latency data using summary structures (HDR Histogram, T-Digest)", "Central server merges the raw distributions to calculate the true global P99"],
 ["Just add all the latencies together and divide by 99"]),

("FULL_STACK_OBSERVABILITY", "fundamentals", "easy", "concept", ["Three Pillars"],
 "What are the 'Three Pillars of Observability'?",
 "The Three Pillars are Metrics, Logs, and Traces. Metrics are highly aggregated numerical time-series data (e.g., CPU %, error rate). Logs are granular, discrete records of specific events (e.g., a specific database query or error stack trace). Traces track the complete lifecycle of a single request as it propagates across distributed services and boundaries, visualizing latency.",
 ["Metrics: Aggregated numerical time-series data (CPU%, error rates)", "Logs: Granular, discrete records of specific events (error stack traces)", "Traces: Tracks the complete lifecycle of a single request across distributed boundaries"],
 ["Hope, Faith, and Server Reboots"])
]
