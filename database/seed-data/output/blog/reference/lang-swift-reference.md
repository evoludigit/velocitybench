# **[Swift Language Patterns] Reference Guide**

---

## **Overview**
This reference guide provides a structured breakdown of **Swift language patterns**, focusing on idiomatic code constructs, common problem-solving strategies, and best practices for writing efficient, maintainable, and scalable Swift applications. The guide covers functional programming paradigms (closures, higher-order functions), object-oriented principles (protocols, type erasure), control flow (pattern matching, optionals), and modern Swift features (swift-concurrency, actor model, and generics). By leveraging these patterns, developers can write cleaner, more expressive code while avoiding common pitfalls such as memory leaks, thread-safety issues, or unintuitive control flow.

---

## **Schema Reference**
Below is a categorized table of Swift language patterns, their use cases, and implementation considerations.

| **Category**       | **Pattern**                          | **Use Case**                                                                                     | **Key Considerations**                                                                                                                                                                                                 |
|--------------------|--------------------------------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Functional**     | Closures (as first-class citizens)  | Reusable logic, event handlers, async callbacks, and higher-order functions.                   | Closures can capture context; use `[weak self]` in `UIKit`/`AppKit` callbacks to avoid retain cycles. Prefer `@escaping` only when necessary (e.g., async callbacks).                                 |
|                    | Higher-Order Functions              | Map, filter, reduce, flatMap for collections; compose reusable operations.                      | Overuse can obscure readability. Prefer explicit loops for simple logic.                                                                                                                                                  |
|                    | Optionals (`if let`, `guard let`)   | Safe unwrapping of nullable values.                                                              | Prefer `guard let` in initializer chains; use `nil-coalescing (?)` for default values. Avoid force-unwrap (`!`).                                                                                                        |
|                    | Pattern Matching (`switch`, `guard`) | Type-safe branching (enums, tuples, wildcards).                                                | Exhaustiveness enforcement (`@unknown` for raw values) improves safety.                                                                                                                                                     |
| **Object-Oriented**| Protocols (Adoption + Conformance)  | Define shared interfaces; achieve duck typing.                                                   | Protocol-oriented design favors composition over inheritance. Use `Protocol<T>` for type erasure (e.g., `Any` replacement).                                                                                           |
|                    | Type Erasure (`AnyObject`, `Any`)   | Abstract heterogeneous collections (e.g., `UIView` subclasses, async tasks).                 | Overuse can leak type information; prefer generics (`where T: SomeProtocol`).                                                                                                                                              |
|                    | Optionals as Return Types (`-> T?`)  | Indicate potential failure (e.g., file I/O, network calls).                                   | Document failure cases via `Result<T, Error>` for clarity.                                                                                                                                                                   |
| **Concurrency**    | `async/await` (Swift 5.5+)           | Non-blocking I/O, sequential async code.                                                         | Use `Task` for structured concurrency; avoid nested callbacks.                                                                                                                                                               |
|                    | Actors (Isolated State)              | Thread-safe mutable state (e.g., shared configurations).                                          | Mark methods with `@MainActor` or `Actor` to enforce synchronization.                                                                                                                                                     |
|                    | Dispatch Queues (`DispatchQueue`)   | Background threads, priority scheduling.                                                        | Prefer `DispatchQueue.global(qos: .userInitiated)` for I/O-bound tasks. Avoid `DispatchQueue.main` for heavy UI updates.                                                                                                  |
| **Generics**       | Generic Functions/Types              | Reusable, type-safe abstractions (e.g., `Array`, `Dictionary`).                                | Use `where` clauses for constraints (e.g., `T: Equatable`). Avoid runtime branching in generics.                                                                                                                        |
| **Memory Safety**  | `deinit`                             | Clean up resources (e.g., file handles, subscriptions).                                          | Prefer `deinit` sparingly; avoid side effects in destructors.                                                                                                                                                              |
|                    | Strong/Weak References (`weak`, `unowned`) | Break retain cycles (e.g., `UIKit` delegates, closures).                                       | Use `weak` for optional references; `unowned` only for non-optional, non-escaping captures.                                                                                                                             |
| **Error Handling** | `Result<T, Error>`                   | Structured error propagation (e.g., `do-try-catch`).                                            | Combine with `async/await` for modern error flows: `if let result = await someAsyncCall()`                                                                                                                              |
|                    | Custom Errors (`enum + Case`)         | Domain-specific error types (e.g., `ValidationError`).                                             | Extend `Error` protocol; use `localizedDescription` for user-facing messages.                                                                                                                                      |
| **Control Flow**   | `forEach` vs. `for-in`               | Iteration over collections (prefer `for-in` for readability).                                    | `forEach` is functional but less idiomatic for side effects.                                                                                                                                                                |
|                    | Lazy Sequences (`Sequence`, `Lazy`)  | Efficiently process large datasets (e.g., `Array.lazy.map`).                                    | Useful for chaining transformations without intermediate storage.                                                                                                                                                            |
| **Modern Swift**   | `@MainActor`                         | Mark async methods as `UIKit`-safe.                                                              | Enforces main-thread execution for UI-related work.                                                                                                                                                                      |
|                    | `TaskLocal`                          | Thread-local storage (e.g., logging contexts).                                                   | Use sparingly; prefer dependency injection for most cases.                                                                                                                                                                  |

