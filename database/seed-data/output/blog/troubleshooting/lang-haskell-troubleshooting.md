# **Debugging Haskell Best Practices: A Troubleshooting Guide**

Haskell’s pure functional nature, strong type system, and lazy evaluation provide powerful abstractions—but they also introduce unique debugging challenges. This guide focuses on **common performance, reliability, and scalability issues** when working with Haskell best practices, offering **practical fixes, debugging techniques, and prevention strategies**.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if these symptoms match your issue:

| **Symptom**                          | **Possible Causes**                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------------|
| **Performance Issues**                | Inefficient algorithms, excessive thunking, unbounded recursion, lazy evaluation pitfalls |
| **Reliability Bugs**                  | Incorrect monad usage, type mismatches, infinite loops, diverging computations       |
| **Scalability Problems**              | Poor memory locality, high GC overhead, inefficient data structures, N+1 queries       |
| **Type Errors**                       | Overuse of wildcard types (`_`), incorrect phantom types, unsafe coercions          |
| **Slow Build Times**                  | Inefficient GHC phase dependencies, excessive `template-haskell` usage              |
| **Concurrency/Parallelism Failures**  | Deadlocks, incorrect `STM` usage, thread starvation, race conditions                  |

If you see multiple symptoms, start with **performance bottlenecks** (they often cause cascading issues).

---

## **2. Common Issues and Fixes**

### **A. Performance Issues**
#### **1. Unbounded Recursion → Stack Overflow**
   - **Symptom:** Program crashes with `stack overflow` or `Segmentation fault`.
   - **Cause:** Tail recursion not enforced (Haskell is not optimized for unbounded recursion like some imperative languages).
   - **Fix:** Convert recursion to **truly tail-recursive** or use **trampolining** (e.g., `Data.Sequence` with `foldl'`).

   ```haskell
   -- ❌ Unbounded recursion (crashes)
   sumList []     = 0
   sumList (x:xs) = x + sumList xs  -- No tail recursion!

   -- ✅ Fixed (tail-recursive)
   sumList xs = go 0 xs
     where go acc []     = acc
           go acc (x:xs) = go (acc + x) xs
   ```

#### **2. Excessive Thunking → Memory Bloat**
   - **Symptom:** High memory usage with `thunks` (`GC alloc'd`, `promoted alloc'd`).
   - **Cause:** Lazy evaluation creates unnecessary intermediate values.
   - **Fix:**
     - Use **strict data structures** (`Data.Vector`, `ByteString`).
     - Force computation with `seq` or `deepseq`.
     - Avoid `IO` in pure contexts (use `ST` or `TMVar` instead).

   ```haskell
   -- ❌ Lazy list (creates thunks)
   xs = [1..1000000]

   -- ✅ Strict version (avoids thunking)
   import Data.Vector (Vector)
   import qualified Data.Vector as V

   xs = V.fromList [1..1000000]  -- Allocates once, no thunks
   ```

#### **3. Lazy Evaluation Pitfalls → Infinite Computations**
   - **Symptom:** Program hangs or never terminates.
   - **Cause:** Circular references, infinite `do`-notations, or lazy dependencies.
   - **Fix:**
     - Use `seq` to force evaluation.
     - Avoid `do` notation in pure functions (prefer `Applicative` or `Monad` explicitly).
     - Add `noinline` pragma for critical functions.

   ```haskell
   -- ❌ Infinite loop due to lazy evaluation
   x = x + 1  -- Diverges (if x is defined elsewhere)

   -- ✅ Force evaluation with seq
   x = x `seq` x + 1  -- Evaluates before addition
   ```

---

### **B. Reliability Problems**
#### **4. Monad Misuse → Implicit Side Effects**
   - **Symptom:** Unexpected behavior due to monad stack pollution (`IO` in pure code, `State` leaks).
   - **Cause:** Overusing `Monad` combinators without isolation.
   - **Fix:**
     - Use `Applicative` for pure transformations.
     - Explicitly lift `IO` with `liftIO` when needed.
     - Prefer `Reader` over `State` for configuration.

   ```haskell
   -- ❌ Polluting monad stack
   -- getUser :: IO User
   -- getUser' = do
   --   u <- getUser
   --   log u  -- Mixes IO with pure logic

   -- ✅ Isolated monad usage
   getUser' :: IO User
   getUser' = liftIO getUser >>= log
   ```

