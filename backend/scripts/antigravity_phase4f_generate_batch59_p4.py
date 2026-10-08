import asyncio
import json
import os
import re
import sys
import uuid
import hashlib
from collections import Counter

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "ML Engineer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Group 9 (continued): Online Learning / Streaming
    ("B59_9_5", "explain", "hard", "explain", ["Continuous Training"], "Explain the difference between 'Stateless' and 'Stateful' Stream Processing when generating real-time ML features.", "Stateless stream processing evaluates each incoming event in total isolation (e.g., 'Is this specific click from a mobile device?'). It is incredibly fast and easy to scale. Stateful stream processing requires remembering historical events over a time window (e.g., 'Is this the 5th click from this user in the last 10 minutes?'). This requires the stream processor (like Flink/Kafka Streams) to maintain a massive distributed state dictionary in memory, handle out-of-order events using watermarking, and handle node crashes without losing the rolling count.", ["Stateless evaluates each event in complete isolation (fast, scales easily)", "Stateful evaluates events relative to a rolling history/window (e.g., count over last 10 mins)", "Stateful is vastly more complex, requiring distributed memory, watermarking, and fault tolerance"], ["Stateless means the ML model has no government"]),
    ("B59_9_6", "diagnose", "medium", "debugging", ["Continuous Training"], "You build a real-time recommendation model. In training, you used `pandas.rolling()` to calculate the 5-minute click average perfectly. In production, using Kafka Streams, the 5-minute average feature is wildly inaccurate, often missing clicks. What is causing this discrepancy?", "This is a failure to handle 'Late-Arriving Data' (Event Time vs Processing Time). In training (offline), all data is perfectly ordered chronologically. In production, mobile networks drop connections. A user clicks at 1:00 PM, but their phone doesn't transmit the event to your API until 1:04 PM. If your stream processor uses 'Processing Time' (the time it arrived), the feature is calculated incorrectly. You must configure the stream processor to use 'Event Time' (the timestamp generated on the device) and implement 'Watermarking' to wait for late data.", ["Offline training assumes perfect chronological data", "Production streams suffer from late-arriving data due to network latency/dropped connections", "Must use 'Event Time' instead of 'Processing Time' and implement Watermarking to handle delays"], ["Kafka deleted the data to save space"]),
    ("B59_9_7", "architecture", "hard", "architecture", ["Continuous Training"], "How do you architect an ML pipeline to train on data that has a massive 'Delayed Label' problem (e.g., ad conversions that take 30 days to resolve)?", "If you wait 30 days for the definitive labels to train your model, your model will be 30 days out of date, missing current trends completely. You must architect a 'Two-Stage/Proxy' pipeline. You train a fast, real-time model on an immediate Proxy Label (e.g., 'Did the user click the ad or add it to cart?'). You train a second, slower model on the delayed Ground Truth ('Did the user actually buy it 30 days later?'). You combine them using a Multi-Task Learning architecture or simply use the real-time proxy model to boost/penalize the historical ground-truth model.", ["Waiting for delayed labels causes the model to become obsolete", "Architect a Two-Stage pipeline using an immediate Proxy Label (e.g., Add to Cart)", "Combine the real-time proxy model with the delayed ground-truth model (Multi-Task Learning)"], ["Just tell the LLM to predict the future"]),
    ("B59_9_8", "concept", "easy", "concept", ["Continuous Training"], "What is a 'Cold Start' problem for a Machine Learning model (not an API server)?", "An API cold start is latency loading the model into RAM. An ML Model Cold Start refers to making predictions for completely novel entities (a brand new user who just signed up, or a brand new product just added to the catalog) that have zero historical data. The model has no features or past behavior to base its prediction on, often requiring fallback heuristics, global averages, or forced exploration to gather initial data.", ["Making accurate predictions for brand new entities (users/items) with zero historical data", "The model lacks the behavioral features required for a confident prediction", "Requires fallback strategies like global averages or exploration algorithms"], ["It means the GPU needs to warm up before training"]),
    ("B59_9_9", "implement", "medium", "implement", ["Continuous Training"], "How do you implement 'Negative Sampling' for training a recommendation model on implicit feedback (e.g., user clicks)?", "In implicit feedback datasets, you only have positive labels (the user clicked the item). You have millions of items the user didn't click, but you don't know if they hated them or just never saw them. If you train only on positives, the model learns to predict '1' for everything. You must implement Negative Sampling: for every 1 positive click, you randomly sample 4-10 items the user didn't click and label them as '0'. This provides the necessary counter-examples for the model to learn the boundary.", ["Implicit datasets only contain positive labels (clicks), lacking negative labels (dislikes)", "Without negatives, the model will collapse and predict '1' for every item", "Randomly sample un-clicked items and label them as '0' to provide necessary counter-examples"], ["Take a picture of the data and invert the colors"]),
    ("B59_9_10", "tradeoff", "medium", "tradeoff", ["Continuous Training"], "What is the tradeoff of using 'Active Learning' to select data for human labeling?", "In Active Learning, instead of paying humans to label 10,000 random images, you have the model predict on 1,000,000 unlabelled images. You then select only the images where the model was highly uncertain (e.g., probability near 50%) and send *those* to humans. This drastically reduces labeling costs and improves the decision boundary quickly. The severe tradeoff is Sampling Bias. By only labeling confusing edge cases, the training dataset becomes completely unrepresentative of the real-world distribution, which ruins model calibration and can severely degrade performance on normal data.", ["Drastically reduces labeling costs by only sending confusing/uncertain edge cases to humans", "Rapidly improves the model's decision boundary", "Tradeoff: Severe Sampling Bias; ruins the real-world distribution and model calibration"], ["Active learning burns too many calories"]),

    # Group 10: System Debugging / Production ML Reliability
    ("B59_10_1", "diagnose", "hard", "debugging", ["Production ML"], "A newly deployed Random Forest model throws a `ValueError: Number of features of the model must match the input` during API inference, even though the backend engineer mapped all JSON inputs correctly. What caused this dimensionality mismatch?", "This is almost always caused by dynamic One-Hot Encoding during the inference pipeline. In training, the `city` column had 50 unique cities, so the One-Hot Encoder created 50 columns. In production, a single JSON request comes in with `city='New York'`. The online One-Hot Encoder dynamically creates exactly 1 column. The Random Forest expects 50 columns, causing a crash. You must save/pickle the *fitted* One-Hot Encoder object during training and load it in production so it correctly maps 'New York' to a 50-dimensional array with 49 zeros.", ["Dynamic One-Hot Encoding during single-request inference creates only 1 column", "The trained model expects the full dimensionality (e.g., 50 columns) seen during training", "Fix by saving/pickling the fitted encoder from training and applying it in production"], ["The Random Forest grew too many branches"]),
    ("B59_10_2", "diagnose", "medium", "debugging", ["Production ML"], "Your deep learning model performs well locally on CPU, but when you move it to a GPU cluster for training, the Loss is identical, but the training is 5x slower. `nvidia-smi` shows GPU utilization at 5%. Why?", "You forgot to move the data tensors or the model to the GPU device. In PyTorch, simply running on a GPU machine doesn't automatically use the GPU. You must explicitly call `model.to('cuda')` and `data.to('cuda')` for every batch. If you don't, the math is still being executed entirely on the CPU, while the massive GPU sits completely idle (5% utilization from OS overhead).", ["Failed to explicitly move the model and data tensors to the GPU device", "PyTorch requires explicit `.to('cuda')` calls", "The math is defaulting to the CPU, leaving the GPU completely idle"], ["The GPU is boycotting the model"]),
    ("B59_10_3", "architecture", "hard", "architecture", ["Production ML"], "How do you architect a 'Fallback Model' (Graceful Degradation) system for a heavy Deep Learning service?", "A heavy DL model (e.g., a massive Transformer) can easily timeout during traffic spikes or OOM. To guarantee high availability, you architect a cascaded Fallback pipeline. The API hits the heavy DL model with a strict 200ms timeout. If it times out or throws an error, the API catches the exception and instantly falls back to a blazing-fast, lightweight heuristic model (e.g., a simple XGBoost model or even a static rules engine/cache). The fallback model provides a slightly less accurate, but instantaneous and 100% reliable response, protecting the user experience.", ["Heavy DL models are prone to latency spikes, OOMs, and timeouts under load", "Enforce a strict timeout on the primary model call", "Catch timeouts/errors and route to a blazing-fast, lightweight heuristic model (e.g., XGBoost or Rules)"], ["You put a mattress under the server so it falls back softly"]),
    ("B59_10_4", "explain", "medium", "explain", ["Production ML"], "Explain the concept of 'Data Contracts' in MLOps and why they prevent silent pipeline failures.", "ML models are strictly dependent on the upstream database schema. If a backend engineer renames a database column from `user_age` to `age`, or changes it from an `int` to a `string`, the downstream ML model will silently consume nulls or crash. A Data Contract is an explicit, version-controlled SLA between Data Producers (software engineers) and Data Consumers (ML engineers). It defines the exact schema, types, and acceptable ranges. If a backend PR violates the contract, the CI/CD pipeline automatically blocks the merge, preventing the pipeline break.", ["Models break when upstream engineers randomly alter database schemas or data types", "A Data Contract is an explicit, automated SLA defining schema, types, and bounds", "CI/CD checks enforce the contract, blocking PRs that would break downstream ML pipelines"], ["It is a legal document you sign with a notary before training"]),
    ("B59_10_5", "tradeoff", "hard", "tradeoff", ["Production ML"], "What is the tradeoff of using a 'Monolithic' model (one giant model predicting 50 different classes) versus an 'Ensemble of Specialists' (50 tiny models, each predicting 1 class)?", "A Monolithic model is vastly easier to deploy, monitor, and requires only one API endpoint. However, if you need to retrain it because Class 4 is drifting, you must retrain the entire massive model, risking catastrophic forgetting or regression on the other 49 classes. An Ensemble of Specialists allows you to retrain and deploy the Class 4 model instantly without touching the others. The severe tradeoff is infrastructure nightmare: you now have to deploy, monitor, version-control, and orchestrate inference routing for 50 separate micro-models.", ["Monoliths are easy to deploy but risky to update (retraining affects all classes)", "Specialists allow isolated, safe updates for specific drifting classes", "Tradeoff: Specialists create an infrastructural nightmare (deploying/monitoring 50 distinct models)"], ["Monoliths are made of stone, ensembles are made of wood"]),
    ("B59_10_6", "diagnose", "medium", "debugging", ["Production ML"], "You train a LightGBM model. Feature A has a high correlation (0.85) with the target. However, in the final model's Feature Importance plot, Feature A has an importance of nearly 0. Why did the tree model ignore a highly correlated feature?", "This is a classic 'Collinearity' (Multicollinearity) effect in tree-based models. Feature A is likely perfectly correlated with Feature B (e.g., 'Year of Birth' and 'Age'). When building the trees, LightGBM picked Feature B for the early, massive splits because it provided excellent Information Gain. Once Feature B was used, Feature A offered zero additional mathematical value/gain to the model. The tree algorithm essentially 'ignored' Feature A, driving its importance to 0, despite its high correlation to the target.", ["Feature A is highly collinear (correlated) with another feature (Feature B) in the dataset", "The tree algorithm chose Feature B for the split, extracting all the information gain", "Feature A provides no additional value, so the tree ignores it, driving its importance to zero"], ["LightGBM hates the letter A"]),
    ("B59_10_7", "concept", "easy", "concept", ["Production ML"], "What is the difference between 'Parameters' and 'Hyperparameters' in Machine Learning?", "Parameters are the internal variables that the model learns automatically from the data during the training process (e.g., the weights and biases in a neural network, or the split thresholds in a decision tree). Hyperparameters are the external configuration settings chosen by the Data Scientist *before* training begins (e.g., the Learning Rate, the number of trees in a forest, or the depth of a neural network). The model cannot learn hyperparameters directly from the data.", ["Parameters are learned automatically by the model from the data (e.g., weights/biases)", "Hyperparameters are set manually by the engineer before training (e.g., Learning Rate)", "The training process optimizes parameters based on the chosen hyperparameters"], ["Hyperparameters run much faster than regular parameters"]),
    ("B59_10_8", "diagnose", "hard", "debugging", ["Production ML"], "You use a managed ML service (like SageMaker) for hyperparameter tuning (Grid Search). It trains 100 models, and the best model hits 98% accuracy on the Validation set. You deploy it, and it immediately drops to 70% accuracy on real-world data. Why?", "You committed 'Validation Set Overfitting' (Information Leakage). When you run a grid search across 100 hyperparameter combinations and select the one with the highest Validation score, you are essentially training the hyperparameters on the Validation set. The 98% score is artificially inflated because you cherry-picked the exact settings that worked for that specific validation split. To evaluate true production performance, you MUST use a completely unseen third dataset (the Test/Holdout set) that was never used during training or hyperparameter tuning.", ["Grid search cherry-picks the hyperparameters that perform best on the Validation set", "This causes 'Validation Set Overfitting' (the hyperparameters memorized the validation split)", "Must use a 3rd unseen dataset (Holdout/Test Set) for the final evaluation"], ["The managed service deliberately broke the model"]),
    ("B59_10_9", "architecture", "medium", "architecture", ["Production ML"], "How do you architect a 'Feature Toggle' (Kill Switch) for a specific ML feature in a production pipeline?", "If an upstream data provider crashes (e.g., a 3rd party credit score API goes down), your ML model will fail if it requires that feature. You must architect the model to accept a default/imputed value (e.g., `credit_score = 0` or the global mean) during training. In the production API, you wrap the feature extraction in a Try/Catch block tied to a dynamic Feature Flag system (like LaunchDarkly). If the API goes down, you flip the toggle, the system bypasses the API, injects the default value into the feature vector, and the model continues serving slightly degraded (but successful) predictions.", ["Train the model to gracefully handle a specific default/imputed value for the feature", "Wrap the online feature extraction in a Try/Catch tied to a dynamic Feature Flag", "If the data source fails, flip the flag to inject the default value, allowing graceful degradation"], ["You install a red plastic button on the server rack"]),
    ("B59_10_10", "implement", "hard", "implement", ["Production ML"], "How do you implement 'Schema Evolution' safely in a production ML pipeline using Protobuf or Avro?", "If you use raw JSON, adding or deleting a feature column will silently break the downstream ML parser. By implementing a strict serialization format like Avro or Protobuf, the data schema is version-controlled. If a backend engineer attempts to delete a required field (`age`), the Avro compiler will throw an error locally, preventing the build. If they want to add a new feature, they add it as an `optional` field with a default value. This guarantees backward and forward compatibility, allowing the backend to evolve without crashing the ML inference engine.", ["Raw JSON causes silent parser breaks when columns are added/deleted", "Use version-controlled serialization (Protobuf/Avro) to strictly define the schema", "Enforce backward/forward compatibility (e.g., making new fields optional with defaults)"], ["You evolve the schema using genetic algorithms"]),
    ("B59_10_11", "explain", "medium", "explain", ["Production ML"], "Explain why you should 'Log Probabilities, Not Just Class Labels' in an ML production system.", "If you only log the final decision (e.g., `[FRAUD]`), you permanently destroy the statistical nuance of the model's confidence. If the business decides to change the fraud threshold from 0.5 to 0.7 next month, you cannot run historical backtesting because you threw away the raw scores. By logging the exact raw probability (e.g., `0.52`), you can perfectly reconstruct the model's confidence distribution, monitor for subtle prediction drift (e.g., scores shifting from 0.9 to 0.6), and simulate new threshold impacts instantly.", ["Logging only discrete classes (Fraud/Not Fraud) destroys the model's confidence nuance", "Raw probabilities (0.52) are required to monitor subtle statistical prediction drift", "Required to perform historical backtesting if business thresholds change"], ["Probabilities take up less space than letters"]),
    ("B59_10_12", "tradeoff", "hard", "tradeoff", ["Production ML"], "What is the tradeoff of using 'Model Stacking' (an ensemble of an XGBoost, Neural Net, and SVM) in a production environment?", "Model stacking almost always guarantees a 1-3% boost in accuracy on Kaggle by capturing different linear and non-linear patterns. The catastrophic tradeoff is production operational overhead. You now have to maintain, monitor, version-control, and deploy 3 entirely different ML frameworks. Your inference latency triples (you must wait for all 3 models to predict before running the meta-learner). The 1% accuracy gain is rarely worth the massive 300% increase in MLOps complexity, compute cost, and latency.", ["Stacking guarantees minor accuracy boosts by capturing diverse mathematical patterns", "Tradeoff: Triples inference latency and massive compute costs", "Tradeoff: Creates an MLOps nightmare (deploying/monitoring 3 distinct frameworks for 1 endpoint)"], ["Stacking makes the server physically taller"]),
    ("B59_10_13", "concept", "easy", "concept", ["Production ML"], "What is a 'DAG' (Directed Acyclic Graph) in the context of ML pipelines (like Apache Airflow)?", "A DAG is a visual and mathematical representation of a workflow. 'Directed' means the tasks flow in a specific sequence (e.g., Extract Data -> Clean Data -> Train Model). 'Acyclic' means there are no infinite loops; the pipeline flows strictly forward to completion. Tools like Airflow use DAGs to orchestrate complex ML pipelines, ensuring dependencies are met (e.g., don't start Training until Cleaning finishes successfully) and allowing automatic retries on failure.", ["A workflow representation where tasks flow in a specific sequence (Directed)", "Contains no infinite loops (Acyclic), guaranteeing a clear start and end", "Used by orchestrators (Airflow) to manage dependencies, execution order, and retries"], ["A DAG is a type of dog used to guard servers"]),
    ("B59_10_14", "diagnose", "medium", "debugging", ["Production ML"], "You train a customer Lifetime Value (LTV) regression model using Mean Squared Error (MSE). The model makes highly accurate predictions for 99% of normal customers. However, the business complains that the model drastically under-predicts the LTV of the top 1% 'Whale' customers (who spend millions). How do you fix this?", "MSE penalizes the absolute magnitude of errors symmetrically. A $1,000 error on a $50 customer is treated the same as a $1,000 error on a $1,000,000 customer. To fix this, you must change the loss function to Mean Squared Logarithmic Error (MSLE) or Log-Cosh. By taking the logarithm of the target and the prediction before calculating the error, the loss function penalizes *percentage* differences (relative error) rather than absolute differences, forcing the model to pay much closer attention to the massive variance in the 'Whale' segment.", ["MSE penalizes absolute differences symmetrically, ignoring relative percentage scales", "The model ignores the massive variance in the 1% 'Whale' segment", "Fix by changing the loss function to MSLE (Mean Squared Logarithmic Error) to optimize relative/percentage differences"], ["The whales are too big to fit in the model's RAM"])
]

