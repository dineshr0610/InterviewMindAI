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

ROLE = "ML Engineer"
VALID_INTENTS = {"fundamentals", "explain", "implement", "tradeoff", "debug", "scenario", "compare",
                 "architecture", "optimize", "diagnose"}
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system prompts|do not proceed|"
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
    # Bucket 1: FEATURE STORES & TRAINING-SERVING SKEW
    ("B1", "architecture", "hard", "architecture", ["Feature Stores"], "When generating a historical training dataset from a data warehouse, why is 'Point-in-Time Correctness' (Time-Travel Joins) an absolute architectural requirement?", "Without Point-in-Time correctness, a naive SQL join will fetch the *current* state of a feature (e.g., a user's lifetime total purchases today) and map it to an event that happened 6 months ago. This causes catastrophic 'Future Data Leakage'. The model trains on information that will not be available at the exact moment of inference in production, rendering the model completely invalid. Time-travel joins guarantee features are joined exactly as they existed precisely at the timestamp of the historical event.", ["Prevents Future Data Leakage", "Naive joins use the current state of a feature instead of the historical state", "Guarantees features exactly match the temporal state at the time of the event"], ["Time travel uses quantum mechanics"]),
    ("B1", "diagnose", "medium", "debugging", ["MLOps"], "A model's offline evaluation metrics are excellent, but online production performance is terrible. The Data Science team writes features using Pandas DataFrames in Jupyter, while the Backend team rewrites the feature extraction in Java for the production API. What is the diagnosis?", "This is a classic 'Training-Serving Skew' caused by logic mismatch. When two different teams write two separate codebases (Pandas vs Java) to calculate the exact same feature, subtle differences in handling nulls, rounding floats, or timezone offsets inevitably occur. The model receives a distribution of data in production that mathematically differs from its training data. The architectural fix is to unify the logic, typically via a centralized Feature Store that serves both environments.", ["Training-Serving Skew caused by logic mismatch", "Subtle bugs in handling nulls, rounding, or timezones between Pandas and Java", "Fix via a centralized Feature Store or unified transformation pipeline"], ["Java is slower than Python"]),
    ("B1", "compare", "medium", "compare", ["Feature Stores"], "Explain the architectural difference between an Offline Feature Store and an Online Feature Store.", "An Offline Feature Store is built for high-throughput, historical batch processing (e.g., Snowflake, Parquet files on S3) to generate massive training datasets. It prioritizes analytical aggregations over latency. An Online Feature Store is built for ultra-low latency, single-record retrieval during real-time inference (e.g., Redis, Cassandra). It strictly acts as a fast Key-Value lookup. A modern Feature Store platform automatically syncs the data between the two to guarantee consistency.", ["Offline: High-throughput batch processing for training (columnar/parquet)", "Online: Ultra-low latency Key-Value lookup for real-time inference (Redis/Cassandra)", "Automatic syncing guarantees consistency between environments"], ["Offline means it works without an internet connection"]),
    ("B1", "scenario", "medium", "scenario", ["MLOps"], "You are building a continuous training pipeline for a fraud detection model. However, you only definitively know if a transaction was fraudulent if a user issues a chargeback 30 to 60 days later. How do you handle this 'Delayed Label' problem in the pipeline?", "Because ground truth is delayed, you cannot train a model on yesterday's data; all recent transactions will falsely appear as 'Not Fraud' (negatives). You must implement a maturity window (e.g., wait 60 days before moving data into the training set) to allow labels to settle. Alternatively, you can train on proxy metrics (e.g., internal risk flags that fire immediately) while waiting for the true labels, using multi-task learning or delayed feedback ingestion.", ["Ground truth (chargebacks) takes 60 days to arrive", "Recent data is heavily biased with false negatives", "Must implement a maturity window or use immediate proxy metrics"], ["Just assume all recent transactions are fraudulent"]),
    ("B1", "architecture", "hard", "architecture", ["Feature Engineering"], "You add a new feature, `user_30_day_clicks`, to a live model. The feature is calculated via a nightly batch job. At 2:00 PM, a brand new user registers and makes a prediction request. How should the system architecture handle this missing feature at inference time?", "The system encounters the 'Cold Start Feature' problem. The online feature store has no record for this user because the nightly job hasn't run. The architecture must include an Imputation Strategy defined directly within the model graph or feature pipeline (e.g., falling back to a global average or median). It must not throw a `NullPointerException` or simply inject `0` unless `0` is mathematically sound, otherwise it will distort the model's prediction.", ["Cold Start Feature problem (batch job hasn't run for the new user)", "Requires a strict Imputation Strategy (e.g., fallback to global median)", "Cannot blindly inject 0 or throw exceptions"], ["The system should ban the user until tomorrow"]),
    ("B1", "tradeoff", "medium", "tradeoff", ["Feature Engineering"], "What is the tradeoff between calculating a feature (e.g., `session_page_views`) dynamically within the inference API server versus pre-calculating it via a streaming job (e.g., Flink) and storing it in an Online Feature Store?", "Calculating dynamically within the API ensures absolute freshness (zero lag) and no complex data engineering overhead, but it heavily increases the API's CPU load and latency, especially for complex aggregations. Pre-calculating via a streaming engine (Flink) into an Online Feature Store drastically reduces API latency (it becomes a simple O(1) Redis lookup), but it introduces infrastructure complexity, pipeline maintenance, and a few seconds of 'staleness' lag.", ["Dynamic API calculation: Absolute freshness, but high latency/CPU load", "Streaming + Feature Store: Ultra-low API latency (O(1) lookup)", "Streaming adds infrastructure complexity and slight staleness lag"], ["Flink is slower than API calculation"]),
    ("B1", "scenario", "hard", "scenario", ["Feature Engineering"], "A Data Scientist invents a brilliant new feature: `time_since_last_password_reset`. They calculate it today and want to train a model on the last two years of historical data. What massive data engineering challenge does this pose?", "This requires a 'Historical Backfill'. The challenge is that you cannot simply calculate the feature based on the user's state *today*. You must simulate the feature exactly as it would have appeared at every single historical event over the last two years. This requires re-playing the entire raw event log chronologically to calculate the exact state of `time_since_last_password_reset` at millions of specific past timestamps, which is exceptionally computationally expensive.", ["Requires a Historical Backfill", "Cannot use current state; must calculate exact state at every past timestamp", "Requires computationally expensive re-playing of chronological raw event logs"], ["The database will run out of storage space immediately"]),
    ("B1", "diagnose", "medium", "debugging", ["Model Monitoring"], "A production model suddenly starts degrading. The monitoring dashboard shows massive 'Covariate Shift' (Data Drift) on a critical feature: `user_age`. The mean shifted from 35 to 0. What is the likely cause?", "This is almost certainly a data pipeline failure (ETL bug), not true statistical drift. A true demographic shift does not plunge the mean to exactly 0 overnight. An upstream data source likely dropped the column, a join failed, or an API format changed, causing the system to default the missing age values to 0 (or NULLs interpreted as 0). You must fix the pipeline, not retrain the model.", ["Pipeline failure / ETL bug, not true demographic drift", "Upstream source dropped the column or API format changed", "Defaulted missing values to 0"], ["The user base suddenly consists of newborns"]),
    ("B1", "architecture", "easy", "architecture", ["MLOps"], "Why is strict 'Feature Versioning' critical in an ML platform?", "If a data engineer updates the logic of a feature (e.g., changing `total_revenue` to include taxes) without versioning it, they silently overwrite the historical definition. Any model trained on the old definition (without taxes) is now receiving the new definition (with taxes) in production, causing severe Training-Serving Skew. Features must be immutably versioned (e.g., `total_revenue_v2`) so existing models continue to pull the `v1` pipeline until they are explicitly retrained.", ["Prevents silently changing feature definitions under live models", "Avoids catastrophic Training-Serving Skew", "Allows models to remain tied to immutable feature logic (v1 vs v2)"], ["Versioning prevents hackers from stealing features"]),
    ("B1", "scenario", "medium", "scenario", ["MLOps"], "You use Python `pickle` to serialize a scikit-learn model and load it in a production server. Why is this considered an architectural security and maintenance risk?", "Python `pickle` is fundamentally insecure; unpickling arbitrary data allows Remote Code Execution (RCE) vulnerabilities. Furthermore, `pickle` tightly couples the model to the exact Python version, library version (e.g., scikit-learn 0.24 vs 1.0), and directory structure used during training. Upgrading the server's Python environment can easily break the unpickling process. Formats like ONNX or strict JSON definitions are vastly superior for secure, interoperable production serving.", ["Insecure: allows Remote Code Execution (RCE) on load", "Tightly coupled to specific Python and library versions", "Upgrades easily break unpickling; ONNX is superior"], ["Pickle compresses the model too much causing accuracy loss"]),

    # Bucket 2: ML SYSTEM DESIGN & DEPLOYMENT
    ("B2", "compare", "medium", "compare", ["MLOps"], "Compare a 'Shadow Deployment' to a 'Canary Deployment' for a high-risk ML model.", "In a Shadow Deployment, the new model is deployed alongside the old model. It receives a copy of live traffic, makes predictions, and logs them, but those predictions are NEVER returned to the user. It is purely for safe, zero-risk validation. In a Canary Deployment, the new model actually serves a small percentage of real live traffic (e.g., 5%), actively impacting users. If it performs well, the traffic is gradually ramped up to 100%.", ["Shadow: Receives traffic, logs predictions, but DOES NOT impact users (zero risk)", "Canary: Serves a small % of real traffic, ACTIVELY impacts users", "Canary ramps up slowly if metrics are stable"], ["Shadow uses dark mode UI, Canary uses bright UI"]),
    ("B2", "tradeoff", "easy", "tradeoff", ["ML System Design"], "What is the primary tradeoff between Batch Inference (e.g., nightly Spark jobs) and Real-Time Inference (e.g., REST API)?", "Batch Inference is incredibly cheap and highly efficient for scoring massive datasets (high throughput), but the predictions are heavily lagged (e.g., 24 hours stale). Real-Time Inference provides instant, low-latency predictions based on the user's immediate context (e.g., an ad click), but it requires highly available infrastructure (APIs, Load Balancers, Online Feature Stores) that is significantly more expensive and complex to maintain.", ["Batch: High throughput, cheap, but predictions are heavily lagged/stale", "Real-Time: Low latency, uses immediate context, but expensive and complex", "Tradeoff between infrastructure cost/complexity and prediction freshness"], ["Batch inference uses CPUs, Real-Time uses GPUs"]),
    ("B2", "architecture", "hard", "architecture", ["ML System Design"], "A real-time recommender model API takes 250ms to execute, but the front-end SLA requires a response in 50ms. How do you architect the system to decouple the heavy ML execution from the strict UI latency?", "You cannot run the model synchronously in the API request. You must decouple it. Option 1: Pre-compute the recommendations via Batch Inference overnight, store them in Redis, and have the API do a 5ms lookup. Option 2: Use an asynchronous message queue (e.g., Kafka). The API immediately returns a fallback or cached generic recommendation (or an empty placeholder) in 50ms, while the heavy model calculates the personalized result in the background for the *next* page load.", ["Cannot run heavy models synchronously within strict SLAs", "Option 1: Pre-compute via Batch Inference and lookup in Redis", "Option 2: Async queues with fallback/generic recommendations returned instantly"], ["Just write the API in C++ instead of Python"]),
    ("B2", "scenario", "medium", "scenario", ["MLOps"], "Your inference API relies on an external pricing service that occasionally times out. If the pricing service fails, the ML model crashes, returning a 500 error to the user. What architectural pattern must you implement?", "You must implement a 'Fallback' or 'Heuristic' strategy. If the pricing service times out, or the model throws an internal exception, the inference code should catch the error and immediately return a safe, pre-calculated baseline heuristic (e.g., the global average price, or a static business rule) rather than crashing the user experience. The system must degrade gracefully.", ["Implement a Fallback or Heuristic strategy", "Return a safe, pre-calculated baseline (e.g., global average) on failure", "Ensures graceful degradation instead of crashing the UI"], ["Delete the pricing service"]),
    ("B2", "diagnose", "medium", "debugging", ["ML System Design"], "A collaborative filtering recommendation system works perfectly for existing users. However, when a brand new user registers, the system completely breaks and recommends irrelevant junk. What is this problem, and how is it architecturally solved?", "This is the 'Cold Start Problem'. Collaborative filtering relies on historical user behavior (clicks, purchases). A brand new user has zero history, so the model has no vector to match against. Architecturally, you solve this by routing new users to a 'Content-Based' model (using their demographics or onboarding survey), or by serving a 'Popularity Baseline' (trending items) until they generate enough clicks to activate the collaborative filtering model.", ["Cold Start Problem", "New users have no behavioral history for collaborative filtering", "Solve by routing to Content-Based models or Popularity Baselines"], ["The model was trained on the wrong timezone"]),
    ("B2", "explain", "easy", "concept", ["MLOps"], "What is the primary role of a 'Model Registry' (e.g., MLflow, Weights & Biases) in a production ML lifecycle?", "A Model Registry acts as the central source of truth for model lifecycle management. It stores the serialized model artifacts, tracks the exact code/data versions used to train them (lineage), and manages their deployment state (e.g., Staging, Production, Archived). This allows teams to easily audit models, rapidly rollback to previous versions if a deployment fails, and ensure reproducibility.", ["Central source of truth for model lifecycle management", "Stores artifacts and tracks lineage (code/data versions)", "Manages deployment states (Staging/Production) and enables rapid rollback"], ["It stores the credit card numbers of users"]),
    ("B2", "tradeoff", "hard", "tradeoff", ["ML System Design"], "What is the tradeoff of using a Multi-Armed Bandit (MAB) for model selection in production instead of a traditional A/B test?", "A traditional A/B test splits traffic evenly (50/50), forcing 50% of users to experience the losing model for the entire duration of the test, but it provides rigorous statistical certainty. A Multi-Armed Bandit dynamically shifts traffic toward the winning model in real-time (Exploitation), minimizing the business cost of the losing model. However, MABs are much harder to engineer, can get stuck in local optima, and make it difficult to calculate pure statistical significance.", ["A/B Test: Static 50/50 split, rigorous stats, but high business cost for the loser", "MAB: Dynamically shifts traffic to the winner, minimizing business cost", "MAB is complex to engineer and complicates statistical analysis"], ["MABs require 10 different models to work"]),
    ("B2", "architecture", "medium", "architecture", ["ML System Design"], "Your ML model performs excellently during the week but performs terribly on weekends because user behavior changes drastically. How do you architect the serving layer to handle this?", "You can implement an 'Ensemble' or 'Conditional Routing' architecture. You train two separate models (a Weekday model and a Weekend model). In the serving layer, a simple routing function checks the current timestamp and routes the request to the appropriate model. Alternatively, you can explicitly add `is_weekend` as a heavily weighted feature to a single, high-capacity model, but explicit routing is often safer and easier to debug.", ["Implement Conditional Routing or an Ensemble", "Train separate models for different behavioral regimes", "Route requests dynamically based on the timestamp"], ["Shut down the server on weekends"]),
    ("B2", "architecture", "medium", "architecture", ["ML System Design"], "You have 50 different PyTorch models for various micro-tasks. Deploying 50 separate Docker containers wastes massive amounts of GPU memory and costs too much. How do you solve this?", "You must implement a Multi-Model Serving architecture (e.g., NVIDIA Triton Inference Server, TorchServe, or Ray Serve). These servers can load multiple models into a single GPU's memory simultaneously. They dynamically manage the VRAM, batch incoming requests across different models, and maximize GPU utilization, drastically reducing infrastructure costs compared to isolated containers.", ["Multi-Model Serving architecture (e.g., Triton, Ray Serve)", "Loads multiple models into a single GPU's memory", "Shares VRAM and batches requests to maximize utilization"], ["Zip the models into a single file"]),
    ("B2", "diagnose", "medium", "debugging", ["MLOps"], "A real-time inference API normally responds in 20ms. Suddenly, latency spikes to 5000ms. CPU usage is low, GPU usage is low, but network connections are maxed out. What architectural bottleneck did you hit?", "You hit an I/O bottleneck in the Feature Store lookup, not a model execution bottleneck. The ML model is waiting for external data (e.g., a Redis or database query) before it can run the forward pass. If the network is saturated, or the database is locked, the inference API threads block while waiting for the network response. You must optimize the feature retrieval latency, implement caching, or increase connection pools.", ["I/O bottleneck in the Feature Store lookup", "Model is blocked waiting for external data over the network", "Optimize feature retrieval, add caching, or fix database locks"], ["The model weights became too heavy"]),

    # Bucket 3: ONLINE LEARNING & CONTINUOUS TRAINING
    ("B3", "scenario", "hard", "scenario", ["Online Learning"], "You implement an Online Learning model that updates its weights continuously based on a live stream of user clicks. After a week, the model completely forgets how to handle rare edge cases it learned during initial offline training. What is this, and how do you mitigate it?", "This is 'Catastrophic Forgetting'. As the model updates on the continuous stream of recent, common data, its weights drastically shift, destroying the representations of older, rare data. To mitigate this, you must implement 'Replay Buffers' (mixing historical data in with the live stream during updates), apply weight regularization (e.g., Elastic Weight Consolidation to penalize large changes to important weights), or use a much smaller learning rate for online updates.", ["Catastrophic Forgetting", "Recent data overwrites representations of older/rare data", "Mitigate using Replay Buffers (mixing old data with live data)"], ["The model ran out of RAM"]),
    ("B3", "diagnose", "medium", "debugging", ["Online Learning"], "A news recommendation model is updated daily using user clicks. Over time, the model only recommends political articles, completely ignoring sports and technology. What bias caused this collapse?", "This is 'Feedback Loop Bias' (or the Echo Chamber effect). The model only receives labels (clicks) on the articles it chose to show the user. If it randomly favored politics on Day 1, it received clicks on politics, reinforcing politics on Day 2, and eventually starved all other categories of exposure (and thus, labels). It collapsed into a self-fulfilling prophecy.", ["Feedback Loop Bias / Echo Chamber effect", "Model only receives labels on items it chooses to expose", "Self-fulfilling prophecy that starves other categories of data"], ["The users genuinely hate sports now"]),
    ("B3", "architecture", "medium", "architecture", ["Online Learning"], "How do you architect an Epsilon-Greedy strategy to break the Feedback Loop Bias in a continuous learning recommender system?", "Epsilon-Greedy introduces deliberate exploration. For a small percentage of traffic (Epsilon, e.g., 5%), the system completely ignores the ML model's prediction and serves a totally random recommendation to the user. This guarantees that all categories of items (even those the model dislikes) receive exposure and generate unbiased ground-truth labels. The model is then continuously trained on this exploration data to discover new trends.", ["Introduces deliberate exploration (e.g., 5% random recommendations)", "Guarantees all items receive exposure to generate unbiased ground-truth labels", "Breaks the self-fulfilling feedback loop"], ["It forces the model to be greedy and maximize revenue"]),
    ("B3", "tradeoff", "medium", "tradeoff", ["Continuous Training"], "When designing a Continuous Training pipeline, what is the tradeoff of triggering a retrain via a 'Drift Threshold' versus a static 'Time-Based Schedule' (e.g., weekly)?", "A Time-Based schedule is extremely predictable, easy to engineer, and guarantees the model incorporates recent data, but it wastes expensive compute retraining models that haven't actually degraded. A Drift-Based trigger is highly efficient (only spending compute when the data distribution actually changes), but is much harder to engineer, highly susceptible to false alarms (e.g., holiday spikes), and requires robust, real-time statistical monitoring infrastructure.", ["Time-Based: Predictable and easy, but wastes compute on unnecessary retrains", "Drift-Based: Efficient compute usage, but complex and prone to false alarms", "Drift requires robust statistical monitoring infrastructure"], ["Time-based is faster to execute"]),
    ("B3", "scenario", "hard", "scenario", ["Online Learning"], "Your online learning pricing model is continuously updated in real-time. A malicious competitor deploys bots that purchase items at ridiculously high prices to poison your data stream. How do you protect the model from instantly adapting to this adversarial attack?", "You must implement strict anomaly detection and clipping on the incoming data stream *before* it reaches the model update step. Furthermore, you should not update the model on single events. Implement Micro-Batching (e.g., accumulating 1000 events) and check the gradients or metric variance of the batch. If the batch metrics exceed a safe threshold, the pipeline automatically halts the update and triggers an alert.", ["Implement anomaly detection and clipping on the live data stream", "Use Micro-Batching instead of single-event updates", "Monitor gradient/metric variance and halt updates if unsafe"], ["Turn off the competitor's internet"]),
    ("B3", "optimize", "medium", "optimize", ["Deep Learning Engineering"], "You want to update a massive user-embedding space in real-time as users click new items. Recomputing the entire Matrix Factorization or Deep Learning embedding space takes 24 hours. How do you optimize this for real-time?", "You use Incremental Updates or 'Folding In'. Instead of recomputing the entire global embedding space, you freeze the item embeddings and only apply a fast, localized gradient descent step (or a simple moving average) to update the specific user's embedding vector based on their recent clicks. This provides a real-time approximate update, while the massive global retraining runs offline nightly.", ["Use Incremental Updates / 'Folding In'", "Freeze item embeddings and apply fast, localized updates to the user vector", "Approximates real-time updates while full retraining runs overnight"], ["Buy a supercomputer"]),
    ("B3", "architecture", "medium", "architecture", ["MLOps"], "A fully automated Continuous Training (CT) pipeline detects drift, extracts data, trains a new model, and pushes it to production. At 3 AM, the new model predicts '0' for everything and destroys revenue. What critical stage was missing from the pipeline?", "The pipeline is missing an Automated Model Validation and Shadow/Canary gate. A newly trained model must never be blindly deployed. The pipeline must first evaluate the model against a static, highly curated 'Golden Holdout Dataset' to verify minimum accuracy constraints. If it passes, it must be deployed as a Canary (1% traffic) with automated rollback triggers if the live business metrics plummet.", ["Automated Model Validation against a Golden Holdout Dataset", "Shadow or Canary deployment gate (e.g., 1% traffic)", "Automated rollback triggers based on live business metrics"], ["The pipeline forgot to compile the code"]),
    ("B3", "scenario", "hard", "scenario", ["Model Monitoring"], "You have a classification model identifying spam emails. You continuously retrain it every week. Over three months, the model's self-reported accuracy on its weekly test sets remains at 99%, but user complaints about spam double. What is happening?", "This is Concept Drift combined with an outdated ground-truth process. Spammers have changed their tactics (Concept Drift). The model's weekly test set is generated by the model's own confident predictions or an outdated heuristic, meaning it is testing itself on old, easy examples it already knows. The new, subtle spam bypassing the system isn't being labeled and added to the test set. You must introduce random sampling and human-in-the-loop manual labeling to capture the new drift.", ["Concept Drift combined with outdated ground-truth labeling", "Test set is biased toward old, easy examples the model already knows", "Requires random sampling and manual human labeling of edge cases"], ["The model weights decayed physically"]),
    ("B3", "tradeoff", "easy", "tradeoff", ["Online Learning"], "In reinforcement learning or continuous recommender systems, what is the fundamental tradeoff known as 'Exploration vs. Exploitation'?", "Exploitation means the model uses its current knowledge to recommend the absolute best item to maximize immediate reward (clicks/revenue). Exploration means the model deliberately chooses a sub-optimal or unknown item to gather new data and learn about changing user preferences. Too much exploitation creates a narrow echo chamber; too much exploration annoys the user with irrelevant items. The system must balance the two to maximize long-term reward.", ["Exploitation: Maximizing immediate reward using current knowledge", "Exploration: Gathering new data on unknown items", "Too much exploitation = echo chamber; Too much exploration = poor user experience"], ["Exploration explores the hard drive, Exploitation uses CPU"]),
    ("B3", "explain", "medium", "concept", ["Online Learning"], "What is 'Label Delay' (or Delayed Feedback) in online learning, and why does it make updating conversion models exceptionally difficult?", "Label Delay occurs when the ground truth for a prediction takes a long, variable amount of time to arrive. For example, if a model predicts whether an ad click will lead to a purchase, the purchase might happen 1 hour, 2 days, or 14 days later. If you update the model quickly, you falsely penalize it with negative labels for users who just haven't purchased *yet*. If you wait 14 days to be sure, the model is reacting to 2-week-old data, breaking the real-time nature of online learning.", ["Ground truth arrives after a long, variable delay (e.g., 14-day purchase window)", "Fast updates falsely penalize the model with premature negative labels", "Delayed updates make the model hopelessly stale"], ["The labels are written in a foreign language"]),

    # Bucket 4: DRIFT MONITORING & FAILURE DIAGNOSIS
    ("B4", "diagnose", "hard", "debugging", ["Model Monitoring"], "You use Population Stability Index (PSI) to monitor data drift on categorical features. A feature representing `city_id` (10,000 unique values) triggers a massive PSI alert. However, upon inspection, the data seems completely normal. What is the mathematical flaw?", "PSI requires binning the data. For high-cardinality categorical features (like `city_id`), many bins (cities) will have zero or near-zero counts in either the baseline or the current window. Because the PSI formula uses a logarithm (`ln(Expected / Actual)`), dividing by near-zero or taking the log of near-zero causes the metric to explode mathematically, throwing massive false positive alerts. You must group long-tail categories into an 'Other' bin before calculating PSI.", ["PSI uses logarithms and division (`ln(Expected / Actual)`)", "High cardinality means many bins have near-zero counts", "Near-zeros cause the math to explode, triggering false alarms"], ["PSI only works on images"]),
    ("B4", "compare", "medium", "compare", ["Drift"], "Explain the difference between 'Covariate Shift' and 'Concept Drift'.", "Covariate Shift (Data Drift) means the distribution of the input features has changed (e.g., you trained on young users, but now older users are joining), but the underlying relationship between the features and the target remains exactly the same. Concept Drift means the fundamental mapping between the input and the target has changed (e.g., what was considered a 'fraudulent pattern' last year is now considered normal behavior today).", ["Covariate Shift: Input feature distribution changes, but underlying relationship is stable", "Concept Drift: The fundamental mapping/relationship between features and target changes", "Concept drift requires retraining with new ground truth"], ["They are literally the exact same thing"]),
    ("B4", "scenario", "medium", "scenario", ["Drift"], "A model predicts housing prices. A pandemic hits, and people suddenly flee cities for the suburbs. The model's accuracy plummets. Do you need to rewrite the model's feature engineering, or just retrain it on recent data?", "This is a classic Concept Drift (the relationship between location and price fundamentally changed overnight). You do not necessarily need to rewrite the feature engineering; the model architecture is fine. You must retrain the model aggressively on recent post-pandemic data (discarding or down-weighting the pre-pandemic data) so the model can learn the new mapping rules.", ["Concept Drift occurred (relationship changed)", "Do not need to rewrite feature engineering", "Retrain aggressively on recent data, discarding/down-weighting old data"], ["The database must be restarted"]),
    ("B4", "diagnose", "medium", "debugging", ["Failure Diagnosis"], "Your team deployed a new Random Forest model. Offline tests showed an AUC of 0.85. In production, the AUC is exactly 0.50 (random guessing). You verify that there is no data drift and the feature pipeline is perfect. What trivial mistake causes this?", "The model was trained on data where the target labels were sorted (e.g., all 0s followed by all 1s), or the production inference API is applying a standard scaler that was fit on a different dataset. But most commonly, if features and drift are perfect, it is an Artifact Mismatch: the deployment pipeline packaged a completely untrained, randomly initialized version of the model, or loaded the wrong weights file.", ["Artifact Mismatch", "Deployment pipeline packaged an untrained, randomly initialized model", "Or loaded the wrong weights file despite identical code"], ["Random Forests don't work in production"]),
    ("B4", "scenario", "hard", "scenario", ["Failure Diagnosis"], "You train a gradient boosting model. During training, it achieves an unbelievable ROC-AUC of 0.999. In production, it completely fails. You investigate the features and find a column named `transaction_id`. How did this cause the failure?", "This is Data Leakage (Target Leakage). The `transaction_id` was likely generated sequentially *after* a fraud review, meaning legitimate IDs start with 'A' and fraud IDs start with 'F'. The model essentially memorized the ID string to perfectly 'predict' the target. In production, new transactions receive random IDs or IDs that don't follow the leaked pattern, causing the model to collapse because it learned a leaked proxy instead of genuine patterns.", ["Data Leakage / Target Leakage", "Model learned a proxy variable generated AFTER the target was decided", "Fails in production because the proxy doesn't exist or pattern breaks"], ["Transaction IDs are integers, not floats"]),
    ("B4", "architecture", "medium", "architecture", ["Model Monitoring"], "You want to monitor the performance of a credit default model, but it takes 90 days to know if a user defaulted (delayed ground truth). How do you monitor the model's health in real-time?", "Because you cannot calculate true Accuracy or AUC in real-time, you must monitor 'Proxy Metrics' and 'Prediction Distributions'. First, monitor the statistical distribution of the model's output probabilities (e.g., is it suddenly predicting 80% default rate when it used to predict 5%?). Second, monitor upstream data drift (PSI) on the input features. Third, monitor short-term proxy business metrics (e.g., missed 1st-week payments).", ["Cannot monitor Accuracy/AUC due to 90-day delay", "Monitor the statistical distribution of the model's output probabilities", "Monitor input feature drift and short-term proxy business metrics"], ["Call the users and ask them if they will default"]),
    ("B4", "diagnose", "medium", "debugging", ["Failure Diagnosis"], "Your ML inference server (written in Python/PyTorch) crashes with Out Of Memory (OOM) errors every 3 days. Traffic is completely stable. What is the likely cause?", "This is a Memory Leak caused by uncollected Tensor objects. If the API logs the model's predictions by appending the PyTorch tensor directly to a global list or logging framework (e.g., `history.append(output_tensor)`), PyTorch keeps the entire computational graph attached to that tensor in memory. You must call `.item()`, `.detach()`, or convert the tensor to a standard Python float/numpy array before logging or storing it.", ["Memory Leak caused by uncollected Tensor objects", "Storing raw tensors keeps the entire computational graph in memory", "Must use .item(), .detach(), or convert to numpy before logging"], ["The server RAM physically degraded"]),
    ("B4", "scenario", "easy", "scenario", ["Drift"], "A marketing campaign floods your website with traffic from a new country. Your model's accuracy drops. What type of drift is this, and how can you quickly verify it?", "This is Covariate Shift (Data Drift). The distribution of the input features (e.g., `country_code`, `device_type`) has fundamentally shifted from the training set. You can quickly verify this by calculating distribution metrics like the Population Stability Index (PSI) or the Kolmogorov-Smirnov (KS) test on the input features between the training dataset and the live production data stream.", ["Covariate Shift / Data Drift", "Input feature distribution fundamentally changed", "Verify using PSI or KS tests on the input features"], ["It is a DDOS attack"]),
    ("B4", "diagnose", "hard", "debugging", ["Failure Diagnosis"], "A model predicts ETA for food delivery. The offline Mean Absolute Error (MAE) is 3 minutes. In production, the MAE is 15 minutes. The features match perfectly. You discover the production system evaluates MAE using the timestamp the user *clicked order*, while the training system used the timestamp the restaurant *accepted the order*. What is this?", "This is an Evaluation Definition Mismatch (or Label Definition Skew). The model is mathematically sound, and the features are correct, but the business definition of the target variable (the 'Label') in production differs drastically from how it was defined in the historical training data. The model is predicting a completely different event timeline than what the production metric is grading it against.", ["Evaluation Definition Mismatch / Label Definition Skew", "Target variable definition in training differs from production metric", "Predicting a different event timeline"], ["The delivery drivers are slow"]),
    ("B4", "optimize", "medium", "optimize", ["MLOps"], "You are using Data Version Control (DVC) to track your datasets. Why is it an anti-pattern to commit the actual 50GB CSV file directly into Git alongside the DVC metadata?", "Git is designed for tracking small text files (code), not massive binary or data files. Committing a 50GB CSV will instantly bloat the Git repository, making it impossible to clone or push, and crashing the version control system. DVC solves this by storing a tiny metadata pointer file (`.dvc`) in Git, while securely storing the actual 50GB file in remote cloud storage (S3/GCS).", ["Git is for code; massive data files crash/bloat the repository", "DVC stores a tiny metadata pointer in Git", "The actual massive data file is stored in S3/GCS"], ["Git compresses the CSV perfectly"]),

    # Bucket 5: DEEP LEARNING ENGINEERING & PERFORMANCE
    ("B5", "compare", "hard", "compare", ["Deep Learning Engineering"], "When training a massive deep learning model across 8 GPUs, explain the exact architectural difference between 'Distributed Data Parallel' (DDP) and 'Tensor Parallelism' (Model Parallelism).", "In Distributed Data Parallel (DDP), a complete, exact copy of the entire model is loaded into the memory of EVERY GPU. The dataset is split, each GPU processes a different batch, and gradients are averaged across GPUs. In Tensor Parallelism, the model is too large to fit in a single GPU. The layers (or tensors) themselves are sliced mathematically across the 8 GPUs. Each GPU computes a fraction of the matrix multiplication, requiring massive inter-GPU communication bandwidth.", ["DDP: Complete model on every GPU, dataset is split", "Tensor Parallelism: Model is sliced mathematically across GPUs because it's too large for one", "DDP synchronizes gradients; Tensor synchronizes matrix math"], ["DDP uses CPU, Tensor uses GPU"]),
    ("B5", "diagnose", "medium", "debugging", ["Deep Learning Engineering"], "You are training a PyTorch model on a high-end A100 GPU. The GPU utilization graph shows it hovering at 20%, spiking to 100% briefly, then dropping to 20%. CPU usage is at 100%. What is the bottleneck, and how do you fix it?", "This is a Data Loading Bottleneck (CPU starvation). The blazing-fast GPU processes the batch in milliseconds, then sits idle (20%) waiting for the CPU to read the next images from the hard drive, decode JPEGs, and apply augmentations. You fix this by increasing the `num_workers` in the PyTorch DataLoader, using a faster drive (NVMe), or moving data augmentations onto the GPU.", ["Data Loading Bottleneck / CPU Starvation", "GPU sits idle waiting for CPU to read/augment data", "Fix by increasing num_workers in DataLoader or optimizing I/O"], ["The GPU is broken"]),
    ("B5", "tradeoff", "medium", "tradeoff", ["Deep Learning Engineering"], "What is the tradeoff of using Mixed Precision Training (e.g., AMP with FP16) instead of standard FP32?", "Mixed Precision Training uses 16-bit floats (FP16) for matrix multiplications, drastically reducing GPU memory usage by 50% and doubling mathematical throughput (via Tensor Cores). The tradeoff is the risk of 'Gradient Underflow'—tiny gradients become mathematically indistinguishable from zero in 16-bit space, destroying training. This forces the use of a 'GradScaler' (Loss Scaling) to artificially multiply gradients before backward passes to keep them visible.", ["Halves GPU memory and doubles throughput (Tensor Cores)", "Risk of Gradient Underflow (tiny numbers become 0 in FP16)", "Requires a GradScaler (Loss Scaling) to prevent training collapse"], ["FP16 makes the model highly inaccurate"]),
    ("B5", "architecture", "hard", "architecture", ["Deep Learning Engineering"], "You are training an object detection model to find rare manufacturing defects (1 defect per 10,000 normal parts). Using standard Cross-Entropy loss, the model instantly predicts 'normal' for everything and gets stuck in a local minimum. What architectural loss function solves this specific deep learning failure?", "You must replace Cross-Entropy with 'Focal Loss'. Standard Cross-Entropy gives equal weight to all examples; the 10,000 easy, normal examples overwhelm the loss gradient, effectively erasing the rare defect signal. Focal Loss mathematically down-weights the loss contributed by easy, well-classified examples (using a modulating factor `(1 - pt)^gamma`). This forces the optimizer to focus its gradient updates almost exclusively on the hard, rare examples.", ["Replace Cross-Entropy with Focal Loss", "Cross-Entropy is overwhelmed by the massive class imbalance", "Focal Loss mathematically down-weights the loss of easy/well-classified examples"], ["Just duplicate the defect images 10,000 times"]),
    ("B5", "diagnose", "medium", "debugging", ["Deep Learning Engineering"], "You are training an LSTM on long time-series data. The loss drops steadily, but suddenly becomes `NaN` (Not a Number) mid-epoch. What mathematical failure occurred, and what is the standard engineering fix?", "This is the 'Exploding Gradient' problem, highly common in recurrent networks processing long sequences. Gradients are repeatedly multiplied across time steps; if values are > 1, they explode to infinity, causing weights to become `NaN`. The standard engineering fix is 'Gradient Clipping' (e.g., `torch.nn.utils.clip_grad_norm_`), which forcefully caps the magnitude of the gradient vector before the optimizer steps.", ["Exploding Gradient problem", "Repeated multiplication across time steps causes gradients to reach infinity/NaN", "Fix using Gradient Clipping before the optimizer step"], ["The data contained letters instead of numbers"]),
    ("B5", "optimize", "medium", "optimize", ["ML System Design"], "You deploy an NLP model using a standard REST API. It handles 5 requests per second perfectly. At 100 requests per second, latency skyrockets because the GPU handles requests one by one. How do you optimize the inference server?", "You must implement 'Dynamic Batching' (or Adaptive Batching) at the serving layer (e.g., using Triton Inference Server or Ray Serve). The server pauses the first incoming request for a few milliseconds (e.g., 5ms window) to accumulate other incoming requests. It groups them into a single batch (e.g., batch size 8), sends the batch to the GPU for massive parallel processing, and disperses the results back to the individual HTTP responses.", ["Implement Dynamic Batching / Adaptive Batching", "Pause incoming requests briefly to group them into a batch", "Maximizes GPU parallel throughput with minimal latency penalty"], ["Use a load balancer to send requests to multiple CPUs"]),
    ("B5", "explain", "hard", "concept", ["Deep Learning Engineering"], "During the forward pass of a deep neural network, the GPU memory is completely fine. During the backward pass (backpropagation), it suddenly throws an OOM error. What specific memory structure consumed the VRAM?", "The OOM is caused by the 'Activation Memory'. During the forward pass, PyTorch/TensorFlow must save all the intermediate activation tensors (the outputs of every single hidden layer). These saved activations are mathematically required later to calculate the chain rule derivatives during the backward pass. The activations consume vastly more memory than the model weights themselves. (Can be mitigated via Gradient Checkpointing).", ["Activation Memory (intermediate layer outputs)", "Saved during the forward pass to calculate gradients in the backward pass", "Consumes vastly more memory than the model weights"], ["The optimizer deleted the model"]),
    ("B5", "tradeoff", "medium", "tradeoff", ["Deep Learning Engineering"], "What is the tradeoff of using Post-Training Quantization (PTQ) to INT8 versus Quantization-Aware Training (QAT)?", "PTQ simply converts an already-trained FP32 model into INT8. It requires zero compute and is instant, but often results in a severe drop in model accuracy because the weights weren't optimized for the lower precision. QAT fakes the quantization noise *during* the training process itself. It requires expensive compute and time to train, but allows the neural network to adapt its weights to the quantization constraints, resulting in drastically higher accuracy upon deployment.", ["PTQ: Instant, zero compute, but suffers severe accuracy drop", "QAT: Simulates quantization during training", "QAT requires expensive compute but yields drastically higher accuracy"], ["INT8 models are strictly better in every way"]),
    ("B5", "scenario", "medium", "scenario", ["MLOps"], "You are tasked with ensuring a PyTorch training script is 100% reproducible for regulatory compliance. You fix the random seed via `torch.manual_seed(42)`. You run the script twice on the same GPU, but the final weights are slightly different. What hardware optimization is breaking reproducibility?", "By default, NVIDIA CuDNN uses non-deterministic, highly optimized heuristic algorithms for certain operations (like convolutions or atomic additions in parallel threads) to maximize speed. Even with fixed random seeds, the order of floating-point operations varies, altering the lowest decimal places. To achieve strict reproducibility, you must explicitly force CuDNN into deterministic mode (`torch.backends.cudnn.deterministic = True`), trading away maximum speed.", ["CuDNN uses non-deterministic algorithms to maximize speed", "Floating-point operations execute in varying orders", "Must explicitly force torch.backends.cudnn.deterministic = True"], ["Cosmic rays mutated the RAM"]),
    ("B5", "architecture", "easy", "architecture", ["Deep Learning Engineering"], "When training a model across 100 spot-instance VMs for two weeks, what architectural mechanism is strictly required to prevent a total loss of progress if a VM crashes?", "You must implement frequent 'Checkpointing'. After every N epochs (or hours), the training loop must save the exact state of the Model Weights, the Optimizer State (moments/learning rates), and the current Epoch/Step number to durable remote storage (like S3). If a spot instance is preempted, the new VM simply loads the latest checkpoint and resumes training exactly where it left off, rather than restarting from zero.", ["Checkpointing to durable remote storage (S3)", "Must save Model Weights, Optimizer State, and Epoch/Step number", "Allows resuming training after preemption/crashes"], ["Print the loss to a text file"])
]

