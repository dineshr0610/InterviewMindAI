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

ROLE = "DevOps / Cloud Engineer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4c gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    # Group 14: Remaining Deep Operational Topics (11 questions)
    ("B61_14_1", "scenario", "hard", "scenario", ["Cloud Architecture"], "You purchase a 3-year Compute Savings Plan to cover your Kubernetes EC2 instances. However, 6 months later, you migrate the entire cluster to AWS Fargate (Serverless). Your finance team complains that the Savings Plan isn't being utilized and you are losing money. Are they correct, and how does this impact Fargate billing?", "The finance team is incorrect. Unlike 'EC2 Instance Savings Plans', the broader 'Compute Savings Plan' is completely agnostic to the compute platform. It automatically applies its hourly dollar commitment to EC2, AWS Fargate, and AWS Lambda seamlessly across any region or instance family. When the Kubernetes cluster migrated to Fargate, the Compute Savings Plan instantly began applying its discount to the Fargate vCPU and memory hours without any manual intervention.", ["Compute Savings Plans are completely agnostic to the underlying compute engine (EC2 vs Fargate vs Lambda)", "They automatically apply the discount to Fargate vCPU and Memory usage", "Zero manual intervention or configuration is required when migrating between compute platforms under this plan"], ["Savings plans only work on Tuesdays"]),
    ("B61_14_2", "explain", "medium", "explain", ["Cloud Architecture"], "Explain the difference between a 'Hub-and-Spoke' network architecture and a 'VPC Mesh' architecture in AWS.", "A VPC Mesh (Full Mesh) means every VPC is connected directly to every other VPC using VPC Peering. For 10 VPCs, this requires 45 peering connections. It is fast but administratively impossible to scale and manage routing tables. A Hub-and-Spoke architecture places a central router (AWS Transit Gateway) in the middle. All 10 VPCs (Spokes) connect only to the Transit Gateway (Hub), requiring exactly 10 attachments. The Hub handles all transitive routing, vastly simplifying network scaling, security inspection, and VPN termination.", ["VPC Mesh requires direct point-to-point peering for every pair (N(N-1)/2 connections), scaling terribly", "Hub-and-Spoke uses a central router (Transit Gateway) where all VPCs attach once", "Hub-and-Spoke enables transitive routing and centralizes security/VPN management"], ["Hub and spoke is for bicycles, mesh is for screen doors"]),
    ("B61_14_3", "concept", "hard", "concept", ["Cloud Security"], "What is 'Dependency Confusion' in a CI/CD pipeline, and how do you architect your package manager (npm/pip) to prevent it?", "Dependency Confusion occurs when a company uses internal, proprietary packages (e.g., `my-internal-auth-lib`) hosted on a private registry, but the package name does not exist on the public registry (npm). An attacker registers that exact same name on the public npm registry and assigns it a ridiculously high version number (v99.9.9). When the CI/CD pipeline runs `npm install`, npm natively looks at both registries, sees the higher version on the public registry, and blindly downloads the malware instead of the private code. To prevent this, you must configure your package manager via Scopes (`@mycompany/auth-lib`) tied strictly to the private registry URL, or use a Proxy Registry (Artifactory) configured to explicitly block upstream lookups for internal namespaces.", ["Attacker publishes malware to public registries using the exact name of your private internal packages, but with a higher version", "CI/CD package managers naturally prefer the higher version, pulling the public malware instead of the private code", "Fix: Use Namespace Scopes (e.g., `@company/pkg`) strictly routed to the private registry, or block upstream resolution via an Artifactory proxy"], ["Dependency confusion is when the developer forgets which library to use"]),
    ("B61_14_4", "diagnose", "medium", "debugging", ["CI/CD Architecture"], "Your GitHub Actions pipeline uses a self-hosted runner on an EC2 instance. The pipeline suddenly fails with `No space left on device` during a Docker build. You SSH into the runner and run `df -h`; the disk is 100% full. You delete all the old Docker images (`docker image prune -a`), but the disk is STILL 100% full. What hidden Docker artifact is consuming the disk?", "While `docker image prune` deletes images, it does NOT delete the 'Docker Build Cache'. Modern Docker builds (BuildKit) cache intermediate build layers (like downloaded `apt` packages or `npm install` caches) to speed up future builds. Over hundreds of CI runs, this build cache can easily consume hundreds of gigabytes. To fix this, you must run `docker builder prune -a -f` or implement a scheduled cron job on the self-hosted runner to continuously purge the BuildKit cache.", ["`docker image prune` only deletes images; it ignores the massive BuildKit cache", "BuildKit caches intermediate build layers (like `npm install`), growing exponentially over time on persistent runners", "Fix: Run `docker builder prune -a` to free the actual disk space"], ["The server downloaded a movie by accident"]),
    ("B61_14_5", "implement", "hard", "implement", ["Reliability Engineering"], "How do you architect a Kubernetes 'Pod Topology Spread Constraint' to guarantee high availability across 3 AWS Availability Zones, but strictly prevent the cluster from scaling up new nodes if the spread becomes slightly unbalanced (to save money)?", "If you use a strict topology spread (`maxSkew: 1` with `whenUnsatisfiable: DoNotSchedule`), Kubernetes will absolutely refuse to schedule a 4th pod in AZ-A unless AZ-B and AZ-C also have pods. If AZ-B is full, the pod stays `Pending`, triggering the Cluster Autoscaler to spin up a brand new expensive EC2 node in AZ-B just to satisfy the strict spread. To prevent this cost, you must change the constraint to `whenUnsatisfiable: ScheduleAnyway`. This tells the scheduler: 'Try your absolute best to spread the pods evenly, but if an AZ is full, just schedule the pod on whatever existing node has space, rather than forcing a scale-up.'", ["Strict constraints (`DoNotSchedule`) force the Cluster Autoscaler to boot expensive new nodes just to satisfy geographic symmetry", "Change the constraint to `whenUnsatisfiable: ScheduleAnyway` (Soft constraint)", "The scheduler will prioritize spreading, but will fall back to using existing unbalanced capacity rather than leaving pods pending/scaling up"], ["You just tell Kubernetes you don't have any money"]),
    ("B61_14_6", "tradeoff", "medium", "tradeoff", ["CI/CD Architecture"], "What is the tradeoff of using 'Trunk-Based Development' (pushing straight to `main`) versus 'GitFlow' (long-lived feature branches) in a high-velocity DevOps team?", "GitFlow uses isolated feature branches that can live for weeks, providing extreme safety and allowing extensive QA before merging. The severe tradeoff is 'Merge Hell': when 5 developers try to merge their month-old branches, the code conflicts are catastrophic, and integration testing is delayed until the end, destroying CI/CD velocity. Trunk-Based Development forces developers to push small, incremental changes to `main` daily. This mathematically eliminates merge conflicts and guarantees continuous integration. The tradeoff is that unfinished or broken features are constantly in `main`, requiring the strict use of 'Feature Flags' to hide incomplete code from production users.", ["GitFlow: Safe, isolated, but causes catastrophic 'Merge Hell' and delays integration", "Trunk-Based: Pushes to `main` daily. Eliminates merge conflicts and enables true Continuous Integration", "Tradeoff: Trunk-based requires strict engineering discipline and Feature Flags to hide incomplete/broken code in production"], ["Trunk based development means programming in the trunk of a car"]),
    ("B61_14_7", "scenario", "hard", "scenario", ["Performance Tuning"], "Your team runs a massive Elasticsearch cluster on Kubernetes. During peak load, the JVM heap is fine, but the OS runs out of file descriptors and the pods crash. You add `ulimit -n 65536` to the Docker entrypoint, but Kubernetes ignores it. How do you permanently raise the `ulimit` and `vm.max_map_count` for a specific pod in Kubernetes without altering the host OS?", "You cannot rely on Docker entrypoints for kernel-level resource limits in Kubernetes. You must use an `InitContainer` with `securityContext: privileged: true`. The InitContainer boots before the Elasticsearch container and executes a shell command: `sysctl -w vm.max_map_count=262144`. Because it is privileged, it successfully modifies the kernel parameters for the Pod's namespace. Once it completes successfully, it exits, and the main Elasticsearch container boots securely without needing root privileges, inheriting the newly expanded limits.", ["Docker entrypoint `ulimit` commands are often ignored or blocked by Kubernetes security policies", "Must use an `InitContainer` configured with `privileged: true`", "The InitContainer runs `sysctl` to modify the kernel limits (e.g., `vm.max_map_count`) and exits, passing the limits to the unprivileged main container"], ["You ask the OS nicely to give you more files"]),
    ("B61_14_8", "explain", "medium", "explain", ["Cloud Architecture"], "Explain the concept of 'Graceful Degradation' in a microservice architecture.", "Graceful Degradation is an architectural pattern ensuring that when a non-critical dependency fails, the core system continues to function with reduced capabilities rather than crashing completely. If an e-commerce site's 'Recommendation Engine' microservice times out, the API Gateway (or BFF) should catch the timeout, instantly inject an empty array or a hardcoded list of generic 'Bestsellers', and return a 200 OK to the frontend. The user can still browse and checkout perfectly; they just miss the personalized recommendations. It prevents partial failures from cascading into complete system outages.", ["System continues to function with reduced capabilities when a dependency fails", "Prevents a non-critical microservice (e.g., Recommendations) from crashing the critical path (e.g., Checkout)", "Accomplished by catching timeouts and injecting fallback data (defaults or empty arrays) instead of returning HTTP 500s"], ["It means the servers bow gracefully before they crash"]),
    ("B61_14_9", "concept", "hard", "concept", ["Linux Core"], "What is 'eBPF' and why is it replacing traditional `iptables` for Kubernetes networking (e.g., Cilium)?", "Traditional Kubernetes networking (kube-proxy) relies on `iptables` to route traffic to pods. `iptables` evaluates rules sequentially; if you have 10,000 pods, routing a packet requires scanning 10,000 rules, causing massive CPU latency. eBPF (Extended Berkeley Packet Filter) allows custom routing programs to be compiled and injected directly into the Linux kernel natively. It uses highly efficient Hash Maps for O(1) lookups instead of sequential scanning. eBPF intercepts packets at the absolute lowest kernel level (socket layer), bypassing the massive overhead of the TCP/IP stack entirely, providing exponential performance gains for massive clusters.", ["`iptables` (kube-proxy) evaluates rules sequentially (O(N)), causing severe latency at scale", "eBPF injects native, compiled routing programs directly into the Linux kernel using O(1) Hash Maps", "eBPF intercepts packets at the lowest socket layer, bypassing TCP/IP stack overhead entirely for massive performance gains"], ["eBPF is a new brand of router you buy from Cisco"]),
    ("B61_14_10", "diagnose", "medium", "debugging", ["Terraform"], "You write a Terraform module to create an AWS SQS Queue and a Lambda function that consumes it. The deployment always fails on the first `terraform apply` saying 'Queue does not exist' when attaching the trigger, but if you immediately run `terraform apply` a second time, it succeeds perfectly. Why?", "This is a 'Race Condition' caused by missing explicit dependencies. Terraform builds a dependency graph natively. However, if the Lambda Trigger resource doesn't explicitly reference an attribute (like the `arn`) of the SQS Queue resource, Terraform assumes they are completely independent and tries to build them concurrently. The Trigger attempts to attach to the Queue before the AWS API finishes creating the Queue, causing a failure. The second run works because the Queue now exists. To fix this, you must explicitly link them using `depends_on = [aws_sqs_queue.my_queue]` or ensure the Trigger block natively references `aws_sqs_queue.my_queue.arn`.", ["Terraform builds resources concurrently unless a strict dependency graph is defined", "The Lambda Trigger tried to attach before the Queue finished provisioning (Race Condition)", "Fix: Use `depends_on` or ensure the Trigger explicitly references an output attribute (e.g., `.arn`) of the Queue to force sequential creation"], ["Terraform is just testing your patience on the first try"]),
    ("B61_14_11", "implement", "hard", "implement", ["CI/CD Architecture"], "How do you implement 'Secret Injection' for a Kubernetes deployment so that plaintext database passwords never exist on the physical disk or in `etcd`?", "Storing secrets as standard Kubernetes `Secrets` is dangerous because they are merely base64 encoded and stored in plaintext in the `etcd` database. To ensure zero disk exposure, you implement a 'Secrets Store CSI Driver' connected to AWS Secrets Manager or HashiCorp Vault. When the pod boots, the CSI driver dynamically reaches out to the external Secrets Manager, fetches the password over TLS, and mounts it directly into the pod's ephemeral RAM (in-memory `tmpfs` volume). The secret never touches the node's physical disk and is never stored in Kubernetes `etcd`.", ["Standard Kubernetes Secrets are base64 encoded and stored in plaintext in `etcd`", "Use the Secrets Store CSI Driver (e.g., Vault or AWS Secrets Manager)", "Fetches secrets dynamically at pod boot and mounts them directly into ephemeral RAM (`tmpfs`), preventing disk or `etcd` exposure"], ["You whisper the secret to the server over a secure microphone"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 5).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Cloud Architect", "Site Reliability Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "AWS / Kubernetes / Terraform",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "Infrastructure",
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
    print(f"Batch: 61")
    print(f"Target role: {ROLE}")
    print(f"Attempted: 100")
    print(f"Accepted: {len(accepted)}") 
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")
    
    sha256 = hashlib.sha256()
    with open(OUT, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            
    print(f"\nFinal SHA256: {sha256.hexdigest()}")


if __name__ == "__main__":
    run_batch()
