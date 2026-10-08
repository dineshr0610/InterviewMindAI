import asyncio
import json
import os
import re
import sys
import uuid
from collections import Counter

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from phase4d_diversity_audit import fetch_all_supabase, normalize_text

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "Full Stack Developer"
VALID_INTENTS = {"fundamentals", "explain", "implement", "tradeoff", "debug", "scenario", "compare",
                 "architecture", "optimize", "diagnose"}
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|prompt instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

def existing_supabase():
    out = []
    for r in asyncio.run(fetch_all_supabase()):
        meta = r.get("metadata", {})
        if meta.get("status") == "inactive":
            continue
        c = r.get("content", "")
        if "### Instruction:" in c and "### Output:" in c:
            q = c.split("### Instruction:")[1].split("### Output:")[0].strip()
            if "write a program" in q.lower() or "implement a function" in q.lower():
                continue
            a = c.split("### Output:")[1].strip()
        elif "**Answer:**" in c:
            q = c.split("**Answer:**")[0].replace("### Technical Interview Question", "").replace("**Question:**", "").strip()
            a = c.split("**Answer:**")[1].strip()
        else:
            q = meta.get("question", c[:200])
            a = meta.get("expected_answer", "")
        if len(set(re.findall(r"[a-z0-9]+", q.lower()))) < 3:
            continue
        out.append((q, a))
    return out

def opening(q, n=3):
    return " ".join(normalize_text(q).split()[:n])

