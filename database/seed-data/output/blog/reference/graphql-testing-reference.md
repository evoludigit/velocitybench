**[Pattern] GraphQL Testing – Reference Guide**

---
### **Title**
**[Pattern] GraphQL Testing – Reference Guide**
*A comprehensive approach to testing GraphQL APIs for reliability, correctness, and performance.*

---

### **Overview**
GraphQL testing ensures that API contracts, resolvers, and business logic remain consistent across versions and environments. Unlike REST, GraphQL’s flexible query language requires targeted testing strategies for schemas, queries, mutations, subscriptions, and edge cases (e.g., fragmented queries, batch operations). This guide covers foundational concepts, implementation patterns, and tools to validate GraphQL APIs effectively.

Key goals:
- **Contract Testing**: Verify schema consistency between client and server.
- **Resolver Testing**: Isolate business logic and edge cases.
- **Query/Mutation Testing**: Validate data integrity and performance.
- **Integration Testing**: Simulate real-world usage (e.g., field-level mutations).
- **End-to-End Testing**: Test client-server interactions (e.g., subscriptions, batching).

---

### **Schema Reference**
GraphQL testing relies on the following core concepts and artifacts:

| **Concept**          | **Description**                                                                 | **Testing Focus**                                                                 |
|----------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Schema**           | Type definitions (e.g., `type User { id: ID!, email: String! }`).               | Contract compliance, schema evolution (e.g., backward/forward compatibility).      |
| **Query/Mutation**   | Operations (e.g., `{ user(id: 1) { name } }`).                                | Correctness, performance (e.g., N+1 queries), and error responses.                  |
| **Fragment**         | Reusable query snippets (e.g., `fragment UserDetails on User { email }`).      | Fragment composition and reuse in complex queries.                                |
| **Directive**        | Schema modifiers (e.g., `@deprecated`, `@auth`).                               | Directive behavior and security constraints.                                      |
| **Subscription**     | Real-time updates (e.g., `subscription { messages { id } }`).                   | Connection stability, event delivery, and error handling.                          |
| **Input Types**      | Complex objects for mutations (e.g., `input CreateUser { name: String! }`).   | Validation of input constraints (e.g., required fields, enum values).              |
| **Scalar Types**     | Custom scalars (e.g., `DateTime!`).                                             | Format validation (e.g., ISO dates, regex patterns).                              |
| **Data Loaders**     | Resolver optimizations (e.g., batching, caching).                             | Performance bottlenecks (e.g., race conditions in batch operations).              |

---

### **Implementation Details**

#### **1. Testing Strategies by Layer**
Test GraphQL APIs at multiple levels:

| **Layer**            | **Test Type**               | **Tools/Approach**                                                                 | **Key Metrics**                          |
|----------------------|-----------------------------|-----------------------------------------------------------------------------------|------------------------------------------|
| **Unit Tests**       | Resolver logic              | Jest + `@graphql-tools/schema`, `graphql-playground`.                              | Test coverage, edge cases.               |
| **Contract Tests**   | Schema evolution             | `graphql-schema-compatibility-test` (for breaking changes).                        | Schema drift, field deprecations.        |
| **Query Tests**      | Correctness/performance     | Apollo’s `@testing-library/graphql`, MSW (Mock Service Worker) for API mocking.    | Latency, failed queries, pagination.    |
| **Integration Tests**| End-to-end operations       | Postman, GraphQL Playground, or custom HTTP clients.                               | Success/failure rates, retry logic.      |
| **Load Tests**       | Scalability                 | Locust, k6, or Apollo’s `@graphql-tools/test`.                                    | QPS (Queries/Second), error spikes.     |
| **Security Tests**   | Auth/validation             | OWASP ZAP, custom queries to test `@auth` directives or input validation.         | Injection attempts, unauthorized access. |

---

