# **Debugging Serverless Conventions: A Troubleshooting Guide**

Serverless Conventions refer to a set of best practices and implementation guidelines for structuring, deploying, and managing serverless applications. This pattern ensures consistency across developers, reduces complexity, and improves maintainability. However, even well-designed serverless architectures can encounter issues.

This guide provides a structured approach to diagnosing and resolving common problems in serverless applications following Serverless Conventions.

---

## **1. Symptom Checklist**

Before diving into debugging, assess the following symptoms to narrow down potential issues:

| **Symptom**                          | **Possible Causes** |
|--------------------------------------|---------------------|
| **Deployment failures**              | Incorrect IAM roles, permission issues, YAML/CloudFormation errors |
| **Cold starts or high latency**      | Improper function configuration, missing dependencies, inefficient triggers |
| **Permission errors (403, 401)**     | Misconfigured IAM roles, resource policies, or missing API Gateway authorizers |
| **Timeout errors (504, 503)**        | Function timeouts set too low, inefficient code, or external dependencies slow |
| **Resource exhaustion (Memory/CPU)** | Insufficient memory allocation, inefficient loops, or unoptimized dependencies |
| **Logging/Monitoring missing**       | Incorrect CloudWatch permissions, logging disabled, or missing X-Ray tracing |
| **Inconsistent environment variables** | Hardcoded values, incorrect secret management, or misconfigured parameter store |
| **Event loop delays**                | Poorly structured async code, missing retries, or deadlocks |
| **Vendor-specific deployment issues** | AWS Lambda cold starts, Google Cloud Run scaling delays, Azure Functions timeouts |

---
## **2. Common Issues and Fixes**

### **Issue 1: Deployment Failures (IAM, YAML Errors, Permissions)**
**Symptoms:**
- `Template format error`, `Validation error`, `Permission denied`
- Deployment stuck in `CREATE_IN_PROGRESS` with no logs

**Root Causes:**
- Incorrect IAM role policies
- Missing or extra YAML/CloudFormation sections
- Resource not authorized (e.g., S3, DynamoDB)

**Debugging Steps:**
1. **Check CloudFormation/YAML errors**
   ```bash
   aws cloudformation validate-template --template-body file://template.yaml
   ```
   - Look for missing `Resources`, `Policies`, or `Mappings`.

2. **Verify IAM roles**
   ```bash
   aws iam get-role --role-name <your-role-name>
   ```
   - Ensure the role has:
     - `AWSLambdaBasicExecutionRole` (for logs)
     - Required permissions (e.g., `dynamodb:PutItem`, `s3:GetObject`)

3. **Fix: Update IAM Role**
   ```yaml
   # Example IAM Policy for Lambda
   Resources:
     MyLambdaRole:
       Type: AWS::IAM::Role
       Properties:
         AssumeRolePolicyDocument:
           Version: "2012-10-17"
           Statement:
             - Effect: Allow
               Principal:
                 Service: lambda.amazonaws.com
               Action: sts:AssumeRole
         Policies:
           - PolicyName: LambdaDynamoAccess
             PolicyDocument:
               Version: "2012-10-17"
               Statement:
                 - Effect: Allow
                   Action:
                     - dynamodb:PutItem
                     - dynamodb:GetItem
                   Resource: "arn:aws:dynamodb:*:*:table/MyTable"
   ```

---

### **Issue 2: Cold Starts & High Latency**
**Symptoms:**
- First request takes **500ms–3s+**
- Consistently high `Duration` in CloudWatch

**Root Causes:**
- No provisioned concurrency
- Large deployment packages (>50MB)
- Missing optimizations (e.g., layer reuse)

**Debugging Steps:**
1. **Check Lambda Configuration**
   ```bash
   aws lambda get-function-configuration --function-name <function-name>
   ```
   - Verify `Memory` (e.g., 1.5GB for heavy workloads)
   - Check `Timeout` (default 3s may be too low)

