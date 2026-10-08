"""Batch 34 Part 3 question content (Frontend Developer). Targeted Gap Generation."""

ROLE = "Frontend Developer"

BUCKET_KEYS = {
    "WEB_PERFORMANCE_AND_API": ("Web Performance & APIs", "Network & Security", "Frontend", ["Frontend Developer", "Full Stack Developer"]),
}

Q = [
# ---------------- WEB_PERFORMANCE_AND_API ----------------
("WEB_PERFORMANCE_AND_API", "debug", "hard", "debugging", ["fetch", "Error Handling"],
 "You use native `fetch`. The backend throws a `500 Internal Server Error`. However, your frontend `catch(err)` block completely fails to execute, and the code proceeds into the `.then()` block, crashing the app. Why didn't `fetch` catch the 500 error?",
 "Unlike Axios, the native `fetch` API *does not* reject its Promise on HTTP error status codes (like 404 or 500). It only rejects on catastrophic network failures (like being offline or DNS failures). To handle HTTP errors, you must manually check `if (!response.ok)` inside the `.then()` block and explicitly `raise new Error()` to route it to `.catch()`.",
 ["Native `fetch` does not reject Promises on HTTP error statuses (404/500)", "It only rejects on physical network failures (offline/DNS)", "Fix: Must manually check `if (!response.ok)` and throw an Error inside the `.then()` block"],
 ["The 500 error was too large to fit in the catch block"]),

("WEB_PERFORMANCE_AND_API", "implement", "medium", "implementation", ["AbortController", "Race Conditions"],
 "You build an autocomplete search bar that fires a network request on every keystroke. How do you implement a mechanism to cancel previous, in-flight network requests so that only the final keystroke is processed, avoiding race conditions?",
 "You use an `AbortController`. Create a `new AbortController()`, pass its `signal` into the `fetch(url, { signal })` options, and store the controller in a ref. On a new keystroke, immediately call `controller.abort()` on the previous instance (canceling the old request and throwing an `AbortError`), then instantiate a new controller for the new request.",
 ["Use the `AbortController` API", "Pass the `signal` property into the `fetch` options", "Call `controller.abort()` on the previous request before initiating the new one"],
 ["Ask the server very nicely to ignore the previous requests"]),

("WEB_PERFORMANCE_AND_API", "tradeoff", "hard", "tradeoff", ["SSR vs SSG", "Core Web Vitals"],
 "When architecting a frontend, what is the exact tradeoff of using Server-Side Rendering (SSR) versus Static Site Generation (SSG) in terms of Core Web Vitals?",
 "SSG pre-builds HTML at compile time; it has an incredibly fast TTFB (Time to First Byte) and FCP because a CDN serves a static file instantly, but data can become stale. SSR builds HTML on-demand at runtime; it guarantees fresh data, but its TTFB and FCP are significantly slower because the server must execute DB queries and render the tree before sending bytes.",
 ["SSG: Lightning fast TTFB and FCP (served statically from CDN), but data can be stale", "SSR: Guarantees fresh data on every request", "SSR Tradeoff: Slower TTFB and FCP because the server must compute/render before sending bytes"],
 ["SSR is for React, SSG is for Angular"]),

("WEB_PERFORMANCE_AND_API", "scenario", "medium", "scenario", ["Security", "XSS"],
 "Your frontend stores a sensitive JWT token in `localStorage`. A marketing script injected via Google Tag Manager is compromised. What specific frontend security vulnerability did this architecture expose, and how should it have been architected?",
 "Storing sensitive tokens in `localStorage` exposes the application to Cross-Site Scripting (XSS). Any third-party JavaScript running on the page can freely read `localStorage` and exfiltrate the JWT. The architecture should have used `HttpOnly` Cookies. An `HttpOnly` cookie is automatically sent by the browser but is physically impossible to read via JavaScript.",
 ["Exposed to Cross-Site Scripting (XSS); JS can easily read `localStorage`", "Any compromised 3rd-party script can steal the JWT", "Fix: Store tokens in `HttpOnly` Cookies, which physically cannot be read by JavaScript"],
 ["The marketing script was just trying to sell the token to advertisers"]),

("WEB_PERFORMANCE_AND_API", "explain", "easy", "concept", ["Core Web Vitals", "CLS"],
 "In the context of Core Web Vitals, what does Cumulative Layout Shift (CLS) measure, and what is the most common cause?",
 "CLS measures visual stability—how much the page layout unexpectedly shifts while the user is reading or interacting. A high CLS is usually caused by images, ads, or iframes loading asynchronously without explicitly defined `width` and `height` attributes. When they finally load, they violently push the surrounding content down the page.",
 ["Measures visual stability (unexpected layout shifting)", "Common cause: Images/Ads loading asynchronously without explicit width/height attributes", "When they load, they push the surrounding content down the page, ruining the experience"],
 ["It measures how many times the user shifts in their chair while waiting"]),

("WEB_PERFORMANCE_AND_API", "debug", "hard", "debugging", ["CORS", "Preflight"],
 "You make a `fetch` POST to a different domain. The console shows a CORS error: `Response to preflight request doesn't pass access control`. The Network tab shows an `OPTIONS` request instead of a `POST`. Why did the browser change the method, and how do you fix it?",
 "The browser automatically sent an `OPTIONS` 'preflight' request because your `POST` was not a 'Simple Request' (e.g., you added an `Authorization` header or used `application/json`). The browser requires the destination server to explicitly approve custom headers first. You cannot fix this from the frontend; the backend server must be configured to respond to `OPTIONS`.",
 ["The browser sent an `OPTIONS` preflight because it was not a 'Simple Request' (e.g., custom headers)", "The browser requires the destination server to explicitly approve the request first", "Fix: The backend server must be configured to accept and respond to the `OPTIONS` request"],
 ["The browser decided to ask for options instead of posting data"]),

("WEB_PERFORMANCE_AND_API", "implement", "medium", "implementation", ["WebSockets", "Resilience"],
 "You build a real-time chat app. Users report that when they switch to a different browser tab and come back 5 minutes later, their WebSocket connection has silently died, missing messages. How do you implement resilience for this API?",
 "WebSockets frequently drop silently due to proxy timeouts or battery-saving tab throttling. You must implement a Heartbeat (ping/pong) mechanism to detect silent drops, and wrap the WebSocket in a reconnection loop with exponential backoff. Alternatively, listen to the browser's `visibilitychange` window event to proactively tear down and rebuild the connection.",
 ["Implement a Heartbeat (ping/pong) mechanism to detect silent drops", "Wrap the connection logic in a reconnect loop with exponential backoff", "Listen to `visibilitychange` to proactively rebuild the connection when the tab regains focus"],
 ["Tell the users to never switch tabs while chatting"]),

("WEB_PERFORMANCE_AND_API", "tradeoff", "medium", "tradeoff", ["Storage APIs", "IndexedDB vs localStorage"],
 "When caching data on the frontend, what is the architectural tradeoff of using `localStorage` versus `IndexedDB`?",
 "`localStorage` has a strict, tiny storage limit (~5MB), operates synchronously (blocking the main UI thread during reads/writes), and stores only primitive strings. `IndexedDB` offers massive storage limits (GBs), operates asynchronously (never blocking UI), and stores complex structured data (Blobs/Arrays) natively, but its API is notoriously complex to work with.",
 ["`localStorage`: Tiny limit (~5MB), synchronous (blocks UI thread), strings only", "`IndexedDB`: Massive limits (GBs), asynchronous (non-blocking), stores complex data (Blobs)", "Tradeoff: IndexedDB has a notoriously complex and difficult API"],
 ["`localStorage` is stored in the cloud, `IndexedDB` is on the hard drive"]),

("WEB_PERFORMANCE_AND_API", "scenario", "hard", "scenario", ["Performance", "Passive Event Listeners"],
 "You implement a 'Pull to Refresh' feature on mobile using `touchstart` and `touchmove` events. However, scrolling the page becomes noticeably choppy and laggy. What modern DOM API feature did you miss that caused this scroll jank?",
 "By default, the browser must wait for your `touchmove` listeners to finish executing before it can physically scroll the page, just in case you call `event.preventDefault()`. This waiting causes massive scroll jank. You must mark the listener as `passive: true`. This guarantees to the browser you will *not* cancel the scroll, allowing the Compositor thread to scroll instantly.",
 ["The browser waits for the listener to finish in case it calls `event.preventDefault()`", "Fix: Mark the event listener as `{ passive: true }`", "Allows the browser's Compositor thread to scroll instantly without waiting for JavaScript execution"],
 ["You pulled too hard and broke the refresh mechanism"]),

("WEB_PERFORMANCE_AND_API", "explain", "medium", "concept", ["Service Workers", "Offline Capabilities"],
 "What is a 'Service Worker' in modern frontend development, and what unique capability does it provide that standard Web Workers do not?",
 "A Service Worker is a specialized background script acting as a programmable network proxy between the browser and the internet. Unlike standard Web Workers (which just do heavy CPU math), Service Workers can intercept all outgoing HTTP requests, cache responses, and serve them from the cache even when the device is completely offline.",
 ["Acts as a programmable network proxy between the browser and the internet", "Can intercept HTTP requests and cache responses", "Uniquely enables offline capabilities, push notifications, and background sync (unlike standard Web Workers)"],
 ["A Service Worker is an employee who serves food at a restaurant"]),

("WEB_PERFORMANCE_AND_API", "debug", "medium", "debugging", ["Performance", "IntersectionObserver"],
 "You implement an 'Infinite Scroll' feed by attaching a listener to `window.onscroll`. As the user scrolls, the app becomes incredibly sluggish. You realize the event fires hundreds of times a second. How do you optimize this specific frontend pattern?",
 "You should completely remove the `scroll` event listener and replace it with the `IntersectionObserver` API. `IntersectionObserver` allows you to place a hidden 'sentinel' element at the bottom of the feed. The browser natively and efficiently monitors when this element enters the viewport, firing a single callback asynchronously without locking the main thread.",
 ["`window.onscroll` fires hundreds of times a second, locking the main thread with heavy math", "Fix: Use the `IntersectionObserver` API", "The browser natively monitors when a target element enters the viewport, firing a clean asynchronous callback"],
 ["Tell the user to scroll slower"]),

("WEB_PERFORMANCE_AND_API", "implement", "hard", "implementation", ["BroadcastChannel", "Cross-Tab Sync"],
 "A user opens your web app in three tabs simultaneously. When they log out in Tab A, Tabs B and C still show them as logged in. Without using WebSockets or a backend server, how do you instantly synchronize state across multiple tabs on the same origin?",
 "You use the `BroadcastChannel` API or the `storage` event. `BroadcastChannel` allows multiple tabs on the same origin to subscribe to a named channel and instantly push/receive JSON messages to each other. Alternatively, mutating `localStorage.setItem('auth', null)` in Tab A natively fires a `storage` window event in Tabs B and C, which can trigger a logout.",
 ["Use the `BroadcastChannel` API to send/receive messages between tabs on the same origin", "Alternatively, mutating `localStorage` fires a `storage` event in all other tabs", "Allows instant, purely client-side cross-tab synchronization without a backend"],
 ["Use a very loud beep to notify the other tabs"]),

("WEB_PERFORMANCE_AND_API", "tradeoff", "easy", "tradeoff", ["Performance", "Lazy Loading"],
 "In image loading optimization, what is the tradeoff of using 'Lazy Loading' (`loading=\"lazy\"`) versus standard eager loading?",
 "Lazy loading prevents the browser from downloading images that are currently off-screen, drastically saving bandwidth, CPU, and speeding up initial page load. The tradeoff is that as the user scrolls rapidly, they may see blank spaces or placeholders while the images scramble to download just-in-time. (Also, lazy loading LCP images degrades performance metrics).",
 ["Saves massive bandwidth and speeds up initial page load by ignoring off-screen images", "Tradeoff: Rapid scrolling can reveal blank spaces while images download just-in-time", "Tradeoff: Lazy loading Above-the-Fold images destroys LCP (Largest Contentful Paint) metrics"],
 ["Lazy loading makes the images look tired and sleepy"]),

("WEB_PERFORMANCE_AND_API", "scenario", "medium", "scenario", ["Security", "CSRF"],
 "Your frontend is vulnerable to CSRF. A malicious site automatically submits a hidden `<form>` POST to your bank's `/transfer` API. Because the user is logged in, their browser attaches session cookies, executing the transfer. How do you mitigate this purely using modern cookie attributes?",
 "You must set the `SameSite` attribute on your authentication cookies. Setting `SameSite=Strict` or `SameSite=Lax` instructs the browser to actively refuse to send the cookie if the HTTP request originates from a completely different domain (the malicious site). Without the session cookie attached, the backend rejects the forged request as unauthorized.",
 ["Set the `SameSite` attribute on the authentication cookie (`Strict` or `Lax`)", "The browser will refuse to send the cookie if the request originates from a 3rd-party domain", "Without the cookie, the forged request is rejected by the backend"],
 ["Ask the malicious site politely to stop submitting forms"]),

("WEB_PERFORMANCE_AND_API", "explain", "hard", "concept", ["Security", "CSP"],
 "What is Content Security Policy (CSP), and how does it protect a frontend application?",
 "CSP is an HTTP response header (or `<meta>` tag) that enforces a strict whitelist of trusted origins and behaviors for the frontend. It dictates exactly where the browser is allowed to load scripts, images, or styles from. Crucially, it can outright ban the execution of inline `<script>` tags or `eval()`, completely neutralizing XSS attacks even if code is successfully injected.",
 ["An HTTP header/meta tag enforcing a strict whitelist of trusted origins and behaviors", "Dictates exactly where scripts, images, and styles can be loaded from", "Neutralizes XSS by banning inline `<script>` execution and `eval()`, even if injection succeeds"],
 ["It is a police force that arrests bad HTML tags"]),

("WEB_PERFORMANCE_AND_API", "debug", "medium", "debugging", ["Deployment", "Cache Invalidation"],
 "You deploy a new version of your SPA. The `index.html` is cached by the CDN for 24 hours. Users load the page, but when they click a link to navigate to a new route, the app crashes, saying 'Chunk not found'. What happened with the deployment?",
 "This is a Webpack/Vite chunk hashing error. The user downloaded the cached `index.html` from yesterday, which references yesterday's JavaScript chunk filenames (`app.v1.js`). When you deployed, the bundler generated new chunk filenames (`app.v2.js`) and deleted the old ones. The router attempted to lazy-load a deleted chunk. Fix: Never cache `index.html`.",
 ["The user is running a cached `index.html` referencing old chunk filenames", "The deployment deleted the old chunks and created new ones (`app.v2.js`)", "Fix: Configure the server/CDN to never cache the `index.html` file (`Cache-Control: no-cache`)"],
 ["The chunks were eaten by a hungry browser extension"])
]
