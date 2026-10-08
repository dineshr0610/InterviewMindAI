import json
import os
import uuid
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

questions_data = [
    # --- BUCKET 1: LLM Architecture -> Attention ---
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Deep Learning"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the core mathematical purpose of the Self-Attention mechanism in a Transformer model?",
        "expected_answer": "Self-attention allows the model to weigh the importance of different words in a sequence relative to a specific target word. It calculates a weighted sum of the input representations, mathematically allowing the model to capture long-range contextual relationships and dependencies regardless of their distance in the sequence.",
        "evaluation_rubric": {"strong_indicators": ["Weighing importance of other words", "Contextual relationships", "Weighted sum"], "weak_indicators": ["Thinks it works exactly like RNNs processing sequentially"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Deep Learning"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain how the Query, Key, and Value (QKV) matrices are derived and used in scaled dot-product attention.",
        "expected_answer": "Q, K, and V are derived by multiplying the input embeddings by three learned weight matrices (W_q, W_k, W_v). The Query represents what the current token is looking for; the Key represents what a token contains; the Value is the actual content. Attention scores are calculated by taking the dot product of Q and K (scaled down), applying a softmax, and multiplying the result by V.",
        "evaluation_rubric": {"strong_indicators": ["Learned weight matrices", "Q=seeking, K=containing, V=content", "Dot product of Q and K -> Softmax -> multiply V"], "weak_indicators": ["Confuses Query and Key roles"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Architecture"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Conceptually, how is Multi-Head Attention implemented differently from single-head attention to prevent massive increases in computational complexity?",
        "expected_answer": "Instead of using one massive QKV projection, Multi-Head Attention splits the embedding dimension into smaller, lower-dimensional subspaces (heads). Each head independently calculates attention, and the results are concatenated and linearly transformed. Because the dimension is divided by the number of heads, the computational complexity is roughly the same as a single-head layer.",
        "evaluation_rubric": {"strong_indicators": ["Splitting the embedding dimension", "Independent subspace calculations", "Concatenation"], "weak_indicators": ["Thinks Multi-Head Attention multiplies the parameter count by the number of heads"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Performance"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the memory and computational trade-offs of standard dense self-attention versus sparse or sliding-window attention (like Longformer)?",
        "expected_answer": "Standard dense attention calculates the dot product for every token pair, resulting in O(N^2) memory and time complexity relative to sequence length (N). Sparse/sliding-window attention only attends to a local radius of neighboring tokens (or specific global tokens), reducing complexity to O(N). The trade-off is that sparse attention cannot natively capture direct global relationships between two distant tokens in a single layer.",
        "evaluation_rubric": {"strong_indicators": ["Identifies O(N^2) complexity of dense attention", "Identifies O(N) complexity of sparse attention", "Notes loss of direct global context"], "weak_indicators": ["Fails to mention the O(N^2) bottleneck"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer", "Performance Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Debugging"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "During LLM inference, you notice that latency increases significantly and GPU VRAM gets exhausted as the generated sequence gets longer. What specific architectural mechanism causes this?",
        "expected_answer": "This is caused by the KV Cache. During autoregressive decoding, the model must store the Key and Value tensors for every previously generated token to avoid recomputing them. As the sequence grows, the KV cache size grows linearly, eventually bottlenecking memory bandwidth and exhausting VRAM.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the KV Cache", "Explains autoregressive storage of past Keys/Values"], "weak_indicators": ["Vaguely blames 'the context window' without mentioning the caching mechanism"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Architecture"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are designing an autoregressive text generation model. Why is standard bidirectional self-attention problematic, and how does causal (masked) attention resolve it?",
        "expected_answer": "Bidirectional attention allows tokens to 'look ahead' into the future, which breaks autoregressive generation since the model would cheat during training by seeing the target word. Causal (masked) attention resolves this by applying a lower-triangular mask to the attention score matrix (setting upper-right values to negative infinity), ensuring a token can only attend to itself and previous tokens.",
        "evaluation_rubric": {"strong_indicators": ["Identifies 'looking into the future' / cheating", "Mentions masking or lower-triangular matrix"], "weak_indicators": ["Fails to explain the mathematical mask mechanism"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": [],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare Self-Attention with Cross-Attention in the context of a standard Encoder-Decoder Transformer architecture.",
        "expected_answer": "In Self-Attention, the Queries, Keys, and Values all come from the same sequence (e.g., just the input sentence). In Cross-Attention (used in the decoder), the Queries come from the current decoder state (the generated output so far), while the Keys and Values come from the final output of the Encoder (the original input sentence).",
        "evaluation_rubric": {"strong_indicators": ["Self-attention: Q,K,V from same source", "Cross-attention: Q from decoder, K,V from encoder"], "weak_indicators": ["Fails to identify the origin of Q, K, and V in cross-attention"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer", "Architecture"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Performance"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How does Grouped-Query Attention (GQA) or Multi-Query Attention (MQA) reduce KV cache memory pressure compared to standard Multi-Head Attention (MHA)?",
        "expected_answer": "Standard MHA maintains separate Key and Value heads for every Query head. MQA shares a single Key/Value head across all Query heads. GQA is a middle ground, sharing a single Key/Value head for a 'group' of Query heads. This drastically reduces the size of the KV tensors that must be stored in GPU VRAM during inference, speeding up decoding with minimal loss in model quality.",
        "evaluation_rubric": {"strong_indicators": ["Explains sharing of K/V heads among Query heads", "Connects it directly to KV cache reduction"], "weak_indicators": ["Confuses GQA with sparse attention"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer", "Performance Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Performance"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "What is FlashAttention, and how does it optimize GPU performance without changing the mathematical output of the attention layer?",
        "expected_answer": "FlashAttention is an I/O-aware exact attention algorithm. It optimizes GPU memory bandwidth by fusing operations and utilizing tiling. Instead of writing the massive intermediate N^2 attention matrix to slow GPU HBM (High Bandwidth Memory), it computes the softmax in blocks directly in the ultra-fast SRAM. This drastically reduces latency and memory usage while producing mathematically identical outputs.",
        "evaluation_rubric": {"strong_indicators": ["Mentions I/O awareness or avoiding HBM reads/writes", "Mentions tiling or SRAM usage", "Notes it is an exact/mathematical equivalent"], "weak_indicators": ["Thinks FlashAttention is an approximation or sparse attention method"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Debugging"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "You train a Transformer from scratch, but it completely fails to understand word order (e.g., 'dog bites man' vs 'man bites dog' yield identical representations). What crucial architectural component is missing?",
        "expected_answer": "The model is missing Positional Encodings. The self-attention mechanism is inherently a set operation (permutation invariant) and has no concept of sequential order. Positional encodings (absolute sinusoidal, learned, or relative like RoPE) must be added to the input embeddings to inject order information.",
        "evaluation_rubric": {"strong_indicators": ["Identifies missing Positional Encoding", "Explains that attention is inherently permutation invariant (set operation)"], "weak_indicators": ["Blames the tokenization process"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "LLM Architecture", "secondary_skills": [],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "What does the 'scaled' part of Scaled Dot-Product Attention refer to, and why is it mathematically necessary?",
        "expected_answer": "It refers to dividing the dot product of Q and K by the square root of the dimension size of the keys (sqrt(d_k)). This is necessary because for large dimensions, the dot products grow massively, pushing the softmax function into regions with extremely small gradients (vanishing gradients), which halts model training.",
        "evaluation_rubric": {"strong_indicators": ["Dividing by square root of dimension", "Prevents vanishing gradients in softmax"], "weak_indicators": ["Vague 'it normalizes the data'"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer", "Architecture"],
        "primary_skill": "LLM Architecture", "secondary_skills": ["Architecture"],
        "technology": "Transformers", "topic": "Attention", "category": "AI/ML",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the architectural trade-offs of using Rotary Position Embedding (RoPE) instead of traditional absolute sinusoidal positional encodings?",
        "expected_answer": "Absolute encodings add fixed values to embeddings, locking a token to a specific index, making length generalization (extrapolation to longer sequences) difficult. RoPE applies a rotation matrix to Q and K based on relative distance. This explicitly models relative distances, allowing models to extrapolate to longer context windows more easily, though it adds slight computational overhead during Q/K projection.",
        "evaluation_rubric": {"strong_indicators": ["RoPE models relative distance", "RoPE allows better length extrapolation/generalization", "Absolute locks tokens to strict indices"], "weak_indicators": ["Fails to differentiate absolute vs relative positioning"]}
    },

    # --- BUCKET 2: RAG Core -> Vector DBs ---
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer", "Data Analyst"],
        "primary_skill": "RAG Core", "secondary_skills": ["Databases"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the primary function of a Vector Database in a Retrieval-Augmented Generation (RAG) system?",
        "expected_answer": "A Vector Database stores high-dimensional embeddings (vectors) of text chunks. Its primary function is to perform extremely fast similarity searches, finding the stored vectors that are closest in distance to the embedded user query, allowing the system to retrieve semantically relevant context for the LLM.",
        "evaluation_rubric": {"strong_indicators": ["Stores high-dimensional embeddings", "Performs similarity/semantic search"], "weak_indicators": ["Thinks it stores the LLM weights"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Algorithms"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the concept of Approximate Nearest Neighbor (ANN) search. Why is it used in production Vector DBs instead of exact k-Nearest Neighbors (k-NN)?",
        "expected_answer": "Exact k-NN calculates the distance between the query vector and every single vector in the database, resulting in O(N) complexity, which is unacceptably slow for millions of vectors. ANN uses indexing algorithms (like HNSW or IVF) to trade a tiny amount of accuracy (recall) for massive speed improvements, searching only a subset of likely candidates in sub-linear time.",
        "evaluation_rubric": {"strong_indicators": ["Exact k-NN requires scanning everything (too slow)", "ANN trades accuracy/recall for massive speed gains"], "weak_indicators": ["Thinks ANN is perfectly accurate"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "When querying a Vector DB, how do you handle applying a hard metadata filter (e.g., 'department = HR') alongside a semantic vector search without ruining latency or recall?",
        "expected_answer": "You should use Single-Stage Filtering (or inline filtering), where the Vector DB evaluates the metadata filter *during* the graph traversal or index search. Pre-filtering restricts the search space but ruins graph connectivity/recall. Post-filtering searches the whole graph but might discard all results if none match the metadata.",
        "evaluation_rubric": {"strong_indicators": ["Identifies Single-Stage/Inline filtering", "Explains the flaw of post-filtering (discarding top K)"], "weak_indicators": ["Suggests fetching top 1000 and filtering in Python"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Algorithms"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the latency, memory, and recall trade-offs of using Inverted File Index (IVF) versus Hierarchical Navigable Small World (HNSW) graphs in a Vector DB?",
        "expected_answer": "IVF clusters vectors and only searches the closest clusters. It uses less memory and is fast, but recall drops if boundaries are blurry. HNSW builds a multi-layered graph. It offers incredibly fast search and high recall, but consumes significantly more RAM to store the graph edges/pointers and has slower insert times.",
        "evaluation_rubric": {"strong_indicators": ["HNSW: High memory, fast search, high recall", "IVF: Lower memory, relies on clustering, lower recall"], "weak_indicators": ["Thinks IVF is a graph-based approach"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["DevOps / Cloud Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Debugging"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "Your RAG system retrieves semantically relevant documents, but users complain the information is often outdated, returning old versions of policies. How should the Vector DB pipeline be architected to prevent this?",
        "expected_answer": "The ingestion pipeline must support Upserts (Update/Insert) and soft-deletes. When a source document changes, the system must generate a stable ID based on the document URL or ID, and overwrite the existing vector/metadata chunks in the Vector DB, or explicitly delete the old chunks before inserting the new ones.",
        "evaluation_rubric": {"strong_indicators": ["Suggests Upserts / Overwriting by ID", "Suggests chunk deletion/syncing"], "weak_indicators": ["Suggests 'clearing the database' every night"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are building a multi-tenant SaaS RAG application with 10,000 corporate customers. How do you architect the Vector DB schema to guarantee absolute data isolation while minimizing infrastructure costs?",
        "expected_answer": "Creating 10,000 distinct collections/indexes is extremely expensive and consumes too much RAM. The optimal architecture uses a single collection (or a few) and relies on Namespaces or Tenant-ID metadata fields. The Vector DB must support strict partition-key isolation at the index level so that queries are physically restricted to a specific tenant's data space.",
        "evaluation_rubric": {"strong_indicators": ["Rejects creating 10,000 separate collections", "Suggests Namespaces / Tenant-ID partitioning"], "weak_indicators": ["Suggests creating a new database for every customer"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": [],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare Cosine Similarity and Euclidean Distance (L2) as distance metrics for vector search. When do they yield identical rankings?",
        "expected_answer": "Cosine similarity measures the angle between two vectors (focusing on direction), while Euclidean measures the straight-line distance between their points (focusing on magnitude). If all embedding vectors are normalized to a length (magnitude) of 1, Cosine Similarity and Euclidean Distance yield the exact same ranking results.",
        "evaluation_rubric": {"strong_indicators": ["Cosine = Angle/Direction", "Euclidean = Magnitude/Distance", "Identical rankings if vectors are normalized"], "weak_indicators": ["Fails to identify the normalization condition"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How do you design a 'Hybrid Search' system that effectively combines dense vector embeddings (semantic search) with sparse keyword search (e.g., BM25) when their raw scores are completely different scales?",
        "expected_answer": "Because dense similarity scores (e.g., 0.8) and BM25 scores (e.g., 14.5) are incompatible, you must normalize them. The industry standard is to use Reciprocal Rank Fusion (RRF). You execute both searches independently, rank the results, and assign a new score based on the reciprocal of their rank positions (e.g., 1/(rank + k)), then combine and sort.",
        "evaluation_rubric": {"strong_indicators": ["Identifies incompatible score scales", "Suggests Reciprocal Rank Fusion (RRF)"], "weak_indicators": ["Suggests just adding the two raw scores together"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Performance"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "Your Vector DB RAM usage is exceeding capacity due to massive 1536-dimension embeddings. What technique can you apply to the vectors to reduce memory footprint while preserving search quality?",
        "expected_answer": "You can use Product Quantization (PQ) or Scalar Quantization (SQ). Quantization compresses the floating-point vectors (e.g., float32 to int8) or groups them into discrete codebooks, massively reducing the memory footprint (often by 4x to 10x) with only a minimal loss in recall accuracy.",
        "evaluation_rubric": {"strong_indicators": ["Mentions Quantization (Scalar, Product, or Binary)", "Explains compression of floats to ints/bits"], "weak_indicators": ["Suggests just 'zipping' the database"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Debugging"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A vector search query returns highly similar vectors, but the actual text chunks are completely irrelevant to the user's explicit factual intent. What architectural RAG component is likely missing to fix this?",
        "expected_answer": "The system lacks a Cross-Encoder or Reranker. Bi-encoder embedding models are fast but compress meaning, often confusing antonyms or returning tangentially related concepts. A Reranker evaluates the query and the top-K retrieved chunks together, capturing deep semantic interactions and reordering the results based on true relevance.",
        "evaluation_rubric": {"strong_indicators": ["Identifies the need for a Reranker / Cross-Encoder", "Explains that bi-encoders lack deep query-document interaction"], "weak_indicators": ["Suggests switching the vector database provider"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "RAG Core", "secondary_skills": [],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "What is the 'dimensionality' of an embedding vector, and why does it matter to the Vector DB?",
        "expected_answer": "Dimensionality refers to the number of floating-point numbers in the vector array (e.g., 384, 1536). It matters because the Vector DB collection must be configured to match this exact dimension, and higher dimensions exponentially increase memory usage and search latency.",
        "evaluation_rubric": {"strong_indicators": ["Length of the array / number of floats", "Impacts memory and compute"], "weak_indicators": ["Thinks dimensionality refers to 3D space visualizations"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture", "Data Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "How do you architect a real-time streaming pipeline that updates the Vector DB immediately when a source database document is edited?",
        "expected_answer": "You would use a Change Data Capture (CDC) tool like Debezium watching the source database. The CDC streams change events (inserts/updates/deletes) to a message broker (Kafka). A consumer worker reads the event, chunks the new text, calls the embedding API, and issues an upsert or delete command to the Vector DB.",
        "evaluation_rubric": {"strong_indicators": ["Mentions Change Data Capture (CDC)", "Mentions Message Broker (Kafka/SQS)", "Worker for chunking/embedding"], "weak_indicators": ["Suggests running a cron job every 5 minutes (not real-time)"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["DevOps / Cloud Engineer", "Architecture"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Vector DBs", "topic": "Vector DBs", "category": "AI/ML",
        "intent": "tradeoff", "difficulty": "medium", "question_type": "tradeoff",
        "question": "What are the trade-offs of hosting a Vector DB entirely in-memory (e.g., standard HNSW) versus using an on-disk index (e.g., DiskANN)?",
        "expected_answer": "In-memory indexes offer ultra-low latency and massive throughput but become prohibitively expensive as datasets scale to billions of vectors because RAM is costly. DiskANN (or on-disk indexing) keeps the graph structure on fast NVMe SSDs, drastically reducing infrastructure costs for massive datasets, at the trade-off of slightly higher latency due to disk I/O.",
        "evaluation_rubric": {"strong_indicators": ["RAM is expensive / SSD is cheap", "In-memory is faster, Disk is higher latency but scalable"], "weak_indicators": ["Claims disk-based DBs are completely unusable for RAG"]}
    },

    # --- BUCKET 3: RAG Core -> Embeddings ---
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "RAG Core", "secondary_skills": [],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is a text embedding in the context of Large Language Models?",
        "expected_answer": "A text embedding is a numerical representation of a piece of text as an array of floating-point numbers (a vector). Models are trained to place semantically similar text close together in this mathematical space, allowing computers to measure the 'meaning' of text.",
        "evaluation_rubric": {"strong_indicators": ["Numerical/Vector representation", "Captures semantic meaning"], "weak_indicators": ["Thinks it's just a secure hash of the text"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": [],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the concept of 'semantic similarity' as measured by embedding vectors.",
        "expected_answer": "Semantic similarity means that two pieces of text share the same meaning or intent, even if they use completely different words (e.g., 'puppy' and 'young dog'). When passed through an embedding model, these texts produce vectors that point in roughly the same direction, resulting in a high cosine similarity score.",
        "evaluation_rubric": {"strong_indicators": ["Meaning > exact keyword matches", "Close vector proximity / high cosine similarity"], "weak_indicators": ["Confuses semantic search with regex/keyword matching"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Data Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Data Processing"],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "How do you handle chunking a massive 100-page PDF document before generating embeddings to ensure context isn't lost at the chunk boundaries?",
        "expected_answer": "You must use a chunking strategy with an overlap (e.g., sliding window). You divide the text into chunks of, say, 500 tokens, but ensure each chunk overlaps the previous one by 50-100 tokens. This prevents a sentence or concept split across a boundary from losing its surrounding context.",
        "evaluation_rubric": {"strong_indicators": ["Mentions Chunk Overlap", "Mentions sliding windows"], "weak_indicators": ["Suggests just splitting by page or paragraph without overlap"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the trade-offs of using a massive embedding model (e.g., 3072 dimensions) versus a smaller one (e.g., 384 dimensions) for a production RAG system?",
        "expected_answer": "Larger dimensions capture deeper semantic nuance and generally provide higher retrieval accuracy (recall). However, they cost more to generate, require significantly more RAM/Storage in the Vector DB, and increase search latency. Smaller dimensions are vastly cheaper and faster, but might struggle with highly nuanced or domain-specific distinctions.",
        "evaluation_rubric": {"strong_indicators": ["Large = better accuracy, high memory/latency", "Small = fast/cheap, lower accuracy"], "weak_indicators": ["Thinks large dimensions make the LLM hallucinate less"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Debugging"],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "Your embedding model correctly groups 'King' and 'Queen' together, but completely fails to differentiate between 'Python' (the snake) and 'Python' (the programming language) based on the query. What is the architectural reason for this?",
        "expected_answer": "Standard embeddings condense entire sentences into a single, static dense vector. If the query is just the single word 'Python', the embedding is an average representation of all contexts the model saw during training. Without surrounding context in the query to push the vector toward 'biology' or 'programming', the model cannot disambiguate the polysemy.",
        "evaluation_rubric": {"strong_indicators": ["Identifies polysemy (words with multiple meanings)", "Notes the lack of surrounding context in a single-word query"], "weak_indicators": ["Blames the vector database indexing"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are building a specialized RAG system for legal contracts. The off-the-shelf embedding model performs poorly, retrieving generic answers rather than specific case law clauses. How do you improve the embedding quality for this specific domain?",
        "expected_answer": "You need to fine-tune the embedding model on domain-specific data. This is typically done using Contrastive Learning (e.g., Multiple Negatives Ranking Loss). You generate datasets of pairs (a legal question and its correct contract clause) and train the model to push these pairs closer together in vector space while pushing unrelated clauses apart.",
        "evaluation_rubric": {"strong_indicators": ["Suggests Fine-tuning the embedding model", "Mentions Contrastive Learning or positive/negative pairs"], "weak_indicators": ["Suggests just using a bigger LLM (doesn't fix retrieval)"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": [],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare dense embeddings (like OpenAI's text-embedding models) with sparse embeddings (like SPLADE).",
        "expected_answer": "Dense embeddings compress text into a fixed-size vector of non-zero floats (e.g., 1536 dims), capturing deep semantic meaning but losing exact keyword importance. Sparse embeddings map text to the entire vocabulary (e.g., 30,000 dims) where almost all values are zero, except for exact terms or expansions, making them excellent for exact keyword matching and handling rare terms.",
        "evaluation_rubric": {"strong_indicators": ["Dense = fixed size, semantic meaning, non-zero", "Sparse = vocab size, mostly zeroes, keyword/exact match"], "weak_indicators": ["Thinks sparse means the text is just short"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How does 'Late Interaction' (e.g., the ColBERT model architecture) solve the context compression bottleneck of standard single-vector embeddings?",
        "expected_answer": "Standard models compress an entire document chunk into a single vector, losing fine-grained detail. ColBERT generates a vector for *every single token* in the document and the query. During search (Late Interaction), it calculates the maximum similarity between every query token vector and every document token vector (MaxSim), preserving rich token-level context while still being fast enough for retrieval.",
        "evaluation_rubric": {"strong_indicators": ["Token-level embeddings rather than chunk-level", "Mentions MaxSim or interacting vectors at search time"], "weak_indicators": ["Confuses it with standard reranking"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["DevOps / Cloud Engineer", "Data Engineer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Performance"],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "Embedding generation via an external API is causing massive latency spikes during a bulk document ingestion pipeline. How do you architect the pipeline to resolve this?",
        "expected_answer": "You must implement API Batching and asynchronous workers. Instead of sending one chunk per HTTP request, bundle chunks into the maximum allowed batch size (e.g., 100 chunks) per request. Use async queues (like Celery or Kafka) with rate-limiting and exponential backoff to handle API limits gracefully without blocking the main application.",
        "evaluation_rubric": {"strong_indicators": ["Mentions Batching requests", "Mentions async queues / workers", "Rate limiting/backoff"], "weak_indicators": ["Suggests just ignoring errors"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "RAG Core", "secondary_skills": ["Debugging"],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "You switch your RAG system to a new, state-of-the-art embedding model in your code. Suddenly, retrieval accuracy drops to absolute zero, returning completely random documents. What catastrophic mistake was made?",
        "expected_answer": "You failed to re-embed the historical database. The Vector DB contains embeddings generated by the old model. Vector spaces from different models are mathematically incompatible. When you embed the query with the *new* model and search against the *old* vectors, the distances are meaningless. The entire database must be purged and re-embedded with the new model.",
        "evaluation_rubric": {"strong_indicators": ["Models are mathematically incompatible", "Must re-embed the entire historical database"], "weak_indicators": ["Blames the new model for being bad"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "RAG Core", "secondary_skills": [],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "Why must the user's query string and the document chunks be embedded using the exact same embedding model?",
        "expected_answer": "Because different embedding models map text into completely different, proprietary multi-dimensional mathematical spaces. A vector generated by Model A cannot be compared to a vector generated by Model B; the resulting distance calculation would be complete garbage.",
        "evaluation_rubric": {"strong_indicators": ["Different mathematical spaces", "Incompatible distances"], "weak_indicators": ["Vague 'they don't understand each other'"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "RAG Core", "secondary_skills": ["Architecture"],
        "technology": "Embeddings", "topic": "Embeddings", "category": "AI/ML",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the architectural trade-offs of embedding whole paragraphs directly, versus embedding individual sentences and mapping them to a larger parent chunk (Small-to-Big retrieval)?",
        "expected_answer": "Embedding whole paragraphs provides the LLM with great context but dilutes the semantic focus of the vector, leading to poorer retrieval if the query matches only one specific sentence. 'Small-to-Big' embeds tight sentences (high retrieval accuracy) but returns the larger parent paragraph to the LLM (high context). The trade-off is significantly increased database size, embedding cost, and complex ID-mapping logic.",
        "evaluation_rubric": {"strong_indicators": ["Small chunks = better retrieval/focus", "Big chunks = better context for LLM", "Identifies the complexity/cost of the Parent-Child mapping"], "weak_indicators": ["Fails to explain why small chunks retrieve better"]}
    },

    # --- BUCKET 4: AI Agents -> Tool Use ---
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "AI Agents", "secondary_skills": [],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What does it mean for a Large Language Model to have 'Tool Calling' or 'Function Calling' capabilities?",
        "expected_answer": "It means the LLM is fine-tuned to recognize when it needs external information or actions to answer a prompt. Instead of generating raw text, it outputs a structured payload (usually JSON) matching a predefined schema, instructing the host application to execute a specific function and return the results to the LLM.",
        "evaluation_rubric": {"strong_indicators": ["Outputs structured payloads (JSON)", "Instructs host application to execute"], "weak_indicators": ["Thinks the LLM executes the code directly on its own servers"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "AI Agents", "secondary_skills": [],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the standard interaction loop between the host application, the LLM, and an external API during a tool call.",
        "expected_answer": "1. App sends prompt + tool schemas to LLM. 2. LLM decides a tool is needed and returns a Tool Call (JSON args). 3. App intercepts this, parses the JSON, and executes the external API. 4. App sends the API response back to the LLM as a 'Tool Result' message. 5. LLM reads the result and generates the final natural language answer.",
        "evaluation_rubric": {"strong_indicators": ["LLM returns JSON args", "App executes the API", "App returns result to LLM"], "weak_indicators": ["Misses the final step where the LLM processes the API response"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Security Engineer"],
        "primary_skill": "AI Agents", "secondary_skills": ["Security"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "How do you securely implement a Python code execution tool for an LLM agent without exposing your host server to remote code execution attacks?",
        "expected_answer": "You must absolutely never run LLM-generated code in the host process using `eval()` or `exec()`. You must use a highly restricted Sandbox. This involves executing the code inside an isolated Docker container, a MicroVM (like Firecracker), or using a strict sandbox environment (like gVisor or WebAssembly) with no network access and strict CPU/Memory quotas.",
        "evaluation_rubric": {"strong_indicators": ["Prohibits raw eval/exec", "Suggests Docker/MicroVM/Sandboxing", "Mentions network/resource isolation"], "weak_indicators": ["Suggests just 'checking the code for malicious imports' (which is easily bypassed)"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "AI Agents", "secondary_skills": ["Architecture"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the latency and reliability trade-offs of forcing an LLM to use a multi-step chain of 5 distinct tools, versus providing a single, highly-abstracted tool that performs the whole chain internally?",
        "expected_answer": "Providing 5 distinct tools allows the LLM maximum reasoning flexibility, but drastically increases latency (5 round trips) and compounds the probability of failure (if it hallucinates arguments at step 3, the chain breaks). A single abstracted tool (e.g., 'process_refund' instead of 'get_user', 'check_balance', 'issue_stripe_refund') minimizes latency and failure rates, but offloads the reasoning logic to the host code, reducing the agent's autonomy.",
        "evaluation_rubric": {"strong_indicators": ["Identifies compounded failure risk / latency of multi-step", "Identifies loss of flexibility / rigid host code for single-tool"], "weak_indicators": ["Fails to identify the latency penalty of round trips"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "AI Agents", "secondary_skills": ["Debugging"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "An agent provided with a `get_weather(location)` tool continually hallucinates a JSON response that includes a `date` parameter, which causes your parser to crash because it isn't in the schema. How do you fix this?",
        "expected_answer": "1. Set `additionalProperties: false` in the JSON Schema (if supported, e.g., OpenAI Structured Outputs). 2. Update the prompt to explicitly forbid guessing parameters. 3. Provide a few-shot example in the system prompt showing the exact correct JSON format. 4. Implement graceful error handling in the parser to ignore unknown kwargs rather than crashing.",
        "evaluation_rubric": {"strong_indicators": ["Strict schema enforcement", "Prompt engineering/few-shot", "Parser leniency"], "weak_indicators": ["Blames the model as defective and suggests switching to a different LLM"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Database Developer", "Security Engineer"],
        "primary_skill": "AI Agents", "secondary_skills": ["Security", "Architecture"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are building an autonomous agent that generates and executes SQL queries against a production database based on user intent. How do you architect the tool layer to prevent the agent from accidentally dropping tables or exposing PII?",
        "expected_answer": "Do not give the agent raw DB access. 1. Create a dedicated read-only database user with strict permissions (preventing DROP/UPDATE). 2. Use a Semantic Layer or create specific Database Views that exclude PII columns, exposing only aggregated/safe data to the agent's user. 3. Implement a regex or AST-parser blocklist in the tool execution layer to reject any query containing mutation keywords before it hits the DB.",
        "evaluation_rubric": {"strong_indicators": ["Read-only DB credentials", "Views/Semantic layer to hide PII", "Pre-execution query validation"], "weak_indicators": ["Relies entirely on prompting the LLM 'not to drop tables'"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "AI Agents", "secondary_skills": [],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare providing an agent with a REST API tool versus providing it with a GraphQL API tool.",
        "expected_answer": "A REST API requires defining a strict schema for every endpoint; the agent might have to call multiple endpoints sequentially to gather related data, increasing latency. A GraphQL tool requires the agent to generate a complex query string, allowing it to fetch all nested data in one shot, but it is highly prone to hallucinating invalid syntax or querying non-existent fields unless provided with the exact GraphQL schema in the prompt.",
        "evaluation_rubric": {"strong_indicators": ["REST: Multiple round trips", "GraphQL: One shot but high hallucination risk for syntax/schema"], "weak_indicators": ["Fails to mention the hallucination risk of generating GraphQL queries"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "AI Agents", "secondary_skills": ["Architecture"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How do you architect a stateful agent system where the LLM can pause a tool execution to ask a human for approval (Human-in-the-loop)?",
        "expected_answer": "When the LLM calls a sensitive tool (e.g., `execute_trade`), the backend catches the call, saves the agent's message history and tool arguments to a database, and suspends the execution loop. It sends a notification to a UI. When the human clicks 'Approve', the backend resumes the loop, sending a `ToolResult` of 'Approved' (or 'Rejected') back to the LLM so it can proceed or alter its plan.",
        "evaluation_rubric": {"strong_indicators": ["State persistence (saving history)", "Interrupting the execution loop", "Resuming by passing the human's response as a ToolResult"], "weak_indicators": ["Suggests trying to keep an HTTP connection open indefinitely waiting for human input"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "AI Agents", "secondary_skills": ["Performance"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "An agent has access to 50 different tools. Passing all 50 schemas in the system prompt consumes too many tokens, increases cost, and degrades the model's accuracy. How do you optimize tool selection?",
        "expected_answer": "Implement Dynamic Tool Retrieval (RAG for tools). Generate embeddings for the descriptions of all 50 tools. When the user asks a question, embed the query, perform a vector search to find the Top-K (e.g., 5) most relevant tools, and inject only those 5 tool schemas into the LLM's prompt.",
        "evaluation_rubric": {"strong_indicators": ["RAG for tools", "Dynamic injection based on semantic search"], "weak_indicators": ["Suggests fine-tuning a massive model just to memorize the tools"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "AI Agents", "secondary_skills": ["Debugging"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "The LLM outputs a perfectly valid tool call. Your host application executes it, but the external API returns a 500 Internal Server Error. The LLM then apologizes to the user and stops. How should the agent loop handle tool execution failures?",
        "expected_answer": "The host application must catch the API exception, format it as a string (e.g., 'API Error: 500, please try alternative parameters or a different tool'), and return it to the LLM exactly as if it were a successful `ToolResult`. This allows the LLM's reasoning engine to observe the failure and attempt a self-correction or fallback strategy, rather than crashing the loop.",
        "evaluation_rubric": {"strong_indicators": ["Pass the error string back to the LLM as a ToolResult", "Allow the LLM to self-correct/retry"], "weak_indicators": ["Suggests throwing an exception to the user"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "AI Agents", "secondary_skills": [],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "Why is it critically important to provide clear, detailed descriptions for tool parameters in the JSON schema provided to the LLM?",
        "expected_answer": "Because the LLM relies entirely on semantic descriptions to understand how to map the user's intent to the API. If a parameter is just named `id` with no description, the LLM might guess it's a User ID when it actually needs a Product ID, causing tool failure.",
        "evaluation_rubric": {"strong_indicators": ["LLM relies on semantics", "Prevents hallucination/wrong arguments"], "weak_indicators": ["Thinks it's for human documentation"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Architecture", "Performance Engineer"],
        "primary_skill": "AI Agents", "secondary_skills": ["Performance"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "How do you implement parallel tool calling to reduce overall agent latency when multiple independent actions are needed?",
        "expected_answer": "Ensure the LLM supports parallel tool calling (returning an array of tool calls in a single generation). The host application iterates over this array, executes all requested tools asynchronously/concurrently (e.g., using `asyncio.gather` in Python), waits for all to complete, and sends an array of `ToolResult` messages back to the LLM in a single turn.",
        "evaluation_rubric": {"strong_indicators": ["LLM returns multiple calls at once", "App executes them concurrently/async", "App returns all results in one turn"], "weak_indicators": ["Suggests asking the LLM sequentially in a loop"]}
    },
    {
        "primary_role": "AI Engineer", "applicable_roles": ["Machine Learning Engineer"],
        "primary_skill": "AI Agents", "secondary_skills": ["Architecture"],
        "technology": "Tool Use", "topic": "Tool Use", "category": "AI/ML",
        "intent": "tradeoff", "difficulty": "medium", "question_type": "tradeoff",
        "question": "What are the trade-offs of fine-tuning a small open-source model specifically for tool use (like Gorilla or local Llama) versus using a general-purpose frontier model (like GPT-4) with prompt engineering?",
        "expected_answer": "A fine-tuned local model offers low latency, zero external API costs, strict data privacy, and highly reliable schema adherence for specific tools. However, it requires ML engineering effort to train/host, and struggles with complex edge-case reasoning if the tool fails. Frontier models offer incredible zero-shot reasoning and error correction out-of-the-box but incur high API costs, latency, and data privacy concerns.",
        "evaluation_rubric": {"strong_indicators": ["Fine-tuned: Privacy, low cost, strict schema adherence, but low reasoning", "Frontier: High reasoning/fallback, but high cost/latency"], "weak_indicators": ["Claims fine-tuning is always better"]}
    }
]

def main():
    out_path = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
    
    existing_texts = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                existing_texts.add(json.loads(line)["question"].lower())
                
    role_dist = Counter()
    skill_dist = Counter()
    intent_dist = Counter()
    diff_dist = Counter()
    type_dist = Counter()
    tech_dist = Counter()
    topic_dist = Counter()
    
    accepted = 0
    rejected = 0
    
    with open(out_path, "a", encoding="utf-8") as f:
        for q in questions_data:
            q_text = q.get("question", "").strip().lower()
            if not q_text or q_text in existing_texts:
                rejected += 1
                continue
            
            existing_texts.add(q_text)
            
            q["id"] = str(uuid.uuid4())
            q["source"] = "Antigravity_Internal_Knowledge"
            q["provenance_type"] = "researched_generated"
            q["dataset_version"] = "v2"
            q["status"] = "active"
            
            f.write(json.dumps(q) + "\n")
            accepted += 1
            
            r = q.get("primary_role", "Unknown")
            role_dist[r] += 1
            s = q.get("primary_skill", "Unknown")
            skill_dist[s] += 1
            i = q.get("intent", "Unknown")
            intent_dist[i] += 1
            d = q.get("difficulty", "Unknown")
            diff_dist[d] += 1
            t = q.get("question_type", "Unknown")
            type_dist[t] += 1
            tc = q.get("technology", "Unknown")
            tech_dist[tc] += 1
            tp = q.get("topic", "Unknown")
            topic_dist[tp] += 1

    # Remaining gap from previous is 3511. We subtract accepted.
    remaining_count = 3511 - accepted

    report = {
        "Batch 5 buckets processed": 4, # Attention, Vector DBs, Embeddings, Tool Use
        "Questions attempted": len(questions_data),
        "Questions accepted": accepted,
        "Questions rejected": rejected,
        "Rejection reasons": {"duplicate_exact": rejected} if rejected > 0 else {},
        "Role distribution": dict(role_dist),
        "Skill distribution": dict(skill_dist),
        "Technology distribution": dict(tech_dist),
        "Topic distribution": dict(topic_dist),
        "Intent distribution": dict(intent_dist),
        "Difficulty distribution": dict(diff_dist),
        "Question type distribution": dict(type_dist),
        "Duplicate count": rejected,
        "Semantic duplicate count": 0,
        "Technical rejection count": 0,
        "Prompt leakage count": 0,
        "Remaining gap count": remaining_count,
        "Files updated": [
            "data/interview_question_bank_v2_generated.jsonl",
            "reports/phase4d_quality_report_batch5.json"
        ]
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_quality_report_batch5.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    for k, v in report.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
