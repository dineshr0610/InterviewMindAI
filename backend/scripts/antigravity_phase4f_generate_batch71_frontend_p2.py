import asyncio
import json
import os
import re
import sys
import uuid
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "Frontend Developer"

LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    (
        "B71_15",
        "Frontend Developer",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Next.js", "Architecture"],
        "React Server Components (RSC)",
        "React Server Components vs Server-Side Rendering (SSR)",
        "A team migrating to Next.js 13+ (App Router) is confused about the difference between Server-Side Rendering (SSR) and React Server Components (RSC). They ask: 'Doesn't SSR already render components on the server? Why do we need RSC?' Explain the architectural difference between how SSR and RSC handle JavaScript bundles, hydration, and client-side execution.",
        "1) SSR Mechanism: In traditional SSR (like Next.js `getServerSideProps`), the component is executed on the server to generate an initial static HTML string for fast First Paint. However, the exact same component code, along with all its heavy dependencies (like `moment.js` or `d3`), is still bundled and sent to the browser. The browser downloads the JS and 'hydrates' the HTML, attaching event listeners. The JS payload is large. 2) RSC Mechanism: React Server Components are executed EXCLUSIVELY on the server. They generate a proprietary binary/JSON stream representing the UI tree, which is sent to the client. The actual JavaScript code of the Server Component (and its heavy dependencies) is NEVER sent to the browser. There is zero hydration for RSCs. 3) Tradeoffs: RSCs drastically reduce the client-side JS bundle size and can securely access backend resources directly (like databases) without building APIs. However, because their JS never ships to the browser, RSCs cannot use interactivity (no `useState`, `onClick`, or `useEffect`). Traditional SSR components (now called 'Client Components' in Next 13+) are still required for interactive islands.",
        [
            "Identifies that SSR still sends the component's JS bundle to the client for hydration",
            "Explains that RSC code never ships to the browser, completely eliminating bundle size overhead for those components",
            "Highlights that RSCs cannot contain interactivity or state, requiring Client Components for dynamic behaviors"
        ],
        [
            "Claims RSCs are just an alias for getServerSideProps",
            "Suggests that RSCs run inside the browser's Service Worker"
        ]
    ),
    (
        "B71_16",
        "Frontend Developer",
        "explain",
        "medium",
        "explain",
        ["Network Protocols", "Web Security"],
        "CORS",
        "CORS Preflight Requests and the OPTIONS Method",
        "A frontend application running on `https://shop.com` makes an AJAX `POST` request with a JSON payload (`Content-Type: application/json`) to an API hosted on `https://api.shop.com`. The browser's network tab shows two requests: first an `OPTIONS` request, then the actual `POST` request. Why does the browser send this `OPTIONS` request, and how do backend developers configure it to prevent the frontend from experiencing a 2x latency penalty on every API call?",
        "1) The CORS Preflight Mechanism: Browsers enforce the Same-Origin Policy. Because `https://shop.com` and `https://api.shop.com` are different origins (different subdomains), the browser must verify if the API permits cross-origin requests. A `POST` with `application/json` is classified as a 'non-simple' request. Before sending the actual data, the browser automatically sends a Preflight `OPTIONS` request asking the server for permissions (`Access-Control-Request-Method` and `Access-Control-Request-Headers`). 2) The Latency Penalty: If the server responds with HTTP 200 and the correct `Access-Control-Allow-Origin` headers, the browser immediately sends the actual `POST`. However, this requires two full HTTP round-trips for every single API call, doubling network latency. 3) Resolution (Caching the Preflight): To eliminate the latency penalty, the backend server must include the `Access-Control-Max-Age: 86400` header in the `OPTIONS` response. This tells the browser to cache the preflight permission for 24 hours (86400 seconds) for that specific endpoint, allowing subsequent `POST` requests to skip the `OPTIONS` check entirely.",
        [
            "Identifies that non-simple cross-origin requests (like application/json) trigger an automatic OPTIONS preflight check",
            "Explains the preflight validates if the target server permits the specific origin, method, and headers",
            "Prescribes the Access-Control-Max-Age header to cache the preflight result and avoid the 2x latency penalty"
        ],
        [
            "Claims OPTIONS requests are used to encrypt the payload before sending",
            "Suggests turning off CORS in the browser settings using a JavaScript command"
        ]
    ),
    (
        "B71_17",
        "Frontend Developer",
        "tradeoff",
        "medium",
        "tradeoff",
        ["React Framework", "Performance Tuning"],
        "React / useMemo",
        "The Performance Cost of Overusing useMemo and useCallback",
        "A junior developer discovers `useMemo` and `useCallback` and decides to wrap every single variable, object, and inline function inside a React functional component with them to 'prevent re-renders and maximize performance.' Explain why this anti-pattern actually degrades performance and increases memory consumption.",
        "1) The Cost of Memoization: `useMemo` and `useCallback` are not free. When invoked, React must execute the hook, allocate memory to store the dependency array, allocate memory to store the cached value/function, and on every subsequent render, loop through the dependency array comparing previous values to current values using `Object.is()`. 2) Performance Degradation: If an object is cheap to create (e.g., `const style = { color: 'red' }`) or a function is simple (`const handleClick = () => setCount(c => c+1)`), the CPU cost of running the dependency array comparison and the memory overhead of the closure retention is actually HIGHER than simply throwing the object away and recreating it. The V8 Garbage Collector is extremely fast at cleaning up short-lived objects. 3) When to use them: You should ONLY use `useMemo` for highly expensive synchronous calculations (e.g., sorting a 10,000 item array) or when the resulting object/function is passed as a prop to a child component that is strictly memoized (using `React.memo`), where referential equality is required to prevent the child from undergoing a heavy re-render.",
        [
            "Explains the CPU and memory overhead of executing the hook, storing dependencies, and comparing them on every render",
            "Asserts that creating simple objects/functions is cheaper than the dependency comparison overhead",
            "Identifies valid use cases: expensive calculations or preserving referential equality for React.memo children"
        ],
        [
            "Claims useMemo stops the component from unmounting",
            "Suggests useMemo pushes variables to the server for caching"
        ]
    ),
    (
        "B71_18",
        "Frontend Developer",
        "diagnose",
        "hard",
        "debugging",
        ["CSS Architecture", "Browser Architecture"],
        "CSS / Specificity",
        "CSS Specificity Wars and the !important Trap",
        "A UI element has the following CSS rules applied to it: `#header .nav-item.active { color: red; }` and `nav > ul > li.active[data-state='open'] { color: blue; }`. Which color is applied to the element, and how is the CSS Specificity score calculated for each selector? Why is `!important` considered a dangerous anti-pattern for resolving these conflicts?",
        "1) Calculating Specificity: CSS specificity is calculated as a 3-tier tuple: (ID, Class/Attribute/Pseudo-class, Element/Pseudo-element). A) `#header .nav-item.active`: 1 ID (`#header`), 2 Classes (`.nav-item`, `.active`), 0 Elements. Score: (1, 2, 0). B) `nav > ul > li.active[data-state='open']`: 0 IDs, 2 Class/Attributes (`.active`, `[data-state]`), 3 Elements (`nav`, `ul`, `li`). Score: (0, 2, 3). 2) The Winner: The first rule wins because it has an ID. Specificity is evaluated left-to-right; (1, 2, 0) strictly defeats (0, 2, 3) regardless of how many classes the latter has. 3) The `!important` Trap: If a developer adds `!important` to the blue rule to 'force' it to work, they bypass the specificity cascade entirely. `!important` creates a parallel, higher-priority cascade tier. Future developers attempting to override that blue color will be forced to write even more `!important` tags, eventually leading to inline styles, destroying the maintainability of the stylesheet. The correct fix is to match or exceed the specificity natively (e.g., adding an ID to the second rule) or refactoring to a flat specificity system like BEM.",
        [
            "Calculates Rule A as (1, 2, 0) and Rule B as (0, 2, 3)",
            "Identifies Rule A (Red) as the winner because IDs trump any number of classes/attributes",
            "Explains that !important breaks the cascade, forcing an arms race of !important declarations that ruins maintainability"
        ],
        [
            "Claims the last rule loaded in the file always wins regardless of specificity",
            "Calculates specificity by counting the total number of characters in the selector string"
        ]
    ),
    (
        "B71_19",
        "Frontend Developer",
        "explain",
        "medium",
        "explain",
        ["Web APIs", "Performance Tuning"],
        "requestAnimationFrame",
        "requestAnimationFrame vs setTimeout for Web Animations",
        "A developer implements a custom JavaScript progress bar animation using `setInterval(() => updateWidth(), 16)` to target 60 frames per second. The animation looks jittery and tears on high-refresh-rate monitors (144Hz), and it continues consuming CPU when the user switches to a different browser tab. Why is `requestAnimationFrame` architecturally superior to `setInterval` for DOM animations?",
        "1) The VSync Problem: `setInterval(fn, 16)` is completely blind to the monitor's refresh rate and the browser's rendering pipeline. It fires a macrotask every 16ms. If the browser happens to be busy parsing layout, or if the monitor refreshes at 144Hz (6.9ms), the interval will drift out of phase with the hardware's VSync. This causes frame drops, micro-stutters, and screen tearing because DOM updates are pushed mid-render. 2) The rAF Synchronization: `requestAnimationFrame(callback)` tells the browser: 'Execute this callback immediately *before* your next scheduled screen repaint'. The browser automatically synchronizes the callback execution with the hardware VSync (e.g., firing exactly 144 times a second on a 144Hz display, or exactly 60 on a 60Hz display). This guarantees butter-smooth frame alignment. 3) Background Tab Throttling: When a user switches tabs, `setInterval` keeps running at 60fps in the background, needlessly draining battery and CPU. Browsers automatically pause or heavily throttle `requestAnimationFrame` callbacks for background tabs, saving massive amounts of system resources.",
        [
            "Identifies that setInterval is blind to hardware VSync and browser paint cycles, causing tearing and jitter",
            "Explains that requestAnimationFrame synchronizes execution immediately prior to the browser's native repaint cycle",
            "Highlights that browsers automatically pause/throttle rAF in background tabs to save battery and CPU"
        ],
        [
            "Claims requestAnimationFrame uses the GPU while setInterval uses the CPU",
            "Suggests requestAnimationFrame is deprecated in favor of CSS transitions exclusively"
        ]
    ),
    (
        "B71_20",
        "Frontend Developer",
        "tradeoff",
        "hard",
        "tradeoff",
        ["WebAssembly", "Architecture"],
        "WebAssembly vs JavaScript",
        "WebAssembly (Wasm) Tradeoffs and the DOM Interoperability Bottleneck",
        "A team wants to rewrite a complex React data-grid component entirely in Rust and compile it to WebAssembly (Wasm) to 'make the UI 10x faster'. However, after implementation, rendering 10,000 DOM nodes from Wasm is actually SLOWER than doing it in pure JavaScript. Why does Wasm underperform JavaScript when manipulating the DOM, and what are the actual optimal use cases for WebAssembly in a web application?",
        "1) The DOM Bottleneck: WebAssembly does NOT have direct access to the browser's Document Object Model (DOM) or Web APIs. To update a div's text from Wasm, the Wasm module must pause, copy memory out of its linear memory space, cross the JavaScript binding boundary, and invoke a JavaScript function that actually manipulates the DOM. 2) Serialization Overhead: Crossing the Wasm-to-JS boundary requires serializing and copying strings/objects, which incurs significant CPU overhead. If Wasm attempts to render 10,000 DOM nodes, it triggers 10,000 costly boundary crossings, making it much slower than JS which executes within the same engine environment as the DOM. 3) Optimal Use Cases: Wasm is designed for CPU-bound, computationally heavy tasks that do not require constant DOM manipulation. Optimal use cases include video/audio encoding, 3D physics engines, cryptography, image processing, or running existing C++ codebases (like AutoCAD or SQLite) purely in the browser's memory, passing only the final rendered canvas or data array back to JS.",
        [
            "Explains that Wasm lacks direct DOM access and must bridge via JavaScript to update the UI",
            "Identifies the serialization and boundary-crossing overhead as the cause of slow DOM manipulation",
            "Correctly scopes Wasm to CPU-heavy, math-intensive tasks rather than UI rendering"
        ],
        [
            "Claims Wasm is slower because Rust is a slower language than JavaScript",
            "Suggests downloading more RAM to fix the Wasm performance issue"
        ]
    ),
    (
        "B71_21",
        "Frontend Developer",
        "scenario",
        "medium",
        "scenario",
        ["Authentication", "Web Security"],
        "JWT / Refresh Tokens",
        "Silent Refresh: Rotating Short-Lived JWTs via Refresh Tokens",
        "To secure an SPA, you implement short-lived JWT access tokens (valid for 15 minutes) and long-lived refresh tokens (valid for 7 days). When the access token expires, the SPA must seamlessly obtain a new one without forcing the user to log in again, and without exposing the refresh token to XSS. Describe the architecture of the 'Silent Refresh' flow, detailing exactly where each token is stored and how the refresh network request is authenticated.",
        "1) Token Storage: The short-lived Access Token is returned in the JSON payload of the login response and stored strictly in an in-memory variable in the SPA (e.g., a React state or Redux store). It is never written to LocalStorage to prevent XSS theft. The long-lived Refresh Token is returned by the server as a `HttpOnly, Secure, SameSite=Strict` cookie, hiding it completely from JavaScript. 2) The Silent Refresh Flow: When the SPA detects the Access Token is expired (or receives a 401 Unauthorized from an API call), it initiates a 'Silent Refresh'. 3) The Request: The SPA makes a background POST request to the `/api/auth/refresh` endpoint. Because the Refresh Token is an HttpOnly cookie, the browser automatically attaches it to this request. JavaScript does not touch the refresh token. 4) The Response: The backend validates the refresh token cookie, generates a new short-lived Access Token, and returns it in the JSON response payload. The SPA updates its in-memory variable and transparently retries the failed API call. If the refresh token is also expired, the server returns 401, and the SPA redirects the user to the login page.",
        [
            "Identifies in-memory storage for the Access Token to prevent XSS",
            "Identifies HttpOnly cookie storage for the Refresh Token to prevent XSS while allowing automatic browser attachment",
            "Describes the interceptor flow: catch 401, POST to /refresh, receive new in-memory JWT, retry original request"
        ],
        [
            "Suggests storing both tokens in LocalStorage for easy access",
            "Claims the Refresh Token must be sent in the Authorization header"
        ]
    ),
    (
        "B71_22",
        "Frontend Developer",
        "explain",
        "medium",
        "explain",
        ["State Management", "Architecture"],
        "Redux / Middleware",
        "Redux Thunk vs Redux Saga for Side Effects",
        "In a large React/Redux application, the team needs to handle complex asynchronous side effects, such as debouncing API calls, polling, and canceling in-flight network requests when a component unmounts. Compare Redux Thunk and Redux Saga. Why is Redux Saga better suited for complex async orchestration than Redux Thunk?",
        "1) Redux Thunk (Simplicity): Thunk is a minimalist middleware that allows action creators to return a function instead of a plain object. It relies on standard JavaScript Promises and `async/await`. While great for simple AJAX calls, handling complex flows like debouncing, concurrent request cancellation, or background polling in Thunk requires messy, stateful boilerplate (tracking `abortControllers` and timer IDs inside the thunk or component). 2) Redux Saga (Power and Orchestration): Saga uses ES6 Generators (`function*`) to model side effects as separate, background threads ('sagas') that listen for dispatched actions. 3) Advantages of Saga: A) Declarative Effects: Sagas yield plain objects describing instructions (e.g., `yield call(api.fetch)`), making them incredibly easy to unit test without mocking the actual API. B) Advanced Concurrency: Saga provides built-in operators like `takeLatest` (automatically cancels the previous in-flight API call if a new action arrives, fixing race conditions), `debounce`, `throttle`, and `race` (e.g., racing an API call against a timeout action). This shifts all complex async orchestration completely out of the UI components and into isolated, testable state machines.",
        [
            "Contrasts Thunk's simple Promise-based function returns with Saga's ES6 Generator-based background threads",
            "Highlights Saga's built-in operators (takeLatest, debounce, race) for handling complex concurrency and cancellation",
            "Notes that Sagas yield declarative effect objects, making them significantly easier to unit test than Thunks"
        ],
        [
            "Claims Redux Thunk is written in Python while Saga is written in JavaScript",
            "Suggests that Saga replaces the React rendering engine"
        ]
    ),
    (
        "B71_23",
        "Frontend Developer",
        "diagnose",
        "hard",
        "debugging",
        ["Performance Tuning", "Network Protocols"],
        "Core Web Vitals / CLS",
        "Diagnosing and Fixing Cumulative Layout Shift (CLS) on Image Load",
        "A news article page suffers from a poor Cumulative Layout Shift (CLS) score in Google Lighthouse. The text of the article loads instantly, but 500ms later, a hero image loads, pushing all the text down the screen by 400 pixels. How do you architect the CSS and HTML to fix this specific CLS issue so the browser knows exactly how much space to reserve before the image downloads?",
        "1) The Root Cause: Browsers cannot know the dimensions of an image until the image metadata is downloaded. If no dimensions are specified in the HTML/CSS, the browser renders the image with a height of 0px. When the image finally downloads, the browser forces a layout recalculation, expanding the image to its natural size and shoving all subsequent content down, causing a severe Layout Shift (CLS penalty). 2) The Modern HTML Solution (Aspect Ratio Mapping): You must explicitly provide `width` and `height` attributes on the `<img>` tag: `<img src=\"hero.jpg\" width=\"800\" height=\"400\" />`. In modern browsers, this does NOT force the image to be exactly 800x400 pixels. Instead, the browser uses these numbers to compute the intrinsic aspect ratio (2:1). 3) Responsive CSS: Combine this with standard responsive CSS: `img { max-width: 100%; height: auto; }`. The browser applies the aspect ratio to the flexible width. If the container is 400px wide, the browser mathematically reserves exactly 200px of vertical space before a single byte of the image is downloaded, completely eliminating the Cumulative Layout Shift.",
        [
            "Identifies the lack of pre-defined dimensions causing the browser to allocate 0px height initially",
            "Prescribes providing explicit width and height attributes directly on the HTML img tag",
            "Explains that modern browsers use these attributes to calculate the aspect ratio and reserve the exact vertical space dynamically when combined with CSS width: 100%"
        ],
        [
            "Suggests converting all images to base64 strings so they load instantly",
            "Claims CLS is fixed by setting the image opacity to 0 until it loads"
        ]
    ),
    (
        "B71_24",
        "Frontend Developer",
        "concept",
        "medium",
        "concept",
        ["HTML5", "Architecture"],
        "Web Components / Shadow DOM",
        "Shadow DOM Isolation in Web Components",
        "A company wants to distribute a custom `<buy-button>` UI widget to third-party clients. They build it using standard HTML/JS, but when clients embed it, the client's global CSS (like `button { background: black !important; }`) ruins the widget's design. How does utilizing the Shadow DOM in a Custom Web Component solve this CSS bleeding issue, and how does event propagation work across the shadow boundary?",
        "1) Shadow DOM Isolation: The Shadow DOM allows developers to attach an encapsulated 'shadow' DOM tree to a custom element. This tree is rendered separately from the main document's 'light' DOM. 2) CSS Encapsulation: The primary benefit is true CSS scoping. Styles defined inside the Shadow DOM do not leak out to the main document, and crucially, global CSS rules from the main document (like `button { background: black !important; }`) CANNOT penetrate the Shadow boundary to affect elements inside it (with the exception of CSS Custom Properties/Variables and inherited properties like font-family). This guarantees the widget looks identical on every client site. 3) Event Retargeting: When an event (like a click) fires inside the Shadow DOM and bubbles up across the shadow boundary into the main document, the browser 'retargets' the event. To the main document, it looks like the event originated from the `<buy-button>` host element itself, not the internal `<button>` inside the shadow tree. This encapsulates the internal DOM structure from third-party JavaScript listeners.",
        [
            "Defines Shadow DOM as an encapsulated DOM tree attached to a custom element",
            "Explains that global CSS selectors cannot pierce the shadow boundary, protecting the widget's styles",
            "Details event retargeting, where events bubbling out appear to originate from the host element rather than internal shadow nodes"
        ],
        [
            "Claims Shadow DOM is a React feature used to render elements on the backend",
            "Suggests using an iframe because Web Components are deprecated"
        ]
    )
]

