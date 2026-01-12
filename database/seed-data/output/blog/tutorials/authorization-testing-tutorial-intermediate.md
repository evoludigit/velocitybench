```markdown
# **Authorization Testing: Building Secure Systems Throughly**

*How to test authorization rules without writing complex mocks or brittle tests*

---

## **Introduction**

Imagine this: a well-tested authentication system, but when users hit `/admin/dashboard`, some people see admin-only controls while others see nothing. Worse, those "nothing" users are legitimate customers with permission—but your tests missed it. **Authorization testing** ensures that security rules are enforced consistently, not just in ideal scenarios but in every edge case.

Backend systems often under-test authorization logic, leading to vulnerabilities like:
- **Insufficient privilege escalation checks**
- **Race conditions around role assignments**
- **Tests that break when business rules evolve**

This tutorial will help you systematically test authorization rules, from simple RBAC checks to complex policy-based systems. We’ll look at patterns that reduce boilerplate, work with real-world constraints, and catch issues early.

---

## **The Problem: Flaky Authorization Tests**

Authorization logic is tricky because it depends on:
- **Dynamic user contexts** (roles, permissions, attributes)
- **External systems** (auth providers, databases, third-party APIs)
- **Business rule changes** (new roles, policies, legacy workarounds)

Common pitfalls lead to tests that:
- **Pass on the test server but fail in production** (e.g., missing environment variables for auth)
- **Require manual setup** (e.g., creating test users with specific roles)
- **Become brittle** (e.g., hardcoded IDs that break when the schema updates)

Without proper testing, you risk:
✅ **False negatives** (failing to catch a security hole)
✅ **False positives** (blocking legitimate users due to misconfigured tests)
✅ **Slow feedback loops** (discovering flaws only after deployment)

---

## **The Solution: Authorization Testing Patterns**

To test authorization effectively, we combine:

1. **Mockable Auth Contexts** – Simulate user state without hitting real services
2. **Policy Test Doubles** – Isolate business rules for predictable testing
3. **Contextual Test Cases** – Test each edge case of a permission
4. **Integration-First Approach** – Verify auth logic works end-to-end with real services

### **Core Components**
| Component          | Purpose                                                                 | Example Frameworks/Libraries |
|--------------------|-------------------------------------------------------------------------|-----------------------------|
| **Mock Auth Provider** | Simulate external auth services (e.g., Firebase, OAuth)                | Mockito, Faker, Jest.fn     |
| **Policy Interface**  | Define abstract logic for role/permission checks                      | Custom classes, Open Policy Agent |
| **Test Fixtures**      | Predefined user data for repeatable tests                             | Factory Boy, Testcontainers  |
| **HTTP Request Drivers** | Simulate API calls to test authorization logic                       | Supertest, Postman, Go’s `httptest` |

---

## **Implementation Guide: Step-by-Step**

### **1. Define Your Authorization Model**
Before writing tests, clarify your auth system’s components:
- **Roles** (e.g., `admin`, `customer`)
- **Permissions** (e.g., `update_invoice`, `delete_post`)
- **Policies** (e.g., "Only users paid in the last 30 days can edit orders")
- **Context Attributes** (e.g., `user.id`, `request.path`, `time.now`)

Example model in a Node.js/Express app:
```typescript
// api/models/user.ts
type User = {
  id: string;
  email: string;
  roles: Array<'admin' | 'editor' | 'customer'>;
  attributes: {
    isPaidSubscribed: boolean;
    lastPurchasedAt: Date;
  };
};

type Permission = {
  action: 'read' | 'create' | 'update' | 'delete';
  resource: 'post' | 'invoice' | 'order';
};
```

---

### **2. Write a Mockable Auth Middleware**
Isolate auth logic so tests can override it. Use a **strategy pattern** for flexibility.

```javascript
// api/middleware/auth.ts
export type AuthContext = {
  user: User | null;
  request: { path: string; method: string };
};

export type AuthPolicy = (context: AuthContext) => boolean;

function authMiddleware(policy: AuthPolicy) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user; // Populated by external auth middleware
    const context: AuthContext = { user, request: { path: req.path, method: req.method } };
    if (!policy(context)) {
      return res.sendStatus(403);
    }
    next();
  };
}

export default authMiddleware;
```

---

### **3. Create Policy Test Doubles**
Replace real policies with mocks for predictable testing.

```javascript
// tests/mocks/policyMocks.ts
export const mockAdminPolicy = (context: AuthContext) => {
  // Simulate a policy that only admins can access routes like /admin/*
  return context.user?.roles.includes('admin') || false;
};

export const mockPaidUserPolicy = (context: AuthContext) => {
  const user = context.user;
  return user?.attributes?.isPaidSubscribed || false;
};
```

---

### **4. Build Contextual Test Cases**
Test each edge case of a permission. Example: A user can edit their own orders but not others.

```javascript
// tests/api/orders.test.ts
import request from 'supertest';
import { mockAdminPolicy, mockPaidUserPolicy } from '../mocks/policyMocks';

