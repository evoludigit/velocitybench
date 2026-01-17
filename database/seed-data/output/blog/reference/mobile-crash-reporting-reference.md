**[Design Pattern] Crash Reporting Patterns: Reference Guide**

---

### **Overview**
Crash Reporting Patterns define structured approaches to collecting, analyzing, and managing application crashes in real-time or near-real-time. These patterns ensure developers receive actionable crash reports that help diagnose stability issues, improve code resilience, and enhance user experience. Typical implementations include **crash logs**, **telemetry**, and **automated triage workflows**, often tied to monitoring and analytics systems. This pattern supports both **client-side (native/mobile/web)** and **server-side (backend/API)** crash detection, with customizable granularity (e.g., stack traces, device/data context, or user impact metrics).

---

### **Key Concepts**
The pattern comprises three core components:

1. **Crash Capture**
   - Mechanisms to detect and extract crash data (e.g., unhandled exceptions, segfaults, or API failures).
   - **Includes**: Error boundaries, crash handlers, and telemetry instrumentation (e.g., custom events for graceful degradation).

2. **Data Enrichment**
   - Augmenting crash reports with contextual metadata (e.g., device specs, SDK versions, or user sessions).
   - **Tools/Techniques**: SDKs (e.g., Sentry, Crashlytics), custom scripts, or server-side logging libraries.

3. **Transport & Storage**
   - Securely transmitting crash data to a centralized repository (e.g., logs-as-a-service, databases, or data lakes).
   - **Considerations**: Rate-limiting, deduplication, and compliance (e.g., GDPR for PII).

---

### **Schema Reference**
Below is a standardized schema for crash report payloads. Adjust fields based on your use case.

| **Field**               | **Type**   | **Description**                                                                                     | **Example Values**                     |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------|
| `event_id`              | UUID       | Unique identifier for the crash report.                                                             | `550e8400-e29b-41d4-a716-446655440000` |
| `timestamp`             | ISO8601    | When the crash occurred (UTC).                                                                     | `2023-10-05T14:30:00.123Z`             |
| `app_version`           | String     | Version of the app experiencing the crash.                                                          | `v1.2.3 (build 120)`                   |
| `crash_type`            | Enum       | Type of crash (e.g., `native`, `js`, `api`, `timeout`).                                             | `native`                                |
| `stack_trace`           | String[]   | Array of stack traces (formatted per platform; e.g., Java/Android, JS/React, or Python).           | `["File: main.py#L42", "def handle_error("]` |
| `device_context`        | Object     | Device/environment metadata.                                                                       | `{ os: "iOS", device: "iPhone 15", os_v: "17.0" }` |
| `user_context`          | Object     | Anonymized user data (if applicable).                                                               | `{ user_id: "anon_42", session_id: "xyz" }` |
| `error_code`            | String     | Platform-specific error code (e.g., `SIGSEGV` for segfaults).                                        | `404` or `EXC_BAD_ACCESS`               |
| `attachments`           | Object[]   | Non-text attachments (e.g., screenshots, logs, or binaries).                                        | `{ url: "https://.../screenshot.png" }` |
| `resolution_status`     | Enum       | Current status (e.g., `open`, `resolved`, `duplicate`).                                             | `open`                                  |
| `priority`              | Integer    | Severity level (1–5, where 5 = critical).                                                          | `5`                                      |

---
**Note**: Use JSON or Protocol Buffers for serialization. For sensitive data, encrypt payloads (e.g., via TLS or client-side hashing).

---

### **Implementation Details**
#### **1. Crash Capture**
- **Native Apps (iOS/Android)**:
  - Use platform SDKs:
    - **Android**: `Thread.setDefaultUncaughtExceptionHandler()` + Firebase Crashlytics.
    - **iOS**: `NSException` handlers + Apple’s Crash Analytics.
  - Example snippet (Android Kotlin):
    ```kotlin
    Thread.setDefaultUncaughtExceptionHandler { _, e ->
        val report = CrashReport(EventId.new(), e.stackTraceToString())
        sendCrashReport(report) // To your backend
    }
    ```

- **Web Apps**:
  - Global error handlers (e.g., `window.onerror`) + custom event listeners for `fetch`/`Promise` rejections.
  - Example (JavaScript):
    ```javascript
    window.addEventListener("error", (event) => {
      const report = { error: event.error, url: window.location.href };
      fetch("/api/crashes", { method: "POST", body: JSON.stringify(report) });
    });
    ```

- **Server-Side**:
  - Wrap critical operations in try-catch blocks and log to a centralized system (e.g., ELK, Datadog).
  - Example (Python):
    ```python
    try:
        risky_operation()
    except Exception as e:
        log_crash(EventId(), str(e), traceback.format_exc())
    ```

