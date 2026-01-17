# **Debugging Recursive Type Definitions: A Troubleshooting Guide**
*(For TypeScript, Rust, Haskell, or similar languages with recursive types)*

---

## **1. Introduction**
Recursive type definitions allow types to reference themselves, enabling modeling of nested structures (e.g., trees, linked lists). While powerful, they can cause:
- **Infinite expansion** (compiler crashes or runtime errors).
- **Performance bottlenecks** (excessive type-checking overhead).
- **Memory leaks** (in languages like Rust with large recursion).

This guide focuses on **practical debugging** for recursive types in **TypeScript, Rust, and Haskell**, with solutions for common pitfalls.

---

## **2. Symptom Checklist**
| **Symptom**                          | **Possible Cause**                          | **Language-Specific Indicator** |
|--------------------------------------|--------------------------------------------|---------------------------------|
| Compiler crashes with "stuck in recursion" | Infinite type expansion | TypeScript/Rust: `maxRecursionDepth` error |
| Slow compilation/long build times   | Deep recursion in type inference          | Haskell: `Tidal wave of size`    |
| Runtime errors (e.g., `NotImplementedError`) | Unbounded recursive instantiation | Rust: `recursion depth exceeded` |
| Type errors like "expected type, got recursive type" | Invalid recursion termination | TypeScript: `Type 'T' does not satisfy itself` |
| Memory exhaustion during macro expansion | Unbounded macro recursion (Rust) | Rust: `stack overflow` |

**Quick Check:**
- Does the issue occur with **shallow recursion** (e.g., `type T = A | B` vs. `type T = A | T`)?
- Are you using recursive types in **interfaces/objects** or just **algebraic data types**?

---

## **3. Common Issues and Fixes**
### **A. TypeScript: Infinite Expansion**
#### **Symptom:**
```ts
type Tree = { value: string; children: Tree[] };
// Compiler hangs or crashes with "Max call stack exceeded."
```

#### **Root Cause:**
TypeScript’s type checker may expand recursion infinitely during validation. This happens when:
- Recursive types are **not effectively finite** (e.g., `type T = T[]`).
- **Generic types** with unbounded recursion (e.g., `type Recursive<T> = { data: T | Recursive<T> }`).

#### **Fixes:**
1. **Use `never` as a termination condition** (for asymmetric recursion):
   ```ts
   type Tree = { value: string; children?: Tree[] | never };
   ```
   - `never` forces the compiler to treat `children` as optional.

2. **Restrict recursion depth explicitly**:
   ```ts
   type Tree<Depth extends number = 3> =
     Depth extends 0 ?
       { value: string; children: never[] } :
       { value: string; children: Tree<Depth extends 0 ? never : Depth - 1>[] };
   ```
   - Limits recursion to 3 levels.

3. **Use `unknown` or `any` (last resort)**:
   ```ts
   type Tree = { value: string; children: Tree[] | any[] };
   ```
   - Disables type checking for `children` (use sparingly).

4. **Split into distinct types for each depth**:
   ```ts
   type Leaf = { value: string; children: never[] };
   type Node = { value: string; children: Tree[] };
   type Tree = Leaf | Node;
   ```

---

#### **Symptom:**
```rust
struct Node<T> {
    data: T,
    children: Vec<Node<T>>,
}
```
#### **Root Cause:**
Rust’s monomorphization (codegen) fails with deep recursion due to:
- **Stack overflow** during type inference.
- **Unbounded trait bounds** (e.g., if `T` implements a recursive trait).

#### **Fixes:**
1. **Use `Box<Self>` for heap allocation**:
   ```rust
   struct Node<T> {
       data: T,
       children: Vec<Box<Node<T>>>,
   }
   ```
   - Avoids stack overflow by moving nodes to the heap.

2. **Add recursion limits via generics**:
   ```rust
   struct Node<T, const N: usize> {
       data: T,
       children: [Option<Node<T, N>>; N], // Fixed-size array
   }
   ```
   - Forces a maximum depth at compile time.

