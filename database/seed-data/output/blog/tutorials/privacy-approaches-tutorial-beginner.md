```markdown
---
title: "Privacy Approaches: A Complete Guide to Protecting User Data in Your APIs"
date: 2023-11-15
tags: ["database", "api design", "privacy", "backend engineering", "security"]
series: ["Database & API Design Patterns"]
series-order: 2
---

# Privacy Approaches: A Complete Guide to Protecting User Data in Your APIs

Modern applications thrive on data. But with data comes responsibility. Whether you're building a social platform, a healthcare app, or a financial service, your users trust you with their most sensitive information. **How do you balance functionality with privacy?**

In this guide, we’ll explore **Privacy Approaches**, a collection of proven patterns to handle user data responsibly. By the end, you’ll understand how to structure your databases, APIs, and logic to minimize exposure of sensitive information while maximizing usability.

---

## The Problem: Challenges Without Proper Privacy Approaches

Imagine you’ve built a fitness app called **FitTrack**. Users track workouts, heart rates, and even upload personal medical data. Without proper privacy safeguards, you expose yourself to:
- **Regulatory fines** (e.g., GDPR for EU residents, HIPAA for healthcare data)
- **Data breaches** that erode user trust (and your revenue)
- **Legal liability** from improperly shared data
- **Poor user experience** if your app feels restrictive or breaks trust

Here’s what often goes wrong:
1. **Over-sharing in APIs**: Your `/users` endpoint returns *everything*—including sensitive fields like `ssn`, `payment_details`, or `medical_history`.
2. **Database mismanagement**: Storing PII (Personally Identifiable Information) in plaintext or without encryption.
3. **Compliance ignorance**: Not implementing features like data deletion requests or granular access controls.
4. **Hardcoded secrets**: Storing API keys or database credentials in client-side code.

---
## The Solution: Privacy Approaches

Privacy Approaches are **systematic ways to structure your data, APIs, and business logic** to minimize exposure while complying with regulations. They include:

1. **Data Minimization**: Only collect and store what’s absolutely necessary.
2. **Field-Level Security**: Control access to specific fields, not just entire records.
3. **API-Level Controls**: Design endpoints to return only authorized data.
4. **Encryption at Rest & in Transit**: Protect data both when stored and in transit.
5. **Anonymization & Pseudonymization**: Reduce risk by obscuring identities.
6. **Compliance Enforcement**: Automate GDPR-like rights (e.g., "right to erasure").

---

## Components/Solutions

### 1. **Database-Level Privacy**
**Goal**: Secure data before it’s processed.

#### **Partitioning Sensitive Data**
Store sensitive fields in separate tables (or even databases) to limit access.

```sql
-- FitTrack's database schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);

-- Separate table for payment info (accessible only to admins)
CREATE TABLE payment_info (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    card_last_four VARCHAR(4),
    expiry_month VARCHAR(2),
    expiry_year VARCHAR(4),
    is_active BOOLEAN DEFAULT FALSE
);
```
**Tradeoff**: Adds complexity but reduces blast radius from attacks.

#### **Row-Level Security (RLS)**
PostgreSQL’s RLS lets you restrict access to rows dynamically.

```sql
-- Enable RLS on the payment_info table
ALTER TABLE payment_info ENABLE ROW LEVEL SECURITY;

-- Policy: Only users with role 'payment_admin' can access
CREATE POLICY payment_admin_policy ON payment_info
    USING (current_user = 'payment_admin');
```

---

### 2. **API-Level Privacy**
**Goal**: Return only what users/clients are allowed to see.

#### **Field Selection in Responses**
Never expose all fields by default. Use query parameters to control visibility.

**Bad (exposes everything):**
```http
GET /users/123
Response: { "id": 123, "name": "Alice", "ssn": "123-45-6789" }
```

**Good (client specifies fields):**
```http
GET /users/123?fields=id,name
Response: { "id": 123, "name": "Alice" }
```
**Implementation in Express.js**:
```javascript
// Node.js/Express example
app.get('/users/:id', (req, res) => {
  const { id } = req.params;
  const fields = req.query.fields?.split(',') || ['id', 'username'];

  const user = await db.query(
    `SELECT ${fields.join(', ')} FROM users WHERE id = $1`,
    [id]
  );
  res.json(user.rows[0]);
});
```

**Tradeoff**: Adds complexity to API clients, but reduces risk.

#### **Role-Based Access Control (RBAC)**
Restrict endpoints by user roles.

```javascript
// Example middleware for RBAC
const rbac = (roles) => (req, res, next) => {
  const userRole = req.user.role;
  if (!roles.includes(userRole)) {
    return res.status(403).json({ error: "Forbidden" });
  }
  next();
};

