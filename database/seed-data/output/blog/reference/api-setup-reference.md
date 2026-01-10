# **[Pattern] API Setup Reference Guide**

---

## **1. Overview**
This guide provides a structured approach to implementing the **API Setup Pattern**, a foundational technique for configuring and exposing APIs in microservices or monolithic applications. The pattern standardizes how APIs are initialized, versioned, documented, and secured, ensuring consistency, maintainability, and scalability. It covers core components like API endpoints, request/response schemas, authentication, rate limiting, and versioning, while adhering to RESTful conventions and modern best practices.

This reference guide assumes familiarity with **HTTP, JSON, REST, and basic API design principles**. It is tailored for developers, architects, and DevOps engineers responsible for designing, deploying, and managing API-driven systems.

---

## **2. Key Concepts & Core Components**
The **API Setup Pattern** consists of the following interconnected layers:

| **Component**            | **Purpose**                                                                                                                                                                                                 | **Key Attributes**                                                                                                                                               |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **API Gateway**          | Routes, secures, and manages incoming requests to backend services, handling load balancing, caching, and request transformations.                                                                         | - **Forward Proxy**: Routes requests to appropriate services.<br>- **Reverse Proxy**: Hides backend architecture.<br>- **Auth/Rate Limiting**: Enforces security policies. |
| **API Endpoint**         | A unique URL path (e.g., `/v1/users`) defining a resource and supported operations (GET, POST, PUT, DELETE).                                                                                            | - **Resource Naming**: Use nouns (e.g., `/orders`, not `/getOrder`).<br>- **HTTP Methods**: Align with CRUD operations.<br>- **Versioning**: Prefix with `/vX`.          |
| **Request/Response Schema** | Defines the structure of incoming data (request payloads) and outgoing data (responses), ensuring consistency and validation.                                                                         | - **OpenAPI/Swagger**: Auto-generates documentation.<br>- **Request Body**: JSON/XML formats.<br>- **Query Parameters**: Filter/sort data.<br>- **Headers**: Auth, metadata. |
| **Authentication**       | Validates and authorizes API consumers using tokens, API keys, or OAuth2/OIDC.                                                                                                                             | - **JWT**: Stateless auth.<br>- **OAuth2**: Delegated auth (e.g., Google, Facebook).<br>- **API Keys**: Simple but less secure.<br>- **Mutual TLS (mTLS)**: Server-side auth. |
| **Rate Limiting**        | Controls API abuse by enforcing request quotas (e.g., 1000 requests/hour per IP).                                                                                                                          | - **Token Bucket**: Smooths traffic.<br>- **Fixed Window**: Counts requests in time slots.<br>- **Sliding Window**: Real-time tracking.<br>- **Headers**: `X-Rate-Limit`. |
| **Versioning**           | Manages backward compatibility and forward compatibility for evolving APIs.                                                                                                                            | - **URI Prefix**: `/v1`, `/v2`.<br>- **Header/Query**: `Accept: application/vnd.api.v1+json`.<br>- **Backward Compatibility**: Avoid breaking changes.            |
| **Error Handling**       | Standardizes error responses (e.g., HTTP status codes, error objects) for consistent debugging.                                                                                                       | - **Standard Codes**: `400` (Bad Request), `401` (Unauthorized), `500` (Server Error).<br>- **Error Objects**: `{ "error": "message", "code": "ERR_123" }`.       |
| **Logging & Monitoring** | Tracks API performance, errors, and usage for observability.                                                                                                                                             | - **Distributed Tracing**: Identify latency bottlenecks.<br>- **Metrics**: Requests/s, latency percentiles.<br>- **Logs**: Structured JSON logs.<br>- **Alerts**: SLA breaches. |
| **Documentation**        | Provides auto-generated or manual documentation for API consumers.                                                                                                                                       | - **OpenAPI/Swagger**: Interactive docs.<br>- **Postman Collections**: Predefined test cases.<br>- **Markdown/PDF**: Static guides.<br>- **Swagger UI**: Browser-based explorer.  |

---

## **3. Schema Reference**
Below is a reference table for common API schemas used in the **API Setup Pattern**:

| **Schema Type**          | **Description**                                                                                                                                                     | **Example**                                                                                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Request Payload**      | Data sent by the client (e.g., JSON body for POST/PUT).                                                                                                           | ```json { "name": "John Doe", "email": "john@example.com", "password": "secure123" } ```                                                                       |
| **Query Parameters**     | Filter/sort data in URL queries.                                                                                                                                   | `?limit=10&offset=0&sort=-createdAt`                                                                                                                         |
| **Response Body**        | Structured data returned by the server.                                                                                                                           | ```json { "status": "success", "data": { "id": "123", "name": "John Doe" }, "metadata": { "count": 1 } } ```                                           |
| **Error Response**       | Standardized error format for failed requests.                                                                                                                       | ```json { "error": { "message": "Invalid email format", "code": "VALIDATION_ERROR_001", "details": { "field": "email" } } } ```                       |
| **Authentication Header**| JWT/OAuth2 tokens or API keys.                                                                                                                                      | `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` or `X-API-Key: abc123xyz`                                                                |
| **Rate Limit Header**    | Enforces request quotas (e.g., `X-RateLimit-Limit: 1000`, `X-RateLimit-Remaining: 995`).                                                                          |                                                                                                                                                                 |
| **Version Header**       | Specifies API version (e.g., `Accept: application/vnd.api.v1+json`).                                                                                                  |                                                                                                                                                                 |