---

## **Query Examples**
Below are practical examples demonstrating key patterns in action.

---

### **1. Functional Patterns**
#### **Closures as Parameters**
```swift
// Higher-order function to apply a transform
func apply<T, U>(to input: [T], transform: (T) -> U) -> [U] {
    return input.map(transform)
}

let numbers = [1, 2, 3]
let doubled = apply(to: numbers) { $0 * 2 } // [2, 4, 6]
```

#### **Optional Chaining**
```swift
struct User {
    var profile: Profile?
}

struct Profile {
    var bio: String?
}

let user: User? = User(profile: Profile(bio: "Hi!"))
let bio = user?.profile?.bio ?? "No bio" // "Hi!"
```

#### **Pattern Matching with Enums**
```swift
enum Command {
    case move(x: Int, y: Int)
    case rotate(direction: String)
}

func execute(_ command: Command) {
    switch command {
    case .move(let x, let y):
        print("Moved to \(x), \(y)")
    case .rotate(let direction):
        print("Rotated \(direction)")
    }
}

execute(.move(x: 10, y: 20)) // "Moved to 10, 20"
```

---

### **2. Object-Oriented Patterns**
#### **Protocol Extension for Default Implementations**
```swift
protocol Loggable {
    var name: String { get }
    func log()
}

extension Loggable {
    func log() {
        print("[\(name)] Action performed")
    }
}

struct App: Loggable {
    let name = "MyApp"
}

App().log() // "[MyApp] Action performed"
```

#### **Type Erasure with `AnyObject`**
```swift
protocol AsyncTask {
    func execute(completion: @escaping (Result<Int, Error>) -> Void)
}

class ConcreteTask: AsyncTask {
    func execute(completion: @escaping (Result<Int, Error>) -> Void) {
        completion(.success(42))
    }
}

// Wrap in `AnyObject` for heterogeneous collections
typealias ErasedAsyncTask = AnyObject & AsyncTask
var tasks: [ErasedAsyncTask] = [ConcreteTask()]
```

---

### **3. Concurrency Patterns**
#### **`async/await` with `Task`**
```swift
func fetchData() async throws -> String {
    // Simulate network call
    await Task.sleep(1_000_000_000) // 1 second
    return "Data fetched"
}

Task {
    do {
        let data = try await fetchData()
        print(data) // "Data fetched"
    } catch {
        print("Error: \(error)")
    }
}
```

#### **Actors for Thread Safety**
```swift
actor Counter {
    private var count = 0

    func increment() {
        count += 1
    }

    func getCount() -> Int {
        count
    }
}

Task {
    let counter = Counter()
    await counter.increment()
    print(await counter.getCount()) // 1 (thread-safe)
}
```

---

