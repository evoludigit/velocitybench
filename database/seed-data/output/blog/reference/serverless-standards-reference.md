# **[Pattern] Serverless Standards Reference Guide**

## **Overview**
The **Serverless Standards** pattern ensures consistency, reliability, and maintainability across serverless architectures by enforcing uniform design principles, naming conventions, deployment methodologies, and operational best practices. Unlike traditional serverless patterns (e.g., Event-Driven, Microservices, or Pipeline Orchestration), this pattern focuses on **standardizing implementation details**—such as IAM policies, environment variables, logging structures, error handling, and deployment templates—to reduce cognitive load, minimize operational drift, and improve traceability.

This guide outlines key components of the **Serverless Standards** pattern, including required schema, implementation rules, and example configurations. Adopting these standards streamlines collaboration, simplifies debugging, and accelerates serverless development cycles while adhering to cloud provider best practices.

---

## **1. Schema Reference**

| **Component**               | **Description**                                                                                                                                                     | **Required** | **Example Value**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|--------------------------------------------------------------------------------------------------------|
| **Project Naming**          | Standardized naming convention for serverless projects (e.g., `Naming-Convention-{service}-{environment}`).                                                         | ✅ Yes        | `aws-serverless-compliance-{auth}-prod`                                                              |
| **IAM Role Policies**       | Predefined cross-account and service-specific IAM policies (e.g., AWS Lambda Execution Role, SQS/SNS permissions).                                                   | ✅ Yes        | `{ "Effect": "Allow", "Action": ["lambda:InvokeFunction"], "Resource": ["arn:aws:lambda:us-east-1:123456789012:function:AuthService"] }` |
| **Environment Variables**   | Structured key-value pairs for configuration (e.g., `API_GATEWAY_URL`, `DB_TABLE_NAME`). Must follow `UPPER_CASE_WITH_UNDERSCORES`.                                      | ✅ Yes        | `APP_ENV=prod`, `LOG_LEVEL=INFO`                                                                       |
| **Log Format**              | JSON-structured logging format with mandatory fields (e.g., `requestId`, `timestamp`, `level`, `serviceName`).                                                     | ✅ Yes        | `{"requestId":"abc123","timestamp":"2023-11-15T12:00:00Z","level":"ERROR","serviceName":"AuthService","message":"UserNotFoundError"}` |
| **Error Handling**          | Standardized HTTP status codes and error formats (e.g., `403 Forbidden` with a `{"error":"Forbidden"}` JSON payload).                                             | ✅ Yes        | `{
    "statusCode": 400,
    "body": JSON.stringify({"error": "InvalidInput", "details": "Missing 'email' field"})
  }`                                                                                              |
| **Deployment Template**     | CloudFormation/SAM/Terraform template includes reusable modules for Lambda, API Gateway, DynamoDB, etc.                                                             | ✅ Yes        | [AWS SAM Example](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification.html) |
| **Monitoring Metrics**      | CloudWatch metrics and alarms (e.g., `Invocations`, `Duration`, `Errors`) with standardized naming (`{serviceName}/MetricName`).                                       | ✅ Yes        | `/lambda/auth-service/invocations`                                                                     |
| **Security Policies**       | Hardened security defaults (e.g., VPC configurations, encryption at rest/transit, principle of least privilege).                                                   | ✅ Yes        | `{"VPCId": "vpc-12345678", "SecurityGroupIds": ["sg-12345678"]}`                                        |
| **Documentation**           | Embedded documentation (e.g., AWS SAM `Metadata` or Terraform `description` comments) for each resource.                                                             | ✅ Yes        | `# API Gateway: Processes auth requests for the AuthService`                                          |

---

## **2. Implementation Details**

### **2.1 Project Structure**
A standardized serverless project follows this structure:
```
project-root/
├── cloud/                     # CloudFormation/SAM/Terraform templates
│   ├── auth-service/
│   │   ├── template.yaml      # SAM template with IAM roles, Lambda, API Gateway
│   │   └── metadata.json      # Embedded documentation
├── src/                       # Application code
│   ├── auth-service/
│   │   ├── lambda/
│   │   │   ├── auth-handler.js  # Business logic
│   │   └── tests/             # Unit/integration tests
├── .github/workflows/         # CI/CD pipelines (e.g., GitHub Actions)
│   └── deploy.yml
└── README.md                  # High-level overview, usage, and compliance notes
```

