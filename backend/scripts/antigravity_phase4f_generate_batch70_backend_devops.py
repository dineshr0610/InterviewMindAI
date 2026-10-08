import asyncio
import json
import os
import re
import sys
import uuid
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

# Q Format: (id_code, role, intent, difficulty, question_type, [skills], technology, topic, question, expected_answer, strong_indicators, weak_indicators)
Q = [
    (
        "B70_1",
        "Backend Developer",
        "diagnose",
        "hard",
        "debugging",
        ["Distributed Systems", "Performance Tuning"],
        "Redis / Connection Pooling",
        "Redis Connection Pool Exhaustion and TIME_WAIT States",
        "A microservice uses a Redis connection pool to fetch session data. During a traffic spike, the service throws 'Connection refused' and 'Cannot assign requested address' errors when connecting to Redis, despite Redis operating at only 10% CPU and having plenty of memory. Running `netstat` on the microservice host reveals 40,000 TCP sockets in the `TIME_WAIT` state. What architectural misconfiguration causes this specific symptom, and how do you resolve it?",
        "The errors 'Cannot assign requested address' (EADDRNOTAVAIL) and the massive number of `TIME_WAIT` sockets indicate ephemeral port exhaustion. 1) Root Cause: The microservice is rapidly creating and destroying short-lived connections to Redis rather than reusing them. When a client initiates an active TCP close, the OS places the socket in the `TIME_WAIT` state for 60 seconds (2x Maximum Segment Lifetime) to handle delayed packets. If the service opens and closes thousands of connections per second, it quickly exhausts the ~28,000 available ephemeral ports on Linux. 2) The Misconfiguration: The application is either not using a connection pool, the connection pool is configured to close idle connections too aggressively, or the application is explicitly calling `conn.close()` after every command instead of returning the connection to the pool. 3) Resolution: Configure a persistent connection pool (e.g., `JedisPool` or `redis-py` ConnectionPool), ensure connections are returned to the pool, increase the ephemeral port range (`net.ipv4.ip_local_port_range`), and optionally tune `net.ipv4.tcp_tw_reuse` if crossing NAT/load balancers safely.",
        [
            "Identifies ephemeral port exhaustion caused by rapid creation and destruction of TCP connections",
            "Explains that active TCP closes leave sockets in TIME_WAIT for 60 seconds (2MSL)",
            "Prescribes using persistent connection pools and ensuring connections are returned rather than closed"
        ],
        [
            "Claims Redis is out of memory and needs to be scaled up",
            "Suggests disabling TCP entirely and using UDP for Redis"
        ]
    ),
    (
        "B70_2",
        "Backend Developer",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Database Architecture", "Data Consistency"],
        "PostgreSQL / B-Tree",
        "UUIDv4 vs ULID/UUIDv7 as Primary Keys in B-Tree Indexes",
        "When designing a multi-tenant SaaS application, developers often choose random UUIDv4 strings for primary keys to prevent ID guessing and simplify distributed generation. However, as the table grows beyond 100 million rows, INSERT performance degrades severely, and disk I/O spikes. Why do random UUIDv4 keys destroy PostgreSQL B-Tree insert performance, and why is ULID or UUIDv7 a superior tradeoff?",
        "1) The UUIDv4 B-Tree Problem: UUIDv4 values are cryptographically random. PostgreSQL uses B-Trees for primary key indexes. Because UUIDv4s have no sequential locality, every new INSERT requires placing the new index entry in a random B-Tree leaf node. 2) Memory/Disk Thrashing: As the index grows larger than available RAM (shared_buffers), these random inserts guarantee high cache miss rates. To insert a row, PostgreSQL must fetch a random 8KB index page from disk into RAM, modify it, and mark it dirty. This causes massive write amplification and continuous disk I/O thrashing. 3) Page Splits and Bloat: Random inserts also cause frequent B-Tree page splits, leading to index bloat (often 2x-3x the size of the actual data) and fragmented storage. 4) The ULID/UUIDv7 Solution: ULIDs and UUIDv7s embed a millisecond-precision timestamp in their high bits, making them lexicographically sortable by time. Inserts become append-only (right-leaning) in the B-Tree. The 'hot' rightmost pages stay pinned in RAM, eliminating random disk reads during inserts, drastically reducing page splits, and improving INSERT throughput by orders of magnitude while retaining collision resistance.",
        [
            "Identifies random UUIDv4 inserts causing random B-Tree leaf node access and high buffer cache misses",
            "Explains disk thrashing and write amplification when the index exceeds RAM",
            "Contrasts with UUIDv7/ULID which are time-ordered, keeping inserts append-only (right-leaning) and cached in RAM"
        ],
        [
            "Claims UUIDv4 is slow because the string is 36 characters long while ULID is only 26",
            "Suggests turning off indexes entirely to speed up INSERTs"
        ]
    ),
    (
        "B70_3",
        "Backend Developer",
        "scenario",
        "hard",
        "scenario",
        ["API Design", "Distributed Systems"],
        "Idempotency / REST",
        "Designing Idempotent Payment APIs with Race Conditions",
        "You are designing a RESTful API for a payment gateway. The endpoint `POST /v1/payments` charges a user's credit card. If a client experiences a network timeout, they might retry the identical request. You implement an `Idempotency-Key` header, checking a Redis cache: if the key exists, you return the cached response. However, if a client sends two requests with the same Idempotency-Key at the *exact same millisecond*, both requests bypass the cache check, charging the user twice. How do you implement distributed concurrency control to guarantee strict idempotency under race conditions?",
        "Checking for existence and then inserting (Check-Then-Act) is a classic race condition. To solve this in a distributed environment: 1) Atomic Locks / Distributed Mutex: Before processing the payment, attempt to acquire a distributed lock in Redis using the idempotency key (e.g., `SET idempotency_key:lock \"1\" NX EX 10`). The `NX` (Not eXists) flag guarantees that only one concurrent request acquires the lock. 2) State Machine Tracking: The payload stored against the idempotency key must track the lifecycle state (`STARTED`, `COMPLETED`, `FAILED`). 3) The Workflow: Request 1 acquires the lock, writes the key state as `STARTED`, and proceeds to the payment processor. Request 2 fails to acquire the lock. Request 2 must then read the state. If the state is `STARTED`, Request 2 should block, return a 409 Conflict, or return a 202 Accepted (processing). It must NOT proceed. 4) Finalization: Once Request 1 succeeds, it updates the idempotency key state to `COMPLETED` along with the JSON response payload, and releases the lock. Future retries read the `COMPLETED` state and immediately return the cached payload.",
        [
            "Identifies the Check-Then-Act race condition caused by non-atomic cache checks",
            "Proposes an atomic locking mechanism (e.g., Redis SET NX) to ensure only one thread initiates processing",
            "Defines a lifecycle state (STARTED, COMPLETED) to handle concurrent requests arriving while the first is still processing"
        ],
        [
            "Suggests using a synchronized keyword in Java to lock the entire API server",
            "Relies solely on database unique constraints which fail if the DB insert happens at the end of the transaction"
        ]
    ),
    (
        "B70_4",
        "DevOps / Cloud Engineer",
        "explain",
        "medium",
        "explain",
        ["Containerization", "Operating Systems"],
        "Docker / Linux Namespaces",
        "PID 1 Zombies and Subreaper Responsibilities in Docker Containers",
        "When running a Node.js or Java application directly as the entrypoint in a Docker container (e.g., `ENTRYPOINT [\"node\", \"app.js\"]`), the process runs as PID 1. Over time, the container accumulates hundreds of 'zombie' (defunct) processes, eventually exhausting the process table. Why does running a standard application as PID 1 cause zombie processes, and how do `tini` or `dumb-init` solve this issue?",
        "1) The Role of PID 1 (init): In Linux, the process with Process ID 1 is the 'init' system (like systemd). It has a special kernel-mandated responsibility: 'reaping' orphaned child processes. If a process spawns a child, and the parent dies before the child, the child becomes an orphan. The kernel automatically re-parents orphans to PID 1. 2) Zombie Creation: When a child process terminates, it becomes a 'zombie' (retaining a PID and exit status in the process table) until its parent explicitly calls the `wait()` syscall to reap it. 3) The Failure: Standard applications like Node.js or Java are not designed to act as init systems. They do not contain signal handlers to reap arbitrary orphaned child processes. Thus, when they run as PID 1 in a container and spawn child processes (e.g., via `child_process.exec`), any orphaned descendants that terminate remain as zombies forever, eventually exhausting PIDs. 4) The Solution: Tools like `tini` or `dumb-init` are minimal init systems designed specifically for containers. By setting `ENTRYPOINT [\"/sbin/tini\", \"--\", \"node\", \"app.js\"]`, `tini` runs as PID 1, executes the application as a child, and explicitly registers a `SIGCHLD` handler to call `wait()` and reap all orphaned zombies automatically.",
        [
            "Explains that PID 1 is responsible for reaping orphaned child processes in Linux",
            "Identifies that standard apps (Node/Java) lack SIGCHLD handlers to call wait() on orphaned descendants",
            "Describes tini/dumb-init as lightweight init systems that run as PID 1 to properly reap zombies and forward signals"
        ],
        [
            "Claims zombies are caused by malware running inside the Docker image"
        ]
    ),
    (
        "B70_5",
        "DevOps / Cloud Engineer",
        "diagnose",
        "hard",
        "debugging",
        ["Kubernetes", "Networking"],
        "Kubernetes / CoreDNS",
        "ndots:5 DNS Amplification and Latency in Kubernetes",
        "A microservice running in Kubernetes is experiencing high latency when making external API calls to `api.stripe.com`. Inspecting CoreDNS logs reveals that for every single request to `api.stripe.com`, CoreDNS receives and processes four to five redundant A/AAAA record queries for domains like `api.stripe.com.default.svc.cluster.local`. What causes this internal DNS amplification, and how do you resolve it?",
        "1) The Root Cause (ndots:5): By default, Kubernetes configures pod `/etc/resolv.conf` with a search path containing local cluster domains (e.g., `default.svc.cluster.local`, `svc.cluster.local`, `cluster.local`) and an `ndots:5` option. 2) The Resolution Logic: `ndots:5` tells the Linux DNS resolver (glibc/musl) that if a queried hostname contains FEWER than 5 dots, it must not treat it as an absolute Fully Qualified Domain Name (FQDN) initially. Instead, it must sequentially append every search domain and query the DNS server before finally trying the absolute name as a fallback. 3) The Amplification: `api.stripe.com` contains only 2 dots. The pod's resolver asks CoreDNS for `api.stripe.com.default.svc.cluster.local` (NXDOMAIN), then `api.stripe.com.svc.cluster.local` (NXDOMAIN), etc., sending up to 4 failed requests before finally querying `api.stripe.com.` and succeeding. This adds tens of milliseconds of latency and crushes CoreDNS under heavy load. 4) Resolution: There are two main fixes: A) Add a trailing dot to external URLs in the application code (`api.stripe.com.`), which forces the resolver to treat it as an absolute FQDN. B) Modify the pod's `dnsConfig` in the deployment manifest to set `ndots: 2` or `ndots: 1`, ensuring external domains with 2+ dots are queried absolutely on the first attempt.",
        [
            "Identifies ndots:5 in /etc/resolv.conf as the trigger for search domain appending",
            "Explains that domains with fewer than 5 dots are queried against cluster search paths before falling back to the absolute name",
            "Proposes lowering the ndots value in pod dnsConfig or appending a trailing dot to the URL to force an absolute query"
        ],
        [
            "Claims CoreDNS is experiencing a DDoS attack from the outside internet",
            "Suggests disabling DNS entirely and hardcoding Stripe's IP address"
        ]
    ),
    (
        "B70_6",
        "DevOps / Cloud Engineer",
        "scenario",
        "medium",
        "scenario",
        ["CI/CD", "Security Architecture"],
        "GitHub Actions / OIDC",
        "Replacing Long-Lived Cloud Credentials with OpenID Connect (OIDC)",
        "A DevOps team uses GitHub Actions to deploy infrastructure to AWS using Terraform. Currently, they store long-lived IAM User Access Keys (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`) as GitHub repository secrets. Security auditing flags this as a critical risk due to the potential for credential exfiltration. How do you architect a credential-less CI/CD pipeline using OpenID Connect (OIDC) to authenticate GitHub Actions directly with AWS IAM?",
        "To eliminate long-lived secrets, you establish a trust relationship between AWS (the Resource Provider) and GitHub (the Identity Provider) using OIDC: 1) Identity Provider Configuration: In AWS IAM, create an OIDC Identity Provider pointing to `https://token.actions.githubusercontent.com`. 2) IAM Role and Trust Policy: Create an IAM Role for the deployment. Attach a Trust Policy (AssumeRoleWithWebIdentity) to this role that strictly validates the `sub` (subject) claim of the incoming OIDC token. The `sub` claim must explicitly match the specific GitHub repository and branch (e.g., `repo:my-org/my-repo:ref:refs/heads/main`). This prevents any other GitHub repository from assuming the role. 3) GitHub Actions Workflow: In the workflow YAML, grant `permissions: id-token: write` and `contents: read`. Use the `aws-actions/configure-aws-credentials` action, passing the `role-to-assume`. 4) The Flow: During the run, GitHub securely mints a short-lived JSON Web Token (JWT) signed by GitHub. The AWS Action sends this JWT to AWS STS. AWS validates the signature and the `sub` claim against the Trust Policy, and returns temporary, short-lived session credentials back to the runner.",
        [
            "Explains establishing GitHub as an OIDC Identity Provider in AWS IAM",
            "Highlights the critical need to scope the IAM Trust Policy's `sub` claim to a specific repository/branch to prevent privilege escalation",
            "Describes the workflow generating a short-lived JWT that AWS STS exchanges for temporary session credentials"
        ],
        [
            "Suggests encrypting the long-lived IAM keys with Base64 before putting them in GitHub Secrets"
        ]
    ),
    (
        "B70_7",
        "DevOps / Cloud Engineer",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Cloud Architecture", "Load Balancing"],
        "AWS ALB vs NLB",
        "ALB vs NLB for High-Throughput gRPC Microservices",
        "You are designing the ingress architecture for a backend fleet of gRPC microservices hosted on AWS ECS. The services handle sustained bursts of millions of concurrent requests. You must choose between an Application Load Balancer (ALB) and a Network Load Balancer (NLB). Compare the architectural tradeoffs of ALB vs NLB specifically regarding gRPC multiplexing, connection termination, and dynamic scaling latencies.",
        "1) Layer/Protocol Support: ALB operates at Layer 7 (HTTP/2, gRPC). It natively inspects HTTP headers, supports gRPC-specific routing, and terminates TLS. NLB operates at Layer 4 (TCP/UDP), passing raw packets directly to the backend. 2) gRPC Multiplexing & Connection Termination: gRPC uses HTTP/2 multiplexing, meaning multiple concurrent requests share a single long-lived TCP connection. If you use an NLB, the NLB forwards the single TCP connection to one specific backend pod/task. That task will receive ALL multiplexed requests for that connection, leading to severe load imbalance across the fleet. ALB terminates the HTTP/2 connection at the load balancer, decodes the individual gRPC requests, and balances them individually across all backends, ensuring even distribution. 3) Scaling Latency: ALB scales up dynamically by provisioning new nodes and updating DNS, which takes 1-3 minutes. Sudden, massive traffic spikes can overwhelm an ALB before it scales, resulting in 503s. NLB is designed for instantaneous scale, handling millions of requests per second natively without 'warming up' because it uses a highly distributed static IP architecture. Conclusion: For gRPC, ALB is strongly preferred due to Layer 7 multiplexing unbundling, preventing backend hotspots. If NLB is strictly required for extreme instantaneous burst traffic, the application clients must implement client-side load balancing or connection-pooling mechanisms to force periodic reconnection and redistribution.",
        [
            "Explains that ALB (Layer 7) terminates HTTP/2 and distributes individual gRPC requests evenly across backends",
            "Identifies that NLB (Layer 4) passes the long-lived HTTP/2 TCP connection to a single backend, causing severe load imbalance for multiplexed traffic",
            "Contrasts the dynamic scaling latency of ALB against the instantaneous static-IP scale of NLB"
        ],
        [
            "Claims gRPC only runs on UDP, so NLB is the only option"
        ]
    ),
    (
        "B70_8",
        "DevOps / Cloud Engineer",
        "explain",
        "medium",
        "explain",
        ["Infrastructure as Code", "State Management"],
        "Terraform / State Locks",
        "Terraform State Corruption and the Purpose of State Locking",
        "A team of DevOps engineers shares a single Terraform state file stored in an S3 bucket. Two engineers inadvertently run `terraform apply` on their local machines at the exact same time targeting the same infrastructure. Without state locking, what exact race condition occurs during the deployment, and how does configuring a DynamoDB table prevent Terraform state corruption?",
        "1) The Race Condition: Terraform uses the state file to map real-world infrastructure objects to the configuration. When an apply begins, Terraform reads the remote state. It then executes API calls to AWS (e.g., creating EC2 instances). Finally, it writes the updated state back to S3. If Engineer A and Engineer B run `apply` concurrently, both read State Version 1. Engineer A creates Instance X, and Engineer B creates Instance Y. Engineer A writes State Version 2 (containing X) to S3. Milliseconds later, Engineer B writes State Version 2 (containing Y) to S3, completely overwriting Engineer A's state file. Instance X is now 'orphaned'—it exists in AWS and incurs costs, but Terraform has lost all knowledge of it, causing configuration drift and state corruption. 2) DynamoDB State Locking: To solve this, a DynamoDB table is configured as a locking backend. Before Engineer A's Terraform reads the state, it attempts an atomic `PutItem` in DynamoDB to create a lock record with a specific Lock ID. 3) The Prevention: Because DynamoDB enforces conditional writes, if Engineer B attempts to run `apply`, their lock request fails because the Lock ID already exists. Engineer B's Terraform immediately aborts with a 'Lock Error', preventing concurrent modification and ensuring strict serialized execution of state updates.",
        [
            "Identifies the Read-Modify-Write race condition where the second write overwrites the first, orphaning deployed resources",
            "Explains the use of a DynamoDB table to establish a distributed atomic lock before reading or modifying state",
            "Notes that DynamoDB conditional writes guarantee only one process can acquire the lock at a time"
        ],
        [
            "Suggests storing the Terraform state file in a GitHub repository to prevent merge conflicts",
            "Claims Terraform automatically merges concurrent state writes using Git-like three-way merges"
        ]
    )
]

