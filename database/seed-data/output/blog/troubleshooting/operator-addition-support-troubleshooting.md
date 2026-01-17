# **Debugging Operator Addition: A Troubleshooting Guide**

## **Introduction**
The **Operator Addition** pattern is used to dynamically extend filtering capabilities in applications (e.g., APIs, search engines, or data pipelines). Commonly implemented via **Fluent Interfaces**, **Builder Pipelines**, or **Query Objects**, this pattern allows users to chain operators (`AND`, `OR`, `NOT`, `LIKE`, `IN`, etc.) for flexible querying. However, issues often arise when adding new operators or modifying existing ones, leading to runtime errors, incorrect query generation, or performance bottlenecks.

This guide provides a systematic approach to troubleshooting issues related to operator addition in filtering systems.

---

## **1. Symptom Checklist**
Before diving into debugging, verify whether your issue matches any of these symptoms:

| **Symptom** | **Description** |
|-------------|----------------|
| **Operator Not Recognized** | Newly added operators (e.g., `STARTS_WITH`, `CONTAINS`) are ignored or throw errors. |
| **Invalid Query Generation** | The final query malforms (e.g., missing parentheses, incorrect syntax). |
| **NPE or ClassCastException** | NullPointerException when building filter chains or incorrect type casting. |
| **Duplicate or Missing Conditions** | Extra/omitted clauses in generated SQL/JSON/NoSQL queries. |
| **Performance Degradation** | Slow query execution after adding an operator. |
| **Inconsistent Behavior** | Works in some environments but fails in others (e.g., dev vs. prod). |
| **Memory Leaks** | Unclosed resources (e.g., connections, streams) in operator logic. |
| **Thread Safety Issues** | Race conditions when multiple requests modify shared filter states. |

If you observe **multiple symptoms**, prioritize **NPE/ClassCastException** or **query malformation** first, as they often indicate structural issues.

---

## **2. Common Issues and Fixes**

### **Issue 1: Operator Not Being Recognized**
**Scenario:**
A new operator (e.g., `STARTS_WITH`) is added but ignored during query construction.

**Root Causes:**
- **Missing registration in operator map:** The operator is not stored in a `HashMap`/`Enum` lookup.
- **Improper method chaining:** The fluent interface method is not exposed or correctly called.
- **Case sensitivity issues:** Operator names must match **exactly** (e.g., `"starts_with"` vs `"START_WITH"`).

**Fixes:**
#### **Example: Java Fluent Interface (Correct Registration)**
```java
// ✅ Correct: Operator registered in a Map
private static final Map<String, FilterOperator> OPERATORS = new EnumMap<>(String.class);
static {
    OPERATORS.put("EQ", new EqualOperator());
    OPERATORS.put("STARTS_WITH", new StartsWithOperator()); // ✔️ Added correctly
}

// ❌ Wrong: Operator not registered
public class FilterBuilder {
    private String currentOperator;

    public FilterBuilder startsWith(String field, String value) {
        this.currentOperator = "STARTS_WITH"; // ❌ May not exist in OPERATORS
        // ...
    }
}
```
**Solution:**
1. **Register the operator in the enum/map:**
   ```java
   OPERATORS.put("STARTS_WITH", new StartsWithOperator());
   ```
2. **Ensure case sensitivity matches:**
   ```java
   OPERATORS.put("starts_with", new StartsWithOperator()); // Force lowercase if needed
   ```
3. **Add input validation:**
   ```java
   public FilterBuilder startsWith(String field, String value) {
       if (!OPERATORS.containsKey("STARTS_WITH")) {
           throw new IllegalArgumentException("Operator 'STARTS_WITH' not supported");
       }
       // ...
   }
   ```

---

### **Issue 2: Query Malformation (Missing Parentheses, Syntax Errors)**
**Scenario:**
A query like `WHERE (age > 25 AND name STARTS_WITH "John") OR (age < 30)` generates incorrectly as `WHERE age > 25 AND name STARTS_WITH "John" OR age < 30`.

**Root Causes:**
- **Improper precedence handling:** Operators are not grouped with parentheses.
- **Incorrect condition concatenation:** Using `+` instead of `AND`/`OR` in SQL/JSON.
- **Lazy evaluation issues:** Conditions are merged sequentially without tracking operator precedence.