Q = [
    # Bucket 1: State Management & Database to UI
    ("B1", "architecture", "medium", "architecture", ["Asynchronous Workflows"], "A user uploads a video which is processed asynchronously by a backend worker. How should the frontend efficiently know when the processing is complete without causing massive database load via aggressive polling?", "The frontend should establish a WebSocket connection or use Server-Sent Events (SSE) to receive a real-time push notification from the backend once the worker finishes. The worker publishes the completion event to a message broker (like Redis Pub/Sub), which the API server listens to and relays to the specific client.", ["WebSockets or Server-Sent Events (SSE)", "Push notifications instead of polling", "Redis Pub/Sub or message broker"], ["Just ping the database every 1 second"]),
    ("B1", "diagnose", "medium", "debugging", ["Frontend/Backend Integration"], "You are using React for Server-Side Rendering (SSR). Users occasionally see a flash of unstyled content followed by an error: 'Hydration failed because the initial UI does not match what was rendered on the server.' What is a common root cause involving dates or times?", "This is caused by a timestamp or locale mismatch. If the server renders a date using the server's UTC timezone, but the client hydrates it using the browser's local timezone, the HTML strings will not match, causing React to discard the server-rendered DOM and re-render entirely.", ["Timestamp or locale mismatch between server and client", "Timezone differences causing HTML mismatch"], ["The server crashed"]),
    ("B1", "debug", "hard", "debugging", ["System Architecture"], "A bug report states that users in Tokyo are seeing their appointments scheduled exactly 9 hours earlier than intended. The database stores all times as strictly UTC, and the frontend converts them to local time. Where is the bug most likely occurring in the stack?", "The bug is likely a 'double-conversion' issue in the backend API or ORM layer. If the backend inadvertently assumes the incoming frontend timestamp (already in UTC) is in the server's local time (or vice versa) and attempts to convert it *again* before saving to the DB, it creates an offset. The backend must treat timestamps as timezone-aware or strictly pass-through UTC.", ["Double conversion in the backend or ORM", "Backend assuming wrong timezone before saving"], ["The database is broken"]),
    ("B1", "scenario", "medium", "scenario", ["State Management"], "A user with a slow connection clicks 'Pay Now' twice rapidly. How do you design the full-stack system to prevent a double-charge, encompassing both the UI and the backend?", "In the UI, immediately disable the button and show a loading state upon the first click. However, UI protection is insufficient. The frontend must generate a unique 'Idempotency Key' (e.g., a UUID) and send it with the request. The backend checks if this key already exists in the database or cache; if it does, it returns the cached success response rather than processing the payment again.", ["Disable button in UI (optimistic state)", "Frontend generates Idempotency Key", "Backend checks key to prevent double processing"], ["Just use a boolean flag in React"]),
    ("B1", "diagnose", "medium", "scenario", ["Database to UI"], "A user is viewing page 1 of a feed using standard offset-based pagination (LIMIT 10 OFFSET 0). While they are reading, a new item is added to the top of the feed by another user. When the first user clicks 'Next Page' (LIMIT 10 OFFSET 10), they see an item they already saw on page 1. How do you fix this at the database and API level?", "This is the 'shifting offset' problem. You must switch to Keyset Pagination (or Cursor-based pagination). The API should return a cursor (e.g., the ID or timestamp of the last item). The next request asks for `LIMIT 10 WHERE id < cursor`, which remains stable regardless of new items inserted at the top.", ["Shifting offset problem", "Keyset or Cursor-based pagination", "Query using WHERE id < cursor instead of OFFSET"], ["Just refresh the page automatically"]),
    ("B1", "optimize", "hard", "architecture", ["System Architecture"], "Your Node.js API allows users to upload 5GB video files, which it then saves to an AWS S3 bucket. Under heavy load, the Node.js servers run out of memory and crash. How should you redesign this upload flow?", "You should redesign the architecture to use Pre-signed URLs. The frontend requests a temporary, secure pre-signed URL from the backend API. The frontend then uploads the 5GB file directly to S3 using that URL, completely bypassing the Node.js API and saving server bandwidth and memory.", ["Pre-signed URLs", "Upload directly from client to S3", "Bypass the backend API entirely"], ["Increase the RAM on the Node servers"]),
    ("B1", "debug", "medium", "debugging", ["Database to UI"], "A user deletes their account, which your backend handles via a 'soft delete' (setting `deleted_at = NOW()`). Later, they try to sign up again with the exact same email, but the backend throws a 500 error because the database unique constraint on `email` fails. How should you design the schema to handle this?", "You should modify the unique constraint to be a composite index on `(email, deleted_at)`. However, since `deleted_at` is usually NULL for active users and some databases don't index NULLs uniquely, a better approach is a partial unique index: `CREATE UNIQUE INDEX on users (email) WHERE deleted_at IS NULL`.", ["Partial unique index WHERE deleted_at IS NULL", "Or composite unique index with a deletion flag"], ["Just hard delete the user instead"]),
    ("B1", "scenario", "hard", "scenario", ["State Management"], "You implement 'optimistic updates' for a Like button. A user clicks Like, the UI updates instantly, and an async request is fired. However, the backend returns a 500 error. Meanwhile, a background polling sync fetches the latest feed state. What race condition can occur, and how do you handle it in the frontend state manager?", "The background sync might fetch the old state (unliked) and overwrite the UI before the 500 error returns, or the 500 error rollback might overwrite the new state. To handle this, the state manager must pause background syncs for that specific entity during optimistic mutations, and explicitly rollback to the pre-mutation snapshot upon API failure.", ["Pause background syncs during optimistic mutations", "Explicitly rollback to pre-mutation snapshot on failure"], ["Optimistic updates should never fail"]),
    ("B1", "architecture", "medium", "architecture", ["Authentication"], "A user logs out in Tab A, clearing their authentication cookies. However, Tab B remains open, and the React application still contains sensitive user data in its Redux/Zustand store. How do you ensure Tab B is securely cleared?", "You can use the browser's `BroadcastChannel` API or listen to the `storage` event on `localStorage`. When Tab A triggers the logout, it broadcasts a message or updates a storage key. Tab B listens for this event and immediately dispatches a global 'RESET_STORE' action to clear the in-memory state and redirect to the login page.", ["BroadcastChannel API or storage event", "Listen across tabs for logout event", "Dispatch global state reset"], ["Set a really short timeout on Redux"]),
    ("B1", "diagnose", "medium", "debugging", ["Asynchronous Workflows"], "Your frontend makes an API request to generate a PDF, which takes 45 seconds. The AWS API Gateway sitting in front of your backend has a hard timeout of 30 seconds, causing the frontend to consistently receive a 504 Gateway Timeout. How must you change the API contract?", "You must change the API contract from a synchronous request-response to an asynchronous polling or webhook model. The backend should immediately return a `202 Accepted` with a `job_id`. The frontend then polls a `/status/{job_id}` endpoint (or waits for a WebSocket event) to retrieve the PDF URL once it finishes.", ["Change from synchronous to asynchronous", "Return 202 Accepted with a job ID", "Frontend polls status or waits for webhook/WebSocket"], ["Just increase the API Gateway timeout to 60 seconds"]),

    # Bucket 2: Full Stack Performance & Caching
    ("B2", "tradeoff", "medium", "tradeoff", ["Caching"], "When using ETag caching, the backend returns a `304 Not Modified` if the frontend's cached version matches the server's version. What is the primary performance tradeoff of this approach compared to a `Cache-Control: max-age` header?", "ETag caching requires the frontend to actually make a network request to the backend to validate the resource, and the backend often must query the database to compute or verify the ETag, meaning it saves network payload bandwidth but does NOT save database CPU/IO or network latency. `max-age` prevents the network request entirely.", ["ETag requires a network request and often DB CPU to validate", "max-age prevents the network request entirely", "Saves bandwidth but not latency/DB load"], ["ETags are faster than max-age"]),
    ("B2", "compare", "hard", "compare", ["Deployment & Architecture"], "Compare traditional Server-Side Rendering (SSR) with modern React Server Components (RSC). What specific architectural advantage do Server Components provide regarding frontend bundle size and API usage?", "Traditional SSR renders the HTML on the server, but still sends the entire JavaScript component code to the client for hydration. React Server Components never send their JavaScript to the client; they execute exclusively on the server. This reduces the client bundle size and allows the component to securely access databases or internal APIs directly without exposing secrets or creating separate REST endpoints.", ["RSC never sends JavaScript to the client", "Reduces client bundle size", "Securely access databases directly without REST endpoints"], ["RSC is just a faster version of SSR"]),
    ("B2", "explain", "medium", "concept", ["Caching"], "The `stale-while-revalidate` (SWR) caching strategy is popular in modern frontend data fetching. Explain the sequence of events when a user navigates to a page whose data in the SWR cache has just expired.", "The SWR strategy immediately returns and renders the stale (expired) data from the local cache so the UI feels instantaneous. Simultaneously, it fires a background network request to the API to fetch the fresh data. Once the fresh data arrives, it silently updates the cache and triggers a re-render of the UI with the new data.", ["Returns stale data immediately for instant UI", "Fires background request for fresh data", "Silently re-renders UI when fresh data arrives"], ["It waits for the fresh data before rendering"]),
    ("B2", "architecture", "medium", "architecture", ["Database to UI"], "Your full-stack application uses GraphQL. A malicious user crafts a deeply nested query (e.g., User -> Posts -> Comments -> Author -> Posts). What two backend strategies must you implement to prevent this from crashing your database?", "You must implement Query Depth Limiting to reject queries nested beyond a certain threshold (e.g., > 5 levels deep). Additionally, you should implement Query Complexity Analysis (assigning a cost to each field and rejecting queries over a total cost limit) and use a batching tool like DataLoader to prevent the N+1 database query problem.", ["Query Depth Limiting", "Query Complexity Analysis", "DataLoader to prevent N+1"], ["Switch back to REST APIs"]),
    ("B2", "optimize", "hard", "optimize", ["Database to UI"], "Your frontend provides a table of 10 million records. A user clicks to page 50,000. The API executes `SELECT * FROM records ORDER BY created_at DESC LIMIT 50 OFFSET 2500000`, which takes 15 seconds and times out. How do you optimize this across the stack?", "You must implement Keyset (Cursor) Pagination. The frontend must pass the last known value instead of a page number. The API executes `SELECT * FROM records WHERE created_at < ? ORDER BY created_at DESC LIMIT 50`. The database can use an index on `created_at` to instantly jump to the correct row, reducing the query time to milliseconds.", ["Keyset or Cursor Pagination", "WHERE created_at < cursor", "Utilizes database index to avoid scanning millions of rows"], ["Add Redis caching for all 10 million pages"]),
    ("B2", "scenario", "medium", "scenario", ["System Architecture"], "You are building a Backend-For-Frontend (BFF). It aggregating data from the Users, Orders, and Recommendations microservices. The Recommendations service goes down. How should the BFF respond to the frontend?", "The BFF should implement partial failures (graceful degradation). It should catch the error from the Recommendations service, log it, and return a `200 OK` (or `206 Partial Content`) to the frontend containing the valid Users and Orders data, along with a null or empty array for recommendations, allowing the UI to render the core page without crashing.", ["Graceful degradation / partial failure handling", "Return 200 OK with valid data and null for failed service", "Do not crash the entire page"], ["Return a 500 error immediately"]),
    ("B2", "architecture", "hard", "tradeoff", ["Full Stack Performance"], "Your backend generates a massive analytics report (100,000 rows). Buffering the entire JSON array in memory before sending it causes a Time To First Byte (TTFB) of 15 seconds. How can you redesign the API and frontend to render data instantly?", "You should stream the response using JSONL (JSON Lines) or NDJSON (Newline Delimited JSON). The backend yields each row as it is retrieved from the database, keeping memory low. The frontend uses the Fetch API's `ReadableStream` to process and render the rows incrementally as the chunks arrive, dropping TTFB to milliseconds.", ["Stream response using JSONL or NDJSON", "Backend yields rows incrementally", "Frontend uses ReadableStream to render chunks"], ["Just paginate the report instead"]),
    ("B2", "diagnose", "medium", "scenario", ["Caching"], "A highly anticipated product launches at midnight. At 12:00:00, the Redis cache for the homepage expires. Instantly, 50,000 users hit the frontend, causing 50,000 identical cache-miss requests to hit the database simultaneously, crashing it. What is this called, and how do you fix it?", "This is a Cache Stampede (or Thundering Herd). To fix it, you can implement Cache Locking (mutex), where only the first request is allowed to query the database and repopulate the cache, while the other 49,999 requests wait for the lock to release. Alternatively, use Probabilistic Early Expiration (XFetch) to recompute the cache in the background before it actually expires.", ["Cache Stampede or Thundering Herd", "Cache Locking / Mutex", "Probabilistic early expiration"], ["Just add more database replicas"]),
    ("B2", "explain", "easy", "concept", ["Frontend/Backend Integration"], "In the context of GraphQL or complex REST aggregations, what specific problem does the `DataLoader` utility solve between the backend resolvers and the database?", "DataLoader solves the N+1 query problem by implementing request coalescing (batching) and caching per-request. If 50 different UI components all independently ask the backend resolver for the same author's data, DataLoader groups those individual lookups into a single batched database query (`SELECT * WHERE id IN (...)`) executed on the next tick of the event loop.", ["Solves N+1 query problem", "Request coalescing / batching", "Executes single batched query using IN clause"], ["It loads data into the frontend state"]),
    ("B2", "diagnose", "medium", "debugging", ["Full Stack Performance"], "A web page downloads 150 small thumbnails. Over an HTTP/1.1 connection, the page takes 8 seconds to load, but over an HTTP/2 connection, it loads in 1.5 seconds. What specific limitation of HTTP/1.1 causes this discrepancy?", "HTTP/1.1 suffers from Head-of-Line Blocking and browser connection limits (typically 6 concurrent TCP connections per domain). The browser must wait for previous images to finish downloading before requesting the next batch. HTTP/2 utilizes multiplexing over a single TCP connection, allowing all 150 requests and responses to be interleaved and transferred concurrently without blocking.", ["Head-of-Line Blocking", "Browser concurrent connection limits (e.g., 6 per domain)", "HTTP/2 uses multiplexing"], ["HTTP/2 compresses images better"]),

    # Bucket 3: Resilience & Error Propagation
    ("B3", "scenario", "medium", "scenario", ["System Architecture"], "A third-party payment API is experiencing extreme latency (taking 30 seconds per request). Your Node.js backend waits for these responses. Suddenly, your entire web app goes down for all users, even those not making payments. Why did a third-party slowdown cause a full-stack outage?", "The slow payment requests exhausted the backend's connection pool, thread pool, or event loop capacity. Because the server was waiting on the slow third-party API, all available worker threads or sockets were occupied, preventing the server from accepting or processing any new incoming requests from the frontend.", ["Connection pool or thread pool exhaustion", "Waiting on slow API occupies all resources", "Prevents serving new requests"], ["The third party sent a virus"]),
    ("B3", "architecture", "hard", "architecture", ["End-to-End Debugging"], "A user places an order. Your backend must insert the order into the PostgreSQL database and send a confirmation email via SendGrid. If the DB commits but the SendGrid API times out, the user doesn't get an email. If SendGrid succeeds but the DB commit fails, the user gets an email for an order that doesn't exist. How do you architect this to guarantee consistency?", "You must implement the Transactional Outbox Pattern. Within the same database transaction that saves the order, you insert an event record (e.g., 'OrderCreated') into an 'outbox' table. A separate asynchronous background worker reliably polls or tails the outbox table, sends the email to SendGrid, and marks the event as processed. This guarantees atomicity.", ["Transactional Outbox Pattern", "Save event to an outbox table in the same DB transaction", "Background worker processes the outbox asynchronously"], ["Just put it in a try/catch block"]),
    ("B3", "tradeoff", "medium", "tradeoff", ["Asynchronous Workflows"], "A frontend client experiences a network timeout during a POST request to create a resource, but the backend actually received and processed it. The client retries, creating a duplicate. Explain how an Idempotency Key solves this and where it should be generated.", "The frontend (client) generates a unique Idempotency Key (e.g., a UUID v4) and includes it in the header of the POST request. The backend stores this key alongside the created resource. If the client retries with the same key, the backend sees it has already processed that key and returns the original success response without executing the creation logic twice.", ["Frontend generates a unique UUID", "Backend stores key and returns cached response on retry", "Prevents duplicate resource creation"], ["The backend generates the key and sends it to the frontend"]),
    ("B3", "scenario", "medium", "scenario", ["Frontend/Backend Integration"], "Your backend API is overwhelmed and returns a `429 Too Many Requests` status. If the frontend immediately retries in a tight loop, it acts like a DDoS attack. How should the full-stack system handle rate limits properly?", "The backend should include a `Retry-After` header in the 429 response, specifying how many seconds to wait. The frontend must read this header, pause all automated retries for that duration, and ideally update the UI (e.g., disabling the submit button and showing a countdown) to inform the user.", ["Backend sends Retry-After header", "Frontend reads header and pauses retries", "Use Exponential Backoff with Jitter if no header"], ["The frontend should retry every 1 second until it works"]),
    ("B3", "diagnose", "easy", "debugging", ["End-to-End Debugging"], "A user submits a form. The frontend limits the 'username' field to 20 characters. The request goes to the backend, which blindly passes it to a PostgreSQL database where the column is `VARCHAR(20)`. A malicious user bypasses the frontend and sends a 50-character string, crashing the backend. What fundamental rule was broken?", "The fundamental rule is: Never trust the client. Client-side validation is strictly for user experience (UX), not security or data integrity. The backend must independently enforce all validation rules, constraints, and sanitization before interacting with the database.", ["Never trust the client", "Client-side validation is only for UX", "Backend must independently validate all data"], ["The database column should be TEXT instead of VARCHAR"]),
    ("B3", "scenario", "medium", "scenario", ["Application Security"], "Your backend API returns a `403 Forbidden` when a user attempts to access `/api/documents/123` which they do not own. A security auditor suggests returning `404 Not Found` instead. Why is this a valid full-stack security architectural choice?", "Returning a `403 Forbidden` explicitly confirms to an attacker that the document ID `123` actually exists in the database, allowing them to enumerate and discover valid record IDs. Returning a `404 Not Found` obfuscates the existence of the resource, making enumeration attacks significantly harder.", ["Prevents resource enumeration", "403 confirms the resource exists", "404 obfuscates existence from unauthorized users"], ["404 is faster to process than 403"]),
    ("B3", "architecture", "hard", "architecture", ["End-to-End Debugging"], "To debug frontend errors in production, you use a tool like Sentry. The errors are unreadable because the JavaScript is minified. You need to upload Source Maps to Sentry, but you don't want to deploy the Source Maps to your public CDN where users can steal your unminified source code. How do you architect this CI/CD pipeline?", "During the CI/CD build step (e.g., Webpack/Vite), you generate the Source Maps alongside the minified code. A script in the CI pipeline securely uploads the Source Maps directly to Sentry using a private API key. Finally, the CI pipeline deletes the `.map` files before deploying the minified static assets to the public CDN.", ["Generate source maps in CI/CD build", "Securely upload directly to Sentry via API key", "Delete .map files before deploying to public CDN"], ["Just leave the source maps on the server, it's fine"]),
    ("B3", "compare", "medium", "compare", ["Deployment & Architecture"], "Compare Stateless APIs (using JWTs) to Stateful APIs (using server-side Sessions with Sticky load balancing). What is the major architectural risk of Sticky Sessions during a backend server crash?", "In a Stateful API with Sticky Sessions, the load balancer routes a specific user to the exact same server holding their session memory. If that specific server crashes, all users pinned to it instantly lose their session and are logged out. Stateless APIs (JWTs) or distributed session stores (Redis) allow any server to handle any request, providing seamless failover.", ["Server crash destroys pinned sessions", "Users get logged out instantly", "Stateless APIs allow seamless failover across servers"], ["Sticky sessions are slower to load"]),
    ("B3", "diagnose", "medium", "debugging", ["Database to UI"], "A message queue is processing background jobs. If a job fails 3 times, it is sent to a Dead Letter Queue (DLQ). The frontend originally received a `202 Accepted` when submitting the job. How should the frontend handle or display the fact that the job eventually died in the DLQ?", "The frontend cannot magically know the job failed in the background. The backend must update the job's status record in the database to 'FAILED' when routing it to the DLQ. The frontend (which should be polling the job status endpoint or listening to a WebSocket) reads this 'FAILED' status and updates the UI accordingly.", ["Backend updates job status to FAILED in the database", "Frontend polls or uses WebSockets to read the final status"], ["The DLQ automatically emails the user"]),
    ("B3", "architecture", "hard", "architecture", ["Resilience"], "In a microservices architecture, the frontend calls the BFF (Backend for Frontend). The BFF calls Service A, which calls Service B. If Service B is completely down, what happens if Service A does not have a Circuit Breaker, and how does it impact the frontend?", "Without a Circuit Breaker, Service A will wait until the network timeout for every single request to Service B. The BFF will wait for Service A, and the frontend will wait for the BFF. This ties up threads across the entire stack, causing massive latency and eventual cascading failure. A Circuit Breaker fails fast, returning an immediate error so the frontend can degrade gracefully.", ["Cascading failure due to tied-up threads", "Timeout delays propagate all the way to the frontend", "Circuit breaker fails fast to prevent resource exhaustion"], ["The frontend will just retry infinitely"]),

    # Bucket 4: Application Security Boundaries
    ("B4", "scenario", "hard", "scenario", ["Application Security"], "Your web app allows users to provide a URL for their avatar, which your Node.js backend downloads and resizes. A malicious user inputs `http://169.254.169.254/latest/meta-data/`. What specific vulnerability is this, and what is the attacker trying to achieve?", "This is Server-Side Request Forgery (SSRF). The attacker is forcing the backend server to make an HTTP request on their behalf to an internal, non-public IP address. Specifically, `169.254.169.254` is the AWS instance metadata service, and the attacker is attempting to steal the EC2 instance's IAM credentials or configuration data.", ["Server-Side Request Forgery (SSRF)", "Forcing backend to query internal network", "Stealing AWS instance metadata/IAM credentials"], ["Cross-Site Scripting (XSS)"]),
    ("B4", "architecture", "medium", "architecture", ["Authentication"], "For security, your SPA (React) receives a short-lived Access Token (5 mins) in memory, and a long-lived Refresh Token in an `HttpOnly`, `Secure` cookie. Architecturally, how does the frontend maintain a seamless session without the user being logged out every 5 minutes?", "The frontend must implement 'Silent Refresh'. It runs a background timer or intercepts 401 Unauthorized API responses. Before the access token expires (or upon a 401), the frontend makes an asynchronous request to a `/refresh` endpoint. The browser automatically attaches the `HttpOnly` refresh cookie. The backend validates it and returns a new Access Token, which the frontend stores in memory.", ["Silent Refresh mechanism", "Frontend requests /refresh endpoint", "Browser automatically includes HttpOnly cookie"], ["Store the refresh token in LocalStorage instead"]),
    ("B4", "diagnose", "medium", "debugging", ["Application Security"], "Your frontend registration form sends `{ \"email\": \"test@test.com\", \"password\": \"secret\" }`. A malicious user intercepts the request and adds `\"is_admin\": true`. The backend uses an ORM like `User.create(req.body)`. What vulnerability occurred?", "This is Mass Assignment (or Over-Posting). Because the backend blindly bound the entire incoming JSON payload directly to the database ORM model without filtering, the attacker successfully injected the `is_admin` property, granting themselves administrator privileges. The backend must strictly whitelist allowed fields (e.g., using DTOs or explicit parameter extraction).", ["Mass Assignment or Over-Posting", "Blindly binding JSON payload to ORM model", "Must explicitly whitelist allowed fields"], ["SQL Injection"]),
    ("B4", "explain", "easy", "concept", ["Application Security"], "A junior developer needs to upload files directly from the React frontend to an AWS S3 bucket. To make it work, they hardcode the AWS Access Key and Secret Key inside the React component. Why is this a catastrophic security failure?", "Frontend JavaScript runs entirely in the user's browser. Anyone can open the browser's Developer Tools, view the source code, and extract the hardcoded AWS Secret Key. The attacker now has full programmatic access to your AWS account. Secrets must never be shipped to the client.", ["Frontend code is public to the user", "Attacker can extract the keys via Developer Tools", "Grants full access to the AWS account"], ["React will fail to compile with secrets in it"]),
    ("B4", "tradeoff", "hard", "tradeoff", ["System Architecture"], "When implementing Rate Limiting in your API Gateway, what is the architectural tradeoff between rate limiting by the client's IP address versus rate limiting by the authenticated User ID?", "Rate limiting by IP protects against unauthenticated DDoS attacks and brute force logins, but can accidentally block hundreds of legitimate users sharing a single NAT gateway (e.g., a corporate office or university). Rate limiting by User ID is fairer and moves with the user across devices, but requires the API gateway to parse and validate the authentication token before it can apply the limit.", ["IP limits can block legitimate users on shared NATs", "User ID limits require parsing auth tokens first", "IP limits protect unauthenticated routes better"], ["User ID limiting is faster to process"]),
    ("B4", "scenario", "medium", "scenario", ["Application Security"], "A malicious website embeds your banking application inside an invisible `<iframe>`. When the user clicks a seemingly harmless button on the malicious site, they are actually clicking the 'Transfer Funds' button on your embedded site. What is this attack, and how do you prevent it across the stack?", "This is Clickjacking (UI Redressing). You prevent it by configuring the backend web server or API to send specific HTTP response headers. Historically, `X-Frame-Options: DENY` or `SAMEORIGIN` was used. The modern approach is the Content Security Policy (CSP) header with the `frame-ancestors 'none'` or `'self'` directive, instructing the browser to refuse to render the page inside an iframe.", ["Clickjacking or UI Redressing", "X-Frame-Options header", "CSP frame-ancestors directive"], ["Cross-Site Request Forgery (CSRF)"]),
    ("B4", "architecture", "hard", "architecture", ["Application Security"], "To mitigate XSS, your security team mandates a strict Content Security Policy (CSP) that disables all inline scripts (`'unsafe-inline'`). However, your server-rendered React app requires a small inline script to inject the initial hydrated state (e.g., `window.__INITIAL_STATE__`). How do you architect the full stack to allow this specific script securely?", "You must implement a CSP Nonce (Number Used Once). The backend server generates a cryptographically secure random string (nonce) for every single page request. The server includes this nonce in the CSP HTTP header, and applies the exact same `nonce=\"xyz\"` attribute to the specific inline `<script>` tag. The browser will execute that specific script and block all other injected inline scripts.", ["CSP Nonce (Number Used Once)", "Server generates random nonce per request", "Nonce matches in HTTP header and script attribute"], ["Just allow 'unsafe-inline' temporarily"]),
    ("B4", "diagnose", "medium", "debugging", ["Application Security"], "Your API uses JWTs for authentication. A developer notices they can take a valid JWT, change the `user_id` in the decoded payload from 1 to 2, re-encode it using Base64, and the backend accepts it. What critical security step was missed in the backend JWT middleware?", "The backend middleware failed to verify the cryptographic signature of the JWT. While anyone can Base64 decode and modify the payload, only the server possesses the secret key required to generate a valid signature for the modified payload. The backend must calculate the signature of the incoming payload and reject the token if it doesn't match the attached signature.", ["Failed to verify cryptographic signature", "Token was modified without updating the signature", "Server must validate signature using the secret key"], ["The JWT expired"]),
    ("B4", "explain", "medium", "concept", ["End-to-End Latency"], "Explain what a 'Replay Attack' is in the context of REST APIs, and describe one full-stack mechanism to prevent it.", "A Replay Attack occurs when an attacker intercepts a valid, authenticated HTTP request (e.g., a funds transfer) and maliciously resends it multiple times to trigger the action repeatedly. It can be prevented using a Nonce (a random value sent by the client that the server rejects if seen twice) or by having the client generate an Idempotency Key that the backend caches to ensure the operation only executes once.", ["Attacker intercepts and resends a valid request", "Prevent using Nonces", "Prevent using Idempotency Keys"], ["The attacker steals the password"]),
    ("B4", "scenario", "hard", "scenario", ["Frontend/Backend Integration"], "Your Node.js backend merges deeply nested JSON objects sent from the frontend client. An attacker sends a payload containing the key `__proto__`, which overwrites fundamental properties of the base JavaScript Object. What is this vulnerability, and how does it impact the full stack?", "This is Prototype Pollution. Because JavaScript uses prototypal inheritance, overwriting `__proto__` pollutes the base object for the entire Node.js runtime environment. This can lead to Denial of Service (crashing the server), Remote Code Execution (if the polluted property is later executed), or bypassing security checks (e.g., setting `isAdmin: true` on the global prototype).", ["Prototype Pollution", "Overwrites base JavaScript Object prototype", "Causes DoS, RCE, or logic bypass across the entire runtime"], ["It causes an SQL injection"]),

    # Bucket 5: System Architecture & Data Consistency
    ("B5", "compare", "medium", "compare", ["Real-Time Systems"], "Compare Server-Sent Events (SSE) and WebSockets for building a real-time live sports scoring dashboard. Why might SSE be the better architectural choice for this specific use case?", "SSE is strictly unidirectional (Server to Client) and operates over standard HTTP, making it simpler to deploy, naturally compatible with load balancers, and able to utilize HTTP multiplexing. WebSockets are bidirectional and require maintaining persistent stateful TCP connections. Since a sports dashboard only involves the server broadcasting scores to clients (without clients sending heavy data back), SSE is significantly more efficient and easier to scale.", ["SSE is unidirectional (Server to Client)", "SSE uses standard HTTP, easier to load balance", "Sports dashboards don't need bidirectional client-to-server data"], ["WebSockets are much slower than SSE"]),
    ("B5", "architecture", "hard", "architecture", ["System Architecture"], "Explain the concept of 'Backend-Driven UI' (or Server-Driven UI). What primary mobile deployment bottleneck does this architecture solve?", "In a Backend-Driven UI, the backend API doesn't just return data; it returns a JSON schema dictating the layout, components, and actions the frontend should render (e.g., 'render a vertical list with a text box and a button'). This solves the App Store review bottleneck. Product teams can radically change the mobile app's layout, features, and workflows instantly by deploying backend code, without requiring users to download an app update.", ["Backend API returns layout and component schema, not just data", "Bypasses App Store review process", "Allows instant UI changes without app updates"], ["It makes the database faster"]),
    ("B5", "scenario", "hard", "scenario", ["Data Consistency"], "A user books a flight and a hotel via your frontend. The backend orchestrator succeeds in booking the flight, but the third-party hotel API fails. Since you cannot wrap external APIs in a single database transaction, what pattern must you implement to ensure data consistency, and how does the UI handle it?", "You must implement the Saga Pattern with Compensating Transactions. When the hotel fails, the backend must execute a new, separate transaction to cancel (rollback) the flight booking. The UI must be designed to handle this eventual consistency, initially showing a 'Processing' state, and eventually updating to 'Failed' once the compensating transaction completes, rather than assuming success.", ["Saga Pattern", "Compensating Transactions to rollback external actions", "UI must handle eventual consistency (e.g., Processing state)"], ["Use a massive SQL lock on both databases"]),
    ("B5", "diagnose", "medium", "debugging", ["Database to UI"], "A user updates their display name on the profile settings page. The UI makes a PUT request, gets a 200 OK, and immediately redirects the user to their public profile page. However, the public profile page still shows their old display name for about 1 second before correcting itself on a refresh. What database architecture causes this?", "This is a Read-After-Write consistency issue caused by a primary-replica database architecture. The PUT request writes the new name to the Primary (Master) database. The redirect causes the UI to read from a Read Replica. Because replication is asynchronous, the replica is lagging by a few milliseconds and returns the stale data. The UI must be designed to read from the Primary immediately after a write, or optimistically update the cache.", ["Read-After-Write consistency issue", "Asynchronous replication lag between Primary and Replica", "Read query hit a stale replica"], ["The browser cache is broken"]),
    ("B5", "optimize", "medium", "architecture", ["Frontend/Backend Integration"], "You are building a global search typeahead (autocomplete) feature. As the user types, requests are fired. Describe the full-stack optimization required: one technique on the frontend, and one on the backend, to prevent overwhelming the system.", "On the frontend, you must implement 'Debouncing', which delays firing the API request until the user stops typing for a specific duration (e.g., 300ms), drastically reducing network requests. On the backend, you must avoid full-table SQL `LIKE` queries; instead, use an in-memory data structure like a Trie, or a specialized search engine like Elasticsearch/Redisearch to ensure sub-millisecond query responses.", ["Frontend: Debouncing to reduce request volume", "Backend: Trie data structure or Elasticsearch", "Avoid full-table SQL LIKE queries"], ["Frontend: WebSockets, Backend: GraphQL"]),
    ("B5", "architecture", "medium", "architecture", ["Deployment & Architecture"], "Your frontend SPA is instantly updated via a CDN deployment, but your iOS/Android apps require weeks for users to upgrade. You need to make a breaking change to a backend JSON response payload. How do you architect the backend to support both the new web users and the old mobile users simultaneously?", "You must implement API Versioning (e.g., via URL paths `/v1/` and `/v2/`, or via HTTP Accept headers). The backend maintains both endpoints. The web frontend is updated to point to `/v2/`, receiving the new payload. The legacy mobile apps continue hitting `/v1/`, which maps the new internal data structures back to the old, expected JSON payload until the old versions are officially deprecated.", ["API Versioning (URL or Headers)", "Maintain backward compatibility for mobile", "/v1/ maps new data to old payload structures"], ["Force the mobile app to crash until they update"]),
    ("B5", "explain", "hard", "concept", ["System Architecture"], "Explain the Event Sourcing pattern. Instead of storing a user's current shopping cart state in a `carts` table, how is the data stored, and what unique feature does this provide for UI debugging?", "In Event Sourcing, the database stores a strict, append-only immutable log of state-changing events (e.g., `ItemAdded`, `QuantityUpdated`, `ItemRemoved`) rather than the current state. The current cart is derived by replaying the events. This provides a perfect audit trail, allowing developers to 'time travel' and reconstruct the exact sequence of UI actions that led to a specific bug at any point in history.", ["Append-only immutable log of events", "Current state derived by replaying events", "Allows 'time travel' debugging of UI actions"], ["It sends events to Google Analytics"]),
    ("B5", "architecture", "hard", "architecture", ["Frontend/Backend Integration"], "In a microservices architecture, the frontend needs data from the User, Order, and Inventory services to render a single page. Instead of the frontend making three separate REST calls, the team implements Apollo Federation (GraphQL Schema Stitching). How does this change the data flow?", "Apollo Federation provides a single unified GraphQL gateway for the frontend. The frontend makes one GraphQL query to the gateway. The gateway intelligently decomposes the query, orchestrates the parallel sub-queries to the underlying User, Order, and Inventory microservices, stitches the responses together in memory, and returns a single combined JSON payload to the frontend.", ["Single unified GraphQL gateway", "Gateway orchestrates sub-queries to microservices", "Stitches responses into a single JSON payload"], ["It moves the database to the browser"]),
    ("B5", "diagnose", "hard", "debugging", ["Real-Time Systems"], "Your application relies on WebSockets for real-time chat. You scale your Node.js backend from 1 server to 3 servers behind an AWS Application Load Balancer. Suddenly, User A sends a message, but User B never receives it, even though both are online. What architectural piece is missing?", "You are missing a Pub/Sub Backplane (e.g., Redis Pub/Sub). Because WebSockets are persistent TCP connections, User A is connected to Server 1, and User B is connected to Server 2. When User A sends a message, Server 1 only knows about its local connections. The server must publish the message to Redis, so Server 2 receives it and broadcasts it to User B.", ["Missing Pub/Sub Backplane (e.g., Redis)", "WebSockets are stateful to specific servers", "Servers must share messages across the cluster"], ["The Load Balancer needs to use Sticky Sessions"]),
    ("B5", "scenario", "medium", "scenario", ["State Management"], "You are building a Progressive Web App (PWA) that allows users to fill out inspection forms while deep underground without internet access. How do you architect the browser storage and synchronization logic to handle offline data collection and eventual transmission?", "The frontend must capture the form data and store it locally using IndexedDB (since localStorage is synchronous and size-limited). It registers a Background Sync event with the Service Worker. When the device regains network connectivity, the Service Worker wakes up, reads the pending payloads from IndexedDB, transmits them to the backend API, and handles conflict resolution.", ["Store data locally in IndexedDB", "Use Service Worker Background Sync", "Transmit when network returns"], ["Just keep the data in a Redux variable"])
]

