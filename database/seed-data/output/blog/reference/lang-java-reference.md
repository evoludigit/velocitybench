# **[Java Language Patterns] Reference Guide**

---

## **Overview**
The **Java Language Patterns** reference guide provides structured best practices for implementing Java language features, idioms, and design patterns. This guide covers essential constructs such as object-oriented principles, functional programming, concurrency, reflection, and annotations—along with their trade-offs, performance implications, and common misuse scenarios.

Whether you're writing high-performance systems, maintaining legacy code, or adopting modern Java (Java 17+), this reference helps you choose the right approach for readability, maintainability, and performance. Key topics include collections handling, exception management, stream processing, and thread safety, ensuring adherence to Java’s evolving best practices.

---

## **Schema Reference**

| **Category**          | **Language Feature/Pattern**       | **When to Use**                                                                 | **Key Considerations**                                                                                     | **Anti-Patterns**                                                                                     |
|-----------------------|-------------------------------------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Object-Oriented**   | **Singleton**                       | Single global instance needed (e.g., configuration, logging).                     | Lazy initialization, thread safety (Enum preferred in Java ≥7).                                          | Global variables, mutable singletons, double-checked locking misuse.                                   |
|                       | **Factory Method**                  | Object creation decoupled from client code (e.g., subclasses, dependencies).      | Follows Open/Closed Principle; reduce `new` keyword clutter.                                               | Direct instantiation bypassing factory logic.                                                         |
|                       | **Builder Pattern**                 | Complex object construction with many optional parameters.                       | Reduces constructor parameter explosion; immutable objects.                                               | Overuse in simple cases; builder nested deeply.                                                        |
| **Functional**        | **Lambda Expressions**              | Functional-style processing (e.g., streams, event handlers).                     | Concise, declarative code; avoids boilerplate (e.g., `Comparator`).                                   | Lambda captures mutable state; excessive nesting in complex logic.                                     |
|                       | **Stream API**                      | Data processing pipelines (filtering, mapping, reducing).                        | Lazy evaluation; chained operations (e.g., `map` → `filter`).                                         | Side effects in streams; premature materialization (`forEach` on infinite streams).                     |
|                       | **Optional**                        | Null-safe value handling (avoids `NullPointerException`).                        | Explicit null handling with `orElse`, `orElseThrow`.                                                    | Overuse as a return type for non-nullable values; chained `Optional` calls.                           |
| **Concurrency**       | **Thread Safety**                   | Shared-state operations (e.g., caches, counters).                                | Use `synchronized`, `ReentrantLock`, or immutable objects.                                               | Unchecked race conditions; visible `volatile` misuse.                                                  |
|                       | **Thread Pools**                    | Reusable thread management (e.g., `ExecutorService`).                            | Configure `ThreadPoolExecutor` for workload (e.g., fixed/cached threads).                               | Oversized pools causing resource exhaustion; hardcoded thread counts.                                   |
|                       | **CompletableFuture**               | Async non-blocking operations with callbacks.                                  | Chaining operations (`thenApply`, `thenCombine`).                                                      | `CompletableFuture` misused as a synchronous wrapper; unhandled exceptions.                            |
| **Reflection/Introspection** | **Reflection**                | Dynamic class/field/method access (e.g., serialization, testing).                | Use sparingly; performance overhead.                                                                | Reflection bypassing access controls; security risks (e.g., `setAccessible(true)`).                   |
|                       | **Annotations**                     | Metadata for compilation/runtime (e.g., `@Override`, `@SuppressWarnings`).        | Decorate methods/classes for tooling (e.g., Lombok, Spring).                                           | Overuse for logic (not just metadata); custom annotations without processing.                          |
| **Collections**       | **Immutable Collections**           | Thread-safe data structures (e.g., `List.of()`, `Map.copyOf`).                   | Prevents unintended modifications; safer for concurrency.                                               | Immutable wrappers around mutable data.                                                              |
|                       | **Custom Collection Implementations** | Domain-specific optimizations (e.g., `Trie`, `LRUCache`).                      | Extend `AbstractCollection`/`AbstractMap` for performance.                                               | Reinventing wheels; violating collection interfaces.                                                    |
| **Error Handling**    | **Checked Exceptions**              | Recovery actions (e.g., file I/O, database).                                     | Forces explicit error handling; improves API clarity.                                                   | Overuse for control flow; catching `Exception`.                                                       |
|                       | **Runtime Exceptions**              | Software bugs (e.g., `NullPointerException` in bad design).                     | Use sparingly; document assumptions (e.g., `@NonNull`).                                                 | Swallowing exceptions; returning `null` instead of throwing.                                           |
| **Performance**       | **Object Pools**                    | Reusing expensive objects (e.g., `DbConnection`).                               | Amortized cost savings (e.g., `HikariCP` for JDBC).                                                     | Object pools for non-expensive objects; memory leaks.                                                   |
|                       | **Primitive Specialization**        | High-performance arrays (e.g., `int[]` vs `List<Integer>`).                      | Avoid autoboxing overhead; use `IntStream` for primitive streams.                                        | Mixing primitives and objects unnecessarily.                                                          |
| **Modern Java**       | **Records**                         | Immutable data carriers (Java ≥16).                                               | Boilerplate-free `getters`/`equals`/`hashCode`.                                                       | Overuse in mutable contexts; records cannot extend classes.                                            |
|                       | **Sealed Classes**                  | Restricted class hierarchies (e.g., `enum`-like types).                        | Enforce closed class hierarchies; pattern matching support (Java ≥17).                                  | Overly permissive inheritance in sealed hierarchies.                                                   |
|                       | **Pattern Matching**                | Type-safe conditional logic (e.g., `instanceof` with `->`).                     | Replace `instanceof` + casting chains.                                                                | Complex nested patterns; incompatible with legacy code.                                                  |

