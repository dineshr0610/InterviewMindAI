import os

ROLE = "DevOps / Cloud Engineer"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b1": ("Infrastructure as Code", "Terraform", "Terraform", ["DevOps / Cloud Engineer", "Backend Developer"]),
    "b2": ("Reliability", "Distributed Systems", "Distributed Systems", ["DevOps / Cloud Engineer", "Backend Developer"]),
    "b3": ("Observability", "SRE & Monitoring", "Prometheus", ["DevOps / Cloud Engineer", "Backend Developer"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    (
        "b1",
        "implement",
        "easy",
        "conceptual",
        ["Terraform", "CI/CD Architecture"],
        "To refactor a complex Terraform codebase without triggering resource recreation, how do you utilize `moved` blocks introduced in modern Terraform?",
        "In modern Terraform (version 1.1+), `moved` blocks provide a declarative mechanism to record refactored resource addresses directly in configuration code, replacing manual and error-prone `terraform state mv` CLI commands. When code is restructured—such as renaming a resource or migrating an inline resource into a reusable module—engineers define a block such as `moved { from = aws_instance.web; to = module.web_cluster.aws_instance.server }`. During execution planning (`terraform plan`), Terraform inspects the state, identifies the old address, and maps it to the new destination address in memory without planning a destructive recreation. Because `moved` blocks are committed to Git, every team member, CI/CD pipeline runner, and deployment workspace automatically executes the state address migration seamlessly on their next apply, ensuring safe refactoring across multi-developer teams.",
        [
            "Explains that `moved` blocks provide declarative, version-controlled state migrations compared to manual `terraform state mv` commands.",
            "Specifies the syntax structure using `from` and `to` attributes and explains how `terraform plan` applies this transition without resource recreation."
        ],
        [
            "Suggests running manual state manipulation commands across production environments instead of declarative blocks.",
            "Claims that renaming resources in Terraform always requires destroying and recreating the cloud infrastructure."
        ]
    ),
    (
        "b1",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Terraform", "Cloud Security"],
        "When managing Terraform provider dependencies across air-gapped or strictly audited enterprise environments, what tradeoffs arise between maintaining a Terraform Provider Lock file (`.terraform.lock.hcl`) versus hosting an internal private provider mirror?",
        "The Terraform Provider Lock file (`.terraform.lock.hcl`) pins specific provider versions and records cryptographic package checksums (both `h1:` and platform-specific `zh:` hashes), guaranteeing that all CI/CD workers and developers download the exact identical binary from the public registry. However, lock files rely on outbound internet access to fetch provider binaries from registry.terraform.io. In air-gapped or restricted VPC environments where external internet connectivity is blocked or forbidden by security policies, lock files alone cannot download providers. Teams must host an internal provider mirror (via filesystem mirror or internal network mirror service configured via CLI configuration `provider_installation`). The tradeoffs involve infrastructure maintenance: internal mirrors require dedicated artifact repository hosting, synchronization pipelines, and ongoing storage management, but deliver guaranteed availability, complete network isolation, and immunity from public registry outages or supply-chain compromises.",
        [
            "Differentiates between checksum verification in `.terraform.lock.hcl` and binary distribution via provider mirrors.",
            "Explains network isolation requirements in air-gapped environments and operational overhead of maintaining private mirror endpoints."
        ],
        [
            "Confuses the lock file with the backend remote state file.",
            "Claims that lock files can store and distribute provider binary executables without external network access."
        ]
    ),
    (
        "b1",
        "scenario",
        "medium",
        "scenario",
        ["Terraform", "Reliability Engineering"],
        "During a blue-green resource update in Terraform, your pipeline encounters a deadlock where an updated resource fails to provision because its name or network attachment conflicts with the existing live resource. How do you resolve this using `lifecycle` meta-arguments?",
        "By default, Terraform executes a destroy-then-create sequence when updating resources that cannot be updated in-place. When configuring zero-downtime updates using `lifecycle { create_before_destroy = true }`, Terraform reverses this order, attempting to provision the new replacement resource before tearing down the old one. If the resource specifies a fixed unique identifier (such as a hardcoded `name` attribute on an AWS Security Group, IAM Role, or Launch Template) or binds to a singleton physical resource, the cloud provider rejects creation due to naming collisions. To resolve this deadlock, engineers must refactor the configuration to use prefix-based naming (e.g., `name_prefix = \"app-sg-\"`) instead of a static `name`. Terraform generates a unique random suffix for the new resource, allows it to provision and bind dependencies concurrently, and smoothly destroys the superseded resource once dependencies transfer.",
        [
            "Identifies how `create_before_destroy = true` conflicts with static unique resource naming in cloud providers.",
            "Recommends transitioning from static `name` attributes to dynamic `name_prefix` attributes to eliminate provisioning deadlocks."
        ],
        [
            "Fails to identify the root cause of naming collision during create-before-destroy transitions.",
            "Suggests manually deleting the existing production resource before running Terraform apply."
        ]
    ),
    (
        "b1",
        "debug",
        "medium",
        "debugging",
        ["Terraform", "CI/CD Architecture"],
        "In a large infrastructure repository, multiple engineers frequently experience `Error: Error acquiring the state lock` during automated CI/CD Terraform runs. How should this be systematically diagnosed and resolved without risking state corruption?",
        "When Terraform executes commands against state backends that support concurrency locking (such as AWS DynamoDB with S3, or Terraform Cloud), it writes an exclusive lock item containing a Lock ID, path, timestamp, and the executing entity. If a pipeline job crashes abruptly, runs into a runner VM termination, or times out without running teardown handlers, the lock remains active. To systematically diagnose, first verify whether an actual concurrent deployment is running in the CI/CD system by cross-referencing the Lock ID and timestamp in DynamoDB (`aws dynamodb get-item`). If confirmed that no execution is active, an authorized engineer must execute `terraform force-unlock <LOCK_ID>`. To prevent future occurrences, CI pipelines should implement signal trapping (ensuring runner containers forward SIGTERM/SIGINT so Terraform can clean up locks before shutdown), set appropriate execution timeouts, and enforce pipeline concurrency queues per environment.",
        [
            "Explains the locking mechanism in remote backends (e.g., DynamoDB) and the diagnostic process of checking active pipeline processes before releasing locks.",
            "Specifies the safe use of `terraform force-unlock` and architectural prevention like CI runner signal forwarding and concurrency queues."
        ],
        [
            "Recommends blindly disabling state locking in the backend configuration to avoid lock errors.",
            "Advises deleting the entire remote state backend table or bucket whenever a lock occurs."
        ]
    ),
    (
        "b1",
        "architecture",
        "hard",
        "architectural",
        ["Terraform", "AWS IAM", "Cloud Architecture"],
        "When architecting a cross-account Terraform deployment strategy across staging and production AWS accounts from a centralized CI/CD management account, how should provider aliasing and IAM role assumption be structured?",
        "The architecture implements a hub-and-spoke governance model where the centralized CI/CD pipeline runs inside a hardened management or tooling account. In the root Terraform configuration, multiple provider aliases are declared, such as `provider \"aws\" { alias = \"prod\"; region = \"us-east-1\"; assume_role { role_arn = \"arn:aws:iam::<PROD_ACCOUNT_ID>:role/TerraformExecutionRole\"; session_name = \"TerraformProdPipeline\" } }`. Target accounts host the execution role with a strict trust policy permitting `sts:AssumeRole` only from the management account's CI/CD identity, bounded by conditions on session tags or external IDs. Modules consume these providers explicitly via the `providers` map. This structure ensures least privilege, prevents credential sprawl, isolates failure domains, and guarantees that compromised staging permissions cannot be leveraged to modify production infrastructure.",
        [
            "Articulates a hub-and-spoke assume-role architecture using Terraform provider aliases and `assume_role` blocks.",
            "Emphasizes least privilege IAM trust boundaries between centralized tooling accounts and spoke environment accounts."
        ],
        [
            "Suggests generating and storing permanent static IAM access keys for each environment inside CI secrets.",
            "Fails to explain how provider aliases pass assumed credentials into child modules."
        ]
    ),
    (
        "b1",
        "debug",
        "hard",
        "debugging",
        ["Terraform", "Reliability Engineering"],
        "Your platform team observes that out-of-band cloud modifications have caused severe configuration drift, and running `terraform apply` attempts to overwrite active production emergency hotfixes. How do you safely reconcile state without losing production changes or corrupting your IaC baseline?",
        "When urgent production changes are made out-of-band (e.g., modifying security group ingress rules or scaling node groups via cloud console during an incident), running a standard `terraform apply` would immediately destroy or revert those changes to match the existing HCL code. To reconcile safely: 1) Execute `terraform plan -refresh-only` to query the live cloud provider API and update the state file with current reality without modifying any infrastructure; 2) Review the refresh plan output to isolate exactly which attributes drifted; 3) Backport those live infrastructure modifications into the Terraform HCL configuration files; 4) Run `terraform plan` to verify that the proposed changes evaluate to zero (`No changes. Your infrastructure matches the configuration.`); 5) Run `terraform apply` to commit the refreshed state. This establishes bidirectional alignment between Git and the live cloud without service degradation.",
        [
            "Details the use of `terraform plan -refresh-only` to update state from live infrastructure without overwriting resources.",
            "Explains the required step of backporting drifted attributes into HCL code to achieve zero-delta reconciliation."
        ],
        [
            "Suggests running `terraform apply -auto-approve` and letting Terraform revert live emergency hotfixes.",
            "Suggests manually deleting resources from the state file using `state rm` without updating configuration."
        ]
    ),
    (
        "b2",
        "compare",
        "easy",
        "conceptual",
        ["Reliability", "Networking"],
        "In distributed consensus systems like Raft or Paxos, how does a split-brain condition occur, and how does the quorum requirement fundamentally prevent data corruption?",
        "A split-brain condition occurs when an asymmetric network partition divides a distributed cluster into two or more isolated network partitions, and multiple partitions simultaneously attempt to elect leaders and process state transitions independently. If both partitions accepted writes, the cluster's state log would diverge irrecoverably. Consensus protocols prevent this via the quorum requirement, which mandates that any cluster decision (leader election or log entry commit) must receive affirmative acknowledgment from a strict majority of nodes: `Q = floor(N / 2) + 1`, where N is the total cluster membership. Because any two majorities in an N-node system must share at least one overlapping node, it is mathematically impossible for two disconnected sub-clusters to concurrently achieve quorum. The minority sub-cluster cannot commit writes and transitions to read-only or disconnects, preserving data integrity.",
        [
            "Explains how network partitions cause split-brain when multiple sub-clusters attempt to act as primary.",
            "States the majority quorum formula `floor(N/2) + 1` and explains why two majorities cannot concurrently exist in a single cluster."
        ],
        [
            "Claims that split-brain is prevented by simply designating a single hardcoded backup server.",
            "Fails to connect quorum intersection to the mathematical impossibility of dual simultaneous majorities."
        ]
    ),
    (
        "b2",
        "scenario",
        "medium",
        "scenario",
        ["Reliability", "Observability"],
        "A high-throughput e-commerce platform suffers a major outage when a Redis cluster restarts and thousands of concurrent client requests simultaneously hit the primary backend database. How do you architect cache rewarming and request coalescing to prevent this cache stampede?",
        "A cache stampede (thundering herd) occurs when a popular cache key expires or the cache node crashes, causing high-volume concurrent worker processes to experience cache misses simultaneously and overwhelm the backend datastore with identical queries. To eliminate this, the platform implements three coordinated architectural defenses: 1) Request Coalescing (Singleflight pattern), where an in-memory lock or mutex at the application layer ensures only the first arriving request queries the database while subsequent concurrent requests wait and share the returned result; 2) Probabilistic Early Expiration (such as the XFetch algorithm), where background worker threads proactively compute and re-populate cache keys before their formal TTL expires based on request compute cost and delta; and 3) Cache warming automation, where deployment scripts pre-populate hot keys before opening public traffic ingress.",
        [
            "Identifies the root mechanics of a cache stampede / thundering herd problem during cache invalidation or restart.",
            "Details mitigation strategies including request coalescing (Singleflight), probabilistic early expiration (XFetch), and automated cache pre-warming."
        ],
        [
            "Suggests merely increasing database CPU capacity without addressing request synchronization.",
            "Claims that setting infinite TTLs on all keys is the standard production solution."
        ]
    ),
    (
        "b2",
        "architecture",
        "medium",
        "architectural",
        ["Reliability", "Cloud Architecture"],
        "When designing a multi-region active-active deployment for a critical microservice, what are the operational tradeoffs between Last-Write-Wins (LWW) timestamp ordering and Conflict-Free Replicated Data Types (CRDTs) for cross-region data replication?",
        "In active-active multi-region systems, concurrent writes to the same entity can occur across distant geographic regions during replication propagation delays. Last-Write-Wins (LWW) resolves conflicts by comparing wall-clock timestamps (using NTP or TrueTime) and discarding older updates. Its advantages are simplicity, low memory footprint, and applicability across arbitrary database schemas; however, its critical risk is silent data loss when clock drift or rapid concurrent mutations cause legitimate updates to be permanently overwritten. Conversely, Conflict-Free Replicated Data Types (CRDTs) use mathematically sound merge semantics (state-based or operation-based) that guarantee convergent state without data loss regardless of message arrival ordering. The tradeoff is architectural complexity: CRDTs require specialized data models (e.g., PN-counters, Observed-Remove sets), impose substantial memory and network bandwidth overhead for metadata tracking, and demand custom application integration.",
        [
            "Analyzes the risks of Last-Write-Wins including silent data loss caused by clock skew and concurrent mutations.",
            "Explains how CRDTs mathematically guarantee convergence without loss while noting tradeoffs in memory overhead and schema complexity."
        ],
        [
            "Claims that wall-clock timestamps across distributed regions are always perfectly synchronized.",
            "Does not articulate the architectural or computational overhead associated with CRDT state tracking."
        ]
    ),
    (
        "b2",
        "scenario",
        "medium",
        "scenario",
        ["Reliability", "Networking"],
        "During a sudden traffic surge, an upstream payment gateway experiences high latency, causing application thread pools to exhaust and threatening cascading failure across the entire checkout platform. How should circuit breakers and graceful degradation be configured to isolate this fault?",
        "To prevent thread pool exhaustion and cascading system collapse, the platform introduces a Circuit Breaker pattern (via service mesh or application libraries like Resilience4j) configured with sliding error and latency windows. When the percentage of requests exceeding a latency threshold (e.g., 2000ms) or returning 5xx status codes exceeds a failure rate limit (e.g., 50% over a 10-second window), the breaker trips from Closed to Open. In the Open state, all outbound requests to the payment gateway fail fast immediately without holding worker threads or socket connections. Graceful degradation routes users to an asynchronous fallback queue (e.g., accepting orders into Kafka/SQS in a 'Payment Processing' status) or seamlessly presents alternate payment providers. After a configured sleep duration, the circuit enters Half-Open, probing the gateway with canary requests before safely resuming traffic.",
        [
            "Defines the state transitions (Closed, Open, Half-Open) of a circuit breaker and explains how fast failure prevents thread exhaustion.",
            "Details graceful degradation techniques such as asynchronous queueing and multi-provider failover."
        ],
        [
            "Suggests setting request timeouts to several minutes so requests eventually succeed.",
            "Fails to mention how circuit breakers isolate thread pools and prevent cascading microservice outages."
        ]
    ),
    (
        "b2",
        "tradeoff",
        "hard",
        "tradeoff",
        ["Reliability", "Observability"],
        "To validate automated failover capabilities before peak shopping season, what are the primary engineering tradeoffs and safety controls when executing production chaos engineering experiments versus staging chaos tests?",
        "Testing chaos engineering in staging provides a risk-free environment where failure injection cannot impact real users or revenue; however, staging environments rarely replicate production fidelity due to synthetic traffic, simplified network topologies, and scaled-down cluster capacities, often missing race conditions and emergent failure modes. Executing chaos experiments in production exposes authentic system resilience under real-world traffic, revealing hidden dependencies, timeout mismatches, and autoscaler lag. However, production experiments introduce severe financial and reputation risks. Crucial safety controls include: 1) Strict blast-radius containment using canary user segments or small percentages of synthetic traffic; 2) Automated Stop Conditions (Hypothesis-driven automated kill switches) that immediately abort experiments if primary business SLIs (e.g., checkout error rate, payment latency) breach thresholds; 3) Scheduling tests during normal business hours with full on-call team readiness.",
        [
            "Contrasts staging safety and lack of environmental fidelity with production authenticity and operational risk.",
            "Specifies production safety controls including blast radius limitation, automated rollback stop conditions based on SLIs, and active incident response coverage."
        ],
        [
            "Advocates running unannounced chaos tests in production without automated abort triggers.",
            "Claims staging tests provide identical guarantees to production experiments without any fidelity gaps."
        ]
    ),
    (
        "b2",
        "architecture",
        "hard",
        "architectural",
        ["Reliability", "Cloud Architecture"],
        "An enterprise application requires a Disaster Recovery strategy with an RTO of less than 5 minutes and an RPO of less than 1 minute across AWS regions. What architecture satisfies these constraints, and what are its operational complexities?",
        "Meeting RPO < 1m requires continuous near-real-time storage replication: deploying Amazon Aurora Global Database (which replicates storage across AWS regions with typical latency under 1 second using dedicated network infrastructure) and cross-region S3 replication with replication time control (RTC). Meeting RTO < 5m rules out cold recovery (backup/restore) or pilot-light models, requiring a Warm Standby or Active-Active compute footprint where container clusters (EKS/ECS) and stateless microservices are pre-provisioned and active in the secondary region. Operational complexities include: 1) Orchestrating automated multi-region DNS failover via AWS Route 53 Application Recovery Controller (ARC) routing controls; 2) Automating secondary Aurora cluster promotion to primary via Lambda/Step Functions; 3) Handling egress data transfer costs between regions; and 4) Avoiding split-brain during partial regional network isolation.",
        [
            "Selects technologies meeting RPO < 1m (e.g., Aurora Global Database, S3 RTC) and compute topologies meeting RTO < 5m (Warm Standby / Active-Active).",
            "Identifies key operational complexities including automated database promotion, Route 53 ARC routing controls, and inter-region data transfer expenses."
        ],
        [
            "Suggests periodic nightly database snapshot restores for an RPO of less than 1 minute.",
            "Claims that cold manual VM provisioning in a secondary region can reliably achieve an RTO of under 5 minutes."
        ]
    ),
    (
        "b3",
        "diagnose",
        "easy",
        "problem_solving",
        ["Observability", "Reliability Engineering"],
        "Following the deployment of a new microservice, your Prometheus monitoring server experiences rapid memory exhaustion and OOM kills due to high metric cardinality. What metric design flaws cause this, and how do you diagnose it?",
        "High metric cardinality occurs when metric labels contain dynamic, unbounded values that produce an explosion of distinct time series in Prometheus's TSDB block index. Common design flaws include attaching user IDs, session tokens, UUIDs, email addresses, or un-sanitized URL request paths (e.g., `http_requests_total{path=\"/api/v1/users/948271\"}`) to Prometheus labels. To diagnose, operators query the Prometheus TSDB status API endpoint (`/api/v1/status/tsdb`), which reports the top 10 label names with the highest value counts and metrics with the highest series count. Immediate operational mitigation involves configuring `metric_relabel_configs` in the Prometheus scrape configuration to drop or sanitize the high-cardinality labels before ingestion. Long-term remediation requires updating application code to use route templates (e.g., `/api/v1/users/{id}`) instead of raw path strings.",
        [
            "Explains how unbounded label values (e.g., user IDs, raw URLs) cause exponential time-series explosion in Prometheus TSDB memory.",
            "Identifies diagnostic tools like the `/api/v1/status/tsdb` endpoint and remediation using `metric_relabel_configs` and route parameterization."
        ],
        [
            "Claims that Prometheus memory exhaustion is caused solely by scraping too many separate target nodes.",
            "Suggests that adding user IDs to Prometheus metrics is a standard best practice for user-level tracking."
        ]
    ),
    (
        "b3",
        "debug",
        "medium",
        "debugging",
        ["Observability", "Cloud Architecture"],
        "In an OpenTelemetry tracing architecture collecting millions of spans per second, storage and ingestion costs are ballooning while latency outlier traces are frequently dropped. How do you transition from Head-Based Sampling to Tail-Based Sampling to solve this?",
        "Head-based sampling makes the sampling decision at the ingestion ingress when the root span begins, before the request's execution path, duration, or status code are known. This results in capturing thousands of mundane 200 OK traces while missing rare 500 errors and p99 latency outliers that were sampled out at the head. To transition to Tail-based sampling, engineers deploy the OpenTelemetry Collector in an agent-gateway topology using the `tail_sampling` processor. The collector buffers all child spans of a trace in memory until the entire trace completes, then evaluates rules: 1) Retain 100% of traces where any span contains HTTP status code >= 500; 2) Retain 100% of traces whose total duration exceeds a threshold (e.g., > 2000ms); and 3) Keep a 1% probabilistic sample of standard successful traces. This dramatically cuts overall storage volume and billing while guaranteeing 100% capture of production errors and latency anomalies.",
        [
            "Explains the fundamental limitation of head-based sampling regarding post-execution awareness.",
            "Details how the OpenTelemetry Collector's `tail_sampling` processor buffers spans to selectively retain errors, latency outliers, and statistical samples."
        ],
        [
            "Suggests reducing sampling rate to 0.01% at the application entrypoint without tail inspection.",
            "Claims tail-based sampling must be executed directly inside client frontend browsers."
        ]
    ),
    (
        "b3",
        "optimize",
        "medium",
        "best_practices",
        ["Observability", "Reliability Engineering"],
        "To avoid alert fatigue while maintaining high operational reliability, how do you implement a Multi-Window Multi-Burn-Rate alerting strategy based on SLOs and Error Budgets?",
        "Traditional single-window threshold alerts (e.g., error rate > 2% over 5 minutes) cause alert fatigue during brief transient blips and fail to detect slow, steady erosions of error budgets. Multi-window multi-burn-rate alerting evaluates the rate of error budget consumption over both short and long lookback windows simultaneously. A burn rate of 1x consumes 100% of the monthly error budget over 30 days; a 14.4x burn rate consumes 2% of the budget in 1 hour. Under Google SRE best practices, a high-severity page triggers only if both a 1-hour window AND a 5-minute window exceed the 14.4x burn rate threshold. The short window confirms that the incident is actively continuing, while the long window verifies that significant error budget is at risk. Lower burn rates (e.g., 6x over 6 hours and 30 minutes) generate non-urgent ticketing alerts, eliminating transient false alarms.",
        [
            "Contrasts naive single-threshold alerts with error budget burn-rate calculations across multiple time windows.",
            "Explains how pairing a long lookback window with a short lookback window prevents paging on transient blips while ensuring urgent response to severe budget consumption."
        ],
        [
            "Recommends setting alerts on raw CPU and memory thresholds instead of SLO error budgets.",
            "Fails to explain the relationship between burn rates, time windows, and paging vs ticketing actions."
        ]
    ),
    (
        "b3",
        "diagnose",
        "medium",
        "problem_solving",
        ["Observability", "Distributed Systems"],
        "Your engineering team struggles to identify end-to-end latency bottlenecks in an asynchronous microservice system where requests traverse Kafka topics and worker queues. How do you propagate W3C Trace Context across message boundaries?",
        "In asynchronous message queues like Apache Kafka, synchronous HTTP headers are absent, breaking trace continuity unless the producer explicitly injects trace context into message metadata. To propagate context using the W3C Trace Context standard, the producer's OpenTelemetry instrumentation uses an `OpenTelemetry.propagators.textMapPropagator` to serialize the active span's `traceparent` (containing trace ID, span ID, and trace flags) into binary Kafka record `Headers`. When the consumer service polls the record from the topic, its OpenTelemetry instrumentation extracts the `traceparent` header and establishes a span context, creating either a child span or a linked span (`SpanKind.CONSUMER`). This links the upstream HTTP request, producer publishing, queue dwell time, and downstream worker execution into a single unified trace tree in Jaeger or Tempo, pinpointing queue wait times and consumer bottlenecks.",
        [
            "Explains the serialization of W3C `traceparent` into Kafka record headers on the producer side.",
            "Details how consumer instrumentation extracts headers to create linked or child spans, visualizing end-to-end queue latency in tracing backends."
        ],
        [
            "Suggests embedding the trace ID in the message JSON payload body as an application field instead of standard transport headers.",
            "Claims that Kafka brokers automatically inject and correlate OpenTelemetry spans natively without client instrumentation."
        ]
    ),
    (
        "b3",
        "scenario",
        "hard",
        "scenario",
        ["Observability", "Networking"],
        "A critical customer-facing API experiences an intermittent regional outage that is not detected by internal pod health checks or Prometheus APM metrics. How do you architect Synthetic Monitoring and Blackbox Probing to catch such edge network failures?",
        "Internal pod health checks and APM metrics only observe service health from within the internal cluster or VPC network; they cannot detect edge failures such as CDN routing misconfigurations, public load balancer TLS certificate expirations, DNS propagation failures, or regional ISP peering outages. To detect these, platform engineers deploy an external Synthetic Monitoring architecture utilizing tools like Prometheus Blackbox Exporter or geographically distributed serverless probes located across multiple public cloud regions and availability zones. Probers execute automated HTTP, DNS, and TLS checks against public endpoints every 30 seconds, evaluating SSL validity, response codes, and end-to-end latency. If probes from multiple distinct external regions fail while internal APM metrics report healthy green status, an automated alert flags edge and transit network failure, initiating rapid failover before customer escalations.",
        [
            "Identifies blind spots of internal APM/health checks (e.g., public DNS, CDN edge routing, TLS certificates, ISP peering).",
            "Architects an external multi-region synthetic monitoring system (e.g., Blackbox Exporter) with cross-region correlation to detect external ingress failures."
        ],
        [
            "Claims that internal Kubernetes liveness probes are sufficient to detect all external customer connectivity issues.",
            "Suggests relying solely on customer support tickets to detect edge DNS and ISP routing failures."
        ]
    )
]
