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
    ("B67_5_1", "scenario", "hard", "scenario", ["Stateful Workloads", "Kubernetes"],
     "You deploy a highly available PostgreSQL cluster on Kubernetes using a StatefulSet with persistent volume claims (PVCs) backed by AWS EBS. Node A, running the primary database pod, suddenly suffers a catastrophic hardware failure and becomes completely unreachable. However, the StatefulSet controller refuses to schedule the replacement pod on a healthy node, leaving the database permanently offline. Why does the StatefulSet refuse to failover, and how do you forcefully resolve the storage deadlock?",
     "Kubernetes StatefulSets enforce a strict 'at most one' guarantee for pod identity. Because Node A is unreachable, the Kubernetes control plane cannot confirm that the pod on Node A has actually stopped executing. If Kubernetes were to schedule the replacement pod on Node B and attach the EBS volume, it risks Split-Brain data corruption if Node A suddenly reconnects and both pods write to the disk simultaneously. Therefore, the StatefulSet controller mathematically refuses to reschedule the pod until Node A is definitively confirmed dead. Furthermore, AWS EBS volumes are single-attach (ReadWriteOnce); the volume remains locked to the dead Node A. To forceful resolve this: You must explicitly delete the Node object from Kubernetes (kubectl delete node node-A). This breaks the deadlock, signals the control plane that the node is definitively gone, forces AWS to detach the EBS volume, and allows the StatefulSet to safely schedule the pod and attach the volume on Node B.",
     ["Identifies the StatefulSet 'at most one' identity guarantee preventing split-brain", "Identifies ReadWriteOnce constraints leaving the EBS volume locked to the unreachable node", "Prescribes forceful Node object deletion from the Kubernetes API to break the deadlock"],
     ["Claims StatefulSets automatically failover in 30 seconds like Deployments do"]),

    ("B67_5_2", "concept", "easy", "concept", ["Storage Architecture", "Cloud Storage"],
     "Explain the architectural difference between AWS EBS (Elastic Block Store) and AWS EFS (Elastic File System) regarding multi-node attachment and underlying storage protocols.",
     "AWS EBS is Block Storage. It behaves like a physical hard drive plugged directly into a server. It provides extremely high-performance, low-latency I/O (good for databases). However, it is fundamentally 'single-attach' (ReadWriteOnce); an EBS volume can only be mounted to exactly one EC2 instance at a time. AWS EFS is Network File Storage (NFS). It provides a shared, hierarchical filesystem over the network. It is 'multi-attach' (ReadWriteMany); thousands of EC2 instances or Kubernetes pods can mount the exact same EFS filesystem simultaneously and read/write files concurrently. The tradeoff is that EFS has significantly higher latency and lower per-node IOPS compared to EBS, making it terrible for databases but excellent for shared web assets or CI/CD caches.",
     ["Defines EBS as Block Storage with Single-Attach (ReadWriteOnce) and high performance", "Defines EFS as Network File Storage (NFS) with Multi-Attach (ReadWriteMany) and higher latency", "Correctly identifies databases belonging on EBS and shared assets belonging on EFS"],
     ["Claims EFS is used for block storage and EBS is used for object storage like S3"]),

    ("B67_5_3", "diagnose", "hard", "debugging", ["Cloud Cost Architecture", "AWS Networking"],
     "A company runs a massive data-processing cluster in AWS across three Availability Zones (AZs) for high availability. The EC2 instances frequently shuffle terabytes of data between each other. The monthly AWS bill arrives, and the 'Data Transfer' costs are unexpectedly astronomically high—nearly exceeding the compute costs. The architect verifies that all data is strictly staying within the same AWS VPC and never touches the public internet. Why is the internal VPC data transfer costing so much, and how do you redesign it?",
     "The massive cost is caused by Cross-AZ Data Transfer fees. While data transfer *within* the exact same Availability Zone is 100% free, AWS charges a premium (e.g., $0.01 per GB) for data transferred *between* different Availability Zones, even if they are in the exact same VPC and region. If terabytes of data are continuously shuffled across AZ boundaries (e.g., a heavily cross-AZ distributed Kafka or Cassandra cluster), the costs explode. To redesign: 1) Implement 'Topology Aware Routing' so that microservices strongly prefer to talk to dependencies residing in the exact same AZ, only crossing the AZ boundary during a failure. 2) For massive batch-processing clusters (like Hadoop/Spark), isolate the compute jobs entirely into a single AZ to guarantee zero cross-AZ shuffling fees, utilizing Multi-AZ strictly for stateless web tiers or long-term storage (S3).",
     ["Diagnoses hidden cross-AZ data transfer fees within the same VPC", "Explains that intra-AZ transfer is free, but inter-AZ transfer incurs per-GB costs", "Prescribes Topology Aware Routing or isolating massive compute jobs to a single AZ"],
     ["Suggests the EC2 instances are accidentally using a NAT Gateway to talk to each other"]),

    ("B67_5_4", "tradeoff", "medium", "tradeoff", ["Cloud Cost Architecture", "FinOps"],
     "What is the tradeoff of using AWS NAT Gateways versus using VPC Endpoints (PrivateLink) to allow private subnets to access AWS managed services like S3 or DynamoDB?",
     "NAT Gateways: Advantages: Extremely simple. You set up one NAT Gateway, and all private subnets instantly gain access to the entire public internet, including all AWS services. Disadvantages: Massive data processing costs. AWS charges a per-GB data processing fee for every byte that flows through the NAT Gateway. If you download 50TB of data from S3 via a NAT Gateway, you pay thousands of dollars in NAT processing fees. VPC Endpoints (Gateway/Interface Endpoints): Advantages: Massive cost savings and security. A Gateway Endpoint for S3 is 100% free and routes traffic directly across the internal AWS backbone, completely bypassing the NAT Gateway. Interface Endpoints (PrivateLink) cost a small hourly fee but drastically reduce per-GB bandwidth charges for services like Kinesis or ECR. Disadvantages: Higher architectural complexity. You must manually provision, configure, and manage DNS/Route Tables for individual endpoints for every single AWS service you want to access privately.",
     ["Contrasts NAT Gateway simplicity against its massive per-GB data processing billing costs", "Contrasts VPC Endpoint massive cost savings/security against high DNS/Route Table configuration complexity", "Highlights that S3 Gateway Endpoints specifically are 100% free"],
     ["Claims NAT Gateways are required by AWS for all S3 traffic"]),

    ("B67_5_5", "scenario", "medium", "scenario", ["Platform Engineering", "Developer Experience"],
     "You are building an Internal Developer Platform (IDP). You want developers to self-serve new infrastructure (like S3 buckets or RDS databases) by simply submitting a YAML file. However, your Security team mandates that all infrastructure must have strict naming conventions, mandatory encryption tags, and maximum size limits. How do you implement automated 'Guardrails' in a GitOps/Terraform-based IDP to enforce these rules without requiring the security team to manually review every PR?",
     "You implement 'Policy-as-Code' directly into the CI/CD pipeline. Using tools like Open Policy Agent (OPA), Checkov, or HashiCorp Sentinel, you write deterministic, programmatic policies. Implementation: 1) The developer submits a PR containing the Terraform/YAML declaring the new database. 2) The CI pipeline runs terraform plan and outputs the JSON plan. 3) The pipeline feeds the JSON plan into the OPA engine. 4) The OPA engine evaluates the plan against the Security team's strict Rego policies (e.g., deny if db.encrypted == false, deny if db.size > 100GB). 5) If the policy fails, the CI pipeline fails immediately, blocking the PR from merging and providing instantaneous feedback to the developer. The security team only needs to audit the centralized OPA policy definitions, not the thousands of individual developer PRs.",
     ["Identifies Policy-as-Code (OPA/Checkov/Sentinel) as the automated guardrail mechanism", "Explains executing policies against the parsed infrastructure plan (e.g., terraform plan JSON) inside the CI pipeline", "Highlights instantaneous developer feedback and blocked PRs without human security reviews"],
     ["Suggests writing a Python script to scan the deployed database after it is created"]),

    ("B67_5_6", "concept", "easy", "concept", ["Platform Engineering", "Architecture"],
     "What is a 'Golden Path' (or Paved Road) in Platform Engineering, and how does it balance developer autonomy with organizational standardization?",
     "A Golden Path is a highly opinionated, fully supported, and heavily automated set of tools and templates provided by the Platform Engineering team to build and deploy software. It balances autonomy by not *forcing* developers to use it, but making it the path of least resistance. If a developer chooses the Golden Path (e.g., using the officially supported Spring Boot template, the standard CI/CD pipeline, and the default Kubernetes deployment), everything works instantly, security is pre-approved, and the platform team provides 24/7 support. If a developer chooses to go 'off-roading' (e.g., writing a custom framework in Haskell and deploying it on raw EC2 instances), they are allowed to do so (autonomy), but they must maintain, secure, and support the entire infrastructure themselves.",
     ["Defines Golden Path as an officially supported, highly automated deployment template", "Explains the balance: not strictly mandated, but incentivized via 'path of least resistance'", "Clarifies that going 'off-road' means the developer inherits 100% of the maintenance burden"],
     ["Claims the Golden Path is the shortest network route between two microservices"]),

    ("B67_5_7", "diagnose", "hard", "debugging", ["Stateful Workloads", "Kubernetes"],
     "A developer deletes a PersistentVolumeClaim (PVC) in Kubernetes, intending to destroy the underlying cloud disk to save costs. However, the PVC gets stuck in a Terminating state forever, and the underlying cloud disk is never deleted. You check the events, but there are no errors. What Kubernetes protection mechanism causes PVCs to hang in the Terminating state, and how do you safely unblock it?",
     "The PVC is stuck because of the kubernetes.io/pvc-protection finalizer. This is a critical Kubernetes safeguard designed to prevent data loss. If a developer accidentally deletes a PVC while a Pod is still actively mounting and using it, the finalizer mathematically blocks the deletion of the PVC object (and the underlying cloud disk). It will remain in the Terminating state indefinitely until the Pod using it is shut down. To safely unblock it, you must identify which Pod is currently using the volume (kubectl get pods -o json | jq ...) and delete or scale down that Pod. Once the Pod is terminated and the volume is unmounted, the Kubernetes control plane automatically removes the finalizer, allowing the PVC deletion to proceed and the cloud disk to be destroyed. Force-removing the finalizer manually while the pod is running is incredibly dangerous and can corrupt the node's mount namespace.",
     ["Identifies the kubernetes.io/pvc-protection finalizer blocking the deletion", "Explains the safeguard prevents destroying disks that are actively mounted to a running Pod", "Prescribes gracefully terminating the associated Pod to naturally unblock the finalizer"],
     ["Suggests manually editing the PVC YAML to delete the finalizer while the pod is running"]),

    ("B67_5_8", "tradeoff", "medium", "tradeoff", ["Storage Architecture", "Data Management"],
     "When designing a disaster recovery strategy for a massive 50TB database, what is the tradeoff between relying entirely on 'Storage-Level Snapshots' (e.g., EBS snapshots) versus 'Application-Level Logical Backups' (e.g., pg_dump or MySQL dump)?",
     "Storage-Level Snapshots: Advantages: Extremely fast and zero impact on the database CPU. Cloud providers take block-level snapshots instantly in the background without locking tables. Recovery is incredibly fast (you just boot a new volume from the snapshot). Disadvantages: They are 'crash-consistent', not 'application-consistent'. If the database had transactions cached in RAM that weren't flushed to disk at the exact millisecond of the snapshot, the recovered database might require complex crash recovery on boot. Also, you cannot restore a single dropped table; you must restore the entire 50TB volume. Application-Level Logical Backups: Advantages: Extremely granular and highly consistent. You can easily extract and restore a single table or single row. They are portable across different database versions or cloud providers. Disadvantages: Extremely slow, consumes massive amounts of database CPU/RAM to generate the dump, and restoring a 50TB logical dump could take days of sequential INSERT statements.",
     ["Contrasts instantaneous, low-impact block snapshots with slow, high-impact logical dumps", "Highlights that snapshots are only crash-consistent and force all-or-nothing volume restoration", "Highlights that logical backups provide row-level granularity and perfect transaction consistency but fail at 50TB scales"],
     ["Claims EBS snapshots cost thousands of dollars per gigabyte"]),

    ("B67_5_9", "scenario", "medium", "scenario", ["Platform Engineering", "Kubernetes"],
     "Your Platform team provides a shared, multi-tenant Kubernetes cluster for 50 different development teams. A rogue developer deploys a poorly written script that creates 100,000 ConfigMaps and Secrets in their specific namespace within 5 minutes. This massive object creation completely overwhelms the cluster's etcd database, crashing the entire control plane for all 50 teams. How do you implement organizational safeguards to strictly limit the 'blast radius' of tenant metadata creation?",
     "While standard ResourceQuotas restrict CPU and Memory, they must also be explicitly configured to restrict Kubernetes Object counts. To prevent etcd exhaustion, the Platform team must implement a strict ResourceQuota in every single tenant namespace. Implementation: You define a quota specifying count/configmaps: 100, count/secrets: 100, and count/pods: 50. Once the developer's script hits the 100th ConfigMap, the Kubernetes API server will actively reject any further POST requests for that namespace with an HTTP 403 Forbidden, protecting etcd from unbounded database growth and entirely neutralizing the blast radius of the rogue script to just that specific tenant.",
     ["Identifies unbounded API object creation exhausting the control plane etcd database", "Prescribes configuring ResourceQuotas specifically for Object Counts (e.g., count/configmaps)", "Explains that the API server will reject subsequent requests, physically containing the blast radius"],
     ["Suggests banning the developer from the company's network firewall"]),

    ("B67_5_10", "implement", "hard", "implement", ["Cloud Cost Architecture", "Autoscaling"],
     "Your EKS cluster uses Karpenter for node autoscaling. You have a highly variable workload that requires massive scaling during the day, but sits idle at night. How do you configure Karpenter's 'Provisioner' (or NodePool) CRDs to implement aggressive cost-optimization through 'Consolidation', and how does it mathematically differ from the legacy Cluster Autoscaler?",
     "1) Configuration: In the Karpenter NodePool CRD, you enable consolidationPolicy: WhenUnderutilized (or WhenEmpty). 2) How Consolidation works: The legacy Cluster Autoscaler only scales down a node if it is completely empty (or heavily underutilized) AND all its pods can fit on other *currently existing* nodes. It is mathematically rigid. Karpenter's Consolidation is highly aggressive and predictive. Karpenter constantly simulates alternative cluster states. It calculates: 'If I terminate these 3 expensive, half-empty m5.4xlarge nodes, and simultaneously provision 1 cheap, tightly packed c5.large node, can I fit all the pods on the new cluster footprint?' If the math proves a cheaper footprint exists, Karpenter will proactively spin up the new cheap node, cordon the 3 expensive nodes, migrate the pods, and terminate the expensive nodes. It actively reorganizes and resizes the cluster continuously to enforce the lowest possible billing cost.",
     ["Identifies setting consolidationPolicy: WhenUnderutilized in Karpenter", "Contrasts legacy ASG scale-down rigidity with Karpenter's dynamic footprint calculation", "Explains that Karpenter will aggressively replace multiple large nodes with a single smaller node to enforce cost density"],
     ["Claims Karpenter saves money by hibernating pods directly to disk during the night"]),

    ("B67_5_11", "concept", "easy", "concept", ["Cloud Cost Architecture", "AWS Storage"],
     "What are AWS S3 Lifecycle Policies, and how do they automate FinOps cost reductions for a company storing petabytes of compliance log data that must be kept for 7 years but is rarely read?",
     "S3 Lifecycle Policies are automated rules applied to an S3 bucket that automatically transition objects to cheaper, colder storage tiers as the objects age. Standard S3 storage is highly performant but very expensive (e.g., $0.023 per GB). For compliance logs that are written once and almost never read, paying Standard prices for 7 years is a massive waste of money. A Lifecycle Policy automates the FinOps strategy: 'Keep logs in S3 Standard for 30 days (for immediate debugging). On day 31, automatically move them to S3 Glacier Deep Archive (which costs $0.00099 per GB, a 95% discount). On day 2555 (7 years), automatically delete the objects.' This completely eliminates the need for engineers to manually groom storage, enforcing massive cost savings automatically.",
     ["Defines S3 Lifecycle Policies as automated rules for transitioning objects between storage tiers based on age", "Highlights the extreme cost savings of moving cold data to S3 Glacier Deep Archive", "Highlights the automation of compliance deletion after the mandatory 7-year retention period"],
     ["Claims S3 Lifecycle policies automatically compress logs using ZIP files to save space"]),

    ("B67_5_12", "diagnose", "medium", "debugging", ["Storage Architecture", "Kubernetes"],
     "A pod mounting an AWS EBS volume gets stuck in ContainerCreating. You check kubectl describe pod and see the error: 'Multi-Attach error for volume \"pvc-1234\" Volume is already exclusively attached to one node and can't be attached to another'. You verify that the previous pod using this volume was successfully deleted 10 minutes ago. Why is the cloud provider refusing to detach the volume from the old node, and how do you resolve it?",
     "This is a classic 'Stuck EBS Detachment' cloud provider race condition. Even though Kubernetes deleted the pod, the Kubernetes AWS EBS CSI driver (or legacy in-tree provider) issued the API call to AWS to detach the volume, but AWS failed to execute it (or the API call timed out/dropped). The cloud provider's physical infrastructure still believes the volume is attached to the old EC2 instance. Because EBS is ReadWriteOnce, AWS strictly blocks the new EC2 instance from attaching it. Resolution: 1) Do NOT forcefully delete the PVC in Kubernetes. 2) Log into the AWS EC2 Console, locate the stuck EBS volume, and manually issue a 'Force Detach' command from the old EC2 instance. Once AWS physically releases the volume lock, the Kubernetes CSI driver will automatically detect the free volume, attach it to the new node, and the pod will successfully transition to Running.",
     ["Diagnoses an out-of-sync state between Kubernetes (pod deleted) and the AWS API (volume still attached)", "Explains that ReadWriteOnce semantics mathematically block the new attachment", "Prescribes manually Force Detaching the volume in the AWS EC2 Console to resync the state"],
     ["Suggests formatting the volume from the command line to clear the error"]),

    ("B67_5_13", "tradeoff", "medium", "tradeoff", ["Stateful Workloads", "Architecture"],
     "When deploying a high-throughput message queue (like Apache Kafka) on Kubernetes, what is the operational tradeoff of using 'Local Persistent Volumes' (directly attached NVMe SSDs on the worker node) versus 'Network Attached Storage' (like AWS EBS or SAN)?",
     "Local Persistent Volumes: Advantages: Extreme performance. Writing directly to the physical NVMe SSDs on the motherboard bypasses all network latency, resulting in massive IOPS and zero network throttling, making it ideal for disk-heavy apps like Kafka. Disadvantages: Severe operational rigidity and data binding. The data is physically trapped on that specific worker node. If that worker node dies, the pod CANNOT be rescheduled to another node because its data is gone. You must rely entirely on Kafka's internal application-level replication to rebuild the data on a new node. Network Attached Storage (EBS): Advantages: Extreme operational flexibility. If a worker node dies, Kubernetes simply detaches the EBS volume from the dead node, attaches it to a new healthy node, and the pod boots up with its data 100% intact. Disadvantages: Lower IOPS, higher latency, and you consume network bandwidth for every disk write, which can saturate the EC2 network interface limits.",
     ["Contrasts Local PV massive performance against its rigid binding to a single physical node", "Contrasts Network Storage high availability and pod portability against network latency and IOPS limits", "Highlights the requirement of robust application-level replication when using Local PVs"],
     ["Claims Local Persistent Volumes are backed up automatically to S3 by Kubernetes"]),

    ("B67_5_14", "scenario", "medium", "scenario", ["Platform Engineering", "CI/CD"],
     "The Platform team builds a centralized, shared Jenkins cluster for 100 developers. Over time, the developers install 50 different Jenkins plugins, write massive imperative Groovy scripts in their pipelines, and tightly couple their builds to the specific version of Java installed on the Jenkins master. When the Platform team attempts to upgrade Jenkins, everything breaks. How do you redesign the CI/CD architecture using 'Declarative' and 'Containerized' principles to eliminate this fragile dependency?",
     "The architecture is failing due to 'Mutable Infrastructure' and 'Tight Coupling' to the CI server's global state. The redesign requires shifting to a Container-Native CI/CD model (e.g., Tekton, GitHub Actions, or GitLab CI). 1) Containerized Execution: Developers must completely stop relying on the software installed on the CI server. Every single step of the pipeline must execute inside a sterile, ephemeral Docker container (e.g., image: maven:3.8). The CI server's only job is to orchestrate containers, not compile code. 2) Declarative Configuration: Eliminate imperative Groovy scripts. Pipelines must be defined as declarative YAML files (Pipeline-as-Code) stored directly in the application's Git repository. 3) Plugin Elimination: Because tasks are executed inside custom Docker containers, developers simply build a container with the tools they need, completely eliminating the need to install risky global plugins on the central CI server. This makes the CI server stateless, enabling seamless upgrades.",
     ["Diagnoses 'Mutable Infrastructure' and global state coupling causing the upgrade breakage", "Prescribes isolating execution inside ephemeral Docker containers rather than the host OS", "Prescribes defining pipelines as declarative YAML stored in Git (Pipeline-as-Code)", "Highlights the elimination of fragile global plugins via containerized custom tools"],
     ["Suggests maintaining 50 different Jenkins servers, one for each developer"]),

    ("B67_5_15", "implement", "hard", "implement", ["Stateful Workloads", "Kubernetes"],
     "You are managing a massive StatefulSet in Kubernetes (e.g., Elasticsearch). You need to increase the size of the Persistent Volume Claim (PVC) from 100GB to 500GB. You update the resources.requests.storage field in the StatefulSet manifest and apply it, but Kubernetes throws an error: \"Forbidden: updates to statefulset spec for fields other than 'replicas', 'template', and 'updateStrategy' are forbidden\". How do you successfully execute a zero-downtime volume expansion for a StatefulSet?",
     "Kubernetes strictly forbids modifying the volumeClaimTemplates field of an existing StatefulSet to prevent catastrophic cascading data destruction. To expand the volumes, you must perform a multi-step manual procedure: 1) Patch the existing PVCs individually: You must run kubectl patch pvc <pvc-name> -p '{\"spec\":{\"resources\":{\"requests\":{\"storage\":\"500Gi\"}}}}' for every single PVC associated with the pods. The CSI driver will communicate with the cloud provider to expand the physical disk. 2) Wait for File System Resize: Kubernetes will dynamically resize the filesystem inside the running pod (if ExpandInUsePersistentVolumes is supported), or require a pod restart to resize the ext4/xfs filesystem. 3) Orphan the StatefulSet (The critical step): Because you cannot update the StatefulSet manifest directly to reflect the new 500GB template, you must delete the StatefulSet *without* deleting the pods using kubectl delete statefulset <name> --cascade=orphan. 4) Recreate the StatefulSet: Apply the updated StatefulSet manifest (with the 500GB template). The new StatefulSet will instantly adopt the existing running pods and expanded PVCs without any downtime.",
     ["Identifies the rigid immutability of the volumeClaimTemplates field in a StatefulSet", "Prescribes manually patching the individual active PVCs to trigger cloud expansion", "Critically details deleting the StatefulSet with --cascade=orphan to preserve pods and PVCs", "Explains recreating the StatefulSet to adopt the running pods with the new template"],
     ["Suggests using pg_dump to back up the data, deleting the cluster, and restoring it from scratch"]),

    ("B67_5_16", "concept", "easy", "concept", ["Cloud Cost Architecture", "FinOps"],
     "In cloud cost management, what is the difference between 'Reserved Instances' (or Savings Plans) and 'Spot Instances', and what type of workload is appropriate for each?",
     "Reserved Instances / Savings Plans involve making a 1-year or 3-year financial commitment to the cloud provider to use a specific amount of compute capacity. In exchange for this long-term commitment, the provider grants a massive discount (e.g., up to 72%). This is appropriate for stable, predictable, baseline workloads (like a primary production database or the minimum baseline of web servers) that run 24/7. Spot Instances utilize the cloud provider's excess, unused server capacity. They offer extreme discounts (up to 90%), but with a severe caveat: the provider can forcibly terminate the instance with only a 2-minute warning if a paying customer needs the capacity. Spot Instances are only appropriate for highly resilient, stateless, fault-tolerant workloads (like batch processing, CI/CD runners, or tightly managed auto-scaling worker nodes) that can survive sudden interruption.",
     ["Defines Reserved Instances as long-term financial commitments ideal for stable 24/7 baseline loads", "Defines Spot Instances as extreme discount excess capacity subject to immediate forceful termination", "Correctly identifies stateless, fault-tolerant batch workloads as the only safe targets for Spot Instances"],
     ["Claims Spot Instances are permanently reserved for your account during high traffic spikes"]),

    ("B67_5_17", "scenario", "medium", "scenario", ["Stateful Workloads", "Kubernetes"],
     "A Cassandra database cluster runs on Kubernetes as a StatefulSet. During an automated node drain, a worker node is shut down, terminating a Cassandra pod. However, the Cassandra pod never reschedules to another node. You check the pod status and see 'Pending: 1 node(s) had volume node affinity conflict'. Why did Kubernetes refuse to move the pod, and what cloud storage constraint enforces this?",
     "The pod is blocked by 'Volume Node Affinity Conflict', which typically occurs when using Zonal Cloud Storage (like AWS EBS). When the Cassandra PVC was originally created, the cloud provider provisioned the EBS volume in a specific Availability Zone (e.g., us-east-1a). EBS volumes are strictly bound to a single AZ; they cannot mathematically be attached to an EC2 instance in a different AZ. When the node drain occurred, the Kubernetes scheduler attempted to place the pending pod on a new node. However, if the only available healthy nodes are located in us-east-1b or us-east-1c, the scheduler physically cannot place the pod there because the EBS volume is trapped in us-east-1a. The pod will remain Pending indefinitely until a new worker node is provisioned specifically in the us-east-1a zone.",
     ["Diagnoses 'Volume Node Affinity Conflict' as a geographic/zonal constraint violation", "Explains that AWS EBS volumes are strictly locked to a single Availability Zone", "Concludes that the scheduler cannot place the pod in AZ 'B' if the disk physically resides in AZ 'A'"],
     ["Suggests the volume has run out of disk space, preventing the pod from scheduling"]),

    ("B67_5_18", "diagnose", "medium", "debugging", ["Platform Engineering", "CI/CD"],
     "A developer complains that their Docker build in the CI/CD pipeline takes 15 minutes to execute every single time they commit, even if they only changed a single line of CSS. You inspect their Dockerfile and see: 1) COPY . /app 2) RUN npm install 3) RUN npm build. What fundamental Docker caching mechanism is being violated, and how do you rewrite the Dockerfile to reduce build times to 30 seconds?",
     "The developer is violating Docker Layer Caching invalidation rules. Docker executes instructions sequentially. If a layer changes, *all* subsequent layers are completely invalidated and must be rebuilt from scratch. By executing COPY . /app (which copies the entire repository, including the frequently changing CSS files) *before* running npm install, the cache for the npm install layer is instantly invalidated on every single commit. The CI pipeline is needlessly downloading gigabytes of Node modules over the internet every time. To fix this, you must separate the dependency installation from the source code. Rewrite: 1) COPY package.json package-lock.json /app/ 2) RUN npm install 3) COPY . /app 4) RUN npm build. Now, changing a CSS file only invalidates step 3. The massive npm install layer is heavily cached and instantly reused across builds, drastically cutting execution time.",
     ["Identifies sequential Docker Layer Caching and downward invalidation cascades", "Diagnoses that copying changing source code before downloading dependencies invalidates the dependency cache", "Prescribes copying only lockfiles first, running the install, and *then* copying the source code"],
     ["Claims the internet connection on the Jenkins server is too slow"]),

    ("B67_5_19", "tradeoff", "hard", "tradeoff", ["Storage Architecture", "Kubernetes"],
     "In Kubernetes, what is the architectural tradeoff of managing persistent storage via static, pre-provisioned Persistent Volumes (PVs) mapped manually by administrators, versus using dynamic provisioning via StorageClasses and Persistent Volume Claims (PVCs)?",
     "Static Provisioning: The cloud administrator manually creates a physical disk in AWS/GCP, manually writes a Kubernetes PV manifest linking the volume ID, and the developer claims it. Advantages: Absolute control over storage costs, highly strict governance, and perfect for attaching legacy, pre-existing datasets to new clusters without risking accidental deletion. Disadvantages: Massive operational bottleneck. Developers cannot self-serve; they must wait for IT tickets to provision disks, completely destroying agile deployment velocity. Dynamic Provisioning (StorageClasses): The administrator defines a StorageClass (e.g., 'fast-ssd'). The developer submits a PVC requesting '100GB of fast-ssd'. Kubernetes automatically commands the cloud provider via the CSI driver to provision the physical disk and bind it instantly. Advantages: Infinite scalability, zero-touch operational overhead, and true developer self-service. Disadvantages: High risk of cost explosions (developers can easily request 50TB of expensive provisioned IOPS SSDs instantly) and requires strict Kubernetes ResourceQuotas and lifecycle policies (ReclaimPolicy: Retain/Delete) to prevent massive orphaned cloud billing.",
     ["Contrasts Static rigid cost-control/legacy integration against massive IT ticketing bottlenecks", "Contrasts Dynamic zero-touch self-service velocity against high risk of cost explosions and orphaned disks", "Mentions the necessity of CSI drivers and ResourceQuotas for managing dynamic storage safely"],
     ["Claims Static Provisioning means the hard drive is physically welded to the server rack"]),

    ("B67_5_20", "implement", "medium", "implement", ["Platform Engineering", "GitOps"],
     "Your Platform team adopts GitOps (using ArgoCD or Flux) to deploy applications to Kubernetes. A senior developer bypasses the Git repository entirely, runs kubectl edit deployment/my-app, and manually increases the replica count from 3 to 10 to handle a traffic spike. What happens 3 minutes later, and how does GitOps fundamentally enforce 'Configuration as Truth'?",
     "Three minutes later (or sooner), the GitOps controller (ArgoCD/Flux) running inside the cluster will automatically terminate the 7 extra pods and scale the deployment back down to 3 replicas. GitOps fundamentally enforces 'Configuration as Truth' via continuous reconciliation. The GitOps controller constantly compares the live state of the Kubernetes cluster against the declarative state stored in the Git repository. Because the Git repository still says replicas: 3, the controller detects the developer's manual kubectl edit as 'Configuration Drift'. It immediately acts to correct the drift, forcefully overwriting the live cluster state to perfectly match the Git repository. To scale the application, the developer *must* submit a Pull Request changing the Git repository; Git is the only acceptable interface to the cluster.",
     ["Predicts the GitOps controller will aggressively overwrite the manual scaling change", "Explains continuous reconciliation comparing live cluster state to the declarative Git state", "Highlights the fundamental GitOps rule: Git is the sole source of truth and exclusively drives mutations"],
     ["Suggests the developer's computer will crash because they bypassed the firewall"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 5).")
    
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
    print("POST-BATCH AUDIT PART 5")
    print("========================================")
    print(f"Batch: 67 Part 5")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
