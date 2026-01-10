# **[Pattern] API Client Patterns – Reference Guide**

---

## **Overview**
The **API Client Patterns** reference guide provides a structured approach to designing, implementing, and maintaining efficient and reliable API clients in application development. Whether consuming RESTful APIs, GraphQL endpoints, or gRPC services, these patterns ensure consistency, error handling, retry logic, caching, and observability. This guide covers core concepts, implementation strategies, and best practices to optimize API interactions while maintaining scalability, security, and performance.

---

## **1. Key Concepts**
The following terms and patterns define the framework for building API clients:

| **Concept**               | **Description**                                                                                     | **Use Case**                                                                                     |
|---------------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Request Handling**      | Structured approach to formatting, sending, and validating requests.                              | Ensures consistency in API calls across microservices or applications.                          |
| **Error Handling**        | Strategies for detecting, classifying, and recovering from API failures.                          | Reduces downtime and improves resilience with retries, fallbacks, or graceful degradation.       |
| **Retry Mechanisms**      | Policies for retrying failed requests with exponential backoff to avoid overwhelming servers.     | Improves reliability in transient network or server errors.                                   |
| **Caching Strategies**    | Storing API responses locally to reduce latency and server load.                                    | Optimizes performance for frequently accessed data.                                             |
| **Rate Limiting**         | Enforcing request quotas to prevent abuse and comply with API provider policies.                   | Prevents throttling or temporary bans from overuse.                                             |
| **Authentication/Authorization** | Securely transmitting credentials and managing tokens (e.g., OAuth 2.0, API keys).          | Ensures data privacy and role-based access control.                                              |
| **Observability**         | Logging, metrics, and tracing API interactions for debugging and monitoring.                       | Facilitates troubleshooting and performance optimization.                                      |
| **Serialization/Deserialization** | Converting data between application formats (e.g., JSON, XML) and in-memory structures (e.g., objects). | Ensures compatibility between APIs and application logic.                                      |
| **IDempotency**           | Designing requests to produce the same outcome for repeated invocations with identical inputs.     | Prevents duplicate operations (e.g., duplicate payments).                                      |
| **WebSockets & Real-Time** | Establishing persistent connections for streaming data or event-driven updates.                 | Enables low-latency updates (e.g., live dashboards, chat apps).                                |

---

## **2. Implementation Patterns**

### **2.1 Request Handling**
#### **Best Practices**
- **Standardize Requests**: Use a uniform structure for endpoints, headers, and payloads.
  ```ts
  interface ApiRequest<T> {
    url: string;
    method: 'GET' | 'POST' | 'PUT' | 'DELETE';
    headers: Record<string, string>;
    body?: T;
    params?: Record<string, string>;
  }
  ```
- **Abstraction Layers**: Encapsulate HTTP client logic (e.g., `Axios`, `Fetch`) behind a higher-level API.
  ```ts
  class ApiClient {
    private client: AxiosInstance;
    constructor(baseUrl: string) {
      this.client = axios.create({ baseURL: baseUrl });
    }
    async send<T>(request: ApiRequest<T>): Promise<T> {
      return this.client.request<T>({
        url: request.url,
        method: request.method,
        headers: request.headers,
        data: request.body,
        params: request.params,
      });
    }
  }
  ```

#### **Schema Reference**
| **Component**       | **Description**                                                                 | **Example**                                                                                     |
|---------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Endpoint Path**   | RESTful resource path (e.g., `/users/{id}`).                                   | `"/api/v1/users/123"`                                                                          |
| **HTTP Method**     | Verb indicating the operation (`GET`, `POST`, etc.).                          | `method: "POST"`                                                                               |
| **Headers**         | Key-value pairs for metadata (e.g., `Authorization`, `Content-Type`).           | `headers: { "Authorization": "Bearer token123" }`                                               |
| **Query Params**    | Key-value pairs for filtering/sorting data.                                     | `params: { limit: "10", sort: "date" }`                                                         |
| **Request Body**    | Structured payload for `POST/PUT` requests (e.g., JSON, form-data).            | `body: { name: "John", email: "john@example.com" }`                                             |
| **Response Body**   | Parsed API response (e.g., `{ id: 123, name: "John" }`).                       | `response.data` (Axios) or `res.json()` (Fetch).                                                 |