2. **Enable Provisioned Concurrency**
   ```bash
   aws lambda put-provisioned-concurrency-config --function-name <function> --qualifier $LATEST --provisioned-concurrent-executions 5
   ```
   - Reduces cold starts by keeping instances warm.

3. **Optimize Deployment Package**
   - Remove unused dependencies (`npm prune --production`)
   - Use **Layers** for shared libraries
   ```python
   # Example: Using Layers in Python
   import os
   os.environ['PATH'] += os.pathsep + '/opt/python/lib/python3.8/site-packages'
   ```

---

### **Issue 3: Permission Errors (403/401)**
**Symptoms:**
- `AccessDeniedException` in DynamoDB
- `UnrecognizedClientException` in API Gateway

**Root Causes:**
- Incorrect resource-based policies
- Missing `Resource` in IAM policies

**Debugging Steps:**
1. **Check CloudTrail Logs**
   ```bash
   aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AuthFailure
   ```
   - Identify which resource was denied access.

2. **Fix: Update API Gateway & DynamoDB Policies**
   ```yaml
   # Example: API Gateway Authorizer
   Resources:
     MyApiAuthorizer:
       Type: AWS::ApiGateway::Authorizer
       Properties:
         Name: CognitoAuthorizer
         Type: COGNITO_USER_POOLS
         IdentitySource: method.request.header.Authorization
         ProviderARNs:
           - !GetAtt MyUserPool.Arn
   ```

   ```yaml
   # Example: DynamoDB Table Policy
   Resources:
     MyDynamoTable:
       Type: AWS::DynamoDB::Table
       Properties:
         TableName: MyTable
         AttributeDefinitions:
           - AttributeName: id
             AttributeType: S
         KeySchema:
           - AttributeName: id
             KeyType: HASH
         Policy:
           Version: "2012-10-17"
           Statement:
             - Effect: Allow
               Principal:
                 AWS: !GetAtt MyLambdaRole.Arn
               Action: dynamodb:*
               Resource: !GetAtt MyDynamoTable.Arn
   ```

---

### **Issue 4: Timeouts (504/503 Errors)**
**Symptoms:**
- Lambda fails after **3s/6s/9s** (default timeout)
- External API calls hanging

**Root Causes:**
- Sync I/O blocking (e.g., slow DB queries)
- Missing retries for transient failures

**Debugging Steps:**
1. **Check Lambda Logs**
   ```bash
   aws logs tail /aws/lambda/<function> --follow
   ```
   - Look for `END RequestId:... Duration: 2900 ms`

2. **Increase Timeout & Memory**
   ```bash
   aws lambda update-function-configuration \
     --function-name <function> \
     --timeout 30 \
     --memory-size 1024
   ```

3. **Fix: Use Async Calls & Retries**
   ```python
   import boto3
   from botocore.config import Config

   def call_external_api():
       client = boto3.client('dynamodb', config=Config(retries={'max_attempts': 3}))
       try:
           response = client.get_item(TableName='MyTable', Key={'id': {'S': '123'}})
           return response['Item']
       except Exception as e:
           print(f"Retry failed: {e}")
           raise
   ```

---

### **Issue 5: Missing Logging/Monitoring**
**Symptoms:**
- No CloudWatch logs
- X-Ray traces show missing segments

**Root Causes:**
- Incorporation of Lambda layers for X-Ray
- Incorrect log retention policy

**Debugging Steps:**
1. **Verify Lambda Logging**
   ```bash
   aws logs describe-log-streams --log-group-name /aws/lambda/<function>
   ```
   - Ensure `BasicExecutionRole` allows `logs:CreateLogGroup`.

2. **Enable X-Ray**
   ```bash
   aws lambda update-function-configuration \
     --function-name <function> \
     --tracing-config Mode=Active
   ```

