# **[Pattern] REST Testing Reference Guide**

---

## **Overview**
The **REST Testing** pattern defines a structured approach to validating RESTful APIs by validating HTTP requests and responses against predefined schemas, business rules, and expected behavior. This pattern ensures API reliability, security, and compliance while supporting automated testing, performance benchmarking, and contract testing. Unlike traditional unit testing, REST Testing focuses on interaction validation at the API layer, covering endpoints, authentication, error handling, and resource states.

Key use cases include:
- **Unit & Integration Testing** – Validating individual endpoints or API workflows.
- **Contract Testing** – Ensuring client/server agreements (e.g., OpenAPI/Swagger specs).
- **Performance & Load Testing** – Simulating traffic to measure response times and failure rates.
- **Security Testing** – Detecting vulnerabilities like injection flaws, unauthorized access, or CSRF.
- **Regression Testing** – Confirming changes to the backend don’t break existing functionality.

This guide covers core concepts, schema validation, query examples, and related patterns for effective REST Testing.

---

## **Implementation Details**
### **Core Principles**
1. **Statelessness**: Each request must contain sufficient information to be processed independently.
2. **Resource-Based**: APIs expose resources (e.g., `/users`, `/orders`) via standard HTTP methods (`GET`, `POST`, `PUT`, `DELETE`).
3. **Uniform Interface**: Clients interact with resources using consistent patterns (e.g., URIs, representations).
4. **Layered System**: APIs can be intermediated (e.g., load balancers, security gateways).
5. **Caching**: Support caching headers (`ETag`, `Cache-Control`) for performance optimization.

### **Key Components**
| Component               | Description                                                                                                                                                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Test Framework**      | Tools like Postman, RestAssured, Karate, or Python’s `requests` to send HTTP calls.                                                                                                                   |
| **Schema Validation**   | JSON Schema, OpenAPI/Swagger, or Protobuf to define expected request/response structures.                                                                                                             |
| **Assertions**          | Validate status codes (e.g., `200 OK`), headers, body content, and error responses. Example: `assert status_code == 200` or `assert 'success': true in response.data`.               |
| **Mock Servers**        | Simulate backend services (e.g., WireMock, Mockoon) for isolated testing.                                                                                                                                   |
| **Authentication**      | Test OAuth2, API keys, JWT, or basic auth flows.                                                                                                                                                          |
| **Pagination & Filtering** | Validate `limit`, `offset`, and query parameters (e.g., `/users?page=2&limit=10`).                                                                                                                        |
| **Idempotency**         | Ensure `PUT` or `PATCH` requests produce the same result for identical inputs.                                                                                                                           |
| **Error Handling**      | Test standard HTTP errors (`400 Bad Request`, `404 Not Found`) and custom payloads (e.g., `{ "error": "Invalid input" }`).                                                                          |
| **Asynchronous Checks** | For long-running operations, use callbacks or polling (e.g., Webhooks or `/status` endpoints).                                                                                                         |
| **Logging & Monitoring** | Track test execution metrics (duration, failures) with tools like Selenium Grid or Prometheus.                                                                                                       |

---

## **Schema Reference**
Use schema definitions to enforce structure in requests/responses. Below are common schemas for REST Testing:

| **Schema Type**       | **Purpose**                                                                                     | **Example**                                                                                                                                                     |
|-----------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Request Schema**    | Validates input (body, query, headers) before sending.                                           | ```json { "type": "object", "properties": { "user": { "type": "string", "minLength": 3 }, "age": { "type": "integer", "minimum": 18 } } } ```          |
| **Response Schema**   | Ensures server returns data in the expected format.                                              | ```json { "type": "object", "required": ["id", "name"], "properties": { "id": { "type": "string" }, "name": { "type": "string" } } } ```             |
| **OpenAPI/Swagger**   | Defines API contracts with endpoints, parameters, and examples.                                 | ```yaml paths: /users: get: responses: 200: description: Successful response schema: $ref: '#/components/schemas/User' ```                           |
| **JWT Payload**       | Validates token claims (e.g., `iss`, `exp`, `aud`).                                               | ```json { "iss": "auth.example.com", "exp": 1735689600, "sub": "user123" } ```                                                                                   |
| **Paginated Response**| Enforces `links`, `data`, and `total` fields in paginated APIs.                                   | ```json { "links": { "next": "/users?page=2" }, "data": [ { "id": 1, "name": "Alice" } ], "total": 100 } ```                                          |
| **Error Response**    | Standardizes error formats (e.g., `error`, `message`, `code`).                                   | ```json { "error": "ValidationError", "message": "Age must be > 18", "code": 400 } ```                                                                           |

