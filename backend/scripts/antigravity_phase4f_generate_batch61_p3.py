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
    # Group 7: CI/CD Delivery
    ("B61_7_1", "concept", "medium", "concept", ["CI/CD Architecture"], "What is the difference between 'Continuous Delivery' and 'Continuous Deployment'?", "In Continuous Delivery, every code commit is automatically built, tested, and staged in a production-like environment, proving that the codebase is *ready* to be deployed at any moment. However, a human must manually click 'Approve' to push the code to live production. In Continuous Deployment, the human approval step is entirely removed. If the automated E2E tests pass, the code is automatically deployed directly to the live production servers without any human intervention. Continuous Deployment requires an incredibly high degree of trust in automated testing and rollback mechanisms.", ["Continuous Delivery: Code is automatically prepared and staged, but requires a manual human click to deploy to production", "Continuous Deployment: Fully automated; code goes straight to production if automated tests pass (no human intervention)", "Continuous Deployment requires flawless automated testing and instant automated rollback capabilities"], ["Delivery means delivering code to the devs, deployment means deploying to the users"]),
    ("B61_7_2", "diagnose", "hard", "debugging", ["CI/CD Architecture"], "Your CI/CD pipeline deploys a microservice to Kubernetes using ArgoCD (GitOps). The developers merge a PR that updates the Deployment YAML with a new Docker image tag. ArgoCD detects the change and syncs it. However, the new pods crash-loop. The developers frantically revert the PR in GitHub, but ArgoCD continues attempting to deploy the broken image. Why did the Git revert fail to fix the cluster?", "This is a failure of 'Automated Rollback' combined with a broken GitOps state. If the new pods crash-loop, the Kubernetes Deployment never reaches a 'Healthy' status. Because it is stuck in `Progressing` or `Degraded`, ArgoCD might pause the sync. When the developers revert the PR, ArgoCD sees the Git change, but depending on the Sync Policy (e.g., lack of automated pruning or getting stuck on a pre-sync hook), it might refuse to apply the old YAML over a broken deployment. To fix this, you must configure ArgoCD with Automated Rollback (or use Flagger) to automatically revert the cluster state to the last known healthy ReplicaSet the moment health checks fail, without waiting for a manual Git revert.", ["GitOps tools (ArgoCD) can get stuck syncing if the cluster state is severely degraded", "A manual Git revert is too slow and might fail to sync over a broken rollout", "Fix: Implement Automated Rollbacks (via ArgoCD or Flagger) to instantly revert the ReplicaSet on health check failure"], ["ArgoCD doesn't know how to read the Git revert commit"]),
    ("B61_7_3", "implement", "medium", "implement", ["CI/CD Architecture"], "How do you implement 'Artifact Promotion' securely across Dev, Staging, and Prod environments without rebuilding the Docker image?", "A fundamental rule of DevOps is 'Build Once, Deploy Anywhere'. Rebuilding a Docker image for Prod introduces the risk that the underlying base OS or dependencies changed between the Dev build and the Prod build (creating 'Works on my machine' bugs). To implement Artifact Promotion: 1) The CI pipeline builds the Docker image EXACTLY once during the Dev stage. 2) The image is tagged with a Git SHA and pushed to the Dev container registry. 3) Once tested, a promotion pipeline physically copies (or retags) that exact same binary image to the Prod registry. Environment-specific config (like DB passwords) is injected at runtime via Kubernetes ConfigMaps/Secrets, never baked into the image.", ["Build Once, Deploy Anywhere: Never rebuild the Docker image for different environments", "Rebuilding risks introducing different OS packages or dependency versions into Prod", "Artifact Promotion involves retagging or copying the exact same binary image across registries, injecting config purely at runtime"], ["You zip the Dev folder and email it to the Prod server"]),
    ("B61_7_4", "tradeoff", "hard", "tradeoff", ["CI/CD Architecture"], "What is the tradeoff of using 'Immutable Infrastructure' (e.g., Packer AMIs) versus Configuration Management tools (e.g., Ansible/Chef) for deploying application updates?", "Configuration Management (Ansible) connects to a running production server via SSH and mutates it in place (e.g., `apt-get update`, pulling new code). This is fast, but risks 'Configuration Drift': over time, Server A and Server B diverge due to failed SSH scripts, creating snowflakes. Immutable Infrastructure (Packer) completely bans in-place mutations. For an update, Packer builds a brand new, pristine OS Image (AMI). The autoscaling group terminates the old servers and boots the new ones. This mathematically guarantees consistency and eliminates drift, but the severe tradeoff is deployment speed: building a new OS image and booting EC2 instances takes 10-15 minutes, whereas Ansible takes 10 seconds.", ["Ansible (Mutable): Mutates running servers in-place. Fast, but causes Configuration Drift and 'snowflake' servers", "Packer (Immutable): Replaces entire servers with pristine new OS images. Guarantees consistency and eliminates drift", "Tradeoff: Immutable deployments are significantly slower (10+ mins to bake and boot AMIs) compared to in-place updates"], ["Immutable infrastructure means the servers are made of concrete"]),
    ("B61_7_5", "scenario", "hard", "scenario", ["CI/CD Architecture"], "You deploy a new backend API and a new Database Schema simultaneously. The deployment succeeds. 10 minutes later, a critical bug is found in the API code. You trigger an automated rollback of the backend API to the previous version. The rollback completes, but now the entire application is throwing 500 errors. Why did the rollback break the system, and how do you prevent this?", "You successfully rolled back the API code, but the Database Schema changes (e.g., dropping a column or renaming a table) were NOT rolled back. The old API code is now running against the new DB schema, causing fatal SQL exceptions. Database migrations are notoriously difficult to roll back automatically. To prevent this, you must adopt 'Expand and Contract' deployments (Non-Breaking Schema Changes). Phase 1: Deploy a DB migration that *adds* the new column, but doesn't delete the old one. The old API still works perfectly. Phase 2: Deploy the new API that writes to both columns. If you roll back the API, it still works. Phase 3: Only delete the old column weeks later when the new API is perfectly stable.", ["The API code rolled back, but the DB schema changes did not, breaking compatibility with the old code", "Automated DB rollbacks are incredibly dangerous and often result in data loss", "Fix by enforcing 'Expand and Contract' deployments: DB changes must be strictly additive and backwards-compatible; delete old columns only weeks later"], ["The rollback script forgot to press save on the database"]),
    ("B61_7_6", "explain", "medium", "explain", ["CI/CD Architecture"], "Explain the concept of 'Progressive Delivery' using Canary deployments.", "Progressive Delivery minimizes the blast radius of a bad deployment by exposing it to users incrementally. Instead of a 'Big Bang' deployment where 100% of users get the new code instantly, a Canary deployment routes exactly 1% of live production traffic to the new version (the Canary), while 99% of traffic stays on the stable version. A tool like Flagger monitors the HTTP 500 errors and latency of the Canary for 5 minutes. If it exceeds a threshold, it automatically rolls back. If it's healthy, it gradually increases traffic to 10%, 25%, 50%, and finally 100%. It mathematically proves the code is safe using real user traffic before committing to it.", ["Incrementally exposing new code to live users (e.g., 1% -> 10% -> 100%) to minimize blast radius", "Uses automated metrics analysis (HTTP 500s, latency) to evaluate the health of the Canary", "Automatically rolls back if metrics degrade, mathematically protecting 99% of users from a bad release"], ["Progressive delivery means delivering the code using progressive insurance"]),

    # Group 8: Performance & Capacity
    ("B61_8_1", "concept", "medium", "concept", ["Performance Tuning"], "What is 'CPU Throttling' in a containerized environment, and why does it occur even when node CPU is available?", "CPU Throttling occurs because of the Linux kernel's CFS (Completely Fair Scheduler) quota system. When you set a Kubernetes `cpu: limit` of 1.0 (1 vCPU), the kernel allocates that time in tiny periods (e.g., 100ms). The container is allowed to use 100ms of CPU time per period. If a highly multi-threaded application (like Java/Node.js) bursts and uses its entire 100ms quota in the first 20ms, the kernel forcibly pauses (throttles) all threads in that container for the remaining 80ms. This causes massive latency spikes for HTTP requests, even if the underlying EC2 node is 90% idle, because the container hit its arbitrary quota.", ["Enforced by the Linux kernel CFS (Completely Fair Scheduler) quota system", "Highly multi-threaded apps can exhaust their time-slice quota instantly during bursts", "The kernel forcibly pauses the container for the remainder of the period, causing massive latency spikes despite the node having idle CPU"], ["The CPU throttle is a physical pedal you press in the datacenter"]),
    ("B61_8_2", "diagnose", "hard", "debugging", ["Performance Tuning"], "Your Kubernetes Horizontal Pod Autoscaler (HPA) is configured to scale based on a target CPU utilization of 50%. You notice the cluster is constantly scaling up to 20 pods, then dropping to 2 pods, then instantly scaling back up to 20 pods in an infinite loop. This 'thrashing' is killing performance. Why is this happening?", "This is an 'Autoscaling Oscillation' (Thrashing) caused by a massive mismatch between the metric target and the application's baseline. If the application requires 80% CPU just to boot and sit idle (or handles background queues inefficiently), it immediately violates the 50% target. The HPA scales up massively to distribute the load. The load drops to 10%, so the HPA aggressively scales down to 2. The remaining 2 pods instantly spike to 80% again. To fix this: 1) Increase the target CPU to a realistic baseline (e.g., 85%), 2) Configure HPA `behavior` blocks with strict `scaleDown` stabilization windows (e.g., wait 5 minutes before scaling down to ensure the spike is truly over).", ["Autoscaling Oscillation (Thrashing): Infinite loop of aggressive scale-ups and scale-downs", "Caused by unrealistic target metrics or sudden bursty workloads that misalign with the app's baseline CPU footprint", "Fix by increasing the target threshold and using HPA `behavior` scaling policies (stabilization windows to delay scale-down)"], ["The autoscaler is trying to save too much money"]),
    ("B61_8_3", "implement", "medium", "implement", ["Performance Tuning"], "How do you architect an autoscaling strategy for a background worker application that processes video uploads from an SQS queue? Why is CPU-based scaling incorrect here?", "Scaling a background worker based on CPU is a trap. If the queue has 100,000 videos, the single worker will max out at 100% CPU. The HPA scales up to 10 workers. They all max out at 100% CPU because the queue is still huge. The HPA scales to 1000 workers, bankrupting the company. Conversely, if the workers are waiting on external API I/O, their CPU might be 5%, but the queue is backing up, and the HPA will refuse to scale. You must use KEDA (Kubernetes Event-driven Autoscaling) or custom metrics to scale based on 'Queue Depth' (the number of pending messages in SQS). E.g., target 1 pod per 100 messages.", ["CPU-based scaling fails for workers: they either max CPU infinitely (runaway scaling) or wait on I/O with low CPU (refuse to scale)", "Must scale based on Event/Queue Depth (the length of the backlog)", "Use KEDA to read the AWS SQS queue depth and scale pods proportionately (e.g., 1 pod per 100 messages)"], ["You scale based on the size of the videos in megabytes"]),
    ("B61_8_4", "tradeoff", "hard", "tradeoff", ["Performance Tuning"], "What is the operational tradeoff of using massive, Vertical Scaling (fewer, huge EC2 instances) versus Horizontal Scaling (many, tiny EC2 instances) for a Kubernetes node group?", "Vertical Scaling (e.g., using `m5.12xlarge` nodes with 48 vCPUs) allows massive pods to run easily, minimizes the Kubernetes control-plane networking overhead (kube-proxy/DaemonSets only run on a few nodes), and reduces IP exhaustion. The severe tradeoff is Blast Radius. If one massive node dies, 200 pods are instantly evicted, causing a massive 'thundering herd' as the cluster struggles to reschedule them. Horizontal Scaling (e.g., `m5.large` nodes with 2 vCPUs) minimizes the blast radius (a node death only affects 5 pods), but wastes massive compute overhead because every node must run system DaemonSets (logging, CNI, CSI), leaving little room for actual workloads.", ["Vertical (Fewer/Huge Nodes): Less DaemonSet overhead, avoids IP exhaustion, but catastrophic blast radius if a node crashes (evicting hundreds of pods)", "Horizontal (Many/Tiny Nodes): Tiny blast radius per node failure, but wastes massive resources running duplicate system DaemonSets on every node", "Tradeoff: Blast Radius vs DaemonSet Overhead efficiency"], ["Vertical scaling means the servers are standing up, horizontal means they are laying down"]),
    ("B61_8_5", "scenario", "medium", "scenario", ["Performance Tuning"], "A Postgres database hosted on AWS RDS is experiencing severe read latency. CPU and RAM utilization are under 30%. You check the AWS metrics and see that `ReadIOPS` is flatlining exactly at 3,000, and `DiskQueueDepth` is spiking. What is the infrastructure bottleneck, and how do you fix it?", "This is an EBS (Elastic Block Store) IOPS limitation. General Purpose SSDs (gp2) in AWS allocate IOPS based on the disk size (3 IOPS per GB). If the database disk is 1,000 GB, its maximum physical speed is capped at 3,000 IOPS. The CPU is idle because it is starved, waiting for the physical storage network to return data. To fix this without over-provisioning storage space, you must migrate the volume to `gp3` (where you can explicitly provision 10,000 IOPS independently of disk size) or migrate to `io1/io2` Provisioned IOPS volumes for mission-critical speed.", ["EBS IOPS Saturation: The disk network is maxed out, starving the idle CPU", "Older `gp2` volumes tie IOPS strictly to disk size (3 IOPS per GB), leading to a hard cap (e.g., 3000 IOPS for 1TB)", "Fix by upgrading to `gp3` or Provisioned IOPS (`io2`), which allow provisioning high IOPS independently of storage capacity"], ["The database is too heavy for the network cables"]),
    ("B61_8_6", "explain", "medium", "explain", ["Performance Tuning"], "Explain the concept of 'Network Bandwidth Exhaustion' between EC2 instances and how it relates to instance types.", "In AWS, network bandwidth is not infinite and is strictly tied to the specific EC2 instance type. An `m5.large` might be capped at 1 Gbps, while an `m5.8xlarge` can handle 10 Gbps. If you run a high-throughput microservice (like a video transcoder or Redis cache) on a cheap `t3.medium`, the CPU might look perfectly healthy, but the instance will physically drop network packets when it hits its 1 Gbps limit. Network exhaustion causes random API timeouts, dropped DB connections, and TCP retransmissions that are notoriously difficult to debug if you aren't explicitly monitoring `NetworkOut` limits.", ["AWS caps network bandwidth strictly based on the EC2 instance type/size", "An instance can have 10% CPU but completely max out its physical Network Interface Card (NIC)", "Causes mysterious packet drops, TCP retransmissions, and API timeouts. Fix by upgrading to network-optimized instances (e.g., `c5n`)"], ["Bandwidth exhaustion is when the wifi router gets tired"]),

    # Group 9: FinOps / Cost Engineering
    ("B61_9_1", "concept", "medium", "concept", ["Cloud Architecture"], "What is the primary driver of runaway AWS NAT Gateway costs, and how do you architect around it?", "NAT Gateways charge an hourly rate AND a hefty fee per Gigabyte of data processed. The runaway cost almost always occurs when private subnets continuously transfer massive amounts of data to an external public IP, OR to an AWS service (like S3 or DynamoDB) over the public internet. If a private EC2 instance pulls 10TB of data from S3, it routes through the NAT Gateway, costing hundreds of dollars. To architect around this, you must deploy a 'VPC Gateway Endpoint' for S3. This explicitly routes S3 traffic over the internal AWS backbone, completely bypassing the NAT Gateway and dropping the data transfer cost to zero.", ["NAT Gateways charge heavily per GB of data processed", "Pulling massive data from S3 or DynamoDB from a private subnet routes through the NAT, incurring massive fees", "Architectural fix: Deploy free VPC Gateway Endpoints for S3/DynamoDB to bypass the NAT completely"], ["NAT Gateways charge you per line of code you write"]),
    ("B61_9_2", "diagnose", "hard", "debugging", ["Cloud Architecture"], "Your company's AWS bill spiked by $10,000 this month. You look at Cost Explorer, and the spike is entirely categorized under 'EC2-Other' -> 'Data Transfer - Inter-AZ'. You are running a massive Kubernetes cluster across 3 Availability Zones (AZs). What is causing this, and how do you stop it?", "AWS charges significantly for data transfer *between* different Availability Zones (e.g., `us-east-1a` to `us-east-1b`). In Kubernetes, the default `kube-proxy` load balancing (iptables) is perfectly random. If a frontend pod in AZ-1a talks to a backend pod, the proxy will happily route the traffic to a backend pod in AZ-1b, incurring Inter-AZ data costs. Over millions of requests, this explodes the bill. To fix this, you must enable Kubernetes 'Topology Aware Routing'. This instructs kube-proxy to strongly prefer routing traffic to endpoints located in the exact same AZ as the requester, drastically slashing cross-AZ network costs while maintaining high availability.", ["AWS charges heavily for data transfer between different Availability Zones (Inter-AZ)", "Kubernetes load balancing is random by default, constantly sending traffic across AZ boundaries", "Fix: Enable Topology Aware Routing to force pods to communicate with local endpoints in their own AZ first"], ["The EC2 instances are sending emails to each other"]),
    ("B61_9_3", "implement", "medium", "implement", ["Cloud Architecture"], "How do you implement accurate Cost Attribution (FinOps) in a multi-tenant Kubernetes cluster where 5 different engineering teams share the exact same EC2 nodes?", "You cannot use standard AWS Cost Explorer because it only sees the underlying EC2 nodes; it doesn't know which team's pods are running on them. You must implement Kubernetes-native cost tracking (e.g., Kubecost or OpenCost). First, you strictly enforce Kubernetes Namespaces or specific `labels` (e.g., `team: frontend`) for all deployments. Kubecost monitors the exact CPU/RAM milliseconds consumed by each pod, cross-references it with the AWS EC2 billing API, and calculates that the `frontend` team consumed 40% of the node's resources, allowing you to accurately charge back the specific dollar amount to that department.", ["Standard cloud billing tools cannot see inside a shared Kubernetes cluster", "Implement strict Namespace isolation or mandatory tagging/labels (e.g., `team: billing`)", "Use tools like Kubecost to track pod-level CPU/RAM milliseconds and calculate precise dollar attributions per team"], ["You manually count the pods on the screen and divide the AWS bill evenly"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 3).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Cloud Architect", "Site Reliability Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "AWS / Kubernetes",
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
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