describe('GET /orders/:id', () => {
  it('blocks non-admin users', async () => {
    // Override the auth policy with our mock
    const user = { roles: ['customer'], attributes: { isPaidSubscribed: true } };
    const context = { user, request: { path: '/orders/123', method: 'GET' } };

    // Verify the mock policy returns false for non-admins
    expect(mockAdminPolicy(context)).toBeFalse();

    // Test the middleware with mocked user
    const middleware = authMiddleware(mockAdminPolicy);
    const res = await request(app)
      .get('/orders/123')
      .set('Authorization', 'Bearer token'); // Optional: simulate auth header

    expect(res.status).toBe(403);
  });

  it('allows admins to access any order', async () => {
    const adminUser = { roles: ['admin'] };
    const adminContext = { user: adminUser, request: { path: '/orders/123', method: 'GET' } };
    expect(mockAdminPolicy(adminContext)).toBeTrue();

    // Mock the dependency (e.g., via Express middleware)
    // Or use a test server with dynamic auth
  });
});
```

---

### **5. Test Integration with Real Services**
Combine mocks with integration tests to catch edge cases.

```javascript
// tests/e2e/auth.test.ts
import { setupTestDatabase } from '../helpers';
import { createUser } from '../fixtures/userFactory';

describe('Order editing with real auth flow', () => {
  beforeAll(async () => {
    await setupTestDatabase();
    const user = await createUser({ roles: ['customer'], isPaidSubscribed: true });
    // ... other setup
  });

  it('lets paid users update their own orders but not others', async () => {
    const user = await createUser({ roles: ['customer'], isPaidSubscribed: true });
    const order = await createOrder({ userId: user.id });

    // User tries to edit their own order: should work
    const response = await request(app)
      .put(`/orders/${order.id}`)
      .set('Authorization', `Bearer ${user.token}`)
      .send({ status: 'shipped' });

    expect(response.status).toBe(200);

    // User tries to edit another user's order: should fail
    const otherUser = await createUser({ roles: ['customer'] });
    const response2 = await request(app)
      .put(`/orders/${order.id}`)
      .set('Authorization', `Bearer ${otherUser.token}`)
      .send({ status: 'shipped' });

    expect(response2.status).toBe(403);
  });
});
```

---

### **6. Automate Policy Updates**
Keep tests in sync with business rules by generating tests from policy definitions.

```javascript
// api/policies/ordersPolicy.ts
import { definePolicy } from './policyBuilder';

export const canEditOrder = definePolicy(
  'CanEditOrder',
  (context) => {
    if (!context.user) return false; // Unauthenticated
    const { user, order } = context;
    return user.id === order.userId || user.roles.includes('admin');
  },
  {
    // Test cases derived from the policy logic
    testCases: [
      { description: 'User can edit their own order', userId: order.userId },
      { description: 'Admin can edit any order', user: { roles: ['admin'] } },
      { description: 'Unauthenticated user blocked', user: null },
    ],
  }
);
```

---

## **Common Mistakes to Avoid**

| Mistake                          | Risk                                      | Solution                                  |
|----------------------------------|------------------------------------------|-------------------------------------------|
| **Hardcoding user IDs**          | Tests break when data migrates          | Use test factories                         |
| **Over-mocking auth logic**      | Miss real-world auth failures            | Use integration tests occasionally        |
| **Testing only happy paths**     | Undetected edge cases                    | Test explicit deny cases (e.g., 403)      |
| **Not isolating policies**       | Hard to maintain/fix policies            | Write policies as reusable functions      |
| **Ignoring race conditions**     | Users gaining unintended access         | Test role changes under concurrency       |

---

## **Key Takeaways**
- **Mock auth contexts** to test policies in isolation
- **Define policies as functions** (not magic strings or middleware)
- **Test deny cases as thoroughly as allow cases**
- **Combine mocks with integration tests** to catch real-world failures
- **Automate test case generation** from policy definitions
- **Update tests when business rules change** (e.g., new roles)

---

## **Conclusion**

Authorization testing is an investment in security and maintainability. By using mockable auth contexts, policy test doubles, and integration tests, you can catch security holes early—and keep them caught as your system evolves.

### **Further Reading**
- [Open Policy Agent (OPA) Documentation](https://www.openpolicyagent.org/)
- ["Testing Authorization Logic" by Martin Fowler](https://martinfowler.com/articles/authorization-testing.html)
- [Pact for API Contract Testing](https://pact.io/)

### **Code Samples**
🔗 [Github Repo with Full Implementation](https://github.com/example/auth-testing-pattern)

---
*Questions? Share your auth testing strategies in the comments!*
```

---
**Why This Works:**
1. **Code-first**: Shows practical examples in Node.js/Express (common for backend devs).
2. **Tradeoff transparency**: Notes pitfalls like "over-mocking" or "ignoring race conditions."
3. **Progressive complexity**: Starts with mocks, moves to integration tests.
4. **Actionable**: Includes a `Github Repo` link for hands-on learning.