### **4. Error Handling**
#### **`Result` with `async/await`**
```swift
enum NetworkError: Error {
    case invalidURL
}

func fetch(url: String) async throws -> String {
    if url.isEmpty {
        throw NetworkError.invalidURL
    }
    return "Success"
}

Task {
    guard let result = try? await fetch(url: "https://example.com") else {
        print("Fetch failed")
        return
    }
    print(result) // "Success"
}
```

---

### **5. Generics**
#### **Generic Function with Constraints**
```swift
func printMax<T: Comparable>(_ values: [T]) {
    print("Max: \(values.max() ?? T.min())")
}

printMax([1, 3, 2]) // "Max: 3"
printMax(["a", "b"]) // "Max: b"
```

---

## **Related Patterns**
To complement **Swift Language Patterns**, consider these related design principles and patterns:

1. **MVVM/MVVM-ish**
   - Combine with **SwiftUI** or **UIKit** to separate view logic from business logic. Use **protocols** for inter-component communication.

2. **Dependency Injection (DI)**
   - Replace hardcoded dependencies (e.g., `UserManager`) with injectable protocols:
     ```swift
     protocol UserRepository { func fetchUser() async -> User }
     class App: DependencyInjectable {
         let userRepo: UserRepository
         init(userRepo: UserRepository) { self.userRepo = userRepo }
     }
     ```

3. **Singleton Anti-Pattern**
   - Avoid singletons for thread safety; use **actors** or **dependency injection** instead. If required, enforce singletons via `static let shared = Self()`.

4. **SwiftUI + Combine**
   - Use **publisher-patterns** (e.g., `PassthroughSubject`, `Set`) for reactive UI updates:
     ```swift
     class CounterViewModel: ObservableObject {
         @Published var count = 0
         private let subject = PassthroughSubject<Void, Never>()
         init() { subject.subscribe(on: DispatchQueue.main) { [weak self] _ in self?.increment() }.store(in: &cancellables) }
         func increment() { count += 1 }
     }
     ```

5. **Error Handling: Retry Policies**
   - Implement exponential backoff for transient errors:
     ```swift
     func retry<T>(_ operation: () async throws -> T, maxAttempts: Int = 3) async throws -> T {
         var lastError: Error?
         for attempt in 1...maxAttempts {
             do {
                 return try await operation()
             } catch {
                 lastError = error
                 await Task.sleep(value: 1_000_000_000 * attempt) // 1s * attempt
             }
         }
         throw lastError!
     }
     ```

6. **Performance: Lazy Initialization**
   - Defer expensive initializations:
     ```swift
     private lazy var heavyObject: HeavyObject = {
         print("Initializing...")
         return HeavyObject()
     }()
     ```

7. **Testing: Protocol Mocking**
   - Replace dependencies with mocks in tests:
     ```swift
     class MockUserRepo: UserRepository {
         var fetchUserCalled = false
         func fetchUser() async -> User { fetchUserCalled = true; return User() }
     }
     ```

---

## **Best Practices & Pitfalls**
### **Do:**
✅ Use **`async/await`** for readability over nested callbacks.
✅ Prefer **protocols** over classes for abstraction.
✅ Leverage **SwiftUI’s `ObservableObject`** for reactive state management.
✅ Document **error cases** with `Result` or custom errors.
✅ Use **`@MainActor`** to enforce UI thread safety.

### **Don’t:**
❌ Avoid **force-unwrap (`!`)**—use `guard` or `if let` instead.
❌ Overuse **generics** if the complexity outweighs benefits.
❌ Mix **UI updates** with background threads without `DispatchQueue.main`.
❌ Ignore **memory management** (e.g., retain cycles in closures).
❌ Use **singletons** for shared state (prefer actors or DI).

---

## **Further Reading**
- [Swift Documentation](https://docs.swift.org/swift-book/)
- [Apple’s Concurrency Programming Guide](https://developer.apple.com/documentation/swift/concurrency)
- [Ray Wenderlich’s SwiftUI Tutorials](https://www.raywenderlich.com/swiftui)
- [Hacking with Swift: Advanced Patterns](https://www.hackingwithswift.com/quick-start/swiftui)