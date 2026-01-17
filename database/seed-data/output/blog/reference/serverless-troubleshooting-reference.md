# **[Pattern] Serverless Troubleshooting: Reference Guide**

---

## **1. Overview**
Serverless architectures simplify deployment and scaling but introduce unique challenges in debugging. This guide provides structured troubleshooting steps for common issues in serverless environments (AWS Lambda, Azure Functions, Google Cloud Functions, etc.). It covers **logging, monitoring, cold starts, concurrency limits, error handling, dependencies, and third-party integrations**, with actionable patterns for root-cause analysis.

Use this guide when:
- Lambda/Function invocations fail intermittently.
- Performance degrades (slow cold starts, throttling).
- Errors persist despite correct syntax.
- Dependencies (databases, APIs) cause cascading failures.

---

## **2. Key Concepts & Schema Reference**

### **2.1 Core Troubleshooting Categories**
| **Category**               | **Description**                                                                 | **Key Tools**                          |
|----------------------------|---------------------------------------------------------------------------------|----------------------------------------|
| **Logging & Observability** | Capture execution traces, metrics, and context.                              | CloudWatch (AWS), Application Insights (Azure), Stackdriver (GCP) |
| **Cold Starts**            | Latency spikes due to initialization delays.                                   | Provisioned Concurrency, SnapStart (GCP) |
| **Concurrency Limits**     | Throttling due to AWS Lambda/Azure Function quotas.                            | Check quotas (`AWS Service Quotas`), adjust scaling |
| **Error Handling**         | Unhandled exceptions, timeouts, or retries causing cascading failures.        | Dead Letter Queues (DLQ), Retry Policies |
| **Dependency Issues**      | External calls (DB, APIs) failing or timing out.                               | Circuit Breakers, Exponential Backoff |
| **Permissions**            | IAM roles or RBAC misconfigurations blocking access.                           | IAM Policy Simulator, AWS CLI (`sts get-caller-identity`) |
| **Networking**             | VPC misconfigurations, private API access failures.                           | VPC Flow Logs, Security Groups        |

---

### **2.2 Schema: Common Error Patterns**
Use this table to diagnose issues systematically.

| **Symptom**                     | **Root Cause**                          | **Diagnostic Query**                          | **Solution**                          |
|---------------------------------|----------------------------------------|-----------------------------------------------|---------------------------------------|
| **5xx Errors (Lambda/Azure)**    | Internal server errors, timeouts       | `Filter by HTTP 5xx in CloudWatch`           | Increase timeout, optimize code       |
| **429 Too Many Requests**        | Concurrency limits hit                 | `Check AWS Lambda Throttling Metrics`        | Increase reserved concurrency         |
| **Cold Start Latency >1s**       | Initialization overhead                | `Compare Invocation Duration in X-Ray`        | Use Provisioned Concurrency, SnapStart|
| **Dependency Timeouts**          | External API/database slow/crashing     | `Check `Duration` metric for DB/API calls`    | Implement retries + circuit breakers  |
| **Permission Denied (403)**      | Missing IAM roles/policies             | `Run `aws iam get-user-policy` (AWS CLI)`    | Attach correct IAM policy             |
| **Missing Environment Variables**| Config not passed to function          | `Query `Environment Variables` in CloudWatch`| Use Lambda Layers or Secrets Manager  |
| **Uncaught Exceptions**         | No error handling in code              | `Filter by `Unhandled Exception` in Logs`     | Add `try-catch` blocks                |

---

## **3. Query Examples**
### **3.1 Logging & Metrics Queries**
**AWS CloudWatch Logs (Lambda):**
```sql
-- Find failed invocations in the last 24h
filter @type = "REPORT"
| stats count(*) by @timestamp, result
| where result = "Failure"
```

**Azure Application Insights:**
```kusto
-- Filter by failed invocations (Azure Functions)
traces
| where operation_Name has "Function"
| where message has "ERROR"
| project timestamp, message, duration
| sort by timestamp desc
```

**GCP Cloud Logging:**
```bash
# Query for Lambda errors (gcloud CLI)
gcloud logging read "resource.type=cloud_function" \
  --filter 'severity=ERROR' \
  --limit 50
```

---

### **3.2 X-Ray/Azure Monitor Traces**
**AWS X-Ray:**
```sql
-- Analyze slow dependencies in a Lambda function
select * from trace_segments
where name = 'YourFunctionName'
and http {
    target = 'external-api'
}
| filter duration > 1000  // ms
```

**Azure Monitor:**
```kusto
-- Find slow HTTP calls in Azure Functions
traces
| where operation_Name has "HttpRequest"
| where duration > 500  // ms
| project timestamp, operation_Name, resultCode, duration
| sort by duration desc
```

---

### **3.3 Concurrency & Throttling Checks**
**AWS CLI (Check Quotas):**
```bash
# List Lambda concurrency limits
aws service-quotas list-service-quotas \
  --service-code lambda \
  --limit-type SERVICE
```

**Azure CLI (Check Limits):**
```bash
# Check Azure Function app limits
az functionapp list-limits --resource-group YourRG --name YourApp
```

---

