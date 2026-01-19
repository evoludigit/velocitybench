# **[Pattern] Testing Anti-Patterns Reference Guide**

---

## **Overview**
Testing Anti-Patterns describe common, counterproductive practices in software testing that introduce technical debt, reduce reliability, or create maintenance burdens. Unlike anti-patterns in architecture or design, these directly impact test quality, maintainability, and project velocity. Identifying and avoiding these pitfalls ensures scalable, high-coverage test suites that adapt to evolving requirements.

Common consequences of testing anti-patterns include:
- **Flaky tests** (inconsistent failures)
- **Test bloat** (redundant or overly complex tests)
- **Slow test execution** (long build cycles)
- **Test ignorance** (lack of coverage for critical paths)
- **Poor maintainability** (tests that break frequently or lack clarity)

This guide categorizes testing anti-patterns by type, provides schema references for key indicators, and offers query examples to detect them in codebases. Mitigation strategies are also outlined.

---

## **Schema Reference**

| **Anti-Pattern**               | **Description**                                                                 | **Key Indicators**                                                                 | **Impact**                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **1. Flaky Tests**            | Tests that pass/fail unpredictably due to race conditions, environment issues, or flakiness. | - Tests manually marked as `[Flaky]` or marked for retries.                     | Degrades CI pipeline trust, wastes developer time.                        |
|                               |                                                                               | - Tests with no deterministic behavior (e.g., `assertEquals(randomValue, expected)`). |                                                                             |
|                               |                                                                               | - High failure rates on stable branches (e.g., main/master).                    |                                                                             |
| **2. Overly Broad Assertions**| Tests that check too much at once, obscuring failures.                          | - Assertions with nested conditions (e.g., `assertThat(user, hasProperty("name", "John").and(hasProperty("age", 30)))`). | Hard to debug; vague error messages.                                     |
|                               |                                                                               | - Tests that assert on implementation details (e.g., `assertEquals(5, list.size())` where size is non-critical). |                                                                             |
| **3. Test Duplication**       | Repeated tests with identical or similar logic across modules.               | - Duplicate test classes with parallel names (e.g., `UserServiceTest` and `UserServiceUnitTest`). | Maintenance burden; redundancy.                                           |
|                               |                                                                               | - Copy-pasted tests with only minor parameter changes.                          |                                                                             |
| **4. Mock Everything**        | Overuse of mocks/stubs, leading to tests that don’t validate real system interactions. | - Tests with >90% mock coverage (e.g., `Mockito.verify` calls dominate).        | Tests fail to catch integration issues; brittle.                          |
|                               |                                                                               | - Absence of real database/API calls in tests.                                  |                                                                             |
| **5. Ignoring Test Coverage** | Tests only cover happy paths or trivial cases, ignoring edge cases/errors.       | - Low branch/line coverage in critical modules.                               | Undetected bugs; poor reliability.                                        |
|                               |                                                                               | - Missing tests for error handling (e.g., no `try-catch` test cases).          |                                                                             |
| **6. Test Ignorance**         | Tests that don’t match the production environment (e.g., dev vs. prod differences). | - Tests using hardcoded "test" databases/users.                             | False positives/negatives; environment-specific bugs.                     |
|                               |                                                                               | - No environment variables for test configurations.                            |                                                                             |
| **7. Slow Tests**             | Tests with excessive I/O, async delays, or inefficient queries.               | - Tests with `Thread.sleep()` or blocking calls.                              | Long CI cycles; discourages frequent testing.                            |
|                               |                                                                               | - Database-heavy tests without connection pooling.                            |                                                                             |
| **8. No Test Isolation**      | Tests that depend on each other’s state or cleanup.                           | - Tests modifying shared resources (e.g., static variables, global caches).      | Inconsistent results; hard to debug.                                       |
|                               |                                                                               | - No `@BeforeEach`/`@AfterEach` cleanup.                                    |                                                                             |
| **9. Tests as Documentation** | Tests written *after* code to "document" behavior, not to validate it.         | - Tests with no assertions (e.g., `public void testLoginPageExists()`).      | Waste of time; no value if broken.                                        |
|                               |                                                                               | - Tests copying requirements specs verbatim.                                  |                                                                             |
| **10. Test Smells in CI**     | CI pipelines that run all tests unnecessarily or lack prioritization.          | - Full suites running on every commit.                                       | Slow feedback loops; wasted compute resources.                           |
|                               |                                                                               | - No test matrix (e.g., unit → integration → e2e phases).                      |                                                                             |

