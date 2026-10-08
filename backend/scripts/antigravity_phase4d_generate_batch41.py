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
    # Feature Engineering
    ("B1", "tradeoff", "medium", "concept", ["Data Cleaning"], "When dealing with high-cardinality categorical features like zip codes, target encoding is often preferred over one-hot encoding. What is the primary risk of target encoding, and what specific technique should you implement to mitigate it?", "The primary risk is data leakage and severe overfitting, as the feature directly encodes information about the target from the training set. To mitigate this, you must use K-fold target encoding (or leave-one-out encoding) where the target mean for a category in one fold is calculated using only the data from the other folds, often combined with smoothing to handle rare categories.", ["K-fold target encoding", "Data leakage", "Overfitting"], ["Just use one-hot encoding instead"]),
    ("B1", "scenario", "hard", "scenario", ["Time-Series"], "You are building a time-series forecasting model using rolling window features (e.g., 7-day moving average). During backtesting, the model achieves near-perfect accuracy, but performance drops significantly in production. What specific type of feature leakage most likely occurred during your windowing process?", "This is a classic case of lookahead bias. The rolling window likely included the target value of the current timestep or future timesteps when calculating the feature (e.g., aggregating from t-3 to t+3 instead of strictly t-7 to t-1). In production, future data is unavailable, causing the performance drop.", ["Lookahead bias", "Including future timesteps", "Rolling window including current target"], ["Overfitting to the training data"]),
    ("B1", "architecture", "medium", "concept", ["Hashing"], "In a system with millions of unique categorical identifiers, feature hashing (the hashing trick) is used to bound the memory footprint. How does feature hashing handle unseen categories, and what is its main drawback?", "Feature hashing handles unseen categories naturally because any new string will simply hash to one of the predefined bins (modulo the bin size) without needing a pre-computed vocabulary mapping. The main drawback is hash collisions, where multiple distinct categories map to the same bin, potentially destroying predictive signals and making model interpretation difficult.", ["Hash collisions", "No vocabulary mapping needed", "Maps strings to fixed bins"], ["It uses an embedding layer"]),
    ("B1", "implement", "medium", "architecture", ["Embeddings"], "You are building a recommendation model that uses both sparse high-cardinality categorical features and dense continuous features. How do you conceptually combine these two distinct feature types in a deep learning architecture before passing them to the final dense layers?", "The standard approach is to pass the sparse categorical features through an Embedding layer to convert them into dense, low-dimensional continuous vectors. These learned embeddings are then concatenated with the normalized dense continuous features to form a single unified dense vector, which is then passed into the subsequent fully connected layers.", ["Embedding layer for sparse features", "Concatenate embeddings with dense features"], ["Add the sparse and dense features together"]),
    ("B1", "tradeoff", "medium", "tradeoff", ["Imbalanced Data"], "When addressing extreme class imbalance in a dataset with very high-dimensional continuous features (e.g., 500+ dimensions), why might using SMOTE be problematic compared to simply applying class weights during model training?", "SMOTE generates synthetic examples by interpolating between nearest neighbors. In high-dimensional spaces, the concept of distance degrades (the curse of dimensionality), causing nearest neighbors to be less meaningful. This often leads SMOTE to generate noisy or unrealistic synthetic samples. Class weighting avoids this by simply scaling the loss function without modifying the feature space.", ["Curse of dimensionality", "Distance metrics degrade", "Class weighting modifies loss directly"], ["SMOTE is too slow"]),
    ("B1", "explain", "easy", "concept", ["Spatial Features"], "When working with cyclical continuous features like the hour of the day (0-23) or day of the year, treating them as standard numerical values is problematic. What transformation should you apply to allow a model to understand that 23:00 and 01:00 are close to each other?", "You should apply a sine and cosine transformation to the cyclical feature. By creating two new features using `sin(2 * pi * x / max_val)` and `cos(2 * pi * x / max_val)`, the model can represent the cyclical nature of the data on a unit circle, preserving the continuous distance across the wrap-around point.", ["Sine and cosine transformations", "Unit circle representation"], ["One-hot encoding"]),
    ("B1", "tradeoff", "easy", "tradeoff", ["Text Processing"], "For a simple text classification task deployed in an environment with severe memory constraints, would you choose TF-IDF or a pre-trained Transformer embedding model to generate text features, and why?", "You would choose TF-IDF. Pre-trained Transformer embeddings require loading a large, memory-intensive neural network (often hundreds of megabytes or gigabytes) just to generate the features. TF-IDF only requires storing a vocabulary mapping and inverse document frequencies, which requires a tiny fraction of the memory.", ["TF-IDF requires much less memory", "Transformers require loading large weights"], ["TF-IDF is more accurate"]),
    ("B1", "compare", "medium", "compare", ["Feature Selection"], "Compare L1 Regularization (Lasso) and Tree-based Feature Importance for the purpose of feature selection. In what scenario would Tree-based importance heavily penalize a genuinely useful feature?", "L1 Regularization selects features by driving the coefficients of less important linear features to exactly zero. Tree-based importance measures how often a feature is used to split the data. If two features are highly correlated, a tree model will typically choose one to split on and ignore the other, causing the second feature to incorrectly appear to have near-zero importance despite being highly predictive.", ["Correlated features", "Trees pick one of the correlated features"], ["L1 is for deep learning"]),
    ("B1", "tradeoff", "hard", "tradeoff", ["Data Leakage"], "When applying standardization (e.g., StandardScaler) to a dataset before training a model, why must you fit the scaler strictly on the training set and only 'transform' the validation/test sets, rather than fitting it on the entire dataset at once?", "Fitting the scaler on the entire dataset causes data leakage, as the global mean and variance used to scale the training data will have been influenced by the test data's distribution. The model would indirectly learn information about the test set during training, leading to overly optimistic evaluation metrics.", ["Data leakage", "Validation/test distribution influences training data"], ["It takes too much memory to scale all at once"]),
    ("B1", "architecture", "medium", "architecture", ["Feature Pipelines"], "In a real-time ML feature pipeline, you compute a 5-minute rolling average of user clicks. What is the fundamental difference in how this feature must be computed for historical training data versus live online inference?", "For live online inference, the feature must be computed incrementally in a stream processing engine (like Flink) or updated in an in-memory database to minimize latency. For historical training data, the feature must be computed in a batch processing engine (like Spark) using window functions to reconstruct exactly what the 5-minute average was at every historical point in time.", ["Stream processing for online inference", "Batch processing for historical training", "Incremental vs window functions"], ["Online uses Python, batch uses SQL"]),

    # Model Training
    ("B2", "explain", "medium", "concept", ["Optimizers"], "Why has AdamW largely replaced standard Adam when training modern deep neural networks with weight decay?", "Standard Adam applies weight decay as part of the L2 regularization term inside the gradient calculation. Because Adam scales gradients by their historical moving averages, it inadvertently scales the weight decay penalty as well, making the regularization less effective. AdamW decouples the weight decay from the gradient update, applying it directly to the weights, which restores its intended regularizing effect.", ["Decouples weight decay from gradient update", "Adam scales the regularization penalty"], ["AdamW is faster to compute"]),
    ("B2", "scenario", "medium", "scenario", ["Learning Rates"], "During the training of a large model, you use a Cosine Annealing with Warm Restarts learning rate scheduler. You notice the training loss periodically spikes up before settling back down to a lower minimum. Is this behavior expected, and what is its theoretical purpose?", "Yes, this behavior is expected. The scheduler periodically 'restarts' by resetting the learning rate to a high value, which causes the temporary spike in loss. The purpose is to jolt the model out of sharp, local minima so it can explore the loss landscape and hopefully settle into flatter, more robust global or local minima that generalize better.", ["Expected behavior", "Jolt the model out of local minima", "Find flatter, more robust minima"], ["The model is diverging and needs clipping"]),
    ("B2", "diagnose", "hard", "debugging", ["Regularization"], "You apply Label Smoothing to your multi-class classification model. After implementation, you notice that while the model's accuracy on the validation set has improved, its overall cross-entropy loss on the validation set has actually increased. How do you diagnose this contradiction?", "This is normal and expected. Label Smoothing prevents the model from predicting exactly 1.0 for the true class, bounding its maximum confidence. Because standard cross-entropy loss heavily rewards extreme confidence on the correct class, the smoothed model will naturally incur a higher absolute loss value, even if it is making more accurate (but less overconfident) discrete predictions.", ["Label smoothing bounds maximum confidence", "Higher loss due to less extreme probabilities", "Accuracy improves because it generalizes better"], ["The labels are wrong"]),
    ("B2", "architecture", "hard", "architecture", ["Noisy Labels"], "You are training an image classifier on a dataset known to have roughly 20% completely incorrect, noisy labels. How does the 'Co-teaching' architecture approach this problem during training?", "Co-teaching involves training two separate neural networks simultaneously. In each mini-batch, each network computes the loss for all samples, selects the samples with the lowest loss (under the assumption that small-loss instances are more likely to be clean labels), and passes only those 'clean' samples to its sibling network to perform the gradient update.", ["Two separate networks", "Networks select low-loss samples for each other"], ["It uses a teacher-student distillation model"]),
    ("B2", "diagnose", "medium", "debugging", ["Activations"], "While training a deep Multi-Layer Perceptron (MLP) with standard ReLU activations, you notice that after a few epochs, a large portion of the network's neurons consistently output zero for all inputs, and the model's capacity degrades. What is this phenomenon and how can you fix it?", "This is the 'Dying ReLU' problem. It occurs when a large gradient update causes the weights to adjust such that the pre-activation value is always negative. Since ReLU outputs zero and has a gradient of zero for negative inputs, the neuron can never update again. It can be fixed by lowering the learning rate or switching to Leaky ReLU, which allows a small negative gradient.", ["Dying ReLU", "Negative pre-activations cause zero gradients", "Fix: Leaky ReLU or lower learning rate"], ["Vanishing gradients in backprop"]),
    ("B2", "explain", "hard", "concept", ["Model Capacity"], "Explain the 'Double Descent' phenomenon in modern machine learning. How does it contradict classical bias-variance tradeoff theory?", "Classical theory dictates a U-shaped risk curve where increasing model capacity beyond a certain point leads to overfitting and higher test error. Double descent shows that as capacity increases past the 'interpolation threshold' (where train error hits zero), test error actually begins to decrease again. Highly over-parameterized models discover smooth interpolating functions that generalize well, contradicting the idea that larger models always overfit.", ["Test error decreases again past interpolation threshold", "Over-parameterized models find smooth functions"], ["It means the model descends the gradient twice"]),
    ("B2", "tradeoff", "medium", "tradeoff", ["Contrastive Learning"], "When training a Siamese network with a Contrastive Loss function, you must select a 'margin' hyperparameter. What is the tradeoff when setting this margin too high versus too low?", "The margin dictates how far apart dissimilar pairs must be pushed in the embedding space. If the margin is too low, the model won't learn to separate different classes sufficiently, leading to overlapping embeddings. If the margin is too high, the model spends too much capacity trying to push already-distant dissimilar pairs infinitely far apart, destabilizing training and distorting the space.", ["Low margin: overlapping embeddings", "High margin: destabilized training / wasted capacity"], ["Margin controls the learning rate"]),
    ("B2", "compare", "medium", "compare", ["Loss Functions"], "Compare Focal Loss to standard Cross Entropy Loss. In what specific data scenario is Focal Loss mathematically designed to outperform Cross Entropy?", "Focal Loss is designed for extreme class imbalance. While standard Cross Entropy penalizes all misclassifications, Focal Loss adds a modulating factor that dynamically down-weights the loss assigned to easy, well-classified examples. This forces the model to focus its learning capacity on hard, misclassified examples (typically the rare minority class).", ["Down-weights easy examples", "Focuses on hard/minority examples", "Extreme class imbalance"], ["It focalizes the gradient on the majority class"]),
    ("B2", "architecture", "hard", "concept", ["Model Averaging"], "In many state-of-the-art training pipelines, developers maintain an Exponential Moving Average (EMA) of the model weights alongside the active training weights. What is the purpose of the EMA weights, and when are they used?", "The EMA weights act as a temporal ensemble of the model over the training process, resulting in a flatter, more stable, and more robust set of parameters. While the active weights are used to compute gradients and backpropagate during training, the EMA weights are used strictly for validation, evaluation, and final inference deployment.", ["Temporal ensemble", "Flatter/more stable parameters", "Used for inference/evaluation, not training updates"], ["It is used to calculate the momentum for Adam"]),
    ("B2", "scenario", "medium", "scenario", ["Curriculum Learning"], "You implement Curriculum Learning by initially training the model on only 'easy' examples and gradually introducing 'hard' examples. However, the model rapidly forgets how to solve the easy examples once the hard examples are introduced. How should you adjust your sampling strategy?", "Instead of purely sequential phasing where easy examples are removed entirely, the sampling strategy should be cumulative. You should gradually increase the proportion of hard examples in the training batches while still retaining a baseline percentage of the easy examples to prevent catastrophic forgetting.", ["Retain a percentage of easy examples", "Cumulative sampling", "Prevent catastrophic forgetting"], ["Lower the learning rate"]),

    # Production ML
    ("B3", "compare", "medium", "compare", ["Model Compression"], "Compare Post-Training Quantization (PTQ) to Quantization-Aware Training (QAT). Which generally yields higher accuracy for extreme 8-bit integer (INT8) quantization, and why?", "Quantization-Aware Training (QAT) yields higher accuracy. PTQ simply truncates a pre-trained FP32 model's weights to INT8, which can severely degrade performance due to clipping and rounding errors. QAT simulates the quantization rounding during the forward pass of training, allowing the model's weights to adapt and optimize around the quantization noise.", ["QAT simulates quantization during training", "Allows model to adapt to rounding errors", "PTQ just truncates weights"], ["PTQ is better because it doesn't change weights"]),
    ("B3", "optimize", "hard", "architecture", ["Inference Optimization"], "When exporting a PyTorch model to TensorRT or ONNX Runtime for production inference, the engine performs 'Operator Fusion'. What does this mean, and how does it reduce inference latency?", "Operator Fusion combines multiple sequential neural network operations (e.g., Convolution + Batch Normalization + ReLU) into a single optimized computational kernel. This reduces latency by minimizing GPU memory reads/writes (memory bandwidth bottleneck) and reducing the kernel launch overhead from the CPU.", ["Combines multiple operations into a single kernel", "Reduces memory reads/writes", "Reduces kernel launch overhead"], ["It merges two different models together"]),
    ("B3", "tradeoff", "medium", "tradeoff", ["Pruning"], "When optimizing a deep neural network, what is the primary tradeoff between unstructured pruning (zeroing individual weights) and structured pruning (removing entire channels/filters)?", "Unstructured pruning preserves higher model accuracy for a given sparsity level but usually provides no actual speedup on standard hardware because the dense matrix dimensions remain the same. Structured pruning physically reduces the tensor dimensions (removing channels), yielding immediate latency reductions and memory savings, but typically causes a larger drop in model accuracy.", ["Unstructured: better accuracy, no hardware speedup", "Structured: real speedup, worse accuracy drop"], ["Unstructured is easier to code"]),
    ("B3", "implement", "medium", "concept", ["Knowledge Distillation"], "In Knowledge Distillation, a small student model is trained to mimic a large teacher model. What is the role of the 'Temperature' parameter applied to the softmax function during this process?", "The Temperature parameter softens the teacher model's output probability distribution. Instead of a hard spike near 1.0 for the true class, higher temperatures reveal the teacher's 'dark knowledge'—the relative probabilities of the incorrect classes (e.g., a cat is more like a dog than a car). The student learns these inter-class relationships.", ["Softens probability distribution", "Reveals relative probabilities of incorrect classes", "Dark knowledge"], ["It controls the learning rate of the student"]),
    ("B3", "architecture", "hard", "architecture", ["Model Serving"], "Instead of a standard A/B test, your team decides to use a Multi-Armed Bandit (e.g., Thompson Sampling) to route traffic between three different production recommendation models. What is the core advantage of this architecture over A/B testing?", "A/B testing uses static traffic splits and requires waiting for statistical significance before picking a winner, wasting traffic on suboptimal models. A Multi-Armed Bandit dynamically updates the traffic routing in real-time, continuously shifting more traffic to the highest-performing model while still exploring the others, thereby minimizing 'regret' (lost conversions) during the experiment.", ["Dynamically shifts traffic to best model", "Minimizes regret/lost conversions during the test"], ["It doesn't require metric tracking"]),
    ("B3", "compare", "medium", "compare", ["Deployment Strategies"], "Compare Shadow Mode and Canary deployments in the context of releasing a new machine learning model to production.", "In Shadow Mode, the new model receives live production traffic and generates predictions, but those predictions are only logged and never returned to the user; the old model still serves the user. In a Canary deployment, the new model is deployed to a small percentage of live users (e.g., 5%) who actually receive its predictions, allowing for real-world business metric evaluation.", ["Shadow: logged only, not returned to user", "Canary: small % of actual users receive predictions"], ["Shadow mode is just staging environment"]),
    ("B3", "tradeoff", "medium", "tradeoff", ["Hardware Acceleration"], "You are serving a large transformer model for real-time inference (batch size = 1). What is the primary tradeoff when deciding whether to serve this model on a CPU versus a GPU?", "While GPUs have massive theoretical throughput for large batches, they suffer from high I/O latency when transferring data over the PCIe bus and kernel launch overheads. For a batch size of 1 with strict real-time latency constraints, a highly optimized CPU (or smaller edge TPU) can sometimes yield lower end-to-end latency than a GPU, though the GPU will vastly outperform the CPU if concurrent requests are dynamically batched.", ["GPU has PCIe data transfer and kernel overhead", "CPU can sometimes have lower latency for batch=1"], ["CPUs have more cores than GPUs"]),
    ("B3", "architecture", "medium", "architecture", ["Caching"], "You are deploying a heavy ML model that predicts product recommendations for users. To reduce compute costs, you implement a caching layer (Redis) for the predictions. What is the most critical logic you must design for this cache to remain effective without degrading the user experience?", "You must design an intelligent cache invalidation or TTL (Time-To-Live) strategy. If the user's underlying state changes (e.g., they add an item to their cart or view a new category), the cached recommendations become instantly stale and must be evicted or recomputed so the model can react to real-time intent.", ["Cache invalidation strategy", "Evict cache when user context/state changes"], ["You must use Memcached instead of Redis"]),
    ("B3", "optimize", "easy", "architecture", ["Retrieval Systems"], "You are building a semantic search system. Passing every document through a bi-encoder model at query time is too slow. What architectural pattern solves this?", "You must pre-compute the embeddings for all documents offline and store them in a Vector Database (like FAISS, Milvus, or Pinecone). At query time, you only pass the user's search query through the model to get a single embedding, and perform a fast Approximate Nearest Neighbor (ANN) search against the pre-computed document embeddings.", ["Pre-compute document embeddings offline", "Store in a Vector Database", "Approximate Nearest Neighbor search at query time"], ["Use a faster CPU"]),
    ("B3", "tradeoff", "easy", "tradeoff", ["Inference Patterns"], "What is the primary architectural tradeoff between Synchronous (REST/gRPC) model serving and Asynchronous (Message Queue/Kafka) model serving?", "Synchronous serving guarantees an immediate response to the client, but the client must block/wait, making the system vulnerable to latency spikes and timeouts under heavy load. Asynchronous serving decouples the request, allowing the system to handle massive traffic spikes via queue buffering and background processing, but the client must poll or receive a webhook for the eventual result.", ["Synchronous: immediate response but blocks, vulnerable to load", "Asynchronous: queue buffering, handles spikes, client must poll"], ["Async is always faster"]),

    # MLOps & Pipelines
    ("B4", "debug", "medium", "scenario", ["Data Validation"], "Your automated ML training pipeline triggered a retrain last night, but the resulting model's performance on the validation set plummeted. You check the raw data warehouse and see no missing files. What specific type of pipeline check likely failed or was missing?", "The pipeline likely lacks Data Validation or schema enforcement checks (e.g., Great Expectations, Deequ). Even if files exist, the underlying data may have suffered from schema drift, changes in unit measurements, unexpected null distributions, or feature range shifts that corrupted the training inputs before the model was trained.", ["Data Validation / Schema enforcement", "Schema drift or feature range shifts"], ["The model ran out of memory"]),
    ("B4", "implement", "hard", "scenario", ["Feature Stores"], "You introduce a new rolling 30-day aggregate feature to your Feature Store today. However, you need to train a model using historical data from the past year. What complex operation must the Feature Store perform to support this?", "The Feature Store must perform 'Backfilling' or 'Point-in-Time Correctness' (time-travel) calculations. It must retroactively compute what that 30-day rolling aggregate would have looked like for every historical training timestamp exactly as it was at that specific moment, ensuring no future data leaks into the historical feature values.", ["Backfilling", "Point-in-Time correctness / time-travel", "Preventing future data leakage"], ["Just copy the current value to all old rows"]),
    ("B4", "architecture", "easy", "concept", ["Model Registry"], "In an MLOps pipeline, what is the conceptual purpose of state transitions (e.g., Staging -> Production -> Archived) within a Model Registry?", "State transitions provide a centralized, version-controlled mechanism to track exactly which model artifact is currently serving live traffic, which one is under testing, and which ones are deprecated. This decouples the training of the model from the deployment of the model, allowing CI/CD systems to safely swap artifacts based on registry tags.", ["Centralized tracking of which artifact serves traffic", "Decouples training from deployment"], ["It stores the training data"]),
    ("B4", "debug", "medium", "debugging", ["Reproducibility"], "Two data scientists run the exact same PyTorch training script on the same GPU but get slightly different final model weights. They have already set `torch.manual_seed()` and `np.random.seed()`. What are they likely missing to ensure strict reproducibility?", "They are likely missing strict determinism flags for the GPU backend. For PyTorch, they must set `torch.backends.cudnn.deterministic = True` and `torch.backends.cudnn.benchmark = False`. Additionally, they must ensure the python `random` module is seeded, and dataloader workers are seeded consistently.", ["cudnn.deterministic = True", "cudnn.benchmark = False"], ["The learning rate is too high"]),
    ("B4", "tradeoff", "medium", "tradeoff", ["Feedback Loops"], "When building an automated continuous training loop for a recommendation system, what is the tradeoff between relying on explicit user feedback (e.g., 5-star ratings) versus implicit feedback (e.g., click-through rate or watch time)?", "Explicit feedback provides a high-quality, definitive signal of user preference, but it is extremely sparse because few users leave ratings. Implicit feedback is abundant and can be collected for almost every interaction, but it is noisy and heavily biased (e.g., a user might click a clickbait title but actually hate the content).", ["Explicit: high quality but very sparse", "Implicit: abundant but noisy and biased"], ["Implicit is harder to store in a database"]),
    ("B4", "scenario", "medium", "scenario", ["Pipeline DAGs"], "Your Airflow ML pipeline DAG consists of Data Extraction -> Preprocessing -> Training. The upstream database team announces their nightly ETL job will now occasionally finish 3 hours late. How should you adjust your ML DAG to handle this?", "You should modify the DAG to use Sensors (e.g., ExternalTaskSensor or S3KeySensor). Instead of triggering the ML pipeline on a fixed schedule, the sensor will poll and wait until the upstream data artifacts or completion flags are physically present before triggering the Preprocessing step.", ["Use Sensors", "Wait for upstream data artifacts to be present"], ["Just run the ML pipeline 3 hours later every day"]),
    ("B4", "architecture", "medium", "architecture", ["Continuous Training"], "Compare time-based triggers (e.g., nightly retrains) to performance-based triggers (e.g., retraining when metric drops below threshold) for Continuous Training pipelines. What infrastructure is required to support the latter?", "Time-based triggers are simple cron jobs. Performance-based triggers require a robust Model Monitoring and Observability infrastructure that constantly collects real-time production inference data, joins it with delayed ground-truth labels, calculates metrics (like accuracy or drift), and emits automated alerts/webhooks to trigger the CI/CD pipeline.", ["Requires Model Monitoring infrastructure", "Must join inferences with delayed ground-truth labels"], ["Performance triggers are just cron jobs running faster"]),
    ("B4", "scenario", "easy", "scenario", ["Model Deployment"], "Ten minutes after a CI/CD pipeline deploys a newly trained model to production, the monitoring system alerts that the API latency has spiked to 5 seconds per request. What is the immediate operational action you should take?", "You should immediately trigger a Rollback to the previous stable model version using the Model Registry or deployment orchestrator. You do not attempt to debug the new model in the live production environment; you restore service first, then debug the failed artifact offline.", ["Immediate Rollback to previous version", "Restore service before debugging"], ["SSH into the server and restart the docker container"]),
    ("B4", "architecture", "hard", "architecture", ["Schema Evolution"], "A software engineering team adds a new mandatory column to the user profile database. Your ML feature pipeline crashes because it doesn't recognize the column. How should an enterprise ML architecture handle schema evolution to prevent pipeline breaks?", "The architecture should use a Schema Registry (like Protobuf or Avro) coupled with strict contract tests between the SWE and ML teams. Data producers must register schema changes, and the ML pipeline should be configured to gracefully ignore unrecognized columns or rely on defined data contracts rather than blindly reading raw database dumps with `SELECT *`.", ["Schema Registry", "Data contracts between teams", "Avoid SELECT * dependencies"], ["Just write a try/except block"]),
    ("B4", "compare", "medium", "compare", ["CI/CD"], "In an ML CI/CD pipeline, how does a Data Test (e.g., checking feature distributions) differ conceptually from a standard Unit Test for the model code?", "A Unit Test verifies that the model's code executes correctly (e.g., the forward pass tensor shapes match, the loss function computes correctly). A Data Test verifies the statistical properties of the inputs and outputs (e.g., checking that the mean age feature is between 0 and 100). The code can be perfectly bug-free, but if the data is corrupted, the ML system will still fail.", ["Unit test checks code execution and tensor shapes", "Data test checks statistical properties of inputs"], ["Data tests are written in SQL, unit tests in Python"]),

    # Model Debugging
    ("B5", "diagnose", "hard", "debugging", ["Explainability"], "Your fraud detection model has been running in production for six months. You monitor SHAP values to explain feature importance. Suddenly, the SHAP value for 'transaction_amount' drops to zero for almost all predictions, though model accuracy remains stable. What is the most likely diagnosis?", "The most likely diagnosis is Feature Drift or a data pipeline breakage where 'transaction_amount' is suddenly being fed as nulls, zeros, or a constant value. The model maintains accuracy because it has shifted reliance to correlated features (e.g., 'merchant_type'), rendering the specific 'transaction_amount' feature irrelevant to the tree splits.", ["Data pipeline breakage feeding constants/nulls", "Model relies on correlated features instead"], ["SHAP values are fundamentally unstable"]),
    ("B5", "diagnose", "hard", "debugging", ["Metrics"], "Your A/B test dashboard shows the new model has a higher overall click-through rate than the old model. However, when you break the metrics down by mobile users and desktop users separately, the old model is actually better in BOTH categories. What statistical phenomenon is occurring?", "This is Simpson's Paradox. It occurs when confounding variables or imbalanced sample sizes distort the aggregate metric. For example, if the new model was served to a heavily disproportionate number of desktop users (who naturally have a higher baseline click rate), the aggregate average will look higher, masking the fact that the per-segment performance actually degraded.", ["Simpson's Paradox", "Confounding variables / imbalanced sample sizes across segments"], ["The database is lagging"]),
    ("B5", "explain", "medium", "concept", ["Adversarial Machine Learning"], "Explain the concept of an 'Adversarial Example' in the context of deep learning for computer vision. Why are neural networks particularly vulnerable to them?", "An adversarial example is an input image that has been intentionally modified with perturbations that are virtually imperceptible to the human eye, causing the model to make a high-confidence incorrect prediction. Deep neural networks are vulnerable because they map high-dimensional linear spaces; tiny perturbations in the input space can compound multiplicatively across deep layers, pushing the final vector across the decision boundary.", ["Imperceptible perturbations", "Causes high-confidence incorrect prediction", "High-dimensional linear nature of deep networks"], ["The image is blurry"]),
    ("B5", "debug", "medium", "scenario", ["Evaluation"], "Your text sentiment model achieves 95% overall accuracy on the test set. However, a customer reports that it systematically classifies any review containing the word 'vegan' as negative. What specific evaluation methodology did you fail to implement before deployment?", "You failed to implement Slice-Based Evaluation (or cohort analysis). While aggregate accuracy was high, evaluating performance on specific critical slices of the data (e.g., minority cohorts, specific keywords) would have revealed the model's localized bias and spurious correlation before deployment.", ["Slice-Based Evaluation", "Cohort analysis", "Evaluating specific sub-populations"], ["You didn't train it long enough"]),
    ("B5", "diagnose", "medium", "debugging", ["Dimensionality Reduction"], "You visualize your high-dimensional document embeddings using t-SNE. You notice that documents from completely different topics are overlapping heavily in a single massive blob in the center of the 2D plot. Assuming the model trained correctly, what t-SNE hyperparameter is likely misconfigured?", "The 'perplexity' hyperparameter is likely set too high. Perplexity dictates the balance between local and global aspects of the data (effectively the number of nearest neighbors each point considers). If set too high (e.g., close to the total number of data points), t-SNE fails to separate local clusters and merges everything into a central blob.", ["Perplexity", "Balance between local and global data structures"], ["The learning rate is too high"]),
    ("B5", "debug", "medium", "debugging", ["Memory Management"], "During a PyTorch training loop, you notice the system RAM (not GPU VRAM) slowly increasing every epoch until the OS kills the process (OOM). You are tracking the training loss in a python list like this: `losses.append(loss)`. What is causing the memory leak?", "In PyTorch, the `loss` variable is a Tensor that remains attached to the entire computational graph for backpropagation. By appending the raw `loss` tensor to a list, you are keeping the entire graph in memory for every step of the epoch, preventing the garbage collector from freeing it. You must append `loss.item()` to extract the raw python float.", ["Appending the raw loss tensor keeps the computation graph in memory", "Must use loss.item()"], ["PyTorch has a built-in memory leak"]),
    ("B5", "scenario", "hard", "scenario", ["Spurious Correlations"], "You train a computer vision model to detect skin cancer from medical images. It gets 99% accuracy. During clinical trials, doctors realize the model is just looking for the presence of a purple surgical ruler that was in all the positive training images. What is this called, and how do you fix it?", "This is a 'Spurious Correlation' or 'Clever Hans' effect, where the model learns a shortcut artifact rather than the true causal feature. To fix it, you must curate the dataset to include positive images without the ruler and negative images with the ruler, or aggressively crop/augment the images to remove the artifact during training.", ["Spurious Correlation", "Clever Hans effect", "Model learned a shortcut artifact"], ["It is called overfitting"]),
    ("B5", "diagnose", "medium", "debugging", ["RNNs"], "While training a recurrent neural network (RNN) on long text sequences, the loss becomes `NaN`. You confirm there are no missing values in the data. What architectural flaw in standard RNNs causes this, and what is the modern replacement?", "This is the Exploding Gradient problem, which is highly prevalent in standard RNNs because the same weight matrix is multiplied repeatedly across many time steps, causing gradients to grow exponentially. The modern architectural replacements are LSTMs or GRUs (which use gating mechanisms to control gradient flow) or Transformers.", ["Exploding Gradient due to repeated weight multiplication across time steps", "Replace with LSTMs, GRUs, or Transformers"], ["The data needs to be normalized"]),
    ("B5", "explain", "medium", "concept", ["Generative Models"], "When training a Generative Adversarial Network (GAN), what is 'Mode Collapse', and how does it manifest in the model's outputs?", "Mode Collapse occurs when the Generator network discovers a small subset of outputs (modes) that consistently fool the Discriminator. Instead of learning the full diversity of the true data distribution, the Generator collapses and begins producing the exact same or very similar outputs repeatedly, ignoring the random noise input.", ["Generator discovers a single output that fools discriminator", "Produces exact same outputs repeatedly", "Fails to capture full data diversity"], ["The generator stops learning entirely"]),
    ("B5", "debug", "easy", "scenario", ["Data Augmentation"], "You apply aggressive random cropping and flipping augmentations to your image object-detection dataset to prevent overfitting. However, the model completely fails to learn where the objects are. What crucial step in the data pipeline did you forget?", "You forgot to apply the exact same spatial transformations to the bounding box coordinates (the labels). If you crop or flip the image but leave the bounding box coordinates in their original locations, the labels will no longer align with the visual objects, destroying the training signal.", ["Apply spatial transformations to bounding box coordinates", "Labels must match the augmented image"], ["The images were cropped too small"])
]

