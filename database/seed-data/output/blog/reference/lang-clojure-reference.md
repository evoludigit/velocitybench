---

# **[Clojure Language Patterns] Reference Guide**

---

## **Overview**
Clojure’s functional paradigm, immutable data structures, and rich set of abstractions enable powerful, expressive patterns that solve common problems elegantly. This reference guide covers core **Clojure language patterns**, including:
- **Functional composition** (threading macros, function chaining)
- **Immutable data handling** (vectors, maps, transients)
- **Concurrent programming** (atoms, agents, STM)
- **Metaprogramming** (macros, special forms)
- **Lazy sequencing** (lazy lists, reducers)

Designed for clarity and scalability, these patterns align with Clojure’s principles of *simplicity* and *predictability*. Mastery of these techniques reduces boilerplate, improves maintainability, and leverages Clojure’s runtime efficiently.

---

## **Key Concepts & Schema Reference**

### **1. Functional Composition**
| Pattern               | Purpose                                                                 | Example Code                                                                 |
|-----------------------|-------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Threading Macros**  | Modular function chaining (pre-postfix notation for readability).       | `(-> x f1 f2 f3)` `(thread-first (f1 (f2 x)))`                             |
| **Function Chaining** | Sequential transformation of data/values using pipes (`->`, `->>`).      | `(-> (read-file) (parse-json) (get :data))`                                  |
| **Partial Application**| Currying/partial function application with `fn` or `partial`.            | `(def partial-add (partial + 10))` `(partial-add 5)` → `15`                   |

---

### **2. Immutable Data Handling**
| Structure            | Use Case                          | Anti-Patterns (Avoid)                     | Optimization Tips                     |
|----------------------|-----------------------------------|-------------------------------------------|---------------------------------------|
| **Vectors (`[]`)**   | Ordered, indexed collections.     | Mutating (e.g., `(assoc-in!)`)            | Use `conj` for appends, `pop` for removal. |
| **Maps (`{}`)**      | Key-value associations.           | Overuse of `update-in` with side effects.  | Prefer `merge` (shallow) or `clojure.set/union` for merging. |
| **Sets (`#{}`)**     | Unordered uniqueness.             | Using `conj` on sorted sets without hints.| Specify coll type: `#{1 2 3}` or `(sorted-set 1 2 3)`. |
| **Transients (`transient`)** | Performance-critical mutations. | Forgetting to `persistent!` after use.   | Use sparingly; reserve for bulk ops (e.g., `into` with transients). |

**Example:**
```clojure
;; Efficient vector appends
(defn batch-process [items]
  (reduce conj (transient []) items)) ;; O(1) per conj
```

---

### **3. Concurrency**
| Construct           | Use Case                          | Key Functions                                      | Pitfalls                                    |
|---------------------|-----------------------------------|----------------------------------------------------|---------------------------------------------|
| **Atoms (`atom`)**  | Single-agent state updates.       | `swap!`, `reset!`, `compare-and-set!`             | Overuse leads to race conditions.           |
| **Agents (`agent`)**| Asynchronous state changes.       | `send`, `send-off`, `await`                        | Blocking `await` can deadlock systems.     |
| **STM (`ref`)**     | Atomic transactions.              | `dosync`, `ref-set`, `compare-and-set!`           | Nested `dosync` can cause cascading rollbacks. |

**Example:**
```clojure
;; STM ref with validation
(defn safe-update [ref key new-val]
  (dosync
    (when (compare-and-set! ref key (:old (ref @ref)) new-val)
      :success)))
```

---

