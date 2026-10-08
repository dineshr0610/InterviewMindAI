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

ROLE = "Data Analyst"
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
    # Bucket 1: A/B TESTING MATHEMATICS / EXPERIMENT DESIGN
    ("B1", "tradeoff", "hard", "tradeoff", ["A/B Testing"], "A Product Manager wants to run an A/B test but insists on stopping the experiment as soon as a statistically significant result is reached, even if it only takes two days. Why is this statistically invalid, and what phenomenon does it introduce?", "This is known as 'Peeking' or sequential testing without proper correction. Checking the p-value repeatedly and stopping as soon as it drops below 0.05 severely inflates the False Positive Rate (Type I Error). Random fluctuations in early data are practically guaranteed to show false significance. The test must be run for the pre-calculated sample size/duration to achieve the designed statistical power and to account for day-of-week seasonality.", ["Peeking inflates the False Positive Rate (Type I Error)", "Random fluctuations cause early false significance", "Must run for the pre-calculated sample size/duration"], ["It slows down product velocity"]),
    ("B1", "scenario", "medium", "scenario", ["A/B Testing"], "During a marketing campaign experiment, you test 20 different email subject lines against a control simultaneously. If you use a standard alpha of 0.05, what is the statistical danger, and how do you correct it?", "This is the 'Multiple Comparisons Problem'. When testing 20 variants at alpha=0.05, the probability of at least one false positive (finding a winner purely by chance) spikes to 64% (1 - 0.95^20). To correct it, you must apply a family-wise error rate correction, such as the Bonferroni correction (alpha/20 = 0.0025 per test), or control the False Discovery Rate (FDR) using the Benjamini-Hochberg procedure.", ["Multiple Comparisons Problem inflates family-wise error rate", "False positive probability spikes significantly", "Correct using Bonferroni or False Discovery Rate (FDR) methods"], ["Just pick the one with the highest click rate"]),
    ("B1", "optimize", "hard", "architecture", ["A/B Testing"], "Your company wants to run an A/B test on a core metric that naturally has massive variance (e.g., total spend per user), which would normally require an impractically large sample size. How can you use pre-experiment data to reduce the required sample size?", "You can use CUPED (Controlled Experiments Using Pre-Experiment Data) for Variance Reduction. By using a user's pre-experiment data (e.g., their spend in the prior 30 days) as a covariate, you can linearly regress the experiment metric on the pre-experiment metric. You analyze the *residual* variance instead of the raw variance. This dramatically reduces the noise caused by natural user differences, increasing statistical power and reducing the required sample size.", ["Use CUPED (Controlled Experiments Using Pre-Experiment Data)", "Use pre-experiment data as a covariate to explain natural variance", "Analyze residuals to increase statistical power"], ["Delete all outliers from the dataset"]),
    ("B1", "diagnose", "medium", "debugging", ["A/B Testing"], "An A/B test in a two-sided marketplace (like Uber or Airbnb) shows a massive 15% lift in bookings for the treatment group. However, when the feature is rolled out to 100% of users, the actual overall lift is 0%. What experimental design flaw caused this?", "This is caused by Network Effects or Interference. In a marketplace with constrained supply (e.g., drivers or hotel rooms), the treatment group 'stole' the limited supply from the control group. The treatment looked incredibly successful relative to the control, but the overall system capacity did not increase. To prevent this, you must run market-level randomization (e.g., treating whole cities/regions) or switch-back testing (alternating time periods) rather than user-level randomization.", ["Network Effects / Interference / Cannibalization", "Treatment group cannibalized constrained supply from the control group", "Requires market-level, cluster, or switch-back randomization"], ["The database was caching the old results"]),
    ("B1", "diagnose", "medium", "debugging", ["A/B Testing"], "A UI redesign A/B test shows an initial 10% drop in conversion rate during the first week, but by the third week, the treatment group outperforms the control group by 5%. What psychological/behavioral phenomena explain this shift?", "This represents the 'Novelty Effect' wearing off, combined with a 'Learning Curve' (or Primacy Effect). Initially, existing users are disoriented by the UI change, causing performance to drop as they relearn the interface. Over time, as users adapt to the new design, its true underlying efficiency emerges. This underscores why A/B tests involving major UI changes must be run long enough to outlast the novelty/learning period.", ["Novelty Effect / Learning Curve", "Users initially perform worse due to disorientation", "Requires running the test long enough for behavior to stabilize"], ["The servers were slow during the first week"]),
    ("B1", "scenario", "medium", "scenario", ["A/B Testing"], "You run an A/B test and calculate a p-value of 0.052 (where alpha=0.05). The Product Manager says, 'It's basically 0.05, let's roll it out.' How do you respond analytically and from a business decision framework?", "Analytically, the result is not statistically significant at the pre-defined threshold; we cannot confidently reject the null hypothesis. However, from a business perspective, the decision depends on the 'cost of being wrong'. If the change is cheap to maintain, reversible, and carries no downside risk, the PM's decision might be acceptable risk. If the change involves a massive backend rewrite or risks revenue, strict adherence to the significance threshold is mandatory. I would present the Confidence Interval to show the range of probable impact rather than just the p-value.", ["Analytically not significant; cannot reject null hypothesis", "Business decision depends on the cost of being wrong (risk tradeoff)", "Present Confidence Intervals to show the range of probable impact"], ["Tell the PM they are mathematically illiterate"]),
    ("B1", "explain", "easy", "concept", ["A/B Testing"], "In experiment design, what is the 'Minimum Detectable Effect' (MDE), and how does it relate to Sample Size?", "The Minimum Detectable Effect (MDE) is the smallest true lift or change in a metric that the experiment is mathematically powered to reliably detect. It has an inverse relationship with Sample Size: if you want to detect a tiny change (a small MDE), you need a massive sample size. If you only care about detecting massive changes (a large MDE), you can achieve that with a much smaller sample size.", ["Smallest true lift the experiment is powered to detect", "Inverse relationship with Sample Size", "Small MDE requires large sample size; Large MDE requires small sample size"], ["MDE is the final result of the test"]),
    ("B1", "scenario", "hard", "scenario", ["A/B Testing"], "An A/B test on a homepage button shows no overall statistical significance. The PM slices the data and finds that users from Canada on Android devices showed a significant 25% lift, and proposes launching the feature only for that segment. What statistical fallacy is occurring?", "This is an example of the 'Multiple Comparisons Problem' exacerbated by 'Data Dredging' or 'P-hacking' (specifically Heterogeneous Treatment Effects analysis done post-hoc). If you slice an insignificant overall test into dozens of overlapping segments, random noise guarantees that at least one obscure segment will look statistically significant. Segment analysis must be defined *before* the experiment starts, or the p-values must be severely corrected (e.g., Bonferroni) to avoid launching false positives.", ["Data Dredging / P-hacking / Multiple Comparisons", "Slicing data post-hoc guarantees finding false positive segments due to random noise", "Segments must be pre-defined or p-values severely corrected"], ["Canada just has better Android phones"]),
    ("B1", "compare", "medium", "compare", ["A/B Testing"], "When communicating A/B test results to non-technical stakeholders, why is reporting a 'Confidence Interval' often much safer and more useful than reporting a 'p-value'?", "A p-value is highly abstract, often misinterpreted as the probability that the variant is worse, and says nothing about the *magnitude* of the effect. A Confidence Interval provides a tangible range of expected business impact (e.g., 'We are 95% confident the true revenue lift is between +$10k and +$50k'). It instantly communicates both the direction of the effect and the degree of uncertainty, anchoring the business decision in real numbers.", ["P-values are abstract and easily misinterpreted", "Confidence Intervals show the expected magnitude of business impact", "CIs communicate both direction and uncertainty in tangible terms"], ["P-values are only used in academia"]),
    ("B1", "diagnose", "medium", "debugging", ["A/B Testing"], "An A/B test on a pricing page shows a massive 20% increase in clicks on the 'Buy Now' button. However, total company revenue remained completely flat. What analytical concept explains this discrepancy?", "Metric Cannibalization (or a shift in the funnel bottleneck). The new design successfully moved users past the pricing page (increasing clicks), but those users dropped off later in the checkout flow. Alternatively, it cannibalized sales from a different product line. This highlights why A/B tests must always measure an ultimate 'Guardrail' or 'North Star' metric (like total realized revenue) rather than optimizing purely for intermediate micro-conversions.", ["Metric Cannibalization / Funnel Bottleneck Shift", "Users converted on the micro-metric but dropped off later", "Must track ultimate Guardrail or North Star metrics (total revenue)"], ["The tracking pixel was broken on the Buy button"]),

    # Bucket 2: CAUSAL INFERENCE
    ("B2", "explain", "hard", "concept", ["Causal Inference"], "Explain the core methodology of 'Difference-in-Differences' (DiD) for observational data, and specify its most critical assumption.", "DiD evaluates the causal effect of an intervention when an A/B test is impossible. It compares the change in outcomes over time between a treatment group and a control group. Instead of comparing absolute levels, it subtracts the control group's pre/post difference from the treatment group's pre/post difference to isolate the true effect. The most critical assumption is the 'Parallel Trends Assumption': in the absence of the treatment, the difference between the two groups would have remained constant over time.", ["Compares the change over time between treatment and control groups", "Subtracts control difference from treatment difference to isolate effect", "Relies on the 'Parallel Trends Assumption'"], ["It takes the difference of two SQL tables"]),
    ("B2", "scenario", "medium", "scenario", ["Causal Inference"], "You are analyzing the impact of a new 'VIP Customer' support tier, which was granted only to users who spent exactly $500 or more last year. How would you design a causal analysis to measure the true impact of this tier without an A/B test?", "You should use a Regression Discontinuity Design (RDD). Because the $500 threshold is a sharp, arbitrary cutoff, users who spent $499 are virtually identical in behavior and demographics to users who spent $500. By analyzing the outcomes of users tightly clustered just above and just below the $500 cutoff, you can isolate the causal impact of the VIP support tier, as the assignment near the threshold is 'as good as random'.", ["Regression Discontinuity Design (RDD)", "Analyzes users just above and just below an arbitrary strict cutoff", "Assignment near the threshold mimics random assignment"], ["Just compare everyone who spent $10 to everyone who spent $1000"]),
    ("B2", "diagnose", "medium", "debugging", ["Causal Inference"], "You evaluate an ad campaign and find that users who clicked the ad have a 50% higher purchase rate than users who didn't click. Marketing claims the ad caused a massive lift. Why is this causal claim fundamentally flawed?", "This is a classic example of Selection Bias and Confounding. The users who chose to click the ad already had a higher underlying intent to purchase the product than those who ignored it. The ad click is highly correlated with purchase intent, but not necessarily the *cause* of the purchase. To find the true causal lift, you must compare a randomized holdout group (who were never shown the ad) against the group who were exposed to the ad.", ["Selection Bias / Confounding Variables", "Users who click already possess higher purchase intent", "Must compare randomized holdout group to exposed group"], ["The ad pixel fired twice"]),
    ("B2", "scenario", "hard", "scenario", ["Causal Inference"], "A hospital wants to know if a new drug works. You notice that doctors only prescribe the new drug to the absolute sickest patients. A naive analysis shows patients taking the new drug die at a higher rate. What is this bias, and how might Propensity Score Matching (PSM) mitigate it?", "This is Omitted Variable Bias (Confounding by indication), where disease severity influences both the treatment and the outcome. Propensity Score Matching (PSM) mitigates this by calculating the probability (propensity score) that each patient would receive the drug based on all observable pre-treatment characteristics (age, severity, comorbidities). It then matches treated patients with control patients who have nearly identical propensity scores, simulating a randomized control trial to isolate the drug's effect.", ["Omitted Variable Bias / Confounding by indication", "PSM calculates probability of treatment based on observable traits", "Matches treated and untreated units with similar probabilities to simulate RCT"], ["The drug is just poisonous"]),
    ("B2", "diagnose", "medium", "debugging", ["Data Analysis"], "You analyze the historical performance of all companies currently listed in the S&P 500 and conclude that their average 10-year growth is incredibly high. What bias invalidates this analysis as a benchmark for general corporate growth?", "Survivorship Bias. The analysis only looks at companies that 'survived' long enough and grew large enough to be in the S&P 500 today. It entirely excludes companies that went bankrupt, merged, or shrank during that 10-year period. By ignoring the failures that fell out of the dataset, the average growth metric is massively and artificially inflated.", ["Survivorship Bias", "Only includes entities that 'survived' a selection process", "Ignores failures, artificially inflating the success metric"], ["The stock market always goes up"]),
    ("B2", "scenario", "hard", "scenario", ["Causal Inference"], "What is 'Instrumental Variables' (IV) analysis, and what two strict conditions must an instrument satisfy?", "IV analysis is used to estimate causal relationships when there is unobserved confounding (e.g., measuring the effect of education on income, where 'innate ability' is an unobserved confounder). An instrument is a third variable (e.g., proximity to a college) that is used to isolate the variation in the treatment. It must satisfy two conditions: 1) Relevance: The instrument must strongly affect the treatment assignment. 2) Exclusion Restriction: The instrument must affect the outcome *only* through its effect on the treatment, and have no direct path to the outcome.", ["Used when there is unobserved confounding", "Relevance: Instrument must strongly affect treatment", "Exclusion Restriction: Instrument affects outcome ONLY through the treatment"], ["It is an analysis of musical instruments in data"]),
    ("B2", "diagnose", "hard", "debugging", ["Data Analysis"], "You analyze an e-commerce platform. Across every single product category, Conversion Rate for Mobile users is higher than for Desktop users. However, when you aggregate all categories together, Desktop has a higher overall Conversion Rate than Mobile. What is this called, and how does it happen?", "This is Simpson's Paradox. It occurs when a trend appears in different groups of data but disappears or reverses when these groups are combined. In this scenario, it happens because of a confounding variable (e.g., traffic volume). Mobile might have higher conversion rates on cheap items, but Desktop receives vastly more traffic on high-priced, low-converting items. The weighted average of the combined data mathematically flips the overall aggregate rate.", ["Simpson's Paradox", "Trends in subgroups reverse when the groups are aggregated together", "Caused by unequal weighting and a confounding variable across the groups"], ["The SQL query used an INNER JOIN instead of a LEFT JOIN"]),
    ("B2", "architecture", "medium", "architecture", ["Causal Inference"], "A government suddenly bans a specific feature in your app on January 1st. You want to measure the impact of this policy change on daily active users. What specific quasi-experimental analysis technique is best suited for this?", "Interrupted Time Series (ITS) analysis. You plot the daily active users for a long period before January 1st to establish the pre-intervention trend and intercept. You then analyze the data after January 1st to see if there is a statistically significant change in the level (immediate drop) or the slope (gradual decline) of the trend line, relative to the counterfactual projection of the pre-intervention trend.", ["Interrupted Time Series (ITS)", "Establishes a pre-intervention trend and intercept", "Checks for significant changes in level or slope after the intervention"], ["Just compare December's average to January's average"]),
    ("B2", "tradeoff", "hard", "tradeoff", ["Causal Inference"], "When attempting to prove causality in observational data, what is the danger of controlling for a 'Collider' variable?", "A Collider is a variable that is causally influenced by *both* the treatment and the outcome (or by unobserved confounders of both). Controlling for (or conditioning on) a confounder removes bias, but controlling for a collider *introduces* bias (Collider Bias / Berkson's Paradox). It creates a false, spurious correlation between the treatment and the outcome that did not actually exist in the raw data, destroying your causal inference.", ["Collider is influenced by both the treatment and the outcome", "Controlling for a collider introduces spurious correlations (Collider Bias)", "Destroys causal inference by creating false associations"], ["Colliders cause the database to crash"]),
    ("B2", "explain", "medium", "concept", ["Data Analysis"], "In marketing attribution, explain the difference between 'First-Touch', 'Last-Touch', and 'Shapley Value' attribution models.", "First-Touch assigns 100% of the conversion credit to the very first ad the user clicked (favoring brand awareness). Last-Touch assigns 100% of the credit to the final ad clicked right before purchase (favoring retargeting). Shapley Value (borrowed from cooperative game theory) looks at all combinations of touchpoints across user journeys to mathematically distribute credit based on the *incremental marginal contribution* of each ad channel to the final conversion.", ["First-Touch: 100% credit to the initial awareness interaction", "Last-Touch: 100% credit to the final closing interaction", "Shapley Value: distributes credit based on incremental marginal contribution"], ["First-touch is for mobile, Last-touch is for desktop"]),

    # Bucket 3: ADVANCED TEMPORAL DATA / TIME SERIES
    ("B3", "diagnose", "hard", "debugging", ["Time Series"], "You build a predictive model to forecast daily revenue. The model shows 99% accuracy in backtesting, but fails miserably in production. You discover you used `user_lifetime_value` as a feature. What temporal error did you commit?", "Temporal Data Leakage (or Target Leakage). `user_lifetime_value` is calculated using data from the *entire* lifecycle of the user, including revenue generated *after* the date you are trying to predict. During backtesting, the model essentially 'looked into the future' to predict the past. In production, the future data doesn't exist yet, causing the model to fail.", ["Temporal Data Leakage / Target Leakage", "Using future information to predict past/current events during training", "The feature won't be available at prediction time in production"], ["The model was trained on too few epochs"]),
    ("B3", "scenario", "medium", "scenario", ["Time Series"], "When designing a daily rolling 7-day average for active users (DAU/MAU), what is the analytical tradeoff between using a 7-day window versus a 30-day window?", "The tradeoff is between 'Smoothness' and 'Lag' (responsiveness). A 30-day rolling average provides a very smooth trend line, entirely absorbing weekly seasonality and minor spikes, but it has severe lag—it takes weeks for a sudden, genuine shift in user behavior to become visible. A 7-day window is much more responsive to sudden changes (less lag) but is much noisier and more susceptible to single-event outliers.", ["Tradeoff between Smoothness and Lag (responsiveness)", "30-day is smooth but heavily lags behind real sudden changes", "7-day is highly responsive but noisy"], ["A 30-day window uses more server RAM"]),
    ("B3", "explain", "medium", "concept", ["Time Series"], "In Time Series analysis, what does the Augmented Dickey-Fuller (ADF) test check for, and why is it a necessary prerequisite for ARIMA modeling?", "The ADF test checks a time series for 'Stationarity' (whether its statistical properties like mean and variance remain constant over time, without trends or seasonality). It is a necessary prerequisite because ARIMA models (and many forecasting algorithms) mathematically assume the data is stationary. If the ADF test fails, the data must be transformed (e.g., via differencing or log transformations) until it becomes stationary before modeling.", ["Checks for Stationarity (constant mean/variance over time)", "ARIMA algorithms mathematically require stationary data", "Non-stationary data must be differenced before modeling"], ["It checks if the database is running out of space"]),
    ("B3", "architecture", "hard", "architecture", ["Data Warehousing"], "A data warehouse stores user profiles. A user changes their subscription from 'Basic' to 'Pro' in November. If you run a query in December to analyze October's revenue by subscription tier, the user's October revenue is incorrectly categorized as 'Pro'. What data warehousing architectural pattern is missing?", "The warehouse is missing 'Slowly Changing Dimensions (SCD) Type 2'. Currently, the user table is simply overwriting the old subscription status (SCD Type 1), destroying historical truth. SCD Type 2 solves this by inserting a completely new row for the user when an attribute changes, using `valid_from` and `valid_to` timestamp columns. This preserves the historical state of the dimension for accurate point-in-time temporal joins.", ["Slowly Changing Dimensions (SCD) Type 2", "Requires inserting new rows with valid_from and valid_to timestamps", "Preserves historical state for accurate point-in-time analysis"], ["The database index is corrupted"]),
    ("B3", "scenario", "medium", "scenario", ["Data Analysis"], "You are building a time-to-event (survival) analysis to understand how long it takes for a newly registered user to make their first purchase. Some users have not purchased yet, but they only registered yesterday. How do you handle these users mathematically?", "You must handle them using 'Right Censoring' (e.g., via Kaplan-Meier estimators). You cannot simply delete them (which biases the analysis toward fast purchasers), nor can you assume they will never purchase. Right censoring allows the mathematical model to use the information that the user has 'survived' without purchasing for exactly 1 day, incorporating their partial time-in-state into the overall probability curve without treating them as a failure.", ["Use Right Censoring (e.g., Kaplan-Meier estimator)", "Incorporates their partial time-in-state into the probability model", "Avoids bias from deleting them or assuming failure"], ["Set their purchase time to infinity"]),
    ("B3", "tradeoff", "medium", "tradeoff", ["Time Series"], "You have a dataset of hourly temperature readings with occasional missing hours due to sensor failure. What is the tradeoff between filling missing values with 'Forward Fill' versus 'Linear Interpolation'?", "Forward Fill simply copies the last known value forward. It prevents data leakage (you only use past data) and is safe for volatile or step-change data, but can create artificial flatlines. Linear Interpolation draws a straight line between the point before and the point after the gap. It provides a much smoother and often more accurate estimation for continuous data (like temperature), but it introduces 'future leakage' because calculating the gap relies on knowing the value *after* the gap.", ["Forward Fill uses only past data (no leakage) but creates flatlines", "Interpolation uses future data to draw a smooth line (causes future leakage)", "Interpolation is better for continuous trends if leakage is acceptable"], ["Forward fill deletes the missing rows"]),
    ("B3", "diagnose", "medium", "debugging", ["Time Series"], "When calculating the standard error of the mean for daily active users over a month, you use the standard formula `sigma / sqrt(N)`. Why will this drastically underestimate the true uncertainty (confidence interval) of your metric?", "The standard error formula assumes that all N observations are independent and identically distributed (i.i.d.). Time series data is highly Autocorrelated (Serial Correlation)—the number of users today is heavily dependent on the number of users yesterday. Because the data points are not independent, the *effective* sample size is much smaller than N. Using the standard formula ignores autocorrelation and results in falsely narrow confidence intervals.", ["Formula assumes observations are independent (i.i.d.)", "Time series data has heavy Autocorrelation / Serial Correlation", "Effective sample size is smaller, causing underestimation of uncertainty"], ["The formula requires calculating the median instead"]),
    ("B3", "architecture", "hard", "architecture", ["Data Analysis"], "You are tasked with building a Cohort Retention Heatmap (e.g., Month 1, Month 2 retention). What is the critical difference in the temporal axis between 'Calendar Time' and 'Lifecycle Time', and which must you use for the X-axis of a retention matrix?", "Calendar Time aligns events to specific absolute dates (e.g., what happened in January, February). Lifecycle Time (or relative time) aligns events to the 'age' of the user since their specific starting event (e.g., Month 0, Month 1 after registration), regardless of the calendar month they joined. A proper Cohort Retention Heatmap uses Cohorts (grouped by Calendar Time of acquisition) on the Y-axis, and Lifecycle Time (Month 1, Month 2) on the X-axis.", ["Calendar Time is absolute dates", "Lifecycle Time is relative 'age' since the user's start event", "Retention X-axis strictly requires Lifecycle Time alignment"], ["Calendar time uses timezones, lifecycle time is UTC"]),
    ("B3", "scenario", "medium", "scenario", ["Time Series"], "You are analyzing global user activity. The data engineering team converted all local timestamps to UTC. When plotting 'activity by hour of day', the chart shows an unexplainable massive double-spike. What timezone issue causes this?", "Converting everything to UTC destroys the 'local hour of day' context. A user acting at 9:00 AM in Tokyo and a user acting at 9:00 AM in New York are aggregated into completely different UTC hours. If you plot by UTC hour, you will see spikes reflecting the waking hours of your largest geographic markets, not the actual local time of day the user prefers to act. You must extract the hour *before* converting to UTC, or use a timezone-aware local offset.", ["UTC conversion destroys 'local time of day' context", "Aggregates reflect geographic market sizes, not local behavior patterns", "Must extract the hour in the user's local timezone offset"], ["The database failed to index the timestamp"]),
    ("B3", "explain", "medium", "concept", ["Time Series"], "Explain the three core mathematical components of 'Time Series Decomposition' (e.g., STL decomposition).", "A time series is mathematically decomposed into three components: 1) Trend: The underlying long-term progression of the series (e.g., YoY user growth). 2) Seasonality: The repeating, predictable periodic fluctuations (e.g., higher sales every December, or lower traffic every weekend). 3) Residual (or Noise): The random, unpredictable remaining variance after the trend and seasonality have been removed from the data.", ["Trend: underlying long-term direction", "Seasonality: predictable, repeating periodic cycles", "Residual/Noise: random remaining variance"], ["Past, Present, and Future components"]),

    # Bucket 4: METRICS & PRODUCT ANALYTICS
    ("B4", "diagnose", "medium", "debugging", ["Metrics"], "Your company's 'Average Revenue Per User' (ARPU) suddenly dropped 15% this week. Overall Revenue increased, and retention of paying users is stable. What demographic shift likely explains this?", "Denominator Drift (or a shift in the user mix). A massive influx of new, free, or low-quality users (e.g., from a viral marketing campaign or a new country launch) drastically inflated the denominator (Total Users). Even though overall revenue went up, the flood of non-paying users diluted the *average* per user. The metric dropped not because business is bad, but because the underlying population mix fundamentally changed.", ["Denominator Drift / Shift in User Mix", "A massive influx of non-paying users inflated the denominator", "Dilutes the average despite absolute revenue growth"], ["The database dropped some revenue rows"]),
    ("B4", "tradeoff", "easy", "tradeoff", ["Metrics"], "When analyzing highly skewed metrics like 'Lifetime Revenue per User' or 'Time to Resolution', why is the Median often a better metric for product decisions than the Mean (Average)?", "The Mean is highly sensitive to extreme outliers. In revenue, a single 'whale' user spending $100,000 can drag the mean upward, hiding the fact that 99% of users spend $0. The Median (the 50th percentile) is robust against outliers and represents the true 'typical' experience of the user base. Tracking both is ideal, but the median provides a more grounded operational metric.", ["Mean is highly sensitive to extreme outliers ('whales')", "Median is robust to outliers and represents the 'typical' user", "Mean can hide the reality of the majority of users"], ["The median is easier to calculate in SQL"]),
    ("B4", "scenario", "medium", "scenario", ["Metrics"], "A product team wants to run an experiment to increase 'Push Notification Click-Through Rate' by sending 5x more notifications. What 'Guardrail Metric' must you insist they track to prevent catastrophic product damage?", "You must track negative downstream metrics like 'Notification Opt-Out Rate', 'App Uninstalls', or 'Daily Active Users (DAU)'. Sending 5x more notifications will almost certainly increase the absolute number of clicks, making the primary metric look successful. However, it will likely annoy users, causing them to disable notifications entirely or delete the app. Guardrail metrics protect the long-term health of the business from short-sighted local optimizations.", ["Guardrail metrics protect against short-sighted local optimizations", "Must track Notification Opt-Outs or App Uninstalls", "Prevents destroying long-term retention for short-term clicks"], ["Track the server CPU usage"]),
    ("B4", "diagnose", "hard", "debugging", ["Metrics"], "You define an 'Active User' as anyone who opens the app. Marketing launches an email campaign. DAU skyrockets, but 'Songs Played' (the core product value) remains flat. What is the fundamental flaw in the 'Active User' metric definition?", "The metric suffers from the 'Passive vs. Active' engagement flaw. Opening an app in response to an email is a passive, shallow interaction (often resulting in an immediate bounce). If the core metric is just 'opening the app', it can be easily manipulated by spamming users without delivering actual product value. A robust metric should be defined around a core value-exchange action (e.g., 'Played a Song' or 'Sent a Message').", ["Metric counts shallow/passive interactions (app opens)", "Easily manipulated by marketing spam without driving true value", "Metric should require a core value-exchange action (e.g., played a song)"], ["The app is crashing on the second screen"]),
    ("B4", "architecture", "hard", "architecture", ["Product Analytics"], "How do you mathematically distinguish between a 'False Positive' drop-off in a Funnel Analysis and a genuine user abandonment, particularly in B2B SaaS products?", "Funnel analyses typically enforce a strict time window (e.g., completing steps 1-4 within a single session). In B2B SaaS, workflows are asynchronous; a user might complete step 1, wait three days for manager approval, and complete step 2 in a new session. A naive session-based funnel will report this as a massive drop-off (False Positive). You must architecture the funnel using an elongated conversion window (e.g., 7 days) or a cross-session user-ID join to capture the true asynchronous conversion rate.", ["Naive funnels enforce single-session strict time windows", "B2B workflows are multi-session and asynchronous", "Must use elongated conversion windows and cross-session user-ID joins"], ["Funnels only work on mobile apps"]),
    ("B4", "scenario", "medium", "scenario", ["Product Analytics"], "Your CEO asks you to forecast the 3-year LTV (Lifetime Value) of a new subscription tier that launched exactly 2 months ago. What analytical constraints prevent you from doing this accurately, and what proxy should you use instead?", "It is mathematically impossible to confidently forecast 3-year survival curves based on only 2 months of truncated data, as you have zero visibility into long-term churn behavior (e.g., annual renewal cliffs). Extrapolating early data out 3 years leads to wild inaccuracies. Instead of a 3-year forecast, you should pivot the business to track a leading indicator proxy, such as 'Month 1 Retention' or 'Engagement Frequency in Week 1', which historically correlate with high LTV.", ["Cannot extrapolate 3-year survival curves from 2 months of truncated data", "Zero visibility into long-term churn cliffs", "Use short-term leading indicators (Month 1 retention) as a proxy"], ["Use a deep learning neural network"]),
    ("B4", "diagnose", "medium", "debugging", ["Metrics"], "A sudden, perfectly vertical 50% spike appears in a core metric chart exactly at midnight on a Tuesday. The Product team claims the new feature is a massive success. What data quality framework should you apply before believing them?", "Sudden, perfectly geometric spikes are rarely human behavior. You should apply a technical diagnostic framework: 1) Instrumentation checks: Did an app update release at midnight that double-fires the tracking pixel? 2) Timezone/ETL checks: Did a batch cron job fail and replay duplicate data? 3) Definition checks: Did the underlying SQL logic for the metric change in the nightly dbt run? Always rule out data pipeline and instrumentation bugs before attributing sudden spikes to user behavior.", ["Sudden geometric spikes are rarely human behavior", "Check for double-firing instrumentation pixels in a new release", "Check for ETL batch job replays or metric definition changes in SQL"], ["Trust the data and celebrate the success"]),
    ("B4", "tradeoff", "medium", "tradeoff", ["Product Analytics"], "What is the tradeoff between calculating Retention using 'N-Day Retention' (e.g., active exactly on Day 7) versus 'Unbounded Retention' (e.g., active on Day 7 or any day after)?", "N-Day Retention measures strict, habitual daily usage (e.g., social media apps); it is harsh and drops quickly if a user skips a single day. Unbounded Retention (Rolling Retention) asks if the user *ever* returns after a specific point. It is much more forgiving and appropriate for products with lower natural frequencies (e.g., food delivery or travel apps). Using N-Day on a low-frequency app will falsely report catastrophic churn.", ["N-Day measures strict habitual usage (punishes skipping a day)", "Unbounded measures if they EVER return (forgiving)", "Must match the metric to the natural frequency of the product"], ["N-Day is calculated in SQL, Unbounded in Pandas"]),

    # Bucket 5: DATA QUALITY & SQL MANIPULATION
    ("B5", "diagnose", "hard", "debugging", ["SQL"], "You write a SQL query: `SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM banned_users)`. You know there are thousands of active users, but the query returns zero rows. What data quality issue causes this silent failure?", "This is caused by SQL's Three-Valued Logic and `NULL` values. If the `banned_users` table contains even a single row where `user_id` is `NULL`, the `NOT IN` evaluation for every user becomes `id != NULL`, which evaluates to `UNKNOWN` (not `TRUE`). Therefore, no rows pass the filter. You must either filter `WHERE user_id IS NOT NULL` in the subquery, or use a `NOT EXISTS` clause, which handles NULLs safely.", ["Three-Valued Logic in SQL", "If the subquery contains a NULL, NOT IN evaluates to UNKNOWN", "Fix by filtering NULLs or using NOT EXISTS"], ["The database is out of memory"]),
    ("B5", "compare", "medium", "compare", ["SQL"], "In SQL Window Functions, if you order sales data and three employees tie for the highest sales, explain the exact numerical difference in how `RANK()` versus `DENSE_RANK()` versus `ROW_NUMBER()` assigns their positions.", "`ROW_NUMBER()` arbitrarily breaks the tie and assigns 1, 2, 3. `RANK()` acknowledges the tie, assigns all three employees a rank of 1, but leaves a gap for the next person, assigning the fourth employee a rank of 4. `DENSE_RANK()` assigns all three employees a rank of 1, but leaves no gap, assigning the fourth employee a rank of 2.", ["ROW_NUMBER breaks ties (1, 2, 3)", "RANK ties but leaves gaps (1, 1, 1, 4)", "DENSE_RANK ties with no gaps (1, 1, 1, 2)"], ["They all do exactly the same thing randomly"]),
    ("B5", "architecture", "hard", "architecture", ["SQL"], "You have a single `events` table. You need to calculate the median time elapsed between a user's *first* purchase and their *second* purchase. How do you architect this SQL query?", "First, use a CTE with a Window Function: `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp ASC)` to assign an event sequence number. Second, self-join the CTE to itself where `A.user_id = B.user_id` and `A.row_num = 1` and `B.row_num = 2`. Third, calculate the `DATEDIFF` between the two timestamps. Finally, use `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY time_diff)` to aggregate the median time elapsed across all users.", ["Use ROW_NUMBER() partitioned by user ordered by time", "Self-join where row 1 joins to row 2", "Calculate timestamp diff and use PERCENTILE_CONT(0.5) for median"], ["Just subtract MIN(time) from MAX(time)"]),
    ("B5", "diagnose", "medium", "debugging", ["SQL"], "A marketing dashboard query executes a `JOIN` between `users` (10,000 rows) and `ad_clicks` (50,000 rows). The resulting dataset contains 5,000,000 rows, crashing the BI tool. What SQL error occurred?", "A Cartesian Product (or Cross Join explosion / fan-out). The `JOIN` condition was either completely omitted, contained a typo, or joined on non-unique columns containing massive amounts of duplicate keys (e.g., joining on `country` instead of `user_id`). This causes every row in the left table to multiply against every matching row in the right table, exponentially blowing up the dataset size.", ["Cartesian Product / Cross Join explosion / fan-out", "Missing or non-unique JOIN conditions", "Multiplies rows exponentially"], ["The database ran out of indexes"]),
    ("B5", "scenario", "medium", "scenario", ["Data Engineering"], "You are scheduling a daily SQL transformation script in Apache Airflow. Why is it critical to design the script to be 'Idempotent', and how is this achieved in SQL?", "Idempotency ensures that running the same script multiple times for the same day produces the exact same final state, without duplicating data. This is critical for data pipelines, because tasks will inevitably fail and be retried. In SQL, idempotency is achieved by beginning the script with a `DELETE FROM target_table WHERE date = '{{ execution_date }}'` before executing the `INSERT`, or by using `MERGE` (Upsert) statements with primary keys.", ["Idempotency ensures rerunning the script does not duplicate data", "Critical for pipeline retries and backfills", "Achieved via DELETE before INSERT or using MERGE/Upserts"], ["Idempotency makes the query run faster"]),
    ("B5", "diagnose", "hard", "debugging", ["Data Analysis"], "You query a production database for 'Total Sales Yesterday' at 8:00 AM and get $10,000. The CEO runs the exact same query at 5:00 PM and gets $11,500. The underlying SQL is identical and the timeframe is identical. What architectural reality of streaming data causes this?", "Late-arriving data (or out-of-order events) in a distributed system. Mobile devices that were offline yesterday might sync their purchase events to the server today when they connect to Wi-Fi. The ETL pipeline (Lambda/Kappa architecture) ingests these events and assigns them to their *original* event timestamp (yesterday). Therefore, historical aggregations will continuously update and mutate as late data arrives.", ["Late-arriving data / out-of-order events from offline clients", "Data is ingested today but timestamped for yesterday", "Historical aggregations mutate as delayed events sync"], ["The CEO has higher database permissions"]),
    ("B5", "architecture", "medium", "architecture", ["SQL"], "You need to match user-entered text (e.g., 'Macdonalds') to an official vendor list ('McDonalds'). Standard SQL `=` and `LIKE` fail. What class of algorithms must you use, and name one specific implementation?", "You must use Fuzzy Matching (String Distance) algorithms. These algorithms mathematically calculate how many character edits are required to transform one string into another. A common implementation available in many SQL dialects (or via Python UDFs) is the 'Levenshtein distance'. Another option is phonetic matching like 'Soundex', which compares strings based on how they sound rather than how they are spelled.", ["Fuzzy Matching / String Distance algorithms", "Calculates the number of character edits required (Levenshtein distance)", "Or uses phonetic similarity (Soundex)"], ["Use a massive CASE statement for every misspelling"]),
    ("B5", "tradeoff", "easy", "tradeoff", ["SQL"], "What is the primary danger of using `SELECT *` in a production data pipeline script that inserts data into another table?", "`SELECT *` tightly couples the query to the exact column structure of the source table. If a backend engineer adds, removes, or reorders a column in the source database, the `SELECT *` pipeline will instantly break (if schemas mismatch) or, far worse, silently insert the wrong data into the wrong columns in the target table. Production pipelines must always explicitly declare `SELECT col1, col2`.", ["Tightly couples the query to the source schema", "Breaks pipelines if upstream columns are added/removed/reordered", "Can silently insert data into the wrong target columns"], ["It uses too much internet bandwidth"])
]

