"""Batch 32 Part 1 question content (Full Stack). Targeted Gap Generation."""

ROLE = "Full Stack Developer"

BUCKET_KEYS = {
    "DEPLOYMENT_SEQUENCING": ("Deployment Sequencing", "CI/CD & Migrations", "Architecture", ["Full Stack Developer", "Backend Developer", "DevOps / Cloud Engineer"]),
}

Q = [
# ---------------- DEPLOYMENT_SEQUENCING ----------------
("DEPLOYMENT_SEQUENCING", "scenario", "hard", "scenario", ["Zero-Downtime", "API Contracts"],
 "You are deploying a breaking change to a REST API and the frontend simultaneously. Your infrastructure uses a 10-minute Rolling Deployment. During rollout, users complain the app is broken. Why did this simultaneous deployment fail, and what is the correct release sequence?",
 "During a rolling deployment, the infrastructure runs a mix of v1 and v2 servers simultaneously. If a user's browser loads the v2 frontend but their API request hits a v1 backend server, the contract is broken. The correct sequence is 'Expand and Contract': 1. Deploy a backward-compatible backend (supporting v1 and v2), 2. Deploy the v2 frontend, 3. Deploy the final backend removing the v1 contract.",
 ["Rolling deployments run a mix of v1 and v2 servers simultaneously, breaking strict contracts", "Requires an 'Expand and Contract' sequence", "Deploy backward-compatible backend first, then frontend, then cleanup backend"],
 ["The rolling deployment made the servers dizzy"]),

("DEPLOYMENT_SEQUENCING", "implement", "medium", "implementation", ["Database Migrations", "Zero-Downtime"],
 "You need to rename a highly queried database column from `first_name` to `given_name`. How do you sequence this database migration across a zero-downtime full-stack deployment without crashing the live app?",
 "Use a multi-phase 'Expand and Contract' migration. Phase 1: Add the new `given_name` column. Phase 2: Deploy backend code that writes to both columns but reads from the old. Phase 3: Run a background script to backfill data. Phase 4: Deploy code that reads/writes exclusively to the new column. Phase 5: Drop the old `first_name` column.",
 ["Use a multi-phase 'Expand and Contract' migration", "Add the new column, dual-write to both, backfill historical data", "Read from the new column exclusively, then finally drop the old column"],
 ["Just run `ALTER TABLE RENAME` and tell users to refresh quickly"]),

("DEPLOYMENT_SEQUENCING", "debug", "hard", "debugging", ["CDN", "Frontend State"],
 "You deploy a new React frontend to a CDN. Five minutes later, you deploy the new backend API. You verify the CDN cache was successfully invalidated. However, thousands of users still experience broken API calls originating from the old frontend code. Why did CDN invalidation fail to protect them?",
 "CDN invalidation only clears the server-side cache. The users experiencing errors already had the Single Page Application (SPA) loaded in their browser's local memory or Service Worker *before* the deployment. Their active browser tabs continued running the old JavaScript, calling the new incompatible backend. You must version APIs or force client-side reloads.",
 ["CDN invalidation does not clear the active browser memory/state of users already on the site", "Active browser tabs continued running the old SPA JavaScript against the new backend", "Fix: Maintain backward-compatible APIs or implement forced client-side reloads on version mismatch"],
 ["The CDN physically forgot to delete the files"]),

("DEPLOYMENT_SEQUENCING", "tradeoff", "medium", "tradeoff", ["Feature Flags", "Branch Deployments"],
 "What is the tradeoff of using 'Feature Flags' (Feature Toggles) versus using isolated 'Branch Deployments' to safely test new full-stack features in production?",
 "Feature flags decouple code deployment from feature release, allowing instant rollbacks without redeploying. The tradeoff is massive technical debt: flags create complex conditional logic (if/else spaghetti) in both frontend and backend code, requiring rigorous cleanup. Branch deployments keep code clean but require spinning up expensive duplicate infrastructure and don't test the true production database state.",
 ["Feature Flags: Instant rollback and decoupled release, but creates technical debt and complex conditional logic", "Branch Deployments: Keeps codebase clean but requires expensive duplicate infrastructure", "Branch deployments also fail to test against the true, live production database state"],
 ["Feature flags are physical flags you wave in the server room"]),

("DEPLOYMENT_SEQUENCING", "scenario", "hard", "scenario", ["WebSockets", "Blue/Green Deployment"],
 "A full-stack application uses WebSockets for real-time chat. You deploy a backend update changing the message schema. During the 5-minute Blue/Green cutover, active WebSockets drop and users see errors. How should you architect the schema change to prevent dropping live connections?",
 "You cannot simply drop WebSockets without client disruption. You must version the WebSocket event payloads (e.g., `{version: 2, type: 'msg'}`). The backend must be deployed first, programmed to concurrently accept v1 and v2 schemas from existing connections. Once the frontend deploys and starts sending v2, the backend seamlessly handles it without forcing a socket disconnect.",
 ["Version the WebSocket event payloads explicitly inside the message data", "Deploy the backend first, programmed to concurrently handle both v1 and v2 schemas", "Allows the frontend to upgrade to v2 seamlessly without forcing a TCP disconnect"],
 ["Tell the users to type slower during the deployment"]),

("DEPLOYMENT_SEQUENCING", "explain", "easy", "concept", ["Blue/Green Deployment"],
 "In a zero-downtime deployment, what is a 'Blue-Green Deployment'?",
 "Blue-Green deployment is a release strategy maintaining two identical production environments (Blue and Green). Live traffic currently points to Blue. You deploy and test the new version entirely on Green without affecting users. Once verified, you switch the load balancer to route 100% of traffic to Green. Rollback is instant by switching the router back to Blue.",
 ["Maintains two identical production environments (Blue and Green)", "New code is deployed and tested on the idle environment", "Traffic is instantly switched at the load balancer level, enabling instant rollbacks"],
 ["Painting the server racks blue and green for cooling efficiency"]),

("DEPLOYMENT_SEQUENCING", "implement", "medium", "implementation", ["Frontend Versioning", "Cache Busting"],
 "You deploy a new version of your frontend SPA. How do you implement 'Frontend Asset Versioning' to ensure browsers don't accidentally load a stale CSS file from a previous deployment alongside the new JavaScript?",
 "You implement Content Hashing (Cache Busting) in your build tool (Webpack/Vite). The build process appends a unique cryptographic hash of the file's contents to the filename (e.g., `app.[hash].css`). The `index.html` references the new hash. The server instructs the browser to cache hashed files infinitely; because the filename changes on every code edit, the browser downloads the new asset instantly.",
 ["Implement Content Hashing (Cache Busting) in the build tool", "Appends a unique hash of the file contents to the filename (`app.[hash].css`)", "Forces the browser to download the new file while allowing infinite caching for unchanged files"],
 ["Ask the user to hard-refresh their browser by pressing F5 10 times"]),

("DEPLOYMENT_SEQUENCING", "debug", "hard", "debugging", ["Rollbacks", "Database Schema"],
 "You use Blue/Green deployment. You deploy a database schema migration, deploy the Green backend/frontend, and switch traffic. Ten minutes later, you find a bug in the Green frontend. You flip the load balancer back to Blue, but suddenly the Blue environment starts crashing. Why did the rollback fail?",
 "Blue/Green environments share the exact same production Database. While you instantly rolled back the stateless frontend/backend code to Blue, the Database schema was permanently mutated by the migration. The old Blue backend code was not forward-compatible with the new database schema (e.g., querying a column you just dropped), causing it to crash upon rollback.",
 ["Blue and Green environments share the exact same persistent Database", "The initial migration permanently mutated the shared database schema", "The old Blue backend code was not forward-compatible with the new schema (e.g., a dropped column)"],
 ["The Blue servers were turned off to save electricity"]),

("DEPLOYMENT_SEQUENCING", "scenario", "medium", "scenario", ["Asynchronous Jobs", "Payload Schemas"],
 "After a backend deployment, a background asynchronous job queue (like Celery or Sidekiq) starts throwing deserialization errors. The frontend and API work perfectly. What deployment sequencing error caused the background workers to crash?",
 "The sequencing failed to coordinate the API servers and the Background Worker servers. The newly deployed API started pushing job payloads to the Redis/RabbitMQ queue using a new JSON schema. However, the background worker nodes were still running the old code version (or deploying on a delay) and could not deserialize the new payload schema, crashing the worker process.",
 ["The new API pushed jobs to the queue using a new, incompatible JSON payload schema", "The background worker nodes were still running the old code version", "The workers crashed because they could not deserialize the new payload structure"],
 ["The background workers went on strike for better pay"]),

("DEPLOYMENT_SEQUENCING", "explain", "easy", "concept", ["Canary Release"],
 "What is the primary purpose of a 'Canary Release' when deploying a full-stack application?",
 "A Canary Release reduces deployment risk by slowly rolling out the new version to a small subset of live users (e.g., 5% of traffic) rather than everyone at once. This allows you to safely monitor latency, error rates, and business metrics on a small scale. If the canary degrades performance, you halt and revert, minimizing the blast radius of the bug.",
 ["Slowly rolls out the new version to a small subset of live traffic (e.g., 5%)", "Allows safe monitoring of latency, errors, and business metrics in production", "Minimizes the blast radius of bugs by allowing early halting and reverting"],
 ["A release that makes bird noises when it completes successfully"]),

("DEPLOYMENT_SEQUENCING", "implement", "hard", "implementation", ["Authentication", "Session State"],
 "You deploy a critical backend security update that changes the JWT signing secret, invalidating all current tokens. How do you sequence this to force active frontends to seamlessly re-authenticate without breaking the UI state?",
 "The backend must reject old JWTs with a `401 Unauthorized` response. The frontend must have a pre-deployed global HTTP interceptor (Axios/Fetch). When the interceptor catches the `401`, it explicitly prevents a hard crash, pauses all outgoing API requests, silently redirects the user to a refresh/login flow, and upon success, automatically retries the paused requests, preserving UI state.",
 ["Backend rejects old tokens with a `401 Unauthorized`", "Frontend global HTTP interceptor catches the 401 and pauses all outgoing requests", "Redirects to refresh/login, then automatically retries the paused requests to preserve UI state"],
 ["Log everyone out violently and delete their unsaved work"]),

("DEPLOYMENT_SEQUENCING", "tradeoff", "medium", "tradeoff", ["Monorepo", "CI/CD"],
 "What is the tradeoff of using a Monorepo versus Polyrepos (Multi-repo) when coordinating frontend and backend deployments?",
 "A Monorepo ensures frontend and backend code/types/contracts are versioned together in a single atomic commit, making cross-boundary refactoring and synchronized CI/CD drastically easier. The tradeoff is that as the codebase grows, CI build times become massive, Git performance degrades, and it requires complex tooling (Turborepo) to prevent frontend changes from needlessly triggering backend rebuilds.",
 ["Monorepo: Atomic commits make cross-boundary refactoring and synchronized deployments drastically easier", "Tradeoff: Massive CI build times and degraded Git performance at scale", "Tradeoff: Requires complex tooling to prevent cascading unnecessary rebuilds"],
 ["Monorepos only allow you to use one programming language for everything"]),

("DEPLOYMENT_SEQUENCING", "debug", "hard", "debugging", ["Rolling Deployment", "Frontend Errors"],
 "You deploy a new frontend requesting a new `status` field from the API. The API is deployed simultaneously in a rolling fashion. The frontend wraps the fetch in a `try/catch`, but the React app crashes with 'Cannot read properties of undefined (reading status)'. Why didn't the `try/catch` work?",
 "The `try/catch` only caught network failures. Due to the rolling deployment, the frontend occasionally hit a v1 API server that returned a perfectly valid `200 OK` JSON response, but simply omitted the new `status` field. The network request succeeded, bypassing the `try/catch`. The crash occurred later during render. You must implement defensive optional chaining (`data?.status`).",
 ["The frontend hit a v1 API server returning a valid `200 OK`, bypassing the `try/catch`", "The v1 server simply omitted the new `status` field from the valid JSON", "Fix: Must implement defensive optional chaining (`data?.status`) for API fields during migrations"],
 ["React naturally ignores `try/catch` blocks because it hates errors"]),

("DEPLOYMENT_SEQUENCING", "scenario", "medium", "scenario", ["Strangler Fig", "Microservices"],
 "You are migrating a legacy backend monolith to a new microservice. How do you use the 'Strangler Fig Pattern' to sequence this deployment without a risky, massive cutover?",
 "You deploy an API Gateway (Reverse Proxy) in front of the legacy monolith. You deploy the new microservice alongside it. You configure the proxy to route *only* specific, isolated API routes (e.g., `/api/billing`) to the new microservice, while leaving all other traffic routing to the monolith. Over time, you migrate route by route until the monolith is entirely 'strangled' and deleted.",
 ["Deploy an API Gateway/Reverse Proxy in front of the legacy monolith", "Route only specific, isolated API endpoints to the new microservice", "Gradually migrate route by route over time until the monolith is obsolete ('strangled')"],
 ["Wrap the server in vines until it physically stops working"]),

("DEPLOYMENT_SEQUENCING", "fundamentals", "easy", "concept", ["Database Migrations"],
 "In the context of database migrations during deployment, what is a 'Backward-Compatible Change'?",
 "A backward-compatible database change is a structural modification (like adding a new nullable column or adding a new table) that does not break the existing application code currently running in production. Dropping a column, renaming a table, or adding a strict `NOT NULL` constraint without a default value are NOT backward-compatible, as they will instantly crash older code versions.",
 ["A structural modification that does not break existing production application code", "Examples: Adding a new nullable column, adding a new table", "Non-examples (Breaking): Dropping columns, renaming tables, adding `NOT NULL` without defaults"],
 ["A change that only works on older versions of Windows"]),

("DEPLOYMENT_SEQUENCING", "implement", "medium", "implementation", ["CLS", "Frontend Assets"],
 "You deploy a marketing page update with 5 heavy images. The deployment completes, but the page looks broken for 3 seconds before images snap into place, shifting the layout. How do you fix this visual deployment glitch?",
 "To structurally prevent the layout shift (Cumulative Layout Shift - CLS), you must explicitly define the `width` and `height` attributes (or CSS aspect-ratio) on the HTML `<img>` tags. This mathematically reserves the exact visual space in the DOM before the newly deployed heavy images actually finish downloading from the CDN.",
 ["Explicitly define `width` and `height` attributes (or CSS `aspect-ratio`) on `<img>` tags", "Reserves the exact visual space in the DOM before the image finishes downloading", "Prevents Cumulative Layout Shift (CLS) during the heavy asset load"],
 ["Tell the marketing team to stop using images"]),

("DEPLOYMENT_SEQUENCING", "scenario", "hard", "scenario", ["SSR", "Cache Bypass"],
 "You deploy a Next.js Server-Side Rendering (SSR) update adding a new query parameter to an internal backend API call. The backend is updated simultaneously. The SSR server CPU spikes to 100% and crashes. Why did adding a query parameter crash the SSR server?",
 "By adding a new, highly cardinal query parameter, you completely bypassed the backend's edge cache (Redis/CDN). The backend was suddenly flooded with raw, uncacheable requests. Because SSR blocks the frontend response until the backend replies, the slow backend caused the SSR Node.js event loop to pile up thousands of pending concurrent requests, exhausting memory and CPU.",
 ["The new query parameter bypassed the backend edge cache (Redis/CDN)", "The backend was flooded with uncacheable requests, drastically slowing down", "SSR blocks responses; pending requests piled up in the Node.js event loop, exhausting CPU/Memory"],
 ["Next.js is allergic to query parameters"])
]
