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
    ("B67_4_1", "scenario", "hard", "scenario", ["Incident Response", "DNS"],
     "During a peak traffic event, an entire AWS region's external DNS resolution begins intermittently failing for your application servers. Pings to 8.8.8.8 work, but resolving external APIs like api.stripe.com times out for 30% of requests. You check the CoreDNS logs in Kubernetes and find them full of 'i/o timeout' errors when forwarding queries upstream. What AWS-specific VPC networking limit are you hitting, and how do you implement a local caching architecture to mitigate it?",
     "You are hitting the AWS VPC DNS Throttle limit. The AWS Route53 Resolver (typically located at 169.254.169.253 or the VPC base +2 IP) enforces a hard, un-raisable limit of 1,024 DNS packets per second per EC2 network interface (ENI). If your Kubernetes node hosts dozens of busy pods constantly querying external APIs without caching, the node's single ENI exceeds 1,024 PPS, and AWS aggressively drops the excess packets, causing intermittent 30% timeouts. To mitigate this: 1) Deploy NodeLocal DNSCache. This runs a lightweight CoreDNS DaemonSet on every single worker node. 2) The node-local cache intercepts all pod DNS queries locally. If the query is cached, it returns instantly without traversing the ENI. 3) If it's a miss, the cache upgrades the request to TCP (which is more efficient and bypasses UDP packet limitations) before forwarding it upstream, drastically reducing ENI UDP packet rates.",
     ["Diagnoses the AWS-specific ENI limit of 1024 DNS packets per second", "Identifies that high pod density without local caching saturates the ENI", "Proposes NodeLocal DNSCache DaemonSet to cache queries and optionally upgrade upstream misses to TCP"],
     ["Claims AWS Route53 is down globally and suggests switching to Google DNS"]),

    ("B67_4_2", "concept", "easy", "concept", ["Capacity Management", "Linux"],
     "What is an 'OOMKilled' event in Linux/Kubernetes, and why does the Linux kernel sometimes kill a perfectly healthy application pod instead of the one that is leaking memory?",
     "OOMKilled (Out Of Memory Killed) is an event triggered by the Linux kernel's OOM Killer when the system (or a specific cgroup) completely exhausts its available RAM. The kernel must forcefully terminate a process to prevent the entire operating system from crashing. The kernel assigns an oom_score to every process. It kills the process with the highest score. However, if a developer configures a rogue Pod *without* Kubernetes memory limits, it can consume 99% of the node's RAM. If a perfectly healthy system pod (with a large baseline memory footprint) suddenly asks for 1MB of RAM, it might trigger the global OOM event. If the kernel calculates the scores improperly, or if the rogue pod is shielded by specific kernel flags, the OOM Killer might randomly terminate the healthy system pod or another innocent application, causing collateral damage. Setting strict Kubernetes memory limits (resources.limits.memory) creates a cgroup boundary, ensuring the rogue pod only kills itself.",
     ["Defines OOMKilled as the kernel terminating processes to prevent full OS crashes", "Explains the oom_score heuristic and the potential for collateral damage", "Highlights the necessity of Kubernetes memory limits to enforce cgroup containment"],
     ["Claims OOMKilled means the CPU overheated and shut down"]),

    ("B67_4_3", "diagnose", "medium", "debugging", ["Capacity Management", "Kubernetes"],
     "You deploy a highly parallelized Java application to Kubernetes. You set the CPU requests to 2 and the CPU limits to 4. The node has 16 empty cores available. Developers complain that the application's processing latency randomly spikes from 50ms to 500ms, yet Prometheus shows the container never exceeds 3.5 cores of CPU usage. What is 'CPU Throttling' (CFS Quota), and why is it destroying the application's latency despite appearing under the limit?",
     "This is caused by the Linux Completely Fair Scheduler (CFS) Quota mechanism, which enforces Kubernetes CPU limits. A limit of 4 does not mean the container gets 4 dedicated physical cores. It means the container is granted an allowance (quota) of 400ms of CPU time per 100ms enforcement period. Because the Java app is highly parallelized (e.g., using 50 threads), it wakes up and utilizes all 16 physical cores on the node simultaneously. It burns through its entire 400ms quota in just 25 milliseconds of physical wall-clock time (16 cores * 25ms = 400ms). For the remaining 75 milliseconds of the period, the Linux kernel aggressively pauses (throttles) all threads in the container. The app literally stops executing, causing massive 500ms latency spikes, even though the aggregate CPU usage over time mathematically averages out to < 4 cores. The fix is to completely remove CPU limits (relying only on CPU requests for scheduling) to prevent CFS throttling.",
     ["Identifies Linux CFS Quota enforcing CPU limits over distinct time windows", "Explains that highly parallel apps exhaust their time quota in milliseconds, resulting in kernel pausing", "Diagnoses that Prometheus averaging hides the micro-bursts and throttling gaps", "Prescribes removing CPU limits to eliminate latency spikes"],
     ["Suggests rewriting the Java application in Python to reduce CPU usage"]),

    ("B67_4_4", "tradeoff", "hard", "tradeoff", ["Capacity Management", "Architecture"],
     "In a Kubernetes cluster, what is the architectural tradeoff of using 'Bin-Packing' scheduling (packing pods as tightly as possible onto the fewest nodes) versus 'Spread' scheduling (distributing pods evenly across all available nodes)?",
     "Bin-Packing: The scheduler actively fills up Node A to 99% capacity before placing a single pod on Node B. Advantages: Maximum cost efficiency. It leaves entire nodes completely empty, allowing the Cluster Autoscaler to safely terminate them and save massive infrastructure costs. Disadvantages: Extremely high blast radius and resource contention. If Node A crashes, you lose dozens of pods simultaneously. Furthermore, noisy-neighbor kernel contention (e.g., shared L3 cache, network IO) degrades performance. Spread Scheduling (PodTopologySpreadConstraints): The scheduler balances pods across all nodes (e.g., Node A gets 30%, Node B gets 30%). Advantages: Maximum high availability and performance isolation. A node crash only affects a small subset of the application, and hardware resources are plentiful. Disadvantages: Terrible cost efficiency. Every node is permanently 30% utilized, making it impossible for the Cluster Autoscaler to scale down any nodes, forcing you to pay for massive amounts of idle cloud capacity.",
     ["Identifies Bin-Packing advantage: high cost-efficiency enabling node scale-down", "Identifies Bin-Packing disadvantage: massive blast radius on node failure and noisy neighbors", "Identifies Spread advantage: High availability and performance isolation", "Identifies Spread disadvantage: Massive waste of money via unscalable idle capacity"],
     ["Claims Bin-Packing refers to compressing container image sizes"]),

    ("B67_4_5", "scenario", "medium", "scenario", ["Incident Response", "Security"],
     "During a production incident, an engineer discovers that an external attacker has stolen a long-lived AWS IAM Access Key and is currently using it to download data from S3. The engineer immediately deletes the IAM User in the AWS Console, but the attacker's downloads successfully continue for another 45 minutes. Why didn't deleting the IAM User instantly revoke access, and what is the correct incident response procedure?",
     "Deleting an IAM User prevents the creation of *new* sessions, but it does NOT automatically invalidate existing, active temporary sessions. If the attacker used the long-lived keys to call sts:GetSessionToken or sts:AssumeRole just before the user was deleted, they received temporary credentials (which default to 1-hour validity). These temporary credentials remain perfectly valid and authorized until their expiration timer runs out, regardless of the underlying user's deletion. The correct incident response procedure: 1) Attach an explicit DenyAll inline policy to the user (or the assumed role) immediately. IAM policy evaluations are dynamic and real-time; a DenyAll instantly blocks all active temporary sessions globally. 2) Revoke active sessions in the IAM console (which applies a time-based Deny policy). 3) *Then* delete the access keys and the user account.",
     ["Diagnoses that temporary STS sessions survive the deletion of the parent IAM user", "Explains that STS sessions enforce their own inherent 1-hour expiry timers", "Prescribes attaching an explicit DenyAll policy *first* to instantly terminate active API calls globally"],
     ["Claims AWS takes 45 minutes to sync databases across regions globally"]),

    ("B67_4_6", "concept", "easy", "concept", ["Incident Response", "Architecture"],
     "What is the purpose of an 'Error Budget' in Site Reliability Engineering, and how does it resolve the fundamental conflict between the Development team (who wants to ship features fast) and the SRE team (who wants maximum stability)?",
     "An Error Budget is the mathematically acceptable amount of unreliability a system is allowed to have over a specific timeframe (e.g., a 99.9% SLO allows for exactly 43 minutes of downtime per month). It resolves the conflict by turning reliability into a shared, objective metric. If the monthly Error Budget is healthy (e.g., only 5 minutes used), the Development team is given the green light to deploy new features, take risks, and push fast. If the Error Budget is exhausted (e.g., 45 minutes of downtime occurred), a strict organizational freeze is enacted. The Development team must stop shipping new product features and pivot 100% of their engineering effort into fixing bugs, improving tests, and restoring reliability until the budget replenishes the next month.",
     ["Defines Error Budget as the mathematical allowance for failure derived from an SLO", "Explains the mechanism of halting feature deployments when the budget is exhausted", "Highlights the alignment of incentives: dev teams self-regulate to protect their ability to ship features"],
     ["Claims Error Budget is a financial fund used to pay customers when the site goes down"]),

    ("B67_4_7", "diagnose", "medium", "debugging", ["Capacity Management", "Linux"],
     "A monolithic application writing heavily to disk suddenly crashes. You run df -h and see that the /var/log disk has 50GB of free space. However, the application continues to throw 'No space left on device' errors when trying to create new files. What hidden filesystem exhaustion has occurred, and how do you diagnose it?",
     "The system has exhausted its inode capacity, not its raw block storage capacity. An inode is a data structure on a Linux filesystem that stores metadata about a file (permissions, ownership, physical block locations). Every single file or directory created consumes exactly one inode, regardless of its size. If an application (like a poorly configured PHP session manager or a runaway logging script) creates millions of tiny 1-byte files, it will consume all available inodes before it consumes the physical gigabytes of disk space. When inodes run out, the kernel cannot allocate a new file record, resulting in the misleading 'No space left on device' error. You diagnose this by running df -i. The fix is to find the directory with millions of files and delete them.",
     ["Identifies inode exhaustion as the hidden constraint causing the error", "Explains that millions of tiny files consume inodes without consuming raw GB storage", "Prescribes the df -i command to explicitly diagnose inode usage"],
     ["Suggests the hard drive is physically corrupted and needs replacement"]),

    ("B67_4_8", "implement", "hard", "implement", ["Incident Response", "Kubernetes"],
     "A critical microservice in Kubernetes goes into a crash-loop during a major incident. The container crashes immediately upon startup, making it impossible to kubectl exec into it to read local configuration files or run diagnostic network commands. How do you use Kubernetes 'Ephemeral Containers' to successfully debug a crashing pod without altering its configuration?",
     "Historically, debugging a crashing pod was impossible without modifying the deployment to inject a sleep command, which changes the state you are trying to debug. Kubernetes Ephemeral Containers solve this. An Ephemeral Container is a temporary container dynamically injected into the exact same network and process namespace of an *already running* (or crashing) pod. Implementation: You run kubectl debug -it <pod-name> --image=busybox:latest --target=<crashing-container-name>. The API server injects the busybox container into the existing pod. Even though the primary application container is dead or crash-looping, the busybox container stays alive. Because it shares the pod's namespaces, you can freely browse the shared filesystem, read the dead container's local config files, and run network diagnostics (curl, nslookup) from the exact perspective of the failing pod, allowing non-destructive root-cause analysis.",
     ["Identifies Ephemeral Containers as dynamically injected debug tools for live pods", "Provides the exact kubectl debug command implementation", "Crucially notes that the ephemeral container shares the network/process namespace of the dead container, allowing internal filesystem/network inspection"],
     ["Suggests SSHing directly into the underlying worker node to debug it"]),

    ("B67_4_9", "scenario", "medium", "scenario", ["Capacity Management", "Kubernetes"],
     "You manage an EKS cluster using the Kubernetes Cluster Autoscaler. A massive traffic spike occurs, and HPA (Horizontal Pod Autoscaler) requests 50 new pods. The Cluster Autoscaler successfully provisions 5 new EC2 worker nodes. However, 15 minutes later, 20 of the pods are still stuck in the Pending state, and the Autoscaler refuses to provision any more nodes. What architectural misconfiguration between the Autoscaler and the cloud provider causes this scaling deadlock?",
     "This deadlock is caused by an ASG (Auto Scaling Group) Maximum Size limit constraint. The Kubernetes Cluster Autoscaler does not provision VMs directly; it manipulates the DesiredCapacity value of the underlying AWS Auto Scaling Group. If the ASG is configured in AWS with a MaxSize of 5, the Cluster Autoscaler will recognize that the group is physically full. Even though Kubernetes has 20 Pending pods desperately needing compute, the Autoscaler respects the AWS infrastructure limit and refuses to issue further scale-up commands. To fix this, you must intervene at the Infrastructure-as-Code (Terraform) layer to increase the AWS ASG max_size parameter, allowing the Cluster Autoscaler to resume provisioning VMs.",
     ["Diagnoses the AWS ASG MaxSize hard limit overriding Kubernetes pod requirements", "Explains the abstraction: Cluster Autoscaler manipulates ASG DesiredCapacity, not raw EC2 instances", "Prescribes modifying the ASG infrastructure layer via Terraform to lift the artificial ceiling"],
     ["Claims AWS ran out of computers in the datacenter"]),

    ("B67_4_10", "tradeoff", "medium", "tradeoff", ["Incident Response", "Architecture"],
     "During a massive DDoS attack or sudden viral traffic spike, what is the tradeoff of relying on 'Dynamic Auto-scaling' (spinning up new servers based on load) versus implementing aggressive 'Load Shedding' (intentionally dropping requests at the edge)?",
     "Dynamic Auto-scaling: Advantages: Attempts to serve 100% of the user traffic, preserving revenue and customer experience. Disadvantages: Scaling is fundamentally slow (VMs take minutes, containers take seconds). A sudden massive spike will crush the existing servers before the new ones can boot. Furthermore, auto-scaling during a DDoS attack is financially catastrophic, as you automatically provision and pay for infinite infrastructure to serve malicious traffic. Load Shedding: Advantages: Instantaneous survival mechanism. By configuring the API Gateway to aggressively drop 50% of requests (HTTP 503/429) when backend latency spikes, you guarantee the survival of the database and core systems. Disadvantages: You intentionally degrade the user experience for legitimate customers. However, the SRE tradeoff philosophy is that 'a system operating at 50% capacity is infinitely better than a system operating at 0% capacity.'",
     ["Contrasts the sluggishness and massive financial risk of auto-scaling against a DDoS attack", "Identifies Load Shedding as an instantaneous survival mechanism sacrificing a percentage of users to save the core", "Articulates the SRE philosophy of partial degradation over total systemic collapse"],
     ["Claims Auto-scaling happens instantly in less than 1 millisecond"]),

    ("B67_4_11", "diagnose", "hard", "debugging", ["Capacity Management", "Linux"],
     "An application node suddenly drops off the network. You reboot it and check the kernel dmesg logs, finding the error 'nf_conntrack: table full, dropping packet'. What is the nf_conntrack table, why did it cause a complete network blackout, and how do you resolve it for a high-throughput proxy server?",
     "The nf_conntrack (Netfilter Connection Tracking) table is an internal Linux kernel memory structure used by iptables and NAT to track the state of every single active TCP/UDP network connection on the machine. If a proxy server handles a massive volume of concurrent connections (or experiences a SYN flood attack), it will quickly fill the fixed-size table. Once the table is 100% full, the Linux kernel aggressively protects itself by instantaneously dropping every single new incoming and outgoing packet, resulting in a complete network blackout. To resolve this: 1) Increase the table size dynamically via sysctl (sysctl -w net.netfilter.nf_conntrack_max=1048576); 2) Reduce the timeout for idle connections (net.netfilter.nf_conntrack_tcp_timeout_established) to flush dead sockets faster; or 3) Use the NOTRACK iptables target in the raw table to bypass connection tracking entirely for specific high-volume trusted ports.",
     ["Identifies nf_conntrack as the kernel structure tracking NAT/iptables TCP connection state", "Explains that hitting the limit causes the kernel to aggressively drop all subsequent network packets", "Prescribes sysctl max expansion, timeout reduction, or NOTRACK bypass for remediation"],
     ["Suggests the error means the ethernet cable is physically disconnected"]),

    ("B67_4_12", "concept", "easy", "concept", ["Incident Response", "Architecture"],
     "What is a 'Runbook' (or Playbook) in incident response, and why is it critical to keep it simple rather than documenting complex, theoretical edge cases?",
     "A Runbook is a documented, step-by-step operational procedure designed to mitigate a specific, known failure mode (e.g., 'How to failover the primary database'). It is critical to keep it simple, actionable, and strictly focused on *mitigation* because it is executed by a panicked on-call engineer at 3:00 AM under extreme pressure. If the runbook contains 15 pages of complex theoretical architectural history or requires the engineer to make complex deductive choices, they will make a mistake. A good runbook provides exact copy-paste CLI commands, explicit expected outputs, and focuses entirely on restoring service as fast as possible, leaving the complex root-cause analysis for the post-mortem the next day.",
     ["Defines Runbook as a step-by-step mitigation procedure for known outages", "Explains the high-stress, low-cognitive-capacity reality of 3 AM on-call incidents", "Mandates simple, copy-paste executable commands focused solely on restoration, not diagnosis"],
     ["Claims a runbook is a legal contract signed by the SRE team"]),

    ("B67_4_13", "implement", "medium", "implement", ["Capacity Management", "Kubernetes"],
     "You deploy an application with Kubernetes Resource Requests set to memory: 1Gi and Limits set to memory: 1Gi. You configure a Horizontal Pod Autoscaler (HPA) to scale up when memory utilization hits 80%. Why is using Memory Utilization as an HPA scaling metric an architectural anti-pattern, especially for JVM or garbage-collected applications?",
     "Memory is a terrible scaling metric because it is fundamentally 'sticky'. A JVM application will request RAM from the operating system and hold onto it indefinitely. If the JVM reaches 85% memory, the HPA will correctly trigger a scale-up, provisioning a new pod. However, because the original JVM pod rarely releases memory back to the Linux kernel (even if it's idle), its memory usage remains at 85%. The HPA sees that the average memory across the deployment is still high, so it scales up again. And again. And again. The HPA enters a runaway scale-up loop, provisioning infinite pods until the cluster runs out of capacity, all because the idle pods refuse to drop their memory footprint. CPU or custom metrics (like HTTP Request Queues) are far safer scaling triggers.",
     ["Identifies memory 'stickiness' where JVMs hoard RAM and do not yield it to the OS during idle times", "Diagnoses the runaway scale-up loop caused by idle pods maintaining high memory metrics", "Recommends CPU or custom queue depth metrics instead of memory for HPA triggers"],
     ["Suggests the JVM will automatically shut down if it hits 80% RAM"]),

    ("B67_4_14", "scenario", "medium", "scenario", ["Incident Response", "Certificates"],
     "A critical internal API abruptly stops accepting connections at precisely 00:00:00 UTC. The load balancer returns SSL Handshake Failures. The engineer checks the TLS certificate, but it shows an expiration date 6 months in the future. What hidden certificate chain issue causes an active, valid leaf certificate to instantly fail validation?",
     "The issue is an Expired Intermediate or Root Certificate Authority (CA). During a TLS handshake, the server sends its Leaf certificate along with an Intermediate certificate to establish a chain of trust back to the client's trusted Root store. Even if the Leaf certificate is perfectly valid for another 6 months, if the Intermediate CA certificate (or the Root CA itself) expires at 00:00:00 UTC, the client's browser or SDK can no longer cryptographically verify the chain of trust. The TLS library throws an x509: certificate signed by unknown authority or handshake error and aggressively terminates the connection. The fix requires updating the server's configuration to serve a newly cross-signed intermediate certificate, or updating the client trust stores.",
     ["Diagnoses an expired Intermediate or Root CA breaking the cryptographic chain of trust", "Explains that the Leaf certificate's own expiration date is irrelevant if the parent is invalid", "Prescribes serving a new cross-signed intermediate certificate to resolve the handshake error"],
     ["Claims the server's system clock is running 6 months too fast"]),

    ("B67_4_15", "diagnose", "hard", "debugging", ["Incident Response", "Networking"],
     "An application deployed in AWS VPC A needs to communicate with a database in AWS VPC B. You establish a VPC Peering connection. You update the Route Tables in both VPCs to point to the Peering connection. However, telnet database-ip 5432 simply hangs and times out. Security Groups on both sides allow all traffic. NACLs are default. What highly specific IP architecture mistake fundamentally breaks VPC Peering and causes this silent blackholing?",
     "The silent blackholing is caused by Overlapping CIDR Blocks. If VPC A is created with the IPv4 CIDR 10.0.0.0/16 and VPC B is also created with 10.0.0.0/16 (or any overlapping subnet), VPC Peering is fundamentally impossible. When an instance in VPC A attempts to route a packet to 10.0.1.5 in VPC B, the Linux networking stack and the AWS VPC router examine the destination IP. Because 10.0.1.5 falls exactly within the VPC A local network range, the router assumes the destination is on the local network. It completely ignores the Peering route table entry and attempts to route the packet locally, dropping it when it can't find the MAC address. The only fix is to completely destroy and recreate one of the VPCs with a non-overlapping IP space (e.g., 10.1.0.0/16), or implement a complex intermediary Transit Gateway with NAT.",
     ["Diagnoses Overlapping CIDR Blocks entirely neutralizing VPC peering", "Explains that local subnets inherently take routing priority over peered route tables", "States the severe resolution: destroying and recreating the VPC with non-overlapping IP space"],
     ["Suggests the telnet command is deprecated and you must use ping"]),

    ("B67_4_16", "concept", "easy", "concept", ["Incident Response", "SRE"],
     "In the context of SRE Post-Mortems, what is 'Blameless Culture', and why is it essential for preventing future catastrophic incidents?",
     "Blameless Culture is the operational philosophy that human error is never the root cause of an incident; rather, human error is a symptom of a poorly designed system or inadequate tooling. If a developer accidentally deletes a production database by running the wrong script, a blameless post-mortem does not punish or fire the developer. Instead, it asks: 'Why did the system allow an individual to run a destructive command without safeguards? Why didn't the pipeline require secondary approval? Why wasn't the database protected by deletion-protection flags?' Punishing the engineer guarantees that the team will hide their mistakes in the future. Blamelessness ensures psychological safety, encouraging engineers to immediately report anomalies, leading to the creation of robust, automated guardrails that prevent the mistake from ever happening again.",
     ["Defines Blameless Culture as viewing human error as a symptom of systemic tooling failure, not a root cause", "Explains that punishing engineers leads to cover-ups and reduced psychological safety", "Highlights the goal: identifying missing automated guardrails to prevent future identical failures"],
     ["Claims Blameless Culture means nobody has to do any work during an incident"]),

    ("B67_4_17", "tradeoff", "medium", "tradeoff", ["Capacity Management", "Architecture"],
     "What are the tradeoffs of solving a sudden database performance bottleneck by 'Scaling Up' (Vertical Scaling - buying a bigger server with more CPU/RAM) versus 'Scaling Out' (Horizontal Scaling - sharding the data across multiple smaller servers)?",
     "Vertical Scaling (Scale Up): Advantages: Requires zero application code changes. You simply stop the database, upgrade the VM instance type, and start it back up. It handles complex ACID transactions and JOINs effortlessly. Disadvantages: Severe physical limitations (you eventually hit the largest VM size cloud providers offer) and it creates a massive Single Point of Failure (if the big box dies, the whole company goes down). Horizontal Scaling (Scale Out): Advantages: Infinite scalability and high availability. If one node dies, the others continue serving traffic. Disadvantages: Massive architectural complexity. You must completely rewrite the application logic to handle Data Sharding, cross-node distributed transactions become mathematically impossible or incredibly slow, and operational maintenance (backing up 50 nodes vs 1 node) increases exponentially.",
     ["Contrasts the immediate simplicity of Vertical Scaling with its physical hardware ceiling and Single Point of Failure risk", "Contrasts the infinite HA/scalability of Horizontal Scaling with its massive architectural complexity", "Identifies the loss of complex JOINs and distributed transaction performance in sharded architectures"],
     ["Claims Vertical Scaling is when you literally stack servers on top of each other physically"]),

    ("B67_4_18", "scenario", "medium", "scenario", ["Capacity Management", "Kubernetes"],
     "A team configures a Kubernetes PodDisruptionBudget (PDB) for a critical deployment, setting minAvailable: 10. The deployment currently has exactly 10 pods running. A DevOps engineer attempts to perform a routine kubectl drain on a worker node to perform a kernel upgrade. The drain command hangs indefinitely and the node cannot be taken offline. Why does the PDB block the operational task, and how do you resolve it?",
     "A PodDisruptionBudget (PDB) is a safety mechanism that prevents voluntary disruptions (like node drains or evictions) from dropping an application's availability below a certain threshold. Because the deployment only has 10 pods, and the PDB mandates that a minimum of 10 must be available at all times, the PDB mathematically forbids Kubernetes from terminating even a single pod. When the drain command attempts to evict a pod on that worker node, the API server rejects the request to protect the application, causing the command to hang. To resolve this, you must temporarily scale the Deployment up to 11 pods. Once the 11th pod is Ready, the PDB condition is satisfied, and the drain command will successfully evict the pod on the target node, gracefully taking it offline.",
     ["Identifies PodDisruptionBudget preventing voluntary evictions from breaching availability constraints", "Diagnoses the mathematical lock: draining a pod drops the count to 9, violating minAvailable: 10", "Prescribes scaling the deployment to 11 to satisfy the PDB before attempting the drain"],
     ["Suggests using sudo to force the drain command to run as root"]),

    ("B67_4_19", "implement", "hard", "implement", ["Incident Response", "Networking"],
     "During an incident, you discover that a compromised EC2 instance is exfiltrating gigabytes of sensitive data to a specific external IP address over an established TCP connection. You must immediately terminate this specific outbound data transfer, but you CANNOT alter AWS Security Groups, you CANNOT reboot the instance, and you CANNOT disable the network interface, because the instance is actively serving legitimate customer traffic. How do you surgically sever the malicious TCP connection using Linux OS-level tools?",
     "You must perform a surgical TCP connection termination directly at the Linux kernel level. 1) Identify the connection: Run ss -ntp | grep <malicious-ip> or netstat -antp to find the exact local port, remote port, and the PID of the malicious process handling the exfiltration. 2) Sever the connection: You can use the ss utility's kill function: ss -K dst <malicious-ip>. Alternatively, use the tcpkill utility: tcpkill -i eth0 host <malicious-ip>. tcpkill works by aggressively sniffing the network interface and injecting spoofed TCP RST (Reset) packets into the active stream. When the kernel and the remote server receive the injected RST packet, they immediately tear down the established TCP socket, instantly halting the data exfiltration while leaving all other legitimate customer connections perfectly intact.",
     ["Diagnoses the constraint of surgical connection termination without disrupting co-resident traffic", "Provides the implementation command using ss -K or tcpkill", "Explains the mechanism of injecting TCP RST (Reset) packets to force the kernel to terminate the specific socket"],
     ["Suggests pulling the physical power cord out of the server"]),

    ("B67_4_20", "diagnose", "medium", "debugging", ["Capacity Management", "Linux"],
     "A monolithic Java application starts failing intermittently. The Linux system logs (/var/log/messages) are flooded with 'Too many open files' errors. You check the server's disk space, and it is only 50% full. You check inodes, and they are fine. What specific Linux resource constraint is being violated, and how do you configure the system to permanently fix it for the Java process?",
     "The application is violating the Linux File Descriptor (ulimit) constraint. In Linux, 'everything is a file.' Every time the Java application opens a text file, creates a network socket (TCP connection), or opens a pipe, it consumes a File Descriptor. By default, Linux imposes a very strict soft limit (often 1,024) on the maximum number of file descriptors a single process can open simultaneously to prevent runaway memory consumption. If a high-throughput Java web server handles 2,000 concurrent user connections, it instantly hits this limit and crashes with 'Too many open files'. To fix this permanently: 1) Edit /etc/security/limits.conf and increase the soft and hard nofile (Number of Open Files) limits for the specific user running the Java app (e.g., javauser soft nofile 65536). 2) Ensure the systemd service file executing the app is updated with LimitNOFILE=65536 to apply the limits at startup.",
     ["Identifies File Descriptor (ulimit / nofile) exhaustion as the root constraint", "Explains that TCP sockets and network connections consume file descriptors in Linux", "Prescribes modifying /etc/security/limits.conf or systemd LimitNOFILE to permanently raise the threshold"],
     ["Suggests the error means the user has too many tabs open in their web browser"])
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
            
    print(f"Accepted {len(accepted)} / {len(Q)} questions (Part 4).")
    
    new_records = []
    for q in accepted:
        rec = {
            "primary_role": ROLE,
            "applicable_roles": ["Site Reliability Engineer", "Platform Engineer"],
            "primary_skill": q[4][0],
            "secondary_skills": q[4][1:] if len(q[4]) > 1 else [],
            "technology": "Linux/Kubernetes",
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
    print("POST-BATCH AUDIT PART 4")
    print("========================================")
    print(f"Batch: 67 Part 4")
    print(f"Target role: {ROLE}")
    print(f"Attempted: {len(Q)}")
    print(f"Accepted: {len(accepted)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Replacement count: 0")
    print(f"Cumulative total: {len(final_existing)}")
    print(f"{ROLE} total: {role_counts[ROLE]}")

if __name__ == "__main__":
    run_batch()
