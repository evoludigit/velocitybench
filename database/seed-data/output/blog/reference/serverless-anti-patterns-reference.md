**[Pattern] Serverless Anti-Patterns: Reference Guide**

---

### **Overview**
Serverless architectures prioritize scalability, cost-efficiency, and reduced operational overhead—but they introduce unique pitfalls if misapplied. **Anti-patterns** are common misunderstandings or misconfigurations that undermine these benefits, leading to **inefficiencies, hidden costs, or system failures**. This guide catalogs well-documented serverless anti-patterns, their causes, impacts, and mitigation strategies. Avoiding these pitfalls ensures cleaner, more maintainable, and performant serverless implementations.

---

### **Schema Reference**
Below is a structured breakdown of **core serverless anti-patterns**, their risks, and mitigation actions.

| **Anti-Pattern**               | **Description**                                                                                     | **Risk**                                                                                     | **Mitigation Strategy**                                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Overusing Lambda for Long-Running Tasks** | Deploying Lambda functions for tasks exceeding 15 minutes (hard limit) or requiring long loops.   | Costly cold starts, timeouts, and inefficiency for batch processing or heavy computations.    | Use **Step Functions** for orchestration or offload to **EC2/Fargate** if needed.                            |
| **Monolithic Lambda Functions**  | Single Lambda handling multiple unrelated business logic (e.g., API routes, file processing).       | Poor scalability, slow cold starts, and harder debugging.                                      | Decompose into smaller, focused functions (e.g., per-API route or event type).                            |
| **Ignoring Cold Start Latency**  | Designing user-facing flows with no consideration for first invocation slowness.                     | Poor UX, failed transactions, or timeout errors.                                             | Use **Provisioned Concurrency** for critical paths or optimize packages (e.g., smaller dependencies).    |
| **Unbounded Retries & Circular Invocations** | Functions recursively calling each other without limits, causing cascading retries.              | Infinite loops, throttling, and cost spikes.                                                  | Set **DLQs (Dead Letter Queues)** + **retry limits**, and validate success responses.                        |
| **Event Source Overload**       | Polling DynamoDB streams/Kinesis aggressively without throttling or batching.                        | Excessive API calls, throttling errors (`ProvisionedThroughputExceeded`), or cost overruns.  | Use **batch settings** (e.g., `BatchSize`, `ParallelizationFactor`) and implement retries with backoff.    |
| **Hardcoding Secrets/Config**   | Embedding API keys, DB credentials, or feature flags directly in Lambda code.                       | Security breaches, credential leaks, and deployment inconsistencies.                          | Use **SSM Parameter Store**, **Secrets Manager**, or CI/CD secrets vaults.                                |
| **Ignoring VPC vs. Non-VPC Tradeoffs** | Running Lambda in a VPC unnecessarily for non-database workloads.                                   | Higher cold starts (ENI attachment delays), higher costs, and unnecessary latency.            | Use **VPC only if required** (e.g., RDS access); otherwise, use **PrivateLink** or VPC endpoints.         |
| **No Observability**           | Missing logging, metrics, or tracing for serverless components.                                     | Blind spots in debugging, undetected failures, and poor performance tuning.                  | Use **CloudWatch Logs**, **X-Ray**, and **custom metrics** (e.g., Lambda Insights).                        |
| **Tight Coupling to Event Sources** | Designing lambdas to expect exact event schemas (e.g., hardcoding field names).                  | Breakage on schema changes or third-party updates.                                            | Use **schema validation** (e.g., AWS EventBridge schemas) or adapt with **dynamic parsing**.               |
| **No Cleanup for Temporary Resources** | Creating S3 buckets, DynamoDB tables, or Step Functions states without cleanup processes.        | Uncontrolled cost growth and resource bloat.                                                | Implement **autodeletion policies** (e.g., lifecycle rules) or **manual cleanup scripts**.                |
| **Overusing "Serverless" for Stateful Workloads** | Using Lambda/SQS/SNS for heavy state management (e.g., caching user sessions).                   | Race conditions, data inconsistency, or increased complexity.                                 | Use **DynamoDB** (for sessions) or **ElastiCache** for shared state.                                       |
| **Neglecting Idempotency**      | Designing event-driven workflows where duplicate processing causes side effects.                    | Duplicate orders, failed transactions, or inconsistent data.                                  | Implement **idempotency keys** (e.g., UUIDs in event payloads) and **dedupe logic**.                     |
| **Assuming Lambda is Free**     | Treating Lambda invocations as cost-neutral without monitoring usage.                                | Unexpected bills for excessive duration/invocations.                                         | Use **AWS Cost Explorer** and **Budget Alerts**; optimize with **right-sized memory/timeout**.               |

---

### **Query Examples**
Below are **real-world scenarios** where anti-patterns surface, along with **diagnostic queries** (using AWS CLI/CloudWatch).