**Tools for Schema Validation:**
- **JSON Schema**: [`jsonschema`](https://python-jsonschema.readthedocs.io/) (Python), [`ajv`](https://ajv.js.org/) (JavaScript).
- **OpenAPI**: [`swagger-parser`](https://github.com/APIs-guru/openapi-directory/tree/master/swagger-parser) (Node.js), [`swaggerscan`](https://github.com/swagger-api/swagger-codegen).
- **Protobuf**: [`protobuf`](https://developers.google.com/protocol-buffers) for binary payloads.

---

## **Query Examples**
### **1. Basic Endpoint Testing**
**Scenario**: Verify `GET /users/1` returns a valid user object.
```http
# POSTMAN Example
GET /api/users/1
Headers:
  Authorization: Bearer xxxxx.yyyyy.zzzzz
  Accept: application/json

# Assertions:
- Status Code: 200 OK
- Response body matches schema: `UserResponseSchema`.
- `response.data.id == "1"`.
```

**Code (Python + `requests`):**
```python
import requests

response = requests.get("https://api.example.com/users/1", headers={"Authorization": "Bearer token"})
response.raise_for_status()  # Raises HTTPError for 4XX/5XX
assert response.json()["id"] == "1"
```

---

### **2. Authentication Flow**
**Scenario**: Test OAuth2 password grant flow.
```http
# Step 1: Get Token
POST /oauth/token
Headers: Content-Type: application/x-www-form-urlencoded
Body: grant_type=password&username=user1&password=pass123&scope=read

# Expected Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}

# Step 2: Use Token to Fetch Data
GET /api/protected/resource
Headers:
  Authorization: Bearer <access_token>

# Assertions:
- Status Code: 200 OK.
- `response.json()["data"]` is not empty.
```

**Code (Java + RestAssured):**
```java
given()
    .formParam("grant_type", "password")
    .formParam("username", "user1")
    .formParam("password", "pass123")
    .when()
    .post("https://api.example.com/oauth/token")
    .then()
    .assertThat()
    .statusCode(200)
    .extract().jsonPath().getString("access_token");

String token = ...;
given()
    .header("Authorization", "Bearer " + token)
    .when()
    .get("/api/protected/resource")
    .then()
    .assertThat()
    .statusCode(200);
```

---

### **3. Pagination Validation**
**Scenario**: Test `/orders?limit=5&page=1` returns 5 orders.
```http
GET /api/orders
Query Params: limit=5&page=1
Headers: Accept: application/json

# Expected Response:
{
  "data": [
    { "id": 1, "user": 101, "amount": 99.99 },
    { "id": 2, "user": 102, "amount": 49.99 }
  ],
  "links": {
    "next": "/api/orders?limit=5&page=2",
    "prev": null
  },
  "total": 125
}

# Assertions:
- `len(response.json()["data"]) == 5`.
- `"next"` link exists (if `total > 5`).
```

**Code (JavaScript + `axios`):**
```javascript
const response = await axios.get("https://api.example.com/orders", {
  params: { limit: 5, page: 1 },
  headers: { Accept: "application/json" }
});
const data = response.data;
assert.strictEqual(data.data.length, 5);
assert.ok(data.links.next.includes("page=2"));
```

---

### **4. Error Handling**
**Scenario**: Test `404 Not Found` for invalid user ID.
```http
GET /api/users/999
Headers: Accept: application/json

# Expected Response:
{
  "error": "NotFoundError",
  "message": "User with ID 999 not found",
  "code": 404
}

# Assertions:
- Status Code: 404.
- `response.json()["code"] == 404`.
```

**Code (Python):**
```python
try:
    response = requests.get("https://api.example.com/users/999")
    assert response.status_code == 404
    assert response.json()["code"] == 404
except requests.exceptions.HTTPError as e:
    assert e.response.status_code == 404
```

---

### **5. Idempotency Check**
**Scenario**: Verify `PUT /orders/1` with identical payload returns `200` twice.
```http
PUT /api/orders/1
Headers:
  Content-Type: application/json
Body: {
  "user": "101",
  "amount": 99.99,
  "status": "shipped"
}

# First Call:
- Status: 200.
- Response: { "id": 1, "status": "shipped" }

# Second Call (same body):
- Status: 200.
- Response: { "id": 1, "status": "shipped" }
```

**Code (Bash + `curl`):**
```bash
# First request
response1=$(curl -X PUT -H "Content-Type: application/json" -d '{"user": "101", "amount": 99.99, "status": "shipped"}' https://api.example.com/orders/1)
echo "$response1" | jq '.status_code' | grep 200

# Second request
response2=$(curl -X PUT -H "Content-Type: application/json" -d '{"user": "101", "amount": 99.99, "status": "shipped"}' https://api.example.com/orders/1)
echo "$response2" | jq '.status_code' | grep 200
```

---

### **6. Asynchronous Validation**
**Scenario**: Test webhook callback after order creation.
```http
# Step 1: Create Order (async)
POST /api/orders
Body: { "user": "101", "amount": 99.99, "status": "pending" }

# Step 2: Poll `/orders/1` until status is "shipped"
GET /api/orders/1
Headers: Accept: application/json

# Assertions:
- Eventually, `response.data.status === "shipped"`.
```

**Code (Python + `time`):**
```python
import time
import requests

order_id = "1"
max_retries = 10
retry_delay = 2

for _ in range(max_retries):
    response = requests.get(f"https://api.example.com/orders/{order_id}")
    if response.json()["status"] == "shipped":
        break
    time.sleep(retry_delay)
else:
    raise AssertionError("Order never shipped")
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Contract Testing**      | Validates API client/server agreements (e.g., OpenAPI specs) using tools like [Pact](https://docs.pact.io/).                                                                                                      | When collaborating with third-party APIs or microservices.                                                                                                           |
| **Mock Server Testing**   | Simulates backend services (e.g., WireMock) to isolate API tests from real dependencies.                                                                                                               | During development or when real services are unavailable.                                                                                                           |
| **Chaos Engineering**     | Intentionally fails components (e.g., timeouts, network partitions) to test resilience.                                                                                                                 | For production-grade reliability testing (e.g., [Gremlin](https://www.gremlin.com/) or [Chaos Mesh](https://chaos-mesh.org/)).                                     |
| **Performance Testing**   | Measures API response times, throughput, and concurrency using tools like [JMeter](https://jmeter.apache.org/) or [Locust](https://locust.io/).                                                          | Before scaling or under load conditions.                                                                                                                              |
| **Security Testing**      | Scans for vulnerabilities (e.g., SQLi, XSS) using [OWASP ZAP](https://www.zaproxy.org/) or [Burp Suite](https://portswigger.net/burp).                                                                     | During security audits or penetration testing.                                                                                                                        |
| **GraphQL Testing**       | Validates GraphQL queries/mutations using tools like [Postman GraphQL](https://learning.postman.com/docs/sending-requests/supported-request-types/graphql-queries/) or [Jest](https://jestjs.io/). | For GraphQL APIs (alternative to REST).                                                                                                                             |
| **Event-Driven Testing**  | Tests event sinks (e.g., Kafka, RabbitMQ) using tools like [Testcontainers](https://testcontainers.com/) for local brokers.                                                                                 | For event-driven architectures (e.g., microservices with pub/sub).                                                                                                     |

---

## **Best Practices**
1. **Isolation**: Run tests in parallel to reduce execution time (e.g., using [Docker Compose](https://docs.docker.com/compose/) for isolated environments).
2. **Idempotency**: Design tests to be repeatable (avoid side effects like database mutations).
3. **Parameterization**: Use variables for dynamic values (e.g., `{{base_url}}` in Postman).
4. **Negative Testing**: Include test cases for invalid inputs, edge cases, and error scenarios.
5. **CI/CD Integration**: Automate REST tests in pipelines (e.g., GitHub Actions, Jenkins).
6. **Feedback Loops**: Use test reports (e.g., Allure, JUnit) to identify regressions quickly.
7. **Schema Evolution**: Update schemas incrementally to avoid breaking changes (e.g., [Backward Compatible](https://json-schema.org/specification-links.html#backward-compatible) updates).

---
## **Tools & Libraries**
| **Category**       | **Tools**                                                                                                                                                                                                 |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Testing Frameworks** | [Postman](https://www.postman.com/), [Karate](https://karatelabs.github.io/karate/), [RestAssured](https://github.com/rest-assured/rest-assured) (Java), [`requests`](https://pypi.org/project/requests/) (Python). |
| **Schema Validation** | [`ajv`](https://ajv.js.org/) (JavaScript), [`jsonschema`](https://python-jsonschema.readthedocs.io/) (Python), [`jsonnet`](https://jsonnet.org/) for dynamic schemas.                         |
| **Mock Servers**    | [WireMock](http://wiremock.org/), [Mockoon](https://mockoon.com/), [Postman Mock Server](https://learning.postman.com/docs/sending-requests/mock-servers/).                                               |
| **CI/CD**           | [GitHub Actions](https://github.com/features/actions), [Jenkins](https://www.jenkins.io/), [CircleCI](https://circleci.com/).                                                                       |
| **Monitoring**      | [Prometheus](https://prometheus.io/), [Grafana](https://grafana.com/), [Datadog](https://www.datadoghq.com/).                                                                                         |
| **Performance**     | [JMeter](https://jmeter.apache.org/), [Locust](https://locust.io/), [k6](https://k6.io/).                                                                                                               |

---
## **Troubleshooting**
| **Issue**               | **Root Cause**                                                                 | **Solution**                                                                                                                                                     |
|-------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Flaky Tests**         | Network latency, race conditions, or async delays.                             | Use retries, timeouts, or asynchronous validation (e.g., polling).                                                                                               |
| **Schema Mismatches**   | Backend schema changed but tests aren’t updated.                               | Automate schema comparison (e.g., [Schemathesis](https://schemathesis.io/)) or use semantic versioning for APIs.                                               |
| **Authentication Failures** | Invalid tokens or expired credentials.                                       | Rotate tokens in test environments or use short-lived tokens.                                                                                                 |
| **Rate Limiting**       | Tests hit API rate limits (e.g., `429 Too Many Requests`).                     | Distribute requests, use caching, or request higher limits.                                                                                                       |
| **Environment Drift**   | Test and prod environments diverge.                                           | Use feature flags, environment variables, or Dockerized test environments.                                                                                       |
| **Slow Tests**          | Inefficient queries or unoptimized mocks.                                      | Cache responses, reduce payload size, or parallelize tests.                                                                                                      