---

## **4. Query Examples**
Below are practical examples demonstrating the **API Setup Pattern**:

---

### **4.1 Basic GET Request (Retrieve User Data)**
**Endpoint**:
`GET /v1/users/{id}`

**Headers**:
```
Accept: application/json
Authorization: Bearer <JWT_TOKEN>
X-API-Key: abc123xyz
```

**Request URL**:
`https://api.example.com/v1/users/123`

**Expected Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "id": "123",
    "name": "John Doe",
    "email": "john@example.com",
    "createdAt": "2023-01-01T00:00:00Z"
  },
  "metadata": {
    "count": 1
  }
}
```

**Expected Response (404 Not Found)**:
```json
{
  "error": {
    "message": "User not found",
    "code": "NOT_FOUND_ERROR_001"
  }
}
```

---

### **4.2 POST Request (Create a New User)**
**Endpoint**:
`POST /v1/users`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
X-API-Key: abc123xyz
```

**Request Body**:
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "secure456"
}
```

**Expected Response (201 Created)**:
```json
{
  "status": "success",
  "data": {
    "id": "456",
    "name": "Jane Smith",
    "email": "jane@example.com"
  }
}
```

**Expected Response (400 Bad Request)**:
```json
{
  "error": {
    "message": "Password must be at least 8 characters",
    "code": "VALIDATION_ERROR_002",
    "details": {
      "field": "password"
    }
  }
}
```

---

### **4.3 Query with Pagination and Filtering**
**Endpoint**:
`GET /v1/orders`

**Query Parameters**:
- `limit`: Number of results per page (max 100).
- `offset`: Pagination offset.
- `status`: Filter by order status (`pending`, `shipped`, `cancelled`).
- `sort`: Sort by field (e.g., `createdAt`, `amount`).

**Request URL**:
`https://api.example.com/v1/orders?limit=10&offset=0&status=shipped&sort=-amount`

**Expected Response (200 OK)**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "789",
      "userId": "123",
      "amount": 99.99,
      "status": "shipped",
      "createdAt": "2023-01-15T09:30:00Z"
    }
  ],
  "metadata": {
    "total": 15,
    "limit": 10,
    "offset": 0
  }
}
```

---

### **4.4 Rate Limiting Example**
**Endpoint**:
`GET /v1/sensitive-data`

**Headers**:
```
Authorization: Bearer <JWT_TOKEN>
X-API-Key: abc123xyz
```

**Rate Limit Headers in Response**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1704662400 (UTC timestamp)
```

**Expected Response (200 OK)**:
```json
{
  "status": "success",
  "data": "Accessible because remaining requests (998) > 0."
}
```

**Expected Response (429 Too Many Requests)**:
```json
{
  "error": {
    "message": "Rate limit exceeded. Try again at 2024-01-01T00:00:00Z.",
    "code": "RATE_LIMIT_EXCEEDED_001"
  }
}
```

---

## **5. Implementation Steps**
Follow these steps to implement the **API Setup Pattern**:

### **5.1 Initialize API Gateway**
1. **Choose a Gateway**:
   - **NGINX**: Lightweight, reverse proxy.
   - **Kong**: Open-source API gateway with plugins (rate limiting, JWT).
   - **Apigee/Apicurio**: Enterprise-grade with advanced features.
   - **AWS API Gateway**: Managed service (serverless).

2. **Configure Routes**:
   ```nginx
   server {
     listen 80;
     server_name api.example.com;

     location /v1/ {
       proxy_pass http://backend_service;
       proxy_set_header Authorization $http_authorization;
       proxy_set_header X-API-Key $http_x_apikey;
     }
   }
   ```

3. **Enable Rate Limiting** (NGINX Example):
   ```nginx
   limit_req_zone $binary_remote_addr zone=api_limit:10m rate=1000r/s;

   location / {
     limit_req zone=api_limit burst=1000 nodelay;
   }
   ```

---

### **5.2 Define API Endpoints**
**Example (Express.js)**:
```javascript
const express = require('express');
const app = express();
const version = 'v1';

app.use(`/${version}`, (req, res, next) => {
  console.log(`Request for ${req.path}`);
  next();
});

// GET /v1/users/:id
app.get(`/${version}/users/:id`, (req, res) => {
  res.json({ user: { id: req.params.id, name: "John Doe" } });
});

// POST /v1/users
app.post(`/${version}/users`, express.json(), (req, res) => {
  const user = req.body;
  if (!user.name) {
    return res.status(400).json({ error: "Name is required" });
  }
  res.status(201).json({ id: "123", ...user });
});

app.listen(3000, () => console.log(`API v${version} running on port 3000`));
```

