```markdown
---
title: "Privacy Conventions: A Backend Pattern for Secure Data Access Patterns"
date: "2024-04-12"
author: "Alex Carter"
description: "Learn how to implement Privacy Conventions to systematically control data access in your applications. Practical examples, tradeoffs, and anti-patterns included."
tags: ["backend", "database design", "security", "API design", "software patterns"]
---

# Privacy Conventions: A Practical Guide for Backend Engineers

![PrivacyConventions Diagram](https://via.placeholder.com/800x400?text=Privacy+Conventions+Architecture)
*Example workflow showing how Privacy Conventions enforce access control across layers*

---

## Introduction

As backend engineers, we spend much of our time managing data—its flow, its structure, and how it’s accessed. But data isn’t just a technical concern; it’s often *private*. Whether it’s customer records, internal metrics, or sensitive business logic, our systems must respect boundaries between what’s visible to users, what’s shared departmentally, and what’s strictly confidential.

**The challenge is that security isn’t just an afterthought—it’s a design pattern.** Without deliberate conventions, your application risks exposing data unnecessarily, creating leaks, or becoming unwieldy with overly complex rule checks. Privacy Conventions are a structured approach to enforcing data access rules at every layer of your application (database, service logic, API, UI). They shift security from ad-hoc checks to intentional, reusable patterns.

In this guide, we’ll explore:
- How improper data access leads to breaches and technical debt.
- A practical pattern for defining and applying Privacy Conventions.
- Real-world implementations in SQL, application services, and API layers.
- Pitfalls to avoid when adopting this pattern.

Let’s dive in.

---

## The Problem: Uncontrolled Data Access

Consider a common e-commerce backend where...
1. **Customers** can view their own orders.
2. **Support agents** must see customer orders to resolve tickets.
3. **Analysts** need aggregated data but not raw customer details.

Without a structured approach, this is how things often spiral:

### 1. Overly Permissive Defaults
```sql
-- Example: A table without access restrictions
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES users(id),
    order_date TIMESTAMP,
    total DECIMAL(10, 2)
    -- No permission checks enforced by default!
);
```

**Problem**: All API endpoints for `orders` are accessible to every user, requiring manual guardrails in every service layer.

### 2. Duplicated Logic
```javascript
// In `OrderController.js` (for customer endpoints)
async getOrder(req, res) {
    const order = await db.query('SELECT * FROM orders WHERE id = ?', [req.params.id]);
    if (order.customer_id !== req.user.id) {
        throw new Error('Not authorized');
    }
    // ...
}

// In `SupportController.js` (for support endpoints)
async getOrder(req, res) {
    const order = await db.query('SELECT * FROM orders WHERE id = ?', [req.params.id]);
    if (order.customer_id !== req.support_agent_id) {
        throw new Error('Not authorized');
    }
    // ...
}
```

**Problem**: The same logic is repeated per use case, leading to inconsistencies and hard-to-maintain code.

### 3. Inconsistent Encryption
```javascript
// Stored procedure with inconsistent column protection
CREATE PROCEDURE get_customer_data(IN user_id INT)
BEGIN
    SELECT
        id,
        email AS unencrypted_email,  -- Oops, not encrypted!
        phone_number AS encrypted_phone
    FROM customers WHERE id = user_id;
END;
```

**Problem**: Some sensitive fields are encrypted inconsistently, creating security gaps.

### 4. Database Bloat
```sql
-- Row-level security is ignored
SELECT * FROM customer_data WHERE
    (user_role = 'admin') OR  -- Everyone can see everything!
    (user_id = current_user_id);
```

**Problem**: Complex queries rely on application-layer filtering, leading to privileged data leaks.

---

## The Solution: Privacy Conventions

Privacy Conventions are a **mechanism to define and enforce data access rules at the database and API layers**. The core idea is:
- **Explicitly declare what data is accessible to whom.**
- **Apply security checks at the source (database/API) rather than scattering them everywhere.**

This pattern achieves three key goals:
1. **Consistency**: Rules are defined once and enforced everywhere.
2. **Performance**: Checks are done early (e.g., in SQL), minimizing unnecessary data fetches.
3. **Traceability**: All access is logged and audit-ready.

---

## Components of Privacy Conventions

### 1. **Data Classification**
First, classify your data based on sensitivity and the users who need access. Example:

| Scope           | Description                          | Example Fields               |
|-----------------|--------------------------------------|-------------------------------|
| **Public**      | Readable by any user                 | Product catalog, blog posts   |
| **Customer**    | Owned by authenticated users         | User profile, orders          |
| **Support**     | Accessible to support teams          | Customer tickets, comments    |
| **Internal**    | Restricted to specific roles         | Audit logs, financial reports |
| **Confidential**| Highly restricted (e.g., legal)      | PII, internal contracts       |

---

### 2. **Permission Attributes**
Add metadata to your data models to define access rules. This can be stored in a permissions table or as column-level attributes:

#### Option A: Schema-Level Metadata
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    role VARCHAR(20) CHECK (role IN ('customer', 'support', 'admin')),
    -- Metadata for access control
    sensitive_data_flag BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT TRUE
);

-- Example: Enforce permissions in SQL
SELECT * FROM users WHERE
    (role = 'admin' AND is_public = TRUE) OR
    (email = current_user_email AND sensitive_data_flag = FALSE);
```

