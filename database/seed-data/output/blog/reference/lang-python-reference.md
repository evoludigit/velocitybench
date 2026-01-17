# **[Pattern] Python Language Patterns – Reference Guide**

---

## **Overview**
Python’s design philosophy ("The Zen of Python") emphasizes readability, simplicity, and expressiveness. This **Python Language Patterns** reference guide documents core idioms, best practices, and anti-patterns that Python developers use to write efficient, maintainable, and Pythonic code.

From **context managers** to **decorators**, this guide covers:
- Key language features and their typical use cases
- Common implementation patterns (e.g., iterators, generators)
- Performance considerations and edge cases
- Best practices for readability and maintainability
- Pitfalls to avoid

Whether you're optimizing loops, working with objects, or managing resources, these patterns ensure you leverage Python’s strengths while avoiding common pitfalls.

---

## **Schema Reference**

Below is a categorized table of Python language patterns, their **purpose**, **implementation**, and **use cases**.

| **Category**               | **Pattern Name**               | **Purpose**                                                                                               | **Implementation Example**                                                                                     | **Best Practices**                                                                                          | **Pitfalls to Avoid**                                                                                     |
|----------------------------|--------------------------------|-----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Basic Control Flow**     | **Walrus Operator (`:=`)**     | Assign and evaluate in a single expression (Python 3.8+)                                                 | `if (n := len(data)) > 0:`                                                                                   | Use sparingly; avoids repeated evaluations but can obscure logic.                                         | Overuse can reduce readability (e.g., in deeply nested expressions).                                      |
|                            | **Unpacking with `*`**         | Distribute iterables into variables (e.g., function args, list splits)                                  | `a, b, *rest = [1, 2, 3, 4]`                                                                               | Use for flexibility (e.g., variable-length args).                                                        | Unchecked `*rest` can lead to unexpected behavior if unused.                                             |
|                            | **Ternary Operator**           | Conditional expression in one line                                                                       | `value = 'A' if x > 0 else 'B'`                                                                                | Prefer for simple conditions; avoid complex nested ternaries.                                             | Overuse can make code harder to debug.                                                                     |
| **Iteration & Loops**      | **List/Dict Comprehensions**   | Concise data transformations                                                                             | `[x**2 for x in range(10)]` or `{k: v**2 for k, v in data.items()}`                                        | Faster than `for` loops for simple operations                                                             | Avoid in performance-critical loops with side effects.                                                   |
|                            | **Generator Expressions**      | Memory-efficient iteration (like comprehensions but lazy-evaluated)                                      | `(x**2 for x in range(10))`                                                                                 | Useful for large datasets or streaming data.                                                              | Misusing as a list (e.g., `[x for x in gen]`) exhausts the generator.                                   |
|                            | **`itertools` Patterns**       | Efficient iteration tools (e.g., `product`, `chain`, `groupby`)                                          | `from itertools import chain; chain([1, 2], [3, 4])`                                                          | Optimize for large datasets (e.g., `tee` for multi-pass iteration).                                       | Avoid `product`/`permutations` for large inputs (computational explosion).                              |
| **Functional Patterns**    | **`functools.lru_cache`**      | Memoization (caching function results)                                                                   | `@lru_cache(maxsize=128)`                                                                                   | Use for expensive, repeatable computations.                                                              | Cache invalidation can lead to stale data.                                                               |
|                            | **`partial` for Fixed Args**   | Freeze some function arguments                                                                          | `from functools import partial; square = partial(pow, exponent=2)`                                           | Reduces boilerplate for common call patterns.                                                          | Debugging partial calls can be tricky.                                                                   |
|                            | **Lambda Functions**           | Short, anonymous functions (often with `map`, `filter`)                                                  | `sorted(data, key=lambda x: x[1])`                                                                            | Use for simple, one-off operations.                                                                       | Overuse can make code harder to read (prefer named functions).                                            |
| **Object-Oriented Patterns** | **`@property` Decorator**      | Control attribute access (getters/setters)                                                               | `@property`<br>`def name(self): return self._name`                                                          | Encapsulate complex logic in property access.                                                             | Overuse can create excessive boilerplate.                                                                |
|                            | **`@dataclass`**               | Auto-generate boilerplate (e.g., `__init__`, `__repr__`)                                               | `@dataclass`<br>`class Point:`<br>`x: int`<br>`y: int`                                                     | Reduces verbosity for data holders.                                                                       | Avoid for mutable objects without custom logic.                                                          |
|                            | **Abstract Base Classes (ABC)** | Define interfaces (e.g., `@abstractmethod`)                                                              | `from abc import ABC, abstractmethod`<br>`class Shape(ABC):`<br>`@abstractmethod def area(self): ...`     | Enforce contracts without inheritance ties.                                                               | Over-abstraction can make inheritance hierarchies rigid.                                                 |
| **Resource Management**    | **Context Managers (`with`)**  | Safe resource handling (files, locks, etc.)                                                              | `with open('file.txt') as f:`                                                                               | Always prefer `with` over manual `open()`/`close()`.                                                    | Forgetting `with` can lead to resource leaks.                                                           |
|                            | **`@contextlib.contextmanager`** | Custom context managers (generators)                                                                     | `@contextmanager`<br>`def timer(): ...`<br>`with timer(): ...`                                               | Extend `with` functionality without subclassing.                                                          | Complex decorators can obscure intent.                                                                      |
| **Advanced Patterns**      | **Decorators (`@decorator`)**  | Modify function/class behavior (e.g., logging, timers)                                                 | `@timer`<br>`def foo(): ...`                                                                              | Use for cross-cutting concerns (logging, auth, retries).                                                 | Deeply nested decorators can be hard to debug.                                                          |
|                            | **Singleton Pattern**           | Restrict class instantiation to one instance                                                            | `__new__` override with `_instance` check                                                                  | Use sparingly (e.g., configuration managers).                                                            | Breaks dependency injection; not thread-safe by default.                                                  |
|                            | **Observer Pattern**           | Event-driven updates (e.g., `weakref` + callbacks)                                                      | `def callback(): ...`<br>`register(cb)`                                                                   | Decouple components via events.                                                                           | Memory leaks if callbacks aren’t cleaned up.                                                              |
| **Concurrency Patterns**   | **Threading (`Thread`/`Queue`)** | Parallel execution (I/O-bound tasks)                                                                     | `from threading import Thread`<br>`t = Thread(target=func)`                                                 | Use for CPU-bound tasks with `multiprocessing` instead.                                                  | Global Interpreter Lock (GIL) limits true parallelism for CPU tasks.                                      |
|                            | **Async/Await (`asyncio`)**     | Non-blocking I/O (coroutines)                                                                           | `async def fetch_data(): ...`<br>`await asyncio.gather(...)`                                                 | Ideal for high-concurrency networking.                                                                   | Blocking calls (e.g., `time.sleep`) break async flow.                                                    |
| **Metaprogramming**        | **Metaclasses**                 | Control class creation (advanced)                                                                         | `class Meta(type): ...`<br>`class MyClass(metaclass=Meta): ...`                                             | Rarely needed; prefer decorators or composition.                                                        | Overuse increases complexity and debugging difficulty.                                                   |
|                            | **Monkey Patching**             | Dynamically modify classes/functions at runtime                                                          | `import module`<br>`module.func = new_func`                                                                  | Use for testing or quick fixes.                                                                            | Unpredictable behavior; avoid in production.                                                             |
| **Type Hints & Safety**    | **Type Annotations**            | Static type checking (PEP 484)                                                                          | `def greet(name: str) -> str:`                                                                              | Improves IDE support and catches bugs early.                                                             | Mock types (e.g., `Any`) can defeat type safety.                                                         |
|                            | **`typing` Module**             | Advanced type hints (e.g., `Optional`, `List`, `Callable`)                                              | `from typing import List`<br>`def process(items: List[int]) -> None:`                                       | Use for complex data structures.                                                                         | Overly verbose hints can reduce readability.                                                              |
| **Error Handling**         | **`try/except/else/finally`**   | Structured exception handling                                                                          | `try:`<br>`    do_something()`<br>`except ValueError:`<br>`    handle()`<br>`else:`<br>`    success()`<br>`finally:`<br>`    cleanup()` | Catch specific exceptions, not bare `except:`.                                                           | Ignoring exceptions (`except: pass`) hides bugs.                                                        |
|                            | **`contextlib.suppress`**      | Ignore specific exceptions silently                                                                   | `with suppress(FileNotFoundError):`                                                                      | Use for expected exceptions (e.g., file access).                                                        | Overuse can mask real issues.                                                                              |