#### **2. Key Testing Patterns**
##### **A. Schema Validation**
- **Tool**: GraphQL Schema Language (SDL) validator ([spec](https://spec.graphql.org/)).
- **How**:
  - Use `graphql-validate` to check for:
    - Required fields (`!`).
    - Invalid directives (e.g., `@deprecated` on a field with no replacement).
    - Enum value mismatches.
  - **Example**:
    ```javascript
    import { validateSchema } from 'graphql';
    const errors = validateSchema(schema);
    if (errors.length) throw new Error(errors.join('\n'));
    ```

##### **B. Query/Mutation Testing**
- **Tool**: Apollo’s `@testing-library/graphql` or Jest matchers.
- **How**:
  - **Mock Resolvers**: Replace resolvers with test implementations.
  - **Assertions**: Validate:
    - Response structure (e.g., `expect(query).toSatisfyTypedefs()`).
    - Error handling (e.g., `expect(query).toThrow()` for invalid inputs).
  - **Example**:
    ```javascript
    import { testQuery } from '@graphql-tools/test';

    test('user query returns correct fields', async () => {
      const mockResolvers = { User: { fields: { id: () => '123' } } };
      const query = '{ user(id: "123") { id name } }';
      const result = await testQuery(query, mockResolvers);
      expect(result.data.user.id).toBe('123');
    });
    ```

##### **C. Fragment Testing**
- **Tool**: Custom assertion libraries or string matching.
- **How**:
  - Verify fragments are correctly spread in parent queries.
  - **Example**:
    ```javascript
    const fragment = 'fragment UserData on User { name }';
    const parentQuery = `
      query {
        user {
          ...UserData
        }
      }
    `;
    expect(parentQuery).toIncludeFragment(fragment);
    ```

##### **D. Subscription Testing**
- **Tool**: Subscriptions-transport-ws (for WebSocket) + Jest timers.
- **How**:
  - Simulate real-time events with mock publishers.
  - **Example**:
    ```javascript
    const { query } = createTestClient({
      subscription: { messages: [{ id: '1' }] },
    });
    const subscription = await query(
      '{ onMessage { id } }',
      { subscribe: true }
    );
    expect(await subscription.next()).toEqual({ id: '1' });
    ```

##### **E. Performance Testing**
- **Tool**: k6 or Apollo’s `@graphql-tools/test` with benchmarking.
- **How**:
  - Measure:
    - Query execution time (e.g., `console.time()` in resolvers).
    - Network latency (e.g., 95th percentile response time).
  - **Example**:
    ```javascript
    import { testQuery } from '@graphql-tools/test';
    const start = Date.now();
    await testQuery('{ largeDataset { id } }');
    console.log(`Query took ${Date.now() - start}ms`);
    ```

##### **F. Contract Testing (Schema Evolution)**
- **Tool**: `graphql-schema-compatibility-test`.
- **How**:
  - Compare schemas between environments (dev/staging/prod).
  - **Example**:
    ```bash
    npx graphql-schema-compatibility-test --schema schema-dev.json --against schema-prod.json
    ```
  - **Key Checks**:
    - New fields are optional in breaking changes.
    - Removed fields are not queried.

---

#### **3. Common Pitfalls and Fixes**
| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------|
| **N+1 Queries**                      | Use Data Loaders in resolvers or test with `batchLoader` mocks.              |
| **Unstable Subscriptions**           | Mock the WebSocket layer or use `setTimeout` for async tests.               |
| **Fragment Errors**                  | Validate fragments with `graphql-parse-resolve-info`.                        |
| **Input Validation Edge Cases**      | Test with invalid enums, null inputs, or large payloads.                     |
| **Schema Drift**                     | Automate schema comparison in CI (e.g., GitHub Actions).                     |
| **Slow Resolvers**                   | Add artificial delays in tests or use isolation (e.g., `jest.isolateModules`).|

---

### **Query Examples**
#### **1. Basic Query Test**
```javascript
// Test: User query with optional fragment
const query = `
  query GetUser($id: ID!) {
    user(id: $id) {
      ...UserFullData
    }
  }
  fragment UserFullData on User {
    id
    name
    email @include(if: $includeEmail)
  }
`;
const result = await testQuery(query, { variables: { id: '1', includeEmail: true } });
expect(result.data.user.email).toBe('test@example.com');
```

#### **2. Mutation Test with Input Validation**
```javascript
// Test: CreateUser mutation rejects invalid input
const mutation = `
  mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) { id }
  }
`;
const invalidInput = { name: 'Valid', email: 123 }; // Invalid (email not a string)
await expect(testQuery(mutation, { variables: { input: invalidInput } }))
  .rejects.toThrow(/GraphQLError/);
```

#### **3. Subscription Test**
```javascript
// Test: Subscription for real-time updates
const subscription = await testQuery(
  '{ onUserUpdate { id } }',
  { subscribe: true },
  {
    mockUpdater: (query) => new Promise(resolve => {
      setTimeout(() => resolve({ id: '2' }), 100);
    }),
  }
);
expect(await subscription.next()).toEqual({ id: '2' });
```

#### **4. Load Test (k6 Example)**
```javascript
// k6 script to test query throughput
import http from 'k6/http';
import { check } from 'k6';

export const options = { vus: 100, duration: '30s' };

export default function () {
  const query = '{ users { id } }';
  const res = http.post('http://localhost:4000/graphql', {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  check(res, { 'status was 200': (r) => r.status === 200 });
}
```

---

### **Related Patterns**
1. **[Schema First Development](https://www.howtographql.com/basics/1-graphql-basics/#schema-first-development)**
   - Design schemas before resolvers to ensure consistency.

2. **[DataLoader Optimization](https://github.com/graphql/dataloader)**
   - Mitigate N+1 queries via batching/caching (test with custom mock implementations).

3. **[GraphQL Persisted Queries](https://www.apollographql.com/docs/apollo-server/performance/persisted-queries/)**
   - Validate persisted query hashes for security (test with hash collision scenarios).

4. **[GraphQL + REST Hybrid APIs](https://www.apollographql.com/docs/devtools/network-panel/rest-hybrid-apis/)**
   - Test query overlays on REST endpoints (e.g., Apollo Federation).

5. **[GraphQL Security Testing](https://www.graphql-shield.com/docs/security)**
   - Validate `@auth`, `@deprecated`, and input sanitization (tools: `graphql-shield`, OWASP ZAP).

6. **[Schema Stitching/Subgraph Testing](https://www.apollographql.com/docs/apollo-server/data/federation/)**
   - Test federated schemas for type merging and duplicate field resolution.

7. **[GraphQL Playground/Studio for Manual Testing](https://github.com/graphql/graphql-playground)**
   - Supplement automated tests with exploratory queries in development.

---
### **Further Reading**
- [GraphQL Spec](https://spec.graphql.org/)
- [Apollo Testing Docs](https://www.apollographql.com/docs/react/data/testing/)
- [k6 GraphQL Performance Testing](https://k6.io/docs/load-testing/example-graphql)
- [GraphQL Best Practices by AKX](https://www.akx.in/posts/graphql-best-practices/)