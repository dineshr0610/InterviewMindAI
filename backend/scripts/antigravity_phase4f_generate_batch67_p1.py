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

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUT = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")

ROLE = "DevOps / Cloud Engineer"
LEAK = re.compile(r"(generate a question|generate \d+ questions|return only json|phase 4f gap plan|"
                  r"generation batch|candidate generation|system instructions|do not proceed|"
                  r"awaiting authorization|minimum target|generation pipeline|"
                  r"batch \d+ generation|expected answer|strong indicator|weak indicator|as an ai|"
                  r"here is the question|\bprompt text\b)", re.I)

Q = [
    ("B67_1_1", "scenario", "hard", "scenario", ["Multi-Region Architecture", "High Availability"],
     "In an active-active multi-region deployment, the application relies on an asynchronous cross-region database replication link (e.g., Aurora Global). During a major US-East outage, the DNS global traffic manager automatically shifts all US traffic to the EU-West region. Immediately, EU-West begins serving 5xx errors for thousands of users. What is 'Replication Lag Failover Corruption', and how do you prevent users from seeing inconsistent states during a regional failover?",
     "When US-East goes down, the asynchronous replication link breaks. If replication was lagging by 5 seconds, the EU-West database is permanently missing the last 5 seconds of US-East writes. When DNS shifts the US users to EU-West, a user who just created an account (or placed an order) in US-East will not exist in the EU-West database, causing immediate 5xx errors or broken states. To prevent this: 1) Active-Passive Pilot Light: Instead of automated active-active routing, enforce manual failover. 2) Write-Pinning: Ensure specific tenant IDs are strictly pinned to specific regions so their data isn't split across active writers. 3) Global Quorum (Spanner/CockroachDB): Use synchronous cross-region consensus, sacrificing write latency for absolute global consistency.",
     ["Identifies asynchronous replication lag causing missing data on the surviving region post-failover", "Explains the resulting 5xx errors from orphaned sessions or missing relational keys", "Proposes architectural fixes: manual failover, strict tenant-region pinning, or synchronous global consensus"],
     ["Claims the 5xx errors are caused by the DNS TTL caching old IP addresses"]),

    ("B67_1_2", "concept", "easy", "concept", ["Multi-Region Architecture", "DNS"],
     "Explain why relying solely on DNS TTL (Time-To-Live) for disaster recovery failover is inherently flawed during a regional outage.",
     "DNS TTL specifies how long resolvers and client browsers should cache a DNS record. If a region goes down, you might update Route 53 to point to the backup region. However, thousands of ISPs, enterprise proxies, and mobile operating systems blatantly ignore short TTLs (e.g., 60 seconds) to save bandwidth, caching the dead IP address for hours. Consequently, a massive percentage of users will remain routed to the dead region long after the DNS change. For true zero-downtime failover, you must use IP Anycast (where the network routes the same IP to the closest healthy endpoint) or a globally distributed load balancer (like AWS Global Accelerator) that masks the underlying regional endpoints behind static Anycast IPs.",
     ["Identifies that ISPs and client browsers frequently ignore or override short TTL values", "Explains that users will continue routing to the dead region due to stale caches", "Recommends Anycast IP routing or global network load balancers as the definitive solution"],
     ["Claims DNS TTL is flawed because it requires manual intervention from a network engineer"]),

    ("B67_1_3", "diagnose", "medium", "debugging", ["Multi-Region Architecture", "High Availability"],
     "You implement a multi-region disaster recovery strategy using a 'Warm Standby' architecture. The primary region goes offline. You trigger the failover to the secondary region, but the secondary region's application servers immediately crash due to OOM (Out of Memory) and CPU exhaustion within 30 seconds. What fundamental capacity planning mistake causes this, and how do you resolve it?",
     "The mistake is 'Thundering Herd' capacity mismatch. A 'Warm Standby' typically runs at a scaled-down capacity (e.g., 10% of the primary's nodes) to save costs. When DNS failover occurs, 100% of the global traffic slams into the scaled-down secondary region instantly. Autoscaling groups (which take 3-5 minutes to spin up new VMs and pass health checks) cannot react fast enough, and the existing nodes are instantly crushed by the traffic spike, causing cascading failures. Resolution: 1) Pre-scale the secondary region before updating DNS. 2) Implement aggressive rate-limiting/load-shedding at the edge during failover. 3) Move to a 'Hot Standby' architecture where the secondary is permanently scaled to handle at least 50-100% of the peak load.",
     ["Diagnoses 'Thundering Herd' destroying the scaled-down Warm Standby nodes", "Highlights the critical latency mismatch between traffic arrival and Autoscaling VM spin-up times", "Recommends pre-scaling, edge load-shedding, or shifting to Hot Standby architectures"],
     ["Suggests fixing the OOM by increasing the JVM heap size on the standby nodes"]),

    ("B67_1_4", "tradeoff", "hard", "tradeoff", ["Multi-Region Architecture", "State Management"],
     "What are the operational tradeoffs of using a 'Cell-Based Architecture' (where users are pinned to isolated, self-contained regional cells) versus a 'Global Megastore' architecture (where all regions read/write to a globally synchronized database cluster) for a massive global application?",
     "Cell-Based Architecture: Advantages include massive blast-radius reduction (an outage in Cell A cannot mathematically impact Cell B), perfect horizontal scalability, and localized low-latency data. Disadvantages: Severe complexity in cross-cell communication (if User A in Cell A needs to interact with User B in Cell B), and complex global analytics gathering. Global Megastore (e.g., Cassandra, Spanner): Advantages include simplified application logic (the database abstractly handles all global state and consistency) and easy global interactions. Disadvantages: Massive cross-region replication latency on writes, vulnerability to global schema migration failures, and the risk that a distributed consensus failure (e.g., split-brain) could take the entire global application offline simultaneously.",
     ["Identifies Cell-Based advantages: blast-radius isolation and low latency", "Identifies Cell-Based disadvantages: complex cross-cell networking and fragmented analytics", "Identifies Global Megastore tradeoff: simple application logic vs high cross-region latency and global failure risk"],
     ["Claims Cell-Based architectures are only used for mobile apps while Megastores are for web browsers"]),

    ("B67_1_5", "scenario", "medium", "scenario", ["Kubernetes", "Control Plane"],
     "During a routine rolling upgrade of a Kubernetes cluster from v1.24 to v1.25, the cluster enters a state where no new Pods can be scheduled, and existing Pods cannot be deleted. The kube-apiserver logs show massive etcd timeout errors and 'context deadline exceeded'. The etcd disk I/O is saturated. What causes this control-plane failure during upgrades, and how do you mitigate it?",
     "Kubernetes upgrades often involve automated controller reconciliations or data migrations (like migrating storage versions of Custom Resource Definitions). When the new kube-apiserver starts, it might trigger a massive burst of LIST or UPDATE calls to etcd to reconcile the cluster state with the new API versions. If the etcd cluster is running on slow disks (e.g., low IOPS SSDs), the sudden burst of write amplification overwhelms etcd's fsync capacity. Because the API server relies entirely on etcd, the entire control plane locks up. Mitigation: 1) Ensure etcd is backed by dedicated, high-IOPS NVMe SSDs; 2) Separate the etcd WAL (Write-Ahead Log) to a different physical disk than the data directory; 3) Throttle the upgrade process or use API Priority and Fairness to rate-limit intensive controllers.",
     ["Identifies upgrade-induced API reconciliation bursts saturating etcd disk IOPS", "Explains that etcd disk saturation causes API server lockup", "Recommends high-IOPS SSDs, dedicated WAL disks, or API Priority and Fairness"],
     ["Claims the upgrade failed because the worker nodes were not drained first"]),

    ("B67_1_6", "concept", "easy", "concept", ["Kubernetes", "Control Plane"],
     "What is the purpose of the kube-controller-manager in a Kubernetes cluster, and what happens to the worker nodes if it crashes?",
     "The kube-controller-manager is the core daemon that runs the background control loops (controllers) responsible for regulating the state of the cluster. It constantly compares the desired state (e.g., 'I want 3 replicas of this Deployment') with the actual state, and takes action to reconcile them (by creating/deleting Pods). If the controller-manager crashes, the worker nodes and existing Pods continue to run perfectly fine, serving user traffic without interruption. However, the cluster becomes 'brain dead': if a Pod crashes, it will not be restarted; if a Node dies, its Pods will not be rescheduled; and new Deployments cannot be created, because the reconciliation loop is offline.",
     ["Defines the controller-manager as the reconciliation loop enforcing desired state", "Explains that existing pods/nodes continue serving traffic normally during a crash", "Explains that the cluster becomes incapable of self-healing or processing new deployments"],
     ["Claims the worker nodes will immediately shut down if they lose contact with the controller-manager"]),

    ("B67_1_7", "diagnose", "hard", "debugging", ["Kubernetes", "Control Plane"],
     "You deploy an OPA Gatekeeper Admission Webhook to your Kubernetes cluster to enforce security policies. Suddenly, developers report that their generic kubectl apply commands are hanging for 30 seconds and then failing. Existing Pods are unaffected. How does a failing Admission Webhook cause cascading control-plane failures, and how do you configure it safely?",
     "An Admission Webhook intercepts API requests (like creating a Pod) *before* they are persisted to etcd. The kube-apiserver makes a synchronous HTTP call to the webhook pod. If the webhook pod is overloaded, misconfigured, or dead, the API server will wait for a timeout (default 30s) before failing the request. This completely breaks the cluster's ability to schedule anything, blocking deployments and auto-scaling. To configure safely: 1) Set failurePolicy: Ignore so the API server allows the request through if the webhook is down (failing open vs failing closed); 2) Set a strict, short timeoutSeconds (e.g., 2 seconds) to prevent API server thread exhaustion; 3) Use namespaceSelector to exempt critical system namespaces (kube-system) from the webhook to prevent deadlocks.",
     ["Identifies synchronous webhook interception blocking API persistence to etcd", "Explains API server thread exhaustion and the 30s default timeout causing deployment lockups", "Proposes failurePolicy: Ignore, timeoutSeconds reduction, and namespaceSelector exemptions"],
     ["Claims the webhook is blocking network traffic between the pods and the internet"]),

    ("B67_1_8", "tradeoff", "medium", "tradeoff", ["Kubernetes", "Architecture"],
     "What is the tradeoff of increasing the Kubernetes kube-apiserver flag --max-requests-inflight and --max-mutating-requests-inflight to handle a massive burst of CI/CD deployment traffic?",
     "These flags control the maximum number of concurrent read and write requests the API server will process before rejecting new requests with HTTP 429 Too Many Requests. Advantage: Increasing the limit allows the API server to absorb massive bursts of simultaneous deployments from heavily parallelized CI/CD pipelines without throttling the developer tools. Disadvantage: The API server consumes memory for every inflight request. More critically, every mutating request translates to an etcd transaction. If you increase the limits beyond what your etcd disk IOPS can handle, you transform a graceful API rejection (HTTP 429) into a catastrophic etcd timeout/crash, taking down the entire control plane for all users. It trades request rejection for severe systemic instability.",
     ["Defines the flags as controlling concurrent API request limits", "Identifies advantage: absorbing CI/CD bursts without 429 throttling", "Identifies severe disadvantage: overwhelming etcd IOPS and memory, crashing the entire control plane"],
     ["Claims increasing the flag allows hackers to bypass API authentication"]),

    ("B67_1_9", "scenario", "hard", "scenario", ["Multi-Region Architecture", "Networking"],
     "You operate a multi-region active-active Kubernetes environment. A user in Europe makes a request to eu.example.com, which hits a European ingress controller. However, trace logs reveal that the European ingress occasionally forwards the request to a backend Pod physically located in the US data center, adding 150ms of latency. How does this cross-region traffic leakage occur in a flat multi-cluster mesh, and how do you prevent it?",
     "This occurs in flat multi-cluster networking (e.g., Cilium Cluster Mesh or Istio Multi-Cluster) where Service endpoints are globally synchronized. By default, a Kubernetes Service load-balances randomly across all healthy Endpoints in the mesh, regardless of their physical geography. Therefore, the EU Ingress will randomly select a US Pod if the US cluster's endpoints are included in the global Service definition. To prevent this, you must implement Topology-Aware Routing (Topology Aware Hints in Kubernetes). This instructs the kube-proxy or CNI to prioritize routing traffic to endpoints within the same zone or region. The global mesh should only route cross-region as a fallback mechanism if the local regional endpoints fail or exceed capacity.",
     ["Identifies flat multi-cluster service synchronization causing random global endpoint selection", "Diagnoses the default round-robin behavior of Kubernetes Services ignoring geography", "Recommends Topology-Aware Routing / Hints to enforce local-region affinity"],
     ["Suggests blocking US IP addresses in the European firewall to force local routing"]),

    ("B67_1_10", "implement", "medium", "implement", ["Multi-Region Architecture", "Data Management"],
     "Your architecture team mandates that European user data must never leave the European Union for GDPR compliance. However, your application uses a single global API gateway endpoint (api.example.com). How do you architect the DNS, Gateway, and Database layers to guarantee strict regional data residency while maintaining a single global URL?",
     "1) DNS Layer: Configure Latency-based or Geolocation-based routing in DNS (e.g., Route53). EU users resolve api.example.com to the EU API Gateway IP; US users resolve to the US IP. 2) Gateway Layer: Since DNS geolocation is not 100% accurate, the API Gateway must intercept the request, inspect the user's JWT token or auth metadata to determine their home region. If an EU user accidentally hits the US Gateway, the US Gateway must issue an HTTP 307 redirect (or transparently reverse-proxy) the request to the EU Gateway. 3) Database Layer: Implement strictly isolated regional databases (No Global Megastore). The US database literally cannot contain EU tables, physically preventing any cross-region data leakage at the storage tier.",
     ["Proposes DNS Geolocation routing as the first line of regional affinity", "Proposes API Gateway JWT/auth inspection and redirecting to catch DNS misroutes", "Mandates physically isolated regional databases to guarantee storage residency"],
     ["Suggests encrypting the EU data so the US servers can't read it, which violates residency"]),

    ("B67_1_11", "diagnose", "hard", "debugging", ["Kubernetes", "Control Plane"],
     "An aggressive custom Kubernetes operator watches thousands of Secrets across all namespaces. When the operator pod restarts, the entire kube-apiserver CPU spikes to 100%, and memory usage balloons until the API server is OOMKilled. What is a 'Watch Cache' / 'Reconciliation Storm', and how should the operator be rewritten to prevent crashing the control plane?",
     "When a Kubernetes operator starts, it performs an initial LIST call to fetch all objects it cares about, followed by opening a WATCH stream for deltas. If an operator requests thousands of large Secrets simultaneously without resource versions, it bypasses the API server's efficient Watch Cache. The API server must deserialize massive amounts of data directly from etcd into memory, serialize it into JSON, and send it to the operator, causing massive CPU/RAM spikes and OOMKills (a Initialization Storm). To fix the operator: 1) Use standard Kubernetes Informers, which handle caching and pagination automatically; 2) Utilize LIMIT and CONTINUE tokens in the LIST request to paginate the initial sync; 3) Set ResourceVersion=0 to force the API server to serve the LIST from its internal memory cache rather than hammering etcd.",
     ["Identifies the initial unpaginated LIST call overwhelming the API server memory/CPU", "Explains the bypass of the API Watch Cache forcing direct etcd deserialization", "Recommends Informers, pagination (LIMIT/CONTINUE), or ResourceVersion=0 caching"],
     ["Claims the operator is mining cryptocurrency and should be deleted"]),

    ("B67_1_12", "concept", "easy", "concept", ["Kubernetes", "Control Plane"],
     "In Kubernetes, what is the role of the kube-scheduler, and how does it determine which Node a new Pod should run on?",
     "The kube-scheduler watches for newly created Pods that have an empty nodeName field. It executes a two-step process: 1) Filtering (Predicates): It filters out nodes that cannot mathematically run the pod (e.g., nodes without enough CPU/Memory, nodes that don't match nodeSelector or affinity rules, or nodes with incompatible taints). 2) Scoring (Priorities): It ranks the remaining eligible nodes based on optimization algorithms (e.g., preferring nodes that already have the container image pulled, or spreading pods across different availability zones to maximize high availability). It selects the node with the highest score and binds the pod to it.",
     ["Defines the scheduler as the component that assigns Nodes to pending Pods", "Explains the two-step algorithm: Filtering (Predicates) and Scoring (Priorities)", "Mentions specific criteria like resource requests, taints, and affinity rules"],
     ["Claims the scheduler actively monitors CPU usage and moves running pods around automatically"]),

    ("B67_1_13", "scenario", "medium", "scenario", ["Kubernetes", "High Availability"],
     "A production Kubernetes cluster is running perfectly. Suddenly, a network partition occurs, completely isolating the three master nodes (Control Plane) from the 50 worker nodes. What happens to the running applications on the worker nodes during the partition, and what happens when the partition heals 30 minutes later?",
     "During the partition, the applications on the worker nodes continue running perfectly. The kubelet on each node maintains the local containers, and kube-proxy maintains the local iptables/IPVS rules, so inter-pod traffic and external ingress traffic (if externally load balanced) remain functional. However, the Control Plane loses contact with the kubelets. After 5 minutes (pod-eviction-timeout), the Control Plane marks all nodes as NotReady and attempts to reschedule all pods to other nodes (which it can't, because all nodes are unreachable). When the partition heals, a severe race condition occurs: the Control Plane suddenly reconnects, realizes the original pods are still running on the nodes, and must rapidly reconcile its internal rescheduled state by terminating the duplicate 'ghost' pods it tried to create during the outage.",
     ["Explains that worker nodes operate autonomously during partition (apps stay up)", "Explains the control plane marks nodes NotReady and attempts eviction/rescheduling", "Identifies the reconciliation race condition upon healing where duplicate pods must be terminated"],
     ["Claims the worker nodes will reboot themselves after 5 minutes of lost contact"]),

    ("B67_1_14", "tradeoff", "medium", "tradeoff", ["Multi-Region Architecture", "Disaster Recovery"],
     "What is the tradeoff between a 'Pilot Light' disaster recovery architecture and a 'Multi-Region Active-Active' architecture in terms of RTO (Recovery Time Objective) and cost?",
     "Pilot Light Architecture: A minimal version of the environment runs in the secondary region (e.g., active database replication, but core application servers are turned off or scaled to zero). Tradeoff: Drastically lower cloud infrastructure costs, but a high RTO (Recovery Time Objective). It takes 10-30 minutes to spin up the VMs/Containers, validate health, and cut over DNS during a disaster. Multi-Region Active-Active: Both regions are scaled up and actively serving live production traffic 24/7. Tradeoff: Zero RTO (failover is instantaneous via DNS/Anycast routing), but it requires paying for 2x the infrastructure costs, and introduces massive architectural complexity regarding cross-region database consistency and split-brain resolution.",
     ["Defines Pilot Light (data synced, compute off) vs Active-Active (compute 100% live)", "Contrasts the massive cost savings of Pilot Light with its high 10-30 minute RTO", "Contrasts the Zero RTO of Active-Active with its 2x cost and high architectural complexity"],
     ["Confuses RTO (Recovery Time) with RPO (Recovery Point)"]),

    ("B67_1_15", "implement", "hard", "implement", ["Multi-Region Architecture", "Networking"],
     "You are designing a globally distributed application on AWS. You need static IP addresses that users around the world can whitelist in their corporate firewalls. You also need user traffic to route to the closest healthy AWS region (US or EU) automatically, failing over in milliseconds if a region dies. How do you implement this using AWS Global Accelerator?",
     "AWS Global Accelerator provisions two static, Anycast IPv4 addresses. Implementation: 1) You provide these two static IPs to your clients for firewall whitelisting. 2) You configure Global Accelerator with two Endpoint Groups (one for the US region ALBs, one for the EU region ALBs). 3) Traffic routing: When a user connects, BGP Anycast routes their traffic to the physically closest AWS Edge Location. From the edge, the traffic traverses the dedicated, highly optimized AWS global fiber backbone directly to the closest healthy Endpoint Group. 4) Failover: Global Accelerator continuously health-checks the regional ALBs. If the EU region fails, the Accelerator immediately reroutes the edge traffic across the AWS backbone to the US region, bypassing the severe limitations and caching delays of DNS-based failover.",
     ["Identifies AWS Global Accelerator providing static Anycast IP addresses for whitelisting", "Explains routing traffic over the AWS global fiber backbone rather than the public internet", "Explains sub-second Anycast/BGP failover bypassing DNS TTL caching entirely"],
     ["Recommends using an Elastic IP attached to an EC2 instance in a single region"]),

    ("B67_1_16", "diagnose", "medium", "debugging", ["Kubernetes", "Architecture"],
     "A team creates a Kubernetes Custom Resource Definition (CRD) Widget with version v1alpha1. Six months later, they introduce v1 with a completely different schema structure. When a legacy script attempts to read a v1alpha1 Widget, the API server crashes the request. How do you implement a 'CRD Conversion Webhook' to support multiple API versions of a custom resource simultaneously?",
     "When a CRD has multiple versions, Kubernetes stores only *one* version physically in etcd (the storage version). If a client requests an older or newer version, the kube-apiserver must convert the JSON on the fly. Because Kubernetes doesn't understand your custom schema changes (e.g., combining firstName and lastName into fullName), you must provide a CRD Conversion Webhook. Implementation: You deploy an HTTPS server running your custom logic. In the CRD manifest, you define the conversion section pointing to this webhook service. When the API server receives a request for v1alpha1, it sends the v1 etcd data to your webhook. Your code translates the schema back to v1alpha1 and returns it to the API server, which then serves it to the legacy client, ensuring backward compatibility.",
     ["Explains that Kubernetes only stores one physical version of a CRD in etcd", "Defines the CRD Conversion Webhook as translating JSON schemas on-the-fly for clients", "Highlights the requirement of a custom HTTPS server to map the legacy fields to the new fields"],
     ["Suggests writing a bash script to update the legacy scripts to use the new v1 version"]),

    ("B67_1_17", "concept", "easy", "concept", ["Multi-Region Architecture", "State Management"],
     "In distributed systems, what is 'Split-Brain', and why is it a critical risk during multi-region network partitions?",
     "Split-Brain occurs when the network link between two active data centers (or database nodes) completely fails, but both data centers remain online and serving clients. Because they cannot communicate, neither node knows if the other is dead or just unreachable. If the system is not designed carefully, both regions will assume they are the active Primary and begin accepting read and write operations independently. This results in severe data divergence and conflicting state (e.g., the same inventory item sold twice). To prevent Split-Brain, distributed systems use Consensus Algorithms (like Raft or Paxos) requiring a strict Quorum (majority vote) to accept writes, or rely on a centralized tie-breaker/witness node.",
     ["Defines Split-Brain as isolated nodes both acting as the primary writer during a network partition", "Identifies severe data divergence and state conflicts as the critical risk", "Mentions Consensus Algorithms (Quorum/Raft/Paxos) as the standard prevention mechanism"],
     ["Claims Split-Brain is a CPU multi-threading error in the database kernel"]),

    ("B67_1_18", "scenario", "medium", "scenario", ["Kubernetes", "Control Plane"],
     "You are securing a Kubernetes cluster. You disable anonymous access and enforce strict RBAC. However, a security audit reveals that if an attacker compromises any single worker node, they can extract the kubelet TLS certificate and use it to read all Secrets across the entire cluster. What configuration feature is missing on the kube-apiserver to restrict node blast radius?",
     "The missing configuration is the NodeRestriction admission controller. By default, a valid kubelet certificate authenticates as the system:nodes group, which technically has permission to read Secrets and modify Node objects. Without restrictions, a compromised worker node can impersonate other nodes or request Secrets belonging to Pods that aren't even scheduled on it. By enabling the --enable-admission-plugins=...,NodeRestriction flag on the kube-apiserver, the control plane strictly enforces that a kubelet can ONLY read Secrets/ConfigMaps that are explicitly mounted to Pods currently assigned to that specific node, and can ONLY modify its own Node object status, massively reducing the blast radius of a node compromise.",
     ["Identifies the NodeRestriction admission controller as the missing component", "Explains that default kubelet certs grant broad cluster-wide secret reading permissions", "Explains NodeRestriction limits secret access exclusively to pods scheduled on that specific node"],
     ["Recommends encrypting the hard drives of the worker nodes to prevent certificate theft"]),

    ("B67_1_19", "tradeoff", "medium", "tradeoff", ["Kubernetes", "Control Plane"],
     "What is the tradeoff of running the Kubernetes Control Plane (etcd, API server, controller-manager) internally as static pods on the master nodes versus running them as standard pods in an external management cluster (Kube-in-Kube architecture)?",
     "Static Pods on Master Nodes: The traditional approach where kubelet on the master node directly manages the control plane pods. Advantages: Self-contained, simpler to bootstrap (kubeadm), and physically isolates control plane resources. Disadvantages: Harder to upgrade, scale, or automate repairs, as you must manage raw VMs and static manifests via Ansible/SSH. Kube-in-Kube (e.g., Cluster API, Hosted Control Planes): The control plane is deployed as standard Deployments/StatefulSets inside a completely separate 'Management' Kubernetes cluster. Advantages: Infinite scalability and automation. You manage tenant control planes using standard K8s tooling (HPA, rolling updates, CRDs). Disadvantages: 'Turtles all the way down' complexity. If the management cluster fails, you lose the ability to manage or recover hundreds of downstream tenant clusters simultaneously, creating a massive single point of failure.",
     ["Defines Static Pods as host-managed isolation vs Kube-in-Kube as fleet-managed control planes", "Highlights the automation and scaling benefits of using K8s to manage K8s (Cluster API)", "Identifies the cascading single-point-of-failure risk if the management cluster goes down"],
     ["Claims Kube-in-Kube runs the worker nodes inside Docker containers for local testing"]),

    ("B67_1_20", "diagnose", "medium", "debugging", ["Multi-Region Architecture", "DNS"],
     "A company uses Route53 Health Checks to manage DNS failover between a Primary and Secondary region. A microservice in the Primary region starts experiencing 30% packet loss and high latency, but the health checks still return HTTP 200 OK because the service eventually responds within the 5-second timeout. Users experience terrible lag, but the failover never triggers. How do you redesign the health check architecture to handle 'Gray Failures'?",
     "This is a classic 'Gray Failure' (partial degradation). Simple endpoint health checks (HTTP GET /health) only test binary UP/DOWN states. Because the app eventually responds, DNS assumes it's healthy. To fix this, you must shift from binary endpoint checks to Metric-Based Health Checks (Composite Health Checks). Redesign: 1) The application emits granular metrics (e.g., p99 latency, 5xx error rate) to CloudWatch/Prometheus. 2) You create an alarm that triggers if p99 latency exceeds 2 seconds or error rate exceeds 5%. 3) You bind the Route53 Health Check directly to the state of this Alarm. If the region gracefully degrades, the alarm fires, the Route53 check fails, and traffic is swiftly routed away from the struggling region before it completely crashes.",
     ["Diagnoses 'Gray Failures' bypassing binary UP/DOWN endpoint health checks", "Recommends Metric-Based Health Checks tied to p99 latency or error rate alarms", "Explains proactively triggering failover via alarms rather than waiting for hard endpoint timeouts"],
     ["Suggests reducing the DNS timeout to 10 milliseconds so it fails instantly"])
]

def run_batch():
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 1).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Backend Developer", "Site Reliability Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Cloud/Kubernetes",
            "topic": q[4][0] if len(q[4]) > 0 else "General",
            "category": "Infrastructure Engineering",
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
            
    with open(OUT, "r", encoding="utf-8") as f:
        final_existing = [json.loads(line) for line in f if line.strip()]
        
    role_counts = Counter(r["primary_role"] for r in final_existing)
    
    print("\n========================================")
    print("POST-BATCH AUDIT PART 1")
    print("========================================")
    print(f"Batch: 67 Part 1")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
