```markdown
---
title: "Intermediate Representation Design: Building Database-Agnostic APIs"
date: "2023-06-15"
author: "Alexei Vartanov"
tags: ["database", "api design", "design patterns", "backend engineering"]
---

# Intermediate Representation Design: The Secret Weapon for Database-Agnostic APIs

As backend developers, we often grapple with the challenge of creating APIs that are both flexible and maintainable. The **Intermediate Representation (IR) design pattern** is a powerful technique that allows us to decouple the input format from the backend logic, enabling seamless integration with multiple databases while reducing duplication and complexity. Think of it like translating a book from English into multiple languages—you first write a universal version (the IR), and then adapt it for each target language (or in our case, database).

IR design is particularly valuable when working with APIs that must support multiple input formats (e.g., REST, GraphQL, CLI) or database backends (e.g., PostgreSQL, MySQL, MongoDB). Without IR, you’d end up with a tangled web of custom parsers and ad-hoc logic for each input or output format. IR lets you abstract away these differences, making your system more modular, testable, and scalable.

In this post, we’ll explore how to implement IR design using a practical example: a user management API that supports both JSON and GraphQL inputs while compiling to a universal schema that can be executed on any SQL database. By the end, you’ll have a reusable framework for handling complex input/output scenarios in your own projects.

---

## The Problem: Custom Logic for Every Input

Imagine you’re building a `User` API with endpoints like `CREATE_USER`, `GET_USER`, and `UPDATE_USER`. Initially, everything seems straightforward:

```go
// REST endpoint for creating a user
func CreateUser(w http.ResponseWriter, r *http.Request) {
    var userData map[string]interface{}
    err := json.NewDecoder(r.Body).Decode(&userData)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Parse fields, validate, and insert into the database
    user := User{
        Name:   userData["name"].(string),
        Email:  userData["email"].(string),
        Age:    int(userData["age"].(float64)),
    }

    // Directly query PostgreSQL
    _, err = db.Exec(`INSERT INTO users (name, email, age) VALUES ($1, $2, $3)`, user.Name, user.Email, user.Age)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
}
```

This works, but now imagine your API needs to support **GraphQL**. Your first thought might be to add a new endpoint:

```go
func graphqlCreateUser(ctx context.Context, input types.CreateUserInput) (*types.User, error) {
    // Parse GraphQL input into a struct
    user := User{
        Name:   input.Name,
        Email:  input.Email,
        Age:    int(input.Age),
    }

    // Repeat the PostgreSQL logic
    _, err := db.Exec(`INSERT INTO users (name, email, age) VALUES ($1, $2, $3)`, user.Name, user.Email, user.Age)
    return &user, err
}
```

This leads to **duplication**:
1. **Input parsing logic** is identical for REST and GraphQL but written twice.
2. **Validation rules** (e.g., "email must be valid") are repeated.
3. **Database queries** are hardcoded to PostgreSQL, making it hard to switch to MySQL or MongoDB.

As the API grows, the duplication becomes unwieldy. You end up with a "spaghetti" architecture where changes to validation or database logic require updates across multiple endpoints. This violates the **DRY (Don’t Repeat Yourself)** principle and makes the system harder to maintain.

---

## The Solution: Intermediate Representation Design

The **Intermediate Representation (IR) pattern** solves this by introducing a universal, normalized schema that sits between the input format and the backend logic. Here’s how it works:

1. **Input Formats** (REST, GraphQL, CLI) serialize their data into a **standardized IR object**.
2. **Validation and Transformation** happens once on the IR, regardless of the input format.
3. **Database-Agnostic Operations** compile the IR into queries for the target database.

This approach ensures that:
- Input parsing logic is centralized.
- Validation and business rules are defined once.
- Database-specific logic is encapsulated in a single place.

---

## Components of the IR Design Pattern

To implement IR design, we’ll need three key components:

1. **IR Schema**: A universal representation of your data and operations.
2. **Input Adapters**: Parsers that translate input formats (REST, GraphQL) into the IR.
3. **IR Compiler**: Converts the IR into database-specific queries.

Let’s walk through each with code examples.

---

### 1. The IR Schema

The IR schema defines a normalized, language-agnostic representation of your data. Here’s an example for `User` operations:

```go
package ir

type UserCreate struct {
    Name  string `validate:"required"`
    Email string `validate:"required,email"`
    Age   int    `validate:"min=0"`
}

type UserUpdate struct {
    ID    int    `validate:"required"`
    Name  *string
    Email *string
    Age   *int
}