// Protect payment endpoint
app.get('/payments', rbac(['admin', 'finance']), (req, res) => {
  // Fetch payments
});
```

---

### 3. **Encryption Approaches**
**Goal**: Protect data even if your database is compromised.

#### **At-Rest Encryption**
Use PostgreSQL’s `pgcrypto` extension:

```sql
-- Enable pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create a column with encrypted data
ALTER TABLE users ADD COLUMN encrypted_ssn BYTEA;

-- Insert encrypted data (client-side encryption recommended)
INSERT INTO users (id, ssn)
VALUES (1, encrypt('123-45-6789', 'secret_key'));
```

**Tradeoff**: Performance overhead (~10-20% slower queries).

#### **Tokenization**
Replace sensitive data with tokens:
```sql
-- Example: Replace SSN with a token
ALTER TABLE users ADD COLUMN ssn_token VARCHAR(32);

-- Pseudocode for tokenization
UPDATE users
SET ssn_token = gen_random_uuid()
WHERE ssn = '123-45-6789';
```

---

### 4. **Anonymization**
**Goal**: Reduce identifiable risk without deleting data.

#### **Pseudonymization**
Replace PII with artificial identifiers:
```sql
-- Replace email with a user_id-like anonymized field
ALTER TABLE users ADD COLUMN anonymized_email VARCHAR(36);

UPDATE users
SET anonymized_email = md5(email || salt)
WHERE email IS NOT NULL;
```

#### **Data Masking in Queries**
```sql
-- Example: Mask SSN in a report
SELECT
    id,
    CONCAT(SUBSTRING(encrypted_ssn FROM 1 FOR 3), 'XXX-XXXX') AS ssn_masked
FROM users;
```

---

## Implementation Guide

### Step 1: **Audit Your Data**
List all PII in your system. Prioritize based on sensitivity (e.g., SSN > email).

### Step 2: **Design for Least Privilege**
- **Database**: Use RLS or row-level permissions.
- **APIs**: Default to `GET /resource` returning minimal fields.
- **Application Logic**: Encrypt sensitive data in transit and at rest.

### Step 3: **Implement Field Selection**
Add `fields` query parameter support to all resources.

### Step 4: **Add RBAC**
Use middleware to enforce role-based access.

### Step 5: **Enable Compliance Features**
- Add `/users/{id}/delete` endpoint for GDPR compliance.
- Log data access requests for auditing.

---

## Common Mistakes to Avoid

1. **Not Encrypting in Transit**: Always use HTTPS. Never expose API keys or tokens in URLs.
2. **Over-Encrypting**: Don’t encrypt everything—balance security with usability.
3. **Ignoring Query Injection**: Use parameterized queries (never string interpolation).
4. **Hardcoding Secrets**: Never commit API keys or database passwords to Git.
5. **Assuming Users Understand Privacy**: Document your data usage clearly (e.g., terms of service).

---

## Key Takeaways
✅ **Data Minimization**: Collect only what’s necessary.
✅ **Field-Level Control**: Let clients specify returned fields.
✅ **Encryption**: Protect data at rest and in transit.
✅ **RBAC**: Enforce least privilege in APIs.
✅ **Audit & Compliance**: Log access and implement GDPR-like features.
✅ **Anonymization**: Mask PII when possible.

---

## Conclusion

Privacy isn’t an afterthought—it’s a **core design principle**. By adopting Privacy Approaches, you protect users, comply with regulations, and build trust. Start small: Audit your data, encrypt sensitive fields, and add RBAC to your APIs. Over time, iteratively improve your system’s privacy posture.

**Next Steps**:
1. Audit your current database schema for PII.
2. Implement field selection in your APIs.
3. Encrypt sensitive fields at rest and in transit.

Remember: **Privacy is a journey, not a destination.**

---
### Further Reading
- [OWASP Privacy Enhancing Technologies Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Privacy_Enhancing_Technologies_Cheat_Sheet.html)
- [PostgreSQL Row-Level Security Docs](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [GDPR Compliance Guide for Developers](https://gdpr.eu/)

---
Would you like a deeper dive into any specific component (e.g., tokenization or RBAC middleware)? Let me know in the comments!
```

This blog post is **practical**, **code-heavy**, and **honest about tradeoffs**, making it ideal for beginner backend engineers. It balances theory with actionable steps and avoids hype.