BUCKET_KEYS = {
    "B1": ("Feature Engineering", "Feature Stores", "MLOps", ["ML Engineer", "Data Scientist"]),
    "B2": ("ML System Design", "Model Deployment", "MLOps", ["ML Engineer", "Backend Developer"]),
    "B3": ("Continuous Training", "Online Learning", "Machine Learning", ["ML Engineer", "Data Scientist"]),
    "B4": ("Model Monitoring", "Failure Diagnosis", "Machine Learning", ["ML Engineer", "Data Scientist"]),
    "B5": ("Deep Learning Engineering", "Performance Optimization", "Deep Learning", ["ML Engineer"])
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
            "category": "Machine Learning",
            "intent": intent,
            "difficulty": diff,
            "question_type": qt,
            "question": q,
            "expected_answer": a,
            "evaluation_rubric": {"strong_indicators": strong, "weak_indicators": weak}
        })

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
        c["generation_batch"] = "batch_48_ml_engineer"

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
        "batch": "batch_48_ml_engineer",
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
    
    with open(os.path.join(REPORTS_DIR, "phase4d_batch48_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_batch48_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Phase 4D - Batch 48 (ML Engineer)\n\n")
        f.write(f"- **Attempted**: {len(cands)}\n")
        f.write(f"- **Accepted**: {len(accepted)}\n")
        f.write(f"- **Rejected**: {sum(rej.values())}\n")
        f.write(f"- **Rejections**: {dict(rej)}\n\n")
        f.write("### Staging Totals\n")
        f.write(f"- **Previous Staging Total**: {len(prior)}\n")
        f.write(f"- **Final Staging Total**: {final_staging_total}\n")
        f.write(f"- **ML Engineer Role Total**: {role_counts[ROLE]}\n")
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

    print(f"Successfully generated 50 ML Engineer questions.")

if __name__ == "__main__":
    main()
