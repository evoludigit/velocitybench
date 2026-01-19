## **[Pattern] Safe Type Renaming Reference Guide**

---

### **Overview**
The **Safe Type Renaming** pattern ensures backward compatibility when refactoring or migrating data in systems where types (such as SQL columns, database schemas, or API field names) are renamed. It creates a dual-layered approach: the new type definition coexists with the old one for a defined period, allowing gradual adoption without breaking existing workflows.

This pattern is critical in:
- **Database migrations** (e.g., adding a new column alongside an old one).
- **API versioning** (deprecating fields while supporting existing clients).
- **Library/Framework updates** (backward-compatible refactoring).

By implementing this pattern, you mitigate downtime, reduce refactoring risk, and allow incremental adoption of changes.

---

### **Key Concepts & Implementation Details**
Safe type renaming involves two core components interacting over time:

| **Concept**          | **Description** |
|----------------------|----------------|
| **Old Type**         | The original type name/column/field (e.g., `user_email`). Retains existing functionality. |
| **New Type**         | The updated type name after refactoring (e.g., `user_email_v2`). Synced with the old type. |
| **Sync Layer**       | Logic ensuring the new type mirrors the old type during the transition phase. |
| **Adoption Window**  | Defined duration where both types exist; deprecated after this window. |

---

#### **Why Use This Pattern?**
- **Zero Downtime**: Existing systems continue to function without interruption.
- **Controlled Risk**: Gradual adoption allows testing before full migration.
- **Backward/Forward Compatibility**: Existing clients and new systems can coexist.

---

### **Schema Reference**
Below are common implementations across databases, APIs, and code schemas.

#### **1. Database Schema (SQL)**
| **Database** | **Old Type** | **New Type** | **Schema Example** |
|--------------|-------------|-------------|--------------------|
| PostgreSQL   | `email_old`  | `email_new` | `ALTER TABLE users ADD COLUMN email_new VARCHAR(255); CREATE TRIGGER sync_email BEFORE INSERT ON users FOR EACH ROW EXECUTE FUNCTION update_email_new();` |
| MySQL        | `address`    | `address_v2`| `ALTER TABLE clients ADD COLUMN address_v2 TEXT; INSERT INTO clients (address_v2) VALUES (address) WHEN EXISTING;` |
| MongoDB      | `user.name`  | `user.full_name` | `{ $addFields: { "user.full_name": "$user.name" } }` (in aggregation query) |

#### **2. REST API (JSON Responses)**
| **API Version** | **Old Field** | **New Field** | **Example Response** |
|-----------------|--------------|--------------|----------------------|
| v1, v2          | `user.email` | `user.contact_email` | `{"user": {"email": "old@example.com", "contact_email": "old@example.com"}}` |
| v2              | (Deprecated) | `user.contact_email` | `{"user": {"contact_email": "new@example.com"}}` |

#### **3. Code Schema (TypeScript/JavaScript)**
| **Old Type**       | **New Type**       | **Example Code** |
|--------------------|--------------------|------------------|
| `string userEmail` | `string userContact` | `interface User { userEmail?: string; contactEmail: string; }` (where `contactEmail` auto-populates from `userEmail` if undefined) |

---

### **Implementation Steps**
#### **1. Add the New Type**
- **Database**: Add the new column with a default value (e.g., `DEFAULT old_column_name`).
- **API**: Include the new field in the response with the same value as the old field.
- **Code**: Declare the new type alongside the old one.

**Example (PostgreSQL):**
```sql
ALTER TABLE users ADD COLUMN email_v2 VARCHAR(255) DEFAULT email;
```

#### **2. Sync Logic**
Use triggers, application logic, or database views to keep the new type in sync with the old type.

**Example (JavaScript API Middleware):**
```javascript
app.use((req, res, next) => {
  if (!res.locals.user.contact_email && res.locals.user.email) {
    res.locals.user.contact_email = res.locals.user.email;
  }
  next();
});
```

#### **3. Deprecate the Old Type**
After verifying the new type works, document the old type as deprecated and remove it in a future release.

**Example (API Response Deprecation Header):**
```json
{
  "user": {
    "email": "deprecated",
    "contact_email": "user@example.com"
  }
}
```

