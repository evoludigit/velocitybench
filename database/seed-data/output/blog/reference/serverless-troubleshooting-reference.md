# **[Pattern] Serverless Troubleshooting Reference Guide**

---

## **Overview**
Serverless architectures abstract infrastructure management, but debugging can be challenging due to distributed, ephemeral, and AWS-specific components. This guide provides a structured approach to troubleshooting common serverless issues, covering AWS Lambda, API Gateway, DynamoDB, SQS/SNS, and X-Ray tracing.

Key focus areas:
- **Log aggregation** (CloudWatch, X-Ray, third-party tools)
- **Dependency verification** (IAM roles, VPC configurations, event sources)
- **Performance bottlenecks** (cold starts, throttling, concurrency limits)
- **Permission errors** (resource policies, execution role issues)

This guide prioritizes **precise troubleshooting steps** with actionable checks, minimizing guesswork.

---

## **Implementation Details**

### **1. Log Analysis & Monitoring**
Serverless components rely on AWS-managed metrics and logs. The following tables map common issues to log sources.

| **Issue**               | **Log Source**                     | **Key Metrics/Logs**                                                                 |
|-------------------------|------------------------------------|------------------------------------------------------------------------------------|
| Lambda cold starts      | CloudWatch Logs                    | `Duration` (low metrics), `Throttles`, `ConcurrentExecutions`                      |
| Permission denied       | CloudWatch Logs (403 errors)       | `ResourceNotFoundException`, `AccessDeniedException`                                |
| DynamoDB throttling     | CloudWatch Metrics (DynamoDB)      | `ConsumedReadCapacityUnits`, `ThrottledRequests`                                   |
| API Gateway timeouts    | CloudWatch Logs                    | `latency`, `IntegrationLatency`, `5XXErrors`                                        |
| Event source failures   | CloudWatch Logs (Lambda)           | `SQS Error`, `EventSourceMapping Error`, `DeadLetterQueue` metrics (if enabled)    |

**Pro Tip:**
- Use **CloudWatch Insights** for structured queries:
  ```sql
  filter LambdaError
  | stats count(*) by bin(5m)
  | sort count(*) desc
  ```

---

### **2. Dependency Validation**
Serverless components depend on IAM roles, VPC configurations, and event sources. Failures often stem from misconfigurations.

| **Component**       | **Common Issues**                     | **Validation Check**                                                                 |
|---------------------|---------------------------------------|------------------------------------------------------------------------------------|
| **Lambda IAM Role** | Missing permissions                   | Run `aws iam get-role-policy --role-name <role_name>`                              |
| **VPC Configuration** | Public subnet misconfiguration         | Check `subnetRouteTables` for NAT gateway connectivity                               |
| **DynamoDB IAM**    | Incorrect table access policies       | Use `aws dynamodb describe-table` + `aws iam get-policy-version`                    |
| **SQS/SNS**         | Event source mapping errors           | Verify `EventSourceMapping` + `SQS Queue Attributes` (`ReceiveMessageWaitTime`)   |

---

### **3. Step-by-Step Troubleshooting Flowchart**
Follow this **decision tree** for root cause analysis:

1. **Step 1:** Check **CloudWatch Logs** for recent errors.
   - Filter by `ERROR` or `REPORT`.
2. **Step 2:** Verify **execution role** permissions.
   - Execute: `aws iam list-attached-role-policies --role-name <role>`
3. **Step 3:** Monitor **CloudWatch Metrics** for throttling.
   - If `Throttles` > 0, check `ConcurrentExecutions` limits.
4. **Step 4:** Inspect **X-Ray traces** (if enabled).
   - Look for `Next` or `Error` segments in the trace.

---

## **Schema Reference**
### **A. CloudWatch Log Retention Policy**
| **Field**               | **Description**                                                                 | **Example**                          |
|-------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| `LogGroup`              | Destination log group (e.g., `/aws/lambda/my-function`)                     | `/aws/lambda/my-function`            |
| `RetentionDays`         | Logs retention period (7–365 days)                                           | `30`                                 |
| `MaxLogEvents`          | Maximum events per log group (default: unlimited)                             | `10000` (optional)                   |

### **B. Lambda Environment Variables**
| **Key**                 | **Description**                                                                 | **Example**                          |
|-------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| `STAGE`                 | Deployment environment (e.g., `dev`, `prod`)                                  | `STAGE=prod`                         |
| `TRACING`               | Enable X-Ray (`AWX_XRAY_DAEMON_ADDRESS` for custom endpoints)                  | `TRACING=AWS_XRAY`                    |
| `DYNAMODB_TABLE`        | Target DynamoDB table name                                                  | `DYNAMODB_TABLE=my-table`             |

---

## **Query Examples**
### **1. CloudWatch Log Query (Lambda Errors)**
```sql
filter isPresent("Error") AND @timestamp > ago(1d)
| stats count(*) by function_name
| sort count(*) desc
```

### **2. DynamoDB Throttling Alert (CloudWatch Metrics)**
```sql
metric 'DynamoDB' 'ThrottledRequests' > 0
| metricFilter
| alarm name 'HighThrottle' comparison OPERATOR 'GreaterThanThreshold' threshold 10
```

### **3. X-Ray Trace Filter (Failed API Gateway Requests)**
```bash
aws xray get-traces --filter "traceSummary.fields('http/responseCode').eq(500')"
```

---

## **Related Patterns**
1. **[Lambda Layer Management]**
   Optimize dependencies with shared libraries and runtime environments.
2. **[Event-Driven Architecture]**
   Leverage SQS, SNS, and EventBridge for decoupled serverless workflows.
3. **[Canary Deployments]**
   Gradually roll out updates to minimize risk.
4. **[Cost Optimization]**
   Use **AWS Budgets** and **Cost Explorer** to monitor serverless spending.
5. **[Security Hardening]**
   Enforce **least-privilege IAM roles** and **VPC isolation**.

---

## **Key Takeaways**
✅ **Start with logs** (CloudWatch + X-Ray).
✅ **Validate permissions** early (IAM roles, event sources).
✅ **Monitor metrics** (throttling, concurrency).
✅ **Use CloudWatch Insights** for structured queries.
✅ **Refer to AWS documentation** for component-specific guidelines.

---
**Further Reading:**
- [AWS Lambda Troubleshooting Guide](https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting.html)
- [Amazon X-Ray Documentation](https://docs.aws.amazon.com/xray/latest/devguide/welcome.html)