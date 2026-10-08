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

ROLE = "Frontend Developer"
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
    # Bucket 1: WEB WORKERS / SERVICE WORKERS AT SCALE
    ("B1", "scenario", "hard", "scenario", ["Service Workers"], "A service worker is updated with new assets, but users complain they still see the old application shell unless they close all browser tabs. How do you architect a 'skip waiting' flow to fix this safely?", "By default, a new Service Worker installs but remains in a 'waiting' state until all browser tabs controlled by the old worker are completely closed. To fix this, the new worker must call `self.skipWaiting()`. However, doing this blindly can break the running app if assets are swapped mid-session. The safe architecture is to prompt the user with an 'Update Available' banner, and when they click it, post a message (`postMessage({ type: 'SKIP_WAITING' })`) to the worker, followed by `window.location.reload()` on the client once the controller changes.", ["Service workers wait for old tabs to close by default", "Use self.skipWaiting() via a user prompt", "postMessage to trigger the skip, then reload the client"], ["Service workers update instantly automatically"]),
    ("B1", "optimize", "medium", "optimize", ["Web Workers"], "You are offloading the parsing of a massive 50MB JSON payload to a Web Worker. However, the main thread still freezes for several seconds during the `postMessage` transfer. Why does this happen, and how can you optimize it?", "By default, `postMessage` uses the Structured Clone algorithm, which synchronously copies the entire data structure. For a 50MB object, this serialization/deserialization CPU cost blocks the main thread. To fix it, you should fetch the data as an `ArrayBuffer` and pass it as a 'Transferable Object' in the second argument of `postMessage`. This transfers memory ownership instantly with zero-copy overhead, eliminating the freeze.", ["Structured Clone algorithm copies data synchronously", "Use ArrayBuffer as a Transferable Object", "Zero-copy ownership transfer avoids main thread blocking"], ["Web Workers are single threaded so they block the main thread"]),
    ("B1", "tradeoff", "medium", "tradeoff", ["Service Workers"], "In a Service Worker, what is the exact tradeoff between using a 'Cache First' strategy versus a 'Stale-While-Revalidate' strategy for an application's CSS and JS assets?", "A 'Cache First' strategy checks the Cache API and only goes to the network if the asset is missing. It provides maximum speed and offline capability but risks serving deeply stale assets unless file hashing/cache-busting is perfectly implemented. 'Stale-While-Revalidate' instantly serves the cached asset (for speed) but silently fetches the latest version in the background and updates the cache for the *next* visit. This ensures eventual consistency but uses more network bandwidth.", ["Cache First: maximum speed but risks permanent staleness", "Stale-While-Revalidate: fast initial load, updates cache in background", "Eventual consistency vs guaranteed freshness"], ["Cache First deletes the network cache"]),
    ("B1", "architecture", "hard", "architecture", ["Web Workers"], "If you need a Web Worker to manage a WebSocket connection and share that single connection across multiple open tabs of the same origin, what technology must you use and what is the primary lifecycle constraint?", "You must use a `SharedWorker`. A standard Web Worker is dedicated to a single script execution context (one tab). A SharedWorker can be accessed by multiple windows, iframes, or tabs on the same origin. The primary lifecycle constraint is that a SharedWorker only stays alive as long as at least one tab is actively connected to it. If all tabs close, the SharedWorker and its WebSocket connection are immediately terminated by the browser.", ["SharedWorker allows cross-tab sharing", "Standard workers are dedicated to one tab", "Terminates when the last connected tab is closed"], ["Use a Service Worker to manage WebSockets"]),
    ("B1", "diagnose", "medium", "debugging", ["Service Workers"], "A Service Worker attempts to use `localStorage` to cache a user preference, but it immediately throws an error. Why does this happen, and what is the correct storage API to use?", "A Service Worker executes in a completely separate, background thread isolated from the DOM and window context. `localStorage` is a synchronous, blocking API tied directly to the main thread's `window` object, so it is deliberately unavailable inside Service Workers. The correct API to use is `IndexedDB`, which is asynchronous and fully accessible within the worker context.", ["localStorage is synchronous and main-thread only", "Service Workers cannot access the DOM or window object", "Must use IndexedDB for asynchronous storage"], ["localStorage is limited to 5MB"]),
    ("B1", "scenario", "medium", "scenario", ["Service Workers"], "Your Progressive Web App (PWA) needs to guarantee that a user's analytical event is sent to the server even if they close the browser tab or go offline while the request is pending. How do you implement this?", "You should use the Background Sync API. In the main thread, you register a sync event (`navigator.serviceWorker.ready.then(sw => sw.sync.register('send-analytics'))`). In the Service Worker, you listen for the `sync` event. If the network is available, the event fires immediately; if offline, the browser safely queues the event and automatically wakes up the Service Worker to fire the event as soon as connectivity is restored, even if the user has closed the tab.", ["Background Sync API", "Registers a sync event in the Service Worker", "Browser queues and automatically retries when online"], ["Use a setTimeout loop in the main thread"]),
    ("B1", "optimize", "hard", "optimize", ["Web Workers"], "You are building a client-side video processing app. Spinning up a new Web Worker for every frame causes massive memory pressure and GC spikes. How do you re-architect this?", "Creating and destroying Web Workers carries significant OS and memory overhead. Instead of creating a worker per task, you should implement a Worker Pool. You instantiate a fixed number of workers (e.g., matching `navigator.hardwareConcurrency`) at startup. You then maintain a queue of frames and pass messages to idle workers in the pool. When a worker finishes a frame, it posts the result back and signals it is ready for the next item in the queue, completely eliminating worker instantiation overhead.", ["Worker instantiation has high memory/OS overhead", "Implement a fixed-size Worker Pool", "Reuse workers via a message queue (hardwareConcurrency)"], ["Web Workers are garbage collected instantly"]),
    ("B1", "explain", "easy", "concept", ["Service Workers"], "What happens to a Service Worker's execution state when it is idle for an extended period, and how does this affect global variables stored inside the worker script?", "To preserve device battery and memory, the browser aggressively terminates Service Workers when they are idle (usually after a few seconds). When a new event (like a fetch or push notification) occurs, the browser spins the worker back up. Because of this constant death-and-rebirth lifecycle, you cannot rely on global variables in the worker script to persist state; all persistent state must be written to `IndexedDB` or the Cache API.", ["Browser aggressively terminates idle service workers", "Workers are constantly killed and restarted", "Global variables are lost; must use IndexedDB/Cache API"], ["Service workers run forever in the background"]),
    ("B1", "diagnose", "medium", "debugging", ["Service Workers"], "You use Workbox to precache a 10MB `main.js` file. You deploy an update, the new Service Worker installs, but users complain that `main.js` is failing to download, resulting in a blank screen. You check the Workbox manifest and the file hash changed, but the server uses a strict `Cache-Control: max-age=31536000` header on that file. What went wrong?", "The Service Worker's `install` event attempted to fetch the newly hashed `main.js` to populate the new precache. However, because the server issued a 1-year `Cache-Control` header, the *browser's* HTTP cache intercepted the fetch and returned the old, stale version instead of hitting the network. Workbox checked the hash of the downloaded file, realized it didn't match the new manifest hash, and aborted the installation. You must configure the server to not cache hashed assets, or configure Workbox to bypass the HTTP cache.", ["Browser HTTP cache intercepted the Service Worker fetch", "Workbox hash validation failed on the stale file", "Server must not heavily cache dynamically hashed assets"], ["Workbox has a 5MB precache limit"]),
    ("B1", "architecture", "medium", "architecture", ["Web Workers"], "If you have a complex React application and you want to move the entire state management (e.g., Redux store) into a Web Worker, what is the primary performance bottleneck you must design around?", "The primary bottleneck is the asynchronous serialization serialization cost across the `postMessage` boundary. Every state update and every UI subscription notification must be serialized, sent across the thread boundary, and deserialized. For highly frequent, granular state changes (like mouse tracking or rapid keystrokes), the serialization overhead can actually exceed the cost of just running the state management on the main thread. You must design the architecture to batch state updates or only send diffs.", ["postMessage serialization/deserialization overhead", "Frequent granular updates cause heavy cross-thread traffic", "Must batch updates or send diffs to mitigate overhead"], ["Web Workers cannot use Redux"]),

    # Bucket 2: SPECIALIZED ACCESSIBILITY / A11Y
    ("B2", "implement", "hard", "implementation", ["Accessibility"], "You are building a custom accessible Grid component. Instead of making every single cell focusable via the Tab key, which would force keyboard users to press Tab 100 times to pass the grid, what keyboard navigation pattern should you implement?", "You should implement a 'Roving tabindex'. You set `tabindex=\"0\"` on only one active cell in the grid, and `tabindex=\"-1\"` on all other cells. When the user tabs into the grid, they land on the active cell. From there, you listen for Arrow Key events. When an arrow key is pressed, you programmatically change the current cell to `-1`, change the new target cell to `0`, and call `.focus()` on the new cell. This allows internal navigation via arrows while keeping the grid as a single tab stop.", ["Roving tabindex", "Only one element has tabindex='0', the rest '-1'", "Use Arrow keys to update tabindex and call .focus()"], ["Set tabindex='1' on everything"]),
    ("B2", "diagnose", "medium", "debugging", ["Accessibility"], "A React Single Page Application (SPA) relies on client-side routing. When a user clicks a link, the URL changes and the view updates instantly. However, blind users using screen readers report that nothing happens when they click links. How do you fix this?", "In an SPA, the browser does not perform a full page reload, so the screen reader is never alerted that the page content has changed, and focus remains on the clicked link. To fix this, upon a successful route transition, you must manually manage focus. You should shift programmatic focus to a primary heading (`<h1>`) on the new page, or to a visually hidden `aria-live` region that announces the new page title.", ["SPA transitions do not trigger screen reader page-load announcements", "Must manually manage focus on route change", "Shift focus to an <h1> or use an aria-live region"], ["Screen readers don't support React"]),
    ("B2", "tradeoff", "medium", "tradeoff", ["Accessibility"], "When building a dynamic notification toast system, what is the difference in screen reader behavior when assigning `aria-live=\"polite\"` versus `aria-live=\"assertive\"`?", "`aria-live=\"polite\"` tells the screen reader to wait until it finishes speaking its current sentence or the user stops typing before announcing the new notification. It is used for non-critical updates. `aria-live=\"assertive\"` tells the screen reader to instantly interrupt whatever it is currently saying to announce the new text immediately. It should be reserved strictly for critical, time-sensitive errors or alerts.", ["Polite waits for the current speech to finish", "Assertive immediately interrupts current speech", "Assertive is for critical errors only"], ["Polite lowers the volume, Assertive raises the volume"]),
    ("B2", "architecture", "hard", "architecture", ["Accessibility"], "You are implementing an infinite-scrolling virtualized list (rendering only 20 DOM nodes for a list of 10,000 items). Why does this completely break native screen reader list announcements, and how do you fix it with ARIA?", "Native screen readers rely on the DOM size to announce list metrics (e.g., 'Item 1 of 20'). Because the virtualizer removes nodes, the screen reader thinks the entire list is only 20 items long, confusing the user. To fix this, you must apply `aria-setsize=\"10000\"` to the container or list items, and `aria-posinset=\"{actual_index}\"` to each currently rendered item, explicitly telling the screen reader the true scale and position of the items despite the DOM limitations.", ["Virtualization removes nodes, breaking native DOM list counts", "Use aria-setsize to declare the total list length", "Use aria-posinset to declare the current item's exact position"], ["Just render all 10,000 nodes invisibly"]),
    ("B2", "diagnose", "medium", "debugging", ["Accessibility"], "You build a custom modal dialog. A keyboard user presses Tab to navigate through the modal's buttons, but when they reach the last button and press Tab again, their focus moves to a link hidden *behind* the modal overlay. How do you implement a 'Focus Trap' to prevent this?", "You must implement a Focus Trap by intercepting the `keydown` event on the modal. If the key is 'Tab', you check if `document.activeElement` is the last focusable element in the modal. If it is, you call `event.preventDefault()` and manually move `.focus()` back to the first focusable element in the modal. You must also handle `Shift+Tab` to wrap focus from the first element back to the last element.", ["Intercept the Tab keydown event", "If on the last element, preventDefault and focus the first element", "Handle Shift+Tab for reverse direction"], ["Use CSS pointer-events: none on the background"]),
    ("B2", "implement", "easy", "implementation", ["Accessibility"], "Your website features heavy parallax animations and spinning loaders. Some users experience vestibular motion sickness. How do you respect their OS-level accessibility preferences in your CSS?", "You use the `prefers-reduced-motion` media query. By writing `@media (prefers-reduced-motion: reduce)`, you can specifically target users who have requested less motion and override your animations. Typically, this involves setting `animation: none`, `transition: none`, or replacing complex spinning loaders with simple fading or static indicators.", ["Use the prefers-reduced-motion media query", "Target OS-level accessibility settings", "Disable or simplify animations and transitions"], ["Use JavaScript to detect their mouse speed"]),
    ("B2", "compare", "medium", "compare", ["Accessibility"], "What is the critical accessibility difference between applying `display: none` in CSS versus applying `aria-hidden=\"true\"` in HTML?", "`display: none` removes the element entirely from both the visual rendering tree and the Accessibility Tree; neither sighted users nor screen readers can interact with it. `aria-hidden=\"true\"` removes the element *only* from the Accessibility Tree. The element remains fully visible on the screen and occupies layout space, but screen readers will completely ignore it. It is used to hide decorative visual elements (like icon fonts) from screen readers.", ["display: none removes from visual layout AND accessibility tree", "aria-hidden='true' hides from screen readers but remains visually visible", "aria-hidden is used for decorative visual elements"], ["They do exactly the same thing"]),
    ("B2", "diagnose", "medium", "debugging", ["Accessibility"], "You build a complex custom drag-and-drop Kanban board. A blind user cannot use a mouse to drag the cards. How do you architect an accessible, keyboard-only drag-and-drop experience?", "You must make the draggable cards focusable (`tabindex=\"0\"`). When focused, you use `aria-describedby` to provide instructions (e.g., 'Press Space to lift, Arrows to move, Space to drop'). You listen for the Spacebar `keydown` event to toggle an internal 'grabbed' state (updating `aria-grabbed` or `aria-roledescription`). You then listen for Arrow keys to programmatically move the card across columns, using an `aria-live` region to announce the card's new position on every move.", ["Make cards focusable and provide instructions via aria-describedby", "Use Spacebar to toggle grabbed state", "Use Arrow keys to move and aria-live to announce new positions"], ["Drag and drop cannot be made accessible"]),
    ("B2", "explain", "medium", "concept", ["Accessibility"], "What is the 'Accessibility Tree', and how does it relate to the DOM?", "The Accessibility Tree is a parallel structure generated by the browser based on the DOM. While the DOM contains all HTML elements (divs, spans, scripts), the Accessibility Tree only contains elements that have semantic meaning or interactive roles (buttons, headings, inputs). The browser translates DOM elements and ARIA attributes into platform-specific accessibility APIs (like UIAutomation on Windows or VoiceOver on Mac), which screen readers use to interpret the page.", ["A parallel structure generated by the browser from the DOM", "Contains only semantically meaningful or interactive elements", "Feeds directly into OS-level accessibility APIs"], ["It is a tree of CSS rules"]),
    ("B2", "scenario", "medium", "scenario", ["Accessibility"], "A developer uses `<div class=\"btn\" onClick={submit}>Submit</div>` instead of a `<button>`. They add `tabindex=\"0\"` and `role=\"button\"` so it can be focused and announced properly. What critical native keyboard functionality is still missing, and how must it be fixed?", "Native `<button>` elements automatically trigger their `click` event when focused and the user presses the `Enter` or `Space` keys. A `<div>`, even with `role=\"button\"`, does not. The developer must manually add a `onKeyDown` listener that checks if `event.key === 'Enter'` or `event.key === ' '` and manually invokes the `submit` function to achieve true keyboard accessibility.", ["Native buttons trigger clicks on Enter and Space", "Divs do not have native keyboard activation", "Must manually listen for Enter/Space keydown events"], ["Divs cannot have the role attribute"]),

    # Bucket 3: CANVAS / WEBGL OPTIMIZATION
    ("B3", "tradeoff", "easy", "tradeoff", ["Canvas"], "When building a fast-paced Canvas game, why is `requestAnimationFrame` strictly superior to `setInterval(draw, 16)` for the render loop?", "`requestAnimationFrame` (rAF) syncs directly with the browser's display refresh rate (typically 60Hz), ensuring smooth, tear-free frame pacing. The browser optimizes rAF by automatically pausing it when the tab is inactive or minimized, saving CPU/battery. `setInterval` is ignorant of the display refresh cycle, leading to dropped frames, and it continues firing aggressively even when the tab is hidden.", ["Syncs with browser display refresh rate", "Automatically pauses in background tabs to save battery", "setInterval causes frame tearing and wastes CPU in background"], ["setInterval is deprecated"]),
    ("B3", "diagnose", "medium", "debugging", ["Canvas"], "You render a large data visualization on an HTML5 `<canvas>`. On a standard 1080p monitor it looks crisp, but on a MacBook Retina display, the text and lines are noticeably blurry. How do you fix this programmatically?", "Retina displays have a high device pixel ratio (e.g., 2 physical pixels per CSS pixel). To fix the blur, you must read `window.devicePixelRatio`. You then explicitly multiply the canvas's internal `.width` and `.height` attributes by this ratio to allocate a larger pixel buffer. Finally, you use CSS to scale the canvas element back down to the logical CSS dimensions, and use `ctx.scale(ratio, ratio)` so your drawing commands match the high-res buffer.", ["Read window.devicePixelRatio", "Multiply internal canvas width/height by the ratio", "Scale the context (ctx.scale) and use CSS for logical size"], ["Change the font family to a Retina-safe font"]),
    ("B3", "optimize", "hard", "optimize", ["Canvas"], "Your 2D Canvas application draws 10,000 independent circles per frame, causing the framerate to drop to 15 FPS. Profiling shows CPU exhaustion from Context API calls. How can you batch these operations to restore 60 FPS?", "Every call to `ctx.beginPath()`, `ctx.fill()`, or `ctx.stroke()` carries heavy state-machine overhead. Instead of iterating 10,000 times and calling begin/arc/fill for each circle independently, you should batch them. Call `ctx.beginPath()` once, iterate 10,000 times calling *only* `ctx.arc()`, and then call `ctx.fill()` exactly once at the end. This reduces 10,000 expensive state changes to just 1, massively accelerating CPU performance.", ["Context API calls carry heavy state-machine overhead", "Call beginPath() once and fill() once", "Batch all shape definitions (e.g., arc) into a single path"], ["Use WebGL instead of Canvas"]),
    ("B3", "architecture", "hard", "architecture", ["Canvas"], "You are building a complex WebGL dashboard. The main thread is freezing due to heavy layout calculations in other DOM components, causing the WebGL animation to stutter. How can you completely decouple the WebGL rendering from the main thread?", "You can use an `OffscreenCanvas`. You retrieve control of the canvas element using `canvas.transferControlToOffscreen()`. You then pass the `OffscreenCanvas` object via `postMessage` to a dedicated Web Worker. Inside the worker, you acquire the WebGL context and run the `requestAnimationFrame` loop. This completely isolates the GPU rendering loop into a background thread, making it immune to main-thread DOM layout thrashing.", ["Use OffscreenCanvas API via transferControlToOffscreen", "Pass the canvas to a Web Worker", "Run the WebGL render loop in the background thread"], ["WebGL already runs on a background thread automatically"]),
    ("B3", "diagnose", "medium", "debugging", ["Canvas"], "You are building a photo-editing app in Canvas. You frequently call `ctx.getImageData()` to apply a custom sepia filter to pixels, and `ctx.putImageData()` to write them back. The performance is terrible. Why are these specific methods so slow?", "`getImageData` and `putImageData` force synchronous data transfers between the GPU's memory and the CPU's main memory. Reading from the GPU to the CPU (`getImageData`) stalls the graphics pipeline, destroying performance. For pixel-level manipulation, you should avoid the CPU entirely by writing a custom WebGL Fragment Shader to apply the sepia filter directly on the GPU in parallel.", ["Forces synchronous memory transfer between GPU and CPU", "Reading from GPU stalls the graphics pipeline", "Should use WebGL Fragment Shaders for pixel manipulation"], ["getImageData only works on JPEGs"]),
    ("B3", "scenario", "medium", "scenario", ["WebGL"], "Your SPA uses WebGL. If the user puts the computer to sleep, opens 50 other tabs, or updates their graphics driver, your WebGL canvas suddenly turns black and throws errors. What lifecycle event did you fail to handle?", "You failed to handle 'Context Loss'. The OS or browser can aggressively reclaim GPU resources from background tabs or during driver resets. When this happens, all WebGL textures, buffers, and shaders are destroyed. You must listen to the `webglcontextlost` event to pause your render loop, and the `webglcontextrestored` event to re-initialize your entire WebGL state, re-upload textures, and resume rendering.", ["Context Loss (webglcontextlost / webglcontextrestored)", "OS/Browser reclaims GPU resources, destroying textures/buffers", "Must listen for restore event and completely re-initialize WebGL state"], ["The canvas element was garbage collected"]),
    ("B3", "optimize", "medium", "optimize", ["WebGL"], "In a massive 3D WebGL scene, you have 50,000 objects, but the user's camera can only see 100 of them at a time. Passing all 50,000 objects to the GPU causes severe CPU bottlenecking. What algorithm is required here?", "Frustum Culling. Before issuing draw calls to the GPU, the CPU calculates the mathematical bounding box (or sphere) of every object and checks if it intersects with the camera's viewing frustum (the 3D pyramid of visible space). If an object is completely outside the frustum, the CPU skips it entirely, ensuring only the 100 visible objects are sent to the GPU.", ["Frustum Culling", "CPU calculates if objects intersect the camera's viewing area", "Only issues GPU draw calls for visible objects"], ["Texture Compression"]),
    ("B3", "tradeoff", "hard", "tradeoff", ["Canvas"], "In a 2D game, the background is a static complex map, and the foreground features a fast-moving player character. What is the performance tradeoff between re-rendering both on a single canvas every frame versus layering two separate canvas elements?", "Rendering both on a single canvas requires the CPU to expensively redraw the complex, static background every single frame (60 times a second) just because the player moved. By layering two canvases using CSS absolute positioning, you draw the static background once on the bottom canvas, and only clear/redraw the small player sprite on the top canvas. This trades a very minor CSS compositing overhead for a massive reduction in CPU drawing time.", ["Single canvas forces redrawing static elements every frame", "Layered canvases isolate static vs dynamic rendering", "Trades minor CSS compositing overhead for massive CPU savings"], ["Layered canvases crash the browser"]),
    ("B3", "diagnose", "medium", "debugging", ["Canvas"], "You profile your canvas animation loop and notice heavy frame drops occurring exactly every 5 seconds. The Memory timeline shows a distinct 'sawtooth' pattern. What is happening, and how do you fix it?", "The 'sawtooth' pattern indicates excessive object allocation and Garbage Collection. Inside the `requestAnimationFrame` loop (running 60 times a second), the code is continuously creating new objects (e.g., `new Vector()`, `{ x, y }` literals). The heap fills rapidly, forcing the GC to trigger a Stop-The-World pause, causing the frame drop. You fix this using 'Object Pooling': pre-allocate a fixed array of objects at startup and reuse them in the loop to achieve zero-allocation rendering.", ["Excessive object allocation inside the animation loop", "Forces aggressive Garbage Collection (STW pauses)", "Fix using Object Pooling (reuse pre-allocated objects)"], ["The canvas is running out of pixels"]),
    ("B3", "architecture", "medium", "architecture", ["WebGL"], "Why is it computationally faster to pack multiple small images (sprites) into a single large 'Texture Atlas' (Sprite Sheet) rather than loading and binding them as individual WebGL textures?", "Binding a texture to the GPU (`gl.bindTexture`) is an expensive state-change operation. If you draw 100 different sprites using 100 separate textures, you must bind 100 times per frame, stalling the pipeline. A Texture Atlas packs them all into one image. You bind the atlas exactly once, and then use UV coordinates to tell the GPU which subset of the texture to draw for each sprite, reducing 100 draw calls to 1.", ["gl.bindTexture is an expensive state-change", "Texture Atlas allows binding once per frame", "Uses UV coordinates to select sub-images, reducing draw calls"], ["Sprite sheets download faster over HTTP"]),

    # Bucket 4: BROWSER PERFORMANCE AT SCALE & ADVANCED APIS
    ("B4", "diagnose", "hard", "debugging", ["Browser Performance"], "A user clicks a button, but the UI doesn't visually update for 500ms, causing a terrible Interaction to Next Paint (INP) score. The actual click handler only takes 2ms to run. What is blocking the paint, and how do you diagnose it?", "The main thread is likely blocked by a 'Long Task' that was already executing when the user clicked, or by heavy DOM rendering/layout triggered immediately after. The browser cannot paint the frame until the main thread is idle. You diagnose this using the Performance tab in DevTools to identify red 'Long Tasks' (>50ms), or programmatically via the `PerformanceObserver` API listening for `longtask` entries to see what blocked the event loop.", ["Main thread is blocked by a Long Task or heavy rendering", "Browser cannot paint until the event loop is idle", "Diagnose using PerformanceObserver for 'longtask' entries"], ["The CSS is too complex"]),
    ("B4", "diagnose", "medium", "debugging", ["Browser Performance"], "You write a loop that updates the `width` of 100 DOM elements based on the `offsetHeight` of a container. The browser locks up completely. What specific rendering anti-pattern did you trigger?", "You triggered 'Layout Thrashing' (Forced Synchronous Layout). Normally, the browser lazily batches DOM writes and calculates layout once at the end of the frame. However, by reading `offsetHeight` immediately after writing `width` *inside* a loop, you force the browser to synchronously recalculate the entire page layout 100 times in a row, devastating CPU performance. Reads and writes must be batched separately (e.g., via `requestAnimationFrame` or FastDOM).", ["Layout Thrashing / Forced Synchronous Layout", "Reading layout properties after writing DOM forces immediate recalculation", "Must batch DOM reads and DOM writes separately"], ["The DOM is too large to fit in memory"]),
    ("B4", "tradeoff", "medium", "tradeoff", ["Browser APIs"], "When implementing an infinite scrolling list, what is the architectural tradeoff of attaching a `scroll` event listener to the window versus using the `IntersectionObserver` API?", "A `scroll` event fires synchronously dozens of times per second. Even if debounced or throttled, it forces the main thread to execute JavaScript and calculate bounding rectangles (`getBoundingClientRect`), which can cause jank. `IntersectionObserver` is deeply integrated into the browser's rendering engine. It calculates intersection asynchronously off the main thread and only fires a callback exactly when the target element crosses the defined threshold, providing vastly superior performance.", ["Scroll events fire synchronously and require expensive layout reads", "IntersectionObserver calculates intersections asynchronously off main thread", "IntersectionObserver only fires when thresholds are crossed"], ["Scroll events don't work on mobile"]),
    ("B4", "architecture", "hard", "architecture", ["Browser APIs"], "You are building a real-time trading dashboard. If a user opens the dashboard in 5 different tabs, you want to avoid opening 5 independent WebSocket connections to your server to save bandwidth. How can the tabs communicate locally to share a single connection?", "You can use the `BroadcastChannel` API (or a SharedWorker). The primary tab (leader) establishes the WebSocket. It instantiates a `new BroadcastChannel('trading_data')`. When the WebSocket receives data, the leader calls `channel.postMessage()`. The other 4 tabs instantiate the same BroadcastChannel and listen to the `onmessage` event, receiving the data locally without any server interaction. You can combine this with the Web Locks API to reliably elect a new leader if the primary tab is closed.", ["Use BroadcastChannel API for cross-tab messaging", "Leader tab holds the WebSocket and broadcasts data locally", "Follower tabs listen to the channel"], ["Use localStorage change events"]),
    ("B4", "diagnose", "medium", "debugging", ["Browser APIs"], "You implement a `ResizeObserver` to dynamically adjust a chart's internal layout when its container resizes. Suddenly, the browser console is flooded with `ResizeObserver loop limit exceeded` errors. What causes this?", "This error occurs when the callback inside the `ResizeObserver` modifies the DOM in a way that triggers *another* resize of the observed element within the exact same animation frame. The browser detects this infinite loop and forcefully aborts further observer callbacks for that frame to prevent the page from freezing. To fix it, you must ensure your chart layout changes do not alter the bounding box of the observed container.", ["Observer callback modified the DOM causing another resize", "Creates an infinite resize loop in a single frame", "Browser aborts to prevent freezing"], ["The ResizeObserver API is deprecated"]),
    ("B4", "scenario", "medium", "scenario", ["Browser Performance"], "Your React SPA feels sluggish after navigating through several pages. A Heap Snapshot reveals thousands of 'Detached DOM Tree' objects. What is a Detached DOM tree and how did your code cause it?", "A Detached DOM Tree occurs when an element is removed from the active document DOM, but JavaScript still holds a reference to it, preventing Garbage Collection. This is almost always caused by failing to remove event listeners (e.g., `window.addEventListener`) when a React component unmounts, or storing DOM node references in a global state manager (like Redux or a closure). The entire tree of elements remains trapped in memory.", ["Element removed from DOM but referenced by JavaScript", "Prevents Garbage Collection", "Caused by uncleared event listeners or global closures"], ["The browser cache is full"]),
    ("B4", "tradeoff", "easy", "tradeoff", ["Browser Performance"], "What is the performance advantage of using CSS `content-visibility: auto` on long, off-screen sections of a complex web page?", "`content-visibility: auto` is a powerful CSS property that tells the browser to skip the rendering, layout, and painting of an element entirely if it is currently outside the viewport. This dramatically speeds up the initial page load time and reduces main-thread layout calculations. As the user scrolls near the element, the browser seamlessly renders it just-in-time.", ["Skips rendering, layout, and painting for off-screen elements", "Dramatically improves initial load and layout times", "Renders Just-In-Time as the element approaches the viewport"], ["It compresses images automatically"]),
    ("B4", "compare", "medium", "compare", ["Browser APIs"], "Compare the legacy `<input type=\"file\">` with the modern `File System Access API` (`showOpenFilePicker`) regarding user workflow and saving capabilities.", "The legacy `<input type=\"file\">` only provides a one-time snapshot (a `File` object) of the data. If the user edits a document in your web app, they must download a completely new copy to their hard drive. The modern File System Access API grants the web app a persistent `FileSystemFileHandle`. This allows the web app to read the file, and more importantly, write changes *directly back to the original file* on the user's local disk, enabling true desktop-like application workflows.", ["Legacy input only gives a one-time read snapshot", "File System API provides a handle for direct writing", "Allows saving changes back to the original local file"], ["The modern API uses the cloud"]),
    ("B4", "architecture", "hard", "architecture", ["Browser APIs"], "In a multi-tab browser environment, you need to ensure that an expensive IndexedDB migration script runs exactly once, preventing race conditions where multiple tabs attempt the migration simultaneously. How do you guarantee mutual exclusion?", "You use the Web Locks API. You wrap the migration logic inside `navigator.locks.request('db_migration', async (lock) => { ... })`. The browser guarantees that only one tab can acquire this lock at a time. If other tabs boot up, their lock requests will be queued. Once the first tab finishes the migration and the promise resolves, the lock is released, and the other tabs can safely proceed (seeing the migration is already complete).", ["Use the Web Locks API (navigator.locks)", "Guarantees cross-tab mutual exclusion", "Queues other tabs until the lock is released"], ["Use a boolean in localStorage"]),
    ("B4", "explain", "medium", "concept", ["Browser Performance"], "During a performance audit, you analyze the Critical Rendering Path. What is the difference between the 'Layout' (Reflow) phase and the 'Paint' phase?", "The 'Layout' phase is a CPU-intensive mathematical calculation where the browser determines the exact geometry, size, and position of every element on the page based on the DOM and CSSOM. The 'Paint' phase takes those calculated bounding boxes and fills them with pixels (colors, text, images, shadows). Changes to `width` or `margin` trigger Layout (which then triggers Paint). Changes to `color` or `opacity` skip Layout and only trigger Paint (or Compositing), making them vastly cheaper.", ["Layout calculates geometry (size/position)", "Paint fills the geometry with pixels", "Layout is mathematically heavy and cascades; Paint is cheaper"], ["Layout is for HTML, Paint is for JS"]),

    # Bucket 5: ADVANCED FRONTEND TESTING
    ("B5", "diagnose", "medium", "debugging", ["Frontend Testing"], "Your Playwright/Cypress End-to-End (E2E) tests are notoriously flaky. They occasionally fail because a UI spinner doesn't disappear in time. Developers keep increasing the hardcoded `setTimeout` waits. What is the correct architectural fix for this?", "Hardcoded timeouts (`sleep` or `wait(5000)`) are the root cause of E2E flakiness because network/rendering speeds vary wildly in CI pipelines. The correct fix is deterministic waiting: you must instruct the testing framework to explicitly wait for the specific state change. Wait for the loading spinner element to be removed from the DOM (`waitForSelector({ state: 'hidden' })`), or intercept the specific API network request and wait for it to return a 200 response before asserting on the UI.", ["Hardcoded timeouts cause flakiness due to CI variance", "Use deterministic DOM state waiting (wait for element hidden)", "Intercept and wait for specific network requests to complete"], ["Switch from Cypress to Selenium"]),
    ("B5", "architecture", "medium", "architecture", ["Frontend Testing"], "You are unit testing a React component that relies heavily on `setTimeout` and `setInterval` for complex animations. Running the tests takes 30 seconds. How do you test this instantly and deterministically using Jest/Vitest?", "You must use 'Fake Timers' (e.g., `jest.useFakeTimers()`). This mocks the browser's native timer APIs. Instead of waiting for real wall-clock time to pass, you can synchronously advance time in your test using `jest.advanceTimersByTime(5000)`. This allows you to instantly trigger callbacks and assert on the UI state exactly 5 seconds into the future, making the tests lightning fast and entirely deterministic.", ["Use Fake Timers (jest.useFakeTimers)", "Mocks native browser timer APIs", "Synchronously fast-forward time (advanceTimersByTime)"], ["Run the tests in parallel on multiple servers"]),
    ("B5", "tradeoff", "hard", "tradeoff", ["Frontend Testing"], "When performing Visual Regression Testing (e.g., Percy, Playwright visual comparisons) across different CI operating systems, tests often fail despite the DOM and CSS being identical. What causes this, and how do visual testing tools mitigate it?", "Tests fail because different operating systems (Linux in CI vs Mac locally) use entirely different graphics libraries for Font Anti-Aliasing, sub-pixel rendering, and CSS shadow painting. Even with identical code, the pixel output differs slightly. Visual testing tools mitigate this by using heuristic algorithms that ignore sub-pixel anti-aliasing differences, applying structural SSIM (Structural Similarity Index), or forcing the exact same Docker container environment for baseline and test captures.", ["Different OS graphics libraries render fonts/anti-aliasing differently", "Causes pixel mismatch despite identical code", "Tools use SSIM algorithms or ignore sub-pixel differences"], ["The CSS relies on local fonts"]),
    ("B5", "scenario", "medium", "scenario", ["Frontend Testing"], "You are testing a complex dashboard. Instead of mocking the fetch calls directly in Jest using `jest.spyOn(global, 'fetch')`, your team decides to use MSW (Mock Service Worker). What is the primary architectural advantage of MSW for frontend testing?", "`jest.spyOn` tightly couples your tests to the specific fetching library (e.g., fetch, axios, react-query) and only works in Node. MSW intercepts requests at the network level using a Service Worker. This means the mock is entirely agnostic to how the app makes the request. Furthermore, because it operates at the network level, the exact same MSW handlers can be shared across Unit tests (Node), E2E browser tests (Cypress/Playwright), and local development environments.", ["MSW intercepts at the network level, not the code level", "Agnostic to the fetching library (axios, fetch)", "Handlers can be shared across Unit, E2E, and local dev"], ["MSW is written in Rust and is faster"]),
    ("B5", "diagnose", "medium", "debugging", ["Frontend Testing"], "You are unit testing a React component using React Testing Library and `jsdom`. The component uses `IntersectionObserver` to lazy-load images, but the test crashes saying `IntersectionObserver is not defined`. Why does this happen, and how do you fix it?", "`jsdom` is a lightweight, pure-JavaScript implementation of the DOM used in Node for fast tests. It does not contain a layout or rendering engine, so APIs that rely on geometric rendering (like `IntersectionObserver`, `ResizeObserver`, or `getBoundingClientRect`) do not exist. To fix this, you must globally mock the `IntersectionObserver` class in your test setup file, providing dummy methods for `observe` and `disconnect`.", ["jsdom lacks a layout/rendering engine", "Geometric APIs like IntersectionObserver do not exist in jsdom", "Must provide a global mock class in the test setup"], ["You forgot to import IntersectionObserver from React"]),
    ("B5", "architecture", "hard", "architecture", ["Frontend Testing"], "Your frontend team frequently breaks production because the backend team changes the API schema without notice. E2E tests catch it, but they run too late in the pipeline. How do you implement 'Contract Testing' to solve this?", "You implement a tool like Pact. The frontend defines an expected 'Contract' (request/response schema) and generates a file. The frontend runs its unit tests against a mock server generated from this contract. Crucially, this contract file is then shared with the backend team. The backend's CI pipeline runs tests forcing the real backend to fulfill the frontend's contract. If the backend changes a field the frontend expects, the *backend's* CI fails immediately, preventing the breaking change.", ["Frontend defines a contract (expected schema)", "Backend CI enforces the backend against the frontend's contract", "Fails the backend build if they break the frontend's expectations"], ["Just use TypeScript interfaces everywhere"]),
    ("B5", "diagnose", "medium", "debugging", ["Frontend Testing"], "You have 50 unit tests for a React component that uses a global Redux store. When run in isolation, every test passes. When run together using `npm test`, test #30 randomly fails with stale data. What is the fundamental testing anti-pattern here?", "The tests are suffering from 'Global State Bleed'. Because Jest reuses the Node environment for tests within the same file (and sometimes across workers depending on config), mutations to the global Redux store in Test #1 persist into Test #30. To fix this, you must ensure test isolation by creating a brand-new, fresh instance of the Redux store in a `beforeEach` block, or by wrapping the rendered component in a newly instantiated `<Provider>` for every single test.", ["Global State Bleed / Lack of Test Isolation", "Mutations to global state persist between tests", "Must instantiate a fresh Redux store for every test"], ["The tests are running too fast for Redux"]),
    ("B5", "explain", "easy", "concept", ["Frontend Testing"], "When writing accessible unit tests with React Testing Library, why is it strongly recommended to query elements using `getByRole` rather than `getByTestId` or `querySelector`?", "React Testing Library strongly advocates testing the software exactly how users interact with it. `getByRole` (e.g., `getByRole('button', { name: /submit/i })`) queries the DOM using the Accessibility Tree. If `getByRole` finds the element, it guarantees that the element is semantically correct and accessible to screen readers. `getByTestId` bypasses semantics entirely, meaning a test could pass on a completely inaccessible `<div>` masquerading as a button.", ["Queries the DOM using the Accessibility Tree", "Guarantees the element is semantically correct and accessible", "getByTestId ignores accessibility completely"], ["getByRole is faster for the CPU"]),
    ("B5", "tradeoff", "medium", "tradeoff", ["Frontend Testing"], "What is the tradeoff of relying entirely on Playwright/Cypress end-to-end tests for your application instead of building a pyramid of Jest unit/integration tests?", "E2E browser tests provide the highest confidence because they run in a real browser and test the full stack. However, the tradeoff is massive execution time, high infrastructure cost, and inherent flakiness (due to network/timing variance). Relying solely on E2E makes the CI pipeline extremely slow and makes diagnosing failures difficult (you know the app broke, but not which specific function failed). A healthy test pyramid uses fast, isolated unit/integration tests for logic, reserving E2E only for critical user journeys.", ["E2E tests provide high confidence but are slow, flaky, and expensive", "E2E failures are hard to pinpoint to specific code", "Unit tests are fast and isolated for logic verification"], ["Playwright doesn't support Chrome"]),
    ("B5", "scenario", "medium", "scenario", ["Frontend Testing"], "You need to unit test a component that renders differently based on `window.matchMedia('(prefers-color-scheme: dark)')`. How do you test the dark mode state in Jest?", "The `window.matchMedia` API is not implemented in `jsdom`. First, you must globally mock `window.matchMedia` to return an object with an `addListener` and `matches` property. To test the dark mode state, you override the mock within the specific test to force `matches: true`. You then render the component and assert that the dark mode CSS classes or correct icons are applied.", ["jsdom does not implement window.matchMedia", "Globally mock the API to return a compliant object", "Force matches: true in the test to simulate the media query"], ["Just change the CSS file in the test"])
]

