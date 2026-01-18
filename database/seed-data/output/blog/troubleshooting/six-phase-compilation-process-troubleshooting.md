# **Debugging the Six-Phase Compilation Process: A Troubleshooting Guide**

The **Six-Phase Compilation Pattern**—comprising **Parser, Binder, WHERE Generator, Validator, Optimizer, and Artifact Emitter**—is a structured approach to compilation. However, issues in any phase can cascade, making debugging complex. This guide helps you isolate, diagnose, and resolve common problems efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue by cross-referencing these symptoms:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|--------------------------------------------|
| Compilation fails with generic errors (e.g., "Invalid syntax") | Parser or Binder misconfiguration |
| Logic errors (e.g., incorrect WHERE conditions) | WHERE Generator or Validator issue |
| Performance degradation (compilation slows unexpectedly) | Optimizer or Artifact Emitter bottleneck |
| Inconsistent outputs for same input | State mismatch between phases |
| New features break existing code | Phase dependency misalignment |
| Artifacts (e.g., compiled bytecode) contain errors | Artifact Emitter or Optimizer corruption |

If multiple symptoms appear, the problem likely spans multiple phases.

---

## **2. Common Issues & Fixes**

### **Issue 1: Parser Fails Silently (No Clear Error Location)**
**Symptoms:**
- Errors like `SyntaxError: Unexpected token` without line numbers.
- The compiler accepts invalid input but generates broken output.

**Root Cause:**
- The parser may lack proper error handling or is not integrated with the Binder.
- Lexer errors are silently discarded.

**Fix:**
1. **Enforce Parsing Errors with Context**
   Modify the parser to include source positions:
   ```java
   // Example: Parser with line/column tracking
   public class CustomParser implements Parser {
       private SourcePosition position = new SourcePosition(1, 1);

       @Override
       public void match(TokenType expected) throws ParseException {
           if (!currentToken.matches(expected)) {
               throw new ParseException(
                   "Unexpected token: " + currentToken.type +
                   " at line " + position.line + ", col " + position.col
               );
           }
           position = position.advance();
       }
   }
   ```
2. **Log Lexer Errors Explicitly**
   Ensure the lexer fails fast:
   ```python
   # Example: Lexer with error propagation
   def next_token(self):
       if current_token.type == UNEXPECTED:
           raise LexerError(f"Invalid token at position {self.position}")
       return current_token
   ```
3. **Use a Testing Framework for Edge Cases**
   Test invalid inputs early:
   ```javascript
   // Unit test for parser
   test("Rejects malformed input", () => {
       const input = "SELECT ; FROM table";
       expect(() => parser.parse(input)).toThrow("SyntaxError");
   });
   ```

---

### **Issue 2: Binder Fails to Resolve Symbols**
**Symptoms:**
- Runtime errors like "Undefined variable" or "Type mismatch."
- The compiler succeeds, but execution fails.

**Root Cause:**
- The binder’s symbol table is incomplete or incorrect.
- Type inference fails in intermediate expressions.

**Fix:**
1. **Validate Symbol Resolution Early**
   Add a Symbol Validation Phase:
   ```java
   // Example: Symbol validation in Binder
   public class BinderExtension {
       public void validateSymbols(SymbolTable table) {
           for (Symbol sym : table.getSymbols()) {
               if (sym.type == UNRESOLVED) {
                   throw new BinderException(
                       "Symbol '" + sym.name + "' unresolved"
                   );
               }
           }
       }
   }
   ```
2. **Improve Type Inference**
   If types are ambiguous, enforce explicit annotations:
   ```sql
   -- Before: Ambiguous type
   SELECT x + y FROM table; -- Could be int or float

   -- After: Explicit type
   SELECT CAST(x AS INT) + y FROM table;
   ```

---

### **Issue 3: WHERE Generator Produces Incorrect Queries**
**Symptoms:**
- SQL queries contain malformed conditions.
- Filtering logic fails (e.g., `WHERE x > 10 AND y < 0` returns unexpected rows).

**Root Cause:**
- Logical operators are misplaced or misinterpreted.
- The WHERE Generator fails to handle nested conditions.

