"""Batch 19 question content (Data Analyst). Antigravity-native, no Gemini API."""

ROLE = "Data Analyst"

BUCKET_KEYS = {
    "DA_SQL1": ("Advanced SQL", "Window Functions & CTEs", "SQL", ["Data Engineer", "Database Developer"]),
    "DA_SQL2": ("SQL Fundamentals", "Joins & Edge Cases", "SQL", ["Data Engineer"]),
    "DA_BIZ": ("Business Analytics", "Metrics & KPIs", "Analytics", ["Product Manager"]),
    "DA_STAT": ("Statistical Reasoning", "A/B Testing & Stats", "Statistics", ["Data Scientist"]),
    "DA_CLN": ("Data Cleaning", "Data Quality & Outliers", "Analytics", ["Data Engineer", "Data Scientist"]),
    "DA_VIS": ("Data Visualization", "Dashboards & Storytelling", "Tableau/Power BI", ["Business Intelligence"]),
    "DA_PY": ("Data Transformation", "Pandas & Python", "Python", ["Data Engineer", "Data Scientist"]),
    "DA_RCA": ("Root Cause Analysis", "Metric Investigation", "Analytics", ["Product Manager"]),
}

Q = [
# ---------------- DA_SQL1 ----------------
("DA_SQL1", "fundamentals", "medium", "concept", ["SQL"],
 "What is the semantic difference between the `RANK()` and `DENSE_RANK()` window functions?",
 "Both assign a ranking to rows based on an ordering, but they handle ties differently. If two rows tie for 1st place, `RANK()` assigns both a rank of 1, and the next row gets a rank of 3 (leaving a gap). `DENSE_RANK()` assigns both a rank of 1, and the next row gets a rank of 2 (no gaps).",
 ["RANK leaves gaps in numbering after ties", "DENSE_RANK leaves no gaps in numbering after ties", "Both handle ordered rankings"],
 ["RANK is for strings and DENSE_RANK is for numbers"]),

("DA_SQL1", "implement", "medium", "implementation", ["Window Functions"],
 "You have a `sales` table with `user_id`, `transaction_date`, and `amount`. How would you write a SQL query to find the 3-day rolling average sales for each user?",
 "I would use the `AVG()` window function combined with a window frame. The syntax would be `AVG(amount) OVER (PARTITION BY user_id ORDER BY transaction_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`. This partitions the data per user, orders by date, and averages the current row with the two preceding rows.",
 ["Use the AVG() window function", "PARTITION BY user_id ORDER BY transaction_date", "Use a window frame: ROWS BETWEEN 2 PRECEDING AND CURRENT ROW"],
 ["Write a while loop in Python to calculate it"]),

("DA_SQL1", "explain", "easy", "concept", ["SQL"],
 "Explain the purpose of a Common Table Expression (CTE) in analytical SQL. When would you use it over a subquery?",
 "A CTE (defined using the `WITH` clause) allows you to define a temporary, named result set that can be referenced within the main query. It is primarily used to vastly improve query readability, break complex logic into modular steps, and prevent writing the exact same subquery multiple times if the logic needs to be referenced twice.",
 ["Improves readability and modularity using the WITH clause", "Allows breaking complex logic into manageable steps", "Prevents rewriting the same subquery multiple times"],
 ["CTEs are physically stored on the hard drive permanently"]),

("DA_SQL1", "scenario", "hard", "scenario", ["Window Functions"],
 "An analyst wrote a query using `ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY purchase_date)` to find each customer's first purchase. The query works, but customers with multiple purchases on the exact same day get unpredictable results for their 'first' purchase. How do you resolve this non-deterministic behavior?",
 "Because `purchase_date` lacks time precision, there is a tie. The SQL engine resolves ties arbitrarily, leading to non-deterministic results on subsequent runs. To fix this, you must add a secondary, unique tie-breaker to the `ORDER BY` clause, such as the `transaction_id` (e.g., `ORDER BY purchase_date, transaction_id ASC`), guaranteeing stable, repeatable results.",
 ["Ties in the ORDER BY clause cause non-deterministic (random) sorting", "The database engine resolves ties arbitrarily", "Fix by adding a unique tie-breaker like transaction_id to the ORDER BY"],
 ["Use DENSE_RANK instead of ROW_NUMBER"]),

("DA_SQL1", "implement", "hard", "implementation", ["Window Functions"],
 "You need to calculate the month-over-month percentage growth in revenue. How would you write this using the `LAG()` window function?",
 "First, I would aggregate revenue by month. In an outer query (or CTE), I would use `LAG(revenue, 1) OVER (ORDER BY month)` to fetch the previous month's revenue into the current row. Finally, I would calculate the growth as: `(current_revenue - previous_revenue) / previous_revenue * 100.0`. I would also handle division by zero using `NULLIF`.",
 ["Aggregate revenue by month first", "Use LAG(revenue) OVER (ORDER BY month) to get the prior month's value", "Formula: (Current - Previous) / Previous"],
 ["LAG() automatically calculates percentage growth"]),

("DA_SQL1", "tradeoff", "medium", "tradeoff", ["SQL"],
 "What tradeoffs exist between using `UNION` and `UNION ALL` when combining two large datasets for an executive report?",
 "`UNION ALL` simply appends the datasets together, making it incredibly fast. `UNION` appends them but then performs a massive, computationally expensive deduplication step (essentially a `DISTINCT` across all columns). You should always use `UNION ALL` for performance unless you strictly require the removal of exact duplicate rows.",
 ["UNION ALL simply appends and is incredibly fast", "UNION performs an expensive deduplication operation across all rows", "Default to UNION ALL unless deduplication is strictly necessary"],
 ["UNION is for left joins and UNION ALL is for right joins"]),

("DA_SQL1", "debug", "medium", "debugging", ["SQL"],
 "A query calculating the total lifetime value (LTV) of customers uses a `LEFT JOIN` from `customers` to `orders`, and then filters `WHERE orders.status = 'completed'`. Why does this filter accidentally exclude customers with zero orders, and how do you fix it?",
 "A `LEFT JOIN` normally preserves all customers, producing NULLs in the `orders` columns if no order exists. However, adding `WHERE orders.status = 'completed'` forces the query to evaluate `NULL = 'completed'`, which is false, implicitly converting the `LEFT JOIN` into an `INNER JOIN`. To fix it, move the condition into the join clause: `ON customers.id = orders.customer_id AND orders.status = 'completed'`.",
 ["The WHERE clause evaluates NULL = 'completed', filtering out non-buyers", "This implicitly turns the LEFT JOIN into an INNER JOIN", "Fix: Move the condition into the ON clause of the LEFT JOIN"],
 ["Customers with zero orders have negative LTV"]),

# ---------------- DA_SQL2 ----------------
("DA_SQL2", "scenario", "easy", "scenario", ["Aggregations"],
 "You are performing a `LEFT JOIN` between `users` and `transactions`. You run `COUNT(transactions.transaction_id)` and `COUNT(*)`. Why might these two numbers be completely different?",
 "`COUNT(*)` counts the total number of rows returned by the query, including rows where the user had no transactions (resulting in NULL transaction columns). `COUNT(column_name)` explicitly ignores NULL values. Therefore, `COUNT(transactions.transaction_id)` will correctly return only the number of actual transactions, which will be lower than `COUNT(*)`.",
 ["COUNT(*) counts total rows, including NULLs", "COUNT(column_name) ignores NULLs", "Users without transactions produce NULL transaction_ids from the LEFT JOIN"],
 ["The database is corrupt"]),

("DA_SQL2", "debug", "hard", "debugging", ["SQL NULLs"],
 "You write a query with `WHERE customer_id NOT IN (SELECT customer_id FROM blacklisted_customers)`. The query suddenly returns zero rows, even though there are millions of valid customers. What data quality issue in the subquery causes this fatal SQL behavior?",
 "If the subquery returns even a single `NULL` value, the `NOT IN` operator fails globally. `NOT IN (1, 2, NULL)` evaluates as `customer_id != 1 AND customer_id != 2 AND customer_id != NULL`. Because any comparison to `NULL` yields `UNKNOWN` (not True), the entire WHERE clause evaluates to False/Unknown for every row. Fix it by using `NOT EXISTS` or filtering `WHERE customer_id IS NOT NULL` in the subquery.",
 ["A single NULL value in the NOT IN subquery causes global failure", "Comparisons to NULL yield UNKNOWN, failing the boolean logic for all rows", "Fix by using NOT EXISTS or filtering out NULLs in the subquery"],
 ["The blacklisted_customers table is empty"]),

("DA_SQL2", "explain", "medium", "concept", ["Joins"],
 "Explain what a 'Cartesian Explosion' (or fan-out) is when joining tables in SQL, and how it corrupts aggregate metrics like total revenue.",
 "A Cartesian explosion occurs when joining tables with a one-to-many or many-to-many relationship without aggregating first. For example, joining 1 `order` (revenue $100) to 3 `items` will duplicate the order row 3 times. If you `SUM(revenue)` on the resulting table, it will incorrectly report $300 instead of $100. You must aggregate the items before joining, or use `SUM(DISTINCT)` carefully.",
 ["Occurs in one-to-many or many-to-many joins, duplicating the parent row", "Corrupts aggregates (e.g., summing revenue counts the same order multiple times)", "Fix by pre-aggregating the 'many' table before joining"],
 ["It is an explosion on the database server hard drive"]),

("DA_SQL2", "implement", "medium", "implementation", ["SQL Functions"],
 "How do you handle division by zero errors in SQL when calculating conversion rates (e.g., conversions / clicks)?",
 "I would use the `NULLIF` function. By writing `conversions / NULLIF(clicks, 0)`, if clicks are 0, `NULLIF` returns `NULL`. Division by `NULL` returns `NULL` rather than throwing a fatal 'division by zero' error. You can then optionally wrap the whole expression in `COALESCE(..., 0)` to return a clean 0 instead of NULL.",
 ["Use the NULLIF(denominator, 0) function", "Returns NULL if the denominator is 0, preventing fatal errors", "Wrap in COALESCE if you want 0 instead of NULL"],
 ["Use a TRY-CATCH block in SQL"]),

("DA_SQL2", "tradeoff", "medium", "tradeoff", ["Timezones"],
 "What tradeoffs exist between storing timestamps in UTC versus storing them in the local timezone of the user when performing global daily active user (DAU) analytics?",
 "Storing in UTC guarantees absolute chronological consistency, prevents Daylight Saving Time gaps/overlaps, and simplifies system architecture. However, analytical queries calculating 'DAU' for a specific country require complex timezone conversions at query time; otherwise, a user active at 11 PM in Tokyo might be counted on the wrong calendar day in UTC.",
 ["UTC: chronologically consistent, immune to DST, standard architecture", "Local: easier to query DAU exactly as the user experienced the day", "UTC: requires complex query-time timezone conversion for regional reporting"],
 ["UTC means the data is encrypted"]),

# ---------------- DA_BIZ ----------------
("DA_BIZ", "fundamentals", "medium", "concept", ["Business Analytics"],
 "What is Cohort Analysis, and why is it generally more useful than looking at aggregate daily active user (DAU) counts for evaluating product changes?",
 "Cohort Analysis tracks the behavior of a specific group of users (a cohort, usually grouped by signup date) over time. Aggregate DAU masks underlying churn; a product might have flat DAU because massive marketing acquisition is perfectly hiding massive user churn. Cohort analysis exposes the actual retention rate of specific user groups, isolating the true impact of product changes.",
 ["Tracks specific groups of users over time (usually by signup date)", "Aggregate metrics mask underlying churn with new acquisitions", "Cohorts isolate true retention and the impact of specific feature releases"],
 ["Cohorts are just a list of users in alphabetical order"]),

("DA_BIZ", "scenario", "medium", "scenario", ["Root Cause Analysis"],
 "You are analyzing a marketing funnel: Impressions -> Clicks -> Signups -> Purchases. Overall purchase volume dropped 20% yesterday. How do you systematically investigate which stage of the funnel is responsible?",
 "I would calculate the step-by-step conversion rates between every adjacent stage (Click-Through Rate, Signup Rate, Purchase Rate) and compare yesterday's rates to the historical baseline. This isolates the exact step where the drop-off occurred. If Impressions dropped, it's an ad spend/platform issue; if Signup Rate plummeted, it's a landing page/UI issue.",
 ["Calculate step-by-step conversion rates between adjacent stages", "Compare yesterday's specific conversion rates to historical baselines", "Isolate the exact stage (e.g., traffic drop vs. conversion drop)"],
 ["Just ask the marketing team what they did wrong"]),

("DA_BIZ", "explain", "easy", "concept", ["Business Metrics"],
 "Explain the difference between 'Retention Rate' and 'Churn Rate'.",
 "They are inverse metrics measuring user loyalty. Retention Rate is the percentage of users from a specific cohort who continue to use the product after a given time period (e.g., 30 days). Churn Rate is the percentage of users who stop using the product or cancel their subscription over a given time period. Retention = 100% - Churn.",
 ["Retention: percentage of users who stay active", "Churn: percentage of users who cancel or leave", "They are mathematical inverses (Retention = 1 - Churn)"],
 ["Churn rate measures how fast the database processes data"]),

("DA_BIZ", "tradeoff", "hard", "tradeoff", ["Metric Design"],
 "When designing a KPI for customer engagement, what are the tradeoffs of using a 'Mean' (average) session duration versus a 'Median' (50th percentile) session duration?",
 "The Mean incorporates all data, but is highly sensitive to extreme outliers; a few users accidentally leaving a tab open for 24 hours can artificially inflate the mean, providing a false sense of engagement. The Median is robust against outliers and reflects the true 'typical' user experience, but it completely ignores behavioral shifts in the top 10% of your power users.",
 ["Mean: sensitive to extreme outliers (e.g., tabs left open), inflating engagement artificially", "Median: robust to outliers, reflects the 'typical' user", "Median: ignores shifts in the behavior of power users at the tail"],
 ["Mean is only used for financial data"]),

("DA_BIZ", "scenario", "hard", "scenario", ["Statistical Reasoning"],
 "A product manager notices that the average revenue per user (ARPU) for mobile users is $50, and for desktop users is $40. However, when looking at the overall ARPU across the entire company, it is $41. Explain how this mathematical paradox can occur.",
 "This is an example of Simpson's Paradox (or a weighted average imbalance). It occurs because the sample sizes of the two groups are vastly different. If the company has 100 Mobile users ($5,000 revenue) and 9,900 Desktop users ($396,000 revenue), the total revenue ($401,000) divided by the total users (10,000) yields an overall ARPU of $40.10, dragging the total average toward the much larger desktop group.",
 ["Simpson's Paradox / weighted average imbalance", "The sample sizes of the two groups are vastly different", "The massive desktop user base drags the overall average down toward its value"],
 ["The database is rounding numbers incorrectly"]),

("DA_BIZ", "implement", "medium", "implementation", ["Retention Analysis"],
 "How do you conceptually design a query to calculate a 7-day retention metric? What data points are required?",
 "I need a `users` table (for signup date) and an `activity` table (for login events). I join the activity to the user. I filter for users who signed up on 'Day 0'. I then check if those specific users have an activity log exactly on 'Day 7' (or within the 7-day window, depending on definition). The retention rate is (Users active on Day 7) / (Total users in the Day 0 cohort).",
 ["Identify the cohort based on a starting event (signup date / Day 0)", "Join with activity logs to find return events", "Calculate: (Active on Day 7) / (Total in Cohort)"],
 ["Add up all the users and divide by 7"]),

("DA_BIZ", "scenario", "medium", "scenario", ["KPI Analysis"],
 "The marketing team claims a new ad campaign is a massive success because it drove 50,000 new signups (a 100% increase). What secondary metrics must you analyze to determine if this campaign actually generated business value?",
 "Signups are a 'vanity metric'. I must analyze down-funnel metrics such as Customer Acquisition Cost (CAC), Day-7 or Day-30 Retention, and Lifetime Value (LTV) of this specific cohort. If the campaign drove 50,000 bots or low-intent users who never purchased and instantly churned, the campaign actually lost the company money.",
 ["Analyze down-funnel conversion metrics (purchases, active usage)", "Check Cohort Retention (did they stay?) and Lifetime Value (LTV)", "Check Customer Acquisition Cost (CAC) to see if it was profitable"],
 ["Check how many likes the ad got on Facebook"]),

("DA_BIZ", "fundamentals", "easy", "concept", ["Business Metrics"],
 "What is a Leading Indicator versus a Lagging Indicator in business analytics?",
 "A lagging indicator tells you what has already happened (e.g., Total Revenue, Churn Rate); it confirms long-term trends but is too late to act upon. A leading indicator predicts future outcomes (e.g., Daily Active Users, Cart Additions, Support Ticket volume); it changes before the lagging indicator does, allowing the business to take proactive corrective action.",
 ["Lagging: measures past results (Revenue, Churn)", "Leading: predicts future outcomes (Daily Active Users, Cart Additions)", "Leading indicators allow proactive business adjustments"],
 ["Leading indicators are metrics for managers, lagging are for engineers"]),

# ---------------- DA_STAT ----------------
("DA_STAT", "explain", "easy", "concept", ["Statistics"],
 "Explain the difference between Correlation and Causation in data analysis.",
 "Correlation means two variables move together statistically (e.g., ice cream sales and shark attacks both spike in summer). Causation means one variable actively triggers the change in the other. Correlation does not imply causation; they may be linked by a third confounding variable (like warm weather). Establishing causation requires controlled experiments (A/B testing).",
 ["Correlation: variables move together statistically", "Causation: one variable actively causes the change in the other", "Correlation does not imply causation (watch for confounding variables)"],
 ["They mean the exact same thing in statistics"]),

("DA_STAT", "scenario", "medium", "scenario", ["A/B Testing"],
 "An A/B test shows that the new checkout button color increased conversions by 5%, with a p-value of 0.04. The product manager wants to roll it out immediately. What caveats or checks should you perform before recommending the rollout?",
 "While statistically significant (p < 0.05), I must check practical significance: does the 5% lift justify the engineering cost of the change? I also need to check the sample size (is the test properly powered?), ensure the test ran long enough to capture weekly seasonality (e.g., weekends vs weekdays), and verify no 'novelty effect' is artificially boosting the metric.",
 ["Check Practical Significance (is the absolute lift worth the cost?)", "Ensure sufficient sample size/statistical power", "Check for weekly seasonality and Novelty Effects (running the test long enough)"],
 ["Roll it out instantly because p < 0.05 is the absolute law"]),

("DA_STAT", "explain", "hard", "concept", ["Experimentation"],
 "Explain the concept of the 'Novelty Effect' in A/B testing and how you can detect it in your data.",
 "The Novelty Effect occurs when users interact heavily with a new feature simply because it is new and draws attention, causing a temporary spike in metrics. Over time, as users get used to the change, the metrics regress to the baseline. You detect it by tracking the treatment group's performance over time (e.g., plotting day-by-day conversion); a sharp initial spike followed by a steady decline indicates novelty.",
 ["Users interact heavily with a change simply because it's new", "Causes a temporary, artificial spike in metrics", "Detect by plotting day-by-day performance; novelty shows an initial spike then decline"],
 ["It means the feature is so good it wins awards"]),

("DA_STAT", "tradeoff", "medium", "tradeoff", ["Statistics"],
 "What are the tradeoffs of using a 99% confidence interval versus a 95% confidence interval when reporting survey results to leadership?",
 "A 99% confidence interval gives you higher certainty that the true population parameter lies within the range, reducing the risk of false positives. However, the tradeoff is that the interval becomes much wider (less precise). A 95% interval is narrower and more precise/actionable, but carries a higher risk (5%) that the true value lies outside the reported range.",
 ["99% is more certain (less risk of false positive) but yields a wider, less precise range", "95% yields a narrower, more actionable range but carries a 5% error risk", "It's a tradeoff between certainty and precision"],
 ["99% is always exactly 4% better than 95%"]),

("DA_STAT", "debug", "hard", "debugging", ["A/B Testing"],
 "You run an A/B test with 20 different variations simultaneously against a control group to see which color button works best. One variation shows a statistically significant improvement with a p-value of 0.03. Why is this result likely a false positive, and what statistical correction is needed?",
 "This is the Multiple Comparisons Problem. If you test 20 variations using a 95% confidence level (alpha = 0.05), you have a 5% chance of a false positive per test. With 20 tests, you are almost guaranteed (1 - 0.95^20 ≈ 64%) to find at least one 'significant' result purely by random noise. You must apply a statistical correction, like the Bonferroni correction, which drastically lowers the required p-value threshold.",
 ["Multiple Comparisons Problem inflates the overall false positive rate", "With 20 tests at alpha=0.05, a false positive is highly likely by pure chance", "Requires statistical corrections like the Bonferroni correction"],
 ["The testing software has a virus"]),

("DA_STAT", "fundamentals", "easy", "concept", ["Statistics"],
 "What does it mean if a dataset has a 'Right-Skewed' (Positive Skew) distribution, and where does the mean sit relative to the median?",
 "A right-skewed distribution has a long tail of extreme values on the right side (positive side) of the graph, such as income distribution where a few billionaires stretch the tail. Because the mean is sensitive to outliers, it gets pulled to the right, meaning the Mean is substantially greater than the Median.",
 ["Long tail on the right side (positive side) of the distribution", "Caused by extreme high-value outliers (e.g., wealth distribution)", "The Mean is pulled to the right, making it greater than the Median"],
 ["It means the graph is drawn leaning to the right side of the paper"]),

("DA_STAT", "scenario", "medium", "scenario", ["Statistics"],
 "You are asked to select a random sample of 1,000 users to survey about a new feature. How do you ensure the sample is truly representative, and what is 'Selection Bias'?",
 "To ensure representativeness, I would use Stratified Random Sampling, ensuring the sample matches the overall population's demographic breakdown (e.g., age, geo, device type). Selection Bias occurs when the sampling method inadvertently favors specific groups (e.g., only surveying active power-users on Twitter), meaning the results cannot be accurately generalized to the entire user base.",
 ["Use Stratified Random Sampling to mirror population demographics", "Selection Bias occurs when the sample collection method favors specific groups", "Prevents generalizing the results to the entire population"],
 ["Just pick the first 1,000 users in the database table"]),

# ---------------- DA_CLN ----------------
("DA_CLN", "explain", "easy", "concept", ["Data Cleaning"],
 "What are the most common strategies for handling missing values (NULLs) in a dataset before performing statistical analysis?",
 "The most common strategies are: 1) Dropping rows or columns if the missing data is minimal or unrecoverable. 2) Imputation, where you fill missing values with the Mean, Median, or Mode. 3) Forward/Backward filling for time-series data. 4) Creating a separate 'Unknown' category for categorical variables to preserve the row.",
 ["Dropping rows/columns", "Imputation (Mean, Median, Mode)", "Forward-fill/Back-fill for time-series, or 'Unknown' for categories"],
 ["Change all NULLs to the number 999999"]),

("DA_CLN", "scenario", "medium", "scenario", ["Data Cleaning"],
 "You are calculating the average salary of employees at a company, but the CEO's salary of $50,000,000 is heavily skewing the data. How do you statistically identify and handle this outlier without simply deleting it arbitrarily?",
 "I can identify the outlier using the Interquartile Range (IQR) method (values > Q3 + 1.5*IQR) or Z-scores (values > 3 standard deviations). To handle it without deleting it, I could report the Median instead of the Mean, use Winsorization (capping the extreme value at the 99th percentile), or segment the analysis (e.g., 'Executive Salary' vs 'IC Salary').",
 ["Identify using IQR method or Z-scores", "Report the Median instead of the Mean", "Use Winsorization (capping) or segment the analysis into cohorts"],
 ["Change the CEO's salary to $0 to balance it out"]),

("DA_CLN", "debug", "medium", "debugging", ["Data Quality"],
 "You receive a dataset of customer birthdates. Upon exploratory analysis, you notice an enormous spike of users born on January 1, 1900, and January 1, 1970. What is the most likely cause of these spikes, and how do you handle them?",
 "These are default system values. 1970-01-01 is the Unix Epoch (timestamp 0), often defaulted when a system encounters a null or invalid date. 1900-01-01 is a common default for old databases (like SQL Server). I would treat these specific dates as missing values (NULLs) in my analysis rather than actual centenarians, and investigate the upstream data ingestion pipeline.",
 ["1970-01-01 is the Unix Epoch (timestamp 0)", "1900-01-01 is a legacy database default for missing dates", "Treat these spikes as missing values/NULLs, not actual birthdates"],
 ["People born in 1900 just really love using our app"]),

("DA_CLN", "tradeoff", "hard", "tradeoff", ["Imputation"],
 "When dealing with missing numerical data, what are the tradeoffs between dropping the rows entirely, imputing the data using the mean, and imputing the data using a predictive model?",
 "Dropping rows is the safest against introducing artificial bias, but drastically reduces sample size and wastes good data in other columns. Mean imputation is fast and preserves sample size, but artificially reduces variance and destroys correlations. Predictive imputation (e.g., K-Nearest Neighbors) accurately preserves variance and relationships, but is computationally expensive and complex to implement.",
 ["Dropping: safest against bias, but reduces sample size and wastes data", "Mean Imputation: fast, preserves sample size, but destroys variance/correlations", "Predictive Imputation: preserves relationships, but computationally complex"],
 ["Imputing the mean is legally required by GDPR"]),

("DA_CLN", "implement", "medium", "implementation", ["Data Cleaning"],
 "In a large dataset, a categorical column `country` has messy user-entered values (e.g., 'US', 'USA', 'United States', 'U.S.'). How do you approach cleaning and standardizing this field?",
 "I would standardize the text format first by converting everything to uppercase and stripping trailing whitespace and punctuation. Then, I would use a mapping dictionary/lookup table to map known variations ('US', 'USA', 'U.S.') to a canonical value (e.g., 'United States'). For unmapped outliers, I would use fuzzy string matching (like Levenshtein distance) to identify close typos, flagging uncertain ones for manual review.",
 ["Standardize casing and strip whitespace/punctuation", "Use a mapping dictionary/lookup table for known variations", "Use fuzzy string matching (Levenshtein) to catch misspellings"],
 ["Read through all 10 million rows manually and fix them one by one"]),

("DA_CLN", "fundamentals", "easy", "concept", ["Data Analytics Process"],
 "Why is Exploratory Data Analysis (EDA) a critical first step before building dashboards or calculating formal KPIs?",
 "EDA allows the analyst to understand the 'shape' of the data, discover hidden missing values, identify extreme outliers, and catch data ingestion bugs. Without EDA, you risk calculating formal KPIs on fundamentally flawed or corrupt data, leading to wildly inaccurate business dashboards and decisions.",
 ["Identifies missing values, extreme outliers, and data bugs", "Understands the shape/distribution of the data", "Prevents building dashboards on fundamentally corrupt or flawed data"],
 ["EDA is just a way to bill the client for more hours"]),

# ---------------- DA_VIS ----------------
("DA_VIS", "fundamentals", "easy", "concept", ["Visualization"],
 "When would you choose to use a Scatter Plot versus a Bar Chart?",
 "A Scatter Plot is used to show the relationship or correlation between two continuous numerical variables (e.g., ad spend vs. revenue). A Bar Chart is used to compare a single numerical metric across distinct, categorical groups (e.g., total sales by region or department).",
 ["Scatter Plot: relationship between two continuous numerical variables", "Bar Chart: comparing a numerical metric across categorical groups", "Scatter plots reveal correlation and outliers"],
 ["Bar charts are for round numbers, scatter plots for decimals"]),

("DA_VIS", "scenario", "medium", "scenario", ["Dashboard Design"],
 "An executive asks you to build a dashboard with 25 different pie charts to show regional sales breakdowns. Why is this a poor data visualization choice, and what alternative would you recommend?",
 "Humans are neurologically very poor at judging the relative area and angles of circles, making pie charts notoriously hard to read, especially with many slices or multiple charts. Comparing 25 pie charts is impossible. I would recommend horizontal Bar Charts, which use length (a highly accurate visual cue), ordered from largest to smallest, or a geographic heat map.",
 ["Humans are poor at judging angles and areas (making pie charts ineffective)", "Comparing multiple pie charts causes immense cognitive load", "Alternative: Use ordered horizontal Bar Charts (length is easily compared)"],
 ["Pie charts require purchasing a special license to use"]),

("DA_VIS", "tradeoff", "medium", "tradeoff", ["Reporting"],
 "What tradeoffs exist between presenting data using a highly interactive Tableau dashboard versus a static, pre-rendered PDF report?",
 "Interactive dashboards allow users to self-serve, drill down, filter, and answer their own follow-up questions, but they require the user to have data literacy, require active server compute, and risk users misinterpreting data by applying wrong filters. Static PDFs guarantee the user sees exactly the intended narrative/context, require zero compute, and are highly portable, but lack flexibility for ad-hoc questions.",
 ["Dashboards: allow self-serve drill downs, but require data literacy and active compute", "PDFs: guarantee the intended narrative and portability", "Dashboards risk users misinterpreting data via incorrect filtering"],
 ["PDFs are fundamentally more accurate mathematically than dashboards"]),

("DA_VIS", "explain", "hard", "concept", ["Data Visualization Principles"],
 "Explain the concept of 'Data-to-Ink Ratio' introduced by Edward Tufte. How do you apply it to improve a cluttered business chart?",
 "The Data-to-Ink ratio is the proportion of ink (or pixels) used to present actual data compared to the total ink used to draw the graphic. To improve a cluttered chart, you maximize this ratio by ruthlessly removing non-essential 'chartjunk': deleting heavy grid lines, removing 3D effects, removing redundant axis labels, and erasing borders, focusing the viewer entirely on the data points.",
 ["Proportion of ink used for actual data vs. total ink used on the graphic", "Apply by ruthlessly removing 'chartjunk'", "Remove heavy gridlines, 3D effects, borders, and redundant labels"],
 ["It means printing charts uses too much printer ink in the office"]),

("DA_VIS", "debug", "medium", "debugging", ["Visualization"],
 "A dual-axis chart (combo chart) shows revenue growing exponentially as a bar chart, and customer count staying perfectly flat as a line chart. However, raw data shows both doubled. What formatting error on the dual-axis chart causes this massive visual misrepresentation?",
 "The two Y-axes are fundamentally unsynchronized and operating on vastly different scales. Revenue might be scaled from 0 to 1,000,000, while the secondary axis for customer count might be scaled from 0 to 10,000,000, making the doubling of customers visually imperceptible. You must either synchronize the axes (if they share the same unit) or distinctly label and format the independent scales to prevent visual deception.",
 ["The two Y-axes are unsynchronized and on vastly different scales", "Causes visual distortion where growth in one metric appears flat", "Fix by clearly labeling scales, synchronizing axes, or avoiding dual-axis charts entirely"],
 ["The data is stored in the wrong cloud region"]),

("DA_VIS", "scenario", "medium", "scenario", ["Visualization"],
 "You are tasked with visualizing the distribution of user ages in a population. Which chart type is most appropriate, and why?",
 "A Histogram is the most appropriate. It groups the continuous numerical age data into discrete bins (e.g., 18-24, 25-34) and uses bars to show the frequency/count of users in each bin. This perfectly visualizes the distribution, skewness, and central tendency of the ages.",
 ["Use a Histogram", "Groups continuous numerical data into discrete bins", "Visualizes distribution, frequency, and skewness perfectly"],
 ["Use a pie chart with 100 slices for every age"]),

# ---------------- DA_PY ----------------
("DA_PY", "fundamentals", "easy", "concept", ["Pandas"],
 "In Python's Pandas library, what is the difference between `merge()` and `concat()`?",
 "`merge()` is the equivalent of a SQL JOIN; it combines DataFrames horizontally based on matching values in common columns or indices. `concat()` physically glues DataFrames together, either vertically (stacking rows on top of each other, like SQL UNION) or horizontally (glueing columns side-by-side based purely on index, not column values).",
 ["merge(): acts like a SQL JOIN, combining horizontally based on common keys", "concat(): physically glues DataFrames together vertically (UNION) or horizontally", "concat() does not match values, it aligns by index structure"],
 ["merge() deletes data, concat() creates data"]),

("DA_PY", "implement", "medium", "implementation", ["Data Transformation"],
 "You have a Pandas DataFrame with a 'date' column in string format (e.g., '2023-01-01'). How do you convert it to a datetime object and extract just the 'month' into a new column?",
 "I would first convert the column using `df['date'] = pd.to_datetime(df['date'])`. Once it is a proper datetime series, I can access the `.dt` accessor to extract the month: `df['month'] = df['date'].dt.month`.",
 ["Convert using pd.to_datetime(df['date'])", "Use the .dt accessor for datetime properties", "Extract using df['date'].dt.month"],
 ["Use a regex to slice the middle characters of the string"]),

("DA_PY", "debug", "medium", "debugging", ["Pandas"],
 "You execute `df.groupby('category')['sales'].mean()` but the result includes 'NaN' for several categories, even though you know those categories have rows. What data issue causes Pandas to return NaN for a mean aggregation?",
 "Pandas returns 'NaN' for the mean if all the values in the 'sales' column for that specific category are themselves 'NaN' (missing values). The category exists in the index because the grouping column has a value, but mathematically, the mean of an empty set of valid numbers is Not a Number.",
 ["All the 'sales' values for that specific category are missing (NaN)", "The category exists, but the values being aggregated are empty", "The mean of an empty set of numbers evaluates to NaN"],
 ["The group by function is broken in Python"]),

("DA_PY", "tradeoff", "hard", "tradeoff", ["Data Processing"],
 "When processing a 10GB CSV file for analysis, what are the tradeoffs of loading it entirely into a Pandas DataFrame versus processing it in chunks or using a tool like Dask/PySpark?",
 "Pandas loads the entire dataset into RAM, which requires at least 2-3x the file size in memory (e.g., 30GB RAM); it is extremely fast but will throw an OutOfMemory error on standard laptops. Processing in chunks (via `chunksize`) or using Dask/PySpark handles out-of-core, parallelized processing that fits in small RAM, but introduces significant compute overhead, complex syntax, and slower execution for smaller tasks.",
 ["Pandas: loads entirely in RAM, requires massive memory, risks OutOfMemory crashes", "Chunks/Dask/PySpark: out-of-core processing, works on small RAM", "Dask/PySpark: introduces heavy overhead and complexity"],
 ["Pandas is legally restricted from opening files larger than 1GB"]),

("DA_PY", "scenario", "medium", "scenario", ["Pandas"],
 "You have a wide DataFrame with columns `Year`, `Q1_Sales`, `Q2_Sales`, `Q3_Sales`, `Q4_Sales`. You need to visualize this in Tableau. How do you transform this data in Pandas to make it suitable for a standard BI tool?",
 "BI tools expect data in a 'long' or 'tidy' format, not 'wide'. I would use the Pandas `melt()` function (an unpivot operation) to transform the DataFrame. I would set `id_vars=['Year']`, creating two new columns: one for the Quarter name (the variable) and one for the Sales value, drastically increasing row count but making it perfectly formatted for BI aggregation.",
 ["BI tools require 'long' or 'tidy' data formats", "Use the Pandas melt() function to unpivot the wide data", "Transforms quarter columns into variable/value rows"],
 ["Tableau can automatically read any data format perfectly"]),

# ---------------- DA_RCA ----------------
("DA_RCA", "scenario", "hard", "scenario", ["Root Cause Analysis"],
 "Global daily active users (DAU) dropped by exactly 15% yesterday and stayed flat today. Describe your step-by-step analytical framework to isolate the root cause of this drop.",
 "First, I verify the data pipeline (is logging broken?). Second, I segment the drop by dimensions: platform (iOS/Android/Web), geography, app version, and user cohort (new vs returning). Third, I check internal factors: were there new app releases, feature flags, or server outages? Fourth, I check external factors: holidays, competitor launches, or bot purges. Usually, segmenting isolates the drop to a specific intersection (e.g., iOS users in Europe on Version 2.0).",
 ["Verify data engineering/pipeline integrity first", "Segment the metric by dimensions (platform, geo, version, user type)", "Check internal events (releases, outages) and external events (holidays, bot purges)"],
 ["Assume the users just got bored and do nothing"]),

("DA_RCA", "explain", "medium", "concept", ["Analytics"],
 "Why is it critical to segment aggregate metrics (like total revenue) by dimensions (like platform, geography, or user type) when investigating an anomaly?",
 "Aggregate metrics mask opposing trends. Total revenue might be flat, but segmenting could reveal that US revenue grew 50% while European revenue crashed 50% due to a local payment gateway outage. Segmenting is the only way to isolate anomalies, identify localized bugs, and uncover the true drivers of business performance.",
 ["Aggregate metrics mask opposing underlying trends", "One segment could be crashing while another grows rapidly", "Segmenting isolates bugs and uncovers true performance drivers"],
 ["Aggregate metrics are mathematically impossible to trust"]),

("DA_RCA", "scenario", "hard", "scenario", ["Data Validation"],
 "Two different teams built dashboards calculating 'Total Weekly Orders'. Team A's dashboard says 10,000. Team B's says 11,500. As a data analyst, what specific logic differences in their SQL queries would you look for to explain the discrepancy?",
 "I would audit their `WHERE` clauses and `JOINs`. Discrepancies usually stem from defining 'Order' differently: Team A might filter out 'cancelled' or 'refunded' orders, while Team B includes all rows. They might be using different timezones for 'Weekly' (UTC vs Local). They might be querying different underlying tables, or one team's `JOIN` is causing a Cartesian explosion/duplication.",
 ["Check definitions of the metric (e.g., filtering out cancelled/refunded orders)", "Check timezone definitions (UTC vs Local boundaries)", "Check JOIN logic causing duplications or dropped rows"],
 ["Team B is simply lying about the numbers"]),

("DA_RCA", "fundamentals", "medium", "concept", ["Metric Design"],
 "What is a 'Proxy Metric', and when is it appropriate to use one?",
 "A Proxy Metric is an indirect, easily measurable metric used to represent a true underlying goal that is impossible or extremely difficult to measure quickly. For example, you cannot easily measure 'User Happiness', so you use the Proxy Metric of 'NPS Score' or 'Session Frequency'. It is appropriate when the true metric has massive latency (like 5-year LTV).",
 ["An indirect, easily measurable metric representing a hard-to-measure goal", "Example: NPS Score as a proxy for User Happiness", "Used when the true metric is unobservable or has massive time latency"],
 ["A metric measured through an IP proxy server"]),

("DA_RCA", "scenario", "medium", "scenario", ["Causal Inference"],
 "A new feature was launched on iOS only. The overall company conversion rate increased. Can you definitively attribute the overall increase to the new iOS feature? Why or why not?",
 "No, you cannot definitively attribute it without an A/B test or rigorous causal inference (like Difference-in-Differences). Because it was a global launch, the increase could be driven by external seasonality, a concurrent marketing campaign, or a competitor going offline. You must compare the iOS trend against the Android trend (as a control group) to isolate the feature's true impact.",
 ["No, correlation does not equal causation in a global launch", "Could be driven by seasonality, marketing, or external factors", "Must use a control group (e.g., Android) to perform Difference-in-Differences analysis"],
 ["Yes, if the numbers go up it is always because of the new feature"]),

("DA_RCA", "tradeoff", "medium", "tradeoff", ["Communication"],
 "When communicating analytical findings to non-technical stakeholders, what are the tradeoffs between showing the raw mathematical uncertainty (e.g., confidence intervals, error bars) versus presenting a simplified, definitive conclusion?",
 "Showing uncertainty is scientifically rigorous and protects the business from making absolute bets on noisy data, but can cause decision paralysis, confusion, or loss of trust from stakeholders who just want a 'Yes/No' answer. Simplifying the conclusion drives rapid decision-making and clear narratives, but hides the statistical risk of the recommendation being wrong.",
 ["Uncertainty: scientifically rigorous, highlights risk, but causes decision paralysis", "Simplified: drives rapid decisions and clear narratives", "Simplified: hides statistical risk and the probability of being wrong"],
 ["Stakeholders love reading dense mathematical formulas"])
]