BUCKET_KEYS = {
    "B1": ("Feature Engineering", "Data Transformation", "Python", ["ML Engineer", "Data Scientist"]),
    "B2": ("Model Training", "Optimization Algorithms", "PyTorch/TensorFlow", ["ML Engineer", "AI Engineer"]),
    "B3": ("Production ML", "Model Optimization", "TensorRT", ["ML Engineer", "Backend Developer"]),
    "B4": ("MLOps & Pipelines", "ML CI/CD", "MLflow/Airflow", ["ML Engineer", "DevOps / Cloud Engineer"]),
    "B5": ("Model Debugging", "Error Analysis", "Python", ["ML Engineer", "Data Scientist"]),
}

def main():
    with open(OUT, encoding="utf-8") as f:
        prior = [json.loads(l) for l in f if l.strip()]
    
    staged_q = [p["question"] for p in prior]
    staged_a = [p["expected_answer"] for p in prior]
    
    # Adding legacy supabase text for overlap detection
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
            "category": "AI/ML",
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
    
    for idx, c in enumerate(cands):
        nq = normalize_text(c["question"])
        reason = None
        if nq in seen_norm:
            reason = "exact_duplicate"
        else:
            qs = cosine_similarity(vec.transform([c["question"]]), SQ)[0]
            as_ = cosine_similarity(vec.transform([c["expected_answer"]]), SA)[0]
            comp = cosine_similarity(vec.transform([c["question"] + " " + c["expected_answer"]]), SC)[0]
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
        print("ERROR: Did not accept exactly 50. Aborting write.")
        sys.exit(1)

    for c in accepted:
        c["id"] = "gen_" + str(uuid.uuid4())
        c["generation_batch"] = "batch_41_ml_engineer"

    with open(OUT, "a", encoding="utf-8") as f:
        for c in accepted:
            f.write(json.dumps(c) + "\n")
            
    final_staging_total = len(prior) + len(accepted)
    role_counts = Counter(p.get("primary_role") for p in prior)
    role_counts[ROLE] += len(accepted)
    
    report = {
        "batch": "batch_41_ml_engineer",
        "records_attempted": len(cands),
        "records_accepted": len(accepted),
        "records_rejected": sum(rej.values()),
        "rejection_reasons": dict(rej),
        "staging_metrics": {
            "previous_staging_total": len(prior),
            "final_staging_total": final_staging_total,
            "role_total": role_counts[ROLE],
            "remaining_to_500": max(0, 500 - role_counts[ROLE])
        }
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_batch41_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(REPORTS_DIR, "phase4d_batch41_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Phase 4D - Batch 41 (ML Engineer)\n\n")
        f.write(f"- **Attempted**: {len(cands)}\n")
        f.write(f"- **Accepted**: {len(accepted)}\n")
        f.write(f"- **Rejected**: {sum(rej.values())}\n")
        f.write(f"- **Rejections**: {dict(rej)}\n\n")
        f.write("### Staging Totals\n")
        f.write(f"- **Previous Staging Total**: {len(prior)}\n")
        f.write(f"- **Final Staging Total**: {final_staging_total}\n")
        f.write(f"- **ML Engineer Role Total**: {role_counts[ROLE]}\n")

    print(f"Successfully generated 50 ML Engineer questions.")

if __name__ == "__main__":
    main()
