"""Batch 11 question content (Frontend Developer). Antigravity-native, no Gemini API."""

ROLE = "Frontend Developer"

# key: (plan skill, plan topic, applicable_roles)
BUCKET_KEYS = {
    "JS_EV": ("Core JavaScript", "Event Loop", ["Full Stack Developer", "Backend Developer"]),
    "RC_CO": ("React Fundamentals", "Components", ["Full Stack Developer"]),
    "RC_UE": ("React Hooks", "useEffect", ["Full Stack Developer"]),
    "PF_MM": ("Performance Optimization", "Memoization", ["Full Stack Developer"]),
    "WS_CO": ("Web Security", "CORS", ["Backend Developer", "Full Stack Developer"]),
    "DB_PR": ("Debugging Tools", "Profiling", ["Full Stack Developer"]),
    "HD_AX": ("HTML/DOM", "Accessibility", ["Full Stack Developer"]),
}

# (bucket, intent, difficulty, qtype, secondary_skills, question, expected_answer, strong, weak)
Q = [
# ---------------- JS_EV ----------------
("JS_EV", "fundamentals", "easy", "concept", ["Concurrency"],
 "What is the difference between the call stack, macrotask queue, and microtask queue in JavaScript?",
 "The call stack executes synchronous code. The macrotask queue (or task queue) holds callbacks from setTimeout, setInterval, etc. The microtask queue holds callbacks from Promises and MutationObservers. The event loop prioritizes the microtask queue, emptying it completely before moving to the next macrotask.",
 ["Microtasks have higher priority", "Call stack is synchronous", "Promises are microtasks"],
 ["Says setTimeout is a microtask", "Confuses the stack with the heap"]),

("JS_EV", "implement", "medium", "implementation", ["Performance"],
 "How can you defer a heavy computation in the browser to prevent blocking the main thread without using Web Workers?",
 "You can chunk the heavy computation into smaller pieces and use setTimeout(..., 0) or requestIdleCallback to schedule each chunk on the event loop. This allows the browser to process UI updates and user interactions between chunks.",
 ["Chunking the workload", "Using setTimeout or requestIdleCallback", "Yielding to the main thread"],
 ["Use a while loop", "Use async/await without actually yielding"]),

("JS_EV", "debug", "hard", "debugging", ["Promises"],
 "A recursive Promise resolution is blocking a UI update. Why might microtasks starve the event loop, and how do you fix it?",
 "Because the event loop drains the entire microtask queue before picking up the next macrotask or rendering. If microtasks continuously queue more microtasks, rendering never occurs. Fix it by yielding to the macrotask queue using setTimeout(..., 0) to break the microtask chain.",
 ["Microtasks are drained completely before rendering", "Infinite microtask loops block the UI", "Use setTimeout to yield"],
 ["Thinks Promises run on a separate thread"]),

("JS_EV", "scenario", "medium", "scenario", ["DOM"],
 "An event listener (e.g., scroll or mousemove) fires thousands of times a second, making the UI sluggish. How do you mitigate this using the event loop?",
 "By using debouncing or throttling. Debouncing delays the execution until a period of inactivity, while throttling limits execution to once every specified timeframe. For purely visual updates, wrapping the logic in requestAnimationFrame is also effective.",
 ["Debouncing", "Throttling", "requestAnimationFrame"],
 ["Remove the event listener completely", "Use a synchronous delay"]),

("JS_EV", "compare", "easy", "comparison", ["Animations"],
 "Compare setTimeout and requestAnimationFrame for scheduling UI updates.",
 "setTimeout schedules a callback after a specified delay, but it doesn't align with the browser's refresh rate, leading to jank. requestAnimationFrame schedules a callback right before the next repaint, ensuring smooth 60fps animations and pausing when the tab is inactive.",
 ["requestAnimationFrame aligns with screen refresh", "setTimeout can cause jank", "rAF pauses in background tabs"],
 ["Says setTimeout is faster"]),

("JS_EV", "tradeoff", "medium", "tradeoff", ["Async/Await"],
 "What is the tradeoff of using async/await in a loop versus using Promise.all when handling multiple network requests?",
 "Using await inside a loop forces the requests to happen sequentially, which is slower but safe if requests depend on each other or you need to rate-limit. Promise.all runs them concurrently, which is faster but can overwhelm the server or hit rate limits if there are too many requests.",
 ["Sequential vs Concurrent execution", "Promise.all is faster", "Awaiting in a loop limits throughput"],
 ["Says Promise.all guarantees order of completion time"]),

("JS_EV", "architecture", "hard", "architecture", ["Web Workers"],
 "How do you architect a data parser that processes a 50MB JSON file in the browser without freezing the UI?",
 "Parsing a 50MB JSON string synchronously will block the main thread. The best architecture is to offload the JSON.parse and data processing to a Web Worker, sending the result back to the main thread via postMessage. Alternatively, use a streaming JSON parser.",
 ["Use a Web Worker", "Avoid synchronous JSON.parse on the main thread", "postMessage for communication"],
 ["Just wrap JSON.parse in a Promise (doesn't prevent blocking)"]),

("JS_EV", "fundamentals", "medium", "concept", ["Execution Context"],
 "What happens to the event loop when a synchronous while loop runs for 5 seconds?",
 "The event loop is completely blocked for 5 seconds. The call stack remains occupied, meaning no microtasks, macrotasks, UI repaints, or user interactions (like clicks) can be processed until the while loop finishes.",
 ["Event loop is blocked", "No rendering occurs", "No callbacks execute"],
 ["The browser moves it to a background thread"]),

# ---------------- RC_CO ----------------
("RC_CO", "explain", "easy", "concept", ["State Management"],
 "Explain the concept of 'lifting state up' in React component architecture.",
 "Lifting state up involves moving state from child components to their closest common parent. This is necessary when multiple sibling components need to share or react to the same state. The parent passes the state and updater functions down as props.",
 ["Move state to closest common ancestor", "Share state between siblings", "Pass state and callbacks via props"],
 ["Use Redux for everything instead"]),

("RC_CO", "implement", "medium", "implementation", ["Error Handling"],
 "Implement a basic React Error Boundary component. What lifecycle methods are required?",
 "An Error Boundary is a class component. It requires static getDerivedStateFromError() to update state and render a fallback UI, and componentDidCatch() to log the error information.",
 ["Must be a class component", "getDerivedStateFromError", "componentDidCatch"],
 ["Try to use a try/catch block inside a functional component render"]),

("RC_CO", "debug", "medium", "debugging", ["Rendering"],
 "A parent component re-renders and causes a heavy child component to re-render unnecessarily, even though its props haven't changed. How do you prevent this?",
 "Wrap the child component in React.memo(), which performs a shallow comparison of props. If the props include functions or objects passed from the parent, ensure they are memoized using useCallback or useMemo in the parent.",
 ["React.memo", "Shallow comparison of props", "Memoize reference props (useCallback/useMemo)"],
 ["Use shouldComponentUpdate in a functional component"]),

("RC_CO", "scenario", "hard", "scenario", ["State Management"],
 "You have a deeply nested 20-level component tree needing access to a user session. Contrast Context API vs prop drilling vs external state.",
 "Prop drilling 20 levels is unmaintainable. Context API solves this elegantly but can cause unnecessary re-renders if the context value changes often and isn't split properly. External state (Zustand, Redux) provides fine-grained selector reactivity, preventing unnecessary re-renders of intermediate components.",
 ["Prop drilling is unmaintainable", "Context causes re-renders without selectors", "External state offers fine-grained reactivity"],
 ["Says Context API is identical to Redux"]),

("RC_CO", "compare", "easy", "comparison", ["Forms"],
 "Compare controlled and uncontrolled components in React forms.",
 "Controlled components have their form data controlled by React state (value and onChange). Uncontrolled components let the DOM handle the form data, and you access it using a ref. Controlled is better for instant validation, uncontrolled is simpler for basic forms.",
 ["Controlled: React state holds the value", "Uncontrolled: DOM holds the value (refs)", "Controlled enables real-time validation"],
 ["Says uncontrolled components use Redux"]),

("RC_CO", "tradeoff", "medium", "tradeoff", ["CSS"],
 "What are the tradeoffs of using inline styles vs CSS modules in a large React application?",
 "Inline styles prevent global scope conflicts and allow dynamic styling based on state, but lack support for pseudo-classes (like :hover) and media queries, and can cause performance overhead. CSS modules offer local scoping and full CSS features but require build-tool configuration and separate files.",
 ["Inline lacks pseudo-classes and media queries", "CSS Modules provide local scope and full CSS", "Inline can be heavy on performance"],
 ["Says inline styles are faster because they don't load a CSS file"]),

("RC_CO", "architecture", "hard", "architecture", ["Design Patterns"],
 "How would you architect a reusable, highly customizable Table component that supports sorting, pagination, and custom cell rendering?",
 "Use the Compound Component pattern or Headless UI pattern (like React Table). Expose hooks for logic (useTable, useSort) and let the consumer handle the rendering markup. Accept render props for custom cells. Maintain state internally or allow it to be controlled via props.",
 ["Compound Components or Headless UI", "Hooks for logic separation", "Render props for custom cells"],
 ["Put everything in one massive component with 50 props"]),

("RC_CO", "fundamentals", "easy", "concept", ["Virtual DOM"],
 "Describe the Virtual DOM and how React's reconciliation algorithm works.",
 "The Virtual DOM is a lightweight JavaScript representation of the actual DOM. When state changes, React creates a new Virtual DOM, diffs it against the previous one (reconciliation), and calculates the minimal set of mutations needed to update the real DOM.",
 ["Lightweight JS object", "Diffing old and new trees", "Minimal batch updates to real DOM"],
 ["Says Virtual DOM is faster than real DOM because it runs in a Web Worker"]),

# ---------------- RC_UE ----------------
("RC_UE", "fundamentals", "easy", "concept", ["Hooks"],
 "What is the dependency array in useEffect, and what happens if you omit it?",
 "The dependency array tells React when to re-run the effect (only when those values change). If omitted, the effect runs after every single render of the component, which can lead to performance issues or infinite loops if it updates state.",
 ["Controls when the effect runs", "Runs on every render if omitted", "Empty array means run once on mount"],
 ["Says omitting it makes it never run"]),

("RC_UE", "explain", "medium", "concept", ["Lifecycle"],
 "Explain the cleanup function in useEffect. When and why does it run?",
 "The cleanup function is returned from the effect. It runs before the component unmounts, and also before the effect re-runs on subsequent renders. It is used to clean up subscriptions, event listeners, or timers to prevent memory leaks.",
 ["Runs on unmount and before re-running the effect", "Prevents memory leaks", "Cleans up listeners/timers"],
 ["Runs after the new effect runs"]),

("RC_UE", "implement", "medium", "implementation", ["Custom Hooks"],
 "Write a custom hook useDebounce that leverages useEffect to debounce a rapidly changing value.",
 "function useDebounce(value, delay) { const [debounced, setDebounced] = useState(value); useEffect(() => { const handler = setTimeout(() => setDebounced(value), delay); return () => clearTimeout(handler); }, [value, delay]); return debounced; }",
 ["Uses useState for the debounced value", "Uses setTimeout inside useEffect", "Returns a cleanup function to clearTimeout"],
 ["Fails to include a cleanup function"]),

("RC_UE", "debug", "hard", "debugging", ["Infinite Loops"],
 "A useEffect hook is causing an infinite loop. What are the common causes and how do you resolve them?",
 "Common causes include updating a state variable inside the effect that is also listed in the dependency array, or depending on an object/array/function created during render (which gets a new reference every render). Resolve by removing the state from dependencies if safe, or wrapping objects/functions in useMemo/useCallback.",
 ["State update triggering the dependency", "Unmemoized reference types in dependencies", "Use useCallback/useMemo"],
 ["Just remove the dependency array completely"]),

("RC_UE", "scenario", "medium", "scenario", ["Async/Await"],
 "You fetch data when a component mounts, but the user navigates away before the fetch completes. How do you prevent state updates on unmounted components?",
 "Use the useEffect cleanup function to set a boolean flag (e.g., isMounted = false) or use an AbortController to cancel the fetch. Before calling setState, check if the component is still mounted, or catch the AbortError.",
 ["Cleanup function with a boolean flag", "AbortController to cancel fetch", "Check flag before setState"],
 ["Use componentWillUnmount (not hooks)"]),

("RC_UE", "compare", "hard", "comparison", ["Rendering"],
 "Compare useEffect and useLayoutEffect. In what specific scenarios must you use useLayoutEffect?",
 "useEffect runs asynchronously after the paint, which is non-blocking. useLayoutEffect runs synchronously immediately after DOM mutations but before the browser paints. It must be used when you need to read DOM measurements (like scroll position or element width) and synchronously mutate the DOM to avoid visible flickering.",
 ["useEffect is async after paint", "useLayoutEffect is sync before paint", "useLayoutEffect prevents flickering for DOM measurements"],
 ["They are completely identical in modern React"]),

("RC_UE", "tradeoff", "medium", "tradeoff", ["Scope"],
 "What is the tradeoff of declaring functions inside vs outside of a useEffect block?",
 "Declaring inside the effect means it doesn't need to be in the dependency array and doesn't get recreated every render, but it can't be reused elsewhere in the component. Declaring outside allows reuse but requires it to be wrapped in useCallback and added to the dependency array to avoid stale closures or infinite loops.",
 ["Inside: no dependency issues, not reusable", "Outside: reusable, requires useCallback", "Stale closures risk if outside without dependencies"],
 ["Outside functions run faster natively"]),

# ---------------- PF_MM ----------------
("PF_MM", "fundamentals", "easy", "concept", ["Rendering"],
 "What is React.memo and when should it be used?",
 "React.memo is a higher-order component that prevents a functional component from re-rendering if its props have not changed (shallow comparison). It should be used for heavy components that receive the same props frequently.",
 ["Prevents re-renders", "Shallow prop comparison", "Use for heavy components"],
 ["It memoizes state values inside the component"]),

("PF_MM", "explain", "medium", "concept", ["Hooks"],
 "Explain the difference between useMemo and useCallback.",
 "useMemo is used to memoize the result of a costly calculation, returning a value. useCallback is used to memoize a function instance, returning the function itself. useCallback(fn, deps) is essentially equivalent to useMemo(() => fn, deps).",
 ["useMemo memoizes a value", "useCallback memoizes a function reference", "Both rely on a dependency array"],
 ["useCallback is for async functions only"]),

("PF_MM", "implement", "medium", "implementation", ["Data Processing"],
 "Show how to use useMemo to cache a computationally expensive data transformation.",
 "const sortedData = useMemo(() => { return expensiveSortAndFilter(data); }, [data]); This ensures the expensive operation only runs when the 'data' dependency changes, not on every re-render of the component.",
 ["Takes a factory function", "Returns the computed value", "Correct dependency array"],
 ["Omits the return statement in the factory"]),

("PF_MM", "debug", "hard", "debugging", ["References"],
 "You applied React.memo to a component, but it still re-renders on every parent render. What is likely going wrong?",
 "The parent is likely passing a new reference type (an object, array, or inline function) as a prop on every render. Because React.memo uses shallow comparison, the new reference breaks the memoization. Fix it by memoizing the prop in the parent using useMemo or useCallback.",
 ["Passing new object/function references", "Shallow comparison fails on new references", "Memoize props in parent"],
 ["React.memo is broken in strict mode"]),

("PF_MM", "scenario", "medium", "scenario", ["Virtualization"],
 "A list of 10,000 items renders slowly. How do you optimize this using memoization and virtualized lists?",
 "Memoization (React.memo) helps prevent re-rendering list items that haven't changed. However, rendering 10,000 DOM nodes is still slow. Virtualization (using libraries like react-window) only renders the visible DOM nodes (e.g., 20 items), drastically reducing the DOM size and initial render time.",
 ["React.memo prevents item re-renders", "Virtualization limits DOM nodes", "Only render visible items"],
 ["Use CSS display: none for items out of view"]),

("PF_MM", "compare", "easy", "comparison", ["Tradeoffs"],
 "Compare memoizing a value vs calculating it on every render. When is memoization actually slower?",
 "Memoization adds memory overhead to store the cached value and CPU overhead to compare the dependency array. For simple operations (like mapping a small array or basic math), the overhead of useMemo is slower than just recalculating it on every render.",
 ["Overhead of dependency comparison", "Memory cost", "Slower for cheap calculations"],
 ["Memoization is always faster no matter what"]),

("PF_MM", "architecture", "hard", "architecture", ["Redux", "Context"],
 "How do you design a state management store to minimize unnecessary re-renders in connected components?",
 "Normalize the state shape to avoid deep nesting. Use granular selectors (like Reselect) to derive data and memoize results. In Context API, split contexts by domain or change frequency (e.g., separate ThemeContext from UserContext) so components only subscribe to what they need.",
 ["Normalize state", "Memoized selectors", "Split contexts by change frequency"],
 ["Put everything in one global context object"]),

# ---------------- WS_CO ----------------
("WS_CO", "fundamentals", "easy", "concept", ["Network"],
 "What is CORS and why do browsers enforce it?",
 "Cross-Origin Resource Sharing (CORS) is a security mechanism enforced by browsers. It prevents a malicious website from making unauthorized API requests on behalf of a user to a different domain, thereby protecting user data and sessions.",
 ["Cross-Origin Resource Sharing", "Enforced by the browser", "Prevents unauthorized cross-origin requests"],
 ["It protects the server from DDoS attacks"]),

("WS_CO", "explain", "medium", "concept", ["HTTP Options"],
 "Explain the purpose of a CORS preflight request (OPTIONS). When is it triggered?",
 "A preflight request is an OPTIONS request sent by the browser to check if the server permits the actual request. It is triggered for 'non-simple' requests, such as those using methods like PUT/DELETE, or requests with custom headers like Authorization or Content-Type: application/json.",
 ["Sent using the OPTIONS method", "Checks server permissions before actual request", "Triggered for non-simple requests (JSON, PUT, custom headers)"],
 ["Triggered on every single GET request"]),

("WS_CO", "implement", "hard", "implementation", ["Tooling"],
 "Your frontend on localhost:3000 needs to access an API on api.example.com that lacks CORS headers. How do you bypass CORS during local development?",
 "Configure a local proxy in your development server (e.g., proxy field in create-react-app, or devServer.proxy in Webpack/Vite). The frontend makes a request to localhost, and the proxy server forwards it to the API. Since servers don't enforce CORS, the request succeeds.",
 ["Use a local dev server proxy", "Proxy forwards request server-to-server", "Bypasses browser enforcement"],
 ["Disable CORS in Chrome permanently for production users"]),

("WS_CO", "debug", "medium", "debugging", ["Headers"],
 "An API request fails with a CORS error, but the Network tab shows a 200 OK for the OPTIONS request. What could be missing in the server's response headers?",
 "The OPTIONS response might be missing the specific 'Access-Control-Allow-Origin' header matching the frontend, or it might be missing 'Access-Control-Allow-Methods' or 'Access-Control-Allow-Headers' that explicitly permit the headers/methods the frontend is trying to use.",
 ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods", "Access-Control-Allow-Headers"],
 ["The backend threw a 500 error"]),

("WS_CO", "scenario", "hard", "scenario", ["Authentication"],
 "You need to send cookies with a cross-origin fetch request. What specific frontend and backend configurations are required?",
 "Frontend: set `credentials: 'include'` on the fetch/axios request. Backend: set `Access-Control-Allow-Credentials: true` and specify an exact domain in `Access-Control-Allow-Origin` (it cannot be the wildcard '*').",
 ["Frontend: credentials: include", "Backend: Access-Control-Allow-Credentials: true", "Backend: specific Origin, not wildcard"],
 ["Just send the cookie manually in a custom header"]),

("WS_CO", "tradeoff", "easy", "tradeoff", ["Security Configuration"],
 "What is the tradeoff of using a wildcard '*' for Access-Control-Allow-Origin?",
 "It allows any website on the internet to make requests to your API, which is great for public APIs but poses a massive security risk for authenticated APIs. It also explicitly prevents the use of credentialed requests (cookies).",
 ["Allows any domain", "Cannot be used with credentials/cookies", "Bad for private/authenticated APIs"],
 ["Makes the API run faster"]),

# ---------------- DB_PR ----------------
("DB_PR", "fundamentals", "easy", "concept", ["React Tools"],
 "What is the React Developer Tools Profiler and what does it measure?",
 "It is a browser extension tool used to record the rendering performance of a React tree. It measures which components rendered, how long each render took, and why a component rendered (e.g., props changed, state changed).",
 ["Records rendering performance", "Measures render duration", "Identifies why components re-rendered"],
 ["It measures network request latency"]),

("DB_PR", "explain", "medium", "concept", ["Memory Management"],
 "Explain how to identify memory leaks in a frontend application using Chrome DevTools.",
 "Open the Memory tab, take a Heap Snapshot before an action, perform the action (like opening and closing a modal), and take another snapshot. Compare the snapshots to see if detached DOM nodes or objects are retained in memory. Alternatively, use the Allocation Timeline.",
 ["Memory tab / Heap Snapshots", "Compare snapshots before and after actions", "Look for detached DOM nodes"],
 ["Check the Network tab for pending requests"]),

("DB_PR", "implement", "hard", "implementation", ["Performance API"],
 "How do you use the Performance API to track custom rendering metrics in a frontend app?",
 "Call `performance.mark('start_task')` before the operation and `performance.mark('end_task')` after. Then call `performance.measure('Task Name', 'start_task', 'end_task')`. You can then retrieve the duration using `performance.getEntriesByName('Task Name')` or view it in the DevTools Performance timeline.",
 ["performance.mark()", "performance.measure()", "View in DevTools or getEntriesByName"],
 ["Use Date.now() and console.log"]),

("DB_PR", "debug", "medium", "debugging", ["Memory Leaks"],
 "A Single Page Application becomes sluggish over time without refreshing. Describe your workflow for diagnosing a DOM node leak.",
 "Open Chrome DevTools, use the Memory tab to take Heap Snapshots. Filter by 'Detached' to find detached DOM elements. Inspect their retainers to find the JavaScript closures, event listeners, or variables that are preventing the garbage collector from destroying them.",
 ["Heap Snapshots", "Search for Detached DOM nodes", "Inspect retainers (event listeners/closures)"],
 ["Clear the local storage to fix it"]),

("DB_PR", "scenario", "medium", "scenario", ["Network Optimization"],
 "The initial load time of your SPA is 5 seconds. How do you use DevTools to diagnose the bottleneck?",
 "Run a Lighthouse audit to get high-level metrics (FCP, LCP). Use the Network tab with throttling enabled (e.g., Fast 3G) to spot large bundle sizes, render-blocking scripts, or waterfall request chains. Check the Performance tab for long tasks blocking the main thread.",
 ["Lighthouse for Core Web Vitals", "Network tab with throttling for asset sizes/waterfalls", "Performance tab for long main thread tasks"],
 ["Use the Elements tab to find slow CSS"]),

("DB_PR", "compare", "easy", "comparison", ["Testing Workflow"],
 "Compare the Network tab's 'Disable cache' vs 'Throttling' features when testing performance.",
 "'Disable cache' simulates a first-time visitor's experience by forcing the browser to redownload all assets. 'Throttling' simulates a slow network connection (like 3G) or slow CPU, helping identify issues that only appear on lower-end devices.",
 ["Disable cache simulates first load", "Throttling simulates poor network/device", "Both are essential for real-world testing"],
 ["They do the exact same thing"]),

("DB_PR", "architecture", "hard", "architecture", ["CI/CD"],
 "How do you build an automated performance regression testing pipeline for a frontend application?",
 "Integrate Lighthouse CI into the GitHub Actions/CI pipeline. Set performance budgets for bundle sizes using tools like webpack-bundle-analyzer or bundlesize. Fail the PR build if metrics like LCP, TBT, or bundle size exceed defined thresholds.",
 ["Lighthouse CI in pipeline", "Set performance budgets", "Fail PRs on threshold breaches"],
 ["Run Lighthouse manually once a year"]),

# ---------------- HD_AX ----------------
("HD_AX", "fundamentals", "easy", "concept", ["HTML"],
 "What are ARIA roles and when should you use them instead of semantic HTML?",
 "ARIA (Accessible Rich Internet Applications) roles provide semantic meaning to screen readers. You should always prefer native semantic HTML (like <button> or <nav>). Use ARIA roles only when building custom complex UI widgets (like tabs or accordions) where native HTML elements fall short.",
 ["Provide semantics for screen readers", "Prefer native semantic HTML first", "Use for custom widgets"],
 ["Use ARIA roles on every single div"]),

("HD_AX", "explain", "medium", "concept", ["Routing"],
 "Explain the importance of focus management in a Single Page Application (SPA) during route transitions.",
 "In an SPA, the browser doesn't do a full page reload, so screen readers aren't notified of the new page, and keyboard focus remains where it was (often on the clicked link). You must programmatically shift focus to the new page's main heading or a specific wrapper to announce the change.",
 ["No full page reload in SPA", "Screen readers need notification of change", "Programmatically shift focus to new content"],
 ["Focus management doesn't matter in React"]),

("HD_AX", "implement", "medium", "implementation", ["UI Components"],
 "Implement a custom modal dialog that adheres to accessibility guidelines regarding focus.",
 "When opened, the modal should trap focus inside it (tabbing cycles through modal interactive elements only), shift initial focus to the first interactive element or the modal itself, return focus to the trigger button when closed, and close on the Escape key.",
 ["Trap focus within modal", "Restore focus on close", "Support Escape key"],
 ["Just use z-index and pointer-events"]),

("HD_AX", "debug", "hard", "debugging", ["ARIA"],
 "A screen reader is skipping over a dynamic live-updating stock ticker on your page. How do you fix this?",
 "Wrap the ticker content in an element with an ARIA live region attribute, such as `aria-live='polite'` (waits until user is idle) or `aria-live='assertive'` (interrupts immediately). This instructs the screen reader to announce DOM updates.",
 ["Use aria-live attribute", "Choose polite or assertive", "Announces dynamic DOM changes"],
 ["Add a title attribute to the div"]),

("HD_AX", "scenario", "easy", "scenario", ["Forms"],
 "You are auditing a form for accessibility. What are three critical things you look for regarding inputs and labels?",
 "1) Every input must have a visible `<label>` associated via the `for`/`id` attribute. 2) Error messages should be linked using `aria-describedby`. 3) Required fields should use the native `required` attribute or `aria-required`.",
 ["Label associated with input (for/id)", "Errors linked with aria-describedby", "Required fields indicated semantically"],
 ["Use placeholders instead of labels"]),

("HD_AX", "compare", "medium", "comparison", ["Images"],
 "Compare the 'alt' attribute on an 'img' tag with the 'aria-label' attribute on a 'div' used as an icon.",
 "The 'alt' attribute provides text for native images when they fail to load and for screen readers. 'aria-label' provides an accessible name for non-text elements (like SVG or div icons) that screen readers will announce, but doesn't show visually if the icon fails to load.",
 ["alt is for native images (fallback + screen reader)", "aria-label is for accessible name on generic elements", "alt shows visually on failure"],
 ["They are interchangeable in all scenarios"]),

("HD_AX", "tradeoff", "hard", "tradeoff", ["Custom UI"],
 "What is the tradeoff of using highly customized, div-based UI components versus native browser controls regarding accessibility?",
 "Custom div-based controls offer total design freedom but require manually implementing all keyboard interactions (Space/Enter), focus states, and ARIA roles/states (like aria-expanded). Native controls (like `<select>`) are accessible out of the box but are notoriously difficult to style consistently across browsers.",
 ["Total design freedom vs built-in accessibility", "Custom needs manual keyboard and ARIA management", "Native is hard to style"],
 ["Custom divs are natively accessible if you add tabIndex"])
]