3. **Lazy evaluation with `Option`**:
   ```rust
   struct Node<T> {
       data: T,
       children: Vec<Option<Box<Node<T>>>>,
   }
   ```
   - Uses `Option` to terminate recursion.

4. **Separate leaf and internal nodes**:
   ```rust
   enum Node<T> {
       Leaf { data: T },
       Inner { data: T, children: Vec<Node<T>> },
   }
   ```

---

### **C. Haskell: Non-Terminating Types**
#### **Symptom:**
```haskell
data Tree a = Node a [Tree a]  deriving (Show)
-- GHC hangs with "Tidal wave of size 1000000000..."
```

#### **Root Cause:**
Haskell’s type system cannot prove termination for **symmetric recursion** (e.g., `Tree a = Node a [Tree a]`). The compiler assumes worst-case unbounded expansion.

#### **Fixes:**
1. **Use `Maybe` or `Either` for termination**:
   ```haskell
   data Tree a = Leaf a | Node a [Tree a] deriving (Show)
   ```
   - `Leaf` acts as a base case.

2. **Add size annotations (GHC extensions)**:
   ```haskell
   {-# LANGUAGE GADTs #-}
   data Tree a size where
       Leaf :: a -> Tree a size
       Node :: a -> [Tree a (size - 1)] -> Tree a size
   ```
   - Forces a depth limit.

3. **Use `Data.List.NonEmpty` for homogeneous lists**:
   ```haskell
   import Data.List.NonEmpty (NonEmpty)
   data Tree a = Node a (NonEmpty (Tree a))
   ```
   - `NonEmpty` ensures at least one child (simpler termination).

4. **Split into distinct constructors**:
   ```haskell
   data Tree a = Empty | Cons a (Tree a) Tree a  -- Binary tree
   ```

---

## **4. Debugging Tools and Techniques**
### **A. TypeScript**
1. **Enable `--strict` and `--traceResolution`**:
   ```bash
   tsc --strict --traceResolution > typecheck.log
   ```
   - Logs recursion details in `typecheck.log`.

2. **Use `unknown` or `any` strategically**:
   ```ts
   type Recursive<T> = { data: T | unknown };
   ```
   - Isolates problematic recursion.

3. **Test with `typeof` in runtime code**:
   ```ts
   type Test<T> = T extends Recursive<infer U> ? U : T;
   ```
   - Helps identify recursive types at runtime.

### **B. Rust**
1. **Compile with `-Zunstable-options` and `--bin`**:
   ```bash
   rustc --edition 2021 --explain my_code.rs
   ```
   - Rust’s `--explain` flag often points to recursion depth issues.

2. **Use `assert!` to validate recursion depth**:
   ```rust
   fn validate_depth<T>(node: &Node<T>, max_depth: usize) -> bool {
       if max_depth == 0 { return false; }
       node.children.iter().all(|child| validate_depth(child, max_depth - 1))
   }
   ```

3. **Profiling with `perf` or `valgrind`**:
   - Check for stack overflows during macro expansion.

### **C. Haskell**
1. **Enable `-ddump-simpl` for type expansion**:
   ```bash
   ghc -ddump-simpl -ddump-to-file -ddump-simpl-log YourModule.hs
   ```
   - Shows how GHC expands recursive types.

2. **Use `TypeApplications` and `ScopedTypeVariables`**:
   ```haskell
   {-# LANGUAGE TypeApplications #-}
   {-# LANGUAGE ScopedTypeVariables #-}
   ```
   - Helps debug generic recursion.

3. **Test with `Data.Size` (from `size-classes`)**:
   ```haskell
   import Data.Size.Class
   data Tree a where
       Leaf :: a -> Size 1 (Tree a)
       Node :: a -> [Tree a] -> Size (1 + Sum (Size (Tree a))) (Tree a)
   ```

---

## **5. Prevention Strategies**
### **A. Design Principles**
1. **Favor asymmetric recursion**:
   - Use `Option`, `Maybe`, or `Either` to terminate recursion.
   - Example: `type List a = Nil | Cons a (List a)` (Haskell) instead of symmetric variants.

