"""Batch 32 Part 2 question content (Full Stack). Targeted Gap Generation."""

ROLE = "Full Stack Developer"

BUCKET_KEYS = {
    "END_TO_END_LATENCY": ("End-to-End Latency", "Performance Optimization", "Architecture", ["Full Stack Developer", "Frontend Developer", "Backend Developer"]),
}

Q = [
# ---------------- END_TO_END_LATENCY ----------------
("END_TO_END_LATENCY", "scenario", "medium", "scenario", ["Network", "Rendering"],
 "Users report a page takes 4 seconds to load. You check the backend logs, and the API response time is perfectly consistent at 50ms. You check the DB, and queries take 10ms. Where is the latency occurring, and how do you diagnose it?",
 "The latency is occurring in the network transport layer (DNS, TLS, massive payload transfer) or the client-side browser rendering (heavy JavaScript execution, main-thread blocking). You diagnose this using the browser's Network tab to inspect Time-to-First-Byte (TTFB) vs content download, and the Performance tab to profile JS rendering bottlenecks.",
 ["Latency is in the network transport layer or client-side browser rendering", "Diagnose network issues using the browser's Network tab (TTFB vs Download time)", "Diagnose rendering issues using the Performance tab (JavaScript execution, main-thread blocking)"],
 ["The backend logs are lying to make the backend engineers look good"]),

("END_TO_END_LATENCY", "debug", "hard", "debugging", ["CORS", "Preflight"],
 "A React frontend requests `/api/dashboard`. The backend processes it in 20ms. The browser Network tab shows it taking 1200ms. An identical request immediately preceding it takes 1180ms and returns no body. What architectural configuration is causing this latency?",
 "This is a CORS Preflight (`OPTIONS`) request penalty. Because the frontend and backend are on different origins and the request includes custom headers or a POST payload, the browser explicitly sends an `OPTIONS` request first to verify permissions. The latency is the round-trip of this preflight. Fix: Cache the preflight (`Access-Control-Max-Age`) or serve from the same origin.",
 ["CORS Preflight (`OPTIONS`) request penalty across different origins", "The browser forces a preflight round-trip to verify permissions before the actual request", "Fix: Cache the preflight response or serve the API and frontend from the same origin via proxy"],
 ["The browser was downloading an invisible tracking pixel"]),

("END_TO_END_LATENCY", "tradeoff", "medium", "tradeoff", ["SSR", "SPA", "Web Vitals"],
 "What is the end-to-end latency tradeoff of using Server-Side Rendering (SSR) versus a pure Single Page Application (SPA)?",
 "SSR delivers populated HTML immediately, drastically improving Time-To-First-Byte (TTFB) and First Contentful Paint (FCP) because the browser doesn't wait for JS. However, SSR delays Time-To-Interactive (TTI) because the server waits for DB queries, and the browser must still hydrate the JS. A pure SPA has a fast initial load but shows a blank spinner until heavy JS executes.",
 ["SSR: Drastically improves TTFB and FCP (delivers populated HTML immediately)", "SSR Tradeoff: Delays TTI (Time-To-Interactive) due to server-side DB waits and client hydration", "SPA: Fast initial load, but shows a blank spinner until heavy JS fetches data"],
 ["SSR physically sends the server to the user's house"]),

("END_TO_END_LATENCY", "implement", "hard", "implementation", ["Parallelization", "Data Fetching"],
 "A dashboard awaits the API, which sequentially queries the DB for Profile, Orders, and Balance, taking 600ms total (200ms each). How do you architect the full-stack data fetching to reduce this to ~200ms?",
 "The API backend must be refactored to execute the three independent database queries concurrently using `Promise.all()` (or async Goroutines). Alternatively, the frontend can be refactored to make three separate, parallel HTTP requests to distinct micro-endpoints (`/api/profile`, `/api/orders`). Both approaches eliminate the waterfall, bounding latency to the single slowest query.",
 ["Execute the three database queries concurrently using `Promise.all()` on the backend", "Alternatively, refactor the frontend to make three parallel HTTP requests to distinct micro-endpoints", "Eliminates the sequential waterfall, bounding total latency to the single slowest query"],
 ["Tell the user they don't really need to see their balance"]),

("END_TO_END_LATENCY", "explain", "easy", "concept", ["TTFB"],
 "In the context of frontend latency, what is 'Time to First Byte' (TTFB)?",
 "TTFB is the exact measurement of time from when the user's browser initiates an HTTP request to when it receives the very first byte of data from the server. It encompasses DNS lookup, TCP handshake, TLS negotiation, and the backend server's processing time. High TTFB indicates slow backend processing or extreme geographic network distance.",
 ["Time from browser initiating the request to receiving the very first byte of data", "Encompasses DNS, TCP, TLS, and backend processing time", "High TTFB indicates slow backend processing, slow DB queries, or geographic distance"],
 ["It measures how long it takes to bite into an apple"]),

("END_TO_END_LATENCY", "debug", "hard", "debugging", ["Cascading Failures", "Timeouts"],
 "An external 3rd-party API usually takes 50ms. Suddenly, it completely hangs. Within seconds, your own application's frontend crashes and the backend Node.js servers run out of memory. How did a slow external API crash your entire system?",
 "This is a Cascading Failure caused by a lack of timeouts and Circuit Breakers. Because the backend HTTP requests to the 3rd-party API had no explicit timeout, the Node.js event loop piled up thousands of unresolved promises and open sockets. Active requests queued indefinitely, exhausting memory. You must enforce strict HTTP timeouts and implement a Circuit Breaker.",
 ["Cascading Failure caused by a lack of strict HTTP timeouts and Circuit Breakers", "Unresolved promises and open sockets queued indefinitely, exhausting backend memory", "Fix: Enforce strict timeouts and implement a Circuit Breaker to fail-fast when degraded"],
 ["The 3rd party API sent a virus through the internet"]),

("END_TO_END_LATENCY", "scenario", "medium", "scenario", ["Pagination", "DOM"],
 "Your API returns a 5MB JSON array of 100,000 transactions. The DB query takes 100ms, but the frontend takes 6 seconds to render the table and the browser freezes. What are the two primary bottlenecks, and how do you fix them?",
 "The bottlenecks are Network Transfer Size (downloading 5MB raw JSON) and Client-Side Rendering (the browser locking the main thread parsing JSON and mounting 100k DOM nodes). The fix is to implement Server-Side Pagination (e.g., `LIMIT 50`). The API should only return the 50 visible rows, eliminating both the network bottleneck and DOM render freeze.",
 ["Bottleneck 1: Network Transfer Size (downloading massive 5MB JSON)", "Bottleneck 2: Client-Side Rendering (locking the main thread parsing/mounting 100k DOM nodes)", "Fix: Implement Server-Side Pagination to only return visible rows"],
 ["The monitor refresh rate is too low to display 100,000 items"]),

("END_TO_END_LATENCY", "tradeoff", "hard", "tradeoff", ["WebSockets", "SSE"],
 "When optimizing an interactive web app, what is the latency tradeoff of using WebSockets versus standard HTTP/2 Server-Sent Events (SSE) for server-to-client streaming?",
 "WebSockets provide full-duplex, bi-directional communication with incredibly low latency, but require managing stateful persistent TCP connections, custom sticky-session load balancing, and complex firewalls. HTTP/2 SSE is strictly unidirectional (server to client) and slightly higher latency, but operates over standard HTTP, making it trivially cacheable and natively supported by proxies.",
 ["WebSockets: Full-duplex/bi-directional, lowest latency, but requires stateful TCP management and sticky sessions", "SSE: Unidirectional (server-to-client), slightly higher latency", "SSE Tradeoff: Operates over standard HTTP (trivially cacheable, natively supported by proxies)"],
 ["WebSockets are literal physical sockets in the wall"]),

("END_TO_END_LATENCY", "implement", "medium", "implementation", ["Image CDN", "LCP"],
 "An e-commerce product image takes 2 seconds to download on mobile, destroying the 'Largest Contentful Paint' (LCP) metric. How do you implement a full-stack solution to optimize this specific image load time?",
 "You must use an Image CDN or dynamic resizing service. The frontend detects screen size/pixel ratio and constructs a specific URL (`cdn.com/img?w=400&format=webp`). The CDN dynamically resizes the massive original image to exactly 400px and converts it to a highly compressed modern format (WebP/AVIF), drastically reducing byte size and network latency.",
 ["Use an Image CDN or dynamic backend resizing service", "Frontend requests a specific size and format based on the device (`w=400&format=webp`)", "CDN resizes and converts to modern compressed formats (WebP/AVIF), drastically reducing payload size"],
 ["Make the image black and white so it uses less ink"]),

("END_TO_END_LATENCY", "debug", "medium", "debugging", ["Timeouts", "Retries"],
 "An API endpoint takes 50ms locally, but exactly 1050ms in production. The DB query takes 10ms. Frontend has no delays. What infrastructure configuration is causing a flat 1000ms delay?",
 "This indicates a synchronous retry loop or a DNS/network timeout in the backend infrastructure. The backend is likely attempting to connect to a caching layer (like Redis) or microservice, failing, waiting for exactly a 1000ms timeout, and then gracefully falling back to the database. The fallback succeeds in 10ms, masking the initial network timeout from standard logs.",
 ["Indicates a synchronous retry loop or fixed network timeout in the backend", "The backend tries a cache/service, hits a hard 1000ms timeout, then falls back to the DB", "The DB fallback succeeds, masking the initial timeout failure from standard application logs"],
 ["The server takes exactly 1 second to breathe between requests"]),

("END_TO_END_LATENCY", "explain", "easy", "concept", ["Waterfall Requests"],
 "What is a 'Waterfall Request' pattern in full-stack web development?",
 "A waterfall request pattern occurs when sequential network requests are blocked waiting for previous requests to finish. For example, downloading HTML triggers a JS bundle, which executes and fetches User ID, which then fetches User Orders. This creates a staggered 'waterfall' where total load time is the sum of every sequential request, instead of fetching concurrently.",
 ["Sequential network requests blocked waiting for previous requests to finish", "Example: Fetch HTML -> Fetch JS -> Fetch User ID -> Fetch Orders", "Total load time is the sum of all sequential requests rather than executing concurrently"],
 ["When a user physically drops their phone in a waterfall"]),

("END_TO_END_LATENCY", "scenario", "hard", "scenario", ["Optimistic UI"],
 "A mobile user on 3G clicks 'save profile'. It takes 3 seconds, making the app feel sluggish. The backend update takes 100ms. How do you architect the frontend to completely hide this network latency from the user?",
 "You must implement 'Optimistic UI Updates'. When the user clicks save, the frontend JS instantly updates the UI state (showing success) *before* the HTTP request finishes, assuming the network call will succeed. If the background network request eventually fails, the UI catches the error, reverts the state to the previous value, and shows an error toast.",
 ["Implement 'Optimistic UI Updates' (Optimistic Concurrency)", "Instantly update the frontend UI state assuming the background network call will succeed", "If the request eventually fails, revert the UI state and display an error toast"],
 ["Tell the user to upgrade to 5G immediately"]),

("END_TO_END_LATENCY", "tradeoff", "medium", "tradeoff", ["GraphQL", "REST", "N+1"],
 "When designing a full-stack API, what is the latency tradeoff of using GraphQL versus traditional REST for a mobile application?",
 "GraphQL drastically reduces mobile network latency by solving over-fetching; a single query retrieves deeply nested data (User + Orders + Reviews) in one round-trip, whereas REST requires multiple waterfall requests. The tradeoff is severe backend complexity: GraphQL is notoriously difficult to edge-cache (CDN), and nested queries cause catastrophic N+1 database bottlenecks without DataLoaders.",
 ["GraphQL: Reduces mobile network latency by fetching nested data in a single round-trip", "Tradeoff: GraphQL is notoriously difficult to edge-cache at the CDN layer", "Tradeoff: Complex queries cause catastrophic N+1 database performance bottlenecks on the backend"],
 ["GraphQL uses complicated math graphs, REST is just relaxing"]),

("END_TO_END_LATENCY", "implement", "hard", "implementation", ["Compression", "Nginx"],
 "Your API serves a 2MB static JSON file. You enable dynamic Gzip on your Nginx proxy. Payload drops to 300KB, but API response time *increases* by 200ms. How do you get both 300KB size AND a 10ms response time?",
 "The 200ms increase is the CPU cost of the proxy dynamically compressing the 2MB file on-the-fly for every request. You must implement 'Pre-compression'. During the CI/CD build step, statically compress the JSON into a `.json.gz` file. Configure Nginx with `gzip_static on;`. Nginx instantly serves the pre-compressed file from disk, bypassing the dynamic CPU penalty.",
 ["The 200ms latency is the CPU penalty of dynamic on-the-fly compression", "Implement 'Pre-compression' during the CI/CD build step (create `.json.gz` files)", "Configure proxy (`gzip_static on`) to serve the pre-compressed file directly from disk"],
 ["Squish the hard drive with a physical hydraulic press"]),

("END_TO_END_LATENCY", "debug", "medium", "debugging", ["Node.js", "Event Loop"],
 "A Node.js API parses a massive CSV upload. While parsing, health checks fail, and unrelated users' requests to different endpoints hang and timeout. Why does parsing a CSV break unrelated API requests?",
 "Node.js is fundamentally single-threaded. Massive CSV parsing is a synchronous, CPU-bound task that entirely blocks the main Event Loop. While crunching the CSV, the server is physically incapable of accepting, routing, or responding to other incoming network requests. You must offload heavy CPU tasks to a Worker Thread or background queue (Celery/Redis).",
 ["Node.js is fundamentally single-threaded; CPU-bound tasks block the main Event Loop", "While blocked, the server cannot accept or respond to any other incoming network requests", "Fix: Offload heavy CPU tasks to Worker Threads or a background message queue"],
 ["The CSV file was too heavy and broke the server's back"]),

("END_TO_END_LATENCY", "fundamentals", "easy", "concept", ["CDN", "Cache Hit Ratio"],
 "What is a 'CDN Cache Hit Ratio'?",
 "The Cache Hit Ratio is the percentage of total user requests successfully served directly from the Content Delivery Network's edge cache, without ever needing to contact your origin backend server. A high hit ratio (e.g., 95%) means massive latency reduction for geographically distributed users and significantly reduced compute load on your backend databases.",
 ["The percentage of user requests served directly from the CDN edge cache", "Requests do not require contacting the origin backend server", "High ratio means massive latency reduction and reduced backend compute load"],
 ["How many times a user hits the physical CDN box with a bat"]),

("END_TO_END_LATENCY", "scenario", "hard", "scenario", ["Edge Compute", "Geographic Latency"],
 "Users in Australia report 300ms latency for every API call. The servers are in Virginia, USA. Database queries take 5ms. A developer suggests deploying a database read-replica in Australia. Why won't this fix the latency, and what is the correct architecture?",
 "The latency is the physical speed-of-light network transit time across the ocean. Deploying an Australian database read-replica does nothing if the primary backend API compute server (Node/Python) is still in Virginia. To fix the latency, you must deploy the *backend API compute layer* to Australia alongside the read-replica to terminate TLS and execute logic geographically locally.",
 ["Latency is physical speed-of-light network transit time", "An Australian DB replica is useless if the HTTP API server is still in Virginia", "Fix: Deploy the backend API compute layer to Australia to terminate TLS locally"],
 ["Australia is upside down so the data falls out of the cables"])
]
