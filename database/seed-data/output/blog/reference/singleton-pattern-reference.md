# **[Design Pattern] Singleton Pattern Reference Guide**

---

## **Overview**
The **Singleton Pattern** is a **creational design pattern** that restricts instantiation of a class to a single instance and provides a global access point to it. Its primary purpose is to ensure *a single, shared point of control* for a class while maintaining efficient resource management. This pattern is useful for:
- Logging services (ensuring all logs go to one centralized system).
- Configuration managers (single configuration state across the application).
- Caching systems (one shared cache instance).
- Hardware devices (e.g., a printer driver controlling a single physical device).

While useful, Singletons introduce global state risks (tight coupling, testing difficulties) and should be used judiciously.

---

## **Schema Reference**
The Singleton pattern consists of **four core components**:

| **Component**          | **Description**                                                                                                                                                                                                                                                                 | **Key Properties**                                                                 |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |-------------------------------------------------------------------------------------|
| **Singleton Class**    | The class whose instantiation is limited to a single instance.                                                                                                                                                                                                                 | Private constructor, static instance holder, global access method.              |
| **Private Constructor**| Ensures no external instantiation of the Singleton.                                                                                                                                                                                                                     | Prevents `new Singleton()` outside the class.                                    |
| **Static Instance**    | Holds the single instance of the class. Initialized on-demand (lazy loading) or eagerly (immediate initialization).                                                                                                                                         | Thread-safe if implemented correctly (e.g., double-checked locking).               |
| **Global Access Method**| Provides controlled access to the Singleton instance (e.g., `getInstance()`).                                                                                                                                                                                                   | Often a static method returning the instance.                                    |

---

## **Implementation Details**
### **1. Basic Singleton Implementation**
The simplest form uses a **eager initialization** approach (instance created at class-load time):

```java
public class Singleton {
    // Private constructor to prevent instantiation
    private Singleton() {}

    // Static instance (eager initialization)
    private static final Singleton INSTANCE = new Singleton();

    // Global access point
    public static Singleton getInstance() {
        return INSTANCE;
    }
}
```
**Pros**:
- Simple and thread-safe by default (due to `final` and static initialization).
**Cons**:
- Instance created even if unused (overhead).

---

### **2. Lazy Initialization (Thread-Safe)**
Defer instance creation until first use (reduces memory usage):

#### **Approach 1: Synchronous Singleton (Java)**
Uses `synchronized` keyword (slower due to thread blocking):

```java
public class Singleton {
    private static Singleton instance;

    private Singleton() {}

    public static synchronized Singleton getInstance() {
        if (instance == null) {
            instance = new Singleton();
        }
        return instance;
    }
}
```
**Pros**:
- Thread-safe.
**Cons**:
- Performance overhead from `synchronized`.

---

#### **Approach 2: Double-Checked Locking (Java)**
Optimizes performance by reducing synchronization:

```java
public class Singleton {
    private static volatile Singleton instance;

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {  // First check (non-synchronized)
            synchronized (Singleton.class) {
                if (instance == null) {  // Second check (synchronized)
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```
**Key Improvements**:
- `volatile` ensures visibility of changes across threads.
- Reduces lock contention after first instantiation.

---

#### **Approach 3: Bill Pugh Singleton (Initialization-on-Demand Holder Idiom)**
Uses a **static inner helper class** for lazy, thread-safe initialization (most efficient):

```java
public class Singleton {
    private Singleton() {}

    private static class SingletonHolder {
        private static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return SingletonHolder.INSTANCE;  // Loads only when called
    }
}
```
**Pros**:
- Thread-safe without synchronization.
- Lazy initialization.
**Cons**:
- Slightly more complex.

---

### **3. Singleton with Enums (Java)**
A concise, thread-safe implementation using enums (recommended for Java):

```java
public enum Singleton {
    INSTANCE;

    public void doSomething() {
        // Method implementations
    }
}
```
**Pros**:
- Thread-safe by default (enum instances are singleton).
- Serialization-safe (avoids "deserialization attacks").
- Simple and concise.
**Cons**:
- Less flexible (all methods must be part of the enum).

---