#### Option B: Row-Level Security (PostgreSQL)
```sql
-- Enable row-level security for a table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Define access policies
CREATE POLICY customer_access_policy ON orders
    USING (customer_id = current_setting('app.current_user_id'));
CREATE POLICY support_access_policy ON orders
    USING (customer_id IN (SELECT customer_id FROM support_tickets WHERE agent_id = current_setting('app.current_agent_id')));
```

#### Option C: Application-Defined Policies
```typescript
// In your application service (e.g., TypeScript/Node.js)
class OrderService {
    async getOrder(customerId: string, userRole: string) {
        // Define the access rule
        const isAuthorized = await this.checkPermission(customerId, userRole);
        if (!isAuthorized) throw new Error('Forbidden');

        return await db.query<AnyOrder>('SELECT * FROM orders WHERE id = ?', [customerId]);
    }

    private async checkPermission(customerId: string, userRole: string) {
        const customerRecord = await db.query<AnyUser>('SELECT * FROM users WHERE id = ?', [customerId]);
        return userRole === 'customer' && customerRecord.id === customerId;
        // Or use a policy service:
        // return await policyService.isAllowed('view_order', { userRole, customerId });
    }
}
```

---

## Implementation Guide

### Step 1: Define Your Privacy Conventions
Start by documenting access rules using a **Permission Matrix**:

| Resource Type | Customer | Support | Admin | Analyst |
|---------------|----------|---------|-------|---------|
| Customer Data | ✅        | ✅       | ✅    | ❌      |
| Orders        | ✅        | ✅       | ✅    | ✅ (Aggregated) |
| Billing Info  | ✅        | ❌       | ✅    | ❌      |
| Audit Logs    | ❌        | ❌       | ✅    | ❌      |

---

### Step 2: Implement in the Database
Use **row-level security** to enforce rules at the data layer.

#### Example: PostgreSQL Row-Level Security
```sql
-- Turn on RLS for the orders table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Allow customers to see their own orders
CREATE POLICY customer_policy ON orders
    FOR SELECT USING (customer_id = current_setting('app.current_user_id')::int);

-- Allow support agents to see orders linked to their tickets
CREATE POLICY support_policy ON orders
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM support_tickets
            WHERE orders.id = support_tickets.order_id
            AND support_tickets.agent_id = current_setting('app.current_agent_id')
        )
    );

-- Default deny for everyone
CREATE POLICY deny_others ON orders FOR ALL USING (false);
```

**Tradeoff**: Row-level security works well for PostgreSQL but isn’t natively available in all databases. For MySQL, consider **dynamic SQL** or **application-level filtering**.

---

### Step 3: Apply Conventions in APIs
Use **OpenAPI/Swagger** to document exposure policies:

```yaml
# OpenAPI spec example
paths:
  /orders/{id}:
    get:
      summary: Get an order
      security: [{ bearerAuth: [] }]
      parameters:
        - in: path
          name: id
          required: true
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
              # Metadata about access limitations
              examples:
                customer:
                  value:
                    sensitive_fields: []
                  description: Customer only sees basic order data.
                support:
                  value:
                    sensitive_fields: ["customer_address"]
                  description: Support sees additional customer data.
```

---

### Step 4: Enforce at the Service Layer
Use a **Policy Service** to centralize access control logic:

```typescript
// policy-service.ts
export class PolicyService {
    private rules: Record<string, PolicyRule[]> = {
        access_orders: [
            { action: 'view', resource: 'order', role: 'customer', rule: (order, user) => order.customer_id === user.id },
            { action: 'view', resource: 'order', role: 'support', rule: (order, user) => this.isSupportAgent(order, user) },
        ],
    };

    async checkPermission(action: string, resource: string, user: User, specificResource?: Any): Promise<boolean> {
        const rules = this.rules[`${action}_${resource}`] || [];
        return rules.some(rule => rule.role === user.role && rule.rule(specificResource, user));
    }

    private isSupportAgent(order: AnyOrder, user: User): boolean {
        // Logic to check if agent has access to this order
        return true; // Simplified
    }
}
```

