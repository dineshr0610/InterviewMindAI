"""Batch 24 Part 2 question content (Frontend Developer). Targeted Gap Generation."""

ROLE = "Frontend Developer"

BUCKET_KEYS = {
    "FE_BROWSER_API": ("Browser APIs", "Workers & Observers", "Web APIs", ["Full Stack Developer", "Software Engineer"]),
}

Q = [
("FE_BROWSER_API", "debug", "medium", "debugging", ["CORS"],
 "You attempt to fetch data from an external API `https://api.example.com/data` using the Fetch API. The browser blocks the request and throws a CORS error. You do not control the backend server. Can you bypass this CORS error using purely client-side browser JavaScript?",
 "No. Cross-Origin Resource Sharing (CORS) is a fundamental browser security mechanism enforced locally by the browser, not the server. If the external server does not return the explicit `Access-Control-Allow-Origin` headers authorizing your domain, the browser will strictly block your JavaScript code from reading the response. You cannot bypass this using client-side JS; you must route the request through a backend proxy server that you control.",
 ["CORS is enforced by the browser as a fundamental security mechanism", "Cannot be bypassed using purely client-side JS", "Must route the request through a backend proxy server that you control"],
 ["Just use `mode: no-cors` to read the data anyway"]),

("FE_BROWSER_API", "tradeoff", "medium", "tradeoff", ["Fetch vs XHR"],
 "What are the performance tradeoffs of using the native `fetch()` API to download a large 100MB file versus using `XMLHttpRequest` (XHR)?",
 "`fetch()` natively supports Streams via the `ReadableStream` API, allowing you to process and render chunks of the file as they arrive over the network without ever loading the entire 100MB into memory. XHR requires buffering the entire response payload into memory before it can be accessed by JavaScript. However, XHR historically provides native, precise upload progress events, which fetch lacks without complex workarounds.",
 ["`fetch` supports Streams (`ReadableStream`), allowing chunk processing without loading the whole file into RAM", "XHR buffers the entire response payload into memory before it can be used", "XHR tradeoff: Natively supports precise upload progress events (which fetch lacks natively)"],
 ["Fetch is 100x faster than XHR"]),

("FE_BROWSER_API", "implement", "hard", "implementation", ["Clipboard API"],
 "You need to implement a 'Copy to Clipboard' button. The legacy `document.execCommand('copy')` is deprecated. How do you implement this using modern asynchronous APIs, and what browser security restriction must you handle?",
 "You use the modern `navigator.clipboard.writeText(string)` API, which returns a Promise. The strict browser security restriction is that this API can only be invoked within a 'transient user activation' context. This means the code must be executed directly and synchronously in response to a genuine user interaction event, like a `click` or `keydown`. You cannot trigger it programmatically in the background.",
 ["Use `navigator.clipboard.writeText(string)` which returns a Promise", "Must be invoked within a 'transient user activation' context", "Cannot be triggered programmatically; must be a direct result of a user click/interaction"],
 ["Write it to `localStorage` and rename the file"]),

("FE_BROWSER_API", "scenario", "medium", "scenario", ["Memory Leaks"],
 "Your web application frequently uses `console.log` to print massive nested JSON objects during development. You forget to remove them in production. Even if the user never opens the DevTools, how can these hidden `console.log` statements cause a massive memory leak in the browser?",
 "When you pass a JavaScript object to `console.log()`, the browser's JavaScript engine must maintain a strong internal reference to that object in memory just in case the user decides to open the DevTools later to inspect it. Because this strong reference exists, the Garbage Collector is completely prevented from freeing those objects, silently leaking massive amounts of memory in the background.",
 ["The browser engine maintains a strong internal reference to objects logged to the console", "Ensures they are available for inspection if DevTools is opened later", "This prevents the Garbage Collector from freeing the objects, causing a silent leak"],
 ["Console logs are sent to a remote server, consuming bandwidth"]),

("FE_BROWSER_API", "explain", "easy", "concept", ["Page Lifecycle"],
 "What does the `visibilitychange` event on the `document` object detect, and why is it preferred over `unload` or `beforeunload` for saving application state?",
 "The `visibilitychange` event detects when the page content becomes visible or hidden to the user (e.g., switching tabs, minimizing the browser, or locking the phone screen). It is preferred because modern mobile operating systems frequently pause, freeze, or outright kill background browser tabs without ever firing the traditional `unload` or `beforeunload` events, making `visibilitychange` the only guaranteed, reliable lifecycle hook for saving state.",
 ["Detects when the page is hidden or shown (e.g., tab switching or minimizing)", "Preferred because mobile OSs frequently kill background tabs without firing `unload`", "It is the only reliable lifecycle hook for saving state before a tab is discarded"],
 ["It detects when the user closes their eyes"])
]