type UserQuery struct {
    ID   int
    Name string
    Email string
}
```

Key features of this schema:
- **Required fields** are marked with `validate` tags (using a library like [go-playground/validator](https://github.com/go-playground/validator)).
- **Optional fields** (e.g., `Age` in `UserUpdate`) are pointers to allow partial updates.
- **No database-specific logic**—this is purely a data contract.

---

### 2. Input Adapters

Input adapters parse incoming requests into IR objects. For REST and GraphQL, we’ll create separate handlers, but both will emit the same IR.

#### REST Adapter
```go
func CreateUserREST(w http.ResponseWriter, r *http.Request) {
    var input struct {
        Name  string `json:"name"`
        Email string `json:"email"`
        Age   int    `json:"age"`
    }

    if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Convert to IR
    userIR := ir.UserCreate{
        Name:  input.Name,
        Email: input.Email,
        Age:   input.Age,
    }

    // Validate (validation is handled by the IR compiler later)
    if err := validate.UserCreate(userIR); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Pass IR to the compiler
    result, err := compiler.CreateUser(userIR)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    // Respond with IR or a database-specific result
    json.NewEncoder(w).Encode(result)
}
```

#### GraphQL Adapter
```go
// Define GraphQL input type
type CreateUserInput struct {
    Name string `json:"name"`
    Email string `json:"email"`
    Age  int    `json:"age"`
}

func graphqlCreateUser(ctx context.Context, input CreateUserInput) (*ir.User, error) {
    // Convert to IR
    userIR := ir.UserCreate{
        Name:  input.Name,
        Email: input.Email,
        Age:   input.Age,
    }

    // Validate
    if err := validate.UserCreate(userIR); err != nil {
        return nil, err
    }

    // Compile and execute
    return compiler.CreateUser(userIR)
}
```

Notice how both adapters **reuse the IR schema** and **delegation logic** to the compiler. The actual parsing logic is minimal—it just bridges the input format to the IR.

---

### 3. The IR Compiler

The compiler takes an IR object and generates database-specific queries. Here’s a PostgreSQL implementation:

```go
package compiler

import (
    "database/sql"
    "fmt"
    "yourmodule/ir"
    "yourmodule/validate"
)

type PostgresCompiler struct {
    db *sql.DB
}

func (c *PostgresCompiler) CreateUser(input ir.UserCreate) (*ir.User, error) {
    // Validate once (could also be done in the adapter)
    if err := validate.UserCreate(input); err != nil {
        return nil, err
    }

    // Generate and execute PostgreSQL query
    query := `INSERT INTO users (name, email, age) VALUES ($1, $2, $3) RETURNING id, name, email, age`
    var user ir.User
    err := c.db.QueryRow(query, input.Name, input.Email, input.Age).Scan(
        &user.ID,
        &user.Name,
        &user.Email,
        &user.Age,
    )
    if err != nil {
        return nil, fmt.Errorf("create user failed: %v", err)
    }
    return &user, nil
}

func (c *PostgresCompiler) GetUser(input ir.UserQuery) (*ir.User, error) {
    query := `SELECT id, name, email, age FROM users WHERE 1=1`
    if input.ID > 0 {
        query += ` AND id = $1`
    }
    if input.Name != "" {
        query += ` AND name = $2`
    }
    // ... (add more conditions)

    var user ir.User
    args := []interface{}{}
    if input.ID > 0 {
        args = append(args, input.ID)
    }
    // ... (append more args)

    err := c.db.QueryRow(query, args...).Scan(
        &user.ID,
        &user.Name,
        &user.Email,
        &user.Age,
    )
    if err != nil {
        return nil, fmt.Errorf("get user failed: %v", err)
    }
    return &user, nil
}
```

#### Switching to MySQL or MongoDB
To support another database, you’d create a new compiler (e.g., `MongodbCompiler`) with identical IR methods but database-specific queries:

```go
type MongodbCompiler struct {
    session *mongo.Session
}

func (c *MongodbCompiler) CreateUser(input ir.UserCreate) (*ir.User, error) {
    collection := c.session.Database("api").Collection("users")
    result, err := collection.InsertOne(context.TODO(), bson.M{
        "name":  input.Name,
        "email": input.Email,
        "age":   input.Age,
    })
    if err != nil {
        return nil, err
    }

    // Return the inserted document (simplified)
    var user ir.User
    err = collection.FindOne(context.TODO(), bson.M{"_id": result.InsertedID}).Decode(&user)
    return &user, err
}
```

By keeping the IR methods identical, you **decouple the business logic from the database**. The same IR can now be used with PostgreSQL, MySQL, or MongoDB without changing the adapters.

---

## Implementation Guide: Step-by-Step

Here’s how to implement IR design in your project:

### 1. Define the IR Schema
Start by modeling your domain in a neutral way. For example:

```go
// ir/user.go
package ir

type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
    Age   int    `json:"age"`
}