#### **1. Detecting Overload on Event Sources (Kinesis/DynamoDB)**
**Problem:** A Lambda processing Kinesis records is failing with `ThrottlingException`.
**Query:**
```bash
# Check Lambda logs for throttling events (last 7 days)
aws logs filter-log-events --log-group-name "/aws/lambda/my-processor" \
  --filter-pattern "\"error\" OR \"throttlingException\""

# Review Kinesis metrics for under/over-scaling
aws cloudwatch get-metric-statistics \
  --namespace AWS/Kinesis \
  --metric-name ReadProvisionedThroughputExceeded \
  --dimensions Name=StreamName,Value=my-stream \
  --start-time $(date -u -v-7D +%FT%H:%M:%SZ) \
  --end-time $(date -u +%FT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

**Mitigation:**
- Adjust `BatchWindow` to reduce bursts (e.g., `BatchWindow=2000`).
- Enable **enhanced fan-out** for Kinesis to decouple consumers.

---

#### **2. Identifying Cold Start Bottlenecks**
**Problem:** API Gateway + Lambda has high latency on cold starts.
**Query:**
```bash
# CloudWatch metric: Lambda cold starts (last 1 hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=my-function \
  --statistics Sum \
  --period 60 \
  --start-time $(date -u -v-1H +%FT%H:%M:%SZ) \
  --end-time $(date -u +%FT%H:%M:%SZ) \
  --label "Last Hour Cold Starts"

# Compare with duration metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=my-function \
  --statistics Average \
  --period 60 \
  --start-time $(date -u -v-1H +%FT%H:%M:%SZ) \
  --end-time $(date -u +%FT%H:%M:%SZ)
```

**Mitigation:**
- Enable **Provisioned Concurrency** for critical paths.
- Reduce package size (e.g., exclude non-essential libraries).

---

#### **3. Finding Uncleaned-Up Resources**
**Problem:** Orphaned DynamoDB tables or S3 buckets accumulate costs.
**Query:**
```bash
# List DynamoDB tables created >30 days ago
aws dynamodb list-tables --query "TableNames" --output text | \
  while read table; do
    creation=$(aws dynamodb describe-table --table-name "$table" --query "Table.Description.CreationDateTime" --output text)
    if [ "$(date -u -v-30D +%F)" -lt "$(date -u -jf "%Y-%m-%d %H:%M:%S" "$creation")" ]; then
      echo "$table (Created: $creation) - Stale!"
    fi
  done

# S3 buckets with no access controls (high-risk)
aws s3api list-buckets --query "Buckets[].Name" --output text | \
  xargs -I {} aws s3api get-bucket-policy --bucket {} 2>/dev/null | \
  grep "NoSuchBucketPolicy" && echo "Bucket {} has no policy!"
```

**Mitigation:**
- Use **AWS Config Rules** to auto-tag/deprovision stale resources.
- Implement **IAM policies with resource limits** (e.g., `MaxTableAge=90`).

---

### **Related Patterns**
To counter anti-patterns, leverage these **complementary serverless patterns**:

| **Related Pattern**          | **Purpose**                                                                                     | **When to Use**                                                                               |
|-------------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Event-Driven Decomposition** | Split workflows into decoupled Lambda + SQS/SNS components.                                    | For complex stateful processes (e.g., order processing).                                      |
| **Saga Pattern**              | Manage distributed transactions with compensating actions.                                     | Critical financial operations or long-running workflows.                                     |
| **Canary Deployments**        | Gradually roll out Lambda updates with traffic splitting.                                      | Reducing risk during feature rollouts.                                                        |
| **Step Functions**           | Orchestrate multi-step serverless workflows with retries/timeouts.                            | Replacing hardcoded Lambda orchestration with a visual map.                                  |
| **Lambda Layers**             | Share reusable code (e.g., DB clients, logging) across functions.                             | Reducing bloat in multiple functions with shared dependencies.                               |
| **API Gateway + Lambda Proxy** | Simplify API routes with dynamic routing.                                                     | For REST APIs with one-to-one function-to-endpoint mapping.                                |
| **Circuit Breakers**          | Fail fast when downstream services are degraded.                                                | Handling DB timeouts or third-party API failures gracefully.                                  |

---

### **Key Takeaways**
- **Design for failure**: Assume Lambda/SQS failures will happen—use retries, DLQs, and idempotency.
- **Monitor aggressively**: Use CloudWatch Alarms for throttling, cold starts, and duration spikes.
- **Decompose early**: Avoid monolithic Lambdas by aligning functions to single responsibilities.
- **Optimize for cost**: Right-size memory, use Provisioned Concurrency judiciously, and clean up resources.
- **Leverage managed services**: Offload state management (DynamoDB), caching (ElastiCache), and async processing (EventBridge).

---
**Further Reading:**
- [AWS Well-Architected Serverless Lens](https://aws.amazon.com/architecture/well-architected/serverless-lens/)
- [Serverless Anti-Patterns (GitHub)](https://github.com/alexcasalboni/serverless-anti-patterns)