"""Batch 30 Part 1 question content (AI Engineer). Targeted Gap Generation."""

ROLE = "AI Engineer"

BUCKET_KEYS = {
    "AI_EVALUATION": ("AI Evaluation", "Model Benchmarking", "LLMs", ["AI Engineer", "Machine Learning Engineer", "Data Scientist"]),
}

Q = [
# ---------------- AI_EVALUATION ----------------
("AI_EVALUATION", "scenario", "medium", "scenario", ["LLM-as-a-judge", "Bias"],
 "You are designing an 'LLM-as-a-judge' evaluation pipeline to grade the relevance of chatbot answers. You notice the evaluator LLM consistently scores answers that are simply longer as 'more relevant', even if they contain hallucinated fluff. What is this phenomenon called, and how can you mitigate it?",
 "This is known as 'Verbosity Bias' or 'Length Bias'. To mitigate it, you must explicitly instruct the evaluator prompt to strictly penalize unnecessary verbosity and prioritize conciseness. Alternatively, you can prompt the judge to extract specific factual claims before grading, artificially normalize the length of the evaluated answers, or fine-tune a specialized evaluator model to ignore length.",
 ["'Verbosity Bias' or 'Length Bias'", "The evaluator LLM inherently prefers longer answers regardless of quality", "Mitigate by explicitly prompting the judge to penalize fluff, or by extracting factual claims first"],
 ["The LLM gets tired of reading short answers"]),

("AI_EVALUATION", "tradeoff", "hard", "tradeoff", ["Regression Testing", "Datasets"],
 "When building a regression testing suite for an AI application, what is the analytical tradeoff between using a small 'Golden Dataset' of 100 human-annotated examples versus using an automated 'LLM-as-a-judge' pipeline on 10,000 unannotated production logs?",
 "The Golden Dataset provides absolute, high-fidelity ground truth and prevents evaluation drift, but is static, expensive to update, and cannot cover long-tail edge cases. The automated LLM-as-a-judge pipeline provides massive scale, diversity, and dynamic coverage of real production traffic, but is susceptible to judge bias, false positives, and might silently drift/degrade without human oversight.",
 ["Golden Dataset: High fidelity ground truth, but static, expensive, and lacks long-tail coverage", "LLM-as-a-judge: Massive scale and dynamic real-world coverage", "LLM-as-a-judge Tradeoff: Susceptible to judge bias and silent drift without human oversight"],
 ["Golden datasets are made of physical gold, which is very expensive for startups"]),

("AI_EVALUATION", "debug", "hard", "debugging", ["LLM-as-a-judge", "Position Bias"],
 "You run an LLM-as-a-judge to compare Model A and Model B pairwise ('Which is better?'). When Model A's answer is presented first, it wins 70% of the time. When Model A's answer is presented second, it only wins 40% of the time. What is this evaluation failure called, and what is the standard architectural fix?",
 "This is 'Position Bias' or 'Order Bias', where the evaluator LLM inherently prefers the first (or sometimes last) option presented in the prompt, regardless of actual quality. The standard architectural fix is to run every pairwise comparison twice, swapping the order of the answers (A then B, and B then A), and only declaring a definitive winner if the model wins in both positions.",
 ["'Position Bias' or 'Order Bias'", "The LLM inherently prefers the first (or last) option presented in the prompt context", "Fix: Run every comparison twice with swapped positions, requiring a win in both to count"],
 ["Model A is physically exhausted by the time it gets to the second position"]),

("AI_EVALUATION", "explain", "easy", "concept", ["RAG", "Metrics"],
 "In AI evaluation, what is the difference between measuring 'Factuality' and measuring 'Groundedness' (or Faithfulness)?",
 "Factuality measures whether the LLM's output is objectively true in the real world (e.g., 'Paris is the capital of France'). Groundedness (Faithfulness) measures whether the LLM's output is strictly supported by the provided context/documents, regardless of whether the context itself is factually true. An answer can be factual but ungrounded, or perfectly grounded but factually false.",
 ["Factuality: Is the output objectively true in the real world?", "Groundedness (Faithfulness): Is the output strictly supported by the provided context?", "An answer can be factual but ungrounded (hallucinating outside the context)"],
 ["Groundedness means the AI servers are physically grounded to prevent electrical shocks"]),

("AI_EVALUATION", "implement", "medium", "implementation", ["RAG", "LLM-as-a-judge"],
 "You need to evaluate the 'Groundedness' of a RAG application using an LLM-as-a-judge. How do you design the prompt for the evaluator LLM to ensure it grades strictly based on the provided documents?",
 "You must provide the evaluator LLM with both the retrieved context and the generated answer. The prompt must instruct the evaluator to perform 'Claim Extraction': first, extract every distinct factual claim made in the generated answer. Second, rigorously verify if each specific claim is explicitly supported by, contradicted by, or missing from the provided context.",
 ["Provide the evaluator with both the retrieved context and the generated answer", "Instruct the judge to perform 'Claim Extraction' (extract distinct factual claims first)", "Verify each specific claim against the context (Supported, Contradicted, or Missing)"],
 ["Just ask the LLM 'Is this grounded?' and trust its answer"]),

("AI_EVALUATION", "tradeoff", "medium", "tradeoff", ["Deployment", "Monitoring"],
 "What is the operational tradeoff between conducting 'Offline Evaluation' (using a static dataset before deployment) versus 'Online Evaluation' (using A/B testing and user feedback in production)?",
 "Offline evaluation is completely safe, highly reproducible, and allows for rapid, isolated regression testing of prompts without impacting users, but relies on historical data that may miss current user behavior. Online evaluation measures the true, dynamic business impact (e.g., acceptance rates), but exposes real users to potentially degraded models, and explicit feedback signals are often highly sparse and noisy.",
 ["Offline: Safe, reproducible regression testing, but relies on static/historical data", "Online: Measures true dynamic business impact with real user behavior", "Online Tradeoff: Exposes real users to degraded models and relies on sparse/noisy feedback"],
 ["Offline evaluation requires turning off the company's internet connection"]),

("AI_EVALUATION", "scenario", "hard", "scenario", ["Metrics", "NLP"],
 "A generative AI system translates legal documents. You calculate the BLEU and ROUGE scores against human reference translations, but both scores are abysmal (e.g., 0.20), even though domain experts say the AI translations are flawless. Why are these traditional metrics failing, and what should you use instead?",
 "BLEU and ROUGE are rigid n-gram overlap metrics; they measure exact word/phrase matches against the reference string. Generative LLMs can produce perfectly valid, highly articulate translations using completely different vocabulary, synonyms, and phrasing than the reference, causing n-gram metrics to fail completely. You must use semantic similarity metrics (like BERTScore or embedding cosine similarity) or an LLM-as-a-judge.",
 ["BLEU and ROUGE are rigid n-gram overlap metrics requiring exact word matches", "LLMs generate valid translations using different vocabulary/phrasing, failing exact-match metrics", "Fix: Use semantic similarity (BERTScore, embeddings) or an LLM-as-a-judge"],
 ["The domain experts are lying to you to protect the AI's feelings"]),

("AI_EVALUATION", "debug", "medium", "debugging", ["Dataset Construction"],
 "You are evaluating a classification prompt that categorizes support tickets into 5 buckets. The LLM gets 95% accuracy on your Golden Dataset. You deploy it, and accuracy drops to 60%. Upon investigation, production contains many tickets that don't neatly fit into the 5 buckets. What fundamental evaluation error did you make?",
 "You constructed an unrepresentative evaluation dataset completely lacking negative examples, ambiguous inputs, or long-tail edge cases. Your Golden Dataset likely only contained clean, perfectly categorizable examples. The evaluation failed to measure the model's ability to handle ambiguity or gracefully decline (e.g., classifying as 'Other'), leading to a massive discrepancy between offline metrics and online reality.",
 ["Constructed an unrepresentative evaluation dataset lacking negative/ambiguous examples", "The Golden dataset was too 'clean' and didn't reflect the messy reality of production", "Failed to evaluate the model's ability to handle ambiguity or out-of-scope inputs"],
 ["The LLM forgot how to classify things overnight"]),

("AI_EVALUATION", "fundamentals", "easy", "concept", ["Annotation"],
 "What is 'Inter-Rater Reliability' (or Inter-Annotator Agreement) in the context of building AI evaluation datasets?",
 "Inter-Rater Reliability measures the degree of agreement or consistency between multiple human annotators grading the exact same AI outputs. If human experts cannot agree on what constitutes a 'Good' or 'Bad' answer (low agreement), the evaluation criteria are too subjective, and an automated LLM judge will never be able to reliably replicate the grading.",
 ["Measures the degree of agreement between multiple human annotators grading the same output", "Low agreement indicates the evaluation criteria/rubric is too subjective or poorly defined", "If humans can't agree, an automated LLM judge cannot reliably automate the evaluation"],
 ["It measures how reliable the internet connection is between the annotators"]),

("AI_EVALUATION", "implement", "hard", "implementation", ["Monitoring", "Drift"],
 "You want to detect 'Evaluation Drift'—the scenario where your LLM-as-a-judge silently degrades over time because the underlying provider (e.g., OpenAI) updated the judge model. How do you architect a monitoring system to catch this drift?",
 "You must implement a 'Judge Calibration Suite'. You maintain a small, strictly frozen dataset of previously graded examples (both good and bad) where the ground-truth scores are known and locked. You run this calibration suite through your LLM-as-a-judge pipeline on a daily cron schedule. If the automated judge's scores on this static dataset suddenly diverge from the historical baseline, the evaluator model has drifted.",
 ["Implement a 'Judge Calibration Suite' using a strictly frozen dataset of known examples", "Run the calibration suite through the LLM-as-a-judge pipeline on a recurring schedule", "If the judge's scores suddenly diverge from the historical baseline, alert on Evaluation Drift"],
 ["Call the model provider on the phone and ask if they changed anything"]),

("AI_EVALUATION", "scenario", "medium", "scenario", ["Regression Testing", "Brittle Tests"],
 "You upgrade a summarization model from GPT-3.5 to GPT-4o. GPT-4o produces much better summaries but fails 40% of the automated tests. You investigate and find the automated tests are strictly parsing for the exact string format `Summary: [text]`, but GPT-4o is outputting `Here is the summary: [text]`. What evaluation anti-pattern is this?",
 "This is 'Overfitting the Evaluation to the Model' (or brittle heuristic parsing). The evaluation pipeline is rigidly relying on exact string matching or fragile regex heuristics that were accidentally tuned to the specific quirks of the old model. When the new model generates better content but slightly different formatting, the brittle pipeline fails. The evaluation should use semantic extraction or structured outputs (JSON).",
 ["'Overfitting the Evaluation to the Model' or brittle heuristic parsing", "Relying on exact string matching/regex tuned to the specific quirks of the old model", "Fix: Use semantic extraction, LLM judges, or strict structured outputs (JSON) instead of regex"],
 ["GPT-4o is objectively worse than GPT-3.5 at summarizing"]),

("AI_EVALUATION", "tradeoff", "hard", "tradeoff", ["Code Generation", "Metrics"],
 "When designing an evaluation metric for an AI coding assistant, what is the tradeoff between measuring 'Execution Correctness' (compiling against unit tests) versus measuring 'Code Similarity' (comparing against a reference solution)?",
 "Execution Correctness is the ultimate test of functional utility; it proves the code actually works, regardless of how novel the implementation is. However, it requires a heavily sandboxed, expensive, and complex secure execution environment. Code Similarity is computationally cheap and completely safe, but fundamentally flawed because there are infinite valid ways to write a function, heavily penalizing valid, novel implementations.",
 ["Execution Correctness: Proves functional utility, but requires complex/expensive secure sandboxing", "Code Similarity: Computationally cheap and safe", "Similarity Tradeoff: Fundamentally flawed, heavily penalizes valid, novel implementations"],
 ["Execution correctness requires the AI to physically type on a keyboard"]),

("AI_EVALUATION", "explain", "medium", "concept", ["Calibration", "Logprobs"],
 "What does 'Calibration' mean in the context of an LLM's confidence scores or logprobs?",
 "Calibration measures how closely the model's internal statistical confidence aligns with its actual empirical accuracy. A perfectly calibrated model that outputs a token with 80% confidence (logprob) will be factually correct exactly 80% of the time. Poorly calibrated models (common after heavy RLHF fine-tuning) are often confidently wrong, outputting hallucinations with 99% probability, rendering logprobs useless.",
 ["How closely the model's internal statistical confidence aligns with its actual accuracy", "An 80% confident token should be factually correct 80% of the time", "Poorly calibrated models are 'confidently wrong', making logprobs useless for anomaly detection"],
 ["Calibration means tuning the LLM's vocal chords to sound more human"]),

("AI_EVALUATION", "scenario", "medium", "scenario", ["Agents", "Trajectory Evaluation"],
 "An AI agent uses tools to answer user questions. You want to evaluate the agent's performance. Why is it analytically insufficient to only evaluate the final text answer the agent returns to the user?",
 "Evaluating only the final answer completely ignores the execution trajectory. The agent might have hallucinated the right answer without actually calling the required tools, or it might have wastefully called the wrong tools 15 times, racking up massive latency and token costs, before finally stumbling upon the right tool. You must evaluate 'Trajectory Correctness'—verifying the sequence, efficiency, and parameters of the tool calls.",
 ["Ignores the execution trajectory (efficiency, tool usage, latency)", "The agent might hallucinate the right answer or wastefully loop through wrong tools 15 times", "Must evaluate 'Trajectory Correctness': verifying the sequence, efficiency, and exact parameters of tool calls"],
 ["The final answer text usually deletes itself after 5 seconds"]),

("AI_EVALUATION", "debug", "hard", "debugging", ["LLM-as-a-judge", "Central Tendency Bias"],
 "You use an LLM-as-a-judge to score the safety of generated responses on a scale of 1 to 5. You notice the judge model almost exclusively outputs scores of 3 or 4, almost never outputting 1 or 5, even for extremely toxic or perfectly safe text. What is this phenomenon, and how do you fix it?",
 "This is 'Central Tendency Bias' (or safe-grading bias), where the evaluator LLM avoids extreme scores to minimize perceived error. To fix it, you should switch from a continuous Likert scale (1-5) to a strictly binary or categorical classification (e.g., 'Pass/Fail', or 'Safe/Toxic/Ambiguous'), forcing the model to make a definitive decision, and provide highly detailed, unambiguous rubrics for each category.",
 ["'Central Tendency Bias' (safe-grading bias)", "The evaluator avoids extreme scores (1 or 5) to minimize perceived error", "Fix: Switch from a continuous scale (1-5) to strict categorical classification (Pass/Fail) with detailed rubrics"],
 ["The LLM is programmed to always be perfectly average"]),

("AI_EVALUATION", "fundamentals", "easy", "concept", ["Datasets", "Machine Learning"],
 "In AI evaluation, what is a 'Holdout Dataset'?",
 "A Holdout Dataset is a completely isolated set of data that is strictly never used during prompt engineering, fine-tuning, or iterative development. It is exclusively reserved for the final, unbiased evaluation of the model before deployment in production, ensuring the system hasn't merely overfitted to the training or development datasets.",
 ["A completely isolated dataset never used during development, prompting, or fine-tuning", "Exclusively reserved for the final, unbiased evaluation before production deployment", "Ensures the model hasn't merely overfitted to the development datasets"],
 ["It is a dataset that you physically hold out of the window"]),

("AI_EVALUATION", "implement", "medium", "implementation", ["Failure Taxonomy", "RAG"],
 "You need to establish a 'Failure Taxonomy' for a RAG-based support bot. What are the three primary functional failure categories you must define to correctly route errors to the correct engineering teams?",
 "1. Retrieval Failure: The search system/vector DB failed to find the relevant document (Data Engineering issue). 2. Groundedness Failure (Hallucination): The system retrieved the correct document, but the LLM ignored it and made up an answer (Prompt/Model issue). 3. Instruction/Formatting Failure: The system got the right answer but failed to format it correctly or failed to adopt the correct persona.",
 ["Retrieval Failure: The vector DB failed to find the relevant document", "Groundedness Failure (Hallucination): Retrieved correctly, but the LLM ignored it and fabricated the answer", "Instruction/Formatting Failure: Answered correctly, but violated formatting or persona instructions"],
 ["Hardware Failure, Software Failure, and User Error"])
]
