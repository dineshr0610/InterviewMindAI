"""Batch 29 Part 1 question content (Data Analyst). Targeted Gap Generation."""

ROLE = "Data Analyst"

BUCKET_KEYS = {
    "ROOT_CAUSE_ANALYSIS": ("Root Cause Analysis", "Metric Investigation", "Data Warehouse", ["Data Analyst", "Data Scientist", "Product Manager"]),
}

Q = [
# ---------------- ROOT_CAUSE_ANALYSIS ----------------
("ROOT_CAUSE_ANALYSIS", "scenario", "medium", "scenario", ["Statistics", "Simpson's Paradox"],
 "The Product Manager panics because the overall 'User Conversion Rate' plummeted by 15% yesterday. You check the data, but the conversion rate for Desktop users increased by 2%, and Mobile users increased by 2%. What statistical phenomenon explains how the overall rate can drop while all individual segments increase?",
 "This is Simpson's Paradox. It occurs because the underlying mix or distribution of traffic changed drastically. Mobile traffic, which historically has a much lower absolute conversion rate than Desktop, suddenly accounted for a massive majority of all traffic yesterday (e.g., due to a mobile ad campaign). Even though Mobile converted slightly better than its own baseline, its massive volume dragged the overall weighted average down.",
 ["Simpson's Paradox", "The underlying distribution or mix of traffic changed drastically", "A segment with a lower absolute baseline suddenly became the dominant volume, dragging the weighted average down"],
 ["Desktop users and Mobile users canceled each other out mathematically"]),

("ROOT_CAUSE_ANALYSIS", "debug", "hard", "debugging", ["Tracking", "Instrumentation"],
 "You investigate a sudden 30% drop in 'Daily Active Users' (DAU) that occurred exactly on October 1st. You confirm the database tables updated correctly, no data pipelines failed, and the product team released zero code changes. Marketing also made no changes. What is the most likely instrumentation or tracking cause?",
 "The most likely cause is an expiration or change in external tracking dependencies. Specifically, a client-side tracking SDK (like Google Analytics or Segment) was blocked by a new ad-blocker list update, or a crucial tracking cookie expired (like an ITP/Safari policy change enforcing a 7-day cookie wipe on the 1st of the month). The business didn't lose users; it just lost the *ability to observe* them.",
 ["An expiration or change in external tracking dependencies", "A client-side tracking SDK was blocked (e.g., new ad-blocker rules)", "A tracking cookie expired due to browser privacy policies (like Safari ITP)"],
 ["Users universally agreed to stop logging in on October 1st"]),

("ROOT_CAUSE_ANALYSIS", "scenario", "medium", "scenario", ["Bias", "Correlation vs Causation"],
 "The marketing team claims their new email campaign was a massive success because users who opened the email spent 50% more money this month than users who didn't. As an analyst, what fundamental flaw in their reasoning must you point out before they double the campaign budget?",
 "They are confusing Correlation with Causation, specifically suffering from Selection Bias. Users who actively open marketing emails are inherently more engaged, loyal, and likely to spend money regardless of the specific email content. To prove the campaign actually *caused* the increase, they must run a randomized control trial (A/B test) holding out a control group of engaged users who do *not* receive the email.",
 ["Confusing Correlation with Causation", "Selection Bias: Users who open emails are inherently more engaged and likely to spend anyway", "Must run a randomized control trial (A/B test) to prove actual causality"],
 ["The email campaign was actually sent to ghosts"]),

("ROOT_CAUSE_ANALYSIS", "tradeoff", "hard", "tradeoff", ["Investigation Workflow"],
 "When investigating a sudden anomaly in a core KPI, what is the analytical tradeoff between immediately digging into granular user-level data versus aggressively segmenting the aggregated data by categorical dimensions (device, country, version)?",
 "Diving into user-level data is incredibly noisy, time-consuming, and prone to finding false patterns or outliers that don't explain the macro shift. Aggressively segmenting aggregated data is the fastest way to isolate the 'blast radius' of an anomaly (e.g., discovering the drop is 100% isolated to iOS users in Germany). Segmenting focuses the investigation, whereas user-level analysis is better suited for later-stage hypothesis validation.",
 ["User-level data is incredibly noisy and prone to false patterns", "Aggressive segmentation isolates the 'blast radius' of the anomaly quickly", "Segmenting focuses the investigation; user-level analysis validates specific hypotheses later"],
 ["Granular data is heavier to download on the analyst's laptop"]),

("ROOT_CAUSE_ANALYSIS", "explain", "easy", "concept", ["Statistics"],
 "Explain the analytical concept of a 'Confounding Variable'.",
 "A confounding variable is an unmeasured third variable that independently influences both the independent variable and the dependent variable, creating a false correlation. For example, if data shows ice cream sales strongly correlate with shark attacks, the confounding variable is 'Summer Weather/Heat', which independently causes both ice cream consumption and beach swimming.",
 ["An unmeasured third variable that influences both independent and dependent variables", "Creates a false or spurious correlation between two variables", "Example: Summer heat causes both ice cream sales and shark attacks"],
 ["A variable that actively tries to confuse the data analyst"]),

("ROOT_CAUSE_ANALYSIS", "debug", "medium", "debugging", ["Data Pipelines", "Aggregation"],
 "An automated alert triggers because the 'Average Order Value' (AOV) doubled overnight. You check the raw sales table: total revenue is completely normal, and the total number of orders is normal. No pipelines failed. How can the average double if the numerator and denominator are normal?",
 "The issue is an anomaly in the metric aggregation pipeline, specifically a duplication error (e.g., a massive `JOIN` multiplying the rows, causing revenue to be counted multiple times for the same order) or a currency conversion bug (e.g., aggregating JPY and USD without conversion) in the specific view used for the dashboard. It is a transformation layer bug, not a business reality.",
 ["An anomaly in the metric aggregation pipeline or view", "A duplication error (e.g., a fan-out JOIN) multiplying rows", "A currency conversion bug aggregating different currencies natively"],
 ["Customers suddenly started tipping 100% on every order"]),

("ROOT_CAUSE_ANALYSIS", "scenario", "hard", "scenario", ["Cohorts", "Data Freshness"],
 "A subscription business notices their 'Month 1 Retention Rate' for January cohorts dropped from 80% to 60%. The executive team wants to overhaul the onboarding flow immediately. What data artifact must you check to prove whether this is a genuine user behavior problem or a reporting artifact?",
 "You must check the 'Data Freshness' and the exact definition of the retention metric window. Because it is likely mid-February, the January cohort is still maturing. If the metric rigidly looks at a rolling 30-day window, users who signed up on January 25th literally haven't had 30 days to be retained yet. They artificially appear as 'churned' in the denominator. You must enforce cohort maturity constraints.",
 ["Check the exact definition of the retention metric window and cohort maturity", "Users who signed up late in the month haven't had a full 30 days to be retained", "They artificially appear as 'churned', skewing the metric. Enforce maturity constraints before reporting."],
 ["The January cohort was uniquely terrified of the onboarding flow"]),

("ROOT_CAUSE_ANALYSIS", "tradeoff", "medium", "tradeoff", ["Metric Design", "Churn"],
 "What is the analytical tradeoff of defining a 'Churned User' as someone who hasn't logged in for 7 days versus 30 days?",
 "A 7-day definition is highly responsive, alerting the business to negative trends quickly, but generates massive noise and false positives because users simply go on vacation or get busy. A 30-day definition is highly accurate and represents genuine product abandonment, but it is extremely lagging; by the time the business realizes retention is dropping, a full month of users has already been lost.",
 ["7-day: Highly responsive, but massive noise and false positives (vacations, busy weeks)", "30-day: Highly accurate for genuine abandonment, but severely lagging", "30-day tradeoff: By the time you detect a drop, a full month of users is lost"],
 ["A 7-day churn means the user's account is physically deleted from the server"]),

("ROOT_CAUSE_ANALYSIS", "implement", "hard", "implementation", ["SQL", "Debugging Views"],
 "You are investigating a massive spike in 'Failed Transactions'. The data engineers say the raw JSON logs in the data lake are accurate, but the SQL view you query shows a 500% spike. How do you construct an analytical query to isolate exactly which transformation logic in the view is creating the phantom failures?",
 "You must bypass the view and query the raw logs directly. You perform an `EXCEPT` or an `ANTI-JOIN` between your raw query results and the view's output on the unique `transaction_id`. This instantly isolates the exact subset of rows causing the discrepancy. You then inspect those specific rows to reverse-engineer which `CASE WHEN` or `JOIN` in the view is misclassifying them.",
 ["Query the raw logs directly to bypass the view", "Perform an `EXCEPT` or `ANTI-JOIN` between the raw data and the view on `transaction_id`", "Isolate the exact subset of discrepant rows and inspect them to find the flawed `CASE WHEN` or `JOIN`"],
 ["Delete the SQL view and tell the engineers to rewrite it in Python"]),

("ROOT_CAUSE_ANALYSIS", "scenario", "medium", "scenario", ["Web Analytics", "Bounces"],
 "The 'Time on Page' metric for a key blog post suddenly drops to zero for thousands of sessions. You investigate and find that all of these zero-second sessions have exactly one page view and then exit. What web analytics phenomenon is this, and is it a bug?",
 "This is a 'Bounce'. In standard web analytics (like Google Analytics), time on page is calculated by subtracting the timestamp of the first pageview from the timestamp of the second pageview. If a user only views one page and leaves (a bounce), there is no second timestamp, so the system defaults to zero seconds, even if the user spent 10 minutes reading the article. It is a known limitation, not a bug.",
 ["This is a 'Bounce' (a single-page session)", "Time is calculated by subtracting the first timestamp from the second timestamp", "With only one event, there is no second timestamp, defaulting to zero. It is a known limitation, not a bug."],
 ["The blog post was so boring people literally spent 0 seconds on it"]),

("ROOT_CAUSE_ANALYSIS", "explain", "easy", "concept", ["Time Series"],
 "What is the analytical difference between an 'Anomaly' and a 'Trend Shift'?",
 "An anomaly is a brief, isolated deviation from expected baseline behavior that quickly returns to normal (e.g., a one-hour traffic spike during a Super Bowl ad, or a brief server outage). A trend shift is a fundamental, permanent change in the trajectory or baseline of the metric (e.g., traffic permanently doubles after successfully launching the product in a new country).",
 ["Anomaly: A brief, isolated deviation that quickly returns to the baseline", "Trend Shift: A fundamental, permanent change in the baseline or trajectory of the metric", "Anomalies are events; Trend Shifts are structural changes"],
 ["An anomaly is a bug in the code; a trend shift is a bug in the database"]),

("ROOT_CAUSE_ANALYSIS", "debug", "hard", "debugging", ["Funnels", "Data Grain"],
 "You are analyzing a funnel: `Pageview -> Add to Cart -> Checkout -> Purchase`. The conversion rate from `Checkout -> Purchase` is somehow 150%. How is a >100% step conversion mathematically occurring in the data warehouse?",
 "The funnel query is likely mismanaging the grain of the events or failing to deduplicate users. If a single user triggers one `Checkout` event, but then clicks the `Purchase` button three times (triggering three purchase events), a naive `COUNT(events)` will show 3 purchases for 1 checkout. The funnel must be strictly built using `COUNT(DISTINCT user_id)` or `session_id` at each step to cap conversion at 100%.",
 ["Mismanaging the grain of the events or failing to deduplicate users", "A naive `COUNT(events)` allows a user clicking a button multiple times to inflate the numerator", "Fix: Strictly use `COUNT(DISTINCT user_id)` or `session_id` to cap conversion at 100%"],
 ["Customers are buying negative quantities of items"]),

("ROOT_CAUSE_ANALYSIS", "tradeoff", "medium", "tradeoff", ["Dashboards", "Metrics"],
 "When designing an executive dashboard, what is the tradeoff between showing absolute metrics (e.g., '10,000 Signups') versus ratio metrics (e.g., '5% Signup Rate')?",
 "Absolute metrics show the sheer scale and volume of business impact, but they are highly susceptible to macro trends (e.g., top-of-funnel traffic spikes artificially inflate signups, even if the product is broken). Ratio metrics normalize for volume and accurately reflect the actual health/efficiency of the product flow, but they can be misleading on tiny sample sizes (e.g., a 100% conversion rate from exactly 1 user).",
 ["Absolute Metrics: Show sheer volume/impact, but susceptible to top-of-funnel macro trends", "Ratio Metrics: Normalize volume to show actual product flow efficiency", "Ratio Tradeoff: Highly misleading on tiny sample sizes (Law of Small Numbers)"],
 ["Absolute metrics are only used for absolute zeros"]),

("ROOT_CAUSE_ANALYSIS", "scenario", "medium", "scenario", ["Outliers", "Communication"],
 "The CEO notices that revenue from the 'Enterprise' segment dropped by 40% on Monday. You investigate and find that exactly one massive client (accounting for 45% of all Enterprise revenue) forgot to renew their contract on Sunday. How do you communicate this root cause without making the entire Enterprise sales team look like they failed?",
 "You must mathematically isolate the impact of the single outlier. You calculate and present the 'Enterprise Revenue excluding Client X', demonstrating that the core segment actually grew by 5%. You explain that the drop is an isolated concentration risk failure (one massive whale churning), not a systemic failure of the entire Enterprise sales pipeline.",
 ["Mathematically isolate the impact of the single outlier", "Calculate and present the metric excluding the outlier (e.g., 'Core revenue grew 5%')", "Communicate it as an isolated concentration risk, not a systemic pipeline failure"],
 ["Blame the accounting department for a typo"]),

("ROOT_CAUSE_ANALYSIS", "implement", "hard", "implementation", ["Contribution Analysis"],
 "You need to perform a root cause analysis on a sudden drop in Daily Active Users (DAU). You have 50 categorical dimensions (country, device, browser, etc.). How do you programmatically or analytically determine which specific dimension caused the drop, without manually writing 50 GROUP BY queries?",
 "You use a Contribution Analysis technique. You calculate the absolute delta (Yesterday DAU - Baseline DAU) for the overall metric. You then write a script or SQL macro to unpivot/iterate through every dimension value, calculating each segment's absolute delta. You divide the segment's delta by the overall delta to calculate its '% Contribution to the Variance'. The segments contributing >80% to the variance instantly bubble to the top.",
 ["Use Contribution Analysis (Variance Analysis)", "Calculate the absolute delta for the overall metric, then the absolute delta for every segment", "Divide segment delta by overall delta to find '% Contribution'. Sort descending to find the culprit."],
 ["Print out all the data and physically highlight the lowest numbers"]),

("ROOT_CAUSE_ANALYSIS", "fundamentals", "medium", "concept", ["Diagnostic Frameworks"],
 "In root cause analysis, what is the 'Five Whys' framework?",
 "The Five Whys is an iterative diagnostic technique used to drill past superficial symptoms to uncover the fundamental systemic root cause of a defect. By repeatedly asking 'Why?' (typically five times) after each answer, the analyst moves from 'The metric dropped' to 'The tracking failed' to 'The deployment overwrote the tag' to 'There is no automated test for analytics tags in the CI pipeline'.",
 ["An iterative diagnostic technique to drill past superficial symptoms", "Repeatedly asking 'Why?' to uncover the fundamental systemic root cause", "Moves the investigation from metric symptoms to underlying process/system failures"],
 ["It is a framework where you ask five different people why they think the metric dropped"]),

("ROOT_CAUSE_ANALYSIS", "scenario", "hard", "scenario", ["Segmentation", "Macro Events"],
 "You are analyzing a sudden spike in 'Customer Support Tickets'. You segment by 'Ticket Category' and see all categories spiked equally. You segment by 'Country' and see all countries spiked equally. You segment by 'Device' and see all devices spiked equally. What does a perfectly uniform spike across all dimensions indicate about the root cause?",
 "A perfectly uniform spike across all segments strongly indicates an external macro event or a centralized infrastructure failure, rather than a localized product bug or a specific targeted marketing campaign. For example, the primary payment gateway for the entire platform went down globally, or a massive PR event drove a 5x spike in overall traffic, raising support tickets proportionally across the board.",
 ["Indicates an external macro event or centralized infrastructure failure", "Rules out localized product bugs or targeted marketing campaigns", "Examples: Global payment gateway failure, or a massive PR-driven traffic spike"],
 ["It indicates the support tickets are multiplying synthetically via a virus"])
]
