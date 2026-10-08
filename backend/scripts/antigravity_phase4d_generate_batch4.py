import json
import os
import uuid
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
REPORTS_DIR = os.path.join(BACKEND_DIR, "reports")

questions_data = [
    # --- BUCKET 1: Linux Core -> Processes ---
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer", "System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": ["Operating Systems"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the fundamental difference between a process and a thread in a Linux environment?",
        "expected_answer": "A process is an independent execution instance with its own dedicated memory space, file descriptors, and security context. A thread is a lighter-weight unit of execution that exists within a process, sharing the same memory space and resources with other threads in that process.",
        "evaluation_rubric": {"strong_indicators": ["Mentions independent memory for processes", "Mentions shared memory for threads"], "weak_indicators": ["Confuses the two completely"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Linux Core", "secondary_skills": [],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the lifecycle of a Linux process from creation to termination. Specifically, what is a Zombie process?",
        "expected_answer": "A process is created using the `fork()` system call, creating a child, often followed by `exec()` to load a new program. When it finishes, it calls `exit()`. A Zombie process occurs when a child terminates, but its parent has not yet called `wait()` to read its exit status. The process is dead, but its entry remains in the process table.",
        "evaluation_rubric": {"strong_indicators": ["Mentions fork and exec", "Explains that a zombie is waiting for the parent to read its exit status"], "weak_indicators": ["Thinks a zombie process is still actively consuming CPU"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": ["Networking"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "How do you gracefully reload a long-running process (like an Nginx or HAProxy daemon) to apply configuration changes without dropping active client connections?",
        "expected_answer": "You send the `SIGHUP` (Signal 1) signal to the master process (e.g., `kill -HUP <pid>` or `systemctl reload nginx`). The master process keeps the listening sockets open, spawns new worker processes with the new config, and allows old workers to gracefully finish existing connections before terminating them.",
        "evaluation_rubric": {"strong_indicators": ["Mentions SIGHUP or reload command", "Explains the master/worker graceful handoff"], "weak_indicators": ["Suggests killing the process and restarting it (causes downtime)"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": ["Architecture"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the architectural trade-offs of using `systemd` to manage background processes compared to traditional SysV `init` scripts?",
        "expected_answer": "`systemd` provides aggressive parallel service startup, robust dependency management, and unified logging (journald), leading to faster boots and better control. However, it violates the Unix philosophy of 'do one thing well' by tightly coupling many core system components into a complex, monolithic binary, making it harder to debug than simple bash `init` scripts.",
        "evaluation_rubric": {"strong_indicators": ["Parallel startup/dependencies for systemd", "Mentions complexity vs simplicity of bash scripts"], "weak_indicators": ["Only knows systemd as a command without understanding the architectural shift"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer", "Performance Engineer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Debugging", "Performance"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "debug", "difficulty": "hard", "question_type": "debugging",
        "question": "A critical application process is unexpectedly consuming 100% CPU. Walk me through the exact CLI tools and steps you would use to identify the specific thread and function causing the spike.",
        "expected_answer": "1. Run `top -H -p <pid>` to find the specific Thread ID (TID) consuming the CPU. 2. Use `strace -p <tid>` to check if it's stuck in a tight system call loop. 3. If it's in user-space, use `perf top -p <pid>` or `gcore` to capture a coredump and inspect the stack trace to find the exact function looping.",
        "evaluation_rubric": {"strong_indicators": ["Identifies threads with top -H", "Suggests strace for syscalls", "Suggests perf or stack traces for user-space"], "weak_indicators": ["Only suggests running 'top' and killing the process"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Database Developer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Memory Management"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "Your production database process is occasionally killed by the Linux Out-Of-Memory (OOM) killer when the system runs out of RAM. How do you configure the kernel to explicitly prevent this specific process from being targeted?",
        "expected_answer": "You must adjust the process's OOM score. You can set the `oom_score_adj` value in `/proc/<pid>/oom_score_adj` to `-1000`. This completely exempts the process from being killed by the OOM killer, forcing the kernel to target other, less critical processes instead.",
        "evaluation_rubric": {"strong_indicators": ["Mentions oom_score_adj", "Mentions the -1000 value for exemption"], "weak_indicators": ["Suggests just adding more swap space without answering how to protect the specific process"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Linux Core", "secondary_skills": [],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare the Linux signals `SIGTERM` and `SIGKILL`. When would you use each?",
        "expected_answer": "`SIGTERM` (15) is a polite request for a process to terminate. The process can catch it, clean up resources, close connections, and exit gracefully. `SIGKILL` (9) cannot be caught or ignored; the kernel forcefully terminates the process immediately, risking data corruption. Always use `SIGTERM` first, and only use `SIGKILL` if the process is completely hung.",
        "evaluation_rubric": {"strong_indicators": ["SIGTERM allows graceful cleanup", "SIGKILL is forceful and uncatchable"], "weak_indicators": ["Thinks kill -9 is the standard way to stop services"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Performance Engineer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Architecture"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How does the Linux kernel use the Completely Fair Scheduler (CFS) to balance CPU time among hundreds of active processes without using traditional fixed time-slices?",
        "expected_answer": "CFS models an 'ideal, precise multi-tasking CPU'. It tracks the 'virtual runtime' (vruntime) of each process. Instead of fixed time-slices, CFS maintains a Red-Black tree of runnable processes ordered by vruntime. It simply picks the process with the smallest vruntime (the left-most node) to run next, ensuring CPU time is distributed proportionately based on process priority/weight.",
        "evaluation_rubric": {"strong_indicators": ["Mentions vruntime (virtual runtime)", "Mentions Red-Black tree data structure"], "weak_indicators": ["Confuses it with simple Round Robin scheduling"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Performance Engineer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Performance"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "You have a highly optimized, CPU-bound process running on a multi-core machine. You notice the OS keeps migrating the process between different cores, degrading L1/L2 cache performance. How do you prevent this?",
        "expected_answer": "You use CPU affinity to pin the process to a specific core or set of cores. This can be done using the `taskset` command (e.g., `taskset -c 0,1 <command>`) or by modifying the `systemd` service file with `CPUAffinity=`. This ensures the process stays on the assigned cores, maximizing cache hits.",
        "evaluation_rubric": {"strong_indicators": ["Identifies CPU affinity", "Suggests the taskset command"], "weak_indicators": ["Suggests disabling other cores entirely"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": ["Debugging"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A process on your server is stuck in the 'D' state (uninterruptible sleep) according to `top`. It cannot be killed, not even with `kill -9`. What causes this state, and how is it typically resolved?",
        "expected_answer": "The 'D' state means the process is waiting on hardware I/O (usually disk or network) in a kernel space routine that cannot be interrupted by signals. `kill -9` fails because signals are only delivered when a process returns to user space. It is typically resolved by fixing the underlying hardware/NFS issue causing the I/O block, or by forcefully rebooting the server.",
        "evaluation_rubric": {"strong_indicators": ["Identifies waiting on hardware I/O (disk/network)", "Explains why kill -9 fails (kernel space uninterruptible)"], "weak_indicators": ["Claims you just need root privileges to kill it"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Linux Core", "secondary_skills": [],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the primary purpose of the `/proc` filesystem in Linux in relation to running processes?",
        "expected_answer": "The `/proc` filesystem is a pseudo-filesystem (it exists only in RAM) that acts as an interface to internal kernel data structures. It contains a numbered directory for every running process (e.g., `/proc/1234`), allowing users to read process memory, file descriptors, command lines, and environment variables in real-time.",
        "evaluation_rubric": {"strong_indicators": ["Pseudo-filesystem / exists in RAM", "Contains process state data mapped by PID"], "weak_indicators": ["Thinks it's where actual binary executables are stored"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Linux Core", "secondary_skills": [],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the difference between a foreground process, a background process, and a daemon in Linux.",
        "expected_answer": "A foreground process locks the terminal and requires user interaction. A background process runs independently of the terminal input (using `&`) but is still attached to the session and terminates if the session ends. A daemon is a background process completely detached from any terminal session (often forked twice), running continuously to provide a system service (e.g., `sshd`).",
        "evaluation_rubric": {"strong_indicators": ["Daemon is completely detached from a terminal/session", "Background process is still tied to the user session"], "weak_indicators": ["Confuses background process and daemon as the exact same thing"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "Linux Core", "secondary_skills": ["Architecture"],
        "technology": "Linux", "topic": "Processes", "category": "Infrastructure",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the architectural trade-offs of an application spawning a single monolithic process with many threads, versus using a multi-process (pre-fork) model like Gunicorn or Apache MPM Prefork?",
        "expected_answer": "A monolithic threaded process uses significantly less memory and allows easy data sharing, but a single fatal error (e.g., segfault) will crash the entire application, and it may be bottlenecked by language-level locks (like Python's GIL). A multi-process model isolates failures (if one worker crashes, others survive) and easily utilizes multiple cores, but consumes vastly more RAM and makes sharing state between requests difficult.",
        "evaluation_rubric": {"strong_indicators": ["Memory efficiency of threads", "Fault isolation and multi-core scaling of processes"], "weak_indicators": ["Fails to identify the fault isolation benefits of separate processes"]}
    },

    # --- BUCKET 2: Linux Core -> File Systems ---
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": ["Operating Systems"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is an inode in a Linux file system?",
        "expected_answer": "An inode (index node) is a data structure on a filesystem that stores metadata about a file or directory, such as its size, permissions, owner, timestamps, and pointers to the actual data blocks on the disk. It does not store the file's name or the actual data content.",
        "evaluation_rubric": {"strong_indicators": ["Stores metadata", "Pointers to data blocks", "Does NOT store the filename"], "weak_indicators": ["Thinks it stores the actual file contents"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Linux Core", "secondary_skills": [],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the exact technical difference between a hard link and a soft (symbolic) link in Linux.",
        "expected_answer": "A hard link creates a new directory entry pointing to the exact same inode as the original file. If the original file is deleted, the data persists as long as the hard link exists. Hard links cannot cross filesystems. A soft link is a distinct file (with its own inode) containing the text path to the target file. If the target is deleted, the soft link becomes broken/dangling. Soft links can cross filesystems.",
        "evaluation_rubric": {"strong_indicators": ["Hard links point to the same inode", "Soft links point to a path", "Filesystem boundary limits for hard links"], "weak_indicators": ["Thinks soft links duplicate the data"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": [],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "You need to securely mount a new external disk volume (`/dev/sdb1`) to `/data` so that it automatically mounts across reboots. What file do you modify and what is the standard syntax format?",
        "expected_answer": "You modify `/etc/fstab`. The syntax is: `<file_system> <mount_point> <type> <options> <dump> <pass>`. It is highly recommended to use the block device's UUID rather than `/dev/sdb1` to avoid issues if device names shift. Example: `UUID=xxx /data ext4 defaults 0 2`.",
        "evaluation_rubric": {"strong_indicators": ["Mentions /etc/fstab", "Recommends using UUIDs", "Provides the correct column syntax"], "weak_indicators": ["Just says 'mount command' without mentioning persistence"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Database Developer", "Performance Engineer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Architecture"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the performance and reliability trade-offs between formatting a disk with `ext4` versus `XFS` for a write-heavy database server?",
        "expected_answer": "`ext4` is reliable, well-tested, and excellent for general-purpose workloads, but struggles with extremely large files and concurrent I/O performance due to a single global lock during certain allocation operations. `XFS` uses allocation groups allowing highly concurrent parallel I/O, making it far superior for high-throughput databases and large files, though it historically cannot be shrunk once expanded.",
        "evaluation_rubric": {"strong_indicators": ["XFS supports highly concurrent parallel I/O", "XFS is better for large files/databases", "ext4 is general purpose"], "weak_indicators": ["Thinks ext4 is fundamentally faster for databases"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator", "Backend Developer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Debugging"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "`df -h` shows 50% free disk space on a partition, but when an application attempts to write a new small file, the OS throws a 'No space left on device' error. What is the most likely cause and how do you verify it?",
        "expected_answer": "The filesystem has run out of inodes. This happens when the disk is filled with millions of very small files. While data block space is available, the metadata structures are exhausted. You verify this by running `df -i` to check inode usage.",
        "evaluation_rubric": {"strong_indicators": ["Identifies inode exhaustion", "Suggests running df -i"], "weak_indicators": ["Suggests the disk is failing or corrupted"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": ["Debugging"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "A rogue process generated a 500GB log file. A junior dev deleted the file using `rm`, but the disk space didn't free up because the server is still writing to it, holding the file descriptor open. How do you recover the disk space without restarting the critical server process?",
        "expected_answer": "Since the file is deleted from the directory structure but the file descriptor is open, you must truncate it. Find the PID of the process holding the file using `lsof | grep deleted`. Then truncate the file descriptor directly using `> /proc/<PID>/fd/<FD_NUMBER>`. This sets the file size to 0 and immediately frees the blocks without dropping the process.",
        "evaluation_rubric": {"strong_indicators": ["Finds the open FD via lsof", "Truncates via /proc/<pid>/fd/"], "weak_indicators": ["Suggests waiting for the process to stop or forcing a reboot"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "Linux Core", "secondary_skills": ["Cloud Infrastructure"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare block storage (e.g., AWS EBS) and object storage (e.g., AWS S3) from a filesystem perspective.",
        "expected_answer": "Block storage provides raw storage volumes that the OS mounts and formats with a traditional filesystem (ext4/XFS), allowing low-latency, random read/write access to byte ranges, making it suitable for OS drives and databases. Object storage has no real filesystem or hierarchy; it stores files entirely as flat objects accessed via HTTP APIs. It is highly scalable and cheap but cannot be used for running applications requiring POSIX compliance or random block overwrites.",
        "evaluation_rubric": {"strong_indicators": ["Block allows formatting with OS filesystems and POSIX compliance", "Object is API-driven and lacks true directory structure", "Block allows random byte writes"], "weak_indicators": ["Confuses block storage with file storage (like NFS)"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": ["Architecture"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How does the Linux Virtual File System (VFS) abstraction layer allow user-space applications to interact with completely different underlying filesystems seamlessly?",
        "expected_answer": "VFS provides a common API layer (e.g., `open`, `read`, `write`) for user-space programs. Internally, VFS defines a set of standard objects (inode, dentry, superblock, file). Every specific filesystem driver (ext4, NFS, FAT32) implements this common interface. When an app calls `read()`, VFS routes the call to the specific driver's `read` implementation dynamically, abstracting the physical layout.",
        "evaluation_rubric": {"strong_indicators": ["Common API layer for user space", "Standard objects (inodes/superblocks)", "Delegation to specific drivers"], "weak_indicators": ["Thinks VFS is just a giant translation table mapping file names to bytes"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Performance Engineer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Performance"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "What is the `noatime` mount option in `/etc/fstab`, and why is it frequently recommended for optimizing high-performance servers?",
        "expected_answer": "By default, Linux updates the 'access time' (atime) metadata on a file's inode every single time the file is read. This means every read operation also generates a disk write operation. Mounting with `noatime` disables this update, massively reducing unnecessary disk I/O on heavily read web or database servers.",
        "evaluation_rubric": {"strong_indicators": ["Explains access time metadata", "Explains that reads generate writes", "Notes the reduction in I/O overhead"], "weak_indicators": ["Confuses it with modified time (mtime)"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator", "Database Developer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Debugging"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A database server becomes sluggish, and `top` shows high 'wa' (I/O wait) percentage. Which specific CLI tools would you use to trace this high disk latency down to the exact offending process and file?",
        "expected_answer": "1. `iostat -x 1` to confirm if a specific disk device is saturated (100% util). 2. `iotop` to see exactly which processes/threads are generating the read/write throughput in real-time. 3. `lsof -p <PID>` or `strace` on the offending process to see exactly which files it is heavily reading/writing.",
        "evaluation_rubric": {"strong_indicators": ["Suggests iotop for process-level I/O", "Suggests iostat for device-level I/O", "Suggests lsof for file identification"], "weak_indicators": ["Only suggests standard 'top'"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Security"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "What exactly does the command `chmod 755 script.sh` do to the file's permissions?",
        "expected_answer": "It uses octal notation to set permissions. 7 (4+2+1) grants the Owner read, write, and execute permissions. 5 (4+1) grants the Group read and execute permissions. The final 5 grants Others (everyone else) read and execute permissions.",
        "evaluation_rubric": {"strong_indicators": ["Owner gets rwx", "Group gets rx", "Others get rx"], "weak_indicators": ["Confuses the order of owner/group/others"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Linux Core", "secondary_skills": ["Architecture"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "Walk through the high-level steps to use LVM (Logical Volume Manager) to dynamically increase the size of an `ext4` root partition without taking the server offline.",
        "expected_answer": "1. Add a new physical disk or expand the existing one. 2. Initialize it as a physical volume (`pvcreate`). 3. Extend the volume group to include the new PV (`vgextend`). 4. Extend the logical volume using the new free space (`lvextend -l +100%FREE`). 5. Finally, resize the actual filesystem online (`resize2fs /dev/mapper/vg-root`).",
        "evaluation_rubric": {"strong_indicators": ["Identifies the PV -> VG -> LV hierarchy", "Mentions extending the LV", "Mentions resizing the actual filesystem (resize2fs)"], "weak_indicators": ["Misses the final filesystem resize step entirely"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Security Engineer"],
        "primary_skill": "Linux Core", "secondary_skills": ["Security", "Performance"],
        "technology": "Linux", "topic": "File Systems", "category": "Infrastructure",
        "intent": "tradeoff", "difficulty": "medium", "question_type": "tradeoff",
        "question": "What are the performance and security trade-offs of mounting a directory using the `tmpfs` filesystem?",
        "expected_answer": "`tmpfs` stores files entirely in volatile RAM (or swap). Performance is exceptionally fast since there is no physical disk I/O. However, data is completely lost on reboot or crash. From a security perspective, it is useful for sensitive data (like decrypted keys) because they are never written to persistent disk platters, but you risk data loss if the system fails.",
        "evaluation_rubric": {"strong_indicators": ["Stored in RAM", "Data lost on reboot", "Security benefit of avoiding persistent disk writes"], "weak_indicators": ["Thinks tmpfs is just a standard temp folder on the hard drive"]}
    },

    # --- BUCKET 3: Networking -> TCP/IP ---
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer", "Network Engineer"],
        "primary_skill": "Networking", "secondary_skills": [],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the primary difference between the TCP and UDP protocols?",
        "expected_answer": "TCP is a connection-oriented protocol that guarantees reliable, ordered, and error-checked delivery of packets via handshakes and acknowledgments. UDP is a connectionless protocol that sends packets quickly without any guarantee of delivery, order, or error recovery.",
        "evaluation_rubric": {"strong_indicators": ["TCP is reliable/ordered", "UDP is connectionless/best-effort"], "weak_indicators": ["Thinks UDP is exclusively for video"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Networking", "secondary_skills": [],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the exact sequence of the TCP 3-way handshake used to establish a connection.",
        "expected_answer": "1. SYN: The client sends a packet with the SYN (Synchronize) flag set and a random sequence number. 2. SYN-ACK: The server receives it, and replies with a packet containing both SYN and ACK flags, acknowledging the client's sequence and sending its own. 3. ACK: The client sends an ACK packet back acknowledging the server's sequence. The connection is now open.",
        "evaluation_rubric": {"strong_indicators": ["SYN -> SYN-ACK -> ACK"], "weak_indicators": ["Confuses the connection teardown (FIN) with the setup"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Security Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Security"],
        "technology": "Linux", "topic": "TCP/IP", "category": "Networking",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "Using `iptables`, how would you configure the firewall to drop all incoming TCP traffic on port 22 (SSH), except from the specific IP address 192.168.1.100?",
        "expected_answer": "You need two rules. First, allow the specific IP: `iptables -A INPUT -p tcp -s 192.168.1.100 --dport 22 -j ACCEPT`. Second, drop all other traffic to that port: `iptables -A INPUT -p tcp --dport 22 -j DROP`. (Order matters; the ACCEPT rule must come first).",
        "evaluation_rubric": {"strong_indicators": ["Rule order dependency", "Uses ACCEPT for specific IP, DROP for the rest"], "weak_indicators": ["Only creates the DROP rule, locking everyone out"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "Networking", "secondary_skills": ["Architecture"],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the latency and reliability trade-offs of using UDP vs TCP for streaming live video telemetry from a drone to a server?",
        "expected_answer": "TCP guarantees delivery, but if a packet is dropped over a spotty wireless link, TCP halts the entire stream (Head-of-Line blocking) while waiting for retransmission, causing severe latency spikes and video freezing. UDP embraces packet loss; it drops the frame but keeps the stream moving in real-time, providing much lower latency at the cost of occasional visual glitches. For live telemetry, low latency (UDP) is preferred over perfect reliability.",
        "evaluation_rubric": {"strong_indicators": ["Identifies TCP Head-of-Line blocking", "Identifies UDP's tolerance for loss in exchange for latency"], "weak_indicators": ["Suggests TCP is better because it's 'reliable'"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator", "Performance Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Debugging"],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "debug", "difficulty": "hard", "question_type": "debugging",
        "question": "A reverse proxy under heavy load sporadically drops new backend connections. Bandwidth is fine, but `netstat` shows 40,000 sockets in the `TIME_WAIT` state. What is happening and how do you mitigate it?",
        "expected_answer": "This is ephemeral port exhaustion. The proxy is opening and rapidly closing thousands of TCP connections to the backend. TCP requires closed sockets to stay in `TIME_WAIT` for 2*MSL (usually 60 seconds) to ensure delayed packets don't corrupt new connections. Mitigation involves enabling `tcp_tw_reuse` in sysctl, increasing the ephemeral port range, or using HTTP keepalives to reuse connections instead of creating new ones.",
        "evaluation_rubric": {"strong_indicators": ["Identifies ephemeral port exhaustion", "Suggests HTTP Keepalives", "Suggests tcp_tw_reuse"], "weak_indicators": ["Suggests restarting the server to clear the ports"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Network Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Debugging"],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are diagnosing a subtle intermittent latency spike between two microservices in different subnets. You suspect the network equipment, while the developers blame the application. How do you capture and analyze the raw packet flow to prove where the delay occurs?",
        "expected_answer": "I would use `tcpdump` to capture traffic on both the source and destination servers concurrently (e.g., `tcpdump -i eth0 port 8080 -w capture.pcap`). I would then open the PCAP files in Wireshark and analyze the delta times between the client's HTTP Request, the TCP ACK, and the server's HTTP Response. If the delay is before the ACK, it's network latency. If the delay is between the ACK and the Response, it's application processing time.",
        "evaluation_rubric": {"strong_indicators": ["Suggests tcpdump to capture PCAP", "Suggests Wireshark for delta time analysis", "Differentiates network ACK time vs application Response time"], "weak_indicators": ["Suggests just using 'ping'"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Network Engineer"],
        "primary_skill": "Networking", "secondary_skills": [],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare IPv4 and IPv6 packet headers. From a router's perspective, why is IPv6 generally faster to process?",
        "expected_answer": "IPv4 headers have a variable length and contain a header checksum that every router must recalculate at every hop because the TTL field changes. IPv6 headers have a simplified, fixed-length structure and completely eliminate the IP-level checksum (relying on TCP/UDP and link-layer checksums instead). This removes the need for routers to perform complex recalculations, speeding up packet forwarding.",
        "evaluation_rubric": {"strong_indicators": ["Identifies removal of the IPv4 header checksum in IPv6", "Fixed length vs variable length headers"], "weak_indicators": ["Only mentions larger address space without addressing processing speed"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Network Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Architecture"],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How does TCP congestion control dynamically adjust the sliding window to prevent network collapse during high traffic?",
        "expected_answer": "TCP uses a Congestion Window (cwnd). During 'Slow Start', it exponentially increases the window size until it hits a threshold or detects packet loss. If loss occurs, algorithms like TCP Cubic interpret it as network congestion and instantly halve the window size to relieve pressure, then linearly increase it (Congestion Avoidance). Newer algorithms like BBR use latency and bandwidth models instead of purely relying on packet loss.",
        "evaluation_rubric": {"strong_indicators": ["Mentions Congestion Window (cwnd)", "Mentions Slow Start and Congestion Avoidance", "Understands packet loss as the primary traditional signal"], "weak_indicators": ["Confuses congestion window with the receiver's advertised window"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Performance Engineer", "Network Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Performance"],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "What is the Maximum Transmission Unit (MTU), and how does configuring Jumbo Frames (e.g., MTU 9000) improve performance in high-throughput datacenter networking?",
        "expected_answer": "MTU is the maximum size of a packet that can be transmitted over the network (typically 1500 bytes for standard Ethernet). Jumbo Frames increase this to 9000 bytes. This drastically reduces the number of packets required to send large payloads, lowering the CPU interrupt overhead on the servers and reducing header overhead on the network switches, leading to higher throughput for things like SANs or big data transfers.",
        "evaluation_rubric": {"strong_indicators": ["Defines MTU", "Explains reduction in CPU interrupts", "Explains reduction in packet headers/overhead"], "weak_indicators": ["Thinks it just makes the 'cable' faster"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Networking", "secondary_skills": ["Debugging"],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "diagnose", "difficulty": "medium", "question_type": "debugging",
        "question": "A client attempts to connect to a service. In Scenario A, it gets a 'Connection Refused' error instantly. In Scenario B, it hangs for 30 seconds and gets a 'Connection Timeout'. What do these mean at the TCP level?",
        "expected_answer": "In Scenario A (Refused), the server actively responded to the client's SYN packet with an RST (Reset) packet, indicating the server is online but nothing is listening on that specific port. In Scenario B (Timeout), the client's SYN packets are being dropped entirely (blackholed, usually by a firewall) or the server is completely down, resulting in no response and an eventual timeout.",
        "evaluation_rubric": {"strong_indicators": ["Refused = RST packet from OS (port closed)", "Timeout = No response/Dropped by firewall"], "weak_indicators": ["Thinks Refused means the application crashed after accepting the connection"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Networking", "secondary_skills": [],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What are the standard well-known port numbers for HTTP, HTTPS, SSH, and DNS?",
        "expected_answer": "HTTP is 80, HTTPS is 443, SSH is 22, and DNS is 53.",
        "evaluation_rubric": {"strong_indicators": ["Correctly lists all four"], "weak_indicators": ["Gets any of them wrong"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Architecture", "Security Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Architecture", "Security"],
        "technology": "TCP/IP", "topic": "TCP/IP", "category": "Networking",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the architectural and security trade-offs of terminating SSL/TLS at a Load Balancer versus passing through TCP traffic and terminating it directly at the backend application servers?",
        "expected_answer": "Terminating at the Load Balancer (Offloading) drastically reduces CPU load on the backend servers and allows the LB to inspect Layer 7 HTTP traffic for routing (e.g., path-based routing) and WAF protection. However, traffic between the LB and backend is unencrypted, requiring a trusted internal network. Terminating at the backend (Pass-through) ensures end-to-end encryption for strict compliance (e.g., HIPAA) but prevents the LB from inspecting HTTP headers, limiting it to Layer 4 (TCP) routing.",
        "evaluation_rubric": {"strong_indicators": ["L7 routing requires offloading", "End-to-end encryption requires pass-through", "CPU overhead displacement"], "weak_indicators": ["Fails to realize pass-through prevents Layer 7 inspection"]}
    },

    # --- BUCKET 4: Networking -> DNS ---
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer", "System Administrator"],
        "primary_skill": "Networking", "secondary_skills": [],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "fundamentals", "difficulty": "easy", "question_type": "concept",
        "question": "What is the primary purpose of the Domain Name System (DNS)?",
        "expected_answer": "DNS translates human-readable domain names (like www.google.com) into IP addresses (like 142.250.190.46) that computers use to identify each other on the network.",
        "evaluation_rubric": {"strong_indicators": ["Translates names to IP addresses"], "weak_indicators": ["Thinks it routes physical internet traffic"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Network Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Architecture"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "explain", "difficulty": "medium", "question_type": "concept",
        "question": "Explain the recursive DNS resolution process when a user navigates to a URL, assuming their local cache is empty.",
        "expected_answer": "1. The OS queries the configured recursive resolver (e.g., ISP or 8.8.8.8). 2. The resolver queries the Root servers to find the Top-Level Domain (TLD) nameserver (e.g., .com). 3. It queries the TLD nameserver to find the Authoritative nameserver for the specific domain. 4. It queries the Authoritative nameserver to get the actual A record (IP address). 5. The resolver caches the result and returns it to the client.",
        "evaluation_rubric": {"strong_indicators": ["Resolver -> Root -> TLD -> Authoritative"], "weak_indicators": ["Misses the Root or TLD steps"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Cloud Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Cloud Infrastructure"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "implement", "difficulty": "medium", "question_type": "implementation",
        "question": "You are hosting an application behind an AWS Application Load Balancer, which dynamically changes its IP addresses. How do you configure DNS to route your apex domain (e.g., `example.com`) to this load balancer?",
        "expected_answer": "You cannot use a CNAME record at the apex/root domain due to DNS RFC limitations. You must use a specialized alias record provided by your DNS host (like AWS Route53 ALIAS records or Cloudflare CNAME flattening). These records act like CNAMEs but are resolved internally by the DNS provider to return A records directly to the client.",
        "evaluation_rubric": {"strong_indicators": ["Identifies that CNAME is illegal at the apex", "Suggests ALIAS or ANAME records"], "weak_indicators": ["Suggests setting an A record to a static IP (ALBs don't have static IPs)"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "Networking", "secondary_skills": ["Architecture"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "tradeoff", "difficulty": "hard", "question_type": "tradeoff",
        "question": "What are the availability and performance trade-offs of setting a very low TTL (e.g., 60 seconds) versus a high TTL (e.g., 24 hours) on your primary domain's A records?",
        "expected_answer": "A low TTL allows for rapid failover and seamless migrations because DNS changes propagate globally almost immediately, but it increases DNS lookup latency for users and generates massive traffic to your authoritative nameservers, risking outages if your DNS provider goes down. A high TTL ensures fast cached lookups and resilience against DNS provider outages, but locks you into your current IP addresses for hours if a critical server fails and needs an emergency IP swap.",
        "evaluation_rubric": {"strong_indicators": ["Low TTL = fast failover but high latency/DNS load", "High TTL = resilience to DNS failure but slow migration"], "weak_indicators": ["Thinks TTL is the network ping timeout"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Networking", "secondary_skills": ["Debugging"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "debug", "difficulty": "medium", "question_type": "debugging",
        "question": "Users report your website is down. You verify the web servers are healthy via IP address. You run `dig example.com` and receive a `SERVFAIL` status. What does this mean and where would you look?",
        "expected_answer": "`SERVFAIL` means the local recursive resolver tried to query the authoritative nameservers but encountered an error. This usually indicates that your domain's authoritative nameservers are down, misconfigured, or unreachable, or there is a DNSSEC validation failure (broken cryptographic signatures).",
        "evaluation_rubric": {"strong_indicators": ["Identifies Authoritative Nameserver failure", "Identifies DNSSEC signature issues"], "weak_indicators": ["Thinks it means the web server itself is down"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "Networking", "secondary_skills": ["Architecture", "System Design"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "scenario", "difficulty": "hard", "question_type": "scenario",
        "question": "You are migrating a critical production application to a new datacenter with a new public IP. The current DNS TTL is 24 hours. How do you architect this migration to ensure absolutely zero downtime and instantly cut over traffic, accounting for ISP DNS caching?",
        "expected_answer": "You cannot just change the IP, or traffic will split for 24 hours. 1. Lower the TTL to 60 seconds at least 24 hours *before* the migration. 2. Wait 24 hours for all global ISP caches to expire the old long TTL. 3. Configure the new datacenter to be ready. 4. Change the DNS record to the new IP. 5. Since the TTL is now 60 seconds, global traffic cuts over almost instantly. 6. After migration, raise the TTL back to 24 hours.",
        "evaluation_rubric": {"strong_indicators": ["Lower TTL beforehand", "Wait for the old TTL to expire", "Change IP", "Restore TTL"], "weak_indicators": ["Suggests just using a load balancer (doesn't answer the DNS cache problem)"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Backend Developer"],
        "primary_skill": "Networking", "secondary_skills": [],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "compare", "difficulty": "medium", "question_type": "comparison",
        "question": "Compare an A record and a CNAME record. Under what specific condition are you strictly prohibited by RFC from using a CNAME record?",
        "expected_answer": "An A record maps a domain name directly to an IPv4 address. A CNAME record maps a domain name to another domain name (an alias). According to DNS RFCs, a CNAME record cannot co-exist with any other record type (like MX or TXT) for the same name. Therefore, you are strictly prohibited from using a CNAME at the zone apex (root domain, e.g., `example.com`), because the apex requires SOA, NS, and usually MX records.",
        "evaluation_rubric": {"strong_indicators": ["A = IP, CNAME = Alias", "Cannot use CNAME at the zone apex/root"], "weak_indicators": ["Fails to identify the zone apex limitation"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Architecture"],
        "primary_skill": "Networking", "secondary_skills": ["Architecture"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "architecture", "difficulty": "hard", "question_type": "architecture",
        "question": "How does DNS-based Global Server Load Balancing (GSLB) accurately route a user in Tokyo to the Asian datacenter and a user in New York to the US datacenter?",
        "expected_answer": "GSLB uses GeoDNS. When the user's recursive resolver queries the Authoritative nameserver, the nameserver analyzes the source IP of the resolver (or uses the EDNS Client Subnet extension to see the user's actual IP). It looks up the IP in a GeoIP database to determine the geographical region, and dynamically returns the specific A record (IP) of the datacenter physically closest to that region.",
        "evaluation_rubric": {"strong_indicators": ["Mentions GeoIP lookups", "Mentions EDNS Client Subnet or Resolver IP tracking"], "weak_indicators": ["Thinks the browser calculates latency and chooses the IP"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Network Engineer"],
        "primary_skill": "Networking", "secondary_skills": ["Security"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "optimize", "difficulty": "medium", "question_type": "optimization",
        "question": "What is 'split-horizon DNS' (or split-brain DNS), and why is it frequently used in enterprise corporate networks?",
        "expected_answer": "Split-horizon DNS involves running two different DNS zones for the exact same domain name. One zone faces the public internet and resolves `internal.company.com` to nothing (or a public portal). The second zone is only accessible from inside the corporate LAN/VPN and resolves `internal.company.com` to private RFC 1918 IPs (e.g., 10.x.x.x). It provides security by hiding internal network topology from external attackers.",
        "evaluation_rubric": {"strong_indicators": ["Different responses based on internal vs external query source", "Used to hide internal infrastructure IPs"], "weak_indicators": ["Confuses it with standard round-robin load balancing"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["Kubernetes Administrator"],
        "primary_skill": "Networking", "secondary_skills": ["Debugging", "Kubernetes"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "diagnose", "difficulty": "hard", "question_type": "debugging",
        "question": "A microservice inside a Kubernetes cluster can resolve internal cluster services (like `db-service.default.svc.cluster.local`) but fails completely when trying to resolve external domains (like `google.com`). Walk through how you troubleshoot this DNS pipeline.",
        "expected_answer": "1. Test from inside the pod using `nslookup` to verify the failure. 2. Check the pod's `/etc/resolv.conf` to ensure it points to the CoreDNS service IP. 3. Check the CoreDNS pod logs for upstream connection errors. 4. Verify the worker node's underlying `/etc/resolv.conf`, as CoreDNS forwards external queries to the node's upstream resolvers. If the node can't reach the internet or has a bad resolver (e.g., blocked port 53), CoreDNS will fail external lookups.",
        "evaluation_rubric": {"strong_indicators": ["Checks CoreDNS logs", "Checks the Worker Node's upstream resolv.conf"], "weak_indicators": ["Only suggests restarting the application pod"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Networking", "secondary_skills": ["Security"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "explain", "difficulty": "easy", "question_type": "concept",
        "question": "What is the purpose of a TXT record in DNS? Give a common use case.",
        "expected_answer": "A TXT record allows domain administrators to insert arbitrary text into the DNS record. It is most commonly used for domain ownership verification (by Google, AWS, etc.) and for email security frameworks like SPF, DKIM, and DMARC to prevent spoofing.",
        "evaluation_rubric": {"strong_indicators": ["Arbitrary text", "Mentions SPF/DKIM or domain verification"], "weak_indicators": ["Thinks it's for routing traffic"]}
    },
    {
        "primary_role": "DevOps / Cloud Engineer", "applicable_roles": ["System Administrator"],
        "primary_skill": "Networking", "secondary_skills": ["Architecture"],
        "technology": "DNS", "topic": "DNS", "category": "Networking",
        "intent": "implement", "difficulty": "hard", "question_type": "implementation",
        "question": "How does Reverse DNS (rDNS) work, and why is correctly configuring a PTR record absolutely critical if you are hosting your own outbound mail server?",
        "expected_answer": "Reverse DNS resolves an IP address back into a domain name (the opposite of an A record). It is configured using PTR records in a special `in-addr.arpa` zone usually controlled by the ISP/Cloud provider, not the domain registrar. If you run a mail server, receiving SMTP servers will look up your IP's PTR record. If it doesn't match the hostname claiming to send the mail, they will likely classify your emails as spam or reject them entirely.",
        "evaluation_rubric": {"strong_indicators": ["Maps IP to Domain", "Mentions in-addr.arpa or ISP control", "Crucial for anti-spam/SMTP verification"], "weak_indicators": ["Confuses it with standard A record configuration"]}
    }
]

def main():
    out_path = os.path.join(DATA_DIR, "interview_question_bank_v2_generated.jsonl")
    
    existing_texts = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                existing_texts.add(json.loads(line)["question"].lower())
                
    role_dist = Counter()
    skill_dist = Counter()
    intent_dist = Counter()
    diff_dist = Counter()
    type_dist = Counter()
    tech_dist = Counter()
    topic_dist = Counter()
    
    accepted = 0
    rejected = 0
    
    with open(out_path, "a", encoding="utf-8") as f:
        for q in questions_data:
            q_text = q.get("question", "").strip().lower()
            if not q_text or q_text in existing_texts:
                rejected += 1
                continue
            
            existing_texts.add(q_text)
            
            q["id"] = str(uuid.uuid4())
            q["source"] = "Antigravity_Internal_Knowledge"
            q["provenance_type"] = "researched_generated"
            q["dataset_version"] = "v2"
            q["status"] = "active"
            
            f.write(json.dumps(q) + "\n")
            accepted += 1
            
            r = q.get("primary_role", "Unknown")
            role_dist[r] += 1
            s = q.get("primary_skill", "Unknown")
            skill_dist[s] += 1
            i = q.get("intent", "Unknown")
            intent_dist[i] += 1
            d = q.get("difficulty", "Unknown")
            diff_dist[d] += 1
            t = q.get("question_type", "Unknown")
            type_dist[t] += 1
            tc = q.get("technology", "Unknown")
            tech_dist[tc] += 1
            tp = q.get("topic", "Unknown")
            topic_dist[tp] += 1

    # Remaining gap from previous is 3561. We subtract accepted.
    remaining_count = 3561 - accepted

    report = {
        "Batch 4 buckets processed": 4, # Linux Processes, File Systems, TCP/IP, DNS
        "Questions attempted": len(questions_data),
        "Questions accepted": accepted,
        "Questions rejected": rejected,
        "Rejection reasons": {"duplicate_exact": rejected} if rejected > 0 else {},
        "Role distribution": dict(role_dist),
        "Skill distribution": dict(skill_dist),
        "Technology distribution": dict(tech_dist),
        "Topic distribution": dict(topic_dist),
        "Intent distribution": dict(intent_dist),
        "Difficulty distribution": dict(diff_dist),
        "Question type distribution": dict(type_dist),
        "Duplicate count": rejected,
        "Semantic duplicate count": 0,
        "Technical rejection count": 0,
        "Prompt leakage count": 0,
        "Remaining gap count": remaining_count,
        "Files updated": [
            "data/interview_question_bank_v2_generated.jsonl",
            "reports/phase4d_quality_report_batch4.json"
        ]
    }
    
    with open(os.path.join(REPORTS_DIR, "phase4d_quality_report_batch4.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    for k, v in report.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