## **4. Step-by-Step Troubleshooting Flowchart**
1. **Is the issue intermittent or consistent?**
   - **Consistent:** Check logs for errors (4xx/5xx, timeouts).
   - **Intermittent:** Investigate cold starts or dependency failures.
2. **Are logs available?**
   - Yes → Parse for stack traces, durations, or missing context.
   - No → Verify permissions (`IAM`, `CloudWatch Logs` access).
3. **Is the problem Lambda/Function-specific?**
   - Yes → Check cold starts, memory allocation, or concurrency.
   - No → Isolate dependency (DB, API) failures.
4. **Reproduce locally?**
   - Use **SAM CLI (AWS)** or **Azure Functions Core Tools** for emulation.

---

## **5. Advanced Techniques**
### **5.1 Distributed Tracing**
- **AWS:** Enable X-Ray for Lambda → Trace requests across services.
- **Azure:** Use Application Insights + Distributed Tracing.
- **GCP:** Enable OpenTelemetry for Cloud Functions.

**Example X-Ray Trace Filter:**
```sql
-- Find Lambda cold starts in X-Ray
select * from trace_segments
where name = 'YourFunction'
and cold_start = true
```

### **5.2 Synthetic Monitoring**
Use **AWS Synthetic Monitoring**, **Azure Load Testing**, or **Locust** to simulate traffic and detect latent issues.

### **5.3 Canary Deployments**
Gradually roll out updates to a subset of users to catch deployment-related bugs early.

---

## **6. Common Pitfalls & Fixes**
| **Pitfall**                          | **Why It Happens**                          | **Fix**                                      |
|---------------------------------------|--------------------------------------------|----------------------------------------------|
| **Unhandled Rejections**              | No DLQ configured                          | Enable DLQ for async invocations             |
| **Circular Dependencies**             | Lambda calls itself recursively           | Set `reserved_concurrency` to `0`             |
| **Over-Permissive IAM Roles**         | Functions have unnecessary permissions      | Use AWS IAM Access Analyzer                  |
| **Hardcoded Secrets**                 | Credentials in code                         | Use AWS Secrets Manager / Azure Key Vault    |
| **No Retry Logic**                    | External API failures unrecoverable        | Implement exponential backoff + retries      |

---

## **7. Related Patterns**
| **Pattern**                          | **Purpose**                                      | **When to Use**                              |
|---------------------------------------|--------------------------------------------------|----------------------------------------------|
| **[Observability-Driven Development](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-patterns/observability-driven-development.html)** | Centralize logs, metrics, and traces          | For production-grade monitoring             |
| **[Retries & Circuit Breakers](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)** | Handle transient failures in dependencies     | When calling external APIs                   |
| **[Provisioned Concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)** | Mitigate cold starts                          | For latency-sensitive applications           |
| **[Step Functions for Workflows](https://aws.amazon.com/step-functions/)** | Orchestrate multi-step serverless workflows   | When functions require coordination          |
| **[Chaos Engineering](https://learn.microsoft.com/en-us/azure/architecture/chaos-engineering/)** | Test resilience to failures                   | During pre-production testing                |

---

## **8. Tools Checklist**
| **Tool**                          | **Purpose**                                      | **Links**                                      |
|------------------------------------|--------------------------------------------------|------------------------------------------------|
| **AWS CloudWatch Logs Insights**   | Query and analyze Lambda logs                    | [AWS Docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html) |
| **Azure Application Insights**     | Monitor Azure Functions performance              | [Azure Docs](https://learn.microsoft.com/en-us/azure/azure-monitor/app/quickstart-functions) |
| **GCP Cloud Logging**              | Search GCP Function logs                         | [GCP Docs](https://cloud.google.com/logging/docs/view/logs-viewer) |
| **Datadog (Multi-Cloud)**          | Unified observability                           | [Datadog](https://www.datadoghq.com/)          |
| **Lumigo (AWS Focused)**           | Serverless-specific debugging                    | [Lumigo](https://lumigo.io/)                  |
| **New Relic**                      | APM for serverless applications                  | [New Relic](https://newrelic.com/)             |
| **AWS X-Ray**                      | Distributed tracing                              | [AWS X-Ray](https://aws.amazon.com/xray/)      |

---

## **9. Glossary**
| **Term**                  | **Definition**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|
| **Cold Start**            | Latency incurred when a Lambda/Function initializes a new instance.            |
| **Provisioned Concurrency** | Pre-warmed instances to reduce cold starts.                                   |
| **Dead Letter Queue (DLQ)** | Asynchronous messaging queue for failed invocations.                          |
| **Concurrency Limit**     | Maximum simultaneous executions allowed per function.                          |
| **Execution Role**        | IAM role attached to a Lambda/Function for permissions.                         |
| **Environment Variables**  | Configurable settings passed to a function at deployment time.                 |
| **VPC Endpoint**          | Private access to AWS services without NAT.                                    |
| **Serverless Application Model (SAM)** | AWS toolkit for developing/serverless apps.                                 |

---
**End of Guide**
*For further reading, see [AWS Serverless Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting.html) and [Microsoft’s Serverless Best Practices](https://learn.microsoft.com/en-us/azure/architecture/serverless).*