type CreateUser struct {
    Name  string `validate:"required"`
    Email string `validate:"required,email"`
    Age   int    `validate:"min=0"`
}
```

### 2. Create Input Adapters
Write parsers for each input format (REST, GraphQL, CLI) that convert to IR.

Example REST adapter:
```go
// handlers/rest.go
func CreateUser(w http.ResponseWriter, r *http.Request) {
    var input struct {
        Name  string `json:"name"`
        Email string `json:"email"`
        Age   int    `json:"age"`
    }
    if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Convert to IR
    userIR := ir.UserCreate{
        Name:  input.Name,
        Email: input.Email,
        Age:   input.Age,
    }

    // Validate
    if err := validate.Struct(userIR); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Compile and execute
    result, err := compiler.CreateUser(userIR)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    json.NewEncoder(w).Encode(result)
}
```

### 3. Implement the Compiler
Write a compiler for each database backend. Share the IR methods but vary the query logic.

Example PostgreSQL compiler:
```go
// compiler/postgres.go
type PostgresCompiler struct {
    db *sql.DB
}

func (c *PostgresCompiler) CreateUser(input ir.UserCreate) (*ir.User, error) {
    query := `INSERT INTO users (name, email, age) VALUES ($1, $2, $3) RETURNING id, name, email, age`
    var user ir.User
    err := c.db.QueryRow(query, input.Name, input.Email, input.Age).Scan(
        &user.ID,
        &user.Name,
        &user.Email,
        &user.Age,
    )
    return &user, err
}
```

### 4. Configure the Compiler
Set up the compiler in your application startup:

```go
// main.go
func main() {
    db, _ := sql.Open("postgres", "your_connection_string")
    compiler := &compiler.PostgresCompiler{db: db}
    // Or for MongoDB:
    // compiler := &compiler.MongodbCompiler{session: session}

    // Register adapters (REST, GraphQL, etc.)
    http.HandleFunc("/users", handlers.CreateUser(compiler))
    // ... other endpoints
}
```

### 5. Test Thoroughly
Test your adapters and compiler in isolation:
- Validate that input parsing works for all formats.
- Test validation rules (e.g., invalid email should fail).
- Verify that the same IR produces correct results across databases.

---

## Common Mistakes to Avoid

1. **Not Normalizing the IR Enough**
   - *Problem*: If your IR is too tightly coupled to a specific input format, you lose flexibility.
   - *Solution*: Keep the IR as neutral as possible. For example, don’t include database column names in the IR.

2. **Skipping Validation**
   - *Problem*: Validating only in the adapter or only in the compiler can lead to inconsistent behavior.
   - *Solution*: Validate **once** in the compiler (or adapter, but ensure consistency).

3. **Over-Engineering the IR**
   - *Problem*: Adding too many IR layers can make the system harder to understand.
   - *Solution*: Start simple. Refactor the IR as your needs grow.

4. **Ignoring Database-Specific Quirks**
   - *Problem*: Not accounting for dialect differences (e.g., PostgreSQL’s `RETURNING` vs MySQL’s `LAST_INSERT_ID`).
   - *Solution*: Keep compiler logic separate and handle differences in each compiler.

5. **Forgetting to Document the IR Schema**
   - *Problem*: Without clear documentation, other developers (or your future self) will struggle to understand the IR contract.
   - *Solution*: Add comments or generate docs for the IR schema.

---

## Key Takeaways

- **Decouple input from logic**: IR design allows you to process REST, GraphQL, and CLI inputs through a single pipeline.
- **Centralize validation**: Define validation rules once in the IR, not per input format.
- **Support multiple databases**: Compile the IR to queries for PostgreSQL, MySQL, MongoDB, etc., without changing the IR.
- **Reduce duplication**: Avoid repeating parsing, validation, or database logic across endpoints.
- **Improve testability**: Since the IR is neutral, you can unit-test adapters and compilers independently.

---

## Conclusion

Intermediate Representation design is a powerful pattern for building flexible, maintainable APIs that can handle multiple input formats and database backends. By abstracting the complexity into a universal IR schema, you reduce duplication, centralize logic, and make your system easier to extend.

Start small: pick one domain (e.g., `User`) and apply IR design to its most complex operations. As you gain confidence, expand the pattern to other domains. Over time, your APIs will become more resilient, scalable, and easier to maintain—all while keeping the core logic clean and database-agnostic.

Happy coding!
```

---
**Post Notes:**
- **Word count**: ~1,800 words
- **Style**: Practical, code-first, and honest about tradeoffs (e.g., initial setup effort vs. long-term maintainability).
- **Audience**: Intermediate backend developers who want to improve their API design skills.
- **Technologies Used**: Go (language-agnostic patterns apply to any language), PostgreSQL/MySQL/MongoDB (as examples), REST/GraphQL (as input formats).
- **Tradeoffs Highlighted**: IR design requires upfront effort but pays off in maintainability and flexibility.