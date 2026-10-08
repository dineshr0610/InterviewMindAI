"""Batch 31 Part 1 question content (ML Engineer). Targeted Gap Generation."""

ROLE = "ML Engineer"

BUCKET_KEYS = {
    "DEEP_LEARNING": ("Deep Learning", "Neural Network Optimization", "PyTorch/TensorFlow", ["ML Engineer", "Data Scientist", "AI Engineer"]),
}

Q = [
# ---------------- DEEP_LEARNING ----------------
("DEEP_LEARNING", "scenario", "medium", "scenario", ["Optimization", "Gradients"],
 "You are training a deep ResNet for image classification. After the first epoch, the training loss immediately goes to `NaN` (Not a Number). You verify that your input data contains no `NaN` values. What is the most likely mathematical cause of this during backpropagation, and what is the standard fix?",
 "This is caused by the Exploding Gradient problem. The gradients multiply exponentially during backpropagation through deep layers, eventually causing a numerical overflow to `NaN` or `Inf`. The standard fix is to implement Gradient Clipping (e.g., `torch.nn.utils.clip_grad_norm_`) which explicitly caps the maximum norm of the gradients before the optimizer step.",
 ["Exploding Gradient problem", "Gradients multiply exponentially and cause numerical overflow to `NaN`", "Fix: Implement Gradient Clipping (`clip_grad_norm_`) to cap the gradient size"],
 ["The model realized it is a computer program and crashed on purpose"]),

("DEEP_LEARNING", "debug", "hard", "debugging", ["Distributed Training", "PyTorch"],
 "You are training a massive Transformer model using Data Parallelism across 8 GPUs. You notice GPU 0 is pinned at 100% memory utilization and eventually OOMs, while GPUs 1 through 7 are sitting at 40% memory utilization. What architectural configuration error in PyTorch caused this severe imbalance?",
 "You likely used `torch.nn.DataParallel` (DP) instead of `torch.nn.parallel.DistributedDataParallel` (DDP). DP operates on a single process with multi-threading and forces GPU 0 to aggregate all gradients, calculate the loss, and broadcast the updated weights back to the other GPUs on every step, massively overloading it. DDP uses multi-processing and synchronizes via All-Reduce.",
 ["Used legacy `DataParallel` (DP) instead of `DistributedDataParallel` (DDP)", "DP forces GPU 0 to aggregate all gradients and broadcast weights, overloading its memory", "DDP uses multi-processing and synchronizes via distributed All-Reduce"],
 ["GPU 0 is just naturally greedier than the other GPUs"]),

("DEEP_LEARNING", "tradeoff", "medium", "tradeoff", ["Normalization"],
 "What is the engineering tradeoff between using Batch Normalization (BatchNorm) versus Layer Normalization (LayerNorm) in a Deep Learning architecture?",
 "BatchNorm normalizes across the batch dimension; it requires running statistics and fails catastrophically if the batch size is too small (e.g., batch size 1 during inference). LayerNorm normalizes across the feature/channel dimension for each individual sample independently, completely ignoring batch size. LayerNorm is strictly required for variable-length sequence tasks (Transformers), but BatchNorm often provides better regularization for static CNNs.",
 ["BatchNorm: Normalizes across the batch. Fails if batch size is too small (e.g., inference).", "LayerNorm: Normalizes across the feature dimension per sample. Independent of batch size.", "Tradeoff: LayerNorm is required for sequence tasks (Transformers); BatchNorm is better for CNN regularization."],
 ["BatchNorm uses a physical batch of files, LayerNorm uses digital layers"]),

("DEEP_LEARNING", "explain", "easy", "concept", ["Transformers", "Positional Encoding"],
 "Explain the purpose of 'Positional Encoding' in a Transformer architecture.",
 "Unlike RNNs which process tokens sequentially, Transformers process all tokens in a sequence completely in parallel via self-attention. This means the model inherently has no concept of token order. Positional Encoding injects deterministic mathematical vectors (like sines/cosines) into the input embeddings, providing the model with a unique continuous signal representing the absolute and relative position of each token.",
 ["Transformers process all tokens in parallel via self-attention, lacking inherent sequential awareness", "Positional Encoding injects vectors (e.g., sines/cosines) into the input embeddings", "Provides the model a signal representing the absolute and relative position of each token"],
 ["It encodes the physical GPS position of the server running the model"]),

("DEEP_LEARNING", "implement", "hard", "implementation", ["PEFT", "LoRA"],
 "You want to perform Parameter-Efficient Fine-Tuning (PEFT) on a massive 70B parameter model using LoRA (Low-Rank Adaptation). How does LoRA mathematically freeze the original model while still allowing it to learn new tasks without requiring 70B trainable parameters?",
 "LoRA freezes all the original pre-trained dense weight matrices ($W$). It then injects trainable rank-decomposition matrices ($A$ and $B$) in parallel. The forward pass computes $h = Wx + BAx$. Because $A$ and $B$ are extremely low-rank (e.g., rank 8), they contain less than 1% of the original parameters. Only $A$ and $B$ are updated during backprop, massively reducing optimizer memory requirements.",
 ["Freezes the original pre-trained dense weight matrices", "Injects trainable rank-decomposition matrices ($A$ and $B$) in parallel", "Because $A$ and $B$ are extremely low-rank, they contain a tiny fraction of parameters to update"],
 ["LoRA deletes 99% of the model's brain to make it run faster"]),

("DEEP_LEARNING", "tradeoff", "hard", "tradeoff", ["Mixed Precision", "Memory"],
 "When training deep networks, what is the tradeoff of using standard 32-bit floating point (FP32) versus Mixed Precision Training (FP16/BF16)?",
 "Standard FP32 provides immense numerical stability and eliminates underflow risks, but consumes massive GPU memory and slows down matrix math. Mixed Precision stores weights/activations in FP16 (doubling batch size and utilizing fast Tensor Cores), while keeping a master copy in FP32 for the optimizer. The tradeoff is you must implement Dynamic Loss Scaling to prevent tiny FP16 gradients from underflowing to zero.",
 ["FP32: Numerically stable, but consumes massive VRAM and is slower", "Mixed Precision (FP16): Halves memory, uses Tensor Cores, but risks numerical underflow", "Tradeoff: Mixed precision strictly requires Dynamic Loss Scaling to prevent gradients from underflowing to zero"],
 ["FP16 literally cuts the GPU in half with a saw"]),

("DEEP_LEARNING", "debug", "medium", "debugging", ["Vanishing Gradients"],
 "A deep 50-layer Multi-Layer Perceptron (MLP) without residual connections refuses to converge. The loss doesn't become `NaN`, it just stagnates at the initial random baseline. You check the gradients at the very first layer and find they are infinitely close to zero. What is this phenomenon called?",
 "This is the Vanishing Gradient problem. During backpropagation, the gradients are repeatedly multiplied by small weight values and the derivative of the activation function (like Sigmoid or Tanh, whose derivatives are < 1). By the time the gradient reaches the early layers, it has exponentially decayed to near zero, meaning the early layers literally cannot learn or update their weights.",
 ["The Vanishing Gradient problem", "Gradients are repeatedly multiplied by small derivatives (e.g., Sigmoid < 1) during backprop", "They exponentially decay to near zero, preventing early layers from updating their weights"],
 ["The gradients went on vacation and forgot to update the weights"]),

("DEEP_LEARNING", "fundamentals", "easy", "concept", ["Residual Connections"],
 "In deep learning, what is a 'Residual Connection' (or Skip Connection)?",
 "A residual connection is an architectural feature where the input to a layer is added directly to the output of a deeper layer (e.g., $F(x) + x$). This creates a completely unobstructed mathematical shortcut path for gradients to flow backward through the network during backpropagation, entirely bypassing the non-linear transformations and directly solving the vanishing gradient problem in extremely deep networks.",
 ["Adds the input of a layer directly to the output of a deeper layer ($F(x) + x$)", "Creates an unobstructed shortcut path for gradients during backpropagation", "Directly solves the vanishing gradient problem in extremely deep networks (like ResNets)"],
 ["It is a physical wire connecting the front of the GPU to the back"]),

("DEEP_LEARNING", "scenario", "medium", "scenario", ["Transfer Learning", "Catastrophic Forgetting"],
 "You are fine-tuning a pre-trained image classification model on a very small dataset of medical X-rays. You unfreeze all 100 layers and train with a high learning rate. After 5 epochs, accuracy drops to 0% on both train and validation sets. What failure mode occurred?",
 "This is 'Catastrophic Forgetting' or representation collapse. By unfreezing the entire network and using a high learning rate on a tiny dataset, the aggressive gradient updates completely destroyed the rich, generalized feature extractors (like edge detectors) learned during massive pre-training. You should have frozen the early layers and only trained the final classification head with a small learning rate.",
 ["'Catastrophic Forgetting' or representation collapse", "Aggressive gradients from the high learning rate destroyed the pre-trained feature extractors", "Fix: Freeze early layers and use a very small learning rate for the classification head"],
 ["The model decided medical X-rays were too depressing to look at"]),

("DEEP_LEARNING", "implement", "hard", "implementation", ["Gradient Accumulation"],
 "You are training a massive model that requires a batch size of 256 for mathematical stability, but your GPU can only fit a batch size of 16 without OOMing. How do you engineer the training loop to achieve an effective batch size of 256 without buying more GPUs?",
 "You must implement Gradient Accumulation. You run the forward and backward passes using the micro-batch size of 16. However, you do *not* call `optimizer.step()` or `optimizer.zero_grad()`. You let PyTorch accumulate (sum) the gradients in memory over 16 consecutive micro-batches (16 * 16 = 256). Only on the 16th step do you finally call `optimizer.step()` to update the weights.",
 ["Implement Gradient Accumulation", "Run forward/backward passes on micro-batches (e.g., 16), but DO NOT call `optimizer.step()`", "Accumulate gradients in memory and only call `optimizer.step()` after 16 iterations (16 * 16 = 256)"],
 ["Put the GPU in the freezer to make it run faster"]),

("DEEP_LEARNING", "tradeoff", "medium", "tradeoff", ["Distributed Training"],
 "What is the tradeoff between Model Parallelism (e.g., Tensor Parallelism) and Data Parallelism when scaling deep learning training across multiple GPUs?",
 "Data Parallelism replicates the entire model on every GPU and splits the data batch across them; it is easy to implement and scales perfectly, but fails if the model itself is too large to fit in a single GPU's memory. Model Parallelism shards the actual layers/tensors across multiple GPUs, allowing you to train massive models, but requires complex synchronization (high network overhead) and can severely underutilize GPUs (pipeline bubbles).",
 ["Data Parallelism: Replicates model, splits data. Easy to scale, but fails if model > single GPU memory.", "Model Parallelism: Shards model tensors across GPUs. Allows massive models.", "Model Tradeoff: Requires complex network synchronization and causes GPU underutilization (pipeline bubbles)."],
 ["Data Parallelism forces the GPUs to read binary code out loud"]),

("DEEP_LEARNING", "scenario", "hard", "scenario", ["Transformers", "Positional Encoding"],
 "You implement a complex Transformer model. During training, you notice the validation loss is identical whether you pass in the input sequence correctly (`[A, B, C, D]`) or completely randomly shuffled (`[C, A, D, B]`). What fatal architectural flaw does this indicate?",
 "The model is completely permutation invariant. This strictly indicates that you either forgot to add the Positional Encodings to the input embeddings, or a bug in your code accidentally stripped them before the self-attention layers. Because self-attention inherently treats sequences as unordered sets, without positional encodings, the model physically cannot distinguish sequence order.",
 ["The model is permutation invariant, indicating missing Positional Encodings", "Self-attention inherently treats sequences as unordered mathematical sets", "Without positional encodings added to the embeddings, the model physically cannot distinguish sequence order"],
 ["The model prefers chaos and randomization over order"]),

("DEEP_LEARNING", "explain", "easy", "concept", ["Learning Rate Schedules"],
 "What is the purpose of 'Learning Rate Warmup' in training deep neural networks?",
 "Learning Rate Warmup starts the training process with a very small learning rate (often near zero) and linearly increases it over the first few thousand steps until it reaches the target maximum. This prevents the model from taking massive, erratic gradient steps during the chaotic early phases of training when weights are randomly initialized, stabilizing convergence and preventing early loss spikes or `NaN` errors.",
 ["Starts training with a very small learning rate and linearly increases it to the maximum", "Prevents massive, erratic gradient steps during the chaotic early phases of training", "Stabilizes initial convergence and prevents early loss spikes or `NaN` errors"],
 ["It literally heats up the GPU using a built-in heater"]),

("DEEP_LEARNING", "debug", "medium", "debugging", ["Attention", "Memory"],
 "You are training a sequence model. It runs perfectly with sequence length 512, consuming 80GB of GPU RAM. You increase the sequence length to 1024. Suddenly, memory usage spikes to over 300GB and OOMs. Why did doubling the input size quadruple the memory usage?",
 "This is the quadratic memory complexity ($O(N^2)$) of the standard Self-Attention mechanism. The self-attention matrix calculates the attention score between every token and every other token in the sequence, creating an $N \\times N$ matrix. Therefore, doubling the sequence length ($N$) results in $4\\times$ the memory footprint for the activation tensors that must be stored for backpropagation.",
 ["Standard Self-Attention has a quadratic memory complexity ($O(N^2)$)", "It calculates attention between every token and every other token (an $N \\times N$ matrix)", "Doubling the sequence length quadruples the memory required for activation tensors during backprop"],
 ["The sequence length was too long for the GPU to read without glasses"]),

("DEEP_LEARNING", "implement", "hard", "implementation", ["Checkpointing"],
 "A training script crashes intermittently after 14 hours. You need to implement 'Checkpointing' to perfectly resume training. What specific state artifacts must you explicitly save to disk to resume a PyTorch training loop as if it never crashed?",
 "You cannot just save the model weights (`model.state_dict()`). To perfectly resume the mathematical trajectory, you must also save the optimizer state (`optimizer.state_dict()`, holding momentum buffers), the Learning Rate Scheduler state, the current Epoch/Step number, and the precise Random Number Generator (RNG) states for PyTorch, NumPy, and CUDA to ensure exactly reproducible data shuffling and dropout.",
 ["Model weights (`model.state_dict()`)", "Optimizer state (`optimizer.state_dict()`) and LR Scheduler state", "Random Number Generator (RNG) states for PyTorch/CUDA to guarantee exact data shuffling/dropout reproduction"],
 ["You just save a screenshot of the terminal output"]),

("DEEP_LEARNING", "scenario", "medium", "scenario", ["PyTorch", "Evaluation"],
 "You are fine-tuning a model using PyTorch. You accidentally forget to call `model.eval()` before running the validation loop. The validation metrics are completely untrustworthy. Why did forgetting this single line of code corrupt the validation pass?",
 "`model.eval()` disables training-specific layers like Dropout and Batch Normalization updates. By forgetting it, Dropout continued to randomly zero out activations during validation, adding massive stochastic noise. Furthermore, BatchNorm continued to update its running mean/variance statistics using the validation data, actively corrupting the model's internal state and causing severe data leakage.",
 ["`model.eval()` disables Dropout and Batch Normalization updates", "Dropout added massive stochastic noise to the validation predictions", "BatchNorm updated its running statistics using validation data, causing data leakage and state corruption"],
 ["`model.eval()` turns on the computer monitor so you can see the results"]),

("DEEP_LEARNING", "explain", "easy", "concept", ["Optimization", "Momentum"],
 "In deep learning optimization, what is the role of 'Momentum'?",
 "Momentum is an optimization technique that helps accelerate gradient descent in the relevant direction and dampens oscillations. It does this by adding a fraction of the previous weight update vector to the current update vector. Mathematically, it acts like a heavy ball rolling down the loss landscape, building up speed in consistent directions and powering through shallow local minima or flat plateaus.",
 ["Accelerates gradient descent in consistent directions and dampens oscillations", "Adds a fraction of the previous weight update vector to the current update", "Acts like a heavy ball rolling down a hill, powering through shallow local minima"],
 ["It refers to how fast the engineer can type the Python code"])
]