def run_batch():
    with open(OUT, "r", encoding="utf-8") as f:
        existing = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(existing)} existing records.")
    
    for q in Q:
        if LEAK.search(q[8]) or LEAK.search(q[9]):
            print(f"PROMPT LEAK DETECTED in: {q[8]}")
            sys.exit(1)
            
    existing_texts = [ex["question"] for ex in existing]
    new_texts = [q[8] for q in Q]
    
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
            print(f"REJECTED (Sim: {max_sim:.2f}): {q[8][:50]}...")
            rejected.append(q)
        else:
            print(f"ACCEPTED (Sim: {max_sim:.2f}): {q[8][:60]}...")
            accepted.append(q)
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions.")
    if len(rejected) > 0:
        print("Stopping due to rejections.")
        sys.exit(1)
        
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": q[1],
            "role": q[1],
            "applicable_roles": ["Backend Developer", "Software Engineer"],
            "primary_skill": q[5][0],
            "skill": q[5][0],
            "secondary_skills": q[5][1:] if len(q[5]) > 1 else [],
            "technology": q[6],
            "topic": q[7],
            "category": "Software Engineering",
            "intent": q[2],
            "difficulty": q[3],
            "question_type": q[4],
            "question": q[8],
            "ideal_answer": q[9],
            "expected_answer": q[9],
            "evaluation_rubric": {
                "strong_indicators": q[10],
                "weak_indicators": q[11]
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
            
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r.get("primary_role") or r.get("role") for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT")
    print("========================================")
    print(f"Batch: 70")
    print(f"Cumulative total: {len(final_existing)}")
    print("Role counts:")
    for role, count in sorted(role_counts.items()):
        print(f"  {role}: {count}")

if __name__ == "__main__":
    run_batch()