### **4. Metaprogramming**
| Tool               | Purpose                                                                 | Example                                                                 |
|--------------------|-------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Macros (`defmacro`)** | Expand code at compile-time.                                          | `(defmacro unless [cond & body] `(if (not ~cond) (do ~@body)))`             |
| **Special Forms**  | Syntax sugar (e.g., `if`, `let`).                                       | `(condp = x 1 :one 2 :two)` (pattern matching via `condp`).               |
| **Compiler Hints** | Guide bytecode generation (e.g., `:tag`, `:inline`).                    | `(defn factorial [n] ^{:tag Long} (if (< n 2) 1 (* n (factorial (dec n)))))` |

**Anti-Pattern:**
Avoid macros for logic that can be expressed with `fn` or `->>`. Macro expansion can obscure semantics.

---

### **5. Lazy Sequences**
| Pattern            | Use Case                          | Performance Considerations                          |
|--------------------|-----------------------------------|-----------------------------------------------------|
| **Lazy Lists (`lazy-seq`)** | Infinite/large data processing.  | Avoid infinite loops via recursion (use `recur`).  |
| **Reducers (`reduce`, `transduce`)** | Efficient bulk operations. | Use `transduce` (e.g., with `category-theory` lib) for custom folds. |

**Example:**
```clojure
;; Lazy infinite sequence of primes
(def primes
  (lazy-cat [2 3]
             (map #(+ % 2) (filter prime? (iterate inc 4)))))
```

---

## **Query Examples**

### **1. Functional Composition**
**Scenario:** Transform a CSV string into a parsed map.
```clojure
(require '[cheshire.core :as json])

;; Using ->>
(defn parse-csv-to-map [csv-line]
  (->> (clojure.string/split csv-line #",")
       (map str/trim)
       (zipmap [:id :name :value])
       (json/parse-string)))

;; Using threading macros
(defn parse-csv-threaded [csv-line]
  (->> csv-line
       (clojure.string/split #",")
       (map str/trim)
       (zipmap [:id :name :value])
       (json/parse-string)))
```

---

### **2. Immutable Data**
**Scenario:** Merge nested maps with precedence to new values.
```clojure
(defn merge-deep [& maps]
  (apply merge-with (fn [& vals] (last vals)) maps))

;; Usage:
(merge-deep {:a 1 :b {:x 10}} {:a 2 :b {:y 20}})
;; => {:a 2, :b {:x 10, :y 20}}
```

**Optimized for Transients:**
```clojure
(defn merge-deep-fast [maps]
  (reduce (fn [acc m]
            (into acc (map (fn [[k v]]
                            [(keyword (name k)) v])
                          m)))
          (transient {})
          maps))
```

---

### **3. Concurrency**
**Scenario:** Safe counter using STM.
```clojure
(def counter (ref 0))

;; Increment in a transaction
(dosync
  (compare-and-set! counter 5 6))

;; Or with `alter`
(alter counter (fnil inc 0))
```

**Anti-Pattern:**
```clojure ; Avoid: Unsafe atom swap
(swap! unsafe-counter inc) ; Risk of lost updates in high contention.
```

---

### **4. Metaprogramming**
**Scenario:** Generate boilerplate test cases.
```clojure
(defmacro test-cases [name cases]
  `(do
     (defn ~name [input]
       (case input
         ~@(for [[i o] cases] `[~i ~o])
         (throw (Exception. "Unknown input"))))

     (doseq [[i o] ~cases]
       (is (= (~name i) o)))))
```
**Usage:**
```clojure
(test-cases factorial-test {1 1, 2 2, 3 6})
```

---

### **5. Lazy Sequences**
**Scenario:** Process lines from a large file without loading it entirely.
```clojure
(defn process-large-file [filename]
  (with-open [rdr (clojure.java.io/reader filename)]
    (doseq [line (line-seq rdr)]
      (when-let [parsed (parse-csv-threaded line)]
        (process-record parsed)))))
```

**Using `transduce` for Efficiency:**
```clojure
(require '[clojure.core.reducers :as r])

(defn reduce-large [f initial coll]
  (transduce (r/repeatedly identity coll) f initial))
```

---

## **Related Patterns**

### **1. Functional Core, Imperative Shell**
- **Context:** Keep business logic pure; use I/O in a shell.
- **Clojure Synergy:** Leverage `->>` for composable pure functions.
- **Example:**
  ```clojure
  (defn process-file [path]
    (->> path
         (slurp)
         (parse-csv-threaded)
         (process-record))) ; Pure function
  ```

---

### **2. Type Hints & Performance**
- **Context:** Optimize hot paths with `@`, `:tag`, or `:inline`.
- **Best Practices:**
  - Use `@ Long` for numeric recursion depths.
  - Prefer `:inline` for small, pure functions.

```clojure
(defn factorial [n] ^{:tag Long} (if (< n 2) 1 (* n (factorial (dec n)))))
```

---

### **3. Structured Concurrency (Clojure 1.11+)**
- **Context:** Use `p promise` for lightweight async/await.
- **Example:**
  ```clojure
  (def p (p/promise))
  (p/deliver p (fetch-data))
  (p/await p) ; Blocks until resolved
  ```

---

### **4. Persistent Data Structures**
- **Context:** Leverage `persistent!` for mutable-like operations.
- **Example:**
  ```clojure
  (def trans (transient []))
  (conj! trans 1) ; => #transaction[{1}]
  (persistent! trans) ; => [1]
  ```

---

### **5. Compiler Macros vs. Runtime Macros**
- **Context:** Use `defmacro` for compile-time expansion; `defmethod` for runtime polymorphism.
- **When to Choose:**
  - **Macro:** Syntax transformation (e.g., `defn`).
  - **Method:** Runtime dispatch (`multimethod`).

---

## **Common Pitfalls & Mitigations**

| Pitfall                          | Solution                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| **Overusing mutations (`conj!`)** | Prefer persistent data; use transients sparingly.                        |
| **Unbounded recursion**          | Use `recur` or `loop` for tail calls; add `:inline` hints.               |
| **STM deadlocks**                | Avoid nested `dosync`; prefer atomic refs with `compare-and-set!`.       |
| **Macro complexity**             | Extract complex macros into functions; document thoroughly.              |
| **Lazy sequence misuse**         | Always ensure termination (e.g., `(take n (lazy-seq ...))`).              |

---

## **Further Reading**
- [Clojure Documentation](https://clojure.org/reference)
- *"Clojure for the Brave and True"* (Daniel Higgins) – Covers patterns deeply.
- [`core.async`](https://clojure.org/reference/core_async) – Advanced concurrency.
- [`spec` library](https://clojure.org/reference/spec) – Runtime validation patterns.