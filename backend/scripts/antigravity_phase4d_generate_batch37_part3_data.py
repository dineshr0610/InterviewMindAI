import os

ROLE = "DevOps / Cloud Engineer"

# Bucket Keys mapping: bucket_id -> (primary_skill, topic, technology, applicable_roles)
BUCKET_KEYS = {
    "b7": ("Containers & OS", "Docker & Linux", "Linux", ["DevOps / Cloud Engineer"]),
    "b8": ("Kubernetes", "Container Orchestration", "Kubernetes", ["DevOps / Cloud Engineer"]),
    "b9": ("CI/CD", "Pipelines & Deployments", "CI/CD", ["DevOps / Cloud Engineer", "Full Stack Developer"]),
}

# Questions list: (bucket, intent, difficulty, question_type, secondary_skills, question, expected_answer, strong_rubric, weak_rubric)
Q = [
    (
        "b7",
        "tradeoff",
        "medium",
        "tradeoff",
        ["Containers & OS", "Networking"],
        "When evaluating high-performance network filtering and tracing in Linux, what operational advantages does eBPF offer over traditional iptables and connection tracking?",
        "Traditional Linux `iptables` uses sequential rule evaluation inside the kernel network stack (Netfilter). In high-density container environments running thousands of pods and microservices, iptables rule sets grow to tens of thousands of entries; every network packet must traverse these rules sequentially (O(N) lookup complexity), incurring severe CPU overhead and packet latency. Furthermore, the Linux connection tracking (`conntrack`) table frequently exhausts its maximum entries under high connection turnover, dropping packets. eBPF (Extended Berkeley Packet Filter) bypasses sequential Netfilter evaluation by executing sandboxed, JIT-compiled bytecode directly at the network driver (XDP) or socket layers (`tc`/`sockops`). eBPF uses O(1) hash tables (BFP maps) for routing and service lookup, dramatically lowering packet processing latency, enabling bypass of the host TCP/IP stack for container-to-container traffic, and providing real-time, non-invasive kernel observability without modifying application code.",
        [
            "Contrasts the O(N) sequential rule traversal of iptables with the O(1) hash table lookups of eBPF (e.g., Cilium).",
            "Explains the performance benefits of eBPF including conntrack bypass, XDP early packet processing, and non-invasive kernel observability."
        ],
        [
            "Claims that iptables and eBPF have identical performance characteristics in large clusters.",
            "Asserts that eBPF requires recompiling the Linux kernel every time a rule changes."
        ]
    ),
    (
        "b7",
        "diagnose",
        "medium",
        "problem_solving",
        ["Containers & OS", "Linux Core"],
        "A container running inside a Kubernetes pod begins accumulating zombie processes (`defunct`), eventually exhausting the node's process table. What Linux kernel mechanism causes this, and how do you resolve it?",
        "In Linux, when a child process exits, its termination status must be read by its parent process using the `wait()` or `waitpid()` system call. Until the parent reads this status, the terminated process remains in the process table as a zombie (`defunct`). If the parent process crashes or is poorly programmed, the orphaned zombie is reparented to PID 1. In standard Linux systems, `systemd` or `init` at PID 1 continuously reaps terminated children. However, in container environments, the containerized application (such as Node.js or Java) often runs as PID 1. Most application runtimes lack the signal handling logic to trap `SIGCHLD` and reap orphaned child processes, causing defunct processes to accumulate indefinitely and exhaust the host PID limit (`/proc/sys/kernel/pid_max`). To resolve this: 1) Run an init process like `tini` or `dumb-init` as the container entrypoint to manage signal forwarding and child reaping; 2) In Kubernetes 1.16+, enable `shareProcessNamespace: true` in the pod spec, allowing an init container or the pause container (PID 1) to reap processes across the pod.",
        [
            "Explains the role of PID 1 in the Linux process lifecycle regarding `SIGCHLD` signal handling and zombie reaping.",
            "Recommends using container init systems (such as `tini` or `dumb-init`) or Kubernetes `shareProcessNamespace` to properly reap defunct processes."
        ],
        [
            "Claims zombie processes consume large amounts of CPU and RAM directly.",
            "Suggests running `kill -9` against the zombie processes, unaware that defunct processes cannot be killed with signals."
        ]
    ),
    (
        "b7",
        "debug",
        "hard",
        "debugging",
        ["Containers & OS", "Networking"],
        "When troubleshooting network connectivity between two Docker containers on the same Linux host, how do you trace packet flow through Linux network namespaces and virtual ethernet (`veth`) pairs?",
        "When Docker creates a container, it provisions an isolated network namespace (`netns`) and a virtual ethernet (`veth`) pair. One end of the pair (`eth0`) resides inside the container's network namespace, while the peer end (`vethxxxx`) resides in the host root namespace and connects to a Linux bridge (`docker0`). To trace packet flow systematically: 1) Identify the container's PID via `docker inspect --format '{{.State.Pid}}' <container_id>`; 2) Enter the container's network namespace using `nsenter -t <PID> -n ip addr` or link the namespace to `/var/run/netns` to use `ip netns exec`; 3) Verify routing inside the container (`ip route`) to ensure traffic targets `docker0` as the default gateway; 4) Check the host bridge using `brctl show` or `bridge link` to verify the peer `veth` interface is attached to `docker0` and in the `forwarding` state; 5) Inspect host iptables rules (`iptables -t filter -L FORWARD -n -v`) to verify that the `DOCKER-USER` or `FORWARD` chains are not dropping inter-container bridge traffic; 6) Use `tcpdump -i docker0` and `tcpdump -i <veth_id>` to identify exactly where packets are dropped.",
        [
            "Details the network topology: container `eth0`, peer `veth` pair on host, and the `docker0` software bridge.",
            "Demonstrates practical debugging commands using `nsenter`, `bridge link`, `iptables -L FORWARD`, and `tcpdump` across namespaces."
        ],
        [
            "Claims all containers share the host root network namespace by default without veth pairs.",
            "Suggests restarting the Docker daemon without inspecting namespace routing or iptables packet drop counters."
        ]
    ),
    (
        "b7",
        "diagnose",
        "hard",
        "problem_solving",
        ["Containers & OS", "Reliability Engineering"],
        "A database server running in a container experiences sudden throughput drops accompanied by high Linux `iowait`, but disk utilization (`%util`) appears below 50%. How do you diagnose whether the bottleneck is storage queue saturation or synchronous write stalls?",
        "High `%iowait` indicates that CPU cores are idling because one or more runnable processes are blocked waiting for outstanding I/O requests to complete. However, low `%util` indicates that the disk controller is not continuously busy, which often obscures the root problem. To diagnose: 1) Run `vmstat 1` to inspect the `b` column (processes blocked on uninterruptible sleep `D` state) and `wa` (`iowait`); 2) Run `iostat -xz 1` to inspect average queue size (`aqu-sz`) and await latency (`r_await` and `w_await`). If `w_await` is high (e.g., > 20ms) while `%util` is low, the workload is performing synchronous, un-pipelined single-threaded disk writes (such as database write-ahead log `fsync` calls) where the disk waits on rotational/commit latency for each block before accepting the next; 3) Use `pidstat -d 1` to isolate the exact process PID responsible for the I/O operations; 4) Use `blktrace` or `perf` to trace disk queue dispatch latency (`D2C` time). If queue depth is low but await is high, the storage subsystem's IOPS or latency SLA (e.g., EBS gp3 IOPS/burst limits) is saturated by serialized `fsync` operations.",
        [
            "Explains how synchronous writes (e.g., database `fsync`/WAL flushes) produce high `iowait` and high `await` with low overall `%util`.",
            "Outlines diagnostic metrics including `vmstat` blocked process queue (`b`), `iostat` await and queue size (`aqu-sz`), and `pidstat -d` process tracking."
        ],
        [
            "Claims that high `iowait` is always caused by high CPU consumption in user space.",
            "Suggests adding more CPU cores without investigating storage latency or synchronous write patterns."
        ]
    ),
    (
        "b8",
        "scenario",
        "easy",
        "scenario",
        ["Kubernetes", "Cloud Architecture"],
        "In a Kubernetes cluster distributed across multiple availability zones, pods are unevenly scheduled, with some AZs holding 80% of replicas. How do Topology Spread Constraints (`topologySpreadConstraints`) ensure high availability across failure domains?",
        "By default, the Kubernetes kube-scheduler does not guarantee uniform pod distribution across geographic availability zones, particularly after node scaling events or spot instance terminations. While Pod Anti-Affinity can spread pods, hard anti-affinity rejects pod scheduling if nodes are full, while soft anti-affinity is only best-effort. Topology Spread Constraints (`topologySpreadConstraints`) provide fine-grained, deterministic control over pod distribution across defined topology keys (such as `topology.kubernetes.io/zone`). By specifying `maxSkew: 1`, `topologyKey: topology.kubernetes.io/zone`, and `whenUnsatisfiable: DoNotSchedule` (or `ScheduleAnyway`), the scheduler ensures that the difference in pod count between any two zones never exceeds the `maxSkew` threshold. As the cluster autoscaler adds or removes nodes across zones, new pods are strictly placed in under-represented zones, preventing single-AZ concentration and ensuring resilient disaster recovery during zone outages.",
        [
            "Explains the limitations of Pod Anti-Affinity and how Topology Spread Constraints control pod distribution across zones.",
            "Defines key parameters including `maxSkew`, `topologyKey: topology.kubernetes.io/zone`, and `whenUnsatisfiable` policies."
        ],
        [
            "Claims that Kubernetes automatically balances all pods equally across zones without any configuration.",
            "Confuses topology spread constraints with node selectors."
        ]
    ),
    (
        "b8",
        "scenario",
        "medium",
        "scenario",
        ["Kubernetes", "Reliability Engineering"],
        "During a scheduled Kubernetes node maintenance window, a `kubectl drain` command hangs indefinitely and fails to evict application workloads. How do you troubleshoot and resolve PodDisruptionBudget (PDB) deadlocks?",
        "When `kubectl drain` runs, it calls the Eviction API to gracefully terminate pods on the target node while honoring active `PodDisruptionBudget` (PDB) constraints. A drain hangs when a PDB's disruption budget is zero (`allowedDisruptions: 0`). Common causes include: 1) Overly restrictive PDB configurations (e.g., a Deployment with 2 replicas and a PDB setting `minAvailable: 2` or `maxUnavailable: 0`), meaning no single pod can ever be taken down without violating the budget; 2) Other replicas are already in an unhealthy or `CrashLoopBackOff` state, meaning taking down the node's replica would breach the minimum available threshold; 3) Unmanaged standalone pods (pods not created by a Deployment, ReplicaSet, or StatefulSet) present on the node, which block drain unless `--force` is passed. To resolve: inspect the PDB status with `kubectl get pdb`; adjust the PDB or scale up the deployment replicas to restore disruption budget allowance; and execute `kubectl drain <node> --ignore-daemonsets --delete-emptydir-data`.",
        [
            "Identifies how PDB constraints (`allowedDisruptions: 0` or `minAvailable == replicas`) cause `kubectl drain` to hang indefinitely.",
            "Details operational resolution steps including inspecting `kubectl get pdb`, scaling deployment replicas, and handling unmanaged pods and emptyDir storage."
        ],
        [
            "Recommends forcibly rebooting the physical node without evicting pods.",
            "Claims that `kubectl drain` automatically deletes and overrides all PDB constraints by default."
        ]
    ),
    (
        "b8",
        "debug",
        "medium",
        "debugging",
        ["Kubernetes", "Containers & OS"],
        "A stateful worker pod using local `emptyDir` volumes is repeatedly evicted with `The node had condition: [DiskPressure]`, but application disk writes remain moderate. How do you configure ephemeral storage requests and limits to isolate disk usage?",
        "In Kubernetes, an `emptyDir` volume defaults to being backed by the node's root filesystem (`/var/lib/kubelet/pods/`). If multiple pods write temporary files, logs, or uncompressed archives to their local `emptyDir` volumes without explicit storage quotas, they compete for the same host disk partition. When the node's available root disk space drops below the kubelet's eviction threshold (typically 10-15% free disk), the kubelet marks the node with `DiskPressure` and begins evicting pods based on disk usage rankings. To resolve and isolate ephemeral disk usage: 1) Configure explicit `resources.requests.ephemeral-storage` and `resources.limits.ephemeral-storage` in the pod's container spec (e.g., request 2Gi, limit 10Gi); 2) The kubelet actively tracks ephemeral storage usage per pod; if a pod exceeds its specified `limits.ephemeral-storage`, the kubelet evicts only that specific offending pod rather than evicting innocent neighbor pods or causing node-wide DiskPressure; 3) For small, ultra-fast scratchpads, configure `emptyDir.medium: Memory` to back the volume with RAM (tmpfs) instead of disk.",
        [
            "Explains that unconstrained `emptyDir` volumes share the node root filesystem and trigger node-wide `DiskPressure` evictions.",
            "Details how setting `resources.limits.ephemeral-storage` enables the kubelet to evict only the offending pod, and suggests `emptyDir.medium: Memory` as an alternative."
        ],
        [
            "Claims that `emptyDir` volumes are allocated from cloud block storage (EBS) volumes automatically.",
            "Suggests disabling kubelet disk pressure eviction checks entirely on production nodes."
        ]
    ),
    (
        "b8",
        "explain",
        "medium",
        "conceptual",
        ["Kubernetes", "Security"],
        "When implementing custom admission webhooks in Kubernetes, what failure mode occurs if a ValidatingWebhookConfiguration is configured with `failurePolicy: Fail` and the webhook service becomes unreachable?",
        "When a webhook is configured with `failurePolicy: Fail`, any failure during webhook invocation—such as the webhook service being down, timing out, experiencing network partition, or having an invalid TLS certificate—causes the Kubernetes API server to reject the incoming API request with a 500/InternalServerError or 403/Forbidden. If the webhook evaluates core resources (like Pods, Deployments, or Namespaces) cluster-wide without scoping, an outage of the webhook pod creates a catastrophic cluster control-plane deadlock: no new pods can be scheduled, existing pods cannot be restarted or updated, and even the webhook's own replacement pods cannot be admitted or scheduled by the API server. To prevent this deadlock: 1) Configure `namespaceSelector` or `objectSelector` to explicitly exempt system namespaces (`kube-system`); 2) Use high-availability multi-replica deployments for webhook pods with PodDisruptionBudgets and anti-affinity; 3) Use `failurePolicy: Ignore` during initial rollout or for non-critical compliance audits.",
        [
            "Describes the control-plane deadlock where `failurePolicy: Fail` blocks all new pod scheduling including the webhook's own recovery pods.",
            "Details architectural mitigations such as namespace exemptions (`kube-system`), multi-replica webhook HA, and using `failurePolicy: Ignore` where appropriate."
        ],
        [
            "Claims that `failurePolicy: Fail` automatically falls back to approving requests if the webhook times out.",
            "Suggests running admission webhooks outside Kubernetes with no TLS certificates."
        ]
    ),
    (
        "b8",
        "debug",
        "hard",
        "debugging",
        ["Kubernetes", "Networking"],
        "Following an upgrade to an Ingress Controller, downstream microservice clients report intermittent connection resets (`ECONNRESET`) during rolling deployments. How do you trace keep-alive connection reuse and configure graceful shutdown hooks?",
        "During a rolling update, Kubernetes deletes old pods and creates new ones. When a pod deletion begins: 1) The pod status changes to `Terminating` and endpoints are removed from the Service; 2) Concurrently, the kubelet sends `SIGTERM` to the container. However, endpoint removal from IPVS/iptables and Ingress Controller upstream pools takes several seconds to propagate across the cluster. If the Ingress Controller maintains persistent HTTP keep-alive connections to the terminating pod, or dispatches a newly arrived request over an existing idle connection right as the application receives `SIGTERM` and closes its listening socket, the TCP connection is abruptly reset with RST, causing `ECONNRESET` or 502 Bad Gateway to clients. To eliminate this: 1) Add a `lifecycle.preStop.exec` hook with `sleep 15` to the pod spec; this delays the delivery of `SIGTERM`, allowing the Ingress Controller and Service endpoints to fully deregister the pod before the application begins shutdown; 2) Ensure the application gracefully drains active requests during `terminationGracePeriodSeconds`; 3) Tune the Ingress Controller's upstream keep-alive timeout to be shorter than the backend application's idle timeout.",
        [
            "Explains the race condition between asynchronous Service endpoint deregistration and immediate container `SIGTERM` shutdown.",
            "Prescribes the use of `preStop` sleep hooks, tuning upstream keep-alive timeouts, and configuring graceful application request draining."
        ],
        [
            "Suggests increasing the CPU and RAM of the ingress controller to solve connection resets.",
            "Claims that Kubernetes automatically delays SIGTERM until all network caches across the cluster are updated."
        ]
    ),
    (
        "b8",
        "optimize",
        "hard",
        "architectural",
        ["Kubernetes", "Networking"],
        "In a large enterprise Kubernetes cluster running on bare metal, network engineers discover that pod-to-pod routing tables exceed physical switch memory limits. How does Calico BGP route reflector architecture resolve this scalability limit?",
        "In a standard Calico CNI deployment using BGP for native Layer 3 pod routing, every node peers with every other node in a full BGP mesh. For a cluster with N nodes, the total number of BGP peering sessions is `N * (N - 1) / 2`. When a cluster grows to hundreds or thousands of nodes, each node and physical Top-of-Rack (ToR) switch must maintain thousands of BGP sessions and route table entries, causing switch TCAM (Ternary Content-Addressable Memory) table exhaustion and severe BGP control plane CPU churn during pod churn. To scale beyond this limit: 1) Disable the default node-to-node BGP mesh; 2) Deploy Calico BGP Route Reflectors (either dedicated virtual appliances or designated Kubernetes worker nodes); 3) Configure worker nodes to peer exclusively with the Route Reflectors in their rack or failure domain rather than with every other node. Route Reflectors aggregate and distribute routing updates, reducing BGP peering sessions from O(N^2) to O(N) and preserving physical switch memory while supporting tens of thousands of pods.",
        [
            "Identifies the O(N^2) scaling limit of a full-mesh BGP network topology and the resulting switch TCAM exhaustion.",
            "Details how Calico BGP Route Reflectors decouple peering, reducing peering connections to O(N) and enabling large-scale multi-rack scalability."
        ],
        [
            "Claims that full-mesh BGP peering scales indefinitely without hardware switch limitations.",
            "Suggests switching from Kubernetes to manual virtual machines to avoid routing tables."
        ]
    ),
    (
        "b9",
        "implement",
        "hard",
        "best_practices",
        ["CI/CD", "Security"],
        "To harden a self-hosted GitHub Actions runner infrastructure against malicious pull requests from external forks, how do you architect ephemeral runner dispatch and network isolation?",
        "Self-hosted CI/CD runners maintain persistent environments; if an untrusted pull request from a public fork runs arbitrary code on a self-hosted runner, an attacker can extract host credentials, inspect disk caches, compromise the local network, or persist a backdoor across subsequent builds. To harden this architecture: 1) Deploy ephemeral, single-use runners (using solutions like Actions Runner Controller - ARC with runner scale sets or ephemeral AWS EC2/Firecracker microVMs launched on-demand via webhooks); each runner process handles exactly one job and is immediately destroyed and wiped upon completion; 2) Enforce strict GitHub repository settings requiring manual approval from a repository maintainer before workflows execute on PRs submitted by outside collaborators (`require approval for all outside collaborators`); 3) Restrict the runner VM's IAM roles and network egress using dedicated VPC subnets and security groups that block access to internal corporate services, databases, and AWS metadata services; 4) Use separate runner pools for public PR validation versus protected branch deployments.",
        [
            "Outlines the architecture of ephemeral, single-use runner environments (e.g., ARC or microVMs) destroyed after every job execution.",
            "Specifies security controls including manual workflow approval for fork PRs, network egress isolation, and separation of runner pools by privilege tier."
        ],
        [
            "Suggests sharing a single persistent build server across all public pull requests and internal deployments.",
            "Claims that running Docker inside a non-ephemeral runner provides complete security isolation against host compromise."
        ]
    ),
    (
        "b9",
        "compare",
        "medium",
        "conceptual",
        ["CI/CD", "Security"],
        "In a regulated software delivery pipeline aiming for SLSA Level 3 compliance, what is the operational relationship between Software Bill of Materials (SBOM) generation and cryptographic attestation using Cosign and Rekor?",
        "A Software Bill of Materials (SBOM), generated by tools like Syft or Trivy in SPDX or CycloneDX formats, provides a machine-readable inventory of all software dependencies, libraries, OS packages, and compiler versions incorporated into a container image. However, an unsigned SBOM can be altered or forged. SLSA (Supply-chain Levels for Software Artifacts) Level 3 requires non-falsifiable provenance and hermetic build attestations. To achieve this, Cosign signs the container image and cryptographically binds the SBOM and build provenance to the image artifact. The cryptographic signature and in-toto provenance attestation are published to Rekor, a tamper-resistant, append-only transparency log. Downstream Kubernetes admission controllers (such as Sigstore Policy Controller or Kyverno) query Rekor to verify the signature and cryptographic attestation before permitting deployment. The SBOM provides transparency into *what* is in the artifact; cryptographic attestation and Rekor verify *who* built it, *where* it was built, and that it has not been tampered with.",
        [
            "Distinguishes between vulnerability transparency (SBOM via SPDX/CycloneDX) and cryptographic verification of provenance (Cosign and Rekor).",
            "Explains the role of Rekor as an immutable transparency log and admission controllers verifying attestations under SLSA Level 3."
        ],
        [
            "Confuses an SBOM with a standard Dockerfile.",
            "Claims that generating an SBOM automatically prevents unauthorized modifications without cryptographic signing."
        ]
    ),
    (
        "b9",
        "scenario",
        "medium",
        "scenario",
        ["CI/CD", "Kubernetes"],
        "A GitOps deployment using ArgoCD enters an infinite out-of-sync reconciliation loop where the application continuously syncs every few seconds. How do you diagnose and eliminate this reconciliation drift?",
        "An infinite reconciliation sync loop in GitOps occurs when there is a permanent discrepancy between the desired manifest declared in Git and the live cluster state, often caused by mutating controllers or admission webhooks modifying the resource after ArgoCD applies it. For example, a Mutating Admission Webhook might inject default fields, horizontal pod autoscalers might alter replica counts, or a cloud controller might inject dynamic annotations. ArgoCD compares the Git manifest against the live resource; detecting a difference, it issues a patch, which the cluster controller mutates again, creating an endless sync loop. To diagnose: inspect the ArgoCD UI or run `argocd app diff <app-name>` to identify the specific mutating fields. To resolve: 1) Update the Git manifest to include the mutated default fields if static; 2) Configure `ignoreDifferences` in the ArgoCD Application manifest specifying the `group`, `kind`, and `jsonPointers` (e.g., ignoring `/spec/replicas` when using HPA, or dynamic metadata annotations); 3) Ensure mutating webhooks do not introduce non-deterministic mutations.",
        [
            "Identifies the root cause: conflict between GitOps desired state and live cluster mutations from admission webhooks or controllers.",
            "Prescribes diagnostic tools (`argocd app diff`) and resolution via `ignoreDifferences` JSON pointers and aligning Git manifests."
        ],
        [
            "Recommends turning off automated sync in ArgoCD and deploying manually with `kubectl apply`.",
            "Claims that deleting the application from GitOps will solve the sync loop while preserving production state."
        ]
    ),
    (
        "b9",
        "implement",
        "medium",
        "best_practices",
        ["CI/CD", "Reliability Engineering"],
        "When executing database schema changes within an automated continuous deployment pipeline, how does the Expand-and-Contract (Parallel-Run) pattern prevent application downtime?",
        "In continuous deployment, code deployments and database schema updates cannot happen with instantaneous atomicity across multiple running instances. If a migration destructively alters a table (e.g., renaming a column or dropping a table), existing running application pods immediately crash with query errors. The Expand-and-Contract (or Parallel-Run) pattern decouples migrations into non-breaking, forward-and-backward compatible phases: 1) Expand Phase: The database migration pipeline adds the new column or table alongside the old one without touching existing columns. The updated application code is deployed; it writes to both the old and new columns simultaneously while reading from the old column. 2) Backfill Phase: A background job backfills existing historical data from the old column into the new column. 3) Switch Phase: A subsequent code deployment shifts the application to read and write exclusively from the new column. 4) Contract Phase: Once all pods run the new code, a final migration drops the deprecated old column. This guarantees zero-downtime rollouts and safe rollbacks at any stage.",
        [
            "Outlines the four sequential phases of Expand and Contract: Expand (additive), Backfill, Switch (read shift), and Contract (deprecate/drop).",
            "Explains why decoupling schema changes from application deployment prevents crashes and maintains backward compatibility during rolling deployments."
        ],
        [
            "Advocates locking the entire database and putting the web application in maintenance mode for all schema changes.",
            "Suggests renaming database columns directly in production during peak traffic without dual-writing."
        ]
    ),
    (
        "b9",
        "optimize",
        "medium",
        "problem_solving",
        ["CI/CD", "Cloud Architecture"],
        "In a large monorepo with hundreds of microservices, pull request CI builds take over 45 minutes to execute. How do you re-architect the pipeline using affected change analysis and remote build caching to reduce build times to under 5 minutes?",
        "A naive CI pipeline in a monorepo runs all linters, tests, and compilation steps across every project on every pull request, causing pipeline execution time to scale linearly with codebase size. To optimize this: 1) Implement Affected Change Analysis (using tools like Nx, Turborepo, or Bazel); by analyzing the Git commit diff (`git diff origin/main...HEAD`) against the internal project dependency graph, the pipeline identifies and executes tests *only* for projects directly modified or downstream dependents affected by the changes, skipping untouched microservices entirely; 2) Implement Distributed Remote Caching: build artifacts and test execution outputs are hashed by input files, compiler flags, and environment variables. When a build step matches an existing hash in the shared cloud remote cache (e.g., S3 or dedicated cache server), the step immediately downloads the cached artifact instead of executing from scratch; 3) Parallelize test matrix execution across dynamic ephemeral worker pools.",
        [
            "Explains affected project graph analysis to skip building and testing unaffected microservices in a monorepo.",
            "Details distributed remote caching where deterministic input hashes fetch pre-built artifacts from shared cloud storage."
        ],
        [
            "Suggests skipping all unit and integration tests completely on pull requests to speed up builds.",
            "Claims that splitting the monorepo into 500 separate Git repositories automatically eliminates build and dependency overhead."
        ]
    ),
    (
        "b9",
        "fundamentals",
        "hard",
        "best_practices",
        ["CI/CD", "Observability", "Reliability Engineering"],
        "When implementing progressive canary delivery using Argo Rollouts or Flagger, what metric analysis criteria and health gates must be configured to trigger an automated rollback?",
        "Progressive canary delivery shifts a small percentage of real production traffic (e.g., 5% -> 20% -> 50% -> 100%) to a new version while actively evaluating system health. Rather than relying on simple pod readiness probes, automated health gates continuously analyze live Prometheus or Datadog metrics during each step interval. Critical metric analysis criteria include: 1) HTTP Success Rate / Error Rate: evaluating whether the canary version's 5xx error percentage remains below a strict threshold (e.g., `success-rate >= 99.5%` or error rate < 0.5%); 2) Latency Percentiles: verifying that p95/p99 request duration does not exceed a baseline (e.g., `p99_latency < 500ms`); 3) Failure Limit / Consecutive Failures: defining how many consecutive metric evaluation failures trigger an immediate rollback (e.g., `failureLimit: 3`). If metric evaluation fails the threshold, the controller halts traffic progression, shifts 100% of traffic back to the stable replica set, and scales down the canary deployment, preventing bad releases from impacting the wider user base.",
        [
            "Specifies key health gate metrics including HTTP error rates, p95/p99 latency thresholds, and custom business SLIs.",
            "Explains the mechanics of automated rollback execution when consecutive metric evaluation checks breach failure limits during canary progression."
        ],
        [
            "Claims that progressive delivery relies solely on manual approvals without automated metric evaluation.",
            "Suggests rolling back only after an entire canary rollout has reached 100% of production traffic."
        ]
    )
]
