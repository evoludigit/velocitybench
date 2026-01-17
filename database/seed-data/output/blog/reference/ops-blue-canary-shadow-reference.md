# **[Pattern] Blue Canary Shadow Patterns Reference Guide**
*Detecting and correlating subtle anomalies in behavioral sequences for advanced threat hunting*

---

## **1. Overview**
Blue Canary Shadow Patterns are a set of **behavioral attack chain heuristics** designed to detect adversaries exploiting lateral movement or privilege escalation via indirect, "shadow" indicators. Unlike traditional signature-based EDR/XDR rules, these patterns identify **unusual sequence deviations** in user commands, network traffic, or process hierarchies—often missed by traditional SOC tools.

Shadow patterns are triggered when:
- A legitimate user exhibits **rare command chaining** (e.g., `strace` + `netcat` + `powershell`).
- A system exhibits **non-standard process lineage** (e.g., `python.exe` → `regsvr32.exe` → `cmd.exe`).
- Suspicious **network connections** (e.g., outdated protocols or C2-like behavior) occur in tandem with benign activity.

This pattern is most effective in **highly restricted environments** (e.g., government, finance) where even subtle deviations from normalized behavior warrant investigation.

---

## **2. Schema Reference**
Below is the **structured schema** for Blue Canary Shadow Patterns, used for detection and alerting.

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Values**                                                                                                                                 |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| **`pattern_id`**        | String (UUID)  | Unique identifier for the shadow pattern.                                                                                                                                                                    | `1d4a6b2e-3c4d-5e6f-7a8b-9c0d1e2f3456`                                                                                                               |
| **`pattern_name`**      | String         | Human-readable name (e.g., "Mimikatz via WMI Dump").                                                                                                                                                           | `"Strace-to-Netcat-to-PS"`, `"Unix-CMD-to-Win-Remote-Exec"`                                                                                       |
| **`severity`**          | Enum           | Severity level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). Defaults to `MEDIUM`.                                                                                                                                      | `HIGH`                                                                                                                                               |
| **`confidence`**        | Float (0-1)    | Probability score (0.1–1.0) indicating likelihood of malicious activity. **Default: 0.7** (adjustable via tuning).                                                                                           | `0.85`                                                                                                                                               |
| **`triggered_by`**      | Array[Object]  | List of **event types** that constitute the shadow pattern. Each object contains:                                                                                                                       | `[{ "event_type": "PROCESS_CREATED", "source": "Linux", "program": "strace" }, { "event_type": "NETWORK_CONN", "proto": "TCP", "port": 4444 }]` |
| **`anti_evade`**        | Boolean        | Whether the pattern includes **anti-evasion checks** (e.g., rule ordering, time windows).                                                                                                                     | `true`                                                                                                                                              |
| **`mitigation`**        | Array[String]  | Recommended responses (e.g., `isolate`, `block`, `investigate`).                                                                                                                                         | `["block_process","escalate_to_soc"]`                                                                                                           |
| **`context`**           | Object         | Metadata including:                                                                                                                                                                                       | `{ "product": "BlueCanary", "version": "2.4", "author": "DFIR Team", "last_review": "2024-05-15" }`                                          |
| **`time_window`**       | Time Duration  | Mandatory window (e.g., `PT15M`, `P1D`) within which events must occur to trigger the pattern. **Default: `PT30M`** (30 minutes).                                                                      | `PT5M` (5-minute window)                                                                                                                        |
| **`exclude_whitelist`**| Array[String]  | System accounts, IPs, or processes to ignore.                                                                                                                                                                | `["sysadmin","192.168.1.0/24","/usr/bin/ls"]`                                                                                                 |
| **`false_positive_mitigations`** | Array[String] | Actions to reduce noise (e.g., `add_to_whitelist`, `adjust_confidence`).                                                                                                                                       | `["adjust_confidence:LOW"]`                                                                                                                     |

---

## **3. Query Examples**
Below are **SIEM query examples** (Presto/ELK/Splunk syntax) to detect Blue Canary Shadow Patterns.

### **Example 1: Linux-to-Windows Lateral Movement via Netcat**
Detects when a Linux `strace` + `netcat` combo leads to a Windows `powershell` payload.

```sql
-- Presto (Athena/Trino)
WITH netcat_events AS (
  SELECT
    user_id,
    event_time,
    CASE
      WHEN program = 'netcat' AND source = 'Linux' THEN 'NC_SOURCE'
      WHEN program LIKE '%powershell.exe' AND source = 'Windows' THEN 'PS_TARGET'
      WHEN program = 'strace' AND source = 'Linux' THEN 'STRACE_PREP'
    END AS event_type
  FROM raw_logs
  WHERE
    event_time >= now() - INTERVAL '30 minutes'
    AND program IN ('netcat', 'strace', 'powershell.exe')
),
pattern_matches AS (
  SELECT
    user_id,
    MAX(event_time) AS last_event_time
  FROM netcat_events
  GROUP BY user_id
  HAVING
    COUNT(DISTINCT event_type) = 3
    AND SUM(CASE WHEN event_type = 'NC_SOURCE' THEN 1 ELSE 0 END) = 1
    AND SUM(CASE WHEN event_type = 'PS_TARGET' THEN 1 ELSE 0 END) = 1
    AND SUM(CASE WHEN event_type = 'STRACE_PREP' THEN 1 ELSE 0 END) = 1
)
SELECT user_id, last_event_time, 'Suspicious Netcat-to-PS Chain' AS pattern_name
FROM pattern_matches;
```

---

