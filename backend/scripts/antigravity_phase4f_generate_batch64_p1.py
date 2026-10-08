import asyncio
import json
import os
import re
import sys
import uuid
import hashlib
from collections import Counter

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "Frontend Developer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Browser Rendering & Performance
    ("B64_1_1", "concept", "hard", "concept", ["Browser Rendering"], "In the browser rendering pipeline, what is 'Forced Synchronous Layout' (Layout Thrashing), and how does a simple JavaScript loop cause it?", "The browser normally batches DOM updates and calculates layout (geometry) asynchronously before painting. However, if your JavaScript writes to the DOM (e.g., `element.style.width = '100px'`) and immediately reads a layout property (e.g., `element.offsetWidth`) inside a loop, you force the browser to halt JavaScript execution, flush the entire rendering queue, and calculate the exact pixel geometry instantly to return the value. Doing this 100 times in a loop forces 100 synchronous layouts, causing massive frame drops (jank). You must batch all reads first, then batch all writes, often using `requestAnimationFrame`.", ["Layout Thrashing occurs when JS interleaves DOM writes and layout reads", "It forces the browser to flush the render queue and calculate geometry synchronously, blocking the main thread", "Fix: Batch all DOM reads first, then execute all DOM writes separately"], ["Layout thrashing is when the CSS file is too large"]),
    ("B64_1_2", "diagnose", "medium", "debugging", ["Browser Rendering"], "Your team implements a sliding side-menu using `left: -300px` transitioning to `left: 0px`. Users on mobile devices report severe stuttering and low FPS during the animation. Why is this CSS property causing jank, and how do you fix it?", "Animating geometric properties like `left`, `top`, `width`, or `height` forces the browser to recalculate the Layout (geometry) and Paint (pixels) for every single frame of the animation (60 times a second) on the CPU. Mobile CPUs cannot handle this. To fix it, you MUST use 'Compositor-Only' properties, specifically `transform: translateX(-300px)`. The `transform` and `opacity` properties completely bypass Layout and Paint; they are offloaded directly to the GPU Compositor thread, guaranteeing buttery-smooth 60FPS animations even on low-end devices.", ["Animating `left`/`top`/`width` forces CPU-bound Layout and Paint recalculations on every frame", "This causes massive main-thread blocking and frame drops on weak devices", "Fix: Use `transform: translate()` which is hardware-accelerated by the GPU Compositor thread"], ["The menu was sliding too fast for the human eye"]),
    ("B64_1_3", "implement", "hard", "implement", ["Browser Rendering"], "How do you implement an `OffscreenCanvas` to prevent a complex WebGL visualization from destroying the Core Web Vital INP (Interaction to Next Paint) on the main thread?", "Rendering thousands of WebGL particles on the main thread consumes 16+ milliseconds per frame. If a user clicks a button while the main thread is busy rendering the canvas, the click event is queued, causing terrible INP (lag). The `OffscreenCanvas` API allows you to completely detach the `<canvas>` element from the DOM and pass its control to a Web Worker. The Web Worker runs on a completely separate OS thread, executing the WebGL rendering loop in the background. The main thread remains 100% idle and instantly responsive to user clicks, perfectly preserving INP.", ["WebGL rendering on the main thread blocks user interactions, destroying INP", "Use `canvas.transferControlToOffscreen()` to detach the canvas", "Pass the `OffscreenCanvas` to a Web Worker to execute rendering on a separate OS thread, freeing the main thread"], ["OffscreenCanvas draws the pixels outside the monitor"]),
    ("B64_1_4", "tradeoff", "medium", "tradeoff", ["Browser Rendering"], "What is the architectural tradeoff of pre-rendering HTML using Static Site Generation (SSG) versus Client-Side Rendering (CSR) regarding LCP and TBT?", "SSG provides phenomenal Largest Contentful Paint (LCP) because the CDN serves fully formed HTML; the browser paints the UI instantly before downloading any JavaScript. However, the tradeoff is Total Blocking Time (TBT) and the 'Uncanny Valley'. The page *looks* ready, but the user must wait for the massive React/JS bundle to download, parse, and execute (Hydration) before buttons actually work. During hydration, the main thread is severely blocked (high TBT). CSR provides terrible LCP (blank white screen until JS loads), but once painted, the page is instantly interactive with near-zero TBT.", ["SSG: Phenomenal LCP (fast visual render), but suffers from the 'Uncanny Valley' and high TBT during Hydration", "CSR: Terrible LCP (slow visual render), but no Uncanny Valley and low TBT once rendered", "Tradeoff: Visual speed vs Time to Interactive (TTI)"], ["SSG makes the server static and unable to move"]),
    ("B64_1_5", "scenario", "hard", "scenario", ["Browser Rendering"], "You are optimizing a massive React data grid. You successfully virtualized the list, but scrolling still feels slightly sluggish. You profile the app and discover that the browser's Garbage Collector (Minor GC) is running hundreds of times a second during scroll. Why?", "The data grid is likely creating thousands of short-lived, transient JavaScript objects or inline functions on every scroll event or render cycle (e.g., `style={{ margin: 10 }}`, inline arrow functions, or mapping new arrays). Every time the virtualized list renders the next 20 rows, it allocates new memory. These objects instantly drop out of scope, forcing the V8 engine's Scavenger (Minor GC) to run continuously to clean up the nursery memory. This GC pause blocks the main thread. To fix this, you must hoist static objects/functions outside the component, use Memoization, and mutate existing objects (object pooling) rather than allocating new ones.", ["Allocating transient objects (inline styles, arrow functions) during high-frequency events (scrolling) thrashes memory", "The V8 Scavenger (Minor GC) must constantly pause the main thread to clean up dead objects, causing micro-stutters", "Fix: Hoist static objects, memoize callbacks, and avoid creating new references inside the render loop"], ["The garbage collector is broken in Chrome"]),

    # Modern TypeScript
    ("B64_1_6", "concept", "hard", "concept", ["TypeScript"], "In advanced TypeScript, how do 'Mapped Types' and 'Key Remapping' (`as`) allow you to automatically generate getter methods for an interface?", "A Mapped Type iterates over the keys of an existing interface (`[K in keyof T]`). With Key Remapping (introduced in TS 4.1), you can use Template Literal Types to transform the string keys during the iteration. For example, if you have `interface User { name: string; age: number; }`, you can write `type Getters<T> = { [K in keyof T as \\`get${Capitalize<string & K>}\\`]: () => T[K] }`. This automatically transforms the interface into `{ getName: () => string; getAge: () => number; }`, enforcing strict compile-time contracts for generated API layers without writing duplicate type definitions.", ["Mapped Types iterate over interface keys: `[K in keyof T]`", "Key Remapping (`as`) and Template Literals allow transforming the string keys themselves", "Example: `\\`get${Capitalize<K>}\\`` generates strict getter method signatures dynamically"], ["Mapped types are used to draw Google Maps in the browser"]),
    ("B64_1_7", "diagnose", "medium", "debugging", ["TypeScript"], "You define an interface `interface Animal { type: string }` and two subtypes `Dog` and `Cat`. You write a function that accepts `Animal`. Inside the function, you check `if (animal.type === 'dog')`, but TypeScript still throws an error when you try to access a Dog-specific property. Why did the Type Guard fail?", "TypeScript cannot magically narrow types based on a generic `string` property unless it is a 'Discriminated Union'. Because `Animal.type` was typed as `string`, the value `'dog'` is just a runtime string, providing no type narrowing guarantees. You must type the discriminator explicitly using String Literal Types: `interface Dog { type: 'dog'; bark: () => void; }` and `interface Cat { type: 'cat'; meow: () => void; }`, and then define `type Animal = Dog | Cat;`. Only then will the `if (animal.type === 'dog')` branch successfully narrow the type to `Dog` and expose the `bark` method.", ["Generic `string` properties cannot be used for type narrowing", "You must use String Literal Types (`type: 'dog'`) to create a Discriminated Union", "Only Discriminated Unions allow the compiler to safely narrow the type inside `if` or `switch` blocks"], ["The type guard needed a password to pass"]),
    ("B64_1_8", "implement", "hard", "implement", ["TypeScript"], "How do you implement the `infer` keyword inside a Conditional Type to automatically extract the return type of a Promise?", "You use `infer` to declare a generic type variable that the compiler will dynamically deduce. To extract the inner type of a Promise, you write a conditional type: `type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;`. When you pass `Promise<string>` into `UnwrapPromise`, TypeScript evaluates `Promise<string> extends Promise<infer U>`, deduces that `U` must be `string`, and returns it. If you pass a non-Promise (like `number`), the condition fails and it simply returns `number`.", ["`infer` dynamically deduces a generic type within a conditional `extends` clause", "Implementation: `type Unwrap<T> = T extends Promise<infer U> ? U : T`", "Allows deep extraction of types from complex wrappers (Promises, Arrays, Functions) without hardcoding them"], ["You just guess the type and hope it works"]),
    ("B64_1_9", "tradeoff", "medium", "tradeoff", ["TypeScript"], "What is the architectural tradeoff of relying strictly on TypeScript Interfaces for API response typing versus using a runtime validation schema like Zod or Yup?", "TypeScript is entirely erased at compile time; it provides absolutely zero guarantees at runtime. If your API returns `{ id: \"123\" }` but your TS Interface said `{ id: number }`, the app will silently accept the string, and crash violently 10 layers deep when you try to call `.toFixed()`. Using Zod enforces runtime validation: it mathematically proves the incoming JSON matches the schema at the exact network boundary, throwing an immediate error if it fails. The tradeoff is that Zod adds KB to the JS bundle size and requires CPU cycles to validate the payload at runtime.", ["TypeScript is erased at compile time and cannot validate actual runtime network data", "Zod guarantees runtime type safety at the network boundary but adds bundle size and CPU parsing overhead", "Tradeoff: Pure TS is fast and light but unsafe for external I/O; Zod is safe but heavier"], ["Zod is a character from Superman, TypeScript is a font"]),
    ("B64_1_10", "scenario", "hard", "scenario", ["TypeScript"], "You use a 'Branded Type' (Opaque Type) in TypeScript to separate `UserId` from `OrderId`: `type UserId = string & { __brand: 'UserId' }`. A developer complains that they cannot simply call `fetchUser('123')` anymore. How do you construct the runtime architecture to properly utilize branded types without frustrating developers?", "The compiler strictly rejects passing raw strings to a Branded Type. You cannot bypass this without `as UserId`. However, littering `as` assertions everywhere destroys the safety of branded types. The correct architecture is to encapsulate the casting inside strict, validated Factory Functions or API boundary parsers. You create a function `function parseUserId(id: string): UserId { if (!isValid(id)) throw Error(); return id as UserId; }`. Developers must pass raw data through this factory at the I/O boundary. Once the data enters the core application logic, it is safely branded, preventing them from accidentally passing an `OrderId` to a user function.", ["Branded types intentionally prevent assigning raw primitives (like strings) to enforce domain logic", "Do not litter the codebase with `as` type assertions to bypass the compiler", "Fix: Encapsulate the casting inside strict, validated Factory Functions at the I/O boundaries"], ["Branded types require paying a licensing fee to the brand owner"]),

    # React Internals & Architecture
    ("B64_1_11", "concept", "hard", "concept", ["React Architecture"], "In React 18, what is 'Selective Hydration', and how does it rely on `Suspense` boundaries to improve Time to Interactive (TTI)?", "In legacy React, hydration was entirely synchronous and blocking: the browser had to download the entire JS bundle and hydrate the entire DOM tree before ANY button became interactive. In React 18, if you wrap components in `<Suspense>` boundaries, React streams the HTML immediately, but defers hydrating those specific suspended chunks. If the user clicks on a suspended component (like a sidebar) while the rest of the page is still hydrating, React's 'Selective Hydration' intercepts the event, instantly pauses the current hydration, prioritizes hydrating the exact component the user clicked, and replays the event. This massively improves perceived TTI.", ["Legacy hydration was a massive, synchronous, blocking pass across the entire DOM tree", "Selective Hydration allows React to hydrate chunks of the UI independently via `<Suspense>` boundaries", "If a user interacts with a Suspended chunk, React prioritizes hydrating that exact chunk to execute the event instantly"], ["Selective hydration is drinking water only when thirsty"]),
    ("B64_1_12", "diagnose", "medium", "debugging", ["React Architecture"], "You fetch data in a React component and store it in state. You notice that when you navigate away from the page and come back, the component briefly flashes old, stale data before fetching the new data. Why does this 'Stale State' flash occur?", "This occurs because the state was initialized in the component, and when the component unmounts, the state is destroyed. WAIT, if the component unmounts and remounts, the state should be empty. If it flashes old data, it means the state is actually hoisted OUTSIDE the component (e.g., in Redux, Zustand, or a global Context) and wasn't explicitly cleared on unmount. Alternatively, you are using a client-side cache (like React Query) with a stale-time configuration, and it is instantly returning the cached (stale) data while triggering a background refetch (Stale-While-Revalidate). This is usually a feature, not a bug, but can be fixed by adjusting cache TTLs.", ["If data flashes on remount, the state is either hoisted globally or cached (React Query)", "The cache instantly returns the stale data to prevent a loading spinner, then refetches in the background", "Fix: Adjust the `staleTime` or explicitly invalidate/clear the global state on component unmount"], ["The browser forgot to delete the HTML cache"]),
    ("B64_1_13", "implement", "hard", "implement", ["React Architecture"], "How do you implement `useSyncExternalStore` in React 18 to connect a vanilla JavaScript mutable state object to React, and why does it prevent 'State Tearing' during concurrent rendering?", "If you try to read from a mutable external store (like Redux or `window.innerWidth`) using standard `useEffect` and `useState`, React 18's Concurrent Mode might pause the render halfway through. If the external store mutates during that pause, the top half of the UI renders the old value, and the bottom half renders the new value (State Tearing). You implement `useSyncExternalStore(subscribe, getSnapshot)` by providing a subscription callback and an immutable snapshot getter. React mathematically guarantees that if the snapshot changes *during* a concurrent render pause, React throws away the render and restarts synchronously, completely preventing tearing.", ["Concurrent Mode can pause renders; if an external mutable store changes during the pause, the UI tears (shows two different states)", "`useSyncExternalStore` takes a `subscribe` function and a `getSnapshot` function", "It guarantees that if the snapshot mutates mid-render, React aborts and restarts synchronously to ensure UI consistency"], ["You sync the store by uploading it to Google Drive"]),
    ("B64_1_14", "tradeoff", "medium", "tradeoff", ["React Architecture"], "What is the architectural tradeoff of using `useMemo` and `React.memo` on every single component and variable in a React application?", "Junior developers often blanket their app in `useMemo` thinking it makes it faster. The severe tradeoff is Memory Overhead and CPU Initialization. `useMemo` is not free; React must allocate memory to store the previous values, store the dependency array, and perform a shallow equality check (`===`) on every single render. If the computation you are memoizing is trivial (like filtering an array of 10 items), the overhead of the equality check and memory allocation is actually SLOWER than just recalculating the array. Memoization should be strictly reserved for mathematically expensive operations or maintaining referential equality for child component props.", ["`useMemo` requires memory allocation for cached values and CPU cycles for dependency equality checks", "For trivial operations, the caching overhead is slower than simply recalculating the value", "Tradeoff: Blanket memoization causes memory bloat and initialization lag; it should be reserved for heavy math or referential stability"], ["Memoization means writing down notes on paper"]),
    ("B64_1_15", "scenario", "hard", "scenario", ["React Architecture"], "You implement a drag-and-drop feature in React. When the user drags an item rapidly, the entire application lags horribly. You discover that the parent component is re-rendering 60 times a second. How do you architect the state to fix this without abandoning React?", "Storing high-frequency continuous state (like X/Y mouse coordinates during a drag) in standard React `useState` at the top of the component tree is an anti-pattern. Every 16ms, React triggers the Reconciliation algorithm, diffing the entire Virtual DOM tree, crushing the CPU. To fix this, you must bypass React's standard render cycle for the drag state. You can use an entirely unmanaged `useRef` to store the coordinates and mutate the DOM node's style directly (`ref.current.style.transform = ...`), or you can isolate the state completely by moving the `useState` down into a tiny, isolated leaf component that ONLY renders the dragging visual, leaving the parent tree untouched.", ["High-frequency events (dragging/scrolling) trigger 60FPS React state updates, crushing the CPU with Virtual DOM diffing", "Fix 1: Isolate the state into a tiny leaf component so the parent tree doesn't re-render", "Fix 2: Bypass React entirely by storing coordinates in a `useRef` and directly mutating the DOM node's `style.transform`"], ["You just tell the user to drag slower"])
]

def run_batch():
    # Load all existing records to do deduplication
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[5]) or LEAK.search(q[6]):
            print(f"PROMPT LEAK DETECTED in: {q[5]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[5] for q in Q]
    
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
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[5][:50]}...")
            rejected.append(q)
        else:
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 1).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Frontend Engineer", "Software Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Frontend",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "Software Engineering",
            "intent": q[1],
            "difficulty": q[2],
            "question_type": q[3],
            "question": q[5],
            "expected_answer": q[6],
            "evaluation_rubric": {
                "strong_indicators": q[7],
                "weak_indicators": q[8]
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
            
    # Final audit reporting
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r["primary_role"] for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT")
    print("========================================")
    print(f"Batch: 64")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
