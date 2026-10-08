import os

ROLE = "Data Analyst"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b1": ("Advanced SQL", "Window Functions & CTEs", "SQL", ["Data Analyst", "Data Engineer"]),
    "b2": ("Statistical Reasoning", "A/B Testing & Stats", "Statistics", ["Data Analyst", "Data Scientist"]),
    "b3": ("Root Cause Analysis", "Metric Investigation", "Analytics", ["Data Analyst"]),
    "b4": ("Business Analytics", "Metric Design", "Analytics", ["Data Analyst", "Data Scientist"]),
    "b5": ("Data Cleaning", "Data Quality & Outliers", "SQL", ["Data Analyst", "Data Engineer"]),
    "b6": ("Data Transformation", "Dimensional Modeling & Workflows", "SQL", ["Data Analyst", "Analytics Engineer"]),
    "b7": ("Python Pandas", "Data Wrangling with Pandas", "Python", ["Data Analyst", "Data Scientist"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    # Q35 (b1 - Advanced SQL, 8th question of b1)
    (
        "b1",
        "implement",
        "hard",
        "coding",
        ["Advanced SQL", "Data Transformation"],
        "You are analyzing web traffic logs where each row is an event timestamped per user. You need to identify 'sessions', defined as sequences of events separated by no more than 30 minutes of inactivity. How do you construct a SQL query using window functions to assign a unique incrementing `session_id` to each user's distinct sessions?",
        "This is solved using a two-step window function technique often called the 'gaps-and-islands' sessionization pattern. First, in a CTE, use `LAG()` to look at the preceding event's timestamp for the same user: `LAG(event_timestamp) OVER (PARTITION BY user_id ORDER BY event_timestamp) AS prev_timestamp`. In the same step, calculate whether the gap exceeds 30 minutes: `CASE WHEN event_timestamp > DATEADD(minute, 30, prev_timestamp) OR prev_timestamp IS NULL THEN 1 ELSE 0 END AS is_new_session`. Second, in an outer query, compute a cumulative running sum of this flag: `SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY event_timestamp ROWS UNBOUNDED PRECEDING) AS session_id`. Because the flag is 1 only when a new session starts and 0 during ongoing session events, the running sum stays constant throughout a session and increments exactly when inactivity exceeds 30 minutes, producing clean, unique session identifiers per user.",
        [
            "Uses `LAG()` partitioned by user and ordered by timestamp to find the previous event time.",
            "Defines the session boundary condition correctly (time difference > 30 minutes or NULL previous timestamp).",
            "Applies a running cumulative `SUM()` over the boundary flag to generate incrementing session IDs."
        ],
        [
            "Suggests grouping directly by timestamp without window functions.",
            "Fails to use a cumulative running sum, leaving only binary flags rather than unique session groupings."
        ]
    ),
    # Q36 (b2 - Statistical Reasoning, 8th question of b2)
    (
        "b2",
        "diagnose",
        "hard",
        "analytical",
        ["Statistical Reasoning", "Business Analytics"],
        "In an A/B test for an e-commerce checkout flow, the test variant demonstrates a statistically significant 15% increase in conversion rate during the first week. However, by week 4, the conversion lift steadily decays to 0% and becomes indistinguishable from the control. What statistical and behavioral phenomena explain this degradation, and how would you verify which one occurred?",
        "The primary behavioral explanation is the Novelty Effect (or Primacy Effect), where existing, habituated users are attracted to or curious about UI changes, resulting in a temporary spike in engagement that dissipates once familiarity returns. A second behavioral factor is Purchase Cannibalization or Intertemporal Substitution, where promotional cues cause users to pull forward planned future purchases into week 1, creating an artificial early spike followed by a slump. A statistical factor is Cohort Sampling Bias: highly active 'power users' visit within the first few days of any test, while infrequent or casual users arrive across the full month, gradually diluting the initial sample. To verify the root cause, I would segment the test by user tenure: if new users (who had never seen the old checkout) maintain the 15% lift across all 4 weeks while only returning users show the decay, it conclusively confirms the Novelty Effect. I would also check cohort reorder rates in weeks 2-4 to test for purchase pull-forward.",
        [
            "Identifies Novelty Effect as the primary behavioral driver of transient early lifts.",
            "Mentions Intertemporal Substitution (purchase pull-forward) or sampling bias from power users visiting early.",
            "Proposes segmenting new users versus returning users to isolate and confirm the Novelty Effect."
        ],
        [
            "Assumes the test must have been hacked or that tracking code broke randomly in week 4.",
            "Suggests stopping the test after week 1 because 'it was significant then', misunderstanding novelty bias."
        ]
    ),
    # Q37 (b3 - Root Cause Analysis, 8th question of b3)
    (
        "b3",
        "diagnose",
        "hard",
        "problem_solving",
        ["Root Cause Analysis", "Business Analytics"],
        "Your marketplace platform tracks Net Revenue Retention (NRR) and Gross Merchandise Value (GMV). Leadership notices that while overall platform GMV grew 25% year-over-year, NRR for existing merchants fell from 115% to 92%. How do you systematically deconstruct this divergence to isolate the structural root cause?",
        "NRR specifically measures revenue evolution within existing merchant cohorts over time (Starting Revenue + Expansion - Contraction - Churn / Starting Revenue), whereas top-line GMV blends existing cohort revenue with new merchant acquisitions. A 25% GMV gain alongside an NRR decline below 100% indicates that top-line growth is masking severe underlying retention or expansion decay in the existing merchant base. To systematically isolate the cause: 1) Decompose the NRR formula into its three drivers: Gross Churn (merchants leaving), Contraction (merchants selling less), and Expansion (merchants selling more). 2) Segment by merchant tier (Enterprise vs SMB): often, aggressive acquisition of low-quality SMBs creates massive churn that drags down NRR, while top-line GMV is supported by a few huge enterprise wins. 3) Inspect cohort aging curves: check if newer merchant vintages are degrading faster than older legacy vintages. 4) Check take-rate and merchant category mix: a shift toward lower-margin or lower-frequency categories can suppress merchant expansion even as transaction volume increases.",
        [
            "Differentiates between cohort-level retention (NRR) and blended aggregate growth (GMV).",
            "Breaks down NRR into Expansion, Contraction, and Churn components to isolate which lever is dropping.",
            "Proposes segmentation by merchant tier (SMB vs Enterprise) and cohort vintage to detect concentration and mix effects."
        ],
        [
            "Claims that NRR and GMV measure the exact same thing and that one of the metrics must be calculated wrong.",
            "Focuses purely on marketing spend without looking at merchant retention or churn mechanics."
        ]
    ),
    # Q38 (b4 - Business Analytics, 8th question of b4)
    (
        "b4",
        "tradeoff",
        "medium",
        "analytical",
        ["Business Analytics", "Root Cause Analysis"],
        "When selecting a primary North Star Metric for a B2B SaaS workflow product, the Head of Product advocates for 'Total Monthly Active Users (MAU)', while the Finance Director insists on 'Monthly Recurring Revenue (MRR)'. What are the critical strategic blind spots of each metric, and what composite or proxy metric would you recommend instead?",
        "MAU's critical blind spot is that it is a vanity volume metric in B2B SaaS: enterprise accounts often purchase seat licenses where employees log in passively once a month without performing any meaningful work. It fails to distinguish between shallow logins and high-value workflows, and it treats a free trial user the same as an enterprise account generating $50k/month. MRR's critical blind spot is that it is a heavily lagging financial indicator: contracts are locked in for 12 months, meaning MRR can remain stable or grow even while actual product engagement has cratered, leaving leadership blind to impending catastrophic churn. To balance customer value with business health, I recommend a 'Value-Realizing Account Metric' like Weekly Active Accounts Completing Core Workflow (e.g., 'Accounts generating >= 3 reports per week') paired with Net Revenue Retention (NRR). This ties recurring usage directly to accounts paying the revenue, serving as an early leading indicator of retention and expansion.",
        [
            "Articulates why MAU is shallow in B2B (vanity logins, lack of value realization, equal weighting of free vs paid).",
            "Articulates why MRR is a lagging indicator (annual contracts mask decaying daily engagement until renewal).",
            "Recommends an account-level active value metric (e.g., Weekly Active Accounts completing core actions) or NRR as a balanced leading indicator."
        ],
        [
            "Chooses one metric without identifying the risks and blind spots of either.",
            "Suggests using website page views instead of an account-level engagement metric."
        ]
    ),
    # Q39 (b5 - Data Cleaning, 7th question of b5)
    (
        "b5",
        "diagnose",
        "medium",
        "problem_solving",
        ["Data Cleaning", "Data Transformation"],
        "You are auditing a table of transaction records and discover that 4% of records have negative transaction amounts, while another 2% have timestamps in the year 1970. How do you distinguish between legitimate business transactions versus corrupted data, and what remediation steps do you take?",
        "Negative amounts can represent legitimate financial adjustments (refunds, credit notes, disputed chargebacks, partner fee rebates) or data ingestion errors (inverted sign bugs, duplicate debits). To verify, I check transaction type codes, payment gateway status fields, and parent-child linkages: legitimate refunds will reference an original `order_id` or `parent_transaction_id` and have an explicit `refund` event status. Timestamps in 1970 (specifically `1970-01-01 00:00:00 UTC`) represent the Unix Epoch (timestamp 0), universally caused by `NULL` values being cast to integer 0 and then converted to datetime, or default fallback dates in upstream services. Remediation: 1) For negative amounts, do not arbitrarily drop them; categorize verified refunds into distinct reporting columns (`gross_revenue` vs `refunds`) and isolate unlinked negative anomalies for engineering review. 2) For 1970 timestamps, map them back to `NULL` to avoid corrupting time-series trends, investigate upstream ingestion logs to retrieve original creation dates, and implement automated schema tests (`dbt test` for `expression_is_true: transaction_timestamp > '2010-01-01'`).",
        [
            "Distinguishes between valid negative entries (refunds, chargebacks with reference IDs) and pipeline sign bugs.",
            "Identifies 1970 timestamps as Unix Epoch 0 caused by NULL handling during type conversion.",
            "Outlines clear remediation: preserving refunds as contra-revenue, nullifying epoch defaults, and adding automated data quality tests."
        ],
        [
            "Blindly deletes all negative rows and all 1970 rows using a `WHERE amount > 0` filter.",
            "Believes 1970 timestamps represent actual transactions made in 1970."
        ]
    ),
    # Q40 (b6 - Data Transformation, 1st question of b6)
    (
        "b6",
        "compare",
        "easy",
        "conceptual",
        ["Data Transformation", "Advanced SQL"],
        "In dimensional modeling for analytics, what is the core structural difference between a Fact table and a Dimension table, and how do their update patterns and granularities typically differ?",
        "A Fact table records numeric measurements, quantitative metrics, and foreign keys that capture business events at a specific point in time (e.g., individual orders, page clicks, wire transfers). Facts represent 'what happened'. They have high row volume, deep transaction granularity, and follow an append-mostly update pattern. A Dimension table provides descriptive, contextual attributes—the 'who, what, where, when, and how'—used to slice, filter, and group the facts (e.g., customer demographics, product catalog, store locations). Dimensions have wide schemas with many text attributes, lower row counts, and undergo updates via Slowly Changing Dimension (SCD) patterns to track attribute evolution over time.",
        [
            "Defines Fact tables as event-driven numeric measurements and metrics with foreign keys.",
            "Defines Dimension tables as contextual attributes providing who/what/where filters.",
            "Contrasts their operational characteristics: facts are append-heavy and narrow/deep; dimensions are wide and update via SCD patterns."
        ],
        [
            "Confuses Facts and Dimensions, claiming dimensions store numeric transactional metrics.",
            "States that fact tables are always smaller than dimension tables."
        ]
    ),
    # Q41 (b6 - Data Transformation, 2nd question of b6)
    (
        "b6",
        "tradeoff",
        "medium",
        "analytical",
        ["Data Transformation", "Data Cleaning"],
        "When designing a dimension table for customer profiles that change over time (e.g., customer tier upgrades from Bronze to Gold), how do you evaluate the tradeoffs between SCD Type 1, SCD Type 2, and SCD Type 3?",
        "SCD Type 1 overwrites old values with the new attribute value. Tradeoffs: It is simple to implement and requires zero additional storage, but it completely destroys historical context. A past order placed when the user was Bronze will retroactively appear under Gold in historical revenue reporting, distorting past cohort performance. SCD Type 2 creates a new record for every attribute change, preserving history using versioning columns like `effective_date`, `expiration_date`, and `is_current_flag`. Tradeoffs: It provides perfect point-in-time historical fidelity and reproducible reporting, but increases table row volume and requires more complex join logic (joining facts between the effective date ranges). SCD Type 3 adds a separate column to store the previous value (e.g., `current_tier` and `previous_tier`). Tradeoffs: It tracks limited history without adding new rows, but cannot accommodate multiple intermediate changes or historical timelines beyond a single previous state.",
        [
            "Accurately defines SCD Type 1 (overwrite), Type 2 (new row with date ranges), and Type 3 (new column for previous state).",
            "Explains the major tradeoff of Type 1: loss of history causing retrospective reporting distortions.",
            "Explains the major tradeoff of Type 2: accurate point-in-time reporting at the cost of storage and join complexity."
        ],
        [
            "Cannot differentiate between the three SCD types.",
            "Suggests SCD Type 1 is always best because 'we only care about current customer status'."
        ]
    ),
    # Q42 (b6 - Data Transformation, 3rd question of b6)
    (
        "b6",
        "optimize",
        "medium",
        "problem_solving",
        ["Data Transformation", "Advanced SQL"],
        "You are building an analytical data model combining marketing ad spend (reported at the daily campaign level) with user conversion purchases (recorded at the individual transaction level). If you join them directly on campaign ID and date, you encounter severe fan-out duplication. How do you structure the data model to prevent this chasm trap?",
        "Joining tables with disparate granularities directly causes a 'fan-out' or chasm trap: if campaign X had $100 in spend on Monday and generated 50 conversion purchases, joining directly on `campaign_id` and `date` will duplicate the $100 spend row 50 times, inflating total spend to $5,000 in downstream aggregations. To solve this: 1) Keep the Fact tables separate at their natural granularities (`fact_daily_campaign_spend` and `fact_user_conversions`). 2) Create a shared, conformed dimension table (`dim_campaign` and `dim_date`). 3) In your data modeling layer (e.g., dbt or intermediate SQL view), pre-aggregate the granular conversion fact table to the exact grain of the ad spend table (grouping conversions by `campaign_id` and `date` to get daily counts and daily conversion value) *before* performing an outer join. 4) Alternatively, use a multi-fact reporting query where spend and conversions are aggregated in separate CTEs and joined along the conformed dimensions.",
        [
            "Explains why direct joining across mismatched granularities causes metric multiplication (fan-out / chasm trap).",
            "Advocates keeping separate fact tables at their native grains rather than forcing an unaggregated join.",
            "Proposes pre-aggregating the conversion metrics to match the campaign/date grain prior to joining."
        ],
        [
            "Suggests using `SELECT DISTINCT` to magically fix the multiplied spend metric.",
            "Fails to recognize that spend is duplicated by multiple conversion rows."
        ]
    ),
    # Q43 (b6 - Data Transformation, 4th question of b6)
    (
        "b6",
        "diagnose",
        "hard",
        "problem_solving",
        ["Data Transformation", "Root Cause Analysis"],
        "Financial reporting generated on the 1st of the month differs noticeably from the exact same month's report re-run on the 5th, despite no changes to report queries. Assuming no warehouse infrastructure failure, what data pipeline and operational dynamics cause this historical data drift, and how do you design pipelines for reproducible financial reporting?",
        "Historical data drift occurs primarily due to: 1) Late-Arriving Facts: Payment processing settlements, refunds, chargebacks, and offline partner transactions that occurred in the prior month may arrive days late in event streams. 2) Slowly Changing Dimension (SCD Type 1) overwrites: If dimensions like product category or customer region are overwritten in place, re-running historical reports retroactively recalculates totals under new groupings. 3) Upstream batch backfills or database replication lag. To design reproducible financial pipelines: 1) Implement snapshot isolation or periodic freeze dates: create an immutable `monthly_financial_snapshot` table locked on a designated fiscal close date. 2) Decouple `transaction_date` (when the user clicked buy) from `accounting_period` or `settlement_date` (the fiscal period the revenue was recognized). 3) Use SCD Type 2 with historical effective date ranges for all dimensions so historical joins remain deterministic regardless of when queries are run.",
        [
            "Identifies Late-Arriving Facts (refunds, delayed partner settlements) as a primary operational cause.",
            "Identifies SCD Type 1 dimension updates retroactively modifying historical classifications.",
            "Proposes architectural solutions: immutable periodic snapshot tables, fiscal close freezing, and separating transaction dates from accounting dates."
        ],
        [
            "Assumes someone manually tampered with the database tables.",
            "Recommends locking the entire database so no new data can enter after the 1st of the month."
        ]
    ),
    # Q44 (b6 - Data Transformation, 5th question of b6)
    (
        "b6",
        "compare",
        "easy",
        "conceptual",
        ["Data Transformation", "Advanced SQL"],
        "What are the structural and analytical query performance differences between a Star Schema and a Snowflake Schema in a modern cloud data warehouse?",
        "In a Star Schema, dimension tables are completely denormalized, meaning attributes (such as category, subcategory, brand) are flattened into a single wide dimension table directly surrounding the central fact table. In a Snowflake Schema, dimension tables are normalized into hierarchical lookup tables (e.g., product links to subcategory, which links to category). Query Performance: Modern columnar cloud data warehouses (Snowflake, BigQuery, Redshift) thrive on denormalized data because columnar compression minimizes storage penalties and avoiding multi-level relational joins drastically speeds up OLAP scan performance. Star schemas are therefore faster to query, simpler to navigate for analysts, and less error-prone. Snowflake schemas reduce redundancy and storage, but introduce multiple table joins that degrade query speed and increase complexity for BI reporting.",
        [
            "Defines Star Schema as denormalized dimensions around a fact, and Snowflake Schema as normalized dimension hierarchies.",
            "Explains that modern columnar warehouses favor Star Schemas due to fewer joins and high compression efficiency.",
            "Notes that Star Schemas simplify query construction and reduce analyst error in BI tools."
        ],
        [
            "Claims Snowflake Schema is named after Snowflake data warehouse.",
            "States that Snowflake schemas are always faster to query because normalized tables are narrower."
        ]
    ),
    # Q45 (b6 - Data Transformation, 6th question of b6)
    (
        "b6",
        "implement",
        "hard",
        "problem_solving",
        ["Data Transformation", "Advanced SQL"],
        "You are tasked with generating a daily revenue report across all product categories. However, on days where a category has zero sales, those dates disappear from standard `GROUP BY` aggregations, breaking 7-day moving averages. How do you implement a robust SQL solution to guarantee continuous daily timelines for every category?",
        "To ensure continuous timelines without dropping zero-activity days, you construct a 'Calendar Scaffold' (or Date Spine) and cross join it with all active categories before joining sales. Step 1: Generate a complete date spine covering the entire reporting window (using `GENERATE_DATE_ARRAY()` in BigQuery, `SEQUENCE` in Presto, or an existing `dim_date` table). Step 2: Perform a `CROSS JOIN` between the date spine and the distinct list of categories (`dim_date CROSS JOIN (SELECT DISTINCT category FROM products)`). This Cartesian product creates every possible `(date, category)` pair, guaranteeing complete coverage. Step 3: `LEFT JOIN` this scaffold against the actual sales aggregation grouped by date and category. Step 4: Wrap the sales metric in `COALESCE(SUM(sales), 0)`. Because every category now has a row for every single calendar day, downstream window functions like `AVG(daily_sales) OVER (PARTITION BY category ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` compute accurate 7-day moving averages without gaps.",
        [
            "Proposes generating a date spine or calendar table covering the full reporting date range.",
            "Uses a `CROSS JOIN` between dates and categories to generate a complete Cartesian matrix of all date-category combinations.",
            "Performs a `LEFT JOIN` from the matrix to sales data and applies `COALESCE(..., 0)` to fill missing dates."
        ],
        [
            "Suggests using an `INNER JOIN`, which continues to drop zero-sale dates.",
            "Attempts to manually insert dummy zero rows into production transactional tables."
        ]
    ),
    # Q46 (b7 - Python Pandas, 1st question of b7)
    (
        "b7",
        "optimize",
        "medium",
        "problem_solving",
        ["Python Pandas", "Data Transformation"],
        "A colleague's Python script calculates sales tax on a 10-million row Pandas DataFrame using `.iterrows()` and appends results to a Python list, taking over 15 minutes to run. How do you refactor this workflow to run in under 2 seconds, and why is the refactored approach so much faster?",
        "The script is slow because `.iterrows()` iterates row-by-row through the Python interpreter, instantiating a new Pandas Series object for every single row, incurring severe memory allocation and type boxing overhead. To refactor this for sub-second execution, replace the loop with vectorized Pandas operations: `df['tax'] = df['amount'] * tax_rate`. If tax rates vary conditionally across states or product categories, use NumPy vectorized conditionals: `df['tax'] = np.where(df['is_exempt'], 0, df['amount'] * df['tax_rate'])` or `np.select(conditions, choices, default=0)`. Vectorization is orders of magnitude faster because NumPy and Pandas delegate the computation down to pre-compiled C/Fortran code operating on contiguous blocks of memory, leveraging CPU SIMD (Single Instruction, Multiple Data) instructions and entirely bypassing the Python interpreter loop overhead.",
        [
            "Explains the bottleneck of `.iterrows()`: row-by-row Series instantiation and Python interpreter overhead.",
            "Replaces iteration with vectorized Pandas arithmetic or NumPy vectorized conditionals (`np.where` / `np.select`).",
            "Explains why vectorization is faster: compiled C-level execution, contiguous memory arrays, and SIMD hardware acceleration."
        ],
        [
            "Suggests replacing `.iterrows()` with `.apply(lambda row: ...)`, which is still slow Python-level iteration.",
            "Claims adding multi-threading in pure Python will fix the 15-minute runtime without changing row iteration."
        ]
    ),
    # Q47 (b7 - Python Pandas, 2nd question of b7)
    (
        "b7",
        "implement",
        "medium",
        "coding",
        ["Python Pandas", "Data Transformation"],
        "You receive an unpivoted marketing dataset in wide format where columns represent monthly ad expenditures (`Jan_Spend`, `Feb_Spend`, `Mar_Spend`) along with a `Campaign_ID` column. How do you transform this DataFrame into tidy long format using Pandas for visualization, and how do you invert the operation back to wide format?",
        "To transform wide data into tidy long format, use `pd.melt()`: `df_long = pd.melt(df, id_vars=['Campaign_ID'], value_vars=['Jan_Spend', 'Feb_Spend', 'Mar_Spend'], var_name='Month', value_name='Spend')`. This produces a three-column DataFrame where each row represents a single campaign-month spend observation, which is the required input format for visualization libraries like Seaborn, Plotly, or Tableau. To invert this transformation back into wide format, use `pd.pivot()` or `pivot_table()`: `df_wide = df_long.pivot(index='Campaign_ID', columns='Month', values='Spend').reset_index()`. If there are duplicate records for the same campaign-month pair, `pivot()` will raise a `ValueError`, in which case `df.pivot_table(index='Campaign_ID', columns='Month', values='Spend', aggfunc='sum').reset_index()` must be used to handle aggregation cleanly.",
        [
            "Uses `pd.melt()` with appropriate `id_vars`, `value_vars`, `var_name`, and `value_name` parameters to unpivot.",
            "Uses `pd.pivot()` or `pivot_table()` to reshape back to wide format.",
            "Notes that `pivot_table()` with an aggregation function is required if duplicate index-column combinations exist."
        ],
        [
            "Confuses `melt` and `pivot`, applying them in reverse order.",
            "Proposes writing manual nested Python loops over DataFrame columns."
        ]
    ),
    # Q48 (b7 - Python Pandas, 3rd question of b7)
    (
        "b7",
        "diagnose",
        "medium",
        "analytical",
        ["Python Pandas", "Statistical Reasoning"],
        "An analyst prepares a customer purchase dataset containing missing values in `annual_orders` by executing `df['annual_orders'].fillna(df['annual_orders'].mean())` before running regression analysis. What statistical distortions does mean imputation introduce, and what alternatives should be used instead?",
        "Mean imputation introduces three severe statistical distortions: 1) Artificial Variance Reduction: Injecting the exact mean into missing values concentrates density at a single point, artificially shrinking the standard deviation and variance of the feature. This inflates t-statistics and deflates p-values in regression, creating false statistical significance. 2) Correlation Attenuation: It weakens the covariance and Pearson correlation between `annual_orders` and other variables because the imputed values exhibit zero variance relative to the mean. 3) Distribution Distortion: If purchase frequency is right-skewed or zero-inflated (which is standard in transaction data), the mean is not a representative central tendency and imputes fractional non-integer orders. Superior alternatives include: 1) Median imputation if distribution is skewed, paired with an explicit missingness indicator column (`df['orders_was_missing'] = df['annual_orders'].isna()`). 2) Multiple Imputation by Chained Equations (MICE) or KNN imputation to preserve multi-variable covariance. 3) Domain logic: verifying if missing `annual_orders` simply signifies 0 purchases for inactive accounts.",
        [
            "Identifies variance shrinkage as a primary flaw leading to artificially inflated statistical significance.",
            "Explains that mean imputation dilutes true correlations and distorts skewed distributions.",
            "Recommends robust alternatives: median imputation with missingness indicators, KNN/MICE imputation, or domain-driven zero imputation."
        ],
        [
            "Claims mean imputation is always the best practice for numerical machine learning models.",
            "Fails to identify the impact on variance, covariance, or standard error."
        ]
    ),
    # Q49 (b7 - Python Pandas, 4th question of b7)
    (
        "b7",
        "compare",
        "easy",
        "conceptual",
        ["Python Pandas", "Data Transformation"],
        "In Pandas, what is the fundamental functional difference between `.loc[]` and `.iloc[]`, and what common indexing bug occurs when slicing a DataFrame with an integer index containing gaps?",
        "`.loc[]` is label-based indexing, selecting data based on the explicit index and column names. Importantly, `.loc[start:stop]` includes both the start and stop boundaries (closed interval). `.iloc[]` is integer position-based indexing (0 to N-1), selecting data purely by its numerical coordinate positions in the memory array, following standard Python slicing where the stop boundary is excluded (half-open interval `[start:stop)`). The common bug occurs when a DataFrame has an integer index with gaps or non-sequential values (e.g., after filtering rows with `df[df['active'] == True]`, leaving index labels `[0, 3, 7, 12]`). If an analyst calls `.loc[0:3]`, Pandas searches for rows where the label is between 0 and 3, returning rows with labels 0 and 3. But if they call `.iloc[0:3]`, Pandas selects the first three physical rows (labels 0, 3, and 7). Treating `.loc` as positional indexing leads to silently incorrect subsets or `KeyError` exceptions.",
        [
            "Clearly distinguishes label-based selection (`.loc`) from integer positional selection (`.iloc`).",
            "Notes the boundary inclusion difference: `.loc` is inclusive of stop, while `.iloc` is exclusive of stop.",
            "Explains the indexing bug when integer indexes have gaps (e.g. after filtering), showing how `.loc` matches labels while `.iloc` matches positional order."
        ],
        [
            "Claims `.loc` and `.iloc` are identical aliases.",
            "Cannot explain whether endpoints are included or excluded."
        ]
    ),
    # Q50 (b7 - Python Pandas, 5th question of b7)
    (
        "b7",
        "optimize",
        "hard",
        "problem_solving",
        ["Python Pandas", "Data Transformation"],
        "You need to analyze a 12GB CSV file using Pandas on a machine with only 16GB of RAM. Running `pd.read_csv()` immediately crashes with a `MemoryError`. How do you systematically re-architect the data ingestion and processing pipeline to analyze this dataset within memory constraints?",
        "To process a 12GB file within a 16GB memory limit, apply systematic ingestion optimization techniques: 1) Column Pruning: Use the `usecols` parameter in `pd.read_csv()` to load only the specific columns required for the analysis, immediately cutting memory usage if the CSV has wide unused attributes. 2) Downcast Data Types: Pandas defaults numeric columns to 64-bit integers and floats. Explicitly pass a `dtype` dictionary casting `float64` to `float32`, and integer IDs to `int32` or `int16`. 3) Convert Low-Cardinality Strings to `category`: String columns in Pandas consume massive object overhead. Converting repeated strings (e.g., state, device type, status) to `category` dtype can slash memory consumption by 80-90%. 4) Chunked Iteration: Use `pd.read_csv(filepath, chunksize=100000)` to stream the file in manageable batches, compute intermediate summary metrics per chunk (e.g., sums and counts), and aggregate final metrics across chunks. 5) High-Performance Engines: Leverage `engine='pyarrow'` for faster parsing and compact memory layouts, or convert the CSV to partitioned Parquet files for persistent memory-mapped querying.",
        [
            "Recommends selective column loading with `usecols` and explicit dtype downcasting (`float32`, smaller integer types).",
            "Recommends converting low-cardinality string/object columns to `category` dtype.",
            "Outlines chunked batch processing (`chunksize`) to stream data and compute intermediate aggregations within memory limits."
        ],
        [
            "Suggests buying more RAM as the only solution.",
            "Suggests reading the entire file line-by-line into a single giant Python dictionary without optimizing data structures."
        ]
    )
]
