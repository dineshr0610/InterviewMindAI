"""Batch 28 Part 3 question content (Backend Developer). Targeted Gap Generation."""

ROLE = "Backend Developer"

BUCKET_KEYS = {
    "BACKEND_RELIABILITY": ("Backend Reliability", "Fault Tolerance", "Backend", ["Backend Developer", "Site Reliability Engineer", "Architecture"]),
}

Q = [
# ---------------- BACKEND_RELIABILITY ----------------
("BACKEND_RELIABILITY", "scenario", "medium", "scenario", ["Timeouts"],
 "A microservice calls an external third-party API that normally takes 50ms. The third-party API experiences an outage and begins hanging indefinitely without dropping the TCP connection. Within minutes, your microservice completely crashes, even for endpoints that don't use the third-party API. Why?",
 "The microservice failed to implement aggressive HTTP Timeouts on the external call. Because the connections hung indefinitely, the microservice's entire thread pool or connection pool became completely exhausted waiting for the external API. Once the pool was exhausted, the service couldn't accept *any* new incoming requests, causing a total localized failure.",
 ["Failed to implement aggressive HTTP Timeouts on the external network call", "Indefinitely hanging connections completely exhausted the microservice's thread/connection pool", "Exhaustion prevents the service from handling any new requests, even unrelated ones"],
 ["The third-party API sent a virus through the open TCP port"]),

("BACKEND_RELIABILITY", "debug", "hard", "debugging", ["Retry Storms"],
 "You implement a 3-second timeout and a 3-retry policy on a downstream service call. The downstream service slows down, taking 5 seconds to respond. Suddenly, both the upstream and downstream services instantly crash under massive load. Why did adding retries cause a total system collapse?",
 "This caused a 'Retry Storm'. Because the downstream is slow but alive, the upstream times out at 3s and immediately fires a retry. The downstream is now processing the original request AND the retry simultaneously. The upstream fires a 3rd retry. This exponentially multiplies the concurrent load on the struggling downstream service by 3x instantly, crashing it, which in turn exhausts the upstream.",
 ["Caused a 'Retry Storm'", "Upstream times out and retries while the downstream is still actively processing the original request", "Exponentially multiplies concurrent load, instantly crashing the struggling downstream service"],
 ["The retries were too fast for the CPU fan to cool down"]),

("BACKEND_RELIABILITY", "tradeoff", "medium", "tradeoff", ["Circuit Breakers"],
 "What is the operational tradeoff of using a 'Circuit Breaker' pattern versus a simple 'Retry with Exponential Backoff' to protect a failing downstream dependency?",
 "Exponential backoff still fundamentally attempts to send traffic to the failing dependency; if it is completely dead, this wastes upstream threads and network resources waiting for timeouts. A Circuit Breaker detects the failure threshold and 'opens', failing fast instantly without even attempting the network call, perfectly preserving upstream resources. The tradeoff is that Circuit Breakers require complex state management and probing logic to 'half-open' and recover.",
 ["Backoff still wastes upstream threads/resources waiting for timeouts on dead dependencies", "Circuit Breaker fails fast instantly, perfectly preserving upstream resources", "Tradeoff: Circuit Breakers require complex state management and probing to recover"],
 ["Circuit breakers require an electrician to reset physically"]),

("BACKEND_RELIABILITY", "explain", "easy", "concept", ["Cascading Failures"],
 "Explain the concept of a 'Cascading Failure' in a backend microservices architecture.",
 "A cascading failure occurs when a localized, minor failure in one service (e.g., Service D running out of DB connections) propagates upwards through the dependency chain (Service C hangs waiting for D, Service B exhausts its threads waiting for C, Service A crashes). A single minor failure entirely brings down the distributed system because the architecture lacks fault isolation and fail-fast mechanisms.",
 ["A localized failure in one service propagates upwards through the dependency chain", "Causes a domino effect that brings down the entire distributed system", "Occurs because the architecture lacks fault isolation (bulkheads) and fail-fast mechanisms"],
 ["It is when a server falls down the stairs"]),

("BACKEND_RELIABILITY", "scenario", "hard", "scenario", ["Timeout Propagation"],
 "Service A has a 5-second HTTP timeout for user requests. It calls Service B, which calls Service C. Service B has a 10-second timeout, and Service C takes 8 seconds to process. What architectural anti-pattern is present, and what is the specific consequence?",
 "This is 'Timeout Inversion' or a lack of 'Timeout Propagation'. Because Service A times out and returns an error to the user after 5 seconds, the user assumes the request failed. However, Service B and C continue processing the complex transaction for another 3 seconds. The backend wastes expensive resources doing useless work for a disconnected client, potentially causing phantom data mutations.",
 ["'Timeout Inversion' / Lack of 'Timeout Propagation' (upstream timeout is shorter than downstream)", "Service A returns an error, but B and C continue processing uselessly", "Wastes expensive resources and causes phantom data mutations for a disconnected client"],
 ["Service C is just inherently lazy"]),

("BACKEND_RELIABILITY", "fundamentals", "medium", "concept", ["Bulkhead Pattern"],
 "In backend reliability architecture, what is the 'Bulkhead Pattern'?",
 "Named after the watertight compartments in a ship, the Bulkhead Pattern isolates critical resources (like thread pools or connection pools) into separate, dedicated buckets for different downstream dependencies or API endpoints. If one downstream dependency hangs and exhausts its dedicated thread pool, it only sinks that specific compartment. The rest of the application remains perfectly healthy.",
 ["Isolates critical resources (threads, connections) into dedicated buckets for specific dependencies", "If one dependency hangs, it only exhausts its specific isolated pool", "Prevents a single failing dependency from sinking the entire application"],
 ["It involves physically stacking servers on top of each other like bulkheads"]),

("BACKEND_RELIABILITY", "tradeoff", "hard", "tradeoff", ["Graceful Degradation"],
 "When implementing Graceful Degradation during a database overload, what is the tradeoff of serving stale cached data versus returning an explicit HTTP 503 Service Unavailable error?",
 "Serving stale cached data masks the outage, perfectly preserving the user experience and revenue flow (e.g., showing slightly old product prices), but fundamentally violates data consistency, which can be catastrophic for transactional systems (e.g., showing a stale bank balance). Returning a 503 guarantees strict transactional correctness and prevents bad mutations, but entirely destroys the user experience.",
 ["Stale Cache: Preserves user experience and uptime, but severely violates data consistency", "HTTP 503: Guarantees strict transactional correctness and safety", "Tradeoff: Serving stale data is fine for product catalogs, but catastrophic for financial balances"],
 ["HTTP 503 causes the server to physically catch fire"]),

("BACKEND_RELIABILITY", "debug", "medium", "debugging", ["Fallback Pattern"],
 "An application connects to a Redis cache and a PostgreSQL database. During a Redis outage, you notice the application starts failing 100% of API requests, even though the data is safely persisted in PostgreSQL. Why did the cache outage cause a total system failure?",
 "The backend failed to implement the 'Fallback Pattern' (or Cache-Aside fallback). The code was poorly written to treat a Redis connection error as a fatal, unhandled exception. A resilient backend must gracefully catch the cache exception, log the degradation, and explicitly fallback to querying the primary PostgreSQL database to fulfill the request, keeping the system alive despite latency.",
 ["Failed to implement the 'Fallback Pattern' (Cache-Aside)", "Code treated a cache connection error as a fatal exception rather than a degradation", "Fix: Catch the cache error and gracefully fallback to querying the primary database"],
 ["Redis deleted the PostgreSQL database out of spite"]),

("BACKEND_RELIABILITY", "scenario", "hard", "scenario", ["Circuit Breakers", "Thundering Herd"],
 "A Circuit Breaker on a payment service trips 'Open' due to high latency. After 30s, it transitions to 'Half-Open' and allows one test request through. The request succeeds in 50ms. The breaker instantly snaps 'Closed' and allows 10,000 queued requests to hit the service simultaneously. The payment service instantly crashes again. How do you fix the Circuit Breaker logic?",
 "The circuit breaker lacks a 'Gradual Ramp-up' or requires a higher success threshold. Snapping instantly from 0 to 100% traffic based on a single successful request causes a Thundering Herd that instantly re-kills the struggling service. The Half-Open state must require a sustained percentage of successful requests (e.g., 10 successes over 5 seconds) or gradually ramp up traffic (10% -> 50% -> 100%).",
 ["Snapping from 0 to 100% traffic based on a single success causes a Thundering Herd", "The Half-Open state must require a sustained threshold of successful requests", "Fix: Implement a gradual traffic ramp-up (10% -> 50% -> 100%) to prove stability"],
 ["The circuit breaker needs to be glued shut"]),

("BACKEND_RELIABILITY", "implement", "medium", "implementation", ["Concurrency", "Resilience"],
 "A backend service must perform three independent external API calls to aggregate data for a dashboard. The APIs take 1s, 2s, and 3s respectively. How do you architect the backend to return in 3 seconds, and how do you handle the scenario where one API fails to ensure the dashboard still loads?",
 "You must execute the API calls concurrently (e.g., using `Promise.allSettled` in Node or Goroutines in Go). To handle failures resiliently, you do not instantly fail the whole request. You catch the failure of the specific API, substitute a default fallback value or `null` for that specific dashboard widget, and successfully return the aggregated data for the surviving APIs.",
 ["Execute the API calls concurrently (e.g., `Promise.allSettled`) to reduce total time to max(T)", "Do not fail the entire request if one API fails", "Catch individual failures and substitute default/fallback values to gracefully degrade"],
 ["Execute them sequentially and tell the user to wait 6 seconds"]),

("BACKEND_RELIABILITY", "tradeoff", "medium", "tradeoff", ["Retries"],
 "What is the operational tradeoff between implementing retries at the Application Layer (e.g., in the backend code) versus implementing retries at the Infrastructure Layer (e.g., inside an Istio Service Mesh)?",
 "Application-level retries are highly context-aware; they can intelligently inspect the business payload and decide not to retry a non-idempotent POST request, preventing data corruption. Infrastructure-level retries are transparent and apply globally without code changes, but they are generally 'dumb' and might blindly retry unsafe network requests unless strictly configured, potentially causing unintended side effects.",
 ["Application layer: Context-aware, can intelligently avoid retrying non-idempotent POSTs", "Infrastructure layer: Transparent and global without code changes", "Infrastructure tradeoff: 'Dumb' retries might blindly duplicate unsafe business transactions"],
 ["Infrastructure layer retries are physically faster through the cables"]),

("BACKEND_RELIABILITY", "explain", "easy", "concept", ["Idempotency"],
 "What is 'Idempotency' in the context of REST API design, and why is it absolutely critical for backend reliability?",
 "Idempotency guarantees that making the exact same API request multiple times (e.g., `PUT /users/123`) produces the exact same backend state as making it only once. It is critical for reliability because if a network connection drops mid-flight, the client can safely retry the request without fear of accidentally creating duplicate records, double-charging a credit card, or corrupting state.",
 ["Making the exact same API request multiple times produces the exact same backend state as once", "Crucial for network reliability; allows clients to safely retry dropped requests", "Prevents duplicate records, double-charging, or state corruption on retries"],
 ["It means the API is very important and omnipotent"]),

("BACKEND_RELIABILITY", "debug", "hard", "debugging", ["Timeouts", "Thread Pools"],
 "Your backend handles 5,000 requests/sec. A downstream service fails, so your code executes a fallback method returning a static JSON string. However, CPU spikes to 100% and the server crashes, even though returning a static string takes 0ms. You investigate and find the fallback is triggered by a Timeout exception. Why did it crash?",
 "The system failed to 'Fail-Fast' (e.g., the Circuit Breaker failed to open). Every single one of the 5,000 requests/sec is waiting the full Timeout duration (e.g., 2 seconds) *before* triggering the fallback. This instantly exhausts the entire thread pool and memory with 10,000 blocked threads doing absolutely nothing. The fallback logic is sound, but you must Open the Circuit to prevent thread blocking entirely.",
 ["Failed to 'Fail-Fast' (Circuit Breaker didn't open)", "5,000 requests/sec waiting the full 2s timeout exhausts the entire thread pool instantly", "You must open the circuit to bypass the timeout and execute the fallback immediately"],
 ["The static JSON string was too heavy to lift into memory"]),

("BACKEND_RELIABILITY", "scenario", "medium", "scenario", ["Context Cancellation"],
 "A mobile app makes an API request to generate a complex report. The user loses cellular connection and closes the app. The backend continues processing the complex report for another 45 seconds, wasting massive CPU and database resources. How do you architect the backend to prevent this?",
 "You must implement Request Cancellation (or Context Cancellation). When the client severs the TCP connection, the backend framework should detect the disconnected socket and cancel the execution Context. The backend application code and database drivers must explicitly listen for this Context Cancellation signal and instantly abort any ongoing CPU tasks or database queries.",
 ["Implement Request/Context Cancellation", "Detect the severed TCP connection and cancel the execution Context", "Application code and database queries must explicitly listen for the cancellation signal and abort"],
 ["Call the user's cell phone provider to re-establish the connection"]),

("BACKEND_RELIABILITY", "fundamentals", "easy", "concept", ["Load Shedding"],
 "In the context of backend overload protection, what is 'Load Shedding'?",
 "Load Shedding is an absolute survival mechanism where a backend server detects that its internal resources (CPU, memory, threads) are critically exhausted. To prevent a total cascading crash, the server universally and intentionally drops or rejects new incoming requests (often returning HTTP 503) regardless of the user, ensuring the server stays alive to process the requests it is already handling.",
 ["An absolute survival mechanism to prevent a total server crash under extreme load", "The server intentionally drops/rejects new incoming requests (returning HTTP 503)", "Prioritizes finishing in-flight requests and keeping the node alive over accepting new traffic"],
 ["It means deleting old data to shed database weight"]),

("BACKEND_RELIABILITY", "implement", "hard", "implementation", ["Bulkhead Pattern", "Load Shedding"],
 "A backend service exposes a critical `/checkout` endpoint and a non-critical `/recommendations` endpoint. During a spike, extreme traffic to the recommendations endpoint exhausts the server's HTTP connection pool, causing the checkout endpoint to fail. How do you architect the backend to prevent this?",
 "You must implement the Bulkhead Pattern or strict priority-based Load Shedding. You configure the web server or application framework to maintain two physically separate connection/thread pools (or strictly enforce concurrency limits): a small pool for `/recommendations` and a massive, guaranteed pool for `/checkout`. Even if the recommendation pool is completely saturated, the checkout pool remains pristine.",
 ["Implement the Bulkhead Pattern or priority-based Load Shedding", "Maintain physically separate thread/connection pools for critical vs non-critical endpoints", "Guarantees the critical `/checkout` pool remains pristine even if recommendations are saturated"],
 ["Tell users to stop checking recommendations during checkout"])
]
