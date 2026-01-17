# **[Pattern] Scala Language Patterns – Reference Guide**

---

## **Overview**
This reference guide provides a structured breakdown of **Scala Language Patterns**, covering fundamental and advanced constructs, idioms, and best practices. Scala’s hybrid object-oriented (OOP) and functional programming (FP) paradigms enable expressive yet performant code.

Key focus areas:
- **Core language features** (e.g., immutability, pattern matching, type inference).
- **Functional patterns** (higher-order functions, monads, lazy evaluation).
- **Object-oriented patterns** (traits, case classes, companion objects).
- **Common anti-patterns and mitigations**.

This guide assumes familiarity with Scala’s syntax (e.g., `val`, `def`, `case`) but surfaces implementation details for clarity.

---

## **Schema Reference**
Below are core Scala patterns categorized by paradigm, with key attributes, use cases, and examples.

| **Pattern**               | **Description**                                                                 | **Key Attributes**                                                                 | **Example Use Case**                                  |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|-------------------------------------------------------|
| **Immutable Values**      | Variables declared with `val`; immutable by default.                          | - Immutability guarantees thread safety. <br> - Enables functional composition.   | Configurations, shared state.                          |
| **Pattern Matching**      | Deconstructs data types (e.g., `case`, `match`).                              | - Handles multiple type variants concisely. <br> - Works with `Option`, `Either`. | JSON parsing, ADTs (algebraic data types).            |
| **Higher-Order Functions**| Functions as first-class citizens (passed as args, returned).                 | - Promotes abstraction (e.g., `.map`, `.filter`). <br> - Enables FP pipelines.   | Data transformations, EventSource callbacks.          |
| **Case Classes**          | Lightweight data classes with `==`, `copy`, and pattern-matching support.    | - Auto-generates `apply`, `toString`. <br> - Immutable by default.                 | DTOs, model objects.                                   |
| **Traits**                | Abstract types with method/field definitions (mixins).                       | - Purely abstract (`abstract def foo`). <br> - Supports multiple inheritance.      | Plugin architectures, interfaces.                     |
| **Lazy Evaluation**       | Deferred computation via `lazy val` or streams.                              | - Memoization of expensive operations. <br> - Infinite streams enabled.           | Caching, infinite sequences.                           |
| **Monads (Option/Either)**| Structured failure handling via `flatMap`/`map`.                              | - `Option` for null safety. <br> - `Either` for explicit errors.                   | Safe API calls, validation.                           |
| **Currying**              | Multi-argument functions decomposed into unary functions.                     | - Enables partial application. <br> - Readable with arrow syntax (`=>`).         | Configuration builders, DSLs.                          |
| **Companion Objects**     | Scala objects sharing namespaces with classes for factory/utility methods.   | - Static methods (`def apply`). <br> - Singleton instances.                       | Singleton instances, factory methods.                 |
| **For-Comprehensions**    | Syntactic sugar for chaining monadic operations (e.g., `Option`).              | - Replaces nested `flatMap`/`map`. <br> - Declarative style.                      | Database queries, parsing.                             |

---

## **Implementation Details**

### **1. Immutable Values**
- **How it works**: `val` binds to a value, which cannot be reassigned.
  ```scala
  val config: Map[String, String] = Map("timeout" -> "30s")
  ```
- **Best practice**: Prefer `val` over `var` to avoid side effects.
- **Pitfall**: Mutability in collections (e.g., `List(1) += 2` creates a new list).

### **2. Pattern Matching**
- **Syntax**: `expr match { case _ => ... }`.
  ```scala
  def describe(value: Any): String = value match {
    case i: Int   => s"$i is an integer"
    case s: String => s"'$s' is a string"
    case _        => "unknown type"
  }
  ```
- **Key features**:
  - **Guard clauses**: Add conditions with `if (guard) case`.
  - **Extractors**: Custom pattern matching via `extract` methods.

### **3. Higher-Order Functions**
- **First-class functions**: Pass/return anonymous functions or method references.
  ```scala
  val doubling: Int => Int = _ * 2  // Method reference
  val numbers = List(1, 2, 3)
  val doubled = numbers.map(doubling)  // [2, 4, 6]
  ```
- **Currying**: Convert methods into functions of functions.
  ```scala
  def add(a: Int)(b: Int) = a + b
  val add5 = add(5) _  // Partial application
  ```