**Fix:**
1. **Debug WHERE Conditions Step-by-Step**
   Log intermediate WHERE clauses:
   ```python
   # Python-like pseudocode
   def generate_where(self, condition):
       print(f"DEBUG: Generating WHERE: {condition.to_sql()}")
       return condition.to_sql()
   ```
2. **Unit Test WHERE Generation**
   Verify edge cases:
   ```java
   @Test
   public void testNestedConditions() {
       WHERE condition = new WHERE("A > 5 AND B < 10 OR C = 'X'");
       assertEquals("(A > 5) AND ((B < 10) OR (C = 'X'))", condition.toSQL());
   }
   ```
3. **Use a WHERE Simplifier**
   Optimize complex conditions early:
   ```sql
   -- Before: Inefficient
   WHERE (A AND B) OR (NOT A AND C)

   -- After: Simplified
   WHERE B OR (NOT A AND C)
   ```

---

### **Issue 4: Validator Fails Due to Missing Constraints**
**Symptoms:**
- "Schema violation" errors despite valid syntax.
- Constraints (e.g., foreign keys) are ignored.

**Root Cause:**
- Validation rules are not applied in the correct order.
- Schema checks are skipped.

**Fix:**
1. **Reorder Validation Steps**
   Ensure foreign keys are checked after schema resolution:
   ```java
   class Validator {
       public void validate(Schema schema) {
           // Check constraints in this order
           checkPrimaryKeys(schema);
           checkForeignKeys(schema); // Critical for WHERE conditions
           checkNotNull(schema);
       }
   }
   ```
2. **Log Validation Rules**
   Debug missing constraints:
   ```sql
   -- Enable constraint logging in SQL dialect
   SET SESSION sql_show_constraints = ON;
   ```

---

### **Issue 5: Optimizer Introduces Regressions**
**Symptoms:**
- Compiled artifacts run slower than expected.
- Optimizations break existing queries.

**Root Cause:**
- Aggressive inlining or query rewriting.
- Missing cost-based optimization.

**Fix:**
1. **Disable Optimizations for Debugging**
   Bypass the optimizer temporarily:
   ```java
   // Example: Skip optimization
   Query query = new Query(parser.parse(input));
   Query optimized = optimizer.optimize(query); // Forced pass
   ```
2. **Profile Query Performance**
   Use a profiler to identify bottlenecks:
   ```bash
   # Example: SQL query execution time
   EXPLAIN ANALYZE SELECT * FROM large_table WHERE x = 5;
   ```
3. **Add Optimization Warnings**
   Log before/after optimization:
   ```java
   // Debug optimization impact
   System.out.printf(
       "Query length before: %d, after: %d%n",
       query.size(), optimizer.optimize(query).size()
   );
   ```

---

### **Issue 6: Artifact Emitter Produces Invalid Code**
**Symptoms:**
- Compiled output (e.g., Java bytecode, SQL) contains syntax errors.
- Artifacts fail to execute.

**Root Cause:**
- Incorrect code generation rules.
- Missing type mappings.

**Fix:**
1. **Validate Artifacts Before Emit**
   Use a linter for generated code:
   ```java
   // Example: Java bytecode validation
   try {
       bytecode.accept(new BytecodeValidator());
   } catch (BytecodeError e) {
       throw new ArtifactError("Generated code invalid", e);
   }
   ```
2. **Use a Code Generator Framework**
   Tools like **StringTemplate** or **ANTLR** reduce manual errors:
   ```java
   // Example: ANTLR-generated code
   public class SqlGenerator {
       public String generate(Query query) {
           return new SqlTemplate(query).toString();
       }
   }
   ```
3. **Test Artifacts in Isolation**
   Execute compiled output without external dependencies:
   ```bash
   # Example: Test bytecode in a sandbox
   java -cp test.jar com.example.CompiledClass
   ```

---

## **3. Debugging Tools & Techniques**

### **A. Logging & Tracing**
- **Phase-Specific Logging:**
  Add logs at each phase to track input/output:
  ```java
  public class DebugCompiler {
      public void compile() {
          log("--- Parser Input ---");
          log(parser.parse(input));
          log("--- Binder Output ---");
          log(binder.bind(parsed));
          // ... repeat for all phases
      }
  }
  ```