### **Example 2: WMI Dumping via Unusual Process Chain**
Detects when `Tasklist.exe` is followed by `regsvr32.exe` (common Mimikatz delivery method).

```splunk
| rest /servicesNS/nobody/search/jobs
| eval _raw=case(match(_raw, "Process Created"), "Process Created", _raw)
| rex field=_raw "Process Name=\"(?<process>[^\"]+)\""
| where process IN ("tasklist.exe", "regsvr32.exe")
| stats
  earliest(_time) as first_event_time,
  latest(_time) as last_event_time,
  values(process) as processes
  BY user, host
| search processes *= "tasklist.exe" AND processes *= "regsvr32.exe"
| where last_event_time - first_event_time < 1800  -- <30 minutes
| table user, host, first_event_time, last_event_time, _raw
```

---

### **Example 3: Shadow Pattern in Azure Sentinel**
Using Azure Sentinel's KQL for Windows Event Log 4688 (Process Creation) + Event 4697 (Token Privileges).

```kql
let shadowPattern =
SecurityEvent
| where TimeGenerated > ago(30m)
| where EventID == 4688  // Process Create
| join kind=inner (
    SecurityEvent
    | where TimeGenerated > ago(30m)
    | where EventID == 4697  // Token Privileges
    | summarize count() by Account, TargetUserName, NewProcessName
    | where count_ > 1
) on $left.Account == $right.Account
| where NewProcessName == "reg.exe" and CommandLine has "secedit"
| project TimeGenerated as Timestamp, Account, NewProcessName, CommandLine;
```

---

## **4. Key Implementation Details**
### **4.1 Trigger Conditions**
Shadow patterns require **sequential events** within the `time_window`. Example:
- **Rule 1**: `strace` → `netcat` (Linux).
- **Rule 2**: `netcat` → `powershell` (Windows).
- **Result**: Pattern matches if **both rules fire** within `PT30M`.

### **4.2 Anti-Evasion Tactics**
- **Rule Ordering**: Enforce strict sequencing (e.g., `A` → `B` → `C`).
- **Time Decay**: Reduce confidence if events lag beyond `time_window`.
- **Process Whitelisting**: Exempt known-good tools (e.g., `git`, `docker`).

### **4.3 Confidence Tuning**
Adjust `confidence` dynamically:
| Scenario                     | Recommended Adjustment |
|------------------------------|-------------------------|
| High false positives         | Set `confidence: 0.9`   |
| New APT campaign observed    | Set `confidence: 0.6`   |
| Whitelisted user/process    | Use `exclude_whitelist` |

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                     | **Overlap with Shadow Patterns**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| **Purple Team Chain Analysis**   | Correlates adversary emulation steps to detect test scenarios.                                                                                                 | Reuses `triggered_by` events but with higher `confidence` threshold.                                               |
| **Legitimate Tool Abuse**        | Detects benign tools used maliciously (e.g., `PowerShell` for persistence).                                                                               | Uses `process_chain` logic but with broader `exclude_whitelist` rules.                                             |
| **C2 Traffic via Shadow Protocols** | Identifies covert C2 through uncommon ports (e.g., DNS over HTTP).                                                                                       | `triggered_by` includes `NETWORK_CONN` events with `proto: "HTTP"` + `port: 853` (DNS over HTTPS).                    |
| **Lateral Movement via RDP**     | Detects unusual RDP sessions followed by credential dumping.                                                                                               | Shadow patterns can supplement by analyzing **post-RDP process behavior**.                                        |
| **Command Injection via Debugger** | Flags `gdb`/`xdebug` followed by shellcode execution.                                                                                                      | Synergizes with `process_chain` when `program: "gdb"` precedes a suspicious `execve`.                               |

---

## **6. Use Cases**
### **6.1 Threat Hunting**
- **Query**: *"Find users who staged a payload via `strace` + `netcat`."*
- **Tool**: Run the **Linux-to-Windows** query in SIEM.

### **6.2 Compliance Auditing**
- **Requirement**: Detect anomalies in **NIST SP 800-53** or **MITRE ATT&CK** technique `T1059` (Command-Line Interface).
- **Action**: Apply `severity: CRITICAL` to patterns matching `T1059` via `Process Creation` events.

### **6.3 Incident Response**
- **Example**: A `shadowPattern` triggers for `python.exe` → `mshta.exe` → `calc.exe`.
- **Next Steps**:
  1. Investigate `mshta.exe` command line (`mitigation: ["escalate_to_soc"]`).
  2. Check for **unusual file modifications** (`find /path -type f -mmin -10`).
  3. Block `python.exe` from the user’s host (`mitigation: ["block_process"]`).

---
## **7. Troubleshooting**
| **Issue**                          | **Solution**                                                                                                                                 |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| False positives on `strace` usage  | Whitelist known-good processes: `"exclude_whitelist": ["/usr/bin/strace", "sysadmin"]`.                                                |
| Missed patterns due to time window | Adjust `time_window` to `PT60M` if events are sporadic.                                                                                     |
| Confidence too low/high            | Use `mitigation: ["adjust_confidence"]` to fine-tune via SIEM console.                                                                   |
| Shadow pattern not firing          | Verify `triggered_by` events are logged in your SIEM buffer (check `event_time` granularity).                                               |

---
## **8. See Also**
- **[BlueCanary Docs: User Guide]** – Setup and configuration.
- **[MITRE ATT&CK Techniques]** – Map shadow patterns to tactics (e.g., `Lateral Movement`).
- **[Splunk SOAR Playbook]** – Automate response to detected shadow patterns.