# **Debugging Property-Based Testing (PBT): A Troubleshooting Guide**

## **Introduction**
Property-Based Testing (PBT) is a powerful technique for generating and validating test cases automatically, ensuring correctness by checking invariants rather than explicit outcomes. While PBT reduces manual test case design, it introduces unique debugging challenges, such as inefficient generator logic, false positives, or scaling issues.

This guide helps backend engineers diagnose and resolve common PBT-related problems efficiently.

---

## **Symptom Checklist**
Before diving into fixes, check if your PBT implementation exhibits these symptoms:

### **Functional Issues**
- [ ] Tests pass for small inputs but fail for larger ones (scale problems)
- [ ] Unexpected test failures despite logically correct generators
- [ ] Randomness in test failures (shrinking issues)
- [ ] Generators produce invalid or edge-case-free inputs
- [ ] Tests slow down significantly with complex properties

### **Performance Issues**
- [ ] Tests take too long to execute (inefficient generators)
- [ ] High memory usage during property checks
- [ ] Shrinking phase is too slow or unresponsive

### **Debugging & Maintenance Issues**
- [ ] Difficulty reproducing failing test cases
- [ ] Tests pass locally but fail in CI/CD
- [ ] Hard to debug generator-specific failures

---

## **Common Issues and Fixes**

### **1. Generator Produces Invalid or Edge-Case-Lacking Inputs**
**Symptom:** Tests fail with messages like *"Expected predicate to hold, but generator produced invalid input."*

**Root Cause:**
- Generators are too simplistic (e.g., always generating small, valid inputs).
- Missing edge cases (empty lists, `null` values, negative numbers).

**Fix:**
- **Ensure generators cover all constraints.**
  ```python
  # Bad: Only generates positive integers
  def int_generator():
      return uniform_int_from_interval(-10, 10)  # Now covers negatives too

  # Good: Explicitly includes edge cases
  def broken_list_generator():
      n = uniform_int_from_interval(0, 5)
      if n == 0:
          return []  # Explicitly handle empty case
      return [uniform_int_from_interval(1, 100) for _ in range(n)]
  ```

- **Use shrinkage strategies to detect invalid generics early.**
  ```haskell
  -- In QuickCheck, ensure generators have `QuickCheck` instances
  prop_example :: Int -> Bool
  prop_example n = not (null (generator_function n)) -- Verify generator never produces empty list
  ```

---

### **2. Tests Fail Randomly (Shrinking Issues)**
**Symptom:** Some test runs pass, others fail with no clear pattern.

**Root Cause:**
- **Shrinking fails to isolate the minimal failing case** (common in `QuickCheck`, `Hypothesis`).
- **Deterministic generation conflicts** (e.g., random seeds not fixed).
- **Non-deterministic side effects** (e.g., database connections, external services).

**Fix:**
- **Force deterministic shrinking** (if applicable).
  ```python
  # In Hypothesis (Python), set random_seed for reproducibility
  from hypothesis import given, strategies as st
  import random

  random.seed(42)  # Fix seed for predictable failures

  @given(st.integers(-100, 100), st.lists(st.integers()))
  def test_property(x, lst):
      assert x not in lst or len(lst) > 0
  ```

- **Use logging to trace shrinking steps.**
  ```javascript
  // In Jest with faker (for example)
  test.each([...])("should handle %i", (input) => {
    console.log(`Shrinking input: ${JSON.stringify(input)}`);
    expect(func(input)).toBeValid();
  });
  ```

---

### **3. Performance Bottlenecks (Slow Tests)**
**Symptom:** Tests take hours to complete or time out.

**Root Cause:**
- **Exhaustive generator combinations** (Cartesian product explosion).
- **Heavy property checks** (e.g., running validation on large datasets).
- **Inefficient shrinking** (e.g., shrinking a list of 1M items).

**Fix:**
- **Optimize generators to reduce combinations.**
  ```python
  # Bad: Generates all possible pairs (O(n²))
  generators = st.integers(), st.lists(st.integers())

  # Good: Limits list size early
  small_lists = st.lists(st.integers(), min_size=1, max_size=5)
  @given(st.integers(), small_lists)
  def test_property(x, lst):
      ...
  ```

- **Add timeouts and early termination.**
  ```python
  import hypothesis.strategies as st
  from hypothesis import HealthCheck, settings

  settings.register_profile("fast", max_examples=100, deadline=30000)  # 30s timeout

  @settings(deadline=None)  # Disable timeout temporarily for debugging
  @given(st.integers())
  def test_slow_property(x):
      ...
  ```

---

### **4. Tests Pass Locally but Fail in CI**
**Symptom:** `"Success in dev, failure in CI/CD."`

**Root Cause:**
- **Different random seeds** (if random inputs are involved).
- **Environment differences** (e.g., CI has stricter timeouts).
- **Missing dependencies** (e.g., database not available in CI).

