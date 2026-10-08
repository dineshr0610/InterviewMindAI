import os

ROLE = "Data Analyst"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b3": ("Root Cause Analysis", "Metric Investigation", "Analytics", ["Data Analyst"]),
    "b4": ("Business Analytics", "Metric Design", "Analytics", ["Data Analyst", "Data Scientist"]),
    "b5": ("Data Cleaning", "Data Quality & Outliers", "SQL", ["Data Analyst", "Data Engineer"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    (
        "b3",
        "optimize",
        "medium",
        "problem_solving",
        ["Data Transformation", "Data Visualization"],
        "A critical executive dashboard takes 45 seconds to load because the underlying SQL query is dynamically aggregating 50 million rows of granular event data. Without changing the BI tool, how do you optimize the data model to achieve sub-second load times?",
        "To optimize BI dashboard performance, you must shift the computational burden from 'read-time' to 'write-time' by pre-aggregating the data. I would build a Materialized View or an automated ETL table (using dbt or Airflow) that rolls up the 50 million granular events into a daily or hourly summary table. Crucially, to maximize performance, I must reduce the 'cardinality' of the data. I would strip out high-cardinality, unneeded dimensions (like `user_id` or `session_id`) and only group by the dimensions the executives actually filter by (e.g., `date`, `region`, `device_type`). This reduces the 50 million row table to a few thousand rows. The BI tool then queries this tiny summary table, rendering the charts in milliseconds.",
        [
            "Identifies pre-aggregation (Materialized Views, summary tables) as the primary solution.",
            "Mentions the importance of reducing cardinality (removing high-granularity dimensions like user_id) to shrink the final table size."
        ],
        [
            "Suggests turning on 'caching' in the BI tool, which only helps the second viewer, not the first.",
            "Recommends buying a faster database without attempting data modeling optimizations."
        ]
    ),
    (
        "b3",
        "scenario",
        "medium",
        "analytical",
        ["Root Cause Analysis", "Business Analytics"],
        "A subscription product's overall Day-30 retention rate has been slowly declining for three months. However, when you look at the retention of individual cohorts (e.g., Organic users, Paid users, Referral users), their specific retention rates are totally flat and stable. How is this mathematically possible?",
        "This is a classic 'Mix Shift' problem, closely related to Simpson's Paradox. The overall retention metric is a weighted average of the underlying acquisition cohorts. If the individual cohort retention rates are stable, the decline in the overall average is caused by a change in the *proportion* of those cohorts in the user base. For example, Organic users might have a high retention rate (60%), while Paid users have a low retention rate (20%). If the marketing team aggressively scaled up Paid advertising over the last three months, the low-retaining Paid users now make up a much larger percentage of the total user base. This mathematically drags the blended average down, even though the product experience hasn't degraded for any specific group. The product isn't breaking; the acquisition mix is shifting toward lower-quality traffic.",
        [
            "Identifies the phenomenon as a Mix Shift or Simpson's Paradox.",
            "Explains that the blended average drops because a lower-performing cohort is growing disproportionately larger in volume."
        ],
        [
            "Assumes the data tracking for retention is broken.",
            "Blames the product team for shipping a bad feature, ignoring the stable segment rates."
        ]
    ),
    (
        "b3",
        "diagnose",
        "hard",
        "debugging",
        ["Root Cause Analysis", "Statistical Reasoning"],
        "A data science team provides you with a 'Churn Prediction Score' to add to your operational dashboard. You notice that the score has 99.9% accuracy—it perfectly flags users who churned. However, when the business tries to use it proactively on active users, it fails completely. What analytical flaw caused this?",
        "This is a classic case of 'Data Leakage' (or target leakage) in the predictive model's training dataset. Data leakage occurs when the model is trained using features that logically occur *after* the target event, or features that are direct proxies for the target. In this scenario, the data scientists likely included a feature like `account_status_last_updated` or `cancellation_reason_code` in the training data. The model learned that if `cancellation_reason_code IS NOT NULL`, the user churns. It achieves 99.9% accuracy on historical data because it's looking at the answer key. However, for active users in the real world, that feature is always null until they actually cancel, rendering the model useless for *predicting* future behavior. To fix this, the training dataset must be strictly point-in-time, masking all data generated after the exact moment of prediction.",
        [
            "Correctly identifies the issue as 'Data Leakage' or 'Target Leakage'.",
            "Explains how including post-event or proxy features artificially inflates historical accuracy but destroys predictive power.",
            "Suggests using strictly point-in-time data for model evaluation."
        ],
        [
            "Assumes the dashboard is filtering the data incorrectly.",
            "Claims the model needs more data to be accurate on active users."
        ]
    ),
    (
        "b3",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Root Cause Analysis", "Business Analytics"],
        "When analyzing engagement on a news media website, what are the analytical tradeoffs between using Session-based metrics (e.g., Pages per Session) versus User-based metrics (e.g., Pages per User per Month)?",
        "Session-based metrics measure short-term, immediate intent. They are highly sensitive to UI changes, navigation friction, and clickbait, making them excellent for evaluating tactical A/B tests (like changing a headline). However, session metrics are easily inflated by fragmented behavior (e.g., a user opening links in new tabs or returning multiple times a day due to short session timeouts). User-based metrics measure long-term value and loyalty across multiple visits. They accurately capture the holistic relationship a reader has with the site (e.g., subscribing to a newsletter and reading weekly). The tradeoff is that user-based metrics are much harder to track accurately due to cross-device usage, cookie clearing, and the need for authenticated logins. Optimizing purely for sessions might encourage clickbait, while optimizing for users encourages deep, recurring journalistic value.",
        [
            "Contrasts session metrics (short-term intent, easy to track, prone to fragmentation/clickbait) with user metrics (long-term loyalty, holistic value).",
            "Identifies the technical difficulty of tracking user metrics (cross-device, cookies) versus the simplicity of session metrics."
        ],
        [
            "Claims that sessions and users are the exact same thing.",
            "Fails to tie the metrics to actual business outcomes like loyalty or A/B testing."
        ]
    ),
    (
        "b4",
        "implement",
        "medium",
        "best_practices",
        ["Business Analytics", "Metric Design"],
        "You are tasked with designing the 'North Star' metric for a two-sided gig economy marketplace (like Uber or TaskRabbit). Why would 'Total App Downloads' or 'Weekly Active Users (WAU)' be poor choices, and how would you design a better metric?",
        "'Total App Downloads' is a vanity metric; it only measures top-of-funnel marketing success, completely ignoring retention, engagement, and actual business value. 'Weekly Active Users (WAU)' is slightly better but still flawed for a marketplace, because a user merely opening the app to browse does not generate liquidity or revenue. A true North Star metric must capture the core value delivered to both sides of the marketplace and align directly with revenue. For a gig economy app, a strong North Star metric would be 'Weekly Transacting Users' or 'Number of Completed Jobs per Week'. This metric guarantees that demand (consumers booking) and supply (workers completing jobs) are successfully matching. It is actionable, reflects true platform liquidity, and is highly correlated with the company's financial success.",
        [
            "Dismisses 'Downloads' as a vanity metric and 'WAU' as lacking business value/revenue alignment.",
            "Proposes a transactional metric (e.g., 'Completed Jobs', 'Transacting Users') that measures core marketplace liquidity.",
            "Explains that the North Star must align with the value delivered to both sides of the marketplace."
        ],
        [
            "Suggests using 'Total Revenue' as the North Star, which is a lagging outcome, not an actionable product metric.",
            "Defends WAU as the best metric because 'investors like it'."
        ]
    ),
    (
        "b4",
        "compare",
        "easy",
        "conceptual",
        ["Business Analytics", "Metric Design"],
        "In marketing analytics, how do Last-Click, First-Click, and Multi-Touch attribution models differ when evaluating a customer's journey?",
        "Attribution models determine how credit for a conversion (sale) is assigned to different marketing touchpoints. **First-Click** attribution gives 100% of the credit to the very first channel the user interacted with (e.g., a Facebook Ad that introduced the brand). It heavily favors brand-awareness campaigns. **Last-Click** attribution gives 100% of the credit to the final channel the user clicked right before buying (e.g., a Google Branded Search). It is the easiest to track but heavily ignores top-of-funnel efforts. **Multi-Touch** (or fractional) attribution distributes the credit across multiple touchpoints in the journey (e.g., Linear splits it evenly, Time-Decay gives more credit to recent clicks, and U-Shape favors the first and last clicks). Multi-touch provides the most accurate holistic view of the customer journey but is technically complex to implement and analyze.",
        [
            "Defines First-Click as favoring top-of-funnel awareness.",
            "Defines Last-Click as favoring bottom-of-funnel conversion but ignoring the prior journey.",
            "Defines Multi-Touch as distributing credit across the journey, providing a holistic but complex view."
        ],
        [
            "Confuses First-Click and Last-Click.",
            "Claims Multi-Touch means clicking the mouse multiple times on the website."
        ]
    ),
    (
        "b4",
        "diagnose",
        "medium",
        "problem_solving",
        ["Business Analytics", "Root Cause Analysis"],
        "Marketing reports that their Blended Customer Acquisition Cost (CAC) is $10, which looks fantastic. However, the Finance team complains that the company is losing money on advertising. How do you diagnose this discrepancy using metric segmentation?",
        "The discrepancy arises because 'Blended CAC' takes the total marketing spend and divides it by *all* new customers acquired, including Organic users (who cost $0 to acquire). If the brand has strong organic growth, a massive influx of free organic users will mathematically drag the Blended CAC down, hiding the true inefficiency of the paid campaigns. To diagnose this, I would segment the metric to calculate 'Paid CAC'. I divide the total marketing spend strictly by the number of customers acquired *specifically through paid channels*. It's highly likely the Paid CAC is actually $100 (which exceeds the customer LTV, causing the financial losses), but the blended view obscured this by mixing free and paid populations. Marketing should evaluate campaign performance using Paid CAC or marginal CAC, not Blended CAC.",
        [
            "Identifies that Blended CAC mixes free organic traffic with paid traffic, artificially lowering the average.",
            "Proposes calculating 'Paid CAC' (Spend / Paid Customers) to reveal the true cost of advertising.",
            "Explains that a high Paid CAC exceeding LTV is causing the financial loss."
        ],
        [
            "Assumes the Finance team simply calculated the math wrong.",
            "Suggests spending more on marketing to bring the CAC down further."
        ]
    ),
    (
        "b4",
        "optimize",
        "hard",
        "best_practices",
        ["Business Analytics", "Metric Design"],
        "Standard 'Bounce Rate' (percentage of single-page sessions) is failing your content team because a user who reads a 5,000-word article for 10 minutes and leaves is counted exactly the same as a user who leaves after 2 seconds. How do you design and implement a superior engagement metric?",
        "Standard Bounce Rate is fundamentally flawed for single-page applications or long-form content because analytics tools only calculate 'Time on Page' if a second pageview event is fired. To design a superior metric, you must implement an 'Adjusted Bounce Rate' or an 'Engagement Score'. To do this technically, you configure the frontend to fire asynchronous 'heartbeat' events or scroll-depth triggers (e.g., firing an event when the user scrolls 50% of the page, or after they stay active for 30 seconds). You then redefine a 'Bounce' as a session that contains no second pageview AND no interaction events AND lasts less than 30 seconds. Alternatively, you can create a composite 'Active Time' metric that aggregates these heartbeat events, providing a true measure of content consumption rather than punishing successful single-page visits.",
        [
            "Identifies the flaw in traditional analytics: time on page requires a second event to calculate.",
            "Proposes firing heartbeat, timer, or scroll-depth events to measure true engagement.",
            "Designs an 'Adjusted Bounce Rate' that only penalizes true abandonment (e.g., leaving under 10 seconds)."
        ],
        [
            "Suggests forcing the user to click a 'Read More' button to fix the analytics, sacrificing UX for data.",
            "Recommends just ignoring bounce rate entirely."
        ]
    ),
    (
        "b4",
        "scenario",
        "medium",
        "analytical",
        ["Business Analytics", "Metric Design"],
        "Your SaaS company wants to reduce customer churn. The executives are obsessively tracking 'Monthly Cancellation Rate'. Why is this metric insufficient for proactive action, and what alternative metrics should you design?",
        "'Monthly Cancellation Rate' is a Lagging Indicator. By the time a user clicks 'Cancel', the business has already lost them; the metric merely reports the failure after the fact, making it impossible to take proactive, preventative action. To empower the business to prevent churn, an analyst must design Leading Indicators. These are predictive metrics that signal a user is *at risk* of churning before they actually do. Examples include 'Drop in Weekly Active Days', 'Decrease in Core Feature Usage', 'Increase in Customer Support Tickets', or a 'Stagnant Account Score' (no new data entered in 14 days). By tracking and alerting on these Leading Indicators, Customer Success teams can proactively reach out to struggling users and save the account before the cancellation occurs.",
        [
            "Defines Cancellation Rate as a Lagging Indicator (reports history, too late to act).",
            "Proposes designing Leading Indicators (predictive behavioral signals).",
            "Provides examples of leading indicators (drop in usage, support tickets) that allow proactive intervention."
        ],
        [
            "Suggests measuring 'Daily Cancellation Rate' instead to get the data faster.",
            "Misses the distinction between predictive (leading) and historical (lagging) metrics."
        ]
    ),
    (
        "b4",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Business Analytics", "Metric Design"],
        "When optimizing a short-term marketing campaign for a subscription service, what are the tradeoffs of using 'Average Revenue Per User' (ARPU) versus 'Customer Lifetime Value' (LTV) as the success metric?",
        "ARPU (typically calculated monthly or annually) measures the immediate, realized cash flow generated by a user. It is a hard, factual metric that is easy to calculate and highly useful for optimizing short-term cash flow and immediate campaign ROI. However, it completely ignores retention and long-term behavior. LTV attempts to project the total net profit a customer will generate over their entire relationship with the company (incorporating retention curves, gross margin, and discount rates). Using LTV allows marketing to bid higher for high-quality users who might have low initial ARPU but stay for years. The tradeoff is that LTV is heavily modeled and predictive; it relies on assumptions about future retention that may be inaccurate for a brand new cohort. Optimizing purely on LTV risks spending real money today based on hypothetical future models, while optimizing purely on ARPU ignores long-term profitability.",
        [
            "Contrasts ARPU (factual, immediate cash flow, ignores long-term) with LTV (holistic, incorporates retention, highly predictive/hypothetical).",
            "Explains the business risk of LTV: spending actual money today based on modeled future assumptions.",
            "Explains the business risk of ARPU: undervaluing long-term loyal customers."
        ],
        [
            "Claims ARPU and LTV are exactly the same formula.",
            "Fails to acknowledge that LTV relies on predictive modeling and assumptions."
        ]
    ),
    (
        "b4",
        "compare",
        "easy",
        "conceptual",
        ["Business Analytics", "Metric Design"],
        "In product analytics, what is the conceptual difference between measuring 'Monthly Active Users' (MAU) versus measuring the 'Stickiness Ratio' (DAU/MAU)?",
        "MAU (Monthly Active Users) is a volume metric. It simply counts the absolute number of unique users who engaged with the product at least once in a 30-day period. It is useful for measuring the overall size and reach of the user base, but it is easily inflated by massive marketing acquisition (lots of people trying the app once and never returning). The Stickiness Ratio (Daily Active Users divided by Monthly Active Users) is an engagement and frequency metric. It calculates the percentage of your monthly user base that engages with the product on any given day. A high DAU/MAU ratio (e.g., 50%+) indicates a highly habitual, daily-use product (like a social network or messaging app), while a low ratio indicates an episodic, infrequent-use product (like an airline booking app). Stickiness measures loyalty, whereas MAU measures size.",
        [
            "Defines MAU as an absolute volume metric, easily influenced by acquisition.",
            "Defines DAU/MAU (Stickiness) as a frequency/engagement metric measuring habituation.",
            "Contrasts 'size of the user base' with 'loyalty/frequency of the users'."
        ],
        [
            "Claims DAU/MAU measures how many users uninstall the app.",
            "Suggests MAU is a percentage and DAU/MAU is a total count."
        ]
    ),
    (
        "b5",
        "diagnose",
        "hard",
        "debugging",
        ["Data Cleaning", "Advanced SQL"],
        "A daily sales report dashboard in UTC shows a consistent pattern: sales between 8:00 PM and Midnight (EST) are seemingly 'lost' and do not appear in that day's total, but the overall monthly revenue matches the bank exactly. How do you diagnose this anomaly?",
        "This is a classic timezone boundary bug in the data pipeline or SQL aggregation. The database is likely storing transaction timestamps in UTC, while the business operates (and expects reports) in EST (UTC-5). If the SQL query aggregates daily sales using `GROUP BY DATE(transaction_timestamp)` without explicitly casting the timestamp to the EST timezone first, transactions occurring at 8:00 PM EST are recorded as 1:00 AM UTC the *next* day. Therefore, the late-evening sales are not 'lost'; they are bleeding over into tomorrow's reporting bucket. This explains why the daily totals look anomalous (missing evening sales) but the monthly macroscopic total matches perfectly. To diagnose, I would run a raw query comparing `DATE(timestamp)` vs `DATE(CONVERT_TIMEZONE('EST', timestamp))` and aggregate the discrepancy. The fix requires enforcing strict timezone conversions in the BI tool or the ETL semantic layer before date truncation.",
        [
            "Identifies the root cause as a timezone conversion mismatch (e.g., UTC vs EST) at the midnight boundary.",
            "Explains that the sales aren't lost, but are misattributed to the following calendar day.",
            "Suggests diagnosing by comparing raw UTC dates vs Timezone-converted dates."
        ],
        [
            "Assumes the database is dropping packets at night.",
            "Suggests manually adding a percentage to the daily report to make up for the missing sales."
        ]
    ),
    (
        "b5",
        "optimize",
        "medium",
        "best_practices",
        ["Data Cleaning", "Statistical Reasoning"],
        "Your automated data quality checks alert you whenever daily revenue drops below $10,000. As the company grows, revenue naturally increases, making this static threshold useless, while holiday spikes trigger false positive alerts on the way down. How do you optimize this anomaly detection?",
        "Static thresholds are brittle and fail to adapt to seasonality, trend growth, or natural variance. To optimize anomaly detection, you must implement dynamic, statistical thresholds. A robust approach is to calculate a Rolling Z-Score or use the Interquartile Range (IQR) over a trailing window (e.g., the last 30 days). For example, the alert triggers if today's revenue falls more than 3 standard deviations away from the rolling 30-day mean. To handle weekly seasonality (e.g., weekends are naturally lower than weekdays), you can compare today's value against the moving average of the *same day of the week* over the last 4 weeks. For highly seasonal data, applying time-series decomposition (like STL or Prophet) to separate trend, seasonality, and residuals, and then alerting only on extreme residuals, provides the most robust anomaly detection with minimal false positives.",
        [
            "Criticizes static thresholds for failing to handle growth trends and seasonality.",
            "Proposes dynamic statistical methods (Rolling Z-Score, IQR, standard deviations).",
            "Suggests handling seasonality by comparing against the same day-of-week or using time-series decomposition."
        ],
        [
            "Suggests just manually changing the static threshold every morning.",
            "Recommends turning off the alerts entirely to prevent false positives."
        ]
    ),
    (
        "b5",
        "implement",
        "medium",
        "problem_solving",
        ["Data Cleaning", "Python Pandas"],
        "You are preparing a customer dataset for an analytical model. You discover that 15% of the 'Age' column contains NULL values. Walk through your decision-making process for handling these missing values.",
        "Handling missing data requires understanding the mechanism of missingness: Missing Completely At Random (MCAR), Missing At Random (MAR), or Missing Not At Random (MNAR). First, I investigate *why* it's missing. If older users are less likely to provide their age (MNAR), dropping the rows introduces a severe demographic bias. If the missingness is truly random (MCAR) and the dataset is massive, dropping the rows might be acceptable, but it's rarely ideal. Instead, I would use Imputation. For a continuous variable like Age, simple imputation involves filling NULLs with the Median or Mean. However, this artificially reduces variance. A superior approach is conditional imputation (e.g., imputing the median age grouped by another feature like 'Income Bracket' or 'Purchasing Category'). For advanced modeling, I could use predictive imputation (like K-Nearest Neighbors or MICE) or simply create a flag column (`is_age_missing = 1`) and fill NULLs with an arbitrary out-of-range value (like -1) so tree-based models can split on the missingness itself.",
        [
            "Outlines the investigation of missingness types (MCAR, MAR, MNAR) and the risk of bias if dropping rows.",
            "Suggests simple imputation (Mean/Median) and conditional imputation based on other variables.",
            "Mentions advanced techniques like KNN imputation or creating a missingness indicator flag."
        ],
        [
            "Suggests always dropping rows with NULLs immediately.",
            "Recommends filling all NULL ages with 0, which would skew the data toward infants."
        ]
    ),
    (
        "b5",
        "tradeoff",
        "easy",
        "tradeoff",
        ["Data Cleaning", "Data Transformation"],
        "When running automated data quality tests in an ETL pipeline (e.g., using dbt tests), what are the tradeoffs between configuring a test to 'Warn' (silently flag the error but continue) versus 'Error' (halt the entire pipeline)?",
        "Configuring a test to 'Error' (halt the pipeline) ensures strict data integrity. It prevents downstream dashboards and models from serving corrupted, duplicated, or inaccurate data to business stakeholders. The tradeoff is operational brittleness; a minor edge case or a single malformed row will stall the entire pipeline, potentially delaying critical reports (like daily financial close) until an engineer manually fixes it. Configuring a test to 'Warn' maximizes pipeline resilience and uptime, ensuring the data is delivered on time. The tradeoff is that stakeholders might make decisions based on silently flawed data if the analytics team does not actively monitor and resolve the warnings. Best practice is to use 'Error' for critical constraints (like primary key uniqueness or NOT NULL on revenue) and 'Warn' for softer business logic or acceptable anomalies.",
        [
            "Explains that 'Error' ensures data integrity but creates operational brittleness and reporting delays.",
            "Explains that 'Warn' ensures pipeline uptime but risks stakeholders consuming flawed data.",
            "Suggests a balanced approach based on the severity of the column (e.g., PKs vs optional fields)."
        ],
        [
            "Claims 'Warn' automatically fixes the data.",
            "Suggests that data pipelines should never have quality tests."
        ]
    ),
    (
        "b5",
        "diagnose",
        "medium",
        "debugging",
        ["Data Cleaning", "Business Analytics"],
        "The marketing frontend team reports 5,000 unique visitors on the homepage yesterday based on their event tracking script. However, your query in the data warehouse (`COUNT(DISTINCT user_id)`) only shows 4,200 unique visitors for the same page and day. How do you diagnose this discrepancy?",
        "Discrepancies between frontend tracking and backend data warehousing are common and usually stem from definition differences or pipeline loss. I would diagnose this in steps: 1) **Identity Definition**: Frontend scripts often count unique browser cookies or device IDs. If a single user visits on their phone, clears their cookies, and visits again on their laptop, the frontend counts 3 unique visitors. The data warehouse might be counting authenticated `user_id`s, deduplicating that single human into 1 count. 2) **Ad Blockers**: Wait, ad blockers reduce frontend counts, so if backend is lower, it's not ad blockers. 3) **Event Batching & Loss**: Check if the frontend drops events before sending them to the backend (e.g., users closing the browser before the batch fires). 4) **Timezones**: Verify both queries are strictly aligned to the exact same timezone boundary. To prove the root cause, I would query the warehouse using the frontend's anonymous `session_id` or `cookie_id` instead of the authenticated `user_id` to see if the numbers converge.",
        [
            "Identifies the difference between anonymous identities (cookies/devices) and authenticated identities (user_id).",
            "Suggests checking timezone boundaries.",
            "Proposes querying the warehouse using the anonymous identifier to validate the discrepancy."
        ],
        [
            "Blames the database for randomly deleting records.",
            "Assumes the frontend team is intentionally lying about the numbers."
        ]
    ),
    (
        "b5",
        "compare",
        "medium",
        "conceptual",
        ["Data Cleaning", "Data Transformation"],
        "When managing data quality, how does a 'Schema-on-Write' architecture (traditional Data Warehouse) compare to a 'Schema-on-Read' architecture (Data Lake)?",
        "In a Schema-on-Write architecture (Data Warehouse), the structure, data types, and constraints of the table are defined *before* the data is loaded. The ETL pipeline must clean, transform, and validate the incoming data to fit this strict schema. If the data is malformed (e.g., a string instead of an integer), the write fails and the data is rejected. This guarantees high data quality and fast, reliable querying for analysts, but makes the ingestion process rigid and slow to adapt to upstream changes. In a Schema-on-Read architecture (Data Lake), raw data (like JSON or CSV files) is dumped into storage without any validation or transformation. The schema is applied dynamically only when an analyst queries the data. This allows for massive, flexible, and rapid ingestion of unstructured data, but shifts the entire burden of data quality, parsing, and error handling onto the data analyst at query time, often resulting in slower queries and 'data swamps'.",
        [
            "Defines Schema-on-Write: strict validation and transformation during ingestion, guaranteeing quality but increasing rigidity.",
            "Defines Schema-on-Read: raw dumping of data, offering flexible ingestion but shifting the cleaning burden to the analyst at query time."
        ],
        [
            "Confuses the two concepts entirely.",
            "Claims Schema-on-Read is faster for analysts to query."
        ]
    )
]
