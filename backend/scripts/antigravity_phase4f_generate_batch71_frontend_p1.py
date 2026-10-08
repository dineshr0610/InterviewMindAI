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
        "B71_1",
        "Frontend Developer",
        "explain",
        "hard",
        "explain",
        ["Browser Architecture", "Performance Tuning"],
        "DOM Rendering",
        "Render Blocking vs Parser Blocking Pipeline",
        "A developer includes an async `<script src='analytics.js' async></script>` in the `<head>` and a `<link rel='stylesheet' href='theme.css'>`. They notice that sometimes the page renders before `analytics.js` executes, but other times the screen remains blank until both the CSS and JS finish loading. Explain the difference between parser-blocking and render-blocking resources in the browser's critical rendering path, and why a stylesheet can unexpectedly block the execution of an async script.",
        "1) Parser vs Render Blocking: A parser-blocking resource halts the HTML parser from building the DOM (e.g., synchronous `<script>`). A render-blocking resource allows the DOM to be parsed but prevents the browser from painting pixels to the screen until it is downloaded and processed (e.g., `<link rel='stylesheet'>`). 2) The Dependency Conflict: While `async` scripts do not block the HTML parser, if `analytics.js` finishes downloading *before* `theme.css` finishes, a race condition occurs. 3) CSSOM Blocks JS Execution: JavaScript has the ability to query the CSS Object Model (CSSOM), such as calling `window.getComputedStyle()`. To prevent race conditions where JS reads incomplete styles, the browser halts the execution of ALL JavaScript (even async scripts that are fully downloaded) if there are pending stylesheets. Therefore, the slow `theme.css` delays the construction of the CSSOM, which in turn blocks the execution of `analytics.js`, keeping the main thread occupied and the screen blank.",
        [
            "Distinguishes between DOM parser-blocking and pixel render-blocking",
            "Identifies that JavaScript execution is paused while the CSSOM is still being constructed",
            "Explains this occurs because scripts might query computed styles, necessitating a complete CSSOM"
        ],
        [
            "Claims async scripts bypass all browser rules and run on a separate CPU thread",
            "Suggests that CSS files contain JavaScript code that must run first"
        ]
    ),
    (
        "B71_2",
        "Frontend Developer",
        "diagnose",
        "hard",
        "debugging",
        ["React Framework", "Memory Management"],
        "React / Hooks",
        "Stale Closures in React useEffect setInterval",
        "A React developer writes a timer component using `useEffect(() => { setInterval(() => setCount(count + 1), 1000); }, []);`. Instead of counting up continuously, the timer increments from 0 to 1, and then stays at 1 forever. Why does this exact symptom occur, and what are two architectural ways to solve it in React 18?",
        "1) The Root Cause (Stale Closures): The `useEffect` has an empty dependency array (`[]`), meaning the setup function runs exactly once during the initial mount. When it runs, it captures the initial state variable `count` (which is `0`) in its lexical closure. The `setInterval` callback `() => setCount(count + 1)` is therefore permanently hardcoded to evaluate as `setCount(0 + 1)`. Every second, it repeatedly sets the state to `1`, never reading the updated state from subsequent renders. 2) Solution 1 (Functional State Updates): Instead of relying on the closed-over `count` variable, pass an updater function to `setCount`. Change it to `setCount(prevCount => prevCount + 1)`. The updater function receives the latest state directly from React's internal fiber node, completely bypassing the closure. 3) Solution 2 (Dependency Array + Cleanup): Add `count` to the dependency array `[count]`, and return `clearInterval(intervalId)` from the effect. This causes the effect to re-run and capture the fresh closure on every render, though it tears down and rebuilds the interval repeatedly.",
        [
            "Identifies the stale closure caused by the empty dependency array capturing the initial render's state",
            "Explains that setCount(count + 1) evaluates to setCount(0 + 1) repeatedly",
            "Provides the functional updater (prev => prev + 1) or dependency array inclusion as solutions"
        ],
        [
            "Claims setInterval runs too fast for React to catch up",
            "Suggests using window.count instead of useState"
        ]
    ),
    (
        "B71_3",
        "Frontend Developer",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Web Security", "Authentication"],
        "Cookies / LocalStorage",
        "LocalStorage vs HttpOnly Cookies for JWT Storage",
        "A Single Page Application (SPA) needs to store a JSON Web Token (JWT) after user login. A junior developer argues for `localStorage` because it is easy to read from JavaScript to attach the `Authorization: Bearer <token>` header. A senior developer insists on using `HttpOnly` cookies. Contrast these two storage mechanisms specifically regarding their vulnerability profiles to XSS vs CSRF attacks, and explain the architectural tradeoffs.",
        "1) LocalStorage Vulnerability (XSS): `localStorage` is accessible via JavaScript. If the application suffers from a Cross-Site Scripting (XSS) vulnerability (e.g., an attacker injects malicious JS into the page), the attacker's script can run `localStorage.getItem('jwt')` and exfiltrate the token to a remote server, fully compromising the user session. 2) HttpOnly Cookie Defense (XSS): An `HttpOnly` cookie is strictly hidden from the browser's JavaScript environment (`document.cookie` cannot read it). Even if an XSS attack executes, the attacker cannot steal the token. The browser automatically attaches the cookie to outgoing requests to the specific domain. 3) Cookie Vulnerability (CSRF): Because browsers automatically attach cookies, they are vulnerable to Cross-Site Request Forgery (CSRF). If a user visits a malicious site, that site can trigger a hidden form POST to the SPA's API, and the browser will attach the HttpOnly cookie. 4) Tradeoff Conclusion: HttpOnly cookies trade XSS token theft for CSRF risk. However, CSRF can be robustly mitigated using `SameSite=Strict` or `Lax` cookie attributes and Anti-CSRF tokens, making HttpOnly cookies the industry standard for session security.",
        [
            "Identifies LocalStorage as highly vulnerable to token exfiltration via XSS",
            "Explains that HttpOnly hides the cookie from JavaScript, preventing direct token theft",
            "Acknowledges that cookies introduce CSRF risks but notes SameSite attributes mitigate this"
        ],
        [
            "Claims LocalStorage is encrypted by the browser by default",
            "Suggests storing the JWT in the URL hash fragment instead"
        ]
    ),
    (
        "B71_4",
        "Frontend Developer",
        "explain",
        "hard",
        "explain",
        ["JavaScript Internals", "Performance Tuning"],
        "V8 Engine",
        "Hidden Classes and Inline Caching in V8",
        "In a high-frequency financial trading dashboard, an array contains millions of JavaScript objects representing trades. A developer initializes trades as `const t1 = { price: 100, symbol: 'AAPL' }` and `const t2 = { symbol: 'MSFT', price: 200 }`. The V8 engine executes a loop summing the prices, but profiling shows severe performance degradation. Explain how V8's Hidden Classes (Shapes/Maps) and Inline Caching work, and why changing the order of property initialization causes a severe de-optimization in the V8 pipeline.",
        "1) Hidden Classes (Shapes): JavaScript is a dynamically typed language without strict structs. To optimize property access, V8 dynamically generates 'Hidden Classes' (or Shapes) in memory. When an object is created, V8 builds a transition tree based on the exact order properties are added. `t1` creates Shape A (empty) -> Shape B (adds 'price') -> Shape C (adds 'symbol'). `t2` creates Shape A (empty) -> Shape D (adds 'symbol') -> Shape E (adds 'price'). Because the initialization order differs, `t1` and `t2` have completely completely different underlying Hidden Classes, even though they contain the exact same keys. 2) Inline Caching (IC): When a function repeatedly accesses `obj.price` in a loop, V8's Inline Cache remembers the memory offset of 'price' for the specific Hidden Class it saw previously. This turns dictionary lookups into $O(1)$ direct pointer arithmetic. 3) Megamorphic De-optimization: Because the loop receives objects with alternating Hidden Classes (Shape C then Shape E), the Inline Cache constantly misses (polymorphic or megamorphic state). V8 aborts the fast pointer arithmetic and falls back to a slow, costly hash dictionary lookup for every single object, destroying execution throughput.",
        [
            "Explains that V8 dynamically creates Hidden Classes based on the exact sequence of property additions",
            "Details Inline Caching turning property lookups into fast memory offset pointer arithmetic",
            "Identifies that different initialization orders create megamorphic cache misses, reverting V8 to slow dictionary lookups"
        ],
        [
            "Claims V8 compiles JavaScript directly into CSS to render objects faster",
            "Suggests using TypeScript because it forces the browser to run native C++ code"
        ]
    ),
    (
        "B71_5",
        "Frontend Developer",
        "diagnose",
        "medium",
        "debugging",
        ["CSS Architecture", "UI Engineering"],
        "CSS / Stacking Contexts",
        "Z-Index Failures and Stacking Contexts",
        "A developer sets a modal dialog to `z-index: 9999; position: absolute;` but it still appears *behind* a simple sticky header that has `z-index: 10; position: sticky;`. The developer increases the modal's z-index to `9999999` but nothing changes. Explain the CSS concept of Stacking Contexts and why a higher z-index on a child element cannot bypass the z-index of its parent's stacking context.",
        "1) The Stacking Context Boundary: In CSS, `z-index` is not a global document-wide absolute scale. It only applies within the local 'Stacking Context' of the element's parent hierarchy. 2) Creation of Contexts: A new stacking context is created by specific CSS properties, including `position: sticky/fixed/relative` (with a z-index > auto), `opacity` < 1, `transform`, `filter`, and `flex/grid` children with z-index. 3) The Trap: If the modal is nested inside a main container, and that main container forms a stacking context with `z-index: 1`, the entire container and all its descendants are painted on layer 1. The sticky header forms a separate stacking context on the same peer level with `z-index: 10`. 4) Resolution: Because the header's context (10) is higher than the main container's context (1), the header paints over the entire main container. The modal's `z-index: 9999` only moves it to the top *within* the main container, but it cannot break out to overlap the header. To fix this, the modal must be rendered via a React Portal (or moved in the DOM) to append it directly to `document.body`, making it a peer to the root context.",
        [
            "Defines Stacking Contexts as isolated rendering layers that trap the z-index of child elements",
            "Identifies that z-index is evaluated locally relative to peer stacking contexts, not globally",
            "Suggests using DOM manipulation (e.g., React Portals) to move the modal to the root of the document"
        ],
        [
            "Claims z-index values max out at 100 in modern browsers",
            "Suggests using !important on the z-index to force it to work globally"
        ]
    ),
    (
        "B71_6",
        "Frontend Developer",
        "tradeoff",
        "medium",
        "tradeoff",
        ["React Framework", "State Management"],
        "React / Context API vs Redux",
        "Prop Drilling vs Context API Render Churn vs Redux",
        "A team is suffering from severe prop drilling (passing props down 7 layers). A junior developer proposes wrapping the entire application in a single React `Context.Provider` containing a massive `userAndAppData` object. What is the severe performance consequence of storing monolithic state in a single React Context, and how do libraries like Redux or Zustand solve this using selectors?",
        "1) The Context API Render Churn: React's Context API is a dependency injection mechanism, not a fine-grained state manager. If a single monolithic Context holds `userAndAppData`, ANY update to ANY property within that object (e.g., changing `user.avatar`) creates a new object reference. This forces React to re-render EVERY single component subscribed to that Context using `useContext`, even if they only care about `appData.theme`. This causes massive, application-wide render churn and freezes the UI. 2) Mitigation within Context: You must split monolithic contexts into many granular contexts (e.g., `ThemeContext`, `UserContext`) and strictly memoize context values. 3) The Redux/Zustand Solution: External state managers bypass React's context render cascade. They maintain state outside the React tree in a store. Components subscribe to specific slices of the store using selectors (e.g., `useSelector(state => state.appData.theme)`). The library acts as an event emitter; when the store updates, the library explicitly checks for equality on the selected slice. If the specific slice hasn't changed, the component is NOT forced to re-render, guaranteeing $O(1)$ targeted updates instead of tree-wide reconciliation.",
        [
            "Identifies that monolithic Context forces a re-render of all subscribed consumers whenever any property changes",
            "Explains that Context lacks fine-grained subscription mechanics",
            "Contrasts with Redux/Zustand selectors which use equality checks to trigger renders only when specific state slices mutate"
        ],
        [
            "Claims React Context is deprecated and removed in React 18",
            "Suggests using jQuery to manually update the DOM instead of state managers"
        ]
    ),
    (
        "B71_7",
        "Frontend Developer",
        "scenario",
        "hard",
        "scenario",
        ["Web APIs", "Architecture"],
        "Service Workers / PWA",
        "Service Worker Cache Expiration and the Zombie Client Problem",
        "You deploy a Progressive Web App (PWA) with a Service Worker that caches `index.html` and `app.js` using a Cache-First strategy for offline support. You deploy v2.0 of the application, but users complain they are stuck seeing the old v1.0 UI indefinitely. Refreshing the browser does not load the new code. Walk through the Service Worker lifecycle (Install, Wait, Activate) and explain how to architect the application to safely prompt the user and instantly swap to the new Service Worker.",
        "1) The Zombie Client Cause: When the browser detects a byte-difference in the Service Worker file, it downloads it and triggers the `install` event in the background. However, the new worker enters the `waiting` phase. Because a Service Worker controls the entire scope (the origin), the browser will NOT `activate` the new worker as long as there are ANY open tabs/clients using the old worker. A normal refresh keeps the client alive long enough to prevent activation. 2) Architectural Solution (SkipWaiting): The new Service Worker must listen for a specific message to call `self.skipWaiting()`, which forcefully terminates the old worker and activates the new one. 3) The UI Flow: A) The application's main thread registers the worker and listens for the `updatefound` event. B) When the new worker finishes installing, its state changes to `installed`. C) The main thread displays a UI toast: 'New version available. Click to Update'. D) Upon clicking, the main thread sends a `postMessage({ type: 'SKIP_WAITING' })` to the waiting worker. E) The worker calls `self.skipWaiting()`. F) The main thread listens for the `controllerchange` event. G) When `controllerchange` fires (indicating the new worker has taken control), the main thread executes `window.location.reload()` to fetch the fresh `index.html` and assets from the new cache.",
        [
            "Explains that new Service Workers enter a waiting phase until all clients using the old worker are completely closed",
            "Describes the need to send a postMessage to trigger self.skipWaiting() to force activation",
            "Details the main thread listening for the controllerchange event to execute a forced page reload"
        ],
        [
            "Claims Service Workers automatically self-destruct after 24 hours",
            "Suggests telling the user to clear their browser cookies"
        ]
    ),
    (
        "B71_8",
        "Frontend Developer",
        "explain",
        "medium",
        "explain",
        ["Build Tools", "Micro-Frontends"],
        "Webpack / Module Federation",
        "Webpack 5 Module Federation and Dependency Sharing",
        "A large enterprise application uses Webpack 5 Module Federation to load a 'Checkout' micro-frontend from a different domain at runtime. Both the Host App and the Checkout App use React v18. How does Module Federation prevent the user's browser from downloading the 130KB React library twice, and what happens if the Host uses React v17 while Checkout requires React v18?",
        "1) The Mechanism of Module Federation: Webpack 5 Module Federation allows independent builds to share modules dynamically at runtime. In the `ModuleFederationPlugin` configuration, both apps declare `react` and `react-dom` in their `shared` dependencies object. 2) Singleton Dependency Sharing: When the Host app loads, it registers its version of React into a global shared scope dictionary. When the Checkout remote loads dynamically, Webpack intercepts its require call for React. It checks the global shared scope. Finding React already initialized by the Host, the Checkout app bypasses its own bundled React and links directly to the Host's React instance in memory, saving 130KB of network transfer and preventing React instance conflicts. 3) Version Conflicts: If configured with `singleton: true` and `requiredVersion: '^18.0.0'` in the remote, and the Host provides v17, the remote's Webpack runtime detects the semantic version mismatch. Depending on configuration, it will either throw a runtime error (strict mode) or fallback to downloading and instantiating its own separate v18 React bundle, which breaks the singleton constraint (often causing 'Hooks can only be called inside the body of a function component' errors due to multiple React instances).",
        [
            "Explains the global shared scope initialized by Webpack to act as a runtime registry for dependencies",
            "Details how remote apps intercept requires and reuse the host's dependency instance if semantic versions match",
            "Identifies the singleton conflict risk when strict versions mismatch, potentially causing multiple React instances to load"
        ],
        [
            "Claims Module Federation uses WebSockets to stream React from the host to the remote",
            "Suggests that Webpack deletes the code from the remote server automatically"
        ]
    ),
    (
        "B71_9",
        "Frontend Developer",
        "diagnose",
        "hard",
        "debugging",
        ["Browser Architecture", "Performance Tuning"],
        "Memory Leaks / Detached DOM",
        "Diagnosing Detached DOM Elements in Single Page Applications",
        "A React dashboard crashes with an 'Out of Memory' error after navigating between the 'Data Grid' and 'Profile' tabs 50 times. Using Chrome DevTools Memory Profiler, you take a Heap Snapshot and observe 15,000 'Detached HTMLDivElement' objects. What is a 'Detached DOM Element', what coding patterns in JS/React cause them, and how does the Garbage Collector treat them?",
        "1) Detached DOM Elements: A detached DOM element is an HTML node that has been removed from the visible document tree (the DOM), but cannot be garbage collected because a JavaScript variable, closure, or event listener still holds a strong memory reference to it. 2) Common Causes in SPAs: A) Global Event Listeners: A component attaches `window.addEventListener('scroll', handleScroll)` and fails to call `removeEventListener` on unmount. The `handleScroll` closure retains a reference to the component's DOM nodes. B) Third-Party Libraries: Initializing a non-React charting library (e.g., D3 or Highcharts) on a `ref` but failing to call the library's `.destroy()` method when the React component unmounts. C) Global State: Storing actual DOM nodes or React elements inside a global Redux store or array. 3) The GC Mechanism: The V8 Garbage Collector traverses object graphs. If the root `window` object points to the event listener, which points to the closure, which points to the `HTMLDivElement`, the GC considers it 'reachable' and retains it in heap memory indefinitely. 4) The Fix: Implement proper cleanup functions in `useEffect` returns (removing listeners, clearing intervals, destroying library instances) to sever the reference graph, allowing the GC to reclaim the memory.",
        [
            "Defines detached DOM elements as nodes removed from the document tree but kept alive by JS references",
            "Identifies global event listeners, uncleared timeouts, and un-destroyed third-party libraries as root causes",
            "Explains that V8's GC cannot collect the memory because the object graph traces back to a root (e.g., window)"
        ],
        [
            "Claims detached elements are elements positioned absolutely off the screen using CSS left: -9999px",
            "Suggests calling document.deleteElement() to fix it"
        ]
    ),
    (
        "B71_10",
        "Frontend Developer",
        "explain",
        "medium",
        "explain",
        ["Network Protocols", "Web APIs"],
        "WebSockets vs Server-Sent Events",
        "Architectural Tradeoffs: WebSockets vs Server-Sent Events (SSE)",
        "A live stock ticker dashboard needs to display real-time price updates pushed from the backend. The engineering team is debating between implementing WebSockets or Server-Sent Events (SSE). Compare the architectural differences between WebSockets and SSE regarding protocol transport, multiplexing over HTTP/2, and bidirectional communication limitations.",
        "1) Protocol Transport: WebSockets begin with an HTTP Upgrade request but then hijack the TCP connection to establish a custom, persistent, binary-framed protocol (ws:// or wss://). SSE remains standard HTTP (Layer 7), utilizing a long-lived HTTP response with `Content-Type: text/event-stream` and chunked transfer encoding to stream text updates. 2) Bidirectional vs Unidirectional: WebSockets provide full-duplex, bidirectional communication; the client and server can push messages to each other concurrently. SSE is strictly unidirectional (Server to Client). If the client needs to send data (e.g., changing the stock symbol), it must issue a standard POST/fetch request over a separate HTTP connection. 3) HTTP/2 Multiplexing: Under HTTP/1.1, browsers strictly limit connections to the same domain (max 6). Opening 6 SSE tabs would exhaust the pool, freezing the browser. However, under HTTP/2, SSE requests are automatically multiplexed over a single TCP connection, eliminating the limit and supporting native HTTP compression and proxy caching. WebSockets do not natively benefit from HTTP/2 multiplexing (though RFC 8441 exists, support is patchy), often requiring dedicated load balancer configurations to maintain persistent raw TCP connections.",
        [
            "Distinguishes WebSockets as a custom binary protocol post-upgrade vs SSE as standard chunked HTTP text streams",
            "Identifies WebSockets as full-duplex bidirectional vs SSE as unidirectional server-push only",
            "Highlights that SSE benefits natively from HTTP/2 multiplexing, whereas WebSockets require dedicated TCP connection management"
        ],
        [
            "Claims SSE requires the user to manually click a refresh button every second",
            "Suggests WebSockets run over UDP to bypass firewall restrictions"
        ]
    ),
    (
        "B71_11",
        "Frontend Developer",
        "concept",
        "hard",
        "concept",
        ["Web Security", "Architecture"],
        "Content Security Policy (CSP)",
        "Strict CSP Nonce Implementation for Inline Scripts",
        "A web application uses a Content Security Policy (CSP). To prevent Cross-Site Scripting (XSS), the security team mandates removing `'unsafe-inline'` from the `script-src` directive. However, the application relies on an inline Webpack runtime script in the `index.html` to bootstrap the app. How do you implement a Cryptographic Nonce within the CSP and the HTML to allow exactly this specific inline script to execute while blocking all injected malicious scripts?",
        "1) The Mechanism of Nonces: A nonce (number used once) is a cryptographically strong, randomly generated Base64 string generated dynamically by the backend server on *every single page request* (e.g., `nonce-rAnd0m123`). 2) The HTTP Header: The server attaches the nonce to the CSP HTTP Response Header: `Content-Security-Policy: script-src 'self' 'nonce-rAnd0m123';`. 3) The HTML Markup: The server injects the exact same nonce into the valid inline script tag attributes: `<script nonce=\"rAnd0m123\">webpackBootstrap();</script>`. 4) How it Blocks XSS: When the browser parses the HTML, it checks every inline script. If the script tag possesses a `nonce` attribute that perfectly matches the value in the CSP header, the browser executes it. If an attacker injects `<script>stealTokens()</script>` via a stored XSS vulnerability, the attacker's script will lack the correct dynamic nonce (since they cannot predict it ahead of time). The browser's security engine will refuse to execute the malicious script and throw a CSP violation error.",
        [
            "Defines a nonce as a dynamic, cryptographically secure random string generated per-request",
            "Explains injecting the nonce into both the CSP HTTP header and the valid script tag attribute",
            "Details how injected attacker scripts fail to execute because they lack the unpredictable nonce value"
        ],
        [
            "Claims a nonce is a static password stored in localStorage",
            "Suggests hashing the entire HTML file with MD5"
        ]
    ),
    (
        "B71_12",
        "Frontend Developer",
        "scenario",
        "medium",
        "scenario",
        ["Accessibility (a11y)", "UI Engineering"],
        "WAI-ARIA / Screen Readers",
        "ARIA Live Regions and Dynamic DOM Updates",
        "A Single Page Application implements an AJAX-based shopping cart. When a user clicks 'Add to Cart', the cart icon number instantly updates from 0 to 1 without a page reload. Sighted users see this immediately, but visually impaired users using a Screen Reader receive absolutely no audio feedback that the action succeeded. How do you architect the DOM using WAI-ARIA attributes to ensure screen readers announce dynamic content changes?",
        "1) The Accessibility Gap: Screen readers generally read the DOM as it exists upon initial focus or page load. They do not automatically watch for silent DOM mutations (like text changing from '0' to '1') unless explicitly instructed, leaving visually impaired users unaware of asynchronous application state changes. 2) The ARIA Solution: You must use ARIA Live Regions. Apply the `aria-live` attribute to the container holding the cart count: `<div aria-live=\"polite\" aria-atomic=\"true\">Cart: 1 item</div>`. 3) How it works: A) `aria-live=\"polite\"` instructs the screen reader's accessibility API to monitor the DOM node for changes. When the text mutates, the screen reader will queue the update and announce it aloud at the next graceful pause in speech (avoiding interrupting the user). B) `aria-live=\"assertive\"` would interrupt the user immediately (used for critical errors or timeouts). C) `aria-atomic=\"true\"` ensures that the screen reader reads the *entire* contents of the live region (e.g., 'Cart: 1 item') rather than just reading the changed node ('1'), providing necessary context.",
        [
            "Identifies that screen readers ignore silent DOM mutations without explicit ARIA instructions",
            "Utilizes the aria-live attribute (polite or assertive) to trigger screen reader announcements on DOM change",
            "Explains the difference between polite (queued) and assertive (interrupting) announcements"
        ],
        [
            "Suggests using the HTML5 <audio> tag to play a ding sound effect",
            "Claims JavaScript should call window.speechSynthesis.speak() to talk to the user directly"
        ]
    ),
    (
        "B71_13",
        "Frontend Developer",
        "explain",
        "hard",
        "explain",
        ["JavaScript Internals", "Async Concurrency"],
        "Event Loop / Microtasks",
        "Microtask vs Macrotask Execution Order in the Event Loop",
        "A developer runs the following synchronous block of JavaScript:\n`console.log('1'); setTimeout(() => console.log('2'), 0); Promise.resolve().then(() => console.log('3')); console.log('4');`\nExplain the internal architecture of the V8 Event Loop (Call Stack, Microtask Queue, and Macrotask/Callback Queue) that dictates the final output order of 1, 4, 3, 2.",
        "1) Synchronous Execution (Call Stack): The engine executes the main script top-to-bottom. `console.log('1')` executes immediately. `setTimeout` registers a Web API timer and pushes its callback into the Macrotask Queue. `Promise.resolve().then` pushes its callback into the Microtask Queue. `console.log('4')` executes immediately. Output so far: 1, 4. 2) The Call Stack Empties: The synchronous execution completes, and the main Call Stack becomes empty. 3) The Microtask Queue: Before the Event Loop yields to the browser for rendering or checks the Macrotask queue, it strictly evaluates the Microtask Queue. It drains the *entire* Microtask queue (including any new microtasks queued by executing microtasks). The Promise callback executes, logging '3'. 4) The Macrotask Queue: Once the Microtask queue is empty, the Event Loop pulls *one* task from the Macrotask Queue. It dequeues the `setTimeout` callback, pushes it to the Call Stack, and executes it, logging '2'. Conclusion: Synchronous code -> Microtasks (Promises, MutationObserver) -> Macrotasks (setTimeout, setInterval, I/O).",
        [
            "Explains the Call Stack executing synchronous code first",
            "Defines the Microtask queue (Promises) being drained completely before any rendering or macrotasks",
            "Defines the Macrotask queue (setTimeout) executing one task per loop iteration after microtasks are cleared"
        ],
        [
            "Claims setTimeout(..., 0) executes instantly, beating Promises",
            "Suggests the order is random depending on CPU speed"
        ]
    ),
    (
        "B71_14",
        "Frontend Developer",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Web APIs", "UI Engineering"],
        "Intersection Observer vs Scroll Events",
        "Infinite Scrolling: Intersection Observer vs Scroll Event Listeners",
        "To implement infinite scrolling on a feed, a junior developer attaches a `window.addEventListener('scroll', checkOffset)` that fires hundreds of times per second to calculate `element.getBoundingClientRect()`. A senior developer rewrites this using the `IntersectionObserver` API. Why does the scroll event approach cause extreme layout thrashing and frame drops, and how does the Intersection Observer architecture solve it?",
        "1) The Scroll Event Thrashing: Scroll events fire synchronously on the main thread during scrolling. Calling `getBoundingClientRect()` forces the browser to calculate the exact pixel geometry of the DOM. Because the browser wants to provide accurate measurements, it must flush all pending CSS styling and layout changes immediately (Synchronous Layout / Layout Thrashing). Doing this 60 times a second maxes out CPU, causing jank and dropping frames below 60FPS. 2) The Intersection Observer Solution: The `IntersectionObserver` API offloads intersection calculations off the main thread. It asks the browser's internal rendering engine to asynchronously monitor when a target element intersects a root viewport. 3) Asynchronous Callbacks: Instead of polling geometry on every pixel scrolled, the browser only fires the JS callback asynchronously *at the exact moment* the element crosses the defined threshold (e.g., 100px before the bottom). This completely eliminates synchronous layout calculations from the main thread, resulting in silky smooth scrolling and near-zero CPU overhead.",
        [
            "Identifies that scroll events fire at high frequency on the main JS thread",
            "Explains that getBoundingClientRect() triggers synchronous layout recalculations (thrashing)",
            "Details how IntersectionObserver delegates intersection checks to the browser internals asynchronously, firing only on threshold crossings"
        ],
        [
            "Claims IntersectionObserver is just a polyfill for scroll events",
            "Suggests using CSS animations to implement infinite scrolling"
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
    print(f"Batch: 71_p1")
    print(f"Target role: {ROLE}")
    print(f"Cumulative total: {len(final_existing)}")
    print("Role counts:")
    for role, count in sorted(role_counts.items()):
        print(f"  {role}: {count}")

if __name__ == "__main__":
    run_batch()