### **2.2 IAM Role Standards**
- **Lambda Execution Roles:**
  - Name convention: `lambda-${project}-${service}-role`
  - Scope to the **least-privilege** principle (e.g., avoid `*` in resource ARNs).
  - Use **AWS Managed Policies** where possible (e.g., `AWSLambdaBasicExecutionRole`).
  - Example:
    ```yaml
    # SAM template snippet
    AuthServiceRole:
      Type: AWS::IAM::Role
      Properties:
        RoleName: lambda-auth-service-role
        AssumeRolePolicyDocument:
          Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Principal:
                Service: lambda.amazonaws.com
              Action: sts:AssumeRole
        Policies:
          - PolicyName: LambdaBasicExecution
            PolicyDocument:
              {
                "Version": "2012-10-17",
                "Statement": [
                  {
                    "Effect": "Allow",
                    "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                    "Resource": "*"
                  }
                ]
              }
          - PolicyName: DynamoDBAccess
            PolicyDocument:
              {
                "Version": "2012-10-17",
                "Statement": [
                  {
                    "Effect": "Allow",
                    "Action": ["dynamodb:GetItem", "dynamodb:PutItem"],
                    "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/AuthUsers"
                  }
                ]
              }
    ```

### **2.3 Logging Standards**
- **Log Format:**
  Use **structured JSON** with mandatory fields:
  ```json
  {
    "requestId": "unique-correlation-id",
    "timestamp": "ISO-8601",
    "level": "INFO/WARN/ERROR",
    "serviceName": "auth-service",
    "message": "Resolution attempt for user: alice@example.com",
    "context": { "userId": "123", "action": "login" }
  }
  ```
- **Tools:**
  - **AWS Lambda:** Use `console.log(JSON.stringify())` or libraries like `pino`.
  - **API Gateway:** Forward request/response headers to CloudWatch.
  - **Example (Node.js):**
    ```javascript
    const logger = pino({
      level: process.env.LOG_LEVEL || 'info',
      timestamp: () => `,"timestamp": "${new Date().toISOString()}"`
    });
    logger.info({ context: { userId: '123' } }, 'User logged in');
    ```

### **2.4 Error Handling**
- **Standardized Responses:**
  Return **HTTP status codes** with JSON payloads:
  | Status Code | Error Type          | Example Payload                                                                 |
  |-------------|---------------------|---------------------------------------------------------------------------------|
  | `400`       | InvalidInput        | `{"error": "InvalidInput", "message": "Missing 'email' field"}`                 |
  | `401`       | Unauthorized        | `{"error": "Unauthorized", "message": "Invalid token"}`                         |
  | `403`       | Forbidden           | `{"error": "Forbidden", "message": "Insufficient permissions"}`                |
  | `500`       | InternalError       | `{"error": "InternalError", "message": "Service unavailable"}`                  |
- **Retryable vs. Non-Retryable:**
  - **Retryable:** `500`, `503`, `429` (with exponential backoff).
  - **Non-Retryable:** `400`, `401`, `403`.

### **2.5 Deployment Standards**
- **Infrastructure as Code (IaC):**
  - Use **AWS SAM**, **Terraform**, or **CloudFormation**.
  - Example SAM template (`template.yaml`):
    ```yaml
    Resources:
      AuthServiceFunction:
        Type: AWS::Serverless::Function
        Properties:
          FunctionName: auth-service
          Runtime: nodejs18.x
          Handler: index.handler
          CodeUri: ./src/auth-service/lambda
          Environment:
            Variables:
              TABLE_NAME: !Ref AuthUsersTable
              LOG_LEVEL: INFO
          Policies:
            - DynamoDBCrudPolicy:
                TableName: !Ref AuthUsersTable
          Events:
            ApiEvent:
              Type: Api
              Properties:
                Path: /auth
                Method: POST
    ```
- **CI/CD Pipeline:**
  - **Triggers:** On `git push` to `main` or tagged releases.
  - **Steps:**
    1. Lint code.
    2. Run unit/integration tests.
    3. Package and deploy using `sam deploy` or `terraform apply`.
    4. Verify deployment via CloudWatch.

