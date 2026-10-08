"""Batch 17 question content (DevOps / Cloud Engineer). Antigravity-native, no Gemini API."""

ROLE = "DevOps / Cloud Engineer"

BUCKET_KEYS = {
    "DO_K8": ("Kubernetes", "Container Orchestration", "Kubernetes", ["Backend Developer"]),
    "DO_AW": ("Cloud Architecture", "AWS / Cloud", "AWS", ["Architecture"]),
    "DO_TF": ("Infrastructure as Code", "Terraform", "Terraform", ["Platform Engineer"]),
    "DO_CI": ("CI/CD", "Pipelines & Deployments", "CI/CD", ["Platform Engineer"]),
    "DO_OB": ("Observability", "SRE & Monitoring", "Monitoring", ["Performance Engineer", "Backend Developer"]),
    "DO_NW": ("Networking", "DNS & Load Balancing", "Networking", ["Network Engineer"]),
    "DO_SC": ("Security", "Cloud Security", "Security", ["Security Engineer"]),
    "DO_CT": ("Containers & OS", "Docker & Linux", "Linux", ["Backend Developer", "System Administrator"]),
    "DO_AR": ("Reliability", "Distributed Systems", "Architecture", ["Architecture", "Backend Developer"]),
}

Q = [
# ---------------- DO_K8 ----------------
("DO_K8", "fundamentals", "easy", "concept", ["Kubernetes"],
 "What is the primary purpose of a Kubernetes Deployment versus a StatefulSet?",
 "A Deployment manages stateless applications where any pod is identical and interchangeable, automatically handling rollouts and replicas. A StatefulSet manages stateful applications (like databases), guaranteeing strict ordering, unique network identifiers (e.g., pod-0, pod-1), and stable persistent storage across pod rescheduling.",
 ["Deployment: for stateless applications, interchangeable pods", "StatefulSet: for stateful applications (databases)", "StatefulSet guarantees stable network IDs and persistent storage ordering"],
 ["Deployments are for production and StatefulSets are for testing"]),

("DO_K8", "scenario", "medium", "scenario", ["Kubernetes Troubleshooting"],
 "You notice a Kubernetes Pod is stuck in the `Pending` state indefinitely. What are the most common reasons for this, and how do you diagnose it?",
 "A `Pending` pod has not been scheduled onto a node. Common causes include insufficient cluster resources (CPU/Memory), missing PersistentVolumeClaims, or unsatisfied NodeSelectors/Taints/Affinities. I would diagnose this by running `kubectl describe pod <pod-name>` and reading the 'Events' section to see exactly why the scheduler rejected it.",
 ["Pending means the scheduler cannot place the pod on a node", "Causes: insufficient resources, missing PVCs, or taint/affinity mismatches", "Diagnose by reading 'Events' in `kubectl describe pod`"],
 ["Pending means the pod is running but the application is booting"]),

("DO_K8", "explain", "medium", "concept", ["Kubernetes Networking"],
 "Explain how Kubernetes Services route traffic to Pods dynamically when Pod IP addresses are constantly changing.",
 "Kubernetes Services provide a stable virtual IP (ClusterIP) and DNS name. They use label selectors (e.g., `app: my-backend`) to dynamically identify matching Pods. The `kube-proxy` component on every node constantly monitors the API server for changes to these endpoints and updates local iptables/IPVS rules to load balance traffic to the current, healthy Pod IPs.",
 ["Services provide a stable virtual IP and DNS name", "Use label selectors to dynamically group Pods", "kube-proxy updates local iptables/IPVS rules to route traffic"],
 ["Services hardcode the Pod IPs in a config file"]),

("DO_K8", "debug", "hard", "debugging", ["Kubernetes Operations"],
 "A Node in your Kubernetes cluster starts aggressively evicting Pods with `Evicted` status, citing `DiskPressure`. You check the node, but the main data disk has 50% free space. What is likely causing the eviction, and how do you fix it?",
 "`DiskPressure` triggers when either available disk space OR available inodes drop below a threshold (usually 10-15%) on the node's root filesystem (which handles container ephemeral storage and overlays), even if a secondary data disk is empty. To fix it, you must clear old unused Docker images/containers, or attach a larger disk specifically for `/var/lib/docker` or `/var/lib/containerd`.",
 ["Node root filesystem is running out of space or INODES", "Main data disk space doesn't prevent root filesystem exhaustion", "Fix by clearing unused images or expanding /var/lib/containerd"],
 ["The pods are using too much CPU"]),

("DO_K8", "tradeoff", "medium", "tradeoff", ["Kubernetes Architecture"],
 "What tradeoffs are involved in using a `DaemonSet` instead of a `Deployment` for running log forwarding agents (like Fluentd or Promtail) in a Kubernetes cluster?",
 "A `DaemonSet` guarantees exactly one instance of the agent runs on every single node, ensuring all node-level logs are captured efficiently without manual scaling, but wastes resources if some nodes don't need logging. A `Deployment` relies on the scheduler and could place multiple agents on one node and none on others, failing to capture complete cluster logs.",
 ["DaemonSet guarantees exactly one pod per node", "Ensures complete node-level log capture", "Deployments could schedule unevenly, missing logs from some nodes"],
 ["DaemonSets are much faster than Deployments"]),

("DO_K8", "implement", "hard", "implementation", ["Kubernetes Security"],
 "How would you configure a Kubernetes Pod to securely assume an AWS IAM Role (using IRSA) rather than passing long-lived AWS credentials as environment variables?",
 "I would configure IAM Roles for Service Accounts (IRSA). First, I would create an AWS IAM Role with a trust policy allowing the cluster's OIDC provider to assume it. Then, I would create a Kubernetes ServiceAccount annotated with the IAM Role ARN. Finally, I would assign that ServiceAccount to the Pod, which allows the AWS SDK inside the container to automatically securely assume the role via a temporary web identity token.",
 ["Use IAM Roles for Service Accounts (IRSA)", "Create an IAM role trusting the cluster's OIDC provider", "Annotate a Kubernetes ServiceAccount with the IAM Role ARN and assign it to the Pod"],
 ["Put the AWS Access Key in a Kubernetes Secret"]),

("DO_K8", "scenario", "medium", "scenario", ["Kubernetes Operations"],
 "During a rolling update of a Kubernetes Deployment, some incoming HTTP requests result in 502 Bad Gateway errors. The pods take 10 seconds to fully initialize their application. What configuration is missing?",
 "The Deployment is missing a `readinessProbe`. Without it, Kubernetes assumes the container is ready to receive traffic the millisecond the process starts, routing traffic to it before the application has actually initialized its HTTP server. Adding a `readinessProbe` ensures Kubernetes waits until the probe passes before adding the Pod to the Service endpoints.",
 ["Missing a readinessProbe", "Kubernetes routes traffic before the application HTTP server is fully booted", "readinessProbe forces Kubernetes to wait until the app is actually ready"],
 ["The Deployment needs more CPU limits"]),

("DO_K8", "compare", "hard", "comparison", ["Kubernetes Scaling"],
 "Compare the operational behavior of Kubernetes `HorizontalPodAutoscaler` (HPA) scaling on CPU utilization versus scaling on custom metrics (like SQS queue depth via KEDA). What challenges arise with custom metrics?",
 "Scaling on CPU is built-in (via Metrics Server), fast, and reactive, but fails for workloads heavily bound by external I/O or queue processing where CPU remains low despite a massive backlog. Scaling on custom metrics (e.g., queue depth) is proactive and strictly reflects actual business load, but requires deploying and maintaining complex external metric adapters (like Prometheus Adapter or KEDA) which adds operational overhead.",
 ["CPU scaling is native/reactive, but fails for I/O or queue-bound workloads", "Custom metrics (queue depth) scale based on actual backlog/work to be done", "Custom metrics require complex external adapters (KEDA/Prometheus)"],
 ["Custom metrics are built natively into the Kubernetes API"]),

# ---------------- DO_AW ----------------
("DO_AW", "fundamentals", "easy", "concept", ["AWS Architecture"],
 "What is the fundamental difference between an AWS Application Load Balancer (ALB) and a Network Load Balancer (NLB)?",
 "An ALB operates at Layer 7 (HTTP/HTTPS), inspecting requests to perform advanced routing based on URL paths, headers, and hostnames. An NLB operates at Layer 4 (TCP/UDP), passing traffic directly to targets with extremely low latency and capable of handling millions of requests per second without needing to inspect the HTTP payload.",
 ["ALB: Layer 7 (HTTP/HTTPS), supports advanced routing (paths, headers)", "NLB: Layer 4 (TCP/UDP), extremely high throughput, low latency", "NLB does not inspect HTTP payloads"],
 ["ALB is for private networks and NLB is for public networks"]),

("DO_AW", "scenario", "medium", "scenario", ["AWS Networking"],
 "An EC2 instance deployed in a private subnet cannot access the internet to download software updates, even though it has a security group allowing outbound traffic `0.0.0.0/0`. What architectural component is missing?",
 "The private subnet is missing a route to a NAT Gateway (or NAT Instance). Instances in private subnets do not have public IP addresses, so they cannot route traffic directly through an Internet Gateway (IGW). The subnet's route table must direct internet-bound traffic (`0.0.0.0/0`) to a NAT Gateway situated in a public subnet.",
 ["Missing a route to a NAT Gateway", "Private subnets cannot route directly to an Internet Gateway (IGW)", "Route table must direct 0.0.0.0/0 to the NAT Gateway in a public subnet"],
 ["The instance needs an Elastic IP attached directly to it"]),

("DO_AW", "tradeoff", "medium", "tradeoff", ["AWS Compute"],
 "What are the tradeoffs between deploying a stateless application on AWS Fargate versus running it on self-managed EC2 instances within an ECS cluster?",
 "AWS Fargate is serverless compute for containers; it eliminates the operational overhead of patching, scaling, and securing underlying OS instances, but it is generally more expensive per compute-hour and prevents access to the underlying host for advanced troubleshooting. EC2 provides full control, cost savings (especially with Reserved/Spot instances), and host access, but requires heavy operational maintenance of the cluster capacity and AMI patching.",
 ["Fargate: serverless, zero host maintenance, but higher cost and no host access", "EC2: full control, cheaper (Spot/Reserved), but requires heavy operational overhead (patching, scaling)", "Fargate removes capacity management headaches"],
 ["Fargate is a database service, EC2 is for containers"]),

("DO_AW", "debug", "hard", "debugging", ["AWS Lambda"],
 "A lambda function configured inside an Amazon VPC occasionally experiences severe cold start latency spikes (up to 10 seconds). How do VPC-attached Lambdas work under the hood, and how can this latency be mitigated?",
 "Historically, VPC-attached Lambdas created a new Elastic Network Interface (ENI) upon cold start, taking seconds. AWS mitigated this using AWS Hyperplane, which creates shared ENIs at function creation time. However, severe cold starts can still occur if the function code initialization is heavy or Provisioned Concurrency is not used. To mitigate, enable Provisioned Concurrency to keep instances warm.",
 ["VPC Lambdas use Hyperplane ENIs (formerly created ENIs dynamically, causing extreme delays)", "Mitigate by enabling Provisioned Concurrency", "Optimize function code initialization/dependencies"],
 ["Move the Lambda out of the VPC completely; Lambdas cannot work in VPCs"]),

("DO_AW", "scenario", "medium", "scenario", ["AWS IAM"],
 "You need to grant a third-party SaaS vendor read-only access to a specific S3 bucket in your AWS account. How do you design this access securely without creating long-lived IAM user access keys?",
 "I would use an IAM Cross-Account Role. I would create an IAM Role in my account with a policy granting `s3:GetObject` to the specific bucket. I would configure the Role's Trust Relationship to allow the third-party vendor's AWS Account ID to assume the role, and mandate the use of a unique `ExternalId` to prevent confused deputy attacks. The vendor will dynamically assume the role to get temporary credentials.",
 ["Create an IAM Cross-Account Role", "Configure the Trust Relationship with the vendor's Account ID", "Require a unique ExternalId to prevent confused deputy attacks"],
 ["Email them the root account password"]),

("DO_AW", "explain", "medium", "concept", ["AWS Auto Scaling"],
 "Explain the concept of an AWS Auto Scaling Group (ASG) lifecycle hook. What operational problem does it solve during scale-in events?",
 "An ASG lifecycle hook allows you to pause an instance's launch or termination process. During a scale-in (termination), the hook puts the instance in a `Terminating:Wait` state. This solves the problem of abrupt termination by allowing you to run a script (via EventBridge/Lambda or SSM) to gracefully drain connections, offload logs, or finish processing queue jobs before the instance is finally killed.",
 ["Pauses the launch or termination process", "Prevents abrupt termination during scale-in", "Allows graceful draining of connections, logs, and queue jobs"],
 ["Lifecycle hooks automatically reboot crashed instances"]),

("DO_AW", "tradeoff", "hard", "tradeoff", ["Cloud Architecture"],
 "What tradeoffs exist between designing a multi-region active-active cloud architecture versus an active-passive (pilot light) disaster recovery architecture?",
 "Active-Active provides near-zero RTO/RPO and immediate failover, but introduces massive complexity in data replication (split-brain, eventual consistency, conflicts) and doubles base infrastructure costs. Active-Passive (Pilot Light) is highly cost-effective and simpler to maintain since data only flows one way, but incurs a higher RTO (minutes/hours to spin up compute) and risks failover mechanisms failing if not regularly tested.",
 ["Active-Active: near-zero RTO, immediate failover, but massive data replication complexity and double costs", "Active-Passive: highly cost-effective, simpler data flow", "Active-Passive: higher RTO (slower recovery) and risks untested failovers failing"],
 ["Active-Active means using both AWS and Azure simultaneously"]),

("DO_AW", "compare", "easy", "comparison", ["AWS Storage"],
 "Compare Amazon S3 Standard storage with S3 Glacier. When would you choose to use Glacier?",
 "S3 Standard is designed for frequently accessed data, offering millisecond latency for immediate retrieval, but costs more per GB. S3 Glacier is a highly secure, low-cost storage class for data archiving. You use Glacier for long-term backups or regulatory compliance data where you rarely need access and can tolerate retrieval times ranging from minutes to hours.",
 ["S3 Standard: immediate millisecond access, higher cost per GB", "Glacier: low-cost data archiving, retrieval takes minutes to hours", "Use Glacier for long-term backups and regulatory compliance"],
 ["Glacier is used for caching website images globally"]),

# ---------------- DO_TF ----------------
("DO_TF", "fundamentals", "easy", "concept", ["Terraform"],
 "What is the purpose of the Terraform state file (`terraform.tfstate`), and why is it dangerous to commit it to a public Git repository?",
 "The state file maps Terraform configuration resources to real-world cloud infrastructure objects (via their IDs). It tracks metadata and resource dependencies. It is dangerous to commit to public Git because it stores all resource attributes in plain text, meaning database passwords, API keys, and sensitive infrastructure details will be fully exposed.",
 ["Maps configuration to real-world cloud resources", "Tracks metadata and dependencies for accurate updates/deletions", "Dangerous because it stores sensitive secrets and passwords in plain text"],
 ["The state file is an executable script that builds servers"]),

("DO_TF", "scenario", "medium", "scenario", ["Terraform"],
 "A colleague manually deleted an AWS RDS instance through the AWS Console, but the resource still exists in the Terraform state. What happens when you run `terraform plan`, and how does Terraform handle the discrepancy?",
 "During the `terraform plan` execution, Terraform performs a 'refresh' phase. It queries the AWS API for the state of all resources. It will notice the RDS instance no longer exists, update the in-memory state, and the resulting plan will output that it intends to recreate (create) the missing RDS instance to match the desired state defined in your `.tf` files.",
 ["Terraform refreshes the state by querying the cloud provider API", "It detects the resource is missing from the real world", "The plan will propose recreating (creating) the missing resource"],
 ["Terraform will crash and corrupt the state file"]),

("DO_TF", "implement", "medium", "implementation", ["Terraform Security"],
 "How do you securely inject a database password into a Terraform configuration without hardcoding it in the `.tf` files or exposing it in CLI logs?",
 "I would define the password as a variable in Terraform and mark it as `sensitive = true` (which redacts it from CLI output). To inject it securely, I would use an environment variable prefixed with `TF_VAR_` (e.g., `export TF_VAR_db_password=secret`) in the CI/CD pipeline, or retrieve it dynamically using a data source (e.g., `data \"aws_secretsmanager_secret_version\"`).",
 ["Mark the Terraform variable as `sensitive = true`", "Inject via environment variable `TF_VAR_db_password`", "Or dynamically fetch it using a Secrets Manager data source"],
 ["Write it in the main.tf file but put a comment saying 'do not read'"]),

("DO_TF", "tradeoff", "hard", "tradeoff", ["Infrastructure as Code"],
 "What are the architectural tradeoffs of maintaining a single monolithic Terraform state file for an entire cloud infrastructure versus breaking it into multiple independent, isolated state files?",
 "A monolithic state is easy to set up and allows seamless cross-resource referencing (e.g., VPC ID to EC2), but a single typo can destroy the entire environment, operations (plans/applies) become painfully slow, and lock contention prevents team collaboration. Multiple isolated states (e.g., separating networking from applications) limit the blast radius, speed up applies, and enable parallel team work, but require complex dependency management (using `terraform_remote_state` or data sources).",
 ["Monolithic: easy referencing, but massive blast radius (one mistake destroys everything) and slow operations", "Isolated states: limits blast radius, fast applies, enables parallel team collaboration", "Isolated states: requires complex remote state sharing/data sources"],
 ["Monolithic states are required by HashiCorp for enterprise support"]),

("DO_TF", "debug", "hard", "debugging", ["Terraform State"],
 "You run `terraform apply` and it fails with a `409 Conflict` or locking error stating the state is locked by another user, but no one else is currently running Terraform. How do you safely resolve this?",
 "This usually happens if a previous CI/CD run crashed or was forcefully aborted, leaving the remote backend (like DynamoDB or Consul) locked. First, I would rigorously verify that absolutely no other pipeline or user is actively running an apply. Once verified, I would run `terraform force-unlock <LOCK_ID>` using the lock ID provided in the error message to manually release the lock.",
 ["Verify definitively that no other process is actively running", "State locks are left orphaned by crashed/aborted CI/CD pipelines", "Use `terraform force-unlock <LOCK_ID>` to release it"],
 ["Delete the entire DynamoDB table and start over"]),

# ---------------- DO_CI ----------------
("DO_CI", "fundamentals", "easy", "concept", ["GitOps"],
 "What is the core philosophy of GitOps regarding infrastructure and application deployments?",
 "The core philosophy of GitOps is that a Git repository acts as the single source of truth for the desired state of the entire system. Instead of imperative scripts pushing changes, software agents (like ArgoCD or Flux) continuously monitor the Git repository and automatically pull and reconcile the cluster state to match the declarative configuration stored in Git.",
 ["Git is the single source of truth for desired state", "Changes are made via pull requests, not manual kubectl commands", "Software agents pull and automatically reconcile the state"],
 ["GitOps means storing passwords in Git"]),

("DO_CI", "explain", "medium", "concept", ["Deployment Strategies"],
 "Explain the difference between a Blue/Green deployment strategy and a Canary deployment strategy.",
 "In Blue/Green, you deploy the new version (Green) alongside the old version (Blue) in an identical but separate environment. Once Green is verified, you switch 100% of the traffic router over instantly; rollback is instant. In a Canary deployment, you route a tiny percentage of live production traffic (e.g., 5%) to the new version, monitor it for errors, and gradually increase traffic to 100% over time.",
 ["Blue/Green: 100% traffic switch to an identical parallel environment", "Canary: Gradual traffic shift (e.g., 5%, then 20%, then 100%)", "Canary minimizes the blast radius of a bad release on users"],
 ["Blue/Green requires painting the servers physical colors"]),

("DO_CI", "scenario", "medium", "scenario", ["CI/CD Optimization"],
 "A CI/CD pipeline building Docker images takes 20 minutes because it installs hundreds of npm packages from scratch on every run. How do you optimize the Dockerfile and pipeline to drastically reduce this build time?",
 "I would leverage Docker layer caching. In the Dockerfile, I would copy `package.json` and `package-lock.json` FIRST, run `npm install`, and ONLY THEN copy the rest of the application source code. If the application code changes but the dependencies don't, Docker uses the cached `npm install` layer. I would also ensure the CI/CD pipeline uses `--cache-from` connected to a remote container registry.",
 ["Leverage Docker layer caching correctly", "Copy dependency files and install BEFORE copying the rest of the source code", "Use `--cache-from` in the CI/CD pipeline to pull external caches"],
 ["Remove the npm install command entirely"]),

("DO_CI", "implement", "hard", "implementation", ["CI/CD Architecture"],
 "How would you design a CI/CD pipeline that strictly prevents untested code from reaching production while still allowing developers to quickly test feature branches in an isolated cloud environment?",
 "I would implement branch-based environments. On a pull request, the CI pipeline builds an image, runs unit tests, and deploys it to a dynamic, ephemeral preview environment (e.g., Kubernetes namespace). Once the PR is merged to `main`, the CD pipeline runs integration tests and deploys to a persistent Staging environment. Promotion to Production would be a gated, manual approval step triggering a deployment of the exact same immutable artifact tested in Staging.",
 ["Create dynamic, ephemeral preview environments on Pull Requests", "Merge to main deploys to Staging; promotion to Prod is gated", "Promote the exact same immutable artifact across environments (build once)"],
 ["Let developers SSH directly into production to test their code"]),

("DO_CI", "tradeoff", "medium", "tradeoff", ["Monorepo"],
 "What tradeoffs exist when adopting a 'monorepo' architecture for CI/CD pipelines compared to having separate repositories and pipelines for every microservice?",
 "A monorepo simplifies dependency management, standardizes tooling, and allows atomic commits across multiple services simultaneously. However, CI/CD pipelines become highly complex; a simple push triggers the entire pipeline unless you implement advanced path-based filtering (e.g., Bazel, Nx) to only build and test the specific microservices that changed. It can also bloat git clone times.",
 ["Monorepo simplifies atomic commits and dependency management", "Pipelines become complex, risking building everything on every commit", "Requires advanced path-based execution/filtering (like Bazel or Nx)"],
 ["Monorepos are banned by Git natively"]),

("DO_CI", "debug", "hard", "debugging", ["Kubernetes Deployments"],
 "A Jenkins pipeline deploying to Kubernetes occasionally fails with a timeout during the `kubectl rollout status` step, even though the new pods are running. What application-level issue usually causes this pipeline failure?",
 "The pods are in a `Running` state, but their `readinessProbe` is failing. `kubectl rollout status` waits for the pods to become completely 'Ready' and for the old pods to terminate. If the application inside the container is failing to connect to a database or returning 500s to the readiness probe, the rollout pauses indefinitely until it hits the progress deadline timeout and fails the pipeline.",
 ["The pods are Running but the `readinessProbe` is failing", "Rollout status waits for pods to become 'Ready', not just 'Running'", "Application is likely crashing, failing health checks, or missing dependencies"],
 ["Jenkins doesn't support Kubernetes rollouts"]),

# ---------------- DO_OB ----------------
("DO_OB", "explain", "easy", "concept", ["Observability"],
 "Explain the difference between a metric, a log, and a trace in the context of system observability.",
 "Metrics are aggregatable numerical data points measured over time (e.g., CPU usage %, HTTP 500 count). Logs are immutable, discrete text records of specific events (e.g., 'User logged in', error stack traces). Traces represent the end-to-end journey of a single request across multiple distributed microservices, showing latency and bottlenecks at each hop.",
 ["Metrics: numerical time-series data (e.g., CPU, error rates)", "Logs: discrete text records of specific events/errors", "Traces: end-to-end journey of a single request across microservices"],
 ["They are three different words for the exact same text file"]),

("DO_OB", "scenario", "medium", "scenario", ["Distributed Tracing"],
 "A microservice architecture has 50 different services. A user reports that checking out their cart occasionally takes 10 seconds, but no single service shows high CPU. How do you instrument the system to find the bottleneck?",
 "I would implement Distributed Tracing (e.g., using OpenTelemetry, Jaeger, or Datadog). When the checkout request enters the API Gateway, a unique `trace_id` is generated. This ID is passed in HTTP headers (context propagation) to every downstream microservice. By visualizing the trace, I can see exactly a waterfall graph of latency, identifying which specific downstream service or database query took 9.5 seconds.",
 ["Implement Distributed Tracing (OpenTelemetry/Jaeger)", "Pass a unique trace_id via HTTP headers to all downstream services", "Visualize the waterfall graph to pinpoint the exact slow service/hop"],
 ["Ask the user to restart their computer"]),

("DO_OB", "tradeoff", "hard", "tradeoff", ["Monitoring Architecture"],
 "What are the tradeoffs between using a push-based metrics collection system (like Telegraf/StatsD) versus a pull-based system (like Prometheus) in a highly dynamic, ephemeral container environment?",
 "A push-based system forces every container to know the address of the central metrics server, risking overwhelming the server with UDP/TCP bursts, but easily handles very short-lived batch jobs. A pull-based system (Prometheus) relies on a central server scraping endpoints; it automatically discovers targets (via Kubernetes API), handles backpressure well, and prevents DDoS, but struggles to scrape very short-lived jobs before they terminate (requiring a Pushgateway).",
 ["Push: easily captures short-lived jobs, but risks overwhelming the central server", "Pull (Prometheus): auto-discovers targets, handles backpressure, resilient", "Pull struggles with short-lived batch jobs (requires Pushgateway)"],
 ["Push-based systems use email, pull-based systems use SMS"]),

("DO_OB", "implement", "medium", "implementation", ["Alerting"],
 "How would you configure Prometheus Alertmanager to prevent alert fatigue during a massive network outage that causes 100 different services to fail simultaneously?",
 "I would use Grouping and Inhibition rules. Grouping combines multiple alerts of a similar nature (e.g., all 'InstanceDown' alerts for a specific cluster) into a single notification. Inhibition suppresses lower-severity alerts when a higher-severity alert is active (e.g., if the 'NetworkSwitchDown' alert fires, inhibit all 'ServiceUnreachable' alerts for machines connected to that switch).",
 ["Use Grouping to roll up 100 similar alerts into 1 single notification", "Use Inhibition to suppress symptom alerts if the root cause alert is firing", "Prevents pagers from exploding with redundant noise"],
 ["Turn off the alerting system completely during outages"]),

("DO_OB", "fundamentals", "medium", "concept", ["Site Reliability Engineering"],
 "In Site Reliability Engineering (SRE), what is an Error Budget, and how does it dictate the balance between feature velocity and system reliability?",
 "An Error Budget is the maximum allowable time a system can be unreliable, derived from the Service Level Objective (SLO). If the SLO is 99.9% uptime, the error budget is 0.1% downtime (43 minutes/month). If developers burn through the error budget due to outages or bad releases, feature releases are halted, and engineering effort is strictly redirected to reliability and technical debt until the budget recovers.",
 ["Derived from the SLO (e.g., 99.9% SLO = 0.1% Error Budget)", "The maximum allowable downtime/errors in a time window", "If exhausted, feature releases halt to focus exclusively on reliability fixes"],
 ["It is a financial budget for buying more servers"]),

# ---------------- DO_NW ----------------
("DO_NW", "explain", "easy", "concept", ["Networking"],
 "What is the purpose of a Reverse Proxy in modern web architecture?",
 "A reverse proxy sits in front of backend servers and intercepts incoming client requests. Its primary purposes are to provide load balancing across multiple backend servers, handle SSL/TLS termination, cache static content, and hide the internal network architecture from the public internet for security.",
 ["Sits in front of backend servers intercepting client requests", "Provides load balancing and SSL termination", "Hides internal network architecture / provides security"],
 ["A reverse proxy makes the website run backwards"]),

("DO_NW", "scenario", "medium", "scenario", ["Content Delivery Networks"],
 "A web application experiences an unexpected spike in global traffic, but users in Europe are reporting extremely slow loading times for static images, while US users are fine. How do you resolve this at the networking layer?",
 "The servers are likely located in the US, causing high network latency for European users across the Atlantic. To resolve this, I would implement a Content Delivery Network (CDN) like Cloudflare or AWS CloudFront. The CDN caches the static images in edge locations globally (e.g., Frankfurt, London), allowing European users to download the assets from a server physically close to them.",
 ["High geographic latency due to US-based origin servers", "Implement a Content Delivery Network (CDN)", "Cache static assets at global edge locations close to the users"],
 ["Move all the servers to Europe instead"]),

("DO_NW", "debug", "hard", "debugging", ["Networking"],
 "An internal service attempting to connect to an external API occasionally hangs for exactly 60 seconds before throwing a timeout, but DNS resolution works perfectly. What network layer component is likely dropping the packets silently instead of rejecting them?",
 "Silent packet drops are almost always caused by a strict Firewall or Security Group rule configured to `DROP` (or ignore) unauthorized packets rather than sending an ICMP `REJECT` packet back. Because the client receives no response, the TCP handshake hangs in a SYN-SENT state until the OS-level TCP timeout (often 60 seconds) is reached.",
 ["Caused by a Firewall or Security Group dropping packets silently", "The firewall is configured to DROP instead of REJECT (no ICMP response)", "TCP handshake hangs until the OS-level timeout (usually 60s)"],
 ["The external API is turned off"]),

("DO_NW", "tradeoff", "medium", "tradeoff", ["Service Mesh"],
 "What tradeoffs exist when implementing a Service Mesh (like Istio or Linkerd) in a Kubernetes cluster instead of relying on standard Kubernetes Services and Ingress?",
 "A Service Mesh provides advanced traffic management (canary routing, retries), mutual TLS (mTLS) encryption between services, and deep observability out of the box. However, it injects a sidecar proxy into every single pod, drastically increasing memory/CPU consumption, adding network latency to every hop, and introducing immense operational complexity to the cluster.",
 ["Provides advanced traffic routing, mTLS security, and deep observability", "Injects sidecar proxies everywhere, increasing resource consumption and latency", "Introduces immense operational and debugging complexity"],
 ["Service meshes remove the need for Kubernetes completely"]),

("DO_NW", "implement", "hard", "implementation", ["DNS and Disaster Recovery"],
 "How would you design a highly available DNS architecture using AWS Route 53 to seamlessly failover user traffic to a backup region if the primary region's application load balancer stops responding?",
 "I would configure Route 53 with a Failover Routing Policy. I would create an active/primary record pointing to the Primary ALB, and a passive/secondary record pointing to the Backup region's ALB. Crucially, I would attach a Route 53 Health Check to the Primary ALB. If the health check fails, Route 53 automatically updates DNS resolution to route all new traffic to the secondary region.",
 ["Use Route 53 Failover Routing Policy", "Create Primary and Secondary/Backup records", "Attach a Route 53 Health Check to the Primary endpoint to trigger automatic failover"],
 ["Change the DNS record manually when someone calls you"]),

# ---------------- DO_SC ----------------
("DO_SC", "fundamentals", "easy", "concept", ["Cloud Security"],
 "What is the Principle of Least Privilege in cloud security architecture?",
 "The Principle of Least Privilege dictates that a user, application, or service should be granted only the absolute minimum permissions and access rights necessary to perform its specific authorized task, and nothing more. This minimizes the blast radius if the entity is compromised.",
 ["Grant only the absolute minimum permissions required for a task", "Applies to users, applications, and services", "Minimizes the blast radius of a security compromise"],
 ["It means everyone gets full admin access by default"]),

("DO_SC", "scenario", "medium", "scenario", ["Incident Response"],
 "A developer accidentally hardcoded a cloud API key in a source code file and pushed it to a public GitHub repository. What immediate incident response steps must you take?",
 "First, instantly revoke/delete the compromised API key in the cloud provider's console; you cannot assume it hasn't been scraped by bots (which happens in seconds). Second, audit the cloud provider's logs (e.g., AWS CloudTrail) to see if the key was used maliciously. Finally, generate a new key, securely inject it via a secrets manager, and remove the key from the Git history.",
 ["Instantly revoke/delete the compromised key in the cloud console", "Audit access logs (CloudTrail) to identify malicious usage", "Generate a new key and securely rotate it (do not just delete from Git)"],
 ["Just delete the file in the next commit and don't tell anyone"]),

("DO_SC", "implement", "medium", "implementation", ["Secrets Management"],
 "How do you securely manage and inject secrets (like database credentials) into a Kubernetes application using a tool like HashiCorp Vault or AWS Secrets Manager, avoiding Kubernetes native Secrets?",
 "Instead of storing secrets in etcd as base64-encoded Kubernetes Secrets, I would use the Secrets Store CSI Driver or a mutating admission webhook (like Vault Agent Injector). These tools dynamically fetch the secret from the external vault using the Pod's identity (ServiceAccount) and mount the secret directly into the Pod's memory or ephemeral volume at runtime, leaving no trace in the Kubernetes API.",
 ["Use Secrets Store CSI Driver or Vault Agent Injector", "Fetch dynamically at runtime using the Pod's ServiceAccount identity", "Mount the secret directly into memory/ephemeral volume, bypassing etcd"],
 ["Hardcode the secrets in the Docker image"]),

("DO_SC", "tradeoff", "hard", "tradeoff", ["Container Security"],
 "What are the tradeoffs between running containers as `root` (UID 0) versus enforcing a strict `runAsNonRoot` security context in a Kubernetes cluster?",
 "Running as root is extremely easy (many legacy apps and package managers assume root access), but is a massive security risk; if a container breakout vulnerability exists, the attacker gains root access on the underlying host node. Enforcing `runAsNonRoot` (using PodSecurityPolicies/Admission Controllers) heavily mitigates breakout impacts, but requires complex Dockerfile modifications (changing file permissions, avoiding ports < 1024).",
 ["Root: easy compatibility, but massive risk of host compromise upon container breakout", "runAsNonRoot: heavily mitigates breakout attacks", "runAsNonRoot: requires rewriting Dockerfiles (permissions, ports > 1024)"],
 ["Running as root makes the application run faster"]),

("DO_SC", "debug", "medium", "debugging", ["Linux Security"],
 "A newly deployed container image fails to start, logging a `Permission denied` error when trying to bind to port 80. Why does this happen on Linux, and how do you fix it without running as root?",
 "On Linux, binding to ports below 1024 (privileged ports) strictly requires root privileges. Because the container is configured with a security context to run as a non-root user, the OS denies the bind. To fix this without running as root, modify the application configuration inside the container to bind to a higher port (e.g., 8080) and use a Load Balancer or Kubernetes Service to map external port 80 to container port 8080.",
 ["Ports below 1024 are privileged and require root access on Linux", "Container is running as a non-root user", "Fix: Bind application to a higher port (e.g., 8080) and map it via Service/LB"],
 ["Give the container administrative sudo access"]),

# ---------------- DO_CT ----------------
("DO_CT", "fundamentals", "easy", "concept", ["Docker Architecture"],
 "What is the primary difference between a Virtual Machine (VM) and a Docker Container?",
 "A Virtual Machine runs a full, independent Guest Operating System with its own kernel on top of a hypervisor. A Docker Container isolates applications at the process level, sharing the underlying Host OS kernel with other containers, making containers drastically lighter, faster to boot, and more resource-efficient.",
 ["VM runs a full Guest OS and kernel on a hypervisor", "Containers share the host OS kernel", "Containers are lightweight, fast to boot, and process-isolated"],
 ["A container is just a smaller virtual machine"]),

("DO_CT", "explain", "medium", "concept", ["Linux Internals"],
 "Explain how Docker uses Linux Namespaces and Cgroups to achieve container isolation.",
 "Linux Namespaces provide process-level isolation; they ensure a container only sees its own restricted view of the system (its own PID tree, network interfaces, and mount points). Control Groups (Cgroups) provide resource limitation and accounting; they ensure a container can only consume a restricted amount of CPU, memory, and disk I/O, preventing it from starving the host.",
 ["Namespaces: isolate the view of the system (PIDs, network, mounts)", "Cgroups (Control Groups): limit and account for resource usage (CPU, Memory)", "Combined, they create the sandbox known as a container"],
 ["Namespaces are for naming containers, Cgroups are for grouping them"]),

("DO_CT", "scenario", "hard", "scenario", ["Linux Troubleshooting"],
 "A production Linux server becomes unresponsive due to a runaway process consuming 100% of the memory. The OOM (Out of Memory) Killer terminates the primary database process instead of the runaway process. How do you configure Linux to prioritize killing the correct process?",
 "The Linux OOM Killer uses a heuristic score (`oom_score`) to decide which process to kill (usually the one using the most memory). You can protect the critical database process by adjusting its `oom_score_adj` value (in `/proc/<pid>/oom_score_adj`) to a highly negative number (e.g., -1000), which heavily discourages the kernel from targeting it during memory pressure.",
 ["OOM Killer targets processes based on a heuristic score", "Protect critical processes by setting a negative `oom_score_adj`", "This discourages the kernel from selecting the database for termination"],
 ["Install more RAM while the server is running"]),

("DO_CT", "tradeoff", "medium", "tradeoff", ["Docker Images"],
 "What are the tradeoffs of building a Docker image using Alpine Linux as the base image versus using a standard distribution like Ubuntu or Debian?",
 "Alpine Linux creates extremely small images (reducing pull times and attack surface area) by using `musl libc` and `apk`. However, many standard applications and Python/Node/C++ libraries are compiled against `glibc` (used by Ubuntu/Debian). Using Alpine can lead to obscure compilation errors, missing dependencies, and slower build times as you manually compile C-extensions from source.",
 ["Alpine: highly secure, extremely small image sizes", "Alpine uses musl libc instead of glibc", "Tradeoff: frequent compilation errors and missing dependencies for C-extensions"],
 ["Alpine Linux is owned by Windows"]),

("DO_CT", "debug", "hard", "debugging", ["Linux Troubleshooting"],
 "You SSH into a Linux server and notice that `df -h` shows the root filesystem is 100% full, but running `du -sh /*` only accounts for 30% of the disk capacity. What is the most likely cause of this hidden disk usage, and how do you free the space?",
 "This occurs when a large file (like an application log file) has been deleted using `rm`, but a running process (like a web server or Docker daemon) still holds an open file descriptor to it. The OS cannot free the disk space until the process closes the file. You must find the process using `lsof | grep deleted` and restart that specific process to free the space.",
 ["Deleted files are still held open by a running process", "The OS cannot free the disk blocks until the file descriptor is closed", "Find with `lsof | grep deleted` and restart the offending process"],
 ["The hard drive has physical bad sectors"]),

# ---------------- DO_AR ----------------
("DO_AR", "scenario", "medium", "scenario", ["System Architecture"],
 "An e-commerce platform relies on a synchronous REST API call to a third-party fraud detection service. The third-party service goes down, causing the entire checkout process to fail. How do you redesign this architecture to be resilient to the dependency's failure?",
 "I would redesign it using asynchronous communication or graceful degradation. Instead of blocking the checkout, the system should accept the order, place a 'Fraud Check Request' onto a message queue (like RabbitMQ or SQS), and return success to the user. A background worker processes the queue when the third-party service recovers, marking the order as 'Verified'.",
 ["Decouple the systems using asynchronous communication (Message Queues)", "Accept the order immediately and process the fraud check in the background", "Ensures checkout succeeds even if the dependency is down"],
 ["Call the third-party service faster"]),

("DO_AR", "tradeoff", "hard", "tradeoff", ["Microservices"],
 "What are the operational tradeoffs of implementing a strict Circuit Breaker pattern on all outbound microservice calls compared to using simple retry mechanisms with exponential backoff?",
 "Retries with backoff are simple to implement and handle transient network blips well, but if a downstream service is truly struggling, massive concurrent retries from all clients will cause a 'retry storm', essentially DDoS'ing the failing service. A Circuit Breaker detects the failure threshold, instantly fails fast (saving client threads/resources), and gives the downstream service time to recover, but requires complex state management and tuning of the open/half-open thresholds.",
 ["Retries: simple, handles transient blips, but risks DDoS'ing a struggling service (retry storm)", "Circuit Breaker: fails fast, protects client resources, allows downstream recovery", "Circuit Breakers require complex state tuning (open/half-open limits)"],
 ["Circuit breakers physically turn off power to the servers"]),

("DO_AR", "fundamentals", "medium", "concept", ["Distributed Systems"],
 "Explain the concept of 'Idempotency' in the context of distributed systems and APIs. Why is it critical for safe automated retry mechanisms?",
 "Idempotency means that executing the exact same operation multiple times yields the same state as executing it exactly once. It is critical for automated retries because network timeouts leave the client unsure if a request (like 'Charge Credit Card') succeeded or failed. If the API is idempotent (using an Idempotency-Key header), the client can safely retry without risking charging the user twice.",
 ["Executing the operation multiple times yields the same result as once", "Crucial for network timeouts where the outcome is unknown", "Allows safe retries without risking duplicate actions (like double charging)"],
 ["Idempotency means the server never crashes"])
]