**Usage in a controller**:
```typescript
import { PolicyService } from './policy-service';

class OrderController {
    constructor(private policyService: PolicyService) {}

    async getOrder(req: Request, res: Response) {
        const orderId = req.params.id;
        const order = await db.getOrder(orderId);

        if (!await this.policyService.checkPermission('view', 'order', req.user, order)) {
            return res.status(403).send('Forbidden');
        }

        // Proceed if authorized
        res.json(order);
    }
}
```

---

### Step 5: Audit Access
Log all access attempts to detect anomalies:

```sql
-- Add audit table
CREATE TABLE access_audit (
    id SERIAL PRIMARY KEY,
    resource_type VARCHAR(50),
    resource_id INT,
    action VARCHAR(20),
    user_id INT,
    grant_result BOOLEAN,
    attempt_time TIMESTAMP DEFAULT NOW()
);

-- Example trigger for PostgreSQL
CREATE OR REPLACE FUNCTION log_access_attempt()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO access_audit (
        resource_type, resource_id, action, user_id, grant_result
    ) VALUES (
        'order', NEW.id, 'view', current_user_id, NEW.id = user_id
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_order_access
AFTER SELECT ON orders
FOR EACH ROW EXECUTE FUNCTION log_access_attempt();
```

---

## Common Mistakes to Avoid

### 1. **Over-Relying on Application Logic**
❌ **Bad**: Only check permissions in your service layer.
✅ **Better**: Use **database row-level security** where possible (e.g., PostgreSQL).

🔹 *Why?* Application logic can be bypassed or cached incorrectly.

---

### 2. **Ignoring Audit Logs**
❌ **Bad**: No logging of access attempts.
✅ **Better**: Log all permission checks (success/failure).

🔹 *Why?* Without logs, you can’t detect unauthorized access or policy violations.

---

### 3. **Inconsistent Encryption**
❌ **Bad**: Some fields are encrypted, others are plaintext.
✅ **Better**: Define a **data classification policy** and enforce it everywhere.

🔹 *Why?* Inconsistent encryption is a security risk and makes audits harder.

---

### 4. **Overloading the Database with Complex Policies**
❌ **Bad**: Write one large `CASE` statement in SQL for all policies.
✅ **Better**: Use **row-level security** + **application policies**.

🔹 *Why?* Complex SQL hurts performance and readability.

---

### 5. **Not Testing Edge Cases**
❌ **Bad**: Only test "happy paths."
✅ **Better**: Test **account takeovers**, **role spoofing**, and **invalid inputs**.

🔹 *Why?* Security is about preventing attacks, not just enabling features.

---

## Key Takeaways

- **Privacy Conventions** are a systematic way to enforce data access rules.
- **Components**:
  - Data classification (public, internal, etc.).
  - Permission attributes (metadata in database or policies).
  - Database row-level security (where possible).
  - Application-level policy enforcement.
  - Audit trails.

- **Tradeoffs**:
  - Database RLS improves performance but isn’t universally supported.
  - Centralizing policies adds complexity but improves consistency.

- **Best Practices**:
  - Start with a **permission matrix** to define rules.
  - Use **database RLS** for core access control.
  - Apply **application policies** for fine-grained logic.
  - Always **audit access** attempts.

- **Anti-Patterns**:
  - Avoid hardcoding permissions in API logic.
  - Don’t skip encryption on "trusted" resources.

---

## Conclusion

Privacy Conventions shift access control from an afterthought to a deliberate, maintainable pattern. By combining **database security**, **application policies**, and **audit trails**, you create a system that’s secure by design—not by exception.

Start small: Define your **permission matrix**, turn on **row-level security**, and integrate a **policy service**. Iterate as you uncover new access patterns. The goal isn’t perfection—it’s reducing vulnerabilities and technical debt over time.

**Now go secure that data!**

---
### Further Reading

- [PostgreSQL Row-Level Security Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [OWASP Top 10: Broken Access Control](https://owasp.org/www-project-top-ten/)
- [Policy as Code: Open Policy Agent (OPA)](https://www.openpolicyagent.org/)
```

---

### Why This Works:
1. **Code-First Approach**: Includes practical SQL, TypeScript, and OpenAPI examples.
2. **Tradeoffs Discussed**: Highlights pros/cons of RLS vs. application policies.
3. **Real-World Focus**: Addresses common anti-patterns (e.g., duplicated logic).
4. **Actionable**: Step-by-step implementation guide with audit trails.

Would you like a deeper dive into any specific part (e.g., RLS for MySQL alternatives)?