### **4. Case Classes**
- **Auto-generated methods**:
  - `copy(newValue)` for shallow copies.
  - `toString` (e.g., `case class Person(name: String)` → `Person("Alice")`).
- **Pattern matching**: Case classes destructure smoothly.
  ```scala
  case class User(id: Int, name: String)
  def greet(user: User): String = user match {
    case User(_, name) => s"Hi $name!"
  }
  ```

### **5. Traits**
- **Mixin composition**: Combine traits via `with`.
  ```scala
  trait Logger {
    def log(message: String): Unit = println(message)
  }
  trait Database {
    def connect(): Unit = log("Connected")
  }
  class App extends Logger with Database
  ```
- **Stackable traits**: Use `this: Trait1 with Trait2` for layered behavior.

### **6. Lazy Evaluation**
- **Lazy vals**: Initialize on first use.
  ```scala
  lazy val heavyData: List[Int] = computeExpensiveValue()
  ```
- **Streams**: Infinite sequences evaluated lazily.
  ```scala
  val stream = Stream.from(1)  // 1, 2, 3, ...
  stream.take(3).foreach(println)
  ```

### **7. Monads (Option/Either)**
- **Option**: Safe "no value" handling.
  ```scala
  val result: Option[Int] = Some(42).flatMap { x =>
    if (x > 0) Some(x * 2) else None
  }
  ```
- **Either**: Explicit error cases.
  ```scala
  type Validation[A] = Either[String, A]
  val validated: Validation[Int] = Right(42)
  ```

### **8. For-Comprehensions**
- **Syntactic sugar**: Replace nested monads.
  ```scala
  for {
    name <- Option("Alice")
    upper <- Option(name.toUpperCase)
  } yield upper  // Some("ALICE")
  ```

---

## **Query Examples**
### **1. Pattern Matching on Nested Data**
**Task**: Extract user data from a nested case class.
```scala
case class Address(city: String, zip: String)
case class User(name: String, address: Address)

val user = User("Alice", Address("Paris", "75001"))

user match {
  case User(name, Address(city, _)) => s"$name lives in $city"
  // Output: "Alice lives in Paris"
}
```

### **2. Higher-Order Function Pipeline**
**Task**: Filter and transform a list.
```scala
val numbers = List(1, 2, 3, 4, 5)
val result = numbers
  .filter(_ % 2 == 0)      // [2, 4]
  .map(_ * 10)            // [20, 40]
```

### **3. Lazy Stream Processing**
**Task**: Process an infinite stream lazily.
```scala
val primes = Stream.from(2).filter(isPrime)  // Infinite stream
primes.take(5).foreach(println)  // 2, 3, 5, 7, 11
```

### **4. Monadic Error Handling**
**Task**: Chain operations with `Either`.
```scala
def divide(a: Int, b: Int): Either[String, Int] =
  if (b == 0) Left("Division by zero")
  else Right(a / b)

val result = for {
  half <- divide(10, 0)  // Left("Division by zero")
  doubled <- divide(half, 2)
} yield doubled  // Left(...) propagated
```

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------|
| **Overusing `var`**                   | Prefer `val`; use `var` only for mutable collections (e.g., `ArrayBuffer`).    |
| **Unchecked pattern matching**       | Use `sealed trait` for exhaustive matching (Scala enforces all cases).        |
| **Improper thread safety**            | Immutable data (`val`) + structural typing (`case class`) ensures safety.     |
| **Lazy evaluation leaks**             | Cache lazy vals explicitly (e.g., `@volatile` for mutable caches).              |
| **Currying complexity**               | Limit to 2–3 arguments; use method references (`_.map`).                       |

---

## **Related Patterns**
1. **[Scala Collections Patterns]** – Efficient APIs for `List`, `Map`, `Set`.
2. **[Akka Actors Patterns]** – Reactive concurrency with Scala.
3. **[FS2 Streams Patterns]** – Lazy, composable data streams.
4. **[Algebraic Data Types (ADT)]** – Advanced pattern matching with sealed hierarchies.
5. **[Macro Patterns]** – Code generation at compile-time (e.g., `quasimodes`).

---
**See also**: [Scala Docs](https://docs.scala-lang.org) for deeper dives into type systems, concurrency, and libraries.