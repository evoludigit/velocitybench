**[Pattern] On-Premise Debugging Reference Guide**

---

### **Overview**
The **On-Premise Debugging** pattern enables developers to diagnose, trace, and resolve issues directly on local environments (physical servers, VMs, or containers) without relying solely on centralized monitoring tools or remote debugging agents. This approach is critical for low-latency troubleshooting, regulatory compliance (e.g., GDPR, HIPAA), or scenarios where external access is restricted. By leveraging native OS tools, IDE integrations, and log-forwarding mechanisms, teams can inspect system state, process flows, and application behavior with high precision. While primarily used for backend troubleshooting, this pattern applies to frontend apps (e.g., debugging mobile apps via ADB) and hybrid architectures.

Key use cases:
- **Security audits**: Inspecting network traffic or kernel-level logs without cloud dependencies.
- **Performance bottlenecks**: Profiling CPU, memory, or disk I/O on-premise.
- **Compliance**: Debugging sensitive data without cloud exposure.

---

## **Implementation Details**

### **1. Key Components**
| **Component**               | **Description**                                                                 | **Example Tools**                          |
|-----------------------------|---------------------------------------------------------------------------------|--------------------------------------------|
| **Debugging Instrumentation** | Runtime extensions (e.g., debuggers, profilers) to capture execution state.    | `GDB`, `lldb`, `Visual Studio Debugger`    |
| **Log Forwarding**          | Tailoring and shipping logs locally for analysis (e.g., journalctl, syslog).     | `journalctl`, `syslog-ng`, `ELK Stack`    |
| **Network Probing**         | Packet inspection (e.g., tcpdump, Wireshark) or port scanning (netstat).        | `tcpdump`, `Wireshark`, `nmap`            |
| **Kernel/OS Tools**         | Low-level diagnostics (e.g., `strace`, `perf`, `vmstat`).                      | `strace`, `perf`, `htop`, `dmesg`        |
| **Container/VM Debugging**  | Debugging isolated environments (e.g., Docker logs, VM console access).         | `docker logs`, `virsh console`, `kubectl` |

---

### **2. Schema Reference**
Define a **standardized debug session workflow** with the following schema:

| **Field**               | **Type**   | **Description**                                                                 | **Example Values**                          |
|-------------------------|------------|---------------------------------------------------------------------------------|---------------------------------------------|
| `session_id`            | UUID       | Unique identifier for the debug session.                                        | `550e8400-e29b-41d4-a716-446655440000`      |
| `start_time`            | Timestamp  | When the session began (ISO 8601 format).                                       | `2023-10-15T14:30:00Z`                     |
| `end_time`              | Timestamp  | When the session concluded (nullable if ongoing).                               | `2023-10-15T15:15:00Z`                     |
| `environment`           | Enum       | Target environment (e.g., `prod`, `staging`, `dev`).                           | `prod`                                     |
| `tool_used`             | String     | Primary debugging tool deployed (e.g., `GDB`, `Wireshark`).                    | `strace`                                   |
| `issue_type`            | Enum       | Type of problem detected (e.g., `crash`, `latency`, `auth_failure`).           | `crash`                                    |
| `logs_collected`        | Array      | Paths to local logs or artifacts.                                              | `["/var/log/app/error.log", "/tmp/core.123"]` |
| `network_traffic`       | Boolean    | Whether network probes (e.g., `tcpdump`) were used.                            | `true`                                     |
| `profiling_data`        | JSON       | CPU/memory metrics (e.g., from `perf` or `top`).                               | `{"cpu_usage": 95, "memory_leaks": 2}`     |
| `resolution`            | String     | Summary of the fix applied (e.g., "patched network library").                   | "Updated JWT validation"                    |
| `severity`              | Enum       | Impact level (e.g., `critical`, `low`).                                         | `high`                                     |

**Example JSON payload:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": "2023-10-15T14:30:00Z",
  "environment": "prod",
  "tool_used": "strace",
  "issue_type": "crash",
  "logs_collected": ["/var/log/app/core.123"],
  "resolution": "Fixed memory leak in `libxyz`"
}
```

---

## **3. Query Examples**
### **A. Filtering Debug Sessions**
**Goal**: Find all `critical` severity sessions from the last 7 days using `perf`.
**SQL (PostgreSQL)**:
```sql
SELECT *
FROM debug_sessions
WHERE severity = 'critical'
  AND start_time >= NOW() - INTERVAL '7 days'
  AND tool_used = 'perf';
```

**CLI (jq)**:
```bash
jq '.[] | select(.severity == "critical" and (.tool_used == "perf"))' debug_sessions.json
```

### **B. Analyzing Log Patterns**
**Goal**: Extract all `403 Forbidden` errors from `/var/log/nginx/error.log` using `grep`.
```bash
grep "403 Forbidden" /var/log/nginx/error.log | awk '{print $1, $4}' | sort | uniq -c
```
**Output**:
```
   15 10.0.0.1
    3 192.168.1.5