def run_batch():
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[8]) or LEAK.search(q[9]):
            print(f"PROMPT LEAK DETECTED in: {q[8]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[8] for q in Q]
    
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
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[8][:50]}...")
            rejected.append(q)
        else:
            print(f"ACCEPTED (Sim: {max_sim:.2f}): {q[8][:60]}...")
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions.")
    if len(rejected) > 0:
        print("Stopping due to rejections.")
        sys.exit(1)
        
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": q[1],
            "role": q[1],
            "applicable_roles": ["Full Stack Developer", "Software Engineer"],
            "primary_skill": q[5][0],
            "skill": q[5][0],
            "secondary_skills": q[5][1:] if len(q[5]) > 1 else [],
            "technology": q[6],
            "topic": q[7],
            "category": "Software Engineering",
            "intent": q[2],
            "difficulty": q[3],
            "question_type": q[4],
            "question": q[8],
            "ideal_answer": q[9],
            "expected_answer": q[9],
            "evaluation_rubric": {
                "strong_indicators": q[10],
                "weak_indicators": q[11]
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
    print("POST-BATCH AUDIT")
    print("========================================")
    print(f"Batch: 71_p2")
    print(f"Target role: {ROLE}")
    print(f"Cumulative total: {len(final_existing)}")
    print("Role counts:")
    for role, count in sorted(role_counts.items()):
        print(f"  {role}: {count}")

if __name__ == "__main__":
    run_batch()
