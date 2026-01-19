# **Debugging "WHERE Type Auto-Generation" Pattern: A Troubleshooting Guide**

## **1. Introduction**
The **"WHERE Type Auto-Generation"** pattern aims to abstract database-specific WHERE clauses by dynamically inferring and translating filter conditions into database-compatible syntax. While this reduces boilerplate code, it introduces complexity in error handling, type validation, and database compatibility.

This guide provides a structured approach to diagnosing and resolving issues when this pattern fails.

---

## **2. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

| **Symptom** | **Description** | **Possible Cause** |
|-------------|----------------|-------------------|
| `UnsupportedFilterError` | Filters like `JSON_CONTAINS` fail on SQLite | Database does not support the filter type |
| Inconsistent Query Output | Same filters return different results across PostgreSQL/MySQL | Dynamic WHERE type generation misaligns with DB capabilities |
| High Maintenance Overhead | Frequent manual fixes needed for new DB features | No standardized filter mapping |
| Query Plan Issues | Slow performance despite correct WHERE clauses | Improper translation of complex filters (e.g., `IS NULL` vs. `NULL` checks) |
| Type Errors | `WHERE` conditions cause schema validation failures | Inconsistent type inference between DB and ORM |

---

## **3. Common Issues and Fixes**

### **3.1 Issue 1: Unsupported Filter Attempted on SQLite**
**Symptom:**
`UnsupportedFilterError: JSON_CONTAINS not supported in SQLite`

**Root Cause:**
SQLite lacks support for `JSON_CONTAINS` or other advanced functions (e.g., `ARRAY_CONTAINS`).

**Solution:**
- **Option A:** Use a database-agnostic fallback:
  ```typescript
  const where = {
    function: "json_contains",
    args: ["{field}", "{value}"],
    fallback: (field, value) => `lower(${field}) LIKE '%${value.toLowerCase()}%'`
  };
  ```
- **Option B:** Conditionally apply filters per DB:
  ```typescript
  const filter = { type: "json_contains", value: "test" };
  const whereClause = db === "sqlite"
    ? `lower(column) LIKE '%${filter.value.toLowerCase()}%'`
    : `JSON_CONTAINS(column, '{"key": "${filter.value}"}')`;
  ```

---

### **3.2 Issue 2: Different WHERE Types Across Databases**
**Symptom:**
Same query works in PostgreSQL but fails in MySQL due to `IS NULL` vs. `NULL` handling.

**Root Cause:**
Different databases interpret `NULL` checks differently (e.g., MySQL requires `IS NULL` explicitly, while PostgreSQL tolerates just `NULL`).

**Solution:**
- **Normalize NULL handling:**
  ```typescript
  const getNullCheck = (field) => {
    return {
      postgres: `${field} IS NULL`,
      mysql: `${field} IS NULL`, // Same in MySQL
      sqlite: `${field} IS NULL` // Also same in SQLite
    }[db];
  };
  ```

- **Use a filter translator:**
  ```typescript
  const translateFilter = (filter, dbType) => {
    if (filter.type === "null") {
      return { type: "is_null", field: filter.field };
    }
    return filter; // Default case
  };
  ```

---

### **3.3 Issue 3: Maintenance Burden from Manual WHERE Type Creation**
**Symptom:**
New database features (e.g., PostgreSQL’s `GIN` index support) require manual updates to WHERE logic.

**Solution:**
- **Adopt a registry pattern:**
  ```typescript
  const filterRegistry = {
    json_contains: (db) => db === "postgres" ? "JSON_CONTAINS" : "LOWER(...LIKE...)",
    array_contains: (db) => db === "postgres" ? "ARRAY_CONTAINS" : "FIND_IN_SET"
  };

  const getWhereType = (filter, db) => {
    const key = `$${filter.type}`;
    return filterRegistry[key]?.(db) || defaultHandler(filter);
  };
  ```

---

### **3.4 Issue 4: Query Plan Performance Degradation**
**Symptom:**
Queries slow down despite correct `WHERE` clause generation.

**Root Cause:**
Dynamic translation may introduce inefficient conditions (e.g., `LIKE '%text%'` instead of `LOWER(...) LIKE ...`).

**Solution:**
- **Validate against known-good patterns:**
  ```typescript
  const optimizeFilter = (filter) => {
    if (filter.type === "contains" && filter.field.includes("%")) {
      return { ...filter, type: "optimized_contains" };
    }
    return filter;
  };
  ```

---

## **4. Debugging Tools and Techniques**

### **4.1 Logging and Instrumentation**
- **Log raw filter->WHERE translations:**
  ```typescript
  console.log("Input:", filter);
  console.log("Translated:", generateWhereClause(filter, db));
  ```
- **Use a debugging middleware:**
  ```typescript
  const debugWhere = (input, output) => {
    console.trace("WHERE generation:");
    console.log("Input:", input);
    console.log("Output:", output);
  };
  ```

### **4.2 Database-Specific Query Inspection**
- **Check SQL generation:**
  ```typescript
  const debugQuery = (query) => {
    console.log(`Executing: ${query.sql}`);
    console.log("Args:", query.args);
  };
  ```
- **Use `EXPLAIN` for performance analysis:**
  ```typescript
  const explain = async (query) => {
    const result = await db.query("EXPLAIN " + query.sql);
    console.log("Query Plan:", result.rows);
  };
  ```

### **4.3 Unit Testing Filter Translations**
- **Test edge cases:**
  ```typescript
  test("SQLite JSON_CONTAINS fallback", () => {
    expect(generateWhereClause({ type: "json_contains" }, "sqlite"))
      .toContain("LOWER(...LIKE...)");
  });
  ```

---

## **5. Prevention Strategies**

### **5.1 Standardize Filter Definitions**
- **Use a schema for filters:**
  ```typescript
  interface Filter {
    type: "exact" | "contains" | "range" | "custom";
    field: string;
    value?: any;
    dbSpecific?: Record<string, any>;
  }
  ```

### **5.2 Database Feature Detection**
- **Runtime DB capability checks:**
  ```typescript
  const supportsJson = async (db) => {
    const test = await db.query("SELECT JSON_CONTAINS('{}', '{}')");
    return test.rows.length > 0;
  };
  ```

### **5.3 Incremental Migration**
- **Deprecate unsupported filters gracefully:**
  ```typescript
  if (!supportsJson) {
    console.warn(`JSON_CONTAINS deprecated; using fallback`);
  }
  ```

---

## **6. Conclusion**
The **"WHERE Type Auto-Generation"** pattern is powerful but prone to edge cases. By systematically checking symptoms, validating translations, and instrumenting debugging, you can resolve issues efficiently. Prevention strategies like standardization and runtime feature detection ensure long-term stability.

**Next Steps:**
✅ Audit existing WHERE clauses for database-specific quirks.
✅ Implement logging for all filter translations.
✅ Test against multiple DB backends in CI.

---
**Final Note:** If the pattern proves too complex, consider a hybrid approach—either enforce stricter type safety or split logic into database-specific implementations.