- **Use Structured Logging (JSON):**
  ```json
  {
    "phase": "WHERE Generator",
    "input": {"condition": "x > 5"},
    "output": {"where_sql": "WHERE x > 5"}
  }
  ```

### **B. Debugging with Mock Inputs**
- **Unit Test Each Phase:**
  ```java
  @Test
  public void testParserPhase() {
      String input = "SELECT id FROM users";
      AST ast = parser.parse(input);
      assertEquals("SELECT", ast.getNodeType());
  }
  ```
- **Fuzz Testing:**
  Generate random invalid inputs to stress-test phases.

### **C. Visual Debugging**
- **Graph Input/Output:**
  Use **D3.js** or **Graphviz** to visualize:
  - AST structure
  - Dependency graphs between phases
  - Optimizer transformations

### **D. Time-Tracking for Bottlenecks**
- Measure phase execution time:
  ```java
  long start = System.nanoTime();
  binder.bind(parsed);
  long duration = System.nanoTime() - start;
  System.out.println("Binder took " + duration + " ns");
  ```

---

## **4. Prevention Strategies**

### **A. Design for Testability**
1. **Separate Concerns Strictly**
   Ensure each phase can be tested independently:
   ```java
   // Example: Parser as a service
   public interface ParserService {
       AST parse(String input) throws ParseException;
   }
   ```
2. **Use Dependency Injection**
   Mock dependencies for unit tests:
   ```java
   @Test
   public void testBinder() {
       ParserService parser = mock(ParserService.class);
       Binder binder = new Binder(parser);
       binder.bind(/* ... */);
   }
   ```

### **B. Automated Validation**
1. **Schema & Syntax Checks**
   Run validation before compilation:
   ```python
   def precompile_checks(query):
       if not schema_validator.validate(query):
           raise PrecompilationError("Schema mismatch")
   ```
2. **Regression Testing**
   Re-run tests on every code change:
   ```bash
   pytest test_compilation_regression.py -v
   ```

### **C. Phase Boundary Guards**
1. **Input/Output Contracts**
   Define explicit contracts between phases:
   ```java
   public interface BinderOutput {
       List<Symbol> resolveSymbols();
       Type inferType(Node node);
   }
   ```
2. **Input Sanitization**
   Validate inputs between phases:
   ```java
   public class PhaseGuard {
       public AST sanitize(AST input) {
           if (input.getNodeType() == NULL) {
               throw new IllegalStateException("Null AST received");
           }
           return input;
       }
   }
   ```

### **D. Documentation & Checklists**
1. **Phase-Specific Documentation**
   Document:
   - Input format (e.g., AST structure)
   - Output format (e.g., WHERE clause rules)
   - Known edge cases
2. **Checklists for New Features**
   ```markdown
   # Adding a New WHERE Condition
   1. Update WHERE Generator parser
   2. Test validation rules
   3. Verify optimizer handles it
   4. Test artifact emission
   ```

---

## **5. Summary of Key Actions**
| **Issue**               | **Quick Fix**                          | **Long-Term Fix**                     |
|-------------------------|----------------------------------------|---------------------------------------|
| Parser errors           | Add line/column tracking               | Use ANTLR/parser generators           |
| Binder failures         | Validate symbols early                 | Improve type inference                |
| WHERE logic errors      | Log intermediate conditions            | Add WHERE simplifier                  |
| Validator failures      | Reorder constraint checks              | Automate schema validation            |
| Optimizer regressions   | Disable optimizations temporarily      | Profile and refine heuristics         |
| Artifact corruption     | Validate before emission               | Use code generation frameworks        |

---

## **Final Tips**
- **Start Small:** Isolate the failing phase by commenting out others.
- **Use a Debug Build:** Compile with `-Ddebug=true` for extra logs.
- **Leverage Existing Tools:** Use SQL grammars (ANTLR), Java decompilers (JD-GUI), or Python’s `ast` module.

By following this guide, you can systematically debug the six-phase compilation process and prevent future issues.