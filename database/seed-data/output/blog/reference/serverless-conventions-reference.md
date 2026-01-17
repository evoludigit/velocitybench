# **[Pattern] Serverless Conventions Reference Guide**

## **Overview**
**Serverless Conventions** standardize naming, structure, and configuration patterns for serverless resources (functions, APIs, triggers, and infrastructure) to improve maintainability, collaboration, and tooling compatibility. By enforcing consistent conventions across projects, teams can reduce cognitive load, automate deployments, and leverage shared tooling (e.g., IaC templates, CI/CD pipelines, monitoring dashboards).

Key benefits:
- **Predictability**: Resources follow a logical hierarchy and naming scheme.
- **Scalability**: Conventions enable programmatic management (e.g., via Terraform, AWS CDK, or SAM).
- **Security**: Standardized IAM roles, policies, and environment tags simplify audits.
- **Observability**: Uniform metadata (e.g., `function-name`, `environment`) streamlines logging and tracing.

---

## **Schema Reference**

### **1. Function Naming (Best Practices)**
| **Component**       | **Convention**                          | **Example**                          | **Purpose**                                                                 |
|---------------------|-----------------------------------------|---------------------------------------|-----------------------------------------------------------------------------|
| **Prefix**          | `{{project}}-{{service}}`               | `myapp-order`                         | Scopes functions to a service/module.                                      |
| **Verb/Noun**       | Lowercase, hyphen-separated             | `process-payment`                     | Describes the function’s action/resource.                                  |
| **Suffix**          | `-{{environment}}` (optional)          | `process-payment-dev`                 | Denotes staging/production environments.                                   |
| **Max Length**      | 64 chars (AWS Lambda limit)             | *None*—truncate if needed.            | Avoids deployment failures.                                                 |
| **Avoid**           | Punctuation, spaces, special chars      | ❌ `process_payment_v2!`               | Risks conflicts in namespaces or IaC tools.                                  |

---

### **2. Directory Structure (Project Layout)**
```
myapp/
├── src/
│   ├── functions/                  # Source code for Lambda functions
│   │   ├── order/
│   │   │   ├── __init__.py         # Entry point
│   │   │   ├── handler.py          # Lambda logic
│   │   │   └── tests/              # Unit tests
│   │   └── payment/
│   │       ├── handler.py
│   │       └── dependencies/
│   │           └── helpers.py
│   ├── templates/                  # IaC templates (CloudFormation/SAM)
│   │   ├── function.template
│   │   └── api.template
│   └── tests/                      # Integration/tests
│       └── unit/
├── infrastructure/                 # Terraform/CDK modules
│   ├── lambda/
│   │   └── main.tf
│   └── api_gateway/
│       └── gateway.tf
└── .github/                         # CI/CD workflows
    └── deploy.yml
```

---

### **3. Environment Variables**
| **Key**               | **Convention**                          | **Example**                          | **Purpose**                                                                 |
|-----------------------|-----------------------------------------|---------------------------------------|-----------------------------------------------------------------------------|
| **Prefix**            | `{{project}}-{{service}}-`              | `myapp-order-`                        | Reduces namespace collisions.                                               |
| **Format**            | `{{PROP}}_{snake_case}`                 | `PROJECT_ID`, `SERVICE_ENDPOINT`      | Human-readable yet IaC-friendly.                                            |
| **Sensitive Data**    | Use **AWS Secrets Manager** or **Parameter Store** | *None*—avoid hardcoding.           | Enforce via CI/CD or deployment policies.                                   |
| **Default Values**    | Set in IaC (e.g., Terraform `default`)   | `default: "dev"`                      | Minimizes runtime errors.                                                   |

---

### **4. API Gateway Endpoints**
| **Component**       | **Convention**                          | **Example**                          | **Notes**                                                                   |
|---------------------|-----------------------------------------|---------------------------------------|-----------------------------------------------------------------------------|
| **Base Path**       | `/{{service}}/v{{version}}`             | `/orders/v1`                          | Supports versioning and service scoping.                                     |
| **Resource Path**   | `{{noun}}` (plural for collections)     | `/orders`, `/order/{id}`              | Follows REST conventions.                                                   |
| **Method Path**     | `{verb}` (lowercase)                    | `GET`, `POST`                         | Standard HTTP verbs.                                                        |
| **Response Models** | `{{Resource}}Response`                 | `OrderResponse`                       | Enables OpenAPI/Swagger documentation.                                        |

---
### **5. Infrastructure as Code (IaC) Tags**
| **Tag**              | **Key**               | **Value**                          | **Purpose**                                                                 |
|----------------------|-----------------------|-------------------------------------|-----------------------------------------------------------------------------|
| **Project**          | `project`             | `myapp`                             | Groups resources across environments.                                       |
| **Service**          | `service`             | `order-service`                     | Isolates bills/permissions per module.                                       |
| **Environment**      | `environment`         | `dev`, `prod`                       | Enables multi-environment tooling (e.g., AWS Organizations).               |
| **Owner**            | `owner`               | `team-frontend`                     | Assigns accountability.                                                     |
| **Cost Center**      | `cost-center`         | `dept-marketing`                     | Tracks cloud spend.                                                          |
| **Automation**       | `automated-deploy`    | `true`/`false`                      | Flags manual vs. CI/CD deployments.                                          |