---

## **Query Examples**

### **1. Singleton Implementation (Thread-Safe)**
```java
// Enum Singleton (Recommended)
public enum DatabaseConfig {
    INSTANCE;

    public void connect() { /* ... */ }
}

// Lazy Initialization with Double-Checked Locking (Legacy)
private static volatile DatabaseConfig instance;
public static DatabaseConfig getInstance() {
    if (instance == null) {
        synchronized (DatabaseConfig.class) {
            if (instance == null) {
                instance = new DatabaseConfig();
            }
        }
    }
    return instance;
}
```

### **2. Stream API Pipeline**
```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");
List<String> filtered =
    names.stream()
         .filter(name -> name.length() > 3)
         .map(String::toUpperCase)
         .sorted()
         .collect(Collectors.toList());
// Result: ["ALICE", "CHARLIE"]
```

### **3. Thread Pool Configuration**
```java
ExecutorService executor = new ThreadPoolExecutor(
    4,                 // Core threads
    8,                 // Max threads
    60,                // Keep-alive time (seconds)
    TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(100),
    new ThreadPoolExecutor.CallerRunsPolicy()
);
```

### **4. Optional Chaining**
```java
Optional<String> name = getUserName();
String upperCaseName = name
    .filter(n -> !n.isEmpty())
    .map(String::toUpperCase)
    .orElse("DEFAULT");
```

### **5. Records for Immutable Data**
```java
record Person(String name, int age) {} // Auto-generates getters, equals(), hashCode()

Person person = new Person("Alice", 30);
System.out.println(person.name()); // "Alice"
```

### **6. Sealed Class Hierarchy**
```java
public sealed interface Shape permits Circle, Square {
    double area();
}

public final class Circle implements Shape {
    @Override public double area() { return Math.PI * radius * radius; }
}
```

### **7. Functional Interface with Lambda**
```java
Function<String, Integer> stringLength = String::length;
System.out.println(stringLength.apply("Java")); // 4
```

### **8. Exception Handling**
```java
try {
    Files.readString(Path.of("file.txt"));
} catch (IOException e) {
    log.error("File read failed", e);
    throw new RuntimeException("Critical error", e);
}
```

