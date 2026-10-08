"""Batch 31 Part 2 question content (ML Engineer). Targeted Gap Generation."""

ROLE = "ML Engineer"

BUCKET_KEYS = {
    "MLOPS": ("MLOps", "Model Deployment", "Machine Learning", ["ML Engineer", "Data Engineer", "Software Engineer"]),
}

Q = [
# ---------------- MLOPS ----------------
("MLOPS", "tradeoff", "medium", "tradeoff", ["Inference", "Architecture"],
 "When deploying an ML model that predicts product recommendations, what is the architectural tradeoff between 'Batch Inference' (pre-computing recommendations overnight) versus 'Online Inference' (computing on-the-fly via API)?",
 "Batch inference is extremely cost-effective, maximizes throughput, and provides near-zero latency at serving time (just a DB lookup). However, it cannot react to real-time user behavior (e.g., items just added to cart). Online inference provides real-time personalization, but is significantly more expensive, complex to scale, and introduces heavy compute latency directly into the user request path.",
 ["Batch: Cost-effective, massive throughput, zero latency at serving. Fails at real-time personalization.", "Online: Real-time personalization based on immediate session behavior.", "Online Tradeoff: Expensive, complex to scale, and introduces compute latency into the user path."],
 ["Batch inference means baking the servers in an oven overnight"]),

("MLOPS", "implement", "hard", "implementation", ["Model Serving", "FastAPI"],
 "You are deploying a massive 10GB PyTorch model as a microservice using FastAPI. If you simply load the model inside the FastAPI route handler (`def predict(): model = load_model()`), the service will crash under load. How must you architect the model loading to serve concurrent traffic safely?",
 "You must load the model *globally* into memory exactly once during the application startup/initialization phase, completely outside of the request route handler. Furthermore, because Python's GIL limits concurrency for heavy models, you should wrap the service using a dedicated model serving framework (like TorchServe or Triton) which handles request batching and GPU memory management natively.",
 ["Load the model globally into memory exactly once during application startup", "Do NOT load the model inside the individual request route handler", "Use a dedicated serving framework (TorchServe, Triton) to handle batching and concurrent GPU memory"],
 ["Ask the user to download the 10GB model to their phone first"]),

("MLOPS", "debug", "hard", "debugging", ["Training-Serving Skew"],
 "Your fraud detection model is deployed via Shadow Deployment. It receives live production traffic but its outputs are dropped. You analyze the logs: the shadow model predicts 'Fraud' 90% of the time, whereas during offline validation it predicted 'Fraud' 1% of the time. What MLOps pipeline failure does this indicate?",
 "This indicates severe 'Training-Serving Skew'. The data being fed to the model in the live production request path is fundamentally structurally different or formatted differently than the historical data used in the training pipeline. For example, training data normalized 'Transaction Amount' to a 0-1 scale, but the live API passes the raw dollar amount (5000), causing activations to explode.",
 ["Indicates severe 'Training-Serving Skew'", "The live production data structure/formatting fundamentally differs from the training data", "Example: Live API passes un-normalized raw values while the model expects scaled 0-1 features"],
 ["The shadow model is just inherently more pessimistic about humanity"]),

("MLOPS", "scenario", "medium", "scenario", ["Deployments", "Canary"],
 "An MLOps engineer implements a 'Canary Deployment' for a new pricing model. The canary receives 5% of production traffic. What specific condition must be met before the engineer can safely route 100% of traffic to the new model?",
 "The canary deployment must not only pass technical health checks (like latency, memory usage, and HTTP 500 error rates), but it must also be statistically validated against a primary business or predictive performance metric (like conversion rate or mean absolute error) over a sufficient time period. It must prove it does not silently degrade the business baseline.",
 ["Must pass technical health checks (latency, memory, error rates)", "Must be statistically validated against a primary business/predictive metric (e.g., conversion rate)", "Prove the canary does not silently degrade the baseline before full rollout"],
 ["Wait until a literal canary bird sings in the server room"]),

("MLOPS", "explain", "easy", "concept", ["Model Monitoring", "Drift"],
 "In MLOps, what is the difference between 'Data Drift' and 'Concept Drift'?",
 "Data Drift (Feature Drift) occurs when the statistical distribution of the input features changes over time (e.g., users switch from desktop to mobile, shifting the 'device_type' distribution). Concept Drift occurs when the fundamental mathematical relationship between the input features and the target variable changes (e.g., consumer purchasing behavior changes fundamentally due to a recession).",
 ["Data Drift: The statistical distribution of the input features changes over time", "Concept Drift: The fundamental relationship between the inputs and the target variable changes", "Data drift is the 'what' changing; Concept drift is the 'meaning' changing"],
 ["Data drift happens on boats, concept drift happens in your mind"]),

("MLOPS", "tradeoff", "medium", "tradeoff", ["Feature Store", "Architecture"],
 "What is the tradeoff of using a centralized 'Feature Store' (like Feast) in an enterprise ML architecture versus having each data science team write their own ad-hoc SQL pipelines for model training and serving?",
 "Ad-hoc SQL pipelines are fast for prototyping but create massive technical debt and severe training-serving skew (offline SQL rarely matches online API logic). A centralized Feature Store guarantees the exact same feature engineering code/data is used for both offline training and online low-latency serving (eliminating skew), but requires significant upfront infrastructure investment and rigid governance.",
 ["Feature Store: Guarantees exact same feature code for training and online serving (eliminates skew)", "Feature Store: Encourages feature reuse across teams", "Tradeoff: Requires massive upfront infrastructure investment and rigid organizational governance"],
 ["A feature store is a literal physical retail store where you buy features"]),

("MLOPS", "implement", "medium", "implementation", ["Dynamic Batching", "Inference"],
 "You need to implement 'Dynamic Batching' for a GPU-backed inference service. How does dynamic batching increase throughput, and what is the primary constraint you must tune?",
 "Dynamic batching intercepts individual asynchronous HTTP requests arriving at the inference server and artificially delays them for a few milliseconds to group them into a single larger matrix (a batch). Sending one large batch to the GPU is vastly more computationally efficient. The primary constraint to tune is the `max_delay_ms`; waiting too long to build a batch violates the latency SLA of the earliest request.",
 ["Intercepts individual requests and artificially delays them to group into a single larger matrix", "GPUs process one large batch vastly more efficiently than many sequential single requests", "Constraint to tune: `max_delay_ms`. Waiting too long violates the latency SLA"],
 ["It forces the data scientists to bake dynamic cookies in batches"]),

("MLOPS", "debug", "hard", "debugging", ["Docker", "Hardware", "Inference"],
 "A model is deployed using a Docker container. In staging, inference takes 50ms. Deployed to production using the EXACT same Docker image, inference takes 2000ms. CPU/Memory utilization in production is barely 10%. Why is the identical container running 40x slower?",
 "This is a dependency or hardware mismatch inside the container runtime environment, specifically related to optimized linear algebra libraries (BLAS/CUDA). While the Docker image is identical, the underlying host CPU in production might lack AVX512 vector instructions, or the container failed to bind to the production GPU drivers, forcing PyTorch to silently fallback to unoptimized, single-threaded CPU execution.",
 ["Hardware mismatch or missing runtime dependencies (CUDA/BLAS) on the production host", "The host CPU lacks vector instructions (AVX512) or the container failed to bind to GPU drivers", "Forces the ML framework to silently fallback to highly unoptimized, single-threaded CPU execution"],
 ["The Docker container got seasick during deployment"]),

("MLOPS", "scenario", "medium", "scenario", ["Data Provenance", "Pipelines"],
 "You build an ML pipeline that retrains a recommendation model weekly. After month 3, performance slowly degrades. You investigate and find the pipeline simply executes a SQL query pulling 'the latest 30 days of data' to train. What fundamental MLOps versioning principle was violated?",
 "The pipeline violated 'Data Provenance' or 'Data Versioning'. By using a dynamic, mutable query ('latest 30 days'), the training dataset is constantly shifting and completely irreproducible. If a model fails, you have no way to mathematically reconstruct the exact data it was trained on to debug it. You must use data versioning tools (DVC) or immutable partition snapshots tied to the model artifact.",
 ["Violated 'Data Provenance' or 'Data Versioning'", "A dynamic query ('latest 30 days') creates a mutable, completely irreproducible training dataset", "Fix: Use immutable data versioning (DVC or partition hashes) linked strictly to the model artifact"],
 ["The pipeline forgot to ask the data for its consent"]),

("MLOPS", "explain", "easy", "concept", ["Model Lineage", "Registry"],
 "What is 'Model Lineage' in an ML model registry?",
 "Model Lineage is the complete, audited historical trail of a deployed model artifact. It explicitly links the final compiled model back to the specific version of the training code (Git commit), the specific version of the dataset used (DVC hash), the hyperparameter configuration, and the evaluation metrics generated during that specific run. It ensures complete reproducibility and compliance.",
 ["The complete, audited historical trail of a deployed model artifact", "Links the model to the exact Git commit, Dataset version (DVC), and hyperparameters used", "Ensures absolute reproducibility and compliance for production systems"],
 ["Model lineage tracks the genetic ancestors of the neural network"]),

("MLOPS", "implement", "hard", "implementation", ["Monitoring", "Delayed Labels"],
 "You design an MLOps architecture for a model predicting 'Will this customer churn in the next 30 days?'. How do you architect the monitoring system to calculate true accuracy in production, given that the labels are strictly delayed by 30 days?",
 "You cannot calculate true accuracy in real-time. You must architect a 'Delayed Label Join' pipeline. The online service logs the prediction and a `prediction_id` to a data lake. A separate asynchronous batch job runs daily, explicitly waiting 30 days for the actual business outcome in the CRM, joining it back to the `prediction_id`. Real-time monitoring must rely on prediction distribution drift instead.",
 ["Architect an asynchronous 'Delayed Label Join' pipeline", "Log the real-time prediction with a unique `prediction_id`", "A batch job waits 30 days, retrieves the true outcome, and joins it back to calculate accuracy"],
 ["Build a time machine to travel 30 days into the future"]),

("MLOPS", "tradeoff", "medium", "tradeoff", ["Quantization", "Optimization"],
 "When optimizing model serving latency, what is the tradeoff of using Model Quantization (e.g., converting FP32 weights to INT8)?",
 "Model Quantization massively reduces the physical memory footprint of the model (by up to 4x) and drastically accelerates inference speed because integer math is computationally cheaper and requires less memory bandwidth. The tradeoff is a potential loss of model accuracy, as continuous continuous weights are compressed into discrete integer buckets, introducing quantization noise.",
 ["Massively reduces memory footprint and drastically accelerates inference speed", "Integer math is computationally cheaper and requires less memory bandwidth", "Tradeoff: Potential loss of model accuracy/precision due to quantization noise"],
 ["Quantization turns the model into quantum physics, which is too confusing"]),

("MLOPS", "debug", "medium", "debugging", ["Feedback Loops", "Monitoring"],
 "An engineer configures an automated retraining pipeline triggered by Data Drift alerts. It successfully retrains and deploys new models. However, over 6 months, the model's performance slowly degrades. Why is performance degrading despite successful retraining on fresh data?",
 "This is the 'Feedback Loop' or 'Filter Bubble' problem. The automated retraining pipeline is blindly training on data generated *by the previous model's predictions*. If the model recommends a product, the user buys it, reinforcing the existing bias. Over time, the model aggressively narrows its focus. Retraining must include randomized exploration data (epsilon-greedy) or holdout control groups.",
 ["'Feedback Loop' or 'Filter Bubble' problem", "The pipeline blindly trains on data generated/influenced by the previous model's own predictions", "Fix: Must include randomized exploration data or holdout control groups to break the bias loop"],
 ["The models are getting tired of being constantly retrained"]),

("MLOPS", "scenario", "hard", "scenario", ["Artifact Compatibility", "Integration Testing"],
 "You deploy an `.h5` model behind a Flask API. It works. A month later, the data scientist gives you a new `.h5` file that is 'much more accurate'. You swap the file, but the API returns garbage predictions. What critical MLOps pipeline component is missing?",
 "The missing component is an automated 'Artifact Compatibility Validation' or 'Integration Test' pipeline. You blindly swapped a binary artifact without verifying if the expected input schema (feature order, normalization parameters, or tensor shape) fundamentally changed between version 1 and 2. The pipeline must rigidly enforce that any new artifact passes programmatic tests against the API contract.",
 ["Missing an automated 'Artifact Compatibility Validation' or 'Integration Test' pipeline", "Blindly swapping artifacts doesn't verify if the input schema/feature order fundamentally changed", "Must programmatically test that the new model contract matches the production API contract"],
 ["The new `.h5` file was actually a virus disguised as a model"]),

("MLOPS", "fundamentals", "easy", "concept", ["Shadow Deployment"],
 "What is a 'Shadow Deployment' in MLOps?",
 "A Shadow Deployment is a risk-free release strategy where a new model is deployed alongside the existing production model. The system duplicates real incoming user traffic and sends it to the shadow model, but completely discards the shadow model's predictions. The shadow predictions are logged to a database to safely analyze real-world performance without impacting the actual user experience.",
 ["A risk-free release strategy deploying a new model alongside the production model", "Duplicates real incoming user traffic to the shadow model, but discards its predictions", "Logs predictions to safely analyze real-world performance without impacting users"],
 ["The model is deployed in a dark room with no lights"]),

("MLOPS", "implement", "medium", "implementation", ["Experiment Tracking", "MLflow"],
 "You are using MLflow to track experiments during a hyperparameter sweep. What three fundamental categories of metadata should you rigorously log to the tracking server for every single run?",
 "1. Parameters: The exact configuration inputs (learning rate, batch size, model architecture). 2. Metrics: The quantitative outputs evaluating performance (training loss, validation accuracy, F1 score). 3. Artifacts: The physical files generated by the run (the compiled model weights `.pt`, confusion matrix plots, dataset sample hashes).",
 ["Parameters: The configuration inputs (learning rate, batch size)", "Metrics: The quantitative evaluation outputs (validation loss, accuracy)", "Artifacts: The physical files generated (model weights, serialized plots)"],
 ["The weather outside, what you ate for lunch, and your mood"]),

("MLOPS", "scenario", "hard", "scenario", ["Cold Starts", "Serverless"],
 "You deploy an NLP model that takes 500ms to load into RAM, and 50ms to run a prediction. You use a serverless architecture (AWS Lambda) that scales to zero. Users complain that occasionally, the API takes >2 seconds to respond. What is this problem, and how do you fix it?",
 "This is the 'Cold Start' problem. When traffic arrives after the service scaled to zero, the serverless provider must provision a new container and physically load the 500ms model into RAM before processing the 50ms request. You must either move away from scale-to-zero serverless to a constantly provisioned container service, or use 'Provisioned Concurrency' to guarantee minimum 'warm' instances.",
 ["The 'Cold Start' problem in scale-to-zero serverless architectures", "The container must be provisioned and the massive model loaded into RAM before serving the request", "Fix: Use 'Provisioned Concurrency' to guarantee minimum 'warm' instances, or move to dedicated containers"],
 ["The server is physically freezing and needs a jacket"])
]
