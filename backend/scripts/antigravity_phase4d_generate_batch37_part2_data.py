import os

ROLE = "DevOps / Cloud Engineer"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b3": ("Observability", "SRE & Monitoring", "Prometheus", ["DevOps / Cloud Engineer", "Backend Developer"]),
    "b4": ("Security", "Policies", "Security", ["DevOps / Cloud Engineer"]),
    "b5": ("AWS IAM", "AWS / Cloud", "AWS", ["DevOps / Cloud Engineer"]),
    "b6": ("Cloud Architecture", "DNS & Load Balancing", "Networking", ["DevOps / Cloud Engineer", "Backend Developer"]),
    "b7": ("Containers & OS", "Docker & Linux", "Linux", ["DevOps / Cloud Engineer"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    (
        "b3",
        "debug",
        "hard",
        "debugging",
        ["Observability", "Reliability Engineering"],
        "During peak load, a centralized logging pipeline using Fluent Bit and OpenSearch halts ingestion because nodes encounter the `read_only_allow_delete` disk watermark. How do you recover ingestion and re-architect buffer management to prevent future data loss?",
        "When an OpenSearch/Elasticsearch cluster node's storage reaches the flood-stage watermark (default 95% disk usage), the cluster automatically applies the `index.blocks.read_only_allow_delete: true` block across all indices on that node, rejecting all indexing requests. This causes upstream forwarders (Fluent Bit) to buffer logs locally until their memory limits or local disk buffers fill up, leading to dropped log events. To recover: 1) Immediately increase underlying EBS volume sizes or delete expired indices; 2) Manually remove the read-only block by executing `PUT /*/_settings { \"index.blocks.read_only_allow_delete\": null }`; 3) To re-architect buffer management and prevent loss: configure Fluent Bit's `storage.type filesystem` with dedicated persistent buffer paths and `storage.max_chunks_up`, ensuring logs spill safely to local disk queues during downstream backpressure; 4) Configure OpenSearch Index State Management (ISM) policies to transition indices to warm storage or delete them based on retention windows before reaching storage watermarks.",
        [
            "Identifies the root cause of the `read_only_allow_delete` flood stage watermark in OpenSearch/Elasticsearch.",
            "Details both the immediate recovery steps (disk expansion, resetting index settings block) and architectural buffers (Fluent Bit disk buffering, ISM retention policies)."
        ],
        [
            "Suggests restarting Fluent Bit daemonsets repeatedly without expanding storage or resetting index blocks.",
            "Fails to recognize that OpenSearch permanently blocks write operations once disk usage exceeds the flood stage watermark."
        ]
    ),
    (
        "b4",
        "implement",
        "easy",
        "conceptual",
        ["Security", "Kubernetes"],
        "To enforce mandatory security controls across a multi-tenant Kubernetes cluster, what is the architectural difference between Mutating Admission Webhooks and Validating Admission Webhooks in the API request lifecycle?",
        "When an API request arrives at the Kubernetes API server, it passes through authentication, authorization, and then admission control. Admission control operates in two sequential phases: 1) Mutating Admission Webhooks execute first, intercepting the submitted object and potentially modifying it before persistence (e.g., automatically injecting sidecar containers, adding required security contexts, setting default resource requests, or assigning image pull secrets); 2) Validating Admission Webhooks execute second, evaluating the final, fully-resolved object against security compliance policies (e.g., Kyverno or OPA Gatekeeper policies verifying that containers do not run as root, disallowing privileged capabilities, or enforcing approved container registry sources). If any validating webhook rejects the object, the API request fails immediately with a 403 Forbidden, and the object is never persisted to etcd.",
        [
            "Differentiates the sequence and responsibilities: mutating webhooks modify resources first, validating webhooks evaluate the final object for acceptance or rejection second.",
            "Explains real-world use cases such as sidecar injection for mutation and policy enforcement (OPA/Kyverno) for validation."
        ],
        [
            "Claims validating webhooks run before mutating webhooks in the admission pipeline.",
            "Suggests that mutating webhooks are used to reject requests while validating webhooks alter resource manifests."
        ]
    ),
    (
        "b4",
        "architecture",
        "medium",
        "architectural",
        ["Security", "AWS IAM", "Cloud Architecture"],
        "In an AWS Organizations multi-account structure, how do you architect Service Control Policies (SCPs) to establish organization-wide security guardrails while preventing administrative lockout for break-glass roles?",
        "Service Control Policies (SCPs) define the maximum available permissions across an AWS Organization or Organizational Unit (OU), acting as guardrails that cannot be bypassed even by the root user or `AdministratorAccess` roles in member accounts. To establish effective guardrails, architect SCPs using explicit `Deny` statements targeting critical security configurations, such as denying `cloudtrail:StopLogging`, `cloudtrail:DeleteTrail`, `guardduty:DeleteDetector`, and restricting regions to approved operational zones. To prevent break-glass administrative lockout, every `Deny` statement must include a `Condition` block with `StringNotLike` or `ArnNotEquals` evaluating `aws:PrincipalARN`, exempting a designated emergency break-glass IAM role (e.g., `arn:aws:iam::*:role/OrganizationBreakGlassRole`). SCPs must be applied hierarchically to OUs rather than individual accounts, and validated in sandbox OUs before widespread attachment.",
        [
            "Explains that SCPs set outer permission guardrails that restrict all principals in member accounts including root and administrators.",
            "Details how condition blocks exempt break-glass administrative roles to prevent emergency management lockout."
        ],
        [
            "Claims that an IAM user with `AdministratorAccess` in a member account can override an SCP.",
            "Suggests applying SCPs directly to individual IAM users within member accounts."
        ]
    ),
    (
        "b4",
        "scenario",
        "medium",
        "scenario",
        ["Security", "CI/CD Architecture"],
        "When establishing CI/CD automation from GitHub Actions into AWS without storing long-lived IAM credentials, how do you configure OpenID Connect (OIDC) Workload Identity Federation?",
        "To eliminate long-lived, high-risk IAM user access keys in CI/CD secrets, teams configure OpenID Connect (OIDC) federation between GitHub and AWS IAM. In AWS, an IAM OIDC Identity Provider is registered pointing to GitHub's issuer URL (`https://token.actions.githubusercontent.com`) with audience `sts.amazonaws.com`. An IAM role is created with a trust policy that permits `sts:AssumeRoleWithWebIdentity` only when GitHub Actions presents a valid signed JSON Web Token (JWT). The trust policy restricts access using conditions: `StringEquals: { 'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com' }` and `StringLike: { 'token.actions.githubusercontent.com:sub': 'repo:organization/repo-name:ref:refs/heads/main' }`. In the workflow, GitHub's `aws-actions/configure-aws-credentials` requests a short-lived OIDC token and exchanges it with AWS STS for temporary credentials that expire automatically after the job completes.",
        [
            "Outlines the registration of the GitHub OIDC provider in AWS IAM and trust policy configuration with `sts:AssumeRoleWithWebIdentity`.",
            "Emphasizes the strict condition enforcement on the `sub` (subject) claim to restrict role assumption to specific repositories and branches."
        ],
        [
            "Recommends generating IAM user access keys and saving them in GitHub Actions repository secrets.",
            "Fails to specify how the subject (`sub`) claim prevents other arbitrary GitHub repositories from assuming the IAM role."
        ]
    ),
    (
        "b4",
        "scenario",
        "hard",
        "scenario",
        ["Security", "Reliability Engineering"],
        "A microservices platform adopts HashiCorp Vault for dynamic database credential generation, but microservice pods experience intermittent connection drops when database credentials rotate. How do you architect credential renewal and connection pool handling?",
        "Dynamic database credentials in Vault provide ephemeral, short-lived database users with strict Time-To-Live (TTL) leases that automatically expire and drop from the database unless renewed. Connection drops occur when application database connection pools hold stale connections authenticated with expired credentials, or fail to re-authenticate when Vault leases rotate. To architect robust credential rotation: 1) Deploy the Vault Agent sidecar or Vault Secrets Operator to handle lease renewals and write updated credentials to an in-memory volume; 2) Configure the application's connection pool (e.g., HikariCP) with connection max-lifetime (`maxLifetime`) configured significantly lower than Vault's credential lease TTL (e.g., 30-minute pool max-lifetime against a 1-hour Vault lease); 3) Implement dynamic reload hooks or database credentials provider plugins within the application framework that dynamically poll updated credentials from disk or Vault without restarting the pod container.",
        [
            "Identifies the mismatch between connection pool lifetimes and ephemeral Vault credential lease TTLs.",
            "Prescribes configuring connection pool `maxLifetime` below the Vault lease TTL and implementing dynamic credential reload hooks via Vault Agent or Secrets Operator."
        ],
        [
            "Suggests setting Vault credential leases to 10 years to avoid connection drops.",
            "Recommends restarting the entire Kubernetes deployment every time a credential lease expires."
        ]
    ),
    (
        "b4",
        "diagnose",
        "hard",
        "problem_solving",
        ["Security", "Cloud Architecture"],
        "A security audit flags that several EC2 workloads are vulnerable to SSRF attacks targeting the AWS Instance Metadata Service (IMDS). How do you enforce IMDSv2 and configure hop limits to prevent credential theft from containerized workloads?",
        "The AWS Instance Metadata Service (IMDS) at `169.254.169.254` serves instance metadata, including temporary IAM role credentials. IMDSv1 uses simple HTTP GET requests, making it vulnerable to Server-Side Request Forgery (SSRF) vulnerabilities where an attacker tricks an application into querying metadata. IMDSv2 remediates this by requiring session-oriented requests: a client must first issue an HTTP `PUT` request with the header `X-aws-ec2-metadata-token-ttl-seconds` to obtain a session token, and pass it in subsequent `X-aws-ec2-metadata-token` headers. To enforce IMDSv2, update instance metadata options via AWS CLI: `aws ec2 modify-instance-metadata-options --instance-id <ID> --http-tokens required`. Furthermore, for containerized workloads, set `--http-put-response-hop-limit 1`; because Docker and container runtimes introduce an IP hop between the container network namespace and the host, a hop limit of 1 prevents containers from reaching IMDSv2, forcing them to use IAM Roles for Service Accounts (IRSA) instead.",
        [
            "Contrasts IMDSv1 GET vulnerabilities with IMDSv2 token-oriented PUT handshake requirements.",
            "Explains the significance of setting `--http-tokens required` and `--http-put-response-hop-limit 1` to prevent containerized workloads from accessing host instance credentials."
        ],
        [
            "Suggests that IMDSv2 is identical to IMDSv1 but only accessible over HTTPS.",
            "Fails to explain how network hop limits prevent containerized workloads from stealing host metadata."
        ]
    ),
    (
        "b5",
        "optimize",
        "easy",
        "best_practices",
        ["AWS IAM", "Security"],
        "To delegate IAM permissions creation to autonomous application teams without allowing privilege escalation, how do you utilize AWS IAM Permissions Boundaries?",
        "An IAM Permissions Boundary is an advanced governance feature that sets the maximum permissions an identity-based policy can grant to an IAM user or role. When platform engineering teams delegate permission creation to developers (allowing developers to create IAM roles for their Lambdas or microservices), malicious or misinformed developers could otherwise attach `AdministratorAccess` to their created roles, achieving privilege escalation. To prevent this, the platform team writes a policy allowing developers to create roles only if they attach a mandatory Permissions Boundary policy (enforced via a `Condition` key: `StringEquals: { 'iam:PermissionsBoundary': 'arn:aws:iam::123456789012:policy/AppBoundary' }`). The permissions boundary explicitly allows only application-specific services (e.g., S3, DynamoDB, SQS) and denies IAM/organization modifications. Even if a developer attaches full admin permissions to their new role, the effective permissions are strictly the intersection of the role policy and the boundary.",
        [
            "Explains how Permissions Boundaries define the maximum permissions boundary for delegated role creation.",
            "Details how IAM condition keys enforce that developers cannot create roles without attaching the mandatory boundary policy, preventing privilege escalation."
        ],
        [
            "Claims that IAM permission boundaries grant permissions directly to users without identity policies.",
            "Suggests using IAM Groups to restrict the permissions of assumed roles."
        ]
    ),
    (
        "b5",
        "architecture",
        "medium",
        "architectural",
        ["AWS IAM", "Networking"],
        "When connecting dozens of VPCs across multiple AWS accounts and on-premises datacenters, what architectural and routing tradeoffs favor AWS Transit Gateway over a full VPC Peering mesh?",
        "A full VPC Peering mesh requires point-to-point connections between every pair of VPCs. For N VPCs, a full mesh requires `N * (N - 1) / 2` peering connections; with 50 VPCs, that requires 1,225 peering connections, each requiring manual route table entries in every VPC, quickly reaching AWS route table limits and creating an unmanageable operational footprint. Furthermore, VPC Peering does not support transitive routing (traffic cannot enter VPC A, transit VPC B, and reach VPC C or on-premises). AWS Transit Gateway (TGW) operates as a regional hub-and-spoke cloud router. Each VPC connects with a single attachment to the TGW, reducing 50 VPC connections to 50 attachments. TGW supports transitive routing, centralized route tables for network segmentation (e.g., isolating dev, prod, and shared services), and integrates directly with AWS Direct Connect and site-to-site VPNs. The tradeoffs are cost: TGW incurs hourly attachment fees and per-GB data processing fees, whereas VPC Peering charges no hourly fees and lower inter-AZ data rates.",
        [
            "Quantifies the operational complexity and route table explosion of a VPC peering mesh versus Transit Gateway hub-and-spoke.",
            "Explains transitive routing limitations in VPC peering and cost considerations (TGW attachment and data processing fees)."
        ],
        [
            "Claims that VPC Peering natively supports transitive routing across intermediate VPCs.",
            "Asserts that AWS Transit Gateway is free of charge and always cheaper than VPC peering."
        ]
    ),
    (
        "b5",
        "scenario",
        "medium",
        "scenario",
        ["AWS IAM", "Cloud Architecture"],
        "A high-volume analytics application in private subnets generates tens of terabytes of data transfers to S3, incurring thousands of dollars in monthly NAT Gateway data processing fees. How do you eliminate these costs using VPC Endpoints?",
        "When EC2 instances or container workloads in private VPC subnets communicate with Amazon S3 over public IP endpoints, outbound traffic routes through the VPC's AWS NAT Gateway. AWS charges a per-GB data processing fee (approx. $0.045/GB) on all NAT Gateway traffic, causing massive cloud bills for high-throughput data pipelines transferring terabytes to S3. To eliminate these processing fees, the platform team provisions an S3 Gateway VPC Endpoint. Gateway VPC Endpoints are entirely free of charge and do not route through NAT Gateways; instead, they add a prefix list route (`pl-xxxx` for S3) directly into the subnet route tables pointing to the Gateway Endpoint (`vpce-xxxx`). All traffic from private subnets to S3 traverses the internal AWS network backbone directly, immediately reducing NAT Gateway data processing fees to zero while improving transfer throughput and reducing network hops.",
        [
            "Identifies NAT Gateway per-GB processing charges as the root driver of S3 data transfer costs.",
            "Explains the deployment of free Gateway VPC Endpoints and updating subnet route tables with S3 prefix lists to bypass NAT gateways."
        ],
        [
            "Recommends moving all private analytics instances into public subnets with public IPs.",
            "Suggests using Interface Endpoints (PrivateLink) for S3 without realizing they also incur hourly and per-GB charges."
        ]
    ),
    (
        "b5",
        "architecture",
        "medium",
        "architectural",
        ["AWS IAM", "Cloud Architecture"],
        "In an AWS enterprise landing zone, how does AWS Resource Access Manager (RAM) enable centralized VPC subnet sharing, and what are its operational benefits over independent VPCs?",
        "AWS Resource Access Manager (RAM) allows an organization to securely share AWS resources across accounts within AWS Organizations without duplicating infrastructure. In a centralized networking architecture, the network administrative account owns the VPC, Internet Gateways, NAT Gateways, and subnets. Using AWS RAM, the network account shares private subnets with participant application accounts. Participant accounts can launch EC2 instances, RDS databases, and EKS worker nodes directly into the shared subnets. Operational benefits include: 1) Efficient IP Address Management (IPAM), eliminating the fragmentation and exhaustion of RFC 1918 CIDR blocks caused by provisioning tiny VPCs per account; 2) Significant cost optimization by centralizing expensive shared networking resources like NAT Gateways and Direct Connect gateways; 3) Strict boundary separation where network administrators retain full control over routing tables, NACLs, and subnets while application teams maintain ownership of their compute resources.",
        [
            "Explains how AWS RAM shares VPC subnets from a central network account to application accounts in AWS Organizations.",
            "Outlines benefits including CIDR IP address conservation, NAT Gateway cost reduction, and clear governance boundaries."
        ],
        [
            "Claims that sharing subnets via RAM merges IAM permissions across all accounts into a single account.",
            "Suggests that application accounts must share their private encryption keys to participate in RAM shared VPCs."
        ]
    ),
    (
        "b5",
        "architecture",
        "hard",
        "architectural",
        ["AWS IAM", "Security"],
        "When building a multi-tenant SaaS platform that programmatically accesses customer AWS resources via AssumeRole, how do you prevent the Confused Deputy problem using an External ID?",
        "The Confused Deputy problem is a security vulnerability where a service (the deputy) with elevated permissions is manipulated by an unauthorized actor into performing actions against a target resource that the actor has no permission to access. In multi-tenant SaaS, the SaaS platform uses a single IAM role to assume customer-provided roles across thousands of customer AWS accounts. If Customer A gives the SaaS platform the ARN of Customer B's role, and the SaaS platform assumes that role without validation, the platform acts as a confused deputy, allowing Customer A to access Customer B's account. To prevent this, the customer's IAM role trust policy must require both the SaaS platform's AWS account principal AND a unique, random, secret `sts:ExternalId` generated specifically for that customer: `Condition: { 'StringEquals': { 'sts:ExternalId': '<UNIQUE_CUSTOMER_SECRET>' } }`. When assuming the role, the SaaS platform passes this External ID in the `sts:AssumeRole` API call, ensuring it only assumes roles with the customer's explicit authorization.",
        [
            "Defines the Confused Deputy vulnerability in multi-tenant SaaS cross-account role assumption.",
            "Explains the technical mechanics of the `sts:ExternalId` condition key in IAM trust policies and how it cryptographically prevents tenant cross-impersonation."
        ],
        [
            "Claims that IAM session tags or role names alone prevent the confused deputy vulnerability without external IDs.",
            "Suggests creating a new dedicated AWS account for every single customer rather than using cross-account roles with external IDs."
        ]
    ),
    (
        "b6",
        "architecture",
        "easy",
        "conceptual",
        ["Cloud Architecture", "Networking"],
        "When architecting global application ingress, what are the primary engineering tradeoffs between Anycast BGP routing and Geo-DNS routing for distributing traffic to regional endpoints?",
        "Geo-DNS routes client traffic by inspecting the client's resolver IP address and returning regional IP addresses based on geographic proximity tables. Its advantage is simplicity and support for complex application-layer routing rules; however, its major drawbacks are slow failover propagation (dictated by DNS client and resolver TTL caching, which can take minutes or hours to clear) and inaccurate routing when clients use public DNS resolvers (like Google 8.8.8.8) located far from their physical location. Anycast BGP announces the exact same single IP address from multiple geographically distributed Points of Presence (PoPs) worldwide via BGP. Internet routers automatically route client packets to the topologically closest PoP along the shortest AS path. Anycast provides near-instantaneous network failover (BGP routes reconverge in seconds if a PoP withdraws its route) and lower latency, but requires complex BGP infrastructure (e.g., AWS Global Accelerator or Cloudflare) and can cause TCP connection resets if routing flaps mid-connection.",
        [
            "Contrasts DNS TTL caching delay and resolver locality issues in Geo-DNS with BGP shortest-path routing in Anycast.",
            "Highlights Anycast's sub-second failover and TCP connection reset risks during BGP route flapping."
        ],
        [
            "Claims DNS records update instantly across the entire internet the moment TTL is set to 0.",
            "Asserts that Anycast requires separate IP addresses for every regional data center."
        ]
    ),
    (
        "b6",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Cloud Architecture", "Networking"],
        "In a high-throughput microservices architecture, what criteria determine whether an AWS Network Load Balancer (NLB) or Application Load Balancer (ALB) is the appropriate ingress controller?",
        "An Application Load Balancer (ALB) operates at Layer 7 (Application Layer). It inspects HTTP/HTTPS headers, paths, query parameters, and methods, enabling advanced routing rules, host-based routing, native gRPC and WebSocket termination, automated TLS offloading, and direct integration with AWS WAF for Layer 7 web security. However, ALB introduces slightly higher latency and terminates TCP connections. A Network Load Balancer (NLB) operates at Layer 4 (Transport Layer). It routes millions of requests per second with ultra-low sub-millisecond latency, handles volatile traffic spikes without pre-warming, supports static Anycast IP addresses and PrivateLink, and preserves the original client IP without X-Forwarded-For headers. Choose ALB when application-level routing, TLS offload, or WAF inspection is required; choose NLB when handling non-HTTP protocols, extreme latency-sensitive high-packet throughput, or when clients require static IP whitelisting.",
        [
            "Distinguishes between Layer 4 (NLB) and Layer 7 (ALB) capabilities including path routing, TLS termination, and WAF integration.",
            "Identifies specific selection criteria such as ultra-low latency, static IP requirements, and protocol support (HTTP vs raw TCP/UDP)."
        ],
        [
            "Claims that ALB handles raw TCP and UDP traffic more efficiently than NLB.",
            "Suggests that NLB can inspect HTTP headers and execute path-based URL routing."
        ]
    ),
    (
        "b6",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Cloud Architecture", "Networking"],
        "A real-time streaming platform experiences severe latency spikes for mobile clients over cellular networks due to packet loss. What advantages does HTTP/3 (QUIC) over UDP provide over HTTP/2 over TCP in resolving head-of-line blocking?",
        "In HTTP/2, multiple logical request/response streams are multiplexed over a single underlying TCP connection. While this eliminates HTTP-level head-of-line blocking, it introduces TCP-level head-of-line blocking: TCP is a byte-stream protocol that guarantees strictly ordered delivery. If a single packet is dropped on a lossy cellular network, the entire TCP connection stalls; the operating system kernel buffers all subsequent packets in the receive queue and refuses to deliver them to any HTTP/2 stream until the lost packet is retransmitted and acknowledged. HTTP/3 eliminates this by using QUIC over UDP. In QUIC, stream multiplexing is native to the transport layer. Each stream is handled independently: if a packet belonging to Stream 1 is lost, only Stream 1 pauses for retransmission, while Streams 2, 3, and 4 continue processing immediately without delay. Additionally, QUIC enables 0-RTT connection resumption and connection migration across changing cellular IP addresses without dropping connections.",
        [
            "Explains TCP-level head-of-line blocking in HTTP/2 where a single dropped packet stalls all multiplexed streams.",
            "Articulates how QUIC over UDP provides independent stream transport, eliminating cross-stream retransmission stalls and enabling connection migration."
        ],
        [
            "Claims that HTTP/2 does not suffer from head-of-line blocking under any network conditions.",
            "Suggests that UDP in HTTP/3 allows dropped packets to be ignored without reliable retransmission."
        ]
    ),
    (
        "b6",
        "optimize",
        "medium",
        "best_practices",
        ["Cloud Architecture", "Reliability Engineering"],
        "To coordinate automated multi-region disaster recovery for mission-critical web applications, how do AWS Route 53 Application Recovery Controller (ARC) routing controls prevent cascading failures during regional failover?",
        "Traditional DNS-based multi-region failover relies on automated health checks that query public endpoints. If a primary region experiences an application bug or sudden traffic spike, standard health checks fail and trigger an automated global traffic shift to the secondary region. If the secondary region lacks capacity or suffers from the same application defect, the sudden influx of shifted traffic immediately overwhelms it, causing a total global outage (cascading failure). AWS Route 53 Application Recovery Controller (ARC) prevents this through: 1) Explicit Routing Controls, which use simple on/off switches that decouple failure detection from automated rerouting, allowing operators to execute deterministic traffic shifts; 2) Safety Rules (such as assertion rules preventing more than one region from being disabled simultaneously); 3) Readiness Checks that continuously audit cross-region resource capacity, quotas, and scaling configurations, ensuring the target region is mathematically capable of handling the redirected load before traffic is shifted.",
        [
            "Explains the dangers of naive automated DNS health check failovers causing cascading cross-region collapse.",
            "Details how Route 53 ARC uses safety rules, routing controls, and continuous readiness checks to enforce safe regional failovers."
        ],
        [
            "Suggests that simple DNS weighted round-robin without safety rules is adequate for multi-region disaster recovery.",
            "Claims that Route 53 ARC automatically provisions EC2 servers during an active failover."
        ]
    ),
    (
        "b6",
        "diagnose",
        "hard",
        "problem_solving",
        ["Cloud Architecture", "Kubernetes"],
        "In a Kubernetes cluster running thousands of microservice pods, DNS lookups occasionally suffer 5-second delays due to CoreDNS UDP packet drops. How do you diagnose and eliminate this issue using `ndots` tuning and `NodeLocal DNSCache`?",
        "In Linux and Kubernetes, `/etc/resolv.conf` defaults to `ndots:5` with multiple search domains (e.g., `<namespace>.svc.cluster.local`, `svc.cluster.local`, `cluster.local`). When an application resolves an external domain containing fewer than 5 dots (e.g., `api.stripe.com` has 2 dots), the resolver sequentially queries all cluster search domains first before querying the external root. This multiplies DNS query volume by 4-5x, saturating CoreDNS pods and Linux conntrack tables. Furthermore, Linux glibc issues simultaneous A and AAAA queries over UDP; when conntrack drops UDP race packets, glibc pauses for a 5-second timeout. To diagnose, monitor CoreDNS Prometheus metrics (`coredns_dns_request_duration_seconds` and UDP drop counters). To remediate: 1) Deploy `NodeLocal DNSCache` as a DaemonSet to cache DNS lookups locally on each node, switching node-to-CoreDNS traffic from UDP to persistent TCP; 2) Tune `dnsConfig` in pod specs to reduce `ndots` (e.g., `ndots:2`) or append a trailing dot to external hostnames in application code (`api.stripe.com.`).",
        [
            "Explains how `ndots:5` triggers multiple sequential search domain queries for external hostnames, creating massive DNS amplification.",
            "Details how Linux UDP conntrack race conditions cause 5-second timeouts and how `NodeLocal DNSCache` and `dnsConfig` tuning resolve the issue."
        ],
        [
            "Claims the 5-second delay is caused by slow internet bandwidth on the host nodes.",
            "Recommends completely removing DNS resolution from Kubernetes and hardcoding IP addresses in microservice manifests."
        ]
    ),
    (
        "b7",
        "debug",
        "easy",
        "problem_solving",
        ["Containers & OS", "Linux Core"],
        "A Linux container host running cgroups v2 starts terminating background worker containers despite available system memory. How does cgroups v2 resource accounting improve over v1, and how do you diagnose memory pressure using PSI (Pressure Stall Information)?",
        "In cgroups v1, resource controllers (memory, cpu, blkio) operate in separate, uncoordinated hierarchies, leading to broken accounting where page cache writebacks and kernel memory allocations could not be reliably tracked back to the originating container. cgroups v2 introduces a single unified hierarchy where all controllers share the same tree structure, enabling comprehensive accounting across anonymous memory, page cache, swap, and kernel structures. Furthermore, cgroups v2 introduces Pressure Stall Information (PSI), exposing `/proc/pressure/memory`, `/proc/pressure/cpu`, and `/proc/pressure/io`. PSI measures the exact percentage of time processes stall waiting for resources (split into `some` and `full` stall metrics over 10s, 60s, and 300s averages). To diagnose, operators inspect container cgroup memory pressure files: if `memory.pressure` exhibits high `some` and `full` stall percentages, the container is actively thrashing memory even before reaching its absolute `memory.max` limit, prompting low-memory killers (like systemd-oomd) to terminate workloads to preserve host stability.",
        [
            "Contrasts the multi-hierarchy fragmentation of cgroups v1 with the unified hierarchy and unified accounting of cgroups v2.",
            "Explains how Pressure Stall Information (PSI) metrics measure resource stall time to detect memory thrashing before hard limit exhaustion."
        ],
        [
            "Claims that cgroups v2 simply increases the maximum RAM an EC2 instance can address.",
            "Fails to identify the diagnostic purpose of Pressure Stall Information (PSI) files."
        ]
    )
]
