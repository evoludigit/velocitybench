```markdown
# Debugging Authorization Issues: A Backend Engineer’s Playbook

*How to systematically resolve authorization headaches in your APIs*

---

## Introduction

Authorization failures can be one of the most infuriating bugs in a backend system. A user with valid credentials suddenly can’t access what they’re supposed to—yet their session looks fine. The error might surface as a `403 Forbidden`, an empty list of permissions, or a cryptic "policy violation." What makes it worse? These issues are often intermittent, making them tricky to reproduce and fix.

As intermediate backend engineers, you’ve likely spent countless hours staring at logs, toggling between databases and middleware, and questioning whether you misconfigured every library in sight. The situation feels worse when you’re unsure where to start. This post cuts through the noise: we’ll explore a **systematic troubleshooting approach** for authorization problems, using concrete examples and real-world tradeoffs.

By the end, you’ll understand how to:
- Distinguish between auth vs. authorization issues
- Navigate complex permission chains (RBAC, ABAC, claim-based)
- Debug policy decisions in production
- Integrate observability into your auth flow

---

## The Problem: When Permissions Break

Authorization failures don’t just happen at random—they follow patterns. Here’s what often goes wrong, and why it’s hard to diagnose:

### **1. The Silent Permission Deny**
A user logs in successfully, but their API requests return empty collections or `"You don’t have access."` errors. Worse, the behavior might change over time:
- *"Why did Sarah’s project list disappear on Tuesday?"*
- *"We rolled out a new role, but users can’t do anything related to it!"*

**Root causes:**
- Permission updates weren’t propagated to the database (e.g., SQL transactions didn’t commit).
- A downstream service’s role assignment changed.
- The user’s session includes stale role claims.

### **2. The Random 403**
A user can access some endpoints but not others, even with identical permissions:
```http
GET /projects/my-active-project  # Returns 200 OK
GET /projects/all               # Returns 403 Forbidden
```
**Root causes:**
- Context matters! Permissions might depend on:
  - Request time (e.g., **time-based access control**)
  - Resource metadata (e.g., **custom policies**)
  - External system states (e.g., **audit logs**)
- A misconfigured middleware redirects traffic through a different auth path.

### **3. The Role Assignment Mismatch**
A developer creates a new role, assigns it to a user, but nothing works:
```javascript
// User has correct role in DB
SELECT * FROM users WHERE username = 'Bob' → {"roles": ["pm-user"]}

// But API returns 403
{
  "code": "P-001",
  "message": "Missing required permission: project:read"
}
```
**Root causes:**
- Permission boundaries were redefined without updating the codebase.
- The role’s permission list is missing a critical grant.

---

## The Solution: A Structured Approach

When debugging authorization, **focus on layers**, not just code. Break the problem into these components:

1. **Authentication Layer**: Ensure the user is who they claim to be.
2. **Claims Extraction**: Verify roles/permissions are included in the token.
3. **Policy Evaluation**: Test the logic that enforces access rules.
4. **Resource Context**: Validate resource-specific rules (e.g., ownership, quotas).

We’ll use a **multi-service e-commerce API** example to illustrate each stage.

---

## Components & Debugging Tools

### 1. Authentication Verification
**Problem**: *"User is logged in, but can’t access anything."*
**Tool**: Check the JWT claims.

#### Example: Validating a JWT
```javascript
// Express middleware to verify and decode token
const jwt = require('jsonwebtoken');
const verifyToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    // Log claims to verify they’re intact
    console.log('Decoded payload:', payload);
    req.user = payload;
    next();
  } catch (err) {
    next(new Error('Invalid token')); // 401
  }
};
```
**Debugging query**: Look for:
- `exp` (expiration) or `iat` (issued-at) issues.
- Claims like `role`, `permissions`, or `org_id`.

---

### 2. Permission Propagation
**Problem**: *"Roles exist in the DB but aren’t applied in the API."*
**Tool**: Audit the token generation flow.

#### Example: Building a JWT with Permissions
```javascript
// Backend: Generate token with role permissions
const generateToken = async (userId) => {
  const user = await db.user.findById(userId);
  const role = await db.role.findByName(user.role);
  const permissions = role.permissions.map(p => p.name);

  return jwt.sign(
    { id: user.id, role: user.role, permissions },
    process.env.JWT_SECRET,
    { expiresIn: '1h' }
  );
};
```
**Debugging tip**: Compare the role assigned in the DB to the token claims:
```sql
SELECT u.role, t.payload
FROM users u
JOIN tokens t ON u.id = t.user_id
WHERE t.token = 'eyJhbGciO...';
```

---

### 3. Policy Evaluation
**Problem**: *"Users have permissions, but policies block access."*
**Tool**: Replay policy logic outside the API.

#### Example: Custom Policy for Delete
```javascript
// Policy middleware
const hasDeletePermission = (resourceId, userRole) => {
  // Example: Only 'admin' or 'project_owner' can delete
  return ['admin', 'project_owner'].includes(userRole);
};