3. **Fix: Configure Log Retention**
   ```bash
   aws logs put-log-event-selector-policy \
     --log-group-name /aws/lambda/<function> \
     --policy-name RetentionPolicy \
     --policy '{"logGroupPermissions": [{"Principal": "*", "Action": "logs:FilterLogEvent"}]}'
   ```

---

## **3. Debugging Tools & Techniques**

| **Tool**              | **Use Case** |
|-----------------------|-------------|
| **AWS CloudWatch Logs Insights** | Query logs (`filter @message like /ERROR/`) |
| **AWS X-Ray** | Trace requests across services |
| **AWS SAM CLI** | Local testing (`sam local invoke`) |
| **Terraform Plan/Apply** | Detect drift (`terraform plan`) |
| **Postman/Newman** | Test API Gateway endpoints |
| **Lambda Powertools** | Structured logging (`logger` object) |

**Example: Debugging with SAM CLI**
```bash
sam build --use-container  # Build Docker image
sam local invoke -e event.json MyFunction  # Test locally
```

---

## **4. Prevention Strategies**

### **Best Practices for Serverless Conventions**
1. **Enforce Naming Conventions**
   - Use `-function-{stage}-{service}` (e.g., `process-order-dev-payments`).
   - Tools like **GitHub Actions** can enforce **regex-based checks**.

2. **Use Infrastructure as Code (IaC)**
   - **AWS SAM** or **Terraform** for repeatable deployments.
   ```yaml
   # SAM Template Example
   Resources:
     MyFunction:
       Type: AWS::Serverless::Function
       Properties:
         CodeUri: ./src
         Handler: app.lambda_handler
         Runtime: python3.8
         MemorySize: 512
         Timeout: 10
   ```

3. **Centralize Secrets & Configs**
   - Use **AWS Secrets Manager** or **Parameter Store** (SSM).
   ```python
   import boto3
   client = boto3.client('ssm')
   db_password = client.get_parameter(Name='/apps/db/password', WithDecryption=True)['Parameter']['Value']
   ```

4. **Implement Canary Deployments**
   - Gradually roll out changes with **AWS CodeDeploy**.
   ```bash
   aws deploy create-deployment \
     --application-name MyApp \
     --deployment-config-name CodeDeployDefault.OneAtATime \
     --deployment-group-name MyLambdaGroup
   ```

5. **Monitor & Alert Early**
   - Set **CloudWatch Alarms** for errors/throttles.
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name HighErrorRate \
     --metric-name Errors \
     --namespace AWS/Lambda \
     --statistic Sum \
     --period 60 \
     --threshold 5 \
     --comparison-operator GreaterThanThreshold \
     --evaluation-periods 1 \
     --alarm-actions arn:aws:sns:us-east-1:123456789012:MyTopic
   ```

6. **Optimize Dependencies**
   - Use **layers** for shared libraries.
   ```bash
   sam package --output-template-file packaged.yaml --s3-bucket my-bucket
   ```

7. **Conduct Postmortems**
   - Document failures in a **wikidata** or **Confluence page** for future reference.

---

## **5. Final Checklist for Quick Resolution**
| **Step** | **Action** |
|----------|------------|
| **1. Check Logs** | `aws logs tail /aws/lambda/<function>` |
| **2. Validate IAM** | `aws iam list-roles` → `get-role` |
| **3. Review Timeout/Memory** | `aws lambda update-function-configuration` |
| **4. Test Locally** | `sam local invoke -e event.json` |
| **5. Enable X-Ray** | `tracing-config Mode=Active` |
| **6. Alert on Errors** | Set CloudWatch Alarms |

---

### **Conclusion**
Serverless Conventions help maintain clean, scalable architectures, but debugging issues requires a structured approach. By following this guide:
- **Deployments** become reliable.
- **Cold starts** are minimized.
- **Permissions** and **timeouts** are proactively managed.
- **Logging & monitoring** are enforced.

Use **SAM CLI**, **X-Ray**, and **IaC** to automate and simplify debugging. Prevention (naming, secrets, canary deployments) is key to avoiding future issues.