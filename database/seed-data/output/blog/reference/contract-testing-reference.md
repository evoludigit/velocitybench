# **[Pattern] Contract Testing & API Mocking – Reference Guide**

---

## **1. Overview**
**Contract Testing & API Mocking** is a testing strategy that ensures API consumers and providers adhere to a shared interface contract (e.g., OpenAPI/Swagger specs, RAML, or custom schemas). Unlike **integration testing**, which requires live services, this pattern validates interactions **independently** using recorded expectations (e.g., request/response payloads, error cases) and mock implementations. It detects mismatches early—before deployment—by treating API contracts as first-class artifacts.

This pattern is particularly useful in **microservices architectures**, **CI/CD pipelines**, and **event-driven systems** where services evolve incrementally. The **Consumer-Driven Contract Testing (CDC)** variant empowers API consumers to define requirements, while the **Provider-Driven Contract (PDC)** approach focuses on provider-side validation. Mocking APIs in local development accelerates testing by replacing real dependencies with controlled stubs.

---

## **2. Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **API Contract**          | Formalized agreement between consumer and provider (e.g., OpenAPI/Swagger YAML, JSON Schema, or HTTP metadata). Defines endpoints, request/response schemas, auth, and error codes.                  | `{ "paths": { "/users": { "get": { "responses": { "200": { "schema": { "$ref": "#/components/schemas/User" } } } } } } }` |
| **Contract Test**         | Unit/integration test that verifies a consumer’s contract against a provider’s implementation or mock. Uses tools like **Pact**, **ContractTestKit**, or **WireMock** to assert expectations.          | `verify: (request: Request, response: Response) => { expect(response.status).toBe(200); expect(response.body).toMatchSchema(UserSchema); }` |
| **Mock Service**          | Lightweight server that mimics a real API (e.g., **Mockoon**, **Postman Mock Server**, **WireMock**). Routes requests to predefined responses or dynamic scripts.                                          | `GET /users/1 => { "id": "1", "name": "Alice", "email": "alice@example.com" }`                |
| **Consumer-Driven (CDC)** | Consumers define contracts (e.g., via OpenAPI) and validate provider compliance. Providers must pass these tests on every push.                                                                                | Company B (consumer) writes OpenAPI spec; Company A (provider) runs tests against it.        |
| **Provider-Driven (PDC)** | Providers define contracts (e.g., OpenAPI) and share them with consumers. Consumers write tests against the provider’s published contracts.                                                                    | Netflix’s OpenAPI spec used by internal teams to build consumers.                               |
| **Pact Broker**           | Central repository (e.g., [Pact.io](https://pact.io/)) to store and version contracts. Enables governance (e.g., approval workflows) and audit trails.                                                                | `pact: { "consumer": "e-commerce-frontend", "provider": "payment-service", "version": "1.0.0" }` |
| **Dynamic Contracts**     | Contracts generated on-the-fly (e.g., from running tests) to capture real-world interactions. Useful for testing partial implementations or edge cases.                                                            | `// Auto-generated from a failed test: { "request": { "method": "POST", "path": "/orders", "body": { "status": "pending" } }, "response": { "status": 400 } }` |
| **Schema Registry**       | Stores and version-controls schemas (e.g., JSON Schema, Avro). Tools like **Confluent Schema Registry** or **Apicurio** enforce backward compatibility.                                                         | `{ "id": "UserSchema_v1", "type": "object", "properties": { "id": { "type": "string" } } }`   |

---

## **3. Implementation Details**

### **3.1 Tools & Frameworks**
| **Category**       | **Tools**                                                                                                                                                     | **Use Case**                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Contract Testing** | [Pact](https://pact.io/), [ContractTestKit](https://github.com/pactfoundation/pact-js), [Mockoon](https://mockoon.com/), [WireMock](http://wiremock.org/) | Run consumer/provider tests against contracts.                                                |
| **Mock Servers**    | [Mockoon](https://mockoon.com/), [Postman Mock Server](https://learning.postman.com/docs/guidelines-best-practices/mock-servers/), [WireMock](http://wiremock.org/) | Local development with fake APIs.                                                              |
| **Schema Validation** | [JSON Schema Validator](https://www.jsonschemavalidator.net/), [OpenAPI Tools](https://github.com/OpenAPITools/openapi-generator), [Joi](https://joi.dev/)  | Validate request/response payloads against schemas.                                            |
| **Pact Broker**     | [Pact Broker](https://pact.io/docs/pact_broker.html), [Pactflow](https://pactflow.io/)                                                                     | Centralized contract storage and collaboration between teams.                                   |
| **API Gateway Mocks** | [Kong](https://konghq.com/), [Apigee](https://cloud.google.com/apigee), [MuleSoft](https://www.mulesoft.com/)                                                      | Mock API gateways for end-to-end testing.                                                       |

---

### **3.2 Workflow**
#### **Consumer-Driven Contract Testing (CDC)**
1. **Define Contract**: The consumer writes an OpenAPI/Swagger spec or uses a tool like **Pact** to generate a contract from actual API calls.
   ```yaml
   # consumer-api-spec.yaml
   openapi: 3.0.0
   paths:
     /orders:
       post:
         requestBody:
           content:
             application/json:
               schema:
                 $ref: '#/components/schemas/Order'
         responses:
           '201':
             description: Created
   components:
     schemas:
       Order:
         type: object
         properties:
           id:
             type: string
           productId:
             type: string
   ```
2. **Run Consumer Tests**: The consumer runs tests against a **mock provider** (e.g., WireMock) to ensure their implementation matches the contract.
   ```java
   // Java consumer test (Pact)
   @Test
   public void test_create_order() {
       given("A valid order is sent to the provider")
           .uponReceiving("a POST request to /orders")
           .withRequestBody(new Order("123", "prod-456"))
           .willRespondWith()
           .status(201)
           .body("{\"id\": \"123\", \"productId\": \"prod-456\"}");

       // Run Pact verification
       PactVerificationContext.runScenario("create_order", pactVerificationContext -> {
           // Make API call to mock provider
           Response response = Unirest.post("http://mock-provider/orders")
               .field("id", "123")
               .field("productId", "prod-456")
               .asString();
           assertEquals(201, response.getStatus());
       });
   }
   ```
3. **Publish Contract**: The consumer publishes the contract to a **Pact Broker** or shares it with the provider.
4. **Provider Verification**: The provider pulls the contract and runs **integration tests** against their implementation to ensure compliance.
   ```bash
   # Run provider tests using Pact (Node.js)
   pact-broker verify --pact-specification Version=3 --pact-url http://pact-broker:8080
   ```

#### **Provider-Driven Contract Testing (PDC)**
1. **Provider Publishes Contract**: The provider shares an OpenAPI spec or contract (e.g., via GitHub, Pact Broker).
2. **Consumer Defines Tests**: The consumer writes tests against the provider’s contract.
   ```bash
   # Generate mock server from OpenAPI spec
   openapi-generator generate -i provider-spec.yaml -g server -o mock-server
   ```
3. **Run Tests Locally**: The consumer uses the mock server to test their implementation in isolation.
4. **Handle Mismatches**: If the provider’s implementation changes, the consumer updates their tests or negotiates changes.

---

### **3.3 Mocking APIs**
Mocking APIs allows teams to test **consumer code in isolation** without waiting for providers. Below are common scenarios:

#### **Scenario 1: Static Mock (Predefined Responses)**
Use tools like **WireMock** or **Mockoon** to define fixed responses.
```java
// Java WireMock example
WireMock.stubFor(WireMock.post(urlEqualTo("/orders"))
    .willReturn(aResponse()
        .withStatus(201)
        .withBody("{\"id\": \"123\", \"status\": \"pending\"}")));
```
**Mockoon GUI**:
- **Request**: `POST /orders`
- **Response**: `201 Created`
- **Body**:
  ```json
  { "id": "123", "status": "pending" }
  ```

#### **Scenario 2: Dynamic Mock (Scripted Responses)**
Use conditional logic or delays to simulate real-world behavior.
```java
// WireMock with dynamic response based on request body
WireMock.stubFor(WireMock.post(urlEqualTo("/orders"))
    .withRequestBody(MatchingJson.just("{\"productId\": \"prod-456\"}"))
    .willReturn(aResponse()
        .withStatus(201)
        .withBody("{\"id\": \"789\", \"productId\": \"prod-456\"}")));
```

#### **Scenario 3: Delayed Responses**
Simulate network latency or timeout scenarios.
```java
// WireMock with delay
WireMock.stubFor(WireMock.get(urlEqualTo("/slow-endpoint"))
    .willReturn(aResponse()
        .withFixedDelay(3000)  // 3-second delay
        .withStatus(200)
        .withBody("{\"status\": \"ok\"}")));
```

---

### **3.4 Schema Validation**
Ensure request/response payloads match expected schemas using tools like **JSON Schema** or **OpenAPI**.

#### **Example: Validate Order Request with JSON Schema**
```json
// OrderRequestSchema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string", "minLength": 3 },
    "productId": { "type": "string", "pattern": "^prod-[0-9]{6}" }
  },
  "required": ["id", "productId"]
}
```
**Validation in Code (Python)**:
```python
import jsonschema
from jsonschema import validate

schema = {...}  # Load from OrderRequestSchema.json
request_body = {"id": "abc", "productId": "prod-123456"}

try:
    validate(instance=request_body, schema=schema)
    print("Request is valid!")
except jsonschema.ValidationError as e:
    print(f"Invalid request: {e}")
```

---

### **3.5 Handling Contract Mismatches**
When contracts change, follow this workflow:
1. **Consumer-Driven**:
   - The provider fails tests when they don’t match the consumer’s contract.
   - Example: Provider returns `201` but consumer expects `202` (Accepted).
2. **Provider-Driven**:
   - The consumer updates their tests to reflect the provider’s changes.
   - Example: Provider adds a new field `deliveryDate` to the response.
3. **Resolution**:
   - Negotiate backward/forward compatibility (e.g., add `deliveryDate` as optional).
   - Version contracts (e.g., `v1` vs. `v2`) and update consumers gradually.

---

## **4. Schema Reference**
Define the structure of contracts and mock responses using the following schema:

| **Field**               | **Type**          | **Description**                                                                                     | **Example**                                                                                     |
|-------------------------|-------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **`id`**                | `string`          | Unique identifier for the contract (e.g., for versioning).                                             | `"order-service-v1"`                                                                      |
| **`provider`**          | `string`          | Name of the API provider service.                                                                     | `"payment-service"`                                                                             |
| **`consumer`**          | `string`          | Name of the API consumer service.                                                                     | `"e-commerce-frontend"`                                                                         |
| **`version`**           | `string`          | Semantic version of the contract (e.g., `1.0.0`).                                                      | `"1.2.0"`                                                                                     |
| **`environments`**      | `array<string>`   | Environments where the contract applies (e.g., `dev`, `prod`).                                        | `["dev", "staging"]`                                                                          |
| **`interactions`**      | `array<Interaction>` | List of HTTP interactions (request/response pairs).                                                  | See table below.                                                                               |
| **`schemas`**           | `object`          | Reference to JSON Schema definitions for validation.                                                  | `{ "User": {...}, "Order": {...} }`                                                          |

#### **Interaction Schema**
| **Field**          | **Type**          | **Description**                                                                                     | **Example**                                                                                     |
|--------------------|-------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **`description`**  | `string`          | Human-readable description of the interaction.                                                      | `"Create a new order"`                                                                      |
| **`request`**      | `object`          | Request details (method, path, headers, body).                                                      | `{ "method": "POST", "path": "/orders", "headers": { "Content-Type": "application/json" } }` |
| **`response`**     | `object`          | Response details (status, headers, body, errors).                                                   | `{ "status": 201, "body": { "id": "123" } }`                                                   |
| **`matches`**      | `object`          | Optional: Pattern matching rules (e.g., regex for dynamic values).                                  | `{ "request.body.id": "^\\d{3}-\\d{3}-\\d{4}$" }`                                              |

**Full Example Contract**:
```json
{
  "id": "order-service-v1",
  "provider": "inventory-api",
  "consumer": "e-commerce-frontend",
  "version": "1.0.0",
  "environments": ["dev", "prod"],
  "interactions": [
    {
      "description": "Create an order",
      "request": {
        "method": "POST",
        "path": "/orders",
        "headers": { "Content-Type": "application/json" },
        "body": { "productId": "prod-456", "quantity": 2 }
      },
      "response": {
        "status": 201,
        "body": { "id": "abc123", "status": "pending" }
      }
    }
  ],
  "schemas": {
    "OrderRequest": {
      "$ref": "#/definitions/OrderRequest"
    }
  }
}
```

---

## **5. Query Examples**
### **5.1 Mocking a GET Endpoint with WireMock**
**Goal**: Mock a `/users/{id}` endpoint that returns a user’s details.
```java
// Java (WireMock)
WireMock.stubFor(WireMock.get(urlPathEqualTo("/users/123"))
    .willReturn(aResponse()
        .withStatus(200)
        .withHeader("Content-Type", "application/json")
        .withBody("{\"id\": \"123\", \"name\": \"Alice\", \"email\": \"alice@example.com\"}")));
```

**Verification**:
```bash
curl http://localhost:8080/users/123
# Output:
# { "id": "123", "name": "Alice", "email": "alice@example.com" }
```

---

### **5.2 Running a Pact Consumer Test**
**Scenario**: Verify that a consumer’s `/users` endpoint matches the provider’s contract.
```bash
# Run Pact tests (Node.js)
pact-test --provider="user-service" --consumer="frontend-app" --provider-state-preparator="pact-mock-service"
```

**Test File (`pact-spec.js`)**:
```javascript
const { Pact, Matchers } = require('@pact-foundation/pact');

describe('Frontend API Contract Tests', () => {
  const provider = new Pact({
    consumer: 'frontend-app',
    provider: 'user-service',
    port: 9292,
    log: 'DEBUG',
  });

  beforeAll(() => provider.setup());

  afterAll(() => provider.finalize());

  describe('GET /users', () => {
    it('should return a user', () => {
      const expect = provider.expectInteraction({
        uponReceiving: 'a request to get a user',
        withRequest: {
          method: 'GET',
          path: '/users/123',
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: provider.matchers.json({
            id: Matchers.somethingLike('123'),
            name: Matchers.somethingLike('Alice'),
          }),
        },
      });

      return fetch('http://localhost:9292/users/123')
        .then(response => response.json())
        .then(body => {
          expect.receive();
          expect.toBeRespondedWith();
        });
    });
  });
});
```

---

### **5.3 Validating a Request Against a Schema**
**Goal**: Validate a `/orders` request body against a JSON Schema.
```python
import jsonschema
from jsonschema import validate

# Load schema
schema = {
  "type": "object",
  "properties": {
    "productId": { "type": "string" },
    "quantity": { "type": "integer", "minimum": 1 }
  },
  "required": ["productId", "quantity"]
}

# Test request
request_body = {"productId": "prod-123", "quantity": 2}

try:
    validate(instance=request_body, schema=schema)