**Fix:**
- **Fix randomness with a deterministic seed.**
  ```bash
  # Set RANDOM_SEED in CI environment
  export RANDOM_SEED=42
  ```

- **Use consistent test configurations in CI.**
  ```yaml
  # GitHub Actions example
  jobs:
    test:
      strategy:
        matrix:
          python-version: ["3.9"]
      steps:
        - run: pip install -r requirements.txt
        - run: pytest --settings=fast  # Use pre-set settings
  ```

---

### **5. Difficulty Reproducing Failing Cases**
**Symptom:** `"Test fails intermittently, but no clear pattern."`

**Root Cause:**
- **Non-deterministic generators.**
- **Shrinking hides the root cause.**

**Fix:**
- **Log failing inputs and shrink manually.**
  ```python
  from hypothesis import Verbosity

  @given(st.integers())
  def test_property(x):
      if not some_predicate(x):
          print(f"Failing input: {x}")
          raise AssertionError
  ```

- **Use a debugger to inspect shrinking steps.**
  ```haskell
  -- In QuickCheck, use `QuickCheck.show` to inspect failing cases
  quickCheckWith stdArgs {maxShrinks = 100} prop_example
  ```

---

## **Debugging Tools and Techniques**

| **Tool**               | **Use Case**                                                                 | **Example**                                                                 |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **`hypothesis.Verbosity` (Python)** | Debug generator behavior step-by-step.                                      | `settings(verbosity=Verbosity.verbose)`                                    |
| **QuickCheck `shrink`** | Manually shrink failing cases in GHCi.                                     | `shrink [1,2,3,4] some_predicate`                                          |
| **Jest Mocking**       | Replace slow generators with mocks.                                         | `jest.mock('some-generator', () => jest.fn(() => { return [1,2,3] }))`       |
| **Logging + Assertions** | Trace test execution flow.                                                   | `console.log('Input:', input); expect(func(input)).toBe(true)`             |
| **CI Artifacts**       | Save failing inputs for later analysis.                                     | `pytest --junitxml=report.xml --log-cli-level=DEBUG`                       |

---

## **Prevention Strategies**

### **1. Write Idempotent Generators**
- Avoid generators with hidden state (e.g., file I/O, DB queries).
- **Example:**
  ```python
  # Bad: Depends on external state
  @dataclass
  class User:
      name: str

  def generate_user() -> User:
      return User(name=fetch_user_name())  # Unreliable!

  # Good: Pure function with controlled inputs
  @given(st.text(), st.integers())
  def generate_user(name: str, id: int) -> User:
      return User(name=name, id=id)
  ```

### **2. Validate Generators Themselves**
- Add **meta-tests** to ensure generators always produce valid inputs.
  ```python
  @given(st.lists(st.integers()))
  def test_generator_valid(lst):
      assert all(isinstance(x, int) for x in lst)  # Verify generator integrity
  ```

### **3. Use Shrinking Wisely**
- **Limit shrinking depth** if the property is complex.
  ```python
  @settings(max_shrinks=50)  # Avoid infinite shrinking
  @given(st.lists(st.integers()))
  def test_property(lst):
      ...
  ```

### **4. Benchmark Generators**
- Profile generators to catch **O(n²)** or **O(n!)** behavior.
  ```bash
  # Use Python's `timeit` for generator performance
  %timeit generate_large_list()
  ```

### **5. Document Constraints Clearly**
- Annotate generators with **minimum/maximum sizes, valid ranges**.
  ```python
  # Example: Documented generator
  ints_in_range = st.integers(min_value=-1000, max_value=1000)
  # Add a comment explaining why this range was chosen
  ```

---

## **Final Checklist for PBT Debugging**
| **Step**                     | **Action**                                                                 |
|------------------------------|----------------------------------------------------------------------------|
| **Reproduce locally**        | Ensure tests fail consistently with a fixed seed.                        |
| **Check shrinking**          | Manually shrink failing cases to isolate the root cause.                  |
| **Log generator inputs**     | Print inputs during test execution.                                       |
| **Optimize generators**      | Reduce combinatorial explosion.                                           |
| **Test in CI**               | Verify behavior matches local environment.                                |
| **Document assumptions**     | Clarify edge cases and constraints in code comments.                     |

---

## **Conclusion**
Property-Based Testing is powerful but requires careful handling. By following this guide, you can:
✅ **Debug failing generators** with logging and shrinking.
✅ **Optimize performance** by limiting test scope.
✅ **Reproduce issues** consistently in CI/CD.
✅ **Prevent future problems** with idempotent, validated generators.

**Next Steps:**
- Start with **log generators** for unclear failures.
- Use **deterministic seeds** to avoid randomness issues.
- **Profile slow tests** to find bottlenecks.

If PBT remains unstable, consider **hybrid testing** (combine PBT with deterministic test cases) for critical paths.