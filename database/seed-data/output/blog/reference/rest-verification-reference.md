---

# **[Pattern] REST Verification Reference Guide**
*Ensure API responses adhere to expected structure, content, and behavior*

---

## **Overview**
The **REST Verification (RV)** pattern validates that API responses align with predefined criteria for correctness, security, and performance. It complements traditional testing by dynamically checking **HTTP status codes, response schemas, headers, and business logic rules** against expected values. RV is critical for maintaining API reliability, diagnosing failures, and enforcing contract compliance post-deployment.

Key use cases:
- Automated contract validation in CI/CD pipelines.
- Monitoring live APIs for drift in schema or behavior.
- Debugging inconsistent responses (e.g., partial failures in microservices).
- Enforcing OpenAPI/Swagger specifications or custom contracts.

---

## **Implementation Details**

### **Core Concepts**
1. **Validation Scope**
   - **Schema Validation**: Compare JSON/XML response structure against a schema (e.g., JSON Schema, OpenAPI).
   - **Status Code Checks**: Verify HTTP responses (e.g., `200` for success, `4xx/5xx` for errors).
   - **Header Validation**: Ensure required headers (e.g., `Content-Type`, `X-Rate-Limit`) are present/valid.
   - **Dynamic Rules**: Custom logic (e.g., "response body must contain a `user.id` > 0").
   - **Performance Metrics**: Latency, throughput, or error rates (optional, may overlap with Load Testing).

2. **Verification Modes**
   - **Pre-Deploy**: Validate API before promoting to production (e.g., via Postman/Newman).
   - **Post-Deploy**: Continuously monitor live APIs (e.g., with tools like **Pact, Assertible, or custom scripts**).
   - **Contract Testing**: Simulate consumer behavior to ensure producer APIs meet expectations (e.g., using **Pact Broker**).

3. **Tools & Frameworks**
   | Tool          | Purpose                                  | Language/Platform       |
   |---------------|------------------------------------------|-------------------------|
   | **Postman**   | Manual/scheduled validation via collections | Web UI, CLI, Newman    |
   | **Pact**      | Consumer-driven contract testing          | Java, Node.js, Ruby     |
   | **Assertible**| Automated API monitoring/validation      | Cloud-based             |
   | **JSON Schema**| Schema validation (standalone)          | Libraries (e.g., AJV)   |
   | **OpenAPI**   | Spec-driven validation (e.g., via OASvalidators) | Any |

4. **Error Handling**
   - **Fail Fast**: Abort tests on critical violations (e.g., schema errors).
   - **Warn/Log**: Flag non-critical issues (e.g., deprecated fields).
   - **Retries**: For intermittent failures (e.g., network issues).

5. **Integration**
   - **CI/CD**: Embed RV in pipelines (e.g., GitHub Actions, Jenkins).
   - **Logging**: Correlate RV results with APM tools (e.g., Datadog, New Relic).
   - **Alerting**: Trigger notifications for schema drift or error spikes.

---

## **Schema Reference**
Use the following tables to define validation rules for REST endpoints.

### **1. Endpoint Metadata**
| Field               | Type       | Description                                                                 | Example Values                          |
|---------------------|------------|-----------------------------------------------------------------------------|-----------------------------------------|
| `endpoint`          | `string`   | REST endpoint path (e.g., `/v1/users/{id}`).                               | `/api/orders`, `/v2/products/{sku}`    |
| `method`            | `enum`     | HTTP method (`GET`, `POST`, `PUT`, `DELETE`).                               | `GET`                                   |
| `status_codes`      | `array`    | Expected HTTP response codes (e.g., `[200, 201, 404]`).                   | `[200]`, `[400, 401]`                  |
| `required_headers`  | `object`   | Headers that must be present/valid.                                         | `{ "Authorization": "Bearer <token>" }` |
| `optional_headers`  | `object`   | Headers to check for (non-critical).                                        | `{ "X-Trace-ID": ".*" }`               |

---

### **2. Response Schema Validation**
| Field          | Type       | Description                                                                 | Example                          |
|----------------|------------|-----------------------------------------------------------------------------|----------------------------------|
| `schema`       | `string`   | Path to JSON Schema file or inline schema.                                  | `"schemas/user_response.json"`   |
| `rules`        | `object`   | Custom validation rules (e.g., `{ "id": { "type": "number", "min": 1 } }`). | `{ "status": { "enum": ["active", "inactive"] } }` |
| `required_fields` | `array`   | Fields that must exist in the response.                                    | `["id", "name", "created_at"]`   |
| `ignored_fields` | `array`    | Fields to exclude from validation.                                         | `["metadata"]`                    |

---
### **3. Dynamic Rules (Example)**
Validate business logic without rigid schemas:
| Rule ID          | Condition                                                                 | Expected Outcome                     |
|------------------|--------------------------------------------------------------------------|--------------------------------------|
| `user_age_check` | `response.body.age >= 18`                                                | Pass if true; fail otherwise.        |
| `price_range`    | `response.body.price > 0 && response.body.price < 1000`                  | Reject out-of-range prices.          |
| `unique_id`      | `response.body.id` matches regex `^\d{8}-[A-Z]{2}$`                     | Validate UUID-like format.           |

