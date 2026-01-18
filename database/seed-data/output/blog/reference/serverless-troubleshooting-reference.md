# **[Pattern] Serverless Troubleshooting – Reference Guide**

---
## **Overview**
Serverless architectures abstract infrastructure management, but debugging issues requires specialized techniques due to ephemeral, distributed, and event-driven execution. This guide provides a systematic approach to troubleshooting serverless applications, covering logs, metrics, traces, and vendor-specific tools. Key challenges—such as cold starts, permission errors, and throttling—are addressed with actionable steps, enabling developers to diagnose and resolve issues efficiently.

---

## **Schema Reference**

| **Category**               | **Component**               | **Description**                                                                                     | **Tools / APIs**                                                                 |
|----------------------------|----------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Observability**          | CloudWatch Logs            | Centralized logs for Lambda, API Gateway, and DynamoDB interactions.                              | AWS CloudWatch Logs Insights, SDK filters                                       |
|                            | X-Ray (Traces)             | End-to-end request tracing to identify latency bottlenecks.                                        | AWS X-Ray SDK, AWS X-Ray Console                                                 |
|                            | Metrics                    | CPU, memory, duration, and throttling metrics for functions/events.                                | AWS CloudWatch Metrics, Prometheus (via CloudWatch Agent)                         |
|                            | Distributed Tracing        | Correlates traces across microservices and serverless components.                                 | OpenTelemetry, Datadog, New Relic                                              |
| **Execution**              | Lambda Console             | Debug runs, view execution logs, and test functions locally.                                       | AWS Lambda Console, SAM CLI                                                   |
|                            | API Gateway Logs           | Request/response payloads, errors, and integration failures.                                        | CloudWatch Logs, API Gateway Execution Logs                                     |
|                            | Event Sources              | Debug failures in SQS, SNS, DynamoDB Streams, or Kinesis triggers.                                | Vendor-specific SDKs, CloudTrail                                               |
| **Permissions**            | IAM Policies               | Audit missing permissions for Lambda roles, DynamoDB access, etc.                                 | AWS IAM Policy Simulator, `aws iam get-role-policy`                             |
| **Throttling**             | Concurrency Limits         | Monitor/resolve throttling due to reserved concurrency or burst limits.                           | CloudWatch Metrics (`ConcurrentExecutions`), Lambda Configuration                |
| **Cold Starts**            | Provisioned Concurrency    | Mitigate cold starts by keeping functions warm.                                                   | AWS Lambda Provisioned Concurrency                                              |
| **Dependencies**           | VPC Issues                 | Network latency or DNS failures in VPC-attached Lambdas.                                          | VPC Flow Logs, Lambda VPC Configuration                                          |
| **Testing**                | SAM/Serverless Framework   | Local emulation of AWS services for pre-production testing.                                        | AWS SAM CLI, `serverless offline`                                              |
| **Vendor-Specific**        | Azure Functions/Monitor    | Diagnose Azure-specific issues (e.g., Durable Functions).                                        | Azure Monitor, Application Insights                                            |
|                            | GCP Cloud Functions        | Debug Cloud Logging, Error Reporting, and Trace-based issues.                                     | Google Cloud Logging, Cloud Trace                                              |

---

## **Query Examples**

### **1. CloudWatch Logs Insights (AWS)**
**Query cold start latency:**
```sql
stats avg(duration) by function_name
| filter function_name like /my-function/
| sort duration desc
| limit 10
```

**Filter Lambda errors:**
```sql
fields @timestamp, @message, errorCode
| filter @message like /ERROR/ and function_name = "my-function"
| sort @timestamp desc
```

### **2. X-Ray Traces (AWS)**
**Find slow API Gateway → Lambda calls:**
```bash
aws xray get-trace-summary --start-time 2023-10-01T00:00:00 --end-time 2023-10-01T23:59:59
```

**Filter traces by service:**
```bash
aws xray get-trace-summary --service-name "api-gateway-*"
```

### **3. IAM Policy Validation**
**Check if a Lambda role has DynamoDB permissions:**
```bash
aws iam get-role-policy --role-name my-lambda-role --policy-name my-policy
```
**Simulate a permission check:**
```bash
aws iam simulate-principal-policy --policy-sourcearn arn:aws:iam::123456789012:policy/my-policy \
  --actionnames PutItem --resourcearn arn:aws:dynamodb:us-east-1:123456789012:table/MyTable
```

### **4. Throttling Analysis (CloudWatch)**
**Detect Lambda throttling:**
```sql
metric "ConcurrentExecutions" unit "Count"
| statistic average
| filter namespace = "AWS/Lambda" and function_name = "my-function"
| sort timestamp desc
| limit 1000
```

### **5. OpenTelemetry (Multi-Cloud)**
**Export traces to Jaeger:**
```yaml
# .env file for OpenTelemetry Collector
OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger:14268/api/traces
```
**Query Jaeger UI:**
```
service: my-serverless-app
operation: ProcessOrder
```

---

## **Implementation Steps by Category**

