"""Batch 21 question content (Machine Learning Engineer). Antigravity-native, no Gemini API."""

ROLE = "Machine Learning Engineer"

BUCKET_KEYS = {
    "ML_CORE": ("Core Algorithms", "Supervised Learning", "Machine Learning", ["Data Scientist"]),
    "ML_FEAT": ("Feature Engineering", "Data Leakage & Preprocessing", "Data Engineering", ["Data Scientist"]),
    "ML_TRAIN": ("Model Training", "Cross-Validation & Tuning", "Machine Learning", ["Data Scientist"]),
    "ML_EVAL": ("Model Evaluation", "Metrics & Calibration", "Machine Learning", ["Data Scientist", "Data Analyst"]),
    "ML_PROD": ("Production ML", "Drift & Skew", "MLOps", ["Data Scientist", "Software Engineer"]),
    "ML_OPS": ("MLOps & Pipelines", "Architecture & Serving", "MLOps", ["DevOps / Cloud Engineer", "Platform Engineer"]),
    "ML_DL": ("Deep Learning", "Optimization & Inference", "AI/ML", ["AI Engineer"]),
    "ML_DEBUG": ("Model Debugging", "Failure Analysis", "Machine Learning", ["Data Scientist"]),
}

Q = [
# ---------------- ML_CORE ----------------
("ML_CORE", "fundamentals", "easy", "concept", ["Random Forests"],
 "Explain how a Random Forest prevents the individual decision trees within it from heavily overfitting the training data.",
 "A Random Forest uses Bagging (Bootstrap Aggregating) and random feature subsets. It trains hundreds of individual trees on random subsets of the data with replacement. Furthermore, at each split in the tree, it only considers a random subset of features. This enforces diversity; while individual trees might overfit their specific subset, averaging their uncorrelated predictions cancels out the noise, preventing global overfitting.",
 ["Uses Bagging (Bootstrap Aggregating) to train on random data subsets", "Selects a random subset of features at each split", "Averaging uncorrelated, diverse trees cancels out individual overfitting"],
 ["It deletes 50% of the data before training"]),

("ML_CORE", "tradeoff", "medium", "tradeoff", ["Algorithm Selection"],
 "What are the tradeoffs between using Logistic Regression versus a Gradient Boosting Machine (like XGBoost) for a binary classification problem?",
 "Logistic Regression is highly interpretable, trains instantly, requires minimal tuning, and serves with near-zero latency, but it assumes a linear relationship and struggles with complex, non-linear patterns. XGBoost captures highly complex non-linear relationships and interactions, yielding higher accuracy, but acts as a 'black box', requires extensive hyperparameter tuning, and is computationally heavier to train and serve.",
 ["Logistic Regression: interpretable, fast to train/serve, but assumes linear relationships", "XGBoost: captures complex non-linear patterns, highly accurate", "XGBoost: black box, requires tuning, computationally heavier"],
 ["Logistic regression can only predict numbers, XGBoost predicts words"]),

("ML_CORE", "explain", "medium", "concept", ["SVM"],
 "Explain the concept of 'Margin' in a Support Vector Machine (SVM). What is the difference between a Hard Margin and a Soft Margin?",
 "The Margin is the distance between the decision boundary (hyperplane) and the closest data points (support vectors) of each class. An SVM aims to maximize this margin. A Hard Margin strictly prohibits any misclassifications, making it highly sensitive to outliers and prone to overfitting. A Soft Margin allows some points to cross the boundary (controlled by a penalty parameter 'C') to create a more robust, generalized model.",
 ["Margin: distance between the decision boundary and the closest data points", "Hard Margin: prohibits misclassifications, prone to overfitting on outliers", "Soft Margin: allows some misclassifications (controlled by 'C') for better generalization"],
 ["The margin is the profit the company makes on the model"]),

("ML_CORE", "implement", "medium", "implementation", ["Clustering"],
 "You are clustering a dataset using K-Means, but the algorithm is converging very slowly and getting stuck in poor local minima. How do you adjust the initialization to fix this?",
 "Standard K-Means initializes centroids completely randomly, which can group them too closely and cause poor convergence. I would switch the initialization method to `k-means++`. This algorithm selects the first centroid randomly, but selects subsequent centroids by maximizing the distance from already chosen centroids, ensuring a spread-out, stable initialization that converges faster to a better global minimum.",
 ["Standard initialization places centroids purely randomly, causing poor convergence", "Switch to `k-means++` initialization", "Selects subsequent centroids to be as far away as possible from existing ones"],
 ["Just run K-Means for 10 million iterations"]),

("ML_CORE", "explain", "hard", "concept", ["Regularization"],
 "Explain how L1 regularization (Lasso) inherently performs feature selection, whereas L2 regularization (Ridge) does not.",
 "Both add a penalty to the loss function based on model weights. L2 penalizes the squared magnitude of weights, shrinking them smoothly toward zero but rarely exactly to zero. L1 penalizes the absolute magnitude of weights. Because the L1 penalty is geometric (a diamond shape constraint), the gradient pushes non-essential feature weights exactly to 0.0, effectively dropping them from the model and performing automatic feature selection.",
 ["L2 (Ridge) penalizes squared weights, shrinking them toward zero but not to exactly zero", "L1 (Lasso) penalizes absolute weights", "L1 geometry forces non-essential weights to exactly 0.0, eliminating the feature"],
 ["L1 deletes rows from the database, L2 deletes columns"]),

("ML_CORE", "scenario", "medium", "scenario", ["Linear Regression"],
 "You fit a linear regression model to predict housing prices based on square footage and number of bedrooms. The model's coefficients are wildly unstable and change drastically if you remove just one row of data. What statistical issue is likely occurring?",
 "This is a classic symptom of Multicollinearity. Square footage and number of bedrooms are highly correlated with each other. When independent variables are highly correlated, the matrix inversion becomes numerically unstable, meaning the model cannot reliably isolate the individual effect of each feature. You solve this by removing one of the correlated features or using Ridge regularization.",
 ["Multicollinearity: independent variables are highly correlated", "Causes coefficient estimates to become numerically unstable and erratic", "Solve by dropping a correlated feature or using L2 (Ridge) regularization"],
 ["The housing market crashed during the training job"]),

# ---------------- ML_FEAT ----------------
("ML_FEAT", "scenario", "hard", "scenario", ["Data Leakage"],
 "You train a model to predict if a user will churn. It achieves 99% accuracy offline. In production, it predicts 100% of users will stay, performing worse than random guessing. Upon investigation, one of your features was `days_since_last_login`. Why did this cause catastrophic Data Leakage?",
 "In the historical training data, `days_since_last_login` for a churned user was likely measured on the day the data was extracted, meaning a user who churned a year ago has a value of 365. The model learned that 'high days = churn'. In live production, you are predicting churn for *active* users, whose `days_since_last_login` is always 0 or 1. The model sees 'low days' and confidently predicts they will stay.",
 ["Historical data calculated the feature after the churn event had already occurred", "Model incorrectly learned that massive inactivity (high days) equals churn", "In production, active users always have low days, so the model never predicts churn"],
 ["The days_since_last_login column was encrypted"]),

("ML_FEAT", "explain", "easy", "concept", ["Data Leakage"],
 "What is 'Target Leakage' (or Feature Leakage) in machine learning?",
 "Target Leakage occurs when the training dataset includes features that would not actually be available at the time of prediction in the real world. For example, using 'surgery_type' to predict 'will_patient_be_admitted_to_hospital'. The model will look artificially perfect in offline training, but will fail entirely in production because that data won't exist at prediction time.",
 ["Training data contains information that won't be available at prediction time", "Causes offline accuracy to look perfect", "Causes catastrophic failure in production inference"],
 ["It means hackers stole the dataset from the server"]),

("ML_FEAT", "implement", "medium", "implementation", ["Imbalanced Data"],
 "You are dealing with a highly imbalanced fraud dataset (99.9% legit, 0.1% fraud). Standard SMOTE oversampling causes the model to overfit heavily on synthetic noise. What alternative data-level or algorithm-level techniques should you use?",
 "At the algorithm level, I would use Class Weights (e.g., `class_weight='balanced'`) to heavily penalize errors on the minority class during loss calculation. Alternatively, I would use a specialized loss function like Focal Loss (which focuses training on hard-to-predict examples). At the data level, instead of oversampling, I could cautiously undersample the majority class using techniques like Tomek Links to clean the boundary.",
 ["Algorithm level: use Class Weights to penalize minority class errors", "Algorithm level: use Focal Loss to focus on hard examples", "Data level: undersample the majority class (e.g., Tomek Links)"],
 ["Just copy and paste the fraud rows 10,000 times in Excel"]),

("ML_FEAT", "debug", "medium", "debugging", ["Data Preprocessing"],
 "You apply StandardScaler to your training data and then train a model. During production inference, you apply `StandardScaler().fit_transform()` to the incoming batch of 5 predictions. The model outputs garbage. What pipeline error did you make?",
 "You used `fit_transform()` in production, meaning you recalculated the Mean and Variance based purely on the tiny incoming batch of 5 predictions. This completely destroys the scaling logic the model learned. You must use `.transform()` in production, utilizing the exact Mean and Variance saved/fitted from the historical training set.",
 ["Used `fit_transform()` instead of `.transform()` in production", "Recalculated mean/variance on the inference batch, corrupting the scale", "Must save the scaler fitted on training data and strictly use `.transform()` in production"],
 ["The standard scaler expired after 30 days"]),

("ML_FEAT", "tradeoff", "medium", "tradeoff", ["Categorical Encoding"],
 "What are the tradeoffs of using One-Hot Encoding versus Target Encoding (Mean Encoding) for a categorical feature with 1,000 unique high-cardinality values?",
 "One-Hot Encoding ensures no artificial ordering is created, but for 1,000 values, it creates 1,000 sparse new columns, exploding memory usage and causing the Curse of Dimensionality. Target Encoding replaces the category with the mean of the target variable; it keeps the feature space strictly to 1 column and captures deep predictive value, but is highly prone to target leakage and overfitting if not rigorously cross-validated.",
 ["One-Hot: safe from leakage, but explodes memory and causes Curse of Dimensionality", "Target Encoding: extremely memory efficient (1 column) and predictive", "Target Encoding: highly prone to overfitting and target leakage without smoothing/CV"],
 ["One-Hot encoding burns the CPU, Target encoding freezes it"]),

("ML_FEAT", "fundamentals", "easy", "concept", ["Data Splitting"],
 "Why is it critical to split your dataset into Train/Test BEFORE performing any imputation of missing numerical values?",
 "If you impute missing values (like using the Mean) on the entire dataset before splitting, information from the Test set 'leaks' into the Mean calculation. The training process indirectly learns from the Test set distribution, invalidating your offline evaluation and falsely inflating accuracy metrics. You must split first, fit the imputer only on Train, and transform both.",
 ["Prevents Data Leakage", "Fitting an imputer on the whole dataset leaks Test set distributions into Train", "Must fit imputer only on Train, then transform Train and Test independently"],
 ["It is a legal requirement of the GDPR privacy act"]),

("ML_FEAT", "scenario", "hard", "scenario", ["Time-Series Leakage"],
 "You are predicting daily sales for a retail store. You engineer a feature `average_sales_past_7_days`. If you calculate this using a standard Pandas `.rolling(7).mean()` on the entire dataset before splitting, what specific ML error have you introduced?",
 "You have introduced Temporal Leakage (Look-ahead bias). A standard `.rolling(7).mean()` includes the *current* row's value in the 7-day average. When predicting today's sales, you are literally feeding today's actual sales into the feature. You must strictly shift the rolling window by 1 (e.g., `rolling(7).mean().shift(1)`) so the feature only uses strictly historical data relative to the prediction row.",
 ["Temporal Leakage / Look-ahead bias", "Standard rolling means include the current target row in the average", "Fix by shifting the window so it only looks at strictly past data"],
 ["Pandas is mathematically incapable of doing averages properly"]),

# ---------------- ML_TRAIN ----------------
("ML_TRAIN", "fundamentals", "easy", "concept", ["Cross Validation"],
 "What is the primary purpose of K-Fold Cross Validation compared to a simple Train/Test split?",
 "A simple Train/Test split can be lucky or unlucky based on exactly which rows ended up in the Test set, yielding a highly variable performance metric. K-Fold Cross Validation splits the data into K parts, trains K separate models, and averages their scores. This provides a significantly more robust, stable, and statistically reliable estimate of how the model will perform on unseen data.",
 ["Simple splits are highly sensitive to the random seed (lucky/unlucky splits)", "K-Fold averages performance across K different hold-out sets", "Provides a much more robust and statistically reliable evaluation metric"],
 ["It makes the model run K times faster in production"]),

("ML_TRAIN", "explain", "medium", "concept", ["Bias-Variance Tradeoff"],
 "Explain the Bias-Variance Tradeoff. If a model is severely overfitting the training data, is it suffering from high bias or high variance?",
 "Bias is the error from simplistic assumptions (e.g., linear regression on non-linear data). Variance is the error from being overly sensitive to noise in the training data. Overfitting means the model has memorized the training noise, meaning it has Low Bias but High Variance. The tradeoff is finding the sweet spot where the model is complex enough to learn patterns (low bias) but simple enough to generalize (low variance).",
 ["Bias: error from simplistic assumptions (underfitting)", "Variance: error from hyper-sensitivity to training noise (overfitting)", "An overfitting model suffers from High Variance"],
 ["High bias means the model is racist"]),

("ML_TRAIN", "tradeoff", "medium", "tradeoff", ["Hyperparameter Tuning"],
 "What are the tradeoffs between using Grid Search versus Random Search for hyperparameter tuning?",
 "Grid Search exhaustively tests every single possible combination; it guarantees finding the absolute best combination within the grid, but scales exponentially (Curse of Dimensionality) and is incredibly slow. Random Search tests random combinations; it is mathematically proven to find near-optimal parameters much faster with far fewer iterations, but it does not guarantee finding the absolute global optimum.",
 ["Grid Search: exhaustive and guarantees finding the best combination in the grid", "Grid Search: suffers from exponential scaling (Curse of Dimensionality), very slow", "Random Search: much faster, finds near-optimal parameters, but doesn't guarantee the absolute best"],
 ["Grid search only works on GPUs, Random search only on CPUs"]),

("ML_TRAIN", "implement", "hard", "implementation", ["Time Series CV"],
 "You are training a time-series forecasting model. Why is standard K-Fold Cross Validation invalid for this dataset, and how should you partition the data for evaluation instead?",
 "Standard K-Fold randomly shuffles data, meaning you would train a model on data from December to predict sales in January of the *same year*. This is temporal leakage; you are predicting the past using the future. For time-series, you must use Forward Chaining (Time Series Split), where you train on Month 1, test on Month 2. Then train on Months 1-2, test on Month 3, strictly preserving chronological order.",
 ["Standard K-Fold randomizes data, allowing the model to predict the past using the future", "Violates the strict chronology of time-series data (Temporal Leakage)", "Use Forward Chaining (Time Series Split) to always train on the past and test on the future"],
 ["K-Fold only works on strings, not timestamps"]),

("ML_TRAIN", "scenario", "medium", "scenario", ["Overfitting"],
 "During training of an XGBoost model, the training error steadily decreases to near zero, but the validation error decreases initially and then starts to rapidly increase. What is happening, and how do you programmatically prevent it?",
 "The model has reached the point of Overfitting; it stopped generalizing and started memorizing the noise in the training set. To prevent this programmatically, you implement Early Stopping. You configure the training loop to monitor the validation metric and halt training if the validation score fails to improve for 'N' consecutive rounds, restoring the model weights from the best epoch.",
 ["The model is Overfitting (memorizing training noise)", "Validation error increases as generalization degrades", "Implement Early Stopping to halt training when validation error degrades for N rounds"],
 ["The CPU is overheating, turn on the fans"]),

("ML_TRAIN", "debug", "medium", "debugging", ["Deep Learning"],
 "You train a deep neural network, but the training loss remains completely flat from Epoch 1 to Epoch 50. What hyperparameter is most likely configured completely wrong?",
 "The Learning Rate is likely configured wrong. If it is too low (e.g., 1e-9), the weight updates are so microscopic that the loss curve is effectively flat. If it is far too high (e.g., 100), the optimizer violently bounces across the loss landscape, failing to descend, also resulting in a flat (or exploding) loss curve. You should adjust the learning rate by orders of magnitude to diagnose.",
 ["The Learning Rate is misconfigured", "Too low: updates are microscopic, preventing descent", "Too high: optimizer overshoots the minima wildly, failing to descend"],
 ["The Epochs are numbered backward"]),

# ---------------- ML_EVAL ----------------
("ML_EVAL", "fundamentals", "easy", "concept", ["Classification Metrics"],
 "For a binary classification model, what is the difference between Precision and Recall?",
 "Precision measures the accuracy of positive predictions (Out of all the emails the model *claimed* were Spam, how many were actually Spam?). Recall measures the ability to find all positive instances (Out of all the *actual* Spam emails in the dataset, how many did the model successfully find?). There is generally a mathematical tradeoff between the two.",
 ["Precision: Out of all positive predictions, how many were actually positive?", "Recall: Out of all actual positive instances, how many did the model find?", "They represent a tradeoff between false positives and false negatives"],
 ["Precision is for numbers, Recall is for images"]),

("ML_EVAL", "scenario", "medium", "scenario", ["Metric Selection"],
 "You are building a cancer detection model. Which metric is strictly more important to optimize: Precision or Recall? Why?",
 "Recall is strictly more important. High Recall minimizes False Negatives (telling a patient they are healthy when they actually have cancer, which is fatal). We accept a lower Precision (more False Positives—telling a healthy patient they might have cancer) because the consequence is just a follow-up test. In medical diagnostics, missing the disease is vastly worse than a false alarm.",
 ["Recall is more important", "Minimizes False Negatives (missing an actual cancer diagnosis is fatal)", "We gladly accept False Positives (lower Precision) as they just trigger follow-up tests"],
 ["Precision is more important because doctors love precise numbers"]),

("ML_EVAL", "explain", "hard", "concept", ["Evaluation Curves"],
 "Explain the difference between the ROC-AUC and the PR-AUC (Precision-Recall Area Under Curve). When must you explicitly choose PR-AUC over ROC-AUC?",
 "ROC-AUC plots True Positive Rate vs False Positive Rate. It can be dangerously misleading on highly imbalanced datasets (e.g., 99% negative) because a massive flood of True Negatives keeps the False Positive Rate artificially low, making a terrible model look excellent. PR-AUC plots Precision vs Recall, completely ignoring True Negatives. You MUST use PR-AUC when evaluating highly imbalanced datasets (like fraud detection).",
 ["ROC-AUC uses True Negatives, which skews results on imbalanced datasets", "PR-AUC ignores True Negatives, focusing entirely on the minority positive class", "Must use PR-AUC for highly imbalanced datasets (e.g., fraud, rare diseases)"],
 ["ROC is for text data, PR is for video data"]),

("ML_EVAL", "debug", "medium", "debugging", ["Model Calibration"],
 "Your binary classifier outputs probabilities (e.g., 0.8). You notice that out of all predictions where the model output 0.8, only 30% actually belong to the positive class. What is wrong with your model's outputs, and how do you fix it?",
 "Your model outputs are Uncalibrated; they are raw confidence scores, not true statistical probabilities. This often happens with Tree-based models or SVMs. To fix it, you must apply Calibration as a post-processing step, using techniques like Platt Scaling (Logistic Calibration) or Isotonic Regression on a hold-out validation set to map the raw scores to true probability curves.",
 ["The model is Uncalibrated (scores do not match actual statistical probabilities)", "Common in non-logistic models like Random Forests or SVMs", "Fix using Platt Scaling or Isotonic Regression on a validation set"],
 ["The model's random seed was set to 0.8"]),

("ML_EVAL", "implement", "medium", "implementation", ["Unsupervised Evaluation"],
 "How do you evaluate a clustering algorithm (like K-Means) when you do not have any ground-truth labels?",
 "You must use intrinsic evaluation metrics that measure cluster density and separation. The Silhouette Score is the most common; it measures how similar an object is to its own cluster compared to other clusters (ranging from -1 to 1). Alternatively, the Davies-Bouldin Index or the Elbow Method (tracking within-cluster sum of squares/inertia) can evaluate cluster quality without ground truth.",
 ["Use intrinsic metrics measuring cluster density and separation", "Use the Silhouette Score (measures cohesion vs separation)", "Use the Elbow Method or Davies-Bouldin Index"],
 ["Ask the user to manually label a million rows"]),

("ML_EVAL", "tradeoff", "medium", "tradeoff", ["Regression Metrics"],
 "In regression tasks, what are the tradeoffs of evaluating your model using MAE (Mean Absolute Error) versus RMSE (Root Mean Squared Error)?",
 "MAE takes the absolute difference of errors, meaning it treats all errors linearly; it is highly robust to outliers and easy to explain to business stakeholders. RMSE squares the errors before averaging them, meaning it heavily penalizes large errors. You use RMSE if a prediction being off by 10 is exponentially worse than being off by 1; you use MAE if outliers should be ignored.",
 ["MAE: robust to outliers, linear penalty, easy to explain (average dollars off)", "RMSE: squares errors, heavily penalizing large outliers", "Use RMSE when large errors are catastrophic, MAE when outliers are expected noise"],
 ["MAE is only for positive numbers, RMSE is for negative numbers"]),

("ML_EVAL", "fundamentals", "easy", "concept", ["Evaluation Metrics"],
 "What does an F1-Score of 1.0 indicate about your classification model?",
 "An F1-Score is the harmonic mean of Precision and Recall. A score of 1.0 is the absolute theoretical maximum. It indicates perfect Precision (zero False Positives) and perfect Recall (zero False Negatives). If you see an F1-Score of 1.0 in a real-world project, it almost universally indicates catastrophic Data Leakage, a broken evaluation pipeline, or a completely trivial dataset.",
 ["Indicates perfect Precision (no false positives) and perfect Recall (no false negatives)", "Theoretical maximum score", "In reality, usually implies catastrophic Data Leakage or a broken evaluation pipeline"],
 ["It means the model crashed and threw error code 1.0"]),

# ---------------- ML_PROD ----------------
("ML_PROD", "explain", "easy", "concept", ["ML Drift"],
 "In production machine learning, what is the difference between Data Drift and Concept Drift?",
 "Data Drift (Covariate Shift) occurs when the statistical distribution of the input features changes (e.g., users get older, incomes rise). Concept Drift occurs when the fundamental relationship between the input features and the target variable changes (e.g., a macro-economic crash changes what an income of $50k means for loan default risk). Both degrade model performance.",
 ["Data Drift: statistical distribution of the input features changes", "Concept Drift: the actual underlying relationship between features and the target changes", "Both require monitoring and model retraining"],
 ["Data drift is for CSV files, concept drift is for JSON files"]),

("ML_PROD", "scenario", "hard", "scenario", ["Concept Drift"],
 "A spam classification model has been in production for 6 months. Model accuracy remains a perfect 99%, but user complaints about spam in their inbox have tripled. How is it mathematically possible for accuracy to remain 99% while the actual business metric collapses?",
 "Spammers realized they were blocked and stopped sending obvious spam, entirely changing their tactics. Your dataset is now massively imbalanced (e.g., 99% of emails are legitimate). The model, failing to recognize the new sneaky spam, simply predicts 'Not Spam' for almost everything. Since 99% of incoming mail is legit, the model mathematically scores 99% accuracy, completely masking the catastrophic drop in Recall for actual spam.",
 ["Severe Concept Drift caused the spammer tactics to change", "The model predicts 'Not Spam' for everything", "Because the live data is heavily skewed towards legit mail, global accuracy stays 99% while Recall drops to 0%"],
 ["The database was hacked by the spammers"]),

("ML_PROD", "implement", "medium", "implementation", ["Model Monitoring"],
 "You suspect Data Drift is degrading your model. How do you mathematically detect covariate shift (drift in the input features) between your training data and your live production data?",
 "You can use statistical distance metrics to compare the distributions. The Population Stability Index (PSI) is the industry standard for measuring shifts in categorical or binned continuous variables. For continuous distributions, you can use the Kolmogorov-Smirnov (KS) test or the Wasserstein distance (Earth Mover's Distance) to definitively quantify how far the production distribution has drifted from training.",
 ["Use statistical distance metrics to compare distributions", "Use Population Stability Index (PSI) for binned/categorical data", "Use Kolmogorov-Smirnov (KS) test or Wasserstein distance for continuous features"],
 ["Just look at the Pandas dataframe and guess"]),

("ML_PROD", "debug", "medium", "debugging", ["Model Serving"],
 "You deploy a model using a Flask API. During offline evaluation, the model takes 10ms per prediction. In production, the API endpoint takes 3 seconds per prediction. The model weights are identical. What bottleneck is likely causing this massive latency spike?",
 "The bottleneck is the serving architecture, not the model. Flask's built-in development server is single-threaded, synchronous, and blocking. If multiple requests hit simultaneously, they queue up, causing massive latency spikes. In production, you must wrap the framework in a WSGI server (like Gunicorn) with multiple workers, or use a dedicated ML serving engine (like Triton or TensorFlow Serving) that supports request batching.",
 ["Flask is a single-threaded, synchronous blocking server", "Concurrent requests queue up, causing latency spikes", "Fix by using Gunicorn with multiple workers or a dedicated serving engine (Triton/TF Serving)"],
 ["The model's math equations take longer to calculate in the cloud"]),

("ML_PROD", "tradeoff", "medium", "tradeoff", ["ML Architecture"],
 "What are the tradeoffs between generating predictions offline in a daily Batch job (e.g., Airflow + Snowflake) versus generating predictions in real-time via a synchronous REST API?",
 "Batch inference is highly cost-effective, leverages massive data-warehouse compute, avoids all real-time latency issues, and gracefully handles retries; however, predictions are 'stale' (up to 24 hours old). Real-time API inference provides instantaneous, context-aware predictions (e.g., reacting to a user clicking a button right now), but requires highly complex 24/7 infrastructure, strict latency SLAs, and expensive always-on compute.",
 ["Batch: highly cost-effective, scalable, reliable, but predictions are stale", "Real-time API: context-aware, instant reactions to live behavior", "Real-time API: requires 24/7 complex infrastructure, strict SLAs, and high costs"],
 ["Batch inference only works at night, APIs only work during the day"]),

("ML_PROD", "scenario", "hard", "scenario", ["Training-Serving Skew"],
 "A model uses a user's `account_age_days` as a feature. During training, this was calculated relative to a fixed snapshot date. In production, the backend recalculates it dynamically every day. Over 3 months, the model's predictions slowly drift into nonsense. What specific production ML failure is this?",
 "This is Training-Serving Skew. The feature definition in the training environment fundamentally differs from the feature definition in the inference environment. Because `account_age_days` artificially increases every day in production without the model being retrained on that new scale, the model extrapolates into unknown feature space, destroying accuracy. You must strictly align feature engineering logic between offline training and online serving.",
 ["Training-Serving Skew", "The feature engineering logic offline differs fundamentally from online serving", "The dynamically growing feature pushes the model into unknown extrapolation territory"],
 ["The server clock is running backwards"]),

("ML_PROD", "explain", "medium", "concept", ["Model Robustness"],
 "Why is it dangerous to silently drop invalid or missing feature columns during production model inference (e.g., just passing zeroes to the model) instead of explicitly failing the request?",
 "Silently imputing defaults (like zeroes) during production inference masks catastrophic upstream data pipeline failures. If a microservice breaks and stops sending a crucial 'credit_score' feature, silently passing '0' will cause the model to confidently output wildly incorrect predictions (e.g., rejecting all loans). It is much safer to 'fail fast', throw an explicit error, and alert engineering, or fallback to a hardcoded heuristic.",
 ["Silently imputing defaults masks catastrophic upstream data pipeline failures", "Causes the model to confidently generate wildly incorrect/harmful predictions", "Better to 'fail fast', throw an error/alert, or fallback to a safe heuristic"],
 ["Passing zeroes causes the model to divide by zero and explode the GPU"]),

# ---------------- ML_OPS ----------------
("ML_OPS", "fundamentals", "easy", "concept", ["Feature Stores"],
 "What is the purpose of a Feature Store in a machine learning architecture?",
 "A Feature Store is a centralized data management layer that calculates, stores, and serves ML features. It solves Training-Serving Skew by providing an offline store (for generating historically accurate training datasets without temporal leakage) and an online store (a low-latency key-value cache for real-time inference), ensuring the exact same feature engineering code is used in both environments.",
 ["Centralized layer to calculate, store, and serve features", "Prevents Training-Serving skew", "Provides historically accurate offline data for training and low-latency online data for inference"],
 ["It is a retail shop where you buy premium ML features"]),

("ML_OPS", "explain", "medium", "concept", ["Model Deployment"],
 "Explain the concept of 'Shadow Deployment' (or Dark Launching) for a new machine learning model.",
 "Shadow Deployment involves deploying the new V2 model alongside the live V1 model. Production traffic is routed to both models, but only V1's prediction is returned to the user. V2's prediction is merely logged to a database. This allows engineers to safely evaluate V2's latency, stability, and real-world accuracy on live data without any risk of impacting the actual user experience.",
 ["Deploying a new model alongside the live model", "V2 receives live traffic but its predictions are only logged, not returned to the user", "Safely evaluates live performance, latency, and stability with zero user risk"],
 ["Deploying a model secretly on the Dark Web"]),

("ML_OPS", "tradeoff", "hard", "tradeoff", ["Model Packaging"],
 "What are the architectural tradeoffs of packaging a model's weights directly inside a Docker container (Baked-in) versus having the container download the weights from cloud storage (e.g., S3) at runtime?",
 "Baking weights into the container ensures absolute immutability, instant startup times (no network dependency), and guarantees code-weight compatibility, but results in massive Docker image sizes (e.g., 5GB+) which bloat container registries. Downloading weights at runtime keeps images tiny and allows updating models without redeploying code, but drastically increases container cold-start times and introduces a critical network point of failure.",
 ["Baked-in: immutable, instant startup, guaranteed code-weight compatibility, but massive Docker images", "Runtime Download: tiny images, decouple model updates from code deployments", "Runtime Download: slow cold-starts, introduces network point of failure"],
 ["Docker containers melt if they get too heavy"]),

("ML_OPS", "scenario", "medium", "scenario", ["A/B Testing"],
 "You are replacing an older recommendation model (V1) with a new model (V2). V2 has 5% better offline metrics. How do you safely validate that V2 actually performs better in the real world before turning off V1 entirely?",
 "I would run a live A/B Test (or a Canary release). I route 90% of user traffic to V1 (the control) and 10% to V2 (the variant). I then monitor the actual business metrics (e.g., Click-Through Rate or Revenue) and system metrics (Latency) over a statistically significant period. If V2 performs better without degradation, I gradually ramp its traffic to 100%.",
 ["Run a live A/B Test (or Canary release)", "Route a small percentage of traffic (e.g., 10%) to V2", "Monitor actual business metrics and system stability before ramping to 100%"],
 ["Just turn off V1 and hope V2 works"]),

("ML_OPS", "implement", "medium", "implementation", ["Reproducibility"],
 "How do you architect an ML training pipeline to ensure complete reproducibility of a model trained 6 months ago?",
 "Complete reproducibility requires versioning three distinct pillars. 1) Code: Ensure the exact Git commit of the training script is logged. 2) Environment: Use Docker or strict `requirements.txt`/Poetry locks for dependencies. 3) Data/Model: Use a tool like DVC (Data Version Control) or MLflow to snapshot the exact dataset hash, the seed values used for random states, and the final model weights artifacts.",
 ["Version the Code: Log the exact Git commit", "Version the Environment: Strict dependency locks or Docker images", "Version the Data/Parameters: Use DVC/MLflow to snapshot data hashes, random seeds, and weights"],
 ["Write the entire code down on a piece of paper and put it in a safe"]),

("ML_OPS", "debug", "hard", "debugging", ["ML Pipelines"],
 "Your automated ML pipeline retrains a model weekly. This week, the pipeline completed successfully, the model passed all unit tests, and was deployed. However, the model immediately started predicting the exact same class for 100% of inputs. What critical pipeline validation step is missing?",
 "The pipeline is missing Data Validation (e.g., using Great Expectations or TensorFlow Data Validation) on the incoming training data. An upstream bug likely corrupted the training data (e.g., setting the target column to all 0s). The model mathematically 'learned' this perfectly, passed unit tests, and deployed. You must explicitly assert the statistical distribution of the incoming training data and halt the pipeline if anomalies are detected.",
 ["Missing Data Validation / Distribution checks on incoming training data", "Upstream bugs can corrupt the training data, which the model will happily learn", "Must assert the statistical distribution of the dataset before training begins"],
 ["The pipeline forgot to tell the model what day it is"]),

# ---------------- ML_DL ----------------
("ML_DL", "fundamentals", "easy", "concept", ["Neural Networks"],
 "In Deep Learning, what is the 'Vanishing Gradient' problem, and what activation function was popularized specifically to solve it?",
 "The Vanishing Gradient problem occurs in deep networks where gradients get exponentially smaller as they backpropagate toward the earlier layers, preventing those layers from updating their weights or learning. The ReLU (Rectified Linear Unit) activation function solved this; because its derivative is exactly 1 for all positive inputs, it allows gradients to flow backwards through deep networks without vanishing.",
 ["Gradients become exponentially smaller as they backpropagate, halting learning in early layers", "Popularized solution: ReLU (Rectified Linear Unit) activation function", "ReLU has a constant derivative of 1 for positive inputs, preventing gradient decay"],
 ["It means the gradient colors on the charts fade away in the sun"]),

("ML_DL", "explain", "medium", "concept", ["Model Quantization"],
 "Explain the concept of Post-Training Quantization (e.g., converting a model from FP32 to INT8). What is its primary benefit for production serving?",
 "Quantization compresses the model by reducing the mathematical precision of its weights and activations. Converting 32-bit floats (FP32) to 8-bit integers (INT8) reduces the model's memory footprint by 4x and drastically increases inference speed (latency) on specialized hardware (like CPUs or Tensor Cores), usually with only a marginal, acceptable loss in predictive accuracy.",
 ["Reduces the mathematical precision of model weights (e.g., 32-bit float to 8-bit integer)", "Reduces memory footprint (VRAM/RAM) by 4x", "Drastically increases inference speed (lower latency) with minimal accuracy loss"],
 ["It converts the model into quantum physics mechanics"]),

("ML_DL", "tradeoff", "medium", "tradeoff", ["Edge Deployment"],
 "What are the tradeoffs of deploying an ML model onto an edge device (e.g., a smartphone) versus running inference on a centralized cloud GPU?",
 "Edge deployment guarantees zero network latency, strict data privacy (data never leaves the phone), and works offline, but is severely constrained by the device's tiny battery, limited RAM, and weak compute power, restricting you to small, quantized models. Cloud deployment allows massive, state-of-the-art models and easy updates, but requires constant internet access, introduces network latency, and incurs heavy recurring cloud compute costs.",
 ["Edge: Zero network latency, strict privacy, offline capability", "Edge: Severely constrained by battery, RAM, and compute (requires small models)", "Cloud: Access to massive compute/SOTA models, but requires network, adds latency, and costs money"],
 ["Edge devices have sharp edges that can cut the server cords"]),

("ML_DL", "scenario", "hard", "scenario", ["Memory Constraints"],
 "You are deploying a massive deep learning model. The model requires 16GB of VRAM to run, but your production GPUs only have 8GB of VRAM. Aside from buying bigger GPUs, what ML engineering techniques can you use to fit the model into memory?",
 "I can use Quantization (converting FP32 weights to FP16 or INT8 to halve or quarter the memory). I can use Pruning (removing near-zero weights from the neural network entirely). I could also use Knowledge Distillation (training a much smaller 'student' model to mimic the predictions of the massive 16GB 'teacher' model). Finally, if latency allows, I could chunk the model across multiple GPUs (Model Parallelism).",
 ["Quantization (reducing precision to INT8/FP16)", "Pruning (removing non-essential neural weights)", "Knowledge Distillation (training a smaller student model to mimic the massive teacher)"],
 ["Just compress the model into a .zip file and run it inside the zip"]),

("ML_DL", "implement", "medium", "implementation", ["Regularization"],
 "You train a deep neural network for image classification. It severely overfits the training data. What structural regularizations can you add to the network architecture to reduce this overfitting?",
 "I would add Dropout layers, which randomly zero out a percentage of neurons during training, preventing the network from relying on specific highly-weighted paths. I would also add Batch Normalization layers, which normalize inputs between layers to smooth the loss landscape. Additionally, I could use Data Augmentation (randomly flipping/rotating training images) to artificially expand the dataset's diversity.",
 ["Add Dropout layers (randomly disables neurons to prevent co-adaptation)", "Add Batch Normalization to smooth the loss landscape", "Implement Data Augmentation (flipping/rotating) to artificially increase dataset diversity"],
 ["Make the network deeper by adding 1,000 more layers"]),

("ML_DL", "debug", "medium", "debugging", ["PyTorch Inference"],
 "During inference of a deployed PyTorch model, memory usage grows continuously by 50MB per request until the server crashes with an Out Of Memory (OOM) error. What fundamental PyTorch inference mistake causes this?",
 "The inference code is missing the `torch.no_grad()` context manager. By default, PyTorch tracks every operation and stores the computational graph in memory to calculate gradients for backpropagation later. During production inference, you are not training the model, so storing this graph is completely useless and causes a massive, continuous memory leak. Wrapping the forward pass in `with torch.no_grad():` fixes it.",
 ["Missing the `torch.no_grad()` context manager during inference", "PyTorch uselessly builds and stores the computational graph in memory for backpropagation", "Causes a massive, continuous memory leak leading to OOM"],
 ["PyTorch naturally consumes 50MB of RAM just to stay warm"]),

# ---------------- ML_DEBUG ----------------
("ML_DEBUG", "scenario", "medium", "scenario", ["Imbalanced Data"],
 "You are building a classification model to detect fraudulent transactions. The model achieves 99% accuracy on the test set. However, a baseline model that simply hardcodes `return 'Not Fraud'` also achieves 99% accuracy. What is the fundamental issue, and how do you evaluate the model correctly?",
 "The dataset is massively imbalanced (99% legitimate, 1% fraud). Accuracy is a mathematically useless metric here because predicting the majority class yields near-perfect accuracy while completely failing the business objective. You must evaluate the model using Precision, Recall, F1-Score, or the PR-AUC (Precision-Recall Area Under Curve), focusing specifically on the model's performance on the minority 'Fraud' class.",
 ["The dataset is massively imbalanced, making Accuracy a useless metric", "Predicting only the majority class mathematically yields 99% accuracy", "Must use Precision, Recall, F1-Score, or PR-AUC focusing on the minority class"],
 ["Fraud is mathematically impossible to detect"]),

("ML_DEBUG", "tradeoff", "hard", "tradeoff", ["Objective Functions"],
 "When building a recommendation system, what are the tradeoffs between explicitly optimizing for Click-Through Rate (CTR) versus optimizing for Session Duration (Watch Time)?",
 "Optimizing for CTR encourages clickbait; the model will highly rank sensationalist, low-quality content that drives instant clicks but ruins the user experience, leading to long-term churn. Optimizing for Session Duration promotes high-quality, engaging content, but heavily penalizes short-form content creators and makes the model slower to react to user intent since you must wait for the session to end to calculate the reward.",
 ["CTR: Encourages clickbait and low-quality content, degrades long-term user experience", "Duration: Promotes high-quality engagement, but penalizes short-form creators", "Duration: Slower feedback loop, requires waiting for the session to end to calculate reward"],
 ["CTR measures how fast the mouse moves, Duration measures how hard they click"]),

("ML_DEBUG", "explain", "medium", "concept", ["Data Splitting Leakage"],
 "Explain why using a simple Random Split to create a Test set is mathematically dangerous when dealing with panel data (multiple rows belonging to the exact same user).",
 "A random split will put some rows of User A in the Train set, and other rows of User A in the Test set. The model will essentially memorize User A's specific behavioral quirks during training, and then perform flawlessly on User A in the test set. This is Data Leakage. To evaluate how the model performs on genuinely *unseen* users, you must use a GroupKFold or group-based split, keeping all of User A's rows firmly in one set.",
 ["Random splits leak specific user behavior into the Test set", "Model memorizes the user, inflating Test accuracy (Data Leakage)", "Must use Group-based splits (e.g., GroupKFold) to ensure the Test set contains entirely unseen users"],
 ["Random splits divide the data alphabetically by default"]),

("ML_DEBUG", "implement", "medium", "implementation", ["AI Fairness"],
 "You discover your model is explicitly biased, rejecting loan applications for a specific demographic group at a much higher rate. How do you mathematically evaluate and measure this fairness discrepancy?",
 "You can measure this using fairness metrics like Disparate Impact (the ratio of positive prediction rates between the unprivileged and privileged groups) or Equal Opportunity Difference (the difference in True Positive Rates / Recall between the groups). If these metrics show severe divergence, you must mitigate the bias through pre-processing (reweighing data), in-processing (adversarial debiasing), or post-processing (threshold adjustment).",
 ["Use fairness metrics like Disparate Impact or Equal Opportunity Difference", "Disparate Impact compares the overall positive prediction rates between demographic groups", "Equal Opportunity compares the True Positive Rates (Recall) between groups"],
 ["Just delete the demographic column and assume the problem is solved"]),

("ML_DEBUG", "fundamentals", "easy", "concept", ["Evaluation Rigor"],
 "What is 'Data Snooping' in machine learning, and why does it invalidate your offline evaluation metrics?",
 "Data Snooping occurs when you repeatedly evaluate your model on the Test set, adjust your hyperparameters, and evaluate again. While you didn't explicitly train on the Test set, you used it to guide your tuning decisions. Your model has now indirectly overfitted to the Test set, invalidating it as a measure of unseen generalization. You must strictly use a separate Validation set for tuning.",
 ["Repeatedly evaluating on the Test set and adjusting hyperparameters based on the result", "Indirectly overfits the model to the Test set", "Invalidates the Test set; must use a separate Validation set for tuning decisions"],
 ["It means an engineer is looking over your shoulder while you code"])
]
