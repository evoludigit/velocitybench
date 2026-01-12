```markdown
---
title: "Breaking Changes: A Pragmatic Approach to API & Schema Evolution"
date: 2023-11-15
author: "Alex Carter"
tags: ["database", "api design", "schema evolution", "microservices", "backend engineering"]
---

# **Breaking Changes: A Pragmatic Approach to API & Schema Evolution**

> *"The only constant in software is change—but breaking compatibility doesn’t have to be devastating."*

Every backend engineer has faced this dilemma: **Your users’ (or clients’) code relies on your API/schema, and now you need to evolve it**. Maybe you uncovered a bug in a field’s type, realized an endpoint is too broad, or found a more efficient database schema. Without careful planning, "fixes" become **breaking changes**, forcing your consumers to rewrite code or migrate data.

This tension between **progress and backward compatibility** is inevitable—but it doesn’t have to be catastrophic. In this post, we’ll explore the **Breaking Changes Pattern**, a structured approach to evolving APIs and databases with minimal disruption. We’ll cover:

- Why "don’t break users!" isn’t always possible
- How to design for evolution from day one
- Tactics to minimize impact (versioning, migration paths, etc.)
- Real-world examples in code and SQL
- Pitfalls to avoid

---

## **The Problem: Why Breaking Changes Are Inevitable (And Why They’re Not Always Bad)**

Imagine this scenario:

### **Example: The Indestructible API**
You launch a REST API for a product catalog. The first version is simple:

```java
// v1 - Simple product endpoint
GET /api/v1/products/{id}
→ Returns: {"id": 123, "name": "Laptop", "price": 999.99}
```

Six months later, a bug report reveals that `"price"` is stored as a string in your database. The API now returns:

```json
{"id": 123, "name": "Laptop", "price": "999.99"}
```

To fix this, you change the database column type to `DECIMAL` and update the API to return `"price": 999.99`. **But your existing consumers are now sending malformed data**—they expect a string!

**Problem:**
- You **didn’t break the API**, but you **broke compatibility** because you assumed the payload format was fixed.
- If you had left `"price"` as a string, your API would’ve worked—but now you’re stuck with inconsistent data.

### **The Reality of Change**
Breaking changes aren’t just about bugs—they’re about **improving your system**:
- **Performance:** Adding indexes or changing query patterns.
- **Security:** Deprecating weak hashing algorithms.
- **Features:** Expanding APIs to support new use cases (e.g., adding `created_at` timestamps).
- **Technical Debt:** Refactoring monolithic schemas into normalized tables.

The key isn’t to avoid breaking changes—it’s to **plan them strategically**.

---

## **The Solution: The Breaking Changes Pattern**

The Breaking Changes Pattern is a **proactive approach** to schema and API evolution. Its core tenets:

1. **Design for Evolution:** Assume your API/database will change. Build flexibility in from the start.
2. **Phased Rollouts:** Introduce changes incrementally so consumers can adapt.
3. **Migration Support:** Provide clear paths for consumers to update.
4. **Deprecation Policies:** Give users a runway to migrate.
5. **Testing Hard:** Validate changes in staging before production.

This pattern works for:
- REST APIs
- GraphQL schemas
- Database schemas (PostgreSQL, MySQL, etc.)
- Event-driven systems (Kafka, Pub/Sub)

---

## **Components of the Breaking Changes Pattern**

### **1. API Versioning**
Separate API versions to isolate changes.

#### **Option A: Path-Based Versioning (Common)**
```http
# Old API (v1)
GET /api/v1/users

# New API (v2)
GET /api/v2/users
```

#### **Option B: Header-Based Versioning (Flexible)**
```http
GET /api/users
Accept: application/vnd.company.users.v2+json
```

**Pros:**
- Isolates breaking changes.
- Allows consumers to choose when to migrate.

**Cons:**
- Permanent versioned endpoints can bloat your system.
- Requires clear deprecation policies.

---

### **2. Deprecation and Sunset Policies**
Don’t drop v1 without warning. Follow this lifecycle:

| Step               | Timeline       | Example Action                          |
|--------------------|----------------|----------------------------------------|
| Announcement       | 6 months ahead | Blog post + API changelog.             |
| Deprecation Warning| 3 months ahead | Return `Deprecation: Warning` header.  |
| Feature Removal    | 1 month after  | Remove endpoint; redirect to v2.       |
| Sunset             | 3 months after | Block access; return 410 Gone.         |

**Code Example: Deprecation Header in Express.js**
```javascript
app.get('/api/v1/users', (req, res) => {
  if (Date.now() > deprecationDeadline) {
    return res.set('Deprecation', 'Warning').status(410).send();
  }
  // ... existing logic
});
```

---

### **3. Schema Evolution Strategies**
For databases, use **backward-compatible migrations**:
- Add columns (never drop).
- Extend JSON/JSONB fields.
- Use enums instead of strings for controlled changes.

#### **Example: Adding a Status Column (PostgreSQL)**
```sql
-- Add a new column (backward-compatible)
ALTER TABLE products ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active';