**Fixes:**
#### **Example: SQL Query Builder (Proper Parenthesization)**
```java
// ✅ Correct: Enforces parentheses for nested conditions
public String buildSql() {
    StringBuilder sb = new StringBuilder("WHERE ");
    sb.append(this.leftCondition);
    sb.append(" ").append(this.operator);
    sb.append(" (").append(this.rightCondition).append(")"); // ✔️ Wraps in parentheses
    return sb.toString();
}

// ❌ Wrong: No grouping
public String buildSql() {
    return "WHERE " + leftCondition + " " + operator + " " + rightCondition; // ❌ Missing parentheses
}
```
**Solution:**
1. **Use a stack-based or recursive approach** to handle precedence:
   ```java
   private String buildNestedConditions(List<Condition> conditions, Operator operator) {
       StringBuilder sb = new StringBuilder();
       conditions.forEach(c ->
           sb.append("(").append(c).append(")").append(" ").append(operator.value).append(" ")
       );
       return sb.toString();
   }
   ```
2. **For JSON-based filters (e.g., Elasticsearch), enforce schema:**
   ```json
   // ✅ Correct: Enforces operator nesting
   {
     "must": [
       { "range": { "age": { "gt": 25 } } },
       {
         "bool": {
           "must": [
             { "wildcard": { "name": "*John*" } }
           ]
         }
       }
     ]
   }
   ```

---

### **Issue 3: NullPointerException or ClassCastException**
**Scenario:**
Adding a new operator crashes with `java.lang.NullPointerException` or `java.lang.ClassCastException`.

**Root Causes:**
- **Uninitialized operator instance:** A new operator is used without creating an instance.
- **Incorrect return type:** A method returns the wrong type (e.g., `Filter` instead of `FilterBuilder`).
- **Thread-local state leaks:** Shared static variables cause race conditions.

**Fixes:**
#### **Example: Safe Operator Initialization**
```java
// ✅ Correct: Lazy-initialize operator
private FilterOperator getOperator(String opName) {
    if (!OPERATORS.containsKey(opName)) {
        return new DefaultOperator(); // Fallback
    }
    return OPERATORS.get(opName);
}

// ❌ Wrong: Null if not registered
private FilterOperator getOperator(String opName) {
    return OPERATORS.get(opName); // ❌ NPE if missing
}
```
**Solution:**
1. **Provide a fallback operator:**
   ```java
   return OPERATORS.getOrDefault(opName, new FallbackOperator());
   ```
2. **Ensure method chaining returns the correct type:**
   ```java
   public FilterBuilder or(String field, Object value) {
       conditions.add(new Condition(field, "OR", value));
       return this; // ✔️ Returns FilterBuilder (not Filter)
   }
   ```
3. **Avoid static shared state:**
   ```java
   // ❌ Bad: Thread-unsafe if shared across requests
   private static List<Condition> conditions = new ArrayList<>();

   // ✅ Better: Instance-local or thread-local
   private final List<Condition> conditions = new ArrayList<>();
   ```

---

### **Issue 4: Duplicate or Missing Conditions**
**Scenario:**
A filter like `age > 25 AND name STARTS_WITH "John"` generates `WHERE age > 25 AND name STARTS_WITH "John" AND name STARTS_WITH "John"` (duplicate) or misses a condition entirely.

**Root Causes:**
- **Accidental re-adding:** Conditions are appended instead of merged.
- **Lazy evaluation timing:** Conditions are evaluated at the wrong stage.
- **Improper merge logic:** `AND`/`OR` logic doesn’t combine conditions correctly.

**Fixes:**
#### **Example: Condition Deduplication**
```java
// ✅ Correct: Check for duplicates before adding
public FilterBuilder addCondition(Condition condition) {
    if (!conditions.contains(condition)) { // ✔️ Avoid duplicates
        conditions.add(condition);
    }
    return this;
}

// ❌ Wrong: Always adds duplicates
public FilterBuilder addCondition(Condition condition) {
    conditions.add(condition); // ❌ No check
    return this;
}
```
**Solution:**
1. **Track conditions in a `Set` for deduplication:**
   ```java
   private final Set<Condition> conditions = new HashSet<>();
   ```
2. **Use a merge strategy for `AND`/`OR`:**
   ```java
   public FilterBuilder and(Condition condition) {
       conditions.add(condition);
       return this;
   }

   public FilterBuilder or(Condition condition) {
       if (conditions.isEmpty()) {
           conditions.add(condition);
       } else {
           // Merge OR logic (e.g., wrap in a parenthetical group)
           conditions.add(new OrGroup(conditions, condition));
       }
       return this;
   }
   ```