## **Requirements & Best Practices**
### **Core Requirements**
1. **Single Instantiation**: Only one instance exists.
2. **Global Access**: Provided via a well-defined method (e.g., `getInstance()`).
3. **Thread Safety**: Must handle concurrent access (see implementations above).
4. **Serialization-Safe**: Implement `readResolve()` in Java to prevent duplicate instances during deserialization:
   ```java
   protected Object readResolve() {
       return getInstance();
   }
   ```

### **Best Practices**
1. **Avoid Overuse**: Use when truly needed (e.g., logging, configuration). Prefer dependency injection otherwise.
2. **Lazy Loading**: Initialize on-demand to save resources.
3. **Immutable State**: Make the Singleton’s state immutable to prevent unintended modifications.
4. **Testing**: Avoid Singletons in unit tests (use mocks or refactor to avoid global state).
5. **Document Dependencies**: Clearly state the Singleton’s role and lifecycle in your codebase.
6. **Consider Alternatives**:
   - **Dependency Injection (DI)**: For testability and flexibility.
   - **Static Utilities**: For stateless, utility-like classes (if no shared state is needed).

---

## **Query Examples**
### **1. Checking Singleton Status**
```java
Singleton instance1 = Singleton.getInstance();
Singleton instance2 = Singleton.getInstance();
System.out.println(instance1 == instance2);  // Output: true
```

### **2. Using Enum Singleton**
```java
Singleton.INSTANCE.doSomething();
```

### **3. Thread-Safety Test (Multi-Threaded)**
```java
ExecutorService executor = Executors.newFixedThreadPool(10);
for (int i = 0; i < 10; i++) {
    executor.submit(() -> {
        Singleton singleton = Singleton.getInstance();
        System.out.println("Thread " + Thread.currentThread().getId() + " got: " + singleton);
    });
}
// All threads should receive the same instance.
```

---

## **Related Patterns**
| **Pattern**            | **Description**                                                                                                                                                                                                                                                                 | **When to Use Together**                                                                 |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |-----------------------------------------------------------------------------------------|
| **Factory Method**     | Defines an interface for creating objects but lets subclasses decide which class to instantiate.                                                                                                                                                         | Use Factory Method to control Singleton instance creation in subclasses.                |
| **Dependency Injection**| Passes dependencies to a class rather than hardcoding them or using static methods.                                                                                                                                                                         | Replace Singletons with DI for better testability and flexibility.                       |
| **Prototype**          | Creates new objects by copying an existing object.                                                                                                                                                                                                             | Use Prototype to clone Singleton instances if needed (rarely recommended).               |
| **Abstract Factory**   | Provides an interface for creating families of related objects.                                                                                                                                                                                           | Use Abstract Factory to manage multiple Singleton-like instances (e.g., database connectors). |
| **Command**            | Encapsulates a request as an object, allowing parameterization of clients with different requests.                                                                                                                                                     | Use Command to control Singleton behavior via commands (e.g., logging actions).         |

---

## **Anti-Patterns to Avoid**
1. **Global State Everywhere**: Avoid Singletons for cross-module communication (leads to tight coupling).
2. **Overusing `static`**: Prefer dependency injection over static Singletons for maintainability.
3. **Ignoring Thread Safety**: Always ensure thread safety in multi-threaded environments.
4. **Singleton as a Database Connection Pool**: Use dedicated connection pool implementations instead.
5. **Mocking Singletons in Tests**: Refactor to avoid Singletons if testing becomes cumbersome.

---

## **Summary Checklist**
| **Task**                          | **Action**                                                                 |
|-----------------------------------|----------------------------------------------------------------------------|
| Implement Singleton               | Choose eager or lazy initialization.                                      |
| Ensure Thread Safety              | Use double-checked locking, enum, or initialization-on-demand.             |
| Handle Serialization              | Implement `readResolve()` in Java.                                       |
| Document Global State             | Clearly state the Singleton’s purpose and lifecycle.                        |
| Prefer Alternatives                | Use DI or static utilities when possible.                                  |
| Test Responsibly                  | Avoid Singletons in unit tests; mock or refactor.                          |

---
**End of Guide**