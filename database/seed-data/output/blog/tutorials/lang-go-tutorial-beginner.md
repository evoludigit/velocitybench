```markdown
---
title: "Go Language Patterns: Clean, Scalable Backend Code (With Real Examples)"
date: "2023-11-15"
author: "Alex Mercer"
description: "A practical guide to Go language patterns for beginner backend developers. Learn how to write clean, maintainable, and scalable Go code with real-world examples."
tags: ["Go", "Backend", "Language Patterns", "Best Practices", "API Design"]
series: ["Backend Engineering Patterns"]
---

# Go Language Patterns: Clean, Scalable Backend Code (With Real Examples)

> "Go is designed to make it easy to write simple code, but not to write simple programs." — Robert Griesemer (Go's co-creator)

As backend developers, we often face challenges like slow performance, tight coupling, or hard-to-maintain codebases—even in a language as elegant as Go. The **Go Language Patterns** (often called "Go Idioms") are conventions and best practices that help us write clean, efficient, and scalable backend code.

In this tutorial, we’ll explore **practical Go patterns**—like error handling, concurrency, struct composition, and interface-based design—that will make your Go code more robust and easier to maintain. By the end, you’ll know how to avoid common pitfalls and write Go code that feels intuitive and professional.

---

## The Problem: Code Without Go Patterns

Imagine you’re building a REST API in Go for a simple task tracker. Without following Go patterns, you might end up with:

### Problem 1: Fragile Error Handling
```go
package main

import (
	"fmt"
	"net/http"
)