BUCKET_KEYS = {
    "B1": ("Web Workers", "Service Workers", "Service Workers", ["Frontend Developer", "Full Stack Developer"]),
    "B2": ("Accessibility Engineering", "Accessibility", "HTML/DOM", ["Frontend Developer"]),
    "B3": ("Canvas", "Canvas/WebGL", "WebGL", ["Frontend Developer"]),
    "B4": ("Browser Performance", "Browser APIs", "Browser APIs", ["Frontend Developer", "Full Stack Developer"]),
    "B5": ("Frontend Testing", "Testing", "JavaScript", ["Frontend Developer", "Full Stack Developer"])
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
        c["generation_batch"] = "batch_44_frontend_developer"

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
        "batch": "batch_44_frontend_developer",
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
    
    with open(os.path.join(REPORTS_DIR, "phase4d_batch44_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_batch44_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Phase 4D - Batch 44 (Frontend Developer)\n\n")
        f.write(f"- **Attempted**: {len(cands)}\n")
        f.write(f"- **Accepted**: {len(accepted)}\n")
        f.write(f"- **Rejected**: {sum(rej.values())}\n")
        f.write(f"- **Rejections**: {dict(rej)}\n\n")
        f.write("### Staging Totals\n")
        f.write(f"- **Previous Staging Total**: {len(prior)}\n")
        f.write(f"- **Final Staging Total**: {final_staging_total}\n")
        f.write(f"- **Frontend Developer Role Total**: {role_counts[ROLE]}\n")
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

    print(f"Successfully generated 50 Frontend Developer questions.")

if __name__ == "__main__":
    main()
