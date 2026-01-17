---
**[Pattern] Reference Guide: Property-Based Testing (PBT)**

---

## **Overview**
Property-Based Testing (PBT) is a **test generation** paradigm where tests derive inputs from a **distribution or generator** rather than hard-coded values. Unlike traditional unit tests, PBT focuses on verifying *properties* (invariants, pre/post-conditions, or business rules) across a **randomized input spectrum**. By validating a property against **numerous generated cases**, PBT increases test coverage and detects edge cases more efficiently.

PBT frameworks (e.g., QuickCheck, Hypothesis, FsCheck) automate test case creation with statistical validation, reducing manual input curation. Common use cases include validating data transformations, state machines, or mathematical algorithms where exhaustive testing is infeasible.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Generator**          | A function that produces random inputs satisfying a predefined distribution (e.g., integers in `[1, 100]`).                                                                                        | `Gen.int(min=1, max=100)` generates a random integer between 1 and 100.                          |
| **Shrinking**          | Automatically reducing complex inputs to their minimal failing case to isolate bug triggers.                                                                                           | A failing test for `fibonacci(200)` shrinks to `fibonacci(23)`.                                  |
| **Law**               | A declarative property to test (e.g., "the sum of two numbers is commutative").                                                                                                                 | `fun commutative(a, b) = plus(a, b) == plus(b, a)` (Haskell-like pseudocode).               |
| **Property**          | The assertion itself—combining generator, law, and validation logic.                                                                                                                                 | `property("Padded length is constant") { input -> padded(input).length == 32 }`         |
| **Seed**              | A deterministic value to reproduce a specific test case or failure.                                                                                                                               | `--seed=12345` reruns a test with the same random inputs.                                        |
| **Distribution**      | How generators sample input data (uniform, normal, biased).                                                                                                                                         | `Gen.choice(['a', 'b', 'cc'])` prioritizes shorter strings.                                      |
| **Filter**            | Constrains generator outputs to specific criteria (e.g., "only even numbers").                                                                                                                 | `Gen.filter(x => x % 2 == 0, Gen.int())` generates only evens.                                  |
| **Timeout**           | Stops a test after `N` iterations or time `T` if no failure is found.                                                                                                                              | `--timeout=100` runs a test for 100ms max.                                                     |

---

## **Implementation Schema**
Below is a **template** for defining a PBT property in common frameworks. Replace `<framework>` with `QuickCheck`/`Hypothesis`/`FsCheck` syntax as needed.

| **Component**         | **Description**                                                                                                                                                                               | **Example (Pseudocode)**                                                                       |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Generator (`Gen`)** | Input data source. Can be combined/composed (e.g., `Gen.tuple`, `Gen.listOf`).                                                                                                       | `genInput = Gen.tuple(Gen.int(-100, 100), Gen.string())` (tuple of int and string).          |
| **Law (Property)**    | The assertion logic. Should be **pure** (no side effects).                                                                                                                               | `fun isEven(x) = x % 2 == 0` (validates `x` is even).                                           |
| **Orchestrator**      | Framework-specific boilerplate to run the test.                                                                                                                                            | `forAll(genInput) { (a, b) => isEven(a + b) /* should hold */ }`                               |
| **Options**           | Configures runs (e.g., `maxTest=1000`, `shrinkSteps=10`).                                                                                                                              | `quickCheck { maxSuccess = 500; shrinkSteps = 5 } { prop }`                                     |

---