BUCKET_KEYS = {
    "B1": ("State Management & Consistency", "Database to UI", "React/Node", ["Full Stack Developer", "Backend Developer"]),
    "B2": ("Full Stack Performance", "Caching & Streaming", "Redis/GraphQL", ["Full Stack Developer", "Frontend Developer"]),
    "B3": ("Resilience & Error Handling", "End-to-End Debugging", "PostgreSQL", ["Full Stack Developer", "DevOps / Cloud Engineer"]),
    "B4": ("Application Security", "Cross-Layer Boundaries", "HTTP/JWT", ["Full Stack Developer", "Backend Developer"]),
    "B5": ("System Architecture", "Deployment Integration", "WebSockets/SSE", ["Full Stack Developer", "Frontend Developer"]),
}

def main():
    with open(OUT, encoding="utf-8") as f:
        prior = [json.loads(l) for l in f if l.strip()]
    
    staged_q = [p["question"] for p in prior]
    staged_a = [p["expected_answer"] for p in prior]
    
    # Adding legacy supabase text for overlap detection
    sup = existing_supabase()
    staged_q.extend([q for q, _ in sup])
    staged_a.extend([a for _, a in sup])

    cands = []
    for b, intent, diff, qt, sec, q, a, strong, weak in Q:
        skill, topic, tech, roles = BUCKET_KEYS[b]
        cands.append({
            "primary_role": ROLE,
            "applicable_roles": roles,
            "primary_skill": skill,
            "secondary_skills": sec,
            "technology": tech,
            "topic": topic,
            "category": "Software Engineering",
            "intent": intent,
            "difficulty": diff,
            "question_type": qt,
            "question": q,
            "expected_answer": a,
            "evaluation_rubric": {"strong_indicators": strong, "weak_indicators": weak}
        })

    corpus = staged_q + staged_a + [c["question"] for c in cands] + [c["expected_answer"] for c in cands]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit(corpus)
    SQ, SA = vec.transform(staged_q), vec.transform(staged_a)
    SC = vec.transform([x + " " + y for x, y in zip(staged_q, staged_a)])
    seen_norm = {normalize_text(q) for q in staged_q}

    rej = Counter()
    accepted = []
    details = []
    ans_flags = []
    
    for idx, c in enumerate(cands):
        nq = normalize_text(c["question"])
        reason = None
        if nq in seen_norm:
            reason = "exact_duplicate"
        else:
            qs = cosine_similarity(vec.transform([c["question"]]), SQ)[0]
            as_ = cosine_similarity(vec.transform([c["expected_answer"]]), SA)[0]
            comp = cosine_similarity(vec.transform([c["question"] + " " + c["expected_answer"]]), SC)[0]
            
            details.append((float(qs.max()), float(as_.max()), float(comp.max())))
            if as_.max() >= 0.5:
                ans_flags.append((c["question"][:70], round(float(as_.max()), 3)))
                
            if qs.max() >= 0.80:
                reason = "near_duplicate"
            elif comp.max() >= 0.60:
                reason = "semantic_competency_duplicate"
            elif as_.max() >= 0.70:
                reason = "expected_answer_overlap"
                
        if not reason and LEAK.search(c["question"] + " " + c["expected_answer"]):
            reason = "prompt_leakage"
        
        if reason:
            rej[reason] += 1
            print(f"Rejected Q{idx+1}: {reason}")
            continue
            
        seen_norm.add(nq)
        accepted.append(c)

    print(f"Attempted: {len(cands)}, Accepted: {len(accepted)}, Rejected: {sum(rej.values())}")
    
    if len(accepted) != 50:
        print(f"ERROR: Did not accept exactly 50 (got {len(accepted)}). Aborting write.")
        sys.exit(1)

    for c in accepted:
        c["id"] = "gen_" + str(uuid.uuid4())
        c["generation_batch"] = "batch_42_fullstack_developer"

    with open(OUT, "a", encoding="utf-8") as f:
        for c in accepted:
            f.write(json.dumps(c) + "\n")
            
    final_staging_total = len(prior) + len(accepted)
    role_counts = Counter(p.get("primary_role") for p in prior)
    role_counts[ROLE] += len(accepted)
    
    diff_counts = Counter(c["difficulty"] for c in accepted)
    intent_counts = Counter(c["intent"] for c in accepted)
    skill_counts = Counter(c["primary_skill"] for c in accepted)
    tech_counts = Counter(c["technology"] for c in accepted)
    topic_counts = Counter(c["topic"] for c in accepted)
    openings = Counter(opening(c["question"], 3) for c in accepted)
    
    bq = [c["question"] for c in accepted]
    M = cosine_similarity(vec.transform(bq)) if bq else [[0]]
    intra = [(i, j, round(float(M[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if M[i][j] >= 0.6]
    intra_qa = cosine_similarity(vec.transform([c["expected_answer"] for c in accepted])) if bq else [[0]]
    intra_ans = [(i, j, round(float(intra_qa[i][j]), 3)) for i in range(len(bq)) for j in range(i + 1, len(bq)) if intra_qa[i][j] >= 0.5]
    
    report = {
        "batch": "batch_42_fullstack_developer",
        "records_attempted": len(cands),
        "records_accepted": len(accepted),
        "records_rejected": sum(rej.values()),
        "rejection_reasons": dict(rej),
        "max_similarity_scores": {
            "question": round(max((d[0] for d in details), default=0), 3),
            "answer": round(max((d[1] for d in details), default=0), 3),
            "combined": round(max((d[2] for d in details), default=0), 3)
        },
        "intra_batch_overlaps": len(intra),
        "intra_batch_answer_overlaps": len(intra_ans),
        "answer_flags_gt_50": len(ans_flags),
        "staging_metrics": {
            "previous_staging_total": len(prior),
            "final_staging_total": final_staging_total,
            "role_total": role_counts[ROLE],
            "remaining_to_500": max(0, 500 - role_counts[ROLE])
        },
        "distributions": {
            "difficulty": dict(diff_counts),
            "intent": dict(intent_counts),
            "primary_skill": dict(skill_counts),
            "technology": dict(tech_counts),
            "topic": dict(topic_counts),
            "opening_diversity": dict(openings.most_common(10))
        }
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_batch42_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_batch42_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Phase 4D - Batch 42 (Full Stack Developer)\n\n")
        f.write(f"- **Attempted**: {len(cands)}\n")
        f.write(f"- **Accepted**: {len(accepted)}\n")
        f.write(f"- **Rejected**: {sum(rej.values())}\n")
        f.write(f"- **Rejections**: {dict(rej)}\n\n")
        f.write("### Staging Totals\n")
        f.write(f"- **Previous Staging Total**: {len(prior)}\n")
        f.write(f"- **Final Staging Total**: {final_staging_total}\n")
        f.write(f"- **Full Stack Developer Role Total**: {role_counts[ROLE]}\n")
        f.write(f"- **Remaining to 500 Target**: {report['staging_metrics']['remaining_to_500']}\n\n")
        f.write("### Similarity\n")
        f.write(f"- **Max Question Sim**: {report['max_similarity_scores']['question']}\n")
        f.write(f"- **Max Answer Sim**: {report['max_similarity_scores']['answer']}\n")
        f.write(f"- **Max Combined Sim**: {report['max_similarity_scores']['combined']}\n")
        f.write(f"- **Intra-batch Overlaps**: {len(intra)}\n")
        f.write(f"- **Answer Overlaps (>0.5)**: {len(ans_flags)}\n\n")
        f.write("### Distributions\n")
        f.write(f"- **Difficulty**: {dict(diff_counts)}\n")
        f.write(f"- **Intent**: {dict(intent_counts)}\n")
        f.write(f"- **Primary Skill**: {dict(skill_counts)}\n")
        f.write(f"- **Technology**: {dict(tech_counts)}\n")
        f.write(f"- **Topic**: {dict(topic_counts)}\n\n")
        f.write("### Top Openings\n")
        for op, count in openings.most_common(8):
            f.write(f"- `{op}`: {count}\n")

    print(f"Successfully generated 50 Full Stack Developer questions.")

if __name__ == "__main__":
    main()