#### **5. Type Errors → Phantom Types or Wildcards**
   - **Symptom:** `Couldn't match expected type` or `Wildcard in type signature`.
   - **Cause:** Poor type safety, overuse of `_`, or missing phantom types.
   - **Fix:**
     - **Replace wildcards** with explicit types.
     - **Add phantom types** for safer data structures.

   ```haskell
   -- ❌ Wildcard abuse
   process :: _ -> IO ()
   process x = ...  -- No type safety!

   -- ✅ Better typing
   process :: String -> IO ()
   process x = ...  -- Clear signature
   ```

#### **6. Infinite (`foldr`, `mapM`) → Stack Overflow**
   - **Symptom:** Works on small inputs but crashes on large ones.
   - **Cause:** Lazy `foldr` or `mapM` without accumulator optimization.
   - **Fix:** Use `foldr'` (from `Data.List`) or `mapAccumL`.

   ```haskell
   -- ❌ Fails on large lists (stack overflow)
   sumList = foldr (+) 0 [1..10000000]

   -- ✅ Fixed (strict fold)
   import Data.List (foldr')
   sumList = foldr' (+) 0 [1..10000000]
   ```

---

### **C. Scalability Issues**
#### **7. High GC Overhead → Slow Performance**
   - **Symptom:** Program spends 90%+ time in garbage collection.
   - **Cause:** Allocating too many thunks, poor data structure choices.
   - **Fix:**
     - Use **immutable `Vector`** instead of lists.
     - Preallocate memory with `newArray`/`unsafeDupablePerformIO`.
     - Tune GHC with `-O2 -fno-strict -threaded`.

   ```haskell
   -- ❌ Lazy list (high GC)
   bigList = [1..10000000]

   -- ✅ Strict Vector (low GC)
   import Data.Vector (Vector)
   import qualified Data.Vector as V
   bigVec = V.replicate 10000000 1  -- Efficient allocation
   ```

#### **8. N+1 Queries → Database Bottlenecks**
   - **Symptom:** Slow database queries due to inefficient fetching.
   - **Cause:** Fetching records one by one in loops.
   - **Fix:** Use **batch loading** with `Data.Map` or `Data.Vector`.

   ```haskell
   -- ❌ N+1 queries (slow)
   users = mapM getUserById [1..1000]

   -- ✅ Batch loading (fast)
   batchLoadUsers = do
     ids <- getAllIds
     users <- mapM getUserById ids  -- Still bad; better:
     users <- getUsersBatch ids     -- Assume this fetches in one query
   ```

---

## **3. Debugging Tools and Techniques**

### **A. Compilation & Profiling**
| **Tool**               | **Usage**                                                                 |
|-------------------------|---------------------------------------------------------------------------|
| `ghc --make -O2`        | Force optimization to catch inefficiencies.                              |
| `ghc -ddump-simpl`      | Inspect core code for optimization issues.                               |
| `criterion`             | Benchmark functions to find bottlenecks.                                  |
| `hp2ps` + `ghc --prof`  | Generate heap profiling reports (`-rtsopts -t`).                           |
| `scrapelog`             | Parse GHC runtime logs for memory leaks.                                  |

**Example profiling workflow:**
```bash
ghc -O2 -prof -fprof-auto -rtsopts -with-rtsopts="-hc" MyApp.hs
./MyApp +RTS -hc
hp2ps *.hp
```

### **B. Debugging Lazy Evaluation**
- **`seq` for strictness:** Force evaluation at compile time.
- **`deepseq` for `NFData`:** Ensure deep evaluation (`import Data DeepSeq`).
- **`stderr` logging:** Add `putStrLn` in `IO` to track thunk creation.

```haskell
import Data DeepSeq (deepseq)
import Control.DeepSeq (NFData)

-- Force evaluation of a list
myList `deepseq` result
```

### **C. Debugging Monads**
- **`MonadFail`:** Use `fail` for better error messages.
- **`do` notation with `print`:** Trace monadic flows.

```haskell
-- ❌ Silent failure
doSomething :: IO ()
doSomething = do
  x <- getX
  unless (valid x) $ fail "Invalid x"

-- ✅ Debugging-friendly
doSomething :: IO ()
doSomething = do
  x <- getX
  unless (valid x) $ error $ "Invalid x: " ++ show x
```