---

## **Detection Query Examples**

Use these queries (pseudo-code/SQL-like syntax) to identify anti-patterns in your codebase. Adapt to your language/framework (e.g., Java, Python, JavaScript).

### **1. Detecting Flaky Tests**
**Java (JUnit + Maven/Gradle):**
```bash
# Grep for tests marked as flaky or with retry logic
grep -r "Flaky\|retry\|failIf.*false" tests/ | grep -v "__tests__"
```
**Python (pytest):**
```python
# Check for tests with non-deterministic conditions (e.g., random values)
grep -r "random\|time.sleep\|mock_patch" tests/
```

### **2. Identifying Overly Broad Assertions**
**Java (AssertJ/hamcrest):**
```bash
# Find tests with nested assertions (e.g., `.and()` chains)
grep -r "hasProperty.*and\|is.*and\|assertThat.*and" tests/
```
**JavaScript (Jest):**
```bash
# Look for vague assertions (e.g., `toBeTruthy()`)
grep -r "toBe\|toHaveBeenCalled" tests/ | grep -v "CalledWith"
```

### **3. Spotting Test Duplication**
**General (any language):**
```bash
# Compare test files for similarity (e.g., using `diff` or `jscodeshift`)
for file in tests/*.java tests/*.py tests/*.js; do
  diff -q "$file" tests/$(basename "$file" .java).java tests/$(basename "$file" .py).py
done | grep "identical"
```

### **4. Mock Overuse**
**Java (Mockito):**
```bash
# Count Mockito.verify calls per test
grep -r "verify" tests/ | wc -l | awk '{if($1 > 10) print "Potential mock overuse in high-verify tests."}'
```
**Python (unittest.mock):**
```bash
# Find tests with excessive mock patches
grep -r "patch.*object\|Mock\|side_effect" tests/ | grep -v "__init__"
```

### **5. Low Test Coverage**
**Java (JaCoCo):**
```bash
# Generate coverage report and filter for low-coverage classes
jacoco report --classfiles=target/classes --sourcefiles=src/main/java \
  --dest=coverage-report && grep -A 5 "Branch.*0%" coverage-report/html/index.html
```
**Python (Coverage.py):**
```bash
# Identify missing branches in critical files
coverage run -m pytest && coverage report --include="src/core/*.py" | grep "0%"
```

### **6. Test Ignorance (Dev vs. Prod Mismatch)**
**Environment Checks:**
```bash
# Look for hardcoded "test" credentials
grep -r "test_.*db\|dev.*db\|localhost" src/ tests/ | grep -v "__tests__"
```

### **7. Slow Tests**
**Java (Timing Analysis):**
```bash
# Use JMH or custom logging to find slow tests
mvn test -Dtest=com.example.SlowTestSuite -Dverbose=true | grep "T"
```
**Python:**
```python
# Profile tests with `cProfile`
python -m cProfile -o test_profiler.prof pytest tests/
```

### **8. No Test Isolation**
**Static Analysis:**
```bash
# Detect tests modifying static/global state
grep -r "static (field|method)|global\|singleton" tests/ | grep -v "__tests__"
```

### **9. Tests as Documentation**
**Check for Assertion-Free Tests:**
```bash
# Find tests with no assertions (e.g., just setup)
grep -r "test.*Exists\|test.*Loads\|test.*Works" tests/ | grep -v "assert\|expect"
```

### **10. CI Test Smells**
**CI Pipeline Analysis:**
```bash
# Check for full-suite CI jobs
grep -r "mvn clean install\|pytest tests/.*--all" .github/workflows/
```

