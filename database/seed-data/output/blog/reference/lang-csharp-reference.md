---
**[Pattern] C# Language Patterns – Reference Guide**
*Version 1.2 | Last updated: [Insert Date]*

---

### **Overview**
The **C# Language Patterns** reference guide documents idiomatic constructions, syntax variations, and best-practices for writing maintainable, performant, and scalable C# code. It covers core language features like **null-coalescing, pattern matching, LINQ, async/await**, and advanced patterns like **dependency injection, immutable design, and state machines**. This documentation serves as a **scannable checklist** for developers implementing modern C# (10+), with emphasis on readability, performance, and thread safety.

---

## **1. Core Language Patterns**
### **1.1 Null Handling**
| Pattern               | Description                                                                 | Best Practices                                                                 | Pitfalls                                                                 |
|-----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `?.` (Null-Conditional)| Safely accesses nested properties if the left operand is non-null.          | Prefer over nested `if (obj != null)` checks.                               | Confusing with `?.` + `!` (null-forgiving operator) in complex chains. |
| `??` (Null-Coalescing)| Returns the left operand if non-null, otherwise the right operand.          | Use for default values (e.g., `null ?? defaultValue`).                        | Overuse can mask validation logic.                                     |
| `!` (Null-Forgiving)| Tells the compiler the object is non-null (risky).                          | Use sparingly; document assumptions.                                         | Can lead to runtime `NullReferenceException`.                           |
| `null` vs `default`  | `null` is a reference type default; `default(T)` works for value types.     | Use `default` for stack-allocated types (e.g., `int`).                       | `default` on `class` types returns `null`.                                |

**Example:**
```csharp
string? name = _user?.Account?.Name ?? "Guest"; // Safe chaining + fallback
```

---

