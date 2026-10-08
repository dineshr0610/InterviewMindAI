"""Batch 31 Part 3 question content (ML Engineer). Targeted Gap Generation."""

ROLE = "ML Engineer"

BUCKET_KEYS = {
    "FAILURE_DIAGNOSIS": ("Failure Diagnosis", "System Debugging", "MLOps", ["ML Engineer", "Data Scientist", "Software Engineer"]),
}

Q = [
# ---------------- FAILURE_DIAGNOSIS ----------------
("FAILURE_DIAGNOSIS", "debug", "hard", "debugging", ["Label Leakage", "Feature Engineering"],
 "You deploy a demand forecasting model. During offline cross-validation, the Mean Absolute Error (MAE) was 10. In production, the online MAE is 50. The distribution of features (like 'temperature') perfectly matches offline. What specific feature engineering anti-pattern during training caused this degradation?",
 "This is 'Label Leakage' (Data Leakage) through improper feature scaling or time-series splitting. During training, the data scientist likely applied `StandardScaler.fit_transform()` on the *entire* dataset before splitting into train/test, or included a future-looking feature. The model memorized future data during offline training, rendering it useless in real-time.",
 ["'Label Leakage' or 'Data Leakage' during preprocessing", "Example: Applying `fit_transform()` on the entire dataset before the train/test split", "The model memorized future data offline, destroying its real-time predictive utility"],
 ["The model realized the future is unpredictable and gave up"]),

("FAILURE_DIAGNOSIS", "debug", "medium", "debugging", ["Hardware", "Latency"],
 "An object detection model on an edge device operates perfectly for 10 minutes, but then inference latency creeps up from 30ms to 200ms, and the system becomes unresponsive. The model weights are not changing. What hardware-level failure is occurring?",
 "This is 'Thermal Throttling'. Continuous heavy matrix multiplications generate massive heat. Because edge devices often lack active cooling, the physical GPU/NPU hits a critical temperature threshold, forcing the OS to drastically underclock the processor frequency to prevent hardware damage, causing inference latency to spike.",
 ["'Thermal Throttling' due to continuous matrix multiplications generating heat", "The physical processor hits a critical temperature threshold", "The OS drastically underclocks the processor frequency to prevent hardware damage, spiking latency"],
 ["The edge device ran out of battery and is falling asleep"]),

("FAILURE_DIAGNOSIS", "debug", "hard", "debugging", ["Preprocessing", "Data Pipelines"],
 "Your tabular model relies on `user_age`. Offline, missing ages were `NaN` and correctly handled. In production, accuracy suddenly tanks. You inspect production data: `user_age` has no `NaN` values, but many users have an age of `0` or `-999`. What happened?",
 "This is a 'Silent Fallback' or 'Preprocessing Version Mismatch' in the upstream data pipeline. An upstream data engineering team likely changed the default imputation behavior for missing values in the data warehouse (from `NULL` to `-999`) without informing the ML team. The model is now interpreting `-999` as a literal biological age, corrupting predictions.",
 ["'Silent Fallback' or 'Preprocessing Version Mismatch' in the upstream data pipeline", "Upstream engineers changed default missing value imputation (e.g., from `NULL` to `-999`)", "The model misinterprets the imputation flag (`-999`) as a literal biological age"],
 ["People are actually being born at age -999 due to a glitch in the matrix"]),

("FAILURE_DIAGNOSIS", "diagnose", "medium", "debugging", ["Overfitting"],
 "You train a gradient boosting model. Training loss decreases beautifully, but validation loss immediately starts increasing on epoch 2 and never stops. You check the data; there is no leakage. What fundamental ML failure is occurring, and how do you diagnose it?",
 "This is textbook 'Overfitting'. The model has excessive capacity and is perfectly memorizing the noise in the training data, rather than learning generalized rules. You diagnose it by plotting the learning curve (training loss vs validation loss); a widening gap where training goes down but validation goes up is the definitive mathematical signature of overfitting.",
 ["'Overfitting': The model is memorizing noise rather than learning generalized rules", "Diagnosed via the Learning Curve (training loss vs validation loss)", "The definitive signature is a widening gap: training loss decreases while validation loss increases"],
 ["The model is getting bored of the validation data"]),

("FAILURE_DIAGNOSIS", "debug", "hard", "debugging", ["PyTorch", "Memory Leaks"],
 "An NLP model is deployed to production. Memory usage is stable at 4GB. However, after 3 days, the Python inference service crashes with an Out Of Memory (OOM) error at 32GB. You verify the model itself isn't leaking memory. What inference-specific memory leak is likely occurring?",
 "The service is likely leaking 'Tensors attached to the computation graph'. In PyTorch, if you log predictions/inputs to a standard Python list for monitoring without calling `.detach()`, `.cpu()`, or `.item()`, Python retains the entire Autograd computation graph in memory for every inference request, waiting for a `.backward()` call that never happens.",
 ["Leaking 'Tensors attached to the computation graph' (Autograd history)", "Failing to call `.detach()` or `.item()` when saving tensors for logging/monitoring", "Retains the entire massive computation graph in memory for every request, causing slow OOM"],
 ["Python lists naturally absorb water from the air and swell over time"]),

("FAILURE_DIAGNOSIS", "diagnose", "medium", "debugging", ["Concept Drift", "Seasonality"],
 "A retail company deploys a model to optimize inventory. It works great for 11 months. In December, predictions become wildly inaccurate, causing stockouts. Upstream pipelines are perfectly healthy and features are arriving correctly. What failure mode is this?",
 "This is 'Concept Drift' driven by extreme Seasonality. The fundamental purchasing behavior of consumers completely changes during the holiday season. If the model was only trained on data from Jan-Nov, or lacks explicit seasonal features (like `is_holiday`), it mathematically cannot comprehend the structural shift in the underlying concept of 'demand'.",
 ["'Concept Drift' driven by extreme Seasonality", "The fundamental relationship between features and target behavior (demand) structurally shifted", "The model cannot comprehend the shift because it wasn't trained on holiday data/features"],
 ["The database froze because it is cold in December"]),

("FAILURE_DIAGNOSIS", "debug", "hard", "debugging", ["Distributed Training", "Deadlock"],
 "You deploy a distributed PyTorch training job across 4 nodes. It initializes, but then completely hangs indefinitely at Epoch 1, Step 0. GPU utilization is 0%. There are no Python stack traces or error logs. What is the most likely cause?",
 "This is a 'Distributed Deadlock' or network synchronization failure during the initial All-Reduce/Broadcast operation. It occurs when there is a mismatch in the network topology (e.g., NCCL cannot communicate across nodes due to a closed firewall port), or when one specific node fails to reach the initialization barrier while the others wait infinitely.",
 ["'Distributed Deadlock' or network synchronization failure", "Fails during the initial All-Reduce or Broadcast operation across the network", "Caused by closed firewall ports (NCCL communication failure) or one node missing the barrier"],
 ["The 4 nodes are playing a game of chicken and refusing to move first"]),

("FAILURE_DIAGNOSIS", "diagnose", "medium", "debugging", ["Evaluation", "Imbalanced Classes"],
 "A model predicts if a user will click an ad. It reports an impressive 99% accuracy offline. You deploy it, and it predicts 'No Click' for literally every single user. Business revenue drops to zero. Why did the offline accuracy metric completely fail?",
 "This is the 'Imbalanced Class' trap. The dataset was highly imbalanced (only 1% of users actually click). The model simply learned to predict the majority class ('No Click') 100% of the time, guaranteeing a 99% mathematical accuracy. The data scientist used the wrong evaluation metric (should have used Precision, Recall, F1-Score, or AUROC).",
 ["The 'Imbalanced Class' trap", "The model learned to predict the majority class 100% of the time, gaming the accuracy metric", "Accuracy is the wrong metric; must use Precision, Recall, F1-Score, or AUROC"],
 ["The model ethically objects to digital advertising"]),

("FAILURE_DIAGNOSIS", "debug", "hard", "debugging", ["Feature Store", "Point-in-Time"],
 "You train a model offline, and the feature `account_balance` has a mean of $1000. In production, the model receives `account_balance` from the central Feature Store, but its mean is consistently $0. Data engineers swear the backend is identical. What temporal failure is occurring?",
 "This is a 'Point-in-Time Correctness' (or 'Stale Feature') failure in the online serving layer. Offline training correctly used point-in-time joins to reconstruct the historical balance. However, the online feature store might only sync batch updates every 24 hours. At serving time, the API retrieves an uninitialized or stale default value from the fast key-value store.",
 ["'Point-in-Time Correctness' or 'Stale Feature' failure in the online serving layer", "Offline training used perfectly synced historical point-in-time joins", "Online serving is querying a fast key-value store whose batch update sync is delayed/stale"],
 ["The feature store was robbed by hackers"]),

("FAILURE_DIAGNOSIS", "diagnose", "medium", "debugging", ["Tree Models", "Extrapolation"],
 "A Random Forest model predicts house prices. R-squared is 0.95. You evaluate it on a test set of houses that are 20% larger than *any* house in the training set. The model's predictions for these new houses are bizarrely flat and capped at a specific maximum price. Why?",
 "This is the 'Extrapolation Failure' inherent to tree-based models. Random Forests and GBDTs cannot mathematically extrapolate continuous values beyond the boundaries of their training data. For any input feature larger than the maximum split threshold seen during training, the model simply falls into the terminal leaf node and predicts the historical average of that leaf.",
 ["'Extrapolation Failure' inherent to tree-based algorithms", "Random Forests cannot extrapolate continuous predictions beyond their training data boundaries", "Extreme inputs just fall into the terminal leaf node, capping the output at that leaf's historical average"],
 ["The Random Forest physically ran out of wood to build bigger houses"]),

("FAILURE_DIAGNOSIS", "debug", "hard", "debugging", ["Latency", "Concurrency"],
 "During a traffic spike, your real-time model's P99 latency jumps from 100ms to 5s. You check the inference servers: CPU is at 20%, Memory is at 30%, and network I/O is fine. Why is the service lagging so severely if hardware resources aren't bottlenecked?",
 "This is a 'Thread Pool Exhaustion' or 'Concurrency Bottleneck' failure, often caused by a synchronous blocking call inside the async serving loop. If the model preprocessing code makes a synchronous database query or runs an unoptimized regex, it blocks the worker thread. Under load, all threads become blocked waiting for I/O, forming a massive queue while CPU sits idle.",
 ["'Thread Pool Exhaustion' or 'Concurrency Bottleneck'", "A synchronous blocking call (like a DB query) inside the asynchronous serving loop", "All worker threads become blocked waiting for I/O, queuing requests while CPU remains idle"],
 ["The CPU is purposely working slowly to protest the traffic spike"]),

("FAILURE_DIAGNOSIS", "diagnose", "medium", "debugging", ["Covariate Shift", "Data Drift"],
 "An image classification model on a factory line identifies defective parts. It works perfectly in the morning. At 4 PM every day, accuracy drops from 98% to 60%. What environmental MLOps failure is this?",
 "This is 'Covariate Shift' (a form of Data Drift) caused by unmodeled environmental changes, specifically ambient lighting. At 4 PM, the sun sets or shifts, drastically changing the lighting, shadows, or color balance of the camera images. The model was likely only trained on well-lit morning images and fails to generalize to the shifted distribution of evening pixels.",
 ["'Covariate Shift' (a form of Data Drift)", "Unmodeled environmental changes (like ambient lighting, shadows, or sun position)", "The model was trained on one distribution (morning lighting) and fails on the shifted distribution (evening)"],
 ["The factory camera gets tired at the end of the shift"]),

("FAILURE_DIAGNOSIS", "debug", "hard", "debugging", ["Data Augmentation", "Validation"],
 "You use PyTorch to train an image model. You apply standard data augmentations: RandomCrop, ColorJitter. The validation loss is completely erratic, jumping from 0.1 to 5.0 and back on consecutive batches. You realize you accidentally applied the augmentations to the *validation* DataLoader. Why does this ruin validation?",
 "Data augmentations intentionally inject heavy stochastic noise (random cropping, color shifting) to force generalization. If accidentally applied to the validation set, you destroy the deterministic, static baseline required to evaluate the model. The erratic validation loss is just the model struggling to predict randomly injected noise on every single pass, rather than evaluating true convergence.",
 ["Destroys the deterministic, static baseline required to evaluate true model convergence", "Augmentations inject heavy stochastic noise (random shifting/cropping)", "The erratic loss is just the model reacting to random noise changing on every validation pass"],
 ["The validation data became too beautiful for the model to handle"]),

("FAILURE_DIAGNOSIS", "diagnose", "medium", "debugging", ["Autoregressive Models", "Generation"],
 "You deploy a translation model. For normal sentences, it works perfectly. But if a user inputs 'hello hello hello...', the model outputs an infinite loop of gibberish, maxes out the `max_length` parameter, and consumes massive GPU resources. What architectural vulnerability is this?",
 "This is a 'Degenerative Repetition' failure, a common vulnerability in autoregressive sequence models (Transformers/RNNs). When forced out-of-distribution by a bizarre input, the model's internal states collapse into a feedback loop, continuously predicting the same token over and over. It is mitigated by implementing `repetition_penalty` or strict early-stopping heuristics during decoding.",
 ["'Degenerative Repetition' failure in autoregressive models", "Out-of-distribution inputs cause internal states to collapse into an infinite feedback loop", "Mitigated via `repetition_penalty`, `presence_penalty`, or early-stopping during decoding"],
 ["The model just really wanted to say hello back"]),

("FAILURE_DIAGNOSIS", "debug", "hard", "debugging", ["Cold Start Problem", "Recommender Systems"],
 "A collaborative filtering recommendation model works great for existing users. When a brand-new user signs up, the model throws a KeyError or recommends absolute garbage. What is this classic failure mode, and how is it mitigated?",
 "This is the 'Cold Start Problem'. Collaborative filtering algorithms rely entirely on historical user-item interaction matrices (e.g., past clicks). A brand-new user has no history, so their latent embedding vector doesn't exist or is purely random noise. It is mitigated by implementing a fallback heuristic system (e.g., global 'Top Trending') or a content-based fallback model.",
 ["The 'Cold Start Problem' in Collaborative Filtering", "Brand-new users have no historical interaction data, so they lack a latent embedding vector", "Fix: Implement a fallback heuristic (Top Trending) or a content-based recommendation model"],
 ["The brand new user is too cool to need recommendations"]),

("FAILURE_DIAGNOSIS", "diagnose", "easy", "debugging", ["Spurious Correlation", "Shortcut Learning"],
 "You train a model to classify tumors using 10k images from Hospital A and 10k from Hospital B. It achieves 99% accuracy. During investigation, you realize all images from Hospital A have a tiny red watermark, and Hospital B does not. Why is this a catastrophic failure?",
 "This is 'Shortcut Learning' or 'Spurious Correlation'. The deep neural network completely bypassed learning complex biological tumor features and instead learned the trivial mathematical shortcut: 'If red watermark exists, predict Class A; else predict Class B'. The model is functionally useless for real-world application because it learned an artifact of the data collection process.",
 ["'Shortcut Learning' or 'Spurious Correlation'", "The network bypassed complex biological features to learn a trivial, completely unrelated visual artifact", "The model is functionally useless because it learned the data collection process, not the physics of the problem"],
 ["The red watermark is actually a known biological symptom of tumors"])
]