---

### **Issue 5: Performance Degradation**
**Scenario:**
Adding a new operator (e.g., `LIKE`) slows down query execution by 10x.

**Root Causes:**
- **Inefficient regex matching:** `LIKE` or `CONTAINS` uses slow regex instead of index lookups.
- **Unoptimized string operations:** `startsWith()` does full scans.
- **Memory bloat:** Intermediate query objects grow unnecessarily.

**Fixes:**
#### **Example: Optimized String Search**
```java
// ✅ Correct: Uses index-aware methods (e.g., Elasticsearch)
public boolean matches(String field, String value) {
    return elasticsearchClient.search(
        query -> query
            .match(m -> m
                .field(field)
                .query(value)
                .operator(Operator.AND)
            )
    ).isValid();
}

// ❌ Wrong: Full-text scan (slow)
public boolean matches(String field, String value) {
    return database.query("SELECT * FROM users WHERE " + field + " LIKE '%" + value + "%'")
        .exists(); // ❌ No index usage
}
```
**Solution:**
1. **Use database-specific optimizations:**
   - **SQL:** Replace `LIKE '%val%'` with full-text search or indexes.
   - **NoSQL (MongoDB):** Use `$text` search or `$regex`.
   - **Elasticsearch:** Leverage `match` instead of `wildcard`.
2. **Cache frequent operators:**
   ```java
   private static final Map<String, BiPredicate<String, Object>> OPERATOR_CACHE =
       new ConcurrentHashMap<>();

   static {
       OPERATOR_CACHE.put("STARTS_WITH", (field, value) ->
           database.startsWith(field, value) // Precompiled
       );
   }
   ```

---

## **3. Debugging Tools and Techniques**

### **Tool 1: Logging and Tracing**
- **Enable debug logs** for the filter builder:
  ```java
  Logger logger = Logger.getLogger(FilterBuilder.class.getName());
  logger.setLevel(Level.DEBUG);

  public FilterBuilder startsWith(String field, String value) {
      logger.debug("Adding STARTS_WITH condition: field={}, value={}", field, value);
      // ...
  }
  ```
- **Use structured logging (JSON):**
  ```java
  logger.debug("{" +
      "\"operator\":\"STARTS_WITH\"," +
      "\"field\":\"%s\"," +
      "\"value\":\"%s\"}" +
      , field, value);
  ```

### **Tool 2: Query Validation**
- **Parse and validate queries before execution:**
  ```java
  public void validateQuery() {
      if (conditions.stream().anyMatch(Condition::isInvalid)) {
          throw new IllegalStateException("Invalid conditions in query");
      }
  }
  ```
- **Use schema validation (e.g., JSON Schema for filters).**

### **Tool 3: Mutation Testing**
- **Use tools like PITest or Stryker** to ensure new operators don’t break existing logic:
  ```bash
  mvn test org.pitest:pitest-maven:mutationCoverage
  ```
- **Example mutation:** Force an `NPE` in an operator to check if exceptions are handled.

### **Tool 4: Profiling**
- **Profile query execution** with:
  - **Java Flight Recorder (JFR):** Identify slow operators.
  - **SQL Profiling (e.g., `EXPLAIN ANALYZE` in PostgreSQL).**

---

## **4. Prevention Strategies**

### **Prevention 1: Operator Registry Pattern**
- **Centralize operator definitions** in an `enum` or `Map`:
  ```java
  public enum FilterOperator {
      EQ((a, b) -> a.equals(b)),
      GT((a, b) -> (Comparable) a).compareTo(b) > 0),
      STARTS_WITH((field, value) -> field.startsWith(value));

      private final BiPredicate<Object, Object> predicate;

      FilterOperator(BiPredicate<Object, Object> predicate) {
          this.predicate = predicate;
      }

      public boolean apply(Object a, Object b) {
          return predicate.test(a, b);
      }
  }
  ```