### **1.2 Pattern Matching**
| Syntax               | Use Case                                                                      | Example                                                                     |
|----------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Relational**       | Equality checks (e.g., `switch` on `int`).                                    | `switch (x) { case 1: ... case > 10: ... }`                                |
| **Deconstruction**   | Parsing composite types (e.g., tuples, records).                              | `switch ((x, y) = pair) { case (1, _): ... }`                              |
| **Type**             | Check type at runtime (e.g., `is`, `as`).                                     | `if (obj is List<string> list) { ... }`                                    |
| **Property**         | Match on property values (C# 9+).                                             | `case var item when item.IsActive: ...`                                     |
| **Parentheses**      | Group conditions (e.g., `case (1 or 2): ...`).                                | `switch (x) { case (1 or 2): Console.WriteLine("Small"); }`               |

**Example:**
```csharp
string Describe(object obj) =>
    obj switch
    {
        null => "Null",
        string s when s.Length > 10 => "Long string",
        _ => "Unknown"
    };
```

---

### **1.3 LINQ Patterns**
| Pattern               | Description                                                                 | Performance Notes                                                                 |
|-----------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Method Syntax**     | `Enumerable.Where()`, `Select()`, etc.                                        | Lazy evaluation (deferred execution).                                           |
| **Query Syntax**      | SQL-like `from`, `where`, `join`.                                             | More readable but slightly slower due to parsing overhead.                       |
| **Lazy Loading**      | `AsEnumerable()` (in-memory) or `AsQueryable()` (database).                 | Avoid materializing data prematurely.                                           |
| **Grouping**          | `GroupBy()` + `Aggregate()` for summaries.                                   | Use `ToLookup()` for faster lookups when grouping is the primary operation.    |
| **Project-to-Type**   | `Select(new { ... })` for anonymous types.                                    | Anonymous types are immutable; cache results if reused.                         |

**Example:**
```csharp
var longNames = users
    .Where(u => u.Name.Length > 5)
    .Select(u => new { u.Id, u.Name }); // Project-to-type
```

---

### **1.4 Async/Await Patterns**
| Pattern               | Description                                                                 | Best Practices                                                                 |
|-----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Basic**             | `Task` chaining with `await`.                                               | Avoid nested `await` (use `Task.WhenAll` or `Task.ContinueWith`).            |
| **ConfigureAwait**    | `await Task.Method(ConfigureAwait(false))` to avoid deadlocks in UI apps.     | Always use `ConfigureAwait(false)` for library code.                          |
| **Fire-and-Forget**   | `Task.Run()` + `_ = task` (use `IHostedService` for production).             | Log exceptions with `TaskScheduler.UnobservedTaskException`.                  |
| **Cancellation**      | `CancellationToken` for graceful shutdowns.                                  | Pass `ct` to all async methods in the chain.                                  |
| **ValueTask**         | Lightweight alternative to `Task` (C# 8+).                                   | Use for high-performance scenarios (e.g., game loops).                        |

**Example:**
```csharp
public async Task<string> FetchData(CancellationToken ct)
{
    using var client = new HttpClient();
    return await client.GetStringAsync("api", ct);
}
```

---

## **2. Advanced Patterns**
### **2.1 Dependency Injection (DI)**
| Pattern               | Description                                                                 | DI Container Example                                                                 |
|-----------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Scoped**            | Lifetime tied to HTTP request/transaction.                                  | `[ServiceLifetime.Scoped]` in .NET Core.                                          |
| **Singleton**         | Single instance per app domain.                                              | `[ServiceLifetime.Singleton]` (use cautiously; thread-safe by design).           |
| **Transient**         | New instance per request.                                                    | Default lifetime; ideal for stateless services.                                  |
| **Factory Method**    | Custom logic for instantiation (e.g., `IUserRepositoryFactory`).            | Avoid magic strings; use interfaces.                                             |

**Example:**
```csharp
services.AddScoped<IUserService, UserService>();
services.AddTransient<ILoggerFactory>(provider =>
    new LoggerFactory(new[] { new ConsoleLoggerProvider() }));
```

---

### **2.2 Immutable Design**
| Technique            | Description                                                                 | Example                                                                         |
|----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Records**          | Value types with structural equality (C# 9+).                                | `record User(string Name, int Age);`                                          |
| **Init-Only Setters**| `init` accessors for immutable properties.                                  | `public string Name { get; init; }`                                           |
| **Defensive Copying**| Return deep copies of mutable state.                                         | `return new List<T>(_items)` for public getters.                               |
| **Pattern Matching** | Validate immutable state in `switch` expressions.                            | `switch (state) { case { IsValid: true } => ... }`                            |

**Example:**
```csharp
public record Point(int X, int Y)
{
    public bool IsOrigin() => X == 0 && Y == 0;
};
```

---

### **2.3 State Machines**
| Approach             | Tools/Libraries                                                             | Use Case                                                                       |
|----------------------|---------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Manual (Switch)**  | `switch` + `Action` delegates.                                             | Simple workflows with known states.                                           |
| **State Pattern**    | Base `State` + concrete `ConcreteState` classes.                           | Complex workflows (e.g., order processing).                                  |
| **FSM Libraries**    | [Stateless](https://stateless.co/) or [XState](https://xstate.js.org/).    | Reactive state machines (e.g., UI interactions).                              |

**Example (Manual):**
```csharp
enum OrderState { New, Paid, Shipped, Cancelled }

public void Process(OrderState state, Action action)
{
    switch (state)
    {
        case OrderState.New when action is Pay:
            _state = OrderState.Paid;
            break;
        // ...
    }
}
```

---

## **3. Schema Reference**
| Category          | Pattern               | Key Methods/Properties                          | NuGet Packages (if applicable)               |
|-------------------|-----------------------|-----------------------------------------------|---------------------------------------------|
| **Null Handling** | Null-Coalescing       | `??`, `?.`, `!`                                | None                                        |
| **Pattern Matching** | Switch Expressions    | `switch`, `case`, `when`                       | None                                        |
| **LINQ**          | Query Operators       | `Where`, `Select`, `GroupBy`, `Join`          | `System.Linq`                               |
| **Async**         | Task Patterns         | `Task`, `ConfigureAwait`, `CancellationToken` | None                                        |
| **DI**            | Service Lifetime      | `IServiceCollection`                           | `Microsoft.Extensions.DependencyInjection`  |
| **Immutable**     | Records               | `record`, `init`, `with`                       | None                                        |
| **State Machines**| Stateless             | `Machine`, `States`, `Transitions`             | `Stateless`                                 |

---

## **4. Query Examples**
### **4.1 LINQ (Filtering + Projection)**
```csharp
// Filter active users > 18, project to tuple
var adults = users
    .Where(u => u.IsActive && u.Age > 18)
    .Select(u => (u.Id, u.Name.Length))
    .ToList();
```

### **4.2 Async with Cancellation**
```csharp
var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
try
{
    var data = await _service.FetchData(cts.Token);
    Console.WriteLine(data);
}
catch (TaskCanceledException)
{
    Console.WriteLine("Timeout");
}
```

### **4.3 Pattern Matching (Records)**
```csharp
record Order(string Id, decimal Amount, bool Shipped);

void Process(Order order) =>
    order switch
    {
        { Shipped: true } => Console.WriteLine("Delivered"),
        { Amount: > 100 } => Console.WriteLine("Large order"),
        _ => Console.WriteLine("Pending")
    };
```

### **4.4 DI with Scoping**
```csharp
// Startup.cs
services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(_configuration.GetConnectionString("Default")));

// In a controller:
public class OrderController : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetOrders([FromServices] AppDbContext db)
    {
        return Ok(await db.Orders.ToListAsync());
    }
}
```

---

## **5. Related Patterns**
| Pattern                          | Description                                                                 | When to Use                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **[Repository Pattern]**         | Abstract DAO layer for databases.                                            | When decoupling persistence logic from business logic.                    |
| **[Strategy Pattern]**           | Encapsulate algorithms (e.g., sorting, logging).                            | For interchangeable behaviors (e.g., payment methods).                    |
| **[Builder Pattern]**            | Step-by-step object construction.                                           | Complex object initialization (e.g., `StringBuilder`).                    |
| **[Observer Pattern]**           | Event-driven updates (e.g., `INotifyPropertyChanged`).                     | Reactive UI or event-driven architectures.                                 |
| **[CQRS]**                       | Separate read/write models.                                                  | High-performance query-heavy applications.                                 |
| **[MediatR]**                    | Handle commands/events (CQRS-friendly).                                     | Microservices or modular apps with clear boundaries.                       |

---

## **6. Pitfalls & Mitigations**
| Pitfall                          | Impact                                      | Mitigation                                                                 |
|----------------------------------|---------------------------------------------|----------------------------------------------------------------------------|
| **Overusing `async void`**       | Uncaught exceptions.                          | Always use `Task` or `Task<T>`.                                            |
| **Blocking on `await`**          | Thread starvation.                           | Use `Task.Run` for CPU-bound work.                                         |
| **Ignoring `ConfigureAwait`**    | Deadlocks in UI apps.                         | Default to `ConfigureAwait(false)` in libraries.                          |
| **Mutable Records**              | Accidental state changes.                     | Use `with` expressions for immutability.                                   |
| **LINQ with Side Effects**       | Non-deterministic results.                   | Avoid `ToList()` + `foreach` loops; use `foreach` directly on `IEnumerable`.|
| **Tight Coupling with DI**       | Harder testing.                              | Favor interfaces + mocking frameworks (e.g., Moq).                        |

---
**See Also:**
- [Microsoft C# Documentation](https://learn.microsoft.com/en-us/dotnet/csharp/)
- [LINQ Performance Tips](https://devblogs.microsoft.com/dotnet/linq-performance-tips/)
- [Effective C# 10](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions)