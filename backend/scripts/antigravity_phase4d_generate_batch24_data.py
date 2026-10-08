"""Batch 24 question content (Frontend Developer). Targeted Gap Generation."""

ROLE = "Frontend Developer"

BUCKET_KEYS = {
    "FE_TESTING": ("Frontend Testing", "E2E & Isolation", "Testing", ["Software Engineer", "Quality Assurance"]),
    "FE_BROWSER_API": ("Browser APIs", "Workers & Observers", "Web APIs", ["Full Stack Developer", "Software Engineer"]),
    "FE_CSS_ARCH": ("CSS Architecture", "Specificity & Cascade", "CSS", ["UX Engineer"]),
}

Q = [
# ---------------- FE_TESTING ----------------
("FE_TESTING", "scenario", "medium", "scenario", ["Flakiness"],
 "An end-to-end (E2E) test using Cypress or Playwright passes consistently on your local machine but randomly fails about 10% of the time in the CI environment. What is the most common cause of this flakiness, and how do you resolve it?",
 "The most common cause is asynchronous timing issues—CI environments are often slower, meaning network requests, rendering, or animations take longer. If tests rely on fixed waits (e.g., `sleep(1000)`), they will flake. You resolve this by replacing manual sleeps with declarative assertions that natively wait and retry, such as asserting on element visibility, waiting for specific mocked network intercepts to complete, or disabling CSS animations in the testing environment.",
 ["Asynchronous timing issues caused by slower CI environments", "Replace fixed waits (sleep) with declarative assertions/waits", "Wait on specific network intercepts or element visibility states"],
 ["The CI server is located in a different time zone"]),

("FE_TESTING", "tradeoff", "hard", "tradeoff", ["Mocking"],
 "When writing frontend unit tests, what are the tradeoffs of heavily mocking the DOM and browser APIs (e.g., using jsdom in Jest) versus running tests in a real browser engine (e.g., Playwright/Vitest browser mode)?",
 "`jsdom` is incredibly fast, runs entirely in Node.js, and requires minimal setup, but it lacks an actual layout engine. It misses CSS rendering quirks, dimensional calculations, and native API behaviors. Real browser engines provide exact execution fidelity, catching layout and real-world API bugs, but they introduce massive CPU/Memory overhead, slower execution times, and complex CI dependencies (like installing browser binaries).",
 ["jsdom: Fast, runs in Node, but lacks a layout engine (no dimensions/CSS parsing)", "Real browser: Exact execution fidelity, catches layout and native API bugs", "Real browser: Massive overhead, slower execution, requires CI browser binaries"],
 ["jsdom is illegal to use in enterprise environments"]),

("FE_TESTING", "debug", "medium", "debugging", ["Selectors"],
 "You write a component test that asserts a specific `<div>` has the class `btn-primary`. The test passes. Six months later, a designer updates the class name to `btn-main`. The test fails, even though the visual appearance and functionality are identical. Why is this a bad test, and how should it be rewritten?",
 "This is a brittle test because it asserts heavily on internal implementation details (CSS classes) rather than user-facing behavior. The user does not care about the class name. The test should be rewritten using behavior-driven selectors, such as querying the button by its accessible role (`getByRole('button', { name: 'Submit' })`) or using a dedicated testing attribute (`data-testid`).",
 ["The test is brittle because it asserts on implementation details (CSS classes)", "Tests should assert on user-facing behavior, not code structure", "Rewrite using accessible roles (`getByRole`) or dedicated `data-testid` attributes"],
 ["The designer should be fired for changing the class name"]),

("FE_TESTING", "explain", "medium", "concept", ["Visual Regression"],
 "Explain the difference between Visual Regression Testing (e.g., Percy, Chromatic) and functional DOM snapshot testing (e.g., Jest snapshots).",
 "DOM snapshot testing serializes the HTML structure into a text file and diffs the text on future runs. It is brittle to harmless DOM refactors and completely ignores CSS changes. Visual Regression Testing takes actual pixel-perfect screenshots of the rendered page in a headless browser and compares the images to a baseline, catching subtle CSS bugs and layout shifts without caring about the underlying DOM structure.",
 ["DOM snapshots diff serialized HTML text (brittle to refactors, ignores CSS)", "Visual regression takes actual pixel screenshots of the rendered page", "Visual regression catches CSS bugs and layout shifts regardless of DOM structure"],
 ["Visual regression requires a VR headset"]),

("FE_TESTING", "scenario", "hard", "scenario", ["Layout APIs"],
 "You are testing a complex data grid component that relies on `window.matchMedia` and `ResizeObserver` to calculate its layout. Your Jest/jsdom tests instantly crash when rendering the component. Why does this happen, and how do you test this component?",
 "It crashes because `jsdom` is a pure JavaScript simulation of the DOM and does not implement a layout engine. Therefore, layout-dependent APIs like `ResizeObserver` and `matchMedia` simply do not exist in the environment. To test it, you must either heavily mock these APIs globally in the Jest setup file, or move the test to a real browser runner that supports native layout APIs.",
 ["jsdom lacks a layout engine and does not implement `ResizeObserver` or `matchMedia`", "You must mock the APIs globally in the test setup", "Alternatively, migrate the test to a real browser engine"],
 ["Jest is strictly for backend testing"]),

("FE_TESTING", "tradeoff", "medium", "tradeoff", ["Network Mocking"],
 "What are the tradeoffs between testing a frontend application against a live staging backend versus intercepting (mocking) all network requests at the browser level?",
 "Testing against a live backend provides true end-to-end confidence and catches API contract drifts, but the tests are extremely slow, require complex database seeding, and will fail randomly if the staging server is down. Mocking requests at the browser level (e.g., MSW) makes tests blazing fast, perfectly isolated, and highly deterministic, but you risk the mock diverging from the real API, leading to false positives.",
 ["Live backend: True E2E confidence, but slow, flaky, and requires DB seeding", "Mocking: Fast, deterministic, isolated", "Mocking tradeoff: Risk of the mock diverging from the real API contract"],
 ["Mocking costs money per API call"]),

("FE_TESTING", "implement", "easy", "implementation", ["Isolation"],
 "How do you mock the browser's `localStorage` in a frontend test suite to ensure tests remain completely isolated and do not bleed state into each other?",
 "You override the global `window.localStorage` object with a custom JavaScript mock (e.g., a simple class or object that implements `getItem`, `setItem`, `removeItem`, and `clear` using an internal dictionary). Crucially, you must call the mock's `clear()` method inside a global `beforeEach` block to ensure the dictionary is wiped clean before every single test.",
 ["Override `window.localStorage` with a custom mock object/class", "Implement standard methods (`getItem`, `setItem`, `clear`) using an internal dictionary", "Call `clear()` in a `beforeEach` block to prevent state bleed"],
 ["Store the test data in a secure blockchain"]),

("FE_TESTING", "debug", "hard", "debugging", ["Async DOM"],
 "Your frontend integration test clicks a 'Submit' button, which triggers an async `fetch` request. The test immediately asserts that a 'Success' message appears, but the test fails because the message hasn't rendered yet. If you cannot use a testing library's built-in wait functions, how do you natively wait for the async DOM update?",
 "You can use a native `MutationObserver`. You wrap the observer in a JavaScript Promise, instructing it to watch the parent DOM node for child insertions. Once the observer detects the 'Success' element being added to the DOM, it resolves the Promise. The test can simply `await` this Promise before executing the final assertion.",
 ["Use a `MutationObserver` wrapped in a Promise", "Observe the DOM for the specific node insertion or text change", "Resolve the promise when the mutation is detected, allowing the test to await it"],
 ["You must use a `while(true)` loop to check the DOM"]),

("FE_TESTING", "scenario", "medium", "scenario", ["Accessibility"],
 "You are writing accessibility (a11y) tests. You run an automated tool like `axe-core`, and it reports zero violations. However, a user relying on a screen reader reports they cannot navigate a custom dropdown menu. Why did the automated test pass, and how must you test this?",
 "Automated a11y tools are static analyzers; they only catch structural errors like missing `aria-labels`, invalid ARIA roles, or poor color contrast. They are completely blind to dynamic interactive state, keyboard focus traps, and complex screen reader announcements. You must test dynamic interactive widgets manually using a keyboard and a screen reader, or by scripting E2E tests that explicitly simulate 'Tab' and 'Enter' keystrokes.",
 ["Automated tools only catch static structural errors (contrast, missing tags)", "They cannot test dynamic interactions, focus traps, or complex announcements", "Must use manual keyboard testing or E2E scripts that simulate keyboard events"],
 ["Automated tools hate custom dropdowns"]),

("FE_TESTING", "explain", "easy", "concept", ["Test Strategy"],
 "In the context of frontend testing, what is the concept of a 'Test Pyramid', and how does it dictate where you spend your testing effort?",
 "The Test Pyramid is a strategy for balancing testing layers. The wide base consists of Unit tests: they are fast, isolated, and cheap to run, so you should write hundreds of them. The middle consists of Integration/Component tests. The narrow top consists of End-to-End (E2E) tests: they provide massive confidence but are extremely slow, expensive, and flaky, so they should be reserved only for critical user flows.",
 ["Base: Unit tests (fast, cheap, numerous)", "Middle: Integration/Component tests", "Top: E2E tests (slow, expensive, flaky, reserved for critical flows)"],
 ["It is a pyramid scheme to sell testing software"]),

("FE_TESTING", "implement", "medium", "implementation", ["Timers"],
 "You need to test a React component that sets a `setTimeout` for 5 seconds before showing a notification. How do you write a unit test for this without physically making the test suite wait for 5 seconds?",
 "You use a fake timer API provided by your test runner (e.g., `jest.useFakeTimers()`). This overrides the browser's native `setTimeout` clock. In the test, you trigger the action, then synchronously advance the fake clock using `jest.advanceTimersByTime(5000)`. The component will instantly process the timeout, allowing you to assert the notification immediately.",
 ["Use fake timers (e.g., `jest.useFakeTimers()`) to override the native clock", "Synchronously advance time using `advanceTimersByTime(5000)`", "Prevents the test suite from actually sleeping, keeping tests blazing fast"],
 ["Edit the source code to 1ms just for the test"]),

("FE_TESTING", "tradeoff", "medium", "tradeoff", ["Selectors"],
 "What are the tradeoffs of using data attributes (like `data-testid=\"submit-btn\"`) explicitly for testing versus querying elements by their text content (e.g., `getByText('Submit')`)?",
 "Data attributes provide highly resilient selectors that are completely immune to copywriting changes, CSS updates, and i18n translations, but they decouple the test from the actual user experience. Querying by text is preferred by testing philosophies (like React Testing Library) because it exactly mimics how a human finds a button, ensuring accessibility, but it makes tests highly brittle to minor text changes.",
 ["`data-testid`: Extremely resilient to changes, but decoupled from user behavior", "Text queries: Mimics human interaction and guarantees accessibility", "Text queries: Highly brittle to copy changes and i18n translations"],
 ["Data attributes are parsed faster by the CPU"]),

("FE_TESTING", "debug", "hard", "debugging", ["State Bleed"],
 "A suite of frontend component tests runs perfectly in isolation, but when running the entire suite together in CI, random tests fail due to Redux store state pollution. Why does this happen, and how do you fix it?",
 "This happens because the tests are importing a single, globally instantiated Redux store module. Since test runners often execute tests sequentially in the same memory space, the mutated state from Test A bleeds into Test B. To fix this, you must export a factory function that creates a fresh Redux store, and wrap every test component in a `<Provider>` with a newly instantiated store generated inside a `beforeEach` block.",
 ["Global state instances retain mutations across sequential tests in the same memory space", "Export a factory function to create a fresh store instance instead of a singleton", "Instantiate a new store in `beforeEach` for complete test isolation"],
 ["Redux is fundamentally incompatible with CI servers"]),

("FE_TESTING", "scenario", "medium", "scenario", ["E2E Performance"],
 "An E2E test suite takes 45 minutes to run sequentially on a single CI machine. What are two architectural strategies to drastically reduce this execution time?",
 "1. Parallelization/Sharding: Split the test suite into smaller chunks and run them concurrently across multiple CI worker nodes. 2. API Seeding/Bypassing the UI: Instead of using the browser UI to slowly log in and create prerequisites for every test, use direct HTTP requests to the backend API in the test setup hook to instantly stage the required state and inject an auth token.",
 ["Parallelization/Sharding across multiple CI nodes", "API Seeding: Bypass the UI and use direct backend requests to stage state", "Inject auth tokens directly instead of UI login sequences"],
 ["Run the tests on a quantum computer"]),

("FE_TESTING", "explain", "medium", "concept", ["Mutation Testing"],
 "What is 'Mutation Testing' in a frontend context, and what specific problem does it solve that code coverage cannot?",
 "Mutation testing is a technique where a tool intentionally injects small bugs (mutants) into your source code (e.g., changing `+` to `-`, or removing a function call) and runs your test suite. If the tests still pass, the mutant 'survived', indicating a bad test. Code coverage only proves that a line of code was executed by a test; mutation testing proves that the test actually asserts the correct behavior.",
 ["Injects intentional bugs (mutants) into source code to verify tests fail", "Code coverage only proves a line was executed, not that behavior was asserted", "Mutation testing guarantees test quality and assertion accuracy"],
 ["It mutates HTML tags into XML tags"]),

# ---------------- FE_BROWSER_API ----------------
("FE_BROWSER_API", "scenario", "medium", "scenario", ["Fetch API"],
 "You have a search input that sends an API request on every keystroke. You implement debouncing, but if the user types slowly, multiple requests are still fired. When the results return out of order, the UI shows stale data. How do you natively abort the previous requests using modern Browser APIs?",
 "You attach an `AbortController` to the `fetch` request. You instantiate `const controller = new AbortController()`, pass `{ signal: controller.signal }` to the fetch options, and store the controller reference. The exact moment the user types a new character and a new request is triggered, you call `.abort()` on the stored controller to instantly cancel the in-flight network request.",
 ["Use the `AbortController` API", "Pass `controller.signal` to the `fetch` options", "Call `controller.abort()` to cancel the previous in-flight request before sending a new one"],
 ["Unplug the user's router programmatically"]),

("FE_BROWSER_API", "implement", "hard", "implementation", ["Web Workers"],
 "You are building a complex dashboard that needs to parse massive 50MB CSV files on the client side. Doing this on the main thread freezes the browser tab. How do you re-architect this using Browser APIs?",
 "You must move the heavy parsing logic off the main thread into a Web Worker. You create a new `Worker('parser.js')`. From the main thread, you send the raw CSV string or `File` object using `worker.postMessage()`. The Web Worker parses the data asynchronously in a separate OS thread without blocking the UI rendering, and then posts the parsed JSON array back to the main thread.",
 ["Move heavy computation to a Web Worker", "Web Workers run in a separate background thread, unblocking the UI rendering", "Communicate data back and forth using `postMessage()`"],
 ["Web Workers are only used for cryptocurrency mining"]),

("FE_BROWSER_API", "tradeoff", "medium", "tradeoff", ["Storage"],
 "What are the tradeoffs of using `localStorage` versus `IndexedDB` for persisting client-side application state?",
 "`localStorage` is extremely simple to use (synchronous key-value strings) but is strictly limited to around 5MB, and crucially, its synchronous nature blocks the main UI thread during massive read/writes. `IndexedDB` supports massive storage quotas (gigabytes) and complex asynchronous queries without blocking the UI, but it has a heavily verbose, complex, and difficult-to-use API.",
 ["`localStorage`: Simple, but synchronous (blocks main thread) and limited to 5MB", "`IndexedDB`: Asynchronous (non-blocking) and supports massive data limits", "`IndexedDB` tradeoff: Extremely complex, verbose, and difficult to query"],
 ["`localStorage` is sent to the FBI, `IndexedDB` is private"]),

("FE_BROWSER_API", "explain", "medium", "concept", ["Observers"],
 "Explain the purpose of the `IntersectionObserver` API. What common frontend performance problem does it solve natively?",
 "The `IntersectionObserver` API provides a way to asynchronously observe changes in the intersection of a target DOM element with an ancestor element or the top-level viewport. It natively solves the massive performance problem of binding expensive, synchronous `scroll` event listeners to the window to calculate element visibility for features like lazy loading images or infinite scrolling.",
 ["Asynchronously observes when elements enter or exit the viewport/ancestor", "Replaces expensive, janky synchronous `scroll` event listeners", "Used for high-performance lazy loading and infinite scrolling"],
 ["It prevents two cars from crashing at a traffic light"]),

("FE_BROWSER_API", "scenario", "hard", "scenario", ["History API"],
 "A Single Page Application (SPA) relies on the `History` API (`pushState`) for client-side routing. When the user navigates through 5 pages and then presses the browser's native 'Back' button, the URL changes but the screen does not update. What event listener is missing?",
 "The SPA is missing an event listener for the `popstate` event. While `pushState` changes the URL without a reload, clicking the native Back/Forward buttons does not automatically re-render the JS application. The application must listen to `window.addEventListener('popstate', callback)` to detect native history traversal and manually trigger a re-render of the correct view.",
 ["Missing the `popstate` event listener on the `window` object", "Native Back/Forward buttons trigger `popstate`, they do not trigger a reload in an SPA", "The router must listen to this event to manually update the DOM"],
 ["The browser ran out of history ink"]),

("FE_BROWSER_API", "debug", "medium", "debugging", ["MutationObserver"],
 "You implement a `MutationObserver` to watch a parent `<div>` for child node additions. However, your observer callback fires, modifies the DOM, and immediately triggers an infinite loop, crashing the browser. How do you fix this?",
 "The observer is recursively reacting to the DOM mutations it is causing itself. To fix this, you must temporarily detach the observer by calling `observer.disconnect()` at the very beginning of the callback, perform your DOM modifications, and then immediately reattach it by calling `observer.observe()` at the end of the callback.",
 ["The observer is reacting to its own DOM mutations (infinite loop)", "Call `observer.disconnect()` before making changes inside the callback", "Call `observer.observe()` again after changes are complete"],
 ["Add a `break` statement to the DOM"]),

("FE_BROWSER_API", "tradeoff", "hard", "tradeoff", ["Networking"],
 "When implementing real-time bidirectional communication in a browser, what are the tradeoffs between using WebSockets versus Server-Sent Events (SSE)?",
 "WebSockets are fully bidirectional, offer extremely low latency, and support binary data, but they require a complex stateful server architecture and often struggle with enterprise firewalls/proxies dropping idle connections. SSE operates over standard HTTP, is incredibly robust for one-way server-to-client streaming, natively supports automatic reconnection, and bypasses firewalls easily, but it cannot send client-to-server data natively.",
 ["WebSockets: Fully bidirectional, low latency, supports binary, but complex scaling/firewall issues", "SSE: Standard HTTP, automatic reconnections, firewall friendly", "SSE: Strictly one-way (server to client)"],
 ["WebSockets use TCP, SSE uses UDP"]),

("FE_BROWSER_API", "implement", "medium", "implementation", ["Observers"],
 "You want to detect when an HTML element's dimensions actually change (e.g., due to a CSS flexbox reflow) rather than just waiting for a window resize event. What modern Browser API do you use?",
 "You use the `ResizeObserver` API. Unlike the `window.onresize` event, which only fires when the browser window changes, `ResizeObserver` specifically tracks the bounding-box dimension changes of individual DOM elements, allowing components to react to layout shifts independently of the viewport.",
 ["Use the `ResizeObserver` API", "Tracks bounding-box dimension changes of specific DOM elements", "Fires on reflows/layout shifts, not just viewport window resizes"],
 ["Use a physical ruler on the monitor"]),

("FE_BROWSER_API", "scenario", "medium", "scenario", ["Service Workers"],
 "You register a Service Worker to cache your static assets for offline support. You deploy a critical hotfix to `app.js`. Users complain they are still seeing the broken old version even after refreshing the page multiple times. Why is the browser aggressively clinging to the old Service Worker, and how do you force an update?",
 "By default, a browser will install a new Service Worker in the background, but it will remain in a 'waiting' state and will not activate as long as ANY tabs controlled by the old worker remain open. To force an update, you must programmatically call `self.skipWaiting()` in the new Service Worker code, and trigger a page reload on the client using `clients.claim()`.",
 ["New Service Workers remain in a 'waiting' state if any tabs are still open", "They do not activate on a simple refresh", "Force activation programmatically using `self.skipWaiting()` and `clients.claim()`"],
 ["The cache is protected by military-grade encryption"]),

("FE_BROWSER_API", "explain", "easy", "concept", ["Lifecycle"],
 "What is the `navigator.sendBeacon()` API, and what specific problem does it solve when users close a tab?",
 "The `sendBeacon()` API asynchronously sends a small amount of data over HTTP to a web server without expecting a response. It solves the unreliability of sending analytics or unsaved state during page unload. Standard `fetch` or `XHR` calls are often cancelled by the browser when the tab closes, whereas `sendBeacon` guarantees delivery in the background.",
 ["Asynchronously sends a small payload to the server without expecting a response", "Solves the problem of reliable data delivery during page unload", "Standard network requests are often cancelled when a tab closes"],
 ["It lights a physical fire on top of the server"]),

("FE_BROWSER_API", "debug", "hard", "debugging", ["Animations"],
 "You use `requestAnimationFrame` (rAF) to animate a 3D canvas element. The animation is perfectly smooth on your 60Hz monitor, but on a user's 144Hz monitor, the animation runs more than twice as fast. What critical mathematical mistake did you make?",
 "You did not account for 'Delta Time'. `requestAnimationFrame` fires at the exact refresh rate of the monitor. If you move an object 1 pixel per frame, it moves 60 pixels/sec on your monitor, but 144 pixels/sec on theirs. You must calculate the time elapsed between frames (delta time) and multiply your movement logic by this delta to ensure frame-rate independent animation speed.",
 ["Did not account for Delta Time (time elapsed between frames)", "`rAF` fires at the monitor's native refresh rate (60Hz vs 144Hz)", "Must multiply movement values by delta time to achieve frame-rate independence"],
 ["The 144Hz monitor is inherently defective"]),

("FE_BROWSER_API", "tradeoff", "medium", "tradeoff", ["Security"],
 "What is the tradeoff of storing JWT authentication tokens in `sessionStorage` versus `HttpOnly` Cookies?",
 "`sessionStorage` makes the token easily accessible to JavaScript, exposing the application to severe Cross-Site Scripting (XSS) attacks, but it naturally prevents Cross-Site Request Forgery (CSRF). `HttpOnly` cookies strictly prevent JavaScript from reading the token (mitigating XSS extraction), but because cookies are sent automatically with every request, they require strict `SameSite` flags and CSRF tokens to prevent forged requests.",
 ["`sessionStorage`: Vulnerable to XSS (JS can read it), immune to CSRF", "`HttpOnly` Cookies: Immune to XSS extraction (JS cannot read it)", "`HttpOnly` tradeoff: Highly vulnerable to CSRF unless `SameSite` is strictly configured"],
 ["Cookies make you gain weight"]),

("FE_BROWSER_API", "implement", "easy", "implementation", ["Selection"],
 "How do you programmatically read the text that a user currently has highlighted/selected on a webpage using browser APIs?",
 "You call `window.getSelection()`. To retrieve the actual string of text rather than the Selection object, you call `window.getSelection().toString()`.",
 ["Use `window.getSelection()`", "Call `.toString()` on the returned selection object"],
 ["Screenshot the page and run OCR"]),

("FE_BROWSER_API", "scenario", "medium", "scenario", ["Throttling"],
 "You are building a music player application. When the user switches to another tab, the browser heavily throttles JavaScript `setTimeout` intervals, causing the music progress bar to desync. How do you reliably keep track of time or execute background code when the tab is inactive?",
 "You offload the timing logic to a Web Worker. Browsers aggressively throttle timers (like `setTimeout` and `setInterval`) on the main thread of inactive tabs to save battery. However, Web Workers run in a separate background thread and are generally exempt from this aggressive throttling, allowing you to maintain accurate timing and post messages back to the main thread.",
 ["Browsers aggressively throttle main-thread timers on inactive tabs to save battery", "Offload the timing logic to a Web Worker", "Web Workers run in a background thread and bypass aggressive tab throttling"],
 ["Play the music extremely loud so the browser stays awake"]),

("FE_BROWSER_API", "explain", "hard", "concept", ["Cross-tab Communication"],
 "What is the `BroadcastChannel` API, and when would you use it instead of `postMessage`?",
 "The `BroadcastChannel` API allows simple, publish-subscribe communication between different browsing contexts (tabs, windows, iframes, Web Workers) that share the exact same origin. You use it instead of `window.postMessage` when you want to blindly broadcast state updates (like a user logging out) to all open tabs of your application without needing explicit references to those `window` objects.",
 ["Allows pub-sub communication across tabs/windows/workers on the same origin", "Broadcasts messages blindly to all listeners", "Unlike `postMessage`, it doesn't require maintaining explicit references to target windows"],
 ["It broadcasts radio signals from the motherboard"]),

# ---------------- FE_CSS_ARCH ----------------
("FE_CSS_ARCH", "tradeoff", "medium", "tradeoff", ["Architecture"],
 "When architecting a large-scale application, what are the tradeoffs of using a Utility-First CSS framework (like Tailwind) versus traditional CSS Modules (scoped CSS)?",
 "Utility CSS prevents stylesheets from growing infinitely, eliminates naming fatigue, and enforces strict design tokens, but it drastically clutters the HTML/JSX with massive, unreadable class strings. CSS Modules keep HTML perfectly clean and provide robust local scoping, but require strict naming conventions, generate more CSS overhead, and can lead to duplicated CSS rules across multiple component files.",
 ["Utility CSS: Eliminates naming fatigue and stylesheet bloat, but clutters HTML with massive class strings", "CSS Modules: Keeps HTML clean and provides perfect scoping", "CSS Modules tradeoff: Generates more CSS overhead and requires inventing class names"],
 ["Utility CSS is illegal in Europe"]),

("FE_CSS_ARCH", "scenario", "hard", "scenario", ["Cascade Layers"],
 "You have a legacy CSS file where a deeply nested selector `#header .nav-menu li a.active` sets the text color to red. You want to override this color in a new CSS file using a simple `.active-link` class, but it won't apply. Without using `!important`, how do you architecturally override this using modern CSS?",
 "You use CSS Cascade Layers (`@layer`). You place the legacy CSS in a lower-priority layer (e.g., `@layer legacy;`) and your new CSS in a higher-priority layer (`@layer modern;`). Because layer priority supersedes selector specificity, a simple class selector in the `modern` layer will effortlessly override an ID selector in the `legacy` layer, avoiding specificity wars.",
 ["Use CSS Cascade Layers (`@layer`)", "Place legacy CSS in a lower layer, and new CSS in a higher layer", "Layer priority evaluates before and overrides selector specificity"],
 ["Delete the entire legacy codebase"]),

("FE_CSS_ARCH", "fundamentals", "medium", "concept", ["Specificity"],
 "Explain how CSS Specificity is calculated. Which selector has higher specificity: `.list > li.item` or `ul li:nth-child(2)`?",
 "Specificity is calculated by counting three categories: (IDs, Classes/Attributes/Pseudo-classes, Elements/Pseudo-elements). The selector `.list > li.item` has 0 IDs, 2 classes, and 1 element, resulting in a specificity of (0, 2, 1). The selector `ul li:nth-child(2)` has 0 IDs, 1 pseudo-class, and 2 elements, resulting in (0, 1, 2). The first selector is higher because it has more classes.",
 ["Calculated by counting (IDs, Classes/Attributes/Pseudo-classes, Elements/Pseudo-elements)", "`.list > li.item` is (0, 2, 1)", "`ul li:nth-child(2)` is (0, 1, 2)", "The first is higher due to having two class-level selectors"],
 ["Specificity is random based on the browser"]),

("FE_CSS_ARCH", "debug", "hard", "debugging", ["Positioning"],
 "You set a parent container to `overflow: hidden; border-radius: 10px;`. Inside, you place a child component that uses `position: absolute;` to break out of the flow, but it gets visually clipped by the parent's boundaries. Why did this happen, and how do you allow the absolute element to escape the clipping?",
 "An absolutely positioned element is positioned relative to its nearest positioned ancestor. Because the parent with `overflow: hidden` is also positioned (e.g., `relative`), the browser enforces the clipping boundary on the child. To escape the clipping while retaining layout logic, the absolute child must be physically moved outside the clipping DOM node, typically utilizing a React Portal to render it at the `<body>` level.",
 ["The absolute element is trapped by the positioned ancestor containing `overflow: hidden`", "The browser strictly enforces clipping boundaries on positioned descendants", "Must physically render the child outside the parent DOM node, usually via Portals"],
 ["You must ask the browser nicely to let it out"]),

("FE_CSS_ARCH", "explain", "medium", "concept", ["Performance"],
 "What is the purpose of the CSS `contain` property (CSS Containment), and how does it optimize rendering performance in massive DOM trees?",
 "The `contain` property explicitly tells the browser engine that a specific subtree of the DOM is completely independent of the rest of the page (e.g., it won't affect outside layout). This allows the browser to aggressively skip layout, style, and paint recalculations for that entire subtree when changes happen elsewhere on the page, drastically improving rendering performance in complex applications.",
 ["Tells the browser a DOM subtree is completely independent of the rest of the page", "Allows the rendering engine to aggressively skip layout/paint recalculations", "Drastically improves performance in complex, heavily mutated DOM trees"],
 ["It contains CSS leaks from ruining the hard drive"]),

("FE_CSS_ARCH", "tradeoff", "hard", "tradeoff", ["CSS-in-JS"],
 "What are the tradeoffs of using Runtime CSS-in-JS (like styled-components or Emotion) versus zero-runtime CSS-in-JS (like Vanilla Extract)?",
 "Runtime CSS-in-JS provides massive flexibility, allowing dynamic CSS generation based on React state and props, but it incurs a heavy performance penalty because it must parse CSS and inject `<style>` tags during browser execution. Zero-runtime tools extract all static CSS into external files at build time, eliminating runtime overhead and allowing native browser caching, but they lose the ability to interpolate dynamic state variables directly into the stylesheet.",
 ["Runtime: Massive dynamic flexibility, but heavy performance penalty for parsing/injecting tags at runtime", "Zero-runtime: Extracts static CSS at build time (fast, cacheable, zero overhead)", "Zero-runtime tradeoff: Cannot interpolate dynamic JS state directly into CSS rules"],
 ["Zero-runtime means the CSS runs backwards"]),

("FE_CSS_ARCH", "scenario", "medium", "scenario", ["Grid"],
 "You are building a fully responsive grid system without using Media Queries. You want the columns to automatically wrap to the next line when they shrink below 300px, but stretch to fill the remaining space otherwise. What specific CSS Grid configuration accomplishes this?",
 "You achieve this fluid layout by combining `auto-fit` with `minmax`. The exact configuration is: `grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));`. This instructs the grid to fit as many columns as possible, ensuring they never shrink below 300px, and allocating any leftover space equally (`1fr`).",
 ["Combine `auto-fit` with `minmax()`", "Configuration: `grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));`", "Automatically wraps and stretches columns without relying on Media Queries"],
 ["Use `display: table` and hope for the best"]),

("FE_CSS_ARCH", "implement", "medium", "implementation", ["Theming"],
 "You are designing a dark mode architecture for a large application. Instead of writing duplicate CSS selectors for every component (e.g., `.card.dark`), how do you architect this globally using modern CSS?",
 "You architect it using CSS Custom Properties (CSS Variables) defined at the `:root` level. You define your light mode tokens (e.g., `--bg-color: white;`). Then, inside a media query `@media (prefers-color-scheme: dark)`, you redefine the exact same variables on `:root` (e.g., `--bg-color: black;`). The components simply reference `background: var(--bg-color);` and adapt automatically without duplicating class logic.",
 ["Use CSS Custom Properties (Variables) defined on `:root`", "Override the exact same variables inside a `@media (prefers-color-scheme: dark)` block", "Components reference `var(--bg-color)` and adapt automatically without extra classes"],
 ["Buy a darker monitor"]),

("FE_CSS_ARCH", "debug", "medium", "debugging", ["Layout"],
 "Two inline-block elements are placed next to each other in the HTML: `<div>A</div> <div>B</div>`. Despite having exactly 50% width and `box-sizing: border-box`, the second div wraps to the next line. Why does this happen, and what is the cleanest architectural fix?",
 "This happens because the browser renders the physical whitespace (the space/newline in the HTML source code) between the two `<div>` tags as a text node, which takes up a few pixels. This pushes the total width past 100%. The modern, clean architectural fix is to abandon `inline-block` for layouts and apply Flexbox (`display: flex`) to the parent container, which inherently ignores whitespace text nodes for layout.",
 ["Physical whitespace in the HTML source code is rendered as a text node, pushing width > 100%", "The classic fix was commenting out the whitespace or setting font-size to 0", "The modern architectural fix is to use Flexbox (`display: flex`) on the parent container"],
 ["The divs are allergic to each other"]),

("FE_CSS_ARCH", "fundamentals", "easy", "concept", ["Box Model"],
 "What does `box-sizing: border-box` do, and why is it considered a mandatory global reset in modern CSS architecture?",
 "By default (content-box), padding and borders are added *to* the defined width/height of an element, causing it to unexpectedly break out of grid layouts. `box-sizing: border-box` forces the browser to calculate padding and borders *within* the defined width/height. This makes dimension calculations highly predictable and is universally applied as a global reset.",
 ["Forces padding and borders to be calculated *inside* the defined width/height", "Prevents elements from unexpectedly expanding and breaking layouts", "Considered a mandatory global reset for predictable dimensional calculations"],
 ["It draws a literal box around the browser window"]),

("FE_CSS_ARCH", "tradeoff", "medium", "tradeoff", ["Design Systems"],
 "When structuring a design system, what is the tradeoff of creating highly abstracted 'Molecule' components (like an entire `UserCard`) versus highly composable 'Atom' components (like `Card`, `Avatar`, `Text`)?",
 "Molecules guarantee extreme visual consistency and are trivial to drop into a page, but they become dangerously rigid, eventually requiring dozens of boolean props (`showAvatar`, `isCompact`) to handle edge cases. Atoms require more boilerplate HTML to assemble every single time, but provide infinite architectural flexibility without prop drilling or component bloat.",
 ["Molecules: Extreme consistency and easy to use, but rigid and prone to prop-bloat", "Atoms: Infinite flexibility and composition without prop drilling", "Atoms tradeoff: Requires writing more boilerplate to assemble standard UI patterns"],
 ["Molecules explode, Atoms cause radiation"]),

("FE_CSS_ARCH", "implement", "hard", "implementation", ["Sticky Positioning"],
 "You need to prevent a deeply nested sticky header from scrolling out of view. You apply `position: sticky; top: 0;`, but it simply scrolls off the screen as if it were `position: relative`. What architectural CSS rule on a parent container is breaking this?",
 "Sticky positioning breaks instantly if ANY ancestor in the DOM tree (up to the viewport) has an `overflow` property set to `hidden`, `scroll`, or `auto`. The ancestor establishes a new scroll container, trapping the sticky element. You must architecturally ensure all parent containers up to the document body have `overflow: visible` for sticky to adhere to the main viewport.",
 ["Breaks if ANY ancestor in the DOM tree has `overflow: hidden`, `scroll`, or `auto`", "The ancestor creates a new local scroll container, trapping the sticky context", "Must ensure all parents up to the viewport have `overflow: visible`"],
 ["The CSS file ran out of glue"]),

("FE_CSS_ARCH", "scenario", "medium", "scenario", ["Stacking Context"],
 "A junior developer uses `z-index: 99999;` on a modal component, but it still appears underneath a fixed navigation bar that has `z-index: 10;`. Why is the modal failing to overlay the navbar?",
 "The modal is trapped inside a local Stacking Context created by one of its parent containers (e.g., a parent with `opacity: 0.9` or `position: relative; z-index: 1`). `z-index` is not a global browser value; it only applies within its current stacking context. A child inside a lower-priority stacking context can never overlap an element in a higher sibling stacking context, regardless of how high its internal `z-index` is.",
 ["Trapped inside a local Stacking Context created by a parent element", "`z-index` is not global; it only competes within its immediate stacking context", "A child in a lower stacking context can never overlap an element in a higher context"],
 ["`99999` is an illegal number in CSS"]),

("FE_CSS_ARCH", "explain", "medium", "concept", ["Formatting Contexts"],
 "What is the Block Formatting Context (BFC) in CSS, and what layout problem does it natively solve regarding floats?",
 "A BFC is an isolated layout region where child elements behave entirely independently of the outside DOM. If you establish a BFC on a parent container (using `display: flow-root` or `overflow: hidden`), it natively contains any floated child elements within it. This solves the classic problem of parent containers collapsing to a height of zero when they only contain floated children, eliminating the need for 'clearfix' hacks.",
 ["An isolated layout region that behaves independently of the outside DOM", "Established via `display: flow-root` or `overflow: hidden`", "Natively contains floated children, preventing the parent's height from collapsing to zero without hacks"],
 ["BFC stands for Big Friendly Container"]),

("FE_CSS_ARCH", "debug", "hard", "debugging", ["Containing Blocks"],
 "You apply a CSS transform `transform: translateZ(0);` or `will-change: transform;` to a static container div simply to force hardware acceleration. Unexpectedly, child elements with `position: fixed` suddenly start scrolling with the page instead of staying fixed to the viewport. Why?",
 "According to the CSS specification, applying any transform, filter, or perspective to an element immediately makes that element the 'containing block' for all absolutely and fixed-positioned descendants. The `fixed` children are now positioned relative to that transformed `div` rather than the browser viewport, causing them to scroll with the document.",
 ["Applying a transform, filter, or perspective establishes a new containing block", "`position: fixed` children are now positioned relative to this transformed div, not the viewport", "Causes fixed elements to suddenly scroll with the document"],
 ["Hardware acceleration melted the fixed positioning logic"])
]