const deleteProject = async (req, res) => {
  const { projectId } = req.params;
  const { role } = req.user;

  if (!hasDeletePermission(projectId, role)) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  // Proceed with deletion
};
```
**Debugging approach**:
1. Print the `resourceId` and `userRole` before evaluation.
2. Test the policy with hardcoded values:
   ```javascript
   console.log(hasDeletePermission('123', 'project_owner')); // true/false
   ```

---

### 4. Context-Specific Rules
**Problem**: *"Users have permissions, but resources are locked."*
**Tool**: Check resource metadata and business rules.

#### Example: Ownership-Based Access
```javascript
const canEditProject = async (projectId, userId) => {
  const project = await db.project.findById(projectId);
  return project.ownerId === userId || project.admins.includes(userId);
};

const editProject = async (req, res) => {
  const { projectId } = req.params;
  const { userId } = req.user;

  if (!(await canEditProject(projectId, userId))) {
    return res.status(403).json({ error: 'Not authorized' });
  }
  // Update project
};
```
**Debugging query**: Verify ownership:
```sql
SELECT ownerId FROM projects WHERE id = '123';
```

---

## Implementation Guide: Step-by-Step Debugging

1. **Reproduce the Issue**
   - Use Postman or a script to trigger the failure.
   - Capture logs with timestamps.

2. **Check the Token**
   - Decode the JWT to verify claims.
   - Compare with the database (e.g., `role` or `permissions` field).

3. **Test Permission Logic**
   - Isolate the policy: comment out the 403 logic and test direct calls.
   - Example:
     ```javascript
     // Standalone test
     console.log(hasPermission('project:delete', ['admin'])); // true
     ```

4. **Review Context**
   - For resource-specific rules, inspect the DB query:
     ```javascript
     console.log(await db.project.findById(projectId)); // Verify metadata
     ```

5. **Check Dependencies**
   - If permissions come from an external service (e.g., **OAuth provider**), verify:
     - Network latency.
     - Rate limits.

---

## Common Mistakes to Avoid

### ❌ Assumption: "Permissions Are Static"
**Problem**: Permissions are hardcoded or outdated.
**Fix**: Automate role-permission mapping and audit via CI.

### ❌ Overusing Wildcards
**Problem**: SQL queries like `SELECT * FROM resources` expose too much.
**Fix**: Use **row-level security** (PostgreSQL RLS) or query filters.

### ❌ Silent Failures
**Problem**: Code skips validation and assumes permissions are valid.
**Fix**: Always log or trace permission decisions.

### ❌ Ignoring Time Zones
**Problem**: Time-based rules (e.g., "only allow access between 9 AM–5 PM") fail due to timezone mismatches.
**Fix**: Use **UTC** or explicitly document DST handling.

### ❌ Debugging Without Metrics
**Problem**: You can’t track how many requests fail for a given permission.
**Fix**: Add an **authorization metrics dashboard** (e.g., Prometheus + Grafana).

---

## Key Takeaways

- **Authorization ≠ Authentication**: Verify the token is valid *and* claims are correct.
- **Context Matters**: Check resource ownership, time, and service states.
- **Test Decisions**: Use stand-alone tests to validate policies.
- **Audit Permissions**: Log or trace permission denials for root cause analysis.
- **Document Boundaries**: Define clearly where permissions are enforced (e.g., API, DB).

---

## Conclusion

Authorization issues are rarely simple—**they’re a chain of decisions** linking authentication, tokens, policies, and resources. The key to resolving them is **systematic debugging**: verify each layer, from JWT claims to backend policies, and validate assumptions with production-ready tools.

Remember:
- **Observability is critical**: Log or monitor permission evaluations.
- **Automate early**: Use CI to test role changes before deployment.
- **Design for debuggability**: Write policies with clear inputs/outputs.

By following this approach, you’ll leave behind the guesswork and turn "why is this 403ing?" into a **structured, repeatable process**. Happy debugging!

---
## Further Reading
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [OpenTelemetry for API Observability](https://opentelemetry.io/)

---
*Have you hit an authorization wall? Share your toughest debug case in the comments!*
```