"""Batch 29 Part 3 question content (Data Analyst). Targeted Gap Generation."""

ROLE = "Data Analyst"

BUCKET_KEYS = {
    "ANALYTICAL_EXPERIMENTATION": ("Analytical Experimentation", "A/B Testing", "Data Analysis", ["Data Analyst", "Data Scientist", "Product Manager"]),
}

Q = [
# ---------------- ANALYTICAL_EXPERIMENTATION ----------------
("ANALYTICAL_EXPERIMENTATION", "scenario", "medium", "scenario", ["SRM", "A/B Testing"],
 "You run an A/B test. The tool shows the Treatment variant won with 99% Statistical Significance. However, you notice the total traffic split, configured to be 50/50, actually landed at 52/48. What is this called, and why does it invalidate the experiment?",
 "This is a Sample-Ratio Mismatch (SRM). It indicates a severe fundamental flaw in the experimentation infrastructure or logging pipeline. For example, the Treatment experience might be crashing the app for 4% of users, preventing them from logging data. Any statistical results from an experiment with an SRM are completely untrustworthy because the samples are no longer truly random or representative.",
 ["Sample-Ratio Mismatch (SRM)", "Indicates a severe fundamental flaw in logging, routing, or crashing in one variant", "Invalidates all statistical results because the samples are no longer truly random"],
 ["The server dynamically adjusted traffic because Treatment was winning"]),

("ANALYTICAL_EXPERIMENTATION", "debug", "hard", "debugging", ["Peeking", "P-Value"],
 "You run a 14-day A/B test. On Day 2, the results are overwhelmingly positive, hitting 95% statistical significance. The Product Manager demands you stop the test early and ship it. Why is stopping a test as soon as it hits significance statistically dangerous?",
 "This is called 'Peeking' or the 'Multiple Comparisons Problem'. Statistical significance tests assume a fixed, predetermined sample size. Because data fluctuates naturally, checking results daily drastically inflates the False Positive rate (Type I error). The test might briefly cross the 95% threshold purely by random chance on Day 2 before regressing to the mean. You must wait for the predetermined sample size.",
 ["Known as 'Peeking' or the 'Multiple Comparisons Problem'", "Data fluctuates; checking daily inflates the False Positive rate", "It may cross significance by pure random chance before regressing to the mean"],
 ["Stopping early hurts the server's feelings"]),

("ANALYTICAL_EXPERIMENTATION", "tradeoff", "medium", "tradeoff", ["Significance", "Power"],
 "What is the analytical tradeoff of choosing an Alpha (Significance Level) of 0.01 instead of the standard 0.05 for an A/B test?",
 "Setting Alpha to 0.01 requires 99% confidence, which drastically reduces your False Positive rate (you won't accidentally ship a useless feature). However, the massive tradeoff is that it severely reduces Statistical Power. It requires a significantly larger sample size (more traffic or time) to detect a true effect, increasing the False Negative rate (missing a genuinely good feature).",
 ["Alpha 0.01 severely reduces the False Positive rate (Type I Error)", "Tradeoff: Drastically reduces Statistical Power (increases False Negatives)", "Requires significantly larger sample sizes (traffic/time) to detect a true effect"],
 ["Alpha 0.01 makes the math 5 times easier to calculate"]),

("ANALYTICAL_EXPERIMENTATION", "explain", "easy", "concept", ["Significance"],
 "Explain the difference between 'Statistical Significance' and 'Practical Significance' in business analytics.",
 "Statistical Significance only proves mathematically that an effect exists and is not due to random chance (e.g., the new button color increased conversion by 0.01% with a p-value of 0.02). Practical Significance asks whether the effect is actually large enough to care about from a business perspective. A 0.01% increase might be statistically real, but it is not practically significant enough to justify engineering costs.",
 ["Statistical Significance proves the effect is real and not random chance", "Practical Significance asks if the effect is large enough to matter to the business", "A tiny effect can be statistically real but practically useless"],
 ["Practical significance means you can physically touch the data"]),

("ANALYTICAL_EXPERIMENTATION", "scenario", "hard", "scenario", ["Novelty Effect"],
 "You run an A/B test changing the website's entire navigation bar. For the first week, Treatment performs 10% worse. By week three, Treatment is outperforming Control by 5%. What behavioral phenomenon explains this flip, and how do you analyze it?",
 "This is the 'Novelty Effect' or 'Change Aversion'. Users are creatures of habit. When a major UI change drops, returning users are confused and slower, temporarily depressing metrics. Over time, they learn the new UI. To isolate this, you segment the data by 'New Users' vs 'Returning Users'. New users, who never saw the old UI, will not experience Change Aversion and will reveal the true baseline performance.",
 ["Known as 'Change Aversion' or the 'Novelty Effect'", "Returning users are temporarily confused, depressing initial metrics until they learn", "Fix: Segment by 'New Users' vs 'Returning Users' to find the true unbiased baseline"],
 ["The servers got faster in week three"]),

("ANALYTICAL_EXPERIMENTATION", "fundamentals", "medium", "concept", ["Statistical Power"],
 "In A/B testing, what is 'Statistical Power'?",
 "Statistical Power is the probability that a test will correctly reject a false null hypothesis (i.e., the probability of detecting a true effect if one actually exists, successfully avoiding a False Negative). Power is generally targeted at 80%, meaning if the feature genuinely works, you have an 80% chance of detecting it with statistical significance given your sample size.",
 ["The probability of detecting a true effect if one actually exists", "The probability of successfully avoiding a False Negative (Type II error)", "Usually targeted at 80% when sizing an experiment"],
 ["The electrical wattage required to run the statistical models"]),

("ANALYTICAL_EXPERIMENTATION", "tradeoff", "hard", "tradeoff", ["Outliers", "Transformations"],
 "When dealing with extreme outliers in a revenue dataset (e.g., a client spending $10M while the average is $100), what is the tradeoff between completely dropping the outliers versus applying logarithmic transformation or winsorization?",
 "Dropping outliers completely cleans the data and makes standard statistical tests (t-tests) work perfectly, but it actively throws away real, valid business revenue, making totals grossly inaccurate. Log transformation/winsorization (capping the max value) preserves the existence of the high-value user without letting their extreme value disproportionately skew variance, but makes final metrics harder to explain to stakeholders.",
 ["Dropping Outliers: Cleans variance, but throws away real business revenue", "Log/Winsorization: Preserves outlier existence without skewing variance", "Tradeoff: Log metrics are difficult to explain to non-technical stakeholders"],
 ["Log transformations turn the data into literal wood logs"]),

("ANALYTICAL_EXPERIMENTATION", "debug", "medium", "debugging", ["P-Hacking", "Segmentation"],
 "An A/B test runs for 2 weeks with no statistical significance. The Product Manager says, 'Let's slice the data by Country, Device, Browser, and Time of Day. Surely one segment won!' Why is this post-hoc segmentation analytically dangerous?",
 "This is 'p-hacking' or 'fishing for significance'. Every time you slice the data and run a new statistical test, you compound the False Positive rate. If you slice by 20 different segments using a 95% confidence level, pure mathematical probability dictates that at least one segment will show a 'significant' win purely by random chance noise. Any segment wins found this way must be re-tested in a dedicated experiment.",
 ["Known as 'p-hacking' or the 'Multiple Comparisons Problem'", "Each new slice compounds the False Positive rate", "Probability dictates random chance noise will eventually produce a 'significant' false positive"],
 ["The data gets physically exhausted from being sliced too much"]),

("ANALYTICAL_EXPERIMENTATION", "implement", "hard", "implementation", ["Network Effects", "Experiment Design"],
 "How do you design an experiment to test a 'Network Effect' feature (like a social sharing program) where the behavior of a user in the Treatment group directly influences users in the Control group?",
 "Standard user-level A/B testing completely fails here due to 'Spillover' or 'Experiment Contamination' (Treatment users invite Control users, ruining isolation). You must implement 'Cluster Randomization' or 'Geo-Testing'. Instead of randomizing by user, you randomize by isolated clusters (e.g., entire cities, or time blocks). City A gets Treatment, City B gets Control, ensuring network effects stay contained.",
 ["Standard user-level testing fails due to 'Spillover' or 'Contamination'", "Treatment users directly influence Control users, ruining isolation", "Implement Cluster Randomization (e.g., Geo-testing entire cities) to contain the network effect"],
 ["Use a highly advanced firewall to block users from talking to each other"]),

("ANALYTICAL_EXPERIMENTATION", "scenario", "medium", "scenario", ["Composite Metrics", "Tradeoffs"],
 "You launch a pricing experiment. The Treatment group sees prices 10% higher. At the end, the Conversion Rate for Treatment dropped by 5%, but the Average Order Value (AOV) increased by 10%. How do you analytically determine if the test was a success?",
 "You cannot look at Conversion Rate and AOV in isolation because they naturally move in opposite directions here. You must evaluate the ultimate composite metric: Revenue Per User (RPU) or Average Revenue Per Visitor (ARPV). RPU mathematically combines the drop in conversion with the increase in AOV into a single definitive number to determine if the pricing increase generated more total net revenue.",
 ["Cannot look at Conversion and AOV in isolation (they move opposite directions)", "Must evaluate the composite metric: Revenue Per User (RPU) or ARPV", "RPU mathematically combines both to determine true net revenue impact"],
 ["Flip a coin to decide which metric is more important"]),

("ANALYTICAL_EXPERIMENTATION", "explain", "easy", "concept", ["Experiment Sizing"],
 "What is the 'Minimum Detectable Effect' (MDE) in A/B testing?",
 "The MDE is the smallest relative or absolute change in a metric that the business actually cares about detecting (e.g., a 2% lift in conversion). It must be set *before* the experiment starts because it heavily dictates the required sample size; detecting a tiny 1% MDE requires massively more traffic and time than detecting a massive 20% MDE.",
 ["The smallest metric change the business actually cares about detecting", "Must be set before the experiment to calculate the required sample size", "Detecting a smaller MDE requires exponentially more traffic/time"],
 ["It is a microscopic effect that requires a microscope to see"]),

("ANALYTICAL_EXPERIMENTATION", "debug", "hard", "debugging", ["Aggregation Bias", "Segmentation"],
 "You run an A/B test comparing a new Search Algorithm. The overall 'Click-Through Rate' is identical between Control and Treatment. You segment the queries into 'Head' (common) and 'Torso/Tail' (rare) queries. You find the new algorithm drastically improved Tail queries but slightly degraded Head queries. What analytical failure almost occurred?",
 "The 'Tyranny of Averages' or an Aggregation masking effect. The overwhelming volume of the Head queries (which slightly degraded) completely drowned out and hid the massive improvements in the Tail queries when aggregated together into a single mean. By failing to segment the data by query intent/frequency, the business almost threw away a highly valuable algorithmic improvement for long-tail searches.",
 ["'Tyranny of Averages' / Aggregation masking effect", "The massive volume of slightly degraded Head queries drowned out the massive Tail improvements", "Aggregated means hide severe underlying variances across disparate segments"],
 ["The algorithms negotiated a truce and decided to tie"]),

("ANALYTICAL_EXPERIMENTATION", "tradeoff", "medium", "tradeoff", ["Confidence Intervals"],
 "What is the analytical tradeoff of using a 99% Confidence Interval versus a 90% Confidence Interval when estimating a business metric?",
 "A 99% CI provides extreme statistical certainty that the true value lies within the range, but the tradeoff is that the range will be extremely wide and vague (e.g., 'Revenue will be between $1M and $10M'), which isn't actionable for business planning. A 90% CI provides a much tighter, precise, and actionable range (e.g., 'Revenue between $4M and $6M'), but carries a 10% risk of being completely wrong.",
 ["99% CI: Extreme certainty, but the range is extremely wide, vague, and un-actionable", "90% CI: Tighter, precise, highly actionable business range", "Tradeoff: 90% CI carries a higher risk (10%) of the true value falling outside the bounds"],
 ["99% CI takes 99 days to calculate on a standard computer"]),

("ANALYTICAL_EXPERIMENTATION", "scenario", "medium", "scenario", ["Guardrail Metrics"],
 "You launch an A/B test. Treatment is a massive refactor of the checkout page using a new JavaScript framework. The Conversion Rate in Treatment drops significantly. You suspect a technical issue. What specific secondary 'Guardrail Metrics' should you check to prove it's a technical failure rather than a UX failure?",
 "You must check technical guardrail metrics like Page Load Time (Latency), JavaScript Error Rates, API Timeout Rates, and Crash Rates across devices. If the new framework increased page load time by 3 seconds or spiked JS errors on older mobile devices, that technical degradation is the true root cause of the conversion drop, not necessarily the new UI/UX design.",
 ["Check technical 'Guardrail Metrics'", "Analyze Page Load Time (Latency), JS Error Rates, and Crash Rates", "Technical degradation (e.g., 3s slower load) causes conversion drops independent of UX design"],
 ["Check if the servers physically crashed into each other"]),

("ANALYTICAL_EXPERIMENTATION", "implement", "hard", "implementation", ["Proxy Metrics", "Velocity"],
 "You want to run an A/B test, but the business cannot afford to wait 4 weeks to reach statistical significance on the primary metric ('Completed Purchase'). How do you architect the analysis to reach a valid decision much faster?",
 "You must identify and use a 'Proxy Metric' (or Leading Indicator). You analytically prove using historical correlation that a top-of-funnel action (like 'Add to Cart' or 'Initiate Checkout') has massive predictive power for 'Completed Purchase'. Because 'Add to Cart' happens 10x more frequently, it reaches statistical significance in a fraction of the time, allowing you to confidently predict downstream impact.",
 ["Identify a 'Proxy Metric' (Leading Indicator) like 'Add to Cart'", "Prove historically that the proxy highly correlates with the downstream primary metric", "Because the proxy occurs more frequently, it reaches statistical significance much faster"],
 ["Just stop the test after 1 day and multiply the results by 28"]),

("ANALYTICAL_EXPERIMENTATION", "fundamentals", "easy", "concept", ["Errors"],
 "What is a 'False Positive' (Type I Error) in the context of A/B testing?",
 "A False Positive occurs when the statistical test concludes that the Treatment variant beat the Control variant, but in reality, there is no actual underlying difference. The observed lift was purely due to random chance noise in the sample data. In business, this results in wasting engineering time shipping a useless feature.",
 ["The test concludes Treatment won, but there is no actual real-world difference", "The observed lift was purely due to random chance noise in the data sample", "Results in wasting engineering resources shipping a useless feature"],
 ["A False Positive is when a user accidentally clicks the 'Like' button"])
]
