# **[JavaScript Language Patterns] Reference Guide**

## **Overview**
The **[JavaScript Language Patterns]** reference guide provides a structured breakdown of essential JavaScript constructs, idioms, and best practices. This documentation covers core patterns such as **first-class functions, closures, async/await, prototypes, and modular design**, along with their implementations, use cases, and anti-patterns.

Designed for developers, this guide ensures consistency in code style, performance optimization, and maintainability. It emphasizes **es6+ language features**, including **arrow functions, destructuring, generators, and promises**, while addressing common pitfalls like **callback hell, memory leaks, and scope issues**.

---

## **Schema Reference**

| **Pattern**          | **Description**                                                                 | **Key Features**                                                                 | **Use Case**                                                                 |
|----------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **First-Class Functions** | Functions are treated as objects (assignable, passable, callable as values). | Assignable, reusable, higher-order functions (HOFs).                          | Event handlers, callbacks, functional programming (e.g., `map`, `filter`). |
| **Closures**         | Inner functions retaining access to outer scope variables.                      | Encapsulation, data privacy, event handlers.                                    | Private variables, debouncing/throttling, modular state management.         |
| **Async/Await**      | Simplified asynchronous code using `async/await` syntax.                       | Non-blocking operations, promise chaining without `.then()/.catch()`.         | API calls, file I/O, user input handling.                                   |
| **Prototype-Based OOP** | Objects inherit from prototypes (avoiding class-based inheritance).          | Prototypal inheritance, dynamic property assignment.                            | Lightweight class implementations, prototype chaining.                     |
| **Module Pattern**   | Encapsulating variables/functions using IIFEs or ES6 `import/export`.         | Private/protected members via closures, clean scope separation.                | Large-scale app organization, code reusability.                            |
| **Arrow Functions**  | Lexical `this` binding and concise syntax (`=>`).                               | No `this` binding issues, shorter syntax.                                        | Callbacks, event handlers, functional components.                            |
| **Destructuring**    | Extracting values from objects/arrays.                                          | Cleaner variable assignment, default values.                                    | API response handling, object parameter extraction.                        |
| **Generators**       | Pause/resume execution with `yield`.                                            | Iterators, lazy loading, cooperative multitasking.                             | Data streaming, custom loops, step-by-step processing.                      |
| **Promises**         | Represent asynchronous operations with `.then()/.catch()`.                     | Error handling, chaining, fallbacks.                                           | Network requests, user actions, file operations.                           |
| **Template Literals** | Multiline strings with embedded expressions (`${var}`).                        | String formatting, multiline templates.                                         | Dynamic content rendering, logging, documentation.                          |

---

## **Implementation Details**

### **1. First-Class Functions**
- **Definition**: Functions are objects (methods, properties, and values).
- **Implementation**:
  ```javascript
  const greet = function(name) { return `Hello, ${name}!` };
  const greetFn = function() { console.log("World!"); };
  greetFn(); // "World!"
  ```
- **Best Practices**:
  - Use arrow functions for callbacks to avoid `this` binding issues.
  - Example:
    ```javascript
    const users = ["Alice", "Bob", "Charlie"];
    users.forEach(user => console.log(user)); // Arrow function (lexical `this`)
    ```

- **Anti-Patterns**:
  - Avoid polluting the global scope with standalone functions.

---

### **2. Closures**
- **Definition**: Inner functions retaining access to outer scope variables.
- **Implementation**:
  ```javascript
  function createCounter() {
    let count = 0;
    return {
      increment: () => ++count,
      getCount: () => count
    };
  }
  const counter = createCounter();
  counter.increment(); // 1
  counter.getCount();  // 1
  ```
- **Best Practices**:
  - Use closures for **private state** in modules.
- **Anti-Patterns**:
  - Overusing closures can cause **memory leaks** (e.g., detached event listeners).

---

### **3. Async/Await**
- **Definition**: Simplified async/await syntax for promises.
- **Implementation**:
  ```javascript
  async function fetchData() {
    const response = await fetch("https://api.example.com/data");
    const data = await response.json();
    return data;
  }
  ```
- **Best Practices**:
  - Always wrap `async` functions in `try/catch`.
- **Anti-Patterns**:
  - Avoid nested `.then()` chains (refactor to `async/await`).

---

### **4. Prototype-Based OOP**
- **Definition**: Objects inherit from a shared prototype.
- **Implementation**:
  ```javascript
  function Person(name) {
    this.name = name;
  }
  Person.prototype.greet = function() {
    console.log(`Hi, I'm ${this.name}`);
  };
  const alice = new Person("Alice");
  alice.greet(); // "Hi, I'm Alice"
  ```
- **Best Practices**:
  - Use `Object.create()` for manual prototype inheritance.
- **Anti-Patterns**:
  - Avoid deep prototype chains (can cause performance issues).

---

### **5. Module Pattern**
- **Definition**: Encapsulating code using IIFEs or ES6 modules.
- **Implementation (IIFE)**:
  ```javascript
  const MyModule = (function() {
    let privateVar = "secret";
    return {
      publicMethod: function() {
        console.log(privateVar);
      }
    };
  })();
  ```
- **Implementation (ES6)**:
  ```javascript
  // module.js
  export const greet = (name) => `Hello, ${name}!`;
  ```
- **Best Practices**:
  - Prefer ES6 `import/export` for modern JS.
- **Anti-Patterns**:
  - Avoid global variable pollution.

---

## **Query Examples**

### **1. First-Class Functions (HOFs)**
```javascript
// Using `map` with a HOF
const numbers = [1, 2, 3];
const squared = numbers.map(n => n * n); // [1, 4, 9]
```

### **2. Closures (Counter Example)**
```javascript
// Nested counters
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100); // Closes over `i` (logs 3)
}
```

### **3. Async/Await (API Call)**
```javascript
async function fetchUser(id) {
  const res = await fetch(`https://api.example.com/users/${id}`);
  const user = await res.json();
  return user;
}
```

### **4. Prototype Inheritance (Mixins)**
```javascript
// Adding methods to a prototype
const Mixin = {
  log: function() { console.log(this.name); }
};
Object.assign(Person.prototype, Mixin);
alice.log(); // "Alice"
```

### **5. Module Pattern (ES6)**
```javascript
// Importing a module
import { greet } from "./module.js";
console.log(greet("Bob")); // "Hello, Bob!"
```

---

## **Related Patterns**

| **Related Pattern**       | **Description**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|
| **Observer Pattern**      | Event-based communication (e.g., `addEventListener`).                          |
| **Singleton Pattern**     | Ensures only one instance of a class exists (e.g., `module.exports.default`).    |
| **Factory Pattern**       | Object creation via a factory function instead of constructors.                 |
| **Decorator Pattern**     | Adding behavior to objects dynamically (e.g., `Object.assign`).                |
| **Event Loop & Callbacks** | Understand how JS handles async operations (non-blocking I/O).                  |

---

## **Key Takeaways**
- **First-class functions** enable **functional programming** (e.g., `map`, `reduce`).
- **Closures** are powerful for **encapsulation** but can cause **memory leaks** if misused.
- **Async/await** simplifies **asynchronous code** but requires proper error handling.
- **Prototypes** offer **flexible inheritance** without heavy class syntax.
- **Modules** improve **code organization** and **scope management**.

This guide ensures **consistent, maintainable, and performant** JavaScript code. For further reading, consult the [MDN Docs](https://developer.mozilla.org/) or **Airbnb JavaScript Style Guide**.