---

## **Mitigation Strategies**

| **Anti-Pattern**          | **Mitigation**                                                                 |
|---------------------------|--------------------------------------------------------------------------------|
| **Flaky Tests**           | - Isolate async operations (e.g., `@Async` tests).                           |
|                           | - Use deterministic seeds for random data.                                    |
|                           | - Implement test retries with backoff (e.g., `pytest-retries`).               |
| **Overly Broad Assertions** | - Split assertions into single, focused checks.                              |
|                           | - Use libraries like `AssertJ` or `Hamcrest` for granular assertions.         |
| **Test Duplication**      | - Use test factories (e.g., Spring’s `@DataJpaTest`, pytest fixtures).         |
|                           | - Refactor duplicate tests into shared helper methods.                       |
| **Mock Everything**       | - Follow the **Mocking Patterns** guide (e.g., mock only external dependencies). |
|                           | - Add integration tests for critical paths.                                    |
| **Ignoring Test Coverage** | - Prioritize edge cases (e.g., error boundaries, race conditions).           |
|                           | - Use property-based testing (e.g., QuickCheck, Hypothesis).                 |
| **Test Ignorance**        | - Use feature flags to toggle test environments.                              |
|                           | - Containerize tests (e.g., Docker) to match prod.                            |
| **Slow Tests**            | - Parallelize tests (e.g., Maven Surefire Parallel, pytest-xdist).              |
|                           | - Cache database fixtures.                                                      |
| **No Test Isolation**     | - Use test containers (e.g., Testcontainers) for isolated DBs.                |
|                           | - Clean up resources in `@AfterEach`.                                         |
| **Tests as Documentation**| - Write tests *before* code (TDD); document in comments or separate files.     |
| **Test Smells in CI**     | - Implement test matrices (unit → integration → e2e).                          |
|                           | - Cache dependencies to speed up builds.                                       |

---

## **Related Patterns**

Consult these complementary patterns to improve testing practices:

1. **[Test-Driven Development (TDD)](TDD.md)**
   - Frameworks: TDD workflows to prevent test ignorance and duplication.
   - *See also*: ["Red-Green-Refactor" cycle](https://www.agilealliance.org/glossary/tdd/).

2. **[Behavior-Driven Development (BDD)](BDD.md)**
   - Frameworks: Cucumber, SpecFlow.
   - *Use case*: Aligns tests with business requirements to reduce flakiness from vague specs.

3. **[Mocking Patterns](Mocking.md)**
   - Techniques: Isolate tests by mocking external dependencies.
   - *Warning*: Avoid "mocking everything" (see this guide’s **Mock Overuse** section).

4. **[Test Pyramid](TestPyramid.md)**
   - Structure: Balance unit, integration, and end-to-end tests to mitigate slow tests and flakiness.
   - *Goal*: ~70% unit tests, 20% integration, 10% e2e.

5. **[Property-Based Testing](PropertyBasedTesting.md)**
   - Frameworks: QuickCheck (Haskell), Hypothesis (Python), JUnit Quark (Java).
   - *Benefit*: Automatically generates edge cases to address **ignored coverage**.

6. **[Test Containers](TestContainers.md)**
   - Tools: Testcontainers (Java), Dockerized test environments.
   - *Mitigates*: **Test Ignorance** by ensuring prod-like environments.

7. **[Flaky Test Detection](FlakyTestDetection.md)**
   - Tools: Flakelink, flaky (Chrome), custom scripts with statistical analysis.
   - *Target*: Proactively identify and fix **Flaky Tests**.

8. **[Test Data Management](TestDataManagement.md)**
   - Frameworks: Testcontainers, SQL mocks (e.g., H2 in-memory DB).
   - *Goal*: Avoid **slow tests** and **test ignorance** with controlled data.

---
**Key Takeaway**: Testing anti-patterns often stem from trade-offs (e.g., speed vs. reliability). Prioritize **isolation**, **determinism**, and **coverage** to build maintainable test suites. Regularly audit your tests using the queries above, and refactor proactively.