### **9. Reflection Usage**
```java
Method method = MyClass.class.getMethod("publicMethod");
Object result = method.invoke(new MyClass(), arg1, arg2);
```

### **10. Immutable Collection**
```java
List<String> immutableList = List.of("A", "B", "C");
// Unmodifiable; throws UnsupportedOperationException on add/remove.
```

---

## **Related Patterns**
| **Related Pattern**               | **Connection to Java Language Patterns**                                                                 | **Key Resources**                                                                                     |
|------------------------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Strategy Pattern**              | Used with lambda expressions or functional interfaces to encapsulate algorithms.                       | [JavaDoc: `java.util.function` Packages](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/function/) |
| **Observer Pattern**              | Implemented with event handlers (e.g., JavaFX, Spring Events) or `CompletableFuture`.                 | [Java Event Handling](https://docs.oracle.com/javase/tutorial/uiswing/events/)                        |
| **Decorator Pattern**             | Achieved with lambdas or functional composition (e.g., chaining `map`/`filter`).                      | [Functional Decorator](https://www.baeldung.com/java-decorator-pattern)                               |
| **Command Pattern**               | Encapsulated as lambdas or functional interfaces (e.g., `Runnable`, `Supplier`).                       | [Java Lambdas for Commands](https://www.baeldung.com/java-lambda-command-pattern)                    |
| **Template Method Pattern**       | Implemented with abstract methods and overridden in subclasses (e.g., `AbstractList`).                 | [Java Template Method](https://refactoring.guru/design-patterns/template-method/java-example)         |
| **Builder Pattern**               | Standardized with `Records` or Lombok’s `@Builder`.                                                     | [Lombok Builder](https://projectlombok.org/features/Builder)                                        |
| **Flyweight Pattern**             | Optimized with object pooling (e.g., `ThreadLocal` caches).                                           | [Java Object Pool](https://www.baeldung.com/java-object-pool)                                       |
| **Proxy Pattern**                 | Implemented via dynamic proxies or `java.lang.invoke` (e.g., dynamic method handling).                | [Java Dynamic Proxies](https://docs.oracle.com/javase/tutorial/reflect/dynamic/)                     |
| **Null Object Pattern**           | Substituted with `Optional` or custom `Null` implementations.                                           | [Optional for Null Handling](https://www.baeldung.com/java-optional)                                |

---

## **Best Practices & Pitfalls**
### **Best Practices**
1. **Prefer Streams Over Loops**:
   Replace manual iteration with declarative streams for readability and concurrency.
   ```java
   // Bad
   for (User user : users) {
       if (user.isActive()) processedUsers.add(user);
   }
   // Good
   users.stream()
        .filter(User::isActive)
        .collect(Collectors.toList());
   ```

2. **Use Records for Data Classes**:
   Reduces boilerplate and enforces immutability.

3. **Leverage `Optional` Judiciously**:
   Avoid `Optional` for method returns with non-nullable semantics.

4. **Thread Safety**:
   Prefer immutable objects or concurrent collections (`ConcurrentHashMap`).

5. **Modern Annotations**:
   Use `@Record`, `@NonNull`, and `@SneakyThrows` (Lombok) where applicable.

### **Pitfalls to Avoid**
1. **Reflection Overhead**:
   Reflection is slow; use it only when necessary (e.g., serialization).

2. **Checked Exceptions in APIs**:
   Use runtime exceptions for internal errors; checked exceptions for recoverable I/O.

3. **Lambda Captures**:
   Avoid capturing mutable state in lambdas passed to threads.

4. **Overusing Lambdas**:
   Don’t replace simple methods with lambdas; readability suffers.

5. **Ignoring Nulls**:
   Treat `null` as a legitimate state (use `Optional` or defensive checks).

---
**Last Updated**: [Insert Date]
**Java Version**: 17+
**License**: [MIT/Apache 2.0]