---

## **Query Examples**

### **1. Loop Optimization**
**Problem:** Slow list comprehension with side effects.
**Solution:** Use generator expressions for memory efficiency.
```python
# ❌ Inefficient (creates full list)
squares = [x**2 for x in range(1_000_000) if x % 2 == 0]

# ✅ Efficient (lazy evaluation)
squares = (x**2 for x in range(1_000_000) if x % 2 == 0)  # Generator
```

### **2. Decorator for Timing**
**Problem:** Measure function execution time.
**Solution:** Use a decorator.
```python
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
```

### **3. Singleton Implementation**
**Problem:** Ensure only one instance of a class exists.
**Solution:** Override `__new__`.
```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Usage
a = Singleton()
b = Singleton()
print(a is b)  # True
```

### **4. Context Manager for Database**
**Problem:** Safely handle database connections.
**Solution:** Custom context manager.
```python
from contextlib import contextmanager

@contextmanager
def db_connection(url):
    conn = connect_to_db(url)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with db_connection("sqlite:///data.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
```

### **5. Type Hinting for Dynamic Arguments**
**Problem:** Handle variable-length positional arguments with types.
**Solution:** Use `*args` and `typing.List`.
```python
from typing import List

def process_numbers(*nums: int) -> List[int]:
    return [x * 2 for x in nums]

result = process_numbers(1, 2, 3)  # List[int]
```

