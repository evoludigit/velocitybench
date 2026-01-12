# **[Pattern] CloudFront Distribution Integration Reference Guide**

---

## **Overview**
This guide describes **CloudFront Distribution Integration Patterns**, providing technical implementation details, best practices, and troubleshooting insights. CloudFront, AWS’s content delivery network (CDN), distributes static and dynamic content with low latency globally. This pattern covers:
- **Basic integration** (clearing cache, origin configurations)
- **Advanced workflows** (A/B testing, dynamic content routing)
- **Security & optimization** (signed cookies, field-level encryption)
- **Monitoring & debugging** (CloudWatch metrics, custom logging)

Use this reference for **AWS CloudFront developers**, DevOps engineers, and architects integrating CloudFront with origins (S3, ALB, EC2, Lambda@Edge).

---

## **1. Key Concepts & Implementation Details**

### **1.1 Core Components**
| **Component**          | **Description**                                                                                     | **Purpose**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Distribution**       | A CloudFront distribution maps domains to origin servers and cache settings.                         | Global content delivery endpoint.                                                              |
| **Cache Behavior**     | Rules defining how CloudFront caches requests (e.g., by path, query strings, headers).              | Controls caching granularity (e.g., `/images/` vs. `/images/*`).                                |
| **Origin**             | Backend server (S3, ALB, EC2, Lambda@Edge) serving content to CloudFront.                           | Originates the content pushed to CloudFront’s edge locations.                                    |
| **Lambda@Edge**        | Serverless functions running at CloudFront edge locations for dynamic logic.                          | Custom request/response transformations (e.g., A/B testing, auth).                              |
| **Signed Cookies/URLs**| Temporary access controls for private content via signed cookies or URLs.                          | Restricts access to premium content or APIs.                                                   |
| **Field-Level Encryption** | Encrypts specific response fields (e.g., PII) at the edge.                                          | Compliance with data protection regulations (e.g., GDPR).                                        |

---

### **1.2 Common Integration Patterns**

#### **Pattern 1: Basic Static Website Hosting**
- **Use Case:** Serve static assets (HTML, CSS, JS) from S3.
- **Steps:**
  1. Set up an **S3 bucket** with your website files.
  2. Configure **CloudFront origin** pointing to the S3 bucket.
  3. Add **cache behaviors** for `/` (HTML) and `/images/*` (assets).
  4. Enable **alternative domain name (CNAME)** for custom domains.
- **Best Practices:**
  - Use **S3 static website hosting** for the origin.
  - Set **TTL to 1 hour** for dynamic content (e.g., `/dashboard`).
  - Enable **compression** (Gzip/Brotli) in CloudFront.

#### **Pattern 2: Dynamic Content with ALB**
- **Use Case:** Serve dynamic APIs or server-rendered apps (e.g., React, Node.js).
- **Steps:**
  1. Deploy backend on **ALB** (or EC2/ECS).
  2. Configure **CloudFront origin** as the ALB’s DNS name.
  3. Add **cache behavior** for `/api/*` with **Forward Query Strings = Yes**.
  4. Use **Lambda@Edge** to:
     - Redirect regional users to regional APIs.
     - Validate JWT tokens in headers preemptively.
- **Best Practices:**
  - Disable caching for **POST/PUT** requests (`Cache-Control: no-store`).
  - Use **Query String Forwarding** for dynamic data.

#### **Pattern 3: A/B Testing with Lambda@Edge**
- **Use Case:** Route users to different versions (V1/V2) of a webpage.
- **Implementation:**
  1. Add **Lambda@Edge** to the **Viewer Request** event.
  2. Use `getViewerCookie()` to detect user segments (e.g., `A/B=V2`).
  3. Rewrite the URL to point to the appropriate origin (S3 bucket).
- **Example Code Snippet:**
  ```javascript
  exports.handler = async (event) => {
    const cookie = event.Records[0].cf.request.cookies.A_B;
    const routeKey = cookie === 'V2' ? '/v2/' : '/v1/';
    const request = event.Records[0].cf.request;
    request.uri = routeKey + request.uri;
    return request;
  };
  ```
- **Best Practices:**
  - Test Lambda@Edge in **dev/stage** before production.
  - Monitor **Lambda errors** in CloudWatch.

#### **Pattern 4: Signed Cookies for Private Content**
- **Use Case:** Restrict access to premium videos or APIs.
- **Steps:**
  1. Generate **signed cookies** in your backend (e.g., using AWS Signer).
  2. Configure CloudFront to **require signed cookies** for `/private/*`.
  3. Set **TTL and permissions** (e.g., `Path=/private`, `TTL=1 hour`).
- **Example Policy:**
  ```json
  {
    "KeyPath": "/private/*",
    "TTL": 3600,
    "Expires": "2024-01-01T00:00:00Z",
    "Private": true
  }
  ```

