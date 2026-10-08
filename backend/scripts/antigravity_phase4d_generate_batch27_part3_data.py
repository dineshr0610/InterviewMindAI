"""Batch 27 Part 3 question content (DevOps / Cloud Engineer). Targeted Gap Generation."""

ROLE = "DevOps / Cloud Engineer"

BUCKET_KEYS = {
    "CICD_ARCHITECTURE": ("CI/CD Architecture", "Deployment Strategies", "Cloud", ["DevOps / Cloud Engineer", "Platform Engineer", "Software Engineer"]),
}

Q = [
# ---------------- CICD_ARCHITECTURE ----------------
("CICD_ARCHITECTURE", "scenario", "medium", "scenario", ["GitOps"],
 "You implement a strict GitOps deployment strategy (e.g., using ArgoCD or Flux). A developer has an urgent production incident, so they use `kubectl edit deployment` to quickly fix an environment variable, resolving the incident. Five minutes later, the incident immediately reoccurs. Why?",
 "In a strict GitOps model, the Git repository is the absolute, declarative single source of truth. The GitOps controller constantly polls the repository and compares it to the live cluster state. When the developer made a manual `kubectl` change, the controller detected 'drift' from Git and automatically reverted the manual change back to the broken state defined in the repository. The fix must be committed to Git.",
 ["GitOps controllers constantly poll the Git repository as the single source of truth", "The controller detected manual 'drift' and automatically reverted the `kubectl` change", "The fix must be committed to the Git repository to be permanently applied"],
 ["Kubernetes automatically reverts all manual changes after 5 minutes by default"]),

("CICD_ARCHITECTURE", "debug", "hard", "debugging", ["Rolling Updates", "Databases"],
 "Your CI/CD pipeline deploys a new version of a microservice using a 'Rolling Update' strategy. The deployment reports 'Successful'. However, customers randomly experience HTTP 500 errors. You check the logs and see the new pods throwing database schema errors, while old pods are fine. What coordination failure occurred?",
 "The pipeline executed a Rolling Update while simultaneously applying a non-backward-compatible database schema migration. During a rolling update, Version 1 and Version 2 of the application run concurrently for a brief window. The schema migration broke the API contract for either the old or new pods. Schema migrations must be deployed separately and designed to be strictly backward-compatible with both versions.",
 ["Version 1 and Version 2 pods run concurrently during a Rolling Update", "A non-backward-compatible database schema migration broke the API contract for one of the versions", "Schema migrations must be backward-compatible and deployed separately from the rolling app update"],
 ["The rolling update accidentally rolled the database server across the floor"]),

("CICD_ARCHITECTURE", "tradeoff", "medium", "tradeoff", ["Deployment Strategies"],
 "What are the operational tradeoffs of using a Blue-Green deployment strategy versus a Canary deployment strategy?",
 "Blue-Green requires exactly 2x the infrastructure capacity to stand up a full duplicate environment, and the traffic cutover is immediate (100% switch)—meaning if a bug is introduced, 100% of users are impacted until the instant rollback. Canary requires no extra infrastructure and slowly routes a tiny percentage of traffic (e.g., 5%) to the new version, vastly limiting the blast radius of a bad release, but requires highly sophisticated traffic routing and observability to evaluate health.",
 ["Blue-Green: Requires 2x infrastructure; instant 100% cutover means 100% blast radius if buggy", "Canary: Limits blast radius by routing only a small percentage of traffic (e.g., 5%)", "Canary tradeoff: Requires sophisticated traffic routing and deep observability to evaluate health"],
 ["Blue-Green uses UDP, Canary uses TCP"]),

("CICD_ARCHITECTURE", "explain", "easy", "concept", ["Progressive Delivery"],
 "What is the concept of 'Progressive Delivery' in CI/CD pipeline architecture?",
 "Progressive Delivery is an advanced deployment pattern that encompasses Canary deployments and Feature Flags. Instead of a single 'big bang' release, features are slowly rolled out to a tightly controlled, gradually increasing segment of users (e.g., internal team -> 1% of users -> 10% -> 100%). If error rates spike at any stage, the system automatically halts the rollout and rolls back.",
 ["An advanced pattern encompassing Canary deployments and Feature Flags", "Avoids 'big bang' releases by rolling out features to a gradually increasing user segment", "Automatically halts and rolls back if error metrics spike during the progressive rollout"],
 ["It means developers must type code progressively faster over time"]),

("CICD_ARCHITECTURE", "scenario", "hard", "scenario", ["GitOps", "Containers"],
 "A critical bug is discovered. The team initiates an automated GitOps rollback by using `git revert` on the last commit. The CI pipeline runs, the GitOps controller syncs, but the application remains completely broken. You inspect the cluster and find the Kubernetes pods are still running the broken Docker image. Why didn't the GitOps rollback work?",
 "The team was likely using a mutable Docker tag like `latest` or `production`. The `git revert` successfully rolled back the Kubernetes manifest YAML in Git, but the manifest still pointed to `image:latest`. The cluster saw no change in the literal tag string, so it didn't trigger a pull of the older image. GitOps strictly requires immutable tags (like the Git commit SHA) so a revert actually changes the manifest string.",
 ["The team used a mutable Docker tag (e.g., `latest`)", "The revert didn't change the tag string in the manifest, so Kubernetes didn't pull a new image", "GitOps requires immutable tags (Git SHA/Digest) to force Kubernetes to trigger an update"],
 ["Git reverts are physically blocked by the Kubernetes firewall"]),

("CICD_ARCHITECTURE", "fundamentals", "medium", "concept", ["CI/CD Concepts"],
 "In the context of pipeline architecture, what is the exact difference between Continuous Delivery (CD) and Continuous Deployment (CD)?",
 "Continuous Delivery means the artifact is automatically built, tested, and staged, mathematically proving it is ready to be deployed to production at any moment, but it strictly requires a human to press the 'Deploy' button. Continuous Deployment takes it a step further: every single commit that passes automated tests is automatically pushed into the production environment with absolutely zero human intervention.",
 ["Continuous Delivery: Artifact is ready for production, but requires manual human approval to deploy", "Continuous Deployment: Every passing commit is automatically deployed to production", "Continuous Deployment has absolutely zero human intervention"],
 ["Continuous Delivery uses FedEx; Continuous Deployment uses UPS"]),

("CICD_ARCHITECTURE", "implement", "hard", "implementation", ["Supply Chain Security", "SLSA"],
 "You are designing a CI/CD pipeline for a regulated financial application. You must cryptographically guarantee that the code approved in a GitHub Pull Request is exactly what was deployed to production, preventing an attacker from injecting code during the CI build phase. How do you architect this Software Supply Chain Provenance?",
 "You implement SLSA (Supply-chain Levels for Software Artifacts) framework concepts. The CI runner must generate a cryptographically signed provenance attestation (a non-forgeable receipt) detailing exactly what source repo, commit SHA, and build steps were used to create the artifact. Before deployment, a policy engine (like OPA or Sigstore) verifies this attestation to ensure the artifact wasn't tampered with post-code-review.",
 ["Implement SLSA (Supply-chain Levels for Software Artifacts) concepts", "Generate a cryptographically signed provenance attestation linking the artifact to the commit SHA", "Use a policy engine (OPA/Sigstore) to verify the attestation before allowing deployment"],
 ["Print the code on physical paper and lock it in a safe"]),

("CICD_ARCHITECTURE", "debug", "medium", "debugging", ["Terraform", "State Locks"],
 "Your team uses Terraform to deploy infrastructure via a CI pipeline. The pipeline fails during the `terraform plan` phase with a 'State lock error'. The previous pipeline run was abruptly cancelled by a developer. How do you resolve this, and what is the underlying mechanism?",
 "Terraform uses state locking (typically via a DynamoDB table in AWS) to prevent concurrent pipelines from corrupting the state file simultaneously. Because the previous run was forcefully killed, it never gracefully released the remote lock. You must manually force-unlock the state using the `terraform force-unlock <LOCK_ID>` command after verifying no other processes are actually running.",
 ["Terraform uses state locking (e.g., DynamoDB) to prevent concurrent corruption", "Forcefully killed pipelines fail to release the remote lock", "Fix: Verify no other processes are running, then use `terraform force-unlock <LOCK_ID>`"],
 ["Terraform locks the state with a physical padlock on the server rack"]),

("CICD_ARCHITECTURE", "tradeoff", "hard", "tradeoff", ["Helm", "Manifests"],
 "What is the architectural tradeoff of managing Kubernetes infrastructure by writing raw YAML manifests versus using a package manager like Helm?",
 "Raw YAML is simple, explicit, and easy to audit, but lacks abstraction; deploying across multiple environments (Dev/Prod) requires massive copy-pasting or complex Kustomize scripts. Helm provides powerful Go-templating, versioned releases, and unified lifecycle management (install/upgrade/rollback), but introduces significant abstraction complexity, a steep learning curve, and the severe risk of un-renderable templates failing silently during deployment.",
 ["Raw YAML: Simple and explicit, but lacks abstraction for multi-environment deployments", "Helm: Powerful templating and unified lifecycle management", "Helm tradeoff: Introduces significant abstraction complexity and risk of un-renderable templates"],
 ["Helm requires a steering wheel to operate the cluster"]),

("CICD_ARCHITECTURE", "scenario", "medium", "scenario", ["Canary Deployments"],
 "You are designing a Canary deployment pipeline. The pipeline routes 5% of traffic to the new version for 10 minutes. At the end of 10 minutes, the pipeline automatically promotes it to 100%. However, 30 minutes later, users report massive latency, and you have to manually roll back. What critical component was missing from your Canary automation?",
 "The Canary pipeline lacked Automated Health Validation (or metric-driven promotion). Simply waiting 10 minutes is useless. The pipeline must actively query the observability platform (e.g., Prometheus/Datadog) for key SLIs (HTTP 500s, latency, CPU) during the 5% phase. If the metrics exceed the baseline threshold, the pipeline should automatically abort and roll back before ever reaching 100%.",
 ["Lacked Automated Health Validation (metric-driven promotion)", "The pipeline must actively query SLIs (latency, errors) during the 5% phase", "If metrics degrade, it must automatically abort and roll back instead of blindly promoting"],
 ["The pipeline forgot to feed the canary bird"]),

("CICD_ARCHITECTURE", "explain", "easy", "concept", ["Feature Flags"],
 "What is the primary purpose of 'Feature Flags' (or Feature Toggles) in modern software delivery?",
 "Feature Flags decouple code deployment from feature release. They allow teams to safely merge and deploy incomplete or risky code into production by wrapping it in a conditional flag. The feature remains entirely dormant until the product team dynamically flips the flag in a management dashboard, enabling the feature for specific users without requiring a new CI/CD pipeline run.",
 ["Decouples code deployment from feature release", "Allows safely merging/deploying dormant code to production", "Features are enabled dynamically via a dashboard without requiring a new CI pipeline run"],
 ["Feature flags are physical flags hung outside the data center when a feature launches"]),

("CICD_ARCHITECTURE", "implement", "medium", "implementation", ["Pipeline Architecture"],
 "You manage 50 distinct microservices, each with their own CI/CD pipeline. Currently, every repository contains a massive, duplicated `.gitlab-ci.yml` or GitHub Actions workflow file. When a security update is required for the pipeline, it takes weeks to update all 50 repos. How do you redesign this CI architecture?",
 "You must implement Centralized Pipeline Templates (or Reusable Workflows). You extract the core build, test, and deploy logic into a single, centralized, version-controlled repository. The 50 microservices then simply 'include' or 'call' this central template, passing in necessary variables. A single security update to the central template instantly propagates to all 50 microservices.",
 ["Implement Centralized Pipeline Templates (Reusable Workflows)", "Extract core pipeline logic into a single version-controlled repository", "Microservices 'include' the template; updates propagate instantly to all 50 repos"],
 ["Hire 50 interns to manually copy-paste the updates every day"]),

("CICD_ARCHITECTURE", "tradeoff", "medium", "tradeoff", ["Blue-Green", "Databases"],
 "When architecting a deployment strategy for a stateful database cluster, why is a Blue-Green deployment generally considered an anti-pattern?",
 "Blue-Green relies on instantaneous traffic cutover between two completely isolated environments. For stateful databases, this means you must maintain complex bi-directional synchronization between the Blue DB and the Green DB during the entire transition window to prevent data loss. The extreme operational complexity of resolving write conflicts and preventing split-brain during this sync makes Blue-Green incredibly dangerous for databases.",
 ["Blue-Green relies on isolated environments and instant traffic cutovers", "Stateful databases would require complex bi-directional synchronization to prevent data loss", "Resolving write conflicts and split-brain makes this extremely dangerous for stateful systems"],
 ["Blue and Green are reserved colors for stateless web servers only"]),

("CICD_ARCHITECTURE", "scenario", "hard", "scenario", ["Kubernetes", "Probes"],
 "A developer pushes a commit that breaks the application startup sequence. The CI pipeline compiles the code, passes unit tests, builds the image, and executes the Kubernetes deployment. However, the deployment hangs indefinitely and never completes. What Kubernetes deployment mechanism caught this failure and prevented a production outage?",
 "Kubernetes Readiness Probes caught the failure. When the new pods attempted to start, the startup sequence crashed or hung. The Readiness Probe continuously failed, so Kubernetes refused to mark the new pods as 'Ready' and refused to route traffic to them. Because the deployment strategy (RollingUpdate) requires a minimum number of healthy new pods before terminating old pods, the rollout correctly paused indefinitely, keeping the old version running.",
 ["Kubernetes Readiness Probes caught the startup failure", "The pods were never marked 'Ready', so no traffic was routed to them", "The RollingUpdate strategy paused indefinitely waiting for healthy pods, keeping the old version alive"],
 ["The Kubernetes CEO personally paused the deployment"]),

("CICD_ARCHITECTURE", "debug", "medium", "debugging", ["Testing"],
 "Your CI/CD pipeline automatically runs end-to-end (E2E) integration tests before promoting to production. Lately, the pipeline fails 30% of the time, but if you simply click 'Retry', it passes. The team is starting to ignore the test failures. What is this phenomenon called, and why is it fatal to CI/CD?",
 "This is called 'Flaky Tests'. It is fatal because it completely destroys developer trust in the CI/CD pipeline. If tests fail randomly due to network timeouts, race conditions, or bad test data, developers will eventually assume *every* failure is a flake and blindly hit retry, eventually pushing genuinely broken code to production. Flaky tests must be immediately quarantined or deleted until permanently fixed.",
 ["Known as 'Flaky Tests' (failing randomly without code changes)", "Destroys developer trust in the pipeline's validity", "Developers will blindly click retry on real failures, pushing broken code to production"],
 ["It is a feature to ensure developers are paying attention"]),

("CICD_ARCHITECTURE", "fundamentals", "easy", "concept", ["Testing Methodologies"],
 "What does 'Shift Right' mean in the context of DevOps testing and observability?",
 "While 'Shift Left' means testing early in the CI pipeline, 'Shift Right' acknowledges that you cannot perfectly replicate production scale in a staging environment. It means implementing safe, controlled testing practices directly in the production environment, such as Canary releases, Chaos Engineering, Dark Launching, and utilizing deep observability to monitor and validate the actual real-world behavior of the system.",
 ["Acknowledges that staging environments cannot perfectly replicate production", "Implementing safe testing practices directly in production (Canary, Chaos Engineering)", "Relies heavily on deep observability to validate real-world system behavior"],
 ["It means moving the testing servers to the right side of the office"])
]
