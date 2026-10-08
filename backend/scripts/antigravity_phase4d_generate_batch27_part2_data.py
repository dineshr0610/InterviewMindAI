"""Batch 27 Part 2 question content (DevOps / Cloud Engineer). Targeted Gap Generation."""

ROLE = "DevOps / Cloud Engineer"

BUCKET_KEYS = {
    "RELIABILITY_ENG": ("Reliability Engineering", "SLOs & Incident Response", "Cloud", ["DevOps / Cloud Engineer", "Site Reliability Engineer"]),
}

Q = [
# ---------------- RELIABILITY_ENG ----------------
("RELIABILITY_ENG", "scenario", "medium", "scenario", ["SLOs", "Error Budgets"],
 "An application has a Service Level Objective (SLO) of 99.9% availability over a 30-day window. Monitoring alerts you that the service just suffered 45 minutes of total downtime. How does this specific outage affect the team's operational behavior for the rest of the month?",
 "The team has completely exhausted their 'Error Budget' for the 30-day window (99.9% allows only ~43.2 minutes of downtime). Operationally, standard SRE principles dictate that the team must immediately freeze all new feature deployments and strictly prioritize reliability engineering, technical debt reduction, and bug fixes until the rolling window recovers budget.",
 ["The team has completely exhausted their 'Error Budget' for the 30-day window", "Must freeze all new feature deployments", "Strictly prioritize reliability engineering and bug fixes until the budget recovers"],
 ["The team receives a bonus for fixing the issue quickly"]),

("RELIABILITY_ENG", "debug", "hard", "debugging", ["Autoscaling", "Capacity Planning"],
 "You deploy a Horizontal Pod Autoscaler (HPA) configured to scale based on CPU utilization. During a load test, the application scales from 2 to 20 pods within minutes, but the 99th percentile response time severely degrades, and the database crashes. Why did autoscaling destroy the system rather than save it?",
 "The architecture failed to implement downstream capacity planning or circuit breakers. The HPA successfully scaled the stateless compute tier, but those 20 new pods immediately overwhelmed the stateful database tier with thousands of new concurrent connection requests (a connection storm). Autoscaling must be holistically modeled across the entire dependency chain, not just CPU.",
 ["Failed to account for downstream capacity limits", "Scaling the stateless compute tier overwhelmed the stateful database tier with a connection storm", "Autoscaling must be holistically modeled across the entire dependency chain"],
 ["The HPA scaled the pods so fast they broke the sound barrier"]),

("RELIABILITY_ENG", "tradeoff", "medium", "tradeoff", ["Disaster Recovery", "DNS"],
 "What is the operational tradeoff of relying on automated DNS failover (e.g., Route53 Health Checks) for regional disaster recovery versus using an active global load balancer failover?",
 "DNS failover is highly cost-effective and completely decoupled from a single region's infrastructure, but it suffers from unpredictable TTL (Time-To-Live) caching. Client ISPs and browsers often ignore TTLs, causing traffic to stubbornly route to the dead region for hours. A global load balancer (like AWS Global Accelerator) provides instant, deterministic failover via Anycast IPs, but is significantly more expensive and complex.",
 ["DNS: Cost-effective, but suffers from unpredictable TTL caching (ISPs/browsers ignore TTLs)", "Traffic can stubbornly route to the dead region for hours", "Global Load Balancer: Instant, deterministic failover via Anycast, but highly expensive"],
 ["DNS failover requires changing the company domain name entirely"]),

("RELIABILITY_ENG", "explain", "hard", "concept", ["Graceful Degradation"],
 "Explain the SRE concept of 'Graceful Degradation' using an e-commerce product page as an example.",
 "Graceful Degradation means designing a system so that when a non-critical microservice fails, the core business transaction can still succeed. For example, if the 'Recommendation Engine' or the 'Review Service' goes offline, the e-commerce product page should gracefully catch the timeout, simply hide the recommendation UI components, but still successfully load the core product details and allow the user to click 'Add to Cart'.",
 ["Designing a system so core business transactions succeed even if non-critical services fail", "Example: If the Recommendation Engine fails, hide the UI component", "The core product details and 'Add to Cart' button must still function normally"],
 ["It means the servers slowly power down while playing classical music"]),

("RELIABILITY_ENG", "scenario", "medium", "scenario", ["Incident Response"],
 "During a severe incident, three different engineers are independently restarting databases, scaling pods, and tweaking configurations to 'fix it', causing massive confusion and prolonging the outage. What fundamental Incident Command System (ICS) role is missing, and what is their sole responsibility?",
 "The missing role is the Incident Commander (IC). The IC's sole responsibility is to orchestrate the response, maintain situational awareness, communicate with stakeholders, and assign specific investigative tasks. Crucially, the IC does *not* execute commands, touch production systems, or debug code themselves; they manage the people who are debugging the code.",
 ["Missing the Incident Commander (IC) role", "Sole responsibility is to orchestrate the response, maintain state, and assign tasks", "The IC strictly does NOT execute commands or touch production systems themselves"],
 ["The missing role is the 'Fixer', who types the fastest"]),

("RELIABILITY_ENG", "tradeoff", "hard", "tradeoff", ["Chaos Engineering"],
 "You want to implement Chaos Engineering. What is the operational tradeoff between running Chaos experiments directly in Production versus running them in a dedicated Staging environment?",
 "Running in Staging is completely safe for customers, but it rarely uncovers true systemic vulnerabilities because Staging lacks production-scale data volumes, real user traffic patterns, and exact infrastructure parity. Running in Production validates the actual system's resilience and monitoring, but carries the severe tradeoff of intentionally inducing risk and potentially causing a real customer-facing outage if the system fails the experiment.",
 ["Staging: Safe for customers, but rarely uncovers true vulnerabilities due to lack of production parity/scale", "Production: Validates the actual system's true resilience and monitoring", "Production Tradeoff: Intentionally induces risk and can cause real customer outages"],
 ["Staging chaos engineering requires paying actors to use the app"]),

("RELIABILITY_ENG", "fundamentals", "easy", "concept", ["SLOs/SLIs"],
 "What is the specific difference between an SLI (Service Level Indicator) and an SLO (Service Level Objective)?",
 "An SLI is a direct, quantitative measurement of service performance (e.g., 'The HTTP 500 error rate is currently 0.05%'). An SLO is the business target or goal set against that indicator (e.g., 'The HTTP 500 error rate must remain strictly below 0.1% over a 30-day rolling window'). The SLI is the measurement; the SLO is the target.",
 ["SLI is the actual quantitative measurement (e.g., current error rate)", "SLO is the target/goal set against that indicator (e.g., must be < 0.1%)", "SLI is the measurement; SLO is the target"],
 ["SLI is a type of hardware server, SLO is the software running on it"]),

("RELIABILITY_ENG", "implement", "medium", "implementation", ["Observability", "Alerting"],
 "Your team frequently experiences 'Alert Fatigue'—getting paged at 3:00 AM for CPU spikes that resolve themselves without intervention. How do you architecturally redesign the alerting strategy to fix this?",
 "You must transition from symptom-based alerting (e.g., 'CPU > 90%') to symptom-based SLO alerting (e.g., 'Error rate is consuming the error budget too fast'). You only page a human engineer if the actual user experience is actively degrading or an SLO is genuinely threatened. High CPU is a metric for dashboards or autoscalers, not a reason to wake a human unless it directly causes latency or errors.",
 ["Transition from symptom-based alerting (CPU spikes) to SLO/User-journey-based alerting", "Only page a human if the user experience is degrading or an SLO is threatened", "High CPU is a dashboard metric, not an actionable page unless it impacts users"],
 ["Delete the monitoring software entirely"]),

("RELIABILITY_ENG", "scenario", "hard", "scenario", ["Cascading Failures"],
 "A microservice architecture uses synchronous REST calls with massive 30-second timeouts. Service A calls Service B, which calls Service C. Service C experiences a severe database lock and hangs. Within 2 minutes, Service A completely crashes due to memory exhaustion. What reliability pattern must be implemented in Service A to prevent this cascading failure?",
 "Service A must implement the Circuit Breaker pattern. Because the timeouts were massive (30s), Service A's connection pool and threads quickly became entirely exhausted waiting for C. A Circuit Breaker would detect the consecutive timeouts, 'open' the circuit, and immediately return fail-fast errors (or fallbacks) for subsequent requests, shedding load and protecting Service A's memory/threads from exhaustion.",
 ["Must implement the Circuit Breaker pattern", "Massive timeouts exhausted Service A's connection pool/threads waiting for downstream responses", "A Circuit Breaker detects failures and fails fast, shedding load to protect memory/threads"],
 ["Service A must implement a louder alarm bell"]),

("RELIABILITY_ENG", "debug", "medium", "debugging", ["Kubernetes", "Probes"],
 "You configure a health check (Liveness Probe) for a Kubernetes pod. The probe runs `SELECT 1` against the central database. When the database undergoes a brief 10-second failover, Kubernetes abruptly kills and restarts every single application pod in the cluster. Why is this Liveness Probe architecturally flawed?",
 "A Liveness Probe dictates whether the *local container process* is in a healthy, running state. By tying it to an external dependency (the DB), a brief database blip causes Kubernetes to mistakenly believe the application containers themselves have irrecoverably crashed, triggering a massive restart storm. External dependency checks belong in Readiness Probes, which merely stop traffic routing rather than killing the pod.",
 ["Liveness Probes dictate local container health, not external dependency health", "Tying it to a database causes a restart storm during a brief DB failover", "External dependency checks belong in Readiness Probes (which stop traffic routing, not kill pods)"],
 ["The pods committed mutiny against Kubernetes"]),

("RELIABILITY_ENG", "explain", "easy", "concept", ["Disaster Recovery"],
 "In the context of disaster recovery and business continuity, define RTO and RPO.",
 "RTO (Recovery Time Objective) is the maximum acceptable amount of downtime before the service is restored and functioning again. RPO (Recovery Point Objective) is the maximum acceptable amount of data loss, measured in time (e.g., the business can afford to lose the last 15 minutes of database writes in a catastrophe).",
 ["RTO (Recovery Time Objective): Maximum acceptable downtime before restoration", "RPO (Recovery Point Objective): Maximum acceptable data loss, measured in time", "RTO dictates operational recovery speed; RPO dictates backup frequency"],
 ["RTO stands for Return To Office"]),

("RELIABILITY_ENG", "scenario", "hard", "scenario", ["Capacity Planning"],
 "You deploy a highly available application across 3 Availability Zones (AZs). AZ-1 completely fails. The Auto Scaling Group successfully provisions new replacement instances in AZ-2 and AZ-3. However, 5 minutes later, AZ-2 and AZ-3 both crash, causing a total regional outage. What capacity planning failure caused this cascading collapse?",
 "The architecture failed to account for 'N+1 Redundancy' at peak load. If the system required 3 AZs running at 80% CPU to handle normal traffic, losing one AZ instantly shifts 100% of the traffic to the remaining 2 AZs, pushing them to 120% CPU. They crash from overload before the replacement instances can finish booting. You must provision enough baseline idle capacity so surviving AZs can absorb the entire load of a failed AZ.",
 ["Failed to account for 'N+1 Redundancy' at peak load", "Losing one AZ shifted 100% of traffic to the remaining 2, pushing them beyond 100% capacity", "Must provision enough baseline idle capacity to absorb the load of a failed AZ before replacements boot"],
 ["The AZs formed a union and went on strike"]),

("RELIABILITY_ENG", "tradeoff", "medium", "tradeoff", ["Microservices Communication"],
 "When designing a microservices architecture, what is the reliability tradeoff of using synchronous HTTP/REST communication versus asynchronous Message Queues (e.g., RabbitMQ, Kafka) for inter-service communication?",
 "Synchronous HTTP is simple to implement and provides immediate success/failure feedback, but it creates tight temporal coupling; if the downstream service is down, the request fails instantly. Asynchronous queues provide extreme resilience and temporal decoupling (the downstream service can be down for hours while messages safely queue), but they severely complicate error handling, tracing, and force the architecture into Eventual Consistency.",
 ["Synchronous HTTP: Simple, immediate feedback, but creates tight temporal coupling (cascading failures)", "Asynchronous Queues: Extreme resilience and temporal decoupling (messages queue if service is down)", "Asynchronous tradeoff: Complicates error handling, tracing, and forces Eventual Consistency"],
 ["Message queues deliver messages via the postal service"]),

("RELIABILITY_ENG", "fundamentals", "medium", "concept", ["Incident Response"],
 "What is a Post-Incident Review (or Blameless Post-Mortem), and why is the 'Blameless' aspect operationally critical?",
 "A PIR is a structured analysis of a production outage to determine root causes and create preventative action items. The 'Blameless' aspect is critical because if engineers fear punishment or firing, they will hide information, alter timelines, and cover up mistakes. By assuming good intent and focusing strictly on systemic failures (e.g., 'Why did the system allow a typo to bring down production?'), organizations uncover the actual truth and build safer systems.",
 ["A structured analysis to determine root causes and create preventative action items", "If engineers fear punishment, they will hide information and cover up mistakes", "Blamelessness focuses on systemic failures (why the system allowed the error), uncovering the truth"],
 ["It is a review conducted by a priest after a server dies"]),

("RELIABILITY_ENG", "implement", "hard", "implementation", ["High Availability", "Autoscaling"],
 "A critical legacy monolith requires 15 minutes to fully boot up and warm its caches. If a node crashes, you cannot wait 15 minutes for a replacement. How do you configure an Auto Scaling Group or Kubernetes Deployment to ensure High Availability without wasting massive amounts of compute budget?",
 "You must use a Warm Standby or Overprovisioning pattern. You intentionally run exactly one extra, fully booted instance (N+1) in the cluster at all times that is already serving traffic or marked ready. When a node crashes, the existing N+1 capacity instantly absorbs the load. The autoscaler then boots a new instance in the background over 15 minutes to restore the N+1 buffer, completely hiding the boot latency from the user.",
 ["Use a Warm Standby or Overprovisioning pattern (N+1 redundancy)", "Always run an extra, fully booted instance capable of absorbing an immediate failure", "The autoscaler boots a replacement in the background to restore the buffer, hiding the 15m latency"],
 ["Pour hot coffee on the server to warm its caches instantly"]),

("RELIABILITY_ENG", "debug", "medium", "debugging", ["SLIs", "Observability"],
 "An application has a documented SLO of 99.9% uptime. However, the Customer Support team is flooded with complaints about the system being completely unusable. You check the monitoring dashboard, and the SLI shows 99.95% uptime (Green). What is the disconnect between the metric and the reality?",
 "The SLI is measuring the wrong thing. It is likely pinging a static `/health` endpoint that trivially returns HTTP 200, while the actual database connection, login flow, or core user journey is entirely broken. The SLI must be redesigned to measure actual user experience (e.g., tracking the success rate of the critical 'Checkout' API). If the SLI doesn't reflect user pain, the SLO is completely meaningless.",
 ["The SLI is measuring a trivial component (e.g., a static `/health` endpoint)", "It fails to measure the actual core user journey or database connectivity", "SLIs must be redesigned to measure critical business flows (e.g., Checkout success rate)"],
 ["The customers are hallucinating the outage"]),

("RELIABILITY_ENG", "explain", "hard", "concept", ["Load Management"],
 "Explain the concept of 'Rate Limiting' vs 'Load Shedding' as reliability mechanisms. How do they fundamentally differ in protecting a service?",
 "Rate Limiting is a business or fairness mechanism: it restricts a specific user, IP, or API key to a defined quota (e.g., 100 requests/min) to prevent noisy neighbor problems, returning HTTP 429. Load Shedding is an absolute survival mechanism: when the server itself detects it is running out of CPU or memory, it universally drops incoming requests (regardless of who the user is or their quota) to prevent the node from crashing entirely.",
 ["Rate Limiting: Fairness mechanism restricting specific users/keys to a quota (prevents noisy neighbors)", "Load Shedding: Absolute survival mechanism dropping universal requests based on server stress", "Load shedding ignores user quotas to prevent the entire node from crashing under extreme load"],
 ["Load shedding is when the server literally sheds its outer metal casing"])
]