BUCKET_KEYS = {
    "B1": ("A/B Testing", "Experiment Design", "Statistics", ["Data Analyst"]),
    "B2": ("Causal Inference", "Statistical Modeling", "Statistics", ["Data Analyst"]),
    "B3": ("Time Series Analysis", "Temporal Data", "Statistics", ["Data Analyst"]),
    "B4": ("Product Analytics", "Metrics", "Analytics", ["Data Analyst"]),
    "B5": ("Data Manipulation", "SQL Analytics", "SQL", ["Data Analyst", "Backend Developer"])
}

def main():
    with open(OUT, encoding="utf-8") as f:
        prior = [json.loads(l) for l in f if l.strip()]
    
    staged_q = [p["question"] for p in prior]
    staged_a = [p["expected_answer"] for p in prior]
    
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
            "category": "Data Science",
            "intent": intent,
            "difficulty": diff,
            "question_type": qt,
            "question": q,
            "expected_answer": a,
            "evaluation_rubric": {"strong_indicators": strong, "weak_indicators": weak}
        })

    # I have exactly 46 candidates above (10 + 10 + 10 + 8 + 8). Let me add 4 more to ensure EXACTLY 50 are generated.
    cands.extend([
        {
            "primary_role": ROLE,
            "applicable_roles": ["Data Analyst"],
            "primary_skill": "A/B Testing",
            "secondary_skills": ["Experiment Design"],
            "technology": "Statistics",
            "topic": "Experiment Interference",
            "category": "Data Science",
            "intent": "scenario",
            "difficulty": "medium",
            "question_type": "scenario",
            "question": "You run an A/B test on a social network feed algorithm. The treatment group shares 20% more posts. When deployed globally, shares remain completely flat. What type of interference caused this?",
            "expected_answer": "This is a Network Effect (specifically a spillover effect). Because users are connected, treating User A affects User B (the control). User A shares more posts, so User B sees more posts in their feed and shares more as well, inflating the baseline. The treatment and control groups were not isolated. You must use cluster randomization (e.g., isolating by disconnected communities) to prevent spillover.",
            "evaluation_rubric": {"strong_indicators": ["Network Effect / Spillover effect", "Treating one user affects the behavior of connected control users", "Requires cluster randomization"], "weak_indicators": ["The database was slow"]}
        },
        {
            "primary_role": ROLE,
            "applicable_roles": ["Data Analyst"],
            "primary_skill": "Data Manipulation",
            "secondary_skills": ["SQL Analytics"],
            "technology": "SQL",
            "topic": "Duplicates",
            "category": "Data Science",
            "intent": "implement",
            "difficulty": "medium",
            "question_type": "implementation",
            "question": "A logging error caused an `events` table to receive exact duplicate rows (all columns are identical, no primary key). How do you write a SQL query to delete the duplicates while keeping exactly one copy of each row?",
            "expected_answer": "You can use a CTE with `ROW_NUMBER()`. You partition by all columns to identify exact matches: `ROW_NUMBER() OVER (PARTITION BY col1, col2 ORDER BY (SELECT NULL)) as rn`. Then you delete from the CTE (in Postgres/SQL Server) or use the CTE to join/filter (in Snowflake/BigQuery) where `rn > 1`. Alternatively, you can `SELECT DISTINCT * INTO new_table`, drop the old table, and rename the new one.",
            "evaluation_rubric": {"strong_indicators": ["Use ROW_NUMBER() partitioned by all columns", "Filter/Delete where row_number > 1", "SELECT DISTINCT into a new table"], "weak_indicators": ["Use DELETE FROM events LIMIT 1"]}
        },
        {
            "primary_role": ROLE,
            "applicable_roles": ["Data Analyst"],
            "primary_skill": "Product Analytics",
            "secondary_skills": ["Metrics"],
            "technology": "Analytics",
            "topic": "Data Quality",
            "category": "Data Science",
            "intent": "diagnose",
            "difficulty": "easy",
            "question_type": "debugging",
            "question": "A dashboard tracks 'Users who completed onboarding'. On March 1st, the metric suddenly drops to exactly zero and stays there, while top-line revenue and daily active users remain completely normal. What is the most likely cause?",
            "expected_answer": "This is almost certainly an instrumentation or telemetry failure, not a behavioral shift. A front-end release likely broke the tracking pixel, the event name was changed in the code without updating the dashboard, or a data pipeline (ETL) job that populates that specific table failed. If users actually stopped onboarding, revenue and DAU would eventually drop as well.",
            "evaluation_rubric": {"strong_indicators": ["Instrumentation failure / broken tracking pixel", "Event name changed in the codebase", "ETL pipeline failure"], "weak_indicators": ["Users hated the new onboarding design"]}
        },
        {
            "primary_role": ROLE,
            "applicable_roles": ["Data Analyst"],
            "primary_skill": "Time Series Analysis",
            "secondary_skills": ["Temporal Data"],
            "technology": "Statistics",
            "topic": "Seasonality",
            "category": "Data Science",
            "intent": "optimize",
            "difficulty": "medium",
            "question_type": "optimize",
            "question": "You are forecasting daily sales for a retail company. The data shows strong weekly seasonality (high on weekends, low on Tuesdays) and strong annual seasonality (massive spikes in December). How do you handle multiple seasonalities in a forecasting model?",
            "expected_answer": "Standard models like basic ARIMA only handle a single seasonality easily. To handle multiple seasonalities, you must use algorithms specifically designed for complex seasonal patterns, such as TBATS (Trigonometric seasonality, Box-Cox, ARMA, Trend, Seasonal components) or Prophet (which models seasonalities as additive Fourier series components). Alternatively, you can use a tree-based model (like XGBoost) by engineering explicit features for `day_of_week` and `month_of_year`.",
            "evaluation_rubric": {"strong_indicators": ["Basic models struggle with multiple seasonalities", "Use Prophet (additive Fourier components) or TBATS", "Feature engineering (day_of_week, month_of_year) for tree models"], "weak_indicators": ["Just take a 7-day average"]}
        }
    ])

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
        c["generation_batch"] = "batch_46_data_analyst"

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
        "batch": "batch_46_data_analyst",
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
    
    with open(os.path.join(REPORTS_DIR, "phase4d_batch46_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_batch46_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Phase 4D - Batch 46 (Data Analyst)\n\n")
        f.write(f"- **Attempted**: {len(cands)}\n")
        f.write(f"- **Accepted**: {len(accepted)}\n")
        f.write(f"- **Rejected**: {sum(rej.values())}\n")
        f.write(f"- **Rejections**: {dict(rej)}\n\n")
        f.write("### Staging Totals\n")
        f.write(f"- **Previous Staging Total**: {len(prior)}\n")
        f.write(f"- **Final Staging Total**: {final_staging_total}\n")
        f.write(f"- **Data Analyst Role Total**: {role_counts[ROLE]}\n")
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

    print(f"Successfully generated 50 Data Analyst questions.")

if __name__ == "__main__":
    main()