### **1. Logs and Metrics**
- **Step 1:** Check CloudWatch Logs for function errors:
  ```bash
  aws logs tail /aws/lambda/my-function --follow
  ```
- **Step 2:** Set up CloudWatch Alarms for throttles:
  ```bash
  aws cloudwatch put-metric-alarm --alarm-name Lambda-Throttle-Alarm \
    --metric-name Throttles --namespace AWS/Lambda --statistic Sum \
    --period 60 --threshold 1 --comparison-operator GreaterThanThreshold
  ```

### **2. Distributed Tracing**
- **Step 1:** Instrument code with AWS X-Ray SDK:
  ```javascript
  const AWSXRay = require('aws-xray-sdk-core');
  AWSXRay.captureAWS(require('aws-sdk'));
  ```
- **Step 2:** Enable active tracing in `serverless.yml`:
  ```yaml
  provider:
    tracing:
      apiGateway: true
      lambda: true
  ```

### **3. Permission Errors**
- **Step 1:** Attach missing policies:
  ```bash
  aws iam attach-role-policy --role-name my-lambda-role --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
  ```
- **Step 2:** Use the IAM Policy Simulator to test:
  ```bash
  aws iam simulate-principal-policy --policy-sourcearn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  ```

### **4. Cold Starts Mitigation**
- **Step 1:** Enable Provisioned Concurrency:
  ```bash
  aws lambda put-provisioned-concurrency-config --function-name my-function \
    --qualifier $LATEST --provisioned-concurrent-executions 5
  ```
- **Step 2:** Use `warmup` scripts (e.g., ping endpoint periodically).

### **5. Event Source Debugging**
- **Step 1:** Test SQS trigger locally with SAM:
  ```bash
  sam local invoke "my-function" -e event.json
  ```
- **Step 2:** Check CloudTrail for permission-related events:
  ```bash
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole
  ```

### **6. VPC Issues**
- **Step 1:** Verify VPC configuration:
  ```bash
  aws lambda get-function-configuration --function-name my-function --query "VpcConfig"
  ```
- **Step 2:** Enable VPC Flow Logs:
  ```bash
  aws ec2 create-flow-logs --resource-type VPC --traffic-type ALL --log-group-name my-vpc-flow-logs
  ```

---

## **Vendor-Specific Tools**

| **Provider**  | **Tool**                     | **Use Case**                                                                 |
|---------------|------------------------------|-----------------------------------------------------------------------------|
| **AWS**       | AWS X-Ray                   | End-to-end tracing for Lambda, API Gateway, DynamoDB.                       |
|               | CloudWatch Logs Insights     | Advanced log filtering and analysis.                                        |
| **Azure**     | Application Insights        | Distributed tracing and performance monitoring for Azure Functions.         |
| **GCP**       | Cloud Logging + Trace        | Combined logs and traces for Cloud Functions.                               |
| **Serverless Framework** | `serverless offline` | Local emulation of AWS, Azure, and GCP services.                           |

---

## **Common Issues and Solutions**

| **Issue**                     | **Diagnosis**                                                                 | **Solution**                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Cold Starts**               | High `Duration` + `Cold Starts` in CloudWatch metrics.                       | Enable Provisioned Concurrency or optimize dependencies.                     |
| **Permission Denied (403)**   | IAM logs show `AccessDenied`.                                                  | Attach correct IAM policy or VPC endpoint policies.                          |
| **Throttling (429)**          | CloudWatch Metric `Throttles` spikes.                                         | Increase reserved concurrency or optimize retries.                          |
| **Missing Event Source**      | Lambda logs show `No invocation events`.                                     | Verify SQS/SNS/DynamoDB Stream permissions and triggers.                     |
| **VPC Connectivity Issues**   | Lambda fails to access RDS.                                                   | Configure VPC Subnets, Security Groups, and NAT Gateway.                    |
| **Dependency Timeouts**       | RDS/DynamoDB latency > 5s.                                                   | Increase timeout in Lambda config or use Provisioned Capacity.              |

---

## **Related Patterns**
1. **[Event-Driven Architecture](https://docs.aws.amazon.com/lambda/latest/dg/arquitecturas-eventos.html)** – Foundational for serverless workflows.
2. **[Canary Deployments](https://aws.amazon.com/blogs/compute/using-aws-lambda-canary-deployments/)** – Safely roll out updates to serverless functions.
3. **[Observability with Distributed Tracing](https://aws.amazon.com/blogs/architecture/distributed-tracing-on-aws/)** – Correlate traces across microservices.
4. **[Retry and Dead Letter Queues (DLQ)](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)** – Handle transient failures in async workflows.
5. **[Infrastructure as Code (IaC)](https://aws.amazon.com/blogs/compute/automating-aws-lambda-function-deployment-with-aws-sam/)** – Manage serverless resources via SAM/Serverless Framework.

---
**Note:** For multi-cloud serverless debugging, use tools like **Datadog** or **New Relic**, which support AWS, Azure, and GCP. Always review vendor documentation for updates.