#### **2. Data Enrichment**
- **Automated Tagging**:
  - Use tools like **Sentry** to auto-tag crashes with:
    - Release versions.
    - User roles (e.g., `admin` vs. `guest`).
    - SDK version mismatches.
  - Example Sentry tags:
    ```json
    { "version": "1.2.3", "sdk": "react-native@0.72.0" }
    ```

- **Contextual Data**:
  - Capture **user actions** leading to the crash (e.g., "Clicked Button X before crash").
  - Example (Flutter):
    ```dart
    // Log user actions alongside crashes
    RouteObserver.of(context)!.didPush(..., () {
      logAction("button_clicked");
    });
    ```

#### **3. Transport & Storage**
- **Batch Processing**:
  - Buffer crashes locally (e.g., SQLite) and upload periodically to reduce bandwidth.
  - Example (iOS):
    ```swift
    let queue = DispatchQueue(label: "crashQueue", attributes: .concurrent)
    queue.async { CrashLogService.uploadPendingCrashes() }
    ```

- **Storage Options**:
  | **Option**               | **Use Case**                                  | **Example Tools**                     |
  |--------------------------|-----------------------------------------------|----------------------------------------|
  | **Logs-as-a-Service**    | Centralized crash aggregation.               | Sentry, Datadog, New Relic             |
  | **Database**             | Custom dashboards or ML analysis.             | PostgreSQL (pg_logical), MongoDB       |
  | **Object Storage**       | Long-term retention of raw logs.             | S3, GCS                                 |
  - **GDPR Compliance**: Anonymize PII (e.g., user IDs) or use differential privacy for analytics.

---

### **Query Examples**
Use SQL-like queries (or tool-specific APIs) to analyze crashes. Below are example queries for a PostgreSQL-backed system.

#### **1. Find Top 5 Crash Types by Frequency**
```sql
SELECT crash_type, COUNT(*) as frequency
FROM crash_reports
GROUP BY crash_type
ORDER BY frequency DESC
LIMIT 5;
```

#### **2. Identify Regression Introduced in v1.2.3**
```sql
SELECT * FROM crash_reports
WHERE app_version = 'v1.2.3'
AND timestamp > '2023-10-01'
ORDER BY frequency DESC;
```

#### **3. Crashes Correlated with Specific User Roles**
```sql
SELECT user_context->>'role', COUNT(*)
FROM crash_reports
WHERE user_context IS NOT NULL
GROUP BY user_context->>'role';
```

#### **4. Filter Crashes with Attached Screenshots**
```sql
SELECT event_id, attachments->>'url'
FROM crash_reports
WHERE attachments IS NOT NULL;
```

---
**Tool-Specific Examples**:
- **Sentry**: [`events` API](https://develop.sentry.io/api/events/)
  ```bash
  curl "https://sentry.example/api/0/projects/my_project/events/?query=crash_type:native"
  ```
- **Crashlytics**: [`crash reporting filters`](https://firebase.google.com/docs/crashlytics/get-started)
  ```bash
  # Filter crashes in Firebase Console:
  # Time Range: Last 7 Days
  # Filter by OS: iOS
  ```

---

### **Related Patterns**
1. **[Error Boundary Pattern](https://example.com/error-boundary)**
   - Isolates UI crashes in client-side apps (e.g., React’s `ErrorBoundary`).

2. **[Graceful Degradation Pattern](https://example.com/graceful-degradation)**
   - Provides fallback UI/UX when crashes occur (e.g., "Retry" buttons or loading states).

3. **[Observability Pattern](https://example.com/observability)**
   - Combines crash reporting with metrics (e.g., Prometheus) and logs (e.g., ELK) for holistic debugging.

4. **[Canary Deployment Pattern](https://example.com/canary-deployment)**
   - Reduces crash impact by rolling out fixes to a subset of users first.

5. **[Feature Flags Pattern](https://example.com/feature-flags)**
   - Temporarily disable high-risk features flagged by crash reports.

---

### **Best Practices**
1. **Minimize Payload Size**:
   - Compress logs (e.g., gzip) or use incremental updates for large attachments.

2. **Handle Rate Limits**:
   - Implement exponential backoff for API uploads (e.g., retry after delays).

3. **Prioritize Actionable Data**:
   - Focus on **root cause** (e.g., stack traces) over verbose logs.

4. **User Communication**:
   - Notify users of crashes with a non-technical message (e.g., "We’re fixing an issue—thank you!").

5. **Retention Policy**:
   - Archive old crashes after 6 months (unless legally required).

---
### **Anti-Patterns**
- **Overloading Reports**:
  - Avoid sending **every** error (e.g., 404s) without filtering.
- **Sensitive Data Leaks**:
  - Never include API keys, passwords, or PII in reports.
- **Ignoring Deduplication**:
  - Identical crashes should be collapsed (e.g., same stack trace + context).