### **6. Observer Pattern for Callbacks**
**Problem:** Notify multiple functions when an event occurs.
**Solution:** Use a callback registry.
```python
callbacks = []

def register_callback(cb):
    callbacks.append(cb)

def notify(event):
    for cb in callbacks:
        cb(event)

# Usage
def handler(event):
    print(f"Event received: {event}")

register_callback(handler)
notify("data_loaded")
```

---

## **Related Patterns**
1. **[Iterators & Generators]** – Leverage lazy evaluation for memory efficiency.
2. **[Functional Programming]** – Use `map`, `filter`, and `reduce` for declarative code.
3. **[Dependency Injection]** – Prefer constructor injection over global state (e.g., `dataclasses` + `typing`).
4. **[Design Patterns]** – Apply GoF patterns (e.g., **Factory**, **Strategy**) with Python’s OOP features.
5. **[Testing Patterns]** – Use `unittest`, `pytest`, and `hypothesis` for robust validation.
6. **[Concurrency Alternatives]** – For CPU-bound tasks, explore `multiprocessing` or `concurrent.futures`.
7. **[Performance Optimization]** – Profile with `timeit` and `cProfile` before optimizing.

---
**Key Takeaways:**
- Prefer **Pythonic** constructs (e.g., comprehensions over loops).
- Use **context managers** for resource safety.
- Leverage **decorators** for cross-cutting concerns.
- **Type hints** improve maintainability without runtime overhead.
- Avoid **anti-patterns** like global state, deep inheritance, or excessive monkey patching.

For further reading, consult:
- [Python Documentation](https://docs.python.org/3/tutorial/)
- *Fluent Python* (Luciano Ramalho)
- *Effective Python* (Brett Slatkin)