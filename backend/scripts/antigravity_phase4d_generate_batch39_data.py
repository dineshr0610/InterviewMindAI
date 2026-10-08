import os

ROLE = "Data Analyst"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b1": ("Advanced SQL", "Window Functions & CTEs", "SQL", ["Data Analyst", "Data Engineer"]),
    "b2": ("Statistical Reasoning", "A/B Testing & Stats", "Statistics", ["Data Analyst", "Data Scientist"]),
    "b3": ("Root Cause Analysis", "Metric Investigation", "Analytics", ["Data Analyst"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    (
        "b1",
        "implement",
        "medium",
        "problem_solving",
        ["Business Analytics", "Data Transformation"],
        "You need to build a 3-step funnel analysis in SQL: Users who Visited (Step 1), Added to Cart (Step 2), and Purchased (Step 3). The events are stored in a single `user_events` table. How do you implement this efficiently without relying on expensive, slow self-joins?",
        "To avoid expensive self-joins on a massive events table, you can implement the funnel using conditional aggregation (PIVOT logic) grouped by user. You write a query grouping by `user_id`, using `CASE` statements to flag if the user completed each step: `MAX(CASE WHEN event = 'visited' THEN 1 ELSE 0 END) AS step1`, `MAX(CASE WHEN event = 'added_to_cart' THEN 1 ELSE 0 END) AS step2`, etc. To enforce strict chronological funnel sequence, you can augment the `CASE` statement with timestamp comparisons, or better, use Window Functions like `LEAD()` or `MIN(timestamp) OVER (PARTITION BY user_id)` to ensure step 2 occurred strictly after step 1. Finally, you wrap this user-level CTE in an outer query that sums up the flags (`SUM(step1)`, `SUM(step2)`) to get the absolute counts for each funnel stage.",
        [
            "Proposes using conditional aggregation (`MAX(CASE WHEN...)`) to flatten events per user without self-joins.",
            "Mentions using window functions or timestamp comparisons to enforce strict chronological ordering of funnel steps.",
            "Wraps the logic in an outer query to aggregate user-level flags into funnel stage totals."
        ],
        [
            "Suggests joining the `user_events` table to itself three times, ignoring the prompt's constraint about self-joins.",
            "Fails to address how to ensure the events happened in the correct sequence."
        ]
    ),
    (
        "b1",
        "diagnose",
        "hard",
        "debugging",
        ["Advanced SQL", "Data Quality"],
        "A business stakeholder complains that a dashboard shows 500,000 total sales for a region, but the operational database only has 10,000 actual transactions. The underlying SQL query uses multiple CTEs and left joins. How do you diagnose and locate the source of this massive data explosion?",
        "This massive metric inflation is caused by a fan-out (Cartesian product / cross-join explosion) occurring within the query's joins. It happens when joining two tables on a non-unique key, causing a single transaction row to multiply. To diagnose, I would systematically isolate the CTEs. First, I would run a simple `COUNT(1)` and `COUNT(DISTINCT transaction_id)` on the base table. Then, I would execute each CTE sequentially, comparing the row counts at each step. The CTE where the row count suddenly multiplies relative to the unique transaction IDs is the culprit. Once identified, I would inspect the `JOIN` condition in that CTE to find the missing granularity—such as joining a transactions table to an items table without including the specific `item_id`, or joining to a dimension table that contains duplicate dimensional records (e.g., multiple status changes per order). To fix, I would either add the missing join keys, or pre-aggregate/deduplicate the right-hand table before joining.",
        [
            "Identifies a 'fan-out' or many-to-many join explosion as the root cause.",
            "Describes a systematic debugging approach: checking row counts and distinct IDs at each CTE step.",
            "Suggests resolutions: adding missing join conditions or pre-aggregating the dimension table."
        ],
        [
            "Assumes the dashboard tool itself is magically multiplying the numbers.",
            "Suggests just dividing the final number by 50 to make it look right."
        ]
    ),
    (
        "b1",
        "compare",
        "easy",
        "conceptual",
        ["Advanced SQL", "Business Analytics"],
        "When performing a cohort analysis in SQL to rank users by their total spending, what is the practical difference in the output of `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()` if two users have the exact same spending amount?",
        "`ROW_NUMBER()` assigns a strictly unique, sequential integer to every row, regardless of ties. If two users tie for 2nd place, one will arbitrarily get 2 and the other 3 (unless a secondary ordering is defined). `RANK()` assigns the same rank to tied rows, but skips subsequent ranks. If two users tie for 2nd place, both receive rank 2, and the next user in the list receives rank 4 (rank 3 is skipped). `DENSE_RANK()` also assigns the same rank to tied rows, but does not skip subsequent ranks. If two users tie for 2nd place, both receive rank 2, and the next user receives rank 3. For a business use case, `ROW_NUMBER()` is used for deduplication or selecting exactly 'Top N', while `RANK` or `DENSE_RANK` is used when ties represent true equal business standing.",
        [
            "Accurately explains `ROW_NUMBER()` assigns unique sequential integers (no ties).",
            "Accurately explains `RANK()` allows ties but skips subsequent numbers.",
            "Accurately explains `DENSE_RANK()` allows ties and does not skip numbers."
        ],
        [
            "Confuses `RANK()` and `DENSE_RANK()`.",
            "Fails to explain what happens to the subsequent numbers after a tie."
        ]
    ),
    (
        "b1",
        "optimize",
        "medium",
        "problem_solving",
        ["Advanced SQL", "Performance"],
        "An analytical query calculating the 'percentage of total regional sales' for every store is running extremely slow. It currently uses a correlated subquery in the SELECT clause to calculate the regional denominator for each row. How do you optimize this SQL query?",
        "Correlated subqueries evaluate row-by-row, which is highly inefficient for large analytical datasets because the database engine must execute the subquery for every single store record. To optimize this, the correlated subquery should be replaced entirely with an analytical Window Function. I would calculate the percentage by dividing the store's sales by `SUM(store_sales) OVER (PARTITION BY region)`. This Window Function calculates the regional total in a single optimized pass over the data without requiring self-joins, subqueries, or group-by aggregations that lose the row-level store granularity. This converts an O(N^2) or iterative operation into a highly vectorized O(N) operation, drastically reducing execution time and database compute cost.",
        [
            "Identifies the row-by-row inefficiency of correlated subqueries.",
            "Proposes replacing the subquery with `SUM(...) OVER (PARTITION BY region)`.",
            "Explains that window functions allow aggregating data (the denominator) while preserving row-level detail in a single pass."
        ],
        [
            "Suggests adding more database indexes, which won't solve the fundamental row-by-row subquery logic.",
            "Recommends exporting the data to Excel or Python to do the math."
        ]
    ),
    (
        "b1",
        "scenario",
        "hard",
        "architectural",
        ["Advanced SQL", "Business Analytics"],
        "You are asked to build a daily dashboard showing the 'Rolling 30-Day Active Users' (WMAU). Your daily login events table has 100 million rows. Calculating this by joining the table to itself on a 30-day date inequality (`a.date >= b.date - 30`) crashes the data warehouse. How do you design this query to scale?",
        "Joining a massive daily events table to itself using date inequalities creates an exponential fan-out (Cartesian explosion) that will exhaust database memory. To scale this, you must change the paradigm from self-joins to state-tracking or cumulative arrays. One optimal approach is to pre-aggregate logins into a daily user state table (`user_id`, `activity_date`). Then, use specialized data warehouse functions: in Snowflake/BigQuery, you can use HyperLogLog (`APPROX_COUNT_DISTINCT`) over a sliding window, or array aggregation. Alternatively, use a cross-join to a sequence of 30 days to generate a 'target_date' for every active event, group by that target date, and `COUNT(DISTINCT user_id)`. The most efficient, scalable pattern for massive data is maintaining a daily snapshot table that stores an array or bitmap (like Roaring Bitmaps) of active user IDs per day, and computing the union of the last 30 bitmaps.",
        [
            "Recognizes that inequality self-joins create a massive Cartesian explosion.",
            "Proposes scalable alternatives: HyperLogLog, Array aggregation, Bitmaps, or exploding via a date dimension rather than a self-join."
        ],
        [
            "Suggests just 'using a bigger data warehouse instance'.",
            "Attempts to solve it with a standard `GROUP BY` without addressing the rolling 30-day window overlap."
        ]
    ),
    (
        "b1",
        "diagnose",
        "medium",
        "debugging",
        ["Advanced SQL", "Data Quality"],
        "You run an aggregation on a `users` table `LEFT JOIN`ed to an `orders` table to find user engagement. You notice that `COUNT(*)` gives a significantly higher number than `COUNT(orders.order_id)`. Why are these results different, and which one is correct for counting users who made a purchase?",
        "The difference arises from how SQL aggregate functions handle NULL values in the context of a `LEFT JOIN`. When you use `COUNT(*)`, SQL counts every single row in the joined output result set, regardless of whether the columns contain NULLs. Because it's a `LEFT JOIN`, users without any orders are still included in the result set as rows with NULL order data. Therefore, `COUNT(*)` essentially counts the total number of users (or total users + their duplicate orders). `COUNT(orders.order_id)` specifically counts only the non-NULL values in the `order_id` column. Users who made no purchases have a NULL `order_id` and are ignored by this count. To accurately count the number of users who made a purchase, you should strictly use `COUNT(orders.order_id)` (or `COUNT(DISTINCT users.user_id) WHERE orders.order_id IS NOT NULL`).",
        [
            "Explains that `COUNT(*)` counts all rows including those with NULLs generated by the `LEFT JOIN`.",
            "Explains that `COUNT(column)` ignores NULL values.",
            "Correctly concludes that `COUNT(orders.order_id)` is the appropriate metric for counting purchases."
        ],
        [
            "Claims `COUNT(*)` is faster and therefore the results are a caching issue.",
            "States the difference is caused by duplicate user IDs without mentioning NULL handling."
        ]
    ),
    (
        "b1",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Advanced SQL", "Data Transformation"],
        "When designing the data layer for a BI dashboard, what are the tradeoffs between querying raw tables using complex CTEs on-the-fly versus building a pre-aggregated Materialized View in the data warehouse?",
        "Querying raw tables with complex CTEs on-the-fly ensures that the dashboard always displays the freshest, real-time data, and it provides infinite flexibility for business users to drill down into the lowest level of granularity. However, the tradeoff is severe performance degradation (slow dashboard load times) and high compute costs on the data warehouse, as the complex aggregations are re-calculated every time a user loads or filters the dashboard. Building a pre-aggregated Materialized View drastically improves dashboard load performance (sub-second queries) and reduces compute costs because the aggregations are computed once. The tradeoffs are data staleness (the view must be refreshed on a schedule, e.g., hourly or daily), a loss of drill-down capability if the required granularity was aggregated away, and increased maintenance overhead in the data pipeline (dbt models, cron jobs).",
        [
            "Contrasts the real-time freshness and drill-down flexibility of on-the-fly queries with their high cost and slow performance.",
            "Contrasts the high performance and lower query cost of Materialized Views with their data staleness and lack of granular drill-down."
        ],
        [
            "Claims Materialized Views are always real-time.",
            "Fails to mention compute costs or dashboard load latency as a tradeoff."
        ]
    ),
    (
        "b2",
        "diagnose",
        "hard",
        "problem_solving",
        ["Statistical Reasoning", "Business Analytics"],
        "An A/B test for a new checkout flow shows that the treatment variant has a lower overall conversion rate than the control. However, when you segment the data by device type (Mobile vs Desktop), the treatment variant actually has a *higher* conversion rate on Mobile AND a *higher* conversion rate on Desktop. What statistical paradox is occurring, and how do you diagnose the root cause?",
        "This is Simpson's Paradox, where a trend appears in different groups of data but disappears or reverses when these groups are combined. In the context of an A/B test, this almost always indicates a severe Sample Ratio Mismatch (SRM) or an imbalance in traffic distribution. To diagnose the root cause, I would calculate the proportion of Mobile vs. Desktop traffic in the Control group versus the Treatment group. The paradox occurs because the underlying segments have vastly different baseline conversion rates (e.g., Desktop converts at 10%, Mobile at 2%), and the A/B testing router accidentally sent a disproportionately large amount of low-converting Mobile traffic to the Treatment group. The treatment improved the specific device conversion, but the heavy weighting of low-converting mobile traffic dragged the overall blended treatment average down. The test results are invalid due to the traffic allocation bug.",
        [
            "Correctly identifies the phenomenon as Simpson's Paradox.",
            "Diagnoses the root cause as a traffic allocation imbalance (uneven distribution of segments across variants).",
            "Explains how differing baseline rates combined with uneven weighting invert the aggregated metric."
        ],
        [
            "Assumes the math in the dashboard tool is simply broken.",
            "Suggests launching the feature anyway because the segments look good, completely ignoring the traffic bug."
        ]
    ),
    (
        "b2",
        "compare",
        "medium",
        "conceptual",
        ["Statistical Reasoning", "Business Analytics"],
        "When evaluating the results of an A/B test on revenue per user (ARPU), why might an analyst choose to use a Mann-Whitney U test (or a bootstrapped method) instead of a standard two-sample T-test?",
        "A standard two-sample T-test assumes that the sample means are normally distributed (which relies on the Central Limit Theorem for large sample sizes) and is highly sensitive to outliers. Revenue data (ARPU) is notoriously non-normal, extremely right-skewed (most users spend $0, a few spend $10, and a tiny fraction of 'whales' spend $10,000), and variance is extremely high. In a standard T-test, a single massive outlier can drastically inflate the mean and variance, causing the test to return a false positive or lose statistical power. The Mann-Whitney U test is a non-parametric test that evaluates the differences in the *ranks* of the data rather than the absolute values, making it highly robust against extreme outliers. Alternatively, bootstrapping estimates the confidence intervals of the mean by repeatedly resampling the data with replacement, providing an accurate distribution without assuming normality. You use these methods to prevent outliers from corrupting the experiment analysis.",
        [
            "Identifies that revenue data is highly right-skewed and prone to extreme outliers.",
            "Explains that the T-test is sensitive to outliers and relies on normality assumptions.",
            "Explains that Mann-Whitney uses rank-based logic (non-parametric) to mitigate the impact of outliers."
        ],
        [
            "Claims T-tests can only be used on boolean (conversion) data.",
            "Asserts that Mann-Whitney is just a faster computational algorithm than a T-test."
        ]
    ),
    (
        "b2",
        "diagnose",
        "medium",
        "problem_solving",
        ["Root Cause Analysis", "A/B Testing & Stats"],
        "Your product team runs an A/B test introducing a 'Quick Buy' button. The test shows a statistically significant 20% uplift in 'Quick Buy' clicks. However, the overall company revenue remained completely flat during the test. How do you diagnose this discrepancy?",
        "This scenario indicates that the local metric ('Quick Buy' clicks) improved, but the global business metric (Revenue) did not, pointing to Cannibalization or a shift in user behavior rather than net-new growth. To diagnose, I would investigate the 'standard checkout' funnels for both the control and treatment groups. It is highly likely that the 20% increase in 'Quick Buy' clicks came entirely at the expense of standard checkout clicks—users simply changed the path they took to buy the exact same items they were already going to buy. Additionally, I would check the Average Order Value (AOV); the 'Quick Buy' might encourage single-item purchases, cannibalizing larger multi-item cart purchases, offsetting any gains in transaction volume. Finally, I would check for a 'Novelty Effect' by plotting the click rate over time to see if the engagement spiked initially and then decayed back to the baseline.",
        [
            "Identifies Cannibalization (shifting behavior from one path to another) as the primary cause.",
            "Recommends analyzing the alternative/standard checkout metrics to prove the shift.",
            "Mentions checking Average Order Value (AOV) or looking for a Novelty effect."
        ],
        [
            "Assumes the statistical significance calculation is broken.",
            "Suggests that the overall revenue must be broken in the database."
        ]
    ),
    (
        "b2",
        "optimize",
        "hard",
        "best_practices",
        ["Statistical Reasoning", "Data Transformation"],
        "You are running an A/B test on a low-traffic B2B landing page. A standard power calculation says you need 3 months to reach statistical significance, which is too slow for the business. How can you statistically optimize the test to reduce variance and reach significance faster?",
        "To reach statistical significance faster without compromising integrity, you must reduce the variance (noise) in the underlying metric. The most common advanced technique is CUPED (Controlled-Experiment Using Pre-Experiment Data). CUPED adjusts the target metric by regressing it against a covariate—typically the user's behavior *before* the experiment started. By subtracting the pre-experiment variance (e.g., historical revenue) from the during-experiment variance, the residual variance is much smaller. This drastically increases the statistical power of the test, allowing you to detect the same Minimum Detectable Effect (MDE) with a significantly smaller sample size (or in less time). Other optimizations include using a more sensitive, upstream proxy metric (e.g., 'add to carts' instead of 'completed purchases', since upstream actions happen more frequently and have higher baseline rates), or employing Stratified Sampling during assignment.",
        [
            "Proposes variance reduction techniques like CUPED (using pre-experiment covariate data).",
            "Suggests utilizing more sensitive, higher-frequency upstream proxy metrics.",
            "Clearly explains how reducing variance or increasing the baseline rate reduces required sample size/time."
        ],
        [
            "Suggests artificially lowering the confidence level (e.g., to 50%) just to finish faster.",
            "Recommends stopping the test as soon as the p-value dips below 0.05 (peeking/early stopping)."
        ]
    ),
    (
        "b2",
        "compare",
        "easy",
        "conceptual",
        ["Statistical Reasoning", "Business Analytics"],
        "An A/B test on a website's font color yields a p-value of 0.01, indicating a statistically significant increase in conversion rate. However, the business decides not to roll out the new font. Explain the difference between statistical significance and practical (business) significance in this context.",
        "Statistical significance (indicated by a low p-value, like 0.01) simply means that the observed difference between the control and treatment groups is very unlikely to be due to random chance or noise. It proves the effect exists, but it does not measure the *size* or *value* of that effect. Practical (business) significance evaluates whether the magnitude of the effect is large enough to matter in the real world. In this context, if the website has massive traffic, a conversion rate increase from 5.000% to 5.001% might be highly statistically significant because of the large sample size. However, the absolute revenue gained from that 0.001% uplift might only be $50 a year. If the engineering cost to permanently change and maintain the new font codebase is $5,000, the change lacks practical significance. A data analyst must evaluate both: the math proves it's real, the business context proves if it's worth it.",
        [
            "Defines statistical significance as confidence that the result is not due to random chance.",
            "Defines practical significance as the real-world magnitude or ROI of the change.",
            "Provides a clear example where a mathematically real result is too small to justify implementation costs."
        ],
        [
            "Claims a p-value of 0.01 means a 1% increase in conversion.",
            "Argues that if a test is statistically significant, it must always be implemented regardless of cost."
        ]
    ),
    (
        "b2",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Statistical Reasoning", "Business Analytics"],
        "A product manager notices the A/B test p-value dropped to 0.04 on day 3 of a planned 14-day experiment. They want to stop the test early and declare a winner. What are the statistical tradeoffs of this 'peeking' behavior, and how can an analyst mitigate it?",
        "Stopping a frequentist A/B test the moment the p-value dips below the significance threshold (0.05) is known as 'peeking' or continuous monitoring. The tradeoff is a massive inflation of the False Positive rate (Type I error). Because p-values naturally fluctuate wildly in the early days of an experiment due to small sample sizes, if you peek continuously and stop at the first sign of significance, you are virtually guaranteed to find a 'winner' even if there is zero true effect (an A/A test will often show significance if peeked enough). To mitigate this, an analyst must enforce the fixed horizon rule: determine the sample size beforehand and do not analyze the p-value until the end. If the business absolutely requires early stopping, the analyst must switch to Sequential Testing frameworks (like the Sequential Probability Ratio Test, SPRT, or alpha-spending functions) or use Bayesian A/B testing methodologies which are more robust to continuous monitoring.",
        [
            "Identifies 'peeking' as inflating the False Positive (Type I error) rate.",
            "Explains that early fluctuations are noise, not true effects.",
            "Recommends mitigating via strict fixed-horizon enforcement, Sequential Testing, or Bayesian methods."
        ],
        [
            "Agrees with the PM that day 3 is fine if the math is correct.",
            "Confuses peeking with Sample Ratio Mismatch."
        ]
    ),
    (
        "b2",
        "diagnose",
        "medium",
        "debugging",
        ["Statistical Reasoning", "Data Quality"],
        "You set up an A/B test with an intended 50/50 traffic split. After one week, the Control group has 100,000 users and the Treatment group has 95,000 users. How do you diagnose if this is normal variance or a critical tracking bug?",
        "This scenario describes a potential Sample Ratio Mismatch (SRM). While a 50/50 split will rarely yield exactly identical numbers, a deviation of 5,000 users across 195,000 total is highly suspicious. To diagnose, I would run a Chi-Squared goodness-of-fit test comparing the observed traffic (100k vs 95k) against the expected traffic (97.5k vs 97.5k). Given these high numbers, the Chi-Squared p-value will be microscopically close to zero, proving this is not normal variance but a systemic SRM bug. Once SRM is confirmed, the entire experiment's metrics are invalid. To find the root cause, I would investigate the assignment pipeline: Is the hashing function skewing assignments? Is the treatment group causing a severe page crash before the analytics pixel fires (survivorship bias)? Are bots skewing the control group? I would segment the SRM by browser, device, and day to isolate where the tracking drop-off occurs.",
        [
            "Identifies the phenomenon as Sample Ratio Mismatch (SRM).",
            "Proposes using a statistical test (Chi-Squared Goodness of Fit) to prove the deviation is not random noise.",
            "Outlines practical debugging steps (checking for survivorship bias, hashing bugs, or bot traffic)."
        ],
        [
            "Assumes a 5,000 user difference is totally normal in large datasets.",
            "Suggests just weighting the treatment metrics by a 1.05x multiplier to 'fix' the mismatch."
        ]
    ),
    (
        "b3",
        "diagnose",
        "hard",
        "problem_solving",
        ["Root Cause Analysis", "Business Analytics"],
        "Overall conversion rate on your e-commerce site suddenly dropped by 15% yesterday. Top-line traffic volume is stable, and engineering confirms there were no code deployments or outages. Walk through your analytical process to diagnose the root cause.",
        "When an aggregate metric drops while top-line volume is stable, the issue is almost always hidden within specific segments or external data quality. I approach this using a hierarchical elimination strategy. 1) **Data Pipeline Check**: Verify if the 'purchase' event tracking is delayed or dropping packets in the ETL pipeline. 2) **Segmentation Analysis**: I would slice the conversion rate by dimensions: Device (Mobile vs Desktop), Browser (Safari vs Chrome), Geography, and Traffic Source (Organic, Paid, Email). If I see Safari conversion dropped to zero, it's an iOS update breaking a cookie. If Paid traffic spiked but conversion is low, marketing launched a bad ad campaign bringing in low-intent users, diluting the overall rate (denominator inflation). 3) **Funnel Analysis**: Identify exactly which step of the funnel broke. Did add-to-cart remain stable, but payment submission drop? If so, the third-party payment gateway (like Stripe) might be silently rejecting cards, even if our internal code didn't change. 4) **Product Mix**: Did a popular, high-converting item go out of stock yesterday?",
        [
            "Provides a structured, hierarchical diagnostic framework (Data Integrity -> Segmentation -> Funnel -> External Factors).",
            "Recognizes that denominator inflation (surge in low-intent traffic) can drop rates without a site breakage.",
            "Mentions segmenting by device/browser to find hidden technical bugs, and isolating specific funnel steps."
        ],
        [
            "Panics and assumes the database is deleted.",
            "Only checks one thing (like asking marketing) without using data to isolate the issue."
        ]
    ),
    (
        "b3",
        "diagnose",
        "medium",
        "debugging",
        ["Root Cause Analysis", "Data Cleaning"],
        "Looking at the marketing acquisition dashboard, you notice a sudden, massive 40% spike in 'Direct' traffic, accompanied by a proportional drop in 'Organic Search' and 'Paid Social' traffic. Overall traffic volume remains unchanged. What is the analytical cause of this shift?",
        "This is a classic attribution tracking failure, not a real shift in user behavior. 'Direct' traffic is the analytics fallback bucket; it simply means the analytics tool (like Google Analytics) received a session without any referrer information or UTM parameters. When Organic and Paid drop proportionally to the Direct spike, it means the tracking metadata is being stripped during the user journey. To diagnose the cause, I would investigate recent changes to the website's infrastructure. Common culprits include: 1) A recent implementation of strict cross-domain tracking boundaries or a move from HTTP to HTTPS without proper redirects, which drops referrer headers. 2) A misconfigured redirect link (e.g., a vanity URL or URL shortener) stripping UTM parameters before the page loads. 3) A newly introduced Cookie Consent banner that blocks tracking scripts from reading the initial referring URL upon entry. 4) Marketing launching a huge email/SMS campaign without applying UTM tags.",
        [
            "Identifies that 'Direct' is a fallback for missing referrer data, not necessarily people typing the URL.",
            "Correlates the proportional drop in other channels as proof of metadata stripping, not changing user volume.",
            "Suggests practical technical causes: HTTPS redirects, stripped UTMs, or cookie consent banners."
        ],
        [
            "Assumes users suddenly memorized the URL and stopped using Google.",
            "Suggests the website was hacked."
        ]
    ),
    (
        "b3",
        "compare",
        "medium",
        "conceptual",
        ["Root Cause Analysis", "Statistical Reasoning"],
        "During a holiday sale, the 'Average Order Value' (AOV) metric on the executive dashboard doubles compared to normal days. However, the 'Median Order Value' remains exactly the same. How do you compare these two metrics to diagnose what actually happened during the sale?",
        "The Mean (Average) is highly sensitive to extreme outliers, whereas the Median (the middle value of the sorted dataset) is robust to outliers and represents the typical user experience. If the Mean doubles but the Median remains flat, it indicates a heavily right-skewed distribution. The holiday sale did not convince the typical, everyday customer to spend more money (hence the flat median). Instead, the sale attracted a small handful of 'whale' customers or B2B bulk buyers who made extraordinarily massive purchases, pulling the mathematical average drastically upward. To diagnose further, I would plot a histogram or box plot of the order values to visualize the long tail, and isolate the top 1% of transactions to prove they are driving the entire AOV spike. From a business perspective, marketing should know that the promotion didn't upsell the general audience, but rather attracted bulk buyers.",
        [
            "Correctly contrasts the outlier-sensitivity of the Mean vs. the robustness of the Median.",
            "Diagnoses the scenario as a right-skewed distribution caused by a few massive outlier purchases (whales/bulk buyers).",
            "Suggests using histograms or percentiles to visually confirm the extreme outliers."
        ],
        [
            "Claims the calculation in the database is broken.",
            "Confuses Median and Mode."
        ]
    )
]