---

## **Query Examples**
### **1. Schema Validation (OpenAPI + JSON Schema)**
**Tool**: **Newman (Postman)**
**Command**:
```bash
newman run "api_collection.json" \
  --reporters "cli,junit" \
  --reporter-junit-export "validation_results.xml" \
  --env "env_vars.json" \
  --schema "schemas/openapi_schema.json"
```
**Input (`env_vars.json`)**:
```json
{
  "baseUrl": "https://api.example.com/v1",
  "auth": "Bearer token123"
}
```

**Schema File (`schemas/user_response.json`)**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "name": { "type": "string", "minLength": 3 },
    "email": { "type": "string", "format": "email" }
  },
  "required": ["id", "name"]
}
```

---

### **2. Custom Rule Validation (Node.js)**
**Libraries**: `assert`, `supertest`, `ajv` (JSON Schema validator).
```javascript
const assert = require('assert');
const supertest = require('supertest');
const Ajv = require('ajv');
const ajv = new Ajv();

const schema = {
  type: 'object',
  properties: {
    data: { type: 'array' },
    pagination: { type: 'object' }
  }
};

async function verifyEndpoint() {
  const response = await supertest('https://api.example.com/v1/items')
    .expect(200)
    .expect('Content-Type', /json/);

  // Schema validation
  assert(ajv.validate(schema, response.body));

  // Custom rule: Ensure pagination has 'total' > 0
  assert(response.body.pagination.total > 0);

  // Dynamic rule: All items must have a price > 0
  response.body.data.forEach(item => assert(item.price > 0));
}

verifyEndpoint().catch(err => console.error(err));
```

---

### **3. Pact Contract Test (Java)**
**Tool**: **Pact**
**Consumer Pact Test**:
```java
@Test
public void verifyUserCreation() {
  Pact pact = new Pact("pact-broker", "user-service-consumer");
  pact.setPactSpecVersion("2.0.0");

  // Define expected interaction
  pact.addInteraction()
      .given("a user exists")
      .uponReceiving("a GET request for user 123")
      .path("/users/123")
      .method("GET")
      .willRespondWith()
      .status(200)
      .body("{\"id\": \"123\", \"name\": \"John Doe\"}")
      .toPact();

  // Verify consumer code matches producer
  PactVerificationResult result = pact.verify();
  assertTrue(result.isSuccess());
}
```

---

### **4. Assertible (Cloud-Based)**
**Tool**: **Assertible** (Supports OpenAPI/Swagger)
**YAML Configuration**:
```yaml
- name: "Verify User Endpoint"
  request:
    url: "https://api.example.com/v1/users/{id}"
    method: "GET"
    headers:
      Authorization: "Bearer {{env.AUTH_TOKEN}}"
  assertions:
    - statusCode: 200
    - contentType: "application/json"
    - body:
        - path: "$.id"
          isNumber: true
        - path: "$.name"
          isString: true
          minLength: 1
    - headers:
        - name: "X-Rate-Limit-Limit"
          isNumber: true
```

**Trigger**: Schedule runs daily or link to CI/CD webhooks.

---

## **Related Patterns**
1. **[API Contract Testing]**
   - *Purpose*: Ensure producer and consumer APIs agree on requests/responses.
   - *Tools*: Pact, Postman Contract Testing.
   - *Connection*: RV validates the **outcome** of contract tests.

2. **[Postman Collections Runner]**
   - *Purpose*: Execute API tests in a CI/CD pipeline.
   - *Tools*: Newman, Postman CLI.
   - *Connection*: RV uses collections to define test cases.

3. **[OpenAPI/Swagger Validation]**
   - *Purpose*: Validate API specs against a standard.
   - *Tools*: Swagger Editor, OASvalidators.
   - *Connection*: RV validates **runtime behavior** against OpenAPI specs.

4. **[Load Testing]**
   - *Purpose*: Test API performance under load.
   - *Tools*: JMeter, k6, Gatling.
   - *Connection*: RV ensures correctness *during* load tests.

5. **[API Gateway Patterns]**
   - *Relevant*: RV can validate responses from gateways (e.g., Kong, Apigee).
   - *Use Case*: Catch misconfigurations in routing or response transformation.

6. **[Schema Registry]**
   - *Purpose*: Centralize API schemas (e.g., Avro, Protobuf).
   - *Connection*: RV references these schemas for validation.

7. **[Canary Testing]**
   - *Purpose*: Gradually roll out API changes.
   - *Connection*: RV validates canary responses against the baseline.

8. **[Logging & Observability]**
   - *Purpose*: Monitor API health.
   - *Connection*: RV results can be logged alongside metrics (e.g., Prometheus).

---
## **Best Practices**
1. **Idempotency**: Validate responses are consistent across retries.
2. **Environment Isolation**: Test in staging/pre-prod before production.
3. **Negative Testing**: Include tests for error cases (e.g., invalid inputs).
4. **Automation**: Embed RV in CI/CD to catch regressions early.
5. **Documentation**: Link RV rules to API specs (e.g., OpenAPI annotations).
6. **Performance**: Optimize schema validation for large responses (e.g., streaming).