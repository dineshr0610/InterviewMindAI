"""Batch 29 Part 2 question content (Data Analyst). Targeted Gap Generation."""

ROLE = "Data Analyst"

BUCKET_KEYS = {
    "DATA_TRANSFORMATION": ("Data Transformation", "Analytical SQL", "Data Warehouse", ["Data Analyst", "Data Engineer", "Data Scientist"]),
}

Q = [
# ---------------- DATA_TRANSFORMATION ----------------
("DATA_TRANSFORMATION", "implement", "medium", "implementation", ["Window Functions", "SQL"],
 "You have a table of user login events with timestamps. How do you construct a SQL query to calculate the 'Time Since Last Login' for each specific login event?",
 "You must use the `LAG()` window function. You query `LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp ASC)` to retrieve the exact timestamp of the user's previous login event onto the current row. You then calculate the mathematical difference (e.g., using `DATEDIFF`) between the current timestamp and the lag timestamp.",
 ["Use the `LAG()` window function", "Partition by `user_id` and order by `timestamp ASC`", "Calculate the difference (`DATEDIFF`) between the current row's timestamp and the lagged timestamp"],
 ["Query the database really fast twice in a row"]),

("DATA_TRANSFORMATION", "scenario", "hard", "scenario", ["Sessionization", "Window Functions"],
 "You are building a 'Sessionization' model in SQL. You have a raw stream of pageview events. You want to group events into the same session if they occur within 30 minutes of each other. How do you implement this logic using window functions?",
 "You use a multi-step CTE. First, use `LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp)` to find the time since the last event. Second, create a flag: `CASE WHEN time_diff > 30 mins THEN 1 ELSE 0 END as is_new_session`. Finally, use a cumulative sum window function `SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY timestamp)` to assign a unique, incrementing session ID to each block of events.",
 ["Use `LAG()` to calculate the time difference between consecutive events for a user", "Create a binary flag (1/0) triggering when the difference exceeds 30 minutes", "Use a cumulative `SUM()` over the flag to generate an incrementing Session ID"],
 ["Ask the frontend developers to generate the session ID instead"]),

("DATA_TRANSFORMATION", "tradeoff", "medium", "tradeoff", ["Data Modeling", "OBT"],
 "When designing an analytical data model, what is the tradeoff between joining all tables into one massive 'One Big Table' (OBT) versus keeping a traditional Star Schema (Fact and Dimension tables) for analysts to query?",
 "OBT is incredibly fast and simple for analysts/BI tools to query because there are zero complex JOINs, eliminating fan-out errors. However, OBT creates massive data redundancy (the same user's name is repeated on 1,000 transaction rows). If a dimension changes (e.g., user changes their name), you must update millions of historical rows in the OBT instead of just one row in a Star Schema dimension table.",
 ["OBT: Extremely fast for BI tools, eliminates JOIN complexity and fan-out risks", "OBT Tradeoff: Massive data redundancy and storage bloat", "OBT Tradeoff: Updating a dimension requires modifying millions of historical rows instead of one"],
 ["OBT requires a physically larger monitor to view the table"]),

("DATA_TRANSFORMATION", "explain", "easy", "concept", ["SCD"],
 "In data warehousing, what is a Slowly Changing Dimension (SCD) Type 2?",
 "SCD Type 2 is a method for tracking historical changes in dimension tables. Instead of overwriting an existing record when data changes (Type 1), you insert a completely new row with the new data, and manage the active periods using `valid_from` and `valid_to` date columns, plus an `is_current` boolean flag. This allows analysts to query historical facts using the dimension values exactly as they existed at that point in time.",
 ["A method for preserving historical changes in dimension tables", "Inserts a new row instead of overwriting the old one", "Manages active periods using `valid_from`, `valid_to`, and `is_current` flags"],
 ["It is a dimension that loads very slowly over the network"]),

("DATA_TRANSFORMATION", "debug", "hard", "debugging", ["Fan-out", "SQL"],
 "You write a SQL query to calculate Total Revenue by Region. The raw `orders` table has 10,000 rows. You `LEFT JOIN` the `order_items` table (which has multiple items per order) and the `regions` table. The Total Revenue output is 3x higher than it should be. Why, and how do you fix it?",
 "This is a fan-out (row multiplication) error. Because an order can have multiple items, joining `order_items` multiplied the base `orders` rows. If an order had 3 items, the `order_total` column was duplicated 3 times in the result set, and `SUM(order_total)` counted it 3 times. You must pre-aggregate the `order_items` table in a CTE (e.g., `GROUP BY order_id`) BEFORE joining it to the `orders` table.",
 ["Fan-out (row multiplication) error caused by joining a one-to-many relationship", "The `order_total` from the parent table was duplicated and summed multiple times", "Fix: Pre-aggregate the `order_items` table in a CTE before joining to the base table"],
 ["The database multiplied the revenue to account for inflation"]),

("DATA_TRANSFORMATION", "implement", "medium", "implementation", ["SQL", "Ranking"],
 "How do you write a SQL query to find the top 3 highest spending customers in *each* country without using `LIMIT`?",
 "You use the `RANK()` or `DENSE_RANK()` window function. In a CTE, you query `RANK() OVER (PARTITION BY country ORDER BY total_spend DESC) as spend_rank`. You then filter the outer query `WHERE spend_rank <= 3` to isolate the top spenders per partition.",
 ["Use the `RANK()` or `DENSE_RANK()` window function", "Partition by `country` and order by `total_spend DESC`", "Wrap in a CTE/subquery and filter `WHERE spend_rank <= 3` in the outer query"],
 ["Use `ORDER BY total_spend DESC` and manually copy the first 3 rows in Excel"]),

("DATA_TRANSFORMATION", "scenario", "hard", "scenario", ["Attribution", "Window Functions"],
 "A marketing team wants a strict 'First Touch' attribution model. You have a `web_visits` table with `user_id`, `timestamp`, and `utm_source`. Users can have hundreds of visits across different sources. How do you construct a dataset that maps every user to *only* their very first `utm_source`?",
 "You use the `ROW_NUMBER()` window function. In a CTE, you query `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp ASC) as rn`. Then in the outer query, you filter `WHERE rn = 1`. This safely isolates the absolute first chronological visit row for each user, which you can then join back to downstream purchase data.",
 ["Use the `ROW_NUMBER()` window function", "Partition by `user_id` and order by `timestamp ASC`", "Filter the outer query `WHERE rn = 1` to isolate the first chronological touchpoint"],
 ["Delete all rows from the database except the first one"]),

("DATA_TRANSFORMATION", "tradeoff", "medium", "tradeoff", ["Pre-aggregation", "BI"],
 "What is the analytical tradeoff of calculating a 'Rolling 30-Day Active Users' metric dynamically in the BI tool versus pre-aggregating it daily in an Airflow/dbt pipeline?",
 "Calculating it dynamically in the BI tool provides maximum flexibility (users can slice the rolling metric by any arbitrary dimension instantly), but is extremely computationally expensive and slow, often timing out dashboards. Pre-aggregating it in a data pipeline guarantees blazing fast dashboard load times, but rigidly locks the metric into the specific dimensions you chose to pre-aggregate by, destroying ad-hoc sliceability.",
 ["Dynamic (BI): Maximum flexibility for ad-hoc slicing by any dimension, but severely slow/expensive", "Pre-aggregated (Pipeline): Blazing fast dashboard load times", "Pre-aggregated Tradeoff: Locks the metric into predefined dimensions, destroying ad-hoc sliceability"],
 ["Pipelines are physical tubes that data flows through"]),

("DATA_TRANSFORMATION", "fundamentals", "easy", "concept", ["SQL", "CTEs"],
 "What is a Common Table Expression (CTE) in SQL, and why is it preferred over nested subqueries for complex data transformations?",
 "A CTE is a temporary, named result set defined at the beginning of a query using the `WITH` clause. It is heavily preferred over nested subqueries because it makes complex, multi-step transformations highly readable (executing logically top-to-bottom), allows the exact same result set to be referenced multiple times in the main query, and makes debugging intermediate steps trivial.",
 ["A temporary, named result set defined using the `WITH` clause", "Improves readability (top-to-bottom logic) compared to deeply nested subqueries", "Allows the result set to be referenced multiple times in the main query (DRY)"],
 ["CTE stands for Chronic Traumatic Encephalopathy"]),

("DATA_TRANSFORMATION", "debug", "medium", "debugging", ["Set Theory"],
 "An analyst writes `SELECT COUNT(user) FROM users WHERE date = '2023-01-01' OR country = 'US'`. They then run the queries individually: one for the date, one for the country. They are confused why the sum of the two individual queries is larger than the `OR` query. Explain the mathematical reason.",
 "This is basic set theory (the inclusion-exclusion principle). The `OR` query counts distinct users who meet *either* condition. If a user is from the 'US' AND signed up on the date, they are counted exactly once. The sum of the two individual queries counts that exact same user twice (once in the date query, once in the country query). The difference represents the intersection of the two sets.",
 ["Based on set theory and the inclusion-exclusion principle", "The `OR` query counts users in the intersection exactly once", "Summing individual queries double-counts users who meet both conditions"],
 ["The database dropped some users to save space"]),

("DATA_TRANSFORMATION", "implement", "hard", "implementation", ["Cohorts"],
 "You need to build a retention cohort analysis (Month 0, Month 1, Month 2 retention) in SQL. What are the three fundamental chronological steps required to construct this dataset?",
 "1. Find the Cohort Date: Find the `MIN(activity_date)` for each user (their signup/first action month). 2. Calculate the Action Month: Extract the month of every subsequent activity for that user. 3. Calculate the Month Delta: Use `DATEDIFF` (in months) between the Action Month and the Cohort Date to define Month 0, 1, 2, etc. Finally, group by Cohort Date and Month Delta to count distinct retained users.",
 ["Find the Cohort Date: The `MIN()` action date for each user", "Calculate the Action Month for all subsequent user activities", "Calculate the Month Delta: `DATEDIFF` between Action Month and Cohort Date"],
 ["Guess the retention based on industry benchmarks"]),

("DATA_TRANSFORMATION", "scenario", "medium", "scenario", ["Window Functions", "Performance"],
 "You have a table of `daily_sales`. You want to calculate the Year-Over-Year (YoY) growth for every single day (e.g., comparing 2023-11-01 to 2022-11-01). You cannot use self-joins because the table is 50 billion rows. How do you calculate this efficiently in SQL?",
 "You use the `LAG()` window function with a fixed offset. Assuming the data is strictly dense (guaranteed one row per day), you can use `LAG(sales, 365) OVER (ORDER BY date)` to pull the sales from exactly 365 rows prior directly onto the current row, calculating the YoY variance linearly without an expensive, massive self-join.",
 ["Use the `LAG()` window function with a fixed offset", "Assuming strictly dense data, use `LAG(sales, 365) OVER (ORDER BY date)`", "Pulls historical data linearly without requiring an expensive massive self-join"],
 ["Print out 50 billion rows and calculate it with a calculator"]),

("DATA_TRANSFORMATION", "tradeoff", "hard", "tradeoff", ["Data Cleaning", "Nulls"],
 "When dealing with missing or `NULL` categorical data in a dimension table (e.g., `marketing_channel` is null), what is the tradeoff between filtering out the `NULL` rows versus replacing them with an explicit string like 'Unknown'?",
 "Filtering out `NULL` rows cleans visualizations, but destroys data integrity; it artificially inflates conversion rates and reduces absolute totals (revenue/counts), causing the dashboard to severely mismatch the source-of-truth database. Replacing them with 'Unknown' guarantees the overall totals match the database perfectly and highlights tracking failures to stakeholders, but clutters visualizations with an ugly 'Unknown' bucket.",
 ["Filtering out NULLs destroys data integrity, causing dashboards to mismatch absolute source-of-truth totals", "Replacing with 'Unknown' guarantees totals match perfectly and highlights tracking bugs", "Tradeoff: 'Unknown' clutters executive visualizations"],
 ["NULLs should always be replaced with random data to look better"]),

("DATA_TRANSFORMATION", "explain", "easy", "concept", ["SQL"],
 "In SQL data transformations, what is the exact difference between `UNION` and `UNION ALL`?",
 "`UNION` combines the result sets of two queries and automatically removes all duplicate rows, which requires an expensive sorting/hashing operation behind the scenes. `UNION ALL` combines the result sets but keeps all duplicates, making it significantly faster and less resource-intensive. `UNION ALL` should always be used for performance unless deduplication is strictly required.",
 ["`UNION` removes duplicate rows (requires expensive sorting/hashing)", "`UNION ALL` keeps duplicates and is significantly faster", "Always default to `UNION ALL` unless deduplication is strictly required"],
 ["`UNION ALL` unions all the databases in the company together"]),

("DATA_TRANSFORMATION", "implement", "medium", "implementation", ["Data Spines", "Cross Joins"],
 "You have a `subscriptions` table with `user_id`, `start_date`, and `end_date`. A user is 'Active' on any given date between their start and end dates. How do you construct a SQL query to show the total number of Active users for every day in January?",
 "You cannot simply group by the subscriptions table. You must generate a 'Date Spine' or 'Calendar' table containing one row for every date in January. You then `LEFT JOIN` the subscriptions table to the calendar table using a non-equi join: `ON calendar.date >= subscriptions.start_date AND calendar.date <= subscriptions.end_date`. Finally, group by the calendar date and count distinct users.",
 ["Generate a 'Date Spine' or 'Calendar' table containing every date in the month", "Perform a non-equi `LEFT JOIN` (`calendar.date >= start_date AND calendar.date <= end_date`)", "Group by the calendar date and count distinct users to measure active concurrent states"],
 ["Look at the calendar on your wall and guess"]),

("DATA_TRANSFORMATION", "scenario", "hard", "scenario", ["Funnels", "Logic constraints"],
 "You are analyzing a funnel using events. You notice a massive spike in 'Drop-offs' between Step 2 and Step 3. However, you look at the raw event stream, and users are successfully executing Step 3. Why is the funnel query showing them as dropped off?",
 "The funnel query is likely enforcing a strict sequential time constraint or session boundary that the user technically violated. For example, the user completed Step 2 on Tuesday, left the site, and completed Step 3 on Wednesday. If the analytical funnel query requires all steps to occur within a single session, or within a rigid 1-hour window, the user is mathematically classified as a drop-off in the data, even though they eventually succeeded in reality.",
 ["The funnel enforces a strict time constraint or session boundary", "Users completing Step 3 outside the allowed time window (e.g., next day) are mathematically discarded", "The user succeeded in reality, but failed the strict criteria of the analytical query"],
 ["The users are falling out of a physical funnel in the office"]),

("DATA_TRANSFORMATION", "debug", "medium", "debugging", ["Statistics", "Distributions"],
 "An analyst uses `AVG(session_duration)` to report the typical user experience on the homepage. The average is 45 minutes, but the Product Manager says that's impossible. What is the fundamental flaw in using an Average for web engagement metrics, and what should be used instead?",
 "Web engagement metrics (like session duration or revenue) follow a heavily right-skewed power-law distribution, not a normal distribution. A few users leaving a tab open for 12 hours (massive outliers) will drastically pull the mathematical mean upwards, making it completely unrepresentative of the 'typical' user. The analyst must use the Median (50th percentile) to accurately report the typical user experience.",
 ["Web metrics follow a heavily right-skewed power-law distribution, not a normal distribution", "Massive outliers (leaving a tab open for 12 hours) drastically pull the mean upwards", "Must use the Median (50th percentile) to represent the 'typical' user"],
 ["The users are actively manipulating the database to look highly engaged"])
]