### **Schema Variations by Framework**
| **Framework** | **Property Syntax**                                                                                          | **Key Options**                                                                               |
|----------------|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **QuickCheck** | `QuickCheck.property { gen => law(gen) }`                                                                  | `maxSuccess`, `tests`, `shrink`, `size`                                                      |
| **Hypothesis** | `@property` decorator with generator + assertion (Python).                                                   | `max_examples`, `shrinkers`, `deadline`                                                     |
| **FsCheck**    | `prop "Name" <|> Gen.input → Fun.invariant (fun x → law x)` (F#).                                                        | `Test.Quick.testConfig`, `arbitrary`, `shrink`                                                |

---

## **Query Examples**
### **1. Basic Property: Commutative Addition**
**Goal**: Verify `(a + b) == (b + a)` for random integers.
**Implementation**:
```python
# Hypothesis (Python)
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_commutative_addition(a, b):
    assert a + b == b + a
```

```haskell
-- QuickCheck (Haskell)
import Test.QuickCheck

prop_commutative_addition :: Int -> Int -> Bool
prop_commutative_addition a b = (a + b) == (b + a)

main = quickCheck prop_commutative_addition
```

**Key**:
- Uses `st.integers()` (Hypothesis) or `Gen.int` (QuickCheck) for random inputs.
- No explicit test cases; **100+ random pairs** are tested automatically.

---

### **2. Property with Constraints**
**Goal**: Validate `strpad(str, length)` always returns a string of exact `length`, padding with `'*'`.
**Implementation**:
```python
# Hypothesis
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=10), st.integers(min_value=1, max_value=20))
def test_padded_length(str, target_len):
    padded = strpad(str, target_len)
    assert len(padded) == target_len
    assert all(c == '*' or c in str for c in padded)
```

**Key**:
- `min_size/max_size` constraints filter generators.
- Shrinking helps identify minimal failing `str`/`target_len` pairs.

---

### **3. Complex Composition: Lists and Sums**
**Goal**: Ensure the sum of a list equals the sum of its reverse.
**Implementation**:
```javascript
// Example with FsCheck (F#)
open FsCheck

let prop_sum_equals_reverse_sum (lst: int list) =
    let sumLst = List.sum lst
    let sumRev = List.sum (List.rev lst)
    sumLst = sumRev

[<Tests>]
let tests =
    test <@ prop_sum_equals_reverse_sum @>
```

**Key**:
- Uses `List.rev` and `List.sum` to test property across all permutations.
- Automatically tests edge cases (empty list, single-element list).

---

### **4. Property with Side Effects (Advanced)**
**Goal**: Validate a stateful system (e.g., a queue) after `N` operations.
**Implementation**:
```python
# Hypothesis (Python) with queue simulation
from hypothesis import given, strategies as st
from queue import Queue

@given(st.integers(min_value=1, max_value=100))
def test_queue_invariants(n_operations):
    q = Queue()
    for _ in range(n_operations):
        if st.booleans().example:
            q.put(st.integers().example())
        else:
            q.get()
    assert q.qsize() >= 0  # Non-negative size invariant
```

**Key**:
- Combines random operations (push/pop) with assertions.
- **Warning**: Side-effect-heavy properties require care to avoid flakiness.

---

## **Query Examples: Edge Cases**
| **Scenario**               | **Goal**                                                                                     | **Implementation Hint**                                                                       |
|----------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Integer Overflow**       | Verify no overflow in `a * b` for large `a`, `b`.                                           | Use `st.integers(min_value=Math.pow(2, 30))` (Hypothesis).                                   |
| **Empty Inputs**           | Ensure functions handle empty lists/strings gracefully.                                     | Add `st.none()` or `st.text(min_size=0)`.                                                    |
| **Floating-Point Precision**| Test rounding/equality with floating-point math.                                           | Use `hypothesis.strategies.floats(min_value=-1e9, max_value=1e9, allow_nan=False)`.            |
| **Custom Distributions**   | Bias tests toward "real-world" input patterns (e.g., 80% valid, 20% malformed).             | Chain generators: `Gen.frequency([(80, valid_input), (20, malformed_input)])`.              |

---

## **Best Practices**
1. **Focus on Properties, Not Test Cases**:
   - Define *what* to test (e.g., "all operations are commutative") rather than *how*.
   - Example: Test `sort(x)` is stable **for any `x`**, not specific `x = [3,1,2]`.

2. **Leverage Shrinking**:
   - If a test fails, shrink inputs to find the **minimal counterexample**.
   - Example: A failing `divide(a, b)` shrinks to `divide(5, 0)`.

3. **Avoid Deterministic Inputs**:
   - Hard-coded values (e.g., `assert divide(10, 2) == 5`) defeat PBT’s purpose.
   - Use generators like `Gen.natural`.

4. **Combine with Traditional Tests**:
   - PBT excels at **coverage**; pair with unit tests for **precision** (e.g., test known edge cases).

5. **Handle Flakiness**:
   - Randomness can cause intermittent failures. Add retries or `st.such_that` to constrain inputs:
     ```python
     @given(st.integers().filter(lambda x: x > 0))
     ```

6. **Document Property Logic**:
   - Clearly state *why* a property matters (e.g., "This ensures thread safety in a queue").

7. **Performance Tuning**:
   - Limit iterations if tests are slow (`max_success=100`).
   - Use `st.binary()` for binary data (e.g., files, buffers).

8. **Framework-Specific Tips**:
   - **QuickCheck**: Use `monad Laws` for algebraic structures (e.g., monoids).
   - **Hypothesis**: `st.recursive()` for nested data (e.g., JSON).
   - **FsCheck**: `Arbitrary` instances for custom types (e.g., `DateTime`).

---

## **Related Patterns**
| **Pattern**                     | **Relationship**                                                                                                                                                     | **When to Pair**                                                                                     |
|----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Unit Testing**                | PBT generates test cases; unit tests provide **precision** for known edge cases.                                                                               | Use PBT for large input spaces; unit tests for critical paths.                                      |
| **Mocking**                     | PBT can mock external dependencies (e.g., random HTTP responses).                                                                                                 | Combine PBT with mocks for **isolation** in distributed systems.                                    |
| **Contract Testing**            | PBT validates API contracts (e.g., "input `X` must return `Y`").                                                                                                 | Test API specs with randomized payloads.                                                             |
| **Chaos Engineering**           | PBT simulates failures (e.g., random timeouts, network drops).                                                                                                   | Validate resilience to **unexpected inputs**.                                                      |
| **Property Invariants**         | PBT tests invariants like "database ACID properties" hold across transactions.                                                                                  | Model invariants as properties (e.g., "no duplicate keys").                                         |
| **Fuzzing**                     | PBT is a form of **generative fuzzing**; fuzzing can use PBT for feedback-driven mutation.                                                          | Use fuzzing for binary code; PBT for high-level invariants.                                        |
| **Mutation Testing**            | PBT can generate mutated inputs to test error handling.                                                                                                         | Validate fault tolerance (e.g., "parse malformed JSON").                                           |

---

## **Anti-Patterns**
| **Anti-Pattern**               | **Risk**                                                                                                                                                           | **Solution**                                                                                         |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Testing Only "Happy Paths"**  | Fails to catch edge cases (e.g., `null` inputs, large numbers).                                                                                                   | Use biased generators or filters to explore edge cases.                                             |
| **Overly Broad Generators**     | Generates invalid inputs that break preconditions (e.g., `divide(a, 0)`).                                                                                     | Add `st.such_that(lambda x: x != 0)` to constrain inputs.                                           |
| **Ignoring Shrinking**          | Minimal counterexamples aren’t found, making bugs harder to debug.                                                                                               | Always enable shrinking (`shrink=True` in Hypothesis).                                                |
| **Purely Random Tests**        | Tests run indefinitely or fail due to noise.                                                                                                                 | Set `max_success` and `timeout` limits.                                                              |
| **Property Coupling**           | Testing two properties in one law (e.g., "add and multiply are commutative") reduces debugging precision.                                                          | Split into separate properties.                                                                     |
| **No Property Documentation**   | Tests are "magic"; unclear why a property matters.                                                                                                           | Document properties as comments or in a separate `README`.                                           |

---
**[End of Reference Guide]**