### **D. Debugging Concurrency**
- **`traceShow` + `STM`:** Debug atomic actions.
- **`STM` retries:** Handle deadlocks with `retry`.
- **`async` + callbacks:** Avoid thread starvation.

```haskell
-- Debug STM with trace
atomicOp = atomically $ do
  traceShow ("Attempting op on " ++ show x) x
  modifyTVar var (x + 1)
```

---

## **4. Prevention Strategies**

### **A. Coding Best Practices**
| **Practice**                          | **Why?**                                                                 |
|----------------------------------------|-------------------------------------------------------------------------|
| **Prefer `Applicative` over `Monad`** | Avoids monad stacking issues.                                           |
| **Use `Vector` instead of lists**     | Better memory locality, strict by default.                               |
| **Add strictness annotations (`Bang`)** | Forces evaluation where needed.                                          |
| **Avoid `let` in recursive positions** | Can create thunks prematurely.                                           |
| **Use `lens`/`optics` for state**     | Safer than manual `State` monad usage.                                   |

### **B. Testing & Validation**
- **Property-based testing (`QuickCheck`)**:
  ```haskell
  import Test.QuickCheck
  prop_length_equals_sum (a:as) = length [a,as] == 1 + length as
  ```
- **Property-based `Vector` testing**:
  ```haskell
  import Test.QuickCheck
  import qualified Data.Vector as V
  prop_vector_cons (a:as) = V.fromList (a:as) == V.cons a (V.fromList as)
  ```
- **Benchmarking (`criterion`)**:
  ```haskell
  import Criterion.Main
  main = defaultMain [
    bgroup "List vs Vector"
      [ bench "sumList" $ nf sum [1..1000000]
      , bench "sumVector" $ nf (V.sum . V.fromList) [1..1000000]
      ]
    ]
  ```

### **C. Architecture Patterns**
- **Modular monads:** Isolate `IO`, `State`, and `Reader` concerns.
- **Free monad transformers:** Compose effects cleanly (`FreeT`).
- **Avoid `IO` in pure functions:** Use `ST` or `STM` for side-effect-free code.

**Example modular monad:**
```haskell
import Control.Monad.Trans.Class (lift)
import Control.Monad.Reader (ask)

type AppM a = ReaderT Config (ExceptT Error IO) a

-- Safe IO lifting
getConfig :: AppM Config
getConfig = ask
```

---

## **5. Quick Fix Cheat Sheet**
| **Issue**               | **Quick Fix**                                      |
|--------------------------|----------------------------------------------------|
| Stack overflow           | Use `foldr'` or trampolining (`Data.Sequence`).     |
| High memory usage        | Replace lists with `Vector` or `ByteString`.       |
| Lazy evaluation pitfalls | Use `seq` or `deepseq`.                            |
| Monad pollution          | Isolate effects with `Reader`/`Writer`.            |
| Slow database queries    | Use batch loading (`Data.Map`).                     |
| Infinite loops           | Add `noinline` pragma or force evaluation.        |
| Type errors              | Replace wildcards (`_`) with explicit types.       |

---

## **6. Final Checklist for Productions Code**
Before deploying:
✅ [ ] **Profile with `criterion`** (benchmark critical paths).
✅ [ ] **Check heap usage** (`hp2ps`).
✅ **Avoid lazy infinite structures** (lists, `Maybe` in loops).
✅ **Use `Data.Vector` for large data**.
✅ **Isolate monads** (no `IO` in pure functions).
✅ **Add `BangPatterns`** where strictness is needed.
✅ **Test edge cases** (`QuickCheck` properties).

---

## **Conclusion**
Haskell’s strengths (purity, laziness, monads) can also be its biggest debugging challenges. By **profiling early**, **avoiding unbounded computations**, and **enforcing strictness where needed**, you can write **high-performance, reliable, and scalable** Haskell code.

**Key Takeaways:**
1. **Profile first** (`criterion`, `hp2ps`).
2. **Prefer strictness** (`Vector`, `BangPatterns`).
3. **Isolate monads** (don’t mix `IO` with pure logic).
4. **Test rigorously** (`QuickCheck`, property-based tests).

If you follow these guidelines, you’ll **minimize debugging time** and **write robust Haskell systems**. Happy coding! 🚀