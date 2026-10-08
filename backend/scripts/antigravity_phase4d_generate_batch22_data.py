"""Batch 22 question content (Full Stack Developer). Antigravity-native, no Gemini API."""

ROLE = "Full Stack Developer"

BUCKET_KEYS = {
    "FS_INT": ("Frontend/Backend Integration", "CORS & HTTP", "Web Architecture", ["Frontend Developer", "Backend Developer"]),
    "FS_SEC": ("Application Security", "Auth & Vulnerabilities", "Security", ["Security Engineer"]),
    "FS_STATE": ("State Management", "Caching & Sync", "Web Architecture", ["Frontend Developer"]),
    "FS_DBUI": ("Database to UI", "Data Flow & Consistency", "Full Stack", ["Backend Developer"]),
    "FS_ASYNC": ("Asynchronous Workflows", "WebSockets & Background Jobs", "Web Architecture", ["Backend Developer"]),
    "FS_DEPLOY": ("Deployment & Architecture", "CI/CD & Versioning", "DevOps", ["DevOps / Cloud Engineer"]),
    "FS_DEBUG": ("End-to-End Debugging", "Tracing & Latency", "Observability", ["Site Reliability Engineer"]),
    "FS_PERF": ("Full Stack Performance", "Scaling & Bottlenecks", "Performance", ["Backend Developer", "Frontend Developer"]),
}