func handleRequest(w http.ResponseWriter, r *http.Request) {
	tasks, err := getTasks(r)
	if err != nil {
		fmt.Println("Error:", err) // Silent failure
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	w.Write([]byte(fmt.Sprintf("Tasks: %v", tasks)))
}

func getTasks(r *http.Request) ([]string, error) {
	// Simulate a DB query
	return nil, fmt.Errorf("database error") // No way to distinguish errors
}
```
- **Issue**: Errors are logged but not consistently handled.
- **Result**: Users see `500 Internal Server Error` without context.

### Problem 2: Tightly Coupled Code
```go
package main

import (
	"database/sql"
	"fmt"
)

type Task struct {
	ID    int
	Title string
}

type Database struct {
	conn *sql.DB
}

func (d *Database) GetTasks() ([]Task, error) {
	rows, err := d.conn.Query("SELECT id, title FROM tasks")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tasks []Task
	for rows.Next() {
		var t Task
		if err := rows.Scan(&t.ID, &t.Title); err != nil {
			return nil, err
		}
		tasks = append(tasks, t)
	}
	return tasks, nil
}
```
- **Issue**: `Database` is tightly coupled to `sql.DB`, making it hard to mock or replace.
- **Result**: Testing becomes difficult, and the code isn’t production-ready.

### Problem 3: Uncontrolled Concurrency
```go
package main

import "sync"

func processTasks(tasks []string) {
	var wg sync.WaitGroup
	var result string

	for _, task := range tasks {
		wg.Add(1)
		go func(t string) {
			defer wg.Done()
			result += fmt.Sprintf("%s processed\n", t) // Race condition!
		}(task)
	}
	wg.Wait()
	fmt.Println(result)
}
```
- **Issue**: Race condition when appending to `result` from goroutines.
- **Result**: Undefined behavior (garbage or loss of data).

---

## The Solution: Go Language Patterns

Go patterns are small but powerful conventions that address these issues. Here are the key patterns we’ll cover:

1. **Error Handling**: Use `errors.New` + error checks with `if err != nil`.
2. **Struct Composition**: Favor composition over inheritance.
3. **Interface-Based Design**: Use interfaces for abstraction and dependency injection.
4. **Concurrency**: Safe goroutine patterns (channels, `sync.WaitGroup`, `sync.Mutex`).
5. **Context**: Propagate cancellation and deadlines across goroutines.
6. **Dependency Injection**: Pass dependencies explicitly.

---

## Components/Solutions: How to Fix the Problems

### 1. Proper Error Handling (with `fmt.Errorf` and `wrap`)
```go
package main

import (
	"errors"
	"fmt"
	"net/http"
)

func handleRequest(w http.ResponseWriter, r *http.Request) {
	tasks, err := getTasks(r)
	if err != nil {
		if errors.Is(err, ErrDatabaseUnavailable) {
			w.WriteHeader(http.StatusServiceUnavailable)
			fmt.Fprintf(w, "Service unavailable")
		} else {
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Error: %v", err)
		}
		return
	}
	w.Write([]byte(fmt.Sprintf("Tasks: %v", tasks)))
}

var (
	ErrDatabaseUnavailable = errors.New("database is unavailable")
	ErrTaskNotFound        = errors.New("task not found")
)

func getTasks(r *http.Request) ([]string, error) {
	// Simulate a DB query with wrapped errors
	return nil, fmt.Errorf("%w: could not connect to DB", ErrDatabaseUnavailable)
}
```
#### Key Improvements:
- **Error Types**: Define custom errors (e.g., `ErrDatabaseUnavailable`) for better error handling.
- **Error Wrapping**: Use `%w` to wrap errors (`fmt.Errorf("%w: message", err)`) for debugging.

---

### 2. Struct Composition (Composition over Inheritance)
```go
package main

import "database/sql"

// Database interface (abstraction)
type Database interface {
	GetTasks() ([]Task, error)
}

// Concrete implementation
type SQLDatabase struct {
	conn *sql.DB
}

func (d *SQLDatabase) GetTasks() ([]Task, error) {
	rows, err := d.conn.Query("SELECT id, title FROM tasks")
	if err != nil {
		return nil, fmt.Errorf("query failed: %w", err)
	}
	defer rows.Close()

	var tasks []Task
	for rows.Next() {
		var t Task
		if err := rows.Scan(&t.ID, &t.Title); err != nil {
			return nil, fmt.Errorf("scan failed: %w", err)
		}
		tasks = append(tasks, t)
	}
	return tasks, nil
}

// Task represents a simple task.
type Task struct {
	ID    int
	Title string
}
```
#### Key Improvements:
- **Abstraction**: `Database` is an interface, making it easy to mock or replace with a `MockDatabase`.
- **Flexibility**: New implementations (e.g., `RedisDatabase`) can be added without changing existing code.

---

### 3. Interface-Based Design (Dependency Injection)
```go
package main

import "fmt"

type TaskService struct {
	db Database // Dependency injected
}

func (s *TaskService) GetTasks() ([]Task, error) {
	return s.db.GetTasks()
}

type TaskHandler struct {
	service *TaskService
}

func NewTaskHandler(db Database) *TaskHandler {
	return &TaskHandler{
		service: &TaskService{db: db},
	}
}

func (h *TaskHandler) Handle(w http.ResponseWriter, r *http.Request) {
	tasks, err := h.service.GetTasks()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	fmt.Fprintf(w, "Tasks: %v", tasks)
}
```
#### Key Improvements:
- **Testable**: Replace `SQLDatabase` with `MockDatabase` for unit tests.
- **Decoupled**: `TaskService` doesn’t know about `sql.DB`; it depends on `Database`.

---

### 4. Safe Concurrency with Channels and `sync.WaitGroup`
```go
package main

import (
	"fmt"
	"sync"
)

func processTasks(tasks []string) string {
	var wg sync.WaitGroup
	var results []string
	ch := make(chan string, len(tasks)) // Buffered channel

	for _, task := range tasks {
		wg.Add(1)
		go func(t string) {
			defer wg.Done()
			ch <- fmt.Sprintf("%s processed", t) // Send result via channel
		}(task)
	}
	go func() {
		wg.Wait()
		close(ch) // Close channel when all goroutines finish
	}()

	// Collect results
	for result := range ch {
		results = append(results, result)
	}

	return fmt.Sprintf("%v", results)
}

func main() {
	tasks := []string{"task1", "task2", "task3"}
	fmt.Println(processTasks(tasks))
}
```
#### Key Improvements:
- **No Race Conditions**: Channels ensure safe communication between goroutines.
- **Clean Shutdown**: `wg.Wait()` ensures all goroutines finish before returning.

---

### 5. Context for Cancellation and Deadlines
```go
package main

import (
	"context"
	"fmt"
	"time"
)

func longRunningTask(ctx context.Context) (string, error) {
	select {
	case <-ctx.Done():
		return "", ctx.Err() // Cancelled or timed out
	case <-time.After(5 * time.Second):
		return "Task completed", nil
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	result, err := longRunningTask(ctx)
	if err != nil {
		fmt.Println("Error:", err) // "context deadline exceeded"
		return
	}
	fmt.Println(result)
}
```
#### Key Improvements:
- **Cancellation**: `ctx.Done()` notifies goroutines to stop.
- **Deadlines**: Enforce timeouts for long-running operations.

---

## Implementation Guide: Step-by-Step

### Step 1: Set Up Your Project
```bash
mkdir task-tracker
cd task-tracker
go mod init github.com/yourname/task-tracker
```

### Step 2: Define Interfaces and Structs
```go
// database.go
package main

import "database/sql"

// Database interface
type Database interface {
	GetTasks() ([]Task, error)
}

// Task represents a task.
type Task struct {
	ID    int    `json:"id"`
	Title string `json:"title"`
}
```

### Step 3: Implement Database Logic
```go
// sql_database.go
package main

import (
	"database/sql"
	"fmt"
)

type SQLDatabase struct {
	conn *sql.DB
}

func NewSQLDatabase(conn *sql.DB) *SQLDatabase {
	return &SQLDatabase{conn: conn}
}

func (d *SQLDatabase) GetTasks() ([]Task, error) {
	// ... (implementation from earlier)
}
```

### Step 4: Write a Service Layer
```go
// task_service.go
package main

type TaskService struct {
	db Database
}

func NewTaskService(db Database) *TaskService {
	return &TaskService{db: db}
}

func (s *TaskService) GetTasks() ([]Task, error) {
	return s.db.GetTasks()
}
```

### Step 5: Handle HTTP Requests
```go
// main.go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
)

func main() {
	// Initialize DB
	db, err := sql.Open("postgres", "postgres://user:pass@localhost/db?sslmode=disable")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Initialize SQLDatabase
	sqlDB := NewSQLDatabase(db)

	// Initialize TaskService
	service := NewTaskService(sqlDB)

	// HTTP handler
	http.HandleFunc("/tasks", func(w http.ResponseWriter, r *http.Request) {
		tasks, err := service.GetTasks()
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		fmt.Fprintf(w, "%v", tasks)
	})

	// Start server
	log.Println("Server running on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```

---

## Common Mistakes to Avoid

1. **Ignoring Errors**
   - ❌ `err := getTasks();` (silent failure)
   - ✅ `tasks, err := getTasks(); if err != nil { ... }`

2. **Overusing Global Variables**
   - ❌ `var db *sql.DB` (hard to test)
   - ✅ Pass dependencies via constructor (e.g., `NewTaskService(db)`).

3. **Uncontrolled Goroutines**
   - ❌ Spawning goroutines without `sync.WaitGroup` or channels.
   - ✅ Use `sync.WaitGroup` or channels to manage goroutines.

4. **Tight Coupling to `sql.DB`**
   - ❌ `type Database { conn *sql.DB }` (not testable).
   - ✅ `type Database interface { GetTasks() ([]Task, error) }`.

5. **Not Using Context**
   - ❌ Long-running operations without timeouts.
   - ✅ Always pass `context.Context` to functions.

---

## Key Takeaways

- **Error Handling**: Use `errors.New`, `fmt.Errorf`, and wrap errors with `%w`.
- **Composition**: Prefer struct composition over inheritance for flexibility.
- **Abstraction**: Define interfaces for dependencies (e.g., `Database`).
- **Concurrency**: Use channels and `sync.WaitGroup` for safe goroutines.
- **Context**: Always use `context.Context` for cancellation and timeouts.
- **Dependency Injection**: Pass dependencies explicitly (not globally).

---

## Conclusion

Go language patterns are not just idioms—they’re best practices that make your code **cleaner, safer, and more maintainable**. By following these patterns, you’ll write backend code that:
- Handles errors gracefully.
- Is easy to test and extend.
- Scales well under concurrency.
- Follows Go’s philosophy of simplicity and efficiency.

Start small: Refactor one component of your project using these patterns, and you’ll see the difference. Happy coding!

---

### Further Reading
- [Go Blog: Finding Missing Breaks](https://go.dev/blog/missing-breaks)
- [Effective Go](https://go.dev/doc/effective_go.html)
- [Gophercises](https://gophercises.com/) (Practice Go patterns)

---
```