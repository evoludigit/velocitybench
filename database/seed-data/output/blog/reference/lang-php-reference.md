# **[PHP Language Patterns Reference Guide]**

## **Overview**
PHP, a versatile and widely used scripting language, offers numerous **language patterns** that optimize readability, performance, and maintainability. This guide covers **core syntax patterns**, **design idioms**, and **best practices**—including object-oriented principles, functional programming techniques, and memory management strategies.

From **type hints and magic methods** to **exception handling and lazy evaluation**, PHP’s language features enable clean, efficient code. This document serves as a reference for developers implementing these patterns, with **implementation details**, **schema tables**, and **real-world examples**.

---

## **1. Key Language Patterns**

### **1.1 Object-Oriented Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                                      |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| **PSR-4 Autoloading**     | Standardized namespace-based autoloading (Composer)                         | Dependency management, modular projects          |
| **Constructor Injection** | Dependency injection via `__construct()` method                              | Testable, loosely coupled code                   |
| **Magic Methods**         | Special methods (`__get()`, `__set()`, `__call()`) for dynamic behavior     | Proxies, lazy loading, property abstraction      |
| **Traits**                | Reusable code via `trait` blocks, mitigating diamond inheritance problems    | Code reuse in classes without inheritance        |
| **Final Classes/Methods** | `final` keyword to prevent subclassing/method overriding                     | API stability, security                         |

**Example: Constructor Injection**
```php
class Database {
    private $connection;

    public function __construct(PDO $connection) {
        $this->connection = $connection;
    }
}
```

---

### **1.2 Functional Patterns**
| **Pattern**            | **Description**                                                                 | **Use Case**                              |
|------------------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **Closures (Anonymous Functions)** | First-class functions (`function() { ... }`)                            | Callbacks, decorators, event handlers    |
| **Lambda Arrow Functions** (`fn()`) | Short syntax for closures (PHP 8+)                                  | Minimal callback syntax                   |
| **array_filter()/map()** | Functional iteration without `foreach`                                 | Cleaner data transformations             |
| **Generators**         | `yield` keyword for lazy iteration                                       | Streaming large datasets                  |
| **Partial Function Application** | Pre-binding arguments to functions (`fn($x) => $func(1, $x)`) | Currying, flexible function reuse         |

**Example: Generator**
```php
function rangeGenerator(int $start, int $end): \Generator {
    for ($i = $start; $i <= $end; $i++) {
        yield $i;
    }
}
```

---

### **1.3 Type Safety & Modern PHP**
| **Pattern**            | **Description**                                                                 | **Use Case**                              |
|------------------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **Strict Typing**      | `declare(strict_types=1)` enforces type safety                            | Prevents type juggling bugs               |
| **Union & Named Types** | `string|int` syntax (PHP 8+); `NamedArgument` for clarity       | Parameter validation                      |
| **Enum Support**       | Strongly-typed constants (`enum Foo { A, B }`)                            | Domain modeling                          |
| **Nullsafe Operator (`->?`)** | Safe property access without null checks                  | Reduces boilerplate                       |

**Example: Named Types (PHP 8+)**
```php
function validate(string|int $input): void {
    // ...
}
```

---

### **1.4 Memory & Performance**
| **Pattern**            | **Description**                                                                 | **Use Case**                              |
|------------------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **Object Cloning**     | `__clone()` method for deep vs shallow copies                                | Session storage, caching                  |
| **SplFixedArray**      | Memory-efficient fixed-size arrays                                           | High-performance indexing                |
| **Lazy Evaluation**    | `__toString()` or generators to defer computation                          | Large file processing                    |
| **JIT (OPcache)**      | Bytecode caching for faster execution                                        | Production optimization                  |

**Example: SplFixedArray**
```php
$fixed = new \SplFixedArray(1000000); // Pre-allocated memory
```

---

## **2. Query Examples**
### **2.1 Object-Oriented Query Pattern**
```php
// Using repository pattern
class UserRepository {
    private $db;

    public function __construct(PDO $db) {
        $this->db = $db;
    }

    public function queryActiveUsers(): array {
        $stmt = $this->db->query('SELECT * FROM users WHERE is_active = 1');
        return $stmt->fetchAll(PDO::FETCH_CLASS, 'User');
    }
}
```

### **2.2 Functional Pipeline**
```php
$users = [
    ['name' => 'Alice', 'age' => 30],
    ['name' => 'Bob', 'age' => 25]
];

$adults = array_filter($users, fn($user) => $user['age'] >= 18);
$names   = array_map(fn($user) => $user['name'], $adults);
```

### **2.3 Magic Method for Dynamic Properties**
```php
class DynamicModel {
    private $data = [];

    public function __get($key) {
        return $this->data[$key] ?? null;
    }

    public function __set($key, $value) {
        $this->data[$key] = $value;
    }
}
```

---

## **3. Best Practices & Pitfalls**
### **✅ Best Practices**
1. **Prefer `fn()` over anonymous functions** (cleaner syntax in PHP 8+).
2. **Use `final` classes** to prevent accidental subclassing.
3. **Leverage `enum`** for type-safe constants.
4. **Lazy-load resources** (e.g., `SplFileObject`) for memory efficiency.
5. **Enable `strict_types`** in production to catch type issues early.

### **❌ Common Pitfalls**
1. **Overusing `eval()`** → Security risks; favor closures.
2. **Ignoring `__destruct()`** → Can leak resources (e.g., DB connections).
3. **Abusing `global` variables** → Leads to unmaintainable code.
4. **Not escaping inputs** → SQL injection (use PDO prepared statements).
5. **Mixing OOP and procedural code** → Harder to maintain; stick to a style.

---

## **4. Related Patterns**
- **[PSR-12 Coding Style Guide]** → Consistent formatting for PHP projects.
- **[Dependency Injection (DI)]** → Decouples services via constructor injection.
- **[Builder Pattern]** → Step-by-step object construction (e.g., `DateTimeBuilder`).
- **[Singleton]** → Global access pattern (use sparingly; prefer dependency injection).
- **[Decorator Pattern]** → Runtime wrapping of objects (e.g., logging decorators).

---

## **5. Further Reading**
- [PHP Manual](https://www.php.net/manual/en/) – Official documentation.
- [PHP The Right Way](https://phptherightway.com/) – Community best practices.
- [PHP 8 New Features](https://www.php.net/migration80.php) – Modern syntax updates.

---
**Last Updated:** [Insert Date]
**Version:** 1.0

---
**Note:** This guide focuses on **PHP 8.x**. For legacy versions, adjust type hints and syntax accordingly.