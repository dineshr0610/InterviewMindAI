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
    ("B67_3_1", "concept", "medium", "concept", ["Supply-Chain Security", "CI/CD"],
     "Explain the concept of 'Build Provenance' in the context of the SLSA (Supply-chain Levels for Software Artifacts) framework. Why is a standard SHA256 hash of a Docker image insufficient for supply-chain security?",
     "A standard SHA256 hash only guarantees the integrity of the *final* artifact (i.e., the file hasn't been corrupted in transit). It provides zero information about *how* it was made. An attacker could compromise your Jenkins server, inject malware into the build process, and the resulting malicious Docker image would still generate a perfectly valid SHA256 hash. Build Provenance is an unforgeable, cryptographically signed metadata document that proves exactly how the artifact was built. It securely records the exact source code commit, the specific build runner identity, the compiler versions, and the build steps executed. It guarantees not just artifact integrity, but the integrity of the entire build process that produced it.",
     ["Distinguishes between artifact integrity (SHA256) and process integrity (Provenance)", "Defines provenance as a signed metadata document detailing the exact build environment and inputs", "Explains that compromised build servers can produce malicious artifacts with valid hashes"],
     ["Claims Build Provenance is a Git feature that tracks who committed the code"]),

    ("B67_3_2", "scenario", "hard", "scenario", ["Supply-Chain Security", "CI/CD"],
     "Your company uses an internal PyPI proxy (like Artifactory) to host proprietary Python packages (e.g., company-auth-lib), mixed with a public PyPI mirror. An attacker registers the exact same package name company-auth-lib on the public internet PyPI with an artificially massive version number (v99.0.0). During the next CI/CD build, the build servers automatically download the attacker's malicious package instead of the internal one. What is this attack called, and how do you architect the CI/CD pipeline and artifact repository to prevent it?",
     "This is a 'Dependency Confusion' (or Namespace Substitution) attack. Package managers like pip or npm often default to fetching the *highest* version number across all configured registries. By publishing v99.0.0 publicly, the attacker tricks the build server into pulling the malicious external payload rather than the internal v1.0.0. To prevent this: 1) Repository Routing/Scoping: Configure Artifactory to strictly route the @company namespace (or specific prefix) *only* to the internal local repository, completely disabling upstream proxying for those names. 2) Lockfiles: Enforce strict cryptographic hash-checking in requirements.txt or package-lock.json so the build fails if the package hash changes unexpectedly. 3) Public Reservation: Register empty placeholder packages with your internal names on the public registry so attackers cannot claim them.",
     ["Identifies the attack as 'Dependency Confusion' or Namespace Substitution", "Explains the package manager behavior of defaulting to the highest version number globally", "Proposes architectural fixes: strict namespace routing, cryptographic lockfiles, or public placeholder registration"],
     ["Suggests blocking external internet access completely on the build servers, which breaks all public dependencies"]),

    ("B67_3_3", "tradeoff", "medium", "tradeoff", ["Advanced Observability", "Architecture"],
     "What is the tradeoff of using a 'Head-Based Sampling' strategy versus a 'Tail-Based Sampling' strategy in a massive distributed tracing architecture (e.g., OpenTelemetry / Jaeger)?",
     "Tracing every single request in a high-volume system is cost-prohibitive. Head-Based Sampling makes the keep/drop decision at the very *beginning* of the request (e.g., the API Gateway randomly selects 1% of requests to trace). Advantage: Extremely cheap, zero memory overhead, and highly scalable. Disadvantage: It randomly drops 99% of requests, meaning you will almost certainly drop the traces for rare, intermittent errors or latency spikes that you actually need to debug. Tail-Based Sampling makes the keep/drop decision at the very *end* of the request lifecycle, after all spans have completed. Advantage: It guarantees you keep 100% of traces containing errors or high latency, while dropping 99% of the boring, successful traffic. Disadvantage: Extremely expensive and complex. It requires deploying massive distributed memory buffers (e.g., OpenTelemetry Collectors) to hold all spans in RAM until the trace completes before making the decision.",
     ["Defines Head-Based sampling as an upfront random decision (cheap, scalable, but misses rare errors)", "Defines Tail-Based sampling as a delayed decision based on trace outcome (expensive/complex, but captures 100% of errors)", "Highlights the massive RAM buffering requirement for Tail-Based sampling architectures"],
     ["Claims Tail-Based sampling only traces the database, while Head-Based traces the frontend"]),

    ("B67_3_4", "diagnose", "hard", "debugging", ["Advanced Observability", "Prometheus"],
     "You deploy a new microservice that emits a Prometheus metric http_requests_total. To track granular customer usage, the developer adds a user_id label to this metric. Within 2 hours, the centralized Prometheus server runs out of memory and crashes, triggering a Sev-1 outage across the observability stack. What is 'High Cardinality', why did it crash Prometheus, and how do you restructure the observability data?",
     "This is a 'High Cardinality Explosion'. Prometheus is a Time Series Database (TSDB). A unique time series is created for every single combination of metric name and label values. If your application has 500,000 users, adding user_id to the metric instantly creates 500,000 unique time series in Prometheus RAM. Because Prometheus stores recent data in memory, this sudden massive state explosion exhausts the server's RAM and crashes it. Metrics are designed for aggregate system health, not individual user tracking. To restructure: 1) Remove unbounded labels (like user_id, email, or session_id) from Prometheus metrics. Use bounded labels (like http_status=200/500, region=us/eu). 2) Move the highly granular user_id data into structured Logging (e.g., ELK/Splunk) or Distributed Tracing (e.g., Jaeger/Honeycomb), which are specifically designed to handle infinite cardinality data.",
     ["Identifies 'High Cardinality Explosion' from unbounded label values creating massive state permutations", "Explains that Prometheus stores every unique label combination as a distinct time series in RAM", "Recommends removing unbounded labels and shifting granular tracking to Logging or Distributed Tracing"],
     ["Recommends increasing the Prometheus server RAM to 1TB so it can track every user"]),

    ("B67_3_5", "implement", "medium", "implement", ["Supply-Chain Security", "CI/CD"],
     "A developer compromises their local laptop, and an attacker steals their GitHub SSH key. The attacker pushes malicious code to the main branch, which instantly deploys to production via the GitOps pipeline. How do you implement 'Branch Protections' and 'Required Reviews' to break this automated attack chain?",
     "An automated pipeline is only as secure as the commit that triggers it. To break the chain, you must implement strict Branch Protection rules on the main (or production) branch. 1) Require Pull Requests: Developers can no longer push directly to main; they must push to a feature branch and open a PR. 2) Require Approvals: The PR must be approved by at least one (or two) other authenticated human engineers. This ensures the attacker's code cannot be merged without a second engineer reviewing the malicious payload. 3) Require Status Checks: Enforce that automated CI security scanners (SAST/Linting) must pass before merging. 4) Code Owners: Require approvals specifically from the designated security or architecture team if critical infrastructure files (like deploy.yaml) are modified.",
     ["Proposes enforcing PRs to prevent direct pushes to the production branch", "Proposes mandatory multi-party review (approvals) to break single-actor compromise chains", "Proposes required CI status checks and Code Owners for critical infrastructure files"],
     ["Suggests turning off the GitOps pipeline entirely and doing manual FTP deployments"]),

    ("B67_3_6", "concept", "easy", "concept", ["Advanced Observability", "SRE"],
     "Explain the difference between the RED method and the USE method in Site Reliability Engineering (SRE) observability. Which one focuses on the user experience, and which focuses on the infrastructure?",
     "The RED method (Rate, Errors, Duration) is used for monitoring Services. It measures the Request Rate (traffic), Error Rate (failures), and Duration (latency). RED focuses strictly on the User Experience: is the application fast and successful for the client? The USE method (Utilization, Saturation, Errors) is used for monitoring Infrastructure/Resources. It measures Utilization (e.g., CPU is 80% busy), Saturation (e.g., CPU run queue is backing up), and Errors (e.g., disk I/O read failures). USE focuses strictly on the underlying hardware capacity and health. When debugging an incident, SREs typically start with RED (to confirm user impact) and drill down into USE (to find the hardware/resource root cause).",
     ["Defines RED (Rate, Errors, Duration) as service-level, user-experience focused", "Defines USE (Utilization, Saturation, Errors) as resource-level, infrastructure focused", "Explains the debugging hierarchy: spotting impact via RED, finding the cause via USE"],
     ["Claims RED stands for Redundancy, Encryption, and Deployment"]),

    ("B67_3_7", "scenario", "medium", "scenario", ["Advanced Observability", "Tracing"],
     "A user reports that adding an item to their cart is incredibly slow. You check the backend logs, and the CartService shows a processing time of only 50ms. However, the user's browser network tab shows the API call taking 4.5 seconds. How do you use Distributed Tracing (e.g., W3C Trace Context) to bridge this massive visibility gap between the frontend client and the backend service?",
     "Logs alone cannot connect the client's experience to the backend execution. The visibility gap (4.45 seconds) is likely hidden in network transit, API Gateway routing, WAF inspection, or load balancer queues. To bridge this, you must implement End-to-End Distributed Tracing starting at the browser. 1) The Frontend Javascript generates a unique traceparent ID and injects it into the HTTP headers of the outbound API request. 2) The API Gateway, Load Balancer, and Backend CartService all extract this header, append their own local span execution times to the trace, and propagate the header downstream. 3) By visualizing the full trace in a tool like Jaeger, you can immediately see the entire 4.5-second waterfall, identifying exactly which middleware component (e.g., a struggling WAF or stalled DNS lookup) is responsible for the missing 4.45 seconds.",
     ["Identifies generating the Trace ID natively in the browser/frontend client", "Explains header propagation (traceparent) forcing all middleware/gateways to participate in the trace", "Explains analyzing the trace waterfall to locate latency outside the backend code"],
     ["Claims tracing is useless here and you should just upgrade the backend database"]),

    ("B67_3_8", "diagnose", "hard", "debugging", ["Supply-Chain Security", "CI/CD"],
     "You implement a hermetic build system. The build script is `docker build -t my-app:latest .`. However, every time you run the build on the same exact source code commit, the output Docker image produces a completely different SHA256 digest. Why is this build fundamentally non-reproducible, and what commands inside the Dockerfile typically destroy reproducibility?",
     "A build is non-reproducible if compiling the exact same source code produces different binary artifacts. This destroys trust, because you cannot cryptographically verify if an image was tampered with or just built at a different time. A docker build naturally destroys reproducibility through several vectors: 1) Unpinned dependencies: Running apt-get update && apt-get install python3 or npm install (without a lockfile) fetches whatever happens to be the latest version on the internet at that exact millisecond. 2) Timestamps: The compiler or archiving tools (like tar) embed the current system build time into the binary metadata. 3) Dynamic remote fetches: Downloading a script via curl https://example.com/install.sh | bash during the build guarantees different results if the remote file changes. To achieve reproducibility, you must strictly pin all package hashes, use lockfiles, and strip embedded timestamps (e.g., using SOURCE_DATE_EPOCH).",
     ["Identifies unpinned package managers dynamically fetching different versions", "Identifies embedded system timestamps inside binaries or archives altering the file hash", "Prescribes strict dependency hash pinning, lockfiles, and timestamp stripping (SOURCE_DATE_EPOCH)"],
     ["Suggests the Docker daemon is broken and needs to be reinstalled"]),

    ("B67_3_9", "tradeoff", "medium", "tradeoff", ["Advanced Observability", "Alerting"],
     "What is the tradeoff of configuring alerts based on static thresholds (e.g., 'Alert if CPU > 90%') versus configuring Service Level Objective (SLO) Burn-Rate alerts (e.g., 'Alert if 5% error budget is burned in 1 hour')?",
     "Static Thresholds: Advantages: Extremely easy to set up and intuitive to understand. Disadvantages: Highly prone to false positives (alert fatigue). A CPU hitting 95% for 2 minutes during a batch job might have zero impact on users, but it still wakes up the on-call engineer at 3 AM. It also misses creeping degradations (e.g., CPU sits at 89% while users experience terrible latency). SLO Burn-Rate Alerts: Advantages: They strictly alert based on actual user impact. If the application handles the 95% CPU spike without failing user requests, no alert fires. If the error rate slightly elevates but threatens to exhaust the monthly error budget within hours, it triggers an alert. Disadvantages: Highly complex to implement (requires complex PromQL math over multiple time windows) and requires mature organizational agreement on what the actual user-facing SLOs should be.",
     ["Contrasts static thresholds (easy but prone to false positives/alert fatigue) with SLO burn-rate alerts", "Highlights that SLOs alert strictly based on actual user-impact, ignoring benign resource spikes", "Identifies the high mathematical and organizational complexity of implementing SLO burn-rates"],
     ["Claims static thresholds are for hardware and SLOs are only for billing metrics"]),

    ("B67_3_10", "implement", "medium", "implement", ["Supply-Chain Security", "CI/CD"],
     "Your CI/CD pipeline builds a Docker image and pushes it to an elastic container registry (ECR). How do you implement cryptographic signing (e.g., using Sigstore Cosign) to ensure the Kubernetes cluster only runs images that were explicitly generated by your trusted CI pipeline?",
     "1) CI/CD Signing: Inside the GitHub Actions pipeline, after the docker build and docker push steps, execute the cosign sign command. Cosign uses keyless signing (via OIDC identity) or a private KMS key to cryptographically sign the specific image digest (SHA256). The signature is pushed to the OCI registry alongside the image. 2) Cluster Enforcement: Install an Admission Controller webhook in the Kubernetes cluster (like Kyverno, OPA Gatekeeper, or the Sigstore Policy Controller). 3) Policy Definition: Create a cluster policy requiring all pods deployed to the prod namespace to have a valid Cosign signature matching the public key of the trusted CI/CD pipeline. If an attacker manually pushes a malicious image to the registry and attempts to deploy it, the Admission Controller will reject the pod because the cryptographic signature is missing or invalid.",
     ["Proposes signing the image digest via tools like Cosign directly within the CI/CD pipeline", "Proposes an Admission Controller (Kyverno/Gatekeeper) to enforce policies at the cluster edge", "Explains that unsigned or maliciously modified images will be rejected before scheduling"],
     ["Suggests password-protecting the Docker registry so attackers can't download the image"]),

    ("B67_3_11", "concept", "easy", "concept", ["Advanced Observability", "Tracing"],
     "In the context of distributed tracing and metrics, what is an 'Exemplar', and how does it radically accelerate incident response?",
     "An Exemplar is a specific, recorded trace ID that is permanently attached to a point-in-time metric aggregation. For example, if a Prometheus metric shows that the p99 latency spiked to 5 seconds at 10:04 AM, an Exemplar attaches a single, real-world Trace ID (e.g., trace_id: 1234abcd) that actually experienced that 5-second delay. It radically accelerates incident response because the engineer doesn't have to manually hunt through millions of logs or traces in Jaeger trying to find a slow request from 10:04 AM. They simply click the data point on the Prometheus Grafana chart, and the Exemplar instantly links them directly to the exact distributed trace showing the root cause of the latency spike.",
     ["Defines an Exemplar as a specific Trace ID embedded inside an aggregated metric data point", "Explains the elimination of manual correlation (hunting for matching logs/traces)", "Highlights the click-through acceleration from high-level dashboards directly to root-cause traces"],
     ["Claims an Exemplar is a mock API endpoint used for load testing"]),

    ("B67_3_12", "scenario", "medium", "scenario", ["Supply-Chain Security", "CI/CD"],
     "Your infrastructure is defined entirely in Terraform. You use a centralized Jenkins server to run terraform apply. An attacker exploits a vulnerability in a developer's application code to gain RCE (Remote Code Execution) on the application pod. However, a few days later, the attacker uses this application compromise to steal the Terraform AWS admin credentials from the Jenkins server. How is this lateral movement possible, and how do you isolate CI/CD infrastructure from application environments?",
     "This lateral movement is likely caused by deploying the Jenkins runners/agents inside the exact same Kubernetes cluster (or VPC network) as the production application workload. If Jenkins and the App share the same cluster, an attacker with RCE on the app pod can potentially exploit internal network trust, weak RBAC, or unpatched cluster vulnerabilities to access the Jenkins runner pods, steal the injected Terraform AWS credentials, and escalate to full cloud account takeover. To prevent this: CI/CD infrastructure must be strictly isolated. Build servers and runners should operate in a completely separate, hardened AWS Account or dedicated Management VPC. They should communicate with the production environment only via strictly controlled IAM roles (cross-account assume-role) or secure deployment APIs, ensuring a compromise in production cannot pivot backward into the deployment pipeline.",
     ["Diagnoses lateral movement caused by co-locating CI runners inside the production workload cluster", "Explains that compromising an app pod exposes highly privileged CI/CD credentials sharing the same environment", "Prescribes strict physical and network isolation (separate AWS accounts or VPCs) for CI/CD infrastructure"],
     ["Suggests the attacker guessed the Jenkins password because it was 'admin123'"]),

    ("B67_3_13", "diagnose", "hard", "debugging", ["Advanced Observability", "Metrics"],
     "You configure Prometheus to scrape a heavily loaded microservice every 5 seconds. The microservice occasionally experiences severe 2-second CPU freezes (garbage collection pauses). However, your Prometheus CPU utilization graphs appear perfectly smooth, never showing the 100% CPU spikes, and no alerts fire. Why is Prometheus completely blind to these massive CPU spikes, and how do you achieve true visibility?",
     "Prometheus is suffering from the 'Nyquist-Shannon / Aliasing' problem due to its pull-based scraping interval. If a 2-second CPU spike occurs exactly *between* the 5-second Prometheus scrapes, Prometheus literally never sees it. Furthermore, CPU metrics in Linux are typically exposed as cumulative counters (e.g., total CPU seconds consumed). Prometheus calculates the rate of this counter over time. Over a 5-second window, a 2-second freeze combined with 3 seconds of idle time mathematically averages out to a smooth, non-alarming 40% CPU utilization. To achieve true visibility into micro-bursts and GC pauses: 1) You must rely on application-level profiling (e.g., continuous profiling tools like Pyroscope or eBPF) which sample CPU state at 100Hz (10 milliseconds); or 2) Monitor the specific GC Pause Duration metrics exposed by the runtime (e.g., JVM jvm_gc_pause_seconds_sum), which capture the exact duration of the freeze regardless of when Prometheus scrapes it.",
     ["Identifies Aliasing/Averaging caused by a scrape interval larger than the spike duration", "Explains that rate calculations over 5-second windows mathematically smooth out micro-bursts", "Recommends continuous profiling (eBPF/Pyroscope) or runtime-specific GC duration metrics"],
     ["Claims Prometheus ignores spikes because it is designed for long-term storage, not real-time alerting"]),

    ("B67_3_14", "tradeoff", "medium", "tradeoff", ["Supply-Chain Security", "Architecture"],
     "What is the tradeoff of relying on automated SAST/DAST (Static/Dynamic Application Security Testing) scanning directly in the CI/CD blocking path versus shifting the security scanning to an asynchronous, out-of-band process?",
     "Synchronous (Blocking) CI/CD Scanning: Advantages: Maximum security posture. Vulnerable code is mathematically prevented from ever merging or deploying to production, as the build strictly fails if a flaw is found. Disadvantages: Severe developer friction. SAST/DAST scans can take 10-30 minutes to run. Blocking the pipeline for every commit destroys rapid iteration, creates massive deployment queues, and false positives halt production hotfixes. Asynchronous (Out-of-band) Scanning: Advantages: Developers experience blazing fast CI/CD pipelines (seconds to deploy), maintaining high deployment velocity. Disadvantages: The vulnerability is successfully deployed to production *before* the security team is alerted. The system relies on rapid incident response and rollbacks rather than absolute prevention.",
     ["Contrasts synchronous blocking (absolute prevention but destroys developer velocity) with asynchronous scanning", "Identifies the risk of asynchronous: vulnerabilities are successfully deployed and require rapid reactive rollbacks", "Highlights the severe friction of 30-minute DAST scans blocking emergency production hotfixes"],
     ["Claims DAST scanning can only be run manually by a penetration tester"]),

    ("B67_3_15", "implement", "hard", "implement", ["Advanced Observability", "Logging"],
     "A high-volume payment processing system generates 50TB of logs per day. Sending all these logs to a centralized indexing platform (like Splunk or Datadog) costs $100,000 a month. However, 90% of the logs are repetitive HTTP 200 OK access logs, while only 10% are critical errors or payment state transitions. How do you design an Observability Pipeline to reduce costs by 80% without losing the ability to debug payment failures or audit traffic?",
     "You must implement an Observability Pipeline / Telemetry Router (like Vector, Fluentd, or Cribl LogStream) sitting between the applications and the expensive SaaS indexer. Implementation: 1) Drop/Sample: The pipeline inspects the log payloads in real-time. For generic HTTP 200 access logs, it applies dynamic sampling (e.g., only forwarding 1 in every 100 successful logs to the expensive indexer). 2) Metricize: Before dropping the 99 HTTP 200 logs, the pipeline converts them into a cheap Prometheus metric (e.g., rate(http_requests_total)), preserving the exact traffic volume data without paying for log storage. 3) Route to Cold Storage: The pipeline simultaneously forks 100% of the raw, un-sampled logs and writes them directly to cheap AWS S3/Glacier object storage. If an audit is required, data can be queried later using Athena. 4) Whitelist Critical Logs: Any log containing level: error or event: payment_transition bypasses sampling and is routed 100% to the expensive real-time indexer for immediate debugging.",
     ["Proposes a telemetry router (Vector/Cribl) to intercept and mutate logs pre-ingestion", "Proposes dynamic sampling (dropping repetitive logs) and converting them into cheap metrics", "Proposes dual-routing: pushing 100% of raw logs to cheap S3 cold storage for compliance, while whitelisting only errors to the expensive SaaS indexer"],
     ["Suggests turning off logging completely and relying only on customer complaints"]),

    ("B67_3_16", "concept", "easy", "concept", ["Advanced Observability", "SRE"],
     "What is 'Synthetic Monitoring' (or Blackbox Monitoring), and how does it catch production outages that internal metrics (like CPU or application error rates) often miss?",
     "Internal metrics (Whitebox Monitoring) rely on the application successfully running to report its own health. If the entire AWS region loses internet connectivity, or the DNS records are accidentally deleted, your application metrics might show 0 errors and 0% CPU, because no traffic is reaching it. Synthetic Monitoring involves running automated scripts (like a headless Selenium browser or API poller) from external locations across the public internet. These bots continuously attempt to log in, click buttons, or query APIs exactly like a real user. If the DNS is broken or the CDN is down, the external Synthetic Monitor will immediately fail and page you, catching the catastrophic outage that the internal telemetry was completely blind to.",
     ["Defines Synthetic Monitoring as external bots simulating real user behavior over the public internet", "Explains that internal metrics go silent/blind during catastrophic network or DNS failures", "Highlights that synthetics validate the entire end-to-end path, including external load balancers and CDNs"],
     ["Claims Synthetic Monitoring generates fake users to inflate website traffic metrics"]),

    ("B67_3_17", "scenario", "medium", "scenario", ["Supply-Chain Security", "CI/CD"],
     "A company uses a shared, persistent Jenkins worker node (a long-running EC2 instance) to build Docker images for 50 different microservices. Why is using a shared, persistent build runner a severe supply-chain security risk, and what is the modern architectural standard for CI execution?",
     "A shared, persistent runner is highly vulnerable to 'Environment Poisoning' and cross-tenant leakage. If Microservice A's build script is compromised, it can write a malicious backdoor into the global /usr/bin/gcc compiler, alter environment variables, or steal cached credentials residing on the EC2 instance. When Microservice B runs its build on the same machine an hour later, it unknowingly uses the poisoned compiler, injecting the backdoor into Microservice B's Docker image. The modern standard is Ephemeral Build Runners. Using tools like Kubernetes Pods or AWS Fargate, every single CI job provisions a brand-new, sterile, isolated container/VM. When the build finishes, the entire environment is immediately destroyed. This guarantees absolute isolation between builds and mathematically eliminates persistent environment poisoning.",
     ["Diagnoses 'Environment Poisoning' via persistent file system modification or credential caching", "Explains the cross-tenant blast radius where one compromised job infects subsequent unrelated jobs", "Recommends Ephemeral Build Runners (Kubernetes Pods/Fargate) to guarantee sterile, one-time execution environments"],
     ["Suggests installing antivirus software on the Jenkins worker node"]),

    ("B67_3_18", "diagnose", "medium", "debugging", ["Advanced Observability", "Tracing"],
     "You implement distributed tracing across a microservice architecture. However, in the trace visualization UI, the traces are 'broken'. You see the API Gateway trace, and you separately see the Backend Database trace, but they are not linked together into a single cohesive waterfall. What specific application code failure causes 'broken traces', and how do you fix it?",
     "Broken traces are caused by a failure in 'Context Propagation' within the application code. When the API Gateway receives a request, it generates a unique Trace ID and passes it downstream in an HTTP header (e.g., traceparent or X-B3-TraceId). When the Backend microservice receives the HTTP request, it must extract that header. The failure occurs because the developer's application code does not explicitly read the incoming header and attach it to the outgoing database call. To fix this, developers must use standard OpenTelemetry instrumentation libraries. When making outbound HTTP or Database calls, the application code must inject the active Trace Context from the incoming request object into the outgoing request payload, ensuring the unique ID survives the network hop and links the spans together.",
     ["Diagnoses a failure in 'Context Propagation' within the microservice code", "Explains that the application must explicitly extract the Trace ID header and inject it into outgoing calls", "Recommends using OpenTelemetry auto-instrumentation libraries to handle context propagation automatically"],
     ["Claims the traces are broken because Jaeger is running out of disk space"]),

    ("B67_3_19", "tradeoff", "medium", "tradeoff", ["Supply-Chain Security", "CI/CD"],
     "In CI/CD, what is the tradeoff of using a 'Monorepo' (all microservices in one git repository) versus 'Polyrepo' (each microservice in its own git repository) regarding pipeline execution and blast radius?",
     "Monorepo: Advantages: Extremely easy to enforce global dependency updates, share common libraries, and perform atomic commits across multiple services simultaneously. Disadvantages: CI/CD execution complexity is massive. If you merge a commit, the pipeline must intelligently detect exactly which subdirectory changed and only build/deploy that specific service. If the detection logic fails, a single typo in a README could trigger the rebuilding and deployment of 500 microservices, creating a massive operational blast radius and exhausting build resources. Polyrepo: Advantages: Perfect pipeline isolation. A commit to Repo A strictly triggers Pipeline A, with zero risk to Repo B. Disadvantages: Nightmare dependency management. Updating a shared internal library requires opening 500 individual Pull Requests across 500 repos and tracking 500 independent pipeline executions to ensure global compliance.",
     ["Contrasts Monorepo advantages (atomic global commits/dependency updates) with high pipeline execution complexity", "Highlights the Monorepo blast radius risk: broken detection logic triggering massive redundant rebuilds", "Contrasts Polyrepo pipeline isolation with severe dependency update fragmentation"],
     ["Claims Monorepos use Subversion while Polyrepos use Git"]),

    ("B67_3_20", "implement", "hard", "implement", ["Advanced Observability", "Prometheus"],
     "Your Prometheus server scrapes metrics from 1,000 pods. During a severe network outage, 500 pods go offline. Instead of generating 500 separate Slack alerts for each dead pod (an alert storm), how do you implement 'Alert Grouping' and 'Inhibition' in Alertmanager to send only a single, actionable notification?",
     "An alert storm destroys incident response by overwhelming the on-call engineer. You mitigate this using Prometheus Alertmanager configurations: 1) Grouping: In the route configuration, you set group_by: ['cluster', 'service']. When 500 pods belonging to the payment-service fail, Alertmanager waits for a group_wait period (e.g., 30 seconds), aggregates all 500 individual InstanceDown alerts into a single Slack message that says '500 Pods down in payment-service'. 2) Inhibition: You define rules to suppress lower-level alerts if a higher-level alert is firing. If the entire us-east-1 network switch fails (generating a NetworkSwitchDown alert), you configure an inhibit_rule that suppresses all InstanceDown or HighLatency alerts originating from that same zone. The engineer only receives the root-cause alert (the network switch), silencing the hundreds of symptomatic pod alerts.",
     ["Defines Alert Grouping via group_by logic to aggregate hundreds of identical alerts into a single payload", "Defines Inhibition rules to suppress symptom-level alerts when a root-cause infrastructure alert is firing", "Highlights the operational necessity of preventing alert storms to avoid on-call engineer fatigue"],
     ["Suggests turning off the Slack integration entirely during major outages"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 3).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Site Reliability Engineer", "Platform Engineer"],
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
    print("POST-BATCH AUDIT PART 3")
    print("========================================")
    print(f"Batch: 67 Part 3")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