---

### **2.2 Error Handling**
#### **Response Status Codes**
| **Code** | **Category**       | **Behavior**                                                                                     |
|----------|--------------------|-------------------------------------------------------------------------------------------------|
| 200      | Success            | Parse and return the response body.                                                              |
| 201      | Created            | Successful resource creation; follow `Location` header.                                          |
| 400      | Client Error       | Validate and reject request with error details (e.g., malformed input).                        |
| 401      | Unauthorized       | Require re-authentication (e.g., renew JWT).                                                    |
| 403      | Forbidden          | Handle access-denied scenarios (e.g., retry with elevated permissions).                        |
| 404      | Not Found          | Gracefully inform the user (e.g., show a "Not Found" UI).                                     |
| 429      | Rate Limit         | Implement retry with backoff (see **Retry Mechanisms**).                                        |
| 5xx      | Server Error       | Log the error and retry (or use a fallback).                                                    |

#### **Error Class Hierarchy**
```ts
class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = `ApiError (${status})`;
  }
}

class RetryableError extends ApiError {}
class AuthenticationError extends ApiError {}
class ValidationError extends ApiError {}
```

#### **Error Handling Strategy**
```ts
async function fetchData(client: ApiClient) {
  try {
    const res = await client.send<User[]>({
      url: "/users",
      method: "GET",
    });
    return res.data;
  } catch (err) {
    if (err instanceof RetryableError) {
      await retryWithBackoff(err, client);
    } else if (err instanceof AuthenticationError) {
      await refreshToken();
    }
    throw new ApiError(500, "Failed to fetch data");
  }
}
```

---

### **2.3 Retry Mechanisms**
#### **Exponential Backoff**
Retry with increasing delays to avoid server overload:
```ts
function retryWithBackoff(
  lastError: RetryableError,
  client: ApiClient,
  maxRetries = 3,
  delay = 100
): Promise<void> {
  return new Promise(async (resolve, reject) => {
    for (let i = 0; i < maxRetries; i++) {
      try {
        await client.send<User[]>({
          url: "/users",
          method: "GET",
        });
        resolve();
        break;
      } catch (err) {
        if (i === maxRetries - 1) reject(err);
        await new Promise(res => setTimeout(res, delay * Math.pow(2, i)));
      }
    }
  });
}
```

#### **Circuit Breaker**
Temporarily stop requests if failures exceed a threshold:
```ts
class CircuitBreaker {
  private open: boolean = false;
  private failureThreshold = 3;
  private failureCount = 0;

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.open) throw new Error("Circuit breaker is open");
    try {
      this.failureCount = 0;
      return await operation();
    } catch {
      this.failureCount++;
      if (this.failureCount >= this.failureThreshold) this.open = true;
      throw;
    }
  }
}
```

---

### **2.4 Caching Strategies**
#### **Cache Layer Options**
| **Strategy**          | **Description**                                                                                     | **Use Case**                                                                                     |
|-----------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **In-Memory (Local)** | Store responses in memory (e.g., `Map` or `Redis` client).                                        | Low-latency access for small datasets.                                                          |
| **HTTP Cache Headers**| Use `Cache-Control` (e.g., `max-age=3600`) or `ETag` for server-side caching.                    | Optimize CDN or proxy caching (e.g., Nginx).                                                   |
| **Database Caching**  | Cache responses in a database (e.g., Redis, Memcached).                                           | Persistent caching for distributed systems.                                                    |
| **Query Result Caching** | Cache API responses by query parameters (e.g., `GET /users?limit=10`).                          | Avoid redundant API calls for identical queries.                                                |