---

### **6. IAM Roles & Policies**
| **Component**       | **Convention**                          | **Example**                          | **Notes**                                                                   |
|---------------------|-----------------------------------------|---------------------------------------|-----------------------------------------------------------------------------|
| **Role Name**       | `arn:aws:iam::{{account}}:role/{{project}}-{{service}}-{{function}}` | `arn:aws:iam::123456789012:role/myapp-order-process-payment` | Avoids hardcoding ARNs in code. |
| **Policy Document** | Use **AWS Managed Policies** + **Custom Scoped Policies** | `AWSLambdaBasicExecutionRole` + `s3:GetObject` | Least privilege principle. |
| **Trust Policy**    | Allow only `lambda.amazonaws.com` or `apigateway.amazonaws.com` | `{ "Principal": "lambda.amazonaws.com" }` | Restricts role use to serverless triggers. |

---

### **7. Logging & Monitoring**
| **Component**       | **Convention**                          | **Example**                          | **Tools**                                                                   |
|---------------------|-----------------------------------------|---------------------------------------|-----------------------------------------------------------------------------|
| **Log Group**       | `/aws/lambda/{{project}}-{{service}}-{{function}}` | `/aws/lambda/myapp-order-process-payment` | CloudWatch Logs |
| **Log Stream**      | Auto-generated by Lambda.               | *None*—use `aws:RequestId` for correlation. | CloudWatch Insights |
| **Metrics Namespace** | `{{project}}/{{service}}`              | `myapp/orders`                        | CloudWatch Metrics (e.g., `Invocations`, `Errors`). |
| **X-Ray Trace Header** | `X-Amzn-Trace-Id`                      | `Root=1-6382e4f4-8a2e4b324b324b32`   | AWS X-Ray for distributed tracing. |

---

## **Query Examples**

### **1. AWS CLI: List Functions by Service**
```bash
aws lambda list-functions \
  --query "Functions[?contains(Name, `myapp-order`)].FunctionName" \
  --output text
```
**Output:**
```
myapp-order-process-payment-dev
myapp-order-process-payment-prod
```

---

### **2. Terraform: Deploy Functions with Tags**
```hcl
resource "aws_lambda_function" "order_processor" {
  function_name = "myapp-order-process-payment-dev"
  filename      = "function.zip"
  handler       = "handler.main"

  tags = {
    project    = "myapp"
    service    = "order-service"
    environment = "dev"
    owner      = "team-backend"
  }
}
```

---

### **3. OpenAPI/Swagger: Define API Endpoints**
```yaml
paths:
  /orders/v1:
    post:
      summary: Create an order
      operationId: createOrder
      x-amazon-apigateway-integration:
        uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${createOrderLambda.Arn}/invocations
        httpMethod: POST
        type: aws_proxy
```

---

### **4. Python (Boto3): Tag Resources Programmatically**
```python
import boto3

client = boto3.client("lambda")

response = client.add_permission(
    FunctionName="myapp-order-process-payment-dev",
    StatementId="apigw-invoke",
    Action="lambda:InvokeFunction",
    Principal="apigateway.amazonaws.com",
    SourceArn="arn:aws:execute-api:us-east-1:123456789012:abc123/*/POST/orders/v1"
)

# Apply tags to the function
client.add_tags(
    Resource="arn:aws:lambda:us-east-1:123456789012:function:myapp-order-process-payment-dev",
    Tags={
        "project": "myapp",
        "environment": "dev"
    }
)
```

---

## **Related Patterns**

1. **Infrastructure as Code (IaC)**
   - *Why*: Serverless Conventions rely on IaC (Terraform, AWS CDK, SAM) for reproducibility.
   - *Key Reference*: [AWS Serverless Application Model (SAM)](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)

2. **Environment Parity**
   - *Why*: Standardized environments reduce "works on my machine" issues.
   - *Key Reference*: [12-Factor App](https://12factor.net/) (config files, secrets management).

3. **Canary Deployments**
   - *Why*: Conventions enable gradual rollouts (e.g., `canary-%` in function names).
   - *Key Reference*: [AWS CodeDeploy](https://aws.amazon.com/codedeploy/features/) + Lambda aliases.

4. **Event-Driven Architecture**
   - *Why*: Serverless excels with event sources (SQS, DynamoDB Streams). Conventions ensure consistent event schemas.
   - *Key Reference*: [EventBridge Patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html).

5. **Cost Optimization**
   - *Why*: Tagging conventions enable fine-grained cost allocation.
   - *Key Reference*: [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) + `cost-center` tags.

6. **Security Hardening**
   - *Why*: Standardized IAM roles and policies reduce misconfigurations.
   - *Key Reference*: [AWS Well-Architected Serverless Lens](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html).

---
## **Further Reading**
- [AWS Serverless Application Repository](https://aws.amazon.com/serverless/serverlessrepo/) (pre-configured templates).
- [Serverless Framework Conventions](https://www.serverless.com/framework/docs/providers/aws/guide/functions/#naming-functions) (alternative to AWS-native conventions).
- [Google Cloud Functions Naming Guide](https://cloud.google.com/functions/docs/concepts/function-naming) (adaptable for multi-cloud).