2. **Limit recursion depth**:
   - Add generics with `const` bounds (Rust) or size annotations (Haskell).
   - Example (Rust):
     ```rust
     struct Tree<T, const MAX_DEPTH: usize> { ... }
     ```

3. **Use phantom types for bounded recursion**:
   - Example (Rust):
     ```rust
     struct BoundedTree<T, const N: usize> {
         depth: std::marker::PhantomData<(N, T)>,
     }
     ```

### **B. Language-Specific Tips**
| **Language** | **Best Practice**                          | **Example**                                  |
|--------------|--------------------------------------------|---------------------------------------------|
| TypeScript   | Prefer `unknown` over `any` for recursion  | `type Node = { data: unknown; children?: Node[] }` |
| Rust         | Use `Box<Self>` or `Rc<RefCell<Self>>`      | `type Tree = Box<Node>;`                     |
| Haskell      | Use `GADTs` with size annotations         | `-XGADTs -XTypeApplications`                 |

### **C. Refactoring Checklist**
1. **Replace infinite recursion with iterative patterns**:
   - Convert trees to **trie-like structures** or **linked lists with explicit terminators**.
   - Example (TypeScript):
     ```ts
     type List<T> = { head: T; tail: List<T> } | { done: true };
     ```

2. **Use lazy evaluation (Haskell)**:
   ```haskell
   data LazyTree a = Node a [LazyTree a]  deriving (Functor, Foldable)
   ```

3. **Separate type-level and value-level recursion**:
   - Example (Rust):
     ```rust
     // Type-level recursion (compile-time)
     trait RecursiveDepth {}
     impl<T> RecursiveDepth for T where T: RecursiveDepth + Default {}

     // Value-level recursion (runtime)
     struct Node<T> { data: T, children: Vec<Node<T>> }
     ```

---

## **6. Example: Debugging a Failing Binary Tree in TypeScript**
### **Problem:**
```ts
type BinaryTree = {
  value: number;
  left: BinaryTree | null;
  right: BinaryTree | null;
};
// Compiler hangs on large trees.
```

### **Debugging Steps:**
1. **Check for symmetric recursion**:
   - `left` and `right` are both `BinaryTree | null`, but the compiler still expands infinitely.

2. **Fix with `unknown`**:
   ```ts
   type BinaryTree = {
     value: number;
     left: BinaryTree | unknown;
     right: BinaryTree | unknown;
   };
   ```
   - Now the compiler treats `left/right` as opaque.

3. **Alternative: Use `infer` to constrain recursion**:
   ```ts
   type BinaryTree = {
     value: number;
     left: BinaryTree | null;
     right: BinaryTree | null;
   } & { _recursive: true };
   ```
   - Not ideal; prefer `unknown` for production.

4. **Final Solution: Split into leaf and node**:
   ```ts
   type BinaryTreeLeaf = { value: number; left: null; right: null };
   type BinaryTreeNode = { value: number; left: BinaryTree; right: BinaryTree };
   type BinaryTree = BinaryTreeLeaf | BinaryTreeNode;
   ```

---

## **7. Key Takeaways**
| **Issue**               | **Quick Fix**                          | **Long-Term Solution**                  |
|-------------------------|----------------------------------------|-----------------------------------------|
| Infinite type expansion | Use `never`, `unknown`, or `Option`     | Split into asymmetric constructors     |
| Stack overflow          | Use `Box<Self>` (Rust) or `lazy` (Haskell) | Add recursion limits via generics      |
| Slow compilation        | Disable strict checks temporarily      | Refactor to use `GADTs` or size classes |
| Runtime errors          | Validate recursion depth at runtime    | Use phantom types or bounded traits    |

---
## **8. Further Reading**
- [TypeScript Handbook: Recursive Types](https://www.typescriptlang.org/docs/handbook/advanced-types.html#recursive-types)
- [Rust Book: Recursive Types](https://doc.rust-lang.org/book/ch16-04-pattern-syntax.html#recursive-patterns)
- [GHC Wiki: Terminating Types](https://downloads.haskell.org/~ghc/latest/docs/html/users_guide/terminating-types.html)
- [Size Classes (Haskell)](https://hackage.haskell.org/package/size-classes)