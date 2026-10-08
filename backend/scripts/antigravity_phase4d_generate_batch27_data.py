"""Batch 27 Part 1 question content (DevOps / Cloud Engineer). Targeted Gap Generation."""

ROLE = "DevOps / Cloud Engineer"

BUCKET_KEYS = {
    "CLOUD_SECURITY": ("Cloud Security", "IAM & Supply Chain", "Cloud", ["DevOps / Cloud Engineer", "Security Engineer", "Site Reliability Engineer"]),
}

Q = [
# ---------------- CLOUD_SECURITY ----------------
("CLOUD_SECURITY", "scenario", "medium", "scenario", ["CI/CD", "Workload Identity"],
 "A CI pipeline deploys infrastructure to AWS using long-lived IAM user credentials stored as GitHub Secrets. What is the fundamental security risk of this architecture, and how should it be modernized?",
 "Long-lived static credentials can be leaked, accidentally committed to logs, or exfiltrated by compromised runners, leading to permanent infrastructure compromise. The architecture must be modernized to use Workload Identity Federation (e.g., OIDC). The CI provider (GitHub Actions) exchanges a cryptographically signed OIDC token for short-lived, temporary cloud credentials, entirely eliminating the need to store static secrets.",
 ["Long-lived credentials are a severe risk for leakage and exfiltration", "Modernize using Workload Identity Federation (OIDC)", "Exchanges short-lived, temporary credentials dynamically, eliminating static secrets"],
 ["The credentials expire every 10 minutes and break the pipeline"]),

("CLOUD_SECURITY", "debug", "hard", "debugging", ["Kubernetes Security", "IAM"],
 "A compromised Kubernetes pod running a basic frontend application suddenly starts terminating EC2 instances in your AWS account. How did a frontend container gain access to the AWS control plane, and how do you prevent this?",
 "The pod was scheduled on an EC2 worker node that had an overly permissive IAM Instance Profile attached. By default, any pod on the node can query the local Instance Metadata Service (IMDS) at `169.254.169.254` to steal the node's underlying IAM credentials. You prevent this by enforcing IMDSv2, blocking the metadata IP via network policies, or exclusively using IAM Roles for Service Accounts (IRSA/Workload Identity) to strictly scope permissions per pod.",
 ["The pod queried the node's Instance Metadata Service (IMDS) to steal the node's IAM credentials", "The node had an overly permissive IAM Instance Profile", "Prevent by blocking IMDS via network policies or using strictly scoped Pod-level IAM (IRSA)"],
 ["The frontend application guessed the AWS root password"]),

("CLOUD_SECURITY", "tradeoff", "medium", "tradeoff", ["Secrets Management"],
 "What is the operational tradeoff between statically baking application secrets (like API keys) into a Docker image during the CI build process versus fetching them dynamically at runtime?",
 "Baking secrets into the image makes deployment trivially simple and avoids runtime dependencies, but it permanently compromises the image; anyone with access to the registry or the container filesystem can extract the plaintext secret. Fetching dynamically at runtime (e.g., via HashiCorp Vault or AWS Secrets Manager) perfectly secures the static image, but adds operational complexity, startup latency, and introduces a critical runtime dependency on the secret manager.",
 ["Baking secrets compromises the image and exposes plaintext to anyone with registry access", "Fetching at runtime perfectly secures the static image", "Runtime tradeoff: Adds operational complexity and a critical runtime dependency on the secret manager"],
 ["Baking secrets makes the Docker image physically heavier to download"]),

("CLOUD_SECURITY", "explain", "easy", "concept", ["IAM"],
 "Explain the Principle of Least Privilege in the context of cloud IAM policies.",
 "Least Privilege mandates that a user, service account, or application should only be granted the absolute minimum permissions strictly necessary to perform its required task. For example, instead of granting broad `s3:*` access to an entire bucket, you explicitly grant only `s3:GetObject` to a highly specific prefix path, minimizing the blast radius if that identity is compromised.",
 ["Grant only the absolute minimum permissions strictly necessary for a task", "Avoid wildcard permissions (e.g., `s3:*`)", "Crucial for minimizing the blast radius of a compromised identity"],
 ["It means executives get fewer privileges than developers"]),

("CLOUD_SECURITY", "scenario", "hard", "scenario", ["Supply Chain Security"],
 "You discover a critical vulnerability in an open-source logging library embedded in your production application. A patch is available, but the library is not a direct dependency in your manifest—it is a transitive dependency brought in by three other packages. How do you secure the supply chain without breaking the build?",
 "You must use your dependency management tool to explicitly override or force the version resolution of the vulnerable transitive dependency (e.g., using Maven `<dependencyManagement>` or npm `overrides`). You then run automated test suites to ensure the forced upgrade doesn't break the intermediate packages' API contracts, and integrate an SCA (Software Composition Analysis) tool into the CI pipeline to block vulnerable transitive dependencies from merging in the future.",
 ["Force version resolution of the transitive dependency using package manager overrides", "Run automated test suites to verify intermediate API contracts are not broken", "Integrate Software Composition Analysis (SCA) into CI to prevent future regressions"],
 ["Delete the transitive dependency manually from the node_modules folder in production"]),

("CLOUD_SECURITY", "tradeoff", "medium", "tradeoff", ["Container Security", "Deployments"],
 "What are the tradeoffs of using a mutable Docker tag (like `latest` or `production`) versus an immutable tag (like the Git commit SHA) when deploying to Kubernetes?",
 "Mutable tags are easier for humans to read, but they completely destroy deployment idempotency. If a pod crashes and Kubernetes pulls `latest`, it might pull a completely different underlying image than what was originally deployed, causing unpredictable production state. Immutable tags (like a commit SHA or image digest) guarantee exact deployment reproducibility, making rollbacks, scaling, and security auditing mathematically precise.",
 ["Mutable tags destroy idempotency; scaling or crashing pods might pull a different underlying image", "Immutable tags (Git SHA/Digest) guarantee exact deployment reproducibility", "Immutable tags make rollbacks, scaling, and auditing mathematically precise"],
 ["Mutable tags mutate into viruses over time"]),

("CLOUD_SECURITY", "implement", "hard", "implementation", ["Kubernetes Security"],
 "A developer wants to run a container as `root` in a Kubernetes cluster because a legacy binary requires it. Security policy forbids `root` execution. How do you architecturally enforce this policy across the entire cluster so that no developer can deploy such a pod, even accidentally?",
 "You must implement a Kubernetes Admission Controller (like OPA Gatekeeper or Kyverno) or use Pod Security Admission (PSA). You configure an admission policy that intercepts the API request and mathematically rejects any Pod manifest that does not explicitly set `securityContext.runAsNonRoot: true`. This enforces the security boundary fundamentally at the cluster API level, entirely bypassing developer intent.",
 ["Implement an Admission Controller (OPA Gatekeeper, Kyverno) or Pod Security Admission (PSA)", "Intercept the Kubernetes API request during pod creation", "Mathematically reject manifests lacking `securityContext.runAsNonRoot: true`"],
 ["Send an automated strongly worded email to the developer"]),

("CLOUD_SECURITY", "explain", "medium", "concept", ["Supply Chain Security"],
 "What is a Software Bill of Materials (SBOM), and why is it becoming a critical component of secure CI/CD pipelines?",
 "An SBOM is a comprehensive, machine-readable inventory of every single open-source and commercial software component, library, and transitive dependency used to build an application or container image. It is critical because if a zero-day vulnerability (like Log4Shell) is announced, an organization can instantly query their SBOMs to identify exactly which applications and images are vulnerable, rather than manually scanning thousands of code repositories.",
 ["A machine-readable inventory of all components, libraries, and transitive dependencies in an artifact", "Critical for rapid vulnerability response (e.g., zero-day exploits)", "Allows organizations to instantly identify vulnerable applications without manual scanning"],
 ["It is an invoice sent to open-source maintainers"]),

("CLOUD_SECURITY", "scenario", "medium", "scenario", ["Container Security", "CI/CD"],
 "During an audit, you realize developers are pushing Docker images to a public registry containing plaintext `npm_auth_token` environment variables. They claim they need the token inside the `Dockerfile` to install private packages. How do you rewrite the CI pipeline to securely build the image without leaking the token?",
 "You must use Docker BuildKit's `--secret` feature or multi-stage builds. By passing the token as a BuildKit secret, it is temporarily mounted in memory strictly during the `RUN npm install` layer. It is never permanently written to the container's filesystem or intermediate image layers, preventing it from being leaked in the final registry push.",
 ["Use Docker BuildKit's `--secret` feature", "The secret is temporarily mounted in memory during the build layer", "It is never permanently written to the filesystem or intermediate image layers"],
 ["Tell them to type the password really fast during the build"]),

("CLOUD_SECURITY", "debug", "hard", "debugging", ["Terraform", "IAM"],
 "You use Terraform to manage IAM roles. A junior engineer manually attaches an `AdministratorAccess` policy to a role directly in the AWS Console to quickly debug an issue. The next time the CI/CD pipeline runs `terraform apply`, it reports 'No changes'. Why did Terraform fail to detect and remove the unauthorized policy?",
 "Terraform only tracks and manages resources explicitly defined in its state. Because the manual policy attachment was created entirely outside of Terraform, and the Terraform code likely manages inline policies or specific individual attachments rather than exclusively managing the *entire* role attachments (e.g., via `aws_iam_role_policy_attachment`), Terraform simply ignores the manual drift. You must use exclusive management resources or implement drift-detection tooling.",
 ["Terraform only tracks resources explicitly defined in its state", "The code was not configured to exclusively manage all attachments on the role", "Terraform ignores out-of-band manual drift unless explicitly told to manage the entire resource state"],
 ["Terraform was intimidated by the AdministratorAccess policy"]),

("CLOUD_SECURITY", "implement", "medium", "implementation", ["IAM Architecture"],
 "You need to grant a third-party SaaS vendor temporary read access to an S3 bucket in your AWS account. Why should you use cross-account IAM roles with an External ID instead of creating an IAM User and sending them the Access Keys?",
 "Creating an IAM User with static Access Keys requires transmitting and storing permanent secrets, which can be leaked or stolen. Using a cross-account IAM Role allows the vendor to assume the role dynamically using STS. The `External ID` is a critical security condition that prevents the 'Confused Deputy' attack by cryptographically proving that the vendor is legitimately acting on behalf of your specific SaaS tenant account.",
 ["Static Access Keys are permanent secrets that can be leaked", "Cross-account roles allow dynamic, short-lived STS credential assumption", "The `External ID` prevents the 'Confused Deputy' attack by verifying the tenant context"],
 ["SaaS vendors are notorious for losing USB drives"]),

("CLOUD_SECURITY", "fundamentals", "easy", "concept", ["IaC"],
 "What is 'Infrastructure as Code' (IaC) drift, and why is it a severe security concern?",
 "Drift occurs when the actual physical state of cloud resources deviates from the declarative state defined in the source-controlled IaC templates (like Terraform or CloudFormation), usually due to manual console changes. It is a severe security concern because a manual change might accidentally open a firewall port to the internet or grant excessive IAM permissions, completely bypassing mandatory code review and automated CI/CD security scanning.",
 ["Occurs when the actual cloud state deviates from the source-controlled IaC state", "Usually caused by manual, out-of-band console changes", "A security concern because it bypasses code review and automated security scanning (e.g., opening a firewall)"],
 ["It is when servers physically slide off their racks in the data center"]),

("CLOUD_SECURITY", "tradeoff", "hard", "tradeoff", ["Service Mesh", "Zero Trust"],
 "In a zero-trust architecture, what is the tradeoff between authenticating microservices using mutual TLS (mTLS) managed by a Service Mesh versus passing signed JWT tokens in the HTTP headers?",
 "mTLS handled by a Service Mesh (like Istio) is completely transparent to the application code, encrypts traffic in transit, and strictly verifies the network identity of the calling pod. However, it requires complex infrastructure sidecars. JWTs require application-level code to generate, sign, and validate tokens, but they allow fine-grained, user-context authorization (e.g., passing the end-user's identity/roles through the microservice chain), which mTLS alone cannot do.",
 ["mTLS (Service Mesh): Transparent to app code, strictly verifies network identity, but requires complex sidecar infrastructure", "JWTs: Require app-level code for validation", "JWT tradeoff: Allows fine-grained, end-user context authorization across the call chain"],
 ["mTLS requires a physical handshake between servers"]),

("CLOUD_SECURITY", "scenario", "medium", "scenario", ["IAM", "MFA"],
 "An attacker gains access to a developer's laptop and steals their cloud credentials. To mitigate this risk, you enforce MFA (Multi-Factor Authentication) for all CLI access. How does a developer actually use the AWS/GCP CLI when MFA is strictly enforced on the IAM policy?",
 "The developer cannot use their static keys directly. They must use the CLI to execute a specific STS (Security Token Service) command, providing their MFA device ARN and the current 6-digit token. The cloud provider responds with a set of temporary, short-lived session credentials that include an `aws:MultiFactorAuthPresent: true` context flag. The developer exports these temporary credentials to their shell to execute further commands.",
 ["Static keys cannot be used directly for protected API calls", "The developer uses STS to exchange their 6-digit MFA token for temporary session credentials", "The temporary credentials contain an MFA-authenticated context flag to satisfy the policy"],
 ["They hold their phone up to the webcam while typing commands"]),

("CLOUD_SECURITY", "explain", "medium", "concept", ["DevSecOps"],
 "What is the operational concept of 'Shift Left' in a DevSecOps pipeline?",
 "Shift Left means integrating security checks, vulnerability scanning, static code analysis (SAST), and dependency scanning as early as possible in the Software Development Life Cycle (SDLC)—typically during the developer's local commit or the very first CI build step. This sharply contrasts with waiting to run security scans just before production deployment, catching vulnerabilities when they are significantly cheaper, faster, and easier to fix.",
 ["Integrating security checks and scans as early as possible in the SDLC (e.g., local commit or early CI)", "Avoids waiting until the end of the pipeline or production deployment to find flaws", "Catches vulnerabilities when they are cheapest and fastest for developers to fix"],
 ["It refers to physically moving security servers to the left side of the rack"]),

("CLOUD_SECURITY", "debug", "hard", "debugging", ["Container Security"],
 "Your CI pipeline builds a container image and pushes it to a registry. However, the automated vulnerability scanner consistently flags the image as having 50 critical OS-level CVEs, even though the application is a simple static Go binary. Why is this happening, and how do you achieve a zero-CVE image?",
 "The Dockerfile is using a massive, general-purpose base image (like `ubuntu:latest` or `node:latest`) which contains hundreds of unnecessary OS utilities, package managers, and libraries that are constantly vulnerable. Because Go compiles to a self-contained static binary, you should change the base image to `scratch` (an entirely empty image) or `distroless`. This completely removes the OS attack surface, immediately dropping the CVE count to zero.",
 ["The base image (e.g., Ubuntu) contains unnecessary OS utilities and libraries prone to vulnerabilities", "Because Go compiles to a static binary, the OS utilities are entirely unused", "Fix: Change the base image to `scratch` or `distroless` to remove the OS attack surface entirely"],
 ["The Go compiler intentionally injected 50 viruses into the binary"]),

("CLOUD_SECURITY", "implement", "medium", "implementation", ["Image Provenance"],
 "How do you mathematically guarantee that the exact container image compiled in your secure CI pipeline is the exact same image deployed to the Kubernetes production cluster, preventing a malicious actor from tampering with the image in the registry?",
 "You must use cryptographic Image Signing (e.g., using Sigstore Cosign). The CI pipeline mathematically signs the image digest using a private key and pushes the signature to the registry. You then configure a Kubernetes Admission Controller to intercept all pod creation requests, fetch the signature, and verify it against your public key. If the signature is invalid or missing, Kubernetes outright rejects the deployment.",
 ["Use cryptographic Image Signing (e.g., Sigstore Cosign) in the CI pipeline", "The pipeline signs the image digest and publishes the signature", "A Kubernetes Admission Controller verifies the signature before allowing the pod to deploy"],
 ["Have a security guard visually inspect the code before it deploys"])
]