#### **Example: In-Memory Cache**
```ts
class Cache {
  private store: Map<string, any>;

  constructor() {
    this.store = new Map();
  }

  get<T>(key: string): T | undefined {
    return this.store.get(key);
  }

  set(key: string, value: any, ttl: number = 0): void {
    this.store.set(key, value);
    if (ttl > 0) setTimeout(() => this.store.delete(key), ttl * 1000);
  }
}
```

#### **Decorate API Client with Cache**
```ts
class CachingApiClient extends ApiClient {
  private cache: Cache;

  constructor(baseUrl: string) {
    super(baseUrl);
    this.cache = new Cache();
  }

  async send<T>(request: ApiRequest<T>): Promise<T> {
    const cacheKey = `${request.method}:${request.url}:${JSON.stringify(request.params)}`;
    const cached = this.cache.get<T>(cacheKey);
    if (cached) return cached;

    const result = await super.send(request);
    this.cache.set(cacheKey, result.data, 60); // Cache for 60s
    return result.data;
  }
}
```

---

### **2.5 Rate Limiting**
#### **Token Bucket Algorithm**
Implement a token bucket to enforce request quotas:
```ts
class RateLimiter {
  private tokens: number = 100; // Burst capacity
  private lastRefill: number = 0;
  private refillRate: number = 100 / 60; // Tokens per minute

  hasCapacity(): boolean {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    this.tokens = Math.min(this.tokens + (elapsed / 1000) * this.refillRate, 100);
    this.lastRefill = now;
    return this.tokens > 0;
  }

  consume(): void {
    if (!this.hasCapacity()) throw new Error("Rate limit exceeded");
    this.tokens--;
  }
}
```

#### **Integrate with API Client**
```ts
class RateLimitedApiClient extends ApiClient {
  private limiter: RateLimiter;

  constructor(baseUrl: string) {
    super(baseUrl);
    this.limiter = new RateLimiter();
  }

  async send<T>(request: ApiRequest<T>): Promise<T> {
    if (!this.limiter.hasCapacity()) {
      throw new ApiError(429, "Rate limit exceeded");
    }
    this.limiter.consume();
    return super.send(request);
  }
}
```

---

### **2.6 Authentication/Authorization**
#### **Token Management**
- **OAuth 2.0 Flow**: Use libraries like `oauth2-client` (Node.js) or `Alamofire` (Swift).
- **JWT Handling**: Store tokens securely and refresh them before expiry:
  ```ts
  class AuthClient {
    private token: string | null = null;
    private expiresAt: number = 0;

    async fetchToken(): Promise<string> {
      const res = await fetch("/oauth/token", {
        method: "POST",
        body: new URLSearchParams({ grant_type: "refresh_token" }),
      });
      const { access_token, expires_in } = await res.json();
      this.token = access_token;
      this.expiresAt = Date.now() + expires_in * 1000;
      return access_token;
    }

    getToken(): string {
      if (!this.token || Date.now() > this.expiresAt) {
        this.token = this.fetchToken();
      }
      return this.token;
    }
  }
  ```

#### **Attach Tokens to Requests**
```ts
class AuthenticatedApiClient extends ApiClient {
  constructor(baseUrl: string, private auth: AuthClient) {
    super(baseUrl);
  }

  async send<T>(request: ApiRequest<T>): Promise<T> {
    const token = this.auth.getToken();
    request.headers = {
      ...request.headers,
      Authorization: `Bearer ${token}`,
    };
    return super.send(request);
  }
}
```

---

### **2.7 Observability**
#### **Logging**
Log API requests/responses with structured data:
```ts
function logApiCall<T>(
  method: string,
  url: string,
  request: ApiRequest<T>,
  response: T | Error,
  duration: number
): void {
  console.log({
    timestamp: new Date().toISOString(),
    method,
    url,
    request,
    response: response instanceof Error ? response.message : response,
    duration: `${duration}ms`,
  });
}
```

