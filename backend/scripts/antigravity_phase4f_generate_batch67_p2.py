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
    ("B67_2_1", "diagnose", "hard", "debugging", ["Kubernetes Networking", "Service Mesh"],
     "In an Istio Service Mesh, developers deploy a new Node.js microservice. They notice that every HTTP request to an external 3rd-party API (e.g., api.stripe.com) hangs for 5 seconds and then times out, but internal service-to-service calls work perfectly. What architectural component of the Service Mesh causes this external traffic blackholing, and how do you configure it to allow egress?",
     "By default, Istio's Envoy sidecar proxy intercepts all outbound traffic from the Pod. If the mesh is configured with outboundTrafficPolicy.mode=REGISTRY_ONLY, the sidecar will strictly drop any request to a destination that is not explicitly registered in the Istio internal service registry. Because api.stripe.com is an external DNS name not known to the mesh, Envoy blackholes the traffic, causing the timeout. To fix this safely without opening the mesh to the entire internet (ALLOW_ANY), you must create an Istio ServiceEntry. This explicitly registers the external domain and ports into the mesh registry, allowing Envoy to route and observe the outbound traffic correctly.",
     ["Identifies the Envoy sidecar proxy intercepting and dropping outbound traffic", "Identifies REGISTRY_ONLY mode restricting egress to known services", "Prescribes creating an Istio ServiceEntry to explicitly whitelist and register external domains"],
     ["Claims the Kubernetes cluster's firewall is blocking port 443 outbound"]),

    ("B67_2_2", "concept", "medium", "concept", ["Kubernetes Networking", "Architecture"],
     "Explain the architectural difference between kube-proxy (iptables mode) and a modern eBPF-based CNI (like Cilium) regarding how Kubernetes Services route traffic to Pods.",
     "kube-proxy in iptables mode creates a complex, linear chain of iptables rules on every worker node for every single Service and Endpoint in the cluster. When a packet hits the kernel network stack, the CPU must sequentially evaluate it against potentially thousands of iptables rules, causing severe latency and CPU overhead in large clusters (O(N) complexity). An eBPF-based CNI like Cilium completely bypasses iptables. It compiles highly optimized byte-code programs directly into the Linux kernel and attaches them to socket hooks. When a pod sends a packet to a Service IP, eBPF intercepts the socket call *before* it even traverses the TCP/IP stack, looks up the destination Pod IP in an O(1) hash map, and translates it instantly. This drastically reduces CPU overhead, lowers latency, and eliminates iptables rule proliferation.",
     ["Contrasts sequential iptables rule chains (O(N)) vs eBPF hash map lookups (O(1))", "Explains eBPF bypassing the traditional Linux TCP/IP network stack via socket hooks", "Highlights the severe performance and latency degradation of iptables in massive clusters"],
     ["Claims eBPF runs in user-space while iptables runs in kernel-space"]),

    ("B67_2_3", "scenario", "hard", "scenario", ["Cloud Identity", "Security Architecture"],
     "An AWS EC2 instance is compromised via a Server-Side Request Forgery (SSRF) vulnerability. The attacker hits 169.254.169.254 to extract the IAM Role credentials attached to the instance, and then uses those credentials to delete S3 buckets. How does upgrading to IMDSv2 completely neutralize this specific SSRF attack vector at the network level?",
     "IMDSv1 relies on simple HTTP GET requests. If an attacker finds an SSRF vulnerability (e.g., tricking the server into fetching a URL), they simply ask the server to fetch http://169.254.169.254/latest/meta-data/iam/security-credentials/. IMDSv2 neutralizes this by enforcing session-based authentication via a strict PUT request requirement. To get credentials in IMDSv2, the client must first send a PUT request with a specific HTTP header (X-aws-ec2-metadata-token-ttl-seconds) to acquire a session token. Crucially, standard SSRF vulnerabilities typically only allow attackers to control the URL (performing GET requests) but *cannot* inject custom HTTP headers or change the HTTP method to PUT. Because the attacker cannot generate the required PUT request with the custom header via the SSRF, they cannot acquire the token, rendering the metadata service completely inaccessible to them.",
     ["Identifies IMDSv1 vulnerability to simple GET-based SSRF attacks", "Explains IMDSv2 enforcing a mandatory PUT request with custom HTTP headers to acquire a session token", "Explains that standard SSRF vulnerabilities cannot arbitrarily forge HTTP methods or inject custom headers"],
     ["Claims IMDSv2 encrypts the credentials using TLS to stop network sniffing"]),

    ("B67_2_4", "tradeoff", "medium", "tradeoff", ["Service Mesh", "Architecture"],
     "What is the primary operational tradeoff of using a Sidecar-based Service Mesh (like Istio/Linkerd) versus an Ambient/Sidecarless Mesh (like Istio Ambient or Cilium) for a massive cluster with 10,000 pods?",
     "Sidecar Mesh: Injects a proxy (Envoy) into every single pod. Advantages: Perfect per-pod isolation, strict mTLS identity per pod, and no shared proxies. Disadvantages: Massive resource amplification. If Envoy takes 50MB of RAM and 0.1 CPU, injecting it into 10,000 pods wastes 500GB of RAM and 1,000 CPU cores globally. Furthermore, upgrading the mesh requires restarting all 10,000 application pods. Ambient/Sidecarless Mesh: Uses a DaemonSet proxy (ztunnel) per node to handle L4 mTLS, and an optional shared L7 proxy (waypoint) for advanced routing. Advantages: Drastically reduces global RAM/CPU overhead (only 1 proxy per node instead of 100), and upgrading the mesh doesn't require restarting application pods. Disadvantages: Reduced isolation; a compromised node-level proxy could potentially impact all traffic on that node, creating a larger blast radius than isolated sidecars.",
     ["Contrasts the massive global RAM/CPU amplification of sidecars with the efficiency of per-node DaemonSet proxies", "Highlights the operational nightmare of restarting all pods to upgrade a sidecar mesh", "Identifies the tradeoff of reduced security isolation (blast radius) in shared per-node proxies"],
     ["Claims Sidecarless meshes do not support mutual TLS (mTLS)"]),

    ("B67_2_5", "diagnose", "medium", "debugging", ["Cloud Identity", "Security Architecture"],
     "A developer has AdministratorAccess explicitly granted to their AWS IAM User. However, when they attempt to create an EC2 instance in a specific production account, they receive an AccessDenied error. You verify their IAM policy is correct. What organizational security mechanism is overriding their administrator policy, and how is it evaluated?",
     "The developer is being blocked by a Service Control Policy (SCP) attached at the AWS Organization level (to the Root, OU, or specific Account). SCPs act as a maximum permission boundary for an account. AWS IAM evaluation follows a strict intersection model: an action is only allowed if it is explicitly permitted by the IAM Policy *and* not explicitly denied (or omitted) by the SCP. Even if the IAM User has AdministratorAccess (Action: '*'), if the overarching SCP denies EC2 creation (Deny: ec2:RunInstances), the SCP always wins. The developer will receive AccessDenied despite their local admin privileges.",
     ["Identifies Service Control Policies (SCPs) at the AWS Organizations level as the root cause", "Explains the intersection evaluation model where SCPs act as maximum boundary filters", "Clarifies that an explicit Deny in an SCP always overrides an explicit Allow in an IAM policy"],
     ["Claims the AWS account billing limit was reached"]),

    ("B67_2_6", "concept", "easy", "concept", ["Kubernetes Networking", "Security"],
     "In Kubernetes, what is the default behavior of pod-to-pod network traffic across namespaces, and how do you enforce strict isolation between namespaces?",
     "By default, Kubernetes implements a 'Flat Network' architecture. All Pods can freely communicate with all other Pods across the entire cluster, completely ignoring namespaces. A Pod in the dev namespace can directly ping and query a database Pod in the prod namespace. To enforce strict isolation, you must implement NetworkPolicies (and use a CNI that supports them, like Calico or Cilium). A NetworkPolicy acts as an internal cluster firewall. To isolate a namespace, you create a Default Deny NetworkPolicy (podSelector: {} with empty ingress/egress rules) in that namespace, which instantly drops all incoming and outgoing traffic. You then explicitly whitelist specific communication paths using namespaceSelector and podSelector rules.",
     ["Identifies the default 'Flat Network' allowing unrestricted cross-namespace communication", "Prescribes NetworkPolicies (and a supporting CNI) as the mechanism for isolation", "Describes implementing a 'Default Deny' policy followed by explicit whitelisting"],
     ["Claims namespaces are physically isolated networks separated by VLANs"]),

    ("B67_2_7", "implement", "hard", "implement", ["Cloud Identity", "Security Architecture"],
     "You are designing an automated CI/CD pipeline running in GitHub Actions that needs to deploy to AWS. Hardcoding AWS Access Keys in GitHub Secrets is a severe security risk. How do you implement OIDC (OpenID Connect) federation to allow GitHub Actions to securely assume an AWS IAM Role without using any long-lived credentials?",
     "Implementation requires setting up an OIDC trust relationship between AWS and GitHub. 1) In AWS IAM, create an OIDC Identity Provider with the URL https://token.actions.githubusercontent.com. 2) Create an IAM Role for the deployment. Crucially, in the Role's Trust Relationship (AssumeRolePolicyDocument), specify the OIDC provider as the Principal, and add a strict Condition: StringLike: {'token.actions.githubusercontent.com:sub': 'repo:my-org/my-repo:*'}. This mathematically guarantees that ONLY your specific GitHub repository can assume the role. 3) In the GitHub Actions YAML, use the aws-actions/configure-aws-credentials action and provide the Role ARN. GitHub will dynamically request a short-lived JSON Web Token (JWT) from its own OIDC provider, pass it to AWS STS, which validates the cryptographic signature and the repo condition, and returns ephemeral, short-lived AWS session tokens to the pipeline. Zero hardcoded keys.",
     ["Identifies OIDC Federation eliminating long-lived access keys", "Explains establishing the OIDC Provider trust relationship in AWS IAM", "Critically highlights the Condition block to restrict assumption to a specific GitHub repository", "Explains the dynamic STS JWT exchange yielding ephemeral tokens"],
     ["Suggests writing a script to rotate the IAM Access Keys every 24 hours automatically"]),

    ("B67_2_8", "tradeoff", "medium", "tradeoff", ["Kubernetes Networking", "Architecture"],
     "What is the tradeoff of using a NodePort Service versus a LoadBalancer Service in Kubernetes to expose an application to the public internet?",
     "NodePort Service: Kubernetes opens a specific static port (e.g., 30080) on every single worker node's external IP address. Advantages: Costs exactly $0, completely vendor-agnostic, and works on bare-metal. Disadvantages: Severe security risk (exposing node IPs directly to the internet), users must append the clunky port to the URL (http://ip:30080), and if that specific Node crashes, the user's connection fails because there is no external load balancing. LoadBalancer Service: Kubernetes provisions an external, highly available cloud load balancer (e.g., AWS ALB). Advantages: Provides a clean DNS name on port 443/80, seamlessly balances traffic across healthy nodes, automatically handles node failures, and terminates SSL at the edge. Disadvantages: High cloud provider costs (you pay hourly for the LB), and cloud vendor lock-in.",
     ["Contrasts NodePort (exposing static ports on worker IPs) with LoadBalancer (provisioning external cloud LBs)", "Identifies NodePort tradeoff: free/vendor-agnostic vs high security risk and no failover redundancy", "Identifies LoadBalancer tradeoff: high availability/clean URLs vs high cloud costs"],
     ["Claims NodePort is faster because it bypasses Kubernetes entirely"]),

    ("B67_2_9", "scenario", "medium", "scenario", ["Cloud Identity", "Security Architecture"],
     "An application running on an EKS cluster needs to access an S3 bucket. A junior engineer creates an IAM User with long-lived Access Keys and injects them as a Kubernetes Secret into the Pod. Why is this a severe security anti-pattern, and what is the modern AWS architecture (IRSA) to solve this?",
     "Long-lived Access Keys are a severe anti-pattern because they never expire. If the Kubernetes Secret is compromised, accidentally logged, or leaked in a git commit, an attacker gains permanent access to the S3 bucket until the keys are manually rotated. The modern architecture is IRSA (IAM Roles for Service Accounts). Instead of giving keys to the pod, you associate an AWS IAM Role directly with a Kubernetes ServiceAccount. The EKS OIDC provider dynamically mints a short-lived, ephemeral web token for that ServiceAccount. The AWS SDK inside the pod automatically trades this token with AWS STS for temporary credentials. If the pod is compromised, the tokens expire automatically in a few hours, neutralizing long-term threat persistence.",
     ["Identifies long-lived static keys as a permanent compromise risk upon leakage", "Proposes IRSA (IAM Roles for Service Accounts) as the modern declarative solution", "Explains the dynamic OIDC/STS token exchange yielding ephemeral credentials"],
     ["Recommends encrypting the Access Keys using base64 before putting them in the Secret"]),

    ("B67_2_10", "diagnose", "hard", "debugging", ["Kubernetes Networking", "Service Mesh"],
     "You enable strict mTLS (mutual TLS) across your entire Istio service mesh. Suddenly, Kubernetes Liveness and Readiness probes for all your applications begin failing, and the pods are continuously restarted by the kubelet. Internal mesh traffic is fine. Why does strict mTLS break health probes, and how do you resolve it safely?",
     "When strict mTLS is enabled, the Envoy sidecar proxy strictly drops any incoming TCP/HTTP connection that does not present a valid cryptographic client certificate signed by the Istio Citadel CA. The problem is that Kubernetes health probes (Liveness/Readiness) are executed directly by the kubelet process running on the worker node. The kubelet is entirely outside the Istio mesh; it does not possess an Istio client certificate. Therefore, Envoy rejects the kubelet's HTTP GET probe with a connection reset, causing the probe to fail and the pod to restart. To resolve this safely, Istio uses 'Probe Rewrite' by default (or configured explicitly). The mutating webhook alters the pod spec so the kubelet sends the probe to a special, unauthenticated port on the Envoy proxy (e.g., 15020). Envoy receives this unauthenticated request, translates it locally, and forwards it to the application container, satisfying the probe without breaking strict mTLS for actual network traffic.",
     ["Identifies the kubelet process running outside the mesh without an mTLS client certificate", "Explains that strict Envoy sidecars reject unauthenticated kubelet probes, causing restarts", "Prescribes 'Probe Rewrite' targeting Envoy's unauthenticated local pass-through port (15020)"],
     ["Suggests turning off mTLS entirely for the production environment to fix the probes"]),

    ("B67_2_11", "concept", "easy", "concept", ["Cloud Identity", "Security Architecture"],
     "What is a 'Permission Boundary' in AWS IAM, and how does it prevent privilege escalation when you delegate IAM Role creation to a junior developer?",
     "A Permission Boundary is an advanced IAM policy used to set the absolute maximum permissions an identity can have, regardless of the policies attached directly to it. If you allow a junior developer to create new IAM Roles for their CI/CD pipelines, they could maliciously create a role with AdministratorAccess and assume it, escalating their own privileges. To prevent this, you enforce a Permission Boundary. You grant the developer iam:CreateRole, but attach a strict Condition stating they can *only* create roles if they attach a specific Permission Boundary policy (e.g., Boundary: S3ReadAndLambdaOnly). Even if the developer attaches AdministratorAccess to the new role, the boundary mathematically overrides it, restricting the role strictly to S3 and Lambda.",
     ["Defines Permission Boundary as setting the absolute maximum allowable permissions for an entity", "Explains preventing privilege escalation via malicious role creation", "Describes enforcing boundary attachment via IAM Conditions during role creation"],
     ["Claims Permission Boundaries define which geographical AWS regions a user can log into"]),

    ("B67_2_12", "scenario", "medium", "scenario", ["Kubernetes Networking", "Architecture"],
     "You are migrating a high-throughput UDP streaming application (like WebRTC or VoIP) into Kubernetes. You expose it via an Ingress Controller (like Nginx Ingress). Clients immediately report that they cannot connect to the stream at all. Why do standard Ingress Controllers fail with UDP traffic, and what Kubernetes networking resource must you use instead?",
     "Standard Kubernetes Ingress Controllers (like Nginx Ingress or ALB Ingress) are strictly Layer 7 (HTTP/HTTPS) reverse proxies. They are designed to inspect hostnames, URL paths, and terminate SSL. They absolutely cannot route native Layer 4 UDP or raw TCP traffic. When the WebRTC client attempts to send UDP packets to the Ingress, they are immediately dropped. To expose a UDP streaming application, you must bypass the Ingress Controller entirely and use a Layer 4 LoadBalancer Service. By defining type: LoadBalancer and protocol: UDP in the Service manifest, Kubernetes will provision a cloud Network Load Balancer (NLB) that forwards raw UDP packets directly to the worker nodes and into your pods, preserving the necessary network protocols.",
     ["Identifies standard Ingress Controllers as strictly Layer 7 HTTP/HTTPS proxies incapable of UDP routing", "Prescribes bypassing the Ingress and using a Layer 4 LoadBalancer Service", "Specifies protocol: UDP to trigger cloud Network Load Balancers (NLBs)"],
     ["Recommends wrapping the UDP packets in HTTP POST requests to pass through the Ingress"]),

    ("B67_2_13", "implement", "hard", "implement", ["Cloud Identity", "Security Architecture"],
     "In a multi-account AWS environment, you have an 'Identity Account' where users authenticate, and a 'Production Account' holding databases. How do you implement Cross-Account Role Assuming (Role Chaining) to allow a user in the Identity Account to read an S3 bucket in the Production Account, detailing the specific policies required in both accounts?",
     "Cross-Account access requires a two-way handshake involving policies in both accounts. 1) In the Production Account (Target): You create an IAM Role (ProdS3Reader). In its Permissions Policy, you grant s3:GetObject on the specific bucket. Crucially, in its Trust Policy (AssumeRolePolicyDocument), you must explicitly list the ARN of the Identity Account (or specific User/Role in it) as the trusted Principal allowed to assume this role. 2) In the Identity Account (Source): You attach an IAM Policy to the user/group granting them the sts:AssumeRole action, specifying the exact ARN of the ProdS3Reader role in the Production Account. When the user executes the CLI command aws sts assume-role, AWS verifies both sides agree: the source is allowed to assume, and the target trusts the source.",
     ["Details the two-way handshake requirement for cross-account delegation", "Explains the Target Account requirements: IAM Role with a Trust Policy defining the Source Account as Principal", "Explains the Source Account requirements: IAM Policy granting sts:AssumeRole for the Target ARN"],
     ["Suggests copying the Root password of the Production account to the Identity account"]),

    ("B67_2_14", "tradeoff", "medium", "tradeoff", ["Cloud Identity", "Security Architecture"],
     "What are the tradeoffs of using AWS KMS (Key Management Service) with AWS Managed Keys versus Customer Managed Keys (CMKs) for encrypting an S3 bucket?",
     "AWS Managed Keys (aws/s3): Advantages: They are completely free, zero-maintenance, automatically rotated by AWS, and instantly available. Disadvantages: You have absolutely no control over the key policies. If another AWS account needs to read your S3 bucket, it is mathematically impossible to grant them access because you cannot modify the AWS Managed Key policy to allow cross-account decryption. Customer Managed Keys (CMKs): Advantages: Ultimate flexibility. You write the IAM Key Policies, allowing you to explicitly grant cross-account decryption rights, strictly audit every single cryptographic operation in CloudTrail, and enforce manual key rotation or deletion (cryptographic shredding). Disadvantages: You pay a monthly fee per key plus usage costs, and if you accidentally misconfigure the Key Policy or delete the key, your S3 data is permanently and irrecoverably lost.",
     ["Identifies AWS Managed Keys tradeoffs: Free/zero-maintenance vs no cross-account sharing capabilities", "Identifies CMK advantages: strict IAM key policy control, cross-account sharing, and detailed CloudTrail auditing", "Identifies CMK risks: Costs and permanent data loss if the CMK is deleted (crypto-shredding)"],
     ["Claims Customer Managed Keys require shipping physical USB drives to the AWS datacenter"]),

    ("B67_2_15", "diagnose", "medium", "debugging", ["Kubernetes Networking", "Architecture"],
     "A pod running in a Kubernetes cluster makes a DNS query for database.prod.svc.cluster.local. The query fails with a timeout. However, ping 8.8.8.8 works perfectly. You check the CoreDNS pods, and they are running. What underlying network configuration (often related to CNI or iptables) causes internal DNS to fail while external internet access works?",
     "This indicates a failure in the cluster's internal overlay network or Service routing layer. When a pod queries database.prod.svc.cluster.local, it sends a UDP packet to the kube-dns Service IP (e.g., 10.96.0.10). This IP doesn't physically exist; it must be translated by kube-proxy (via iptables/IPVS) or the CNI into the actual IP of a healthy CoreDNS pod. If external internet (8.8.8.8) works, the node's NAT and outbound routing are fine. The internal DNS failure is caused by either: 1) kube-proxy crashed on that specific node, failing to create the iptables NAT rules for the Service IP; 2) The CNI (e.g., Calico/Flannel) overlay tunnels (VXLAN/IPIP) are broken, preventing the packet from reaching the node where CoreDNS lives; or 3) A NetworkPolicy is explicitly blocking port 53 UDP traffic between namespaces.",
     ["Distinguishes between node external outbound NAT routing and internal cluster Service routing", "Diagnoses kube-proxy / iptables rule translation failure for the virtual kube-dns IP", "Identifies broken CNI overlay tunnels or restrictive NetworkPolicies as alternative culprits"],
     ["Suggests the database pod is turned off, causing DNS to fail"]),

    ("B67_2_16", "concept", "easy", "concept", ["Cloud Identity", "Security Architecture"],
     "What is the Principle of Least Privilege (PoLP) in cloud security, and why is the AWS managed policy AmazonS3FullAccess often considered a violation of it for a web server?",
     "The Principle of Least Privilege dictates that an identity (user, server, or application) should only be granted the absolute minimum permissions strictly necessary to perform its specific job, and nothing more. The AmazonS3FullAccess managed policy is a massive violation because it grants s3:* on * (every single S3 bucket in the entire AWS account). If a web server only needs to upload user avatars to an images-bucket, giving it FullAccess allows a compromised web server to delete the company's financial backup buckets, read sensitive HR document buckets, or alter logging buckets. PoLP dictates writing a custom policy granting only s3:PutObject strictly restricted to arn:aws:s3:::images-bucket/*.",
     ["Defines PoLP as granting minimum necessary permissions for a specific function", "Explains that broad managed policies expose excessive attack surface during a compromise", "Recommends custom IAM policies restricted by specific actions and resource ARNs"],
     ["Claims Least Privilege means giving permissions only to the newest employees"]),

    ("B67_2_17", "implement", "hard", "implement", ["Kubernetes Networking", "Service Mesh"],
     "You are migrating a legacy monolithic application to microservices. The frontend code is hardcoded to make API calls to http://legacy-backend:8080/api/v1/users, but you have rewritten the users service into a new Go microservice running at http://users-v2:9000/v1/users. You cannot change the legacy frontend code. How do you use Istio VirtualServices to seamlessly rewrite and reroute this traffic without touching the frontend?",
     "Istio Envoy sidecars intercept all outbound traffic. You can implement this transparently by creating an Istio VirtualService attached to the legacy-backend host. Implementation: 1) Define the VirtualService matching the hosts: ['legacy-backend']. 2) Add an HTTP match block targeting the specific prefix match: [{uri: {prefix: '/api/v1/users'}}]. 3) Define the rewrite block to strip the old prefix and apply the new one: rewrite: {uri: '/v1/users'}. 4) Define the route destination targeting the new microservice: route: [{destination: {host: 'users-v2', port: {number: 9000}}}]. When the legacy frontend blindly calls the old URL, the Envoy proxy instantly intercepts it, rewrites the URL path, changes the port, and routes it to the new Go service, completely abstracting the migration from the legacy codebase.",
     ["Identifies Istio VirtualService rewriting capabilities via Envoy sidecar interception", "Provides exact implementation blocks: hosts match, uri prefix match, rewrite block, and destination route", "Highlights the architectural abstraction allowing zero code changes to legacy clients"],
     ["Recommends editing the /etc/hosts file on the Kubernetes worker nodes"]),

    ("B67_2_18", "scenario", "medium", "scenario", ["Cloud Identity", "Security Architecture"],
     "Your automated infrastructure pipeline requires access to an external third-party API (e.g., Datadog or PagerDuty). You store the API token in AWS Secrets Manager. A Lambda function fetches the secret on every invocation to authenticate. During a severe production incident, the Lambda function scales to 10,000 concurrent executions and suddenly crashes with ThrottlingException on the Secrets Manager API. How do you redesign this architecture to prevent KMS/Secrets Manager throttling during massive scaling events?",
     "AWS Secrets Manager and KMS have hard API rate limits (e.g., 5000 requests per second). When Lambda scales massively, every concurrent sandbox makes an independent synchronous HTTP call to Secrets Manager, instantly exhausting the account's API quota and crashing the system when you need it most. To redesign for resilience: 1) Implement In-Memory Caching within the Lambda function. Fetch the secret once during the Lambda 'INIT' phase (outside the main handler function) and store it in a global variable. Subsequent invocations reusing the same warm Lambda sandbox will read the variable from RAM, making zero API calls to AWS. 2) For more advanced architectures, use the AWS Parameters and Secrets Lambda Extension, which runs a local caching proxy alongside the Lambda execution environment, automatically handling caching, TTL, and backoff retries without writing custom caching code.",
     ["Diagnoses 'Thundering Herd' exhausting hard AWS API rate limits during massive concurrent scaling", "Recommends leveraging the Lambda 'INIT' phase to globally cache the secret in memory for warm re-use", "Recommends the official AWS Parameters and Secrets Lambda Extension proxy"],
     ["Suggests paying AWS a fee to completely disable API rate limits on the account"]),

    ("B67_2_19", "tradeoff", "medium", "tradeoff", ["Kubernetes Networking", "Architecture"],
     "What are the tradeoffs of using a wildcard SSL certificate (*.example.com) terminated at a single Kubernetes Ingress Controller versus using cert-manager to automatically provision and terminate individual Let's Encrypt SSL certificates for every single microservice (e.g., api.example.com, auth.example.com)?",
     "Wildcard Certificate at Ingress: Advantages: Extremely simple to configure. You mount one Secret to the Ingress Controller, and it instantly secures infinite subdomains without relying on external DNS challenges or rate-limits. Disadvantages: Severe security risk. If the Ingress Controller is compromised, the attacker steals the wildcard private key and can impersonate the entire company domain globally. Cert-Manager Individual Certs: Advantages: Strict cryptographic isolation and zero-trust. If auth.example.com's private key is leaked, api.example.com remains perfectly secure. Short-lived Let's Encrypt certs rotate automatically every 60 days, drastically reducing the blast radius of a leak. Disadvantages: High operational complexity. Relies on constant ACME DNS/HTTP01 challenges; if the cert-manager pod crashes or Let's Encrypt rate limits your domain, certificates expire and applications go completely offline.",
     ["Contrasts Wildcard operational simplicity against the catastrophic blast radius of a private key leak", "Contrasts Cert-Manager strict per-domain isolation and short-lived rotation against high operational complexity", "Identifies the risk of automated ACME challenge failures causing mass certificate expiration"],
     ["Claims wildcard certificates are legally prohibited in the European Union"]),

    ("B67_2_20", "diagnose", "medium", "debugging", ["Cloud Identity", "Security Architecture"],
     "A developer deletes an IAM user and immediately creates a new IAM user with the exact same username (jdoe). However, the new jdoe user is denied access to an S3 bucket that explicitly had arn:aws:iam::123:user/jdoe allowed in its Resource Policy. Why does recreating a user with the exact same ARN break permissions, and how does AWS track identity fundamentally?",
     "Recreating a user with the identical username and ARN breaks permissions because AWS IAM does not actually authorize based on the string ARN; it authorizes based on a hidden, immutable Unique ID (e.g., AIDAJQABLZS4A3QDU576Q). When the original jdoe was created, AWS generated a Unique ID and quietly bound it to the S3 bucket policy. When the user was deleted and recreated, the new jdoe received a brand new Unique ID, even though the ARN string looks identical. The S3 bucket policy is now technically orphaned—it is internally tied to the deleted Unique ID. To fix this, you must edit the S3 bucket policy, remove the old ARN, save it, and then add the ARN back. This forces AWS to re-evaluate the string ARN and bind the policy to the *new* Unique ID.",
     ["Explains that AWS IAM fundamentally relies on immutable hidden Unique IDs, not string ARNs", "Diagnoses that deleting and recreating a user creates a new Unique ID, invalidating previous policy bindings", "Prescribes manually removing and re-adding the ARN in the resource policy to force re-evaluation"],
     ["Suggests the new user needs to clear their browser cookies to fix the login permission"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 2).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Cloud Security Engineer", "Site Reliability Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "AWS/Kubernetes",
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
    print("POST-BATCH AUDIT PART 2")
    print("========================================")
    print(f"Batch: 67 Part 2")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
