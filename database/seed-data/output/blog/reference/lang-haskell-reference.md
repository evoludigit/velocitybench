# **[Pattern] Haskell Language Patterns: Reference Guide**

---

## **Overview**
Haskell is a purely functional, statically-typed language known for its elegance, type system, and expressive pattern matching. This guide provides a **structured reference** for Haskell’s **core language patterns**, covering syntax, idiomatic constructs, type system nuances, and best practices. Whether you're defining algebraic data types (ADTs), writing monadic pipelines, or leveraging lazy evaluation, this reference ensures clarity and consistency.

Key topics include:
- **Basic & Advanced Pattern Matching** (data constructors, guards, wildcards)
- **Functional Constructs** (currying, partial application, higher-order functions)
- **Type Classes & Polymorphism** (monads, functors, traversable types)
- **Lazy Evaluation & Performance** (strictness annotations, memoization)
- **Common Pitfalls** (infinite recursion, orphan instances, referential transparency)

---

## **Schema Reference**
Below is a **scannable table** of core Haskell patterns, their **purpose**, **syntax**, and **use cases**.

| **Pattern Type**          | **Purpose**                                                                 | **Syntax**                                                                                     | **Key Considerations**                                                                                     |
|---------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Basic Pattern Matching** | Destructure data types (e.g., `Maybe`, `Either`) or literal values.         | `f Just x = ...; f Nothing = ...`                                                          | Exhaustiveness: Match all constructors or use `_` as a wildcard.                                     |
| **Guarded Patterns**      | Apply conditions to match patterns.                                         | `f [] = 0; f (x:xs) | null xs = 1; f (x:xs) = 2`                                                              | Use `|` for guards; avoid redundant checks.                                                          |
| **As-Patterns**           | Bind sub-patterns to variables (e.g., destructure nested tuples).           | `(x, (y, z)) -> ...` or `Just (x : xs) -> ...`                                                | Useful for extracting intermediate values.                                                          |
| **Lazy Patterns**         | Delay evaluation of large/thunked data.                                     | `_ ~(x : _) -> ...` (matches head but thunks tail)                                           | Prevents unnecessary computation; risky with unbounded data (e.g., `repeat`).                          |
| **Type Application**      | Constrain type variables with explicit types.                              | `length :: forall a. [a] -> Int` → `length @Int`                                             | Rarely needed; use when type inference fails.                                                        |
| **Do-Notation (Monads)**  | Write monadic code as imperative-like steps.                               | `do { x <- getLine; putStrLn x }`                                                            | Under the hood: `>>=` and `return`; avoid side effects in pure monads.                              |
| **List Comprehensions**   | Filter/map/fold lists concisely.                                           | `[x^2 | x <- [1..5], even x]`                                                                     | Equivalent to `map` + `filter`; less efficient than pure functions for large data.                   |
| **Case Expressions**      | Alternative to pattern matching in guards/expressions.                     | `case expr of { Just x -> x; Nothing -> 0 }`                                                  | Cleaner for complex nested matches.                                                                |
| **Recursive Types**       | Define mutually recursive data types (e.g., `data Expr = Var String | App Expr Expr`). | `data Expr = Var String | App Expr Expr`                                                                     | Requires `Foldable`/`Traversable` for practical use; risk of stack overflow.                     |
| **Type Classes**          | Define polymorphic behavior (e.g., `Eq`, `Show`, `Functor`).               | `class Eq a where (==) :: a -> a -> Bool`                                                    | Orphan instances should be avoided; prefer `Default`/`Generic` where possible.                      |
| **Monad Transformers**    | Stack monads for combined effects (e.g., `EitherT` + `StateT`).            | `import Control.Monad.Trans`; `runStateT (do { ... }) state`                                | Careful with transformation order (e.g., `StateT` before `MaybeT`).                                    |
| **View Patterns**         | Extract parts of data without consuming it (GHC extension).                 | `case x of { (a, b, _) -> ... }`                                                               | Use for peeking into thunked data (e.g., `(:)` tuples); enables lazy analysis.                        |
| **Strict Patterns**       | Force evaluation of subexpressions (GHC extension).                          | `data Strict a = Strict !a`                                                                   | Use sparingly; breaks lazy semantics for performance-critical paths.                                  |
| **Record Patterns**       | Destructure record fields by name.                                          | `{ name = n, age = a } -> ...`                                                              | Cleaner than positional matching for nested records.                                                 |
| **Type Families**         | Define type synonyms or rewrite types based on arguments.                    | `type instance Show (Array i e) = Show e`                                                     | Advanced; use for opaque type aliases or indexed types.                                               |

---

## **Query Examples**

