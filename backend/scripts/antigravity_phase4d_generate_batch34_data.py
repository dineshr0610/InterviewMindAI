"""Batch 34 Part 1 question content (Frontend Developer). Targeted Gap Generation."""

ROLE = "Frontend Developer"

BUCKET_KEYS = {
    "CSS_AND_DOM": ("HTML/DOM & CSS", "CSS Architecture & Performance", "Frontend", ["Frontend Developer", "Full Stack Developer"]),
}

Q = [
# ---------------- CSS_AND_DOM ----------------
("CSS_AND_DOM", "debug", "medium", "debugging", ["Stacking Contexts", "z-index"],
 "A developer applies `z-index: 9999` to a modal, but it still appears *behind* a simple floating button that has `z-index: 2`. The modal's position is fixed. Why did the massive `z-index` fail, and how do you fix it?",
 "The modal and the button belong to different 'Stacking Contexts'. If the button's parent element creates a new stacking context (via `z-index`, `opacity`, or `transform`), elements inside it are locked into that layer. An element in a lower stacking context can *never* overlap a higher one, regardless of internal `z-index`. Fix: Move the modal DOM node to the root `<body>` level (e.g., using React Portals).",
 ["They belong to different 'Stacking Contexts'", "An element in a lower stacking context cannot overlap a higher one, regardless of internal `z-index`", "Fix: Move the modal directly to the `<body>` element (using a Portal)"],
 ["The browser ran out of numbers and ignored the 9999"]),

("CSS_AND_DOM", "tradeoff", "medium", "tradeoff", ["Grid", "Flexbox"],
 "When building a complex, dynamic 2D layout, what is the architectural tradeoff of using CSS Grid versus CSS Flexbox?",
 "CSS Grid is natively two-dimensional (columns and rows simultaneously) and controls the layout from the *parent* container down, making it perfect for rigid, predictable page structures. Flexbox is natively one-dimensional (row OR column) and distributes space based on the *children's* content size, making it perfect for fluid, wrapping micro-layouts where items dictate their own size.",
 ["CSS Grid is two-dimensional (rows and columns); controls layout strictly from the Parent down", "Flexbox is one-dimensional (row or column); layout is heavily influenced by Children content size", "Grid is for rigid macro page structure; Flexbox is for fluid, wrapping micro-components"],
 ["Grid costs money to use, Flexbox is open source"]),

("CSS_AND_DOM", "implement", "hard", "implementation", ["DOM Rendering", "CSS Containment"],
 "You are rendering a massive DOM table with 10,000 rows. Scrolling is sluggish because the browser struggles with layout calculations. Without using React virtual scrolling, what CSS property can drastically improve native rendering performance?",
 "Apply `content-visibility: auto;` (and `contain-intrinsic-size`) to the rows. This CSS property tells the browser to skip rendering, layout, and paint calculations for elements that are currently off-screen. As the user scrolls, the browser dynamically computes only the visible rows, drastically reducing main-thread blocking and improving scrolling FPS.",
 ["Apply `content-visibility: auto;` to the rows", "Forces the browser to skip layout and paint calculations for off-screen elements", "Greatly reduces main-thread blocking during scroll without JavaScript virtualization"],
 ["Apply `display: none` to the entire table so it scrolls instantly"]),

("CSS_AND_DOM", "fundamentals", "easy", "concept", ["display", "visibility"],
 "What is the functional difference between `display: none` and `visibility: hidden` in CSS?",
 "`display: none` completely removes the element from the DOM's layout flow; it takes up zero physical space and triggers a full document Reflow. `visibility: hidden` makes the element completely transparent but keeps it in the layout flow; it still occupies its exact physical dimensions and triggers only a Repaint, not a Reflow.",
 ["`display: none` removes the element from the layout flow entirely (takes up 0 space)", "`visibility: hidden` makes it transparent but retains its exact physical space in the layout", "`display: none` triggers a heavy Reflow; `visibility: hidden` triggers a lighter Repaint"],
 ["`display: none` deletes the HTML file from the server"]),

("CSS_AND_DOM", "scenario", "hard", "scenario", ["Performance", "Reflow vs Repaint"],
 "A JS animation loop modifies an element's `margin-left` by 1px every frame using `requestAnimationFrame`. The laptop fan spins up, CPU hits 100%, and the animation stutters. Why is this animation so expensive, and how do you optimize it?",
 "Modifying `margin-left` forces the browser to mathematically recalculate the Layout (Reflow) of the entire page on every single frame (60fps), which is enormously CPU-intensive. You must optimize it by animating `transform: translateX()` instead. Transforms do not affect document layout and are handled exclusively by the GPU (Compositor thread), resulting in a stutter-free 60fps at near-zero CPU cost.",
 ["Modifying `margin-left` triggers a full document Layout/Reflow on every single frame (massive CPU cost)", "Fix: Animate `transform: translateX()` instead", "Transforms are offloaded to the GPU (Compositor thread) and do not trigger layout calculations"],
 ["The computer is just old and needs more RAM"]),

("CSS_AND_DOM", "debug", "medium", "debugging", ["Viewport Units", "Scrollbars"],
 "You build a responsive layout using `width: 100vw`. However, on Windows desktop browsers, this causes an unwanted horizontal scrollbar to appear at the bottom of the page. Why, and what is the fix?",
 "`100vw` calculates the width of the entire browser window viewport *including* the space occupied by the vertical scrollbar. When the page content exceeds `100vh`, a vertical scrollbar appears (typically 15px wide on Windows), causing the `100vw` element to overflow the usable window space. The fix is to use `width: 100%`, which calculates available width *excluding* the scrollbar.",
 ["`100vw` includes the width of the vertical scrollbar in its calculation", "If a vertical scrollbar appears, `100vw` causes the content to overflow horizontally", "Fix: Use `width: 100%`, which respects the parent container excluding the scrollbar"],
 ["Windows computers don't support modern CSS properly"]),

("CSS_AND_DOM", "implement", "medium", "implementation", ["Accessibility", "ARIA"],
 "You build a custom accessible checkbox using a `<div>`. When a screen reader navigates to it, it announces simply as 'group'. What specific HTML attributes must you add to make it behave exactly like a native `<input type='checkbox'>`?",
 "You must add `role=\"checkbox\"` to explicitly define its semantic purpose. You must add `tabindex=\"0\"` to make it discoverable via keyboard navigation. Finally, you must dynamically toggle the `aria-checked=\"true\"` or `aria-checked=\"false\"` attribute via JavaScript when it is clicked or activated by the Spacebar.",
 ["Add `role=\"checkbox\"` to define the semantic meaning for screen readers", "Add `tabindex=\"0\"` to make it keyboard focusable", "Dynamically toggle `aria-checked=\"true|false\"` via JavaScript state"],
 ["Add a `<title>` tag that says 'This is a checkbox'"]),

("CSS_AND_DOM", "tradeoff", "easy", "tradeoff", ["CSS Architecture", "BEM"],
 "In CSS architecture, what is the primary benefit of the BEM (Block Element Modifier) naming convention over standard semantic class names?",
 "Standard semantic class names (e.g., `.title` or `.active`) frequently cause catastrophic global styling collisions in large codebases due to CSS's global nature. BEM (`.block__element--modifier`) enforces strict isolation and zero nesting by namespacing every class. It guarantees that styles applied to a specific component will never accidentally mutate unrelated parts of the app.",
 ["Prevents global CSS class name collisions", "Enforces strict isolation by namespacing every class (`.block__element--modifier`)", "Eliminates the need for deep, fragile CSS nesting selectors"],
 ["BEM makes the CSS file download significantly faster over HTTP"]),

("CSS_AND_DOM", "explain", "medium", "concept", ["Reflow", "Repaint"],
 "What is a 'Repaint' versus a 'Reflow' (Layout) in browser rendering, and which is more expensive?",
 "A Repaint occurs when visual styles change (like `color` or `background-color`) but the geometry remains identical; it is relatively cheap. A Reflow (Layout) occurs when the physical geometry changes (like `width`, `margin`, or DOM node insertion). Reflow is vastly more expensive because the browser must mathematically recalculate the position and size of potentially every element in the tree.",
 ["Repaint: Visual changes (color, background) without geometry changes (Cheap)", "Reflow (Layout): Physical geometry changes (width, height, DOM insertion) (Expensive)", "Reflow requires recalculating the layout of the target and its children/siblings"],
 ["Reflow is when you refresh the page, Repaint is when you draw a picture"]),

("CSS_AND_DOM", "debug", "hard", "debugging", ["Performance", "Layout Thrashing"],
 "You read an element's `offsetHeight`, change its `className`, and read `offsetHeight` again. You repeat this in a loop for 100 items. The browser completely locks up for 3 seconds. Why did reading and writing freeze the browser?",
 "This is 'Layout Thrashing' (Forced Synchronous Layout). Normally, the browser batches DOM updates. But when you write to the DOM (changing `className`) and immediately read a layout property (`offsetHeight`), the browser is forced to pause JS, synchronously recalculate the entire page layout to return the accurate height, and then resume. Doing this 100 times forces 100 synchronous reflows.",
 ["'Layout Thrashing' or 'Forced Synchronous Layout'", "Writing to the DOM and immediately reading layout forces the browser to flush the batched updates", "Forces a massive synchronous layout recalculation on every loop iteration, locking the main thread"],
 ["The browser fell asleep counting to 100"]),

("CSS_AND_DOM", "implement", "medium", "implementation", ["Layout", "Centering"],
 "You want a specific button to remain perfectly centered both horizontally and vertically inside its parent container, regardless of the parent's size. Provide the most robust modern CSS solution using only 3 lines of code on the parent.",
 "Using modern CSS, you apply Flexbox or Grid to the parent container. Flexbox: `display: flex; justify-content: center; align-items: center;`. Grid: `display: grid; place-items: center;`. Both approaches eliminate the need for fragile absolute positioning, negative margins, or manual calculations.",
 ["Flexbox: `display: flex; justify-content: center; align-items: center;`", "Grid: `display: grid; place-items: center;`", "Eliminates fragile absolute positioning hacks"],
 ["Use `<center>` tags around the button"]),

("CSS_AND_DOM", "scenario", "hard", "scenario", ["Memory Leaks", "Detached DOM"],
 "A Single Page Application has a memory leak. You take a Heap Snapshot in Chrome DevTools and see thousands of 'Detached DOM nodes'. What JavaScript architectural error causes this, and how do you fix it?",
 "A Detached DOM node occurs when an element is removed from the visible HTML document (the DOM tree), but a lingering JavaScript variable, closure, or event listener still holds a strong reference to it in memory. The Garbage Collector cannot destroy it. You fix it by explicitly nullifying references (`element = null`) and calling `removeEventListener` when a component unmounts.",
 ["Detached DOM: Removed from the document tree, but still referenced by a JavaScript variable/closure", "The Garbage Collector cannot free the memory because JS still holds a strong reference", "Fix: Nullify JS references and `removeEventListener` when unmounting components"],
 ["The nodes physically detached from the motherboard"]),

("CSS_AND_DOM", "explain", "easy", "concept", ["Box Model", "box-sizing"],
 "What is the purpose of the CSS `box-sizing: border-box;` property, and why is it globally applied in almost every modern CSS reset?",
 "By default (`content-box`), CSS calculates width based purely on content; adding padding/borders increases the total physical size of the element, breaking layouts. `border-box` forces padding and borders to be calculated *inside* the defined width/height. If you set `width: 100px`, the element is exactly 100px wide, automatically shrinking the inner content area to accommodate padding.",
 ["`content-box` (default) adds padding/borders to the total width, breaking layouts", "`border-box` includes padding/borders *inside* the defined width and height", "If `width: 100px`, the physical element will always remain exactly 100px wide"],
 ["It makes the browser render the website inside a 3D box"]),

("CSS_AND_DOM", "tradeoff", "medium", "tradeoff", ["Security", "DOM Injection"],
 "When injecting dynamic HTML into the DOM, what is the exact security/performance tradeoff between using `Element.innerHTML` versus `Element.textContent`?",
 "`innerHTML` invokes the browser's heavy HTML parser to evaluate and render DOM nodes. It is slower and extremely vulnerable to Cross-Site Scripting (XSS) if the string contains unsanitized user input. `textContent` completely bypasses the HTML parser, treating the string purely as raw text. It is drastically faster and 100% secure against XSS, but cannot render bold tags or links.",
 ["`innerHTML` invokes the heavy HTML parser; extremely vulnerable to XSS injection", "`textContent` bypasses the parser entirely, treating input strictly as raw text", "Tradeoff: `textContent` is 100% secure and faster, but cannot render HTML tags"],
 ["`innerHTML` requires a paid license from the W3C"]),

("CSS_AND_DOM", "implement", "hard", "implementation", ["CSS Variables", "Theming"],
 "You need to implement a dark mode toggle. Instead of swapping dozens of individual CSS classes via JavaScript, how do you architect a scalable dark mode using modern CSS variables?",
 "Define a palette of CSS variables at the `:root` level (`--bg: white;`). Define the dark palette inside a specific attribute selector (`[data-theme=\"dark\"] { --bg: black; }`). Your application CSS exclusively uses the variables (`background: var(--bg)`). To toggle, JavaScript executes `document.documentElement.setAttribute('data-theme', 'dark')`, and the browser repaints the app instantly.",
 ["Define CSS variables (`--color`) at the `:root` level", "Override those variables inside a `[data-theme=\"dark\"]` selector", "Use JS to toggle the `data-theme` attribute on the `<html>` root element, triggering a global repaint"],
 ["Tell the user to turn down their monitor brightness"]),

("CSS_AND_DOM", "scenario", "medium", "scenario", ["Positioning", "Overflow"],
 "An absolute positioned tooltip `div` is placed inside a relative container. The tooltip is clipped and hidden where it overflows the parent container's boundaries because the parent has `overflow: hidden`. How do you allow the tooltip to break out without removing `overflow: hidden`?",
 "If the tooltip must break out of an `overflow: hidden` parent, you must decouple it from that clipping context. You remove the tooltip from the parent DOM node entirely and append it directly to `document.body` (e.g., using a React Portal). You then calculate its absolute position on the screen using `getBoundingClientRect()` of the trigger element.",
 ["Remove the tooltip from the parent DOM node and append it directly to `document.body` (e.g., React Portals)", "Use `getBoundingClientRect()` on the trigger element to calculate the exact absolute coordinates", "Decouples the tooltip from the parent's `overflow: hidden` clipping context"],
 ["Apply `overflow: please-show-it` to the parent"]),

("CSS_AND_DOM", "fundamentals", "easy", "concept", ["CSS Cascade", "Specificity"],
 "What is the 'CSS Cascade' and how does it determine which style to apply when rules conflict?",
 "The Cascade is the algorithm browsers use to resolve conflicting CSS rules. It calculates priority based on three strict tiers: 1. Importance (e.g., `!important` flags or inline styles), 2. Specificity (IDs beat Classes, Classes beat Tags), and 3. Source Order (if Importance and Specificity are identical, the rule declared *last* in the CSS file wins).",
 ["The algorithm to resolve conflicting CSS rules", "Tier 1: Importance (`!important`, inline styles)", "Tier 2: Specificity (IDs > Classes > Tags). Tier 3: Source Order (Last declared wins)"],
 ["A physical waterfall inside the browser rendering engine"])
]
