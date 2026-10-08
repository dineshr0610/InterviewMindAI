"""Batch 34 Part 2 question content (Frontend Developer). Targeted Gap Generation."""

ROLE = "Frontend Developer"

BUCKET_KEYS = {
    "REACT_ARCHITECTURE": ("Component Architecture", "Design Patterns", "React", ["Frontend Developer", "Full Stack Developer"]),
}

Q = [
# ---------------- REACT_ARCHITECTURE ----------------
("REACT_ARCHITECTURE", "debug", "hard", "debugging", ["Memoization", "Referential Equality"],
 "You wrap a child component in `React.memo()`. You pass an object prop: `<Child config={{ showIcons: true }} />`. The React DevTools profiler shows the child is still re-rendering every time the parent renders. Why did memoization fail?",
 "Memoization relies on a shallow equality check (`===`). Because you pass an inline object literal `{{ showIcons: true }}`, a brand new object reference is created in memory on every single parent render. `React.memo` sees the new reference, assumes props changed, and re-renders. Fix: Move the static object outside the component or wrap it in `useMemo`.",
 ["Passed an inline object literal, creating a new memory reference on every render", "`React.memo` uses shallow equality (`===`); it sees a new reference and triggers a re-render", "Fix: Move the object outside the component or wrap it in `useMemo`"],
 ["`React.memo` is deprecated and broken in the latest version"]),

("REACT_ARCHITECTURE", "implement", "medium", "implementation", ["State Management", "Co-location"],
 "You are building a complex form. When typing into a text input, the entire page (including heavy charts) lags. You realize the `onChange` handler is updating state at the very top of the component tree. How do you architecturally fix this?",
 "This is caused by state being lifted too high. Updating state at the top of the tree forces React to recursively re-render every descendant component on every keystroke. You fix this by 'co-locating' state: move the `value` state and the text input down into its own isolated, dedicated child component. Now, only that tiny component re-renders.",
 ["State lifted too high forces the entire application tree to re-render on every keystroke", "Fix by 'co-locating' state: move the state and input into an isolated child component", "Ensures only the specific input component re-renders during typing"],
 ["Add a `setTimeout` to the typing so it only renders every 5 seconds"]),

("REACT_ARCHITECTURE", "tradeoff", "hard", "tradeoff", ["Context API", "Global State"],
 "When managing global state, what is the architectural tradeoff between using native React Context API versus a dedicated state manager like Redux or Zustand?",
 "React Context is excellent for dependency injection (passing static themes/auth tokens deep into the tree). Tradeoff: any time the Context value changes, *every* component consuming it is forced to re-render. Redux/Zustand allow fine-grained subscriptions, ensuring components only re-render if the exact slice of state they care about changes.",
 ["Context API: Excellent for dependency injection (avoiding prop drilling) for static/rarely changing data", "Context Tradeoff: No fine-grained subscriptions; *all* consumers re-render when the value changes", "Redux/Zustand: Allow fine-grained subscriptions, preventing unnecessary re-renders for high-frequency state"],
 ["Redux is built into the browser, Context requires an npm install"]),

("REACT_ARCHITECTURE", "scenario", "medium", "scenario", ["useEffect", "Memory Leaks"],
 "A React component fetches data on mount (`useEffect(..., [])`). A bug report states that if the user quickly navigates away before the fetch completes, the app crashes with a memory leak warning. What did you fail to handle?",
 "You failed to provide a cleanup function to handle unmounting. When the asynchronous fetch finally resolves, the `.then()` block attempts to call `setState` on a component that has already been destroyed by the router. You must return a cleanup function from the `useEffect` that aborts the fetch (via `AbortController`) or sets a local `isMounted` flag.",
 ["Failed to provide a cleanup function for the asynchronous fetch", "The promise resolves and attempts to `setState` on an unmounted component", "Fix: Return a cleanup function that aborts the fetch (via `AbortController`) or sets an `isMounted` flag"],
 ["You forgot to tell the server the user left the page"]),

("REACT_ARCHITECTURE", "explain", "easy", "concept", ["Automatic Batching", "Performance"],
 "In React 18, what is 'Automatic Batching'?",
 "Before React 18, React only batched state updates inside native React event handlers (like `onClick`). State updates inside Promises, setTimeout, or native DOM events triggered separate, sequential re-renders. In React 18, Automatic Batching groups *all* state updates (regardless of origin) into a single re-render, significantly improving performance.",
 ["React 18 groups multiple state updates into a single re-render", "Previously, only native React event handlers were batched", "Now includes updates inside Promises, `setTimeout`, and native DOM events"],
 ["It automatically batches HTTP requests into a single network call"]),

("REACT_ARCHITECTURE", "debug", "hard", "debugging", ["useEffect", "Infinite Loops"],
 "A custom hook `useFetch(url)` gets stuck in an infinite loop, spamming the API. The hook uses `useEffect(() => fetch(url).then(setData), [options])`, where `options` is an object passed from the component. Why did this loop?",
 "The component is passing a new inline object reference (e.g., `useFetch(url, { method: 'GET' })`) on every render. The `useEffect` dependency array checks referential equality, sees a 'new' dependency, fetches data, calls `setData`, and triggers a re-render. The re-render creates a brand new `options` object, starting the loop over. Fix: `useMemo` the options.",
 ["Passing a new inline object reference creates a new memory address on every render", "`useEffect` dependency array fails the shallow equality check, triggering the effect", "The effect updates state, triggering a re-render, creating a new object, causing an infinite loop"],
 ["The API server is sending a response that asks for more requests"]),

("REACT_ARCHITECTURE", "implement", "medium", "implementation", ["Lists", "Keys"],
 "You build an e-commerce cart. When a user deletes a `<CartItem>` from the middle of the list, the wrong item disappears visually, and state becomes corrupted. What critical React rule did you violate?",
 "You likely used the array `index` as the `key` prop when mapping the items. When an item is deleted from the middle, the indices of all subsequent items shift. React uses keys to identify DOM elements; it sees the keys are intact but the data shifted, causing it to incorrectly recycle and re-render the wrong DOM nodes. You must use a unique identifier (like `item.id`).",
 ["Used the array `index` as the `key` prop", "Deleting an item shifts indices, causing React to mismatch DOM nodes with state", "Fix: Use a stable, unique identifier (like database `id`) for the `key` prop"],
 ["You forgot to call `window.location.reload()` after deleting the item"]),

("REACT_ARCHITECTURE", "tradeoff", "medium", "tradeoff", ["Performance", "Web Workers vs useMemo"],
 "When filtering 50,000 records on the client, what is the tradeoff of using React's `useMemo` versus offloading the work to a Web Worker?",
 "`useMemo` caches the result, but when it *does* run, it executes synchronously on the main UI thread, completely freezing the browser (blocking scrolling/typing). A Web Worker executes the calculation in a separate OS thread in the background, keeping the UI perfectly responsive. Tradeoff: Web Workers require complex asynchronous messaging (postMessage).",
 ["`useMemo` runs synchronously on the main thread, freezing the UI for heavy calculations", "Web Workers run in a separate background thread, keeping the UI perfectly responsive", "Tradeoff: Web Workers require complex asynchronous IPC (postMessage) and serialization"],
 ["Web Workers cost money, `useMemo` is free"]),

("REACT_ARCHITECTURE", "scenario", "hard", "scenario", ["React Server Components", "Next.js"],
 "You are using React Server Components (RSC) in Next.js App Router. You try to use `useState` and an `onClick` handler in a child component, but the compiler throws an error. Why?",
 "React Server Components execute entirely on the server and never ship JavaScript to the client. Because they run on the server, they physically cannot have interactive DOM event listeners (`onClick`) or client-side lifecycle state (`useState`). To add interactivity, you must declare the component as a Client Component by adding the `\"use client\"` directive at the top.",
 ["React Server Components run exclusively on the server and ship no JS to the client", "They physically cannot support DOM events (`onClick`) or client lifecycle hooks (`useState`)", "Fix: Add the `\"use client\"` directive to explicitly mark it as a Client Component"],
 ["The server doesn't have a mouse to click on things"]),

("REACT_ARCHITECTURE", "explain", "medium", "concept", ["Strict Mode", "Development"],
 "What is the purpose of React's 'Strict Mode', and why does it purposefully call your components twice in development?",
 "Strict Mode is a development-only tool designed to highlight potential architectural problems. It purposefully double-invokes function components, state updaters, and `useEffect` hooks to aggressively expose subtle bugs related to impure functions, missing cleanup functions, or mutable side effects. It guarantees that if a component is not pure, it will visibly break in development.",
 ["A development-only tool to highlight potential architectural problems", "Purposefully double-invokes components, effects, and updaters", "Aggressively exposes impure functions, side effects, and missing cleanups"],
 ["It forces developers to write code twice to build muscle memory"]),

("REACT_ARCHITECTURE", "debug", "medium", "debugging", ["State Closures", "Functional Updaters"],
 "A junior writes: `setCount(count + 1); setCount(count + 1);`. They expect the count to increase by 2, but it only increases by 1. Why did the first state update seemingly disappear?",
 "State updates in React are asynchronously batched and evaluated based on the closure's captured value of `count` at the time the render began. Both functions see the exact same original `count` value (e.g., 0) and both evaluate to `setCount(1)`. To increment it sequentially based on previous state, they must use the functional updater: `setCount(prev => prev + 1);`.",
 ["State updates are batched and rely on the closure's captured value of `count` during that render", "Both calls see the same initial value and overwrite each other", "Fix: Use the functional updater pattern `setCount(prev => prev + 1)`"],
 ["React assumes you made a typo and ignores the second command"]),

("REACT_ARCHITECTURE", "implement", "hard", "implementation", ["Portals", "DOM Hierarchy"],
 "A deep child component triggers a full-page modal. Rendering the modal deep in the DOM tree breaks its layout due to ancestor CSS (`overflow: hidden` or `z-index`). What React feature solves this architectural problem?",
 "You use React Portals (`ReactDOM.createPortal()`). Portals allow you to render the modal's physical DOM node directly into the `<body>` element (escaping all ancestor CSS constraints), while allowing the React component itself to remain logically located deep inside the React tree. This preserves React context, event bubbling, and state management.",
 ["Use React Portals (`ReactDOM.createPortal()`)", "Renders the physical DOM node directly into the `<body>` element to escape ancestor CSS constraints", "Preserves the logical React tree location for Context, state, and event bubbling"],
 ["Use `iframe` to load the modal in a separate browser window"]),

("REACT_ARCHITECTURE", "tradeoff", "easy", "tradeoff", ["Testing", "RTL vs Enzyme"],
 "In React testing, what is the tradeoff of using 'Shallow Rendering' (Enzyme) versus 'DOM Testing' (React Testing Library)?",
 "Shallow rendering isolates the component by refusing to render children. It makes tests fast but heavily tests implementation details (state variables) rather than user behavior. React Testing Library renders the full DOM tree and forces querying exactly as a user would (by text/ARIA). RTL is slightly slower, but yields vastly higher confidence that the app actually works.",
 ["Shallow Rendering: Fast, but tests implementation details (internal state/methods)", "DOM Testing (RTL): Renders full tree, tests actual user behavior (ARIA/text queries)", "RTL provides vastly higher confidence that the application works for the end user"],
 ["Shallow testing only tests the top half of the screen"]),

("REACT_ARCHITECTURE", "scenario", "medium", "scenario", ["TypeScript", "children prop"],
 "You migrate a large React codebase to TypeScript. A component accepts a `children` prop. How do you correctly type the `children` prop to accept any valid React renderable content?",
 "You should type the `children` prop as `React.ReactNode`. `ReactNode` is the most permissive and correct type; it encompasses everything React can legally render: JSX elements, strings, numbers, arrays, fragments, booleans, and null. Using `JSX.Element` or `React.ReactElement` is too restrictive, as they reject primitive strings and numbers.",
 ["Type it as `React.ReactNode`", "`ReactNode` encompasses everything React can render (elements, strings, numbers, arrays, null)", "`JSX.Element` or `ReactElement` is too restrictive and rejects primitives"],
 ["Type it as `any` and hope for the best"]),

("REACT_ARCHITECTURE", "explain", "hard", "concept", ["SSR", "Hydration"],
 "What is 'Hydration' in the context of Server-Side Rendered (SSR) React applications?",
 "In SSR, the server generates and sends raw, static HTML so the user sees the page immediately. However, this HTML has no interactivity (no event listeners). Hydration is the subsequent client-side process where React boots up, walks the existing static DOM tree, and attaches the necessary JavaScript event handlers and state, 'hydrating' the dead HTML into a live SPA.",
 ["The server sends raw, static HTML for immediate visual rendering", "The static HTML has no JavaScript event listeners attached", "Hydration is the client-side process where React attaches event handlers and state to the existing DOM tree"],
 ["It is when you make sure the server has enough water cooling"]),

("REACT_ARCHITECTURE", "debug", "medium", "debugging", ["useRef", "Rendering"],
 "You use `const clicks = useRef(0)`. On button click, you do `clicks.current += 1` and display `{clicks.current}` in JSX. The screen always shows 0, though logs show the value increasing. Why?",
 "Mutating the `.current` property of a `useRef` object is completely synchronous and *does not* trigger a React re-render. Because no re-render is triggered, the JSX never updates to reflect the new value. `useRef` is strictly for storing mutable data that does *not* affect visual output. For visual data, you must use `useState`.",
 ["Mutating a `useRef` object does NOT trigger a React re-render", "Because there is no re-render, the JSX is never updated on the screen", "`useRef` is for non-visual data; use `useState` for anything rendered in JSX"],
 ["The screen freezes to protect the user from too many clicks"]),

("REACT_ARCHITECTURE", "fundamentals", "easy", "concept", ["Error Boundaries", "Resilience"],
 "What is a React 'Error Boundary'?",
 "An Error Boundary is a specialized component that catches JavaScript errors occurring anywhere in its child component tree during rendering or lifecycle methods. Instead of allowing the error to crash the entire application (displaying a blank white screen), the Error Boundary catches it and renders a fallback UI (like an error message). Currently, they require Class components.",
 ["Catches JavaScript errors occurring anywhere in its child component tree", "Prevents the error from crashing the entire application (blank white screen)", "Renders a graceful fallback UI instead"],
 ["A physical boundary drawn on the monitor to keep errors contained"])
]