```

### **C. Profiling CPU Usage with `perf`**
**Command**:
```bash
sudo perf record -g -p <PID> -- sleep 5
sudo perf script | grep "symbol"
```
**Key Metrics**:
- **`symbol`**: Function causing high CPU.
- **`__perf_event`**: Event type (e.g., `CPU_CLK_UNHALTED`).

---

## **4. Step-by-Step Workflow**
### **Phase 1: Reproduce the Issue**
1. **Isolate the environment**:
   - Recreate the issue on a VM/container with identical config (e.g., `docker run --rm -it ubuntu:latest`).
   - Use `journalctl -xe` (systemd) or `dmesg` (kernel logs) to check pre-existing state.

2. **Enable debugging tools**:
   - **Debuggers**: Attach `GDB` to a running process:
     ```bash
     gdb -p <PID>
     ```
   - **Profilers**: Capture CPU samples with `perf`:
     ```bash
     perf top -p <PID> --latency-target=5000
     ```

3. **Forward logs locally**:
   - Tail real-time logs:
     ```bash
     tail -f /var/log/syslog | grep -i "error"
     ```
   - Use `syslog-ng` to pipe logs to a local file:
     ```ini
     source s_local { file("/var/log/syslog"); };
     destination d_local { file("/tmp/debug_syslog.log"); };
     log { source(s_local); destination(d_local); };
     ```

### **Phase 2: Analyze Data**
- **Network**: Inspect packet capture (e.g., `tcpdump -i eth0 -w capture.pcap`).
  ```bash
  wireshark capture.pcap  # GUI analysis
  ```
- **Process**: Trace system calls with `strace`:
  ```bash
  strace -p <PID> -f -o /tmp/process_trace.log
  ```
- **Database**: Use `pg_dump` (PostgreSQL) or `mysqldump` for schema inspection:
  ```bash
  mysqldump -u root -p db_name > schema.sql
  ```

### **Phase 3: Resolve and Validate**
1. **Apply fixes** (e.g., patch code, update configs).
2. **Re-test locally**:
   - Use `docker exec -it <container> bash` to verify changes.
3. **Document**:
   - Update the `resolution` field in the debug session schema.
   - Commit changes with a commit message referencing the `session_id`.

---

## **5. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|--------------------------------------------------------------------------------|
| **Permission errors** (e.g., `strace`). | Run as root (`sudo`) or use `setcap` for capabilities.                       |
| **Log overload**                      | Filter logs early (e.g., `grep "ERROR"` during `tail`).                       |
| **Debugger conflicts**                | Use `--attach` (`GDB`) or `ptrace` to avoid process corruption.                |
| **VM snapshots corrupting data**.    | Take snapshots *before* debugging; use `virsh snapshot-create-as`.             |
| **Missing dependencies** (e.g., `perf`).| Install tools via package manager (e.g., `sudo apt install perf`).            |

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Distributed Tracing]** | Correlate logs across microservices using OpenTelemetry.                       | Hybrid cloud/on-premise debugging.       |
| **[Blue-Green Deployment]** | Isolate debug traffic to a secondary environment.                            | Zero-downtime debugging.                |
| **[Canary Analysis]**      | Gradually expose debug traffic to a subset of users.                           | Production-grade validation.            |
| **[Log Aggregation]**      | Centralize logs (e.g., ELK, Splunk) for cross-environment analysis.           | Multi-cloud debugging.                  |
| **[Kernel Debugging]**     | Use `ktrace` or `ftrace` for deep OS-level insights.                           | Driver/low-level software issues.       |

---

## **7. Tools Cheat Sheet**
| **Tool**       | **Purpose**                          | **Example Command**                              |
|-----------------|---------------------------------------|--------------------------------------------------|
| `GDB`           | Debug binaries.                       | `gdb ./myapp core.123`                           |
| `strace`        | Trace system calls.                   | `strace -f -p 1234 -o trace.log`                 |
| `perf`          | Profile CPU/memory.                   | `perf record -g ./myapp`                        |
| `tcpdump`       | Capture network traffic.              | `tcpdump -i eth0 -w capture.pcap`                |
| `journalctl`    | Inspect systemd logs.                 | `journalctl -u nginx --since "2023-10-15"`       |
| `netstat`/`ss`  | Check network connections.            | `ss -tulnp`                                     |
| `htop`          | Monitor processes.                    | `htop --pid <PID>`                              |
| `docker logs`   | Debug containers.                     | `docker logs --tail 50 <container>`              |

---
**Note**: Replace `<PID>`, `<container>`, and paths with actual values for your environment. For compliance, ensure logs are encrypted (e.g., `gpg`) and retained per policies.