### **1. Basic Pattern Matching (Destruction)**
**Use Case:** Handle `Maybe` values safely.
```haskell
safeDivide :: Float -> Maybe Float -> Maybe Float
safeDivide _ Nothing  = Nothing
safeDivide x (Just y) = Just (x / y)
```
- **Key:** Exhaustive matching on `Maybe` constructors.
- **Pitfall:** Forgetting the `Nothing` case (GHC warns with `-Wmissing-patterns`).

---

### **2. Guarded Patterns (Conditional Matching)**
**Use Case:** Apply business rules to lists.
```haskell
processLogs :: [String] -> [String]
processLogs []       = []
processLogs (h:t)    | null h    = processLogs t  -- Skip empty lines
                     | otherwise = h : processLogs t
```
- **Key:** Guards (`|`) enable arbitrary conditions.
- **Best Practice:** Combine with pattern matching for clarity.

---

### **3. Lazy Patterns (Thunk Management)**
**Use Case:** Stream large files without loading into memory.
```haskell
chunkLines :: String -> [[Char]]
chunkLines = take 1000 . lines  -- Thunks the entire input
-- Safer alternative:
chunkLinesSafe :: String -> [[Char]]
chunkLinesSafe s = case drop 1000 s of
                     _ ~(_, rest) -> lines rest  -- Matches head but thunks rest
                     _            -> []          -- Fallback (unlikely for finite strings)
```
- **Key:** `~` forces matching but delays evaluation of the tail.
- **Pitfall:** Infinite recursion if `s` is infinite (e.g., `cycle "x"`).

---

### **4. Monad Transformers (Combining Effects)**
**Use Case:** Add error handling to a stateful program.
```haskell
import Control.Monad.Trans.State
import Control.Monad.Trans.Except

type GameState = Int
type GameM a = ExceptT String (StateT GameState IO) a

increment :: GameM ()
increment = do
  modify (+1)
  liftIO $ putStrLn "Incremented!"
```
- **Key:** `ExceptT` wraps `StateT`; `>>=` chains operations.
- **Pitfall:** Nesting transformers increases boilerplate (use `transformers` library).

---

### **5. View Patterns (Lazy Analysis)**
**Use Case:** Peek into a thunked list without consuming it.
```haskell
-- GHC extension: {-# LANGUAGE ViewPatterns #-}
safeHead :: [a] -> Maybe a
safeHead (view (_:xs)) = Just _  -- Matches head but thunks tail
safeHead _             = Nothing
```
- **Key:** Views avoid forcing evaluation prematurely.
- **Best Practice:** Use for debugging or lazy traversal.

---

### **6. Type Classes (Polymorphic Behavior)**
**Use Case:** Define custom `Show` for custom types.
```haskell
data Person = Person String Int deriving (Eq)

instance Show Person where
  show (Person name age) = name ++ " (" ++ show age ++ ")"
```
- **Key:** Derive `Eq` automatically; define `Show` manually.
- **Pitfall:** Orphan instances can break module compatibility.

---

## **Best Practices & Pitfalls**

### **✅ Do:**
- **Use `Eq`/`Ord` exhaustively**: Derive where possible; manually define for complex types.
- **Prefer ` Pure Functions`**: Avoid side effects in core logic (use `IO` only where necessary).
- **Leverage `TypeApplications`**: Disambiguate ambiguous types (e.g., `length @Int`).
- **Document `orphan` instances**: Explain why they’re needed (e.g., `instance Show (MyLib.Type)`).
- **Use `ViewPatterns` judiciously**: For lazy analysis, not performance-critical code.

### **❌ Avoid:**
- **Unbounded recursion**: Lazy evaluation can lead to stack overflows (e.g., `tail [1..]`).
- **Overusing `MonadTransformer` stacks**: Prefer `IO`-based monads for side effects.
- **Ignoring warnings**: `-Wmissing-patterns`, `-Wincomplete-patterns` catch bugs early.
- **Mixing strict/lazy semantics**: Force evaluation only when necessary.
- **Orphan instances without reason**: Prefer `Generic` or `Default` where possible.

---

## **Related Patterns**
For deeper exploration, see:
1. **[Monadic Pipelines]** – Chaining monadic actions with `>>=` and `do`-notation.
2. **[Pure Functional Data Processing]** – Using `foldr`, `map`, and `filter` for transformations.
3. **[Lazy vs. Strict Evaluation]** – Trade-offs between thunking and strictness.
4. **[Type-Level Programming]** – Advanced type-safe abstractions with `TypeFamilies`/`GADTs`.
5. **[Dependency Injection with `Reader` Monad]** – Managing configuration in pure code.

---
**Further Reading:**
- [Haskell Wiki: Patterns](https://wiki.haskell.org/Pattern_matching)
- [Real World Haskell: Patterns](http://book.realworldhaskell.org/read/using-patterns.html)
- [GHC User Guide: Extensions](https://downloads.haskell.org/~ghc/latest/docs/html/users_guide/extns.html)