#### **Pattern 5: Field-Level Encryption**
- **Use Case:** Mask sensitive fields (e.g., credit cards) in API responses.
- **Steps:**
  1. Enable **Field-Level Encryption** in CloudFront distribution.
  2. Configure **encryption keys** (AWS KMS or custom).
  3. Define **encryption rules** for headers/fields (e.g., `X-Sensitive-Data`).
- **Best Practices:**
  - Use KMS for key rotation.
  - Test encryption/decryption in **dev** before production.

---

## **2. Schema Reference**

| **Attribute**               | **Type**       | **Description**                                                                                     | **Example Value**                     |
|-----------------------------|----------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| **Distribution ID**         | String         | Unique identifier for the CloudFront distribution.                                                   | `E1Q2R3S4T5W6X7Y8Z9`                   |
| **Origin Domain**           | String         | DNS name of the origin (S3 bucket, ALB, etc.).                                                       | `my-app.s3.amazonaws.com`              |
| **Cache Behavior Path**     | String Array   | Paths matched by the behavior (e.g., `["/*", "/images/*"]`).                                         | `["/*"]`                               |
| **TTL (Default)**           | Integer (sec)  | Default Time-To-Live for cached objects.                                                             | `3600` (1 hour)                        |
| **Forward Query Strings**   | Boolean        | Whether to forward query strings to the origin.                                                      | `true`                                 |
| **Signed Cookies**          | JSON Object    | Signed cookie policy (KeyPath, TTL, Private).                                                        | `{"KeyPath": "/private/*", "TTL": 3600}` |
| **Lambda@Edge ARN**         | String         | ARN of the Lambda function deployed at CloudFront edge.                                              | `arn:aws:lambda:us-east-1:123456789012:function:edge-function` |
| **Field-Level Encryption**  | Boolean        | Enable/disable field-level encryption.                                                              | `true`                                 |

---

## **3. Query Examples**

### **3.1 Creating a Distribution via AWS CLI**
```bash
aws cloudfront create-distribution \
  --origin-domain-name="my-app.s3.amazonaws.com" \
  --default-root-object="index.html" \
  --cache-behavior 'PathPattern=/*,TargetOriginId=my-origin,ForwardedValues={QueryString=true},TTL=3600' \
  --enabled
```

### **3.2 Updating Cache Behavior**
```bash
aws cloudfront update-distribution \
  --id="E1Q2R3S4T5W6X7Y8Z9" \
  --cache-behavior 'PathPattern=/api/*,TargetOriginId=api-lb,ForwardedValues={QueryString=true},TTL=60'
```

### **3.3 Validating Signed Cookie**
```bash
aws cloudfront get-signer-cookie \
  --key-pair-id="ABCD1234EFGH" \
  --distribution-id="E1Q2R3S4T5W6X7Y8Z9" \
  --ttl="3600" \
  --key-path="/private/*"
```

### **3.4 Lambda@Edge Test Invocation**
```bash
aws lambda invoke \
  --function-name="edge-ab-test" \
  --payload '{"region": "us-west-2", "cookie": {"A_B": "V2"}}' \
  ./response.json
```

---

## **4. Best Practices & Pitfalls**

### **Best Practices**
1. **Cache Strategically:**
   - Cache static assets (CSS/JS) aggressively (`TTL=1 year`).
   - Disable caching for dynamic content (`Cache-Control: no-store`).
2. **Use Lambda@Edge Wisely:**
   - Test in **dev** before production.
   - Monitor **Lambda errors** in CloudWatch Logs.
3. **Secure Origins:**
   - Use **custom SSL certificates** (ACM) for origins.
   - Enable **Origin Shield** to reduce origin load.
4. **Monitor Performance:**
   - Set up **CloudWatch Alarms** for `4XX/5XX` errors.
   - Use **CloudFront Real-Time Logs** for debugging.

### **Common Pitfalls**
- **Cache Stampede:** Too many requests miss cache (use **TTL tuning**).
- **Lambda Timeouts:** Lambda@Edge has a **5-second timeout** (optimize code).
- **Signed Cookie Expiry:** Forgetting to update **TTL** causes broken access.
- **Origin Failures:** Failing to monitor **origin health checks** leads to downtime.

---

## **5. Related Patterns**
1. **[Origin Shield Optimization]**
   - Reduces origin server load by using AWS CloudFront edge locations.
   - *See:* [AWS Docs - Origin Shield](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html)

2. **[Lambda@Edge for Auth]**
   - Validate JWT tokens or IP restrictions at the edge.
   - *See:* [Lambda@Edge Use Cases](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html)

3. **[S3 + CloudFront + API Gateway]**
   - Hybrid setup for static sites + dynamic APIs.
   - *See:* [API Gateway + CloudFront Integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-ways-to-integrate.html)

4. **CloudFront + ALB for Microservices**
   - Route traffic to different ALB targets based on path/headers.
   - *See:* [ALB + CloudFront Guide](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/alb-cloudfront-integration.html)

---

## **6. Further Reading**
- [AWS CloudFront Developer Guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/)
- [Lambda@Edge Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html)
- [CloudFront Caching Best Practices](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html)