### **2.6 Monitoring and Alerts**
- **CloudWatch Metrics:**
  - **Lambda:** `Invocations`, `Duration`, `Errors`, `Throttles`.
  - **API Gateway:** `Latency`, `4XX/5XX Errors`.
  - **Example Alarm (SAM):**
    ```yaml
    AuthServiceErrorsAlarm:
      Type: AWS::CloudWatch::Alarm
      Properties:
        AlarmName: auth-service-errors-alarm
        ComparisonOperator: GreaterThanThreshold
        EvaluationPeriods: 1
        MetricName: Errors
        Namespace: AWS/Lambda
        Period: 300
        Statistic: Sum
        Threshold: 0
        Dimensions:
          - Name: FunctionName
            Value: !Ref AuthServiceFunction
        AlarmDescription: "Alarm when AuthService has errors"
    ```

### **2.7 Security Standards**
- **VPC Configuration:**
  - Place Lambda functions in a **private subnet** if accessing RDS/ElastiCache.
  - Use **VPC endpoints** for AWS services (e.g., DynamoDB, S3).
- **Encryption:**
  - Enable **KMS encryption** for secrets (e.g., `SecretsManager`).
  - Use **TLSS endpoints** for API Gateway.
- **IAM:**
  - Avoid hardcoded credentials; use **IAM roles** and **SSM Parameter Store**.

---

## **3. Query Examples**

### **3.1 CloudWatch Logs Query**
Filter logs for errors in `auth-service`:
```sql
filter @message like /ERROR/
| stats count(*) by serviceName, @timestamp
| sort @timestamp desc
```

### **3.2 SAM Deploy Command**
Deploy the `auth-service` with specific parameters:
```bash
sam deploy \
  --template-file cloud/auth-service/template.yaml \
  --stack-name auth-service-prod \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides Environment=prod TableName=AuthUsersTable
```

### **3.3 AWS CLI IAM Policy Validation**
Validate a Lambda function’s IAM role policy:
```bash
aws iam get-policy --policy-arn arn:aws:iam::123456789012:policy/lambda-auth-service-role
```

### **3.4 API Gateway Test Invocation**
Test the `POST /auth` endpoint locally:
```bash
sam local invoke AuthServiceFunction -e event.json
```
Where `event.json`:
```json
{
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"email\": \"user@example.com\", \"password\": \"secure123\"}"
}
```

---

## **4. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                             |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Event-Driven Architecture** | Decouples components using events (e.g., SQS, SNS, EventBridge).                                                                                                                                                     | When building scalable, asynchronous systems.                                                              |
| **Pipeline Orchestration** | Chains serverless functions using Step Functions for complex workflows.                                                                                                                                           | For multi-stage processes (e.g., ETL, approval workflows).                                                  |
| **Canary Deployments**     | Gradually roll out changes to a subset of traffic.                                                                                                                                                               | For zero-downtime updates with risk mitigation.                                                              |
| **Cold Start Mitigation**  | Optimizes Lambda initialization (e.g., provisioned concurrency, smaller packages).                                                                                                                               | When low-latency is critical for user-facing services.                                                        |
| **Multi-Region Deployment** | Deploy identical serverless stacks across regions for failover.                                                                                                                                                   | For global low-latency or disaster recovery.                                                                |
| **Observability as Code**  | Embeds monitoring and logging configurations in IaC.                                                                                                                                                               | When operational visibility is part of the deployment pipeline.                                             |

---

## **5. Best Practices**
1. **Automate Compliance Checks:**
   - Use tools like **AWS Config Rules** or **Open Policy Agent (OPA)** to enforce standards.
   - Example: Block deployments if Lambda memory exceeds `512MB`.
2. **Document Exceptions:**
   - Justify deviations from standards in a `DEVIATIONS.md` file.
3. **Update Regularly:**
   - Revisit standards 2–3 times/year to align with new cloud features (e.g., AWS Graviton2).
4. **Onboard Teams:**
   - Provide a **cheat sheet** and **interactive tutorial** for new developers.
5. **Measure Adoption:**
   - Track compliance via GitHub checks or CI/CD pipeline badges (e.g., "✅ Standards Passed").

---
**Last Updated:** [YYYY-MM-DD]
**Owner:** [Team/Contact]
**Version:** 1.2