---

### **5.3 Schema Validation (JSON Schema)**
Validate request/response payloads using **JSON Schema**:
```json
// request.schema.json (for POST /v1/users)
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": { "type": "string", "minLength": 2 },
    "email": { "type": "string", "format": "email" },
    "password": { "type": "string", "minLength": 8 }
  },
  "required": ["name", "email", "password"]
}
```

**Tooling**:
- **Ajv**: JavaScript validator.
- **JSON Schema Validator (Online)**: https://www.jsonschemavalidator.net/
- **FastAPI/Pydantic**: Auto-validation in Python.

---

### **5.4 Authentication Setup (JWT Example)**
```javascript
const jwt = require('jsonwebtoken');

app.post('/v1/auth/login', (req, res) => {
  const { email, password } = req.body;
  if (email === 'admin@example.com' && password === 'admin123') {
    const token = jwt.sign({ email }, 'SECRET_KEY', { expiresIn: '1h' });
    res.json({ token });
  } else {
    res.status(401).json({ error: "Unauthorized" });
  }
});

app.use((req, res, next) => {
  const token = req.header('Authorization')?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: "Access denied" });

  try {
    const decoded = jwt.verify(token, 'SECRET_KEY');
    req.user = decoded;
    next();
  } catch (err) {
    res.status(400).json({ error: "Invalid token" });
  }
});
```

---

### **5.5 Generate OpenAPI Documentation**
**Example (Swagger/OpenAPI 3.0)**:
```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /v1/users:
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      responses:
        201:
          description: User created
        400:
          description: Invalid input
components:
  schemas:
    User:
      type: object
      properties:
        name:
          type: string
        email:
          type: string
          format: email
```

**Tools**:
- **Swagger UI**: Auto-render docs from OpenAPI spec.
- **Postman**: Import OpenAPI to generate collections.
- **Redoc**: Alternative to Swagger UI.

---

### **5.6 Monitor and Log API Traffic**
**Example (Structured Logging with Winston)**:
```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'api.log' })
  ]
});

app.use((req, res, next) => {
  const start = Date.now();
  logger.info({
    method: req.method,
    path: req.path,
    status: undefined,
    duration: undefined,
    user: req.user?.email
  });
  res.on('finish', () => {
    logger.info({
      ...logger.fields,
      status: res.statusCode,
      duration: Date.now() - start
    });
  });
  next();
});
```

**Monitoring Tools**:
- **Prometheus + Grafana**: Metrics visualization.
- **ELK Stack (Elasticsearch, Logstash, Kibana)**: Log aggregation.
- **Datadog/New Relic**: APM for distributed tracing.

---

## **6. Best Practices**
1. **Versioning**:
   - Use **URI prefix** (`/v1`, `/v2`) for simplicity.
   - Avoid **query parameters** (`?version=1`) due to caching issues.
   - Document deprecation timelines for older versions.

2. **Security**:
   - Always use **HTTPS** (TLS 1.2+).
   - Rotate **API keys/JWT secrets** regularly.
   - Implement **CORS** restrictions to prevent CSRF.
   - Validate all inputs to prevent **SQL Injection/XSS**.

3. **Performance**:
   - Enable **gzip/compression** for responses.
   - Use **caching** (CDN, Redis) for static data.
   - Optimize **database queries** with indexing.

4. **Documentation**:
   - Keep OpenAPI specs **up-to-date**.
   - Use **interactive docs** (Swagger UI) for developers.
   - Provide **examples** for common use cases.

5. **Error Handling**:
   - Use **standard HTTP status codes**.
   - Include **machine-readable error details** (codes, timestamps).
   - Avoid exposing **stack traces** in production.

6. **Testing**:
   - Write **unit tests** for endpoints (Jest, pytest).
   - Use **contract testing** (Pact, Postman) for API consumers.
   - Simulate **load testing** (JMeter, k6).

---

## **7. Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                                                                                                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Tight coupling with consumers**     | Use **versioned endpoints** and **backward-compatible changes**.                                                                                                                              |
| **No rate limiting**                  | Implement **global/local rate limits** (e.g., per IP, per user).                                                                                                                               |
| **Lack of documentation**             | Auto-generate docs with **OpenAPI/Swagger**.                                                                                                                                                   |
| **Poor error messages**               | Standardize errors with **codes, details, and HTTP status codes**.                                                                                                                          |
| **Ignoring CORS**                     | Configure **CORS headers** explicitly (e.g., `Access-Control-Allow-Origin`).                                                                                                                  |
| **No monitoring**                     | Integrate **