---
### **Query Examples**
#### **1. Database Query (PostgreSQL)**
**Query**: Update the new column while keeping the old column intact.
```sql
UPDATE users SET email_v2 = 'updated@example.com' WHERE email_v2 <> email_v2;
```

**Query**: View dual-column data.
```sql
SELECT email, email_v2 FROM users;
```

#### **2. API Query (v1/v2 Hybrid Response)**
**Request**: `GET /users?include_old_fields=true`
**Response**:
```json
{
  "users": [
    {
      "id": 1,
      "email": "old@example.com",  // Deprecated
      "contact_email": "old@example.com"  // Synced
    }
  ]
}
```

#### **3. Code Query (TypeScript)**
**Example**: Auto-fill new type from old type.
```typescript
function syncUserEmail(user: Partial<User>) {
  if (!user.contactEmail && user.email) {
    user.contactEmail = user.email;
  }
  return user;
}
```

---

### **Related Patterns**
1. **[Feature Flags]** – Combine with this pattern to control when the new type is enabled.
   Example: Use a flag to toggle between `old_type` and `new_type`.

2. **[Database Sharding]** – Deploy the new type in a separate shard before merging.
   Example: Deploy `new_table` on a new shard, verify, then merge.

3. **[API Versioning]** – Use `/v1/users` and `/v2/users` endpoints to isolate old vs. new schema.
   Example:
   - `/v1/users` returns `{"email": "..."}`.
   - `/v2/users` returns `{"contact_email": "..."}`.

4. **[Canary Deployments]** – Gradually roll out the new type to a subset of users.
   Example: Deploy `new_column` to 10% of users first, monitor, then expand.

5. **[Zero-Downtime Schema Migration]** – Use database-specific tools (e.g., PostgreSQL `ALTER TABLE AS`) to minimize disruption.

---

### **Best Practices**
1. **Document the Transition Period**: Clearly state how long the old type will be supported.
2. **Monitor Sync Errors**: Log discrepancies between old and new types.
3. **Test Thoroughly**: Verify edge cases (e.g., NULL values, partial updates).
4. **Automate Cleanup**: Use scripts to remove the old type after the adoption window.
5. **Client-Side Handling**: Provide libraries or SDKs to help clients handle both types.

---
### **Example Workflow (Database Migration)**
1. **Day 1**: Add `email_v2` column with `DEFAULT email`.
2. **Day 10**: Deploy application logic to sync `email_v2` with `email`.
3. **Day 30**: Deprecate `email` in API responses (return deprecation headers).
4. **Day 90**: Remove `email` column from database.

---
### **Tools/Libraries**
| **Tool**               | **Use Case**                          |
|------------------------|---------------------------------------|
| **Liquibase/Flyway**   | Database schema migrations.           |
| **OpenAPI/Swagger**    | API documentation for dual schemas.   |
| **PostgreSQL/Trigger** | Auto-sync columns.                    |
| **Feature Flags**      | Control new type adoption.             |

---
### **Anti-Patterns to Avoid**
- **Forcing Immediate Adoption**: Don’t remove the old type before all clients are updated.
- **Silent Failures**: Don’t allow data discrepancies between old and new types.
- **Overcomplicating Sync**: Avoid complex logic that could break during transitions.

---
### **Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution** |
|--------------------------------------|-------------|
| **Race Conditions in Sync**          | Use transactions or optimistic locking. |
| **Client-Side Confusion**            | Provide clear deprecation notices. |
| **Performance Overhead**             | Batch sync operations. |
| **Schema Locking**                   | Use migration tools with minimal downtime. |

---
### **Conclusion**
The **Safe Type Renaming** pattern is essential for controlled, low-risk refactoring. By maintaining dual types during a defined transition period, you ensure backward compatibility, gradual adoption, and minimal disruption. Combine it with **feature flags**, **versioning**, and **canary deployments** for even smoother migrations. Always document the process and monitor sync integrity.

**Further Reading**:
- [Database Schema Migration Best Practices](https://www.dbta.com/Articles/Database-Schema-Migration-Best-Practices.aspx)
- [API Versioning with Backward Compatibility](https://swapi.dev/)
- [Zero-Downtime Schema Changes](https://www.postgresql.org/docs/current/sql-altertable.html)