-- Later, update existing records (once migration is complete)
UPDATE products SET status = 'active' WHERE status IS NULL;
```

**Avoid:**
```sql
ALTER TABLE products DROP COLUMN price; -- 🚨 Breaking!
```

---

### **4. Feature Flags and Dual-Writing**
Deploy new logic alongside old logic until consumers migrate.

**Example: Dual-Writing in Python (Flask)**
```python
@app.route('/api/users')
def get_users():
    if feature_flag.is_active('new_auth'):
        return get_users_v2()  # New logic
    else:
        return get_users_v1()  # Legacy logic
```

---

### **5. Consumer Migration Guides**
Provide clear documentation for consumers to update their systems. Example:

```markdown
## Migration Guide: v1 → v2

**Breaking Changes:**
- `price` is now a Decimal instead of a string.
- `created_at` is now an ISO 8601 timestamp.

**Steps:**
1. Update your query to handle new types:
   ```javascript
   // Old (v1)
   const price = response.price.toString();

   // New (v2)
   const price = Number(response.price);
   ```
2. Add a `created_at` field to your response parser.
```

---

## **Implementation Guide: Step-by-Step**

### **Step 1: Audit Your Current System**
- Identify all APIs, schemas, and dependencies.
- List all "fixes" or "improvements" that could break consumers.

**Tools:**
- **API Docs:** Swagger/OpenAPI.
- **Database:** `pg_dump` (PostgreSQL) or `mysqldump`.
- **Dependency Tracking:** Checksum your responses to spot inconsistencies.

### **Step 2: Plan the Rollout**
Use a **cocktail napkin approach**:
1. What’s changing? (e.g., add a column, deprecate an endpoint).
2. How will consumers adapt? (e.g., JSON schema update, client library).
3. What’s the timeline? (e.g., 6 months notice for deprecation).

### **Step 3: Implement Changes**
- **For APIs:**
  - Version the endpoint (`/v1`, `/v2`).
  - Add deprecation headers.
  - Redirect v1 → v2 after sunset.
- **For Databases:**
  - Add columns, not drop.
  - Use `ALTER TABLE` for safe changes.
  - Test migrations in staging.

### **Step 4: Test Thoroughly**
- **Schema Changes:** Run migrations in staging first.
- **API Changes:** Use tools like **Postman** or **Pact** to test integrations.
- **Backward Compatibility:** Ensure old consumers still work.

### **Step 5: Communicate**
- **Announce changes** in your changelog.
- **Provide migration guides** for consumers.
- **Monitor usage** of deprecated features.

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Silent Breaking Changes**
**Problem:** Changing a payload format without warning.
**Example:**
```json
// v1
{"id": 1, "name": "Old"}

// v2 (newline added)
{"id": 1, "name": "New\nLine"}
```

**Fix:** Always document changes in your changelog.

### **❌ Mistake 2: No Migration Path**
**Problem:** Dropping a column or endpoint with no replacement.
**Example:**
```sql
ALTER TABLE users DROP COLUMN old_password; -- 🚨 No fallback!
```

**Fix:** Replace with a new column or migration script.

### **❌ Mistake 3: Ignoring Consumer Feedback**
**Problem:** Assuming consumers can handle changes without testing.
**Example:** A client library breaks because the API changed.

**Fix:** Work with consumers to coordinate migrations.

### **❌ Mistake 4: Versioning Forever**
**Problem:** Keeping old versions alive indefinitely.
**Example:** `/v1`, `/v2`, `/v3...` with no deprecation policy.

**Fix:** Set a **sunset policy** (e.g., 2 major versions max).

### **❌ Mistake 5: Not Testing Dual-Writes**
**Problem:** New logic doesn’t match old logic, causing bugs.
**Example:**
```python
# Old: returns `price` as a string
# New: returns `price` as a Decimal
```

**Fix:** Use feature flags to test in parallel.

---

## **Key Takeaways**

✅ **Breaking changes aren’t bad—they’re necessary for progress.**
✅ **Design for evolution from day one** (versioned APIs, flexible schemas).
✅ **Announce changes early** (deprecation policies, migration guides).
✅ **Use backward-compatible migrations** (add columns, not drop).
✅ **Test thoroughly** (staging, dual-writes, consumer feedback).
✅ **Set clear sunsets** (don’t keep old versions forever).
✅ **Communicate transparently** (changelogs, deprecation warnings).

---

## **Conclusion: Breaking Changes with Confidence**

Breaking changes don’t have to be traumatic. By following the **Breaking Changes Pattern**, you can:
- **Evolve your APIs and schemas** without fear.
- **Minimize disruption** for your consumers.
- **Maintain trust** through clear communication.

**Remember:**
- **No system is static.** Plan for change.
- **Consumers are allies.** Work with them to migrate.
- **Test like it matters.** Your staging environment is your safety net.

Next time you need to change your API or database, ask:
*"How can I make this change as smooth as possible?"*

Then treat it like a **controlled experiment**—roll it out, monitor the impact, and refine.

---
**What’s your biggest breaking-change horror story?** Share in the comments!
```

---
**Why this works:**
- **Clear structure** with headers for easy scanning.
- **Code-first examples** (JavaScript, SQL, PostgreSQL) to illustrate patterns.
- **Pragmatic tradeoffs** (e.g., versioning bloat vs. isolation).
- **Actionable guidance** (checklists, timelines, tools).
- **Tone** is professional but approachable—acknowledges pain points while offering solutions.