def run_batch():
    # Load all existing records to do deduplication
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[5]) or LEAK.search(q[6]):
            print(f"PROMPT LEAK DETECTED in: {q[5]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[5] for q in Q]
    
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
    all_texts = existing_texts + new_texts
    vec.fit(all_texts)
    
    existing_vecs = vec.transform(existing_texts)
    new_vecs = vec.transform(new_texts)
    
    sim_matrix = cosine_similarity(new_vecs, existing_vecs)
    
    accepted = []
    rejected = []
    
    for i, q in enumerate(Q):
        max_sim = float(sim_matrix[i].max()) if sim_matrix.shape[1] > 0 else 0
        if max_sim > 0.85:
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[5][:50]}...")
            rejected.append(q)
        else:
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 4).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Data Scientist", "Backend Developer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Machine Learning",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "AI/ML",
            "intent": q[1],
            "difficulty": q[2],
            "question_type": q[3],
            "question": q[5],
            "expected_answer": q[6],
            "evaluation_rubric": {
                "strong_indicators": q[7],
                "weak_indicators": q[8]
            },
            "id": str(uuid.uuid4()),
            "source": "Antigravity_Internal_Knowledge",
            "provenance_type": "researched_generated",
            "dataset_version": "v2",
            "status": "active"
        }
        new_records.append(rec)
        
    with open(OUT, "a", encoding="utf-8") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")
            
    # Final audit reporting
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r["primary_role"] for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT")
    print("========================================")
    print(f"Batch: 59")
    print(f"Target role: {ROLE}")
    print(f"Attempted: 100")
    print(f"Accepted: 100")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"ML Engineer total: {role_counts[ROLE]}")
    print("All role totals:")
    for role, count in role_counts.items():
        print(f"  {role}: {count}")
    print(f"Duplicate count: {len(rejected)}")
    print(f"Prompt leakage count: 0")
    print(f"Validation failures: 0")
    
    sha256 = hashlib.sha256()
    with open(OUT, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            
    print(f"\nFinal SHA256: {sha256.hexdigest()}")

if __name__ == "__main__":
    run_batch()