#### **Metrics (Prometheus)**
Track latency, error rates, and request volumes:
```ts
class MetricsApiClient extends ApiClient {
  private counter = new Counter("api_requests_total");
  private histogram = new Histogram("api_request_duration_seconds");
  private errors = new Counter("api_errors_total");

  async send<T>(request: ApiRequest<T>): Promise<T> {
    const start = performance.now();
    this.counter.inc();
    try {
      const res = await super.send(request);
      this.histogram.observe((performance.now() - start) / 1000);
      return res;
    } catch (err) {
      this.errors.inc();
      throw err;
    }
  }
}
```

#### **Tracing (OpenTelemetry)**
Instrument API calls with distributed tracing:
```ts
async function traceApiCall<T>(client: ApiClient, request: ApiRequest<T>) {
  const span = tracer.startSpan("api_call");
  const ctx = span.makeRemoteContext();
  try {
    const res = await client.send<T>({ ...request, [HTTP_HEADER_TRACING]: ctx.traceparent });
    span.setAttribute("http.status_code", res.status);
    return res;
  } catch (err) {
    span.setAttribute("error", err.message);
    throw err;
  } finally {
    span.end();
  }
}
```

---

### **2.8 Serialization/Deserialization**
#### **JSON Handling**
- **Request**: Convert objects to JSON strings:
  ```ts
  const payload = { name: "John", age: 30 };
  const jsonBody = JSON.stringify(payload);
  ```
- **Response**: Parse JSON responses:
  ```ts
  const res = await fetch("/users");
  const user = await res.json(); // { id: 123, name: "John" }
  ```

#### **Custom Formats (e.g., Protobuf)**
Use libraries like `protobufjs` for binary formats:
```ts
import { User } from "./proto/user_pb";
const buffer = await fetch("/users").then(res => res.arrayBuffer());
const user = User.decode(buffer);
```

---

### **2.9 Idempotency**
Ensure requests produce the same outcome for identical inputs:
- **Idempotency Key**: Generate a unique key for each request (e.g., UUID).
- **Server-Side Handling**: Store keys and validate on retry:
  ```http
  POST /orders HTTP/1.1
  Idempotency-Key: abc123-4567-890xyz
  ```

#### **Client-Side Implementation**
```ts
class IdempotentClient extends ApiClient {
  private keys = new Map<string, Promise<any>>();

  async send<T>(request: ApiRequest<T>): Promise<T> {
    const key = request.body?.idempotencyKey || crypto.randomUUID();
    if (this.keys.has(key)) return this.keys.get(key)!;

    const promise = super.send<T>({ ...request, headers: { "Idempotency-Key": key } });
    this.keys.set(key, promise);
    promise.finally(() => this.keys.delete(key));
    return promise;
  }
}
```

---

### **2.10 WebSockets & Real-Time**
#### **Connection Management**
Use libraries like `socket.io-client` (Node.js) or `SwiftSocketIO`:
```ts
import { io } from "socket.io-client";

const socket = io("https://api.example.com", {
  reconnection: true,
  reconnectionAttempts: 5,
  timeout: 5000,
});

socket.on("connect", () => console.log("Connected"));
socket.on("disconnect", () => console.log("Disconnected"));
socket.emit("subscribe", { channel: "orders" });
```

#### **Event Handling**
```ts
socket.on("orders:update", (data) => {
  console.log("New order:", data);
});
```

---

## **3. Query Examples**
### **3.1 Basic GET Request**
```ts
const client = new ApiClient("https://api.example.com");
const users = await client.send<User[]>({
  url: "/users",
  method: "GET",
  params: { limit: 10, offset: 0 },
});
```

### **3.2 POST with JSON Body**
```ts
const newUser = await client.send<User>({
  url: "/users",
  method: "POST",
  body: { name: "Alice", email: "alice@example.com" },
});
```

### **3.3 Error Handling Example**
```ts
try {
  await client.send<User>({
    url: "/private/data",
    method: "GET",
  });
} catch (err) {
  if (err instanceof AuthenticationError) {
    await auth.refreshToken();
    retryWithBackoff(err, client);
  }
}
```

### **3.4 Caching Example**
```ts
const cachingClient = new CachingApiClient("https://api.example