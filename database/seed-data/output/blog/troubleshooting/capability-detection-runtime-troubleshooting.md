# **Debugging Capability Detection Runtime (CDR): A Troubleshooting Guide**

## **Introduction**
The **Capability Detection Runtime (CDR)** pattern dynamically probes database features at runtime, adjusting behavior (e.g., query syntax, extension usage) based on supported capabilities. While this enables backward compatibility and graceful degradation, misconfigurations and edge cases can lead to failures.

This guide focuses on **quick resolution** of runtime feature detection issues, covering symptoms, root causes, debugging techniques, and prevention strategies.

---

## **1. Symptom Checklist**
Check these signs when diagnosing CDR-related issues:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| `UnsupportedOperatorError`           | Queries fail with unsupported operators (e.g., `JOIN` in older DB versions)   |
| `ExtensionNotFoundError`             | Missing database extensions cause runtime crashes or compilation failures       |
| `IncompatibleSyntaxError`            | SQL queries use unsupported syntax (e.g., `WITH RECURSIVE` in MySQL 5.7)        |
| `Performance Degradation`            | Runtime probing adds overhead, slowing down queries                              |
| `Graceful Degradation Fails`         | Fallback logic (e.g., legacy syntax) doesn’t execute as expected              |
| `Log Spam**                          | Excessive probing logs cluttering system logs                                   |

---

## **2. Common Issues & Fixes**

### **Issue 1: Queries Fail on Older Database Versions**
**Symptom:**
`UnsupportedOperatorError: Database does not support JOIN operations. Fallback to legacy syntax.`

**Root Cause:**
- Newer queries use unsupported operators (e.g., `LATERAL JOIN`, `WINDOW FUNCTIONS`).
- Probing logic fails to detect compatibility.

**Fix:**
- **Adjust the probing logic** to cache detected capabilities.
- **Fallback to legacy queries** gracefully.

**Example (Pseudocode):**
```python
def build_query(db_version: str) -> str:
    if db_version < "10.0":
        return "SELECT * FROM old_table WHERE id = ?"  # Legacy syntax
    else:
        return "SELECT * FROM new_table WHERE id = ? WITH (LATERAL JOIN)"  # New syntax
```

**Verification:**
- Test with a **downgraded DB** (e.g., Docker MySQL 5.7) to confirm fallback works.

---

### **Issue 2: Missing Extensions Cause Compilation Errors**
**Symptom:**
`ExtensionNotFoundError: UUID extension unavailable. Fallback to string conversion.`

**Root Cause:**
- The application assumes `uuid-ossp` is available, but it’s not installed.
- Runtime probing fails silently or crashes.

**Fix:**
- **Check for extension availability** before use.
- **Provide a fallback** (e.g., use `CAST` instead of `uuid_generate_v4()`).

**Example (Pseudocode):**
```python
def generate_uuid(db_version: str) -> str:
    if check_extension_available("uuid-ossp"):
        return "uuid_generate_v4()"
    else:
        return "CAST(RANDOMUUID() AS VARCHAR(36))"  # Fallback (PostgreSQL 11+)
```

**Verification:**
- Run `SHOW PLUGINS;` (MySQL) or `\dx` (PostgreSQL) to confirm extension status.

---

### **Issue 3: Dynamic Operator Detection Fails**
**Symptom:**
`OperatorDetectionError: Could not determine if CTAS (CREATE TABLE AS) is supported.`

**Root Cause:**
- Probing query returns ambiguous results.
- Edge cases (e.g., read-only DBs) prevent detection.

**Fix:**
- **Use a known-safe query** for probing.
- **Cache results** to avoid repeated checks.

**Example (Pseudocode):**
```python
def supports_ctas(db_version: str) -> bool:
    try:
        supported = execute_probe_query(
            "SELECT 1 FROM (SELECT * FROM (VALUES (1)) AS t) AS temp_table"  # Simple test
        )
        return supported
    except DatabaseError:
        return False
```

**Verification:**
- Test with a **read-only DB** to ensure no side effects.

---

### **Issue 4: Graceful Degradation Fails**
**Symptom:**
`DegradationError: Legacy query syntax not executed.`

**Root Cause:**
- Fallback logic is too strict (e.g., only supports exact versions).
- Missing error handling in fallback paths.

**Fix:**
- **Expand fallback queries** to cover more cases.
- **Log fallback decisions** for debugging.

**Example (Pseudocode):**
```python
def query_data(db_version: str) -> List[dict]:
    try:
        # Try modern query
        return db.execute("SELECT * FROM users WHERE created_at > NOW() - INTERVAL '1 week'")
    except UnsupportedOperatorError:
        # Fallback to older syntax
        log.warning(f"Using legacy query for DB v{db_version}")
        return db.execute("SELECT * FROM users WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)")
```

**Verification:**
- Force a **fallback scenario** (e.g., fake old DB version) to test recovery.

---

## **3. Debugging Tools & Techniques**

### **A. Logging & Probing**
- **Enable detailed logging** for CDR decisions:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  logging.debug(f"Probed DB v{db_version}, supports WINDOWS: {supports_windows()}")
  ```
- **Use SQL dumps** (`EXPLAIN ANALYZE`) to verify query execution.

### **B. Dynamic SQL Inspection**
- **Log executed queries** before sending them to the DB:
  ```python
  final_query = build_query(db_version)
  logging.debug(f"Executing: {final_query}")
  db.execute(final_query)
  ```

### **C. Version Detection Testing**
- **Test edge cases** (e.g., `5.7.0`, `8.0.0`, `10.0.0`).
- **Use a Docker DB container** for isolated testing:
  ```bash
  docker run --name test-mysql -e MYSQL_ROOT_PASSWORD=pass -d mysql:5.7
  ```

### **D. Performance Profiling**
- **Measure probing overhead** (e.g., with `cProfile` in Python).
- **Optimize caching** to reduce runtime checks.

---

## **4. Prevention Strategies**

### **A. Version Testing Matrix**
- **Test against multiple DB versions** in CI:
  ```yaml
  # GitHub Actions example
  matrix:
    db-version: ["5.7", "8.0", "10.0"]
  ```

### **B. Feature Flagging**
- **Use runtime flags** to control behavior:
  ```python
  if get_feature_flag("supports_windows"):
      query.push("OVER (PARTITION BY id)")
  ```

### **C. Runtime Capability Cache**
- **Cache detected capabilities** to avoid repeated probes:
  ```python
  from functools import lru_cache

  @lru_cache(maxsize=32)
  def supports_operator(op: str) -> bool:
      return probe_db(op)
  ```

### **D. Extensive Unit Tests**
- **Mock DB responses** in tests:
  ```python
  @pytest.fixture
  def mock_db():
      class MockDB:
          def execute(self, query):
              # Simulate different DB responses
              if "JOIN" in query:
                  raise UnsupportedOperatorError()
              return [{"id": 1}]
      return MockDB()
  ```

---

## **Conclusion**
The **Capability Detection Runtime** pattern is powerful but requires careful handling. By following this guide, you can:
✅ **Quickly diagnose** runtime feature detection failures.
✅ **Fix issues** with targeted code changes.
✅ **Prevent regressions** with testing and caching.

**Key Takeaways:**
- **Log probing decisions** for debugging.
- **Test edge cases** early.
- **Cache capabilities** to reduce overhead.
- **Fallback gracefully** with fallback queries.

For further reading, consult **database-specific documentation** (e.g., MySQL’s `SHOW STATUS`, PostgreSQL’s `\dx`).