### **Prevention 2: Immutable Filter Builder**
- **Avoid mutable state** to prevent race conditions:
  ```java
  public final class ImmutableFilter {
      private final List<Condition> conditions;
      private final Operator defaultOperator;

      private ImmutableFilter(Builder builder) {
          this.conditions = Collections.unmodifiableList(builder.conditions);
          this.defaultOperator = builder.defaultOperator;
      }

      public static class Builder {
          private final List<Condition> conditions = new ArrayList<>();
          private Operator defaultOperator = Operator.AND;

          public Builder and(Condition condition) {
              conditions.add(condition);
              return this;
          }

          public ImmutableFilter build() {
              return new ImmutableFilter(this);
          }
      }
  }
  ```

### **Prevention 3: Unit Testing Operators**
- **Test each operator independently:**
  ```java
  @Test
  public void testStartsWithOperator() {
      assertTrue(new StartsWithOperator().test("JohnDoe", "John"));
      assertFalse(new StartsWithOperator().test("DoeJohn", "John"));
  }
  ```
- **Use property-based testing (QuickCheck, JUnit 5 Parametrized):**
  ```java
  @ParameterizedTest
  @ValueSource(strings = {"John", "J"})
  public void testStartsWithVariations(String prefix) {
      assertTrue(new StartsWithOperator().test("JohnDoe", prefix));
  }
  ```

### **Prevention 4: Documentation and Conventions**
- **Document operator constraints:**
  ```java
  /**
   * Adds a STARTS_WITH condition.
   *
   * @param field The field to match (e.g., "name").
   * @param value The prefix to match (case-sensitive).
   * @throws IllegalArgumentException If field is empty or value is null.
   */
  public FilterBuilder startsWith(String field, String value) { ... }
  ```
- **Enforce naming conventions:**
  - Use `snake_case` for operator names (`starts_with`, not `startsWith`).
  - Avoid reserved words (e.g., `or`, `and`).

### **Prevention 5: Gradual Rollout**
- **Feature flags for new operators:**
  ```java
  public FilterBuilder startsWith(String field, String value) {
      if (!isFeatureEnabled("new_operators")) {
          throw new UnsupportedOperationException("Feature disabled");
      }
      // ...
  }
  ```
- **Canary testing:** Release new operators to a subset of users first.

---

## **5. Step-by-Step Debugging Workflow**

| **Step** | **Action** | **Tools/Techniques** |
|----------|------------|----------------------|
| 1 | **Reproduce the issue** | Check logs, run unit tests, validate input data. |
| 2 | **Check operator registration** | Verify the operator exists in the registry map. |
| 3 | **Inspect query generation** | Log the intermediate query string. |
| 4 | **Validate method chaining** | Ensure `FilterBuilder` returns `this` at each step. |
| 5 | **Profile performance** | Use JFR or SQL profiler to find bottlenecks. |
| 6 | **Isolate the operator** | Test the new operator in isolation (unit test). |
| 7 | **Review thread safety** | Check for shared mutable state. |
| 8 | **Compare with working code** | Diff against a stable version. |
| 9 | **Apply fixes incrementally** | Test after each change. |
| 10 | **Monitor in production** | Use feature flags to roll back if needed. |

---

## **6. Example: Full Debugging Session**
**Problem:** A new `CONTAINS` operator is silently ignored.

### **Debugging Steps:**
1. **Check logs:**
   ```
   DEBUG [FilterBuilder] - Adding CONTAINS condition: field=description, value=test
   INFO  [QueryExecutor] - Generated query: WHERE age > 25  // ❌ CONTAINS missing
   ```
   → **Issue:** The operator is not being applied.

2. **Verify registration:**
   ```java
   System.out.println(FilterOperator.OPERATORS.keySet()); // Prints [EQ, GT, STARTS_WITH] ❌
   ```
   → **Fix:** Register `CONTAINS`.
   ```java
   OPERATORS.put("CONTAINS", new ContainsOperator());
   ```

3. **Test isolation:**
   ```java
   @Test
   public void testContainsOperator() {
       assertTrue(new ContainsOperator().test("Hello world", "world")); // ✅
       assertFalse(new ContainsOperator().test("Hello", "world"));    // ✅
   }
   ```
   → Operator works in isolation.

4. **Check query builder:**
   ```java
   public String buildSql() {
       StringBuilder sb = new StringBuilder("WHERE ");
       conditions.forEach(c -> sb.append(c.field).append(" ").append(c.operator).append(" '").append(c.value).append("' AND "));
       return sb.toString().replace(" AND ", " "); // ❌ Missing parentheses
   }
   ```
   → **Fix:** Use proper grouping.
   ```java
   public String buildSql() {
       return "WHERE (" + String.join(")