Q = [
# ---------------- FS_INT ----------------
("FS_INT", "explain", "easy", "concept", ["HTTP Semantics"],
 "Explain the purpose of a CORS Preflight Request (`OPTIONS`). Why does the browser send it?",
 "A CORS preflight request is an automatic `OPTIONS` request sent by the browser before a cross-origin 'complex' request (like a POST with a JSON body or custom headers). The browser sends it to ask the destination server if it permits the specific HTTP method and headers. If the server replies favorably, the browser proceeds with the actual request; otherwise, it blocks it to protect the server from unauthorized cross-origin actions.",
 ["Sent automatically by the browser before a complex cross-origin request", "Uses the HTTP OPTIONS method", "Asks the server for permission (methods/headers) before sending the actual data"],
 ["It is a request to book an airplane flight via an API"]),

("FS_INT", "scenario", "hard", "scenario", ["CORS", "Authentication"],
 "An API `GET /users` works perfectly when you test it via Postman or `curl`. However, when your frontend React app calls it, the browser blocks it with a CORS policy error. You check the backend, and it is explicitly sending `Access-Control-Allow-Origin: *`. What is the most likely reason the browser is still failing the request?",
 "The frontend is likely attempting to send credentials (like cookies or an Authorization header) by setting `credentials: 'include'` on the fetch request. The CORS specification strictly forbids using the wildcard `*` for the Allow-Origin header when credentials are included. The backend must explicitly return the exact origin (e.g., `https://myapp.com`) and add `Access-Control-Allow-Credentials: true`.",
 ["Frontend is trying to send credentials/cookies", "CORS specification forbids using wildcard `*` with credentials", "Backend must explicitly specify the exact origin and allow credentials"],
 ["Postman has a secret VIP agreement with the server"]),

("FS_INT", "debug", "medium", "debugging", ["HTTP Headers"],
 "Your frontend sends a `POST` request with JSON data, but the backend receives an empty body or null values. If you check the Network tab, the payload is definitely there. What HTTP header mismatch is likely causing the backend parser to ignore the body?",
 "The frontend is likely missing the `Content-Type: application/json` header in the request. Most backend frameworks (like Express or Django) use specific middleware to parse incoming bodies based on the Content-Type. If it defaults to `text/plain` or is missing entirely, the JSON parser ignores the payload, resulting in an empty or null body in the controller.",
 ["Missing the `Content-Type: application/json` header in the frontend request", "Backend middleware relies on this header to trigger the correct parser", "Without it, the backend ignores the JSON payload"],
 ["The JSON data evaporated during network transit"]),

("FS_INT", "fundamentals", "easy", "concept", ["HTTP Status Codes"],
 "What is the semantic difference between returning an HTTP 401 (Unauthorized) versus an HTTP 403 (Forbidden) from your backend API?",
 "HTTP 401 means 'Unauthenticated' (the server does not know who you are, please log in). HTTP 403 means 'Unauthorized' (the server knows exactly who you are, but you do not have the permissions/role required to access this specific resource).",
 ["401: Unauthenticated (You are not logged in / identity unknown)", "403: Forbidden (Identity known, but you lack permissions/roles)", "401 is about identity, 403 is about access rights"],
 ["401 means the server is broken, 403 means the database is broken"]),

("FS_INT", "tradeoff", "medium", "tradeoff", ["API Design"],
 "What are the full-stack tradeoffs of implementing API pagination using Offset/Limit versus Cursor-based pagination?",
 "Offset/Limit allows the frontend to easily jump to specific pages (e.g., Page 5), but it becomes incredibly slow on deep queries (databases must scan and skip rows) and suffers from skipped/duplicated data if rows are inserted during pagination. Cursor-based pagination uses a unique pointer (like an ID), making it extremely fast at scale and immune to data insertion shifts, but it completely prevents jumping to arbitrary pages.",
 ["Offset/Limit: enables jumping to arbitrary pages, but slow at scale and skips data if rows are inserted", "Cursor: extremely fast, immune to data shifting", "Cursor: prevents jumping to specific pages (only next/prev)"],
 ["Cursors require moving the physical computer mouse over the data"]),

("FS_INT", "scenario", "medium", "scenario", ["HTTP Semantics"],
 "A user clicks a 'Delete Account' button twice rapidly. The frontend sends two identical `DELETE /user/123` requests. The backend returns a 200 OK for the first request, and a 404 Not Found for the second. Is this behavior REST-compliant?",
 "Yes. In REST, the `DELETE` method is required to be Idempotent, meaning the *side-effect* on the server (the account being deleted) must be the same regardless of how many times the request is made. Returning a 404 on the second attempt is perfectly compliant, as the end state of the resource (it does not exist) is achieved safely.",
 ["Yes, it is REST-compliant", "DELETE must be Idempotent (the end state is the same regardless of repeat calls)", "Returning 404 is valid because the resource is successfully gone"],
 ["No, the server must crash if you delete twice"]),

("FS_INT", "implement", "medium", "implementation", ["File Downloads"],
 "You are building an endpoint to download a dynamically generated PDF. How do you instruct the browser to trigger a 'Save As' file download dialog rather than trying to render the raw PDF data directly in the current window?",
 "You must set the `Content-Disposition` HTTP header on the backend response to `attachment; filename=\"report.pdf\"`. This explicitly forces the browser to treat the payload as a downloadable file rather than attempting to display it inline.",
 ["Set the `Content-Disposition` HTTP header", "Use the value `attachment`", "Optionally provide the `filename` parameter"],
 ["Ask the user to right-click and save the screen"]),

# ---------------- FS_SEC ----------------
("FS_SEC", "tradeoff", "hard", "tradeoff", ["JWT Storage"],
 "When storing a JWT on the frontend, what are the security tradeoffs between storing it in `localStorage` versus an `HttpOnly` Cookie?",
 "Storing a JWT in `localStorage` makes it vulnerable to Cross-Site Scripting (XSS)—any malicious JavaScript can easily read it and steal the session. Storing it in an `HttpOnly` cookie prevents JavaScript from reading it entirely, neutralizing XSS theft, but it automatically attaches to every request, making the application vulnerable to Cross-Site Request Forgery (CSRF) unless explicitly mitigated with CSRF tokens or SameSite attributes.",
 ["localStorage: Vulnerable to XSS (JS can read and steal it)", "HttpOnly Cookie: Immune to XSS theft (JS cannot read it)", "HttpOnly Cookie: Vulnerable to CSRF (browser attaches it automatically)"],
 ["localStorage deletes data after 5 minutes"]),

("FS_SEC", "scenario", "medium", "scenario", ["CSRF"],
 "Your frontend stores an authentication token in an `HttpOnly` cookie. An attacker builds a malicious website that submits a hidden form to your backend `/transfer-funds` endpoint. Because the user is logged in, the browser automatically attaches the cookie, and the transfer succeeds. What vulnerability is this, and how do you fix it full-stack?",
 "This is a Cross-Site Request Forgery (CSRF) attack. The browser automatically sent the auth cookie despite the request originating from an attacker's domain. To fix it, you must configure the cookie with the `SameSite=Lax` or `SameSite=Strict` attribute to prevent cross-origin cookie sending, or implement a CSRF Token validation pattern on the backend.",
 ["Cross-Site Request Forgery (CSRF)", "Fix by setting the `SameSite=Lax` or `SameSite=Strict` attribute on the cookie", "Alternatively, implement a CSRF Token validation pattern"],
 ["The attacker guessed the user's password using HTML"]),

("FS_SEC", "debug", "medium", "debugging", ["XSS"],
 "A user copies and pastes a block of text into a comment section on your React app. When other users view the comment, a hidden `<script>` tag executes and steals their session. If React automatically escapes HTML by default, how did this XSS attack succeed?",
 "The frontend developer explicitly disabled React's built-in XSS protection by rendering the user input using the `dangerouslySetInnerHTML` attribute, or by bypassing React entirely and manually injecting the string directly into the DOM using vanilla JavaScript (`innerHTML`).",
 ["React automatically escapes standard variables to prevent XSS", "The developer explicitly used `dangerouslySetInnerHTML`", "Or the developer manually mutated the DOM using raw `innerHTML`"],
 ["React was offline when the comment was posted"]),

("FS_SEC", "fundamentals", "easy", "concept", ["Authentication"],
 "Explain the difference between Authentication (AuthN) and Authorization (AuthZ) in a full-stack web application.",
 "Authentication (AuthN) is the process of verifying a user's identity (e.g., checking a username/password to prove *who* they are). Authorization (AuthZ) is the process of verifying permissions (e.g., checking if the logged-in user has the 'Admin' role to decide *what* they are allowed to do).",
 ["Authentication: Verifying identity (Who are you?)", "Authorization: Verifying permissions (What are you allowed to do?)", "AuthN happens before AuthZ"],
 ["They are exactly the same thing but spelled differently"]),

("FS_SEC", "scenario", "hard", "scenario", ["Microservices Security"],
 "You have a microservices backend behind an API Gateway. The frontend passes a JWT to the Gateway. The Gateway verifies the JWT signature. How should the Gateway securely pass the user's identity to the internal downstream microservices?",
 "The Gateway should terminate the external JWT, and inject a trusted internal header (like `X-User-Id` or a new internally-signed token) into the request before routing it downstream. The internal microservices must be secured inside a private network (VPC/Service Mesh) and configured to trust these headers only if they originate explicitly from the API Gateway, preventing spoofing.",
 ["Gateway terminates the external JWT and extracts the identity", "Passes identity via trusted internal headers (e.g., `X-User-Id`)", "Internal network (VPC) ensures microservices only accept traffic from the Gateway to prevent header spoofing"],
 ["Just email the user ID to the microservice"]),

("FS_SEC", "explain", "medium", "concept", ["Validation"],
 "Why is it a dangerous security practice to rely solely on frontend Javascript validation (e.g., HTML5 `required` or Regex) for form submissions?",
 "Frontend validation is purely for User Experience (UX), providing instant feedback. It provides absolutely zero security. An attacker can easily bypass the frontend entirely by using tools like Postman, `curl`, or browser developer tools to send malicious payloads directly to the API endpoint. You MUST replicate and enforce all validation strictly on the backend.",
 ["Frontend validation is purely for UX/convenience, offering zero security", "Attackers bypass the browser entirely using Postman or curl", "Backend must independently validate and sanitize all incoming payloads"],
 ["Javascript validation is unhackable due to encryption"]),

("FS_SEC", "implement", "medium", "implementation", ["Rate Limiting"],
 "Your API is receiving a massive brute-force password-guessing attack from thousands of different IP addresses. Standard IP-based rate limiting is failing to stop it. What application-layer rate limiting strategy should you implement?",
 "Since the attack is distributed across many IPs (a botnet), IP rate limiting fails. You must implement rate limiting based on the requested resource itself: Rate limit by the 'Username' or 'Email Address' being attempted. If a specific account is targeted more than 5 times a minute, lock the account temporarily, regardless of how many different IPs the requests come from.",
 ["Standard IP limiting fails against distributed botnets", "Implement rate limiting based on the specific Username or Email Address", "Lock the targeted account temporarily after N failed attempts, regardless of IP"],
 ["Unplug the router from the wall"]),

# ---------------- FS_STATE ----------------
("FS_STATE", "scenario", "hard", "scenario", ["Caching Layers"],
 "A user updates their profile picture. The backend confirms the database was updated, and the React frontend immediately re-fetches the user data. However, the old profile picture is still displayed on the screen. What caching layers could be causing this stale data issue?",
 "Stale data can hide in multiple layers: 1) Browser Cache (the browser cached the image URL aggressively and didn't re-download it). 2) CDN/Edge Cache (Cloudflare cached the image globally and hasn't purged it). 3) Frontend State Cache (React Query/Apollo returned a cached memory object without hitting the network). You fix this via Cache-Control headers, cache invalidation, or cache-busting (appending `?v=123` to the image URL).",
 ["Browser Cache (aggressively caching the identical image URL)", "CDN/Edge Cache (intermediate caching proxy holding stale assets)", "Frontend State Cache (e.g., React Query returning stale memory data)", "Fix via Cache-Control, cache purging, or URL cache-busting parameters"],
 ["The database is running too slow to update the picture"]),

("FS_STATE", "tradeoff", "medium", "tradeoff", ["State Management"],
 "What are the full-stack tradeoffs of managing all application state in a global store (like Redux) versus managing server-state using a dedicated fetching library (like React Query or SWR)?",
 "Redux forces you to manually write immense amounts of boilerplate to handle loading states, errors, caching, and background refetching for API data. Dedicated libraries (React Query) abstract away all server-state complexity, handling caching, deduplication, and stale-while-revalidate automatically out of the box, but they reduce the utility of the global store to only handle true client-side state (like UI toggles).",
 ["Redux requires massive boilerplate for loading/error/cache states of API data", "React Query/SWR handles caching, deduplication, and refetching automatically", "React Query shifts server-state out of the global store, reserving Redux only for UI state"],
 ["Redux is illegal to use in production apps"]),

("FS_STATE", "explain", "easy", "concept", ["HTTP Headers"],
 "What is the purpose of an ETag (Entity Tag) in HTTP, and how does it optimize frontend-backend data transfer?",
 "An ETag is a unique hash representing the current version of a resource on the backend. When the frontend requests data, the backend sends the ETag. On the next request, the frontend sends `If-None-Match: <ETag>`. If the data hasn't changed, the backend returns a tiny `304 Not Modified` response without sending the heavy payload again, drastically saving bandwidth and frontend processing time.",
 ["A unique hash representing the current version of a backend resource", "Frontend sends it back using `If-None-Match`", "If unchanged, backend returns `304 Not Modified` with empty body, saving massive bandwidth"],
 ["It is an electronic tag used to track the physical location of the server"]),

("FS_STATE", "debug", "medium", "debugging", ["Build Pipelines"],
 "You deploy a new frontend build, but users complain the app is totally broken, showing a blank white screen. Upon investigation, they are loading the new `index.html`, but their browser is using a heavily cached, old `main.js` file from a week ago. How do you permanently fix this build pipeline issue?",
 "You must implement Cache Busting via file hashing in your bundler (Webpack/Vite). The bundler will append a unique hash of the file's contents to the filename (e.g., `main.[contenthash].js`). When you deploy an update, the filename physically changes, forcing the browser to download the new file immediately, while still allowing aggressive caching of unchanged assets.",
 ["Implement Cache Busting via file hashing in the bundler (e.g., Webpack/Vite)", "Appends a unique content hash to the filename (e.g., `main.[hash].js`)", "Changing filenames forces the browser to bypass the cache entirely for new deployments"],
 ["Tell all users to press F5 100 times to fix the cache"]),

("FS_STATE", "implement", "medium", "implementation", ["CDN Caching"],
 "You have a highly read-heavy public endpoint `/api/articles`. You put a CDN (like Cloudflare) in front of it. How do you specifically instruct the CDN to cache the JSON response for 5 minutes, but force the user's browser to never cache it locally?",
 "You must configure the HTTP `Cache-Control` header on the backend response. To instruct the CDN (shared cache), use `s-maxage=300` (5 minutes). To instruct the browser (local cache), use `max-age=0` (or `no-cache`). The final header looks like: `Cache-Control: max-age=0, s-maxage=300`.",
 ["Configure the `Cache-Control` HTTP header", "Use `s-maxage=300` to tell the shared CDN to cache for 5 minutes", "Use `max-age=0` or `no-cache` to forbid the user's browser from caching it locally"],
 ["Send an email to the CEO of Cloudflare asking them to cache it"]),

("FS_STATE", "scenario", "medium", "scenario", ["State Syncing"],
 "A user opens your web app in two different browser tabs. In Tab 1, they log out. In Tab 2, they try to submit a form, which hits a 401 Unauthorized error. How do you gracefully handle this cross-tab state mismatch on the frontend?",
 "To proactively handle this, you can listen to the `storage` event on the `window` object; when Tab 1 clears the auth token from localStorage, Tab 2 instantly detects the event and forces a local logout/redirect. Reactively, you should configure a global Axios/Fetch interceptor to catch any 401 response and automatically redirect the user to the login page, rather than crashing the form.",
 ["Proactive: Listen to the `storage` event to detect localStorage token deletion across tabs", "Reactive: Use a global API interceptor to catch 401 Unauthorized errors", "Automatically redirect the user to the login screen instead of crashing"],
 ["Just disable multiple tabs in the browser settings"]),

# ---------------- FS_DBUI ----------------
("FS_DBUI", "fundamentals", "easy", "concept", ["ORM Performance"],
 "What is the 'N+1 Query Problem', and how does an ORM commonly cause it in a full-stack application?",
 "The N+1 problem occurs when an application executes one database query to retrieve a list of 'N' parent records, and then explicitly executes an additional query for each individual parent to fetch their child records (resulting in N + 1 total queries). ORMs cause this via 'Lazy Loading', where looping over the parent list in the backend code silently triggers a new database trip for every single iteration.",
 ["Retrieving N parent records, then executing N individual queries to fetch children", "Causes massive database round-trip latency (N+1 total queries)", "ORMs cause this via Lazy Loading when looping over relationships"],
 ["It means the database requires N+1 passwords to log in"]),

("FS_DBUI", "scenario", "hard", "scenario", ["Concurrency"],
 "A frontend form requires a username to be unique. It checks `GET /api/check-username`. The API returns 'available'. The user clicks submit. At the exact same millisecond, another user submits the exact same username. Both requests pass the backend ORM check and attempt to save. How do you guarantee the database doesn't create duplicate usernames?",
 "You cannot rely entirely on application-layer checks for concurrency safety, as race conditions will bypass them. You MUST enforce a `UNIQUE` constraint on the username column directly at the database schema level. The database will process the transactions atomically; the first will succeed, and the second will throw a definitive constraint violation error, which the backend can catch and return to the frontend.",
 ["Application-layer checks are vulnerable to race conditions", "Must enforce a `UNIQUE` constraint at the database schema level", "The database guarantees atomicity; the second attempt will throw a safe constraint error"],
 ["Just ask the users nicely not to click at the exact same time"]),

("FS_DBUI", "tradeoff", "medium", "tradeoff", ["Search Architecture"],
 "When building a search feature, what are the tradeoffs of filtering a list entirely on the frontend (client-side search) versus querying the backend database for every keystroke (server-side search)?",
 "Client-side search requires sending the entire dataset to the browser upfront; it offers instant, zero-latency filtering and works offline, but crashes the browser's memory on massive datasets and exposes all data. Server-side search handles millions of rows effortlessly, keeps data secure, and minimizes frontend memory, but introduces network latency on every keystroke and heavily loads the backend database (requiring debouncing).",
 ["Client-side: Instant zero-latency filtering, but crashes browser memory on large datasets and exposes data", "Server-side: Handles massive datasets effortlessly, keeps data secure", "Server-side: Introduces network latency per keystroke, requires debouncing to protect backend"],
 ["Client side search deletes the backend database to save space"]),

("FS_DBUI", "debug", "medium", "debugging", ["Frontend Performance"],
 "A backend API performs a database query returning 10,000 rows, serializes it to JSON, and sends it to the frontend. The frontend renders it into a massive HTML table. The browser completely freezes. Which specific layer (DB, Network, or DOM) usually causes the browser to lock up, and how do you fix it?",
 "The DOM (Document Object Model) rendering layer causes the freeze. Browsers can easily download and parse large JSON objects, but attempting to construct and render 10,000 complex DOM nodes simultaneously locks the main UI thread. You fix this by implementing Server-Side Pagination, or if all data must be loaded, using UI Virtualization (e.g., `react-window`) to only render the 20 rows currently visible on screen.",
 ["The DOM rendering layer causes the browser to freeze", "Constructing 10,000 DOM nodes simultaneously locks the main UI thread", "Fix via backend Pagination or frontend UI Virtualization (rendering only visible rows)"],
 ["The database froze because it got too cold"]),

("FS_DBUI", "implement", "medium", "implementation", ["Transactions"],
 "You are building a full-stack e-commerce checkout. The frontend sends an order to the backend. The backend must deduct inventory, charge a Stripe credit card, and save the order. If the credit card fails, the inventory must not be deducted. How do you architect this sequence safely?",
 "You must use Database Transactions and orchestrate the external API carefully. Wrap the inventory deduction and order creation in a database transaction. Then, attempt the Stripe charge. If Stripe succeeds, `COMMIT` the transaction. If Stripe fails (or the server crashes mid-flight), issue a `ROLLBACK` to restore the inventory. Alternatively, use Stripe Idempotency keys to safely retry failed network states.",
 ["Wrap database writes (inventory, order) in a Transaction", "Call external API (Stripe); if it fails, ROLLBACK the database transaction", "If successful, COMMIT the transaction. Use Idempotency keys for network retries"],
 ["Just deduct the inventory anyway and send them a free product"]),

("FS_DBUI", "explain", "medium", "concept", ["Optimistic UI"],
 "Explain how 'Optimistic UI Updates' work. What must the frontend do if the underlying backend request ultimately fails?",
 "Optimistic updates instantly mutate the frontend UI state (e.g., clicking 'Like' instantly turns the button blue) before the backend API confirms the action was successful, providing a hyper-responsive user experience. However, the frontend must cache the previous state. If the API request ultimately fails, the frontend must catch the error, show a toast notification, and explicitly roll back the UI to the cached previous state.",
 ["Instantly updates UI state before the backend API confirms success", "Provides a hyper-responsive, zero-latency user experience", "Must cache previous state; if API fails, the UI must rollback to the previous state and alert the user"],
 ["The UI hopes the user is optimistic and happy today"]),

# ---------------- FS_ASYNC ----------------
("FS_ASYNC", "fundamentals", "easy", "concept", ["WebSockets"],
 "What is the fundamental difference between standard HTTP polling and a WebSocket connection for real-time full-stack features?",
 "HTTP polling requires the client to repeatedly open and close new connections to ask the server 'Are there updates?' every few seconds, causing massive network overhead and latency. A WebSocket establishes a single, persistent, bi-directional TCP connection. The server can actively push data to the client the exact millisecond an event occurs, resulting in zero overhead and true real-time latency.",
 ["Polling: Client repeatedly opens/closes HTTP requests asking for updates, causing heavy overhead", "WebSocket: Single, persistent, bi-directional TCP connection", "Server pushes data instantly, eliminating overhead and achieving true real-time latency"],
 ["WebSockets are made of physical string and tin cans"]),

("FS_ASYNC", "scenario", "hard", "scenario", ["File Uploads"],
 "A user uploads a 5GB video file via a React frontend. If they upload it directly to your Node/Python backend API, it locks up the server and consumes all RAM. How do you re-architect the upload flow to completely bypass your backend server?",
 "You architect a Direct-to-Cloud upload flow using Presigned URLs. The frontend requests an upload ticket from the backend. The backend authenticates the user and generates a temporary, secure Presigned URL (e.g., to AWS S3). The frontend then uploads the 5GB file directly to S3, completely bypassing the backend server. S3 then triggers a webhook back to your server confirming completion.",
 ["Use Direct-to-Cloud uploads via Presigned URLs", "Backend authenticates and returns a temporary secure S3 URL to the frontend", "Frontend uploads massive file directly to cloud storage, bypassing backend compute entirely"],
 ["Break the video into 10 million separate 1-byte API requests"]),

("FS_ASYNC", "debug", "medium", "debugging", ["Async Architectures"],
 "Your frontend submits a 'Generate Monthly Report' request. The backend takes 45 seconds to generate the PDF and return it. The browser consistently cuts the connection at exactly 30 seconds, showing a timeout error. How do you redesign this synchronous flow to be asynchronous?",
 "Browsers and Load Balancers strictly timeout long-lived synchronous HTTP requests. You must re-architect to an asynchronous flow: The frontend submits the request. The backend queues a background job (e.g., Celery/Sidekiq) and instantly returns a `202 Accepted` with a Job ID. The frontend then either polls a `/status/{job_id}` endpoint or listens on a WebSocket until the job finishes and returns the PDF URL.",
 ["Browsers/Load Balancers forcefully timeout long synchronous HTTP requests", "Backend should queue a background job and instantly return `202 Accepted` with a Job ID", "Frontend polls a status endpoint or uses WebSockets to retrieve the final result"],
 ["Tell the user to buy a faster internet connection"]),

("FS_ASYNC", "tradeoff", "medium", "tradeoff", ["Realtime Systems"],
 "What are the tradeoffs between using WebSockets versus Server-Sent Events (SSE) for streaming real-time notifications to a web client?",
 "WebSockets provide true bi-directional communication (client can send and receive) and low latency, but they require maintaining a persistent stateful connection on the server, complicating load balancing and scaling. Server-Sent Events (SSE) are unidirectional (server to client only), but they run over standard HTTP, making them vastly easier to scale, cache, proxy, and load-balance using existing infrastructure.",
 ["WebSockets: Bi-directional, low latency, but stateful and difficult to load-balance/scale", "SSE: Unidirectional (server-to-client only) real-time stream", "SSE: Runs over standard HTTP, making it trivial to proxy, load-balance, and scale"],
 ["SSE requires sending an email to the server"]),

("FS_ASYNC", "implement", "medium", "implementation", ["Background Jobs"],
 "You have a background job worker processing image thumbnails. Once the job finishes, how does the frontend (which is currently looking at a loading spinner) know the image is ready without constantly polling the database?",
 "You must use an event-driven push architecture. When the background worker finishes, it publishes a 'job_complete' event to a message broker (like Redis Pub/Sub). Your web server subscribes to this channel, receives the event, and pushes it over an active WebSocket connection specifically to the user's browser, which intercepts the message and removes the loading spinner.",
 ["Background worker publishes a completion event to a message broker (e.g., Redis Pub/Sub)", "Web server subscribes to the broker and pushes the event over a WebSocket to the client", "Eliminates database polling entirely via event-driven architecture"],
 ["The frontend guesses when it's done and removes the spinner"]),

("FS_ASYNC", "scenario", "medium", "scenario", ["Idempotency"],
 "A user double-clicks a 'Submit Payment' button. The frontend successfully disables the button after the first click, but because of a tiny rendering delay, two identical HTTP POST requests are sent. How do you handle this defensively on the backend to prevent charging the user twice?",
 "Frontend UI disables are insufficient against network races. You must implement Backend Idempotency. The frontend generates a unique UUID (Idempotency Key) when the checkout page loads, and sends it in the header of the POST request. The backend checks if it has already processed this exact key. If it sees the key a second time, it safely ignores the execution and returns the cached success response of the first attempt.",
 ["Implement Backend Idempotency using unique Idempotency Keys", "Frontend generates a UUID and sends it with the request", "Backend checks the key; if it's a duplicate, it bypasses execution and returns the cached result"],
 ["Just charge them twice and hope they don't look at their bank statement"]),

# ---------------- FS_DEPLOY ----------------
("FS_DEPLOY", "fundamentals", "easy", "concept", ["Reverse Proxies"],
 "What is a Reverse Proxy (like Nginx), and what role does it play when placed in front of a Node.js or Python web server?",
 "A reverse proxy sits in front of the application server to handle internet-facing tasks that app servers are bad at. It terminates SSL/HTTPS connections, serves static files (HTML/CSS/Images) directly with extreme speed, acts as a load balancer to distribute traffic across multiple app servers, and provides a layer of security buffering against DDoS attacks.",
 ["Sits in front of the application server to handle internet-facing tasks", "Terminates SSL/HTTPS and serves static files incredibly fast", "Acts as a load balancer and security buffer"],
 ["It puts the server in reverse gear to run code backwards"]),

("FS_DEPLOY", "scenario", "hard", "scenario", ["Zero Downtime Deployment"],
 "You have a Single Page Application (SPA) deployed to AWS S3 + CloudFront. You deploy a backend database migration that drops a column, and you deploy the new API and Frontend simultaneously. For 10 minutes, users complain the app is broken. What deployment sequencing error caused this outage?",
 "You violated backward compatibility during deployment. Users who had the site open before the deployment have the *old* frontend cached in their browser. They click a button, sending an old API payload to the *new* API, which crashes because the database column is gone. You must NEVER drop columns in a single step. You must decouple migrations: 1) Deploy new API that ignores the column, 2) Deploy new Frontend, 3) Wait for cache expiry, 4) Drop the column days later.",
 ["Violated backward compatibility; old cached frontends crashed against the new API/DB", "Never drop database columns in a single deployment step", "Sequence: Deploy compatible API -> Deploy Frontend -> Wait for cache expiry -> Drop column later"],
 ["AWS S3 broke the internet again"]),

("FS_DEPLOY", "explain", "medium", "concept", ["Graceful Degradation"],
 "Explain the concept of 'Graceful Degradation' in a full-stack web application. Give an example involving a third-party API outage.",
 "Graceful degradation ensures that if a non-critical component fails, the core application continues to function rather than throwing a catastrophic 500 error. For example, if a third-party Recommendation Engine API goes down, the backend catches the network timeout, logs the error, and instead of crashing the homepage, returns a hardcoded list of 'Trending Products' so the user can still browse and checkout seamlessly.",
 ["Core application continues functioning when non-critical components fail", "Prevents catastrophic total system crashes (500 errors)", "Example: If recommendation API fails, catch the error and return a static fallback list"],
 ["It means deleting the app gracefully when it gets too old"]),

("FS_DEPLOY", "tradeoff", "medium", "tradeoff", ["Frontend Deployment"],
 "What are the tradeoffs between embedding your frontend build files directly inside your backend server's static folder (e.g., serving React via Django/Express) versus deploying the frontend entirely separately to a CDN?",
 "Embedding the frontend provides a highly simplified, single-server deployment without CORS issues, but forces the backend compute server to waste resources serving static files, coupling release cycles together. Deploying to a CDN offers blistering global load times, zero load on the backend, and decoupled deployments, but introduces complex CORS configurations and requires orchestrating two distinct CI/CD pipelines.",
 ["Embedded: Simple single-server deployment, no CORS issues, but wastes backend compute serving static files", "CDN: Blistering global load times, zero backend load, decoupled deployments", "CDN: Requires complex CORS configuration and dual CI/CD pipelines"],
 ["CDNs are slower because the data travels further away"]),

("FS_DEPLOY", "debug", "medium", "debugging", ["Client-Side Routing"],
 "You deploy a React app using React Router (client-side routing) to a static hosting provider. Navigating via links works perfectly. However, if a user refreshes the page on `/dashboard`, they get a 404 Not Found error from the server. How do you fix this hosting configuration?",
 "The static server is looking for a physical file named `dashboard.html` on the hard drive, which doesn't exist because React handles routing in JavaScript. You must configure the hosting provider (or Nginx/Apache) to implement a 'Catch-All' route (Rewrite Rule) that redirects all 404 errors back to `index.html`, allowing React Router to boot up and render the correct view.",
 ["Server looks for a physical `dashboard.html` file and 404s", "React Router handles routing purely in JavaScript on the client side", "Fix by configuring a Catch-All route on the server to redirect all traffic to `index.html`"],
 ["The React router got unplugged from the wall"]),

("FS_DEPLOY", "implement", "medium", "implementation", ["API Versioning"],
 "You need to introduce a breaking change to a REST API payload structure. You cannot force all users to refresh their browser tabs instantly. How do you safely roll out this change?",
 "You must implement API Versioning. Instead of overwriting the endpoint, you create a new endpoint (e.g., `/api/v2/users`) with the new payload structure. The frontend deployment is updated to point to `v2`. The old endpoint (`/api/v1/users`) is kept alive and maintained on the backend, allowing users with old cached browser tabs (or old mobile app versions) to continue functioning until they refresh.",
 ["Implement API Versioning (e.g., `/api/v1/` vs `/api/v2/`)", "Keep the old endpoint alive to serve stale clients", "Update the new frontend deployment to consume the v2 endpoint safely"],
 ["Just shut the servers down until everyone refreshes their page"]),

# ---------------- FS_DEBUG ----------------
("FS_DEBUG", "fundamentals", "easy", "concept", ["Distributed Tracing"],
 "What is 'Distributed Tracing', and why is it essential for debugging modern full-stack microservice architectures?",
 "Distributed Tracing tracks a single user request as it traverses across multiple different servers, microservices, and databases. It attaches a unique 'Trace ID' to the initial frontend request. By passing this ID downstream, engineers can visualize the exact timeline of the request, instantly pinpointing exactly which specific microservice or database query caused a latency spike or error.",
 ["Tracks a single request as it traverses across multiple microservices/databases", "Uses a unique Trace ID attached at the frontend origin", "Visualizes the request timeline to pinpoint exactly which service caused latency/errors"],
 ["It tracks the physical GPS location of the server racks"]),

("FS_DEBUG", "scenario", "hard", "scenario", ["Latency Investigation"],
 "A user reports that logging into your app takes 15 seconds. You check the backend logs, and the `/login` endpoint executes in 50ms. You check the database, and the query takes 10ms. Where else in the full-stack request lifecycle could this massive 15-second delay be hiding?",
 "The delay is outside the backend compute execution. Likely culprits: 1) The frontend is making a massive, unoptimized JS bundle download before even rendering the login button. 2) DNS resolution or SSL handshake latency. 3) The backend is making an unlogged synchronous call to a third-party API (like sending a welcome email via SendGrid) that is timing out before returning the HTTP response. 4) Severe packet loss on the user's ISP.",
 ["Frontend rendering block or massive JS bundle parsing delay", "Unlogged synchronous calls to third-party APIs (e.g., emailing services) timing out", "Network-level issues: DNS resolution, SSL handshakes, or user packet loss"],
 ["The database took a 14 second nap before responding"]),

("FS_DEBUG", "explain", "medium", "concept", ["Observability"],
 "What is the purpose of a 'Correlation ID' (or Request ID) header passed from the frontend to the backend?",
 "A Correlation ID is a unique UUID generated by the frontend for a specific action. When the backend receives it, it includes this ID in every single log statement related to that request. If an error occurs, engineers can search the central logging system (e.g., Datadog, Splunk) for that specific UUID and instantly see the entire lifecycle of the request without digging through thousands of concurrent server logs.",
 ["Unique UUID generated by the frontend to track a specific request", "Included in all backend log statements related to that execution", "Allows engineers to filter central logs and instantly trace the lifecycle of a specific error"],
 ["It correlates the user's zodiac sign with the database schema"]),

("FS_DEBUG", "debug", "medium", "debugging", ["Cookies & CORS"],
 "A web app works perfectly in Chrome but fails completely in Safari. The API calls are identical. You discover Safari is aggressively blocking third-party cookies, breaking your authentication. Why would your backend authentication rely on a 'third-party' cookie, and how do you fix it?",
 "This occurs because the frontend and backend are hosted on completely different root domains (e.g., `myapp.com` and `api-server.net`). Browsers consider cookies set by `api-server.net` on `myapp.com` as cross-site (third-party) trackers, which Safari blocks by default. You fix this by hosting the API on a subdomain of the frontend (e.g., `api.myapp.com`), making the cookies 'first-party'.",
 ["Frontend and backend are hosted on completely different root domains", "Browsers (like Safari) block these as cross-site tracking cookies by default", "Fix by hosting the backend on a subdomain (e.g., `api.myapp.com`) to make cookies first-party"],
 ["Safari randomly deletes cookies for fun"]),

("FS_DEBUG", "tradeoff", "medium", "tradeoff", ["Error Handling"],
 "When an API endpoint fails due to a database outage, what are the tradeoffs of returning a generic '500 Internal Server Error' to the frontend versus returning the raw database stack trace?",
 "Returning a stack trace provides the frontend developer with instant, perfect debugging context in the browser console, but creates a catastrophic security vulnerability, leaking table names, SQL queries, and infrastructure details to malicious attackers. Returning a generic 500 is completely secure, but requires developers to dig through backend logs using Correlation IDs to diagnose the actual problem.",
 ["Stack trace: provides instant debugging context, but causes catastrophic security leaks (SQL schemas)", "Generic 500: Completely secure against information disclosure", "Generic 500: Requires developers to use Correlation IDs and search backend logs to diagnose"],
 ["Stack traces use too much bandwidth on mobile devices"]),

("FS_DEBUG", "scenario", "medium", "scenario", ["Global Latency"],
 "Users in Australia complain your web app is unbearably slow. Your servers are in Virginia, USA. The database queries are incredibly optimized (5ms). How do you architect a solution to reduce the latency for Australian users without completely replicating the database globally?",
 "The latency is governed by the speed of light (ping time from Australia to Virginia is ~250ms). To mitigate this, put the frontend assets entirely on a global CDN to ensure instant initial rendering. For the API, cache heavily-read, non-personalized endpoints at the Edge (CDN level). For dynamic data, consider edge functions or read-replicas in a closer region (e.g., Sydney) while routing writes back to Virginia.",
 ["Latency is limited by physics/network distance (ping time)", "Host all static frontend assets on a global CDN", "Cache heavily-read API endpoints at Edge nodes, or use regional read-replicas"],
 ["Move the country of Australia closer to Virginia"]),

# ---------------- FS_PERF ----------------
("FS_PERF", "fundamentals", "easy", "concept", ["Scaling"],
 "What is 'Horizontal Scaling' compared to 'Vertical Scaling' when applied to a backend web server?",
 "Vertical scaling means making a single server stronger by adding more RAM or CPU power (scaling up); it is simple but eventually hits a hardware limit and represents a single point of failure. Horizontal scaling means adding more independent servers to the pool behind a load balancer (scaling out); it offers infinite scalability and high availability, but introduces complexity in maintaining state (sessions) across servers.",
 ["Vertical (Up): Adding more CPU/RAM to a single machine (hits hardware limits, single point of failure)", "Horizontal (Out): Adding more servers behind a load balancer", "Horizontal provides infinite scale but requires stateless architecture"],
 ["Horizontal scaling means turning the server physically on its side"]),

("FS_PERF", "scenario", "hard", "scenario", ["Session State"],
 "You horizontally scale your backend Node.js API from 1 server to 5 servers behind a Load Balancer to handle traffic. Instantly, users start randomly getting logged out as they navigate between pages. What architectural state issue did scaling introduce?",
 "The original server stored user login sessions 'In-Memory'. When the Load Balancer round-robins the user's second request to Server #2, Server #2 has no memory of the session and rejects the request as unauthorized. You must architect a stateless backend by moving session storage to a centralized, shared cache (like Redis) or using stateless JWTs.",
 ["Original server stored sessions locally 'In-Memory'", "Load balancer sent subsequent requests to a new server lacking that memory state", "Fix by making servers stateless using a centralized Redis store or JWTs"],
 ["The servers got confused and forgot the passwords"]),

("FS_PERF", "implement", "medium", "implementation", ["API Optimization"],
 "Your full-stack app pulls a list of 500 products. The database query takes 10ms. However, fetching this data via the API takes 2 seconds and uses 5MB of bandwidth. How do you optimize this without adding caching or pagination?",
 "The API is 'Over-fetching'—returning every single column (including massive description text or binary image data) when the UI likely only needs the Product ID, Name, and Price. You fix this by implementing Sparse Fieldsets in REST (e.g., `?fields=id,name,price`), defining explicit projection queries in the ORM, or migrating the endpoint to GraphQL so the frontend dictates exactly what minimal data is returned.",
 ["The API is Over-fetching massive unnecessary text/binary columns", "Implement Sparse Fieldsets in REST (e.g., `?fields=id,name`) or use GraphQL", "Apply projection queries in the ORM to prevent fetching unused columns from the DB"],
 ["Zip the database and email it to the user"]),

("FS_PERF", "tradeoff", "medium", "tradeoff", ["Rendering Architecture"],
 "What are the tradeoffs between Server-Side Rendering (SSR) and Client-Side Rendering (CSR) regarding initial page load performance and SEO?",
 "SSR (e.g., Next.js) generates full HTML on the server; it provides perfect SEO (crawlers see instant content) and a blazing fast First Contentful Paint, but increases server compute costs and delays interactivity until JS hydrates. CSR (standard React) sends a blank HTML file and renders via JS; it is incredibly cheap to host and highly interactive once loaded, but causes terrible SEO and a slow initial blank screen.",
 ["SSR: Perfect SEO, fast initial paint, but heavy server compute and delayed interactivity", "CSR: Cheap static hosting, fast interactions, but terrible SEO and slow initial blank screen", "SSR shifts rendering cost to backend, CSR shifts it to the user's device"],
 ["SSR means the server reads the website out loud to the user"]),

("FS_PERF", "debug", "medium", "debugging", ["Frontend Optimization"],
 "You implement a 'Search as you type' feature in your React frontend. Every time the user types a letter, the frontend fires a database query. A user typing 'macbook' rapidly fires 7 heavy queries, crashing the backend. How do you fix this on the frontend?",
 "You must implement 'Debouncing' on the input handler. Debouncing delays the execution of the API call until the user has stopped typing for a specified amount of time (e.g., 300 milliseconds). If they type the 7 letters of 'macbook' rapidly, the timer resets on every keystroke, and only one single API call is sent to the backend when they pause.",
 ["Implement Debouncing on the input event handler", "Delays execution until the user stops typing for X milliseconds (e.g., 300ms)", "Prevents network spam by collapsing rapid keystrokes into a single API call"],
 ["Tell the backend database to run faster"]),

("FS_PERF", "explain", "medium", "concept", ["Database Connections"],
 "What is a 'Connection Pool' in a backend application, and how does it prevent the database from crashing under heavy API load?",
 "Opening and closing a TCP connection to a database is extremely slow and resource-intensive. A Connection Pool maintains a fixed number of pre-opened, persistent database connections in memory. When an API request comes in, it borrows an active connection, runs the query, and instantly returns it to the pool. This eliminates connection overhead and caps the maximum concurrent queries, preventing the database from crashing due to connection exhaustion.",
 ["Opening/closing DB connections per request is incredibly slow and CPU intensive", "Maintains a fixed cache of pre-opened, persistent database connections", "Caps maximum concurrency to protect the database from connection exhaustion crashes"],
 ["It is a literal swimming pool used to water-cool the servers"])
]
