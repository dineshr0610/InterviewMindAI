"""Batch 12 question content (Frontend Developer). Antigravity-native, no Gemini API."""

ROLE = "Frontend Developer"

# key: (skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "TS_TY": ("TypeScript", "Types", "TypeScript", ["Full Stack Developer"]),
    "RA_AR": ("Component Architecture", "Design Patterns", "React", ["Full Stack Developer"]),
    "SM_GS": ("State Management", "Global State", "React", ["Full Stack Developer"]),
    "WP_CW": ("Web Performance", "Core Web Vitals", "Web", ["Full Stack Developer"]),
    "FT_CT": ("Frontend Testing", "Component Testing", "Jest", ["Full Stack Developer"]),
    "BA_SW": ("Browser APIs", "Service Workers", "JavaScript", ["Full Stack Developer"]),
    "WS_CS": ("Web Security", "CSRF", "Security", ["Backend Developer", "Full Stack Developer"]),
    "FN_DF": ("Network Requests", "Data Fetching", "JavaScript", ["Full Stack Developer"]),
    "CS_GR": ("CSS & Styling", "Grid", "CSS", ["Full Stack Developer"]),
}

# (bucket, intent, difficulty, qtype, secondary_skills, question, expected_answer, strong, weak)
Q = [
# ---------------- TS_TY ----------------
("TS_TY", "tradeoff", "easy", "tradeoff", ["Type Safety"],
 "Why would you choose to use `unknown` over `any` when handling a third-party API response?",
 "Using `any` completely disables TypeScript's type checking, allowing you to access any property safely at compile time but risking runtime crashes. `unknown` is type-safe; it forces you to perform type checking (narrowing) before you can access properties or call methods on the variable.",
 ["unknown forces type narrowing", "any disables type checking", "unknown prevents runtime errors"],
 ["Says unknown and any are exactly the same"]),

("TS_TY", "implement", "medium", "implementation", ["Unions"],
 "How would you approach creating a discriminated union to handle the state of a data-fetching component (idle, loading, success, error)?",
 "I would define a common literal type property, usually called `status` or `type`, across multiple interfaces. For example: `type FetchState = { status: 'idle' } | { status: 'loading' } | { status: 'success', data: Data } | { status: 'error', error: Error }`. TypeScript can then narrow the type based on the `status` field.",
 ["Common discriminant property like status", "Interfaces for each state", "Type narrowing via switch/if"],
 ["Uses boolean flags for isLoading, isError in a single interface (not a discriminated union)"]),

("TS_TY", "debug", "hard", "debugging", ["Generics"],
 "You notice that a generic function `function getProperty<T, K>(obj: T, key: K)` allows passing keys that don't exist on the object. How do you constrain `K` to safely type this?",
 "You must use the `extends keyof` constraint. The signature should be `function getProperty<T, K extends keyof T>(obj: T, key: K)`. This ensures that the compiler throws an error if `key` is not a valid property name of the type `T`.",
 ["Use extends keyof", "K extends keyof T", "Enforces compile-time key validation"],
 ["Suggests using any for the key"]),

("TS_TY", "compare", "medium", "comparison", ["Syntax"],
 "Compare the use cases for `interface` versus `type` aliases in modern TypeScript.",
 "`interface` is generally preferred for defining object shapes and class contracts because they support declaration merging (useful for extending third-party library types). `type` aliases are more versatile and must be used for unions, intersections, primitives, and mapped types. In modern TypeScript, their capabilities heavily overlap.",
 ["Interfaces support declaration merging", "Types are needed for unions and mapped types", "Heavy overlap for basic objects"],
 ["Says interfaces are only for classes"]),

("TS_TY", "scenario", "medium", "scenario", ["Performance"],
 "An application uses deeply nested generic mapped types that significantly slow down the IDE server. How do you mitigate this compilation overhead?",
 "Deeply nested conditional or mapped types create massive computational complexity for the TypeScript compiler. Mitigate this by breaking complex types into smaller, simpler interfaces, avoiding infinite recursion in types, using concrete types where extreme flexibility isn't needed, and utilizing `--diagnostics` to find the bottleneck.",
 ["Break down complex mapped types", "Avoid deep recursion", "Prefer concrete interfaces over complex generics"],
 ["Increase computer RAM as the only solution"]),

("TS_TY", "architecture", "hard", "architecture", ["Events"],
 "How would you design a type-safe event bus that enforces correct payload types for dynamically registered event names?",
 "I would define a central mapping interface where keys are event names and values are the corresponding payload types (e.g., `interface EventMap { 'login': User; 'logout': void }`). The `emit` and `on` functions would use generics constrained by `keyof EventMap` to statically link the event name to its specific payload type.",
 ["Central interface mapping events to payloads", "Generics constrained by keyof EventMap", "emit(event: K, payload: EventMap[K])"],
 ["Use `any` for the payload"]),

# ---------------- RA_AR ----------------
("RA_AR", "scenario", "medium", "scenario", ["State"],
 "A production application uses a single giant Context to store user data, theme, and notifications, causing the entire app to re-render. How do you re-architect this?",
 "Split the giant Context into multiple smaller, logically grouped Contexts (e.g., `UserContext`, `ThemeContext`, `NotificationContext`). This ensures that a component only subscribes to the specific data it needs, preventing a theme change from re-rendering components that only care about user data.",
 ["Split into multiple smaller contexts", "Group by domain or change frequency", "Prevents unnecessary re-renders"],
 ["Wrap the entire app in useMemo"]),

("RA_AR", "fundamentals", "easy", "concept", ["Patterns"],
 "When would you choose to use the Compound Component pattern instead of passing dozens of configuration props to a single component?",
 "When building complex UI elements like Select dropdowns, Accordions, or Tabs where the consumer needs control over the internal layout and ordering of children. It avoids 'prop drilling' and massive configuration objects by exposing child components (e.g., `<Menu.Item>`) that implicitly share state with the parent.",
 ["Avoids prop drilling/massive config objects", "Gives consumer layout control", "Implicit state sharing"],
 ["When the component has no children"]),

("RA_AR", "debug", "hard", "debugging", ["Reconciliation"],
 "You notice that a heavily memoized child component still loses its internal DOM state (like input focus) when its parent renders conditionally. What could be destroying the component instance?",
 "The parent is likely conditionally rendering the child in different positions of the JSX tree, or changing the `key` prop dynamically on every render (e.g., using `Math.random()`). React's reconciliation algorithm sees a different tree structure or key and destroys the old instance to mount a new one, wiping internal state.",
 ["Dynamic or random keys", "Changing component position in the JSX tree", "React unmounts and remounts the component"],
 ["useMemo doesn't preserve DOM state"]),

("RA_AR", "implement", "medium", "implementation", ["Hooks"],
 "How would you approach building a custom hook `useLocalStorage` that syncs state across multiple browser tabs?",
 "The hook should wrap `useState`, initializing the value from `localStorage`. It provides a setter that updates both the React state and `localStorage`. To sync across tabs, attach an event listener to the `window` 'storage' event, updating the local React state when the key changes in another tab.",
 ["Initialize from localStorage", "Update state and localStorage on change", "Listen to the 'storage' event for cross-tab sync"],
 ["Only use useState without event listeners"]),

("RA_AR", "tradeoff", "medium", "tradeoff", ["Patterns"],
 "What tradeoffs are involved in using Render Props versus Custom Hooks for sharing component logic?",
 "Custom hooks are modern, cleaner, and avoid 'wrapper hell' in the JSX tree, making logic easier to compose. Render props can sometimes be useful for dynamically injecting JSX, but they lead to deep nesting and less readable markup. Hooks cannot be used inside loops or conditions, whereas render props have no such rule.",
 ["Hooks avoid wrapper hell/nesting", "Hooks are cleaner for logic", "Hooks have strict rules of execution"],
 ["Render props are faster natively"]),

("RA_AR", "architecture", "hard", "architecture", ["Security"],
 "Suppose you are building a widget system where third-party developers supply React components. How do you safely render them while isolating errors and styling?",
 "Use React Error Boundaries to catch crashes in the third-party components so they don't unmount the main app. For strict isolation of styling and security (preventing XSS or global DOM access), wrap the widgets inside isolated `<iframe>` elements or use Shadow DOM.",
 ["Error Boundaries to prevent app crashes", "iframes for strict JS/CSS isolation", "Shadow DOM for style scoping"],
 ["Just render them directly via dangerouslySetInnerHTML"]),

# ---------------- SM_GS ----------------
("SM_GS", "compare", "easy", "comparison", ["Architecture"],
 "Compare lifting state up to a parent component versus introducing a global state management tool like Redux.",
 "Lifting state up is perfect for localized sharing between a few sibling components, but causes prop drilling and widespread re-renders if the state is needed deep in the tree. Global state (Redux) allows components to subscribe directly to the data they need, bypassing the component tree entirely.",
 ["Lifting state causes prop drilling in deep trees", "Global state avoids prop drilling", "Global state provides direct subscriptions"],
 ["Lifting state requires Redux"]),

("SM_GS", "scenario", "medium", "scenario", ["Hooks"],
 "An application experiences 'stale UI' because derived state was stored in a `useEffect` instead of being calculated during render. How do you correct this?",
 "Remove the `useEffect` and the duplicate `useState`. Calculate the derived state synchronously during the component's render body based on the existing props or state. This ensures the derived value is always up-to-date and eliminates an unnecessary extra render cycle.",
 ["Calculate derived state during render", "Remove the duplicate state/useEffect", "Eliminates unnecessary re-renders"],
 ["Add more dependencies to the useEffect"]),

("SM_GS", "implement", "medium", "implementation", ["Redux"],
 "How would you design a slice in Redux Toolkit to handle paginated data fetching and cache invalidation?",
 "I would define a slice with a dictionary or normalized structure (e.g., using `createEntityAdapter`) storing pages by index or ID, along with loading/error flags. Better yet, I would use RTK Query (part of Redux Toolkit), which automatically handles caching, paginated queries, and cache invalidation out of the box.",
 ["Use createEntityAdapter or RTK Query", "Store loading/error metadata", "RTK Query handles caching automatically"],
 ["Just store an array and push to it infinitely"]),

("SM_GS", "debug", "hard", "debugging", ["Updates"],
 "You encounter a race condition where two rapid state updates override each other. How do you ensure the previous state is correctly referenced during rapid updates?",
 "Use the functional updater form of `setState` (e.g., `setCount(prev => prev + 1)`). This guarantees that the update function receives the most recent state value, bypassing any stale closures that might have captured an older version of the state variable.",
 ["Use the functional updater callback", "prev => prev + new_value", "Bypasses stale closures"],
 ["Use a setTimeout delay"]),

("SM_GS", "tradeoff", "easy", "tradeoff", ["Local State"],
 "What are the tradeoffs of storing the UI open/closed state of a dropdown in Redux versus keeping it as local component state?",
 "Storing it in Redux clutters the global store, causes unnecessary global action dispatches, and forces the component to be coupled to the store. Keeping it in local state (`useState`) makes the component reusable, isolated, and highly performant.",
 ["Clutters global store", "Local state makes component reusable", "Redux causes unnecessary global dispatches"],
 ["Redux makes it render faster"]),

("SM_GS", "architecture", "hard", "architecture", ["Normalization"],
 "How would you approach normalizing a deeply nested JSON response in the frontend store to optimize updates?",
 "I would flatten the nested structure using a library like `normalizr`. Entities (posts, comments, authors) are stored in separate dictionaries keyed by their IDs. The main state only holds arrays of IDs. This prevents deep cloning during updates and allows individual components to connect to specific IDs without re-rendering the whole tree.",
 ["Flatten nested structures into dictionaries by ID", "Store arrays of IDs", "Prevents deep cloning and massive re-renders"],
 ["Store the JSON stringified in local storage"]),

# ---------------- WP_CW ----------------
("WP_CW", "fundamentals", "medium", "concept", ["Metrics"],
 "What happens when a large synchronous JavaScript bundle blocks the main thread, and which Core Web Vital does this most negatively impact?",
 "The browser cannot respond to user inputs (clicks, typing) or render updates while the main thread is blocked. This heavily degrades Interaction to Next Paint (INP) and Total Blocking Time (TBT).",
 ["Blocks UI updates and user input", "Negatively impacts Interaction to Next Paint (INP)", "Negatively impacts Total Blocking Time"],
 ["Impacts Cumulative Layout Shift"]),

("WP_CW", "scenario", "hard", "scenario", ["LCP"],
 "You notice that Largest Contentful Paint (LCP) is failing because the hero image is loaded via a CSS background. How do you optimize this to improve LCP?",
 "Browsers discover CSS background images late in the critical rendering path. Fix this by using a standard `<img>` tag with fetchpriority='high', or add a `<link rel='preload' href='hero.jpg' as='image'>` in the HTML head so the browser begins downloading the image immediately.",
 ["CSS backgrounds are discovered late", "Use standard img tag with fetchpriority", "Use preload link in the head"],
 ["Compress the CSS file"]),

("WP_CW", "explain", "easy", "concept", ["CLS"],
 "Explain the purpose of Cumulative Layout Shift (CLS) and name one common cause of poor CLS scores.",
 "CLS measures visual stability by tracking unexpected layout shifts during page load. A common cause is loading images or iframes without explicit width/height dimensions, or injecting dynamic content (like ads or banners) above existing content without reserving space.",
 ["Measures visual stability / layout shifts", "Images without width/height dimensions", "Injecting dynamic content without reserving space"],
 ["It measures how long it takes to paint the layout"]),

("WP_CW", "implement", "medium", "implementation", ["Lazy Loading"],
 "How would you approach lazy-loading a heavy charting library only when a user scrolls it into the viewport?",
 "I would use an `IntersectionObserver` to detect when the container enters the viewport. Once visible, I would use a dynamic import (`import('chart-lib')`) or React's `lazy`/`Suspense` to fetch the library chunk over the network and render the chart.",
 ["IntersectionObserver to detect visibility", "Dynamic import()", "React.lazy and Suspense"],
 ["Just put it at the bottom of the HTML file"]),

("WP_CW", "compare", "medium", "comparison", ["Network"],
 "Compare the `<link rel='preload'>` and `<link rel='prefetch'>` tags regarding their use cases and browser prioritization.",
 "`preload` is for critical resources needed on the current page immediately (high priority, like a hero image or critical font). `prefetch` is for resources likely needed on a future page navigation (low priority, downloaded during idle time).",
 ["Preload is high priority for the current page", "Prefetch is low priority for future navigations", "Browser fetches prefetch during idle time"],
 ["They are completely identical"]),

("WP_CW", "debug", "hard", "debugging", ["INP"],
 "A site achieves great Lighthouse scores in the lab, but real-world Interaction to Next Paint (INP) is very high. How do you diagnose real-user interactivity delays?",
 "Lab data doesn't simulate complex user journeys or third-party script interference. Diagnose this using Real User Monitoring (RUM) data (web-vitals.js library) to send specific interaction timings to analytics. Use the Chrome DevTools Performance panel CPU throttling to profile heavy event listeners or massive React re-renders triggered by clicks.",
 ["Use Real User Monitoring (RUM) / web-vitals data", "Throttle CPU in DevTools Performance tab", "Profile event listeners and React re-renders"],
 ["Rerun Lighthouse ten times"]),

# ---------------- FT_CT ----------------
("FT_CT", "tradeoff", "easy", "tradeoff", ["Testing Philosophy"],
 "Why would you choose to test a component's behavioral outcomes (e.g., finding text on the screen) rather than asserting its internal state?",
 "Testing internal state makes tests brittle; they break if you refactor the implementation without changing the UI behavior. Testing behavioral outcomes (what the user actually sees and interacts with) ensures the component fulfills its contract regardless of internal refactoring, as promoted by React Testing Library.",
 ["Internal state tests are brittle to refactoring", "Behavioral tests simulate user experience", "Ensures the UI contract is met"],
 ["Behavioral testing runs much faster"]),

("FT_CT", "scenario", "medium", "scenario", ["Async Testing"],
 "An application experiences flaky tests because API responses return at unpredictable times. How do you stabilize async UI tests in Jest/React Testing Library?",
 "Use robust async utilities like `waitFor` or `findByText` instead of hardcoded timeouts. Ensure all network requests are properly mocked at the boundary (e.g., using MSW - Mock Service Worker) so responses are instantaneous and deterministic, completely isolating the test from network variability.",
 ["Use findBy/waitFor instead of hard timeouts", "Mock the network layer (e.g., MSW)", "Ensure deterministic responses"],
 ["Add a 5-second timeout to every test"]),

("FT_CT", "implement", "medium", "implementation", ["Mocking"],
 "How would you approach mocking a global object like `window.matchMedia` for a component test that relies on responsive design hooks?",
 "I would define `Object.defineProperty(window, 'matchMedia', { writable: true, value: jest.fn().mockImplementation(query => ({ matches: false, addListener: jest.fn(), removeListener: jest.fn() })) })` in the test setup file. This intercepts the hook's call to the missing JSDOM API without crashing.",
 ["Use Object.defineProperty on window", "Provide a jest.fn() mock", "Return mock properties like matches/addListener"],
 ["You cannot mock window objects in Jest"]),

("FT_CT", "debug", "hard", "debugging", ["React Warning"],
 "You notice that multiple test suites are failing intermittently with the 'act(...) warning' in React. What is the fundamental cause of this warning?",
 "The warning occurs when a state update happens outside of React's testing `act()` wrapper. Usually, this means an asynchronous operation (like a Promise or API mock) resolved and called `setState` after the test already completed its assertions. Fix it by awaiting `findBy` or using `waitFor` to ensure the test waits for the async state update.",
 ["State update outside act()", "Async operation resolved after test finished", "Fix by awaiting findBy or using waitFor"],
 ["It's a bug in React Testing Library"]),

("FT_CT", "architecture", "hard", "architecture", ["Test Strategy"],
 "How would you design a test strategy that balances the speed of unit tests with the confidence of E2E tests in a complex SPA?",
 "Rely heavily on integration tests (using React Testing Library) to test page-level workflows with mocked network layers (MSW). Keep E2E tests (Cypress/Playwright) limited to critical paths (login, checkout) against a real staging environment. Reserve pure unit tests for complex utility functions and isolated reducers.",
 ["Integration tests with mocked networks for the bulk", "E2E for critical business paths only", "Unit tests for pure logic/reducers"],
 ["Test everything 100% with E2E tests only"]),

# ---------------- BA_SW ----------------
("BA_SW", "fundamentals", "easy", "concept", ["Storage"],
 "When would you choose `sessionStorage` over `localStorage` for persisting user data?",
 "Use `sessionStorage` for data that should only persist for the duration of the current page session (e.g., temporary form drafts). It is cleared when the tab or window is closed. Use `localStorage` for data that needs to persist across multiple sessions and tabs.",
 ["sessionStorage clears when tab closes", "localStorage persists across sessions", "Use for temporary session state"],
 ["sessionStorage holds more data than localStorage"]),

("BA_SW", "explain", "medium", "concept", ["DOM APIs"],
 "Explain how an IntersectionObserver differs from binding to the window scroll event for implementing infinite scrolling.",
 "Binding to the scroll event fires continuously on the main thread, causing severe performance issues unless heavily throttled. `IntersectionObserver` is a modern browser API that asynchronously calculates element visibility off the main thread, triggering a callback only when the element enters or exits the viewport.",
 ["Scroll events block main thread and need throttling", "IntersectionObserver is asynchronous and performant", "Triggers only on visibility threshold changes"],
 ["IntersectionObserver requires jQuery"]),

("BA_SW", "implement", "hard", "implementation", ["Caching"],
 "How would you approach setting up a Service Worker to intercept network requests and serve a stale-while-revalidate caching strategy?",
 "Register the Service Worker. In the `fetch` event listener, intercept the request. Check the Cache API for a cached response. If found, immediately return it (stale), while concurrently executing a `fetch` request to the network to get the fresh response, updating the cache with the new data for the next visit.",
 ["Intercept the fetch event", "Return cached response immediately if present", "Concurrently fetch network and update cache"],
 ["Download everything in the install event only"]),

("BA_SW", "debug", "medium", "debugging", ["Storage"],
 "An application experiences silent failures when attempting to store a large Blob in `localStorage`. What is the issue, and what API should be used instead?",
 "`localStorage` is strictly synchronous, string-only, and typically limited to 5MB, which causes large Blobs or data sets to exceed quotas and block the main thread. The correct API to use is `IndexedDB`, which is asynchronous and supports large volumes of structured data and Blobs.",
 ["localStorage is limited (5MB) and synchronous", "Cannot store Blobs natively", "Use IndexedDB instead"],
 ["Increase the localStorage quota in HTML settings"]),

("BA_SW", "scenario", "medium", "scenario", ["Cross-Tab Communication"],
 "You need to notify all open browser tabs of a user logout event to sync the UI state. How would you implement this using modern browser APIs?",
 "The easiest approach is to listen to the `storage` event on the window, which fires in other tabs when `localStorage` changes. Alternatively, use the `BroadcastChannel` API, which allows direct publish/subscribe messaging between all scripts sharing the same origin.",
 ["Listen to the 'storage' event on window", "Use the BroadcastChannel API", "Updates across same-origin tabs"],
 ["Use a continuous setInterval to ping the server"]),

# ---------------- WS_CS ----------------
("WS_CS", "fundamentals", "medium", "concept", ["Security"],
 "What happens when a malicious site submits a form to your authenticated endpoint, and how does CSRF protection mitigate it?",
 "In a Cross-Site Request Forgery (CSRF) attack, the browser automatically attaches the user's session cookies to the cross-origin request. CSRF is mitigated by requiring an unpredictable CSRF token in a hidden form field or custom header, which the malicious site cannot read, or by using `SameSite=Strict` on cookies.",
 ["Browser auto-attaches cookies", "Requires unpredictable CSRF token", "SameSite cookie attribute mitigates it"],
 ["CSRF steals passwords directly from the DOM"]),

("WS_CS", "tradeoff", "easy", "tradeoff", ["Auth"],
 "What tradeoffs exist between storing a JWT in an HttpOnly cookie versus storing it in localStorage?",
 "Storing a JWT in `localStorage` exposes it to XSS attacks (any malicious script can read it), but avoids CSRF issues. Storing it in an `HttpOnly` cookie protects it from XSS (JavaScript cannot read it) but makes the application vulnerable to CSRF attacks unless mitigated.",
 ["localStorage is vulnerable to XSS", "HttpOnly cookies are protected from XSS", "Cookies are vulnerable to CSRF"],
 ["HttpOnly cookies are faster to read in React"]),

("WS_CS", "explain", "hard", "concept", ["CSP"],
 "Explain how a Content Security Policy (CSP) helps prevent XSS, and describe how strict nonces function in an inline script environment.",
 "CSP is an HTTP header restricting the sources from which the browser can load/execute resources. It blocks XSS by disallowing unauthorized external scripts and inline scripts. A strict nonce is a random base64 string generated per request; inline scripts are only executed if their `nonce` attribute exactly matches the one in the CSP header.",
 ["Restricts trusted sources for scripts", "Blocks inline and unauthorized scripts", "Nonce requires cryptographically random matching string per request"],
 ["CSP encrypts the HTML payloads"]),

("WS_CS", "scenario", "medium", "scenario", ["Sanitization"],
 "An application experiences a vulnerability where user input is passed directly to `innerHTML`. How would you safely render user-generated HTML in React?",
 "React's `dangerouslySetInnerHTML` bypasses built-in escaping. To safely render user-generated HTML, you must sanitize the input string before rendering using a robust sanitization library like `DOMPurify`. This strips out malicious `<script>` tags and event handlers while preserving safe HTML.",
 ["dangerouslySetInnerHTML bypasses React escaping", "Must use a sanitization library like DOMPurify", "Strips scripts and event handlers"],
 ["Use a regular expression to remove <script>"]),

("WS_CS", "debug", "hard", "debugging", ["Cookies"],
 "You notice that your `SameSite=Strict` cookie is not being sent on navigation from an external site, breaking deep links. How do you resolve this while maintaining security?",
 "`SameSite=Strict` prevents the cookie from being sent on top-level cross-site navigations. To fix broken deep links while maintaining security, change the cookie to `SameSite=Lax`. This allows the cookie to be sent on safe top-level navigations (like GET requests from clicking a link) while still blocking it on cross-site POSTs (preventing CSRF).",
 ["Strict blocks cross-site top-level navigation cookies", "Change to SameSite=Lax", "Lax allows GET requests but blocks POST CSRF"],
 ["Remove SameSite attribute completely"]),

# ---------------- FN_DF ----------------
("FN_DF", "scenario", "easy", "scenario", ["UX"],
 "Why would you choose to implement optimistic UI updates, and what happens if the underlying network request fails?",
 "Optimistic updates instantly reflect the user's action in the UI before the server confirms it, making the app feel incredibly fast. If the network request fails, you must catch the error, revert the UI state back to its previous correct state, and display an error message to the user.",
 ["Makes the app feel fast/responsive", "Instantly updates UI", "Requires rolling back state on failure"],
 ["Optimistic updates skip the network request entirely"]),

("FN_DF", "implement", "medium", "implementation", ["Cancellation"],
 "How would you approach canceling a pending `fetch` request when the user navigates away from the current React component?",
 "I would instantiate an `AbortController` and pass its `signal` to the `fetch` options. Inside the `useEffect` cleanup function, I would call `controller.abort()`. This cancels the network request and prevents the Promise from resolving and updating unmounted component state.",
 ["Use AbortController", "Pass signal to fetch", "Call abort() in useEffect cleanup"],
 ["Use Promise.reject()"]),

("FN_DF", "debug", "hard", "debugging", ["Race Conditions"],
 "An application experiences a race condition where navigating quickly between tabs causes the older network response to overwrite the newer one. How do you fix this?",
 "This happens because the older, slower request resolves last. Fix it by ignoring stale responses. In `useEffect`, use a boolean flag (e.g., `let ignore = false`) that is set to true in the cleanup function. Or use an `AbortController` to cancel the previous fetch entirely before starting a new one.",
 ["Older/slower request resolves last", "Use a cleanup boolean flag to ignore stale response", "Use AbortController to cancel previous request"],
 ["Force synchronous fetches"]),

("FN_DF", "compare", "medium", "comparison", ["Pagination"],
 "Compare cursor-based pagination with offset-based pagination in terms of frontend implementation and resilience to data mutations.",
 "Offset-based (page/limit) is simple to implement but vulnerable to data drift (items shifting pages if elements are added/deleted). Cursor-based passes a unique ID/timestamp (the cursor) to fetch the next chunk. Cursor-based guarantees no duplicates/skips during data mutations, making it ideal for infinite feeds.",
 ["Offset is simple but suffers from data drift", "Cursor uses unique ID/timestamp", "Cursor is resilient to insertions/deletions"],
 ["Offset is faster for the database"]),

("FN_DF", "tradeoff", "medium", "tradeoff", ["Retries"],
 "What are the tradeoffs of implementing automated exponential backoff retries for failed frontend API requests?",
 "It vastly improves UX during temporary network hiccups or 503 errors. The tradeoff is increased complexity, potential thundering herd problems against a recovering server (if jitter isn't added), and masking permanent 4xx errors if you don't specifically filter them out.",
 ["Improves UX for temporary failures", "Risk of thundering herd / overloading server", "Requires filtering out unrecoverable 4xx errors"],
 ["Exponential backoff makes the first request faster"]),

("FN_DF", "architecture", "hard", "architecture", ["Auth"],
 "How would you design a resilient data-fetching abstraction that globally handles authorization token refresh without dropping the original queued requests?",
 "Use an Axios interceptor on responses. If a request returns a 401, catch it, push the original request configuration into a queue, and trigger the token refresh request. Once the refresh succeeds, update the headers and iterate through the queue to retry all stalled requests. Use a mutex/flag to ensure only one refresh happens simultaneously.",
 ["Axios response interceptor for 401s", "Queue failed requests during refresh", "Retry queue upon successful refresh with mutex"],
 ["Just redirect to login immediately on 401"]),

# ---------------- CS_GR ----------------
("CS_GR", "fundamentals", "easy", "concept", ["Layouts"],
 "When would you choose CSS Grid over Flexbox for a page layout?",
 "Choose CSS Grid when you need a complex two-dimensional layout (controlling both rows and columns simultaneously). Flexbox is better suited for one-dimensional layouts (aligning items along a single row or a single column).",
 ["Grid is two-dimensional (rows and columns)", "Flexbox is one-dimensional", "Grid for overall page layout"],
 ["Grid is faster to render"]),

("CS_GR", "implement", "medium", "implementation", ["Responsiveness"],
 "How would you approach creating a responsive, auto-wrapping grid of cards where each card maintains a minimum width but expands to fill available space, without media queries?",
 "I would use CSS Grid with the `repeat`, `auto-fit`, and `minmax` functions. Specifically: `grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));`. This automatically creates as many columns as will fit and wraps smoothly without explicit media queries.",
 ["CSS Grid", "repeat(auto-fit, ...)", "minmax(min, 1fr)"],
 ["Use float: left and calc()"]),

("CS_GR", "debug", "medium", "debugging", ["Positioning"],
 "You notice that a child element with `position: absolute` is escaping its intended parent container and positioning itself relative to the body. What CSS property is missing on the parent?",
 "The parent container is missing a positioning context. You need to add `position: relative;` (or absolute/fixed/sticky) to the parent. Absolute positioning bases its coordinates on the nearest positioned ancestor.",
 ["Parent needs position: relative", "Absolute looks for nearest positioned ancestor", "Escapes to body/root without it"],
 ["Add z-index to the parent"]),

("CS_GR", "explain", "hard", "concept", ["Stacking Context"],
 "Explain the concept of a CSS Stacking Context. How does `z-index` behave differently when a new stacking context is created?",
 "A stacking context is a three-dimensional conceptualization of HTML elements. Elements within a stacking context cannot interleave with elements in a sibling stacking context. A child with `z-index: 9999` will still render underneath a sibling of its parent if the parent has a lower `z-index` and forms a stacking context (e.g., via `position: relative` + `z-index`, or `opacity < 1`).",
 ["Group of elements ordered together on the z-axis", "Child z-index is constrained by parent's context", "Created by position+z-index, opacity, transform"],
 ["z-index is strictly global across the entire page"]),

("CS_GR", "scenario", "hard", "scenario", ["CSS Architecture"],
 "A production application suffers from CSS specificity wars, with many `!important` tags overriding each other. How would you re-architect the CSS to resolve this?",
 "I would adopt a strict CSS methodology like BEM (Block Element Modifier) to keep specificity flat. Alternatively, migrate to CSS Modules, styled-components, or utility classes (Tailwind) to scope styles locally. Finally, audit and remove `!important` tags, relying on CSS cascade layers (`@layer`) to explicitly define precedence.",
 ["Adopt a flat methodology like BEM", "Use scoped CSS (Modules/CSS-in-JS)", "Use CSS Cascade Layers (@layer)"],
 ["Just add more nested selectors and IDs"])
]
